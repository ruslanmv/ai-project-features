"""Request parser agent (Phase P1) - Extract constraints from user prompts."""

from __future__ import annotations

from typing import Any

from aurora.agents.base import BaseAgent


class RequestParserAgent(BaseAgent):
    """Phase P1: Parse user prompts and extract structured constraints."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize with phase ID P1."""
        super().__init__(*args, **kwargs, phase_id="P1")

    async def run(self) -> dict[str, Any]:
        """Extract constraints from user prompt.

        Returns:
            Dictionary of extracted constraints.
        """
        user_prompt = await self._get_required("user_prompt")
        self.logger.info("parsing_request", prompt_length=len(user_prompt))

        # Simplified implementation - in production, use LLM to extract constraints
        constraints = {
            "action": "refactor",
            "scope": "codebase",
            "prompt": user_prompt,
        }

        self.logger.info("request_parsed", constraints=constraints)
        return constraints
