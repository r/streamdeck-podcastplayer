#!/usr/bin/env python3
"""
Database persistence for episode positions and metadata.
"""
from __future__ import annotations

import os
import sqlite3
from typing import Any

from podplayer.utils import log


# Global state (imported from main module)
EPISODE_POSITIONS: dict[str, int] = {}


def get_db_path(script_dir: str) -> str:
    """Get the path to the SQLite database file."""
    return os.path.join(script_dir, "episode_positions.db")


def init_database(script_dir: str) -> None:
    """Initialize the SQLite database for episode positions and metadata."""
    db_path = get_db_path(script_dir)
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS episode_positions (
                uri TEXT PRIMARY KEY,
                position INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS episode_metadata (
                file_path TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                publication_date TEXT,
                publication_datetime TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        # Add publication columns if they don't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE episode_metadata ADD COLUMN publication_date TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        try:
            cursor.execute("ALTER TABLE episode_metadata ADD COLUMN publication_datetime TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        conn.commit()
        conn.close()
        log(f"Database initialized at {db_path}")
    except Exception as e:
        log(f"[Database Error] Failed to initialize database: {e}")


def load_positions_from_db(script_dir: str, episode_positions: dict[str, int]) -> None:
    """Load all episode positions from the database into memory."""
    db_path = get_db_path(script_dir)
    if not os.path.exists(db_path):
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT uri, position FROM episode_positions")
        rows = cursor.fetchall()

        for uri, position in rows:
            if position > 0:
                episode_positions[uri] = position

        conn.close()
        log(f"Database loaded {len(episode_positions)} episode positions")
    except Exception as e:
        log(f"[Database Error] Failed to load positions: {e}")


def save_position_to_db(script_dir: str, uri: str, position: int) -> None:
    """Save an episode position to the database."""
    if not uri or position <= 0:
        return

    db_path = get_db_path(script_dir)
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO episode_positions (uri, position, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """,
            (uri, position),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"[Database Error] Failed to save position to database: {e}")


def get_episode_metadata(script_dir: str, uri: str, testing_mode: bool = False) -> dict[str, str]:
    """Get episode metadata (title, description) from the database."""
    if not uri:
        return {}

    db_path = get_db_path(script_dir)
    if not os.path.exists(db_path):
        return {}

    try:
        # Extract the relative file path from URI
        if "/podcasts/" in uri:
            parts = uri.split("/podcasts/")
            if len(parts) > 1:
                file_path = "podcasts/" + parts[1]
            else:
                return {}
        else:
            return {}

        if testing_mode:
            log(f"  Looking for metadata: {file_path}")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT title, description FROM episode_metadata WHERE file_path = ?", (file_path,)
        )
        row = cursor.fetchone()

        if testing_mode:
            if row:
                log(f"  Found metadata: title={row[0][:50]}, desc={len(row[1] or '')} chars")
            else:
                log(f"  No metadata found for: {file_path}")
                # Show what's in the DB
                cursor.execute(
                    "SELECT file_path FROM episode_metadata WHERE file_path LIKE ?",
                    (f'%{parts[1].split("/")[0]}%',),
                )
                sample = cursor.fetchall()
                log(f"  Sample paths in DB for this podcast: {sample[:3]}")

        conn.close()

        if row:
            return {"title": row[0], "description": row[1] or ""}
    except Exception as e:
        if testing_mode:
            log(f"  Metadata error: {e}")
        pass

    return {}


def save_current_position(
    script_dir: str, episode_positions: dict[str, int], playback_info: dict[str, Any]
) -> None:
    """Save the current playback position for the currently playing episode."""
    try:
        uri = playback_info.get("uri", "")
        position = playback_info.get("position", 0)

        if uri and position > 0:
            episode_positions[uri] = position
            save_position_to_db(script_dir, uri, position)
            log(f"[Position] Saved position {position}s for episode")
    except Exception as e:
        log(f"[Position Error] Failed to save position: {e}")


def restore_position(
    script_dir: str, episode_positions: dict[str, int], speaker: Any, uri: str
) -> None:
    """Restore saved playback position for an episode, if available."""
    if not uri:
        return

    # Check memory first, then database
    saved_position = episode_positions.get(uri)

    # If not in memory, try loading from database
    if not saved_position or saved_position <= 0:
        db_path = get_db_path(script_dir)
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT position FROM episode_positions WHERE uri = ?", (uri,))
                row = cursor.fetchone()
                conn.close()

                if row:
                    saved_position = row[0]
                    episode_positions[uri] = saved_position  # Cache in memory
            except Exception as e:
                log(f"[Database Error] Failed to load position from database: {e}")

    if saved_position and saved_position > 0:
        try:
            # Convert to HH:MM:SS format for Sonos
            hours = saved_position // 3600
            mins = (saved_position % 3600) // 60
            secs = saved_position % 60
            time_str = f"{hours:01d}:{mins:02d}:{secs:02d}"

            log(f"[Position] Restoring position {time_str} ({saved_position}s) for episode")
            speaker.seek(time_str)
        except Exception as e:
            log(f"[Position Error] Failed to restore position: {e}")
