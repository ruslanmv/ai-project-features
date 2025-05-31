"""
app.py
────────────────────────────────────────────────────────────────────────────
Minimal Flask façade for *ai-project-features*.

Endpoints
─────────
GET  /health                → "OK"               (liveness probe)
POST /apply                 → JSON recap         (core API)

    Content-Type: multipart/form-data
        file    = <.zip archive of code base>
        prompt  = <natural-language instruction>

The request body is **not** persisted on disk, except transiently inside
`tempfile.TemporaryDirectory()`.  The zip is passed to `workflows.run_all`
and the resulting Markdown recap is returned:

    {
      "recap": "## New agent added …"
    }

Run locally:

    export FLASK_APP=app.py
    python app.py          # or `flask run`

Behind a reverse proxy you can use `PORT=8080` to rebind.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from workflows import run_all

# ──────────────────────────────────────────────────────────────────────────
# Flask setup
# ──────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)  # allow all origins; tighten in production as needed
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
_LOG = logging.getLogger("api")

# Maximum upload size (bytes) – 25 MB by default
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_ZIP_SIZE", 25 * 1024 * 1024))


# ──────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────
@app.get("/health")
def health() -> tuple[str, int]:
    """Liveness probe for containers / k8s."""
    return "OK", 200


@app.post("/apply")
def apply() -> tuple[Any, int]:
    """
    Main API endpoint.  Requires multipart/form-data with:

        • file   – .zip
        • prompt – text

    Returns JSON: {"recap": "<markdown string>"}  on success,
    or {"error": "…"} on failure.
    """
    if "file" not in request.files or "prompt" not in request.form:
        return _error("Both 'file' and 'prompt' fields are required.", 400)

    up_file = request.files["file"]
    prompt = request.form["prompt"].strip()
    if not prompt:
        return _error("'prompt' must not be empty.", 400)

    # Secure the filename and stream to a temp dir
    safe_name = secure_filename(up_file.filename or "project.zip")
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / safe_name
        up_file.save(zip_path)

        try:
            _LOG.info("Running pipeline on %s (size=%s B)", safe_name, zip_path.stat().st_size)
            recap = run_all(str(zip_path), prompt)
        except Exception as exc:  # noqa: BLE001
            _LOG.exception("Pipeline failed")
            return _error(str(exc), 500)

    return jsonify({"recap": recap}), 200


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────
def _error(msg: str, code: int) -> tuple[Dict[str, str], int]:
    return jsonify({"error": msg}), code


# ──────────────────────────────────────────────────────────────────────────
# Entry-point
# ──────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 9000))
    app.run(host="0.0.0.0", port=port)
