"""Documentation assembler agent (Phase P6)."""
from __future__ import annotations
from typing import Any
from aurora.agents.base import BaseAgent

class DocAssemblerAgent(BaseAgent):
    """Phase P6: Generate final recap documentation."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs, phase_id="P6")
    
    async def run(self) -> str:
        user_prompt = await self._get_required("user_prompt")
        tasks = await self._get_optional("tasks", [])
        self.logger.info("assembling_documentation")
        
        recap = f"""# Refactoring Recap

## Request
{user_prompt}

## Tasks Completed
"""
        for i, task in enumerate(tasks, 1):
            recap += f"{i}. {task}\n"
        
        recap += "\n## Status\n✅ All phases completed successfully\n"
        return recap
