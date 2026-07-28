from __future__ import annotations

import json

from pulsar_whisper.config import AppConfig, ConfigStore


def test_defaults_are_product_defaults(tmp_path):
    config = ConfigStore(tmp_path / "config.json").load()
    assert config.model == "small"
    assert config.hotkey == "F8"
    assert config.autostart is True
    assert config.overlay_position == "screen_center"


def test_last_model_is_persisted(tmp_path):
    store = ConfigStore(tmp_path / "config.json")
    config = AppConfig(model="medium", microphone="ME6S USB")
    store.save(config)
    loaded = store.load()
    assert loaded.model == "medium"
    assert loaded.microphone == "ME6S USB"


def test_invalid_values_fall_back_safely(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"model": "gigante", "hotkey": "", "extra": 3}))
    config = ConfigStore(path).load()
    assert config.model == "small"
    assert config.hotkey == "F8"


def test_legacy_configuration_is_copied_without_deleting_the_original(tmp_path):
    current = tmp_path / "PulsarWhisper" / "config.json"
    legacy = tmp_path / "WhisperDitado" / "config.json"
    legacy.parent.mkdir()
    legacy.write_text(json.dumps({"model": "medium", "microphone": "ME6S"}))

    config = ConfigStore(current, legacy).load()

    assert config.model == "medium"
    assert config.microphone == "ME6S"
    assert current.is_file()
    assert legacy.is_file()
