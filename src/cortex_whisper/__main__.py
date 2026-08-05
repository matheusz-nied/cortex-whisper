"""Cortex Whisper command-line entry point."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import ConfigStore
from .metadata import APP_DESCRIPTION, APP_NAME


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=f"{APP_NAME} — {APP_DESCRIPTION.lower()}")
    result.add_argument("--version", action="version", version=__version__)
    result.add_argument("--list-microphones", action="store_true")
    result.add_argument("--diagnostics", action="store_true")
    result.add_argument("--no-gui", action="store_true")
    result.add_argument("--model", choices=("small", "medium"))
    result.add_argument("--microphone")
    result.add_argument("--self-test", action="store_true", help=argparse.SUPPRESS)
    return result


def main() -> int:
    args = parser().parse_args()
    if args.list_microphones:
        from .cli import list_microphones

        return list_microphones()
    if args.diagnostics:
        from .cli import diagnostics

        return diagnostics()
    if args.self_test:
        from .transcriber import Transcriber

        Transcriber()
        print(f"{APP_NAME} import self-test passed")
        return 0

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
