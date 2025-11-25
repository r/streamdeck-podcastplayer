# Configuration Guide

The koa-sonos StreamDeck controller uses a centralized YAML configuration file (`config.yaml`) to manage all settings.

## Configuration File: `config.yaml`

All configuration is stored in a single YAML file that is easy to read and modify.

### Structure

```yaml
# Sonos speaker settings
sonos:
  speaker_name: "Koa's room"  # Name of your Sonos speaker

# StreamDeck settings
streamdeck:
  brightness: 80     # Brightness level (0-100)
  http_port: 8000    # Port for HTTP server (serves audio to Sonos)

# White noise loop settings
white_noise:
  audio_file: "music/white_noise.mp3"  # Path to white noise MP3
  icon: "icons/white_noise.png"         # Path to button icon
  button: 0                              # StreamDeck button number

# Podcast settings
podcasts:
  episodes_per_feed: 5  # How many episodes to keep per podcast
  
  feeds:
    # Each podcast has a unique slug identifier
    million-bazillion:
      name: "Million Bazillion"
      rss: "https://feeds.publicradio.org/public_feeds/million-bazillion"
      icon: "icons/mb.png"
      button: 1
    
    short-and-curly:
      name: "Short and Curly"
      rss: "https://www.abc.net.au/feeds/7388142/podcast.xml"
      icon: "icons/sc.png"
      button: 2
```

## Adding a New Podcast

To add a new podcast, edit `config.yaml` and add an entry under `podcasts.feeds`:

```yaml
podcasts:
  episodes_per_feed: 5
  
  feeds:
    my-new-podcast:                    # Unique slug identifier
      name: "My New Podcast"           # Display name
      rss: "https://example.com/feed"  # RSS feed URL
      icon: "icons/my-podcast.png"     # Icon file (place in icons/ directory)
      button: 3                         # StreamDeck button number (optional)
```

Steps:
1. Add your podcast icon image to the `icons/` directory
2. Edit `config.yaml` to add the new podcast
3. Restart the application
4. Run `fetch_podcasts.py` to download episodes

## Configuration Module: `config.py`

The `config.py` module loads and provides access to configuration settings.

### Usage in Code

```python
from config import get_config

# Get configuration instance
config = get_config()

# Access settings
speaker_name = config.sonos_speaker_name
brightness = config.streamdeck_brightness
podcast_feeds = config.podcast_feeds
button_mapping = config.podcast_button_mapping
```

### Available Properties

#### Sonos Settings
- `config.sonos_speaker_name` - Name of Sonos speaker

#### StreamDeck Settings
- `config.streamdeck_brightness` - Brightness (0-100)
- `config.http_port` - HTTP server port

#### White Noise Settings
- `config.white_noise_audio_path` - Full path to MP3
- `config.white_noise_icon_path` - Full path to icon
- `config.white_noise_button` - Button number

#### Podcast Settings
- `config.episodes_per_feed` - Number of episodes to keep
- `config.podcast_feeds` - Dictionary of all podcasts
- `config.podcast_button_mapping` - Button number → podcast slug mapping
- `config.get_podcast_info(slug)` - Get info for specific podcast

#### Utility Properties
- `config.script_dir` - Directory where scripts are located

## Benefits of Centralized Configuration

1. **Easy to Modify**: Change settings without editing code
2. **No Circular Imports**: Both `sonos_streamdeck.py` and `fetch_podcasts.py` can read the same config
3. **Version Control Friendly**: YAML is easy to diff and track changes
4. **Documented**: Comments in YAML explain each setting
5. **Type-Safe**: Config module provides typed properties
6. **Testable**: Tests use a separate test configuration

## File Paths

All file paths in `config.yaml` are relative to the project directory. The config module automatically converts them to absolute paths.

Example:
- Config: `icon: "icons/mb.png"`
- Loaded as: `/full/path/to/koa-sonos/icons/mb.png`

## Troubleshooting

### Config file not found
If you see an error about missing `config.yaml`, make sure it exists in the same directory as the Python scripts.

### Invalid YAML syntax
YAML is sensitive to indentation. Use spaces (not tabs) and maintain consistent indentation (2 spaces recommended).

### Podcast not appearing
1. Check that the podcast slug is unique
2. Verify the RSS feed URL is correct
3. Make sure the icon file exists
4. Restart the application after editing config

### Button conflicts
If multiple podcasts use the same button number, the last one in the config file will take precedence. Ensure each podcast has a unique button number.

