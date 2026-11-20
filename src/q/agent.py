"""The agent loop: let the model use tools until it has an answer.

How it works, in four lines:
  1. Send the task plus a description of every tool to the model.
  2. The model either answers in plain text (done) or asks for one or more tool calls.
  3. We run each requested tool ourselves and append the result as a "tool" message.
  4. Go back to 1 with the longer conversation. Stop after `max_steps` rounds.

The model never runs anything. It can only *ask*; our code decides what really
happens. That is where all the safety lives (see tools.py).
"""

from collections.abc import Callable
from typing import Any

import ollama

from q import llm
from q.tools import ALL_TOOLS, ToolError

AGENT_SYSTEM = (
    "You are Q, a terminal assistant that can use tools to look at files in the user's "
    "current folder, fetch web pages and (with permission) run shell commands. "
    "Use a tool when you need facts you do not have. When you have enough, answer briefly "
    "and mention which files you used."
)

# Called with (tool name, arguments, result) after every tool run, so the CLI can show progress.
StepCallback = Callable[[str, dict, str], None]


def run_tool(name: str, args: dict[str, Any]) -> str:
    """Run one tool call from the model and always return text, never raise.

    Errors go back to the model as text so it can fix its mistake (a wrong path,
    a missing argument) and try again, instead of the whole agent crashing.
    """
    fn = ALL_TOOLS.get(name)
    if fn is None:
        return f"Error: there is no tool called {name}. Available: {', '.join(ALL_TOOLS)}."
    try:
        return str(fn(**args))
    except ToolError as err:
        return f"Error: {err}"
    except TypeError as err:  # the model passed wrong or missing arguments
        return f"Error: bad arguments for {name}: {err}"


def run_agent(
    task: str,
    model: str,
    max_steps: int = 8,
    on_step: StepCallback | None = None,
    chat: Callable[..., Any] | None = None,
) -> str:
    chat = chat or ollama.chat  # tests pass a fake here
    messages: list[Any] = [
        {"role": "system", "content": AGENT_SYSTEM},
        {"role": "user", "content": task},
    ]
    for _ in range(max_steps):
        try:
            resp = chat(model=model, messages=messages, tools=list(ALL_TOOLS.values()))
        except Exception as err:
            raise llm.friendly_error(err, model) from err
        msg = resp.message
        messages.append(msg)  # the model's tool request must stay in the history
        if not msg.tool_calls:
            return msg.content or ""  # no tool requested: this is the final answer
        for call in msg.tool_calls:
            name, args = call.function.name, dict(call.function.arguments or {})
            result = run_tool(name, args)
            if on_step:
                on_step(name, args, result)
            messages.append({"role": "tool", "content": result, "tool_name": name})
    return f"Stopped after {max_steps} steps without a final answer. Try a more specific task."
