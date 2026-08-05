"""Cross-platform global hotkey backends."""

from __future__ import annotations

import os
import sys
import threading
from collections.abc import Callable
from typing import Any, Protocol

from PySide6.QtDBus import QDBusObjectPath, QDBusVariant

from .environment import is_flatpak
from .metadata import APP_ID
from .portals import (
    REGISTRY_INTERFACE,
    SESSION_INTERFACE,
    SHORTCUTS_INTERFACE,
    PortalConnection,
    QtPortalConnection,
    expected_request_path,
    request_token,
)


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


class PortalHotkey:
    name = "xdg-desktop-portal"
    shortcut_id = "cortex_whisper_hold_to_talk"

    def __init__(
        self,
        key_name: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
        on_error: Callable[[str], None],
        connection: PortalConnection | None = None,
    ) -> None:
        self.key_name = key_name
        self.on_press = on_press
        self.on_release = on_release
        self.on_error = on_error
        self.connection = connection
        self.session_handle: str | None = None
        self.started = False

    def start(self) -> None:
        try:
            self.connection = self.connection or QtPortalConnection()
            if not is_flatpak():
                self.connection.call(
                    REGISTRY_INTERFACE,
                    "Register",
                    [APP_ID, {}],
                )
            self.connection.subscribe_shortcuts(self._activated, self._deactivated)
            token = request_token("create")
            session_token = request_token("session")
            path = expected_request_path(self.connection, token)
            self.connection.subscribe_response(path, self._session_created)
            options = {
                "handle_token": QDBusVariant(token),
                "session_handle_token": QDBusVariant(session_token),
            }
            self.connection.call(SHORTCUTS_INTERFACE, "CreateSession", [options])
            self.started = True
        except Exception as exc:
            self._fail(str(exc))

    def _session_created(self, response: int, results: dict[str, Any]) -> None:
        if response != 0:
            self._fail(f"session creation was denied (code {response})")
            return
        handle = results.get("session_handle")
        self.session_handle = handle.path() if isinstance(handle, QDBusObjectPath) else str(handle or "")
        if not self.session_handle:
            self._fail("the portal returned no shortcut session")
            return
        assert self.connection is not None
        token = request_token("bind")
        path = expected_request_path(self.connection, token)
        self.connection.subscribe_response(path, self._shortcut_bound)
        properties = {
            "description": QDBusVariant("Hold to dictate"),
            "preferred_trigger": QDBusVariant(self.key_name),
        }
        shortcuts = [(self.shortcut_id, properties)]
        options = {"handle_token": QDBusVariant(token)}
        try:
            self.connection.call(
                SHORTCUTS_INTERFACE,
                "BindShortcuts",
                [QDBusObjectPath(self.session_handle), shortcuts, "", options],
            )
        except Exception as exc:
            self._fail(str(exc))

    def _shortcut_bound(self, response: int, results: dict[str, Any]) -> None:
        if response != 0:
            self._fail(f"shortcut {self.key_name} was denied (code {response})")
            return
        shortcuts = results.get("shortcuts", [])
        if shortcuts and not any(str(shortcut[0]) == self.shortcut_id for shortcut in shortcuts):
            self._fail("no shortcut was authorized")

    def _activated(self, session_handle: str, shortcut_id: str) -> None:
        if session_handle == self.session_handle and shortcut_id == self.shortcut_id:
            self.on_press()

    def _deactivated(self, session_handle: str, shortcut_id: str) -> None:
        if session_handle == self.session_handle and shortcut_id == self.shortcut_id:
            self.on_release()

    def _fail(self, message: str) -> None:
        self.on_error(message)

    def stop(self) -> None:
        if self.connection and self.session_handle:
            try:
                self.connection.call(SESSION_INTERFACE, "Close", [], path=self.session_handle)
            except Exception:
                pass
        if self.connection:
            self.connection.clear()
        self.session_handle = None
        self.started = False


def create_hotkey_backend(
    key_name: str,
    on_press: Callable[[], None],
    on_release: Callable[[], None],
    on_error: Callable[[str], None],
) -> HotkeyBackend:
    if sys.platform.startswith("linux") and os.environ.get("XDG_SESSION_TYPE", "").casefold() == "wayland":
        return PortalHotkey(key_name, on_press, on_release, on_error)
    return PynputHotkey(key_name, on_press, on_release)
