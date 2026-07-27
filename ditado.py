#!/usr/bin/env python3
"""Entrada compatível para executar o Whisper Ditado direto do repositório."""

import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from whisper_ditado.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
