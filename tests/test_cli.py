from __future__ import annotations

import json

from cortex_whisper.cli import diagnostics


def test_diagnostics_reports_unavailable_audio_without_crashing(monkeypatch, capsys):
    def unavailable():
        raise RuntimeError("audio service unavailable")

    monkeypatch.setattr("cortex_whisper.cli.AudioRecorder.devices", unavailable)

    assert diagnostics() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["microphones"] is None
    assert result["microphone_error"] == "audio service unavailable"
