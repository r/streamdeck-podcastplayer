#!/usr/bin/env python3
"""
Sonos speaker control functions.
"""
from __future__ import annotations

import os
import sys
import time
from typing import Any

import soco

from podplayer.utils import log, get_ip


# Cached playback info (to avoid frequent network calls)
cached_playback_info: dict[str, Any] = {
    "position": 0,
    "duration": 0,
    "state": "STOPPED",
    "title": "No track",
    "artist": "",
    "album": "",
    "uri": "",
}
last_playback_fetch: float = 0


def connect_sonos(sonos_name: str) -> Any:
    """Connect to the Sonos speaker by name."""
    log("[Sonos] discovering…")
    log(f"[Sonos] Looking for speaker: '{sonos_name}'")

    # Try by_name first (most direct)
    spk = soco.discovery.by_name(sonos_name)

    # If that fails, try discovering all speakers and matching manually
    # This helps with special characters like apostrophes
    if not spk:
        log("[Sonos] Direct lookup failed, trying discovery...")
        speakers = soco.discover()
        if speakers:
            log(f"[Sonos] Found {len(speakers)} speaker(s):")
            for s in speakers:
                log(f"  - '{s.player_name}'")
                # Case-insensitive match
                if s.player_name.lower() == sonos_name.lower():
                    spk = s
                    break

    if not spk:
        log(f"[Sonos] Could not find speaker named '{sonos_name}'")
        log("[Sonos] Available speakers:")
        try:
            speakers = soco.discover()
            for s in speakers:
                log(f"  - '{s.player_name}'")
        except:
            log("  (Could not discover speakers)")
        sys.exit(1)

    log(f"[Sonos] Connected to {spk.player_name} @ {spk.ip_address}")
    return spk


def toggle_loop(speaker: Any, script_dir: str, mp3_path: str, http_port: int) -> None:
    """Toggle the MP3 loop on/off on the target Sonos."""
    ip = get_ip()
    rel = os.path.relpath(mp3_path, script_dir)
    mp3_url = f"http://{ip}:{http_port}/{rel}"

    try:
        info = speaker.get_current_transport_info()
        state = info.get("current_transport_state")
        track = speaker.get_current_track_info()
        current_uri = track.get("uri", "")

        log(f"[Loop] Current state={state}, uri={current_uri}")
        log(f"[Loop] Target loop URL={mp3_url}")

        if state == "PLAYING" and current_uri == mp3_url:
            log("[Loop] Toggle → PAUSE")
            speaker.pause()
        else:
            log(f"[Loop] Toggle → PLAY {mp3_url}")
            speaker.play_uri(mp3_url)
            speaker.repeat = True
            speaker.play()
    except Exception as e:
        log(f"[Toggle Error] {e}")


def get_playback_info(speaker: Any, force_refresh: bool = False) -> dict[str, Any]:
    """
    Get current playback information from Sonos.
    Uses cached info unless force_refresh=True or cache is stale (>1 second).

    Returns:
        dict with 'position', 'duration', 'state', 'title', 'uri' keys
    """
    global cached_playback_info, last_playback_fetch

    current_time = time.time()

    # Use cache if it's recent (within 1 second) and not forcing refresh
    if not force_refresh and (current_time - last_playback_fetch) < 1.0:
        return cached_playback_info

    try:
        track_info = speaker.get_current_track_info()
        position_str = track_info.get("position", "0:00:00")
        duration_str = track_info.get("duration", "0:00:00")
        title = track_info.get("title", "No track")
        artist = track_info.get("artist", "")
        album = track_info.get("album", "")
        uri = track_info.get("uri", "")

        # Convert HH:MM:SS to seconds
        def parse_time(time_str):
            parts = time_str.split(":")
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            return 0

        position = parse_time(position_str)
        duration = parse_time(duration_str)

        transport_info = speaker.get_current_transport_info()
        state = transport_info.get("current_transport_state", "STOPPED")

        cached_playback_info = {
            "position": position,
            "duration": duration,
            "state": state,
            "title": title,
            "artist": artist,
            "album": album,
            "uri": uri,
        }
        last_playback_fetch = current_time

        return cached_playback_info
    except Exception as e:
        # Return cached info on error
        return cached_playback_info


def detect_current_podcast(podcasts: dict[str, Any]) -> str | None:
    """
    Detect which podcast is currently playing based on the URI.
    Returns the podcast slug if detected, None otherwise.
    Uses cached playback info to avoid network calls.
    """
    global cached_playback_info

    try:
        # Use cached URI instead of making network call
        uri = cached_playback_info.get("uri", "")

        if not uri:
            return None

        # Check if URI matches podcast pattern: http://ip:port/podcasts/slug/filename.mp3
        if "/podcasts/" in uri:
            # Extract slug from URI
            parts = uri.split("/podcasts/")
            if len(parts) > 1:
                slug_part: str = parts[1].split("/")[0]
                # Check if this slug exists in our podcast config
                if slug_part in podcasts:
                    return slug_part

        return None
    except Exception as e:
        return None


def is_spotify_playing() -> bool:
    """
    Check if Spotify content is currently playing.
    Returns True if the current URI indicates Spotify playback.
    Uses cached playback info to avoid network calls.
    """
    global cached_playback_info

    try:
        uri = cached_playback_info.get("uri", "")
        if not uri:
            return False

        # Spotify URIs contain 'spotify' or 'x-sonos-spotify'
        # Examples:
        #   x-sonos-spotify:spotify:track:xxx
        #   x-rincon-cpcontainer:1006206cspotify:playlist:xxx
        return "spotify" in uri.lower()
    except Exception:
        return False


def skip_track(speaker: Any, direction: int) -> bool:
    """
    Skip to next or previous track.

    Args:
        speaker: Sonos speaker object
        direction: positive for next track, negative for previous track

    Returns:
        True if skip was successful, False otherwise
    """
    try:
        if direction > 0:
            speaker.next()
            log("[Sonos] Skipped to next track")
        else:
            speaker.previous()
            log("[Sonos] Skipped to previous track")
        return True
    except Exception as e:
        log(f"[Skip Error] {e}")
        return False
