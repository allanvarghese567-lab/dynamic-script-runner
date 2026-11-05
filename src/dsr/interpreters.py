"""Interpreter Manager – maps file extensions to executable interpreters."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .config import ConfigManager


class InterpreterManager:
    def __init__(self, config: ConfigManager):
        self.config = config
        self._cache: Dict[str, Optional[str]] = {}

    def resolve(self, extension: str) -> Optional[str]:
        ext = extension.lower()
        if ext in self._cache:
            return self._cache[ext]

        preferred = self.config.get_interpreter(ext)
        candidates: List[str] = []

        if preferred:
            candidates.append(preferred)

        # Platform-aware fallbacks
        if ext == ".ps1":
            candidates.extend(["pwsh", "powershell", "pwsh.exe", "powershell.exe"])
        elif ext == ".sh":
            candidates.extend(["bash", "zsh", "sh"])
        elif ext in (".bat", ".cmd"):
            if sys.platform == "win32":
                candidates.extend(["cmd.exe", "cmd"])
            else:
                # On non-Windows we can try wine or just fail cleanly
                candidates.extend(["cmd.exe"])
        elif ext == ".py":
            candidates.extend([sys.executable, "python3", "python"])

        for cand in candidates:
            path = shutil.which(cand)
            if path:
                self._cache[ext] = path
                return path

        self._cache[ext] = None
        return None

    def build_command(self, script_path: Path, args: List[str]) -> List[str]:
        """Build a safe argument list (no shell=True)."""
        ext = script_path.suffix.lower()
        interpreter = self.resolve(ext)

        if interpreter is None:
            raise RuntimeError(
                f"No suitable interpreter found for '{ext}'. "
                f"Install the required runtime or update settings.json."
            )

        # PowerShell needs special handling for execution policy / file
        if ext == ".ps1":
            return [
                interpreter,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy", "Bypass",
                "-File", str(script_path),
                *args,
            ]

        if ext in (".bat", ".cmd") and sys.platform == "win32":
            return [interpreter, "/c", str(script_path), *args]

        # Generic: interpreter + script + args
        return [interpreter, str(script_path), *args]
