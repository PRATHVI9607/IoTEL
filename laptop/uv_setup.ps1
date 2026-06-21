#!/usr/bin/env pwsh
# ================================================================
#  UV Setup Script for Laptop GCS (Ground Control Station)
#  Windows PowerShell version
# ================================================================

Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Laptop GCS — UV Package Setup               ║" -ForegroundColor Cyan
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
uv sync --all-extras

Write-Host ""
Write-Host "✓ Setup complete! To run the GCS:" -ForegroundColor Green
Write-Host ""
Write-Host "  uv run python laptop_gcs.py --rpi <RPI_IP> --port 5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or with voice control:" -ForegroundColor Cyan
Write-Host "  uv run -f voice python laptop_gcs.py --rpi <RPI_IP>" -ForegroundColor Cyan
Write-Host ""
