#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

APP_ID="io.github.matheusz_nied.CortexWhisper"
VERSION="$(python3 -c "import runpy; print(runpy.run_path('src/cortex_whisper/metadata.py')['APP_VERSION'])")"
BUILD_DIR="$PROJECT_DIR/build/flatpak-build"
REPO_DIR="$PROJECT_DIR/build/flatpak-repo"
BUNDLE="$PROJECT_DIR/dist/Cortex-Whisper-${VERSION}-x86_64.flatpak"

mkdir -p "$PROJECT_DIR/dist"
if command -v flatpak-builder >/dev/null 2>&1; then
  BUILDER=(flatpak-builder)
else
  BUILDER=(flatpak run --filesystem=host --share=network org.flatpak.Builder)
fi

"${BUILDER[@]}" --disable-rofiles-fuse --default-branch=stable --force-clean \
  --repo="$REPO_DIR" "$BUILD_DIR" \
  io.github.matheusz_nied.CortexWhisper.yml
flatpak build-bundle "$REPO_DIR" "$BUNDLE" "$APP_ID" stable
(
  cd "$PROJECT_DIR/dist"
  sha256sum "$(basename "$BUNDLE")" > SHA256SUMS-flatpak
)
