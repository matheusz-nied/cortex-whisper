#!/usr/bin/env python3
"""Compatibility entry point for running Whisper Ditado from the repository."""

import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from whisper_ditado.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
