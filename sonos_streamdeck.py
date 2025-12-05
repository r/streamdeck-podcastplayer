#!/usr/bin/env python3
"""
Main entry point for the Sonos Stream Deck controller.
"""
from __future__ import annotations

import os
import sys
import http.server
import time
import signal
import threading
from typing import Any, Optional, Callable

from StreamDeck.DeviceManager import DeviceManager

from podplayer.config import get_config
from podplayer.utils import log
from podplayer.persistence import init_database, load_positions_from_db, get_episode_metadata
from podplayer.sonos_control import connect_sonos, get_playback_info, detect_current_podcast
from podplayer.podcast_manager import list_podcast_files, play_podcast_episode
from podplayer.streamdeck_ui import load_fonts, set_key_image, update_touchscreen_ui
from podplayer.streamdeck_handlers import (
    on_key_change,
    on_dial_change,
    pending_volume,
    pending_scrub_position,
)


# Load configuration
config = get_config()

# ====== CONFIG (loaded from config.yaml) ======
SONOS_NAME = config.sonos_speaker_name

# Override speaker name if TESTING file exists
TESTING_FILE = os.path.join(config.script_dir, "TESTING")
TESTING_MODE = os.path.exists(TESTING_FILE)
if TESTING_MODE:
    SONOS_NAME = "Desk"
    log(f"[Config] TESTING file detected, overriding speaker_name to '{SONOS_NAME}'")

SCRIPT_DIR = config.script_dir
HTTP_PORT = config.http_port
BRIGHTNESS = config.streamdeck_brightness

# Button configuration
LOOP_BUTTONS = (
    config.loop_buttons
)  # Dict[int, Dict[str, str]] - button num -> {name, audio_file, icon}
PODCAST_BUTTONS = config.podcast_buttons  # Dict[int, str] - button num -> podcast slug
SPOTIFY_BUTTONS = (
    config.spotify_buttons
)  # Dict[int, Dict[str, str]] - button num -> {name, uri, icon}
PODCASTS = config.podcast_feeds  # Dict[str, Dict] - podcast slug -> {name, rss, icon}
# ====== END CONFIG ======

# Debounce delay (seconds) for dial actions; can be overridden in tests
DIAL_DEBOUNCE_SECONDS = 0.25

# Global state
httpd: Optional[Any] = None
deck: Optional[Any] = None
speaker: Optional[Any] = None

# Per-podcast episode index (newest-first list)
PODCAST_STATE: dict[str, int] = {}

# Track playback positions per episode (by URI)
EPISODE_POSITIONS: dict[str, int] = {}

# Track current StreamDeck brightness (0-100) - use list for mutable reference
current_brightness_ref: list[int] = [BRIGHTNESS]


def start_http_server() -> None:
    """Serve SCRIPT_DIR over HTTP for Sonos to pull music & podcasts."""
    global httpd

    directory = SCRIPT_DIR

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

        # Silence default logging
        def log_message(self, format, *args):
            return

        # Ignore broken pipes when Sonos drops the connection
        def copyfile(self, source, outputfile):
            try:
                super().copyfile(source, outputfile)
            except (BrokenPipeError, ConnectionResetError):
                pass

    httpd = http.server.ThreadingHTTPServer(("", HTTP_PORT), QuietHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    log(f"[HTTP] Serving {directory} on port {HTTP_PORT}")


def open_stream_deck() -> Any:
    """Initialize and configure the Stream Deck device."""
    devices = DeviceManager().enumerate()
    if not devices:
        log("[Deck] No Stream Deck found.")
        sys.exit(1)

    d = devices[0]
    d.open()
    d.reset()
    time.sleep(0.2)
    current_brightness_ref[0] = BRIGHTNESS
    d.set_brightness(BRIGHTNESS)

    # Create wrapper functions that capture dependencies
    def key_callback(deck_obj, key, state):
        from podplayer.sonos_control import toggle_loop
        from podplayer.podcast_manager import play_podcast_next
        from podplayer.persistence import save_current_position

        on_key_change(
            deck_obj,
            key,
            state,
            speaker,
            LOOP_BUTTONS,
            PODCAST_BUTTONS,
            SPOTIFY_BUTTONS,
            SCRIPT_DIR,
            HTTP_PORT,
            PODCAST_STATE,
            EPISODE_POSITIONS,
            toggle_loop,
            play_podcast_next,
            save_current_position,
            get_playback_info,
            make_update_ui_func(deck_obj),
        )

    def dial_callback(deck_obj, dial, event, value):
        from podplayer.persistence import save_current_position

        on_dial_change(
            deck_obj,
            dial,
            event,
            value,
            speaker,
            SCRIPT_DIR,
            HTTP_PORT,
            current_brightness_ref,
            PODCAST_STATE,
            EPISODE_POSITIONS,
            PODCASTS,
            DIAL_DEBOUNCE_SECONDS,
            TESTING_MODE,
            get_playback_info,
            save_current_position,
            detect_current_podcast,
            list_podcast_files,
            play_podcast_episode,
            make_update_ui_func(deck_obj),
        )

    # Hook callbacks
    d.set_key_callback(key_callback)
    d.set_dial_callback(dial_callback)

    # Set icons for all configured buttons
    # Loop buttons
    for button_num, loop_config in LOOP_BUTTONS.items():
        set_key_image(d, button_num, loop_config["icon"])

    # Podcast buttons
    for button_num, slug in PODCAST_BUTTONS.items():
        podcast_info = PODCASTS.get(slug)
        if podcast_info and "icon" in podcast_info:
            set_key_image(d, button_num, podcast_info["icon"])

    # Spotify buttons
    for button_num, spotify_config in SPOTIFY_BUTTONS.items():
        if "icon" in spotify_config:
            set_key_image(d, button_num, spotify_config["icon"])

    log(f"[Deck] connected with {d.key_count()} keys")
    return d


def make_update_ui_func(deck_obj: Any) -> Callable[[Any], None]:
    """Create a closure for update_touchscreen_ui with all dependencies."""

    def update_ui(ignored_deck: Any = None) -> None:
        # Import here to get the actual global state from handlers module
        from podplayer import streamdeck_handlers

        if speaker is not None:
            update_touchscreen_ui(
                deck_obj,
                speaker,
                PODCASTS,
                streamdeck_handlers.pending_volume,
                streamdeck_handlers.pending_scrub_position,
                lambda: get_playback_info(speaker),
                lambda: detect_current_podcast(PODCASTS),
                lambda uri: get_episode_metadata(SCRIPT_DIR, uri, TESTING_MODE),
                TESTING_MODE,
            )

    return update_ui


def signal_handler(sig: Optional[int], frame: Optional[Any]) -> None:
    """Handle shutdown signals gracefully."""
    print("\n[Main] Caught signal, shutting down...")
    global deck, httpd, speaker

    if deck:
        try:
            deck.reset()
            deck.close()
        except Exception:
            pass

    if httpd:
        try:
            httpd.shutdown()
            httpd.server_close()
        except Exception:
            pass

    if speaker:
        try:
            speaker.pause()
        except Exception:
            pass

    sys.exit(0)


def main() -> None:
    """Main entry point."""
    global deck, speaker

    # Trap Ctrl+C / SIGTERM
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize database and load saved positions
    init_database(SCRIPT_DIR)
    load_positions_from_db(SCRIPT_DIR, EPISODE_POSITIONS)

    # Load fonts once at startup
    load_fonts(SCRIPT_DIR)

    start_http_server()
    speaker = connect_sonos(SONOS_NAME)
    deck = open_stream_deck()

    log("[Main] Ready.")

    # Display configured buttons
    for button_num, loop_config in LOOP_BUTTONS.items():
        print(f"  Button {button_num} = {loop_config['name']} (loop)")

    for button_num, slug in PODCAST_BUTTONS.items():
        podcast_name = PODCASTS.get(slug, {}).get("name", slug)
        print(f"  Button {button_num} = {podcast_name}")

    for button_num, spotify_config in SPOTIFY_BUTTONS.items():
        print(f"  Button {button_num} = {spotify_config['name']} (spotify)")

    print(
        "  Dial 0 = volume, Dial 1 = playback scrub/pause, Dial 2 = episode navigation, Dial 3 = brightness"
    )

    update_ui = make_update_ui_func(deck)

    # Initial display update to show current state at startup
    try:
        update_ui(deck)
    except Exception as e:
        log(f"[Initial UI Error] {e}")

    try:
        last_update = time.time()
        while True:
            # Only update display periodically when something is PLAYING
            # (paused/stopped state is static until next button/knob interaction)
            if time.time() - last_update >= 0.25:
                try:
                    if speaker is not None:
                        # Check if we're playing - only update if so
                        playback = get_playback_info(speaker, force_refresh=True)
                        if playback["state"] == "PLAYING":
                            update_ui(deck)
                        # If paused/stopped, no need to update (position isn't changing)
                        # Button/knob handlers will trigger updates on interaction
                    last_update = time.time()
                except Exception as e:
                    log(f"[UI Update Error] {e}")

            time.sleep(0.1)  # Check more frequently for responsiveness
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()
