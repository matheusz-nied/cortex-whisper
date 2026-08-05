#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VERSION="$("$PYTHON_BIN" -c "import runpy; print(runpy.run_path('src/cortex_whisper/metadata.py')['APP_VERSION'])")"

"$PYTHON_BIN" scripts/collect_licenses.py
"$PYTHON_BIN" -m PyInstaller --noconfirm --clean packaging/cortex-whisper.spec
"$PYTHON_BIN" scripts/prune_qt_components.py dist/cortex-whisper
"$PYTHON_BIN" scripts/collect_native_notices.py \
  --analysis build/cortex-whisper/Analysis-00.toc \
  --bundle dist/cortex-whisper \
  --legal build/legal
cp -a build/legal/. dist/cortex-whisper/_internal/legal/

PACKAGE_ROOT="$PROJECT_DIR/build/deb-root"
rm -rf "$PACKAGE_ROOT"
install -d "$PACKAGE_ROOT/DEBIAN" "$PACKAGE_ROOT/opt/cortex-whisper" \
  "$PACKAGE_ROOT/usr/bin" "$PACKAGE_ROOT/usr/share/applications" \
  "$PACKAGE_ROOT/usr/share/metainfo" \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/scalable/apps" \
  "$PACKAGE_ROOT/usr/share/doc/cortex-whisper"
sed "s/@VERSION@/$VERSION/g" packaging/linux/control.in > "$PACKAGE_ROOT/DEBIAN/control"
cp -a dist/cortex-whisper/. "$PACKAGE_ROOT/opt/cortex-whisper/"
ln -s /opt/cortex-whisper/cortex-whisper "$PACKAGE_ROOT/usr/bin/cortex-whisper-gui"
ln -s /opt/cortex-whisper/cortex-whisper "$PACKAGE_ROOT/usr/bin/cortex-whisper"
ln -s /opt/cortex-whisper/cortex-whisper "$PACKAGE_ROOT/usr/bin/whisper-ditado"
cp io.github.matheusz_nied.CortexWhisper.desktop "$PACKAGE_ROOT/usr/share/applications/"
sed "s/@VERSION@/$VERSION/g" \
  packaging/linux/io.github.matheusz_nied.CortexWhisper.metainfo.xml.in \
  > "$PACKAGE_ROOT/usr/share/metainfo/io.github.matheusz_nied.CortexWhisper.metainfo.xml"
cp assets/cortex-whisper.svg "$PACKAGE_ROOT/usr/share/icons/hicolor/scalable/apps/"
cp -a build/legal/. "$PACKAGE_ROOT/usr/share/doc/cortex-whisper/"
find "$PACKAGE_ROOT" -type d -exec chmod 0755 {} +
find "$PACKAGE_ROOT" -type f -exec chmod 0644 {} +
chmod 0755 "$PACKAGE_ROOT/opt/cortex-whisper/cortex-whisper"
dpkg-deb --root-owner-group --build \
  "$PACKAGE_ROOT" "$PROJECT_DIR/dist/cortex-whisper_${VERSION}_amd64.deb"

if command -v appimagetool >/dev/null 2>&1; then
  APPDIR="$PROJECT_DIR/build/CortexWhisper.AppDir"
  rm -rf "$APPDIR"
  install -d "$APPDIR/usr/bin" "$APPDIR/usr/share/doc/cortex-whisper" \
    "$APPDIR/usr/share/applications" \
    "$APPDIR/usr/share/icons/hicolor/scalable/apps" \
    "$APPDIR/usr/share/metainfo"
  cp -a dist/cortex-whisper/. "$APPDIR/usr/bin/"
  cp -a build/legal/. "$APPDIR/usr/share/doc/cortex-whisper/"
  cp packaging/linux/AppRun "$APPDIR/AppRun"
  chmod +x "$APPDIR/AppRun"
  cp io.github.matheusz_nied.CortexWhisper.desktop "$APPDIR/"
  cp io.github.matheusz_nied.CortexWhisper.desktop "$APPDIR/usr/share/applications/"
  sed "s/@VERSION@/$VERSION/g" \
    packaging/linux/io.github.matheusz_nied.CortexWhisper.metainfo.xml.in \
    > "$APPDIR/usr/share/metainfo/io.github.matheusz_nied.CortexWhisper.appdata.xml"
  cp assets/cortex-whisper.svg "$APPDIR/cortex-whisper.svg"
  cp assets/cortex-whisper.svg \
    "$APPDIR/usr/share/icons/hicolor/scalable/apps/cortex-whisper.svg"
  # Validate the same metadata explicitly in CI with appstreamcli --no-net.
  # appimagetool's built-in check requires network access for homepage URLs.
  APPIMAGETOOL_ARGS=(--no-appstream)
  if [[ -n "${APPIMAGE_RUNTIME_FILE:-}" ]]; then
    APPIMAGETOOL_ARGS+=(--runtime-file "$APPIMAGE_RUNTIME_FILE")
  fi
  APPIMAGE_PATH="$PROJECT_DIR/dist/Cortex-Whisper-${VERSION}-x86_64.AppImage"
  rm -f "$APPIMAGE_PATH"
  ARCH=x86_64 appimagetool "${APPIMAGETOOL_ARGS[@]}" \
    "$APPDIR" "$APPIMAGE_PATH"
else
  echo "appimagetool was not found; the .deb was built and the AppImage was skipped."
fi

(
  cd "$PROJECT_DIR/dist"
  sha256sum "cortex-whisper_${VERSION}_amd64.deb" > SHA256SUMS
  if [[ -f "Cortex-Whisper-${VERSION}-x86_64.AppImage" ]]; then
    sha256sum "Cortex-Whisper-${VERSION}-x86_64.AppImage" >> SHA256SUMS
  fi
)
