import runpy
import sys
from pathlib import Path

from scripts.collect_licenses import collect
from scripts.collect_native_notices import binary_entries
from scripts.prune_linux_system_libraries import prune as prune_linux_system_libraries
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
    duplicate_library = tmp_path / "bundle" / "_internal" / "libQt6VirtualKeyboard.so.6"
    duplicate_library.write_text("unused", encoding="utf-8")

    removed = prune(tmp_path / "bundle")

    assert len(removed) == 3
    assert not virtual_keyboard.exists()
    assert not virtual_keyboard_library.exists()
    assert not duplicate_library.exists()
    assert qt_widgets.exists()


def test_linux_bundle_uses_host_glib_libraries(tmp_path):
    internal = tmp_path / "bundle" / "_internal"
    internal.mkdir(parents=True)
    host_libraries = (
        "libgio-2.0.so.0",
        "libglib-2.0.so.0",
        "libgmodule-2.0.so.0",
        "libgobject-2.0.so.0",
        "libgthread-2.0.so.0",
    )
    for name in host_libraries:
        (internal / name).write_text("provided by the host", encoding="utf-8")
    unrelated = internal / "libportaudio.so.2"
    unrelated.write_text("bundled", encoding="utf-8")

    removed = prune_linux_system_libraries(tmp_path / "bundle")

    assert {path.name for path in removed} == set(host_libraries)
    assert all(not (internal / name).exists() for name in host_libraries)
    assert unrelated.exists()


def test_debian_launcher_isolates_host_gio_modules():
    project_root = Path(__file__).resolve().parent.parent
    launcher = project_root / "packaging" / "linux" / "cortex-whisper-launcher"

    content = launcher.read_text(encoding="utf-8")
    assert "GIO_MODULE_DIR=" in content
    assert "GIO_USE_VFS=local" in content
    assert "GSETTINGS_BACKEND=memory" in content


def test_frozen_pyav_stub_supports_import_but_rejects_file_api():
    project_root = Path(__file__).resolve().parent.parent
    hook = project_root / "packaging" / "runtime_hooks" / "pyi_rth_av_stub.py"
    previous = sys.modules.pop("av", None)
    try:
        runpy.run_path(str(hook))
        import av

        assert "compatibility stub" in av.__file__
        assert getattr(av, "__wrapped__", None) is None
        try:
            _ = av.open
        except RuntimeError as exc:
            assert "intentionally excluded" in str(exc)
        else:
            raise AssertionError("The PyAV compatibility stub unexpectedly exposed av.open")
    finally:
        sys.modules.pop("av", None)
        if previous is not None:
            sys.modules["av"] = previous


def test_flatpak_replaces_pyav_with_compatibility_stub():
    project_root = Path(__file__).resolve().parent.parent
    manifest = (project_root / "io.github.matheusz_nied.CortexWhisper.yml").read_text(
        encoding="utf-8"
    )
    stub = project_root / "packaging" / "flatpak" / "av_stub.py"

    assert "rm -rf /app/lib/python3.13/site-packages/av" in manifest
    assert "install -Dm644 packaging/flatpak/av_stub.py" in manifest
    assert "PyAV is intentionally excluded" in stub.read_text(encoding="utf-8")
    assert "THIRD_PARTY_NOTICES.md" in manifest
    assert "/app/share/licenses/portaudio/LICENSE" in manifest
    assert "/app/share/licenses/ydotool/LICENSE" in manifest


def test_native_inventory_extracts_binary_entries_recursively():
    toc = (
        ["ignored"],
        [("libexample.so", "/usr/lib/libexample.so", "BINARY")],
        ("module.so", "/venv/module.so", "EXTENSION"),
        ("module.py", "/project/module.py", "PYMODULE"),
    )

    assert list(binary_entries(toc)) == [
        ("libexample.so", "/usr/lib/libexample.so", "BINARY"),
        ("module.so", "/venv/module.so", "EXTENSION"),
    ]
