"""Shared memory (blackboard pattern) for Aurora multi-agent system.

This module provides a thread-safe, type-safe shared memory system that allows
agents to communicate by reading and writing to a common blackboard. This
implementation uses asyncio locks for thread-safety in async contexts.

The blackboard pattern enables loose coupling between agents while maintaining
a clear data flow through the multi-phase pipeline.

Examples:
    >>> import asyncio
    >>> from aurora.core.memory import Memory
    >>>
    >>> async def example():
    ...     memory = Memory()
    ...     await memory.put("user_prompt", "Add logging")
    ...     prompt = await memory.get("user_prompt")
    ...     print(prompt)
    >>> asyncio.run(example())
    Add logging
"""

from __future__ import annotations

import asyncio
from typing import Any, TypeVar

from aurora.core.exceptions import ValidationError
from aurora.core.logging import get_logger

T = TypeVar("T")

logger = get_logger(__name__)


class Memory:
    """Thread-safe shared memory for agent communication.

    This class implements the blackboard pattern, providing a shared data store
    that multiple agents can read from and write to. All operations are async
    and protected by locks to ensure thread-safety.

    The memory is designed to be passed through the agent pipeline, with each
    agent reading inputs from previous phases and writing outputs for subsequent
    phases.

    Attributes:
        _store: Internal dictionary storing key-value pairs.
        _lock: Asyncio lock for thread-safe operations.

    Examples:
        >>> import asyncio
        >>> async def demo():
        ...     mem = Memory()
        ...     await mem.put("tree", "src/\\n  app.py")
        ...     tree = await mem.get("tree")
        ...     assert "app.py" in tree
        >>> asyncio.run(demo())
    """

    def __init__(self) -> None:
        """Initialize empty memory with thread-safety lock."""
        self._store: dict[str, Any] = {}
        self._lock = asyncio.Lock()
        logger.debug("memory_initialized")

    async def put(self, key: str, value: Any) -> None:
        """Store a value in shared memory.

        Args:
            key: The key to store the value under.
            value: The value to store (any type).

        Raises:
            ValidationError: If key is empty or not a string.

        Examples:
            >>> import asyncio
            >>> async def example():
            ...     mem = Memory()
            ...     await mem.put("tasks", ["task1", "task2"])
            ...     await mem.put("count", 42)
            >>> asyncio.run(example())
        """
        if not isinstance(key, str) or not key.strip():
            msg = "Memory key must be a non-empty string"
            raise ValidationError(msg, details={"key": key})

        async with self._lock:
            self._store[key] = value
            logger.debug(
                "memory_write",
                key=key,
                value_type=type(value).__name__,
                store_size=len(self._store),
            )

    async def get(self, key: str, default: T | None = None) -> T | None:
        """Retrieve a value from shared memory.

        Args:
            key: The key to retrieve.
            default: Default value to return if key doesn't exist.

        Returns:
            The stored value, or default if key not found.

        Examples:
            >>> import asyncio
            >>> async def example():
            ...     mem = Memory()
            ...     await mem.put("answer", 42)
            ...     value = await mem.get("answer")
            ...     assert value == 42
            ...     missing = await mem.get("missing", default="not found")
            ...     assert missing == "not found"
            >>> asyncio.run(example())
        """
        async with self._lock:
            value = self._store.get(key, default)
            logger.debug(
                "memory_read",
                key=key,
                found=key in self._store,
                value_type=type(value).__name__ if value is not None else "None",
            )
            return value  # type: ignore[return-value]

    async def has(self, key: str) -> bool:
        """Check if a key exists in memory.

        Args:
            key: The key to check.

        Returns:
            True if key exists, False otherwise.

        Examples:
            >>> import asyncio
            >>> async def example():
            ...     mem = Memory()
            ...     await mem.put("exists", True)
            ...     assert await mem.has("exists")
            ...     assert not await mem.has("missing")
            >>> asyncio.run(example())
        """
        async with self._lock:
            return key in self._store

    async def delete(self, key: str) -> bool:
        """Remove a key from memory.

        Args:
            key: The key to remove.

        Returns:
            True if key was removed, False if key didn't exist.

        Examples:
            >>> import asyncio
            >>> async def example():
            ...     mem = Memory()
            ...     await mem.put("temp", "data")
            ...     removed = await mem.delete("temp")
            ...     assert removed
            ...     assert not await mem.has("temp")
            >>> asyncio.run(example())
        """
        async with self._lock:
            if key in self._store:
                del self._store[key]
                logger.debug("memory_delete", key=key, success=True)
                return True
            logger.debug("memory_delete", key=key, success=False)
            return False

    async def clear(self) -> None:
        """Clear all data from memory.

        This method is useful for resetting state between pipeline runs
        or for cleanup in tests.

        Examples:
            >>> import asyncio
            >>> async def example():
            ...     mem = Memory()
            ...     await mem.put("key1", "value1")
            ...     await mem.put("key2", "value2")
            ...     await mem.clear()
            ...     assert not await mem.has("key1")
            ...     assert not await mem.has("key2")
            >>> asyncio.run(example())
        """
        async with self._lock:
            count = len(self._store)
            self._store.clear()
            logger.debug("memory_cleared", items_removed=count)

    async def keys(self) -> list[str]:
        """Get all keys currently in memory.

        Returns:
            List of all keys in memory.

        Examples:
            >>> import asyncio
            >>> async def example():
            ...     mem = Memory()
            ...     await mem.put("a", 1)
            ...     await mem.put("b", 2)
            ...     keys = await mem.keys()
            ...     assert set(keys) == {"a", "b"}
            >>> asyncio.run(example())
        """
        async with self._lock:
            return list(self._store.keys())

    async def snapshot(self) -> dict[str, Any]:
        """Get a snapshot of all memory contents.

        Returns:
            Copy of the internal store as a dictionary.

        Examples:
            >>> import asyncio
            >>> async def example():
            ...     mem = Memory()
            ...     await mem.put("x", 10)
            ...     await mem.put("y", 20)
            ...     snap = await mem.snapshot()
            ...     assert snap == {"x": 10, "y": 20}
            >>> asyncio.run(example())
        """
        async with self._lock:
            return self._store.copy()

    def __repr__(self) -> str:
        """Generate debug representation of memory state.

        Returns:
            String showing key count and keys.
        """
        keys = list(self._store.keys())
        return f"Memory(keys={len(keys)}, {keys!r})"
