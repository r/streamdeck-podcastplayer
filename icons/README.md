# Icons Directory

This directory contains button icons for the StreamDeck.

## Setup

Add icon images for your buttons:

```
icons/
  ├── white_noise.png     # Button 0 - White noise loop
  ├── mb.png              # Button 1 - Million Bazillion podcast
  └── sc.png              # Button 2 - Short and Curly podcast
```

## File Requirements

- **Format**: PNG (recommended for transparency)
- **Size**: 120x120 pixels (will be automatically resized if needed)
- **Naming**: Match the filenames in `config.yaml`

## Creating Icons

### Option 1: Download Podcast Artwork
1. Find the podcast RSS feed
2. Look for the `<itunes:image>` tag
3. Download and resize the image

### Option 2: Design Your Own
- Use any image editor (Photoshop, GIMP, Canva, etc.)
- Create 120x120px images
- Export as PNG

### Option 3: Use Emoji/Symbols
```bash
# Convert emoji to image on macOS
# (requires ImageMagick)
convert -size 120x120 -background transparent \
  -fill white -font "Apple Color Emoji" \
  label:🎵 white_noise.png
```

## Adding New Podcasts

When adding a new podcast in `config.yaml`:

1. Add the icon file to this directory
2. Reference it in your podcast config:
   ```yaml
   podcasts:
     feeds:
       my-podcast:
         icon: "icons/my-podcast.png"
   ```

## Image Resources

- Podcast RSS feeds (often include artwork URLs)
- [Noun Project](https://thenounproject.com/) - Icons
- [Unsplash](https://unsplash.com/) - Free images
- [Flaticon](https://www.flaticon.com/) - Icon packs

## Note

Icon files are not tracked in git (see `.gitignore`).
Each user should provide their own icon images.

