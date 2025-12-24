"""Tests for exception hierarchy."""
import pytest
from aurora.core.exceptions import (
    AuroraException,
    ConfigurationError,
    ValidationError,
    AgentExecutionError,
)


class TestAuroraException:
    """Test suite for base AuroraException."""

    def test_should_store_message_and_details(self):
        """Exception should store message and details."""
        exc = AuroraException(
            "Test error",
            details={"code": 42, "field": "test"}
        )
        
        assert exc.message == "Test error"
        assert exc.details == {"code": 42, "field": "test"}

    def test_should_provide_context(self):
        """Exception should provide context dictionary."""
        exc = ValidationError(
            "Invalid input",
            details={"field": "prompt", "error": "too short"}
        )
        
        context = exc.get_context()
        
        assert context["type"] == "ValidationError"
        assert context["message"] == "Invalid input"
        assert context["details"]["field"] == "prompt"

    def test_should_format_str_with_details(self):
        """Exception str should include details."""
        exc = AuroraException(
            "Error occurred",
            details={"x": 1, "y": 2}
        )
        
        exc_str = str(exc)
        
        assert "Error occurred" in exc_str
        assert "x=1" in exc_str
        assert "y=2" in exc_str

    def test_should_wrap_original_exception(self):
        """Exception should wrap original exceptions."""
        original = ValueError("Original error")
        exc = ConfigurationError(
            "Config failed",
            original_exception=original
        )
        
        assert exc.original_exception is original
