# Authoring guide

## Keeping agent docs up to date

Agent docs can go stale when classes change: new methods, changed behavior, or removed APIs. Install the companion skill to teach your agent to run `agent_help()` before modifying a class, prefer docstrings over `__agent_notes__()` for API summaries, and verify that the output stays accurate after changes.

```bash
npx skills add zydo/skills --skill agent-readable
```

## The `__agent_help__` protocol

`__agent_help__()` is a dunder protocol for tool-specific documentation, similar in spirit to:

- `__doc__`: read by Python `help()`, Sphinx, IDEs, and REPLs.
- `__rich_repr__`: read by Rich when it renders an object.
- `__html__`: read by Django, Jinja2, and MarkupSafe when rendering HTML.

Unlike `__str__` or `__fspath__`, these dunders do not change Python runtime behavior. They are metadata slots a specific tool reads when it wants a representation. `__agent_help__` follows the same pattern for agent documentation.

Classes that define a `@classmethod` named `__agent_help__` returning a `str` are considered agent-readable. Modules can define a top-level `__agent_help__` attribute, either callable or string. Call the top-level `agent_help(obj)` function to get the docs, just like `str()` calls `__str__()`.

The `AgentReadable` `typing.Protocol` and `AgentReadableMixin` are provided for convenience and type-checking, but neither is required.

## `__agent_help__` vs `__agent_notes__`

The two dunders intentionally encode different composition rules:

| Aspect          | `__agent_help__()`                         | `__agent_notes__()`                                                           |
| --------------- | ------------------------------------------ | ----------------------------------------------------------------------------- |
| Semantics       | Replaces the auto-generated base document  | Additive: appended after the auto-doc or custom `__agent_help__()` output     |
| Composition     | Single class wins, closest in MRO          | Accumulated across the MRO; leaf class wins on conflict                       |
| When to use     | Custom control over the base document      | Extra do/don't rules on top of any base                                       |
| Skipped when    | Always called if defined                   | Never skipped when defined; a notes method that raises is skipped             |
| Mixin required? | No                                         | No                                                                            |

When a class defines both `__agent_help__()` and `__agent_notes__()`, the custom help replaces the auto-generated base document and the notes are appended after it — the same additive behavior as the auto-doc path, so no combination of the two dunders silently drops notes. If you need full verbatim control of the entire output, do not define `__agent_notes__()` anywhere in the class hierarchy.

## Class docstring hints

For classes that inherit `AgentReadableMixin`, add a short hint in the class docstring:

```python
class ResourcePool(AgentReadableMixin):
    """
    Rotates interchangeable resources such as API keys.

    Agent usage:
        Run ``agent_help(ResourcePool)`` before using this class in generated code.
    """
```

This way, even agents that only see the source or call `help()` are reminded to check `agent_help()`.

## API reference

### `agent_help(target)`

Render agent-oriented Markdown for a class, module, function, or method.

For classes, the output includes purpose, constructor, public API (methods, properties, cached properties, constants, and enum members), default usage rules, and accumulated `__agent_notes__()` sections when present. For modules, it includes purpose, public functions (including C builtins), public classes, and constants. For functions and methods, it includes signature, docstring, and default usage rules.

For classes and instances, if `__agent_help__()` is defined through the mixin or duck typing, it is called and its return value is used as the base document. Duck-typed implementations replace the auto-generated base; `__agent_notes__()` sections from the MRO are still appended after it (the mixin default already embeds notes, so its output is used as-is). If `__agent_help__()` raises, `agent_help()` falls back to the auto-generated path, which does include notes. A `__agent_notes__()` that raises is skipped rather than fatal, so one broken notes method cannot take down help for a class and its subclasses.

For modules, if the module defines a `__agent_help__` attribute, either callable or string, it is used. Otherwise, auto-generated docs are produced from the module docstring and its public functions and classes. When the module defines `__all__`, that list is the authoritative public API, so re-exported symbols are included. Otherwise public members are discovered by introspection, skipping private names and anything defined outside the module.

For functions and methods, if the routine defines a `__agent_help__` attribute, either callable or string, it is used. Otherwise, auto-generated docs render the signature, full docstring, and usage rules. A bound method's signature drops `self`, and a classmethod's signature drops `cls`. If a callable `__agent_help__` raises, `agent_help()` falls back to the auto-generated path.

### `AgentReadable`

A runtime-checkable `typing.Protocol` that requires `__agent_help__() -> str`.

### `AgentReadableMixin`

A mixin class for classes that provides a default `__agent_help__()` implementation using introspection. The mixin is convenience only: defining `__agent_notes__()` directly on any class also works, and notes are collected automatically regardless of inheritance from the mixin.

The mixin does not apply to modules; modules are supported directly by `agent_help()`.

If a class inherits from `AgentReadableMixin`, coding agents should call `agent_help(TheClass)` before generating code that uses it.
