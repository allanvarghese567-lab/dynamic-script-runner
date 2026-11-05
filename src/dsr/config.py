"""Configuration Manager for Dynamic Script Runner."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class LoggingConfig(BaseModel):
    level: str = "INFO"
    console: bool = True
    file: bool = True


class AppConfig(BaseModel):
    script_directories: List[str] = Field(default_factory=lambda: ["./scripts"])
    default_interpreters: Dict[str, str] = Field(
        default_factory=lambda: {
            ".ps1": "pwsh",
            ".sh": "bash",
            ".bat": "cmd.exe",
            ".cmd": "cmd.exe",
            ".py": "python",
        }
    )
    approved_public_ips: List[str] = Field(
        default_factory=lambda: ["103.142.31.212", "103.181.238.50"]
    )
    execution_timeout_seconds: int = 120
    require_confirmation_for_new_scripts: bool = True
    log_directory: str = "./logs"
    history_file: str = "./logs/executions/history.jsonl"
    aliases: Dict[str, str] = Field(default_factory=dict)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @field_validator("script_directories", mode="before")
    @classmethod
    def ensure_list(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [v]
        return v or ["./scripts"]


class ConfigManager:
    """Loads, validates and provides access to application configuration."""

    def __init__(self, config_path: Optional[str | Path] = None):
        self.config_path = Path(config_path or "settings.json").resolve()
        self._config: AppConfig = self._load()

    def _load(self) -> AppConfig:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AppConfig(**data)
        # Return defaults and write a starter file
        config = AppConfig()
        self.save(config)
        return config

    def save(self, config: Optional[AppConfig] = None) -> None:
        cfg = config or self._config
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(cfg.model_dump(), f, indent=2)

    @property
    def config(self) -> AppConfig:
        return self._config

    def reload(self) -> AppConfig:
        self._config = self._load()
        return self._config

    def get_script_roots(self) -> List[Path]:
        roots = []
        for d in self._config.script_directories:
            p = Path(d).expanduser().resolve()
            if p.exists() and p.is_dir():
                roots.append(p)
        return roots

    def get_approved_ips(self) -> List[str]:
        return list(self._config.approved_public_ips)

    def get_interpreter(self, extension: str) -> Optional[str]:
        return self._config.default_interpreters.get(extension.lower())

    def resolve_alias(self, name: str) -> str:
        return self._config.aliases.get(name, name)
