from __future__ import annotations

import math
import time

from PySide6.QtCore import QPoint, QRectF, Qt, QTimer, Slot
from PySide6.QtGui import QColor, QCursor, QFont, QGuiApplication, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ..state import AppState


class StatusOverlay(QWidget):
    def __init__(self, position_mode: str = "screen_center") -> None:
        super().__init__()
        self.position_mode = position_mode
        self.state = AppState.READY
        self.message = ""
        self.level = 0.0
        self.spinner_angle = 0
        self.started_at = time.monotonic()
        self.setFixedSize(248, 58)
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
        self.timer.setInterval(45)
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
        # No Wayland, deixar o compositor posicionar a nova superfície faz com
        # que ela apareça no centro do monitor atualmente ativo.
        if not (
            self.position_mode == "screen_center" and QGuiApplication.platformName() == "wayland"
        ):
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

    def _place(self, cursor: QPoint | None = None) -> None:
        screens = QGuiApplication.screens()
        if not screens:
            return
        if cursor is None:
            cursor = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor) or QGuiApplication.primaryScreen() or screens[0]
        area = screen.availableGeometry()
        if self.position_mode == "cursor" and not cursor.isNull():
            target = QPoint(cursor.x() + 24, cursor.y() + 28)
            x = max(area.left() + 8, min(target.x(), area.right() - self.width() - 8))
            y = max(area.top() + 8, min(target.y(), area.bottom() - self.height() - 8))
        elif self.position_mode == "bottom_center":
            x = area.center().x() - self.width() // 2
            y = area.bottom() - self.height() - 28
        else:
            x = area.center().x() - self.width() // 2
            y = area.center().y() - self.height() // 2
        self.move(x, y)

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = QRectF(2.5, 2.5, self.width() - 5, self.height() - 5)
        accent = self._accent_color()

        glow_pen = QPen(QColor(accent.red(), accent.green(), accent.blue(), 42), 5)
        painter.setPen(glow_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(bounds, 17, 17)

        background = QLinearGradient(0, 0, self.width(), self.height())
        background.setColorAt(0.0, QColor(7, 12, 24, 248))
        background.setColorAt(0.52, QColor(16, 14, 34, 246))
        background.setColorAt(1.0, QColor(8, 20, 32, 248))
        painter.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 150), 1.2))
        painter.setBrush(background)
        painter.drawRoundedRect(bounds, 17, 17)

        painter.setPen(QPen(QColor(255, 255, 255, 18), 1))
        painter.drawRoundedRect(QRectF(4, 4, self.width() - 8, self.height() - 8), 15, 15)

        painter.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 16), 1))
        for y in range(10, self.height() - 7, 6):
            painter.drawLine(12, y, self.width() - 12, y)

        painter.setPen(QPen(accent, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(18, 4, 72, 4)
        painter.drawLine(self.width() - 48, self.height() - 4, self.width() - 18, self.height() - 4)

        if self.state == AppState.RECORDING:
            self._paint_recording(painter)
        elif self.state in {AppState.TRANSCRIBING, AppState.LOADING}:
            self._paint_spinner(painter, QColor("#36e7ff"))
            label = "DECODIFICANDO" if self.state == AppState.TRANSCRIBING else "INICIALIZANDO"
            self._paint_text(painter, label)
        elif self.state == AppState.SUCCESS:
            self._paint_check(painter)
            self._paint_text(painter, "TEXTO INSERIDO")
        else:
            self._paint_error(painter)
            self._paint_text(painter, self.message or "FALHA NO SISTEMA")

    def _accent_color(self) -> QColor:
        colors = {
            AppState.RECORDING: QColor("#ff3b81"),
            AppState.TRANSCRIBING: QColor("#36e7ff"),
            AppState.LOADING: QColor("#8a7dff"),
            AppState.SUCCESS: QColor("#49f6a5"),
            AppState.ERROR: QColor("#ffb547"),
        }
        return colors.get(self.state, QColor("#36e7ff"))

    def _paint_recording(self, painter: QPainter) -> None:
        pulse = 0.68 + 0.32 * abs(math.sin(self.spinner_angle / 28))
        painter.setPen(QPen(QColor(255, 59, 129, int(90 * pulse)), 2))
        painter.setBrush(QColor("#ff3b81"))
        painter.drawEllipse(QPoint(23, 29), 5, 5)
        painter.setPen(Qt.PenStyle.NoPen)
        elapsed = int(time.monotonic() - self.started_at)
        label = f"{elapsed // 60:02d}:{elapsed % 60:02d}"
        self._paint_text(painter, "REC", x=40, width=38, color=QColor("#ff78a9"), size=8)
        self._paint_text(painter, label, x=184, width=48, color=QColor("#f5f8ff"), size=9)
        center_y = 29
        for index in range(8):
            wave = 0.35 + 0.65 * abs(math.sin(self.spinner_angle / 30 + index * 0.9))
            height = 4 + int(26 * max(0.1, self.level) * wave)
            color = QColor("#ff3b81") if index < 4 else QColor("#36e7ff")
            color.setAlpha(180 + index * 7)
            painter.setBrush(color)
            painter.drawRoundedRect(QRectF(84 + index * 10, center_y - height / 2, 4, height), 2, 2)

    def _paint_spinner(self, painter: QPainter, color: QColor) -> None:
        pen = QPen(QColor(255, 255, 255, 45), 3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(16, 21, 16, 16))
        pen.setColor(color)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(QRectF(16, 21, 16, 16), self.spinner_angle * 16, 105 * 16)

    def _paint_check(self, painter: QPainter) -> None:
        pen = QPen(
            QColor("#49f6a5"),
            3,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
        painter.setPen(pen)
        painter.drawLine(16, 29, 21, 34)
        painter.drawLine(21, 34, 32, 23)

    def _paint_error(self, painter: QPainter) -> None:
        painter.setBrush(QColor("#ffb44d"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(24, 29), 10, 10)
        painter.setPen(QPen(QColor("#191b20"), 2))
        painter.drawLine(24, 23, 24, 30)
        painter.drawPoint(24, 34)

    def _paint_text(
        self,
        painter: QPainter,
        text: str,
        x: int = 46,
        width: int | None = None,
        color: QColor | None = None,
        size: int = 9,
    ) -> None:
        painter.setPen(color or QColor("#eaf8ff"))
        font = QFont("DejaVu Sans Mono")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPointSize(size)
        font.setWeight(QFont.Weight.DemiBold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8)
        painter.setFont(font)
        available = width or self.width() - x - 18
        shortened = painter.fontMetrics().elidedText(text, Qt.TextElideMode.ElideRight, available)
        painter.drawText(QRectF(x, 0, available, self.height()), Qt.AlignmentFlag.AlignVCenter, shortened)
