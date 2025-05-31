"""
request_parser_agent.py
────────────────────────────────────────────────────────────────────────────
Phase **P1** – turn *raw* user input + the deterministic file-tree string
into a **strictly-typed JSON object** of “constraints” that downstream
agents use to make safe decisions.

Expected JSON schema
────────────────────
{
  "projectName"     : <str>,   # name the assistant should use for the project
  "nonDestructive"  : <bool>,  # if true, do NOT overwrite existing files
  "wantsNewAgent"   : <bool>,  # whether the user explicitly asked for a new agent
  "brief"           : <str>    # one-line summary of the request   (optional)
}

If extra keys appear we keep them; unknown types raise `ValueError`.

Security / Robustness
─────────────────────
* The LLM is instructed to output **ONLY** a JSON object.
* We still defensively locate the *first* curly-brace block via regex
  in case a welcome message slips through.
* If parsing fails we raise `RuntimeError`, causing the orchestrator to
  abort early with a clear error.

The parsed dict is stored under `MEM["constraints"]`.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Dict, Any

from llm import generate
from memory import MEM
from config import Settings

_LOG = logging.getLogger(__name__)
_CFG = Settings()  # validates env on first import

# ──────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────
def run() -> None:
    """
    Execute phase P1.  Reads *user_prompt* and *tree* from the blackboard,
    asks the LLM for a concise JSON descriptor, validates it, then places
    the result back in the blackboard under `"constraints"`.
    """
    user_prompt: str | None = MEM.get("user_prompt")
    tree: str | None = MEM.get("tree")

    if not user_prompt or not tree:
        raise RuntimeError(
            "request_parser_agent: missing 'user_prompt' or 'tree' in MEM."
        )

    llm_prompt = _build_prompt(user_prompt, tree)
    _LOG.debug("Request-parser prompt (chars=%s)", len(llm_prompt))

    assistant_reply = generate(
        [
            {
                "role": "system",
                "content": (
                    "You are a JSON-only extraction engine.  "
                    "Never add commentary.  "
                    "Return a single JSON object and nothing else."
                ),
            },
            {"role": "user", "content": llm_prompt},
        ],
        temperature=0.0,  # deterministic extraction
    )

    constraints = _parse_and_validate(assistant_reply)
    MEM.put("constraints", constraints)
    _LOG.info("Phase P1 completed – extracted constraints: %s", constraints)


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────
_JSON_RE = re.compile(r"\{.*\}", re.S)  # first {...} block, non-greedy


def _build_prompt(user_prompt: str, tree_md: str) -> str:
    """Compose the string given to the LLM for extraction."""
    return (
        "## User prompt\n"
        f"{user_prompt}\n\n"
        "## Directory tree (truncated markdown)\n"
        f"{tree_md}\n\n"
        "----\n"
        "Extract a JSON object with at least these keys:\n"
        '  - "projectName"    (string)\n'
        '  - "nonDestructive" (boolean)\n'
        '  - "wantsNewAgent"  (boolean)\n'
        '  - "brief"          (short string, optional)\n'
        "Return ONLY the JSON; do not wrap it in triple-backticks."
    )


def _parse_and_validate(raw: str) -> Dict[str, Any]:
    """Locate JSON in *raw*, load it, and enforce basic schema."""
    m = _JSON_RE.search(raw)
    if not m:
        raise RuntimeError("request_parser_agent: no JSON object found in LLM reply.")

    try:
        data: Dict[str, Any] = json.loads(m.group(0))
    except json.JSONDecodeError as exc:  # noqa: EM102
        raise RuntimeError(
            f"request_parser_agent: invalid JSON returned by LLM – {exc}"
        ) from exc

    # Basic sanity checks
    required_keys = {"projectName": str, "nonDestructive": bool, "wantsNewAgent": bool}
    for key, typ in required_keys.items():
        if key not in data:
            raise RuntimeError(f"Missing required key '{key}' in constraints JSON.")
        if not isinstance(data[key], typ):
            raise RuntimeError(
                f"Key '{key}' expected type {typ.__name__}, got {type(data[key]).__name__}"
            )

    # Optional brief → str
    if "brief" in data and not isinstance(data["brief"], str):
        raise RuntimeError("Key 'brief' must be a string if provided.")

    return data
