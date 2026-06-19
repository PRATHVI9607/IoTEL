# IoTEL Laptop GCS — Windows setup with uv
Set-Location $PSScriptRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv via winget..."
    winget install astral-sh.uv
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
}

Write-Host "Syncing dependencies..."
uv sync

Write-Host ""
Write-Host "Done! Run the GCS with:"
Write-Host "  uv run python laptop_gcs.py"
Write-Host "  uv run python laptop_gcs.py --rpi <RPI_IP> --port 5760 --web 5000"
