"""`q ask`: one question, one streamed answer, optionally about a file."""

from pathlib import Path

import typer
from rich.console import Console

from q import config, llm
from q.commands.chat import stream_and_render
from q.files import FileReadError, read_text

console = Console()


def build_messages(question: str, file_text: str | None, file_name: str | None) -> list[dict]:
    messages = [{"role": "system", "content": config.DEFAULT_SYSTEM}]
    if file_text is not None:
        # Put the file before the question, clearly fenced, so the model knows
        # which part is material and which part is the instruction.
        question = f"Here is the file {file_name}:\n<file>\n{file_text}\n</file>\n\n{question}"
    messages.append({"role": "user", "content": question})
    return messages


def ask(
    question: str = typer.Argument(..., help="What to ask."),
    file: Path | None = typer.Option(None, "--file", "-f", help="A text, Markdown, code or PDF file."),
    model: str = typer.Option(config.DEFAULT_MODEL, "--model", "-m"),
    temperature: float | None = typer.Option(None, "--temperature", "-t"),
) -> None:
    """Ask one question, for example: q ask "summarise this" -f notes.pdf"""
    file_text = None
    if file is not None:
        try:
            file_text = read_text(file)
        except FileReadError as err:
            console.print(f"[red]{err}[/red]")
            raise typer.Exit(1) from err
    try:
        stream_and_render(
            build_messages(question, file_text, file.name if file else None), model, temperature
        )
    except llm.LLMError as err:
        console.print(f"[red]{err}[/red]")
        raise typer.Exit(1) from err
