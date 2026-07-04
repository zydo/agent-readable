# Getting started

## Installation

```bash
uv add agent-readable
```

Or with pip:

```bash
pip install agent-readable
```

Requires Python 3.10+. No runtime dependencies.

## One-off CLI use

If you only want to print readable documentation for a Python target and do not want to add `agent-readable` to the current environment, run it in a temporary tool environment:

The examples below use `sqlite3:Connection` as the target; replace it with any importable class, module, function, or method.

With `uvx`:

```bash
uvx --from agent-readable python -m agent_readable sqlite3:Connection
```

With `uv tool run`:

```bash
uv tool run --from agent-readable python -m agent_readable sqlite3:Connection
```

With `pipx`:

```bash
pipx run --spec agent-readable python -m agent_readable sqlite3:Connection
```

`uvx` is shorthand for `uv tool run`. These commands are useful for standard-library targets and packages available inside the temporary environment. For your own project classes, run from an environment where that project is importable.

To let your coding agent automatically call `agent_help()` before using an unfamiliar API, install the companion skill:

```bash
npx skills add zydo/skills --skill agent-readable
```

## Quickstart

`agent_help()` works on any Python class, module, function, or method with no opt-in required. Point it at a stdlib class:

```python
from agent_readable import agent_help
import logging

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

Instances of the Logger class represent a single logging channel. ...

## Public API

- `addHandler(hdlr)` method: Add the specified handler to this logger.
- `debug(msg, *args, **kwargs)` method: Log 'msg % args' with severity 'DEBUG'.
- `info(msg, *args, **kwargs)` method: Log 'msg % args' with severity 'INFO'.
- `setLevel(level)` method: Set the logging level of this logger.
- `warning(msg, *args, **kwargs)` method: Log 'msg % args' with severity 'WARNING'.
- ...
````

The `## Public API` list comes from runtime introspection of the live, installed version: current signatures, no inherited-dunder noise, and no stale training-data guesses. Substitute any class, module, function, or method from your code, a third-party package, or the standard library.

## Optional author notes

When you own a class, you can also ship class-level usage rules such as lifecycle order, preconditions, and anti-patterns. Define a `__agent_notes__()` classmethod; notes accumulate across the MRO so subclasses do not lose parent rules.

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

`agent_help(Sensor)` returns the same auto-generated public API list plus a `## Notes from class Sensor` section with those rules.

## CLI

```bash
# Any stdlib class
python -m agent_readable sqlite3:Connection

# A class in your own package
python -m agent_readable my_package.temperature:CalibratedSensor

# The library itself
python -m agent_readable agent_readable:AgentReadableMixin

# Any module
python -m agent_readable pathlib

# A function or method
python -m agent_readable json:dumps
python -m agent_readable pathlib:Path.read_text
```

The CLI writes agent-oriented documentation for the target to stdout.

## Other Languages

- TypeScript: [`agent-readable-ts`](https://github.com/zydo/agent-readable-ts)
