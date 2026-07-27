from __future__ import annotations

import json
import tempfile
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from platformdirs import user_config_dir, user_log_dir

APP_NAME = "WhisperDitado"
APP_AUTHOR = "WhisperDitado"
CONFIG_VERSION = 1


@dataclass(slots=True)
class AppConfig:
    version: int = CONFIG_VERSION
    model: str = "small"
    microphone: str = "ME6S"
    hotkey: str = "F8"
    autostart: bool = True
    overlay_position: str = "cursor"
    language: str = "pt"

    def normalized(self) -> AppConfig:
        if self.model not in {"small", "medium"}:
            self.model = "small"
        self.hotkey = self.hotkey.upper() if self.hotkey else "F8"
        if self.overlay_position not in {"cursor", "bottom_center"}:
            self.overlay_position = "cursor"
        self.version = CONFIG_VERSION
        return self


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(user_config_dir(APP_NAME, APP_AUTHOR)) / "config.json"

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            allowed = {field.name for field in fields(AppConfig)}
            values = {key: value for key, value in raw.items() if key in allowed}
            return AppConfig(**values).normalized()
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return AppConfig()

    def save(self, config: AppConfig) -> None:
        config.normalized()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(asdict(config), ensure_ascii=False, indent=2) + "\n"
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix="config-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary_path = Path(temporary.name)
        temporary_path.replace(self.path)


def log_directory() -> Path:
    path = Path(user_log_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path

