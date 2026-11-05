"""Basic discovery and registry tests."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dsr.config import ConfigManager
from dsr.registry import ScriptRegistry


def test_discovery_finds_network_script():
    config = ConfigManager(ROOT / "settings.json")
    registry = ScriptRegistry(config)
    assert "network-check" in registry or registry.get("network-check") is not None
    script = registry.get("network-check")
    assert script is not None
    assert script.extension in (".ps1", ".py")
    assert script.category == "network"


def test_list_returns_scripts():
    config = ConfigManager(ROOT / "settings.json")
    registry = ScriptRegistry(config)
    scripts = registry.list()
    assert len(scripts) >= 1
