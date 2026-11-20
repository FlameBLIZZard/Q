"""`q agent`: give the model a task it can solve with tools."""

from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Confirm

from q import llm, tools
from q.agent import run_agent

console = Console()

# Small models often cannot call tools. qwen2.5:7b can, and fits easily in 24 GB.
AGENT_MODEL = "qwen2.5:7b"


def ask_user(command: str) -> bool:
    console.print(f"[bold yellow]Q wants to run:[/bold yellow] {command}")
    return Confirm.ask("Run it?", default=False, console=console)


def show_step(name: str, args: dict, result: str) -> None:
    shown = ", ".join(f"{k}={v!r}" for k, v in args.items())
    first = result.splitlines()[0][:80] if result else ""
    console.print(f"[dim]  calling {name}({shown}) -> {first}[/dim]")


def agent(
    task: str = typer.Argument(..., help='For example: "which file here talks about attention?"'),
    model: str = typer.Option(AGENT_MODEL, "--model", "-m", help="A model with tool support."),
    max_steps: int = typer.Option(8, "--max-steps", help="Give up after this many rounds."),
) -> None:
    """Let the model read, list and search files in this folder to finish a task."""
    tools.set_root(Path.cwd())  # the agent may only see the folder you started it in
    tools.set_confirm(ask_user)  # and must ask you before every shell command
    try:
        # No spinner here on purpose: it would draw over the y/N question for shell commands.
        answer = run_agent(task, model=model, max_steps=max_steps, on_step=show_step)
    except llm.LLMError as err:
        console.print(f"[red]{err}[/red]")
        raise typer.Exit(1) from err
    console.print(Markdown(answer))
