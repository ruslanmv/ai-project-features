#!/usr/bin/env bash
# docker/entrypoint.sh
# ────────────────────────────────────────────────────────────────────────────
# Entrypoint script for the Docker container.  Depending on the MODE environment
# variable, it either launches the Flask server or runs the CLI pipeline.

set -euo pipefail

# Load environment variables from /app/.env if it exists
if [ -f "/app/.env" ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' /app/.env | xargs)
fi

# Default MODE is "cli"; set MODE=server for Flask API mode
MODE="${MODE:-cli}"

if [ "$MODE" = "server" ]; then
  echo "🚀 Starting Flask server on port ${PORT:-9000} (MODE=server)..."
  # Ensure FLASK_APP is set to our app.py
  export FLASK_APP="app.py"
  # Run Flask
  exec flask run --host=0.0.0.0 --port="${PORT:-9000}"
else
  echo "🔧 Running CLI pipeline (MODE=cli)..."
  # Pass all additional arguments to the Python module
  exec python -m src "$@"
fi
