"""
src/workflows.py
────────────────
Declaratively maps the logical phases described in the security-oriented
Mermaid flowchart

    Z → LST → P0 → P1 → P2 → P3 → P4 → P5 → D1 → P6 → OUT

to concrete Python functions.  The mapping lives in the OrderedDict
`PHASES`, so you can swap agents in or out by editing that one object.

The file also exposes a `run_all()` helper that executes the entire
pipeline end-to-end and returns the Markdown recap generated in phase
P6.  `run_all()` is what both the CLI driver (`src/main.py`) and the
Flask façade (`app.py`) import.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Callable, Any

# ────────────────────────────────────────────────────────────────────────────
# Core shared state (“blackboard”)
# ────────────────────────────────────────────────────────────────────────────
from memory import MEM  # a simple module-level dict shared by all agents

# ────────────────────────────────────────────────────────────────────────────
# Deterministic tools (no LLMs involved)
# ────────────────────────────────────────────────────────────────────────────
from tools.file_scanner import scan_zip

# ────────────────────────────────────────────────────────────────────────────
# Agents for each phase
# ────────────────────────────────────────────────────────────────────────────
from agents import (
    request_parser_agent,         # P1
    architecture_lookup_agent,    # P2
    task_planner_agent,           # P3
    feature_instantiation_agent,  # P4
    code_writer_agent,            # P5 (part)
    static_checker_agent,         # D1
    doc_assembler_agent,          # P6
)

# ────────────────────────────────────────────────────────────────────────────
# Phase helpers
# ────────────────────────────────────────────────────────────────────────────
def phase_Z(zip_path: str) -> str:
    """
    Z  – Deterministic “file_search.tree(zip)” step.
    Reads the provided archive *read-only*, constructs a Markdown-formatted
    directory tree with one-line previews, and stores it in shared memory
    under key ``"tree"``.  Returns the tree string so callers may log it.
    """
    tree = scan_zip(zip_path)
    MEM.put("tree", tree)
    return tree


def phase_P0(user_prompt: str) -> None:
    """
    P0 – Attach the user-supplied natural-language prompt to shared memory.

    Only data transfer here; *no LLM calls* and definitely *no code exec*.
    """
    MEM.put("user_prompt", user_prompt)


def phase_P5_loop_until_clean(max_attempts: int = 4) -> None:
    """
    Combined P5 + D1 loop.

    • Runs ``code_writer_agent.run()`` (phase P5) to produce or patch files.  
    • Immediately invokes ``static_checker_agent.run()`` (phase D1).  
      – On success, returns and the pipeline proceeds to P6.  
      – On failure, the loop repeats up to *max_attempts* times.

    Raises
    ------
    RuntimeError
        If static checks have not passed after the configured number of
        attempts, signalling a hard failure to the orchestrator.
    """
    for attempt in range(1, max_attempts + 1):
        code_writer_agent.run()           # P5  – generate / patch code
        if static_checker_agent.run():    # D1 – inline import & lint
            return                        # good to proceed
        # Otherwise, let the next iteration try to self-refine
    raise RuntimeError(
        f"[P5/D1] Static check never passed after {max_attempts} attempts."
    )


# ────────────────────────────────────────────────────────────────────────────
# Declarative phase-to-callable table
# Edit this OrderedDict to customise the workflow.
# ────────────────────────────────────────────────────────────────────────────
PHASES: "OrderedDict[str, Callable[..., Any]]" = OrderedDict(
    [
        ("Z",  phase_Z),                       # deterministic tree extractor
        ("P0", phase_P0),                      # attach prompt + tree
        ("P1", request_parser_agent.run),      # constraint / intent extraction
        ("P2", architecture_lookup_agent.run), # architecture recall
        ("P3", task_planner_agent.run),        # task decomposition
        ("P4", feature_instantiation_agent.run),  # feature design
        ("P5", phase_P5_loop_until_clean),     # code gen + self-check loop
        ("P6", doc_assembler_agent.run),       # recap / re-enumeration
        # OUT is implicit: run_all() returns MEM["final_answer"]
    ]
)

# ────────────────────────────────────────────────────────────────────────────
# Public orchestrator helper
# ────────────────────────────────────────────────────────────────────────────
def run_all(zip_path: str, user_prompt: str) -> str:
    """
    Execute every workflow phase in the declared order and return the
    final, human-readable recap stored under ``MEM["final_answer"]``.

    Parameters
    ----------
    zip_path : str
        Path to the codebase archive to refactor.
    user_prompt : str
        Natural-language instructions from the user.

    Returns
    -------
    str
        Markdown recap produced by ``doc_assembler_agent`` in phase P6.
    """
    for phase_id, func in PHASES.items():
        # Functions have varying signatures; dispatch on phase key.
        if phase_id == "Z":
            func(zip_path)
        elif phase_id == "P0":
            func(user_prompt)
        else:
            func()  # remaining phases take no positional args

    return MEM.get("final_answer")
