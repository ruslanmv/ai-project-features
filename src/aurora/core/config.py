"""Configuration management for Aurora using Pydantic V2 Settings.

This module provides type-safe configuration with automatic environment variable
loading, validation, and sensible defaults for production deployment.

All configuration is immutable after initialization to prevent runtime mutations
that could lead to inconsistent states.

Examples:
    >>> from aurora.core.config import get_settings
    >>> settings = get_settings()
    >>> print(settings.watsonx_api_key[:4] + "...")
    abc1...
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration with type validation and environment variable support.

    All fields can be overridden via environment variables (case-insensitive).
    Secrets should be provided via `.env` file or environment injection in production.

    Attributes:
        watsonx_api_key: IBM Watson X.ai API authentication key.
        watsonx_project_id: Watson X.ai project identifier.
        watsonx_url: Base URL for Watson X.ai API endpoint.
        default_llm_model_id: Default foundation model for LLM calls.
        llm_temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
        max_code_gen_attempts: Maximum retry budget for code generation loop.
        preview_bytes: Number of bytes to preview when scanning files.
        log_level: Application-wide logging level.
        log_json: Enable structured JSON logging for production.
        max_concurrent_agents: Maximum number of agents to run concurrently.
        timeout_seconds: Global timeout for agent operations.

    Examples:
        >>> settings = Settings()  # Loads from environment
        >>> settings = Settings(llm_temperature=0.0)  # Override specific field
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        frozen=True,  # Immutable after creation
        extra="ignore",  # Ignore unknown environment variables
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Watson X.ai Configuration
    # ═══════════════════════════════════════════════════════════════════════════
    watsonx_api_key: str = Field(
        ...,
        description="IBM Watson X.ai API key for authentication",
        min_length=10,
    )

    watsonx_project_id: str = Field(
        ...,
        description="Watson X.ai project ID",
        min_length=10,
    )

    watsonx_url: str = Field(
        default="https://us-south.ml.cloud.ibm.com",
        description="Watson X.ai API endpoint URL",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # LLM Configuration
    # ═══════════════════════════════════════════════════════════════════════════
    default_llm_model_id: str = Field(
        default="granite-20b-chat",
        description="Default foundation model for LLM inference",
        min_length=1,
    )

    llm_temperature: float = Field(
        default=0.2,
        description="Sampling temperature for LLM generation",
        ge=0.0,
        le=1.0,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Workflow Configuration
    # ═══════════════════════════════════════════════════════════════════════════
    max_code_gen_attempts: int = Field(
        default=4,
        description="Maximum retry attempts for code generation + validation loop",
        gt=0,
        le=10,
    )

    preview_bytes: int = Field(
        default=120,
        description="Number of bytes to show in file previews",
        ge=32,
        le=4096,
    )

    max_concurrent_agents: int = Field(
        default=5,
        description="Maximum number of concurrent agent executions",
        gt=0,
        le=20,
    )

    timeout_seconds: int = Field(
        default=300,
        description="Global timeout for agent operations (seconds)",
        gt=0,
        le=3600,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Logging Configuration
    # ═══════════════════════════════════════════════════════════════════════════
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Application-wide logging level",
    )

    log_json: bool = Field(
        default=False,
        description="Enable structured JSON logging (recommended for production)",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Derived Properties
    # ═══════════════════════════════════════════════════════════════════════════
    @property
    def project_root(self) -> Path:
        """Absolute path to the project root directory.

        Returns:
            Path object pointing to the project root (3 levels up from this file).
        """
        return Path(__file__).resolve().parent.parent.parent.parent

    @property
    def src_dir(self) -> Path:
        """Absolute path to the source code directory.

        Returns:
            Path object pointing to the src/aurora directory.
        """
        return self.project_root / "src" / "aurora"

    # ═══════════════════════════════════════════════════════════════════════════
    # Validators
    # ═══════════════════════════════════════════════════════════════════════════
    @field_validator("default_llm_model_id")
    @classmethod
    def validate_model_id(cls, v: str) -> str:
        """Ensure model ID is not empty after stripping whitespace.

        Args:
            v: The model ID to validate.

        Returns:
            The validated model ID.

        Raises:
            ValueError: If model ID is empty or whitespace-only.
        """
        if not v.strip():
            msg = "default_llm_model_id must not be empty or whitespace-only"
            raise ValueError(msg)
        return v.strip()

    @field_validator("watsonx_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure Watson X.ai URL starts with https://.

        Args:
            v: The URL to validate.

        Returns:
            The validated URL.

        Raises:
            ValueError: If URL doesn't start with https://.
        """
        if not v.startswith("https://"):
            msg = "watsonx_url must start with 'https://'"
            raise ValueError(msg)
        return v.rstrip("/")

    # ═══════════════════════════════════════════════════════════════════════════
    # Utility Methods
    # ═══════════════════════════════════════════════════════════════════════════
    def __repr__(self) -> str:
        """Generate a debug-friendly representation with masked secrets.

        Returns:
            String representation with API key partially masked.
        """
        masked_key = (
            f"{self.watsonx_api_key[:4]}...{self.watsonx_api_key[-4:]}"
            if len(self.watsonx_api_key) > 8
            else "***"
        )
        return (
            f"Settings("
            f"model={self.default_llm_model_id!r}, "
            f"temp={self.llm_temperature}, "
            f"api_key={masked_key!r}"
            f")"
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings instance.

    This function returns a singleton Settings instance that is cached
    for the lifetime of the application. Subsequent calls return the
    same instance.

    Returns:
        Cached Settings instance.

    Examples:
        >>> settings = get_settings()
        >>> same_settings = get_settings()
        >>> assert settings is same_settings
    """
    return Settings()
