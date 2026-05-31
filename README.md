# agent-readable

Stop coding agents from hallucinating Python APIs. `agent_help(target)` reads the live public-API surface off any class, module, function, or method — no author opt-in needed — and optionally returns class-level usage rules (lifecycle order, pre-conditions, anti-patterns) when the library ships them.

<!-- markdownlint-disable MD033 -->
<p align="center">
  <strong><code>logging.Logger</code> compared with <code>agent_help()</code> and <code>help()</code></strong><br>
  <img src="docs/agent_help_vs_help.gif" alt="agent_help vs help">
</p>
<!-- markdownlint-enable MD033 -->

## Problem

AI coding agents recognize established libraries from their training data, but they hallucinate when APIs change, when libraries are new, or when correct usage depends on rules that aren't visible from the API surface — pre-conditions, lifecycle order, anti-patterns, *"use `call()` for non-streaming, `stream()` for streaming."*

Today there's nowhere to put those rules where an agent will reliably find them. Docstrings document the API surface, not behavioral rules. `AGENTS.md` and `llms.txt` work at project granularity, drift fast, and don't travel with refactors. `help()` only describes interfaces — and mixes inherited dunders and MRO detail in with the methods you actually want to use.

`agent-readable` has two halves, and the lighter one stands alone. The **consume side** is one function — `agent_help(target)` — that works on every Python library today, annotated or not. It introspects the live, installed class/module/function and returns a curated public-API list with current signatures, no inherited-dunder or MRO noise to wade through. That alone closes the *what exists* hallucination — agents stop inventing methods that aren't there and stop calling real ones with stale signatures. The **author side** adds two dunders: `__agent_help__` for full custom output and `__agent_notes__` for additive behavioral rules that accumulate across inheritance. When a library opts in, those rules show up next to the public-API list in the same `agent_help()` output — so the rules travel with refactors instead of rotting in a sidecar file.

## Installation

```bash
pip install agent-readable
```

Requires Python 3.10+. No runtime dependencies.

## Quickstart

`agent_help()` works on **any Python class, module, function, or method — no opt-in required**. Point it at a stdlib class:

```python
from agent_readable import agent_help
import logging

print(agent_help(logging.Logger))
```

Output (excerpted):

````
# Logger

## Constructor

```python
Logger(name, level=0)
```

## Purpose

Instances of the Logger class represent a single logging channel. ...

## Public API

- `addHandler(hdlr)` method: Add the specified handler to this logger.
- `debug(msg, *args, **kwargs)` method: Log 'msg % args' with severity 'DEBUG'.
- `info(msg, *args, **kwargs)` method: Log 'msg % args' with severity 'INFO'.
- `setLevel(level)` method: Set the logging level of this logger.
- `warning(msg, *args, **kwargs)` method: Log 'msg % args' with severity 'WARNING'.
- ...
````

The `## Public API` list comes from **runtime introspection of the live, installed version** — current signatures, no inherited-dunder noise, no stale training-data guesses. Substitute any class, module, function, or method (yours, a third party's, or a stdlib one); zero setup on the target side.

### Library authors: ship usage rules next to the code (optional)

When you own the class, you can also ship class-level usage rules — lifecycle order, pre-conditions, anti-patterns — that `agent_help()` returns alongside the auto-generated public-API list. Define a `__agent_notes__()` classmethod (no mixin, no inheritance required); notes accumulate across the MRO so subclasses don't lose parent rules:

```python
from agent_readable import agent_help


class Sensor:
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

`agent_help(Sensor)` now returns the same auto-generated public-API list, plus a `## Notes from class Sensor` section carrying the rules above. Full output and inheritance-with-notes behavior in [Example 2](#example-2-inheritance-with-accumulated-notes) below.

## Why it matters

`agent_help()` covers two failure modes agents hit on real APIs:

1. **What exists.** The `## Public API` section is a curated list of current signatures pulled from runtime introspection — no hallucinated methods, no stale signatures from training data, no private members leaking in. If the agent reads this list first, it stops inventing methods that don't exist and stops calling real ones with the wrong arguments.
2. **How to use it correctly.** Lifecycle order, pre-conditions, anti-patterns, *"this method is for X, that one for Y."* These don't fit in any single method's docstring and don't belong in a project-level `AGENTS.md` (which describes whole repos). They're class-level, and they need to travel with refactors. `__agent_notes__()` gives them a home next to the code.

A concrete contrast:

```
# help(sqlite3.Connection) — every inherited dunder, in source order:
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
 |  ... (no curation, no behavioral rules, no signal that backup() needs an
 |        open target connection before being called)
```

`agent_help(sqlite3.Connection)` produces a curated public-API list with current signatures and any class-level rules attached — see Example 1 below. Notes from `__agent_notes__()` accumulate across inheritance. Class docs travel with the code in commits, reviews, and refactors. Drift gets caught in code review, not weeks later in a sidecar file.

The examples below demonstrate five ways to use `agent_help()`, three with library-author opt-in (Examples 1–3) and two on plain classes/modules with no setup (Examples 4–5).

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

- `backup(target, *, pages=-1, progress=None, name='main', sleep=0.25)` method: Makes a backup of the database.
- ...
- `close()` method: Close the database connection.
- `commit()` method: Commit any pending transaction to the database.
- ...
- `execute(...)` method: Executes an SQL statement.
- ...
- `rollback()` method: Roll back to the start of any pending transaction.
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

Even without the mixin or duck-typing, `agent_help()` still generates structured Markdown from introspection — a curated public-API list with current signatures, free of inherited dunders and MRO clutter. If the class (or any class in its MRO) defines `__agent_notes__()`, those notes are auto-appended too — no mixin required.
Full example: [`examples/any_class.py`](examples/any_class.py).

```python
import logging
from agent_readable import agent_help

print(agent_help(logging.Logger))
```

Compare what `agent_help(logging.Logger)` returns to what `help(logging.Logger)` does — the former lists only the public methods you'd actually call, with their current signatures and docstring summaries:

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

Example: Using agent_help() on modules, functions, and methods.

Demonstrates non-class targets:
  1. A custom module (this file itself).
  2. A stdlib module (pathlib).
  3. A function (connect, defined below).
  4. A method (Query.execute, defined below).

Run this file to see all outputs:
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

- `Path` class: PurePath subclass that can make system calls.
- `PosixPath` class: Path subclass for non-Windows systems.
- `PurePath` class: Base class for manipulating paths without I/O.
- `PurePosixPath` class: PurePath subclass for non-Windows systems.
- `PureWindowsPath` class: PurePath subclass for Windows systems.
- `UnsupportedOperation` class: An exception that is raised when an unsupported operation is attempted.
- `WindowsPath` class: Path subclass for Windows systems.

## Agent usage rules

- Prefer the public API listed above.
- Do not use private names starting with `_`.
- Do not invent unsupported behavior.
- If usage is ambiguous, prefer the simplest documented usage pattern.
````

Modules support less customization than classes — there is no mixin inheritance or `__agent_notes__()`. You can override the auto-generated output entirely by setting a module-level `__agent_help__` attribute (callable or string), but this is discouraged since it replaces the auto-generated summary — signatures, purpose, and public API listing are all lost. Prefer clear docstrings on the module and its functions/classes instead. If the module defines `__all__`, that list is honored as the authoritative public API — including symbols re-exported from other modules.

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

Install the agent **skill** that ships in this repo at [`skills/agent-readable/`](skills/agent-readable/). It follows the [Agent Skills open standard](https://agentskills.io) — adopted by Claude Code, Codex CLI (OpenAI), Gemini CLI (Google), GitHub Copilot, JetBrains Junie, Goose, OpenCode, and 40+ other tools — so dropping the folder into your agent's skills directory (`~/.claude/skills/`, `~/.codex/skills/`, your editor's equivalent) is enough for the agent to auto-discover it. (Cursor is among the adopters too, but its skill integration is manual — you invoke the skill explicitly there rather than relying on description-match auto-activation.) The skill teaches the agent to install `agent-readable`, call `agent_help(target)` before writing code against a class, module, function, or method, and add `__agent_notes__()` (or improve docstrings) when authoring new public APIs.

The folder lives next to the source code for now; a hub-published version (so you can install it through your harness's marketplace) is the next step on the roadmap.

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

### Is `agent_help()` the strongest fix for API hallucination?

No, and worth being upfront about it. The strongest known mitigation is **constrained decoding** at the harness or decoder layer — masking illegal API tokens before generation, so the model can't produce a nonexistent method at all. `agent_help()` takes the lighter, library-side path: an authoritative usage guide injected into the agent's context, leaving the agent to read and follow it. Recent research on Python API misuse shows the in-context route leaves a meaningful slice of hallucinations on the table even when verified API references are provided. The two approaches compose. Pick `agent_help()` when you have leverage on the library side and want a fix that works on every agent and every library today, without harness changes. Reach for constrained decoding when you control the harness or the decoder. Either way, verify generated code before merging.

## Keeping agent docs up to date

Agent docs can go stale when classes change — new methods, changed behavior, removed APIs. Install the skill at [`skills/agent-readable/`](skills/agent-readable/) into your agent (see the FAQ above for the install). It teaches your agent to run `agent_help()` before modifying a class, prefer docstrings over `__agent_notes__()`, and verify that the output stays accurate after changes.

## The `__agent_help__` protocol

`__agent_help__()` is a dunder protocol for tool-specific documentation, similar in spirit to:

- `__doc__` (Python `help()`, Sphinx, IDEs, REPLs) — the canonical "this is my human-readable documentation" slot, read by inspection tools and surfaced through `help()`
- `__rich_repr__` (Rich) — Rich-specific console representation read only when Rich renders the object
- `__html__` (Django, Jinja2, MarkupSafe) — HTML-renderer-specific representation read only when those template engines render the object

Unlike `__str__` or `__fspath__`, these dunders don't change Python runtime behavior — they're metadata slots a specific tool reads when it wants a representation. `__agent_help__` follows the same pattern for the agent-docs case.

Classes that define a `@classmethod` named `__agent_help__` returning a `str` are considered agent-readable. Modules can define a top-level `__agent_help__` attribute (callable or string). Call the top-level `agent_help(obj)` function to get the docs — just like `str()` calls `__str__()`. The `AgentReadable` `typing.Protocol` and `AgentReadableMixin` are provided for convenience and type-checking, but neither is required.

### `__agent_help__` vs `__agent_notes__`

The two dunders intentionally encode different composition rules:

| Aspect          | `__agent_help__()`                              | `__agent_notes__()`                                                                                  |
| --------------- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Semantics       | **Replacement** — returned string IS the output | **Additive** — appended to auto-generated docs                                                       |
| Composition     | Single class wins (the one closest in MRO)      | Accumulated across the MRO; leaf class wins on conflict (header marks this)                          |
| When to use     | Total control over the rendered text            | "Auto-doc + my extra do/don't rules"                                                                 |
| Skipped when    | (always called if defined)                      | Silently dropped (with `UserWarning`) when a custom `__agent_help__` is present (it owns the output) |
| Mixin required? | No — duck-typed classmethod is enough           | No — defining `__agent_notes__` on any class is enough                                               |

**Heads up on the both-defined case.** When a class defines both `__agent_help__()` and `__agent_notes__()`, the notes are silently dropped — `__agent_help__()` owns the output, and the auto-doc + notes path never runs. A `UserWarning` is emitted, but warnings are easy to miss in agent shells, CI logs, and notebooks — **treat "both defined" as a hard review error** rather than something the warning will reliably catch. Fix it by folding the notes into `__agent_help__()`, or by dropping the custom `__agent_help__()` and letting the auto-doc + notes path run.

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

Returns a string of agent-oriented documentation for a class, instance, module, function, or method.

- For classes and instances: if `__agent_help__()` is defined (via mixin or duck-typing), it is called and its return value is used verbatim — duck-typed implementations are responsible for their own formatting and notes are NOT auto-appended. If such a class also defines `__agent_notes__()`, a `UserWarning` is emitted because those notes are silently dropped (fold them into `__agent_help__()`, or drop the custom `__agent_help__()` to use the auto-doc path). Otherwise, auto-generated docs are produced from introspection, with `__agent_notes__()` from every class in the MRO appended automatically. If `__agent_help__()` raises, falls back to the auto-generated path (which does include notes).
- For modules: if the module defines a `__agent_help__` attribute (callable or string), it is used. Otherwise, auto-generated docs are produced from the module docstring and its public functions and classes. When the module defines `__all__`, that list is the authoritative public API (so re-exported symbols are included); otherwise public members are discovered by introspection, skipping private names and anything defined outside the module.
- For functions and methods (anything `inspect.isroutine` accepts): if the routine defines an `__agent_help__` attribute (callable or string), it is used. Otherwise, auto-generated docs render the signature, full docstring, and usage rules. A bound method's signature drops `self` and a classmethod's drops `cls`. If a callable `__agent_help__` raises, falls back to the auto-generated path.

## License

MIT
