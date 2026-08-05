from __future__ import annotations

import subprocess
from types import SimpleNamespace

from cortex_whisper.integration import SystemIntegration


def test_wayland_copy_uses_wl_copy(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setattr("cortex_whisper.integration.shutil.which", lambda name: f"/usr/bin/{name}")
    called = {}

    def run(command, **kwargs):
        called["command"] = command
        called["input"] = kwargs["input"]
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr("cortex_whisper.integration.subprocess.run", run)
    copied, backend = SystemIntegration().copy_text("Hello ")

    assert copied is True
    assert backend == "wl-copy"
    assert called == {"command": ["wl-copy"], "input": "Hello "}


def test_ydotool_timeout_becomes_a_visible_error(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setattr("cortex_whisper.integration.shutil.which", lambda _name: "/usr/bin/ydotool")

    def run(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("ydotool", 5)

    monkeypatch.setattr("cortex_whisper.integration.subprocess.run", run)
    pasted, error = SystemIntegration().paste()

    assert pasted is False
    assert "ydotool" in error
