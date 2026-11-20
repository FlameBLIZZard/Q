"""A thin wrapper around the Ollama client.

Every other module talks to the model through this file. That gives us one place to
handle errors kindly and one thing to mock in tests.
"""

from collections.abc import Iterator

import httpx
import ollama


class LLMError(Exception):
    """An error with a message meant for the user, not a stack trace."""


def friendly_error(err: Exception, model: str) -> LLMError:
    if isinstance(err, (ConnectionError, httpx.ConnectError)):
        return LLMError("Ollama is not running. Start it with: ollama serve")
    if isinstance(err, ollama.ResponseError) and err.status_code == 404:
        return LLMError(f"Model '{model}' is not installed. Get it with: ollama pull {model}")
    if isinstance(err, ollama.ResponseError) and "does not support tools" in str(err):
        return LLMError(f"Model '{model}' cannot use tools. Try: q agent -m qwen2.5:7b ...")
    return LLMError(f"Ollama error: {err}")


def stream_chat(
    messages: list[dict],
    model: str,
    temperature: float | None = None,
) -> Iterator[str]:
    """Yield the reply piece by piece as the model generates it.

    Why stream: the first words appear in well under a second, even though the
    whole answer may take several seconds. The model has no memory, so the full
    `messages` list (the history) is sent every turn.
    """
    options = {"temperature": temperature} if temperature is not None else None
    try:
        for chunk in ollama.chat(model=model, messages=messages, stream=True, options=options):
            piece = chunk["message"]["content"]
            if piece:
                yield piece
    except LLMError:
        raise
    except Exception as err:  # turn any client error into a readable message
        raise friendly_error(err, model) from err


def list_models() -> list[str]:
    """Names of the models installed in Ollama."""
    try:
        resp = ollama.list()
    except Exception as err:
        raise friendly_error(err, "") from err
    return [m.model for m in resp.models]
