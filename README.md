# agent-readable

A lightweight Python protocol for exposing agent-oriented documentation from classes and modules.

<!-- markdownlint-disable MD033 -->
<p align="center">
  <strong><code>logging.Logger</code> compared with <code>agent_help()</code> and <code>help()</code></strong><br>
  <img src="docs/agent_help_vs_help.gif" alt="agent_help vs help">
</p>
<!-- markdownlint-enable MD033 -->

## Problem

AI coding agents recognize established libraries from their training data, but they hallucinate when APIs change, when libraries are new, or when correct usage depends on rules that aren't visible from the API surface — pre-conditions, lifecycle order, anti-patterns, *"use `call()` for non-streaming, `stream()` for streaming."*

Today there's nowhere to put those rules where an agent will reliably find them. Docstrings document the API surface, not behavioral rules. `AGENTS.md` and `llms.txt` work at project granularity, drift fast, and don't travel with refactors. `help()` is verbose and only describes interfaces.

`agent-readable` adds two dunders — `__agent_help__` (full custom output) and `__agent_notes__` (additive guidance that accumulates across inheritance) — that live next to the code. Library authors annotate once; any agent that calls `agent_help(cls)` gets the rules.

```text
help(logging.Logger)        217 lines — every inherited method, dunder, and MRO detail.
agent_help(logging.Logger)   56 lines — structured sections + any author notes.
```

The compactness is a side effect; the structure is the point.

## Installation

```bash
pip install agent-readable
```

Requires Python 3.10+. No runtime dependencies.

## Quickstart

```python
from agent_readable import AgentReadableMixin, agent_help


class Sensor(AgentReadableMixin):
    """Reads a value from a hardware sensor."""

    def __init__(self, pin: int, *, unit: str = "C"): ...

    def read(self) -> float:
        """Read the current sensor value."""

    def calibrate(self, offset: float):
        """Apply a calibration offset."""

    @classmethod
    def __agent_notes__(cls) -> str:
        return """
## Do

- Call `calibrate()` once during setup, before `read()`.

## Do not

- Do not call `read()` before `calibrate()` on first use.
"""


print(agent_help(Sensor))
```

Output:

````
# Sensor

## Constructor

```python
Sensor(pin: int, *, unit: str = 'C')
```

## Purpose

Reads a value from a hardware sensor.

## Public API

- `calibrate(offset: float)` method: Apply a calibration offset.
- `read() -> float` method: Read the current sensor value.

## Agent usage rules

- Prefer the public API listed above.
- Do not use private methods or attributes starting with `_`.
- Do not invent unsupported behavior.
- If usage is ambiguous, prefer the simplest documented usage pattern.

## Notes from class Sensor

## Do

- Call `calibrate()` once during setup, before `read()`.

## Do not

- Do not call `read()` before `calibrate()` on first use.
````

## Why it matters

`help()` documents the **API surface** — what each method does. But agents fail less often on *what methods exist* than on *how to use them*: lifecycle order, pre-conditions, anti-patterns, "this method is for X, that one for Y." Those rules don't fit in docstrings (which describe single methods) and don't belong in a project-level `AGENTS.md` (which describes whole repos). They're class-level, and they need to travel with refactors.

`agent_help()` gives them a home next to the code:

```
# help(sqlite3.Connection) — 200+ lines of terminal output:
Help on class Connection in module sqlite3:

class Connection(builtins.object)
 |  SQLite database connection object.
 |
 |  Methods defined here:
 |
 |  __call__(self, /, *args, **kwargs)
 |  __del__(self, /, *args, **kwargs)
 |  __enter__(self, /, *args, **kwargs)
 |  ...
 |  backup(self, target, /, *, pages=-1, progress=None, ...)
 |  blobopen(self, table, column, rowid, /, *, readonly=False, ...)
 |  ... (continues for 200+ more lines)
```

`agent_help(sqlite3.Connection)` produces a scannable summary instead — see Example 1 below. Notes from `__agent_notes__()` accumulate across inheritance. Class docs travel with the code in commits, reviews, and refactors. Drift gets caught in code review, not weeks later in a sidecar file.

The examples below demonstrate four ways to use `agent_help()`.

## Example 1: Wrapping an existing class

Add agent-readable docs to any class, including ones you don't own. Full example: [`examples/sqlite_connection.py`](examples/sqlite_connection.py).

```python
import sqlite3
from agent_readable import AgentReadableMixin, agent_help


class Connection(sqlite3.Connection, AgentReadableMixin):
    """An agent-friendly wrapper around sqlite3.Connection."""

    @classmethod
    def __agent_notes__(cls) -> str:
        return (
            "Additional notes about using Connection here. "
            "For example, common pitfalls, best practices, etc."
        )
```

Override `__agent_notes__()` to add extra guidance, or leave it out for auto-generated docs only.

`agent_help(Connection)` output:

```
# Connection

## Purpose

An agent-friendly wrapper around sqlite3.Connection.

## Public API

- `backup(/, target, *, pages=-1, progress=None, name='main', sleep=0.25)` method: Makes a backup of the database.
- ...
- `close(/)` method: Close the database connection.
- `commit(/)` method: Commit any pending transaction to the database.
- ...
- `execute(...)` method: Executes an SQL statement.
- ...
- `rollback(/)` method: Roll back to the start of any pending transaction.
- ...

## Agent usage rules

- Prefer the public API listed above.
- Do not use private methods or attributes starting with `_`.
- Do not invent unsupported behavior.
- If usage is ambiguous, prefer the simplest documented usage pattern.

## Notes from class Connection

Additional notes about using Connection here. For example, common pitfalls, best practices, etc.
```

## Example 2: Inheritance with accumulated notes

Override `__agent_notes__()` to add usage guidance. Notes accumulate through inheritance automatically. Full example: [`examples/temperature.py`](examples/temperature.py).

```python
from agent_readable import AgentReadableMixin, agent_help


class Sensor(AgentReadableMixin):
    """Reads a value from a hardware sensor."""

    def __init__(self, pin: int, *, unit: str = "C"): ...

    def read(self) -> float:
        """Read the current sensor value."""

    def calibrate(self, offset: float):
        """Apply a calibration offset."""

    @classmethod
    def __agent_notes__(cls) -> str:
        return """
## Do

- Call `calibrate()` once during setup, before `read()`.
- Handle negative values — sensors may report below zero.

## Do not

- Do not call `read()` before `calibrate()` on first use.
"""


class CalibratedSensor(Sensor):
    """A sensor with factory calibration applied."""

    def reset(self):
        """Reset to factory calibration."""

    @classmethod
    def __agent_notes__(cls) -> str:
        return """
## Do

- Call `reset()` if readings drift unexpectedly.

## Do not

- Do not call `calibrate()` — use `reset()` instead. Factory calibration
  is pre-applied and `calibrate()` would double-adjust.
"""
```

`agent_help(CalibratedSensor)` output — includes inherited notes with conflict resolution:

````
# CalibratedSensor

## Constructor

```python
CalibratedSensor(pin: int, *, unit: str = 'C')
```

## Purpose

A sensor with factory calibration applied.

## Public API

- `calibrate(offset: float)` method: Apply a calibration offset.
- `read() -> float` method: Read the current sensor value.
- `reset()` method: Reset to factory calibration.

## Agent usage rules

- Prefer the public API listed above.
- Do not use private methods or attributes starting with `_`.
- Do not invent unsupported behavior.
- If usage is ambiguous, prefer the simplest documented usage pattern.

## Notes from class Sensor

## Do

- Call `calibrate()` once during setup, before `read()`.
- Handle negative values — sensors may report below zero.

## Do not

- Do not call `read()` before `calibrate()` on first use.

## Notes from class CalibratedSensor (inherits Sensor; if notes conflict, these take precedence)

## Do

- Call `reset()` if readings drift unexpectedly.

## Do not

- Do not call `calibrate()` — use `reset()` instead. Factory calibration
  is pre-applied and `calibrate()` would double-adjust.
````

The child class's notes explicitly state they take precedence over the parent's — so the agent knows `reset()` replaces `calibrate()` for `CalibratedSensor`.

## Example 3: Duck-typed (no mixin needed)

Any class that defines a `__agent_help__()` classmethod works — no inheritance required. Full example: [`examples/duck_type.py`](examples/duck_type.py).

```python
from agent_readable import agent_help


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_tokens: int, refill_rate: float): ...

    def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens. Returns False if rate-limited."""

    def wait(self, tokens: int = 1) -> None:
        """Block until tokens are available."""

    @classmethod
    def __agent_help__(cls) -> str:
        return (
            "# RateLimiter\n"
            "\n"
            "## Constructor\n"
            "\n"
            "```python\n"
            "RateLimiter(max_tokens: int, refill_rate: float)\n"
            "```\n"
            "\n"
            "## Do\n"
            "\n"
            "- Use `acquire()` for non-blocking checks.\n"
            "- Use `wait()` when you must proceed regardless of rate.\n"
            "- Set `refill_rate` to tokens/second.\n"
            "\n"
            "## Do not\n"
            "\n"
            "- Do not call `acquire()` in a tight loop without sleeping.\n"
            "- Do not assume `acquire()` always returns True.\n"
        )


print(agent_help(RateLimiter))
```

## Example 4: Any class — no setup required

Even without the mixin or duck-typing, `agent_help()` still generates compact, structured Markdown from introspection. If the class (or any class in its MRO) defines `__agent_notes__()`, those notes are auto-appended too — no mixin required. The output is still more agent-friendly than `help()`.
Full example: [`examples/any_class.py`](examples/any_class.py).

```python
import logging
from agent_readable import agent_help

print(agent_help(logging.Logger))
```

`help(logging.Logger)` produces **217 lines** of output. `agent_help(logging.Logger)` produces a compact, scannable summary:

````
# Logger

## Constructor

```python
Logger(name, level=0)
```

## Purpose

Instances of the Logger class represent a single logging channel. A
"logging channel" indicates an area of an application.

...

## Public API

- `addFilter(filter)` method: Add the specified filter to this handler.
- `addHandler(hdlr)` method: Add the specified handler to this logger.
- ...
- `debug(msg, *args, **kwargs)` method: Log 'msg % args' with severity 'DEBUG'.
- `error(msg, *args, **kwargs)` method: Log 'msg % args' with severity 'ERROR'.
- ...
- `info(msg, *args, **kwargs)` method: Log 'msg % args' with severity 'INFO'.
- ...
- `setLevel(level)` method: Set the logging level of this logger.  level must be an int or a str.
- ...
- `warning(msg, *args, **kwargs)` method: Log 'msg % args' with severity 'WARNING'.
````

No mixin, no duck-typing — just pass any class to `agent_help()`.

## Example 5: Modules, functions, and methods

`agent_help()` also works on modules — it generates a summary with the module docstring, public functions, and classes. Full example: [`examples/modules_and_functions.py`](examples/modules_and_functions.py).

```python
import sys
from agent_readable import agent_help

print(agent_help(sys.modules[__name__]))
```

Output:

````python
# __main__

## Purpose

Example: Using agent_help() on modules.

Demonstrates both shapes of module support:
  1. A custom module (this file itself).
  2. A stdlib module (pathlib).

Run this file to see both outputs:
    python examples/modules_and_functions.py

## Public API

- `Query` class: Build and execute a query.
- `connect(host: str, port: int = 5432) -> str` function: Connect to a database server.
- `disconnect()` function: Close the connection.

## Agent usage rules

- Prefer the public API listed above.
- Do not use private names starting with `_`.
- Do not invent unsupported behavior.
- If usage is ambiguous, prefer the simplest documented usage pattern.
````

You can also pass any stdlib or third-party module — same `modules_and_functions.py` shows it.

```python
import pathlib
from agent_readable import agent_help

print(agent_help(pathlib))
```

Output:

````python
# pathlib

## Purpose

Object-oriented filesystem paths.

This module provides classes to represent abstract paths and concrete
paths with operations that have semantics appropriate for different
operating systems.

## Public API

- `DirEntryInfo` class: Implementation of pathlib.types.PathInfo that provides status information by querying a wrapped os.DirEntry object. Don't try to construct it yourself.
- `Path` class: PurePath subclass that can make system calls.
- `PathInfo` class: Implementation of pathlib.types.PathInfo that provides status information for POSIX paths. Don't try to construct it yourself.
- `PosixPath` class: Path subclass for non-Windows systems.
- `PurePath` class: Base class for manipulating paths without I/O.
- `PurePosixPath` class: PurePath subclass for non-Windows systems.
- `PureWindowsPath` class: PurePath subclass for Windows systems.
- `UnsupportedOperation` class: An exception that is raised when an unsupported operation is attempted.
- `WindowsPath` class: Path subclass for Windows systems.
- `copy_info(info, target, follow_symlinks=True)` function: Copy metadata from the given PathInfo to the given local path.
- `copyfileobj(source_f, target_f)` function: Copy data from file-like object source_f to file-like object target_f.
- `ensure_different_files(source, target)` function: Raise OSError(EINVAL) if both paths refer to the same file.
- `ensure_distinct_paths(source, target)` function: Raise OSError(EINVAL) if the other path is within this path.
- `magic_open(path, mode='r', buffering=-1, encoding=None, errors=None, newline=None)` function: Open the file pointed to by this path and return a file object, as the built-in open() function does.

## Agent usage rules

- Prefer the public API listed above.
- Do not use private names starting with `_`.
- Do not invent unsupported behavior.
- If usage is ambiguous, prefer the simplest documented usage pattern.
````

Modules support less customization than classes — there is no mixin inheritance or `__agent_notes__()`. You can override the auto-generated output entirely by setting a module-level `__agent_help__` attribute (callable or string), but this is discouraged since it replaces the auto-generated summary — signatures, purpose, and public API listing are all lost. Prefer clear docstrings on the module and its functions/classes instead.

You can also pass a function or method directly — `agent_help()` renders the signature, full docstring, and usage rules. The output is close to `help()` for a single callable; the bigger wins are still on classes and modules.

```python
import pathlib
from agent_readable import agent_help

print(agent_help(pathlib.Path.read_text))
```

```python
import sys

# Discouraged — replaces everything, including auto-generated docs.
sys.modules[__name__].__agent_help__ = "Custom module help."
```

## CLI

```bash
# Any stdlib class
python -m agent_readable sqlite3:Connection

# A class in your own package
python -m agent_readable my_package.temperature:CalibratedSensor

# The library itself — self-documenting
python -m agent_readable agent_readable:AgentReadableMixin

# Any module
python -m agent_readable pathlib

# A function or method
python -m agent_readable json:dumps
python -m agent_readable pathlib:Path.read_text
```

Outputs agent-oriented documentation for the given class, module, function, or method to stdout.

## FAQ

### How does my agent know to call `agent_help()` instead of `help()`?

Today, you tell it. Either:

- Paste [`AGENT-PROMPT.md`](AGENT-PROMPT.md) into your conversation, or
- Add it permanently to your repo's `AGENTS.md` / `CLAUDE.md` / `.cursor/rules` / equivalent instruction file.

"You tell it" is the hard part of any new agent protocol. An MCP server (so MCP-aware clients auto-discover the tool) is on the roadmap.

### How is this different from `AGENTS.md` / `llms.txt` / Cursor rules?

Different granularity, different drift profile.

- `AGENTS.md` / `llms.txt` / `.cursor/rules` are **project-level**: one file per repo. Good for *"use pnpm,"* *"run lint before commit,"* *"this codebase prefers functional style."*
- `agent-readable` is **class- or module-level**: rules live next to the API they describe. Good for *"`ResourcePool.call()` is for non-streaming requests; for streaming, use `stream()` instead."*

Use both — they don't compete. The advantage of class-level: docs travel with the code. When someone refactors `ResourcePool` into two classes, the rules move with them in the same PR; they don't sit stale in a sidecar file.

### Why not just write better docstrings?

Docstrings answer *what does this do?* They aren't designed for *when may I call this?* or *what's the wrong way to use this?* Mixing both into the docstring makes the API summary noisier without helping agents find the rules. `__agent_notes__()` is for the second category, and it accumulates across the MRO automatically — class docstrings don't compose like that.

### Does this work for libraries I don't own?

Yes. Two ways:

- Subclass + `AgentReadableMixin` (Example 1).
- Monkey-patch: `ThirdPartyClass.__agent_notes__ = classmethod(lambda cls: "...")`. `agent_help()` collects notes from the entire MRO; the mixin is not required.

### Does it work without my class doing anything?

Yes — `agent_help()` falls back to introspection (Example 4). You get a structured summary of every plain class, mixin or not. Notes are added on top *if* the class defines them; otherwise the auto-doc is what you see.

## Keeping agent docs up to date

Agent docs can go stale when classes change — new methods, changed behavior, removed APIs. Copy [`AGENT-PROMPT.md`](AGENT-PROMPT.md) into your coding agent's conversation, or permanently add it to your repo's `AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, `.trae/rules`, `.github/copilot-instructions.md`, or equivalent instruction file. It tells your coding agent to run `agent_help()` before modifying a class, prefer docstrings over `__agent_notes__()`, and verify that docs stay accurate after changes.

## The `__agent_help__` protocol

`__agent_help__()` is a dunder protocol, similar in spirit to ecosystem protocols such as:

- `__str__` (str) — string representation
- `__rich_repr__` (Rich) — custom console representation
- `__html__` (Django, Jinja2) — HTML rendering
- `__array__` (NumPy) — array conversion
- `__fspath__` (os.fspath) — filesystem path conversion

Classes that define a `@classmethod` named `__agent_help__` returning a `str` are considered agent-readable. Modules can define a top-level `__agent_help__` attribute (callable or string). Call the top-level `agent_help(obj)` function to get the docs — just like `str()` calls `__str__()`. The `AgentReadable` `typing.Protocol` and `AgentReadableMixin` are provided for convenience and type-checking, but neither is required.

### `__agent_help__` vs `__agent_notes__`

The two dunders intentionally encode different composition rules:

| Aspect          | `__agent_help__()`                              | `__agent_notes__()`                                                         |
| --------------- | ----------------------------------------------- | --------------------------------------------------------------------------- |
| Semantics       | **Replacement** — returned string IS the output | **Additive** — appended to auto-generated docs                              |
| Composition     | Single class wins (the one closest in MRO)      | Accumulated across the MRO; leaf class wins on conflict (header marks this) |
| When to use     | Total control over the rendered text            | "Auto-doc + my extra do/don't rules"                                        |
| Skipped when    | (always called if defined)                      | Skipped when a duck-typed `__agent_help__` is present (it owns the output)  |
| Mixin required? | No — duck-typed classmethod is enough           | No — defining `__agent_notes__` on any class is enough                      |

## Class docstring hints

For classes that inherit `AgentReadableMixin`, add a short hint in the class docstring:

```python
class ResourcePool(AgentReadableMixin):
    """
    Rotates interchangeable resources such as API keys.

    Agent usage:
        Run ``agent_help(ResourcePool)`` before using this class in generated code.
    """
```

This way, even agents that only see the source or call `help()` are reminded to check `agent_help()`.

## API reference

### `AgentReadable`

A `typing.Protocol` (runtime-checkable) that requires `__agent_help__() -> str`.

### `AgentReadableMixin`

A mixin class for *classes* providing a default `__agent_help__()` implementation that generates structured Markdown from introspection. The mixin is convenience — defining `__agent_notes__()` directly on any class (no inheritance) also works; notes are collected automatically regardless. The mixin does not apply to modules; modules are supported directly by `agent_help()`.

If a class inherits from `AgentReadableMixin`, coding agents should call `agent_help(TheClass)` before generating code that uses it.

### `agent_help(obj)`

Returns a string of agent-oriented documentation for a class, instance, or module.

- For classes and instances: if `__agent_help__()` is defined (via mixin or duck-typing), it is called and its return value is used verbatim — duck-typed implementations are responsible for their own formatting and notes are NOT auto-appended. Otherwise, auto-generated docs are produced from introspection, with `__agent_notes__()` from every class in the MRO appended automatically. If `__agent_help__()` raises, falls back to the auto-generated path (which does include notes).
- For modules: if the module defines a `__agent_help__` attribute (callable or string), it is used. Otherwise, auto-generated docs are produced from the module docstring and its public functions and classes.

## License

MIT
