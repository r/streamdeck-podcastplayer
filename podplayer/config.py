#!/usr/bin/env python3
"""
Configuration module for koa-sonos StreamDeck controller.

Loads configuration from config.yaml and provides easy access to settings.
"""
from __future__ import annotations

import os
from typing import Any, Optional
import yaml
from typing import Dict, Any


class Config:
    """Configuration manager for the Sonos StreamDeck controller."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize configuration.

        Args:
            config_path: Path to config.yaml file. If None, looks in script directory.
        """
        if config_path is None:
            # config.yaml is in project root, not in src/
            src_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(src_dir)
            config_path = os.path.join(project_root, "config.yaml")

        self._config_path = config_path
        # script_dir is the project root, not src/
        self._script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Load configuration
        with open(self._config_path, "r") as f:
            self._config: dict[str, Any] = yaml.safe_load(f)

    # ===== Core Properties =====

    @property
    def script_dir(self) -> str:
        """Directory where the script is located."""
        return self._script_dir

    # ===== Sonos Settings =====

    @property
    def sonos_speaker_name(self) -> str:
        """Name of the Sonos speaker to connect to."""
        name: str = self._config["sonos"]["speaker_name"]
        return name

    # ===== StreamDeck Settings =====

    @property
    def streamdeck_brightness(self) -> int:
        """StreamDeck brightness (0-100)."""
        brightness: int = self._config["streamdeck"]["brightness"]
        return brightness

    @property
    def http_port(self) -> int:
        """HTTP server port for serving audio files to Sonos."""
        port: int = self._config["streamdeck"]["http_port"]
        return port

    # ===== Button Configuration =====

    @property
    def button_config(self) -> Dict[int, Dict[str, Any]]:
        """
        Get all button configurations.

        Returns:
            Dict with button number as key and button config as value.
            Button config has 'type' and type-specific fields.
        """
        buttons = {}
        button_section = self._config.get("buttons", {})

        for button_num, config in button_section.items():
            button_int = int(button_num)
            button_type = config.get("type")

            if button_type == "loop":
                buttons[button_int] = {
                    "type": "loop",
                    "name": config.get("name", "Loop"),
                    "audio_file": os.path.join(self._script_dir, config["audio_file"]),
                    "icon": os.path.join(self._script_dir, config["icon"]),
                }
            elif button_type == "podcast":
                buttons[button_int] = {
                    "type": "podcast",
                    "podcast": config["podcast"],
                }

        return buttons

    @property
    def loop_buttons(self) -> Dict[int, Dict[str, str]]:
        """
        Get all loop button configurations.

        Returns:
            Dict with button number as key and loop config (name, audio_file, icon) as value.
        """
        loops = {}
        for button_num, config in self.button_config.items():
            if config["type"] == "loop":
                loops[button_num] = {
                    "name": config["name"],
                    "audio_file": config["audio_file"],
                    "icon": config["icon"],
                }
        return loops

    @property
    def podcast_buttons(self) -> Dict[int, str]:
        """
        Get mapping of podcast buttons to podcast slugs.

        Returns:
            Dict with button number as key and podcast slug as value.
        """
        podcasts = {}
        for button_num, config in self.button_config.items():
            if config["type"] == "podcast":
                podcasts[button_num] = config["podcast"]
        return podcasts

    # ===== Podcast Settings =====

    @property
    def episodes_to_download(self) -> int:
        """Number of latest episodes to download per podcast feed."""
        episodes: int = self._config["podcasts"]["episodes_to_download"]
        return episodes

    @property
    def episodes_to_keep(self) -> int:
        """Maximum number of episodes to keep per podcast feed (older episodes are deleted)."""
        episodes: int = self._config["podcasts"]["episodes_to_keep"]
        return episodes

    @property
    def episodes_per_feed(self) -> int:
        """Legacy property - returns episodes_to_keep for backward compatibility."""
        return self.episodes_to_keep

    @property
    def podcast_feeds(self) -> Dict[str, Dict[str, Any]]:
        """
        Dictionary of podcast feeds.

        Returns:
            Dict with podcast slug as key, and dict with 'name', 'rss', 'icon' as value.
        """
        feeds = {}
        for slug, info in self._config["podcasts"]["feeds"].items():
            feeds[slug] = {
                "name": info["name"],
                "rss": info["rss"],
                "icon": os.path.join(self._script_dir, info["icon"]),
            }
        return feeds

    def get_podcast_info(self, slug: str) -> Dict[str, Any]:
        """
        Get information for a specific podcast.

        Args:
            slug: Podcast slug identifier

        Returns:
            Dict with 'name', 'rss', 'icon', 'button' keys
        """
        return self.podcast_feeds.get(slug, {})


# Global config instance
_config_instance: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get the global configuration instance.

    Args:
        config_path: Path to config file (only used on first call)

    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance


# Convenience function for backward compatibility
def load_config(config_path: str = None) -> Config:
    """Load and return configuration. Alias for get_config()."""
    return get_config(config_path)
