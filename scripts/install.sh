#!/usr/bin/env bash
# scripts/install.sh
# ───────────────────────────────────────────────────────────────────────────────
# Bootstrap script for ai-project-features.
# Creates a Python virtual environment (if one doesn’t already exist),
# installs runtime dependencies from requirements.txt, and initializes
# any additional setup needed for local development.

set -euo pipefail

# ───────────────────────────────────────────────────────────────────────────────
# 1. Define variables
# ───────────────────────────────────────────────────────────────────────────────
# Default Python interpreter; override by exporting PYTHON_BIN before running.
PYTHON_BIN="${PYTHON_BIN:-python3}"

# Virtual environment directory
VENV_DIR=".venv"

# ───────────────────────────────────────────────────────────────────────────────
# 2. Create virtual environment if missing
# ───────────────────────────────────────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
  echo "🛠  Creating virtual environment in $VENV_DIR ..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
else
  echo "✅  Virtual environment already exists at $VENV_DIR"
fi

# ───────────────────────────────────────────────────────────────────────────────
# 3. Activate the virtual environment
# ───────────────────────────────────────────────────────────────────────────────
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ───────────────────────────────────────────────────────────────────────────────
# 4. Upgrade pip and install dependencies
# ───────────────────────────────────────────────────────────────────────────────
echo "📦  Upgrading pip and installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# ───────────────────────────────────────────────────────────────────────────────
# 5. Create .env from .env.sample if missing
# ───────────────────────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
  if [ -f ".env.sample" ]; then
    echo "🔐  Copying .env.sample to .env. Please fill in credentials."
    cp .env.sample .env
  else
    echo "⚠️   .env.sample not found; skipping env file creation."
  fi
else
  echo "🔑  .env already exists; skipping."
fi

# ───────────────────────────────────────────────────────────────────────────────
# 6. Finish
# ───────────────────────────────────────────────────────────────────────────────
echo "🎉  Installation complete!"
echo "To activate the virtual environment, run:"
echo "  source $VENV_DIR/bin/activate"
echo "Then you can run the CLI with:"
echo "  python -m src --help"
