#!/usr/bin/env python3
"""
Utility functions for the Sonos Stream Deck controller.
"""
from __future__ import annotations

import socket
from datetime import datetime


def log(message: str) -> None:
    """Print with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")


def get_ip() -> str:
    """Best-effort local IP for building the Sonos URL."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip: str = s.getsockname()[0]
    except OSError:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def format_time(seconds: int) -> str:
    """Format seconds as MM:SS."""
    if seconds < 0:
        return "0:00"
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins}:{secs:02d}"
