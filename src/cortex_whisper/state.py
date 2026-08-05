"""Application state definitions."""

from __future__ import annotations

from enum import Enum


class AppState(str, Enum):
    """String-valued state enum compatible with Python 3.10."""

    LOADING = "loading"
    READY = "ready"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    SUCCESS = "success"
    ERROR = "error"
    PAUSED = "paused"

    def __str__(self) -> str:
        return self.value
