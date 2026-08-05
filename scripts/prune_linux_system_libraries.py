"""Keep Linux GLib libraries provided by the host distribution.

Bundling these libraries in a portable application can mix an older GLib with
newer GIO/GVfs modules installed on the user's system.  The resulting ABI
mismatch produces loader errors and can disable desktop integration.
"""

from __future__ import annotations

import argparse
from pathlib import Path

HOST_GLIB_LIBRARIES = (
    "libgio-2.0.so.0",
    "libglib-2.0.so.0",
    "libgmodule-2.0.so.0",
    "libgobject-2.0.so.0",
    "libgthread-2.0.so.0",
)


def prune(bundle: Path) -> list[Path]:
    internal = bundle / "_internal"
    removed = []
    for name in HOST_GLIB_LIBRARIES:
        target = internal / name
        if target.is_file() or target.is_symlink():
            target.unlink()
            removed.append(target)
    return removed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    removed = prune(args.bundle.resolve())
    print(f"Removed {len(removed)} host-provided Linux GLib libraries")


if __name__ == "__main__":
    main()
