#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
PYTHON_BIN="${PYTHON_BIN:-python3}"

"$PYTHON_BIN" scripts/collect_licenses.py
"$PYTHON_BIN" -m PyInstaller --noconfirm --clean packaging/whisper-ditado.spec
"$PYTHON_BIN" scripts/prune_qt_components.py dist/whisper-ditado

PACKAGE_ROOT="$PROJECT_DIR/build/deb-root"
rm -rf "$PACKAGE_ROOT"
install -d "$PACKAGE_ROOT/DEBIAN" "$PACKAGE_ROOT/opt/whisper-ditado" \
  "$PACKAGE_ROOT/usr/bin" "$PACKAGE_ROOT/usr/share/applications" \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/scalable/apps" \
  "$PACKAGE_ROOT/usr/share/doc/whisper-ditado"
cp packaging/linux/control "$PACKAGE_ROOT/DEBIAN/control"
cp -a dist/whisper-ditado/. "$PACKAGE_ROOT/opt/whisper-ditado/"
ln -s /opt/whisper-ditado/whisper-ditado "$PACKAGE_ROOT/usr/bin/whisper-ditado-gui"
ln -s /opt/whisper-ditado/whisper-ditado "$PACKAGE_ROOT/usr/bin/whisper-ditado"
cp io.github.kaizen.WhisperDitado.desktop "$PACKAGE_ROOT/usr/share/applications/"
cp assets/whisper-ditado.svg "$PACKAGE_ROOT/usr/share/icons/hicolor/scalable/apps/"
cp -a build/legal/. "$PACKAGE_ROOT/usr/share/doc/whisper-ditado/"
dpkg-deb --root-owner-group --build \
  "$PACKAGE_ROOT" "$PROJECT_DIR/dist/whisper-ditado_2.0.0_amd64.deb"

if command -v appimagetool >/dev/null 2>&1; then
  APPDIR="$PROJECT_DIR/build/WhisperDitado.AppDir"
  rm -rf "$APPDIR"
  install -d "$APPDIR/usr/bin" "$APPDIR/usr/share/doc/whisper-ditado"
  cp -a dist/whisper-ditado/. "$APPDIR/usr/bin/"
  cp -a build/legal/. "$APPDIR/usr/share/doc/whisper-ditado/"
  cp packaging/linux/AppRun "$APPDIR/AppRun"
  chmod +x "$APPDIR/AppRun"
  cp io.github.kaizen.WhisperDitado.desktop "$APPDIR/"
  cp assets/whisper-ditado.svg "$APPDIR/whisper-ditado.svg"
  ARCH=x86_64 appimagetool "$APPDIR" "$PROJECT_DIR/dist/Whisper-Ditado-2.0.0-x86_64.AppImage"
else
  echo "appimagetool was not found; the .deb was built and the AppImage was skipped."
fi
