import httpx
import ollama
import pytest

from q import llm


def test_stream_yields_pieces(fake_ollama):
    pieces = list(llm.stream_chat([{"role": "user", "content": "hi"}], model="m"))
    assert "".join(pieces) == "Hello from Q."
    assert fake_ollama[0]["model"] == "m"


def test_temperature_passed_as_option(fake_ollama):
    list(llm.stream_chat([], model="m", temperature=0))
    assert fake_ollama[0]["options"] == {"temperature": 0}


def test_ollama_not_running_gives_friendly_message(monkeypatch):
    def boom(**kw):
        raise httpx.ConnectError("refused")
        yield  # make it a generator like the real streaming call

    monkeypatch.setattr("q.llm.ollama.chat", boom)
    with pytest.raises(llm.LLMError, match="ollama serve"):
        list(llm.stream_chat([], model="m"))


def test_missing_model_suggests_pull(monkeypatch):
    def missing(**kw):
        raise ollama.ResponseError("model not found", status_code=404)
        yield

    monkeypatch.setattr("q.llm.ollama.chat", missing)
    with pytest.raises(llm.LLMError, match="ollama pull m"):
        list(llm.stream_chat([], model="m"))
