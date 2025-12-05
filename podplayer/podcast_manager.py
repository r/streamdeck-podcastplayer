#!/usr/bin/env python3
"""
Podcast management functions.
"""
from __future__ import annotations

import os
import time
import sqlite3
from typing import Any, Callable

from podplayer.utils import log, get_ip
from podplayer.persistence import save_current_position, restore_position, get_db_path


def list_podcast_files(script_dir: str, slug: str) -> list[str]:
    """
    Return newest-first list of episode files for a given slug.
    Orders by publication_datetime from database (for episodes published on same day),
    falling back to publication_date, then filename, then file time.
    """
    feed_dir = os.path.join(script_dir, "podcasts", slug)
    if not os.path.isdir(feed_dir):
        return []

    files = [os.path.join(feed_dir, f) for f in os.listdir(feed_dir) if f.lower().endswith(".mp3")]

    # Get publication datetimes from database
    file_datetimes: dict[str, str] = {}
    try:
        db_path = get_db_path(script_dir)
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            for file_path in files:
                rel_path = os.path.relpath(file_path, script_dir)
                # Try to get full datetime first, fall back to date
                cursor.execute(
                    "SELECT publication_datetime, publication_date FROM episode_metadata WHERE file_path = ?",
                    (rel_path,),
                )
                result = cursor.fetchone()
                if result:
                    # Prefer publication_datetime (includes time), fall back to publication_date
                    if result[0]:  # publication_datetime
                        file_datetimes[file_path] = result[0]
                    elif result[1]:  # publication_date
                        file_datetimes[file_path] = result[1]
                    else:
                        # Extract date from filename
                        basename = os.path.basename(file_path)
                        if len(basename) >= 10 and basename[:10].replace("-", "").isdigit():
                            file_datetimes[file_path] = basename[:10]
                        else:
                            # Use file modification time
                            file_datetimes[file_path] = time.strftime(
                                "%Y-%m-%dT%H:%M:%S", time.localtime(os.path.getmtime(file_path))
                            )
                else:
                    # No database entry, extract from filename or use file time
                    basename = os.path.basename(file_path)
                    if len(basename) >= 10 and basename[:10].replace("-", "").isdigit():
                        file_datetimes[file_path] = basename[:10]
                    else:
                        file_datetimes[file_path] = time.strftime(
                            "%Y-%m-%dT%H:%M:%S", time.localtime(os.path.getmtime(file_path))
                        )

            conn.close()
    except Exception as e:
        log(f"[Podcast] Error reading publication datetimes: {e}, falling back to file time")
        # Fallback to modification time
        files.sort(key=os.path.getmtime, reverse=True)
        return files

    # Sort by publication datetime (newest first)
    # ISO 8601 format sorts correctly as strings
    files.sort(key=lambda f: file_datetimes.get(f, ""), reverse=True)
    return files


def play_podcast_episode(
    speaker: Any,
    script_dir: str,
    http_port: int,
    slug: str,
    episode_index: int,
    episode_positions: dict[str, int],
    playback_info_getter: Callable[[], dict[str, Any]],
    restore_pos: bool = True,
) -> bool:
    """
    Play a specific episode of a podcast by index.
    If restore_pos is True, restores saved position for that episode.

    Args:
        playback_info_getter: Function to get current playback info for position saving
    """
    files = list_podcast_files(script_dir, slug)
    if not files:
        log(f"[Podcast] No local episodes found for '{slug}'")
        return False

    if episode_index < 0:
        episode_index = len(files) - 1
    elif episode_index >= len(files):
        episode_index = 0

    episode = files[episode_index]

    ip = get_ip()
    rel = os.path.relpath(episode, script_dir)
    url = f"http://{ip}:{http_port}/{rel}"
    log(f"[Podcast] Playing {slug} idx={episode_index}/{len(files)}: {url}")

    try:
        # Save current position before switching
        playback_info = playback_info_getter()
        save_current_position(script_dir, episode_positions, playback_info)

        speaker.repeat = False
        speaker.play_uri(url)
        speaker.play()

        # Restore position if requested and available
        if restore_pos:
            # Small delay to ensure playback has started
            time.sleep(0.5)
            restore_position(script_dir, episode_positions, speaker, url)

        return True
    except Exception as e:
        log(f"[Podcast Error] {e}")
        return False


def play_podcast_next(
    speaker: Any,
    script_dir: str,
    http_port: int,
    slug: str,
    podcast_state: dict[str, int],
    episode_positions: dict[str, int],
    playback_info_getter: Callable[[], dict[str, Any]],
) -> None:
    """
    Play the next episode for the given podcast slug.
    Keeps a per-podcast index in podcast_state, wraps when it hits the end.
    """
    files = list_podcast_files(script_dir, slug)
    if not files:
        log(f"[Podcast] No local episodes found for '{slug}'")
        return

    idx = podcast_state.get(slug, 0)
    if idx >= len(files):
        idx = 0

    play_podcast_episode(
        speaker,
        script_dir,
        http_port,
        slug,
        idx,
        episode_positions,
        playback_info_getter,
        restore_pos=True,
    )

    podcast_state[slug] = idx + 1  # advance for next
