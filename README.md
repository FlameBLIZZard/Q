# Q

A terminal assistant that chats with local LLMs through [Ollama](https://ollama.com). Everything runs on your own machine: no API keys, no data leaves your PC.

> Status: early (v0.0.1). Streaming chat, one-shot questions about files, saved history and a tool-using agent work. Folder search, local images and a quantization benchmark are on the roadmap below.
>
> New to the code? Read [HOW_Q_WORKS.md](HOW_Q_WORKS.md): 13 short lessons, one per piece.

## Install (for development)

You need Python 3.12+, [uv](https://docs.astral.sh/uv/) and Ollama.

```bash
ollama pull llama3.2:3b          # a small model that also runs on CPU
git clone https://github.com/FlameBLIZZard/q && cd q
uv sync --extra pdf              # installs Q plus PDF support into .venv
uv run q chat
```

## Use

```bash
q chat                           # streaming chat, history saved to ~/.q/history.db
q chat -m qwen2.5:7b -t 0.2      # pick a model and temperature
q ask "explain this" -f notes.md # one-shot question about a text, code or PDF file
q agent "which file here talks about attention? quote it"   # uses tools, asks before shell commands
q version
```

Inside `q chat`:

| Command | Does |
| --- | --- |
| `/model NAME` | switch model (no name: list installed models) |
| `/clear` | start a new conversation |
| `/save FILE` | save the conversation as Markdown |
| `/history` | list recent conversations |
| `/exit` | quit |

Set `Q_MODEL` to change the default model.

## How it works

```
terminal (Typer + Rich) -> commands/chat.py, ask.py, agent.py -> llm.py / agent.py -> Ollama server
                                      |                               |
                                history.py (SQLite ~/.q/history.db)   tools.py (files, web, shell)
```

The model has no memory. Every turn, Q sends the whole conversation so far; the history *is* the memory. That is why long chats get slower and why context length matters.

## Safety

`q agent` file tools can only read inside the folder Q was started in. Every path is resolved (following symlinks and `..`) and refused if it lands outside that folder. `run_shell` asks y/N before every command, defaults to No, and is denied outright unless the agent command has set up the prompt (fail closed). Once you approve a command it runs with your permissions, so read it first. Pages fetched with `web_fetch` can contain prompt injection; the y/N prompt is the guard.

## Development

```bash
uv run pytest      # tests mock Ollama, so no model is needed
uv run ruff check .
```

## Roadmap

- [x] Streaming chat with history and slash commands
- [x] `q ask` with `-f` for text and PDF files
- [x] Sandboxed file tools with tests
- [x] `q agent`: tool-calling loop (read, list, search files; web fetch; shell with confirmation)
- [ ] `q index` / `q search`: embed a folder into ChromaDB and search it
- [ ] `q img`: local images with SD-Turbo (optional extra)
- [ ] `q bench`: speed vs quiz accuracy across quantizations
- [ ] Publish to PyPI

## License

MIT
