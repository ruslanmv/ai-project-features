"""Multi-agent orchestrator for Aurora refactoring workflow.

This module implements the main workflow orchestrator that coordinates all
refactoring phases from code scanning through final documentation generation.

The orchestrator follows a deterministic pipeline:
    Z → P0 → P1 → P2 → P3 → P4 → P5 → D1 → P6 → OUT

Each phase is executed sequentially with shared memory for data passing.

Examples:
    >>> import asyncio
    >>> from aurora.core.orchestrator import RefactorOrchestrator
    >>>
    >>> async def main():
    ...     orchestrator = RefactorOrchestrator()
    ...     result = await orchestrator.run("project.zip", "Add logging")
    ...     print(result)
    >>> asyncio.run(main())
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from aurora.core.config import get_settings
from aurora.core.exceptions import AgentExecutionError, FileOperationError, TimeoutError as AuroraTimeoutError
from aurora.core.logging import get_logger, log_exception
from aurora.core.memory import Memory

logger = get_logger(__name__)


class RefactorOrchestrator:
    """Orchestrates the multi-agent refactoring workflow.

    This class manages the entire refactoring pipeline, coordinating multiple
    AI agents to analyze code, plan changes, generate patches, and validate
    results.

    Attributes:
        settings: Application configuration.
        memory: Shared memory for agent communication.
        progress_callback: Optional callback for progress updates.

    Examples:
        >>> import asyncio
        >>> async def example():
        ...     orchestrator = RefactorOrchestrator()
        ...     result = await orchestrator.run("app.zip", "Add type hints")
        >>> asyncio.run(example())
    """

    def __init__(self) -> None:
        """Initialize the orchestrator with settings and memory."""
        self.settings = get_settings()
        self.memory = Memory()
        self.progress_callback: Callable[[str, str], Awaitable[None]] | None = None
        logger.info("orchestrator_initialized", timeout=self.settings.timeout_seconds)

    def set_progress_callback(
        self,
        callback: Callable[[str, str], Awaitable[None]],
    ) -> None:
        """Set a callback function for progress updates.

        Args:
            callback: Async function that receives (phase, status) updates.

        Examples:
            >>> import asyncio
            >>> async def my_callback(phase: str, status: str) -> None:
            ...     print(f"{phase}: {status}")
            >>> orchestrator = RefactorOrchestrator()
            >>> orchestrator.set_progress_callback(my_callback)
        """
        self.progress_callback = callback

    async def _update_progress(self, phase: str, status: str) -> None:
        """Update progress through the callback if set.

        Args:
            phase: Current phase identifier (e.g., "P1", "P5").
            status: Human-readable status message.
        """
        if self.progress_callback:
            await self.progress_callback(phase, status)
        logger.debug("phase_progress", phase=phase, status=status)

    async def run(self, zip_path: str, user_prompt: str) -> str:
        """Execute the complete refactoring workflow.

        This method runs all pipeline phases in sequence, coordinating data
        flow through shared memory and handling errors gracefully.

        Args:
            zip_path: Path to the ZIP archive containing the codebase.
            user_prompt: Natural language refactoring instruction.

        Returns:
            Markdown-formatted recap of the refactoring results.

        Raises:
            FileOperationError: If ZIP file cannot be read.
            AgentExecutionError: If any agent fails to complete.
            AuroraTimeoutError: If workflow exceeds timeout.

        Examples:
            >>> import asyncio
            >>> async def example():
            ...     orchestrator = RefactorOrchestrator()
            ...     result = await orchestrator.run(
            ...         "project.zip",
            ...         "Add comprehensive docstrings"
            ...     )
            ...     print(result)
            >>> asyncio.run(example())
        """
        logger.info(
            "workflow_started",
            zip_path=zip_path,
            prompt=user_prompt[:100],
            timeout=self.settings.timeout_seconds,
        )

        try:
            # Execute workflow with global timeout
            result = await asyncio.wait_for(
                self._execute_pipeline(zip_path, user_prompt),
                timeout=self.settings.timeout_seconds,
            )

            logger.info("workflow_completed", success=True)
            return result

        except asyncio.TimeoutError as e:
            msg = f"Workflow exceeded timeout of {self.settings.timeout_seconds}s"
            logger.error("workflow_timeout", timeout=self.settings.timeout_seconds)
            raise AuroraTimeoutError(
                msg,
                details={"timeout_seconds": self.settings.timeout_seconds},
            ) from e

        except Exception as e:
            log_exception(logger, e, context={"phase": "workflow_run"})
            raise

    async def _execute_pipeline(self, zip_path: str, user_prompt: str) -> str:
        """Execute all pipeline phases in sequence.

        Args:
            zip_path: Path to ZIP archive.
            user_prompt: User's refactoring instruction.

        Returns:
            Final markdown recap from P6.
        """
        # Phase Z: Scan ZIP file and extract tree
        await self._update_progress("Z", "Scanning codebase")
        await self._phase_z_scan(zip_path)

        # Phase P0: Store user prompt
        await self._update_progress("P0", "Storing context")
        await self._phase_p0_context(user_prompt)

        # Phase P1: Parse and extract constraints
        await self._update_progress("P1", "Extracting constraints")
        await self._phase_p1_parse()

        # Phase P2: Architecture lookup
        await self._update_progress("P2", "Analyzing architecture")
        await self._phase_p2_architecture()

        # Phase P3: Task planning
        await self._update_progress("P3", "Planning tasks")
        await self._phase_p3_planning()

        # Phase P4: Feature instantiation
        await self._update_progress("P4", "Designing features")
        await self._phase_p4_design()

        # Phase P5 + D1: Code generation loop
        await self._update_progress("P5", "Generating code")
        await self._phase_p5_d1_codegen()

        # Phase P6: Documentation assembly
        await self._update_progress("P6", "Generating recap")
        await self._phase_p6_recap()

        # Return final answer
        final_answer = await self.memory.get("final_answer", "")
        if not final_answer:
            msg = "Pipeline completed but no final answer was generated"
            raise AgentExecutionError(msg, details={"phase": "P6"})

        return str(final_answer)

    # ═══════════════════════════════════════════════════════════════════════════
    # Phase Implementations
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_z_scan(self, zip_path: str) -> None:
        """Phase Z: Deterministic ZIP scanning.

        Args:
            zip_path: Path to ZIP archive.

        Raises:
            FileOperationError: If ZIP cannot be read.
        """
        from aurora.tools.file_scanner import scan_zip_async

        try:
            tree = await scan_zip_async(zip_path, self.settings.preview_bytes)
            await self.memory.put("tree", tree)
            await self.memory.put("zip_path", zip_path)
            logger.debug("phase_z_complete", tree_length=len(tree))

        except Exception as e:
            msg = f"Failed to scan ZIP file: {zip_path}"
            logger.error("phase_z_failed", zip_path=zip_path, error=str(e))
            raise FileOperationError(
                msg,
                details={"zip_path": zip_path},
                original_exception=e,
            ) from e

    async def _phase_p0_context(self, user_prompt: str) -> None:
        """Phase P0: Store user context in memory.

        Args:
            user_prompt: User's natural language instruction.
        """
        await self.memory.put("user_prompt", user_prompt)
        logger.debug("phase_p0_complete", prompt_length=len(user_prompt))

    async def _phase_p1_parse(self) -> None:
        """Phase P1: Parse user prompt and extract constraints."""
        from aurora.agents.request_parser import RequestParserAgent

        agent = RequestParserAgent(self.memory, self.settings)
        constraints = await agent.run()
        await self.memory.put("constraints", constraints)
        logger.debug("phase_p1_complete", constraints=constraints)

    async def _phase_p2_architecture(self) -> None:
        """Phase P2: Architecture lookup and analysis."""
        from aurora.agents.architecture_lookup import ArchitectureLookupAgent

        agent = ArchitectureLookupAgent(self.memory, self.settings)
        snippets = await agent.run()
        await self.memory.put("architecture_snippets", snippets)
        logger.debug("phase_p2_complete", snippets_count=len(snippets))

    async def _phase_p3_planning(self) -> None:
        """Phase P3: Task decomposition and planning."""
        from aurora.agents.task_planner import TaskPlannerAgent

        agent = TaskPlannerAgent(self.memory, self.settings)
        tasks = await agent.run()
        await self.memory.put("tasks", tasks)
        logger.debug("phase_p3_complete", task_count=len(tasks))

    async def _phase_p4_design(self) -> None:
        """Phase P4: Feature design and instantiation."""
        from aurora.agents.feature_designer import FeatureDesignerAgent

        agent = FeatureDesignerAgent(self.memory, self.settings)
        design = await agent.run()
        await self.memory.put("design", design)
        logger.debug("phase_p4_complete")

    async def _phase_p5_d1_codegen(self) -> None:
        """Phase P5 + D1: Code generation with validation loop."""
        from aurora.agents.code_generator import CodeGeneratorAgent
        from aurora.agents.static_checker import StaticCheckerAgent

        code_gen = CodeGeneratorAgent(self.memory, self.settings)
        checker = StaticCheckerAgent(self.memory, self.settings)

        for attempt in range(1, self.settings.max_code_gen_attempts + 1):
            await self._update_progress("P5", f"Generating code (attempt {attempt})")
            await code_gen.run()

            await self._update_progress("D1", f"Validating code (attempt {attempt})")
            is_valid = await checker.run()

            if is_valid:
                logger.info("phase_p5_d1_complete", attempts=attempt)
                return

        # Exhausted all attempts
        msg = f"Code generation failed after {self.settings.max_code_gen_attempts} attempts"
        logger.error(
            "phase_p5_d1_failed",
            max_attempts=self.settings.max_code_gen_attempts,
        )
        raise AgentExecutionError(
            msg,
            details={"max_attempts": self.settings.max_code_gen_attempts},
        )

    async def _phase_p6_recap(self) -> None:
        """Phase P6: Generate final documentation recap."""
        from aurora.agents.doc_assembler import DocAssemblerAgent

        agent = DocAssemblerAgent(self.memory, self.settings)
        recap = await agent.run()
        await self.memory.put("final_answer", recap)
        logger.debug("phase_p6_complete", recap_length=len(recap))
