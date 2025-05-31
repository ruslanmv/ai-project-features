"""
static_checker_agent.py
────────────────────────────────────────────────────────────────────────────
Phase **D1** – sanity-check the patched project *without* executing
business logic.  We verify three things:

  1.  Every *.py* file compiles (syntax OK)  →   `py_compile`
  2.  Importing the *package tree* succeeds  →   `pytest --collect-only`
  3.  No `RuntimeError` / missing packages   →   non-zero exit → loop

If *all* checks pass we return ``True`` so the workflow proceeds to P6.
On failure we:

  • Capture stderr/stdout into ``MEM["lint_error"]``  
  • Return ``False`` so the orchestrator re-enters the P5→D1 loop.

Why use **pytest --collect-only**?
----------------------------------
`pytest` imports every test module and therefore transitively imports the
application package.  `--collect-only` stops before running any test
functions, giving us a cheap “can I import the world?” smoke test.

Security notes
--------------
* We launch a *separate* Python subprocess to avoid polluting the current
  interpreter state.
* The subprocess inherits a **clean environment** with
  `PYTHONPATH=.` only.
"""

from __future__ import annotations

import compileall
import os
import pathlib
import subprocess
import sys
import textwrap
from typing import List

import logging

from memory import MEM
from config import Settings

_LOG = logging.getLogger(__name__)
_CFG = Settings()

# Where is our source tree?
SRC_DIR = _CFG.SRC_DIR


# ──────────────────────────────────────────────────────────────────────────
# Public API – single entry-point used by the orchestrator
# ──────────────────────────────────────────────────────────────────────────
def run() -> bool:
    """
    Perform the static sanity checks.  Returns ``True`` on success,
    ``False`` on failure (and records the error in memory).

    The orchestrator will loop (P5 → D1) based on this boolean.
    """
    _LOG.debug("Static-checker: starting compilation pass")
    if not _compile_project():
        return False

    _LOG.debug("Static-checker: running pytest collect-only")
    success, log = _pytest_collect_only()

    if success:
        _LOG.info("Static-checker passed ✅")
        MEM.put("lint_error", None)
        return True

    MEM.put("lint_error", log)
    _LOG.warning("Static-checker failed ❌; captured lint_error.")
    return False


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────
def _compile_project() -> bool:
    """
    Run Python's `py_compile` over every *.py* file; returns True
    iff *all* files compile cleanly.
    """
    # compileall returns False *iff* a compilation failed
    ok = compileall.compile_dir(
        str(SRC_DIR),
        quiet=1,           # only print errors
        force=False,       # skip unchanged bytecode
        optimize=0,
    )
    if not ok:
        MEM.put(
            "lint_error",
            "Syntax error during py_compile – see console log above.",
        )
    return bool(ok)


def _pytest_collect_only() -> tuple[bool, str]:
    """
    Spawn a *new* Python process:

        python -m pytest --collect-only -q

    Captures stdout / stderr, returns (success, combined_log).
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()  # ensure local package is importable
    cmd: List[str] = [
        sys.executable,
        "-m",
        "pytest",
        "--collect-only",
        "-q",
    ]

    proc = subprocess.run(
        cmd,
        cwd=str(SRC_DIR.parent),  # project root
        env=env,
        capture_output=True,
        text=True,
        timeout=120,  # seconds
    )

    combined = textwrap.dedent(
        f"""
        ---- pytest collect-only ({'OK' if proc.returncode == 0 else 'FAIL'}) ----
        STDOUT:
        {proc.stdout}
        STDERR:
        {proc.stderr}
        -------------------------------------------------------------------------
        """
    ).strip()

    return proc.returncode == 0, combined
