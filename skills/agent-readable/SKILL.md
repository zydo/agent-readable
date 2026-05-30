***

name: agent-readable
description: Use agent\_readable to get authoritative usage guidance for Python classes, modules, functions, and methods before writing code against them, and to make new Python APIs agent-readable. Activate when writing or modifying Python code that calls into a class, module, function, or method from any library, OR when adding/changing a public Python API. Covers calling `agent_help(obj)` for structured docs + behavioral rules, and authoring docstrings + `__agent_notes__()` so usage rules travel with the code.
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# agent-readable

`agent-readable` is a tiny Python library (`pip install agent-readable`, zero
runtime deps, Python 3.10+) that gives any class, module, function, or method a
structured, agent-oriented "usage guide" — the canonical answer to *how do I
correctly use this?* — produced by one call: `agent_help(obj)`.

This skill teaches you two jobs:

1. **Consume** — before writing Python code that uses a class, module, function,
   or method, call `agent_help(target)` and use the output as the source of truth.
2. **Author** — when adding or modifying a public Python API, make it
   agent-readable so future agents get correct usage on the first try.

## When to activate this skill

* The user asks you to write, modify, or refactor Python code that calls into a
  class, module, function, or method (from a third-party library or from this
  project).
* The user asks you to add or change a public Python class, module, or function
  (especially one other code or other agents will use).
* The user mentions `agent_help`, `__agent_notes__`, `AgentReadableMixin`, the
  `AgentReadable` protocol, or the `agent-readable` library by name.

## Install

```bash
pip install agent-readable      # or: uv add agent-readable
```

Python 3.10+. No runtime dependencies. The library exposes one top-level function
(`agent_help`), one protocol (`AgentReadable`), and one optional mixin
(`AgentReadableMixin`).

## Job 1 — Consume: call `agent_help(target)` first

**Before writing code against a Python target, always call `agent_help(target)`.**
Even if the target does *not* opt in: `agent_help()` falls back to introspection
and returns a structured, current-signature public-API listing — strictly better
than guessing from training data.

```python
from agent_readable import agent_help

print(agent_help(SomeClass))      # class — constructor, public API, notes
print(agent_help(some_instance))  # instance — dispatches to its class
print(agent_help(some_module))    # module — docstring + public functions/classes
print(agent_help(some_func))      # function or method — signature + docstring
```

From a coding-agent shell:

```bash
python -c "from agent_readable import agent_help; import target_lib; print(agent_help(target_lib.SomeClass))"
```

### How to read the output

`agent_help()` returns Markdown with these sections (a subset appears depending
on the target):

* `# <name>` and `## Purpose` — the docstring summary.
* `## Constructor` / `## Signature` — the **current** signature (the source of
  truth, beats anything in training data).
* `## Public API` — every public member with current signatures. Treat this as
  the authoritative list; do not call methods not listed here.
* `## Agent usage rules` — generic rules (prefer the public API, no private
  names, etc.).
* `## Notes from class <X>` — **load-bearing** class-specific behavioral rules:
  lifecycle order, pre-conditions, anti-patterns. If a note says *"call
  `calibrate()` once before `read()`"*, honor it. If multiple `Notes from class`
  sections appear, the leaf class wins on conflict (the header marks this).

If you are unsure how to use a target, run `agent_help()` again — it is cheap and
the docstrings/notes are the canonical source.

## Job 2 — Author: make new Python APIs agent-readable

Default to **better docstrings** first; only reach for the dunders when
docstrings cannot compose the rule.

### 2a. Docstrings are the primary surface

`agent_help()` already extracts docstrings: the class docstring becomes
`## Purpose`, and each method's first paragraph becomes its `## Public API`
summary. So the bar for a good docstring here is the same as for any
well-documented library: concise summary line, then params/returns/raises if
nontrivial. Keep per-method behavior in the method's docstring — that is where it
stays attached through refactors.

### 2b. Add `__agent_notes__()` only for cross-method behavioral rules

When a rule does not fit in any single method's docstring — lifecycle order
across methods, pre-conditions, anti-patterns ("use `call()` for non-streaming,
`stream()` for streaming"), do/don't lists — put it on the **class** as a
`classmethod` named `__agent_notes__()`:

```python
class Sensor:
    """Reads a value from a hardware sensor."""

    def __init__(self, pin: int, *, unit: str = "C"): ...
    def calibrate(self, offset: float): ...
    def read(self) -> float: ...

    @classmethod
    def __agent_notes__(cls) -> str:
        return """
## Do

- Call `calibrate()` once during setup, before `read()`.

## Do not

- Do not call `read()` before `calibrate()` on first use.
"""
```

Facts about `__agent_notes__()` worth knowing:

* **Accumulates across the MRO.** Every class in the inheritance chain that
  defines its own `__agent_notes__()` contributes a section to `agent_help()`'s
  output. The leaf class is marked as taking precedence on conflict.
* **Do not call `super().__agent_notes__()`** — collection is automatic.
* **No mixin required.** Defining `__agent_notes__` on any class is enough.
  Monkey-patching also works for classes you do not own:
  ```python
  ThirdPartyClass.__agent_notes__ = classmethod(lambda cls: "...")
  ```
* **Optional `AgentReadableMixin`.** Inheriting from
  `agent_readable.AgentReadableMixin` is purely a convenience for type-checking
  and IDE hints — `agent_help()` works on plain classes too.

### 2c. Almost never define a custom `__agent_help__()`

`__agent_help__()` **replaces** the entire auto-generated output. Use it only
when you have a hand-formatted help string you genuinely want to ship verbatim.
In every other case, let the auto-doc generate from your class + docstrings +
`__agent_notes__()`.

### 2d. Verify after annotating

After adding or changing notes, run:

```bash
python -c "from agent_readable import agent_help; from your_module import YourClass; print(agent_help(YourClass))"
```

Check that signatures are correct (you may need to fix type hints), notes appear
in MRO order with the leaf class marked precedence-winning, and no private
members leaked into `## Public API`.

## Footguns

* **Do not define both a custom `__agent_help__()` and `__agent_notes__()` on
  the same class.** A custom `__agent_help__()` owns the full output, so the
  notes are silently dropped (a `UserWarning` is emitted). Fix it one of two
  ways: fold the notes into your custom `__agent_help__()`, or remove the
  custom `__agent_help__()` and let the auto-doc + notes path run.
* **Do not put per-method instructions in `__agent_notes__()`.** Single-method
  behavior belongs in that method's docstring, where it stays attached through
  refactors. `__agent_notes__()` is for rules that span methods.
* **Do not mix `agent_help()` with `help()`.** `help()` returns hundreds of
  lines of inherited dunders and MRO detail; `agent_help()` returns a curated,
  structured guide with behavioral rules attached. Use `agent_help()`.

## The one rule

> Before writing or modifying Python code that uses an external class, module,
> function, or method, call `agent_help(target)` and use its output as the
> canonical usage guide.

That call is cheap, runs in any coding-agent shell, and works on any Python
object — annotated or not.
