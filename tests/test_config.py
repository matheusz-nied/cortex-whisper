from __future__ import annotations

import json

from whisper_ditado.config import AppConfig, ConfigStore


def test_defaults_are_product_defaults(tmp_path):
    config = ConfigStore(tmp_path / "config.json").load()
    assert config.model == "small"
    assert config.hotkey == "F8"
    assert config.autostart is True
    assert config.overlay_position == "cursor"


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

