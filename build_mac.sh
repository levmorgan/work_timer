#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

PYTHON=".venv/bin/python"

echo "=== 1. Running tests ==="
.venv/bin/pytest tests/ -q

echo ""
echo "=== 2. Generating icon ==="
"$PYTHON" generate_icon.py

echo ""
echo "=== 3. Cleaning previous build ==="
rm -rf build dist

echo ""
echo "=== 4. Building .app with PyInstaller ==="
"$PYTHON" -m PyInstaller pomodoro.spec

echo ""
echo "=== Done ==="
echo "App: $(pwd)/dist/work_timer.app"
ls -la dist/work_timer.app/Contents/MacOS/work_timer
