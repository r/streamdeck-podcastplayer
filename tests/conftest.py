#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures.

This file sets up mocks for hardware dependencies (StreamDeck, Sonos)
BEFORE any test modules are imported, ensuring consistent mocking across all tests.
"""
import sys
import os
import pytest
import requests_mock as rm
from unittest.mock import MagicMock, patch
import tempfile


# ===== Mock Hardware Dependencies =====
# These mocks must be set up BEFORE importing any project modules
# that depend on StreamDeck or soco libraries.


# Create proper mock DialEventType enum with unique objects
class MockDialEventType:
    TURN = object()
    PUSH = object()


# Mock StreamDeck modules
sys.modules["StreamDeck"] = MagicMock()
sys.modules["StreamDeck.DeviceManager"] = MagicMock()
sys.modules["StreamDeck.Devices"] = MagicMock()

mock_streamdeck_module = MagicMock()
mock_streamdeck_module.DialEventType = MockDialEventType
sys.modules["StreamDeck.Devices.StreamDeck"] = mock_streamdeck_module

# Mock Sonos modules
sys.modules["soco"] = MagicMock()
sys.modules["soco.discovery"] = MagicMock()
sys.modules["soco.plugins"] = MagicMock()
sys.modules["soco.plugins.sharelink"] = MagicMock()


# ===== Test Configuration =====


@pytest.fixture(scope="session")
def test_config_file(tmp_path_factory):
    """Create a temporary config.yaml for tests."""
    tmp_dir = tmp_path_factory.mktemp("config")
    config_file = tmp_dir / "config.yaml"

    # Get the actual project directory for icon paths
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    config_content = f"""
# Test configuration
sonos:
  speaker_name: "Test Speaker"

streamdeck:
  brightness: 80
  http_port: 8000

podcasts:
  episodes_to_download: 5
  episodes_to_keep: 20

buttons:
  0:
    type: "loop"
    name: "White Noise"
    audio_file: "music/white_noise.mp3"
    icon: "icons/white_noise.png"
  1:
    type: "podcast"
    name: "Test Podcast"
    slug: "test-podcast"
    rss: "https://example.com/feed.xml"
    icon: "icons/test.png"
  2:
    type: "podcast"
    name: "Million Bazillion"
    slug: "million-bazillion"
    rss: "https://feeds.publicradio.org/public_feeds/million-bazillion"
    icon: "icons/mb.png"
  3:
    type: "podcast"
    name: "Short and Curly"
    slug: "short-and-curly"
    rss: "https://www.abc.net.au/feeds/7388142/podcast.xml"
    icon: "icons/sc.png"
"""
    config_file.write_text(config_content)
    return str(config_file)


@pytest.fixture
def mock_config(test_config_file, monkeypatch, request):
    """Mock the config module to use test configuration."""
    # Skip for test_config.py tests
    if "test_config" in request.node.nodeid:
        yield
        return

    # Reset the config module's global instance
    from podplayer import config as config_module

    config_module._config_instance = None

    # Patch the config path to use our test config
    original_init = config_module.Config.__init__

    def mock_init(self, config_path=None):
        original_init(self, test_config_file)

    monkeypatch.setattr(config_module.Config, "__init__", mock_init)

    yield

    # Reset after test
    config_module._config_instance = None


# Auto-use mock_config for all tests except config tests
@pytest.fixture(autouse=True)
def auto_mock_config(mock_config):
    """Automatically use mock_config for all tests."""
    pass


# ===== Shared Fixtures =====


@pytest.fixture
def requests_mock():
    """Provide a requests_mock adapter for mocking HTTP requests."""
    with rm.Mocker() as m:
        yield m
