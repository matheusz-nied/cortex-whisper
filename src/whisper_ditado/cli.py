from __future__ import annotations

import json
import os
import platform
import sys

from . import __version__
from .audio import AudioRecorder
from .config import ConfigStore
from .integration import SystemIntegration


def list_microphones() -> int:
    default_found = False
    print("Available microphones:\n")
    for device in AudioRecorder.devices():
        marker = " [default]" if device.is_default else ""
        default_found = default_found or device.is_default
        print(
            f"  {device.index:>3}: {device.name} — {device.host_api}, "
            f"{device.default_sample_rate} Hz{marker}"
        )
    if not default_found:
        print("\nWarning: PortAudio did not report a default input device.")
    return 0


def diagnostics() -> int:
    config = ConfigStore().load()
    integration = SystemIntegration()
    data = {
        "app_version": __version__,
        "python": sys.version.split()[0],
        "system": platform.platform(),
        "session": os.environ.get("XDG_SESSION_TYPE", "n/a"),
        "model": config.model,
        "microphone": config.microphone,
        "hotkey": config.hotkey,
        "paste_backend": integration.paste_backend,
        "microphones": len(AudioRecorder.devices()),
    }
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def run_terminal(model_name: str, microphone: str, language: str = "pt") -> int:
    import numpy as np

    from .transcriber import Transcriber

    transcriber = Transcriber()
    print(f"Loading Whisper {model_name}…")
    info = transcriber.load(model_name)
    print(f"Ready: {info.name} on {info.device.upper()} ({info.compute_type})")
    recorder = AudioRecorder()
    print("Press Enter to start or stop recording; press q to quit.")
    while True:
        command = input().strip().casefold()
        if command in {"q", "quit", "exit"}:
            return 0
        if not recorder.recording:
            device = recorder.start(microphone)
            print(f"🔴 Recording from {device}…")
            continue
        audio = recorder.stop()
        if audio.size == 0 or float(np.abs(audio).max(initial=0.0)) < 0.005:
            print("Audio is empty or too quiet.")
            continue
        print("Transcribing…")
        text = transcriber.transcribe(audio, language)
        print(f"✅ {text}")
