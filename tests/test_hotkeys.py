from typing import Any

from cortex_whisper.hotkeys import PortalHotkey
from cortex_whisper.metadata import APP_ID
from cortex_whisper.portals import (
    REGISTRY_INTERFACE,
    SESSION_INTERFACE,
    SHORTCUTS_INTERFACE,
    unwrap_variants,
)


class FakePortalConnection:
    sender_name = "1_99"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, list[Any], str]] = []
        self.responses: list[tuple[str, Any]] = []
        self.activated = None
        self.deactivated = None
        self.cleared = False

    def call(self, interface, method, signature, arguments, path="/org/freedesktop/portal/desktop"):
        self.calls.append((interface, method, signature, arguments, path))
        return []

    def subscribe_response(self, path, callback):
        self.responses.append((path, callback))

    def subscribe_shortcuts(self, activated, deactivated):
        self.activated = activated
        self.deactivated = deactivated

    def clear(self):
        self.cleared = True


def assert_dbus_variants(options):
    """Every value of an a{sv} must carry its own signature, or the portal
    answers "Expected type 's' for option ...".
    """
    for key, value in options.items():
        assert isinstance(value, tuple) and len(value) == 2, f"{key} must be a (signature, value) tuple"
        assert isinstance(value[0], str), f"{key} must declare a D-Bus signature"


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

    assert connection.calls[0][:4] == (REGISTRY_INTERFACE, "Register", "sa{sv}", [APP_ID, {}])
    assert connection.calls[1][0:3] == (SHORTCUTS_INTERFACE, "CreateSession", "a{sv}")
    assert_dbus_variants(connection.calls[1][3][0])
    assert len(connection.responses) == 1
    connection.responses.pop(0)[1](0, {"session_handle": "/session/1"})
    bind = connection.calls[-1]
    assert bind[0:3] == (SHORTCUTS_INTERFACE, "BindShortcuts", "oa(sa{sv})sa{sv}")
    assert bind[3][0] == "/session/1"
    shortcut_id, properties = bind[3][1][0]
    assert shortcut_id == hotkey.shortcut_id
    assert unwrap_variants(properties)["preferred_trigger"] == "F8"
    assert_dbus_variants(properties)
    assert_dbus_variants(bind[3][3])
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
    assert connection.calls[0][0:3] == (SHORTCUTS_INTERFACE, "CreateSession", "a{sv}")


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
    connection.responses[0][1](0, {"session_handle": "/session/1"})

    hotkey.stop()

    assert (SESSION_INTERFACE, "Close", "", [], "/session/1") in connection.calls
    assert connection.cleared is True


def test_unwrap_variants_strips_the_signature_of_each_value():
    values = {"session_handle": ("o", "/session/1"), "shortcuts": ("a(sa{sv})", [("hold", {})])}

    assert unwrap_variants(values) == {"session_handle": "/session/1", "shortcuts": [("hold", {})]}
