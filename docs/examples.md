# Examples

These examples demonstrate five ways to use `agent_help()`: three with library-author opt-in and two on plain classes or modules with no setup.

## Example 1: Wrapping an existing class

Add agent-readable docs to any class, including ones you do not own. Full example: [`examples/sqlite_connection.py`](../examples/sqlite_connection.py).

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

`agent_help(Connection)` output excerpt:

```text
# Connection

## Purpose

An agent-friendly wrapper around sqlite3.Connection.

## Public API

- `backup(target, *, pages=-1, progress=None, name='main', sleep=0.25)` method: Makes a backup of the database.
- `close()` method: Close the database connection.
- `commit()` method: Commit any pending transaction to the database.
- `execute(...)` method: Executes an SQL statement.
- `rollback()` method: Roll back to the start of any pending transaction.

## Agent usage rules

- Prefer the public API listed above.
- Do not use private methods or attributes starting with `_`.
- Do not invent unsupported behavior.
- If usage is ambiguous, prefer the simplest documented usage pattern.

## Notes from class Connection

Additional notes about using Connection here. For example, common pitfalls, best practices, etc.
```

## Example 2: Inheritance with accumulated notes

Override `__agent_notes__()` to add usage guidance. Notes accumulate through inheritance automatically. Full example: [`examples/temperature.py`](../examples/temperature.py).

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
- Handle negative values -- sensors may report below zero.

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

- Do not call `calibrate()` -- use `reset()` instead. Factory calibration
  is pre-applied and `calibrate()` would double-adjust.
"""
```

`agent_help(CalibratedSensor)` includes notes from both classes. The child class's notes explicitly state they take precedence over the parent's, so the agent knows `reset()` replaces `calibrate()` for `CalibratedSensor`.

## Example 3: Duck-typed custom output

Any class that defines a `__agent_help__()` classmethod works, with no inheritance required. Full example: [`examples/duck_type.py`](../examples/duck_type.py).

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

Use `__agent_help__()` when the auto-generated base document is not what you want and you prefer to write the base by hand. Use `__agent_notes__()` when the auto-generated API docs are fine and you just want extra rules on top. `__agent_notes__()` sections defined anywhere in the MRO are appended after custom `__agent_help__()` output too, so mixed setups do not lose notes.

## Example 4: Any class, no setup required

Even without the mixin or duck typing, `agent_help()` generates structured Markdown from introspection: a curated public API list with current signatures, free of inherited dunders and MRO clutter. Methods, properties, cached properties, public constants (with their values), and enum members are all listed. Full example: [`examples/any_class.py`](../examples/any_class.py).

```python
import logging
from agent_readable import agent_help

print(agent_help(logging.Logger))
```

Output excerpt:

````
# Logger

## Constructor

```python
Logger(name, level=0)
```

## Purpose

Instances of the Logger class represent a single logging channel. A
"logging channel" indicates an area of an application.

## Public API

- `addFilter(filter)` method: Add the specified filter to this handler.
- `addHandler(hdlr)` method: Add the specified handler to this logger.
- `debug(msg, *args, **kwargs)` method: Log 'msg % args' with severity 'DEBUG'.
- `error(msg, *args, **kwargs)` method: Log 'msg % args' with severity 'ERROR'.
- `info(msg, *args, **kwargs)` method: Log 'msg % args' with severity 'INFO'.
- `setLevel(level)` method: Set the logging level of this logger.
- `warning(msg, *args, **kwargs)` method: Log 'msg % args' with severity 'WARNING'.
````

No mixin, no duck typing: just pass any class to `agent_help()`.

## Example 5: Modules, functions, and methods

`agent_help()` also works on modules, functions, and methods. Full example: [`examples/modules_and_functions.py`](../examples/modules_and_functions.py).

```python
import sys
from agent_readable import agent_help

print(agent_help(sys.modules[__name__]))
```

Module output includes the module docstring, public functions, and classes:

````python
# __main__

## Purpose

Example: Using agent_help() on modules, functions, and methods.

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

You can also pass any stdlib or third-party module:

```python
import pathlib
from agent_readable import agent_help

print(agent_help(pathlib))
```

If the module defines `__all__`, that list is honored as the authoritative public API, including symbols re-exported from other modules.

Functions and methods render their signature, full docstring, and usage rules:

```python
import pathlib
from agent_readable import agent_help

print(agent_help(pathlib.Path.read_text))
```

Modules support less customization than classes. You can override generated module output entirely by setting a module-level `__agent_help__` attribute, but this is discouraged because it replaces the auto-generated summary, signatures, purpose, and public API list. Prefer clear module, function, and class docstrings instead.
