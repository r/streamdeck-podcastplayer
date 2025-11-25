# Setup Guide

Complete setup instructions for the Koa Sonos StreamDeck controller.

## Prerequisites

### Hardware
- **Elgato StreamDeck+** (with dials and touchscreen)
- **Sonos speaker** (on same network)
- **Raspberry Pi** or computer running Linux/macOS

### Software
- Python 3.9 or higher
- pip (Python package manager)
- git

## Installation Steps

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd koa-sonos
```

### 2. Install Dependencies

```bash
pip3 install -r requirements.txt
```

Or with virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Provide Your Own Media Files

⚠️ **Important**: The repository doesn't include audio or image files. You need to provide your own.

#### White Noise Audio

Add your white noise audio file:

```bash
# Place your MP3 file in the music directory
cp /path/to/your/whitenoise.mp3 music/white_noise.mp3
```

See `music/README.md` for audio sources and requirements.

#### Button Icons

Add icon images for your StreamDeck buttons:

```bash
# Add icon for white noise button (120x120 pixels recommended)
cp /path/to/whitenoise-icon.png icons/white_noise.png

# Add podcast icons
cp /path/to/mb-icon.png icons/mb.png
cp /path/to/sc-icon.png icons/sc.png
```

See `icons/README.md` for icon creation tips.

### 4. Configure Settings

Edit `config.yaml` to match your setup:

```yaml
sonos:
  speaker_name: "Your Speaker Name"  # Change to your Sonos speaker name

podcasts:
  feeds:
    your-podcast:
      name: "Your Podcast"
      rss: "https://example.com/feed.xml"
      icon: "icons/your-podcast.png"
      button: 1
```

See `CONFIG_README.md` for full configuration options.

### 5. Download Podcast Episodes

```bash
python3 fetch_podcasts.py
```

This will:
- Download the latest episodes from your configured podcasts
- Store them in the `podcasts/` directory
- Keep the most recent episodes (configurable)

### 6. Find Your Sonos Speaker Name

```bash
python3 -c "import soco; print([s.player_name for s in soco.discover()])"
```

Update `config.yaml` with the exact name shown.

### 7. Run the Application

```bash
python3 sonos_streamdeck.py
```

You should see:
```
[HTTP] Serving /path/to/koa-sonos on port 8000
[Sonos] Connected to Speaker Name @ 192.168.x.x
[Deck] connected with 8 keys
[Main] Ready.
```

## Directory Structure After Setup

```
koa-sonos/
├── config.yaml              # Your configuration
├── sonos_streamdeck.py      # Main application
├── fetch_podcasts.py        # Podcast downloader
├── music/
│   ├── README.md
│   └── white_noise.mp3      # YOUR FILE (not in git)
├── icons/
│   ├── README.md
│   ├── white_noise.png      # YOUR FILE (not in git)
│   ├── mb.png               # YOUR FILE (not in git)
│   └── sc.png               # YOUR FILE (not in git)
├── podcasts/                # Downloaded episodes (not in git)
│   ├── million-bazillion/
│   │   └── *.mp3
│   └── short-and-curly/
│       └── *.mp3
└── tests/                   # Test suite
```

## Troubleshooting

### "No StreamDeck found"
- Ensure StreamDeck is connected via USB
- Check USB permissions (may need udev rules on Linux)
- Try: `lsusb` to see if device is detected

### "Could not find speaker"
- Verify Sonos speaker is on and connected to network
- Check speaker name matches exactly (case-sensitive)
- Ensure computer and Sonos are on same network

### "Module not found" errors
- Ensure all dependencies are installed: `pip3 install -r requirements.txt`
- Check Python version: `python3 --version` (should be 3.9+)

### Icons not showing
- Verify icon files exist in `icons/` directory
- Check file permissions (should be readable)
- Ensure filenames match `config.yaml` exactly

### White noise not playing
- Verify `music/white_noise.mp3` exists
- Check file is a valid MP3
- Try playing directly: `mpv music/white_noise.mp3`

## Running on Startup (Raspberry Pi)

Create a systemd service:

```bash
sudo nano /etc/systemd/system/koa-sonos.service
```

```ini
[Unit]
Description=Koa Sonos StreamDeck Controller
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/koa-sonos
ExecStart=/usr/bin/python3 /home/pi/koa-sonos/sonos_streamdeck.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable koa-sonos
sudo systemctl start koa-sonos
sudo systemctl status koa-sonos
```

## Updating Podcasts Automatically

Add to crontab to download new episodes daily:

```bash
crontab -e
```

Add:
```
0 6 * * * cd /home/pi/koa-sonos && /usr/bin/python3 fetch_podcasts.py
```

This downloads new episodes at 6am daily.

## Development Setup

### Running Tests

```bash
# Run all tests
python3 -m pytest -v

# Run specific test file
python3 -m pytest tests/test_sonos_streamdeck.py -v

# Run with coverage (requires pytest-cov)
python3 -m pytest --cov=. --cov-report=html
```

### Making Changes

1. Tests are in `tests/` directory
2. Run tests before and after changes
3. Update documentation if adding features
4. Check `TEST_README.md` for testing guide

## Security Notes

- `.gitignore` prevents committing binary files
- Don't commit personal audio or images
- `config.yaml` is tracked - don't put sensitive data there
- Consider `config.local.yaml` for personal overrides (ignored by git)

## Getting Help

- Check documentation files:
  - `CONFIG_README.md` - Configuration options
  - `TEST_README.md` - Testing guide
  - `STREAMDECK_CONTROLS.md` - Control reference
  - `TOUCHSCREEN_LAYOUT.md` - Display layout
- Run tests to verify setup: `python3 -m pytest`
- Check console output for error messages

## Next Steps

After setup is complete:

1. **Test white noise**: Press button 0 or push dial 0
2. **Test volume**: Turn dial 0
3. **Play a podcast**: Press button 1 or 2
4. **Try scrubbing**: Turn dial 1 during playback
5. **Adjust brightness**: Turn dial 3

See `STREAMDECK_CONTROLS.md` for complete control reference.

