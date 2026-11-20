"""Agent loop tests with a scripted fake model: no Ollama needed."""

import sys

import pytest
from ollama import ChatResponse, Message
from typer.testing import CliRunner

from q import tools
from q.agent import run_agent, run_tool
from q.cli import app


def call(name, **args):
    return Message.ToolCall(function=Message.ToolCall.Function(name=name, arguments=args))


class ScriptedModel:
    """Returns pre-written replies in order and records what it was sent."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.seen = []

    def __call__(self, model, messages, tools=None, **kw):
        self.seen.append(list(messages))
        return ChatResponse(model=model, message=self.replies.pop(0))


@pytest.fixture
def folder(tmp_path):
    (tmp_path / "attention.md").write_text("Attention lets each token look at every other token.\n")
    tools.set_root(tmp_path)
    tools.set_confirm(lambda cmd: False)
    return tmp_path


def test_answer_without_tools_stops_at_once(folder):
    model = ScriptedModel(Message(role="assistant", content="42"))
    assert run_agent("hi", model="m", chat=model) == "42"
    assert len(model.seen) == 1


def test_tool_result_goes_back_to_model(folder):
    model = ScriptedModel(
        Message(role="assistant", content="", tool_calls=[call("search_files", query="attention")]),
        Message(role="assistant", content="It is attention.md"),
    )
    steps = []
    answer = run_agent("which file?", model="m", chat=model, on_step=lambda *s: steps.append(s))
    assert answer == "It is attention.md"
    assert steps[0][0] == "search_files"
    tool_msg = model.seen[1][-1]
    assert tool_msg["role"] == "tool" and "attention.md:1" in tool_msg["content"]


def test_max_steps_stops_a_looping_model(folder):
    loop = [Message(role="assistant", content="", tool_calls=[call("list_dir")]) for _ in range(3)]
    assert "Stopped after 3 steps" in run_agent("x", model="m", max_steps=3, chat=ScriptedModel(*loop))


def test_tool_errors_are_returned_not_raised(folder):
    assert run_tool("read_file", {"path": "../../etc/passwd"}).startswith("Error: Refused")
    assert run_tool("delete_everything", {}).startswith("Error: there is no tool")
    assert run_tool("read_file", {"wrong": 1}).startswith("Error: bad arguments")


def test_shell_never_runs_without_approval(folder):
    marker = folder / "ran.txt"
    out = tools.run_shell(f"{sys.executable} -c \"open(r'{marker}', 'w')\"")
    assert "declined" in out and not marker.exists()


def test_shell_runs_after_approval(folder):
    tools.set_confirm(lambda cmd: True)
    out = tools.run_shell(f'{sys.executable} -c "print(6 * 7)"')
    assert out.startswith("exit code 0") and "42" in out


def test_default_confirm_is_deny():
    assert tools._deny("rm -rf /") is False


def test_web_fetch_rejects_other_schemes():
    with pytest.raises(tools.ToolError):
        tools.web_fetch("file:///etc/passwd")


def test_html_to_text():
    page = "<html><style>p{}</style><script>evil()</script><p>Hello &amp; welcome</p></html>"
    assert tools.html_to_text(page) == "Hello & welcome"


def test_agent_command_end_to_end(folder, monkeypatch):
    monkeypatch.chdir(folder)
    model = ScriptedModel(
        Message(role="assistant", content="", tool_calls=[call("read_file", path="attention.md")]),
        Message(role="assistant", content="**Found it** in attention.md"),
    )
    monkeypatch.setattr("q.agent.ollama.chat", model)
    result = CliRunner().invoke(app, ["agent", "what is attention?"])
    assert result.exit_code == 0, result.output
    assert "calling read_file" in result.output and "Found it" in result.output
