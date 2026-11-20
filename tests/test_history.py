from q.history import History


def test_round_trip_and_title(isolated_home):
    h = History()
    conv = h.new_conversation("llama3.2:3b")
    h.add_message(conv, "system", "be brief")
    h.add_message(conv, "user", "what is a deadlock?")
    h.add_message(conv, "assistant", "Two processes waiting on each other.")
    assert [m["role"] for m in h.messages(conv)] == ["system", "user", "assistant"]
    recent = h.recent()
    assert recent[0]["title"] == "what is a deadlock?"
    assert recent[0]["n"] == 3
    assert (isolated_home / "history.db").exists()


def test_title_is_first_user_message_only():
    h = History()
    conv = h.new_conversation("m")
    h.add_message(conv, "user", "first")
    h.add_message(conv, "user", "second")
    assert h.recent()[0]["title"] == "first"


def test_conversations_are_separate():
    h = History()
    a, b = h.new_conversation("m"), h.new_conversation("m")
    h.add_message(a, "user", "in a")
    assert h.messages(b) == []
