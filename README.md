# Cortex Whisper

[![Build](https://github.com/matheusz-nied/cortex-whisper/actions/workflows/build.yml/badge.svg)](https://github.com/matheusz-nied/cortex-whisper/actions/workflows/build.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-22d3ee)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0%20beta-ff2e7e)](https://github.com/matheusz-nied/cortex-whisper/releases)
[![Platform](https://img.shields.io/badge/platform-Linux-7c5cff)](#platform-status)

Private, local AI voice dictation powered by `faster-whisper`.

Hold **F8**, speak, and release. Cortex Whisper records your voice, transcribes
it on your computer, and pastes the result into the application that already has
focus. A compact cyberpunk-inspired overlay shows when the app is recording,
transcribing, or finished.

<p align="center">
  <img src="docs/assets/overlay-recording.png" alt="Recording overlay" width="248">
  <img src="docs/assets/overlay-decoding.png" alt="Transcribing overlay" width="248">
  <img src="docs/assets/overlay-success.png" alt="Success overlay" width="248">
</p>

> [!IMPORTANT]
> Version **0.1.0 Beta** is validated only on Linux with GNOME/Wayland. Windows
> support is experimental and has not been tested on real hardware. macOS is not
> implemented yet.

Cortex Whisper is an independent open-source project. It is not affiliated with,
endorsed by, or sponsored by OpenAI.

## Platform status

| Platform | Status | Notes |
| --- | --- | --- |
| Linux / GNOME Wayland | Tested | Primary development platform |
| Linux / X11 | Implemented | Needs broader testing |
| Windows 10/11 | Experimental | Build and installer exist, but need real-hardware testing |
| macOS | Not supported | Platform integration has not been implemented |

## Features

- Hold-to-talk global hotkey, with **F8** as the default.
- Local transcription; recorded audio is never sent to an application server.
- `small` and `medium` Whisper models with persistent selection.
- CPU inference with `int8` quantization and an automatic CUDA attempt when available.
- Microphone selection and a built-in three-second input test.
- Compact neon overlay for recording, transcribing, success, and errors.
- Clipboard delivery and automatic paste into the focused application.
- Tray controls, pause mode, rotating logs, and optional automatic startup.
- GUI and terminal modes.

The interface and documentation are in English. Transcription defaults to
Portuguese (`pt`) for the project's original use case.

```text
Hold F8 → record audio → release F8 → transcribe locally → copy → paste
```

Models are not bundled. The selected model is downloaded to the user's Hugging
Face cache on first use and reused afterward. Expect a wait on the very first
run while the model downloads.

## Install

Download a Linux x86_64 build from the
[releases page](https://github.com/matheusz-nied/cortex-whisper/releases).

**Debian / Ubuntu (`.deb`)**

```bash
sudo apt install ./cortex-whisper_0.1.0_amd64.deb
cortex-whisper
```

The package declares its own dependencies, so `apt` pulls in what it needs.
`ydotool` and `wl-clipboard` are listed as recommended packages because
automatic paste depends on them; keep the default `apt` behaviour that installs
recommendations, or add them manually.

**Any distribution (AppImage)**

```bash
chmod +x Cortex-Whisper-0.1.0-x86_64.AppImage
./Cortex-Whisper-0.1.0-x86_64.AppImage
```

The AppImage does not install system dependencies. Install the runtime packages
listed under [Linux requirements](#linux-requirements) before running it.

Verify your download against the `SHA256SUMS` file published with the release:

```bash
sha256sum -c SHA256SUMS --ignore-missing
```

Prefer to build it yourself? See [Build packages](#build-packages).

### Linux requirements

Required when running from source or from the AppImage. On Ubuntu and
Debian-based systems:

```bash
sudo apt install libportaudio2 wl-clipboard ydotool python3-dbus python3-gi
systemctl --user enable --now ydotool.service
```

GNOME/Wayland requests permission for the global shortcut on first launch.
`wl-copy` provides the clipboard and `ydotool` sends Ctrl+V to the focused app.

### Uninstall

```bash
sudo apt remove cortex-whisper          # .deb install
rm Cortex-Whisper-0.1.0-x86_64.AppImage # AppImage
```

Configuration, logs, and downloaded models are left in place. Remove them with:

```bash
rm -rf ~/.config/CortexWhisper ~/.local/state/CortexWhisper
rm -rf ~/.cache/huggingface/hub/models--Systran--faster-whisper-*
```

## Usage

1. Start Cortex Whisper and wait for the model to become ready.
2. Place the cursor in a text field.
3. Hold **F8** while speaking.
4. Release **F8** to transcribe and paste.
5. Use the tray menu to pause, open Settings, inspect logs, or quit.

The overlay stays centered on the active display. This is reliable on Wayland
and avoids stealing focus in multi-monitor layouts.

Settings include the model, microphone, an F6–F12 hold-to-talk hotkey, automatic
startup, and a live microphone test.

## Command line

```bash
cortex-whisper --help
cortex-whisper --version
cortex-whisper --list-microphones
cortex-whisper --diagnostics
cortex-whisper --no-gui --model medium
cortex-whisper --microphone "ME6S"
```

From a source checkout, replace `cortex-whisper` with `python cortex_whisper.py`.

Terminal mode uses Enter to start and stop recording and `q` to quit.

## Troubleshooting

Start with the built-in environment report. It prints JSON covering the app
version, session type, selected model and hotkey, the detected paste backend,
and how many microphones were found:

```bash
cortex-whisper --diagnostics
```

| Symptom | Check |
| --- | --- |
| Text is copied but never pasted | `systemctl --user status ydotool.service`. Automatic paste on Wayland needs this service running. The text is still on the clipboard, so Ctrl+V works meanwhile. |
| F8 does nothing | GNOME asks for global-shortcut permission on first launch. If it was denied, reset it under Settings → Applications → Cortex Whisper. Also confirm no other app owns F8. |
| No audio captured | `cortex-whisper --list-microphones`, then select the right input in Settings and use the built-in three-second test. |
| First run hangs on startup | The Whisper model is downloading to the Hugging Face cache. Subsequent runs are offline and fast. |
| AppImage will not start | Some distributions no longer ship FUSE 2. Run it with `./Cortex-Whisper-0.1.0-x86_64.AppImage --appimage-extract-and-run`. |

Logs are written to `~/.local/state/CortexWhisper/log/` and record operational
events only, never transcribed text.

## Data and privacy

- Audio is processed locally by `faster-whisper`, kept in memory, and not saved.
- Transcribed text is placed in the system clipboard.
- Hugging Face may be contacted when a model must be downloaded.
- There is no telemetry.
- Logs contain operational events and character counts, never transcribed text.

| Data | Linux | Windows |
| --- | --- | --- |
| Configuration | `~/.config/CortexWhisper/config.json` | `%LOCALAPPDATA%\CortexWhisper\config.json` |
| Logs | `~/.local/state/CortexWhisper/log/` | `%LOCALAPPDATA%\CortexWhisper\Logs\` |
| Models | Hugging Face user cache | Hugging Face user cache |

Existing `WhisperDitado` configuration and logs are copied automatically on the
first Cortex Whisper launch. The originals are retained as a recovery backup.

## Run from source

Python 3.10 or newer is required.

```bash
git clone https://github.com/matheusz-nied/cortex-whisper.git
cd cortex-whisper
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python cortex_whisper.py
```

The former `python ditado.py` entry point remains as a temporary compatibility alias.

## Build packages

```bash
source venv/bin/activate
python -m pip install -r requirements-dev.txt
PYTHON_BIN=venv/bin/python scripts/build_linux.sh
sudo apt install ./dist/cortex-whisper_0.1.0_amd64.deb
```

The script always produces the `.deb`. When `appimagetool` is also installed it
creates `dist/Cortex-Whisper-0.1.0-x86_64.AppImage`, and it writes a
`dist/SHA256SUMS` covering both artifacts.

On Windows, install Inno Setup and run `scripts\build_windows.ps1` from PowerShell.

## Development

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m pytest
python -m compileall -q cortex_whisper.py cortex_shortcut_portal.py src
```

Source layout:

| Path | Contents |
| --- | --- |
| `src/cortex_whisper/` | Application package: audio capture, transcription, hotkeys, desktop integration |
| `src/cortex_whisper/ui/` | Qt overlay and settings window |
| `packaging/` | PyInstaller spec, Debian metadata, Inno Setup script |
| `scripts/` | Linux and Windows build scripts |
| `docs/` | Landing page published with GitHub Pages |

The `build` workflow runs on `v*` tags and on manual dispatch. It builds the
Linux and Windows artifacts and attaches them to the workflow run; publishing a
GitHub Release is still a manual step.

## Known limitations

- Wayland global shortcuts currently depend on GNOME's Global Shortcuts portal.
- Automatic paste on Wayland requires a working `ydotool` user service.
- Wayland prevents normal applications from reading global pointer coordinates,
  so the overlay is centered rather than attached to the pointer.
- Windows packaging has not been validated on a physical Windows machine.
- macOS hotkeys, paste integration, packaging, and startup are not implemented.

See the [release checklist](RELEASE_CHECKLIST.md) for the full launch roadmap.

## Contributing

Bug reports and focused pull requests are welcome. Include the operating system,
desktop session, microphone, logs, and reproduction steps for integration issues.
Run `ruff` and `pytest` before opening a pull request.

## License

Cortex Whisper is released under the [MIT License](LICENSE).

Copyright (c) 2026 Matheus Fernandes da Silva.

Bundled libraries retain their own licenses. See the
[Third-Party Notices](THIRD_PARTY_NOTICES.md) for the audited dependency inventory
and binary-distribution notes.
