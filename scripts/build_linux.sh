#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
PYTHON_BIN="${PYTHON_BIN:-python3}"

"$PYTHON_BIN" -m PyInstaller --noconfirm --clean packaging/whisper-ditado.spec

PACKAGE_ROOT="$PROJECT_DIR/build/deb-root"
rm -rf "$PACKAGE_ROOT"
install -d "$PACKAGE_ROOT/DEBIAN" "$PACKAGE_ROOT/opt/whisper-ditado" \
  "$PACKAGE_ROOT/usr/bin" "$PACKAGE_ROOT/usr/share/applications" \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/scalable/apps"
cp packaging/linux/control "$PACKAGE_ROOT/DEBIAN/control"
cp -a dist/whisper-ditado/. "$PACKAGE_ROOT/opt/whisper-ditado/"
ln -s /opt/whisper-ditado/whisper-ditado "$PACKAGE_ROOT/usr/bin/whisper-ditado-gui"
ln -s /opt/whisper-ditado/whisper-ditado "$PACKAGE_ROOT/usr/bin/whisper-ditado"
cp io.github.kaizen.WhisperDitado.desktop "$PACKAGE_ROOT/usr/share/applications/"
cp assets/whisper-ditado.svg "$PACKAGE_ROOT/usr/share/icons/hicolor/scalable/apps/"
dpkg-deb --root-owner-group --build \
  "$PACKAGE_ROOT" "$PROJECT_DIR/dist/whisper-ditado_2.0.0_amd64.deb"

if command -v appimagetool >/dev/null 2>&1; then
  APPDIR="$PROJECT_DIR/build/WhisperDitado.AppDir"
  rm -rf "$APPDIR"
  install -d "$APPDIR/usr/bin"
  cp -a dist/whisper-ditado/. "$APPDIR/usr/bin/"
  cp packaging/linux/AppRun "$APPDIR/AppRun"
  chmod +x "$APPDIR/AppRun"
  cp io.github.kaizen.WhisperDitado.desktop "$APPDIR/"
  cp assets/whisper-ditado.svg "$APPDIR/whisper-ditado.svg"
  ARCH=x86_64 appimagetool "$APPDIR" "$PROJECT_DIR/dist/Whisper-Ditado-2.0.0-x86_64.AppImage"
else
  echo "appimagetool não encontrado; o .deb foi gerado e o AppImage foi ignorado."
fi
