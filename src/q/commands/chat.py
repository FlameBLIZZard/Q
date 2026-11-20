"""`q chat`: an interactive, streaming chat with history and slash commands."""

import typer
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.table import Table


from q import config, llm
from q.history import History

console = Console()

HELP = """[bold]Slash commands[/bold]
  /model NAME   switch model (no NAME: list installed models)
  /clear        start a new conversation
  /save FILE    save this conversation as Markdown
  /history      list recent conversations
  /help         show this list
  /exit         quit"""


def stream_and_render(messages: list[dict], model: str, temperature: float | None) -> str:
    """Stream the reply into a live Markdown view and return the full text."""
    reply = ""
    with Live(Markdown(""), console=console, refresh_per_second=12, vertical_overflow="visible") as live:
        for piece in llm.stream_chat(messages, model=model, temperature=temperature):
            reply += piece
            live.update(Markdown(reply))
    return reply


def save_markdown(messages: list[dict], path: str) -> None:
    lines = []
    for m in messages:
        if m["role"] == "system":
            continue
        who = "You" if m["role"] == "user" else "Q"
        lines.append(f"**{who}:**\n\n{m['content']}\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def chat(
    model: str = typer.Option(config.DEFAULT_MODEL, "--model", "-m", help="Ollama model to use."),
    system: str = typer.Option(config.DEFAULT_SYSTEM, "--system", "-s", help="System prompt."),
    temperature: float | None = typer.Option(None, "--temperature", "-t", help="0 = focused, 1 = creative."),
) -> None:
    """Chat with a local model. Type /help for commands."""
    history = History()
    conv = history.new_conversation(model)
    messages = [{"role": "system", "content": system}]
    history.add_message(conv, "system", system)
    console.print(f"[dim]Q · model {model} · /help for commands · /exit to quit[/dim]")

    while True:
        try:
            user = console.input("[bold cyan]you> [/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            break
        if not user:
            continue

        if user.startswith("/"):
            cmd, _, arg = user.partition(" ")
            arg = arg.strip()
            if cmd in ("/exit", "/quit"):
                break
            elif cmd == "/help":
                console.print(HELP)
            elif cmd == "/clear":
                conv = history.new_conversation(model)
                messages = [{"role": "system", "content": system}]
                history.add_message(conv, "system", system)
                console.print("[dim]New conversation.[/dim]")
            elif cmd == "/model":
                if arg:
                    model = arg
                    console.print(f"[dim]Model is now {model}.[/dim]")
                else:
                    try:
                        console.print("\n".join(llm.list_models()) or "No models installed.")
                    except llm.LLMError as err:
                        console.print(f"[red]{err}[/red]")
            elif cmd == "/save":
                path = arg or f"q-chat-{conv}.md"
                save_markdown(messages, path)
                console.print(f"[dim]Saved to {path}[/dim]")
            elif cmd == "/history":
                table = Table("id", "title", "model", "messages", "started (UTC)")
                for r in history.recent():
                    table.add_row(str(r["id"]), r["title"] or "", r["model"], str(r["n"]), r["created_at"])
                console.print(table)
            elif cmd == "/system":
                if arg:
                    messages[0]["content"] = arg
                    history.add_message(conv, "system", arg)
                    console.print(f"[dim]System prompt is now: {arg}[/dim]")
                else:
                    console.print(f"[dim]System prompt: {messages[0]['content']}[/dim]")
                
            else:
                console.print(f"[yellow]Unknown command {cmd}. Try /help.[/yellow]")
            continue

        messages.append({"role": "user", "content": user})
        history.add_message(conv, "user", user)
        try:
            reply = stream_and_render(messages, model, temperature)
        except llm.LLMError as err:
            console.print(f"[red]{err}[/red]")
            messages.pop()  # drop the unanswered question so the history stays consistent
            continue
        messages.append({"role": "assistant", "content": reply})
        history.add_message(conv, "assistant", reply)

    history.close()
