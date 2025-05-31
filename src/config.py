"""
src/config.py
════════════════════════════════════════════════════════════════════════════
Centralised configuration for *ai-project-features*.

All “knobs” come from environment variables **or** the optional `.env`
file in the project root (thanks to `dotenv` support baked into Pydantic).

Why it matters
--------------
*  **Single source of truth** – Agents and helpers import `Settings()`; no
   hard-coded secrets scattered across the codebase.
*  **Early failure** – Missing keys or out-of-range values raise a clear
   `ValidationError` *before* we ever hit the LLM or touch the filesystem.
*  **Intellisense-friendly** – Every field has type hints and docstrings.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """
    All configuration values with type validation.

    You can override any field by exporting an environment variable with
    the same name (case-insensitive), or by editing a local `.env` file
    next to the repo root.

    Examples
    --------
    ```bash
    export WATSONX_API_KEY="abc-123"
    export LLM_TEMPERATURE="0.0"     # fully deterministic
    ```
    """

    # ──────────────────────────────────────────────────────────────────────
    # Watsonx.ai credentials & defaults
    # ──────────────────────────────────────────────────────────────────────
    WATSONX_API_KEY: str = Field(..., env="WATSONX_API_KEY")
    WATSONX_PROJECT_ID: str = Field(..., env="WATSONX_PROJECT_ID")
    WATSONX_URL: str = Field(
        "https://us-south.ml.cloud.ibm.com",
        env="WATSONX_URL",
        description="Base URL for IBM watsonx.ai",
    )

    DEFAULT_LLM_MODEL_ID: str = Field(
        "granite-20b-chat",
        env="DEFAULT_LLM_MODEL_ID",
        description="Foundation-model slug used unless an agent overrides it.",
    )

    LLM_TEMPERATURE: float = Field(
        0.2,
        env="LLM_TEMPERATURE",
        ge=0.0,
        le=1.0,
        description="Sampling temperature passed to Watsonx; 0 = deterministic.",
    )

    # ──────────────────────────────────────────────────────────────────────
    # Workflow & tooling knobs
    # ──────────────────────────────────────────────────────────────────────
    MAX_P5_ATTEMPTS: int = Field(
        4,
        env="MAX_P5_ATTEMPTS",
        gt=0,
        le=10,
        description="Retry budget for the code-write ⇄ static-check loop.",
    )

    PREVIEW_BYTES: int = Field(
        120,
        env="PREVIEW_BYTES",
        ge=32,
        le=4096,
        description="How many bytes of each file `file_scanner` shows as preview.",
    )

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        "INFO",
        env="LOG_LEVEL",
        description="Root log-level for the whole application.",
    )

    # ──────────────────────────────────────────────────────────────────────
    # Derived / convenience fields
    # ──────────────────────────────────────────────────────────────────────
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

    @property
    def SRC_DIR(self) -> Path:  # noqa: N802  (property looks like constant)
        """Absolute path to the `src/` directory."""
        return self.PROJECT_ROOT / "src"

    # ──────────────────────────────────────────────────────────────────────
    # Validators
    # ──────────────────────────────────────────────────────────────────────
    @validator("DEFAULT_LLM_MODEL_ID")
    def _model_slug_not_blank(cls, v: str) -> str:  # noqa: N805
        if not v.strip():
            raise ValueError("DEFAULT_LLM_MODEL_ID must not be empty.")
        return v

    # ──────────────────────────────────────────────────────────────────────
    # pydantic config
    # ──────────────────────────────────────────────────────────────────────
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # allow `watsonx_api_key=...` too
        frozen = True           # make Settings immutable once created

    # ──────────────────────────────────────────────────────────────────────
    # Convenience dunder methods
    # ──────────────────────────────────────────────────────────────────────
    def __repr__(self) -> str:  # pragma: no cover
        """Short one-liner for debug sessions; masks secrets."""
        api_key_masked = (
            self.WATSONX_API_KEY[:4] + "…" + self.WATSONX_API_KEY[-4:]
            if self.WATSONX_API_KEY
            else "NOT-SET"
        )
        return (
            f"Settings(model='{self.DEFAULT_LLM_MODEL_ID}', "
            f"temp={self.LLM_TEMPERATURE}, "
            f"api_key='{api_key_masked}')"
        )
