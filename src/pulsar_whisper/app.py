"""Pulsar Whisper Qt application."""

from __future__ import annotations

import logging
import signal
import subprocess
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import QByteArray, QObject, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .config import ConfigStore, log_directory
from .controller import Controller
from .metadata import APP_COMPACT_NAME, APP_ID, APP_NAME, APP_SLUG
from .state import AppState
from .ui.overlay import StatusOverlay
from .ui.settings import SettingsDialog

SERVER_NAME = f"{APP_ID}.v1"


def configure_logging() -> Path:
    log_file = log_directory() / f"{APP_SLUG}.log"
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(formatter)
    terminal_handler = logging.StreamHandler(sys.stderr)
    terminal_handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    root.addHandler(terminal_handler)
    root.info("%s started; log file: %s", APP_NAME, log_file)
    return log_file


def tray_icon(color: str) -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    painter.drawEllipse(8, 8, 48, 48)
    painter.setBrush(QColor("#ffffff"))
    painter.drawRoundedRect(27, 18, 10, 20, 5, 5)
    painter.drawRoundedRect(22, 34, 20, 5, 2, 2)
    painter.drawRoundedRect(29, 38, 6, 9, 2, 2)
    painter.end()
    return QIcon(pixmap)


class SingleInstance(QObject):
    show_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._receive)
        self.message = ""

    def acquire(self) -> bool:
        if self.server.listen(SERVER_NAME):
            return True
        socket = QLocalSocket()
        socket.connectToServer(SERVER_NAME)
        if socket.waitForConnected(500):
            socket.write(QByteArray(b"show"))
            socket.waitForBytesWritten(500)
            if socket.waitForReadyRead(700) and bytes(socket.readAll()) == b"ok":
                self.message = f"{APP_NAME} is already running; opening Settings."
            else:
                self.message = (
                    f"Another {APP_NAME} instance exists but did not respond. "
                    "It may be suspended; run 'jobs -l' and stop it before trying again."
                )
            socket.disconnectFromServer()
            return False
        QLocalServer.removeServer(SERVER_NAME)
        return self.server.listen(SERVER_NAME)

    def _receive(self) -> None:
        socket = self.server.nextPendingConnection()
        if socket:
            socket.waitForReadyRead(250)
            self.show_requested.emit()
            socket.write(QByteArray(b"ok"))
            socket.waitForBytesWritten(250)
            socket.disconnectFromServer()


class PulsarWhisperApplication(QObject):
    def __init__(self, qt_app: QApplication, log_file: Path) -> None:
        super().__init__()
        self.qt_app = qt_app
        self.log_file = log_file
        self.store = ConfigStore()
        self.controller = Controller(self.store)
        self.overlay = StatusOverlay(self.controller.config.overlay_position)
        self.settings: SettingsDialog | None = None
        self.tray = QSystemTrayIcon(tray_icon("#5da9ff"), self)
        self.menu = QMenu()

        self.status_action = QAction("Loading model…", self.menu)
        self.status_action.setEnabled(False)
        self.pause_action = QAction("Pause dictation", self.menu)
        self.pause_action.setCheckable(True)
        settings_action = QAction("Settings…", self.menu)
        logs_action = QAction("Open logs folder", self.menu)
        quit_action = QAction("Quit", self.menu)
        self.menu.addAction(self.status_action)
        self.menu.addSeparator()
        self.menu.addAction(self.pause_action)
        self.menu.addAction(settings_action)
        self.menu.addAction(logs_action)
        self.menu.addSeparator()
        self.menu.addAction(quit_action)
        self.tray.setContextMenu(self.menu)

        self.controller.state_changed.connect(self._state_changed)
        self.controller.state_changed.connect(self.overlay.set_status)
        self.controller.audio_level.connect(self.overlay.set_level)
        self.controller.prepare_paste.connect(self.overlay.hide)
        self.controller.notification.connect(self._notify)
        self.pause_action.toggled.connect(self.controller.set_paused)
        settings_action.triggered.connect(self.show_settings)
        logs_action.triggered.connect(self.open_logs)
        quit_action.triggered.connect(self.quit)
        self.tray.activated.connect(self._tray_activated)

    def start(self) -> None:
        self.tray.show()
        self.controller.start()
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.show_settings()

    @Slot(str, str)
    def _state_changed(self, state: str, message: str) -> None:
        parsed = AppState(state)
        labels = {
            AppState.LOADING: message or "Loading model…",
            AppState.READY: f"Ready — hold {self.controller.config.hotkey}",
            AppState.RECORDING: "Recording…",
            AppState.TRANSCRIBING: "Transcribing…",
            AppState.SUCCESS: "Transcription completed",
            AppState.ERROR: message or "Error",
            AppState.PAUSED: "Dictation paused",
        }
        colors = {
            AppState.RECORDING: "#ff4d5a",
            AppState.TRANSCRIBING: "#5da9ff",
            AppState.SUCCESS: "#42d392",
            AppState.ERROR: "#ffb44d",
            AppState.PAUSED: "#8a8f98",
        }
        self.status_action.setText(labels[parsed])
        self.tray.setIcon(tray_icon(colors.get(parsed, "#5da9ff")))
        self.tray.setToolTip(f"{APP_NAME} — {labels[parsed]}")
        if self.settings:
            self.settings.backend_label.setText(self.controller.backend_summary)

    @Slot(str, str)
    def _notify(self, title: str, message: str) -> None:
        self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3500)

    @Slot()
    def show_settings(self) -> None:
        if self.settings is None:
            self.settings = SettingsDialog(self.controller.config, self.controller.backend_summary)
            self.settings.config_saved.connect(self._save_settings)
        self.settings.config = self.controller.config
        self.settings.show()
        self.settings.raise_()
        self.settings.activateWindow()

    @Slot(object)
    def _save_settings(self, config) -> None:
        self.controller.update_config(config)
        self.overlay.position_mode = config.overlay_position

    @Slot()
    def open_logs(self) -> None:
        folder = str(self.log_file.parent)
        if sys.platform == "win32":
            subprocess.Popen(["explorer", folder])
        else:
            subprocess.Popen(["xdg-open", folder])

    def _tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_settings()

    @Slot()
    def quit(self) -> None:
        self.controller.shutdown()
        self.tray.hide()
        self.qt_app.quit()


def run_gui() -> int:
    QApplication.setApplicationName(APP_NAME)
    QApplication.setOrganizationName(APP_COMPACT_NAME)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    log_file = configure_logging()
    logging.getLogger(__name__).info("Qt graphics backend: %s", app.platformName())
    instance = SingleInstance()
    if not instance.acquire():
        logging.getLogger(__name__).warning(instance.message)
        print(instance.message, file=sys.stderr, flush=True)
        return 0
    pulsar_app = PulsarWhisperApplication(app, log_file)
    instance.show_requested.connect(pulsar_app.show_settings)
    app.aboutToQuit.connect(pulsar_app.controller.shutdown)

    def handle_shutdown_signal(signum, _frame) -> None:
        logging.getLogger(__name__).info("Received signal %s; shutting down", signum)
        pulsar_app.quit()

    signal.signal(signal.SIGINT, handle_shutdown_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_shutdown_signal)

    # The native Qt event loop must return control to Python periodically so
    # SIGINT (Ctrl+C) can be processed.
    signal_pump = QTimer()
    signal_pump.setInterval(150)
    signal_pump.timeout.connect(lambda: None)
    signal_pump.start()
    pulsar_app.start()
    # Keep these references alive for the duration of the event loop.
    app._single_instance = instance  # type: ignore[attr-defined]
    app._pulsar_app = pulsar_app  # type: ignore[attr-defined]
    app._signal_pump = signal_pump  # type: ignore[attr-defined]
    return app.exec()
