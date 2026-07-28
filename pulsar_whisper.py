#!/usr/bin/env python3
"""Run Pulsar Whisper directly from a source checkout."""

import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "src"
if str(SOURCE) in sys.path:
    sys.path.remove(str(SOURCE))
sys.path.insert(0, str(SOURCE))

from pulsar_whisper.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
