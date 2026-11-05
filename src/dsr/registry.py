"""Script Registry – in-memory store of discovered scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from .config import ConfigManager
from .discovery import ScriptDiscovery, ScriptInfo


class ScriptRegistry:
    def __init__(self, config: ConfigManager):
        self.config = config
        self._scripts: Dict[str, ScriptInfo] = {}
        self.refresh()

    def refresh(self) -> int:
        """Re-discover scripts from configured directories. Returns count."""
        roots = self.config.get_script_roots()
        discovery = ScriptDiscovery(roots)
        self._scripts = discovery.discover()

        # Apply aliases from config
        for alias, target in self.config.config.aliases.items():
            if target in self._scripts and alias not in self._scripts:
                self._scripts[alias] = self._scripts[target]

        return len(self._scripts)

    def get(self, name: str) -> Optional[ScriptInfo]:
        # Resolve alias first
        resolved = self.config.resolve_alias(name)
        return self._scripts.get(resolved) or self._scripts.get(name)

    def list(self, category: Optional[str] = None) -> List[ScriptInfo]:
        scripts = list(self._scripts.values())
        # Deduplicate by path
        seen = set()
        unique = []
        for s in scripts:
            key = str(s.path)
            if key not in seen:
                seen.add(key)
                if category is None or s.category == category:
                    unique.append(s)
        return sorted(unique, key=lambda x: (x.category, x.name))

    def search(self, query: str) -> List[ScriptInfo]:
        q = query.lower()
        results = []
        seen = set()
        for s in self._scripts.values():
            key = str(s.path)
            if key in seen:
                continue
            if (
                q in s.name.lower()
                or q in s.category.lower()
                or q in s.description.lower()
                or q in s.relative_path.lower()
            ):
                seen.add(key)
                results.append(s)
        return sorted(results, key=lambda x: x.name)

    def categories(self) -> List[str]:
        return sorted({s.category for s in self._scripts.values()})

    def __len__(self) -> int:
        # Unique by path
        return len({str(s.path) for s in self._scripts.values()})

    def __contains__(self, name: str) -> bool:
        return self.get(name) is not None
