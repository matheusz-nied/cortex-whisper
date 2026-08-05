"""QtDBus clients for XDG desktop portals."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any, Protocol

from PySide6.QtCore import SLOT, QObject, Slot
from PySide6.QtDBus import (
    QDBus,
    QDBusConnection,
    QDBusMessage,
    QDBusObjectPath,
    QDBusVariant,
)

BUS_NAME = "org.freedesktop.portal.Desktop"
OBJECT_PATH = "/org/freedesktop/portal/desktop"
REQUEST_INTERFACE = "org.freedesktop.portal.Request"
SESSION_INTERFACE = "org.freedesktop.portal.Session"
SHORTCUTS_INTERFACE = "org.freedesktop.portal.GlobalShortcuts"
REGISTRY_INTERFACE = "org.freedesktop.host.portal.Registry"
BACKGROUND_INTERFACE = "org.freedesktop.portal.Background"


def unwrap_dbus(value: Any) -> Any:
    if isinstance(value, QDBusVariant):
        return unwrap_dbus(value.variant())
    if isinstance(value, QDBusObjectPath):
        return value.path()
    if isinstance(value, dict):
        return {str(key): unwrap_dbus(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [unwrap_dbus(child) for child in value]
    return value


class PortalConnection(Protocol):
    @property
    def sender_name(self) -> str: ...

    def call(
        self,
        interface: str,
        method: str,
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


class _ResponseReceiver(QObject):
    def __init__(self, callback: Callable[[int, dict[str, Any]], None]) -> None:
        super().__init__()
        self.callback = callback

    @Slot("uint", "QVariantMap")
    def response(self, response: int, results: dict[str, Any]) -> None:
        self.callback(int(response), unwrap_dbus(results))


class _ShortcutReceiver(QObject):
    def __init__(
        self,
        activated: Callable[[str, str], None],
        deactivated: Callable[[str, str], None],
    ) -> None:
        super().__init__()
        self.activated_callback = activated
        self.deactivated_callback = deactivated

    @Slot("QDBusObjectPath", str, "qulonglong", "QVariantMap")
    def activated(
        self,
        session_handle: QDBusObjectPath,
        shortcut_id: str,
        _timestamp: int,
        _options: dict[str, Any],
    ) -> None:
        self.activated_callback(session_handle.path(), shortcut_id)

    @Slot("QDBusObjectPath", str, "qulonglong", "QVariantMap")
    def deactivated(
        self,
        session_handle: QDBusObjectPath,
        shortcut_id: str,
        _timestamp: int,
        _options: dict[str, Any],
    ) -> None:
        self.deactivated_callback(session_handle.path(), shortcut_id)


class QtPortalConnection:
    def __init__(self) -> None:
        self.bus = QDBusConnection.sessionBus()
        if not self.bus.isConnected():
            raise RuntimeError(self.bus.lastError().message() or "the D-Bus session bus is unavailable")
        self.receivers: list[QObject] = []

    @property
    def sender_name(self) -> str:
        return self.bus.baseService().lstrip(":").replace(".", "_")

    def call(
        self,
        interface: str,
        method: str,
        arguments: list[Any],
        path: str = OBJECT_PATH,
    ) -> list[Any]:
        message = QDBusMessage.createMethodCall(BUS_NAME, path, interface, method)
        message.setArguments(arguments)
        reply = self.bus.call(message, QDBus.CallMode.Block, 5_000)
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            detail = reply.errorMessage() or reply.errorName() or f"{interface}.{method} failed"
            raise RuntimeError(detail)
        return unwrap_dbus(reply.arguments())

    def subscribe_response(
        self,
        path: str,
        callback: Callable[[int, dict[str, Any]], None],
    ) -> None:
        receiver = _ResponseReceiver(callback)
        connected = self.bus.connect(
            BUS_NAME,
            path,
            REQUEST_INTERFACE,
            "Response",
            receiver,
            SLOT("response(uint,QVariantMap)"),
        )
        if not connected:
            raise RuntimeError(self.bus.lastError().message() or "could not monitor the portal request")
        self.receivers.append(receiver)

    def subscribe_shortcuts(
        self,
        activated: Callable[[str, str], None],
        deactivated: Callable[[str, str], None],
    ) -> None:
        receiver = _ShortcutReceiver(activated, deactivated)
        for signal, slot in (
            ("Activated", "activated(QDBusObjectPath,QString,qulonglong,QVariantMap)"),
            ("Deactivated", "deactivated(QDBusObjectPath,QString,qulonglong,QVariantMap)"),
        ):
            if not self.bus.connect(
                BUS_NAME,
                OBJECT_PATH,
                SHORTCUTS_INTERFACE,
                signal,
                receiver,
                SLOT(slot),
            ):
                raise RuntimeError(self.bus.lastError().message() or f"could not monitor {signal}")
        self.receivers.append(receiver)

    def clear(self) -> None:
        for receiver in self.receivers:
            receiver.deleteLater()
        self.receivers.clear()


def request_token(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def expected_request_path(connection: PortalConnection, token: str) -> str:
    return f"{OBJECT_PATH}/request/{connection.sender_name}/{token}"


class BackgroundPortal:
    def __init__(self, connection: PortalConnection | None = None) -> None:
        self.connection = connection or QtPortalConnection()
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
            "handle_token": QDBusVariant(token),
            "reason": QDBusVariant("Keep voice dictation ready after login"),
            "autostart": QDBusVariant(enabled),
            "commandline": QDBusVariant(["cortex-whisper"]),
        }
        try:
            self.connection.call(BACKGROUND_INTERFACE, "RequestBackground", ["", options])
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
