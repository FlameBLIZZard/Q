"""Read text out of the files a user passes with -f."""

from pathlib import Path

# Small models have small context windows; trim long files instead of failing.
MAX_CHARS = 24_000


class FileReadError(Exception):
    pass


def read_text(path: Path, max_chars: int = MAX_CHARS) -> str:
    if not path.is_file():
        raise FileReadError(f"No such file: {path}")
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as err:
            raise FileReadError("Reading PDFs needs pypdf: uv add pypdf") from err
        pages = PdfReader(path).pages
        text = "\n\n".join(f"[page {i}]\n{p.extract_text() or ''}" for i, p in enumerate(pages, 1))
    else:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as err:
            raise FileReadError(f"{path.name} is not a text file.") from err
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n\n[trimmed: file was {len(text):,} characters]"
    return text
