#!/usr/bin/env python3
"""
Unit tests for fetch_podcasts.py

Tests cover podcast feed parsing and downloading with mocked network requests.
"""
import os
import sys
import time
import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
import requests

# Hardware mocking is done in conftest.py before any imports

import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fetch_podcasts import (
    slugify,
    ensure_dir,
    download_episode,
    cleanup_old_episodes,
)


# ====== Fixtures ======


@pytest.fixture
def temp_podcast_dir(tmp_path):
    """Create temporary podcast directory."""
    podcast_dir = tmp_path / "podcasts"
    podcast_dir.mkdir()
    return podcast_dir


@pytest.fixture
def mock_rss_entry():
    """Create a mock RSS feed entry."""
    return {
        "title": "Test Episode: How Money Works!",
        "links": [
            {"rel": "enclosure", "type": "audio/mpeg", "href": "https://example.com/episode.mp3"}
        ],
        "published_parsed": time.strptime("2024-01-15", "%Y-%m-%d"),
    }


@pytest.fixture
def mock_rss_entry_no_date():
    """Create a mock RSS feed entry without a date."""
    return {
        "title": "Episode Without Date",
        "links": [
            {"rel": "enclosure", "type": "audio/mpeg", "href": "https://example.com/episode2.mp3"}
        ],
    }


# ====== Tests: Utility Functions ======


def test_slugify_basic():
    """Test slugify converts text to lowercase with hyphens."""
    assert slugify("Hello World") == "hello-world"
    assert slugify("Test Episode") == "test-episode"


def test_slugify_removes_special_characters():
    """Test slugify removes special characters."""
    assert slugify("Episode #1: The Beginning!") == "episode-1-the-beginning"
    assert slugify("100% Amazing") == "100-amazing"


def test_slugify_handles_multiple_spaces():
    """Test slugify converts multiple spaces to single hyphen."""
    assert slugify("lots   of    spaces") == "lots-of-spaces"


def test_slugify_strips_leading_trailing_hyphens():
    """Test slugify removes leading/trailing hyphens."""
    assert slugify("!!! Amazing !!!") == "amazing"
    assert slugify("---test---") == "test"


def test_slugify_handles_empty_string():
    """Test slugify returns 'episode' for empty input."""
    assert slugify("") == "episode"
    assert slugify("!!!") == "episode"


def test_slugify_handles_unicode():
    """Test slugify handles unicode characters."""
    assert slugify("Café") == "caf"
    assert slugify("naïve") == "na-ve"


def test_ensure_dir_creates_directory(tmp_path):
    """Test ensure_dir creates directory if it doesn't exist."""
    test_dir = tmp_path / "new" / "nested" / "dir"

    ensure_dir(str(test_dir))

    assert test_dir.exists()
    assert test_dir.is_dir()


def test_ensure_dir_handles_existing_directory(tmp_path):
    """Test ensure_dir doesn't fail if directory exists."""
    test_dir = tmp_path / "existing"
    test_dir.mkdir()

    # Should not raise
    ensure_dir(str(test_dir))
    assert test_dir.exists()


# ====== Tests: Download Episode ======


def test_download_episode_success(mock_rss_entry, temp_podcast_dir, requests_mock):
    """Test download_episode successfully downloads file."""
    # Mock the HTTP response
    requests_mock.get(
        "https://example.com/episode.mp3",
        content=b"fake mp3 data",
    )

    with patch("fetch_podcasts.SCRIPT_DIR", str(temp_podcast_dir.parent)):
        download_episode("test-podcast", mock_rss_entry)

    # Check file was created
    expected_file = (
        temp_podcast_dir / "test-podcast" / "2024-01-15-test-episode-how-money-works.mp3"
    )
    assert expected_file.exists()
    assert expected_file.read_bytes() == b"fake mp3 data"


def test_download_episode_with_no_date(mock_rss_entry_no_date, temp_podcast_dir, requests_mock):
    """Test download_episode uses current date when no date in entry."""
    requests_mock.get(
        "https://example.com/episode2.mp3",
        content=b"fake mp3 data",
    )

    with patch("fetch_podcasts.SCRIPT_DIR", str(temp_podcast_dir.parent)):
        download_episode("test-podcast", mock_rss_entry_no_date)

    # Should use today's date
    today = time.strftime("%Y-%m-%d")
    expected_file = temp_podcast_dir / "test-podcast" / f"{today}-episode-without-date.mp3"
    assert expected_file.exists()


def test_download_episode_skips_existing_file(mock_rss_entry, temp_podcast_dir, requests_mock):
    """Test download_episode skips downloading if file exists."""
    # Create the file first
    podcast_slug_dir = temp_podcast_dir / "test-podcast"
    podcast_slug_dir.mkdir()
    existing_file = podcast_slug_dir / "2024-01-15-test-episode-how-money-works.mp3"
    existing_file.write_text("existing content")

    # Mock should not be called
    requests_mock.get(
        "https://example.com/episode.mp3",
        content=b"new mp3 data",
    )

    with patch("fetch_podcasts.SCRIPT_DIR", str(temp_podcast_dir.parent)):
        download_episode("test-podcast", mock_rss_entry)

    # File should still have old content
    assert existing_file.read_text() == "existing content"


def test_download_episode_no_audio_links(temp_podcast_dir):
    """Test download_episode skips entries without audio links."""
    entry = {
        "title": "Text Only Episode",
        "links": [{"rel": "alternate", "type": "text/html", "href": "https://example.com/page"}],
    }

    with patch("fetch_podcasts.SCRIPT_DIR", str(temp_podcast_dir.parent)):
        download_episode("test-podcast", entry)

    # No file should be created
    podcast_dir = temp_podcast_dir / "test-podcast"
    assert not podcast_dir.exists() or len(list(podcast_dir.glob("*.mp3"))) == 0


def test_download_episode_handles_network_error(mock_rss_entry, temp_podcast_dir, requests_mock):
    """Test download_episode propagates network errors."""
    requests_mock.get(
        "https://example.com/episode.mp3",
        status_code=404,
    )

    with patch("fetch_podcasts.SCRIPT_DIR", str(temp_podcast_dir.parent)):
        with pytest.raises(requests.exceptions.HTTPError):
            download_episode("test-podcast", mock_rss_entry)


def test_download_episode_creates_directory(mock_rss_entry, temp_podcast_dir, requests_mock):
    """Test download_episode creates podcast directory if needed."""
    requests_mock.get(
        "https://example.com/episode.mp3",
        content=b"fake mp3 data",
    )

    # Don't create directory beforehand
    with patch("fetch_podcasts.SCRIPT_DIR", str(temp_podcast_dir.parent)):
        download_episode("new-podcast", mock_rss_entry)

    # Directory should be created
    new_dir = temp_podcast_dir / "new-podcast"
    assert new_dir.exists()
    assert new_dir.is_dir()


def test_download_episode_uses_updated_parsed_date(temp_podcast_dir, requests_mock):
    """Test download_episode falls back to updated_parsed if no published_parsed."""
    entry = {
        "title": "Updated Episode",
        "links": [
            {"rel": "enclosure", "type": "audio/mpeg", "href": "https://example.com/episode3.mp3"}
        ],
        "updated_parsed": time.strptime("2024-02-20", "%Y-%m-%d"),
    }

    requests_mock.get(
        "https://example.com/episode3.mp3",
        content=b"fake mp3 data",
    )

    with patch("fetch_podcasts.SCRIPT_DIR", str(temp_podcast_dir.parent)):
        download_episode("test-podcast", entry)

    expected_file = temp_podcast_dir / "test-podcast" / "2024-02-20-updated-episode.mp3"
    assert expected_file.exists()


# ====== Tests: Cleanup Old Episodes ======


def test_cleanup_old_episodes_removes_excess(temp_podcast_dir):
    """Test cleanup_old_episodes removes old episodes beyond limit."""
    slug_dir = temp_podcast_dir / "test-podcast"
    slug_dir.mkdir()

    # Create 7 episodes with different modification times
    for i in range(7):
        episode = slug_dir / f"episode-{i}.mp3"
        episode.write_text(f"content {i}")
        # Set modification times (older = lower number)
        os.utime(episode, (1000 + i, 1000 + i))

    with (
        patch("fetch_podcasts.SCRIPT_DIR", str(temp_podcast_dir.parent)),
        patch("fetch_podcasts.EPISODES_TO_KEEP", 5),
    ):

        cleanup_old_episodes("test-podcast")

    # Should keep only 5 newest episodes
    remaining = list(slug_dir.glob("*.mp3"))
    assert len(remaining) == 5

    # Oldest 2 should be removed (episode-0 and episode-1)
    assert not (slug_dir / "episode-0.mp3").exists()
    assert not (slug_dir / "episode-1.mp3").exists()

    # Newest 5 should remain
    assert (slug_dir / "episode-6.mp3").exists()
    assert (slug_dir / "episode-5.mp3").exists()
    assert (slug_dir / "episode-4.mp3").exists()


def test_cleanup_old_episodes_keeps_all_if_under_limit(temp_podcast_dir):
    """Test cleanup_old_episodes keeps all episodes if under limit."""
    slug_dir = temp_podcast_dir / "test-podcast"
    slug_dir.mkdir()

    # Create only 3 episodes
    for i in range(3):
        episode = slug_dir / f"episode-{i}.mp3"
        episode.write_text(f"content {i}")

    with (
        patch("fetch_podcasts.SCRIPT_DIR", str(temp_podcast_dir.parent)),
        patch("fetch_podcasts.EPISODES_TO_KEEP", 5),
    ):

        cleanup_old_episodes("test-podcast")

    # All 3 should remain
    remaining = list(slug_dir.glob("*.mp3"))
    assert len(remaining) == 3


def test_cleanup_old_episodes_handles_missing_directory(temp_podcast_dir):
    """Test cleanup_old_episodes handles non-existent directory."""
    with patch("fetch_podcasts.SCRIPT_DIR", str(temp_podcast_dir.parent)):
        # Should not raise
        cleanup_old_episodes("nonexistent-podcast")


def test_cleanup_old_episodes_ignores_non_mp3_files(temp_podcast_dir):
    """Test cleanup_old_episodes only counts .mp3 files."""
    slug_dir = temp_podcast_dir / "test-podcast"
    slug_dir.mkdir()

    # Create 6 .mp3 files and some non-mp3 files
    for i in range(6):
        episode = slug_dir / f"episode-{i}.mp3"
        episode.write_text(f"content {i}")
        os.utime(episode, (1000 + i, 1000 + i))

    # Create non-mp3 files (should be ignored)
    (slug_dir / "readme.txt").write_text("info")
    (slug_dir / "cover.jpg").write_bytes(b"image")

    with (
        patch("fetch_podcasts.SCRIPT_DIR", str(temp_podcast_dir.parent)),
        patch("fetch_podcasts.EPISODES_TO_KEEP", 5),
    ):

        cleanup_old_episodes("test-podcast")

    # Should remove 1 mp3 file
    remaining_mp3 = list(slug_dir.glob("*.mp3"))
    assert len(remaining_mp3) == 5

    # Non-mp3 files should remain
    assert (slug_dir / "readme.txt").exists()
    assert (slug_dir / "cover.jpg").exists()


# ====== Integration-style Tests ======


@patch("fetch_podcasts.feedparser.parse")
@patch("fetch_podcasts.requests.get")
def test_main_downloads_latest_episodes(mock_get, mock_parse, temp_podcast_dir):
    """Test main function flow (without actually calling main)."""
    from fetch_podcasts import PODCASTS

    # Mock RSS feed response
    mock_parse.return_value = Mock(
        entries=[
            {
                "title": "Episode 1",
                "links": [
                    {"rel": "enclosure", "type": "audio/mpeg", "href": "http://ex.com/ep1.mp3"}
                ],
                "published_parsed": time.strptime("2024-01-01", "%Y-%m-%d"),
            },
            {
                "title": "Episode 2",
                "links": [
                    {"rel": "enclosure", "type": "audio/mpeg", "href": "http://ex.com/ep2.mp3"}
                ],
                "published_parsed": time.strptime("2024-01-02", "%Y-%m-%d"),
            },
        ]
    )

    # Mock download response
    mock_response = Mock()
    mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    with (
        patch("fetch_podcasts.SCRIPT_DIR", str(temp_podcast_dir.parent)),
        patch("fetch_podcasts.PODCASTS", {"test": {"rss": "http://example.com/feed.xml"}}),
        patch("fetch_podcasts.EPISODES_TO_DOWNLOAD", 5),
    ):

        # Simulate what main() does
        from fetch_podcasts import EPISODES_TO_DOWNLOAD

        for slug, info in {"test": {"rss": "http://example.com/feed.xml"}}.items():
            feed = mock_parse(info["rss"])
            for entry in feed.entries[:EPISODES_TO_DOWNLOAD]:
                try:
                    download_episode(slug, entry)
                except Exception:
                    pass

    # Verify episodes were downloaded
    test_dir = temp_podcast_dir / "test"
    assert test_dir.exists()
    episodes = list(test_dir.glob("*.mp3"))
    assert len(episodes) == 2
