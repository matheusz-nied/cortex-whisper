#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VERSION="$("$PYTHON_BIN" -c "import runpy; print(runpy.run_path('src/pulsar_whisper/metadata.py')['APP_VERSION'])")"

"$PYTHON_BIN" scripts/collect_licenses.py
"$PYTHON_BIN" -m PyInstaller --noconfirm --clean packaging/pulsar-whisper.spec
"$PYTHON_BIN" scripts/prune_qt_components.py dist/pulsar-whisper
"$PYTHON_BIN" scripts/collect_native_notices.py \
  --analysis build/pulsar-whisper/Analysis-00.toc \
  --bundle dist/pulsar-whisper \
  --legal build/legal
cp -a build/legal/. dist/pulsar-whisper/_internal/legal/

PACKAGE_ROOT="$PROJECT_DIR/build/deb-root"
rm -rf "$PACKAGE_ROOT"
install -d "$PACKAGE_ROOT/DEBIAN" "$PACKAGE_ROOT/opt/pulsar-whisper" \
  "$PACKAGE_ROOT/usr/bin" "$PACKAGE_ROOT/usr/share/applications" \
  "$PACKAGE_ROOT/usr/share/metainfo" \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/scalable/apps" \
  "$PACKAGE_ROOT/usr/share/doc/pulsar-whisper"
sed "s/@VERSION@/$VERSION/g" packaging/linux/control.in > "$PACKAGE_ROOT/DEBIAN/control"
cp -a dist/pulsar-whisper/. "$PACKAGE_ROOT/opt/pulsar-whisper/"
ln -s /opt/pulsar-whisper/pulsar-whisper "$PACKAGE_ROOT/usr/bin/pulsar-whisper-gui"
ln -s /opt/pulsar-whisper/pulsar-whisper "$PACKAGE_ROOT/usr/bin/pulsar-whisper"
ln -s /opt/pulsar-whisper/pulsar-whisper "$PACKAGE_ROOT/usr/bin/whisper-ditado"
cp io.github.matheusz_nied.PulsarWhisper.desktop "$PACKAGE_ROOT/usr/share/applications/"
sed "s/@VERSION@/$VERSION/g" \
  packaging/linux/io.github.matheusz_nied.PulsarWhisper.metainfo.xml.in \
  > "$PACKAGE_ROOT/usr/share/metainfo/io.github.matheusz_nied.PulsarWhisper.metainfo.xml"
cp assets/pulsar-whisper.svg "$PACKAGE_ROOT/usr/share/icons/hicolor/scalable/apps/"
cp -a build/legal/. "$PACKAGE_ROOT/usr/share/doc/pulsar-whisper/"
find "$PACKAGE_ROOT" -type d -exec chmod 0755 {} +
find "$PACKAGE_ROOT" -type f -exec chmod 0644 {} +
chmod 0755 "$PACKAGE_ROOT/opt/pulsar-whisper/pulsar-whisper"
dpkg-deb --root-owner-group --build \
  "$PACKAGE_ROOT" "$PROJECT_DIR/dist/pulsar-whisper_${VERSION}_amd64.deb"

if command -v appimagetool >/dev/null 2>&1; then
  APPDIR="$PROJECT_DIR/build/PulsarWhisper.AppDir"
  rm -rf "$APPDIR"
  install -d "$APPDIR/usr/bin" "$APPDIR/usr/share/doc/pulsar-whisper" \
    "$APPDIR/usr/share/metainfo"
  cp -a dist/pulsar-whisper/. "$APPDIR/usr/bin/"
  cp -a build/legal/. "$APPDIR/usr/share/doc/pulsar-whisper/"
  cp packaging/linux/AppRun "$APPDIR/AppRun"
  chmod +x "$APPDIR/AppRun"
  cp io.github.matheusz_nied.PulsarWhisper.desktop "$APPDIR/"
  sed "s/@VERSION@/$VERSION/g" \
    packaging/linux/io.github.matheusz_nied.PulsarWhisper.metainfo.xml.in \
    > "$APPDIR/usr/share/metainfo/io.github.matheusz_nied.PulsarWhisper.metainfo.xml"
  cp assets/pulsar-whisper.svg "$APPDIR/pulsar-whisper.svg"
  ARCH=x86_64 appimagetool "$APPDIR" "$PROJECT_DIR/dist/Pulsar-Whisper-${VERSION}-x86_64.AppImage"
else
  echo "appimagetool was not found; the .deb was built and the AppImage was skipped."
fi

(
  cd "$PROJECT_DIR/dist"
  sha256sum "pulsar-whisper_${VERSION}_amd64.deb" > SHA256SUMS
  if [[ -f "Pulsar-Whisper-${VERSION}-x86_64.AppImage" ]]; then
    sha256sum "Pulsar-Whisper-${VERSION}-x86_64.AppImage" >> SHA256SUMS
  fi
)
