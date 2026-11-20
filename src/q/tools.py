"""Tools the agent (Milestone 3) will be allowed to call.

Each tool is a plain Python function with type hints and a docstring: the Ollama
library turns those into the tool description the model sees.

Safety rule: file tools may only touch files inside the folder Q was started in.
We resolve every path (which follows symlinks and removes "..") and check that the
result is still inside that folder. This is the answer to the interview question
"What stops your agent from reading or deleting my home folder?"
"""

import html
import re
import subprocess
from collections.abc import Callable
from pathlib import Path

import httpx

MAX_TOOL_OUTPUT = 4_000  # characters; keeps tool results inside a small model's context
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__"}

# The folder the tools are allowed to see. Tests point it at a temp folder.
ROOT = Path.cwd().resolve()


class ToolError(Exception):
    pass


def set_root(path: Path) -> None:
    global ROOT
    ROOT = Path(path).resolve()


def safe_path(path: str) -> Path:
    """Resolve `path` relative to ROOT and refuse anything that escapes it."""
    candidate = (ROOT / path).resolve()
    if not candidate.is_relative_to(ROOT):
        raise ToolError(f"Refused: {path} is outside {ROOT}")
    return candidate


def read_file(path: str) -> str:
    """Read a text file inside the current folder and return its contents.

    Args:
        path: File path relative to the current folder.
    """
    p = safe_path(path)
    if not p.is_file():
        raise ToolError(f"No such file: {path}")
    text = p.read_text(encoding="utf-8", errors="replace")
    return text[:MAX_TOOL_OUTPUT]


def list_dir(path: str = ".") -> str:
    """List the files and folders in a folder inside the current folder.

    Args:
        path: Folder path relative to the current folder. Defaults to the current folder.
    """
    p = safe_path(path)
    if not p.is_dir():
        raise ToolError(f"No such folder: {path}")
    entries = sorted(p.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
    lines = [f"{e.name}/" if e.is_dir() else e.name for e in entries if e.name not in SKIP_DIRS]
    return "\n".join(lines)[:MAX_TOOL_OUTPUT] or "(empty folder)"


def search_files(query: str, path: str = ".") -> str:
    """Find lines containing `query` (case-insensitive) in text files under a folder.

    Args:
        query: Text to look for.
        path: Folder to search, relative to the current folder.
    """
    base = safe_path(path)
    q = query.lower()
    hits: list[str] = []
    for f in sorted(base.rglob("*")):
        if not f.is_file() or any(part in SKIP_DIRS for part in f.parts):
            continue
        if not f.resolve().is_relative_to(ROOT):  # a symlink pointing outside
            continue
        try:
            for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if q in line.lower():
                    hits.append(f"{f.relative_to(ROOT)}:{n}: {line.strip()}")
        except (UnicodeDecodeError, OSError):
            continue  # binary or unreadable file
        if sum(len(h) for h in hits) > MAX_TOOL_OUTPUT:
            break
    return "\n".join(hits)[:MAX_TOOL_OUTPUT] or f"No matches for '{query}'."


# ---------------------------------------------------------------------------
# Tools with side effects. These reach outside Q, so they get extra guards.
# ---------------------------------------------------------------------------


def _deny(command: str) -> bool:
    return False


# Who approves shell commands. The agent command swaps in a function that asks the
# user y/N. The default is "always no", so if anything forgets to set it, nothing runs.
CONFIRM: Callable[[str], bool] = _deny

SHELL_TIMEOUT = 60  # seconds


def set_confirm(fn: Callable[[str], bool]) -> None:
    global CONFIRM
    CONFIRM = fn


def run_shell(command: str) -> str:
    """Run a shell command in the current folder and return its output. The user must approve it first.

    Args:
        command: The exact command line to run.
    """
    if not CONFIRM(command):
        return "The user declined to run this command."
    try:
        done = subprocess.run(
            command, shell=True, cwd=ROOT, capture_output=True, text=True, timeout=SHELL_TIMEOUT
        )
    except subprocess.TimeoutExpired:
        return f"Stopped: the command ran longer than {SHELL_TIMEOUT} seconds."
    out = (done.stdout + done.stderr).strip() or "(no output)"
    return f"exit code {done.returncode}\n{out}"[:MAX_TOOL_OUTPUT]


def web_fetch(url: str) -> str:
    """Download a web page and return its visible text, trimmed.

    Args:
        url: A full http or https address.
    """
    if not url.startswith(("http://", "https://")):
        raise ToolError("Only http and https addresses are allowed.")
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=15, headers={"User-Agent": "q-local"})
        resp.raise_for_status()
    except httpx.HTTPError as err:
        raise ToolError(f"Could not fetch {url}: {err}") from err
    return html_to_text(resp.text)[:MAX_TOOL_OUTPUT]


def html_to_text(page: str) -> str:
    """Very small HTML-to-text: drop scripts and styles, then all tags, then extra spaces."""
    page = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", page)
    page = re.sub(r"(?s)<[^>]+>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(page)).strip()


# The tools the agent may use, by name. The model only ever sees these.
ALL_TOOLS: dict[str, Callable[..., str]] = {
    f.__name__: f for f in (read_file, list_dir, search_files, web_fetch, run_shell)
}
