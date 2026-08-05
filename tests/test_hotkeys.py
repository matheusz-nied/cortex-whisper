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
