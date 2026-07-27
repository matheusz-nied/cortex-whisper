from __future__ import annotations

import numpy as np

from whisper_ditado.audio import SAMPLE_RATE, resample_audio


def test_resample_keeps_float32_and_duration():
    source = np.linspace(-1, 1, 48_000, dtype=np.float32)
    result = resample_audio(source, 48_000, SAMPLE_RATE)
    assert result.dtype == np.float32
    assert result.shape == (16_000,)


def test_empty_audio_is_safe():
    result = resample_audio(np.empty(0, dtype=np.float32), 48_000)
    assert result.size == 0

