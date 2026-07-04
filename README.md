# agent-readable

[![CI](https://github.com/zydo/agent-readable/actions/workflows/ci.yml/badge.svg)](https://github.com/zydo/agent-readable/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/agent-readable.svg)](https://pypi.org/project/agent-readable/)

Stop coding agents from hallucinating Python APIs. `agent_help(target)` reads the live public API surface from any Python class, module, function, or method and renders compact, agent-oriented Markdown with current signatures and docstring summaries. When a library opts in, it can also return class-level usage rules such as lifecycle order, preconditions, and anti-patterns.

To let your coding agent automatically call `agent_help()` before using an unfamiliar API, install the companion skill:

```bash
npx skills add zydo/skills --skill agent-readable
```

<!-- markdownlint-disable MD033 -->
<p align="center">
  <strong><code>logging.Logger</code> compared with <code>agent_help()</code> and <code>help()</code></strong><br>
  <img src="docs/agent_help_vs_help.gif" alt="agent_help vs help">
</p>
<!-- markdownlint-enable MD033 -->

## Quickstart

See [Getting started](docs/getting-started.md) for installation, one-off CLI usage with `uvx`, `uv tool run`, or `pipx`, and full CLI examples.

```python
from agent_readable import agent_help
import logging

print(agent_help(logging.Logger))
```

`agent_help()` works on plain Python objects with no setup required. It returns a curated public API list from runtime introspection, so agents see what exists in the installed version instead of guessing from stale training data.

Library authors can optionally add usage rules next to the code:

```python
class Sensor:
    """Reads a value from a hardware sensor."""

    def read(self) -> float:
        """Read the current sensor value."""

    @classmethod
    def __agent_notes__(cls) -> str:
        return """
## Do

- Call `calibrate()` once during setup, before `read()`.

## Do not

- Do not call `read()` before calibration on first use.
"""
```

## Docs

- [Getting started](docs/getting-started.md): installation, quickstart, CLI usage, and other language implementations.
- [Why it matters](docs/why.md): the API hallucination problem, token efficiency, and how this compares to other agent-doc patterns.
- [Examples](docs/examples.md): wrapping existing classes, inherited notes, duck typing, plain classes, modules, functions, and methods.
- [Authoring guide](docs/authoring.md): `__agent_help__`, `__agent_notes__`, class docstring hints, freshness guidance, and API reference.
- [FAQ](docs/faq.md): common questions about agent skills, docstrings, `AGENTS.md`, third-party libraries, and constrained decoding.

## Other Languages

- TypeScript: [`agent-readable-ts`](https://github.com/zydo/agent-readable-ts)

## License

[MIT](LICENSE)
