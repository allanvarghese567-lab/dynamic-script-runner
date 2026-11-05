"""Security helpers – path validation, confirmation, redaction."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional


class SecurityError(Exception):
    pass


def is_path_safe(script_path: Path, allowed_roots: List[Path]) -> bool:
    """Ensure the script path resolves inside one of the allowed roots."""
    try:
        resolved = script_path.resolve()
    except Exception:
        return False

    for root in allowed_roots:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


def require_confirmation(script_name: str, path: Path) -> bool:
    """Interactive confirmation for untrusted / new scripts.
    Returns True if the user confirms.
    """
    print(f"\n[SECURITY] About to execute external script:")
    print(f"  Name : {script_name}")
    print(f"  Path : {path}")
    answer = input("Proceed? [y/N]: ").strip().lower()
    return answer in ("y", "yes")


def redact_secrets(text: str) -> str:
    """Best-effort redaction of common secret patterns from log output."""
    import re

    patterns = [
        (r"(?i)(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key)\s*[=:]\s*\S+", r"\1=***REDACTED***"),
        (r"(?i)(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*", r"\1***REDACTED***"),
        (r"(?i)(sk-[A-Za-z0-9]{20,})", r"***REDACTED***"),
    ]
    for pat, repl in patterns:
        text = re.sub(pat, repl, text)
    return text
