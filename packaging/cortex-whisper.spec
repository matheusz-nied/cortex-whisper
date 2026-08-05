import sys
from pathlib import Path

root = Path.cwd()
keyboard_imports = (
    ["pynput.keyboard._win32", "pynput._util.win32"]
    if sys.platform == "win32"
    else ["pynput.keyboard._xorg", "pynput._util.xorg"]
)

a = Analysis(  # noqa: F821
    [str(root / "packaging" / "launcher.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=[
        (str(root / "assets" / "cortex-whisper.svg"), "assets"),
        (str(root / "build" / "legal"), "legal"),
    ],
    hiddenimports=["faster_whisper", "sounddevice", "pynput", *keyboard_imports],
    hookspath=[],
    runtime_hooks=[str(root / "packaging" / "runtime_hooks" / "pyi_rth_av_stub.py")],
    excludes=[
        "av",
        "matplotlib",
        "pytest",
        "ruff",
        "scipy",
        "sympy",
        "torch",
        "torchaudio",
        "torchvision",
        "triton",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)  # noqa: F821
exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="cortex-whisper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    # On Linux, preserve stdout for CLI commands. On Windows, keep the tray
    # application free of a console window.
    console=sys.platform != "win32",
)
coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="cortex-whisper",
)
