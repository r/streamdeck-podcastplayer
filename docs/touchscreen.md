# StreamDeck+ Touchscreen Layout

## Complete Display Overview

The StreamDeck+ touchscreen is divided into 4 regions, one above each dial:

```
┌─────────────┬─────────────┬──────────────────────────────┐
│   Dial 0    │   Dial 1    │        Dials 2 & 3          │
│   Volume    │  Playback   │       Track Info             │
│             │             │                              │
│    75%      │ 1:23 / 4:56 │ How Interest Works           │
│  ████░░░    │ ███░░░░░    │ Million Bazillion            │
│   Volume    │     ▶       │                              │
└─────────────┴─────────────┴──────────────────────────────┘
```

## Region Details

### Region 1: Volume (Dial 0)

```
┌──────────────┐
│    75%       │  ← Large percentage (24pt, white)
│  ████░░░░    │  ← Blue progress bar
│   Volume     │  ← Label (gray)
└──────────────┘
```

**Shows:**
- Current volume percentage (0-100%)
- Visual progress bar in blue
- "Volume" label

**Updates:**
- Immediately when dial is turned
- Color: Blue fill

### Region 2: Playback Position (Dial 1)

```
┌──────────────┐
│  1:23 / 4:56 │  ← Time: current / duration (14pt, white)
│  ███░░░░░    │  ← Orange progress bar
│      ▶       │  ← Play state icon (gray)
└──────────────┘
```

**Shows:**
- Current position / Total duration (MM:SS format)
- Visual progress bar in orange
- Playback state icon: ▶ (playing) ⏸ (paused) ⏹ (stopped)

**Updates:**
- Immediately when dial is turned or pushed
- Every 2 seconds automatically (shows progress)
- Color: Orange fill

### Region 3+4: Track Info (Dials 2 & 3)

```
┌────────────────────────────────┐
│ How Interest Works             │  ← Track title (14pt, white)
│ Million Bazillion              │  ← Artist/Album (small, light gray)
│                                │
└────────────────────────────────┘
```

**Shows:**
- **Line 1**: Track/Episode title
- **Line 2**: Artist name or Album name (whichever is available)
- Smart text truncation with ellipsis if too long

**Works with:**
- Podcasts: Shows episode title + podcast name
- Music: Shows track title + artist name
- White noise: Shows file name
- Any audio source on Sonos

**Updates:**
- Every 2 seconds when track changes
- Automatically truncates long titles

## Visual Design

### Colors

| Element | Color | Hex | Purpose |
|---------|-------|-----|---------|
| Volume bar | Blue | `#00B4FF` | Familiar volume indicator |
| Playback bar | Orange | `#FF8C00` | Distinct from volume |
| Primary text | White | `#FFFFFF` | High visibility |
| Secondary text | Light gray | `#B4B4B4` | Labels and metadata |
| Label text | Medium gray | `#969696` | Subtle labels |
| Background | Black | `#000000` | High contrast |
| Track outline | Dark gray | `#505050` | Subtle borders |

### Fonts

- **24pt Helvetica**: Volume percentage (large, bold)
- **14pt Helvetica**: Time display, track title
- **Default system**: Labels, artist/album

### Layout Measurements

```
Total width: 800px
Total height: 100px

Dial region width: 200px each (4 regions)
Track info spans: 400px (regions 3+4 combined)

Margins: 8-10px
Track height: 18px
```

## Example Scenarios

### Playing a Podcast

```
┌─────────────┬─────────────┬──────────────────────────────┐
│    65%      │ 12:34/45:00 │ Why Do We Have Toes?         │
│  ██████░    │ ██░░░░░░    │ Short and Curly              │
│   Volume    │     ▶       │                              │
└─────────────┴─────────────┴──────────────────────────────┘
```

- Volume at 65%
- 12 minutes 34 seconds into 45-minute episode
- Currently playing
- Episode title with podcast name

### Playing Music (Spotify/Apple Music)

```
┌─────────────┬─────────────┬──────────────────────────────┐
│    80%      │  2:15/3:42  │ Bohemian Rhapsody            │
│  ████████   │ ██████░░    │ Queen                        │
│   Volume    │     ▶       │                              │
└─────────────┴─────────────┴──────────────────────────────┘
```

- Song title and artist displayed
- Progress through the song
- Volume and playback controls

### Paused White Noise

```
┌─────────────┬─────────────┬──────────────────────────────┐
│    50%      │  0:00/0:00  │ white_noise.mp3              │
│  █████░░    │             │                              │
│   Volume    │     ⏸       │                              │
└─────────────┴─────────────┴──────────────────────────────┘
```

- Paused (⏸ icon)
- Shows filename
- No artist/album info available

### Long Title Truncation

```
┌─────────────┬─────────────┬──────────────────────────────┐
│    70%      │  8:42/22:18 │ The Science of Why People... │
│  ███████░   │ ████░░░░    │ Million Bazillion            │
│   Volume    │     ▶       │                              │
└─────────────┴─────────────┴──────────────────────────────┘
```

- Long titles automatically truncated
- Ellipsis (...) added when text is too long
- Maximum readability maintained

## Smart Features

### 1. Automatic Text Truncation

- Measures text width before displaying
- Intelligently truncates to fit available space
- Always adds ellipsis (...) when truncated
- Binary search algorithm for optimal truncation point

### 2. Metadata Fallback

Priority order for subtitle (line 2):
1. Artist name (if different from title)
2. Album name (if different from title)
3. Nothing (if no metadata available)

### 3. Progressive Updates

- **User interaction**: Immediate update
- **Playback progress**: Every 2 seconds
- **Track changes**: Automatic detection

### 4. Error Handling

- Gracefully handles missing metadata
- Shows "No track" when nothing playing
- Doesn't crash if Sonos connection drops

## Accessibility

- **High contrast**: White text on black background
- **Large text**: 14-24pt fonts for readability
- **Clear icons**: Universally recognized symbols (▶⏸⏹)
- **Color coding**: Blue (volume) vs Orange (playback) for quick identification
- **Text truncation**: Ensures all text is readable, never cut off mid-character

## Technical Implementation

### Drawing Order

1. Clear screen (black background)
2. Draw volume region (dial 0)
3. Draw playback region (dial 1)
4. Draw track info region (dials 2+3)
5. Render to JPEG
6. Send to StreamDeck

### Performance

- Single unified rendering pass
- Efficient text truncation algorithm
- Minimal API calls to Sonos
- Updates only when needed

### Memory Usage

- Single 800x100px image buffer
- JPEG compression for efficient transfer
- No persistent image caching

## Future Enhancements

Potential additions:
- **Scrolling text** for very long titles
- **Album art thumbnail** in track info area
- **Queue preview** showing next track
- **Podcast artwork** when available
- **Lyrics display** for music
- **Play count** or episode number
- **Release date** or publish date

