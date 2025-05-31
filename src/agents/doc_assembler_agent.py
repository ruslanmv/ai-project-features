"""
doc_assembler_agent.py
────────────────────────────────────────────────────────────────────────────
Phase **P6** – gather all results after a successful P5⇄D1 loop and produce
the final Markdown recap.  This includes:

  • The user’s original constraints and new feature specification  
  • A summary of what files were created or patched  
  • A “post-update” directory tree (depth ≤3)

The resulting recap is stored under MEM["final_answer"], which is returned
to the user by the orchestrator.
"""

from __future__ import annotations

import subprocess
import textwrap
from typing import Any

from memory import MEM


def run() -> None:
    """
    Execute phase P6:

    1.  Run a shell command to list all files (depth ≤3) under the project root.
    2.  Retrieve `constraints`, `feature_spec`, and `patch_summary` from memory.
    3.  Format a Markdown recap string combining these pieces.
    4.  Store the recap under MEM["final_answer"].
    """
    # ── 1. Capture the post-patch file tree (max depth 3) ────────────────
    proc = subprocess.run(
        ["bash", "-lc", "find . -maxdepth 3 -type f | sort"],
        shell=True,
        capture_output=True,
        text=True,
    )
    tree_after = proc.stdout.strip()

    # ── 2. Pull data from memory ─────────────────────────────────────────
    constraints: dict[str, Any] = MEM.get("constraints") or {}
    spec: dict[str, Any] = MEM.get("feature_spec") or {}
    patch_summary: str = MEM.get("patch_summary") or "(no summary available)"

    # ── 3. Build the Markdown recap ─────────────────────────────────────
    recap = textwrap.dedent(f"""
        ## New agent added
        * **Class**: {spec.get("className", "(unknown)")}
        * **Purpose**: {spec.get("purpose", "(unspecified)")}  
        * **File**: src/agents/{spec.get("className", "").lower()}.py

        ## What was changed
        {patch_summary}

        ## Updated directory tree (depth ≤3)
        ```
        {tree_after}
        ```
    """).strip()

    # ── 4. Store the final recap in shared memory ───────────────────────
    MEM.put("final_answer", recap)
