"""The Typer app. Each command lives in its own module under q/commands/."""

import typer

from q import __version__
from q.commands.agent import agent
from q.commands.ask import ask
from q.commands.chat import chat

app = typer.Typer(
    help="Q: chat with local LLMs from your terminal.",
    no_args_is_help=True,
    add_completion=False,
)
app.command()(chat)
app.command()(ask)
app.command()(agent)


@app.command()
def version() -> None:
    """Print Q's version."""
    typer.echo(__version__)


if __name__ == "__main__":
    app()
