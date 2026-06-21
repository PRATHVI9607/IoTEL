#!/usr/bin/env pwsh
# ================================================================
#  Complete System Start Script — All 3 Components
#  Windows PowerShell helper to launch everything
# ================================================================

Write-Host @"
╔════════════════════════════════════════════════════════════════╗
║                IoTEL SYSTEM - START HELPER                    ║
║           Drone Control & Security Research Demo              ║
╚════════════════════════════════════════════════════════════════╝

This script helps you launch all components in the right order.

REQUIREMENTS:
  ✓ UV package manager installed
  ✓ RPI with Pixhawk connected (separate machine)
  ✓ 3 terminals ready
  ✓ Network connectivity between all systems

COMPONENTS:
  1. RPI Bridge     — Connects to drone hardware
  2. Laptop GCS     — Ground Control Station (defender)
  3. Attacker       — Security research tools

PORTS USED:
  5000  — Laptop GCS web dashboard
  5760  — RPI drone bridge (TCP telemetry)

Let's get started!
"@

Write-Host ""
Write-Host "STEP 1: Configure Your Network IPs" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════"
Write-Host ""

$rpiIp = Read-Host "Enter RPI IP (or press Enter for 10.58.17.137)"
if ([string]::IsNullOrWhiteSpace($rpiIp)) { $rpiIp = "10.58.17.137" }

$laptopIp = Read-Host "Enter Laptop GCS IP (or press Enter for auto-detect)"

$attackerMachine = Read-Host "Are you running attacker on this machine? (y/n)"

Write-Host ""
Write-Host "Configuration Summary:" -ForegroundColor Green
Write-Host "  RPI IP:              $rpiIp"
Write-Host "  Laptop GCS IP:       $(if ($laptopIp) { $laptopIp } else { 'This machine' })"
Write-Host "  Attacker on this PC: $(if ($attackerMachine -eq 'y') { 'YES' } else { 'NO' })"
Write-Host ""

Write-Host "STEP 2: Terminal Instructions" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════"
Write-Host ""

Write-Host "Terminal 1 (RPI - via SSH):" -ForegroundColor Yellow
Write-Host @"
  ssh pi@$rpiIp
  cd rpi
  ./uv_setup.sh  (first time only)
  ./uv_run.sh $laptopIp 5000
"@

Write-Host ""
Write-Host "Terminal 2 (This Machine - Laptop GCS):" -ForegroundColor Yellow
Write-Host @"
  cd c:\Workspace\IoTEL\laptop
  .\uv_setup.ps1  (first time only)
  .\uv_run.ps1 -RpiIp $rpiIp -Voice

  Then open browser: http://localhost:5000
"@

if ($attackerMachine -eq 'y') {
    Write-Host ""
    Write-Host "Terminal 3 (This Machine - Attacker):" -ForegroundColor Yellow
    Write-Host @"
  cd c:\Workspace\IoTEL\laptop2_attacker
  .\uv_setup.ps1  (first time only)
  .\uv_run.ps1

  Choose phases from menu...
"@
} else {
    Write-Host ""
    Write-Host "Terminal 3 (Different PC - Attacker):" -ForegroundColor Yellow
    Write-Host @"
  cd c:\Workspace\IoTEL\laptop2_attacker
  .\uv_setup.ps1  (first time only)
  .\uv_run.ps1 -RpiIp $rpiIp -GcsIp $laptopIp

  Choose phases from menu...
"@
}

Write-Host ""
Write-Host "STEP 3: Verify Everything is Running" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════"
Write-Host ""

Write-Host "Checklist:" -ForegroundColor Green
Write-Host "  [ ] RPI Bridge shows: [OK] Connected successfully"
Write-Host "  [ ] Laptop GCS running on http://localhost:5000"
Write-Host "  [ ] GCS dashboard shows live telemetry"
Write-Host "  [ ] Attacker console shows attack menu"
Write-Host ""

Write-Host "STEP 4: Run Your First Test" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════"
Write-Host ""

Write-Host "On GCS Dashboard:" -ForegroundColor Yellow
Write-Host "  • Check telemetry display (GPS, battery, heading)"
Write-Host "  • Try a voice command: 'arm' or 'loiter'"
Write-Host "  • Watch command history log"
Write-Host ""

Write-Host "On Attacker Console:" -ForegroundColor Yellow
Write-Host "  • Select [1] Phase 1 to discover targets"
Write-Host "  • Select [2] Phase 2 to sniff real telemetry"
Write-Host "  • Select [3] Phase 3A to spoof GPS position"
Write-Host "  • Watch GCS dashboard values change!"
Write-Host ""

Write-Host "STEP 5: Learn More" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════"
Write-Host ""

Write-Host "📚 Documentation:"
Write-Host "  • UV_COMPLETE_SETUP.md      — Detailed setup guide"
Write-Host "  • UV_QUICK_REFERENCE.md     — UV commands reference"
Write-Host "  • docs/enemy_drone_demo_plan.md — Architecture overview"
Write-Host ""

Write-Host "🎓 Educational Resources:"
Write-Host "  • https://docs.astral.sh/uv/"
Write-Host "  • https://flask.palletsprojects.com/"
Write-Host "  • https://ardupilot.org/"
Write-Host ""

Write-Host "═════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Ready to launch! Follow the Terminal instructions above." -ForegroundColor Green
Write-Host ""
