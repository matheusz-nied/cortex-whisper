from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import ConfigStore


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Whisper Ditado — ditado local multiplataforma")
    result.add_argument("--version", action="version", version=__version__)
    result.add_argument("--listar-microfones", action="store_true")
    result.add_argument("--diagnostico", action="store_true")
    result.add_argument("--sem-interface", action="store_true")
    result.add_argument("--modelo", choices=("small", "medium"))
    result.add_argument("--microfone")
    return result


def main() -> int:
    args = parser().parse_args()
    if args.listar_microfones:
        from .cli import list_microphones

        return list_microphones()
    if args.diagnostico:
        from .cli import diagnostics

        return diagnostics()

    store = ConfigStore()
    config = store.load()
    changed = False
    if args.modelo:
        config.model = args.modelo
        changed = True
    if args.microfone:
        config.microphone = args.microfone
        changed = True
    if changed:
        store.save(config)
    if args.sem_interface:
        from .cli import run_terminal

        return run_terminal(config.model, config.microphone, config.language)

    from .app import run_gui

    return run_gui()


if __name__ == "__main__":
    sys.exit(main())
