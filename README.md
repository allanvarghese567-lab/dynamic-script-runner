# Dynamic Developer Script Runner

A reusable, modular developer utility that discovers, executes, manages, and monitors external scripts through a centralized command interface.

**Primary experience:** Discover → Select → Pass Arguments → Execute → View Output → Review History

## Features

- **Dynamic Script Discovery** – Automatically finds `.ps1`, `.sh`, `.bat`, `.cmd`, and `.py` scripts under configured directories (including nested folders).
- **Registry & Aliases** – Scripts are registered as commands; aliases are configurable.
- **Safe Execution Engine** – Uses proper interpreters, argument lists (no `shell=True`), timeouts, path validation, and optional confirmation.
- **CLI** – `runner list`, `runner search`, `runner run <name>`, `runner info`, `runner history`, `runner refresh`, `runner config`, plus direct `runner network-check`.
- **Function-style API** – `network_check()`, `aws_check()`, etc. for use from other Python code.
- **Execution History** – JSONL history with duration, exit code, and output previews.
- **Network Diagnostics** – Full office-network script with SSID/BSSID/signal, local & public IP, and QUBIQON approved-IP whitelist check (IPs live in config, not hard-coded).
- **Cross-platform design** – Primary support for Windows; architecture ready for Linux/macOS.

## Quick Start

```bash
# Clone / enter the project
cd dynamic-script-runner

# Install dependencies
python -m pip install -r requirements.txt

# Optional: install PowerShell 7 (recommended on Windows)
# winget install Microsoft.PowerShell

# List discovered scripts
python runner.py list

# Run the network diagnostic
python runner.py run network-check
# or directly
python runner.py network-check

# Pass arguments
python runner.py run app-health --environment production

# Search
python runner.py search network

# History
python runner.py history
```

## Project Structure

```
dynamic-script-runner/
├── runner.py                 # CLI entry point
├── settings.json             # Configuration
├── requirements.txt
├── src/dsr/                  # Core package
│   ├── config.py
│   ├── discovery.py
│   ├── registry.py
│   ├── interpreters.py
│   ├── executor.py
│   ├── security.py
│   ├── history.py
│   ├── cli.py
│   └── api.py
├── scripts/                  # Example / default script root
│   ├── network/
│   │   ├── network-check.ps1
│   │   └── network-check.py
│   ├── aws/
│   ├── git/
│   └── application/
├── config/
├── logs/executions/
└── tests/
```

## Configuration (`settings.json`)

Key settings:

- `script_directories` – list of roots to scan
- `approved_public_ips` – QUBIQON whitelist (used by network-check)
- `default_interpreters` – extension → executable mapping
- `execution_timeout_seconds`
- `require_confirmation_for_new_scripts`
- `aliases` – short names for scripts

Approved IPs can be updated in configuration without touching the diagnostic script.

## Network Diagnostic Notes

The PowerShell version (`network-check.ps1`) collects:

- Connected Wi-Fi SSID, BSSID, signal strength, channel
- Local IPv4, adapter info, default gateway, DNS
- Public IP (multiple fallback services)
- Available networks (brief)
- Whitelist status: **APPROVED** / **NOT APPROVED** / **UNKNOWN**

A Python fallback (`network-check.py`) provides local IP + public IP + whitelist on non-Windows platforms.

## Security

- Scripts must reside under configured roots (path traversal protection).
- Optional interactive confirmation before execution.
- Secrets are redacted from logged output.
- No elevation to Administrator by default.
- Timeouts and cancellation support.
- Argument handling avoids unsafe string concatenation.

## Windows Setup

1. Install Python 3.10+.
2. Install PowerShell 7 (`pwsh`) for best `.ps1` support.
3. `pip install -r requirements.txt`
4. Place your scripts under `scripts/` or add more roots in `settings.json`.
5. Run `python runner.py refresh` then `python runner.py list`.

## Programmatic Use

```python
from dsr.api import network_check, run_script

result = network_check()
print(result.success, result.stdout)

result = run_script("app-health", ["--environment", "staging"])
```

## Extending

- Drop new scripts into any configured directory; run `runner refresh`.
- Add aliases in `settings.json`.
- The execution engine is independent of the CLI – you can build additional UIs on top of `ExecutionEngine` and `ScriptRegistry`.

## License

MIT (or your preferred license).
