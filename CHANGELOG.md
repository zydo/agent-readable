# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `py.typed` marker so inline type annotations are visible to downstream type
  checkers (PEP 561).
- A module's `__all__` is now honored as the authoritative public API when
  present, including symbols re-exported from other modules.
- `agent_help()` now emits a `UserWarning` when a class defines both a custom
  `__agent_help__()` and `__agent_notes__()`, since the notes are silently
  dropped in that case.
- Agent Skill at `skills/agent-readable/SKILL.md` following the
  [Agent Skills open standard](https://agentskills.io). Portable across
  Claude Code, Codex CLI (OpenAI), Gemini CLI (Google), GitHub Copilot, Cursor,
  JetBrains Junie, Goose, OpenCode, and 40+ other adopters — drop the folder
  into your agent's skills directory and it teaches the agent to call
  `agent_help()` and to author new APIs with `__agent_notes__()`. Supersedes
  `AGENT-PROMPT.md` as the recommended way to wire up coding agents.

### Fixed

- Method signatures with a positional-only `self` no longer render a dangling
  `/` (e.g. `backup(/, target)` now renders as `backup(target)`).

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

[Unreleased]: https://github.com/zydo/agent-readable/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/zydo/agent-readable/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/zydo/agent-readable/releases/tag/v0.1.0
