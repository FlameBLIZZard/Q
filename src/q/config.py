"""Defaults and paths in one place, so every module agrees on them."""

import os
from pathlib import Path

# Small enough to run on CPU, good enough to be useful. Override with Q_MODEL or --model.
DEFAULT_MODEL = os.environ.get("Q_MODEL", "llama3.2:3b")

DEFAULT_SYSTEM = "You are Q, a concise terminal assistant. Answer clearly and briefly."

# Everything Q stores lives in ~/.q (override with Q_HOME, which the tests use).
Q_HOME = Path(os.environ.get("Q_HOME", Path.home() / ".q"))


def history_path() -> Path:
    return Q_HOME / "history.db"
