# Why agent-readable exists

AI coding agents recognize established libraries from their training data, but they hallucinate when APIs change, when libraries are new, or when correct usage depends on rules that are not visible from the API surface: preconditions, lifecycle order, anti-patterns, or distinctions like "use `call()` for non-streaming and `stream()` for streaming."

Today there is no standard place to put those rules where an agent will reliably find them. Docstrings document the API surface, not behavioral rules. `AGENTS.md` and `llms.txt` work at project granularity, drift quickly, and do not travel with refactors. `help()` describes interfaces, but mixes inherited dunders and MRO detail in with the methods you actually want to use.

`agent-readable` has two halves:

- The consume side is one function: `agent_help(target)`. It works on every Python library today, annotated or not. It introspects the live installed class, module, function, or method and returns a curated public API list with current signatures.
- The author side adds two dunders: `__agent_help__` for full custom output and `__agent_notes__` for additive behavioral rules that accumulate across inheritance.

When a library opts in, those rules show up next to the public API list in the same `agent_help()` output, so the rules travel with refactors instead of rotting in a sidecar file.

## Failure modes covered

`agent_help()` covers two failure modes agents hit on real APIs:

1. What exists. The `## Public API` section is a curated list of current signatures pulled from runtime introspection: no hallucinated methods, no stale signatures from training data, and no private members leaking in.
2. How to use it correctly. Lifecycle order, preconditions, anti-patterns, and "this method is for X, that one is for Y" do not fit in any single method's docstring and do not belong only in a project-level `AGENTS.md`.

## Token efficiency

Hallucinated APIs produce wrong code and trigger failure-retry loops that burn context and tokens. A single invented method can cost multiple rounds of write, run, error, and rewrite before the agent converges on a real API.

`agent_help()` generates compact, precise descriptions of publicly exposed interfaces. Because those descriptions are runtime-checked against the live installed package, calling it before writing code against an unfamiliar class or module can remove those retry rounds.

If the companion skill is installed, your agent can do this automatically before coding against unfamiliar APIs.

## A concrete contrast

`help(sqlite3.Connection)` includes inherited dunders and low-signal implementation detail:

```text
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
```

`agent_help(sqlite3.Connection)` produces a curated public API list with current signatures and any class-level rules attached. Notes from `__agent_notes__()` accumulate across inheritance. Class docs travel with the code in commits, reviews, and refactors; drift gets caught in code review instead of weeks later in a sidecar file.
