"""
task_planner_agent.py
────────────────────────────────────────────────────────────────────────────
Phase **P3** of the multi-agent pipeline.

Goal
────
Given:

• A deterministic *file-tree* string stored under ``MEM["tree"]`` (phase Z)  
• A structured *constraints* JSON object in ``MEM["constraints"]`` (phase P1)  
• Optional *architecture snippets* list in ``MEM["architecture_snippets"]`` (phase P2)

…ask the LLM to derive an **ordered, human-readable bullet list** of the
code-editing steps required to satisfy the user request *without breaking
existing architecture*.

The result is stored under ``MEM["tasks"]`` as ``list[str]`` so that
downstream agents (P4 → P5) can consume it programmatically.

Implementation notes
────────────────────
* Uses the Watsonx.ai wrapper from ``llm.generate`` for a single call.  
* Adds a *guard-rail* that rejects replies longer than 25 items to avoid
  runaway hallucinated task lists.  
* Splits the assistant response into tidy bullet-lines, stripping common
  list prefixes (“1. ”, “- ”, “• ”, etc.).

Security
────────
This agent is **read-only** with regard to the local filesystem; it
merely passes strings to the LLM and parses its textual reply.
"""

from __future__ import annotations

import logging
import re
from typing import List

from llm import generate
from memory import MEM
from config import Settings

_LOG = logging.getLogger(__name__)
_CFG = Settings()  # cached singleton; validates env on first import


# ──────────────────────────────────────────────────────────────────────────
# Public API – single entry-point called by the orchestrator
# ──────────────────────────────────────────────────────────────────────────
def run() -> None:
    """
    Execute phase P3 and place the ordered *tasks* list into the shared
    blackboard under key ``"tasks"``.
    """
    constraints = MEM.get("constraints") or {}
    tree_md = MEM.get("tree") or "(no tree found)"
    arch_snippets: List[str] | None = MEM.get("architecture_snippets")

    prompt = _build_prompt(constraints, tree_md, arch_snippets)
    _LOG.debug("Task-planner prompt (chars=%s)", len(prompt))

    assistant_reply = generate(
        [
            {
                "role": "system",
                "content": (
                    "You are a senior software architect.  "
                    "Given a codebase tree + user constraints, "
                    "list the minimal numbered steps needed to apply those changes "
                    "without breaking existing architecture.  "
                    "Return ONLY the bullet list."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=_CFG.LLM_TEMPERATURE,
    )

    tasks = _extract_bullets(assistant_reply)
    if not tasks:
        raise RuntimeError("Task planner produced an empty or unparsable list.")

    if len(tasks) > 25:
        raise RuntimeError(
            f"Task planner returned {len(tasks)} items (max 25 allowed) – aborting."
        )

    MEM.put("tasks", tasks)
    _LOG.info("Phase P3 completed – derived %s tasks", len(tasks))


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────
def _build_prompt(
    constraints: dict,
    tree_markdown: str,
    arch_snippets: List[str] | None,
) -> str:
    """Assemble the user-visible prompt for the LLM."""
    lines: list[str] = []
    lines.append("## Current directory tree")
    lines.append(tree_markdown)
    lines.append("\n## Constraints JSON")
    lines.append(str(constraints))

    if arch_snippets:
        lines.append("\n## Relevant design notes")
        for snip in arch_snippets:
            lines.append(f"- {snip}")

    lines.append(
        "\n---\n"
        "Produce an *ordered* bullet list (use '-' or '1.' prefixes) of the actions "
        "a code-modifier agent should perform.  "
        "Be concise; one sentence per bullet."
    )
    return "\n".join(lines)


_BULLET_PATTERN = re.compile(
    r"""^\s*           # leading whitespace
        (?:[-*•]|      # unordered bullet
        \d+[.)])\s+    # or ordered "1.", "2)", etc.
        (.*\S)         # capture the remainder (non-blank)
    $""",
    re.VERBOSE,
)


def _extract_bullets(text: str) -> List[str]:
    """
    Parse the assistant response into a clean list of bullet strings.
    Lines that do not match ``_BULLET_PATTERN`` are ignored.
    """
    bullets: list[str] = []
    for line in text.splitlines():
        m = _BULLET_PATTERN.match(line)
        if m:
            bullets.append(m.group(1).strip())
    return bullets
