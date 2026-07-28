"""Application state definitions."""

from __future__ import annotations

from enum import StrEnum


class AppState(StrEnum):
    LOADING = "loading"
    READY = "ready"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    SUCCESS = "success"
    ERROR = "error"
    PAUSED = "paused"
