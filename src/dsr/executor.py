"""Execution Engine – safe, timed, logged script execution."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .config import ConfigManager
from .interpreters import InterpreterManager
from .registry import ScriptRegistry
from .security import SecurityError, is_path_safe, redact_secrets, require_confirmation
from .history import HistoryManager


@dataclass
class ExecutionResult:
    script_name: str
    script_path: str
    args: List[str]
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    started_at: str
    finished_at: str
    success: bool
    error_message: Optional[str] = None

    def summary(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"[{status}] {self.script_name}  "
            f"exit={self.exit_code}  "
            f"duration={self.duration_seconds:.2f}s"
        )


class ExecutionEngine:
    def __init__(
        self,
        config: ConfigManager,
        registry: ScriptRegistry,
        history: Optional[HistoryManager] = None,
    ):
        self.config = config
        self.registry = registry
        self.interpreters = InterpreterManager(config)
        self.history = history or HistoryManager(config)

    def run(
        self,
        name: str,
        args: Optional[List[str]] = None,
        confirm: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        args = args or []
        timeout = timeout or self.config.config.execution_timeout_seconds

        script = self.registry.get(name)
        if script is None:
            raise FileNotFoundError(
                f"Script '{name}' not found in registry. "
                f"Run 'runner refresh' or check configured directories."
            )

        # Security: path must be under configured roots
        roots = self.config.get_script_roots()
        if not is_path_safe(script.path, roots):
            raise SecurityError(
                f"Script path '{script.path}' is outside configured script directories."
            )

        # Optional confirmation
        need_confirm = (
            confirm
            if confirm is not None
            else self.config.config.require_confirmation_for_new_scripts
        )
        if need_confirm and not require_confirmation(script.name, script.path):
            raise SecurityError("Execution cancelled by user.")

        cmd = self.interpreters.build_command(script.path, args)

        started = datetime.now(timezone.utc)
        start_ts = time.perf_counter()

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(script.path.parent),  # run from script's directory
                env=None,  # inherit but never inject secrets
            )
            exit_code = proc.returncode
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            error_message = None
        except subprocess.TimeoutExpired as exc:
            exit_code = -1
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
            error_message = f"Execution timed out after {timeout}s"
        except FileNotFoundError as exc:
            exit_code = 127
            stdout = ""
            stderr = str(exc)
            error_message = f"Interpreter or script not found: {exc}"
        except Exception as exc:
            exit_code = 1
            stdout = ""
            stderr = str(exc)
            error_message = str(exc)

        finished = datetime.now(timezone.utc)
        duration = time.perf_counter() - start_ts

        # Redact before storing / displaying
        stdout = redact_secrets(stdout)
        stderr = redact_secrets(stderr)

        result = ExecutionResult(
            script_name=script.name,
            script_path=str(script.path),
            args=args,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=round(duration, 3),
            started_at=started.isoformat(),
            finished_at=finished.isoformat(),
            success=(exit_code == 0 and error_message is None),
            error_message=error_message,
        )

        self.history.record(result)
        return result
