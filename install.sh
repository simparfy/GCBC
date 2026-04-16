#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/simparfy/GCBC.git"
DEFAULT_DIR="$HOME/.gcbc"

echo "=== GCBC Installer ==="
echo ""

# Allow override via GCBC_DIR env var
INSTALL_DIR="${GCBC_DIR:-$DEFAULT_DIR}"

# Check Python version
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is required (>= 3.11)"
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]; }; then
    echo "Error: Python >= 3.11 required, found $PY_VERSION"
    exit 1
fi

echo "Python $PY_VERSION — OK"

# Check git
if ! command -v git &>/dev/null; then
    echo "Error: git is required"
    exit 1
fi

# Clone or update
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Existing installation found at $INSTALL_DIR — updating ..."
    git -C "$INSTALL_DIR" pull origin main
else
    echo "Cloning GCBC to $INSTALL_DIR ..."
    git clone "$REPO" "$INSTALL_DIR"
fi

# Install
echo "Installing Python package ..."
python3 -m pip install -e "$INSTALL_DIR" --quiet

# Verify
if command -v gcbc &>/dev/null; then
    VERSION=$(gcbc version 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])" 2>/dev/null || echo "unknown")
    echo ""
    echo "GCBC v${VERSION} installed successfully!"
    echo ""
    echo "Get started:"
    echo "  gcbc --help"
    echo "  gcbc version"
else
    echo ""
    echo "Installation complete, but 'gcbc' not found on PATH."
    echo "You may need to add your Python scripts directory to PATH."
    echo "Try: python3 -m gcbc.cli --help"
fi
