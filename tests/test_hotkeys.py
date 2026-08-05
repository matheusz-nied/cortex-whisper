from cortex_whisper.hotkeys import system_process_environment


def test_system_process_environment_removes_pyinstaller_library_path(monkeypatch):
    monkeypatch.setenv("LD_LIBRARY_PATH", "/app/_internal")
    monkeypatch.delenv("LD_LIBRARY_PATH_ORIG", raising=False)

    environment = system_process_environment()

    assert "LD_LIBRARY_PATH" not in environment


def test_system_process_environment_restores_original_library_path(monkeypatch):
    monkeypatch.setenv("LD_LIBRARY_PATH", "/app/_internal")
    monkeypatch.setenv("LD_LIBRARY_PATH_ORIG", "/system/custom")

    environment = system_process_environment()

    assert environment["LD_LIBRARY_PATH"] == "/system/custom"
    assert "LD_LIBRARY_PATH_ORIG" not in environment


def test_system_process_environment_removes_appimage_gio_isolation(monkeypatch):
    monkeypatch.setenv("CORTEX_WHISPER_APPIMAGE_GIO_ISOLATED", "1")
    monkeypatch.setenv("GIO_MODULE_DIR", "/app/empty-gio-modules")
    monkeypatch.setenv("GIO_USE_VFS", "local")
    monkeypatch.setenv("GSETTINGS_BACKEND", "memory")

    environment = system_process_environment()

    assert "CORTEX_WHISPER_APPIMAGE_GIO_ISOLATED" not in environment
    assert "GIO_MODULE_DIR" not in environment
    assert "GIO_USE_VFS" not in environment
    assert "GSETTINGS_BACKEND" not in environment
