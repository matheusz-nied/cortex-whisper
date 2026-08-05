# Cortex Whisper

[![Build](https://github.com/matheusz-nied/cortex-whisper/actions/workflows/build.yml/badge.svg)](https://github.com/matheusz-nied/cortex-whisper/actions/workflows/build.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-22d3ee)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0%20beta-ff2e7e)](https://github.com/matheusz-nied/cortex-whisper/releases)
[![Platform](https://img.shields.io/badge/platform-Linux-7c5cff)](#platform-status)

Private, local AI voice dictation powered by `faster-whisper`.

Hold **F8**, speak, and release. Cortex Whisper records your voice, transcribes
it on your computer, copies the result, and attempts to paste it into the
application that already has focus.

<p align="center">
  <img src="docs/assets/overlay-recording.png" alt="Recording overlay" width="248">
  <img src="docs/assets/overlay-decoding.png" alt="Transcribing overlay" width="248">
  <img src="docs/assets/overlay-success.png" alt="Success overlay" width="248">
</p>

> [!IMPORTANT]
> Version **0.2.0 Beta** targets Linux x86_64 with GNOME/Wayland. The Flatpak is
> the primary Linux package. Ubuntu `.deb` builds are produced separately for
> 24.04 and 26.04. Windows remains experimental; macOS is not implemented.

Cortex Whisper is an independent open-source project. It is not affiliated
with, endorsed by, or sponsored by OpenAI.

## Platform status

| Platform | Status | Notes |
| --- | --- | --- |
| Linux / GNOME Wayland | Tested | Primary platform; use Flatpak |
| Ubuntu 24.04 and 26.04 | Beta | Dedicated `.deb` for each Ubuntu version |
| Linux / X11 | Implemented | Needs broader testing |
| Windows 10/11 | Experimental | Installer exists; real-hardware testing is incomplete |
| macOS | Not supported | Desktop integration is not implemented |

## Features

- Hold-to-talk global shortcut through the desktop portal; F8 is the default.
- Local transcription; audio is kept in memory and is not uploaded.
- `small` and `medium` models with persistent selection.
- CPU `int8` inference and best-effort CUDA detection.
- Microphone selection and a three-second input test.
- Status overlay, tray controls, pause mode, logs, and optional autostart.
- Clipboard fallback when automatic paste is unavailable.

```text
Hold F8 → record → release F8 → transcribe locally → copy → paste
```

Models are not bundled. The selected model is downloaded from Hugging Face on
first use and reused afterward.

## Install

Download the Linux x86_64 artifacts from the
[releases page](https://github.com/matheusz-nied/cortex-whisper/releases).

### Flatpak — recommended

Make sure Flathub is configured, then install the downloaded bundle:

```bash
flatpak remote-add --if-not-exists flathub \
  https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user ./Cortex-Whisper-0.2.0-x86_64.flatpak
flatpak run io.github.matheusz_nied.CortexWhisper
```

The Flatpak isolates Qt, GLib, Python, PortAudio, and the transcription stack
from the host distribution. It has narrow access to Wayland/X11, audio, the
network for model downloads, the legacy Cortex Whisper configuration directory,
and the `ydotool` socket.

### Ubuntu `.deb`

Choose the file that exactly matches the Ubuntu release:

```bash
# Ubuntu 24.04
sudo apt install ./cortex-whisper_0.2.0-1_ubuntu24.04_amd64.deb

# Ubuntu 26.04
sudo apt install ./cortex-whisper_0.2.0-1_ubuntu26.04_amd64.deb

cortex-whisper
```

Do not install a 26.04 package on 24.04. Each `.deb` is built and tested inside
its target Ubuntu environment.

### Verify downloads

Run this from the folder containing an artifact and its checksum file:

```bash
sha256sum --check SHA256SUMS-flatpak
# or SHA256SUMS-ubuntu24.04 / SHA256SUMS-ubuntu26.04
```

### Automatic paste on Wayland

Wayland intentionally prevents ordinary applications from injecting keyboard
events. Cortex Whisper therefore copies every result to the clipboard first,
then uses the host `ydotool` service for Ctrl+V when available:

```bash
sudo apt install ydotool
systemctl --user enable --now ydotool.service
systemctl --user status ydotool.service
```

The Flatpak contains only the unprivileged ydotool client and can access only
`$XDG_RUNTIME_DIR/.ydotool_socket`; it does not bundle or start the privileged
daemon. If the service is unavailable, transcription still succeeds and the
text remains on the clipboard for manual Ctrl+V.

### Uninstall

```bash
flatpak uninstall --user io.github.matheusz_nied.CortexWhisper
sudo apt remove cortex-whisper # only for a .deb installation
```

Add `--delete-data` to the Flatpak uninstall command only if you also want to
remove its configuration, logs, and downloaded model cache.

## Usage

1. Start Cortex Whisper and wait until the model is ready.
2. Place the cursor in a text field.
3. Hold **F8** while speaking.
4. Release **F8** to transcribe, copy, and paste.
5. Use the tray menu for Settings, pause, logs, or quit.

GNOME requests global-shortcut and background-start permission through desktop
portals. Cortex Whisper remembers the completed background request and does not
ask on every launch.

## Command line

```bash
cortex-whisper --help
cortex-whisper --version
cortex-whisper --list-microphones
cortex-whisper --diagnostics
cortex-whisper --no-gui --model medium
```

For Flatpak, prefix commands with:

```bash
flatpak run io.github.matheusz_nied.CortexWhisper --diagnostics
```

Terminal mode uses Enter to start and stop recording and `q` to quit.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Text is copied but not pasted | Run `systemctl --user status ydotool.service`; use Ctrl+V while fixing the service. |
| F8 does nothing | Review the Global Shortcuts permission for Cortex Whisper in desktop settings and check whether another app owns F8. |
| No audio is captured | Run `--list-microphones`, select the correct input, then use the built-in microphone test. |
| First startup is slow | The selected Whisper model is downloading; later starts reuse the cache. |
| Flatpak needs a clean reset | Run `flatpak uninstall --user --delete-data io.github.matheusz_nied.CortexWhisper`, then reinstall. |

Logs contain operational events and character counts, never transcribed text.

## Data and privacy

- Audio is processed locally and is not saved.
- Transcribed text is placed in the system clipboard.
- Hugging Face is contacted only when model files are needed.
- There is no telemetry.
- Existing native Cortex Whisper preferences are copied on the first Flatpak
  launch; model caches are intentionally not migrated into the sandbox.

| Data | Native Linux | Flatpak |
| --- | --- | --- |
| Configuration | `~/.config/CortexWhisper/` | `~/.var/app/io.github.matheusz_nied.CortexWhisper/config/CortexWhisper/` |
| Logs | `~/.local/state/CortexWhisper/log/` | App-specific Flatpak data directory |
| Models | Hugging Face user cache | App-specific Flatpak cache |

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

## Build packages

```bash
source venv/bin/activate
python -m pip install -r requirements-dev.txt

# On Ubuntu 24.04 or 26.04 only
PYTHON_BIN=venv/bin/python scripts/build_linux.sh

# Requires Flatpak Builder, KDE SDK 6.11, and PySide BaseApp 6.11
scripts/build_flatpak.sh
```

The Flatpak dependency manifest contains immutable URLs and SHA-256 hashes. The
CI builds each `.deb` in its matching Ubuntu container. On Windows, install Inno
Setup and run `scripts\build_windows.ps1`.

## Development

```bash
python -m ruff check .
python -m pytest
python -m compileall -q cortex_whisper.py src
```

The `CI and release` workflow runs tests on every push and pull request. Manual
runs and `v*` tags also build Flatpak, Ubuntu 24.04/26.04 `.deb` packages, and
the experimental Windows installer. A tag creates a GitHub pre-release.

## Known limitations

- GNOME/Wayland is the primary tested desktop.
- Automatic paste on Wayland requires a working host ydotool service.
- CUDA inside Flatpak is best effort; CPU is the supported baseline.
- Linux release artifacts currently target x86_64 only.
- Windows packaging remains experimental; macOS is not implemented.

See the [release checklist](RELEASE_CHECKLIST.md) for the remaining publication
work.

## Contributing and license

Bug reports and focused pull requests are welcome. Include the operating system,
desktop session, microphone, logs, and reproduction steps for integration bugs.

Cortex Whisper is released under the [MIT License](LICENSE). Bundled components
retain their own licenses; see [Third-Party Notices](THIRD_PARTY_NOTICES.md).

Copyright (c) 2026 Matheus Fernandes da Silva.
