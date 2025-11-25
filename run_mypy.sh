#!/bin/bash
# Run mypy type checking on all source files
uv run python3 -m mypy \
  podplayer/utils.py \
  podplayer/persistence.py \
  podplayer/sonos_control.py \
  podplayer/podcast_manager.py \
  podplayer/streamdeck_ui.py \
  podplayer/streamdeck_handlers.py \
  podplayer/config.py \
  sonos_streamdeck.py \
  fetch_podcasts.py

