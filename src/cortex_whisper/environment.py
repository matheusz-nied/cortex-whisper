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
    # os.getuid() only exists on POSIX; on Windows there is no ydotool socket,
    # so return a path that simply never resolves instead of crashing.
    if hasattr(os, "getuid"):
        return Path(f"/run/user/{os.getuid()}/.ydotool_socket")
    return Path("/run/user/.ydotool_socket")
