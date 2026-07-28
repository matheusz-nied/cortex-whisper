"""Operating-system integration for clipboard, paste, and startup."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from .metadata import (
    APP_COMPACT_NAME,
    APP_DESCRIPTION,
    APP_ID,
    APP_NAME,
    LEGACY_APP_ID,
    LEGACY_COMPACT_NAME,
)


def launch_command() -> list[str]:
    if sys.platform.startswith("linux") and os.environ.get("APPIMAGE"):
        return [os.environ["APPIMAGE"]]
    if getattr(sys, "frozen", False):
        return [sys.executable]
    return [sys.executable, str(Path(__file__).resolve().parents[2] / "pulsar_whisper.py")]


def command_string(command: list[str]) -> str:
    if sys.platform == "win32":
        return subprocess.list2cmdline(command)
    return shlex.join(command)


class SystemIntegration:
    def __init__(self) -> None:
        self.platform = "windows" if sys.platform == "win32" else "linux"

    @property
    def paste_backend(self) -> str:
        if self.platform == "windows":
            return "Windows SendInput"
        if shutil.which("ydotool"):
            return "ydotool"
        if os.environ.get("XDG_SESSION_TYPE", "").casefold() != "wayland":
            return "pynput/X11"
        return "clipboard (Ctrl+V manual)"

    def copy_text(self, text: str) -> tuple[bool, str]:
        """Persist text in the native clipboard when Qt alone is insufficient.

        Qt's Wayland clipboard is tied to the GUI process/event loop. ``wl-copy``
        owns the selection independently and proved more reliable on GNOME.
        The controller still fills QClipboard first, so Windows and systems
        without these helpers retain the normal Qt fallback.
        """
        if self.platform != "linux":
            return True, "Qt clipboard"

        command: list[str] | None = None
        backend = "Qt clipboard"
        if os.environ.get("XDG_SESSION_TYPE", "").casefold() == "wayland" and shutil.which("wl-copy"):
            command = ["wl-copy"]
            backend = "wl-copy"
        elif shutil.which("xclip"):
            command = ["xclip", "-selection", "clipboard"]
            backend = "xclip"

        if command is None:
            return True, backend
        try:
            result = subprocess.run(
                command,
                input=text,
                stdout=subprocess.DEVNULL,
                # wl-copy leaves a child process owning the selection. PIPE
                # would wait for its descriptor and cause a false timeout.
                stderr=subprocess.DEVNULL,
                text=True,
                check=False,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, f"{backend}: {exc}"
        if result.returncode == 0:
            return True, backend
        return False, f"{backend}: exit code {result.returncode}"

    def paste(self) -> tuple[bool, str]:
        if self.platform == "linux" and os.environ.get("XDG_SESSION_TYPE", "").casefold() == "wayland":
            if not shutil.which("ydotool"):
                return False, "ydotool is not installed; press Ctrl+V to paste"
            try:
                result = subprocess.run(
                    ["ydotool", "key", "29:1", "47:1", "47:0", "29:0"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=5,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                return False, f"ydotool: {exc}"
            if result.returncode == 0:
                return True, ""
            detail = result.stderr.strip() or result.stdout.strip()
            return False, detail or f"ydotool exited with code {result.returncode}"

        from pynput.keyboard import Controller, Key

        keyboard = Controller()
        with keyboard.pressed(Key.ctrl):
            keyboard.press("v")
            keyboard.release("v")
        return True, ""

    def ensure_application_entry(self) -> None:
        """Register the app ID required by the Wayland GlobalShortcuts portal.

        Debian installs the entry system-wide. AppImage and source checkouts need
        a per-user entry so GNOME can associate the portal request with this app.
        """
        if self.platform != "linux":
            return
        system_entry = Path("/usr/share/applications") / f"{APP_ID}.desktop"
        legacy_user_entry = (
            Path.home() / ".local" / "share" / "applications" / f"{LEGACY_APP_ID}.desktop"
        )
        legacy_user_entry.unlink(missing_ok=True)
        if system_entry.exists():
            return
        user_entry = Path.home() / ".local" / "share" / "applications" / f"{APP_ID}.desktop"
        content = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={APP_NAME}\n"
            f"Comment={APP_DESCRIPTION}\n"
            f"Exec={command_string(launch_command())}\n"
            "Icon=audio-input-microphone-symbolic\n"
            "Terminal=false\n"
            "Categories=Utility;\n"
            "StartupNotify=false\n"
        )
        if user_entry.exists() and user_entry.read_text(encoding="utf-8") == content:
            return
        user_entry.parent.mkdir(parents=True, exist_ok=True)
        user_entry.write_text(content, encoding="utf-8")

    def set_autostart(self, enabled: bool) -> None:
        if self.platform == "windows":
            import winreg

            path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE) as key:
                if enabled:
                    winreg.SetValueEx(
                        key,
                        APP_COMPACT_NAME,
                        0,
                        winreg.REG_SZ,
                        command_string(launch_command()),
                    )
                else:
                    try:
                        winreg.DeleteValue(key, APP_COMPACT_NAME)
                    except FileNotFoundError:
                        pass
                try:
                    winreg.DeleteValue(key, LEGACY_COMPACT_NAME)
                except FileNotFoundError:
                    pass
            return

        desktop = Path.home() / ".config" / "autostart" / f"{APP_ID}.desktop"
        legacy_desktop = desktop.with_name(f"{LEGACY_APP_ID}.desktop")
        if not enabled:
            desktop.unlink(missing_ok=True)
            legacy_desktop.unlink(missing_ok=True)
            return
        desktop.parent.mkdir(parents=True, exist_ok=True)
        desktop.write_text(
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={APP_NAME}\n"
            f"Exec={command_string(launch_command())}\n"
            "Icon=audio-input-microphone-symbolic\n"
            "Terminal=false\n"
            "X-GNOME-Autostart-enabled=true\n",
            encoding="utf-8",
        )
        legacy_desktop.unlink(missing_ok=True)
