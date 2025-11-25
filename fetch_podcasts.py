#!/usr/bin/env python3
from __future__ import annotations

import os
import time
import pathlib
import re
import sqlite3
from typing import Any

import feedparser
import requests

from podplayer.config import get_config

# Load configuration
config = get_config()
PODCASTS = config.podcast_feeds
SCRIPT_DIR = config.script_dir
EPISODES_TO_DOWNLOAD = config.episodes_to_download
EPISODES_TO_KEEP = config.episodes_to_keep


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "episode"


def ensure_dir(path: str) -> None:
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def save_episode_metadata(file_path: str, title: str, description: str = "") -> None:
    """
    Save episode metadata to the database.
    Uses file path pattern instead of full URI to handle IP/port changes.
    """
    db_path = os.path.join(SCRIPT_DIR, "episode_positions.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Ensure episode_metadata table exists
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS episode_metadata (
                file_path TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        # Use relative path from SCRIPT_DIR for matching
        rel_path = os.path.relpath(file_path, SCRIPT_DIR)
        cursor.execute(
            """
            INSERT OR REPLACE INTO episode_metadata (file_path, title, description, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """,
            (rel_path, title, description),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Metadata Error] Failed to save metadata: {e}")


def download_episode(slug: str, entry: Any) -> None:
    audio_links = [
        l
        for l in entry.get("links", [])
        if l.get("rel") == "enclosure" and l.get("type", "").startswith("audio")
    ]
    if not audio_links:
        return

    url = audio_links[0]["href"]
    title = entry.get("title", "episode")
    # Get description from RSS feed (try summary, description, or content)
    description = (
        entry.get("summary", "")
        or entry.get("description", "")
        or entry.get("content", [{}])[0].get("value", "")
    )
    # Clean up HTML tags if present
    if description:
        import re

        description = re.sub(r"<[^>]+>", "", description)  # Remove HTML tags
        description = description.strip()
        # Debug: show first 100 chars of description
        print(f"  Description: {description[:100]}...")

    date_struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if date_struct:
        date_prefix = time.strftime("%Y-%m-%d", date_struct)
    else:
        date_prefix = time.strftime("%Y-%m-%d")

    feed_dir = os.path.join(SCRIPT_DIR, "podcasts", slug)
    ensure_dir(feed_dir)

    fname = f"{date_prefix}-{slugify(title)}.mp3"
    dest = os.path.join(feed_dir, fname)

    # Always update metadata from RSS feed, even if file already exists
    # This ensures we have the latest title and description
    save_episode_metadata(dest, title, description)

    if os.path.exists(dest):
        print(f"[{slug}] Already have {fname}, metadata updated from RSS feed")
        return

    print(f"[{slug}] Downloading {title} -> {fname}")
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):  # <-- note iter_content
            if chunk:
                f.write(chunk)


def cleanup_old_episodes(slug: str) -> None:
    """Remove episodes older than EPISODES_TO_KEEP limit."""
    feed_dir = os.path.join(SCRIPT_DIR, "podcasts", slug)
    if not os.path.isdir(feed_dir):
        return
    files = sorted(
        (os.path.join(feed_dir, f) for f in os.listdir(feed_dir) if f.endswith(".mp3")),
        key=os.path.getmtime,
        reverse=True,
    )
    for old in files[EPISODES_TO_KEEP:]:
        print(f"[{slug}] Removing old episode {os.path.basename(old)}")
        os.remove(old)


def main() -> None:
    ensure_dir(os.path.join(SCRIPT_DIR, "podcasts"))
    for slug, info in PODCASTS.items():
        rss = info["rss"]
        print(f"[{slug}] Fetching feed {rss}")
        feed = feedparser.parse(rss)
        print(f"[{slug}] Downloading up to {EPISODES_TO_DOWNLOAD} latest episodes")
        for entry in feed.entries[:EPISODES_TO_DOWNLOAD]:
            try:
                download_episode(slug, entry)
            except Exception as e:
                print(f"[{slug}] Error downloading episode: {e}")
        cleanup_old_episodes(slug)


if __name__ == "__main__":
    main()
