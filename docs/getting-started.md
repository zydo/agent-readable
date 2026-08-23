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

Two parallel series — pick whichever matches your tooling. Each one-off command creates an isolated tool environment on first use, caches it for instant repeat runs, and never touches the current environment. Replace `sqlite3:Connection` with any importable class, module, function, or method.

### uv series

```bash
# One-off — isolated tool environment, cached by uv
uvx agent-readable sqlite3:Connection

# One-off for a third-party package — --with adds it to the environment
uvx --with requests agent-readable requests:Session

# Repeated use — install once, then run the bare command
uv tool install agent-readable
agent-readable sqlite3:Connection
```

### pip series

```bash
# One-off — pipx builds and caches an isolated environment
pipx run --spec agent-readable agent-readable sqlite3:Connection

# Repeated use — install once with pipx (isolated, on PATH)
pipx install agent-readable
agent-readable sqlite3:Connection

# Plain pip — persistent install into any environment you choose
pip install agent-readable
```

To let your coding agent automatically call `agent_help()` before using an unfamiliar API, install the companion skill:

```bash
npx skills add zydo/skills --skill agent-readable
```

## Your own project

The one-off environments above cannot import your own project's code. Run the CLI from an environment where the project is importable:

```bash
uv add --dev agent-readable
uv run agent-readable my_package.temperature:CalibratedSensor
```

Or with pip, install into the project's environment and run the bare command:

```bash
pip install agent-readable
agent-readable my_package.temperature:CalibratedSensor
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

Wherever the package is installed, both `agent-readable` and `python -m agent_readable` work:

```bash
# Any stdlib class
agent-readable sqlite3:Connection

# A class in your own package
agent-readable my_package.temperature:CalibratedSensor

# The library itself
agent-readable agent_readable:AgentReadableMixin

# Any module
agent-readable pathlib

# A function or method
agent-readable json:dumps
agent-readable pathlib:Path.read_text

# Installed version
agent-readable --version
```

The CLI writes agent-oriented documentation for the target to stdout. A target that cannot be imported or resolved prints a one-line error to stderr and exits with status 2.

## Other Languages

- TypeScript: [`agent-readable-ts`](https://github.com/zydo/agent-readable-ts)
