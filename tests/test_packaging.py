from pathlib import Path

from scripts.collect_licenses import collect
from scripts.prune_qt_components import prune


def test_license_collector_creates_release_inventory(tmp_path):
    project_root = Path(__file__).resolve().parent.parent
    output = tmp_path / "legal"

    collect(project_root, output)

    assert (output / "LICENSE").is_file()
    assert (output / "THIRD_PARTY_NOTICES.md").is_file()
    inventory = (output / "BUNDLED_COMPONENTS.md").read_text(encoding="utf-8")
    assert "faster-whisper" in inventory
    assert "PySide6" in inventory
    assert any((output / "licenses").iterdir())


def test_prune_removes_only_unused_qt_virtual_keyboard(tmp_path):
    qt_root = tmp_path / "bundle" / "_internal" / "PySide6" / "Qt"
    virtual_keyboard = qt_root / "qml" / "QtQuick" / "VirtualKeyboard"
    virtual_keyboard.mkdir(parents=True)
    (virtual_keyboard / "plugin.qmltypes").write_text("unused", encoding="utf-8")
    qt_widgets = qt_root / "lib" / "libQt6Widgets.so.6"
    qt_widgets.parent.mkdir(parents=True)
    qt_widgets.write_text("required", encoding="utf-8")
    virtual_keyboard_library = qt_root / "lib" / "libQt6VirtualKeyboard.so.6"
    virtual_keyboard_library.write_text("unused", encoding="utf-8")

    removed = prune(tmp_path / "bundle")

    assert len(removed) == 2
    assert not virtual_keyboard.exists()
    assert not virtual_keyboard_library.exists()
    assert qt_widgets.exists()
