"""Pytest configuration and shared fixtures for Aurora tests."""
import pytest
from aurora.core.memory import Memory
from aurora.core.config import Settings


@pytest.fixture
def memory():
    """Provide a fresh Memory instance for each test."""
    return Memory()


@pytest.fixture
def mock_settings(monkeypatch):
    """Provide mock settings with test credentials."""
    monkeypatch.setenv("WATSONX_API_KEY", "test_key_12345678")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "test_project_12345")
    return Settings()
