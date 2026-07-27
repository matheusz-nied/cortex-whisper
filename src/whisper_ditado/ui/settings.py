from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from ..audio import AudioRecorder, InputDevice
from ..config import AppConfig


class SettingsDialog(QDialog):
    config_saved = Signal(object)
    level_received = Signal(float)

    def __init__(self, config: AppConfig, backend_summary: str, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.test_recorder: AudioRecorder | None = None
        self.devices: list[InputDevice] = []
        self.setWindowTitle("Whisper Ditado — Configurações")
        self.setMinimumWidth(470)

        root = QVBoxLayout(self)
        title = QLabel("<h2>Whisper Ditado</h2><p>Ditado local e privado, sempre pronto no F8.</p>")
        root.addWidget(title)

        essentials = QGroupBox("Configurações essenciais")
        form = QFormLayout(essentials)
        self.model_combo = QComboBox()
        self.model_combo.addItem("Small — mais rápido", "small")
        self.model_combo.addItem("Medium — mais preciso", "medium")
        self.model_combo.setCurrentIndex(max(0, self.model_combo.findData(config.model)))
        form.addRow("Modelo Whisper:", self.model_combo)

        mic_row = QHBoxLayout()
        self.microphone_combo = QComboBox()
        refresh = QPushButton("Atualizar")
        refresh.clicked.connect(self.refresh_microphones)
        mic_row.addWidget(self.microphone_combo, 1)
        mic_row.addWidget(refresh)
        form.addRow("Microfone:", mic_row)

        self.hotkey_combo = QComboBox()
        for number in range(6, 13):
            self.hotkey_combo.addItem(f"F{number}")
        index = self.hotkey_combo.findText(config.hotkey)
        self.hotkey_combo.setCurrentIndex(index if index >= 0 else 2)
        form.addRow("Segurar para falar:", self.hotkey_combo)

        self.autostart_check = QCheckBox("Iniciar minimizado com o sistema")
        self.autostart_check.setChecked(config.autostart)
        form.addRow("", self.autostart_check)
        root.addWidget(essentials)

        test_group = QGroupBox("Teste rápido do microfone")
        test_layout = QHBoxLayout(test_group)
        self.test_button = QPushButton("Testar por 3 segundos")
        self.test_button.clicked.connect(self.test_microphone)
        self.level_bar = QProgressBar()
        self.level_bar.setRange(0, 100)
        self.level_bar.setTextVisible(False)
        test_layout.addWidget(self.test_button)
        test_layout.addWidget(self.level_bar, 1)
        root.addWidget(test_group)

        self.backend_label = QLabel(backend_summary)
        self.backend_label.setWordWrap(True)
        self.backend_label.setStyleSheet("color: palette(mid); font-size: 11px;")
        root.addWidget(self.backend_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Close
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("Fechar")
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.hide)
        root.addWidget(buttons)

        self.level_received.connect(self._set_level)
        self.refresh_microphones()

    @Slot()
    def refresh_microphones(self) -> None:
        selected = self.config.microphone
        self.microphone_combo.clear()
        try:
            self.devices = AudioRecorder.devices()
        except Exception as exc:
            self.microphone_combo.addItem(f"Erro: {exc}", selected)
            return
        for device in self.devices:
            suffix = " (padrão)" if device.is_default else ""
            self.microphone_combo.addItem(f"{device.name}{suffix}", device.name)
        match = next(
            (
                index
                for index in range(self.microphone_combo.count())
                if selected.casefold() in str(self.microphone_combo.itemData(index)).casefold()
            ),
            0,
        )
        self.microphone_combo.setCurrentIndex(match)

    @Slot()
    def test_microphone(self) -> None:
        if self.test_recorder and self.test_recorder.recording:
            return
        microphone = str(self.microphone_combo.currentData() or "")
        self.test_recorder = AudioRecorder(level_callback=self.level_received.emit)
        try:
            self.test_recorder.start(microphone)
        except Exception as exc:
            QMessageBox.warning(self, "Teste do microfone", str(exc))
            self.test_recorder = None
            return
        self.test_button.setEnabled(False)
        self.test_button.setText("Fale agora…")
        QTimer.singleShot(3000, self._finish_test)

    def _finish_test(self) -> None:
        if self.test_recorder:
            self.test_recorder.stop()
            self.test_recorder = None
        self.test_button.setEnabled(True)
        self.test_button.setText("Testar por 3 segundos")
        self.level_bar.setValue(0)

    @Slot(float)
    def _set_level(self, level: float) -> None:
        self.level_bar.setValue(int(level * 100))

    @Slot()
    def save(self) -> None:
        self.config = replace(
            self.config,
            model=str(self.model_combo.currentData()),
            microphone=str(self.microphone_combo.currentData() or ""),
            hotkey=self.hotkey_combo.currentText(),
            autostart=self.autostart_check.isChecked(),
        )
        self.config_saved.emit(self.config)
        self.hide()

    def closeEvent(self, event) -> None:
        self._finish_test()
        event.ignore()
        self.hide()
