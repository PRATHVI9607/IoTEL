#!/usr/bin/env pwsh
# ================================================================
#  UV Run Script for Attacker Console
#  Full attack orchestration tool
# ================================================================

param(
    [string]$RpiIp = "",
    [string]$GcsIp = "",
    [int]$RpiPort = 5760,
    [int]$GcsPort = 5000,
    [switch]$Help
)

if ($Help -or ($RpiIp -eq "" -and $GcsIp -eq "")) {
    Write-Host @"
╔════════════════════════════════════════════════════════════════╗
║         Attacker Console — Full Attack Framework               ║
║         Educational Use — IDP Security Research                ║
╚════════════════════════════════════════════════════════════════╝

USAGE:
  .\uv_run.ps1 [-RpiIp <IP>] [-GcsIp <IP>] [-RpiPort <PORT>] [-GcsPort <PORT>] [-Help]

PARAMETERS:
  -RpiIp <IP>       RPI Drone IP (auto-discover if not set)
  -GcsIp <IP>       Laptop GCS IP (auto-discover if not set)
  -RpiPort <PORT>   RPI port (default: 5760)
  -GcsPort <PORT>   GCS port (default: 5000)
  -Help             Show this help

EXAMPLES:
  # Auto-discover targets via network scan
  .\uv_run.ps1

  # Specify targets
  .\uv_run.ps1 -RpiIp 10.193.181.136 -GcsIp 10.193.181.50

  # Custom ports
  .\uv_run.ps1 -RpiIp 192.168.1.100 -GcsIp 192.168.1.50 -RpiPort 5760 -GcsPort 5000

FEATURES:
  [1] Phase 1  — Network Scan (discover drone & GCS)
  [2] Phase 2  — Passive Telemetry Sniff
  [3] Phase 3A — Telemetry Spoof (fake GCS data)
  [4] Phase 3B — Command Injection (TCP)
  [5] Combo    — Sniff + Spoof simultaneously

ATTACKS:
  - GPS Position Shift (500m offset)
  - Battery Critical (fake low battery)
  - Fake Landing (drone stopped)
  - Inject Alerts (confuse operator)
  - Mode Change (LOITER → STABILIZE)
  - Fake Jamming Alerts
  - Command Injection (arm, disarm, land, etc.)
"@
    exit 0
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Red
Write-Host "║           ATTACK CONSOLE                      ║" -ForegroundColor Red
Write-Host "║     Enemy Drone Detection & Spoofing          ║" -ForegroundColor Red
Write-Host "║     Educational Use Only                      ║" -ForegroundColor Red
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Red
Write-Host ""

if ($RpiIp) {
    Write-Host "RPI Target:  $RpiIp`:$RpiPort" -ForegroundColor Yellow
}
if ($GcsIp) {
    Write-Host "GCS Target:  $GcsIp`:$GcsPort" -ForegroundColor Yellow
}
if (-not $RpiIp -and -not $GcsIp) {
    Write-Host "No targets specified — Network scan will auto-discover" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Starting Attack Console..." -ForegroundColor Green
Write-Host ""

$args = @("full_attack.py")
if ($RpiIp) { $args += @("--rpi", $RpiIp) }
if ($GcsIp) { $args += @("--gcs", $GcsIp) }

uv run python $args
