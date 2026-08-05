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
    integration = SystemIntegration()
    integration.platform = "linux"
    copied, backend = integration.copy_text("Hello ")

    assert copied is True
    assert backend == "wl-copy"
    assert called == {"command": ["wl-copy"], "input": "Hello "}


def test_ydotool_timeout_becomes_a_visible_error(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setattr("cortex_whisper.integration.shutil.which", lambda _name: "/usr/bin/ydotool")

    def run(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("ydotool", 5)

    monkeypatch.setattr("cortex_whisper.integration.subprocess.run", run)
    integration = SystemIntegration()
    integration.platform = "linux"
    pasted, error = integration.paste()

    assert pasted is False
    assert "ydotool" in error


def test_flatpak_uses_qt_clipboard_without_host_clipboard_tools(monkeypatch):
    monkeypatch.setenv("FLATPAK_ID", "io.github.matheusz_nied.CortexWhisper")
    monkeypatch.setattr(
        "cortex_whisper.integration.subprocess.run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    integration = SystemIntegration()
    integration.platform = "linux"
    integration.flatpak = True

    assert integration.copy_text("Hello") == (True, "Qt clipboard")


def test_flatpak_without_ydotool_socket_keeps_manual_paste_fallback(monkeypatch, tmp_path):
    socket = tmp_path / ".ydotool_socket"
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("YDOTOOL_SOCKET", str(socket))
    monkeypatch.setattr("cortex_whisper.integration.shutil.which", lambda _name: "/app/bin/ydotool")

    integration = SystemIntegration()
    integration.platform = "linux"
    integration.flatpak = True
    pasted, error = integration.paste()

    assert pasted is False
    assert "press Ctrl+V" in error


def test_flatpak_passes_the_exact_ydotool_socket(monkeypatch, tmp_path):
    socket = tmp_path / ".ydotool_socket"
    socket.touch()
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("YDOTOOL_SOCKET", str(socket))
    monkeypatch.setattr("cortex_whisper.integration.shutil.which", lambda _name: "/app/bin/ydotool")
    called = {}

    def run(command, **kwargs):
        called["command"] = command
        called["socket"] = kwargs["env"]["YDOTOOL_SOCKET"]
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr("cortex_whisper.integration.subprocess.run", run)
    integration = SystemIntegration()
    integration.platform = "linux"
    integration.flatpak = True

    assert integration.paste() == (True, "")
    assert called["command"] == ["ydotool", "key", "29:1", "47:1", "47:0", "29:0"]
    assert called["socket"] == str(socket)
