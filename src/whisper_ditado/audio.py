from __future__ import annotations

import queue
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

SAMPLE_RATE = 16_000


@dataclass(frozen=True, slots=True)
class InputDevice:
    index: int
    name: str
    host_api: str
    default_sample_rate: int
    is_default: bool = False


class AudioError(RuntimeError):
    pass


def resample_audio(audio: np.ndarray, source_rate: int, target_rate: int = SAMPLE_RATE) -> np.ndarray:
    if source_rate == target_rate or audio.size == 0:
        return audio.astype(np.float32, copy=False)
    target_size = max(1, int(round(audio.size * target_rate / source_rate)))
    source_positions = np.arange(audio.size, dtype=np.float64)
    target_positions = np.linspace(0, audio.size - 1, target_size)
    return np.interp(target_positions, source_positions, audio).astype(np.float32)


class AudioRecorder:
    def __init__(self, level_callback: Callable[[float], None] | None = None) -> None:
        self.level_callback = level_callback
        self._queue: queue.Queue[np.ndarray] = queue.Queue()
        self._stream: Any | None = None
        self._recording = False
        self._sample_rate = SAMPLE_RATE
        self._last_level_at = 0.0
        self.active_device = ""

    @property
    def recording(self) -> bool:
        return self._recording

    @staticmethod
    def devices() -> list[InputDevice]:
        import sounddevice as sd

        default_input = sd.default.device[0]
        result: list[InputDevice] = []
        host_apis = sd.query_hostapis()
        for index, raw in enumerate(sd.query_devices()):
            if int(raw["max_input_channels"]) <= 0:
                continue
            try:
                host_name = str(host_apis[int(raw["hostapi"])]["name"])
            except Exception:
                host_name = "unknown"
            result.append(
                InputDevice(
                    index=index,
                    name=str(raw["name"]),
                    host_api=host_name,
                    default_sample_rate=int(round(float(raw["default_samplerate"]))),
                    is_default=index == default_input,
                )
            )
        return result

    @classmethod
    def candidates(cls, hint: str) -> list[InputDevice | None]:
        devices = cls.devices()
        normalized = hint.casefold().strip()
        matches = [device for device in devices if normalized and normalized in device.name.casefold()]

        def score(device: InputDevice) -> tuple[int, int, int]:
            description = f"{device.name} {device.host_api}".casefold()
            return (
                int(device.is_default),
                int("pipewire" in description or "pulse" in description),
                device.index,
            )

        matches.sort(key=score, reverse=True)
        default_device = next((device for device in devices if device.is_default), None)
        if default_device and all(item.index != default_device.index for item in matches):
            matches.append(default_device)
        return [*matches, None]

    def _callback(self, indata, frames, time_info, status) -> None:
        del frames, time_info
        if status:
            # PortAudio may report overflow here; valid frames are still preserved.
            pass
        if not self._recording:
            return
        chunk = indata.copy()
        self._queue.put(chunk)
        now = time.monotonic()
        if self.level_callback and now - self._last_level_at >= 1 / 30:
            peak = float(np.abs(chunk).max(initial=0.0))
            self._last_level_at = now
            self.level_callback(min(1.0, peak * 18.0))

    def _open(self, device: InputDevice | None) -> tuple[Any, int]:
        import sounddevice as sd

        rates = [SAMPLE_RATE]
        if device and device.default_sample_rate not in rates:
            rates.append(device.default_sample_rate)
        last_error: Exception | None = None
        for rate in rates:
            try:
                stream = sd.InputStream(
                    device=device.index if device else None,
                    samplerate=rate,
                    channels=1,
                    dtype="float32",
                    callback=self._callback,
                )
                stream.start()
                return stream, rate
            except Exception as exc:
                last_error = exc
        raise AudioError(str(last_error or "unknown error while opening the microphone"))

    def start(self, microphone_hint: str) -> str:
        if self._recording:
            return self.active_device
        self._queue = queue.Queue()
        failures: list[str] = []
        for device in self.candidates(microphone_hint):
            name = device.name if device else "default device"
            try:
                self._stream, self._sample_rate = self._open(device)
                self.active_device = name
                self._recording = True
                return name
            except Exception as exc:
                failures.append(f"{name}: {exc}")
        raise AudioError("Could not open a microphone. " + " | ".join(failures))

    def stop(self) -> np.ndarray:
        if not self._recording:
            return np.empty(0, dtype=np.float32)
        self._recording = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            finally:
                self._stream = None
        chunks: list[np.ndarray] = []
        while not self._queue.empty():
            chunks.append(self._queue.get())
        if not chunks:
            return np.empty(0, dtype=np.float32)
        audio = np.concatenate(chunks, axis=0).reshape(-1)
        return resample_audio(audio, self._sample_rate)

    def close(self) -> None:
        if self._recording:
            self.stop()
