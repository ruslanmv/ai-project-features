"""Tests for shared memory system."""
import pytest
from aurora.core.memory import Memory
from aurora.core.exceptions import ValidationError


@pytest.mark.asyncio
class TestMemory:
    """Test suite for Memory class."""

    async def test_should_store_and_retrieve_values(self):
        """Memory should store and retrieve values correctly."""
        memory = Memory()
        
        await memory.put("key1", "value1")
        await memory.put("key2", 42)
        
        assert await memory.get("key1") == "value1"
        assert await memory.get("key2") == 42

    async def test_should_return_default_for_missing_keys(self):
        """Memory should return default for non-existent keys."""
        memory = Memory()
        
        result = await memory.get("missing", default="default_value")
        
        assert result == "default_value"

    async def test_should_check_key_existence(self):
        """Memory should correctly check if keys exist."""
        memory = Memory()
        
        await memory.put("exists", "value")
        
        assert await memory.has("exists")
        assert not await memory.has("missing")

    async def test_should_delete_keys(self):
        """Memory should delete keys correctly."""
        memory = Memory()
        
        await memory.put("temp", "value")
        removed = await memory.delete("temp")
        
        assert removed
        assert not await memory.has("temp")

    async def test_should_clear_all_data(self):
        """Memory should clear all data."""
        memory = Memory()
        
        await memory.put("key1", "value1")
        await memory.put("key2", "value2")
        await memory.clear()
        
        assert not await memory.has("key1")
        assert not await memory.has("key2")

    async def test_should_list_all_keys(self):
        """Memory should list all stored keys."""
        memory = Memory()
        
        await memory.put("a", 1)
        await memory.put("b", 2)
        await memory.put("c", 3)
        
        keys = await memory.keys()
        
        assert set(keys) == {"a", "b", "c"}

    async def test_should_provide_snapshot(self):
        """Memory should provide a snapshot of all data."""
        memory = Memory()
        
        await memory.put("x", 10)
        await memory.put("y", 20)
        
        snapshot = await memory.snapshot()
        
        assert snapshot == {"x": 10, "y": 20}

    async def test_should_reject_invalid_keys(self):
        """Memory should reject invalid keys."""
        memory = Memory()
        
        with pytest.raises(ValidationError, match="non-empty string"):
            await memory.put("", "value")
        
        with pytest.raises(ValidationError):
            await memory.put("   ", "value")
