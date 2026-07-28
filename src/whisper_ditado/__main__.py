from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import ConfigStore


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Whisper Ditado — private, local voice dictation")
    result.add_argument("--version", action="version", version=__version__)
    result.add_argument("--list-microphones", action="store_true")
    result.add_argument("--diagnostics", action="store_true")
    result.add_argument("--no-gui", action="store_true")
    result.add_argument("--model", choices=("small", "medium"))
    result.add_argument("--microphone")
    return result


def main() -> int:
    args = parser().parse_args()
    if args.list_microphones:
        from .cli import list_microphones

        return list_microphones()
    if args.diagnostics:
        from .cli import diagnostics

        return diagnostics()

    store = ConfigStore()
    config = store.load()
    changed = False
    if args.model:
        config.model = args.model
        changed = True
    if args.microphone:
        config.microphone = args.microphone
        changed = True
    if changed:
        store.save(config)
    if args.no_gui:
        from .cli import run_terminal

        return run_terminal(config.model, config.microphone, config.language)

    from .app import run_gui

    return run_gui()


if __name__ == "__main__":
    sys.exit(main())
