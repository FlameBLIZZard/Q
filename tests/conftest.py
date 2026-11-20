"""Shared test setup: tests never touch ~/.q and never need a running model."""

import pytest


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    from q import config

    monkeypatch.setattr(config, "Q_HOME", tmp_path / ".q")
    return tmp_path / ".q"


@pytest.fixture
def fake_ollama(monkeypatch):
    """Replace ollama.chat with a fake that streams a fixed reply and records calls."""
    calls = []

    def fake_chat(model, messages, stream=False, options=None, **kw):
        calls.append({"model": model, "messages": [dict(m) for m in messages], "options": options})
        for piece in ["Hello", " from", " Q."]:
            yield {"message": {"content": piece}}

    monkeypatch.setattr("q.llm.ollama.chat", fake_chat)
    return calls


@pytest.fixture(autouse=True)
def reset_tool_state(monkeypatch):
    """Every test starts with shell commands denied, as in real use."""
    from q import tools

    monkeypatch.setattr(tools, "CONFIRM", tools._deny)
    monkeypatch.setattr(tools, "ROOT", tools.ROOT)
