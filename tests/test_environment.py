from __future__ import annotations

import os
from pathlib import Path

from cortex_whisper.environment import ydotool_socket_path


def test_configured_socket_wins(monkeypatch, tmp_path):
    socket = tmp_path / ".ydotool_socket"
    monkeypatch.setenv("YDOTOOL_SOCKET", str(socket))
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/1000")

    assert ydotool_socket_path() == socket


def test_runtime_dir_is_used_when_no_socket_is_configured(monkeypatch, tmp_path):
    monkeypatch.delenv("YDOTOOL_SOCKET", raising=False)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))

    assert ydotool_socket_path() == tmp_path / ".ydotool_socket"


def test_socket_path_does_not_crash_without_getuid(monkeypatch):
    """Windows has no os.getuid; the Linux default path must still resolve."""
    monkeypatch.delenv("YDOTOOL_SOCKET", raising=False)
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    monkeypatch.delattr(os, "getuid", raising=False)

    assert ydotool_socket_path() == Path("/run/user/.ydotool_socket")
