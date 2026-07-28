"""Remove unused Qt components whose terms differ from the LGPL Qt modules."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

UNUSED_GPL_COMPONENTS = (
    "PySide6/Qt/qml/QtQuick/VirtualKeyboard",
    "PySide6/Qt/plugins/platforminputcontexts/libqtvirtualkeyboardplugin.so",
    "PySide6/Qt/plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll",
    "PySide6/Qt/lib/libQt6VirtualKeyboard.so.6",
    "PySide6/Qt/lib/libQt6VirtualKeyboardQml.so.6",
    "PySide6/Qt/bin/Qt6VirtualKeyboard.dll",
    "PySide6/Qt/bin/Qt6VirtualKeyboardQml.dll",
)


def prune(bundle: Path) -> list[Path]:
    internal = bundle / "_internal"
    removed = []
    for relative in UNUSED_GPL_COMPONENTS:
        target = internal / relative
        if target.is_dir():
            shutil.rmtree(target)
            removed.append(target)
        elif target.exists():
            target.unlink()
            removed.append(target)
    return removed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    removed = prune(args.bundle.resolve())
    print(f"Removed {len(removed)} unused GPL-only Qt Virtual Keyboard files")


if __name__ == "__main__":
    main()
