"""Execution History Manager."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .config import ConfigManager


class HistoryManager:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.history_path = Path(config.config.history_file).resolve()
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, result) -> None:
        entry = {
            "script_name": result.script_name,
            "script_path": result.script_path,
            "args": result.args,
            "exit_code": result.exit_code,
            "duration_seconds": result.duration_seconds,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
            "success": result.success,
            "error_message": result.error_message,
            # Store truncated output to keep history lean
            "stdout_preview": (result.stdout or "")[:500],
            "stderr_preview": (result.stderr or "")[:500],
        }
        with open(self.history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def list(self, limit: int = 20) -> List[dict]:
        if not self.history_path.exists():
            return []
        lines = self.history_path.read_text(encoding="utf-8").strip().splitlines()
        entries = []
        for line in reversed(lines[-limit:]):
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries

    def clear(self) -> None:
        if self.history_path.exists():
            self.history_path.write_text("")
