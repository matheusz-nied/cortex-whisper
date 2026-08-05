"""Compatibility import for faster-whisper packages without PyAV/FFmpeg.

Cortex Whisper supplies captured microphone audio as NumPy arrays. PyAV is
only needed when faster-whisper receives a filename or file-like object, a
feature that this application does not expose.
"""


def __getattr__(name: str):
    if name.startswith("__") and name.endswith("__"):
        raise AttributeError(name)
    raise RuntimeError(
        "PyAV is intentionally excluded from Cortex Whisper release packages; "
        f"the unavailable av.{name} API is only required for file input"
    )
