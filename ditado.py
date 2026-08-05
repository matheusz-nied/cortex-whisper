#!/usr/bin/env python3
"""Legacy compatibility entry point for Cortex Whisper."""

import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from cortex_whisper.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
