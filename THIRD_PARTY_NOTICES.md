# Third-Party Notices

Whisper Ditado is licensed under the MIT License. The project uses and, in its
binary releases, redistributes third-party components under their own terms.
Those terms are not replaced by the Whisper Ditado license.

Release packages include this notice, the project's `LICENSE`, a generated
component inventory, and the license files supplied by installed distributions.
Versions below describe the environment audited on July 27, 2026. The generated
inventory inside each release is authoritative for that particular build.

## Direct runtime dependencies

| Component | Audited version | License | Project |
| --- | ---: | --- | --- |
| faster-whisper | 1.2.1 | MIT | https://github.com/SYSTRAN/faster-whisper |
| NumPy | 2.5.1 | BSD-3-Clause and bundled notices | https://numpy.org |
| platformdirs | 4.11.0 | MIT | https://github.com/tox-dev/platformdirs |
| pynput | 1.8.2 | LGPL-3.0 | https://github.com/moses-palmer/pynput |
| PySide6 / Qt for Python | 6.11.1 | LGPL-3.0-only (used under this option) | https://pyside.org |
| sounddevice | 0.5.5 | MIT | https://github.com/spatialaudio/python-sounddevice |

## Runtime and bundled transitive components

| Component | Audited version | License | Project |
| --- | ---: | --- | --- |
| anyio | 4.14.2 | MIT | https://github.com/agronholm/anyio |
| PyAV | 18.0.0 | BSD-3-Clause | https://github.com/PyAV-Org/PyAV |
| certifi | 2026.7.22 | MPL-2.0 | https://github.com/certifi/python-certifi |
| CFFI | 2.1.0 | MIT-0 | https://github.com/python-cffi/cffi |
| Click | 8.4.2 | BSD-3-Clause | https://github.com/pallets/click |
| CTranslate2 | 4.8.1 | MIT | https://github.com/OpenNMT/CTranslate2 |
| evdev | 1.9.3 | BSD-3-Clause | https://github.com/gvalkov/python-evdev |
| filelock | 3.32.0 | MIT | https://github.com/tox-dev/filelock |
| FlatBuffers | 25.12.19 | Apache-2.0 | https://github.com/google/flatbuffers |
| fsspec | 2026.6.0 | BSD-3-Clause | https://github.com/fsspec/filesystem_spec |
| h11 | 0.16.0 | MIT | https://github.com/python-hyper/h11 |
| hf-xet | 1.5.2 | Apache-2.0 | https://github.com/huggingface/xet-core |
| httpcore | 1.0.9 | BSD-3-Clause | https://github.com/encode/httpcore |
| HTTPX | 0.28.1 | BSD-3-Clause | https://github.com/encode/httpx |
| huggingface_hub | 1.25.1 | Apache-2.0 | https://github.com/huggingface/huggingface_hub |
| idna | 3.18 | BSD-3-Clause | https://github.com/kjd/idna |
| Jinja2 | 3.1.6 | BSD-3-Clause | https://github.com/pallets/jinja |
| MarkupSafe | 3.0.3 | BSD-3-Clause | https://github.com/pallets/markupsafe |
| ONNX Runtime | 1.28.0 | MIT and bundled notices | https://github.com/microsoft/onnxruntime |
| packaging | 26.2 | Apache-2.0 OR BSD-2-Clause | https://github.com/pypa/packaging |
| Pillow | 12.3.0 | MIT-CMU and bundled notices | https://github.com/python-pillow/Pillow |
| protobuf | 7.35.1 | BSD-3-Clause | https://github.com/protocolbuffers/protobuf |
| pycparser | 3.0 | BSD-3-Clause | https://github.com/eliben/pycparser |
| Pygments | 2.20.0 | BSD-2-Clause | https://github.com/pygments/pygments |
| python-xlib | 0.33 | LGPL-2.0-or-later | https://github.com/python-xlib/python-xlib |
| PyYAML | 6.0.3 | MIT | https://github.com/yaml/pyyaml |
| setuptools | 83.0.0 | MIT | https://github.com/pypa/setuptools |
| shiboken6 | 6.11.1 | LGPL-3.0-only (used under this option) | https://pyside.org |
| six | 1.17.0 | MIT | https://github.com/benjaminp/six |
| tokenizers | 0.23.1 | Apache-2.0 | https://github.com/huggingface/tokenizers |
| tqdm | 4.69.1 | MPL-2.0 AND MIT | https://github.com/tqdm/tqdm |
| typing_extensions | 4.16.0 | PSF-2.0 | https://github.com/python/typing_extensions |

The platform-specific build may also include `colorama` on Windows and native
system or wheel libraries. Their supplied notices are collected when present.

## Python and build tooling

Frozen releases contain the applicable CPython runtime and standard library,
which are distributed under the Python Software Foundation License. PyInstaller
provides the executable bootloader under GPL-2.0-or-later with its special
exception permitting distribution of applications built with PyInstaller. The
release inventory records the exact Python and PyInstaller versions used.

- Python: https://www.python.org/psf/license/
- PyInstaller: https://pyinstaller.org/en/stable/license.html

## Qt and PySide6

Whisper Ditado uses the community PySide6 distribution under LGPL-3.0-only. Qt
shared libraries remain separate dynamically loaded files in the onedir bundle.
Users may inspect, replace, or relink those libraries after extracting a package.
The source code for the corresponding Qt release is available from Qt's official
source archives.

Whisper Ditado does not use Qt Virtual Keyboard. Packaging removes its plugin,
QML module, and libraries because that Qt module is GPL-3.0-only or commercially
licensed, rather than LGPL-3.0.

- Qt for Python licensing: https://doc.qt.io/qtforpython-6/licenses.html
- Qt licensing and GPL-only modules: https://doc.qt.io/qt-6/licensing.html
- Qt source archives: https://download.qt.io/archive/qt/

## PyAV, FFmpeg, and native codec libraries

PyAV wheels contain FFmpeg shared libraries and may contain additional native
codec libraries. The audited Linux wheel reports FFmpeg 8.1.2 under LGPL-3.0-or-
later, but its native library set includes separately licensed components. This
area must be re-audited for every release platform and PyAV wheel before public
binary distribution. In particular, verify the effective FFmpeg configuration,
all codec-library notices, corresponding-source obligations, and that no
non-redistributable component is present.

- PyAV: https://github.com/PyAV-Org/PyAV
- FFmpeg license: https://ffmpeg.org/legal.html

## ONNX Runtime

ONNX Runtime ships an upstream `ThirdPartyNotices.txt`. The build-time collector
copies that file and the ONNX Runtime license into every release package.

## Models

Whisper model files are not bundled with Whisper Ditado. They are downloaded on
first use from the selected model repository. Model weights and their associated
files remain subject to the terms published by their provider.

## No legal advice

This inventory is an engineering compliance aid, not legal advice. Dependency
licenses and binary contents can change. Review the generated inventory and
notices before every public release and obtain qualified legal advice when the
distribution model or commercial risk warrants it.
