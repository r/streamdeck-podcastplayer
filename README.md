# Koa Sonos StreamDeck Controller

Control your Sonos speaker and play podcasts using an Elgato StreamDeck+ with dials and touchscreen display.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Type Checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)
[![Tests: pytest](https://img.shields.io/badge/tests-pytest-green.svg)](https://pytest.org/)

## Features

- 🎚️ **Volume Control** - Dial 0 with visual percentage and progress bar
- ⏯️ **Playback Scrubbing** - Dial 1 to seek through tracks, push to play/pause
- 🎵 **Episode Navigation** - Dial 2 to skip between podcast episodes or Spotify tracks
- 💡 **Brightness Control** - Dial 3 to adjust StreamDeck brightness
- 🔁 **Audio Loop** - Button to play/pause looping audio (white noise, rain sounds, etc.)
- 📻 **Podcast Management** - Auto-download and play podcast episodes
- 🎧 **Spotify Integration** - Play Spotify playlists and albums via Sonos
- 📺 **Rich Display** - Touchscreen shows volume, playback position, track/artist info

## StreamDeck Layout

```
Buttons (configurable):
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │
│Loop │ Pod │ Pod │ Pod │Spot │     │     │     │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

Dials:
┌──────────┬──────────┬──────────┬──────────┐
│   0      │   1      │   2      │   3      │
│ Volume   │ Playback │  Track/  │Brightness│
│          │ Scrub    │ Episode  │          │
└──────────┴──────────┴──────────┴──────────┘

Touchscreen:
┌─────────────┬─────────────┬──────────────────────────────┐
│    75%      │ 1:23 / 4:56 │ Anti-Hero                    │
│  ████░░░    │ ███░░░░░    │ Taylor Swift                 │
│   Volume    │   Playing   │ Midnights                    │
└─────────────┴─────────────┴──────────────────────────────┘
```

## Quick Start

### Prerequisites

- Elgato StreamDeck+ (with dials and touchscreen)
- Sonos speaker on the same network
- Python 3.9+

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd koa-sonos

# Install dependencies
pip3 install -r requirements.txt

# Add your media files
cp /path/to/whitenoise.mp3 music/white_noise.mp3
cp /path/to/icons/*.png icons/

# Configure
nano config.yaml  # Set your Sonos speaker name

# Download podcast episodes
python3 fetch_podcasts.py

# Run
python3 sonos_streamdeck.py
```

See [SETUP.md](SETUP.md) for detailed instructions.

## Controls

| Control | Function | Description |
|---------|----------|-------------|
| **Buttons** | Configurable | Loop audio, podcast, or Spotify (see config) |
| **Dial 0 Turn** | Volume | Adjust Sonos speaker volume (0-100%) |
| **Dial 1 Turn** | Scrub playback | Seek forward/backward (5 sec per turn) |
| **Dial 1 Push** | Play/Pause | Toggle playback |
| **Dial 2 Turn** | Track/Episode | Skip tracks (Spotify) or episodes (podcast) |
| **Dial 3 Turn** | Brightness | Adjust StreamDeck brightness |

See [docs/controls.md](docs/controls.md) for complete control reference.

## Configuration

Edit `config.yaml` to customize buttons and settings:

```yaml
sonos:
  speaker_name: "Your Speaker Name"

streamdeck:
  brightness: 80
  http_port: 8000

podcasts:
  episodes_to_download: 15
  episodes_to_keep: 50

# Each button can be: loop, podcast, or spotify
buttons:
  0:
    type: "loop"
    name: "White Noise"
    audio_file: "music/white_noise.mp3"
    icon: "icons/white_noise.png"
  
  1:
    type: "podcast"
    name: "Million Bazillion"
    rss: "https://feeds.publicradio.org/public_feeds/million-bazillion"
    icon: "icons/mb.png"
  
  4:
    type: "spotify"
    name: "Kids Playlist"
    uri: "spotify:playlist:37i9dQZF1DX6z20IXmBjWI"
    icon: "icons/spotify.png"
```

### Spotify Setup

1. Link Spotify to your Sonos in the Sonos app (Settings → Services & Voice → Spotify)
2. Get the Spotify URI: Right-click playlist/album in Spotify → Share → Copy Spotify URI
3. Add a `spotify` button in `config.yaml` with the URI

See [docs/configuration.md](docs/configuration.md) for all options.

## Documentation

- **[SETUP.md](SETUP.md)** - Installation and setup guide
- **[docs/configuration.md](docs/configuration.md)** - Configuration options
- **[docs/controls.md](docs/controls.md)** - Complete control reference
- **[docs/touchscreen.md](docs/touchscreen.md)** - Display layout details
- **[docs/testing.md](docs/testing.md)** - Running tests
- **[docs/development/](docs/development/)** - Development documentation

## Testing

```bash
# Run all tests
python3 -m pytest -v

# Run specific test file
python3 -m pytest tests/test_sonos_streamdeck.py -v
```

59 tests with full hardware mocking - no StreamDeck or Sonos required!

## Architecture

- **sonos_streamdeck.py** - Main application, StreamDeck control
- **fetch_podcasts.py** - Download podcast episodes from RSS feeds
- **config.py** - Configuration loader (reads config.yaml)
- **config.yaml** - User configuration (speaker, podcasts, etc.)
- **tests/** - Comprehensive test suite with mocked hardware

## Requirements

- Python 3.9+
- Elgato StreamDeck+ (with dials and touchscreen)
- Sonos speaker
- See [requirements.txt](requirements.txt) for Python packages

## Project Status

✅ Fully functional and tested (59 tests passing)  
✅ Hardware fully mocked for testing  
✅ Configuration externalized to YAML  
✅ Spotify integration via Sonos  
✅ Comprehensive documentation  
✅ Ready for deployment on Raspberry Pi

## Development

### Running Tests

```bash
uv run pytest
```

### Type Checking

```bash
./run_mypy.sh
# or
uv run mypy podplayer/
```

### Code Formatting

This project uses [Black](https://github.com/psf/black) for consistent code formatting:

```bash
./run_black.sh
# or
uv run python -m black podplayer/ tests/ *.py
```

Black is configured in `pyproject.toml` with a line length of 100 characters.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Raffi Krikorian

## Acknowledgments

Built for Koa's room to make bedtime easier! 🌙

**Technologies:**
- [python-soco](https://github.com/SoCo/SoCo) - Sonos control library
- [python-elgato-streamdeck](https://github.com/abcminiuser/python-elgato-streamdeck) - Stream Deck interface
- [feedparser](https://github.com/kurtmckee/feedparser) - RSS feed parsing
- [Pillow](https://python-pillow.org/) - Image processing for touchscreen display

