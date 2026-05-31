---
name: agent-readable
description: Use agent_readable to inspect the current runtime API and any author-supplied usage rules for a Python class, module, function, or method before writing code against it — and to make your own public Python APIs agent-readable. Activate when writing, modifying, or refactoring Python that calls into an API you don't already know cold — typically project-local or third-party code that is stateful, version-sensitive, poorly documented, has lifecycle or ordering constraints, or exposes several similar entrypoints that are easy to confuse. Also activate when adding or changing a public Python API meant for reuse, or when the user mentions agent_help, __agent_notes__, AgentReadableMixin, AgentReadable, or the agent-readable library. Skip it for trivial builtins, standard-library usage you already know, routine calls into familiar common libraries (e.g. a basic pandas read or a simple requests GET), and pure algorithmic code with no API-specific behavior.
---

# agent-readable

`agent-readable` is a tiny Python library (`pip install agent-readable`, zero
runtime deps, Python 3.10+). Its one job: `agent_help(obj)` returns a structured,
agent-oriented usage guide for a class, module, function, or method. How much you
get depends on the target — at minimum the **current runtime signature and public
API** (read live, so more reliable than training data); when the author opted in
(docstrings + `__agent_notes__()`), also **behavioral rules** a signature can't
express. Signatures are a fact read off the code; notes are a maintained human
claim. Don't treat the output as a complete behavioral contract unless the author
supplied one.

## Language support

Python 3.10+. Other languages are on the roadmap.

## When to activate

Call `agent_help(target)` before writing code against an API where guessing the
usage could plausibly be wrong — concretely, when:

* The target is **project-local or third-party code you don't already know cold**.
* It's **stateful, version-sensitive, poorly documented, has lifecycle or
  ordering constraints, or exposes several similar entrypoints** that are easy to
  confuse.
* You're **adding or changing a public Python API** meant for reuse by humans or
  agents.
* The user asks about `agent_help`, `__agent_notes__`, `AgentReadableMixin`,
  `AgentReadable`, or the `agent-readable` library.

## When not to activate

Skip it — just write the code — for trivial builtins (`len`, `dict`, …),
standard-library usage you already know, **routine calls into familiar common
libraries** (a basic pandas read, a simple `requests` GET), and pure algorithmic
code with no external or project-specific API. One `agent_help()` call is cheap,
but consulting the skill for every snippet adds noise; reserve it for APIs where
getting usage wrong is plausible.

## Install

```bash
pip install agent-readable      # or: uv add agent-readable
```

Python 3.10+, no runtime deps. Exposes `agent_help`, the `AgentReadable`
protocol, and the optional `AgentReadableMixin`.

## Job 1 — Consume: inspect before you call

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

## Safety: imports, side effects, and environment mismatch

`agent_help()` usually has to **import the target module**, and import-time code
runs — it may open connections, touch files or the network, read env vars, do
heavy init, or rarely something destructive. So:

* Run it only in a **trusted project environment**.
* Don't blindly import untrusted, expensive, destructive, or
  environment-dependent modules just to get help.
* If import is unsafe, impossible, or too expensive, read **source, tests,
  existing docs, and type hints**, or ask the user — don't run arbitrary repo
  code to obtain help when the repo isn't trusted.

**Environment and version.** The output reflects the object **as installed here,
now**. If your code will run elsewhere (prod, CI, the user's runtime), verify the
package version there rather than assuming the inspected API matches; when it
matters, check lockfiles, package metadata, installed versions, or source.

## How to interpret the output

`agent_help()` returns Markdown; read each section with the right trust level:

| Section | Source | How to treat it |
|---|---|---|
| `## Signature` / `## Constructor` | live introspection | **Ground truth** for the current call shape. Prefer over memory. |
| `## Public API` | live introspection (private names filtered) | Authoritative for *which names exist*; does **not** prove a method behaves as named. |
| `## Purpose`, per-method summaries | docstrings | As accurate as the author's docstrings. |
| `## Notes from class <X>` | `__agent_notes__()` | **Behavioral guidance, if supplied and maintained** — a claim, not a guarantee. |

* **Annotated vs. fallback.** With `__agent_notes__()` or custom metadata, treat
  the output as behavioral guidance. Introspection-only output is a *current
  runtime inventory* (signatures, public members, docstrings): better than stale
  training data, but it won't reveal hidden lifecycle constraints, side effects,
  performance traps, async/streaming rules, thread-safety, or invalid parameter
  combinations. For those, read source/tests or ask.
* **Public API.** `## Public API` lists members per the library's filtering plus
  live inspection. Call only what's listed; avoid private names unless the user
  asks or the codebase already relies on them.
* **Conflicts.** If a note contradicts a visible signature, trust the signature.
  Among multiple `## Notes from class` sections, the **leaf class wins** (the
  header marks this).

## Job 2 — Author: make your Python APIs agent-readable

Preference order: **good docstrings → focused `__agent_notes__()` → (rarely) a
custom `__agent_help__()`.**

### Docstrings first

`agent_help()` reads docstrings directly: the class docstring becomes
`## Purpose`, each method's first paragraph its `## Public API` summary. Same bar
as any well-documented library — concise summary line, then params/returns/raises
when nontrivial. Per-method behavior stays in that method's docstring, where it
survives refactors.

### `__agent_notes__()` — cross-method rules only

For rules that span methods, add a `classmethod` on the **class**:

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
- Call `calibrate()` once during setup, before the first `read()`.

## Do not
- Do not call `read()` before `calibrate()` on first use.
"""
```

**Belongs here:** lifecycle/ordering, preconditions, cleanup, sync vs async,
streaming vs non-streaming, retry/backoff/cooldown, do/don't lists. **Doesn't:**
per-method behavior (→ the method's docstring), and duplicated docstring content.

Mechanics: notes **accumulate across the MRO** (leaf wins on conflict); **don't
call `super()`** (collection is automatic); no mixin required
(`AgentReadableMixin` only adds type-checking/IDE hints).

**Monkey-patching** classes you don't own works
(`ThirdPartyClass.__agent_notes__ = classmethod(lambda cls: "...")`), but keep it
to **local adapters, test fixtures, or controlled runtime contexts**. Don't ship
**global** patches against third-party classes in reusable library code unless
you fully control the runtime; document why the patch exists and keep it next to
the integration code.

#### Make notes verifiable

A free-prose note is a docstring in a different place — it rots silently. Anchor
it to something that **fails a test on drift**:

1. **Name real members** (`calibrate()`, not "the setup step"), so renames
   surface via grep and the test below.
2. **Make examples executable** — a doctest, or a snippet in a docstring /
   `examples/` file the note points to.
3. **Ship a contract test:**

   ```python
   import re, doctest
   from your_module import Sensor

   def test_agent_notes_reference_real_members():
       for name in re.findall(r"`(\w+)\(\)`", Sensor.__agent_notes__()):
           assert hasattr(Sensor, name), f"note references missing member: {name}"

   def test_agent_notes_examples_run():
       assert doctest.testmod(m=__import__(Sensor.__module__)).failed == 0
   ```

**Limit:** this catches *name* and *example* drift, not *semantic* drift —
"calibrate before read" can go wrong while every name stays valid. To close that,
assert the behavior itself (e.g. that `read()` fails before `calibrate()`). A
rule worth writing down is usually worth asserting.

### Custom `__agent_help__()` — rarely

It **replaces** the entire auto-generated output. Use only when you have a
hand-formatted string to ship verbatim; otherwise let the auto-doc compose from
class + docstrings + `__agent_notes__()`.

### Verify after annotating

```bash
python -c "from agent_readable import agent_help; from your_module import YourClass; print(agent_help(YourClass))"
```

Check signatures are right (fix type hints if not), notes appear in MRO order
with the leaf winning, and no private members leaked into `## Public API`. Then
run the contract test.

## Footguns

* **Never define both a custom `__agent_help__()` and `__agent_notes__()` on one
  class.** The custom `__agent_help__()` owns the output, so the notes are
  dropped. The library emits a `UserWarning`, but **don't rely on seeing it** —
  warnings get swallowed in agent shells, CI, and notebooks. Treat "both defined"
  as a hard review error.
* **Prefer `agent_help()` over the built-in `help()`** for agent-facing usage
  guidance. `help()` is still fine for human debugging, but it's verbose and
  isn't structured around behavioral rules.

## The one rule

> Before coding against an unfamiliar or risky Python API, call
> `agent_help(target)`: trust the **signatures**, sanity-check the **notes**,
> mind **imports and version**. When you author an API, make the notes verifiable
> so they fail loudly instead of lying quietly.
