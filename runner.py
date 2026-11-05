#!/usr/bin/env python3
"""
Dynamic Developer Script Runner – main entry point.
Usage:
    python runner.py list
    python runner.py run network-check
    python runner.py network-check --verbose
    python -m dsr.cli ...
"""

import sys
from pathlib import Path

# Ensure the package is importable when running from the project root
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dsr.cli import app

if __name__ == "__main__":
    app()
