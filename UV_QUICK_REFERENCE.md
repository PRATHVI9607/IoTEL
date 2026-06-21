# 🚀 IoTEL — UV Package Manager Quick Reference

## Installation

### Windows (PowerShell)
```powershell
# Install UV
irm https://astral.sh/uv/install.ps1 | iex

# Verify installation
uv --version
```

### macOS / Linux
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

---

## Quick Start — All Three Components

### 1️⃣ Laptop GCS (Defender - Windows)
```powershell
cd c:\Workspace\IoTEL\laptop

# Setup once
.\uv_setup.ps1

# Run GCS
.\uv_run.ps1 -RpiIp 10.58.17.137 -Voice

# Or specific port
.\uv_run.ps1 -RpiIp 192.168.1.100 -Port 8000
```

### 2️⃣ RPI Bridge (Linux/SSH)
```bash
ssh pi@<RPI_IP>
cd rpi

# Setup once
./uv_setup.sh

# Run bridge
./uv_run.sh 10.58.17.137 5000
```

### 3️⃣ Attacker Console (Laptop B - Windows)
```powershell
cd c:\Workspace\IoTEL\laptop2_attacker

# Setup once
.\uv_setup.ps1

# Run with auto-discovery
.\uv_run.ps1

# Or specify targets
.\uv_run.ps1 -RpiIp 10.193.181.136 -GcsIp 10.193.181.50
```

---

## Common UV Commands

### Project Management
```bash
# Install all dependencies from pyproject.toml
uv sync

# Install with optional extras (voice control)
uv sync --all-extras

# Add a new package
uv add requests colorama

# Remove a package
uv remove requests
```

### Running Code
```bash
# Run a Python file
uv run python script.py

# Run with specific dependencies/extras
uv run -f voice python laptop_gcs.py

# Run with arguments
uv run python script.py --arg1 value1 --arg2 value2

# Run shell command in UV environment
uv run -- python --version
```

### Virtual Environment (if needed)
```bash
# Create/use venv folder
uv venv

# Activate venv (Windows)
.venv\Scripts\Activate.ps1

# Activate venv (Linux/macOS)
source .venv/bin/activate

# Run without explicit activation
uv run python script.py
```

---

## 📦 Project Dependencies

### Laptop GCS Dependencies
```toml
[project.dependencies]
flask>=3.0
pymavlink>=2.4.40
pyserial>=3.5
requests>=2.28

[project.optional-dependencies]
voice = [
    "SpeechRecognition>=3.10",
    "pyaudio>=0.2.14",
]
```

### RPI Bridge Dependencies
```toml
[project.dependencies]
pymavlink>=2.4.40
pyserial>=3.5
requests>=2.28
```

### Attacker Console Dependencies
```toml
[project.dependencies]
requests>=2.28
scapy>=2.5
colorama>=0.4.6
```

---

## 📝 Typical Workflow

### First Time Setup
```powershell
# Laptop GCS
cd laptop
.\uv_setup.ps1           # One-time setup
.\uv_run.ps1             # Start running

# In another terminal on RPI
./uv_setup.sh            # One-time
./uv_run.sh             # Start running

# In another terminal on Attacker PC
.\uv_setup.ps1          # One-time
.\uv_run.ps1            # Start running
```

### Subsequent Runs (after initial setup)
```powershell
# Just run the scripts, uv will handle everything
.\uv_run.ps1

# No need for venv activation or manual pip installs
```

### Adding New Dependencies
```bash
cd <project_folder>

# Add to project
uv add new_package_name

# Or manually edit pyproject.toml, then:
uv sync
```

---

## ⚡ UV Advantages Over pip + venv

| Feature | pip + venv | uv |
|---------|-----------|-----|
| Speed | Slow | ⚡ Lightning fast |
| Venv setup | Manual | Automatic |
| Dependency resolution | Can be slow | Instant |
| Python management | Manual | Automatic |
| Lock file | Optional | Built-in |
| Cross-platform | Works if set up right | Always works |
| Virtual env activation | Required (annoying) | Automatic |

---

## 🔧 Troubleshooting

### "uv: command not found"
```bash
# Add UV to PATH (if using Linux/macOS)
export PATH="$HOME/.local/bin:$PATH"

# Or reinstall
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Dependencies not installing
```powershell
# Force re-sync
uv sync --force

# Check for conflicts
uv sync --verbose
```

### Python version mismatch
```powershell
# Check UV's Python version
uv python list

# Use specific Python
uv sync --python 3.11
```

### "Cannot connect to RPI" when running scripts
```bash
# Check network connectivity
ping <RPI_IP>

# Verify ports are accessible
Test-NetConnection -ComputerName <RPI_IP> -Port 5760
```

---

## 📚 UV Documentation

- **Official Docs**: https://docs.astral.sh/uv/
- **Getting Started**: https://docs.astral.sh/uv/getting-started/
- **CLI Reference**: https://docs.astral.sh/uv/reference/cli/
- **Configuration**: https://docs.astral.sh/uv/configuration/

---

## ✅ Verify Your Setup

```powershell
# Check UV installation
uv --version

# Check Python availability
uv python list

# Test project sync
cd laptop
uv sync --all-extras

# Quick test run
uv run python -c "import flask; print('Flask OK')"
```

All set! Start with the quick start commands above. 🚁
