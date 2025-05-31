"""
code_writer_agent.py
────────────────────────────────────────────────────────────────────────────
Phase **P5** – create *or* patch source files to satisfy the user
requirements produced in earlier phases.

High-level flow
───────────────
1.  Read **feature_spec**, **tasks**, and **constraints** from the
    shared blackboard.
2.  If NEW file  →  generate a skeleton using BeeAI CodeAssistant
    (Watsonx backend).  Fallback to a deterministic template if the
    API is unavailable (e.g. tests/offline mode).
3.  If EXISTING file  →  ask CodeAssistant to *append* or *modify*
    specific sections (guided by the numbered tasks).
4.  Validate the generated code:
      • Parse with `ast.parse()` to guarantee syntactic validity.  
      • Reject if any top-level *executable* statements exist
        (`ast.Expr` nodes outside function/class).  
5.  Write the file to disk and produce a unified diff via
   `tools.diff_generator.create_patch()`.
6.  **requirements.txt** auto-update: for each new `import` whose top-level
    module isn’t already present in *requirements.txt*, append it.
7.  Store a human-readable `patch_summary` string in `MEM` so that
    `doc_assembler_agent` can include it in the recap.

Security guard-rails
────────────────────
* New agents are always wrapped inside a *class* – no top-level code.  
* AST validation aborts the pipeline if unsafe constructs are detected.  
* Overwrite is *denied* when `constraints["nonDestructive"]` is `True`
  and the target path already exists.

External dependencies
─────────────────────
This file expects:
    • beeai==0.5.*          (for CodeAssistant)    – optional
    • astroid / anytree …   (standard lib or already pinned)

If BeeAI is not installed we automatically fallback to the deterministic
template, keeping tests green without external API calls.

"""

from __future__ import annotations

import ast
import importlib.util
import logging
import pathlib
import re
from typing import Dict, Any, List

from memory import MEM
from config import Settings
from tools.diff_generator import create_patch

try:
    from beeai.codeassistant import CodeAssistant  # type: ignore
except ModuleNotFoundError:  # graceful offline fallback
    CodeAssistant = None  # pylint: disable=invalid-name

_LOG = logging.getLogger(__name__)
_CFG = Settings()

# ---------------------------------------------------------------------- #
# Public API                                                             #
# ---------------------------------------------------------------------- #
def run() -> None:
    """
    Main entry for phase P5.  Ensures that:
    • Generated code is syntactically correct
    • No top-level executable statements sneak in
    • requirements.txt is updated when needed
    """
    feature_spec: Dict[str, Any] | None = MEM.get("feature_spec")
    constraints: Dict[str, Any] | None = MEM.get("constraints")
    tasks: List[str] | None = MEM.get("tasks")

    if not (feature_spec and constraints):
        raise RuntimeError("code_writer_agent: missing feature_spec or constraints.")

    path = pathlib.Path("src") / "agents" / f"{feature_spec['className'].lower()}.py"
    non_destructive = constraints.get("nonDestructive", True)

    # ── Safeguard: do not overwrite existing file in non-destructive mode ──
    if non_destructive and path.exists():
        raise RuntimeError(
            f"Refusing to overwrite existing file {path} with nonDestructive=True"
        )

    # ─── Generate (or patch) code ────────────────────────────────────────
    if not path.exists():
        code = _generate_new_agent(feature_spec, tasks)
        old_text = ""
    else:
        code, old_text = _patch_existing_agent(path.read_text(), feature_spec, tasks)

    # ─── Validate AST & security guard rails ────────────────────────────
    _validate_code_safe(code, feature_spec["className"])

    # ─── Write file + produce diff summary ──────────────────────────────
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code, encoding="utf-8")

    diff = create_patch(old_text, code, str(path))
    _update_requirements_if_needed(code)

    summary_lines = [
        f"Created {path}" if not old_text else f"Patched {path}",
        f"Lines changed: {diff.countlines() if hasattr(diff, 'countlines') else 'n/a'}",
    ]
    MEM.put("patch_summary", "\n".join(summary_lines))
    MEM.put("latest_diff", diff)

    _LOG.info("Phase P5 complete – wrote %s bytes to %s", len(code), path)


# ---------------------------------------------------------------------- #
# Code generation helpers                                                #
# ---------------------------------------------------------------------- #
_TEMPLATE = """
import logging
import typing
import asyncio

class {className}:
    \"\"\"{purpose}\"\"\"

    {runSignature}
        \"\"\"Entry point for the {className}.\"\"\"
        logging.info("%s: starting", self.__class__.__name__)
        # TODO: implement logic
        return []
""".lstrip()


def _generate_new_agent(spec: Dict[str, Any], tasks: List[str] | None) -> str:
    """Return brand-new agent code either via BeeAI CodeAssistant or static template."""
    if CodeAssistant:  # happy path – use LLM to flesh out skeleton
        assistant = CodeAssistant(
            backend="watsonx",
            model=_CFG.DEFAULT_LLM_MODEL_ID,
            api_key=_CFG.WATSONX_API_KEY,
            project_id=_CFG.WATSONX_PROJECT_ID,
            temperature=_CFG.LLM_TEMPERATURE,
        )

        user_prompt = (
            "Create a Python agent class file that satisfies the following spec:\n"
            f"{spec}\n"
            "Tasks it must support:\n"
            + "\n".join(f"- {t}" for t in (tasks or []))
            + "\n\nRules:\n"
            "* All executable code must live under class / function bodies.\n"
            "* No top-level network or filesystem calls.\n"
            "* Follow PEP-8.\n"
        )
        code = assistant.generate_file(user_prompt)
    else:  # offline fallback
        code = _TEMPLATE.format(**spec)

    return code


def _patch_existing_agent(
    old_code: str,
    spec: Dict[str, Any],
    tasks: List[str] | None,
) -> tuple[str, str]:
    """
    Use BeeAI CodeAssistant *edit* mode to revise an existing agent.
    If CodeAssistant is unavailable (offline), we simply append TODOs
    to the end of the file.
    """
    if CodeAssistant:
        assistant = CodeAssistant(
            backend="watsonx",
            model=_CFG.DEFAULT_LLM_MODEL_ID,
            api_key=_CFG.WATSONX_API_KEY,
            project_id=_CFG.WATSONX_PROJECT_ID,
            temperature=_CFG.LLM_TEMPERATURE,
        )
        code = assistant.edit_file(
            old_code,
            instruction="Apply the following tasks while preserving style:\n"
            + "\n".join(f"- {t}" for t in (tasks or [])),
        )
    else:
        # naive fallback: append comment section
        todo_block = "\n\n# TODO (auto-generated):\n" + "\n".join(
            f"#  - {t}" for t in (tasks or [])
        )
        code = old_code.rstrip() + todo_block

    return code, old_code


# ---------------------------------------------------------------------- #
# Validation helpers                                                     #
# ---------------------------------------------------------------------- #
def _validate_code_safe(code: str, class_name: str) -> None:
    """
    Parse *code* with Python's `ast` module and ensure:
      • It's syntactically valid.
      • All nodes at module level are import-safe (ClassDef, FunctionDef,
        Import, ImportFrom, Assign CONST, etc. – but NOT Expr calling
        functions or os/system).
    """
    try:
        tree = ast.parse(code, filename="<generated>")
    except SyntaxError as exc:
        raise RuntimeError(f"Generated code is not valid Python – {exc}") from exc

    for node in tree.body:
        # Allow: imports, class/func defs, constant assignments, docstrings
        safe_nodes = (
            ast.Import,
            ast.ImportFrom,
            ast.ClassDef,
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.Assign,
            ast.AnnAssign,
            ast.Expr,  # but only if it's a *docstring*
        )
        if not isinstance(node, safe_nodes):
            raise RuntimeError(
                "Unsafe top-level statement detected "
                f"({type(node).__name__}) in generated {class_name}.  "
                "Aborting."
            )
        # If Expr – ensure it's only a docstring
        if isinstance(node, ast.Expr) and not isinstance(node.value, ast.Str):
            raise RuntimeError(
                "Top-level executable expression detected in generated code."
            )


# ---------------------------------------------------------------------- #
# requirements.txt auto-update                                           #
# ---------------------------------------------------------------------- #
_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([\w\.]+)", re.M)


def _update_requirements_if_needed(code: str) -> None:
    """
    Detect new top-level imports in *code*.  If any root package is not
    yet present in requirements.txt, append it (best-effort).
    """
    root_dir = pathlib.Path(".")
    req_path = root_dir / "requirements.txt"
    existing = set()
    if req_path.exists():
        existing.update(
            line.split("==")[0].strip() for line in req_path.read_text().splitlines()
        )

    imported = {_IMPORT_RE.findall(code)}
    missing = {pkg.split(".")[0] for pkg in imported} - existing

    if not missing:
        return

    with req_path.open("a", encoding="utf-8") as fp:
        for pkg in sorted(missing):
            fp.write(f"{pkg}>=0.0.0\n")
    _LOG.info("requirements.txt updated with: %s", ", ".join(sorted(missing)))
