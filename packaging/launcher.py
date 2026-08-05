"""PyInstaller entry point for Cortex Whisper release binaries."""

import sys

from cortex_whisper.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
