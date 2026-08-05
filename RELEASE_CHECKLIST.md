# Cortex Whisper 0.2.0 Beta release checklist

This checklist distinguishes completed engineering work from validation that
still requires clean machines or other people.

## Release target

- Product: `Cortex Whisper`
- Version/tag: `0.2.0 Beta` / `v0.2.0`
- Application ID: `io.github.matheusz_nied.CortexWhisper`
- Primary package: Flatpak bundle, Linux x86_64
- Native packages: separate Ubuntu 24.04 and 26.04 `.deb` files
- Windows: experimental
- macOS and ARM64: not supported in this release

## Completed

- [x] MIT project license and third-party notices.
- [x] Stable product name, repository URL, desktop ID, icon, and metadata.
- [x] Native QtDBus Global Shortcuts integration; no system-Python DBus helper.
- [x] Flatpak manifest using KDE/PySide BaseApp 6.11.
- [x] Flatpak-pinned Python sources and wheels with SHA-256 hashes.
- [x] PortAudio included in the Flatpak.
- [x] Only the ydotool client included; the privileged daemon stays on the host.
- [x] ydotool corresponding source is attached automatically to tagged releases.
- [x] Third-party notices and native component licenses are included in Flatpak.
- [x] PyAV and FFmpeg codec libraries are excluded from binary packages.
- [x] Narrow ydotool socket permission and clipboard fallback.
- [x] Background/autostart request through the desktop portal.
- [x] One-time native-configuration migration into Flatpak; models are not migrated.
- [x] Dedicated `.deb` names and versions for Ubuntu 24.04 and 26.04.
- [x] Removed Python, dbus-python, and PyGObject package dependencies.
- [x] Removed the legacy portable-package workflow that mixed host and bundled GLib.
- [x] CI tests Python 3.10, 3.13, and 3.14 on Linux plus Python 3.13 on Windows.
- [x] CI builds Flatpak, two Ubuntu packages, and the experimental Windows installer.
- [x] Tag builds create a GitHub pre-release and consolidated checksums.
- [x] Local unit tests and Ruff pass.
- [x] Local Flatpak `--version`, `--self-test`, `--diagnostics`, and SHA-256 pass.
- [x] Local Ubuntu 26.04 `.deb` build, self-test, metadata, and SHA-256 pass.

## Required before tagging v0.2.0

- [ ] Push the current changes to `main`.
- [ ] Run `CI and release` manually and confirm every package job is green.
- [ ] Download every workflow artifact and verify its checksum.
- [ ] Install the Flatpak bundle on a clean GNOME/Wayland user account.
- [ ] Confirm the first-run Global Shortcuts prompt and hold/release F8.
- [ ] Confirm the first-run Background/autostart prompt.
- [ ] Confirm microphone enumeration, three-second input test, and recording.
- [ ] Confirm first model download and a later offline launch.
- [ ] Confirm automatic paste with the host ydotool service running.
- [ ] Stop ydotool and confirm transcription still lands on the clipboard.
- [ ] Test paste in a browser, editor, and IDE.
- [ ] Test settings persistence and native-to-Flatpak preference migration.
- [ ] Test sign-out/sign-in autostart.
- [ ] Test uninstall and reinstall with and without `--delete-data`.
- [ ] Install the 24.04 `.deb` on clean Ubuntu 24.04.
- [ ] Install the 26.04 `.deb` on clean Ubuntu 26.04.
- [ ] Ask at least two other Linux users to test the release candidate.
- [ ] Review GitHub release notes and attach `SHA256SUMS`.

## Repository readiness

- [ ] Require passing CI checks before merging to `main`.
- [ ] Enable dependency graph and Dependabot alerts.
- [ ] Add `SECURITY.md`, `CONTRIBUTING.md`, and issue templates.
- [ ] Add `CHANGELOG.md` with the 0.2.0 entry.
- [ ] Confirm GitHub detects the MIT license.
- [ ] Decide whether to sign tags and release checksums.
- [ ] Consider an SBOM for a later beta.

## Release procedure

```bash
git tag -a v0.2.0 -m "Cortex Whisper 0.2.0 Beta"
git push origin v0.2.0
```

The tag starts the same tested workflow and publishes a pre-release only after
the Flatpak, both `.deb` packages, and the Windows installer succeed.

## Known limitations to publish

- GNOME/Wayland is the primary tested desktop.
- Automatic paste needs the host ydotool daemon; manual Ctrl+V is the fallback.
- CPU is the supported inference baseline; CUDA in Flatpak is best effort.
- The first model download requires network access and may take several minutes.
- Flatpak is currently distributed as a GitHub bundle; Flathub submission comes later.
- Linux builds are x86_64 only.
- Windows is experimental; macOS is not implemented.
