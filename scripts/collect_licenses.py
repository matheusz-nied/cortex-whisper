"""Collect license material from the environment used to build a release."""

from __future__ import annotations

import argparse
import platform
import re
import shutil
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path

RUNTIME_DISTRIBUTIONS = (
    "anyio",
    "av",
    "certifi",
    "cffi",
    "click",
    "ctranslate2",
    "evdev",
    "faster-whisper",
    "filelock",
    "flatbuffers",
    "fsspec",
    "h11",
    "hf-xet",
    "httpcore",
    "httpx",
    "huggingface-hub",
    "idna",
    "jeepney",
    "Jinja2",
    "MarkupSafe",
    "numpy",
    "onnxruntime",
    "packaging",
    "Pillow",
    "platformdirs",
    "protobuf",
    "pycparser",
    "Pygments",
    "pynput",
    "PySide6",
    "PySide6-Addons",
    "PySide6-Essentials",
    "python-xlib",
    "PyYAML",
    "setuptools",
    "shiboken6",
    "six",
    "sounddevice",
    "tokenizers",
    "tqdm",
    "typing-extensions",
)

BUILD_DISTRIBUTIONS = (
    "PyInstaller",
    "pyinstaller-hooks-contrib",
)

WINDOWS_DISTRIBUTIONS = ("colorama",)
EXCLUDED_FROM_FROZEN = {"av"}
LEGAL_FILE_NAMES = re.compile(r"^(licen[cs]e|copying|notice|thirdparty)", re.IGNORECASE)
TEXT_SUFFIXES = {"", ".md", ".rst", ".txt"}


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")


def _license_files(package_name: str):
    package = distribution(package_name)
    declared = set(package.metadata.get_all("License-File") or [])
    declared_names = {Path(name).name for name in declared}
    candidates = []
    for entry in package.files or ():
        entry_text = str(entry)
        if entry_text in declared or entry.name in declared_names or (
            LEGAL_FILE_NAMES.match(entry.name) and entry.suffix.lower() in TEXT_SUFFIXES
        ):
            path = package.locate_file(entry)
            if path.is_file() and "__pycache__" not in path.parts:
                candidates.append((entry_text, path))
    return package, sorted(candidates)


def collect(project_root: Path, output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    licenses_dir = output / "licenses"
    licenses_dir.mkdir(parents=True)

    shutil.copy2(project_root / "LICENSE", output / "LICENSE")
    shutil.copy2(project_root / "THIRD_PARTY_NOTICES.md", output / "THIRD_PARTY_NOTICES.md")

    inventory = [
        "# Bundled component inventory",
        "",
        "Generated from the Python environment used for this build.",
        "",
        "| Distribution | Version | Declared license | Release status | Copied license files |",
        "| --- | --- | --- | --- | ---: |",
        f"| CPython | {platform.python_version()} | PSF-2.0 | bundled | 0 |",
    ]
    missing = []
    names = RUNTIME_DISTRIBUTIONS + BUILD_DISTRIBUTIONS + WINDOWS_DISTRIBUTIONS
    for name in names:
        try:
            package, legal_files = _license_files(name)
        except PackageNotFoundError:
            continue

        metadata = package.metadata
        display_name = metadata.get("Name", name)
        license_expression = metadata.get("License-Expression") or metadata.get("License") or "See notice"
        license_expression = " ".join(license_expression.split()).replace("|", "/")
        status = "excluded from frozen app" if name.lower() in EXCLUDED_FROM_FROZEN else "build environment"
        target = licenses_dir / f"{_safe_name(display_name)}-{package.version}"
        target.mkdir()
        copied = 0
        used_names: set[str] = set()
        for relative, source in legal_files:
            filename = _safe_name(Path(relative).name)
            if filename in used_names:
                filename = f"{copied + 1:02d}-{filename}"
            used_names.add(filename)
            shutil.copy2(source, target / filename)
            copied += 1

        if not copied:
            target.rmdir()
            missing.append(display_name)
        inventory.append(
            f"| {display_name} | {package.version} | {license_expression} | {status} | {copied} |"
        )

    inventory.extend(
        [
            "",
            "Packages without a license file in their installed wheel are still identified in",
            "`THIRD_PARTY_NOTICES.md`; shared standard license texts are supplied by other",
            "bundled packages. Verify upstream notices whenever dependency versions change.",
            "",
            "No wheel license file found for: " + (", ".join(missing) if missing else "none"),
            "",
        ]
    )
    (output / "BUNDLED_COMPONENTS.md").write_text("\n".join(inventory), encoding="utf-8")
    for path in output.rglob("*"):
        path.chmod(0o755 if path.is_dir() else 0o644)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("build/legal"))
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parent.parent
    output = args.output if args.output.is_absolute() else project_root / args.output
    collect(project_root, output)
    print(f"License material collected in {output}")


if __name__ == "__main__":
    main()
