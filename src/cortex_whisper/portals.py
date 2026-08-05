"""D-Bus clients for XDG desktop portals.

The transport is jeepney rather than QtDBus. ``GlobalShortcuts.BindShortcuts``
expects ``a(sa{sv})``, and PySide6 cannot marshal D-Bus structs: the element
type of an array has to be registered with ``qDBusRegisterMetaType``, a C++
template that the bindings do not expose.

Values inside an ``a{sv}`` are variants, which jeepney writes as a
``(signature, value)`` tuple -- ``("s", token)``, ``("b", True)``.
"""

from __future__ import annotations

import queue
import threading
import uuid
from collections.abc import Callable
from typing import Any, Protocol

from jeepney import (
    DBusAddress,
    HeaderFields,
    MatchRule,
    MessageType,
    new_method_call,
)
from jeepney.bus_messages import message_bus
from jeepney.io.threading import DBusRouter, open_dbus_connection
from PySide6.QtCore import QObject, Qt, Signal, Slot

BUS_NAME = "org.freedesktop.portal.Desktop"
OBJECT_PATH = "/org/freedesktop/portal/desktop"
REQUEST_INTERFACE = "org.freedesktop.portal.Request"
SESSION_INTERFACE = "org.freedesktop.portal.Session"
SHORTCUTS_INTERFACE = "org.freedesktop.portal.GlobalShortcuts"
REGISTRY_INTERFACE = "org.freedesktop.host.portal.Registry"
BACKGROUND_INTERFACE = "org.freedesktop.portal.Background"
CALL_TIMEOUT = 5.0


def unwrap_variants(values: dict[str, Any]) -> dict[str, Any]:
    """Drop the ``(signature, value)`` wrapper from the values of an a{sv}."""
    return {
        str(key): value[1] if isinstance(value, tuple) and len(value) == 2 else value
        for key, value in values.items()
    }


class PortalConnection(Protocol):
    @property
    def sender_name(self) -> str: ...

    def call(
        self,
        interface: str,
        method: str,
        signature: str,
        arguments: list[Any],
        path: str = OBJECT_PATH,
    ) -> list[Any]: ...

    def subscribe_response(self, path: str, callback: Callable[[int, dict[str, Any]], None]) -> None: ...

    def subscribe_shortcuts(
        self,
        activated: Callable[[str, str], None],
        deactivated: Callable[[str, str], None],
    ) -> None: ...

    def clear(self) -> None: ...


class PortalBusConnection(QObject):
    """A private session-bus connection for portal conversations.

    jeepney reads the socket on its own thread. The queued signal below hands
    each message over to the Qt thread, so callbacks reach the controller where
    the rest of the GUI lives.
    """

    _message_received = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        try:
            self.connection = open_dbus_connection(bus="SESSION")
        except Exception as exc:
            raise RuntimeError(f"the D-Bus session bus is unavailable: {exc}") from exc
        self.router = DBusRouter(self.connection)
        self.messages: queue.Queue[Any] = queue.Queue()
        self.filters: list[Any] = []
        self.response_callbacks: dict[str, Callable[[int, dict[str, Any]], None]] = {}
        self.shortcut_callbacks: tuple[Callable[[str, str], None], Callable[[str, str], None]] | None = None
        self.closed = False
        self._message_received.connect(self._deliver, Qt.ConnectionType.QueuedConnection)
        self.reader = threading.Thread(target=self._forward_messages, name="portal-messages", daemon=True)
        self.reader.start()

    @property
    def sender_name(self) -> str:
        return (self.connection.unique_name or "").lstrip(":").replace(".", "_")

    def call(
        self,
        interface: str,
        method: str,
        signature: str,
        arguments: list[Any],
        path: str = OBJECT_PATH,
    ) -> list[Any]:
        address = DBusAddress(path, bus_name=BUS_NAME, interface=interface)
        message = new_method_call(address, method, signature, tuple(arguments))
        return self._send(message, f"{interface}.{method}")

    def subscribe_response(
        self,
        path: str,
        callback: Callable[[int, dict[str, Any]], None],
    ) -> None:
        self.response_callbacks[path] = callback
        self._watch(type="signal", interface=REQUEST_INTERFACE, member="Response", path=path)

    def subscribe_shortcuts(
        self,
        activated: Callable[[str, str], None],
        deactivated: Callable[[str, str], None],
    ) -> None:
        self.shortcut_callbacks = (activated, deactivated)
        for member in ("Activated", "Deactivated"):
            self._watch(type="signal", interface=SHORTCUTS_INTERFACE, member=member, path=OBJECT_PATH)

    def clear(self) -> None:
        if self.closed:
            return
        self.closed = True
        for handle in self.filters:
            handle.close()
        self.filters.clear()
        self.response_callbacks.clear()
        self.shortcut_callbacks = None
        self.messages.put(None)
        self.router.close()
        self.connection.close()

    def _send(self, message: Any, description: str) -> list[Any]:
        try:
            reply = self.router.send_and_get_reply(message, timeout=CALL_TIMEOUT)
        except Exception as exc:
            raise RuntimeError(f"{description}: {exc}") from exc
        if reply.header.message_type is MessageType.error:
            detail = reply.body[0] if reply.body else reply.header.fields.get(HeaderFields.error_name)
            raise RuntimeError(str(detail) if detail else f"{description} failed")
        return list(reply.body)

    def _watch(self, **rule: Any) -> None:
        # The bus resolves the well-known sender name while routing, so asking it
        # for that sender keeps other applications out. The local filter compares
        # header fields literally and would never match it: signals carry the
        # unique name of the portal (":1.42"), so its rule leaves sender out.
        self.filters.append(self.router.filter(MatchRule(**rule), queue=self.messages))
        self._send(message_bus.AddMatch(MatchRule(sender=BUS_NAME, **rule)), "AddMatch")

    def _forward_messages(self) -> None:
        while True:
            message = self.messages.get()
            if message is None:
                return
            self._message_received.emit(message)

    @Slot(object)
    def _deliver(self, message: Any) -> None:
        fields = message.header.fields
        interface = fields.get(HeaderFields.interface)
        member = fields.get(HeaderFields.member)
        if interface == REQUEST_INTERFACE and member == "Response":
            callback = self.response_callbacks.pop(fields.get(HeaderFields.path), None)
            if callback is not None:
                response, results = message.body
                callback(int(response), unwrap_variants(results))
            return
        if interface == SHORTCUTS_INTERFACE and self.shortcut_callbacks is not None:
            activated, deactivated = self.shortcut_callbacks
            session_handle, shortcut_id = message.body[0], message.body[1]
            if member == "Activated":
                activated(str(session_handle), str(shortcut_id))
            elif member == "Deactivated":
                deactivated(str(session_handle), str(shortcut_id))


def request_token(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def expected_request_path(connection: PortalConnection, token: str) -> str:
    return f"{OBJECT_PATH}/request/{connection.sender_name}/{token}"


class BackgroundPortal:
    def __init__(self, connection: PortalConnection | None = None) -> None:
        self.connection = connection or PortalBusConnection()
        self.pending: Callable[[bool, str], None] | None = None

    def request(self, enabled: bool, callback: Callable[[bool, str], None]) -> None:
        if self.pending is not None:
            callback(False, "an automatic-start request is already pending")
            return
        self.pending = callback
        token = request_token("background")
        path = expected_request_path(self.connection, token)
        self.connection.subscribe_response(
            path,
            lambda response, results: self._complete(enabled, response, results),
        )
        options = {
            "handle_token": ("s", token),
            "reason": ("s", "Keep voice dictation ready after login"),
            "autostart": ("b", enabled),
            "commandline": ("as", ["cortex-whisper"]),
        }
        try:
            self.connection.call(BACKGROUND_INTERFACE, "RequestBackground", "sa{sv}", ["", options])
        except Exception as exc:
            self._finish(False, str(exc))

    def _complete(self, enabled: bool, response: int, results: dict[str, Any]) -> None:
        if response != 0:
            self._finish(False, f"background permission was denied (code {response})")
            return
        active = bool(results.get("autostart", False))
        if enabled and not active:
            self._finish(False, "automatic startup was not authorized")
            return
        self._finish(True, "")

    def _finish(self, success: bool, error: str) -> None:
        callback, self.pending = self.pending, None
        if callback:
            callback(success, error)

    def close(self) -> None:
        self.connection.clear()
        self.pending = None
