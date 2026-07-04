# FAQ

## How does my agent know to call `agent_help()` instead of `help()`?

Install the companion agent skill:

```bash
npx skills add zydo/skills --skill agent-readable
```

The skill teaches the agent to install `agent-readable`, call `agent_help(target)` before writing code against a class, module, function, or method, and add `__agent_notes__()` or improve docstrings when authoring new public APIs.

Cursor is among the adopters too, but its skill integration is manual: invoke the skill explicitly there rather than relying on description-match auto-activation.

## How is this different from `AGENTS.md`, `llms.txt`, or Cursor rules?

Different granularity, different drift profile.

`AGENTS.md`, `llms.txt`, and `.cursor/rules` are project-level: one file per repo. They are good for rules like "use pnpm," "run lint before commit," or "this codebase prefers functional style."

`agent-readable` is class- or module-level: rules live next to the API they describe. It is better for guidance like "`ResourcePool.call()` is for non-streaming requests; for streaming, use `stream()` instead."

Use both. They do not compete. The advantage of class-level docs is that they travel with the code. When someone refactors `ResourcePool` into two classes, the rules move with the relevant class in the same PR instead of sitting stale in a sidecar file.

## Why not just write better docstrings?

Docstrings answer "what does this do?" They are not designed for "when may I call this?" or "what is the wrong way to use this?"

Mixing both categories into the docstring makes the API summary noisier without helping agents reliably find usage rules. `__agent_notes__()` is for the second category, and it accumulates across the MRO automatically. Class docstrings do not compose like that.

## Does this work for libraries I do not own?

Yes. Two common options:

- Subclass the target class and add `AgentReadableMixin` or `__agent_notes__()`.
- Monkey-patch: `ThirdPartyClass.__agent_notes__ = classmethod(lambda cls: "...")`.

`agent_help()` collects notes from the entire MRO; the mixin is not required.

## Does it work without my class doing anything?

Yes. `agent_help()` falls back to introspection. You get a structured summary of every plain class, mixin or not. Notes are added on top if the class defines them; otherwise the auto-doc is what you see.

## Is `agent_help()` the strongest fix for API hallucination?

No. The strongest known mitigation is constrained decoding at the harness or decoder layer: masking illegal API tokens before generation, so the model cannot produce a nonexistent method at all.

`agent_help()` takes a lighter, library-side path: an authoritative usage guide injected into the agent's context, leaving the agent to read and follow it. Recent research on Python API misuse shows the in-context route leaves a meaningful slice of hallucinations on the table even when verified API references are provided.

The two approaches compose. Pick `agent_help()` when you have leverage on the library side and want a fix that works on every agent and every library today, without harness changes. Reach for constrained decoding when you control the harness or decoder. Either way, verify generated code before merging.
