# ✨ UV Setup Complete — All Scripts Ready

Your IoTEL system is now fully configured to use the **UV package manager**. Here's what's been created:

---

## 📦 What Changed

### ✅ UV Scripts Created

**Laptop GCS** (`laptop/`):
- `uv_setup.ps1` — One-time setup (Windows)
- `uv_setup.sh` — One-time setup (Linux/macOS)
- `uv_run.ps1` — Run GCS with voice/settings support (Windows)
- `uv_run.sh` — Run GCS (Linux/macOS)

**RPI Bridge** (`rpi/`):
- `uv_setup.sh` — One-time setup
- `uv_run.sh` — Run drone bridge

**Attacker Console** (`laptop2_attacker/`):
- `uv_setup.ps1` — One-time setup (Windows)
- `uv_setup.sh` — One-time setup (Linux/macOS)
- `uv_run.ps1` — Run attack console with targets (Windows)
- `uv_run.sh` — Run attack console (Linux/macOS)

**System Helpers** (root):
- `START_SYSTEM.ps1` — Interactive startup guide
- `UV_QUICK_REFERENCE.md` — UV commands cheat sheet
- `UV_COMPLETE_SETUP.md` — Full setup walkthrough

---

## 🚀 Quick Start (TL;DR)

### For Laptop GCS (Windows)
```powershell
cd c:\Workspace\IoTEL\laptop

# First time
.\uv_setup.ps1

# Every time
.\uv_run.ps1 -RpiIp 10.58.17.137 -Voice
```

### For RPI (Linux)
```bash
ssh pi@10.58.17.137

cd rpi

# First time
./uv_setup.sh

# Every time
./uv_run.sh 10.58.17.137 5000
```

### For Attacker Console (Windows)
```powershell
cd c:\Workspace\IoTEL\laptop2_attacker

# First time
.\uv_setup.ps1

# Every time
.\uv_run.ps1 -RpiIp 10.193.181.136 -GcsIp 10.193.181.50
```

---

## 🎯 Key Benefits Over pip + venv

| Old Way | UV Way |
|---------|--------|
| `python -m venv .venv` | `uv sync` ✨ |
| `.\.venv\Scripts\Activate` | Automatic! |
| `pip install -r requirements.txt` | Already done! |
| `python script.py` | `uv run python script.py` |
| Manual venv per project | One command per project |
| Virtual environments | Managed transparently |

---

## 📋 All Available Commands

### Laptop GCS
```powershell
# Setup with all optional features (voice control)
.\uv_setup.ps1

# Run basic GCS
.\uv_run.ps1

# Run with custom RPI IP
.\uv_run.ps1 -RpiIp 192.168.1.100

# Run with voice control
.\uv_run.ps1 -RpiIp 192.168.1.100 -Voice

# Custom port
.\uv_run.ps1 -RpiIp 192.168.1.100 -Port 8000

# Show help
.\uv_run.ps1 -Help
```

### RPI Bridge
```bash
# Setup
./uv_setup.sh

# Run with defaults
./uv_run.sh

# Run with custom laptop IP
./uv_run.sh 192.168.1.50

# Custom port
./uv_run.sh 192.168.1.50 5000

# Show help
./uv_run.sh -h
```

### Attacker Console
```powershell
# Setup
.\uv_setup.ps1

# Auto-discover targets
.\uv_run.ps1

# Specify targets
.\uv_run.ps1 -RpiIp 10.193.181.136 -GcsIp 10.193.181.50

# Custom ports
.\uv_run.ps1 -RpiIp 192.168.1.100 -RpiPort 5760 -GcsPort 5000

# Show help
.\uv_run.ps1 -Help
```

---

## 🔧 Manual UV Commands (Advanced)

If you want to run things manually with UV:

```bash
# Navigate to project
cd laptop

# Install dependencies
uv sync --all-extras

# Run Python directly
uv run python laptop_gcs.py --rpi 192.168.1.100

# Run with specific extras
uv run -f voice python laptop_gcs.py

# Install a new package
uv add new_package_name

# Remove a package
uv remove old_package

# Check installed packages
uv pip list
```

---

## ✅ Verification

### Test Each Component

**Laptop GCS**
```powershell
cd laptop
uv run python -c "import flask; import requests; print('✓ GCS OK')"
```

**RPI Bridge**
```bash
cd rpi
uv run python -c "import pymavlink; import serial; print('✓ RPI OK')"
```

**Attacker**
```powershell
cd laptop2_attacker
uv run python -c "import requests; import scapy; print('✓ Attacker OK')"
```

---

## 📚 Documentation Files

- **[UV_QUICK_REFERENCE.md](UV_QUICK_REFERENCE.md)** — Command cheat sheet
- **[UV_COMPLETE_SETUP.md](UV_COMPLETE_SETUP.md)** — Full setup walkthrough
- **[docs/enemy_drone_demo_plan.md.resolved](docs/enemy_drone_demo_plan.md.resolved)** — Architecture
- **[START_SYSTEM.ps1](START_SYSTEM.ps1)** — Interactive setup guide

---

## 🎮 Launch Everything

### Easy Way: Run the Interactive Script
```powershell
.\START_SYSTEM.ps1
```

This will:
1. Ask for your network IPs
2. Display terminal-by-terminal instructions
3. Show checklist for verification
4. Provide learning resources

### Manual Way: Open 3 Terminals

**Terminal 1 - RPI Bridge**
```bash
ssh pi@10.58.17.137
cd rpi
./uv_run.sh YOUR_LAPTOP_IP 5000
```

**Terminal 2 - Laptop GCS**
```powershell
cd c:\Workspace\IoTEL\laptop
.\uv_run.ps1 -RpiIp 10.58.17.137 -Voice
# Open: http://localhost:5000
```

**Terminal 3 - Attacker Console**
```powershell
cd c:\Workspace\IoTEL\laptop2_attacker
.\uv_run.ps1 -RpiIp 10.58.17.137 -GcsIp <YOUR_GCS_IP>
```

---

## 🆘 Need Help?

### UV Not Found
```powershell
# Windows: PowerShell as Admin
irm https://astral.sh/uv/install.ps1 | iex

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Dependencies Not Installing
```bash
cd <project_folder>
uv sync --force --verbose
```

### Can't Connect to RPI
```powershell
# Check if online
ping 10.58.17.137

# Check if port is open
Test-NetConnection -ComputerName 10.58.17.137 -Port 5760
```

### Scripts Won't Execute
```powershell
# Allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Make shell script executable (Linux)
chmod +x ./uv_run.sh
```

---

## 📖 Next Steps

1. **Read** → [UV_COMPLETE_SETUP.md](UV_COMPLETE_SETUP.md)
2. **Run** → `.\START_SYSTEM.ps1`
3. **Verify** → Check all components are running
4. **Test** → Send a voice command or spoof GPS
5. **Learn** → Explore attack phases

---

## 🚀 You're Ready!

Everything is set up to use UV package manager. No more:
- Manual venv activation
- pip install errors
- Dependency conflicts
- Version mismatches

Just **run the scripts and go**! 🎉

---

Last updated: June 21, 2026
