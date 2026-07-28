#!/usr/bin/python3
"""Expose portal global-shortcut events as lines on stdout.

This helper runs with system Python, which provides dbus-python and PyGObject.
The main application continues to use the project's virtual environment.
"""

from __future__ import annotations

import argparse
import signal
import sys
import uuid

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

BUS_NAME = "org.freedesktop.portal.Desktop"
OBJECT_PATH = "/org/freedesktop/portal/desktop"
SHORTCUTS_INTERFACE = "org.freedesktop.portal.GlobalShortcuts"
REGISTRY_INTERFACE = "org.freedesktop.host.portal.Registry"
REQUEST_INTERFACE = "org.freedesktop.portal.Request"
SESSION_INTERFACE = "org.freedesktop.portal.Session"
SHORTCUT_ID = "pulsar_whisper_hold_to_talk"


def emit(message: str) -> None:
    print(message, flush=True)


class GlobalShortcut:
    def __init__(self, trigger: str, app_id: str) -> None:
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        portal_object = self.bus.get_object(BUS_NAME, OBJECT_PATH)
        self.portal = dbus.Interface(portal_object, SHORTCUTS_INTERFACE)
        self.registry = dbus.Interface(portal_object, REGISTRY_INTERFACE)
        self.loop = GLib.MainLoop()
        self.session_handle: str | None = None
        self.finished = False
        self.trigger = trigger
        self.app_id = app_id

        unique_name = self.bus.get_unique_name().lstrip(":")
        self.sender_name = unique_name.replace(".", "_")

        self.bus.add_signal_receiver(
            self.on_activated,
            signal_name="Activated",
            dbus_interface=SHORTCUTS_INTERFACE,
            path=OBJECT_PATH,
        )
        self.bus.add_signal_receiver(
            self.on_deactivated,
            signal_name="Deactivated",
            dbus_interface=SHORTCUTS_INTERFACE,
            path=OBJECT_PATH,
        )

    def token(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex}"

    def request_path(self, token: str) -> str:
        return f"{OBJECT_PATH}/request/{self.sender_name}/{token}"

    def listen_for_response(self, path: str, callback) -> None:
        self.bus.add_signal_receiver(
            callback,
            signal_name="Response",
            dbus_interface=REQUEST_INTERFACE,
            path=path,
        )

    def start(self) -> None:
        # Directly executed Python processes do not receive a GNOME App ID. The
        # Registry associates this connection with the locally installed desktop file.
        self.registry.Register(
            dbus.String(self.app_id),
            dbus.Dictionary({}, signature="sv"),
        )

        request_token = self.token("create")
        session_token = self.token("session")
        expected_path = self.request_path(request_token)
        self.listen_for_response(expected_path, self.on_session_created)

        options = dbus.Dictionary(
            {
                "handle_token": dbus.String(request_token),
                "session_handle_token": dbus.String(session_token),
            },
            signature="sv",
        )
        self.portal.CreateSession(options)
        self.loop.run()

    def on_session_created(self, response, results) -> None:
        if int(response) != 0:
            self.fail(f"session creation was denied (code {int(response)})")
            return

        self.session_handle = str(results["session_handle"])
        request_token = self.token("bind")
        expected_path = self.request_path(request_token)
        self.listen_for_response(expected_path, self.on_shortcut_bound)

        properties = dbus.Dictionary(
            {
                "description": dbus.String("Hold to dictate"),
                "preferred_trigger": dbus.String(self.trigger),
            },
            signature="sv",
        )
        shortcuts = dbus.Array(
            [dbus.Struct((dbus.String(SHORTCUT_ID), properties))],
            signature="(sa{sv})",
        )
        options = dbus.Dictionary(
            {"handle_token": dbus.String(request_token)},
            signature="sv",
        )

        self.portal.BindShortcuts(
            dbus.ObjectPath(self.session_handle),
            shortcuts,
            dbus.String(""),
            options,
        )

    def on_shortcut_bound(self, response, results) -> None:
        if int(response) != 0:
            self.fail(f"shortcut {self.trigger} was denied (code {int(response)})")
            return

        shortcuts = results.get("shortcuts", [])
        if not any(str(shortcut[0]) == SHORTCUT_ID for shortcut in shortcuts):
            self.fail("no shortcut was authorized")
            return
        emit("READY")

    def event_is_ours(self, session_handle, shortcut_id) -> bool:
        return (
            self.session_handle is not None
            and str(session_handle) == self.session_handle
            and str(shortcut_id) == SHORTCUT_ID
        )

    def on_activated(self, session_handle, shortcut_id, timestamp, options) -> None:
        del timestamp, options
        if self.event_is_ours(session_handle, shortcut_id):
            emit("PRESS")

    def on_deactivated(self, session_handle, shortcut_id, timestamp, options) -> None:
        del timestamp, options
        if self.event_is_ours(session_handle, shortcut_id):
            emit("RELEASE")

    def close(self) -> None:
        if self.finished:
            return
        self.finished = True
        if self.session_handle:
            try:
                session_object = self.bus.get_object(BUS_NAME, self.session_handle)
                dbus.Interface(session_object, SESSION_INTERFACE).Close()
            except Exception:
                pass
        if self.loop.is_running():
            self.loop.quit()

    def fail(self, message: str) -> None:
        emit(f"ERROR: {message}")
        self.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trigger", default="F8")
    parser.add_argument("--app-id", required=True)
    args = parser.parse_args()
    try:
        shortcut = GlobalShortcut(args.trigger, args.app_id)
        signal.signal(signal.SIGTERM, lambda *_: shortcut.close())
        signal.signal(signal.SIGINT, lambda *_: shortcut.close())
        shortcut.start()
        return 0
    except Exception as exc:
        emit(f"ERROR: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
