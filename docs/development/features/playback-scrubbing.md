# Playback Scrubbing Feature

## Overview

Dial 1 (the second dial) now provides complete playback control with a visual progress bar showing your position in the currently playing track.

## Visual Display

```
┌──────────────────┐
│  1:23 / 4:56     │  ← Current position / Total duration
│  ███████░░░░░    │  ← Orange progress bar
│       ▶          │  ← Playback state icon
└──────────────────┘
```

### Display Elements

1. **Time Display** (top)
   - Shows: `[current] / [duration]`
   - Format: MM:SS
   - Example: `1:23 / 4:56` = 1 minute 23 seconds into a 4 minute 56 second track
   - Updates every 2 seconds automatically

2. **Progress Bar** (middle)
   - **Orange fill** shows current position in track
   - Track background shows total duration
   - Visual representation makes it easy to see where you are

3. **Playback State Icon** (bottom)
   - `▶` = Currently playing
   - `⏸` = Paused
   - `⏹` = Stopped

## Controls

### Turn Dial 1: Scrub Through Track

**Turn Clockwise** → Fast forward (skip ahead)
- Each turn increment = 5 seconds forward
- Smoothly scrubs through the track
- Automatically clamps at track end

**Turn Counter-clockwise** → Rewind (go back)
- Each turn increment = 5 seconds backward  
- Smoothly scrubs back through the track
- Automatically clamps at track start (0:00)

**Examples:**
- Turn dial 5 notches clockwise = 25 seconds forward
- Turn dial 3 notches counter-clockwise = 15 seconds backward

### Push Dial 1: Play/Pause

**Push** → Toggle playback
- If playing → Pause
- If paused → Resume playing
- Visual icon updates to show new state

## Technical Details

### Scrubbing Behavior

- **Increment**: 5 seconds per dial notch
- **Clamping**: Automatically prevents seeking before 0:00 or after track end
- **Response**: Immediate seeking via Sonos API
- **Display Update**: Touchscreen updates after each scrub

### Display Updates

- **Manual**: Updates immediately when you turn or push the dial
- **Automatic**: Updates every 2 seconds to show playback progress
- **Lightweight**: Only fetches track info when needed

### Supported Formats

Works with any audio source playing on Sonos:
- Local files (white noise, podcasts)
- Streaming services (Spotify, Apple Music, etc.)
- Radio streams (may not support seeking)
- Line-in sources

## Integration with Other Dials

| Dial | Function | Display |
|------|----------|---------|
| 0 | Volume Control | Blue bar with percentage + "Volume" label |
| 1 | **Playback Scrubbing** | **Orange bar with time + play/pause icon** |
| 2 | *(Available)* | - |
| 3 | Brightness Control | No display |

## Code Implementation

### New Functions

1. **`format_time(seconds)`**
   - Converts seconds to MM:SS format
   - Example: `85` → `"1:25"`

2. **`get_playback_info()`**
   - Fetches current track position, duration, state, title from Sonos
   - Parses HH:MM:SS time format to seconds
   - Returns dict with all playback information

3. **`update_touchscreen_ui(deck_obj)`**
   - Draws complete touchscreen with both volume (dial 0) and playback (dial 1)
   - Updates both displays simultaneously
   - Called automatically every 2 seconds

### Updated Functions

- **`on_dial_change()`**: Added dial 1 handling for scrubbing and play/pause
- **`main()`**: Added periodic touchscreen updates (every 2 seconds)

## Testing

Added 6 comprehensive tests:
- ✅ Scrub forward
- ✅ Scrub backward  
- ✅ Clamp at track start
- ✅ Clamp at track end
- ✅ Push to pause when playing
- ✅ Push to play when paused

**Result:** All 68 tests passing! ✓

## Console Output

When using the playback scrubbing feature, you'll see:

```
[Dial 1] Seeking to 0:01:25 (85s)
[Dial 1] Push: Pause
[Dial 1] Push: Play
```

## Usage Tips

1. **Fine Control**: Each turn = 5 seconds, so you can scrub precisely
2. **Quick Skip**: Turn multiple notches quickly to jump further
3. **Progress Tracking**: Glance at the display to see where you are
4. **Quick Pause**: Push dial 1 instead of reaching for your phone
5. **Resume**: Push again to resume right where you left off

## Future Enhancements

Potential additions for dial 1:
- Variable scrub speed (hold to scrub faster)
- Chapter markers for podcast
- Repeat/loop controls
- Skip to next/previous track (with long press)

## Limitations

- Some streaming services may have limitations on seeking
- Radio streams typically don't support seeking
- Display updates every 2 seconds (not real-time)
- Scrubbing while paused may require resuming playback first

## Troubleshooting

**Display not updating?**
- Check that Sonos speaker is connected
- Verify track is actually playing
- Try restarting the application

**Can't scrub?**
- Some audio sources don't support seeking
- Try with a local file or different source

**Position seems incorrect?**
- Display updates every 2 seconds - wait a moment
- Try pushing dial 1 to refresh state

