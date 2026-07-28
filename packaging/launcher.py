"""PyInstaller entry point for Pulsar Whisper release binaries."""

import sys

from pulsar_whisper.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
