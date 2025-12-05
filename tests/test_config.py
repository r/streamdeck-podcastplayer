#!/usr/bin/env python3
"""
Unit tests for config.py

Tests configuration loading and parsing from YAML.
"""
import os
import sys
import pytest
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from podplayer import config as config_module
from podplayer.config import Config, get_config


@pytest.fixture(autouse=True)
def reset_config():
    """Reset the config singleton before and after each test."""
    config_module._config_instance = None
    yield
    config_module._config_instance = None


def test_config_loads_yaml(tmp_path):
    """Test that Config successfully loads a YAML file."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(
        """
sonos:
  speaker_name: "Test Room"

streamdeck:
  brightness: 75
  http_port: 9000

podcasts:
  episodes_to_download: 3
  episodes_to_keep: 10

buttons:
  0:
    type: "loop"
    name: "Test Sound"
    audio_file: "sounds/test.mp3"
    icon: "images/test.png"
  1:
    type: "podcast"
    name: "Test Show"
    rss: "https://example.com/feed.xml"
    icon: "images/show.png"
"""
    )

    config = Config(str(config_file))

    assert config.sonos_speaker_name == "Test Room"
    assert config.streamdeck_brightness == 75
    assert config.http_port == 9000


def test_config_sonos_settings(tmp_path):
    """Test Sonos-related configuration properties."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(
        """
sonos:
  speaker_name: "Living Room"
streamdeck:
  brightness: 80
  http_port: 8000
buttons: {}
podcasts:
  episodes_to_download: 5
  episodes_to_keep: 20
"""
    )

    config = Config(str(config_file))

    assert config.sonos_speaker_name == "Living Room"


def test_config_white_noise_paths(tmp_path):
    """Test loop button configuration with paths."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(
        """
sonos:
  speaker_name: "Test"
streamdeck:
  brightness: 80
  http_port: 8000
buttons:
  0:
    type: "loop"
    name: "White Noise"
    audio_file: "music/white_noise.mp3"
    icon: "icons/white_noise.png"
podcasts:
  episodes_to_download: 5
  episodes_to_keep: 20
"""
    )

    config = Config(str(config_file))

    # Check loop buttons configuration
    loop_buttons = config.loop_buttons
    assert 0 in loop_buttons
    assert loop_buttons[0]["name"] == "White Noise"
    assert loop_buttons[0]["audio_file"].endswith("music/white_noise.mp3")
    assert loop_buttons[0]["icon"].endswith("icons/white_noise.png")
    assert os.path.isabs(loop_buttons[0]["audio_file"])
    assert os.path.isabs(loop_buttons[0]["icon"])


def test_config_podcast_feeds(tmp_path):
    """Test podcast feed configuration from buttons."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(
        """
sonos:
  speaker_name: "Test"
streamdeck:
  brightness: 80
  http_port: 8000
buttons:
  1:
    type: "podcast"
    name: "Show One"
    rss: "https://example.com/show1.xml"
    icon: "icons/show1.png"
  2:
    type: "podcast"
    name: "Show Two"
    rss: "https://example.com/show2.xml"
    icon: "icons/show2.png"
podcasts:
  episodes_to_download: 5
  episodes_to_keep: 20
"""
    )

    config = Config(str(config_file))

    feeds = config.podcast_feeds
    assert len(feeds) == 2
    # Slugs are auto-generated from names
    assert "show-one" in feeds
    assert "show-two" in feeds

    assert feeds["show-one"]["name"] == "Show One"
    assert feeds["show-one"]["rss"] == "https://example.com/show1.xml"
    assert feeds["show-one"]["icon"].endswith("icons/show1.png")


def test_config_podcast_button_mapping(tmp_path):
    """Test podcast button mapping generation."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(
        """
sonos:
  speaker_name: "Test"
streamdeck:
  brightness: 80
  http_port: 8000
buttons:
  0:
    type: "loop"
    name: "Test Loop"
    audio_file: "music/test.mp3"
    icon: "icons/test.png"
  1:
    type: "podcast"
    name: "Show One"
    rss: "https://example.com/show1.xml"
    icon: "icons/show1.png"
  3:
    type: "podcast"
    name: "Show Two"
    rss: "https://example.com/show2.xml"
    icon: "icons/show2.png"
podcasts:
  episodes_to_download: 5
  episodes_to_keep: 20
"""
    )

    config = Config(str(config_file))

    button_mapping = config.podcast_buttons
    # Slugs are auto-generated from names
    assert button_mapping[1] == "show-one"
    assert button_mapping[3] == "show-two"
    # Button 2 not mapped
    assert 2 not in button_mapping
    # Button 0 is a loop button, not a podcast button
    assert 0 not in button_mapping


def test_config_podcast_explicit_slug(tmp_path):
    """Test podcast button with explicit slug."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(
        """
sonos:
  speaker_name: "Test"
streamdeck:
  brightness: 80
  http_port: 8000
buttons:
  1:
    type: "podcast"
    name: "My Fancy Podcast Name!"
    slug: "my-podcast"
    rss: "https://example.com/feed.xml"
    icon: "icons/podcast.png"
podcasts:
  episodes_to_download: 5
  episodes_to_keep: 20
"""
    )

    config = Config(str(config_file))

    # Should use explicit slug instead of auto-generating from name
    assert config.podcast_buttons[1] == "my-podcast"
    assert "my-podcast" in config.podcast_feeds


def test_config_get_podcast_info(tmp_path):
    """Test getting info for a specific podcast."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(
        """
sonos:
  speaker_name: "Test"
streamdeck:
  brightness: 80
  http_port: 8000
buttons:
  1:
    type: "podcast"
    name: "My Show"
    rss: "https://example.com/myshow.xml"
    icon: "icons/myshow.png"
podcasts:
  episodes_to_download: 5
  episodes_to_keep: 20
"""
    )

    config = Config(str(config_file))

    info = config.get_podcast_info("my-show")
    assert info["name"] == "My Show"
    assert info["rss"] == "https://example.com/myshow.xml"

    # Non-existent podcast returns empty dict
    assert config.get_podcast_info("non-existent") == {}


def test_config_episodes_per_feed(tmp_path):
    """Test episodes download and keep settings."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(
        """
sonos:
  speaker_name: "Test"
streamdeck:
  brightness: 80
  http_port: 8000
buttons: {}
podcasts:
  episodes_to_download: 10
  episodes_to_keep: 30
"""
    )

    config = Config(str(config_file))

    assert config.episodes_to_download == 10
    assert config.episodes_to_keep == 30
    # Legacy property should return episodes_to_keep
    assert config.episodes_per_feed == 30


def test_config_episodes_defaults(tmp_path):
    """Test episodes settings have sensible defaults."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(
        """
sonos:
  speaker_name: "Test"
streamdeck:
  brightness: 80
  http_port: 8000
buttons: {}
podcasts: {}
"""
    )

    config = Config(str(config_file))

    # Should have sensible defaults
    assert config.episodes_to_download == 15
    assert config.episodes_to_keep == 50


def test_config_script_dir_property(tmp_path):
    """Test that script_dir property returns a valid path."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(
        """
sonos:
  speaker_name: "Test"
streamdeck:
  brightness: 80
  http_port: 8000
buttons: {}
podcasts:
  episodes_to_download: 5
  episodes_to_keep: 20
"""
    )

    config = Config(str(config_file))

    assert os.path.isabs(config.script_dir)
    assert os.path.exists(config.script_dir)


def test_get_config_singleton():
    """Test that get_config returns a singleton instance."""
    # This test uses the mocked config from conftest.py
    config1 = get_config()
    config2 = get_config()

    assert config1 is config2


def test_config_spotify_buttons(tmp_path):
    """Test Spotify button configuration."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(
        """
sonos:
  speaker_name: "Test"
streamdeck:
  brightness: 80
  http_port: 8000
buttons:
  0:
    type: "loop"
    name: "White Noise"
    audio_file: "music/white_noise.mp3"
    icon: "icons/white_noise.png"
  1:
    type: "podcast"
    name: "Test Show"
    rss: "https://example.com/feed.xml"
    icon: "images/show.png"
  4:
    type: "spotify"
    name: "Kids Playlist"
    uri: "spotify:playlist:37i9dQZF1DX6z20IXmBjWI"
    icon: "icons/spotify.png"
  5:
    type: "spotify"
    name: "Calm Music"
    uri: "spotify:playlist:37i9dQZF1DWXe9gFZP0gtP"
    icon: "icons/calm.png"
podcasts:
  episodes_to_download: 5
  episodes_to_keep: 20
"""
    )

    config = Config(str(config_file))

    # Check spotify buttons configuration
    spotify_buttons = config.spotify_buttons
    assert len(spotify_buttons) == 2
    assert 4 in spotify_buttons
    assert 5 in spotify_buttons

    # Check button 4 configuration
    assert spotify_buttons[4]["name"] == "Kids Playlist"
    assert spotify_buttons[4]["uri"] == "spotify:playlist:37i9dQZF1DX6z20IXmBjWI"
    assert spotify_buttons[4]["icon"].endswith("icons/spotify.png")
    assert os.path.isabs(spotify_buttons[4]["icon"])

    # Check button 5 configuration
    assert spotify_buttons[5]["name"] == "Calm Music"
    assert spotify_buttons[5]["uri"] == "spotify:playlist:37i9dQZF1DWXe9gFZP0gtP"
    assert spotify_buttons[5]["icon"].endswith("icons/calm.png")

    # Verify spotify buttons are NOT in loop_buttons or podcast_buttons
    assert 4 not in config.loop_buttons
    assert 5 not in config.loop_buttons
    assert 4 not in config.podcast_buttons
    assert 5 not in config.podcast_buttons


def test_config_button_config_includes_spotify(tmp_path):
    """Test that button_config includes Spotify type buttons."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(
        """
sonos:
  speaker_name: "Test"
streamdeck:
  brightness: 80
  http_port: 8000
buttons:
  2:
    type: "spotify"
    name: "Party Mix"
    uri: "spotify:album:1234567890"
    icon: "icons/party.png"
podcasts:
  episodes_to_download: 5
  episodes_to_keep: 20
"""
    )

    config = Config(str(config_file))

    # Check full button_config includes spotify type
    button_config = config.button_config
    assert 2 in button_config
    assert button_config[2]["type"] == "spotify"
    assert button_config[2]["name"] == "Party Mix"
    assert button_config[2]["uri"] == "spotify:album:1234567890"
    assert button_config[2]["icon"].endswith("icons/party.png")


def test_config_mixed_button_types(tmp_path):
    """Test configuration with all button types: loop, podcast, and spotify."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(
        """
sonos:
  speaker_name: "Test"
streamdeck:
  brightness: 80
  http_port: 8000
buttons:
  0:
    type: "loop"
    name: "Rain Sounds"
    audio_file: "music/rain.mp3"
    icon: "icons/rain.png"
  1:
    type: "podcast"
    name: "News"
    rss: "https://example.com/news.xml"
    icon: "icons/news.png"
  2:
    type: "spotify"
    name: "Focus Music"
    uri: "spotify:playlist:focus123"
    icon: "icons/focus.png"
  3:
    type: "podcast"
    name: "Comedy"
    rss: "https://example.com/comedy.xml"
    icon: "icons/comedy.png"
  4:
    type: "spotify"
    name: "Workout"
    uri: "spotify:playlist:workout456"
    icon: "icons/workout.png"
podcasts:
  episodes_to_download: 5
  episodes_to_keep: 20
"""
    )

    config = Config(str(config_file))

    # Verify each button type is correctly categorized
    loop_buttons = config.loop_buttons
    podcast_buttons = config.podcast_buttons
    spotify_buttons = config.spotify_buttons

    assert len(loop_buttons) == 1
    assert len(podcast_buttons) == 2
    assert len(spotify_buttons) == 2

    assert 0 in loop_buttons
    assert 1 in podcast_buttons
    assert 3 in podcast_buttons
    assert 2 in spotify_buttons
    assert 4 in spotify_buttons

    # Verify no overlap between button types
    all_buttons = (
        set(loop_buttons.keys()) | set(podcast_buttons.keys()) | set(spotify_buttons.keys())
    )
    assert len(all_buttons) == 5  # All unique

    # Verify podcast feeds are derived correctly
    feeds = config.podcast_feeds
    assert len(feeds) == 2
    assert "news" in feeds
    assert "comedy" in feeds
