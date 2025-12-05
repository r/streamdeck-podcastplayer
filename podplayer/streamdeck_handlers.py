#!/usr/bin/env python3
"""
Stream Deck event handlers (buttons and dials).
"""
from __future__ import annotations

import os
import time
import threading
from typing import Any, Callable, Optional

from StreamDeck.Devices.StreamDeck import DialEventType

from podplayer.utils import log, get_ip
from podplayer.sonos_control import is_spotify_playing, skip_track


# Debounce timers for dial controls (to avoid rapid API calls)
volume_debounce_timer: Optional[threading.Timer] = None
scrub_debounce_timer: Optional[threading.Timer] = None
episode_debounce_timer: Optional[threading.Timer] = None
track_skip_debounce_timer: Optional[threading.Timer] = None
state_refresh_timer: Optional[threading.Timer] = None

# Pending values (for display updates before API calls)
pending_volume: Optional[int] = None
pending_scrub_position: Optional[int] = None
pending_episode_index: Optional[int] = None
pending_episode_slug: Optional[str] = None


def schedule_state_refresh(
    deck_obj: Any,
    speaker: Any,
    get_playback_info_func: Callable[..., dict[str, Any]],
    update_ui_func: Callable[[Any], None],
    delay: float = 0.3,
) -> None:
    """
    Schedule a delayed UI refresh to capture final state after Sonos processes a command.
    Used after play/pause/stop commands to ensure display shows correct final state.
    """
    global state_refresh_timer

    def refresh_state():
        try:
            # Force refresh to get latest state from Sonos
            get_playback_info_func(speaker, force_refresh=True)
            update_ui_func(deck_obj)
        except Exception as e:
            log(f"[State Refresh Error] {e}")

    # Cancel any existing refresh timer
    if state_refresh_timer:
        state_refresh_timer.cancel()

    # Schedule new refresh
    state_refresh_timer = threading.Timer(delay, refresh_state)
    state_refresh_timer.start()


def on_key_change(
    deck_obj: Any,
    key: int,
    state: bool,
    speaker: Any,
    loop_buttons: dict[int, dict[str, str]],
    podcast_buttons: dict[int, str],
    spotify_buttons: dict[int, dict[str, str]],
    script_dir: str,
    http_port: int,
    podcast_state: dict[str, int],
    episode_positions: dict[str, int],
    toggle_loop_func: Callable[[Any, str, str, int], None],
    play_podcast_next_func: Callable[..., None],
    save_position_func: Callable[[str, dict[str, int], dict[str, Any]], None],
    get_playback_info_func: Callable[..., dict[str, Any]],
    update_ui_func: Callable[[Any], None],
) -> None:
    """
    Callback when a Stream Deck key changes state.

    Args:
        loop_buttons: Dict mapping button number to loop config {name, audio_file, icon}
        podcast_buttons: Dict mapping button number to podcast slug
        spotify_buttons: Dict mapping button number to Spotify config {name, uri, icon}
    """
    if not state:
        return  # ignore key release

    log(f"Key {key} pressed")

    try:
        if key in loop_buttons:
            # Loop button: toggle audio loop
            loop_config = loop_buttons[key]
            log(f"[Deck] Loop button -> {loop_config['name']}")
            toggle_loop_func(speaker, script_dir, loop_config["audio_file"], http_port)
            # Update display immediately, then schedule delayed refresh for final state
            update_ui_func(deck_obj)
            schedule_state_refresh(deck_obj, speaker, get_playback_info_func, update_ui_func)

        elif key in podcast_buttons:
            # Podcast buttons: play next episode
            slug = podcast_buttons[key]
            log(f"[Deck] Podcast button -> {slug}")
            # Save current position before switching podcasts
            playback_info = get_playback_info_func(speaker)
            save_position_func(script_dir, episode_positions, playback_info)
            play_podcast_next_func(
                speaker,
                script_dir,
                http_port,
                slug,
                podcast_state,
                episode_positions,
                lambda: get_playback_info_func(speaker),
            )
            # Force refresh playback info after switching podcasts
            time.sleep(0.5)  # Wait for playback to start
            get_playback_info_func(speaker, force_refresh=True)
            update_ui_func(deck_obj)
            # Schedule one more refresh to ensure final state is captured
            schedule_state_refresh(deck_obj, speaker, get_playback_info_func, update_ui_func)

        elif key in spotify_buttons:
            # Spotify button: play Spotify URI (playlist, album, track)
            spotify_config = spotify_buttons[key]
            log(f"[Deck] Spotify button -> {spotify_config['name']}")
            try:
                # Save current position before switching
                playback_info = get_playback_info_func(speaker)
                save_position_func(script_dir, episode_positions, playback_info)

                # Use ShareLinkPlugin to play Spotify content (handles music service URIs)
                from soco.plugins.sharelink import ShareLinkPlugin

                share_link = ShareLinkPlugin(speaker)
                spotify_uri = spotify_config["uri"]

                # Clear the queue and add the Spotify content
                speaker.clear_queue()
                share_link.add_share_link_to_queue(spotify_uri)
                speaker.play_from_queue(0)

                # Wait for playback to start and refresh
                time.sleep(0.5)
                get_playback_info_func(speaker, force_refresh=True)
                update_ui_func(deck_obj)
                schedule_state_refresh(deck_obj, speaker, get_playback_info_func, update_ui_func)
            except Exception as e:
                log(f"[Spotify Error] {e} - Is Spotify linked in Sonos app?")

        else:
            # All other buttons: do nothing
            log(f"[Deck] No action mapped for key {key}")

    except Exception as e:
        log(f"[Key Error] {e}")


def apply_volume_change(
    deck_obj: Any, target_volume: int, speaker: Any, update_ui_func: Callable[[Any], None]
) -> None:
    """Apply volume change to Sonos (called after debounce)."""
    global pending_volume
    try:
        log(f"[Dial 0] volume {speaker.volume} → {target_volume}")
        speaker.volume = target_volume
        pending_volume = None  # Clear pending value
        update_ui_func(deck_obj)
    except Exception as e:
        log(f"[Volume Error] {e}")
        pending_volume = None


def apply_scrub_change(
    deck_obj: Any,
    target_position: int,
    speaker: Any,
    get_playback_info_func: Callable[..., dict[str, Any]],
    update_ui_func: Callable[[Any], None],
) -> None:
    """Apply scrub position change to Sonos (called after debounce)."""
    global pending_scrub_position

    try:
        # Convert to HH:MM:SS format for Sonos
        hours = target_position // 3600
        mins = (target_position % 3600) // 60
        secs = target_position % 60
        time_str = f"{hours:01d}:{mins:02d}:{secs:02d}"

        log(f"[Dial 1] Seeking to {time_str} ({target_position}s)")
        speaker.seek(time_str)

        # Wait briefly for Sonos to process the seek command
        # This ensures the speaker has updated its position before we refresh the cache
        time.sleep(0.15)

        # Force refresh the cache to get the updated position from Sonos
        get_playback_info_func(speaker, force_refresh=True)

    except Exception as e:
        log(f"[Scrub Error] {e}")
        # On error, try to refresh cache anyway to get actual position
        try:
            get_playback_info_func(speaker, force_refresh=True)
        except:
            pass
    finally:
        # Always clear pending and update display
        pending_scrub_position = None
        update_ui_func(deck_obj)


def apply_episode_change(
    deck_obj: Any,
    slug: str,
    episode_index: int,
    speaker: Any,
    script_dir: str,
    http_port: int,
    episode_positions: dict[str, int],
    play_episode_func: Callable[..., bool],
    get_playback_info_func: Callable[..., dict[str, Any]],
    update_ui_func: Callable[[Any], None],
) -> None:
    """Apply episode change (called after debounce)."""
    global pending_episode_index, pending_episode_slug
    try:
        play_episode_func(
            speaker,
            script_dir,
            http_port,
            slug,
            episode_index,
            episode_positions,
            lambda: get_playback_info_func(speaker),
            restore_pos=True,
        )
        pending_episode_index = None
        pending_episode_slug = None
        # Force refresh playback info after episode change
        time.sleep(0.3)  # Brief wait for playback to start
        get_playback_info_func(speaker, force_refresh=True)
        update_ui_func(deck_obj)
    except Exception as e:
        log(f"[Episode Error] {e}")
        pending_episode_index = None
        pending_episode_slug = None


def apply_track_skip(
    deck_obj: Any,
    direction: int,
    speaker: Any,
    get_playback_info_func: Callable[..., dict[str, Any]],
    update_ui_func: Callable[[Any], None],
) -> None:
    """Apply track skip for Spotify/queue playback (called after debounce)."""
    try:
        skip_track(speaker, direction)
        # Wait for Sonos to update and refresh display
        time.sleep(0.3)
        get_playback_info_func(speaker, force_refresh=True)
        update_ui_func(deck_obj)
    except Exception as e:
        log(f"[Track Skip Error] {e}")


def on_dial_change(
    deck_obj: Any,
    dial: int,
    event: Any,
    value: int,
    speaker: Any,
    script_dir: str,
    http_port: int,
    current_brightness_ref: list[int],
    podcast_state: dict[str, int],
    episode_positions: dict[str, int],
    podcasts: dict[str, Any],
    dial_debounce_seconds: float,
    testing_mode: bool,
    get_playback_info_func: Callable[..., dict[str, Any]],
    save_position_func: Callable[[str, dict[str, int], dict[str, Any]], None],
    detect_podcast_func: Callable[[dict[str, Any]], Optional[str]],
    list_podcast_files_func: Callable[[str, str], list[str]],
    play_episode_func: Callable[..., bool],
    update_ui_func: Callable[[Any], None],
) -> None:
    """Callback when a Stream Deck dial changes (turn or push)."""
    global volume_debounce_timer, scrub_debounce_timer, episode_debounce_timer
    global pending_volume, pending_scrub_position, pending_episode_index, pending_episode_slug

    if testing_mode:
        log(f"Dial {dial} {event} value={value}")

    try:
        # Dial 0: Volume control
        if dial == 0:
            if event == DialEventType.TURN:
                delta = int(value)
                if delta == 0:
                    return

                # Cancel existing debounce timer
                if volume_debounce_timer:
                    volume_debounce_timer.cancel()

                # Calculate new volume
                current_vol = pending_volume if pending_volume is not None else speaker.volume
                new_vol = max(0, min(100, current_vol + delta))

                # Set pending value and update display immediately (using cached data)
                pending_volume = new_vol
                update_ui_func(deck_obj)  # Fast - uses cached playback info

                # Schedule actual API call after debounce delay (or immediately if disabled)
                delay = dial_debounce_seconds
                if delay <= 0:
                    apply_volume_change(deck_obj, new_vol, speaker, update_ui_func)
                else:
                    volume_debounce_timer = threading.Timer(
                        delay,
                        apply_volume_change,
                        args=(deck_obj, new_vol, speaker, update_ui_func),
                    )
                    volume_debounce_timer.start()

            # Dial 0 push: no action (loop buttons are on the button keys)

        # Dial 1: Playback scrubbing (seek) and pause/play
        elif dial == 1:
            if event == DialEventType.TURN:
                delta = int(value)
                if delta == 0:
                    return

                # Cancel existing debounce timer
                if scrub_debounce_timer:
                    scrub_debounce_timer.cancel()

                # Get current position (use pending if available)
                playback = get_playback_info_func(speaker)
                current_pos = (
                    pending_scrub_position
                    if pending_scrub_position is not None
                    else playback["position"]
                )
                duration = playback["duration"]

                if duration > 0:
                    # Scrub by 5 seconds per turn increment
                    seek_delta = delta * 5
                    new_position = max(0, min(duration, current_pos + seek_delta))

                    # Set pending value and update display immediately (using cached data)
                    pending_scrub_position = new_position
                    update_ui_func(deck_obj)  # Fast - uses cached playback info

                    # Schedule actual API call after debounce delay (or immediately if disabled)
                    delay = dial_debounce_seconds
                    if delay <= 0:
                        apply_scrub_change(
                            deck_obj, new_position, speaker, get_playback_info_func, update_ui_func
                        )
                    else:
                        scrub_debounce_timer = threading.Timer(
                            delay,
                            apply_scrub_change,
                            args=(
                                deck_obj,
                                new_position,
                                speaker,
                                get_playback_info_func,
                                update_ui_func,
                            ),
                        )
                        scrub_debounce_timer.start()

            elif event == DialEventType.PUSH:
                if value:
                    # Toggle play/pause
                    transport_info = speaker.get_current_transport_info()
                    state = transport_info.get("current_transport_state", "STOPPED")

                    if state == "PLAYING":
                        log("[Dial 1] Push: Pause")
                        playback_info = get_playback_info_func(speaker)
                        save_position_func(script_dir, episode_positions, playback_info)
                        speaker.pause()
                    else:
                        log("[Dial 1] Push: Play")
                        speaker.play()
                        # Note: Sonos maintains position on pause/play, so no restore needed

                    # Update display immediately, then schedule delayed refresh for final state
                    update_ui_func(deck_obj)
                    schedule_state_refresh(
                        deck_obj, speaker, get_playback_info_func, update_ui_func
                    )

        # Dial 2: Track/Episode navigation (forward/backward)
        # For Spotify/queue: skip tracks
        # For podcasts: navigate episodes
        elif dial == 2:
            if event == DialEventType.TURN:
                delta = int(value)
                if delta == 0:
                    return

                # Check if Spotify is playing - use track skip instead of episode navigation
                if is_spotify_playing():
                    global track_skip_debounce_timer

                    # Cancel existing debounce timer
                    if track_skip_debounce_timer:
                        track_skip_debounce_timer.cancel()

                    # Determine skip direction (positive = next, negative = previous)
                    direction = 1 if delta > 0 else -1
                    log(f"[Dial 2] Spotify: {'next' if direction > 0 else 'previous'} track")

                    # Schedule track skip after debounce delay (or immediately if disabled)
                    delay = dial_debounce_seconds
                    if delay <= 0:
                        apply_track_skip(
                            deck_obj,
                            direction,
                            speaker,
                            get_playback_info_func,
                            update_ui_func,
                        )
                    else:
                        track_skip_debounce_timer = threading.Timer(
                            delay,
                            apply_track_skip,
                            args=(
                                deck_obj,
                                direction,
                                speaker,
                                get_playback_info_func,
                                update_ui_func,
                            ),
                        )
                        track_skip_debounce_timer.start()
                    return

                # Cancel existing debounce timer for episode navigation
                if episode_debounce_timer:
                    episode_debounce_timer.cancel()

                # Detect current podcast
                current_slug = detect_podcast_func(podcasts)
                if not current_slug:
                    log("[Dial 2] No podcast or Spotify currently playing")
                    return

                # Get current episode index
                files = list_podcast_files_func(script_dir, current_slug)
                if not files:
                    log(f"[Dial 2] No episodes found for '{current_slug}'")
                    return

                # Find current episode index
                # Use pending value if available, otherwise try to detect from URI
                current_idx = None

                if pending_episode_index is not None and pending_episode_slug == current_slug:
                    # Use pending index if we're already navigating
                    current_idx = pending_episode_index
                else:
                    # Try to detect from current playback (but don't block on slow network call)
                    try:
                        playback = get_playback_info_func(speaker)
                        current_uri = playback.get("uri", "")
                        if current_uri:
                            ip = get_ip()
                            for i, episode_file in enumerate(files):
                                rel = os.path.relpath(episode_file, script_dir)
                                episode_url = f"http://{ip}:{http_port}/{rel}"
                                if episode_url == current_uri:
                                    current_idx = i
                                    break
                    except:
                        pass  # If network call fails, fall back to podcast_state

                if current_idx is None:
                    # Fallback to podcast_state
                    current_idx = podcast_state.get(current_slug, 0) - 1
                    if current_idx < 0:
                        current_idx = 0

                # Navigate to next/previous episode
                new_idx = current_idx + delta

                # Wrap around
                if new_idx < 0:
                    new_idx = len(files) - 1
                elif new_idx >= len(files):
                    new_idx = 0

                # Set pending values and update display immediately (using cached data)
                pending_episode_index = new_idx
                pending_episode_slug = current_slug
                update_ui_func(deck_obj)  # Fast - uses cached playback info

                # Schedule actual API call after debounce delay (or immediately if disabled)
                delay = dial_debounce_seconds
                if delay <= 0:
                    apply_episode_change(
                        deck_obj,
                        current_slug,
                        new_idx,
                        speaker,
                        script_dir,
                        http_port,
                        episode_positions,
                        play_episode_func,
                        get_playback_info_func,
                        update_ui_func,
                    )
                else:
                    episode_debounce_timer = threading.Timer(
                        delay,
                        apply_episode_change,
                        args=(
                            deck_obj,
                            current_slug,
                            new_idx,
                            speaker,
                            script_dir,
                            http_port,
                            episode_positions,
                            play_episode_func,
                            get_playback_info_func,
                            update_ui_func,
                        ),
                    )
                    episode_debounce_timer.start()

        # Dial 3: Brightness control
        elif dial == 3:
            if event == DialEventType.TURN:
                delta = int(value)
                if delta == 0:
                    return

                current_brightness = current_brightness_ref[0]
                # Adjust brightness in increments of 5 (0-100 range)
                brightness_delta = delta * 5
                new_brightness = max(0, min(100, current_brightness + brightness_delta))

                log(f"[Dial 3] brightness {current_brightness} → {new_brightness}")
                deck_obj.set_brightness(new_brightness)
                current_brightness_ref[0] = new_brightness

    except Exception as e:
        log(f"[Dial Error] {e}")
