# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.1] - 2026-08-23

### Documentation

- Restructured the getting-started one-off CLI section into two parallel
  series, uv and pip, each with a one-off command and a repeated-use install,
  and added a "Your own project" section for documenting project-local
  targets.

## [0.3.0] - 2026-08-23

### Added

- Console script `agent-readable`, so one-off use is
  `uvx agent-readable sqlite3:Connection` instead of
  `uvx --from agent-readable python -m agent_readable sqlite3:Connection`.
  `python -m agent_readable` keeps working.
- `--version` flag for the CLI.
- Public class attributes and module constants are now listed in the Public API
  section with their current value: `repr` for exact primitive types (never
  executing a custom `__repr__`), the type name otherwise.
- Enum members are listed (e.g. ``- `RED` member: 1``), and the misleading
  `EnumMeta.__call__` constructor signature is no longer shown for enum
  classes.
- Module docs now include C builtins (`inspect.isroutine` instead of
  `inspect.isfunction`), so `agent_help(math)` lists `sin` alongside
  pure-Python functions, and module-level constants such as `math.pi` are no
  longer dropped by the origin heuristic.
- A constructor that introspection renders as the placeholder `(*args,
  **kwargs)` — e.g. masked by a metaclass `__call__` — now falls back to the
  class's `__init__`/`__new__` signature.
- Mypy type-checking job in CI.
- Benchmark harness (`scripts/benchmark.py`) and methodology
  (`docs/benchmark.md`) for measuring whether `agent_help()` context reduces
  hallucinated-API failures versus a baseline prompt. Status: not yet run;
  no numbers are claimed until a real run is recorded.

### Changed

- **Breaking:** `__agent_notes__()` sections are now always appended, including
  after a custom `__agent_help__()`'s output. Previously the notes were
  silently dropped when a custom `__agent_help__` was defined and a
  `UserWarning` was emitted; defining both is now a supported combination and
  the warning is gone. For full verbatim control of the entire output, do not
  define `__agent_notes__()` anywhere in the MRO.
- The CLI prints a one-line `error: ...` message to stderr and exits with
  status 2 for targets that cannot be imported or resolved, instead of raising
  a traceback.

### Fixed

- A raising `__agent_notes__()` no longer breaks `agent_help()` for the class
  and all of its subclasses; the broken notes are skipped, mirroring the
  existing `__agent_help__()` fallback.
- `functools.cached_property` members are no longer silently dropped from the
  Public API; they render as properties with the wrapped function's docstring.

## [0.2.1] - 2026-07-04

### Documentation

- Restructured the README into a concise overview and moved detailed guidance
  into focused docs for getting started, examples, authoring, rationale, and
  FAQ.
- Added CI and PyPI badges to the README.
- Added `uv add`, `uvx`, `uv tool run`, and `pipx run` installation and
  one-off execution examples.
- Added the TypeScript implementation under "Other Languages".

### Changed

- Renamed the GitHub Actions test workflow file to `ci.yml` and its display
  name to `CI`.
- Updated GitHub Actions versions to Node 24-compatible releases.
- Made the uv cache key unique for each Python version in the CI matrix.

## [0.1.2] - 2026-05-30

### Added

- `py.typed` marker so inline type annotations are visible to downstream type
  checkers (PEP 561).
- A module's `__all__` is now honored as the authoritative public API when
  present, including symbols re-exported from other modules.
- `agent_help()` now emits a `UserWarning` when a class defines both a custom
  `__agent_help__()` and `__agent_notes__()`, since the notes are silently
  dropped in that case.
- Agent Skill at `skills/agent-readable/SKILL.md` following the
  [Agent Skills open standard](https://agentskills.io). Installable via
  `npx skills add zydo/agent-readable --skill agent-readable` and portable
  across Claude Code, Codex CLI (OpenAI), Gemini CLI (Google), GitHub Copilot,
  Cursor, JetBrains Junie, Goose, OpenCode, and 40+ other adopters. The skill
  teaches the agent to call `agent_help()` before writing Python against a
  library and to author new APIs with `__agent_notes__()`. Supersedes
  `AGENT-PROMPT.md` as the recommended way to wire up coding agents.

### Fixed

- Method signatures with a positional-only `self` no longer render a dangling
  `/` (e.g. `backup(/, target)` now renders as `backup(target)`).

### Documentation

- README and examples reframed around curation, not compactness. The "Why it
  matters" section now leads with two failure modes — what-exists (curated
  Public API list curbs hallucinated methods and stale signatures) and
  how-to-use (lifecycle rules via `__agent_notes__()`) — instead of a
  comparative empirical claim about which is more common. Removed the
  "217 vs 56 lines" framing in favor of structure-and-rules language.
- Tagline sharpened to lead with the hallucination-stopping outcome rather
  than the protocol mechanics.

### Removed

- `AGENT-PROMPT.md` (superseded by the agent skill at
  `skills/agent-readable/SKILL.md`).

## [0.1.1] - 2026-05-11

### Added

- `agent_help()` support for functions and methods.

### Documentation

- Demo GIF comparing `agent_help()` and `help()`, plus additional README
  examples.

## [0.1.0] - 2026-05-10

### Added

- Initial release: the `agent_help()` function, the `AgentReadable` protocol,
  `AgentReadableMixin`, `__agent_notes__` accumulation across the MRO, module
  support, and the `python -m agent_readable` CLI.

[Unreleased]: https://github.com/zydo/agent-readable/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/zydo/agent-readable/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/zydo/agent-readable/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/zydo/agent-readable/compare/v0.2.0...v0.2.1
[0.1.2]: https://github.com/zydo/agent-readable/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/zydo/agent-readable/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/zydo/agent-readable/releases/tag/v0.1.0
