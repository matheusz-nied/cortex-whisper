"""Local faster-whisper model integration."""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
from faster_whisper import WhisperModel


@dataclass(frozen=True, slots=True)
class ModelInfo:
    name: str
    device: str
    compute_type: str


class Transcriber:
    def __init__(self) -> None:
        self.model: WhisperModel | None = None
        self.info: ModelInfo | None = None

    def load(self, model_name: str) -> ModelInfo:
        try:
            loaded = WhisperModel(model_name, device="cuda", compute_type="int8")
            info = ModelInfo(model_name, "cuda", "int8")
        except Exception:
            loaded = WhisperModel(
                model_name,
                device="cpu",
                compute_type="int8",
                cpu_threads=max(1, min(4, os.cpu_count() or 1)),
            )
            info = ModelInfo(model_name, "cpu", "int8")
        self.model = loaded
        self.info = info
        return info

    def transcribe(self, audio: np.ndarray, language: str = "pt") -> str:
        if self.model is None:
            raise RuntimeError("The Whisper model has not been loaded yet")
        segments, _ = self.model.transcribe(audio, language=language, beam_size=1)
        return "".join(segment.text for segment in segments).strip()
