"""
feature_instantiation_agent.py
────────────────────────────────────────────────────────────────────────────
Phase **P4** – decide whether the workflow should create a *new* agent
(or another file) to satisfy the numbered tasks produced in P3.  If a new
file is required, emit a *minimal* JSON spec so the code-writer knows what
to generate.

JSON schema (stored in MEM["feature_spec"])
───────────────────────────────────────────
{
  "file"        : "src/agents/foo_agent.py",
  "className"   : "FooAgent",
  "runSignature": "async def run(self, *args, **kwargs) -> list[str]:",
  "purpose"     : "Short one-sentence human description"
}

If the user explicitly sets `"wantsNewAgent": false`, the agent will
simply echo back an empty dict so code_writer_agent knows to patch an
existing file instead.

The agent enforces:
  • PascalCase for `className`
  • snake_case filename derived automatically
  • `file` must live under `src/agents/`
"""

from __future__ import annotations

import json
import logging
import re
import textwrap
from typing import Dict, Any, List

from llm import generate
from memory import MEM
from config import Settings

_LOG = logging.getLogger(__name__)
_CFG = Settings()

_JSON_RE = re.compile(r"\{.*\}", re.S)


# ──────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────
def run() -> None:
    """
    Execute phase P4.  Write `feature_spec` into MEM.
    """
    constraints: Dict[str, Any] | None = MEM.get("constraints")
    tasks: List[str] | None = MEM.get("tasks")

    if not constraints or tasks is None:
        raise RuntimeError("feature_instantiation_agent: prerequisites missing")

    # If user said no new agent – short-circuit
    if constraints.get("wantsNewAgent") is False:
        MEM.put("feature_spec", {})
        _LOG.info("User opted out of new agent; feature_spec left empty.")
        return

    llm_prompt = _build_prompt(constraints, tasks)

    assistant_reply = generate(
        [
            {
                "role": "system",
                "content": (
                    "You are a senior Python architect.  "
                    "Given the numbered tasks and constraints, propose a concise "
                    "JSON spec for ONE new agent class.  "
                    "Output ONLY the JSON object."
                ),
            },
            {"role": "user", "content": llm_prompt},
        ],
        temperature=_CFG.LLM_TEMPERATURE,
    )

    spec = _parse_and_validate(assistant_reply)
    MEM.put("feature_spec", spec)
    _LOG.info("Phase P4 complete – feature_spec=%s", spec)


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────
def _build_prompt(constraints: Dict[str, Any], tasks: List[str]) -> str:
    body = textwrap.dedent(
        f"""
        ## Constraints
        {json.dumps(constraints, indent=2)}

        ## Derived tasks
        {"".join(f"- {t}\n" for t in tasks)}

        ---
        Provide a JSON object with keys:
          * className   – PascalCase name
          * runSignature – Python async def signature string
          * purpose     – one-line description
        Do NOT include commentary or markdown fences.
        """
    ).strip()
    return body


def _parse_and_validate(raw: str) -> Dict[str, Any]:
    m = _JSON_RE.search(raw)
    if not m:
        raise RuntimeError("feature_instantiation_agent: no JSON found in LLM reply")

    data = json.loads(m.group(0))

    # Basic keys
    required = {"className", "runSignature", "purpose"}
    if not required.issubset(data):
        missing = required - data.keys()
        raise RuntimeError(f"feature_spec missing keys: {missing}")

    class_name = data["className"]
    if not re.fullmatch(r"[A-Z][A-Za-z0-9]+", class_name):
        raise RuntimeError("className must be PascalCase")

    # Derive file path
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()
    data["file"] = f"src/agents/{snake}.py"
    return data
