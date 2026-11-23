from typer.testing import CliRunner

from q.cli import app
from q.commands.ask import build_messages
from q.history import History

runner = CliRunner()


def test_ask_streams_answer(fake_ollama):
    result = runner.invoke(app, ["ask", "hi", "-m", "tiny"])
    assert result.exit_code == 0
    assert "Hello from Q." in result.output
    assert fake_ollama[0]["model"] == "tiny"


def test_ask_with_file(fake_ollama, tmp_path):
    f = tmp_path / "notes.md"
    f.write_text("Paging avoids external fragmentation.")
    result = runner.invoke(app, ["ask", "summarise", "-f", str(f)])
    assert result.exit_code == 0
    sent = fake_ollama[0]["messages"][-1]["content"]
    assert "external fragmentation" in sent and sent.endswith("summarise")


def test_ask_missing_file_is_a_clean_error(fake_ollama):
    result = runner.invoke(app, ["ask", "x", "-f", "nope.txt"])
    assert result.exit_code == 1
    assert "No such file" in result.output


def test_build_messages_without_file():
    msgs = build_messages("why?", None, None)
    assert msgs[-1] == {"role": "user", "content": "why?"}


def test_chat_session_saves_history(fake_ollama):
    result = runner.invoke(app, ["chat"], input="hi there\n/history\n/exit\n")
    assert result.exit_code == 0, result.output
    assert "Hello from Q." in result.output
    conv = History().recent()[0]
    assert conv["title"] == "hi there" and conv["n"] == 3  # system, user, assistant


def test_chat_sends_whole_history_each_turn(fake_ollama):
    runner.invoke(app, ["chat"], input="one\ntwo\n/exit\n")
    second_call = fake_ollama[1]["messages"]
    assert [m["role"] for m in second_call] == ["system", "user", "assistant", "user"]


def test_chat_clear_starts_fresh(fake_ollama):
    runner.invoke(app, ["chat"], input="one\n/clear\ntwo\n/exit\n")
    assert [m["role"] for m in fake_ollama[1]["messages"]] == ["system", "user"]


def test_chat_system_prompt_can_be_changed(fake_ollama):
    runner.invoke(app, ["chat"], input="/system new prompt\nhi\n/exit\n")
    assert fake_ollama[0]["messages"][0]["content"] == "new prompt"


def test_unknown_slash_command(fake_ollama):
    result = runner.invoke(app, ["chat"], input="/fly\n/exit\n")
    assert "Unknown command" in result.output
