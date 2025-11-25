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

buttons:
  0:
    type: "loop"
    name: "Test Sound"
    audio_file: "sounds/test.mp3"
    icon: "images/test.png"
  1:
    type: "podcast"
    podcast: "test-show"

podcasts:
  episodes_to_download: 3
  episodes_to_keep: 10
  feeds:
    test-show:
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
  feeds: {}
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
  feeds: {}
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
    """Test podcast feed configuration."""
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
    podcast: "show-one"
  2:
    type: "podcast"
    podcast: "show-two"
podcasts:
  episodes_per_feed: 5
  feeds:
    show-one:
      name: "Show One"
      rss: "https://example.com/show1.xml"
      icon: "icons/show1.png"
    show-two:
      name: "Show Two"
      rss: "https://example.com/show2.xml"
      icon: "icons/show2.png"
"""
    )

    config = Config(str(config_file))

    feeds = config.podcast_feeds
    assert len(feeds) == 2
    assert "show-one" in feeds
    assert "show-two" in feeds

    assert feeds["show-one"]["name"] == "Show One"
    assert feeds["show-one"]["rss"] == "https://example.com/show1.xml"
    assert feeds["show-one"]["icon"].endswith("icons/show1.png")
    # button is now in buttons section, not in feed info
    assert "button" not in feeds["show-one"]


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
    podcast: "show-one"
  3:
    type: "podcast"
    podcast: "show-two"
podcasts:
  episodes_per_feed: 5
  feeds:
    show-one:
      name: "Show One"
      rss: "https://example.com/show1.xml"
      icon: "icons/show1.png"
    show-two:
      name: "Show Two"
      rss: "https://example.com/show2.xml"
      icon: "icons/show2.png"
    show-three:
      name: "Show Three"
      rss: "https://example.com/show3.xml"
      icon: "icons/show3.png"
"""
    )

    config = Config(str(config_file))

    button_mapping = config.podcast_buttons
    assert button_mapping[1] == "show-one"
    assert button_mapping[3] == "show-two"
    # show-three has no button, so it shouldn't be in mapping
    assert 2 not in button_mapping
    # Button 0 is a loop button, not a podcast button
    assert 0 not in button_mapping


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
    podcast: "my-show"
podcasts:
  episodes_per_feed: 5
  feeds:
    my-show:
      name: "My Show"
      rss: "https://example.com/myshow.xml"
      icon: "icons/myshow.png"
"""
    )

    config = Config(str(config_file))

    info = config.get_podcast_info("my-show")
    assert info["name"] == "My Show"
    assert info["rss"] == "https://example.com/myshow.xml"
    # button is now in buttons section, not in feed info
    assert "button" not in info

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
  feeds: {}
"""
    )

    config = Config(str(config_file))

    assert config.episodes_to_download == 10
    assert config.episodes_to_keep == 30
    # Legacy property should return episodes_to_keep
    assert config.episodes_per_feed == 30


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
  feeds: {}
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
