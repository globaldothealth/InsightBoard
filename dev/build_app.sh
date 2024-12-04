#!/usr/bin/env bash

set -euxo pipefail

# Change to the parent directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
pushd "$SCRIPT_DIR/.."

# Cleanup any previous build
rm -rf build dist

# Active the virtual environment (with all dependencies installed)
uv sync
uv pip install pyinstaller
source .venv/bin/activate

# Build the app
uv run pyinstaller  \
    --name InsightBoard \
    --noconfirm \
    --hidden-import InsightBoard \
    --hidden-import InsightBoard.parsers \
    --add-data "src/InsightBoard/pages/*:./pages/" \
    src/InsightBoard/__main__.py

# Return to original directory
popd
