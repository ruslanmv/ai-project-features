# src/memory.py
# ─────────────────────────────────────────────────────────────────────────────
# Shared blackboard-like in-memory key-value store for agents to exchange data.
# Each agent reads/writes from this singleton dictionary without tight coupling.
# Used in all phases: user_prompt, tree, constraints, tasks, feature_spec, etc.

from typing import Any


class Memory:
    """
    Tiny in-process blackboard memory for cross-agent state sharing.
    All data is stored in a dictionary that lives at module level.

    Example:
        MEM.put("constraints", {...})
        value = MEM.get("constraints")
    """

    def __init__(self):
        self._data: dict[str, Any] = {}

    def put(self, key: str, value: Any) -> None:
        """Stores `value` under `key`."""
        self._data[key] = value

    def get(self, key: str) -> Any:
        """Retrieves the value stored under `key`, or None if not found."""
        return self._data.get(key)

    def clear(self) -> None:
        """Clears the entire memory store (useful for test resets)."""
        self._data.clear()

    def keys(self):
        return self._data.keys()

    def as_dict(self) -> dict[str, Any]:
        """Return a full copy of the underlying memory dictionary."""
        return dict(self._data)


# Global instance used by all agents
MEM = Memory()
