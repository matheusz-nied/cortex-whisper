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
    _model_result = Signal(object)
    _model_failure = Signal(str)
    _transcription_result = Signal(str)
    _transcription_failure = Signal(str)

    def __init__(self, store: ConfigStore) -> None:
        super().__init__()
        self.store = store
        self.config = store.load()
        self.state = AppState.LOADING
        self.message = "Carregando modelo…"
        self.integration = SystemIntegration()
        self.recorder = AudioRecorder(level_callback=self.audio_level.emit)
        self.transcriber = Transcriber()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="whisper")
        self.hotkey: HotkeyBackend | None = None
        self.paused = False

        self.hotkey_pressed.connect(self._on_hotkey_pressed)
        self.hotkey_released.connect(self._on_hotkey_released)
        self.hotkey_error.connect(self._on_hotkey_error)
        self._model_result.connect(self._on_model_loaded)
        self._model_failure.connect(self._on_model_failed)
        self._transcription_result.connect(self._on_transcribed)
        self._transcription_failure.connect(self._on_transcription_failed)

    @property
    def backend_summary(self) -> str:
        hotkey = self.hotkey.name if self.hotkey else "iniciando"
        model = self.transcriber.info
        model_text = f"{model.name} / {model.device}" if model else self.config.model
        return f"Atalho: {hotkey} · Colagem: {self.integration.paste_backend} · Modelo: {model_text}"

    def start(self) -> None:
        try:
            self.integration.ensure_application_entry()
            self.integration.set_autostart(self.config.autostart)
        except Exception as exc:
            LOGGER.warning("Não foi possível integrar o aplicativo ao sistema: %s", exc)
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
        self.set_state(AppState.LOADING, f"Carregando {model_name}…")
        future = self.executor.submit(self.transcriber.load, model_name)
        future.add_done_callback(self._complete_model)

    def _complete_model(self, future: Future[ModelInfo]) -> None:
        try:
            self._model_result.emit(future.result())
        except Exception as exc:
            LOGGER.exception("Falha ao carregar modelo")
            self._model_failure.emit(str(exc))

    @Slot(object)
    def _on_model_loaded(self, info: ModelInfo) -> None:
        self.config.model = info.name
        self.store.save(self.config)
        LOGGER.info("Modelo pronto: %s em %s (%s)", info.name, info.device, info.compute_type)
        self.model_changed.emit(f"{info.name} na {info.device.upper()}")
        self.set_state(AppState.PAUSED if self.paused else AppState.READY)

    @Slot(str)
    def _on_model_failed(self, error: str) -> None:
        self.set_state(AppState.ERROR, "Falha ao carregar o modelo")
        self.notification.emit("Erro no modelo Whisper", error)

    @Slot()
    def _on_hotkey_pressed(self) -> None:
        if self.state != AppState.READY or self.paused:
            return
        self.set_state(AppState.RECORDING, "Gravando")
        try:
            device = self.recorder.start(self.config.microphone)
            LOGGER.info("Gravação iniciada em %s", device)
        except AudioError as exc:
            self.set_state(AppState.ERROR, "Microfone indisponível")
            self.notification.emit("Microfone indisponível", str(exc))
            QTimer.singleShot(2500, self._return_to_ready)

    @Slot()
    def _on_hotkey_released(self) -> None:
        if self.state != AppState.RECORDING:
            return
        audio = self.recorder.stop()
        self.audio_level.emit(0.0)
        if audio.size == 0:
            self._transcription_failure.emit("Nenhum áudio foi capturado")
            return
        max_volume = float(np.abs(audio).max(initial=0.0))
        if max_volume < 0.005:
            self._transcription_failure.emit("O áudio está muito baixo")
            return
        self.set_state(AppState.TRANSCRIBING, "Transcrevendo…")
        future = self.executor.submit(self.transcriber.transcribe, audio, self.config.language)
        future.add_done_callback(self._complete_transcription)

    def _complete_transcription(self, future: Future[str]) -> None:
        try:
            self._transcription_result.emit(future.result())
        except Exception as exc:
            LOGGER.exception("Falha na transcrição")
            self._transcription_failure.emit(str(exc))

    @Slot(str)
    def _on_transcribed(self, text: str) -> None:
        if not text:
            self._on_transcription_failed("Nenhuma fala foi reconhecida")
            return
        LOGGER.info("Transcrição concluída (%d caracteres)", len(text))
        text_with_space = f"{text} "
        QGuiApplication.clipboard().setText(text_with_space)
        copied, clipboard_backend = self.integration.copy_text(text_with_space)
        if copied:
            LOGGER.info("Texto colocado no clipboard por %s", clipboard_backend)
        else:
            LOGGER.warning("Falha no clipboard nativo: %s; mantendo fallback do Qt", clipboard_backend)
        # Dê ao compositor tempo para publicar a nova seleção antes do Ctrl+V.
        QTimer.singleShot(220, self._paste_transcription)

    def _paste_transcription(self) -> None:
        try:
            pasted, error = self.integration.paste()
        except Exception as exc:
            LOGGER.exception("Erro inesperado durante a colagem")
            pasted, error = False, str(exc)
        if pasted:
            LOGGER.info("Comando de colagem enviado por %s", self.integration.paste_backend)
        else:
            LOGGER.error("Falha ao colar: %s", error)
        self.set_state(AppState.SUCCESS, "Pronto" if pasted else "Copiado")
        if not pasted:
            self.notification.emit("Transcrição copiada", error)
        QTimer.singleShot(850, self._return_to_ready)

    @Slot(str)
    def _on_transcription_failed(self, error: str) -> None:
        self.set_state(AppState.ERROR, error)
        self.notification.emit("Não foi possível transcrever", error)
        QTimer.singleShot(2500, self._return_to_ready)

    @Slot(str)
    def _on_hotkey_error(self, error: str) -> None:
        LOGGER.error("Atalho global: %s", error)
        self.notification.emit("Atalho global indisponível", error)

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
                self.integration.set_autostart(self.config.autostart)
            except Exception as exc:
                self.notification.emit("Inicialização automática", str(exc))
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
        if self.hotkey:
            self.hotkey.stop()
        self.recorder.close()
        self.executor.shutdown(wait=False, cancel_futures=True)
