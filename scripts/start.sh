#!/usr/bin/env bash
# start.sh
# ────────────────────────────────────────────────────────────────────────────
# Entry-point script for ai-project-features.
# Depending on MODE, either runs the CLI pipeline or starts the Flask server.

set -euo pipefail

# Load environment variables from .env if present
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Activate virtualenv if it exists
if [ -d ".venv" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

# Default behavior: run CLI. If MODE=server, run Flask app.
MODE="${MODE:-cli}"

if [ "$MODE" = "server" ]; then
  echo "🚀 Starting Flask server on port ${PORT:-9000} (MODE=server)..."
  # If FLASK_APP is not set, point it to app.py
  export FLASK_APP="app.py"
  flask run --host=0.0.0.0 --port="${PORT:-9000}"
else
  echo "🔧 Running CLI pipeline (MODE=cli)..."
  # Example usage: ./start.sh --zip path/to/project.zip --prompt "Add logging"
  python -m src "$@"
fi
