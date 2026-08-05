#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VERSION="$("$PYTHON_BIN" -c "import runpy; print(runpy.run_path('src/cortex_whisper/metadata.py')['APP_VERSION'])")"
if [[ -z "${DISTRO_VERSION:-}" ]]; then
  DISTRO_VERSION="$(. /etc/os-release && printf '%s' "$VERSION_ID")"
fi
case "$DISTRO_VERSION" in
  24.04|26.04) ;;
  *)
    echo "Unsupported .deb target: Ubuntu $DISTRO_VERSION (expected 24.04 or 26.04)." >&2
    exit 2
    ;;
esac
DISTRO_TOKEN="${DISTRO_VERSION//./}"
PACKAGE_VERSION="${VERSION}-1~ubuntu${DISTRO_TOKEN}.1"
PACKAGE_FILE="cortex-whisper_${VERSION}-1_ubuntu${DISTRO_VERSION}_amd64.deb"

"$PYTHON_BIN" scripts/collect_licenses.py
"$PYTHON_BIN" -m PyInstaller --noconfirm --clean packaging/cortex-whisper.spec
"$PYTHON_BIN" scripts/prune_qt_components.py dist/cortex-whisper
"$PYTHON_BIN" scripts/prune_linux_system_libraries.py dist/cortex-whisper
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
sed "s/@PACKAGE_VERSION@/$PACKAGE_VERSION/g" packaging/linux/control.in > "$PACKAGE_ROOT/DEBIAN/control"
cp -a dist/cortex-whisper/. "$PACKAGE_ROOT/opt/cortex-whisper/"
cp packaging/linux/cortex-whisper-launcher "$PACKAGE_ROOT/usr/bin/cortex-whisper"
ln -s cortex-whisper "$PACKAGE_ROOT/usr/bin/cortex-whisper-gui"
ln -s cortex-whisper "$PACKAGE_ROOT/usr/bin/whisper-ditado"
cp io.github.matheusz_nied.CortexWhisper.desktop "$PACKAGE_ROOT/usr/share/applications/"
sed "s/@VERSION@/$VERSION/g" \
  packaging/linux/io.github.matheusz_nied.CortexWhisper.metainfo.xml.in \
  > "$PACKAGE_ROOT/usr/share/metainfo/io.github.matheusz_nied.CortexWhisper.metainfo.xml"
cp assets/cortex-whisper.svg \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/scalable/apps/io.github.matheusz_nied.CortexWhisper.svg"
cp -a build/legal/. "$PACKAGE_ROOT/usr/share/doc/cortex-whisper/"
find "$PACKAGE_ROOT" -type d -exec chmod 0755 {} +
find "$PACKAGE_ROOT" -type f -exec chmod 0644 {} +
chmod 0755 "$PACKAGE_ROOT/opt/cortex-whisper/cortex-whisper"
chmod 0755 "$PACKAGE_ROOT/usr/bin/cortex-whisper"
dpkg-deb --root-owner-group --build \
  "$PACKAGE_ROOT" "$PROJECT_DIR/dist/$PACKAGE_FILE"

(
  cd "$PROJECT_DIR/dist"
  sha256sum "$PACKAGE_FILE" > "SHA256SUMS-ubuntu${DISTRO_VERSION}"
)
