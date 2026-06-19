#!/bin/bash
# IoTEL Laptop GCS — setup with uv
set -e

cd "$(dirname "$0")"

if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.local/bin/env"
fi

echo "Syncing dependencies..."
uv sync

echo ""
echo "Done! Run the GCS with:"
echo "  uv run python laptop_gcs.py"
echo "  uv run python laptop_gcs.py --rpi <RPI_IP> --port 5760 --web 5000"
