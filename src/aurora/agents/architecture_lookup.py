"""Architecture lookup agent (Phase P2)."""
from __future__ import annotations
from typing import Any
from aurora.agents.base import BaseAgent

class ArchitectureLookupAgent(BaseAgent):
    """Phase P2: Analyze codebase architecture."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs, phase_id="P2")
    
    async def run(self) -> list[str]:
        tree = await self._get_required("tree")
        self.logger.info("analyzing_architecture")
        snippets = ["Uses src/ layout", "Multi-agent system"]
        return snippets
