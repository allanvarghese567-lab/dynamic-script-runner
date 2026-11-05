"""Script Discovery Service."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

SUPPORTED_EXTENSIONS = {".ps1", ".sh", ".bat", ".cmd", ".py"}


@dataclass
class ScriptInfo:
    name: str
    path: Path
    relative_path: str
    extension: str
    category: str
    description: str = ""
    aliases: List[str] = field(default_factory=list)

    @property
    def command_name(self) -> str:
        """Canonical command name (filename without extension)."""
        return self.name


class ScriptDiscovery:
    """Recursively discovers scripts under configured roots."""

    def __init__(self, roots: List[Path]):
        self.roots = [r.resolve() for r in roots]

    def discover(self) -> Dict[str, ScriptInfo]:
        registry: Dict[str, ScriptInfo] = {}
        seen_paths: Set[Path] = set()

        for root in self.roots:
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    continue
                resolved = path.resolve()
                if resolved in seen_paths:
                    continue
                # Security: ensure the file is still under a configured root
                if not any(self._is_under(resolved, r) for r in self.roots):
                    continue

                seen_paths.add(resolved)
                info = self._build_info(resolved, root)
                # Prefer first occurrence; later ones can be registered under relative name
                if info.command_name not in registry:
                    registry[info.command_name] = info
                # Also register under category-prefixed name for uniqueness
                prefixed = f"{info.category}-{info.command_name}"
                if prefixed not in registry:
                    registry[prefixed] = info

        return registry

    def _is_under(self, path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False

    def _build_info(self, path: Path, root: Path) -> ScriptInfo:
        rel = path.relative_to(root)
        category = rel.parts[0] if len(rel.parts) > 1 else "root"
        name = path.stem
        description = self._extract_description(path)
        return ScriptInfo(
            name=name,
            path=path,
            relative_path=str(rel),
            extension=path.suffix.lower(),
            category=category,
            description=description,
        )

    def _extract_description(self, path: Path) -> str:
        """Try to pull a short description from the first comment block."""
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")[:2000]
        except Exception:
            return ""

        # PowerShell / shell style comments
        patterns = [
            r"^\s*#\s*(.+)$",  # # comment
            r"^\s*<!--\s*(.+?)\s*-->",  # HTML style (rare)
            r'^\s*"""\s*(.+?)\s*"""',  # Python docstring start
        ]
        for line in text.splitlines()[:30]:
            for pat in patterns:
                m = re.match(pat, line.strip())
                if m:
                    desc = m.group(1).strip()
                    if len(desc) > 8:
                        return desc[:200]
        return ""
