"""Cross-platform global hotkey backends."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from .metadata import APP_ID


class HotkeyBackend(Protocol):
    name: str

    def start(self) -> None: ...
    def stop(self) -> None: ...


def pynput_key(name: str):
    from pynput import keyboard

    normalized = name.casefold()
    special = getattr(keyboard.Key, normalized, None)
    return special if special is not None else keyboard.KeyCode.from_char(name)


class PynputHotkey:
    name = "pynput"

    def __init__(self, key_name: str, on_press: Callable[[], None], on_release: Callable[[], None]) -> None:
        self.key_name = key_name
        self.on_press = on_press
        self.on_release = on_release
        self.listener = None
        self._down = False
        self._lock = threading.Lock()

    def start(self) -> None:
        from pynput import keyboard

        target = pynput_key(self.key_name)

        def pressed(key) -> None:
            if key != target:
                return
            with self._lock:
                if self._down:
                    return
                self._down = True
            self.on_press()

        def released(key) -> None:
            if key != target:
                return
            with self._lock:
                if not self._down:
                    return
                self._down = False
            self.on_release()

        self.listener = keyboard.Listener(on_press=pressed, on_release=released)
        self.listener.start()

    def stop(self) -> None:
        if self.listener is not None:
            self.listener.stop()
            self.listener = None


def portal_helper_path() -> Path:
    candidates = []
    if getattr(sys, "_MEIPASS", None):
        candidates.append(Path(sys._MEIPASS) / "cortex_shortcut_portal.py")
    candidates.extend(
        [
            Path(__file__).resolve().parents[2] / "cortex_shortcut_portal.py",
            Path.cwd() / "cortex_shortcut_portal.py",
        ]
    )
    return next((path for path in candidates if path.exists()), candidates[0])


class PortalHotkey:
    name = "xdg-desktop-portal"

    def __init__(
        self,
        key_name: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
        on_error: Callable[[str], None],
    ) -> None:
        self.key_name = key_name
        self.on_press = on_press
        self.on_release = on_release
        self.on_error = on_error
        self.process: subprocess.Popen[str] | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        helper = portal_helper_path()
        python = shutil.which("python3", path="/usr/bin:/bin")
        if not helper.exists() or not python:
            raise RuntimeError("the portal helper or system Python could not be found")
        self.process = subprocess.Popen(
            [
                python,
                "-u",
                str(helper),
                "--trigger",
                self.key_name,
                "--app-id",
                APP_ID,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.thread = threading.Thread(target=self._read, name="portal-hotkey", daemon=True)
        self.thread.start()

    def _read(self) -> None:
        assert self.process is not None and self.process.stdout is not None
        for raw in self.process.stdout:
            line = raw.strip()
            if line == "PRESS":
                self.on_press()
            elif line == "RELEASE":
                self.on_release()
            elif line.startswith("ERROR:"):
                self.on_error(line.removeprefix("ERROR:").strip())
        if self.process.poll() not in {0, None}:
            self.on_error("the global hotkey service stopped unexpectedly")

    def stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
        self.process = None


def create_hotkey_backend(
    key_name: str,
    on_press: Callable[[], None],
    on_release: Callable[[], None],
    on_error: Callable[[str], None],
) -> HotkeyBackend:
    if sys.platform.startswith("linux") and os.environ.get("XDG_SESSION_TYPE", "").casefold() == "wayland":
        return PortalHotkey(key_name, on_press, on_release, on_error)
    return PynputHotkey(key_name, on_press, on_release)
