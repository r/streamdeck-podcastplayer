#!/usr/bin/env python3
"""
Stream Deck UI rendering functions.
"""
from __future__ import annotations

import os
import io
import time
from typing import Any, Callable, Optional

from PIL import Image, ImageDraw, ImageFont

from podplayer.utils import log, format_time


# Cached fonts (loaded once at startup)
font_large: Any = None
font_medium: Any = None
font_label: Any = None
font_bold: Any = None
font_small: Any = None


def load_fonts(script_dir: str) -> None:
    """Load fonts once at startup and cache them."""
    global font_large, font_medium, font_label, font_bold, font_small

    # Fonts are bundled with the package in podplayer/fonts/
    package_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(package_dir, "fonts", "Helvetica.ttf")
    font_bold_path = os.path.join(package_dir, "fonts", "Helvetica-Bold.ttf")
    try:
        font_large = ImageFont.truetype(font_path, 28)
        font_medium = ImageFont.truetype(font_path, 22)
        font_label = ImageFont.truetype(font_path, 22)
        font_bold = ImageFont.truetype(font_bold_path, 22)
        font_small = ImageFont.truetype(font_path, 16)  # Bigger description font
    except Exception as e:
        log(f"Font loading error: {e}, using defaults")
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_label = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_small = ImageFont.load_default()

    log("Fonts loaded")


def set_key_image(deck_obj: Any, key: int, filename: str) -> None:
    """
    Set a JPEG icon on a key. Your Stream Deck+ reports key_image_format()
    as JPEG with size (120, 120).
    """
    if not os.path.exists(filename):
        log(f"[Icon] Not found: {filename}")
        return

    icon = Image.open(filename).convert("RGB")

    fmt = deck_obj.key_image_format()
    key_w, key_h = fmt["size"]

    # Use LANCZOS for Pillow < 10.0, Resampling.LANCZOS for >= 10.0
    try:
        icon = icon.resize((key_w, key_h), Image.Resampling.LANCZOS)  # type: ignore
    except AttributeError:
        icon = icon.resize((key_w, key_h), Image.LANCZOS)  # type: ignore

    buffer = io.BytesIO()
    icon.save(buffer, format="JPEG")
    jpeg_bytes = buffer.getvalue()

    deck_obj.set_key_image(key, jpeg_bytes)


def update_touchscreen_ui(
    deck_obj: Any,
    speaker: Any,
    podcasts: dict[str, Any],
    pending_volume: Optional[int],
    pending_scrub_position: Optional[int],
    get_playback_info_func: Callable[[], dict[str, Any]],
    detect_podcast_func: Callable[[], Optional[str]],
    get_metadata_func: Callable[[str], dict[str, str]],
    testing_mode: bool = False,
) -> None:
    """
    Update the entire touchscreen with volume (dial 0) and playback (dial 1) displays.

    Args:
        deck_obj: Stream Deck device
        speaker: Sonos speaker object
        podcasts: Podcast configuration dict
        pending_volume: Pending volume value (for immediate display)
        pending_scrub_position: Pending scrub position (for immediate display)
        get_playback_info_func: Function to get current playback info
        detect_podcast_func: Function to detect current podcast
        get_metadata_func: Function to get episode metadata
        testing_mode: Whether to enable timing logs
    """
    start_time: float = time.time() if testing_mode else 0.0
    global font_large, font_medium, font_label, font_bold, font_small

    if not hasattr(deck_obj, "touchscreen_image_format") or not hasattr(
        deck_obj, "set_touchscreen_image"
    ):
        return

    try:
        fmt = deck_obj.touchscreen_image_format()
    except Exception as e:
        return

    w, h = fmt.get("size", (800, 100))
    img = Image.new("RGB", (w, h), "black")
    draw = ImageDraw.Draw(img)

    if testing_mode:
        log(f"  Display setup took {(time.time() - start_time)*1000:.1f}ms")

    dial_count = 4
    region_w = w // dial_count
    margin = 10
    track_height = 18
    track_y = h // 2 + 5

    # ===== DIAL 0: VOLUME =====
    x0 = 0
    track_x0 = x0 + margin
    track_x1 = (x0 + region_w) - margin

    # Volume track background
    draw.rectangle(
        [track_x0, track_y, track_x1, track_y + track_height],
        outline=(80, 80, 80),
        width=2,
        fill=(30, 30, 30),
    )

    # Volume fill
    try:
        # Use pending volume if available (for immediate display update), otherwise use actual
        if pending_volume is not None:
            volume = pending_volume
        else:
            volume = speaker.volume
        vol_pct = max(0, min(100, int(volume)))
        fill_w = (track_x1 - track_x0) * vol_pct // 100
        if fill_w > 0:
            draw.rectangle(
                [track_x0, track_y, track_x0 + fill_w, track_y + track_height],
                fill=(0, 180, 255),
            )

        # Volume percentage
        vol_text = f"{vol_pct}%"
        vol_bbox = draw.textbbox((0, 0), vol_text, font=font_large)
        vol_text_w = vol_bbox[2] - vol_bbox[0]
        vol_text_x = x0 + (region_w - vol_text_w) // 2
        draw.text((vol_text_x, 8), vol_text, fill=(255, 255, 255), font=font_large)

        # Volume label
        label_text = "Volume"
        label_bbox = draw.textbbox((0, 0), label_text, font=font_label)
        label_text_w = label_bbox[2] - label_bbox[0]
        label_text_x = x0 + (region_w - label_text_w) // 2
        draw.text(
            (label_text_x, track_y + track_height + 4),
            label_text,
            fill=(150, 150, 150),
            font=font_label,
        )
    except:
        pass

    # ===== DIAL 1: PLAYBACK SCRUBBING =====
    x1 = region_w
    track_x0_pb = x1 + margin
    track_x1_pb = (x1 + region_w) - margin

    # Playback track background
    draw.rectangle(
        [track_x0_pb, track_y, track_x1_pb, track_y + track_height],
        outline=(80, 80, 80),
        width=2,
        fill=(30, 30, 30),
    )

    # Get playback info
    checkpoint: float = time.time() if testing_mode else 0.0
    playback = get_playback_info_func()
    if testing_mode:
        log(f"  get_playback_info took {(time.time() - checkpoint)*1000:.1f}ms")

    # Use pending scrub position if available (for immediate display update), otherwise use actual
    if pending_scrub_position is not None:
        position = pending_scrub_position
    else:
        position = playback["position"]
    duration = playback["duration"]
    state = playback["state"]
    title = playback["title"]
    uri = playback.get("uri", "")

    if testing_mode:
        log(f"  Playback: title='{title}', uri='{uri}'")

    # Playback fill
    if duration > 0:
        progress_pct = min(100, int((position / duration) * 100))
        fill_w_pb = (track_x1_pb - track_x0_pb) * progress_pct // 100
        if fill_w_pb > 0:
            # Blue color for playback (matches volume bar)
            draw.rectangle(
                [track_x0_pb, track_y, track_x0_pb + fill_w_pb, track_y + track_height],
                fill=(0, 180, 255),
            )

    # Time display
    time_text = f"{format_time(position)} / {format_time(duration)}"
    time_bbox = draw.textbbox((0, 0), time_text, font=font_medium)
    time_text_w = time_bbox[2] - time_bbox[0]
    time_text_x = x1 + (region_w - time_text_w) // 2
    draw.text((time_text_x, 10), time_text, fill=(255, 255, 255), font=font_medium)

    # Playback label (shows state: Playing or Paused)
    if state == "PLAYING":
        label_text = "Playing"
    elif state == "PAUSED_PLAYBACK":
        label_text = "Paused"
    else:
        label_text = "Stopped"
    label_bbox = draw.textbbox((0, 0), label_text, font=font_label)
    label_text_w = label_bbox[2] - label_bbox[0]
    label_text_x = x1 + (region_w - label_text_w) // 2
    draw.text(
        (label_text_x, track_y + track_height + 4),
        label_text,
        fill=(150, 150, 150),
        font=font_label,
    )

    # ===== DIALS 2 & 3: TRACK INFO (Title & Description) =====
    # This covers the right half of the screen (dials 2 and 3)
    x_info_start = region_w * 2
    info_width = region_w * 2
    info_margin = 8

    # Truncate title to fit in available space
    def truncate_text(text, font, max_width):
        """Truncate text to fit within max_width, adding ellipsis if needed."""
        if not text:
            return ""

        # Limit text length before processing (descriptions can be very long)
        # Assume ~10 pixels per character as rough estimate
        max_chars = int(max_width / 5)  # Conservative estimate
        if len(text) > max_chars:
            text = text[:max_chars]

        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        if text_w <= max_width:
            return text

        # Binary search for the right length (much faster than linear)
        left, right = 0, len(text)
        best = ""

        while left <= right:
            mid = (left + right) // 2
            truncated = text[:mid] + "..."
            bbox = draw.textbbox((0, 0), truncated, font=font)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                best = truncated
                left = mid + 1
            else:
                right = mid - 1

        return best if best else "..."

    # Check if this is a podcast episode (even if title is empty)
    current_slug = detect_podcast_func()

    if testing_mode:
        log(f"  detect_current_podcast returned: {current_slug}, uri={uri}")

    show_name = None
    episode_title = title
    episode_description = ""

    # Draw track/episode info
    # For podcasts, always show info even if Sonos title is empty
    if current_slug and current_slug in podcasts:
        # This is a podcast - show name first, then episode title, then description
        show_name = podcasts[current_slug].get("name", current_slug)

        # Get episode metadata from database (use uri from playback info we already have)
        metadata = get_metadata_func(uri)
        if metadata:
            # Use metadata title if available (more accurate than Sonos title)
            if metadata.get("title"):
                episode_title = metadata["title"]
            if metadata.get("description"):
                episode_description = metadata["description"]

        # Ensure we have something to display
        if not episode_title:
            episode_title = "Episode"  # Fallback

    # Draw if we have podcast info OR a title from Sonos
    if show_name or (title and title != "No track"):
        title_x = x_info_start + info_margin
        title_y = 8

        if show_name:
            # Podcast: Show name (bold) on first line, episode title on second, description on third
            show_display = truncate_text(show_name, font_bold, info_width - info_margin * 2)
            draw.text((title_x, title_y), show_display, fill=(255, 255, 255), font=font_bold)

            # Always show episode title (from metadata if available, otherwise from Sonos)
            if not episode_title or episode_title == "No track":
                episode_title = title  # Fallback to Sonos title

            episode_display = truncate_text(
                episode_title, font_medium, info_width - info_margin * 2
            )
            episode_y = title_y + 22
            draw.text((title_x, episode_y), episode_display, fill=(220, 220, 220), font=font_medium)

            # Third and fourth lines: episode description (two lines if we have it)
            if episode_description:
                desc_y = episode_y + 20

                # Split description into two lines for better readability
                # First line
                desc_line1 = truncate_text(
                    episode_description, font_small, info_width - info_margin * 2
                )
                draw.text((title_x, desc_y), desc_line1, fill=(200, 200, 200), font=font_small)

                # Second line (continue from where first line ended)
                if len(episode_description) > len(desc_line1) - 3:  # Has more text beyond line 1
                    # Calculate where first line ended (roughly)
                    remaining_desc = episode_description[
                        len(desc_line1) - 3 :
                    ]  # Skip the "..." if present
                    if remaining_desc and not desc_line1.endswith("..."):
                        remaining_desc = episode_description[len(desc_line1) :]

                    if remaining_desc and len(remaining_desc) > 3:
                        desc_line2 = truncate_text(
                            remaining_desc, font_small, info_width - info_margin * 2
                        )
                        desc_y2 = desc_y + 16
                        draw.text(
                            (title_x, desc_y2), desc_line2, fill=(200, 200, 200), font=font_small
                        )
        else:
            # Not a podcast: Show title, then artist/album if available
            title_display = truncate_text(title, font_medium, info_width - info_margin * 2)
            draw.text((title_x, title_y), title_display, fill=(255, 255, 255), font=font_medium)

            # Skip artist/album for now - it requires network calls
            # We can add this back later with proper caching

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    touchscreen_bytes = buf.getvalue()

    try:
        deck_obj.set_touchscreen_image(touchscreen_bytes, 0, 0, w, h)
    except Exception as e:
        pass

    if testing_mode:
        log(f"Display updated (total: {(time.time() - start_time)*1000:.1f}ms)")


def update_volume_ui(
    deck_obj: Any,
    volume: int,
    speaker: Any,
    podcasts: dict[str, Any],
    pending_volume: Optional[int],
    pending_scrub_position: Optional[int],
    get_playback_info_func: Callable[[], dict[str, Any]],
    detect_podcast_func: Callable[[], Optional[str]],
    get_metadata_func: Callable[[str], dict[str, str]],
    testing_mode: bool = False,
) -> None:
    """Update the touchscreen (includes both volume and playback)."""
    update_touchscreen_ui(
        deck_obj,
        speaker,
        podcasts,
        pending_volume,
        pending_scrub_position,
        get_playback_info_func,
        detect_podcast_func,
        get_metadata_func,
        testing_mode,
    )
