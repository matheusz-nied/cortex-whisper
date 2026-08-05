from typing import Any

from PySide6.QtDBus import QDBusObjectPath, QDBusVariant

from cortex_whisper.hotkeys import PortalHotkey
from cortex_whisper.metadata import APP_ID
from cortex_whisper.portals import (
    REGISTRY_INTERFACE,
    SESSION_INTERFACE,
    SHORTCUTS_INTERFACE,
    unwrap_dbus,
)


class FakePortalConnection:
    sender_name = "1_99"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, list[Any], str]] = []
        self.responses: list[tuple[str, Any]] = []
        self.activated = None
        self.deactivated = None
        self.cleared = False

    def call(self, interface, method, arguments, path="/org/freedesktop/portal/desktop"):
        self.calls.append((interface, method, arguments, path))
        return []

    def subscribe_response(self, path, callback):
        self.responses.append((path, callback))

    def subscribe_shortcuts(self, activated, deactivated):
        self.activated = activated
        self.deactivated = deactivated

    def clear(self):
        self.cleared = True


def make_hotkey(connection, events, errors):
    return PortalHotkey(
        "F8",
        lambda: events.append("pressed"),
        lambda: events.append("released"),
        errors.append,
        connection,
    )


def test_native_portal_registers_app_and_binds_shortcut(monkeypatch):
    monkeypatch.delenv("FLATPAK_ID", raising=False)
    connection = FakePortalConnection()
    events: list[str] = []
    errors: list[str] = []
    hotkey = make_hotkey(connection, events, errors)

    hotkey.start()

    assert connection.calls[0][:3] == (REGISTRY_INTERFACE, "Register", [APP_ID, {}])
    assert connection.calls[1][0:2] == (SHORTCUTS_INTERFACE, "CreateSession")
    assert len(connection.responses) == 1
    connection.responses.pop(0)[1](0, {"session_handle": "/session/1"})
    bind = connection.calls[-1]
    assert bind[0:2] == (SHORTCUTS_INTERFACE, "BindShortcuts")
    assert bind[2][0].path() == "/session/1"
    shortcut_id, properties = bind[2][1][0]
    assert shortcut_id == hotkey.shortcut_id
    assert unwrap_dbus(properties)["preferred_trigger"] == "F8"
    connection.responses.pop(0)[1](0, {"shortcuts": [(hotkey.shortcut_id, {})]})
    connection.activated("/session/1", hotkey.shortcut_id)
    connection.deactivated("/session/1", hotkey.shortcut_id)
    assert events == ["pressed", "released"]
    assert errors == []


def test_flatpak_skips_host_registry(monkeypatch):
    monkeypatch.setenv("FLATPAK_ID", APP_ID)
    connection = FakePortalConnection()
    hotkey = make_hotkey(connection, [], [])

    hotkey.start()

    assert all(call[0] != REGISTRY_INTERFACE for call in connection.calls)
    assert connection.calls[0][0:2] == (SHORTCUTS_INTERFACE, "CreateSession")


def test_portal_denial_reports_error(monkeypatch):
    monkeypatch.setenv("FLATPAK_ID", APP_ID)
    connection = FakePortalConnection()
    errors: list[str] = []
    hotkey = make_hotkey(connection, [], errors)
    hotkey.start()

    connection.responses[0][1](1, {})

    assert errors == ["session creation was denied (code 1)"]


def test_stop_closes_session(monkeypatch):
    monkeypatch.setenv("FLATPAK_ID", APP_ID)
    connection = FakePortalConnection()
    hotkey = make_hotkey(connection, [], [])
    hotkey.start()
    connection.responses[0][1](0, {"session_handle": QDBusObjectPath("/session/1")})

    hotkey.stop()

    assert (SESSION_INTERFACE, "Close", [], "/session/1") in connection.calls
    assert connection.cleared is True


def test_unwrap_dbus_recursively_unwraps_values():
    value = {"handle": QDBusVariant(QDBusObjectPath("/session/1")), "items": (QDBusVariant("ok"),)}

    assert unwrap_dbus(value) == {"handle": "/session/1", "items": ["ok"]}
