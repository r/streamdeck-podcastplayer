# Music Directory

This directory contains audio files for the white noise loop.

## Setup

Add your white noise audio file here:

```
music/
  └── white_noise.mp3
```

## File Requirements

- **Filename**: `white_noise.mp3` (as specified in `config.yaml`)
- **Format**: MP3 (recommended), or update `config.yaml` for other formats
- **Content**: Any audio you want to loop (white noise, rain sounds, etc.)

## Sources

You can find white noise audio from:
- [MyNoise.net](https://mynoise.net/) - Customizable soundscapes
- [YouTube](https://youtube.com) - Search "white noise" (use youtube-dl to download)
- Record your own ambient sounds
- Use audio editing software to create loops

## Customization

To use a different file:
1. Place your audio file in this directory
2. Update `config.yaml`:
   ```yaml
   white_noise:
     audio_file: "music/your-file.mp3"
   ```

## Note

Audio files are not tracked in git (see `.gitignore`).
Each user should provide their own audio files.

