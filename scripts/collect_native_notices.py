"""Inventory native files collected by PyInstaller and copy system notices."""

from __future__ import annotations

import argparse
import ast
import hashlib
import re
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any

NATIVE_TYPES = {"BINARY", "EXTENSION"}


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")


def binary_entries(value: Any) -> Iterator[tuple[str, str, str]]:
    if (
        isinstance(value, tuple)
        and len(value) == 3
        and isinstance(value[0], str)
        and isinstance(value[1], str)
        and value[2] in NATIVE_TYPES
    ):
        yield value
        return
    if isinstance(value, (list, tuple)):
        for child in value:
            yield from binary_entries(child)


def _debian_owner(path: Path) -> tuple[str, str] | None:
    if shutil.which("dpkg-query") is None or not path.is_absolute():
        return None
    result = subprocess.run(
        ["dpkg-query", "-S", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        return None
    owner = result.stdout.splitlines()[0].split(": ", 1)[0]
    version_result = subprocess.run(
        ["dpkg-query", "-W", "-f=${Version}", owner],
        check=False,
        capture_output=True,
        text=True,
    )
    version = version_result.stdout.strip() if version_result.returncode == 0 else "unknown"
    return owner, version


def _bundle_path(bundle: Path, destination: str) -> Path:
    direct = bundle / destination
    if direct.exists():
        return direct
    return bundle / "_internal" / destination


def collect(analysis: Path, bundle: Path, legal: Path) -> None:
    toc = ast.literal_eval(analysis.read_text(encoding="utf-8"))
    entries = sorted(set(binary_entries(toc)))
    rows = []
    copied_packages: set[str] = set()

    for destination, source_text, native_type in entries:
        source = Path(source_text)
        packaged = _bundle_path(bundle, destination)
        if not packaged.is_file():
            continue
        digest = hashlib.sha256(packaged.read_bytes()).hexdigest()[:16]
        owner = _debian_owner(source)
        if owner:
            package, version = owner
            origin = f"Debian `{package}` `{version}`"
            base_package = package.split(":", 1)[0]
            copyright_file = Path("/usr/share/doc") / base_package / "copyright"
            if copyright_file.is_file() and package not in copied_packages:
                target = legal / "licenses" / f"system-{_safe_name(package)}-{_safe_name(version)}"
                target.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(copyright_file, target / "copyright")
                copied_packages.add(package)
        else:
            origin = "Python or build environment"
        rows.append(f"| `{destination}` | {native_type} | {origin} | `{digest}` |")

    document = [
        "# Native component inventory",
        "",
        "Generated from the PyInstaller analysis for this release build. Hashes are",
        "the first 16 hexadecimal characters of each packaged file's SHA-256 digest.",
        "Debian package copyright files are copied into the adjacent `licenses` tree.",
        "",
        "| Packaged file | Type | Origin | SHA-256 prefix |",
        "| --- | --- | --- | --- |",
        *rows,
        "",
    ]
    (legal / "NATIVE_COMPONENTS.md").write_text("\n".join(document), encoding="utf-8")
    for path in legal.rglob("*"):
        path.chmod(0o755 if path.is_dir() else 0o644)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--legal", type=Path, default=Path("build/legal"))
    args = parser.parse_args()
    collect(args.analysis.resolve(), args.bundle.resolve(), args.legal.resolve())
    print(f"Native component inventory written to {args.legal.resolve()}")


if __name__ == "__main__":
    main()
