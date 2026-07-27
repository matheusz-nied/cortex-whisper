from __future__ import annotations

import math
import time

from PySide6.QtCore import QPoint, QRectF, Qt, QTimer, Slot
from PySide6.QtGui import QColor, QCursor, QFont, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ..state import AppState


class StatusOverlay(QWidget):
    def __init__(self, position_mode: str = "cursor") -> None:
        super().__init__()
        self.position_mode = position_mode
        self.state = AppState.READY
        self.message = ""
        self.level = 0.0
        self.spinner_angle = 0
        self.started_at = time.monotonic()
        self.setFixedSize(202, 48)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self._animate)

    @Slot(str, str)
    def set_status(self, state: str, message: str) -> None:
        self.state = AppState(state)
        self.message = message
        if self.state == AppState.RECORDING:
            self.started_at = time.monotonic()
        if self.state in {AppState.READY, AppState.PAUSED}:
            self.timer.stop()
            self.hide()
            return
        self._place()
        self.show()
        if not self.timer.isActive():
            self.timer.start()
        self.update()

    @Slot(float)
    def set_level(self, level: float) -> None:
        self.level = max(0.0, min(1.0, level))
        if self.state == AppState.RECORDING:
            self.update()

    def _animate(self) -> None:
        self.spinner_angle = (self.spinner_angle + 18) % 360
        self.update()

    def _place(self) -> None:
        screens = QGuiApplication.screens()
        if not screens:
            return
        cursor = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor) or QGuiApplication.primaryScreen() or screens[0]
        area = screen.availableGeometry()
        if self.position_mode == "cursor" and not cursor.isNull():
            target = QPoint(cursor.x() + 24, cursor.y() + 28)
            x = max(area.left() + 8, min(target.x(), area.right() - self.width() - 8))
            y = max(area.top() + 8, min(target.y(), area.bottom() - self.height() - 8))
        else:
            x = area.center().x() - self.width() // 2
            y = area.bottom() - self.height() - 28
        self.move(x, y)

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(20, 22, 27, 236))
        painter.drawRoundedRect(QRectF(1, 1, self.width() - 2, self.height() - 2), 20, 20)

        if self.state == AppState.RECORDING:
            self._paint_recording(painter)
        elif self.state in {AppState.TRANSCRIBING, AppState.LOADING}:
            self._paint_spinner(painter, QColor("#5da9ff"))
            self._paint_text(painter, self.message or "Transcrevendo…")
        elif self.state == AppState.SUCCESS:
            self._paint_check(painter)
            self._paint_text(painter, self.message or "Pronto")
        else:
            self._paint_error(painter)
            self._paint_text(painter, self.message or "Algo deu errado")

    def _paint_recording(self, painter: QPainter) -> None:
        painter.setBrush(QColor("#ff4d5a"))
        painter.drawEllipse(QPoint(20, 24), 5, 5)
        elapsed = int(time.monotonic() - self.started_at)
        label = f"{elapsed // 60:02d}:{elapsed % 60:02d}"
        self._paint_text(painter, label, x=119)
        center_y = 24
        for index in range(6):
            wave = 0.35 + 0.65 * abs(math.sin(self.spinner_angle / 30 + index * 0.9))
            height = 4 + int(22 * max(0.08, self.level) * wave)
            painter.setBrush(QColor("#ff6670"))
            painter.drawRoundedRect(QRectF(42 + index * 10, center_y - height / 2, 5, height), 2.5, 2.5)

    def _paint_spinner(self, painter: QPainter, color: QColor) -> None:
        pen = QPen(QColor(255, 255, 255, 45), 3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(12, 16, 16, 16))
        pen.setColor(color)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(QRectF(12, 16, 16, 16), self.spinner_angle * 16, 110 * 16)

    def _paint_check(self, painter: QPainter) -> None:
        pen = QPen(
            QColor("#42d392"),
            3,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
        painter.setPen(pen)
        painter.drawLine(13, 24, 18, 29)
        painter.drawLine(18, 29, 28, 18)

    def _paint_error(self, painter: QPainter) -> None:
        painter.setBrush(QColor("#ffb44d"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(20, 24), 10, 10)
        painter.setPen(QPen(QColor("#191b20"), 2))
        painter.drawLine(20, 18, 20, 25)
        painter.drawPoint(20, 29)

    def _paint_text(self, painter: QPainter, text: str, x: int = 40) -> None:
        painter.setPen(QColor("#f4f5f7"))
        font = QFont()
        font.setPointSize(10)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        available = self.width() - x - 12
        shortened = painter.fontMetrics().elidedText(text, Qt.TextElideMode.ElideRight, available)
        painter.drawText(QRectF(x, 0, available, self.height()), Qt.AlignmentFlag.AlignVCenter, shortened)
