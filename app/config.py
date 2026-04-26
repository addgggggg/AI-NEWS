from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    root_dir: Path
    config_path: Path
    data: dict[str, Any]

    def path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return self.root_dir / path

    def get(self, *keys: str, default: Any = None) -> Any:
        current: Any = self.data
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        return current


def load_settings(config_path: str | None = None) -> Settings:
    root_dir = Path(__file__).resolve().parents[1]
    load_dotenv(root_dir / ".env")
    selected = config_path or os.getenv("AI_NEWS_CONFIG") or "config.yaml"
    config_file = Path(selected)
    if not config_file.is_absolute():
        config_file = root_dir / config_file
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")
    with config_file.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return Settings(root_dir=root_dir, config_path=config_file, data=data)


def load_douyin_accounts(settings: Settings) -> list[dict[str, Any]]:
    accounts_file = settings.get("douyin", "accounts_file", default="./config/douyin_accounts.yaml")
    path = settings.path(accounts_file)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return [item for item in data.get("accounts", []) if item.get("enabled", True)]
