#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

PYTHON=".venv/bin/python"
if [ ! -f "$PYTHON" ]; then
    echo "No virtualenv found at .venv — please create one and install dependencies:"
    echo "  python3 -m venv .venv"
    echo "  .venv/bin/pip install -r requirements-dev.txt"
    exit 1
fi

echo "=== 1. Running tests ==="
.venv/bin/pytest tests/ -q

echo ""
echo "=== 2. Cleaning previous build ==="
rm -rf build dist

echo ""
echo "=== 3. Building executable with PyInstaller ==="
"$PYTHON" -m PyInstaller pomodoro.spec

echo ""
echo "=== Done ==="
echo "Executable: $(pwd)/dist/work_timer/work_timer"
ls -la dist/work_timer/work_timer
