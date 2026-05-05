# 💀 Attacker Laptop — Enemy Drone Detection & Telemetry Misleading

This folder contains all scripts for **Laptop B (Attacker)** as part of the IDP drone security demonstration.

> [!IMPORTANT]
> **Educational use only.** Run these ONLY against your own drone system in a controlled lab environment.

---

## 📁 File Overview

| File | Phase | Purpose |
|------|-------|---------|
| `scanner.py` | Phase 1 | Discover drone (RPI) and GCS (Laptop A) on the network |
| `sniffer.py` | Phase 2 | Passively intercept live telemetry from the drone |
| `telemetry_spoofer.py` | Phase 3A | Inject fake telemetry to the GCS dashboard |
| `cmd_injector.py` | Phase 3B | Send fake commands to the drone via TCP |
| `full_attack.py` | All | Combined menu console for all phases |
| `requirements.txt` | — | Python dependencies |

---

## ⚙️ Setup

```bash
# Install dependencies
pip install -r requirements.txt

# On Windows for scapy (optional, needed for HTTP sniffing):
# Install Npcap from https://npcap.com/
```

---

## 🚀 Quick Start

### Option A — Use the combined console (recommended for demo)
```bash
python full_attack.py
# or pre-set IPs:
python full_attack.py --rpi 10.193.181.136 --gcs 10.193.181.50
```

### Option B — Run phases individually

```bash
# Phase 1: Discover the drone
python scanner.py --subnet 10.193.181.0/24

# Phase 2: Sniff live telemetry
python sniffer.py --rpi 10.193.181.136

# Phase 3A: Spoof GCS dashboard (fake GPS)
python telemetry_spoofer.py --gcs 10.193.181.50 --attack gps

# Phase 3A: Panic battery
python telemetry_spoofer.py --gcs 10.193.181.50 --attack battery

# Phase 3B: Inject a command (interactive)
python cmd_injector.py --rpi 10.193.181.136 --interactive

# Phase 3B: Inject a single command
python cmd_injector.py --rpi 10.193.181.136 --cmd land
```

---

## 🎯 Attack Types (`telemetry_spoofer.py`)

| Attack | Flag | Effect on Laptop A Dashboard |
|--------|------|------------------------------|
| GPS Position Shift | `--attack gps` | Map jumps 500m away |
| GPS Gradual Drift | `--attack drift` | Position slowly drifts (stealthy) |
| Battery Critical | `--attack battery` | Shows 1–5% battery → operator panics |
| Fake Landing | `--attack landing` | Shows drone as landed/disarmed |
| Inject Alerts | `--attack alerts` | Floods dashboard with fake warnings |
| Clear Alerts | `--attack clear` | Hides real anomaly alerts |
| Mode Change | `--attack mode` | Shows wrong flight mode |

---

## ⚡ Injectable Commands (`cmd_injector.py`)

These are sent via TCP to the RPI bridge and executed directly on the Pixhawk:

| Command | Effect |
|---------|--------|
| `land` | Force drone to land |
| `rtl` | Return to launch |
| `loiter` | Switch to hover mode |
| `stabilize` | Switch to manual stabilize |
| `guided` | Switch to guided mode |
| `arm` | ⚠️ Arm motors |
| `disarm` | ⚠️ DANGEROUS — cuts motors mid-flight |
| `takeoff` | ⚠️ Command unauthorized takeoff |

---

## 🗺️ Demo Flow (for presentation)

| Step | What to run | What audience sees |
|------|-------------|-------------------|
| 1 | `scanner.py` | Drone found at IP X, GCS at IP Y |
| 2 | `sniffer.py` | Live GPS, battery, mode intercepted |
| 3 | `telemetry_spoofer.py --attack gps` | Dashboard map jumps to wrong location |
| 4 | `telemetry_spoofer.py --attack battery` | Battery shows 3%, operator panics |
| 5 | `cmd_injector.py --cmd land` | Drone physically lands |
| 6 | Laptop A dashboard | `MODE_CHANGE` and anomaly alerts fire |

---

## 🔗 How the Vulnerabilities Work

The attack is possible because the existing system has **no authentication**:

- **RPI TCP bridge** (`:5760`) — accepts any JSON command from any client
- **GCS `/telemetry` endpoint** — blindly accepts any `POST` with no API key or IP check

```
RPI bridge code:
    gcs.telemetry_data = data.get('telemetry', {})   # ← no verification
    gcs.alerts = data.get('alerts', [])               # ← attacker can set anything
```

---

## 🛡️ Defenses (to present after demo)

1. **Shared secret token** in TCP JSON commands
2. **HMAC signature** on telemetry packets
3. **Source IP whitelist** on `/telemetry` endpoint
4. **TLS/SSL** on both TCP and HTTP channels
5. **Rate limiting** on command endpoint
