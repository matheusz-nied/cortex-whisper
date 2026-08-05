"""Persistent configuration and legacy migration."""

from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from platformdirs import user_config_dir, user_log_dir

from .environment import is_flatpak
from .metadata import APP_COMPACT_NAME, LEGACY_COMPACT_NAME

APP_NAME = APP_COMPACT_NAME
CONFIG_VERSION = 3


@dataclass(slots=True)
class AppConfig:
    version: int = CONFIG_VERSION
    model: str = "small"
    microphone: str = "ME6S"
    hotkey: str = "F8"
    autostart: bool = True
    autostart_portal_configured: bool = False
    overlay_position: str = "screen_center"
    language: str = "pt"

    def normalized(self) -> AppConfig:
        if self.version < 2 and self.overlay_position == "cursor":
            self.overlay_position = "screen_center"
        if self.model not in {"small", "medium"}:
            self.model = "small"
        self.hotkey = self.hotkey.upper() if self.hotkey else "F8"
        if self.overlay_position not in {"cursor", "screen_center", "bottom_center"}:
            self.overlay_position = "screen_center"
        self.version = CONFIG_VERSION
        return self


class ConfigStore:
    def __init__(self, path: Path | None = None, legacy_path: Path | None = None) -> None:
        self.path = path or Path(user_config_dir(APP_NAME, appauthor=False)) / "config.json"
        self.legacy_path = legacy_path
        if path is None and legacy_path is None:
            if is_flatpak():
                # The sandbox has its own XDG_CONFIG_HOME. This narrowly exposed
                # host path lets the first Flatpak run import preferences without
                # granting access to Whisper model caches or the rest of $HOME.
                self.legacy_path = Path.home() / ".config" / APP_NAME / "config.json"
            else:
                self.legacy_path = (
                    Path(user_config_dir(LEGACY_COMPACT_NAME, LEGACY_COMPACT_NAME)) / "config.json"
                )

    def load(self) -> AppConfig:
        source = self.path
        migrated = False
        if not source.exists() and self.legacy_path and self.legacy_path.exists():
            source = self.legacy_path
            migrated = True
        if not source.exists():
            return AppConfig()
        try:
            raw = json.loads(source.read_text(encoding="utf-8"))
            allowed = {field.name for field in fields(AppConfig)}
            values = {key: value for key, value in raw.items() if key in allowed}
            config = AppConfig(**values).normalized()
            if migrated:
                try:
                    self.save(config)
                except OSError:
                    pass
            return config
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
    path = Path(user_log_dir(APP_NAME, appauthor=False))
    path.mkdir(parents=True, exist_ok=True)
    legacy = Path(user_log_dir(LEGACY_COMPACT_NAME, LEGACY_COMPACT_NAME))
    if legacy.is_dir() and legacy != path:
        for source in legacy.iterdir():
            target = path / source.name.replace("whisper-ditado", "cortex-whisper")
            if source.is_file() and not target.exists():
                try:
                    shutil.copy2(source, target)
                except OSError:
                    pass
    return path
