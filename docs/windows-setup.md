# Windows Setup Instructions

## Prerequisites

1. **Python 3.10+**  
   Download from https://www.python.org/downloads/ or use `winget install Python.Python.3.12`

2. **PowerShell 7 (recommended)**  
   ```powershell
   winget install Microsoft.PowerShell
   ```
   Verify: `pwsh -Version`

3. **Git** (optional, for cloning)  
   `winget install Git.Git`

## Installation

```powershell
# Clone or copy the project
cd path\to\dynamic-script-runner

# Create virtual environment (recommended)
python -m venv .venv
.\.​venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## First Run

```powershell
python runner.py refresh
python runner.py list
python runner.py run network-check
```

## Adding Your Own Scripts

1. Place `.ps1`, `.bat`, `.cmd`, `.sh` or `.py` files under `scripts\` or any directory listed in `settings.json`.
2. Run `python runner.py refresh`.
3. The new scripts appear in `runner list` and can be executed with `runner run <name>`.

## Configuration

Edit `settings.json` to:

- Add more script directories
- Update the QUBIQON approved public IP list
- Change default interpreters or timeouts
- Define aliases

## Troubleshooting

- **"No suitable interpreter"** – Install PowerShell 7 and ensure `pwsh` is on PATH.
- **Script not found** – Confirm the file is under a configured root and run `runner refresh`.
- **Execution Policy** – The runner invokes PowerShell with `-ExecutionPolicy Bypass` for the specific file only.
