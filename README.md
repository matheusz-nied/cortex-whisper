# Whisper Ditado

Private, local voice dictation powered by `faster-whisper`.

Hold **F8**, speak, and release the key. Whisper Ditado records your voice,
transcribes it on your computer, and pastes the result into the application that
already has focus. A compact cyberpunk-inspired overlay shows when the app is
recording, decoding, or finished.

<p align="center">
  <img src="docs/assets/overlay-recording.png" alt="Recording overlay" width="248">
  <img src="docs/assets/overlay-decoding.png" alt="Decoding overlay" width="248">
  <img src="docs/assets/overlay-success.png" alt="Success overlay" width="248">
</p>

> [!IMPORTANT]
> Linux with GNOME/Wayland is the only platform validated on real hardware so
> far. Windows support is implemented but still experimental. macOS is not yet
> implemented.

## Platform status

| Platform | Status | Notes |
| --- | --- | --- |
| Linux / GNOME Wayland | Tested | Primary development platform |
| Linux / X11 | Implemented | Needs broader testing |
| Windows 10/11 | Experimental | Build and installer are available, but untested on real hardware |
| macOS | Not supported yet | Platform integration has not been implemented |

## Features

- Hold-to-talk global hotkey, with **F8** as the default.
- Fully local transcription: recorded audio is never sent to an application server.
- `small` and `medium` Whisper models with persistent selection.
- CPU inference with `int8` quantization and an automatic CUDA attempt when available.
- Microphone selection and a built-in three-second input test.
- Compact neon status overlay for recording, decoding, success, and error states.
- Automatic clipboard delivery and paste into the focused application.
- System tray controls, pause mode, rotating logs, and optional automatic startup.
- GUI and terminal modes.

The interface and documentation are in English. Transcription currently defaults
to Portuguese (`pt`) to preserve the project's original use case.

## How it works

```text
Hold F8 → record audio → release F8 → transcribe locally → copy → paste
```

Whisper models are not bundled with the application. The selected model is
downloaded to the user's cache on first use and reused on subsequent launches.

## Linux requirements

Ubuntu and Debian-based systems:

```bash
sudo apt install libportaudio2 wl-clipboard ydotool python3-dbus python3-gi
systemctl --user enable --now ydotool.service
```

GNOME/Wayland asks for permission to register the global shortcut the first time
the application starts. `wl-copy` provides a reliable Wayland clipboard, while
`ydotool` sends Ctrl+V to the focused application.

## Run from source

Python 3.10 or newer is required.

```bash
cd whisper-ditado
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python ditado.py
```

## Install on Linux

### Debian package

Build and install the local package:

```bash
source venv/bin/activate
python -m pip install -r requirements-dev.txt
PYTHON_BIN=venv/bin/python scripts/build_linux.sh
sudo apt install ./dist/whisper-ditado_2.0.0_amd64.deb
```

Launch it from the application menu or run:

```bash
whisper-ditado
```

### AppImage

When `appimagetool` is available, the Linux build script also creates:

```text
dist/Whisper-Ditado-2.0.0-x86_64.AppImage
```

Run it with:

```bash
chmod +x dist/Whisper-Ditado-2.0.0-x86_64.AppImage
./dist/Whisper-Ditado-2.0.0-x86_64.AppImage
```

## Usage

1. Start Whisper Ditado and wait for the model to become ready.
2. Place the cursor in any text field.
3. Press and hold **F8** while speaking.
4. Release **F8** to transcribe and paste the text.
5. Use the tray menu to pause dictation, open Settings, inspect logs, or quit.

The status overlay is centered by the Wayland compositor on the active display.
This avoids stealing focus and works reliably with multi-monitor layouts.

## Settings

The settings window provides:

- Whisper model: `small` or `medium`.
- Input microphone.
- Hold-to-talk hotkey from F6 through F12.
- Automatic startup.
- Live microphone test.

Settings persist in the operating system's standard user configuration directory.

## Command-line interface

```bash
python ditado.py --help
python ditado.py --version
python ditado.py --list-microphones
python ditado.py --diagnostics
python ditado.py --no-gui --model medium
python ditado.py --microphone "ME6S"
```

Terminal mode uses Enter to start and stop recording and `q` to quit.

## Data and privacy

- Audio is processed locally by `faster-whisper`.
- Audio recordings are kept in memory and are not saved to disk.
- Transcribed text is placed in the system clipboard.
- The model provider may be contacted only when a model must be downloaded.
- Application logs contain operational events and character counts, not the
  transcribed text itself.

Default locations:

| Data | Linux | Windows |
| --- | --- | --- |
| Configuration | `~/.config/WhisperDitado/config.json` | `%APPDATA%\WhisperDitado\config.json` |
| Logs | `~/.local/state/WhisperDitado/log/` | `%LOCALAPPDATA%\WhisperDitado\Logs\` |
| Model cache | Hugging Face user cache | Hugging Face user cache |

## Development

Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run the quality checks:

```bash
python -m ruff check .
python -m pytest
python -m compileall -q ditado.py atalho_wayland.py src
```

Current automated coverage includes configuration migration, audio resampling,
application states, Wayland clipboard integration, and paste failure handling.

## Packaging

Linux:

```bash
PYTHON_BIN=venv/bin/python scripts/build_linux.sh
```

Windows, from PowerShell with Inno Setup installed:

```powershell
scripts\build_windows.ps1
```

Tagged releases and manual workflow runs are configured to test and package the
project through GitHub Actions.

## Known limitations

- The Wayland global shortcut currently depends on GNOME's Global Shortcuts portal.
- Automatic paste on Wayland requires a working `ydotool` user service.
- The overlay is centered on the active monitor because Wayland intentionally
  prevents regular applications from reading global pointer coordinates.
- Windows packaging has not yet been validated on a physical Windows machine.
- macOS hotkeys, paste integration, packaging, and startup behavior are not implemented.

## Roadmap

- Validate and harden the Windows build.
- Add native macOS support.
- Add an in-app transcription language selector.
- Publish signed release artifacts and checksums.
- Create the public landing page and release media.

## Contributing

Bug reports and focused pull requests are welcome. Include the operating system,
desktop session, microphone model, application logs, and reproduction steps when
reporting platform-integration issues.

## License

Whisper Ditado is released under the [MIT License](LICENSE).

Copyright (c) 2026 Matheus Fernandes da Silva.
