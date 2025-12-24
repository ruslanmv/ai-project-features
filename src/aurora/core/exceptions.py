"""Exception hierarchy for Aurora AI Refactor Assistant.

This module defines a structured exception hierarchy that enables precise error
handling and reporting throughout the application. All exceptions include
context information and are designed for both programmatic handling and
user-friendly error messages.

Examples:
    >>> try:
    ...     raise ValidationError("Invalid input", details={"field": "prompt"})
    ... except AuroraException as e:
    ...     print(e.get_context())
"""

from __future__ import annotations

from typing import Any


class AuroraException(Exception):
    """Base exception for all Aurora-specific errors.

    All custom exceptions in the Aurora application should inherit from this
    base class to enable consistent error handling and logging.

    Attributes:
        message: Human-readable error description.
        details: Additional context information (dict).
        original_exception: The underlying exception if this is a wrapper.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        original_exception: Exception | None = None,
    ) -> None:
        """Initialize Aurora exception with context.

        Args:
            message: Human-readable error description.
            details: Optional dictionary with additional context.
            original_exception: Optional underlying exception being wrapped.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.original_exception = original_exception

    def get_context(self) -> dict[str, Any]:
        """Get full exception context as a dictionary.

        Returns:
            Dictionary containing message, details, and exception type.

        Examples:
            >>> exc = AuroraException("Test error", details={"code": 42})
            >>> context = exc.get_context()
            >>> assert context["message"] == "Test error"
            >>> assert context["details"]["code"] == 42
        """
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        """Generate string representation with context.

        Returns:
            Formatted error message with details if present.
        """
        if self.details:
            details_str = ", ".join(f"{k}={v!r}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class ConfigurationError(AuroraException):
    """Raised when application configuration is invalid or incomplete.

    This exception is typically raised during startup when environment
    variables are missing or have invalid values.

    Examples:
        >>> raise ConfigurationError(
        ...     "Missing API key",
        ...     details={"required_var": "WATSONX_API_KEY"}
        ... )
    """


class ValidationError(AuroraException):
    """Raised when input validation fails.

    Used for validating user inputs like prompts, file paths, or
    configuration values.

    Examples:
        >>> raise ValidationError(
        ...     "Invalid prompt length",
        ...     details={"length": 5, "min_required": 10}
        ... )
    """


class AgentExecutionError(AuroraException):
    """Raised when an agent fails to complete its task.

    This exception wraps errors that occur during agent execution,
    providing context about which agent failed and why.

    Examples:
        >>> raise AgentExecutionError(
        ...     "Task planner failed",
        ...     details={"agent": "TaskPlannerAgent", "phase": "P3"}
        ... )
    """


class CodeGenerationError(AuroraException):
    """Raised when code generation or static checking fails.

    This exception is raised when the code generation loop exhausts
    its retry budget or encounters unrecoverable errors.

    Examples:
        >>> raise CodeGenerationError(
        ...     "Static checks never passed",
        ...     details={"attempts": 4, "last_error": "ImportError"}
        ... )
    """


class FileOperationError(AuroraException):
    """Raised when file or ZIP operations fail.

    Used for errors during file scanning, reading, or writing operations.

    Examples:
        >>> raise FileOperationError(
        ...     "Cannot read ZIP file",
        ...     details={"path": "/tmp/project.zip"},
        ...     original_exception=OSError("File not found")
        ... )
    """


class LLMError(AuroraException):
    """Raised when LLM API calls fail.

    This exception wraps errors from Watson X.ai or other LLM providers,
    including timeout, rate limiting, or invalid responses.

    Examples:
        >>> raise LLMError(
        ...     "Watson X.ai API timeout",
        ...     details={"model": "granite-20b-chat", "timeout_seconds": 30}
        ... )
    """


class TimeoutError(AuroraException):
    """Raised when an operation exceeds its time limit.

    Used for agent timeouts or long-running operations that exceed
    configured limits.

    Examples:
        >>> raise TimeoutError(
        ...     "Agent execution timeout",
        ...     details={"agent": "CodeWriterAgent", "timeout_seconds": 300}
        ... )
    """
