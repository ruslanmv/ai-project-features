"""
self_refine_agent.py
────────────────────────────────────────────────────────────────────────────
Phase (Optional) – invoked when the static checker (D1) fails after the
maximum number of P5⇄D1 retries.  This meta-agent inspects the last `lint_error`
and the most recent diff, asks the LLM to suggest concrete fixes or to roll
back a bad patch, and then updates the in-memory “tasks” so that the next
iteration of code_writer_agent has more precise instructions.

If no reasonable fix is suggested, this agent raises a RuntimeError to
abort the pipeline, signaling that human intervention is required.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Dict, Any

from llm import generate
from memory import MEM

_LOG = logging.getLogger(__name__)


def run() -> None:
    """
    Execute self-refinement:

    1.  Retrieve the last lint error and diff from memory.
    2.  If no lint error is present, do nothing.
    3.  Otherwise, prompt the LLM to propose a revised list of tasks
        that explicitly addresses the reported errors.
    4.  Parse the LLM output into bullet points and overwrite MEM["tasks"].
    5.  If the LLM cannot produce a valid bullet list, raise RuntimeError.
    """
    lint_error: Optional[str] = MEM.get("lint_error")
    if not lint_error:
        _LOG.info("self_refine_agent: no lint_error found; skipping refinement.")
        return

    last_diff: Optional[str] = MEM.get("latest_diff")
    old_tasks: Optional[List[str]] = MEM.get("tasks")
    if old_tasks is None:
        raise RuntimeError("self_refine_agent: no previous tasks found.")

    _LOG.debug("Self-refine: lint_error:\n%s", lint_error)

    # Build a prompt that includes the lint error, the diff, and the previous tasks
    prompt = _build_refinement_prompt(old_tasks, lint_error, last_diff)

    assistant_reply = generate(
        [
            {
                "role": "system",
                "content": (
                    "You are a code-fix assistant.  The user’s last patch failed "
                    "the static checker.  Propose a revised set of tasks to "
                    "fix the errors."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,  # deterministic guidance
    )

    new_tasks = _extract_bullets(assistant_reply)
    if not new_tasks:
        raise RuntimeError(
            "self_refine_agent: LLM did not return a valid bullet list."
        )

    MEM.put("tasks", new_tasks)
    _LOG.info(
        "Self-refine completed: replaced %d old tasks with %d new tasks",
        len(old_tasks),
        len(new_tasks),
    )


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────
def _build_refinement_prompt(
    old_tasks: List[str], lint_error: str, last_diff: Optional[str]
) -> str:
    """
    Construct the user-visible prompt for the LLM, including:

    • The previous numbered tasks
    • The lint error message
    • The unified diff of the last patch (if available)
    • Instructions to return a bullet list of revised tasks
    """
    lines: List[str] = []
    lines.append("## Previously attempted tasks")
    for i, t in enumerate(old_tasks, start=1):
        lines.append(f"{i}. {t}")

    lines.append("\n## Lint error from static checker")
    lines.append(f"```\n{lint_error.strip()}\n```")

    if last_diff:
        lines.append("\n## Last patch diff")
        lines.append(f"```\n{last_diff.strip()}\n```")

    lines.append(
        "\n---\n"
        "Based on the lint error and the diff, produce an *ordered* bullet list "
        "(use '-' or '1.' prefixes) of precise actions to fix the code. "
        "Each bullet should be a single sentence.\n"
    )
    return "\n".join(lines)


_BULLET_PATTERN = re.compile(
    r"""^\s*            # optional leading whitespace
        (?:[-*•]|\d+[.)])\s+  # bullet marker: '-', '*', '•', or '1.' / '2)'
        (.*\S)           # capture the rest (non-blank)
    $""",
    re.VERBOSE,
)


def _extract_bullets(text: str) -> List[str]:
    """
    Parse the assistant's reply into a list of bullet strings.
    Lines not matching the bullet pattern are discarded.
    """
    bullets: List[str] = []
    for line in text.splitlines():
        m = _BULLET_PATTERN.match(line)
        if m:
            bullets.append(m.group(1).strip())
    return bullets
