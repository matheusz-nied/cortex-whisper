"""Provide the optional PyAV import without bundling FFmpeg in frozen builds.

Cortex Whisper always passes microphone audio to faster-whisper as a NumPy
array. faster-whisper imports PyAV unconditionally, but only accesses it when
the input is a filename or file object.
"""

import sys
import types


def _unsupported_file_input(name):
    if name.startswith("__") and name.endswith("__"):
        raise AttributeError(name)
    raise RuntimeError(
        "PyAV is intentionally excluded from Cortex Whisper release packages; "
        f"the unavailable av.{name} API is only required for file input"
    )


if "av" not in sys.modules:
    av_stub = types.ModuleType("av")
    av_stub.__file__ = "<Cortex Whisper PyAV compatibility stub>"
    av_stub.__getattr__ = _unsupported_file_input
    sys.modules["av"] = av_stub
