#!/usr/bin/env pwsh
# ================================================================
#  UV Run Script for Laptop GCS
#  Quick launcher with intelligent defaults
# ================================================================

param(
    [string]$RpiIp = "10.58.17.137",
    [int]$Port = 5000,
    [switch]$Voice,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
╔════════════════════════════════════════════════════════════════╗
║           Laptop GCS — UV Run Script                           ║
╚════════════════════════════════════════════════════════════════╝

USAGE:
  .\uv_run.ps1 [-RpiIp <IP>] [-Port <PORT>] [-Voice] [-Help]

PARAMETERS:
  -RpiIp <IP>     RPI IP address (default: 10.58.17.137)
  -Port <PORT>    Web server port (default: 5000)
  -Voice          Enable voice control features
  -Help           Show this help message

EXAMPLES:
  # Basic run with defaults
  .\uv_run.ps1

  # Connect to specific RPI
  .\uv_run.ps1 -RpiIp 192.168.1.100

  # With voice control + custom port
  .\uv_run.ps1 -RpiIp 192.168.1.100 -Port 8000 -Voice

ACCESS:
  Once running, open your browser to: http://localhost:$Port
"@
    exit 0
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Laptop GCS — Ground Control Station         ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  RPI IP:        $RpiIp"
Write-Host "  Web Port:      $Port"
Write-Host "  Voice Control: $(if ($Voice) { 'ENABLED' } else { 'disabled' })"
Write-Host ""

Write-Host "Starting Ground Control Station..." -ForegroundColor Green
Write-Host "Dashboard URL: http://localhost:$Port" -ForegroundColor Cyan
Write-Host ""

if ($Voice) {
    uv run -f voice python laptop_gcs.py --rpi $RpiIp --port $Port
} else {
    uv run python laptop_gcs.py --rpi $RpiIp --port $Port
}
