"""Runtime environment helpers shared by desktop integrations."""

from __future__ import annotations

import os
from pathlib import Path

from .metadata import APP_ID


def is_flatpak() -> bool:
    return os.environ.get("FLATPAK_ID") == APP_ID


def ydotool_socket_path() -> Path:
    configured = os.environ.get("YDOTOOL_SOCKET")
    if configured:
        return Path(configured)
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if runtime:
        return Path(runtime) / ".ydotool_socket"
    return Path(f"/run/user/{os.getuid()}/.ydotool_socket")
