"""
watson_client.py
────────────────
A paper-thin, retry-hardened wrapper around IBM watsonx.ai Foundation
Models.  The goal is *just enough* abstraction so the rest of the code
base never needs to know about SDK details, authentication headers, or
token accounting.

Dependencies
------------
pip install ibm-watsonx-ai==0.1.2  (version current as of May-2025)

Environment Variables (read via config.Settings)
------------------------------------------------
WATSONX_API_KEY        – service credential
WATSONX_PROJECT_ID     – workspace ID inside watsonx.ai
WATSONX_URL            – optional; defaults to cloud.ibm.com endpoint
DEFAULT_LLM_MODEL_ID   – e.g. "granite-20b-chat"
LLM_TEMPERATURE        – float, default 0.2
"""

from __future__ import annotations

import json
import os
import time
from typing import List, Dict, Any, Optional

import backoff  # type: ignore
from ibm_watsonx_ai.foundation_models import Model

from config import Settings


def _backoff_hdlr(details):
    """backoff debug helper"""
    wait = details["wait"]
    tries = details["tries"]
    exc = details["exception"]
    print(
        f"[watson_client] retry {tries} in {wait:.1f}s "
        f"after exception: {exc!r}"
    )


class WatsonClient:
    """
    Stateless helper around IBM watsonx.ai chat completions.
    A single instance can be shared across threads or asyncio tasks.
    """

    def __init__(
        self,
        api_key: str,
        project_id: str,
        url: str = "https://us-south.ml.cloud.ibm.com",
        default_model: str = "granite-20b-chat",
        default_temperature: float = 0.2,
    ):
        self._model_id = default_model
        self._temperature = default_temperature

        # Initialise the official SDK model object
        self._model = Model(
            model_id=default_model,
            params={
                "project_id": project_id,
                "url": url,
                "api_key": api_key,
            },
        )

    # --------------------------------------------------------------------- #
    # Constructors
    # --------------------------------------------------------------------- #
    @classmethod
    def from_env(cls) -> "WatsonClient":
        """Create a client from environment variables via Settings."""
        cfg = Settings()  # validates presence and types
        return cls(
            api_key=cfg.WATSONX_API_KEY,
            project_id=cfg.WATSONX_PROJECT_ID,
            url=cfg.WATSONX_URL,
            default_model=cfg.DEFAULT_LLM_MODEL_ID,
            default_temperature=cfg.LLM_TEMPERATURE,
        )

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    @backoff.on_exception(
        backoff.expo,
        Exception,  # noqa: BLE001  – watsonx SDK raises base Exception :-(
        max_tries=4,
        max_time=60,
        on_backoff=_backoff_hdlr,
    )
    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float | None = None,
        model_id: str | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Call the watsonx.ai *chat* interface with OpenAI-style messages.

        The SDK expects a flattened prompt, so we apply a very simple
        role → text mapping:

            "system":  <<prefix>>
            "user":    \n\nUser: <content>
            "assistant": \n\nAssistant: <content>

        Parameters
        ----------
        messages
            OpenAI-style message dicts, in chronological order.
        temperature
            Optional override of the sampling temperature.
        model_id
            Optional override of the foundation-model slug.
        max_tokens
            Hard cap on the completion length.  If ``None`` the SDK
            default (currently 1024) is used.

        Returns
        -------
        str
            The assistant’s reply content (not including role markers).
        """
        prompt = self._serialize_messages(messages)
        params: Dict[str, Any] = {
            "temperature": (
                temperature if temperature is not None else self._temperature
            ),
        }
        if max_tokens:
            params["max_new_tokens"] = max_tokens

        # Create a *new* Model each request if the caller changed model_id
        model_to_use = self._model
        if model_id and model_id != self._model_id:
            model_to_use = Model(
                model_id=model_id,
                params=self._model._params,  # reuse auth / project / url
            )

        start = time.time()
        response = model_to_use.generate(prompt, **params)

        # Standardise to OpenAI-like str return
        elapsed = (time.time() - start) * 1000
        content = response["results"][0]["generated_text"].lstrip()
        print(
            f"[watson_client] model={model_to_use.model_id} "
            f"tokens_in≈{len(prompt.split())} "
            f"tokens_out≈{len(content.split())} "
            f"{elapsed:.0f} ms"
        )
        return content

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #
    @staticmethod
    def _serialize_messages(messages: List[Dict[str, str]]) -> str:
        """
        Transform an OpenAI “messages” list into the prompt format that
        IBM watsonx *generate* expects.  Watsonx currently uses a single
        string prompt; the Foundation-Models “understand” the tags
        ``<|system|>``, ``<|user|>``, and ``<|assistant|>`` but we’ll
        keep it simple and readable.

        Example result:

            <<system>>
            You are an LLM that follows instructions.

            User:
            Explain what an AST is.

            Assistant:
            (… prior assistant messages if present …)

            User:
            Please summarise your answer in two bullet points.
        """
        block_map = {
            "system": "<<system>>",
            "user": "User:",
            "assistant": "Assistant:",
        }
        lines: list[str] = []
        for m in messages:
            role = m["role"]
            content = m["content"]
            lines.append(block_map.get(role, role))
            lines.append(content)
            lines.append("")  # blank line for readability
        return "\n".join(lines).strip()
