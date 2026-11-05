"""Function-style API for programmatic use."""

from __future__ import annotations

from typing import List, Optional

from .config import ConfigManager
from .registry import ScriptRegistry
from .executor import ExecutionEngine, ExecutionResult
from .history import HistoryManager


def _engine() -> ExecutionEngine:
    config = ConfigManager()
    registry = ScriptRegistry(config)
    history = HistoryManager(config)
    return ExecutionEngine(config, registry, history)


def run_script(name: str, args: Optional[List[str]] = None, **kwargs) -> ExecutionResult:
    """Generic runner."""
    return _engine().run(name, args=args or [], **kwargs)


# Convenience functions matching the required style
def network_check(*args, **kwargs) -> ExecutionResult:
    return run_script("network-check", list(args), **kwargs)


def aws_check(*args, **kwargs) -> ExecutionResult:
    return run_script("aws-check", list(args), **kwargs)


def git_check(*args, **kwargs) -> ExecutionResult:
    return run_script("git-check", list(args), **kwargs)


def app_health(*args, **kwargs) -> ExecutionResult:
    return run_script("app-health", list(args), **kwargs)
