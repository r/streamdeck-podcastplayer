# StreamDeck+ Controls Reference

Quick reference guide for all StreamDeck+ controls in the Koa Sonos controller.

## Buttons

```
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │
│ 🔊  │ 📻  │ 📻  │     │     │     │     │     │
│Loop │ MB  │ SC  │     │     │     │     │     │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
```

| Button | Function | Action |
|--------|----------|--------|
| 0 | White Noise Loop | Toggle white noise loop on/off |
| 1 | Million Bazillion | Play next episode |
| 2 | Short and Curly | Play next episode |
| 3-7 | *(Available)* | Not yet assigned |

## Dials

```
┌──────────┬──────────┬──────────┬──────────┐
│   0      │   1      │   2      │   3      │
│ Volume   │ Playback │          │Brightness│
└──────────┴──────────┴──────────┴──────────┘
```

### Dial 0: Volume & Loop Control

**Turn:** Adjust Sonos speaker volume
- Clockwise = louder
- Counter-clockwise = quieter
- Range: 0-100%

**Push:** Toggle white noise loop

**Display:**
```
┌──────────────┐
│    75%       │  ← Large percentage
│  ████░░░░    │  ← Blue progress bar
│   Volume     │  ← Label
└──────────────┘
```

### Dial 1: Playback Scrubbing ⭐ NEW!

**Turn:** Scrub through current track
- Clockwise = skip forward (5 sec per notch)
- Counter-clockwise = rewind (5 sec per notch)
- Automatically clamps at track boundaries

**Push:** Play/Pause toggle
- Playing → Pause
- Paused → Play

**Display:**
```
┌──────────────┐
│  1:23 / 4:56 │  ← Time position
│  ███░░░░░    │  ← Orange progress bar
│      ▶       │  ← Play/pause icon
└──────────────┘
```

### Dial 2: Available

*Not yet assigned - available for future features*

Potential uses:
- Skip to next/previous track
- Adjust bass/treble
- Room grouping controls

### Dial 3: StreamDeck Brightness

**Turn:** Adjust StreamDeck brightness
- Clockwise = brighter
- Counter-clockwise = dimmer
- Range: 0-100%

**Display:** None (silent control)

## Touchscreen Layout

```
┌─────────────┬─────────────┬──────────────────────────────┐
│  Dial 0     │  Dial 1     │     Dials 2 & 3              │
│  Volume     │  Playback   │     Track Info               │
│             │             │                              │
│    75%      │ 1:23 / 4:56 │ How Interest Works           │
│  ████░░░    │ ███░░░░░    │ Million Bazillion            │
│   Volume    │     ▶       │                              │
└─────────────┴─────────────┴──────────────────────────────┘
```

### Display Regions

1. **Dial 0 (Left)**: Volume control with percentage and blue bar
2. **Dial 1 (Center-left)**: Playback position with time and orange bar  
3. **Dials 2 & 3 (Right Half)**: Track info ⭐ NEW!
   - **Line 1**: Track/Episode title (white)
   - **Line 2**: Artist or Podcast name (gray)
   - Auto-truncates long text with ellipsis

### Display Colors

- **Blue** = Volume (dial 0)
- **Orange** = Playback position (dial 1)
- **White** = Track title, time, percentage
- **Light Gray** = Artist/Album info
- **Medium Gray** = Labels (Volume, play icons)
- **Black** = Background

### Auto-Update

The touchscreen updates:
- **Immediately** when you interact with dials
- **Every 2 seconds** to show playback progress & track info
- **Silently** without interrupting playback
- **Smart**: Only fetches data when display needs refresh

## Quick Tips

### Volume Control
- Small adjustment: Turn dial 0 slowly
- Quick mute: Turn dial 0 all the way left
- Check level: Glance at dial 0 display

### Playback Navigation
- Skip ahead 30 sec: Turn dial 1 clockwise 6 times
- Go back 15 sec: Turn dial 1 counter-clockwise 3 times
- Pause quickly: Push dial 1

### White Noise
- Start loop: Press button 0 OR push dial 0
- Stop loop: Press button 0 OR push dial 0 (toggle)
- Adjust volume: Turn dial 0

### Podcasts
- Play episode: Press button 1 or 2
- Scrub within episode: Turn dial 1
- Pause episode: Push dial 1
- Next episode: Press button 1 or 2 again (cycles)

### Brightness
- Too bright?: Turn dial 3 counter-clockwise
- Too dim?: Turn dial 3 clockwise
- No visual feedback - just adjust until comfortable

## Control Philosophy

1. **Dials for continuous values** (volume, position, brightness)
2. **Buttons for discrete actions** (play podcast, toggle loop)
3. **Visual feedback** for important controls (volume, playback)
4. **Silent controls** for secondary functions (brightness)
5. **Intuitive mapping** (physical knob = adjustment)

## All Controls Summary

| Control | Primary Function | Secondary Function |
|---------|------------------|-------------------|
| Button 0 | White noise loop | - |
| Button 1 | Million Bazillion | - |
| Button 2 | Short and Curly | - |
| Dial 0 Turn | Volume | - |
| Dial 0 Push | White noise toggle | - |
| Dial 1 Turn | **Scrub playback** | - |
| Dial 1 Push | **Play/Pause** | - |
| Dial 3 Turn | Brightness | - |

## Console Monitoring

Watch the console for feedback:

```
[Dial 0] volume 50 → 60
[Dial 1] Seeking to 0:01:25 (85s)
[Dial 1] Push: Pause
[Dial 3] brightness 80 → 85
[Deck] Key 1 pressed
[Podcast] Playing million-bazillion idx=0/5
```

## Advanced Features

- **Episode cycling**: Pressing podcast buttons advances through episodes
- **Repeat mode**: White noise automatically loops
- **Smart clamping**: All dials respect min/max limits
- **Error recovery**: Graceful handling of connection issues
- **State preservation**: Podcast episode position remembered

## Future Enhancements

Possible additions:
- Dial 2 for track skip (next/previous)
- Long press for alternative actions
- Visual feedback for dial 3 (brightness indicator)
- Customizable scrub increment (e.g., 10 seconds)
- Room grouping controls
- EQ adjustments
- Sleep timer
- Alarm controls

