"""
Dynamic Script Runner (DSR)
A reusable developer utility for discovering, executing, and managing external scripts.
"""

__version__ = "1.0.0"
__author__ = "Allan Varghese"

from .config import ConfigManager
from .registry import ScriptRegistry
from .executor import ExecutionEngine

__all__ = ["ConfigManager", "ScriptRegistry", "ExecutionEngine"]
