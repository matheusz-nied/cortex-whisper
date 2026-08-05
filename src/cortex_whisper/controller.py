"""Application workflow controller."""

from __future__ import annotations

import logging
from concurrent.futures import Future, ThreadPoolExecutor

import numpy as np
from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication

from .audio import AudioError, AudioRecorder
from .config import AppConfig, ConfigStore
from .hotkeys import HotkeyBackend, create_hotkey_backend
from .integration import SystemIntegration
from .state import AppState
from .transcriber import ModelInfo, Transcriber

LOGGER = logging.getLogger(__name__)


class Controller(QObject):
    state_changed = Signal(str, str)
    audio_level = Signal(float)
    model_changed = Signal(str)
    notification = Signal(str, str)
    hotkey_pressed = Signal()
    hotkey_released = Signal()
    hotkey_error = Signal(str)
    prepare_paste = Signal()
    _model_result = Signal(object)
    _model_failure = Signal(str)
    _transcription_result = Signal(str)
    _transcription_failure = Signal(str)

    def __init__(self, store: ConfigStore) -> None:
        super().__init__()
        self.store = store
        self.config = store.load()
        self.state = AppState.LOADING
        self.message = "Loading model…"
        self.integration = SystemIntegration()
        self.recorder = AudioRecorder(level_callback=self.audio_level.emit)
        self.transcriber = Transcriber()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="whisper")
        self.hotkey: HotkeyBackend | None = None
        self.paused = False
        self._shutting_down = False

        self.hotkey_pressed.connect(self._on_hotkey_pressed)
        self.hotkey_released.connect(self._on_hotkey_released)
        self.hotkey_error.connect(self._on_hotkey_error)
        self._model_result.connect(self._on_model_loaded)
        self._model_failure.connect(self._on_model_failed)
        self._transcription_result.connect(self._on_transcribed)
        self._transcription_failure.connect(self._on_transcription_failed)

    @property
    def backend_summary(self) -> str:
        hotkey = self.hotkey.name if self.hotkey else "starting"
        model = self.transcriber.info
        model_text = f"{model.name} / {model.device}" if model else self.config.model
        return f"Hotkey: {hotkey} · Paste: {self.integration.paste_backend} · Model: {model_text}"

    def start(self) -> None:
        try:
            self.integration.ensure_application_entry()
            if not self.integration.flatpak:
                self.integration.set_autostart(self.config.autostart)
            elif not self.config.autostart_portal_configured:
                self.integration.set_autostart(self.config.autostart, self._autostart_completed)
        except Exception as exc:
            LOGGER.warning("Could not integrate the application with the operating system: %s", exc)
        self._start_hotkey()
        self.load_model(self.config.model)

    def _start_hotkey(self) -> None:
        if self.hotkey:
            self.hotkey.stop()
        self.hotkey = create_hotkey_backend(
            self.config.hotkey,
            self.hotkey_pressed.emit,
            self.hotkey_released.emit,
            self.hotkey_error.emit,
        )
        try:
            self.hotkey.start()
        except Exception as exc:
            self.hotkey_error.emit(str(exc))

    def set_state(self, state: AppState, message: str = "") -> None:
        self.state = state
        self.message = message
        self.state_changed.emit(state.value, message)

    def load_model(self, model_name: str) -> None:
        self.set_state(AppState.LOADING, f"Loading {model_name}…")
        future = self.executor.submit(self.transcriber.load, model_name)
        future.add_done_callback(self._complete_model)

    def _complete_model(self, future: Future[ModelInfo]) -> None:
        try:
            self._model_result.emit(future.result())
        except Exception as exc:
            LOGGER.exception("Failed to load the model")
            self._model_failure.emit(str(exc))

    @Slot(object)
    def _on_model_loaded(self, info: ModelInfo) -> None:
        self.config.model = info.name
        self.store.save(self.config)
        LOGGER.info("Model ready: %s on %s (%s)", info.name, info.device, info.compute_type)
        self.model_changed.emit(f"{info.name} on {info.device.upper()}")
        self.set_state(AppState.PAUSED if self.paused else AppState.READY)

    @Slot(str)
    def _on_model_failed(self, error: str) -> None:
        self.set_state(AppState.ERROR, "Failed to load the model")
        self.notification.emit("Whisper model error", error)

    @Slot()
    def _on_hotkey_pressed(self) -> None:
        if self.state != AppState.READY or self.paused:
            return
        self.set_state(AppState.RECORDING, "Recording")
        try:
            device = self.recorder.start(self.config.microphone)
            LOGGER.info("Recording started from %s", device)
        except AudioError as exc:
            self.set_state(AppState.ERROR, "Microphone unavailable")
            self.notification.emit("Microphone unavailable", str(exc))
            QTimer.singleShot(2500, self._return_to_ready)

    @Slot()
    def _on_hotkey_released(self) -> None:
        if self.state != AppState.RECORDING:
            return
        audio = self.recorder.stop()
        self.audio_level.emit(0.0)
        if audio.size == 0:
            self._transcription_failure.emit("No audio was captured")
            return
        max_volume = float(np.abs(audio).max(initial=0.0))
        if max_volume < 0.005:
            self._transcription_failure.emit("The audio is too quiet")
            return
        self.set_state(AppState.TRANSCRIBING, "Transcribing…")
        future = self.executor.submit(self.transcriber.transcribe, audio, self.config.language)
        future.add_done_callback(self._complete_transcription)

    def _complete_transcription(self, future: Future[str]) -> None:
        try:
            self._transcription_result.emit(future.result())
        except Exception as exc:
            LOGGER.exception("Transcription failed")
            self._transcription_failure.emit(str(exc))

    @Slot(str)
    def _on_transcribed(self, text: str) -> None:
        if not text:
            self._on_transcription_failed("No speech was recognized")
            return
        LOGGER.info("Transcription completed (%d characters)", len(text))
        text_with_space = f"{text} "
        QGuiApplication.clipboard().setText(text_with_space)
        copied, clipboard_backend = self.integration.copy_text(text_with_space)
        if copied:
            LOGGER.info("Text copied to the clipboard via %s", clipboard_backend)
        else:
            LOGGER.warning("Native clipboard failed: %s; keeping the Qt fallback", clipboard_backend)
        # Hide the floating surface before Ctrl+V. Some Wayland compositors may
        # treat the last raised surface as a keyboard target despite no-focus hints.
        self.prepare_paste.emit()
        LOGGER.info("Overlay hidden; waiting for the target application to regain focus")
        QTimer.singleShot(350, self._paste_transcription)

    def _paste_transcription(self) -> None:
        try:
            pasted, error = self.integration.paste()
        except Exception as exc:
            LOGGER.exception("Unexpected error while pasting")
            pasted, error = False, str(exc)
        if pasted:
            LOGGER.info("Paste command sent via %s", self.integration.paste_backend)
        else:
            LOGGER.error("Paste failed: %s", error)
        self.set_state(AppState.SUCCESS, "Ready" if pasted else "Copied")
        if not pasted:
            self.notification.emit("Transcription copied", error)
        QTimer.singleShot(850, self._return_to_ready)

    @Slot(str)
    def _on_transcription_failed(self, error: str) -> None:
        self.set_state(AppState.ERROR, error)
        self.notification.emit("Could not transcribe the audio", error)
        QTimer.singleShot(2500, self._return_to_ready)

    @Slot(str)
    def _on_hotkey_error(self, error: str) -> None:
        LOGGER.error("Global hotkey: %s", error)
        self.notification.emit("Global hotkey unavailable", error)

    def _return_to_ready(self) -> None:
        if self.state in {AppState.SUCCESS, AppState.ERROR}:
            self.set_state(AppState.PAUSED if self.paused else AppState.READY)

    def update_config(self, new_config: AppConfig) -> None:
        old_model = self.config.model
        old_hotkey = self.config.hotkey
        old_autostart = self.config.autostart
        self.config = new_config.normalized()
        self.store.save(self.config)
        if old_autostart != self.config.autostart:
            try:
                if self.integration.flatpak:
                    self.config.autostart_portal_configured = False
                    self.store.save(self.config)
                    self.integration.set_autostart(self.config.autostart, self._autostart_completed)
                else:
                    self.integration.set_autostart(self.config.autostart)
            except Exception as exc:
                self.notification.emit("Automatic startup", str(exc))
        if old_hotkey != self.config.hotkey:
            self._start_hotkey()
        if old_model != self.config.model:
            self.load_model(self.config.model)

    def set_paused(self, paused: bool) -> None:
        self.paused = paused
        if paused and self.recorder.recording:
            self.recorder.stop()
        self.set_state(AppState.PAUSED if paused else AppState.READY)

    def shutdown(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        LOGGER.info("Stopping the microphone, global hotkey, and Whisper tasks")
        if self.hotkey:
            self.hotkey.stop()
        self.integration.close()
        self.recorder.close()
        self.executor.shutdown(wait=False, cancel_futures=True)

    def _autostart_completed(self, success: bool, error: str) -> None:
        if success:
            self.config.autostart_portal_configured = True
            self.store.save(self.config)
            return
        if self.config.autostart:
            self.config.autostart = False
        self.config.autostart_portal_configured = True
        self.store.save(self.config)
        LOGGER.warning("Automatic startup portal: %s", error)
        self.notification.emit("Automatic startup", error)
