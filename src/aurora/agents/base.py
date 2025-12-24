"""Base agent class for Aurora multi-agent system.

This module defines the abstract base class that all Aurora agents inherit from.
It provides common functionality for memory access, logging, and execution patterns.

Examples:
    >>> from aurora.agents.base import BaseAgent
    >>> from aurora.core.memory import Memory
    >>> from aurora.core.config import get_settings
    >>>
    >>> class MyAgent(BaseAgent):
    ...     async def run(self) -> str:
    ...         prompt = await self.memory.get("user_prompt")
    ...         return f"Processed: {prompt}"
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from aurora.core.config import Settings
from aurora.core.logging import get_logger
from aurora.core.memory import Memory


class BaseAgent(ABC):
    """Abstract base class for all Aurora agents.

    All agents in the Aurora system inherit from this base class, which provides
    common functionality for memory access, configuration, and logging.

    Agents are designed to be stateless and side-effect-free, communicating only
    through the shared memory system.

    Attributes:
        memory: Shared memory for agent communication.
        settings: Application configuration.
        logger: Structured logger for this agent.
        phase_id: Identifier for this agent's pipeline phase.

    Examples:
        >>> import asyncio
        >>> from aurora.core.memory import Memory
        >>> from aurora.core.config import get_settings
        >>>
        >>> class EchoAgent(BaseAgent):
        ...     async def run(self) -> str:
        ...         msg = await self.memory.get("message", "")
        ...         return f"Echo: {msg}"
        >>>
        >>> async def example():
        ...     memory = Memory()
        ...     await memory.put("message", "Hello")
        ...     agent = EchoAgent(memory, get_settings())
        ...     result = await agent.run()
        ...     print(result)
        >>> asyncio.run(example())
        Echo: Hello
    """

    def __init__(
        self,
        memory: Memory,
        settings: Settings,
        *,
        phase_id: str = "UNKNOWN",
    ) -> None:
        """Initialize the agent with shared resources.

        Args:
            memory: Shared memory for agent communication.
            settings: Application configuration.
            phase_id: Pipeline phase identifier (e.g., "P1", "P5").

        Examples:
            >>> from aurora.core.memory import Memory
            >>> from aurora.core.config import get_settings
            >>> memory = Memory()
            >>> settings = get_settings()
            >>> agent = EchoAgent(memory, settings, phase_id="P1")
        """
        self.memory = memory
        self.settings = settings
        self.phase_id = phase_id
        self.logger = get_logger(self.__class__.__name__)

        self.logger.debug(
            "agent_initialized",
            agent=self.__class__.__name__,
            phase=phase_id,
        )

    @abstractmethod
    async def run(self) -> Any:
        """Execute the agent's primary task.

        This method must be implemented by all concrete agents. It should:
        1. Read required inputs from shared memory
        2. Perform its specialized task (analysis, generation, validation)
        3. Return results (optionally writing to memory)

        Returns:
            Agent-specific result (type varies by agent).

        Raises:
            AgentExecutionError: If the agent fails to complete its task.

        Examples:
            >>> import asyncio
            >>> async def example():
            ...     agent = MyAgent(memory, settings)
            ...     result = await agent.run()
            >>> asyncio.run(example())
        """
        ...

    async def _get_required(self, key: str) -> Any:
        """Get a required value from memory, raising if missing.

        Args:
            key: The memory key to retrieve.

        Returns:
            The value stored under the key.

        Raises:
            AgentExecutionError: If the key doesn't exist in memory.

        Examples:
            >>> import asyncio
            >>> async def example():
            ...     prompt = await agent._get_required("user_prompt")
            >>> asyncio.run(example())
        """
        from aurora.core.exceptions import AgentExecutionError

        value = await self.memory.get(key)
        if value is None:
            msg = f"Required memory key '{key}' not found"
            self.logger.error("missing_required_key", key=key, phase=self.phase_id)
            raise AgentExecutionError(
                msg,
                details={"key": key, "phase": self.phase_id},
            )
        return value

    async def _get_optional(self, key: str, default: Any = None) -> Any:
        """Get an optional value from memory with a default.

        Args:
            key: The memory key to retrieve.
            default: Default value if key doesn't exist.

        Returns:
            The stored value or the default.

        Examples:
            >>> import asyncio
            >>> async def example():
            ...     snippets = await agent._get_optional("architecture_snippets", [])
            >>> asyncio.run(example())
        """
        value = await self.memory.get(key, default)
        self.logger.debug("retrieved_optional", key=key, has_value=value is not None)
        return value

    def __repr__(self) -> str:
        """Generate debug representation of the agent.

        Returns:
            String representation with class name and phase ID.
        """
        return f"{self.__class__.__name__}(phase={self.phase_id!r})"
