# Whisper Ditado Release Checklist

This document tracks the work required for the first public release. Update each
item from `[ ]` to `[x]` only after it has been implemented and verified.

## Current release target

- Recommended version: `v0.1.0 Beta`
- Primary platform: Linux x86_64 with GNOME/Wayland
- Linux/X11 status: implemented, broader testing required
- Windows status: experimental and not validated on real hardware
- macOS status: not implemented
- Interface and documentation language: English
- Default transcription language: Portuguese (`pt`)

## Next action

Complete these decisions before changing release identifiers or legal files:

- [x] Choose the project license: MIT.
- [x] Choose the copyright holder name: `Matheus Fernandes da Silva`.
- [x] Confirm the first public version: `v0.1.0 Beta`.
- [x] Confirm the GitHub user or organization: `matheusz-nied`.
- [x] Choose a public maintainer email address: `matheusz.nied@gmail.com`.

Decision record:

| Decision | Value |
| --- | --- |
| License | MIT |
| Copyright holder | Matheus Fernandes da Silva |
| First public version | `v0.1.0 Beta` |
| GitHub owner | `matheusz-nied` |
| Public maintainer email | `matheusz.nied@gmail.com` |
| Final repository URL | `https://github.com/matheusz-nied/whisper-ditado` (planned) |
| Final Linux application ID | `io.github.kaizen.WhisperDitado` — must be confirmed |

## 1. License the project

Without an explicit license, publishing the source does not clearly authorize
other people to use, modify, or redistribute it.

- [x] Review the available license models.
- [x] Select MIT, Apache-2.0, GPL-3.0, or another appropriate license: MIT.
- [x] Add a root `LICENSE` file using the official, unmodified license text.
- [x] Insert the correct year and copyright holder.
- [x] Declare the SPDX license identifier in `pyproject.toml`.
- [x] Update the License section in `README.md`.
- [ ] Confirm that GitHub detects the license on the repository page.

Recommended copyright line:

```text
Copyright (c) 2026 Matheus Fernandes da Silva
```

References:

- [GitHub: Licensing a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
- [Choose a License: MIT](https://choosealicense.com/licenses/mit/)

## 2. Document third-party licenses

The project license applies to original Whisper Ditado code. Bundled dependencies
retain their own licenses.

- [ ] Create `THIRD_PARTY_NOTICES.md`.
- [ ] Record every direct runtime dependency, version, project URL, and license.
- [ ] Review transitive dependencies included by PyInstaller.
- [ ] Include the relevant license texts in binary distributions.
- [ ] Add license files to the Debian package under
      `/usr/share/doc/whisper-ditado/`.
- [ ] Add license files to the AppImage.
- [ ] Add license files to the Windows installer.
- [ ] Review LGPL obligations for PySide6/Qt and `pynput`.
- [ ] Confirm that bundled Qt libraries remain dynamically loadable and replaceable.
- [ ] Obtain legal review before significant commercial distribution, if needed.

Known direct dependencies requiring review:

| Dependency | Current license information |
| --- | --- |
| `faster-whisper` | MIT |
| `numpy` | BSD family |
| `platformdirs` | MIT |
| `sounddevice` | MIT |
| `pynput` | LGPLv3 |
| `PySide6` / Qt | LGPL/GPL or commercial terms |

Reference:

- [Qt for Python licenses](https://doc.qt.io/qtforpython-6.9/licenses.html)

## 3. Establish release identity and versioning

The current internal version is `2.0.0`. A beta version is more appropriate for
the first public Linux-tested release.

- [x] Decide between `v0.1.0 Beta` and `v1.0.0`: `v0.1.0 Beta`.
- [ ] Centralize the version in one source file.
- [ ] Remove hard-coded version duplication from Python, Debian, Inno Setup, and build scripts.
- [ ] Generate artifact names from the central version.
- [ ] Confirm the final product name: `Whisper Ditado`.
- [x] Confirm the final GitHub owner: `matheusz-nied`.
- [ ] Replace `local@whisper-ditado.invalid` with a public maintainer email.
- [ ] Confirm or change `io.github.kaizen.WhisperDitado` before the first release.
- [ ] Confirm the Windows application GUID will remain stable.
- [ ] Check for naming conflicts and avoid implying official affiliation with Whisper's creators.

Changing the Linux application ID after release may affect settings, autostart,
desktop integration, and GNOME shortcut permissions.

## 4. Publish the source repository

Current local state:

- [x] Git repository created.
- [x] Default branch is `main`.
- [x] Commit history exists.
- [ ] Remote repository configured.

Steps:

- [ ] Create an empty GitHub repository named `whisper-ditado`.
- [ ] Do not generate another README, license, or `.gitignore` during creation.
- [ ] Add the remote:

```bash
git remote add origin REPOSITORY_URL
git push -u origin main
```

- [ ] Add this repository description:

```text
Private, local voice dictation powered by faster-whisper.
```

- [ ] Add repository topics:

```text
whisper speech-to-text dictation voice-recognition faster-whisper
linux wayland python pyside6 privacy
```

- [ ] Add the final repository URL to `README.md` and package metadata.
- [ ] Configure branch protection for `main`.
- [ ] Require CI checks before merging pull requests.
- [ ] Decide whether to enable Issues and Discussions.

## 5. Add community and maintenance files

- [x] Create a launch-oriented English `README.md`.
- [x] Add real overlay images to the README.
- [ ] Add `CHANGELOG.md`.
- [ ] Add `CONTRIBUTING.md`.
- [ ] Add `SECURITY.md` with a private vulnerability-reporting method.
- [ ] Add `CODE_OF_CONDUCT.md` if community contributions are expected.
- [ ] Add GitHub issue templates for bugs and feature requests.
- [ ] Add a pull request template with a test checklist.

## 6. Complete Linux package metadata

- [x] Build a Debian package locally.
- [x] Build an AppImage locally.
- [x] Provide a desktop entry and scalable icon.
- [x] Declare `ydotool` and `wl-clipboard` package recommendations.
- [ ] Add `io.github.kaizen.WhisperDitado.metainfo.xml`.
- [ ] Include name, summary, description, version, license, and launchable ID.
- [ ] Validate AppStream metadata:

```bash
appstreamcli validate io.github.kaizen.WhisperDitado.metainfo.xml
```

- [ ] Install license and third-party notice files with every package.
- [ ] Verify Debian package ownership and permissions.
- [ ] Verify application menu integration.
- [ ] Verify upgrade from one package version to the next.
- [ ] Verify clean uninstallation.

## 7. Build on a compatible Linux baseline

Locally built artifacts currently depend on the host system's newer glibc and
should not be published as universal Linux release artifacts.

- [ ] Pin the Linux GitHub Actions runner instead of using `ubuntu-latest`.
- [ ] Choose `ubuntu-22.04` or `ubuntu-24.04` as the build baseline.
- [ ] Build the public `.deb` and AppImage in CI.
- [ ] Test on Ubuntu 22.04.
- [ ] Test on Ubuntu 24.04.
- [ ] Test on the current development machine.
- [ ] Document that the initial release supports x86_64/amd64 only.
- [ ] Decide whether ARM64 support belongs on the roadmap.

## 8. Strengthen automated tests and CI

- [x] Run unit tests on Linux locally.
- [x] Run Ruff locally.
- [x] Compile all Python sources locally.
- [x] Validate packaged English CLI output locally.
- [ ] Test the minimum supported Python version, currently Python 3.10.
- [ ] Test the primary build version, recommended Python 3.13.
- [ ] Keep Python 3.14 as an additional compatibility job if desired.
- [ ] Add packaged executable smoke tests:

```bash
whisper-ditado --version
whisper-ditado --help
whisper-ditado --diagnostics
```

- [ ] Validate the Debian control metadata in CI.
- [ ] Validate AppStream metadata in CI.
- [ ] Generate `SHA256SUMS` automatically.
- [ ] Upload packages to a GitHub Release, not only workflow artifacts.
- [ ] Pin or verify downloaded packaging tools such as `appimagetool`.
- [ ] Consider pinning GitHub Actions by commit SHA.

## 9. Secure dependencies and releases

- [ ] Enable the GitHub dependency graph.
- [ ] Enable Dependabot alerts.
- [ ] Enable Dependabot security updates.
- [ ] Add `.github/dependabot.yml` for Python and GitHub Actions updates.
- [ ] Enable secret scanning if available.
- [ ] Review dependencies before each release.
- [ ] Produce a dependency license report.
- [ ] Consider producing an SBOM for release artifacts.
- [ ] Create and publish `SHA256SUMS`.
- [ ] Decide whether to sign tags with GPG or SSH.
- [ ] Decide whether to sign Linux artifacts.
- [ ] Plan Windows code signing before claiming stable Windows support.

Reference:

- [GitHub: Dependabot quickstart](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/dependabot-quickstart)

## 10. Perform clean-environment Linux testing

Use a clean virtual machine or a separate user account without existing model
caches, settings, virtual environments, or development packages.

- [ ] Install the `.deb` on a clean supported Ubuntu system.
- [ ] Launch from the application menu.
- [ ] Approve the GNOME global shortcut.
- [ ] Verify first-run model download.
- [ ] Verify microphone selection.
- [ ] Verify the three-second microphone test.
- [ ] Verify hold F8, record, release, transcribe, copy, and paste.
- [ ] Test paste in a browser text field.
- [ ] Test paste in a text editor.
- [ ] Test paste in VS Code or another IDE.
- [ ] Test a multi-monitor layout.
- [ ] Confirm that the overlay appears on the active monitor.
- [ ] Confirm that the overlay never steals focus.
- [ ] Test switching from `small` to `medium`.
- [ ] Confirm model selection persists after restart.
- [ ] Test automatic startup after signing out and back in.
- [ ] Test pause and resume from the tray menu.
- [ ] Test Ctrl+C when launched from a terminal.
- [ ] Test log rotation and the Open Logs action.
- [ ] Test uninstall and confirm no broken processes remain.
- [ ] Ask at least two other Linux users to test the release candidate.

## 11. Publish privacy and security information

- [x] Document that transcription is local.
- [x] Document that audio remains in memory and is not saved to disk.
- [x] Document clipboard use.
- [x] Document model downloads.
- [x] Avoid logging transcribed text.
- [ ] Add a short standalone privacy policy for the future landing page.
- [ ] Explicitly state that there is no telemetry.
- [ ] Document which third-party domains may be contacted for model downloads.
- [ ] Audit exception paths to ensure transcribed text is never logged.
- [ ] Add a private security contact method.

## 12. Prepare release media

- [x] Add recording, decoding, and success overlay images.
- [ ] Add a settings window screenshot.
- [ ] Record a short F8-to-text demonstration GIF or video.
- [ ] Export application icons in Linux and Windows sizes.
- [ ] Create a Windows `.ico` file.
- [ ] Create a `1280 × 640` social preview image.
- [ ] Write a short product description.
- [ ] Write a longer release description.
- [ ] Prepare a visible Known Limitations section for release notes.

Suggested short description:

```text
Whisper Ditado is a private, local voice dictation app. Hold F8, speak,
and release to transcribe and paste anywhere.
```

## 13. Validate Windows before claiming support

- [x] Implement the Windows hotkey, clipboard, autostart, and installer paths.
- [x] Configure a Windows build job.
- [ ] Build the installer successfully on the Windows CI runner.
- [ ] Test on a real Windows 10 machine.
- [ ] Test on a real Windows 11 machine.
- [ ] Test global hotkey press and release behavior.
- [ ] Test microphone enumeration and recording.
- [ ] Test Unicode clipboard and automatic paste.
- [ ] Test tray behavior and automatic startup.
- [ ] Test model download and persistence.
- [ ] Add a Windows application icon.
- [ ] Investigate code signing and SmartScreen reputation.
- [ ] Keep Windows marked Experimental until these items pass.

## 14. Plan macOS support separately

macOS is not part of the first release.

- [ ] Design native microphone permission handling.
- [ ] Design Accessibility permission handling for paste automation.
- [ ] Implement a macOS global hotkey backend.
- [ ] Implement menu bar integration.
- [ ] Implement macOS autostart.
- [ ] Create a signed `.app` bundle.
- [ ] Add Apple notarization.
- [ ] Test on supported Intel and Apple Silicon machines.

## 15. Create the first GitHub release

- [ ] Merge all release preparation changes into `main`.
- [ ] Confirm the working tree is clean.
- [ ] Confirm CI passes on the release commit.
- [ ] Create an annotated tag:

```bash
git tag -a v0.1.0 -m "Whisper Ditado v0.1.0 Beta"
git push origin v0.1.0
```

- [ ] Create a draft GitHub Release from the tag.
- [ ] Mark it as a pre-release.
- [ ] Attach the CI-built `.deb`.
- [ ] Attach the CI-built AppImage.
- [ ] Attach `SHA256SUMS`.
- [ ] Include installation instructions.
- [ ] Include supported platforms.
- [ ] Include known limitations.
- [ ] Publish the release.
- [ ] Install and test the artifacts downloaded from the public Release page.

Reference:

- [GitHub: About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)

## 16. Build the landing page

Create the landing page after a stable repository and Release URL exist.

- [ ] Add a concise hero statement.
- [ ] Add a demonstration video or GIF.
- [ ] Explain local processing and privacy.
- [ ] Add a Download for Linux button pointing to the GitHub Release.
- [ ] Show supported and experimental platforms honestly.
- [ ] Document GNOME/Wayland, `wl-copy`, and `ydotool` requirements.
- [ ] Add an FAQ.
- [ ] Link to the GitHub repository.
- [ ] Link to the license.
- [ ] Link to the privacy policy.
- [ ] Add release notes or a changelog link.

## Recommended execution order

- [x] 1. Choose license, copyright holder, GitHub owner, email, and public version.
- [ ] 2. Add legal files and third-party notices.
- [ ] 3. Centralize versioning and finalize application identifiers.
- [ ] 4. Add community, AppStream, privacy, and security files.
- [ ] 5. Improve CI and release automation.
- [ ] 6. Create and push the GitHub repository.
- [ ] 7. Produce a release candidate from the pinned CI environment.
- [ ] 8. Test on clean Linux systems and with external testers.
- [ ] 9. Publish `v0.1.0 Beta`.
- [ ] 10. Build the landing page around the public Release URL.
