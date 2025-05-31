"""
Low-level LLM helpers for *ai-project-features*.

At the moment we expose just two call-sites:

    from llm import client            # lazily-constructed singleton
    from llm import generate          # convenience wrapper

`client` is an instance of :class:`WatsonClient` (see *watson_client.py*),
pre-configured from environment variables via `config.Settings`.

If you need multiple, differently-configured Watson Clients (e.g. one
with deterministic temperature=0 and another with “creative” params),
instantiate :class:`WatsonClient` directly.
"""
from __future__ import annotations

from typing import List, Dict, Any

from .watson_client import WatsonClient

# A lazily-created singleton; instantiated when `generate()` is called
_client: WatsonClient | None = None


def _get_client() -> WatsonClient:
    global _client  # pylint: disable=global-statement
    if _client is None:
        _client = WatsonClient.from_env()
    return _client


def generate(
    messages: List[Dict[str, str]],
    *,
    temperature: float | None = None,
    model_id: str | None = None,
    max_tokens: int | None = None,
) -> str:
    """
    Thin convenience wrapper around :pymeth:`WatsonClient.chat`.

    Parameters
    ----------
    messages
        List of ``{"role": <"system"|"user"|"assistant">, "content": str}``
        dictionaries.
    temperature
        Override the default sampling temperature.
    model_id
        Override the default foundation-model slug (e.g. ``"granite-20b"``).
    max_tokens
        Optional hard cap for the completion.

    Returns
    -------
    str
        The assistant’s reply *content*.
    """
    return _get_client().chat(
        messages,
        temperature=temperature,
        model_id=model_id,
        max_tokens=max_tokens,
    )


# Re-export for direct use
client = _get_client  # note: a *function* that returns the singleton
__all__: list[str] = ["generate", "client", "WatsonClient"]
