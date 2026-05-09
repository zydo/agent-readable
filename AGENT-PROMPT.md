# Coding Agent Instructions — agent-readable

This repository uses `agent-readable`. Install if needed: `pip install agent-readable`

## Before using or modifying a class or module

Do not guess. Run this first:

```python
from agent_readable import agent_help

print(agent_help(ClassName))
# or: python -m agent_readable package.module:ClassName

# or
print(agent_help(package.module))
# or: python -m agent_readable package.module
```

Treat the output as the canonical usage guide. Follow do/don't rules, anti-patterns, and lifecycle constraints exactly. Do not invent behavior that contradicts it.

After modifying a class, prefer docstrings first — only update `__agent_notes__()` for corner cases docstrings cannot express. Verify `agent_help(ClassName)` is still accurate.

## Making a class agent-readable

**New class** — inherit `AgentReadableMixin`:

```python
from agent_readable import AgentReadableMixin


class ResourcePool(AgentReadableMixin):
    """
    Rotates interchangeable resources such as API keys.

    Agent usage:
        Run ``agent_help(ResourcePool)`` before using this class in generated code.
    """

    def __init__(self, resources, *, cooldown: float = 60): ...

    def call(self, fn):
        """Call fn(resource) with automatic rotation and retry."""

    @classmethod
    def __agent_notes__(cls) -> str:
        return """
## Do

- Use `call()` for normal non-streaming requests.

## Do not

- Do not use for streaming requests.
"""
```

**Wrapping an existing class** — just mix in:

```python
class Connection(sqlite3.Connection, AgentReadableMixin):
    """An agent-friendly wrapper around sqlite3.Connection."""
```

Guidelines:

- Class docstring → "Purpose" section. Method docstrings → "Public API" summaries.
- Override `__agent_notes__()` only for corner cases and anti-patterns. The mixin is not required for notes — Defining `__agent_notes__()` on any class (or monkey-patching it onto a third-party class) is enough; `agent_help()` collects it from the MRO automatically.
- Add an "Agent usage" hint in the docstring — agents see it even via `help()`.
- Simple data-only classes do not need agent docs.

## Making a module agent-readable

Modules are auto-documented — `agent_help()` generates docs from the module docstring and public members.

**Do not override `__agent_help__` on a module unless absolutely necessary.** Unlike classes (which have `__agent_notes__()` to append guidance), overriding `__agent_help__` on a module replaces the auto-generated summary entirely — you lose signatures, purpose, and public API listing. Prefer writing clear docstrings on the module and its functions/classes instead.
