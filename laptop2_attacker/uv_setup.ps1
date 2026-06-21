#!/usr/bin/env pwsh
# ================================================================
#  UV Setup Script for Attacker Console
#  Windows PowerShell version
# ================================================================

Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Attacker Console — UV Setup                 ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if uv is installed
try {
    $uvVersion = uv --version
    Write-Host "✓ UV found: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ UV not found! Install from: https://docs.astral.sh/uv/getting-started/" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Installing dependencies with UV..." -ForegroundColor Yellow
uv sync

Write-Host ""
Write-Host "✓ Setup complete! To run the attack console:" -ForegroundColor Green
Write-Host ""
Write-Host "  uv run python full_attack.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or with specific targets:" -ForegroundColor Cyan
Write-Host "  uv run python full_attack.py --rpi 10.193.181.136 --gcs 10.193.181.50" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠ WARNING: Educational use only!" -ForegroundColor Yellow
Write-Host ""
