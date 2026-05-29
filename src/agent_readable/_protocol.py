from __future__ import annotations

import inspect
import types
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AgentReadable(Protocol):
    """Protocol for classes that expose agent-oriented documentation.

    Implementing ``__agent_help__()`` opts the class into **full replacement**:
    the returned string IS what ``agent_help(cls)`` returns, verbatim. Notes from
    ``__agent_notes__()`` are NOT auto-appended — implementers control the entire
    output. To get auto-doc + appended notes instead, use ``AgentReadableMixin``
    (or just define ``__agent_notes__()`` and let the auto-doc path run).
    """

    @classmethod
    def __agent_help__(cls) -> str:
        """Return agent-oriented help for this class (full output, verbatim)."""
        ...


class AgentReadableMixin:
    """
    Optional mixin for classes that want agent-readable documentation.

    Deriving from this mixin gives your class a default ``__agent_help__()`` that
    auto-generates structured docs from introspection.

    Optionally, to append more help instructions to coding agents, override
    ``__agent_notes__()`` to add usage examples, do/don't rules, and anti-patterns, etc.
    """

    @classmethod
    def __agent_help__(cls) -> str:
        """Return agent-oriented help for this class.

        Do NOT override this method directly. To add custom notes, override
        ``__agent_notes__()`` instead.

        Coding agents:
            Call ``agent_help(TheClass)`` to learn how to use the class before
            generating code that uses it. Treat the output as the canonical usage guide.
        """
        return _base_agent_doc(cls)

    @classmethod
    def __agent_notes__(cls) -> str:
        """
        Additive custom guidance, collected from every class in the MRO.

        Unlike ``__agent_help__`` (which replaces the entire output),
        ``__agent_notes__`` is **appended** to the auto-generated docs and
        **accumulates across the MRO** — every class that defines its own
        ``__agent_notes__`` contributes a section. The leaf class is tagged as
        taking precedence over inherited notes when they conflict.

        Do not prepend ``super().__agent_notes__()`` — collection is automatic.
        Defining this method on any class is enough; the ``AgentReadableMixin``
        is not required.
        """
        return ""


def agent_help(obj: Any) -> str:
    """
    Return agent-oriented help for a class, instance, module, function, or method.

    Dispatch for classes/instances:

    1. **``__agent_help__()`` is defined** — call it and return its result
       verbatim. The ``AgentReadableMixin`` default returns
       ``_base_agent_doc(cls)`` (auto-doc with ``__agent_notes__`` appended);
       duck-typed implementations return whatever the user formatted, so notes
       are NOT auto-included on that path — the implementer owns the full
       output.
    2. **``__agent_help__`` is missing** — fall through to
       ``_base_agent_doc(cls)``, which appends ``__agent_notes__()`` from every
       class in the MRO automatically.
    3. **``__agent_help__()`` raises** — same fallback as path 2 (auto-doc with
       notes).

    Notes accumulation lives in ``_base_agent_doc()``, which is why duck-typed
    ``__agent_help__()`` skips it: that path never reaches ``_base_agent_doc``.

    For modules: if the module defines a ``__agent_help__`` attribute (callable
    or string), it is used directly. Otherwise auto-generated docs are produced
    via ``_module_doc()``. Module ``__agent_notes__`` is not part of the
    protocol — modules don't have an MRO to accumulate over.

    For functions and methods (anything ``inspect.isroutine`` accepts): an
    ``__agent_help__`` attribute on the routine — callable or string — is used
    directly if present; otherwise ``_function_doc()`` renders signature, full
    docstring, and agent usage rules.
    """
    if inspect.ismodule(obj):
        fn = getattr(obj, "__agent_help__", None)
        if callable(fn):
            try:
                result = fn()
                if isinstance(result, str):
                    return result
                return str(result)
            except Exception:
                pass
        if isinstance(fn, str):
            return fn
        return _module_doc(obj)

    if inspect.isroutine(obj):
        override = getattr(obj, "__agent_help__", None)
        if callable(override):
            try:
                result = override()
                if isinstance(result, str):
                    return result
                return str(result)
            except Exception:
                pass
        if isinstance(override, str):
            return override
        return _function_doc(obj)

    target = obj if inspect.isclass(obj) else obj.__class__

    fn = getattr(target, "__agent_help__", None)
    if callable(fn):
        try:
            result = fn()
            if isinstance(result, str):
                return result
            return str(result)
        except Exception:
            pass

    return _base_agent_doc(target)


def _module_doc(module: types.ModuleType) -> str:
    """Generate compact Markdown documentation for a module."""
    parts: list[str] = []

    parts.append(f"# {module.__name__}")
    parts.append("")

    doc = inspect.getdoc(module)
    if doc:
        parts.append("## Purpose")
        parts.append("")
        parts.append(doc)
        parts.append("")

    public_api = _collect_module_api(module)
    if public_api:
        parts.append("## Public API")
        parts.append("")
        parts.extend(public_api)
        parts.append("")

    parts.append("## Agent usage rules")
    parts.append("")
    parts.append("- Prefer the public API listed above.")
    parts.append("- Do not use private names starting with `_`.")
    parts.append("- Do not invent unsupported behavior.")
    parts.append(
        "- If usage is ambiguous, prefer the simplest documented usage pattern."
    )

    return "\n".join(parts)


def _collect_module_api(module: types.ModuleType) -> list[str]:
    lines: list[str] = []
    mod_name = module.__name__
    for name, obj in inspect.getmembers(module):
        if name.startswith("_"):
            continue
        obj_module = getattr(obj, "__module__", None)
        if (
            obj_module is not None
            and obj_module != mod_name
            and not obj_module.startswith(mod_name + ".")
        ):
            continue
        if inspect.isclass(obj):
            summary = _first_doc_line(obj)
            line = f"- `{name}` class"
            if summary:
                line += f": {summary}"
            lines.append(line)
        elif inspect.isfunction(obj):
            sig = _safe_signature(obj)
            summary = _first_doc_line(obj)
            line = f"- `{name}{sig}` function"
            if summary:
                line += f": {summary}"
            lines.append(line)
        elif isinstance(obj, types.ModuleType):
            continue
    return lines


def _function_doc(fn: Any) -> str:
    """Generate compact Markdown documentation for a function or method."""
    parts: list[str] = []

    short_name = getattr(fn, "__name__", None) or "function"
    display_name = getattr(fn, "__qualname__", None) or short_name
    parts.append(f"# {display_name}")
    parts.append("")

    sig = _safe_signature(fn)
    parts.append("## Signature")
    parts.append("")
    parts.append("```python")
    parts.append(f"{short_name}{sig}")
    parts.append("```")
    parts.append("")

    doc = inspect.getdoc(fn)
    if doc:
        parts.append("## Purpose")
        parts.append("")
        parts.append(doc)
        parts.append("")

    parts.append("## Agent usage rules")
    parts.append("")
    parts.append("- Call with the documented signature.")
    parts.append("- Do not invent unsupported behavior.")
    parts.append(
        "- If usage is ambiguous, prefer the simplest documented usage pattern."
    )

    return "\n".join(parts)


def _base_agent_doc(cls: type) -> str:
    """
    Generate compact Markdown documentation for AI coding agents.

    Appends ``__agent_notes__()`` from every class in ``cls.__mro__``,
    whether or not the class uses ``AgentReadableMixin``.
    """
    parts: list[str] = []

    parts.append(f"# {cls.__name__}")
    parts.append("")

    constructor = _format_constructor(cls)
    if constructor:
        parts.append("## Constructor")
        parts.append("")
        parts.append("```python")
        parts.append(constructor)
        parts.append("```")
        parts.append("")

    doc = inspect.getdoc(cls)
    if doc:
        parts.append("## Purpose")
        parts.append("")
        parts.append(doc)
        parts.append("")

    public_api = _collect_public_api(cls)
    if public_api:
        parts.append("## Public API")
        parts.append("")
        parts.extend(public_api)
        parts.append("")

    parts.append("## Agent usage rules")
    parts.append("")
    parts.append("- Prefer the public API listed above.")
    parts.append("- Do not use private methods or attributes starting with `_`.")
    parts.append("- Do not invent unsupported behavior.")
    parts.append(
        "- If usage is ambiguous, prefer the simplest documented usage pattern."
    )

    base = "\n".join(parts)
    notes = _collect_agent_notes(cls)
    if notes:
        return base + "\n\n" + "\n\n".join(notes)
    return base


def _collect_agent_notes(cls: type) -> list[str]:
    """Collect ``__agent_notes__()`` sections from every class in ``cls.__mro__``.

    Each class that defines its own ``__agent_notes__`` becomes a Markdown section.
    The leaf class's notes are tagged as taking precedence over inherited ones when
    conflicts arise.
    """
    notes: list[str] = []
    parent_names: list[str] = []
    for klass in reversed(cls.__mro__):
        raw = klass.__dict__.get("__agent_notes__")
        if raw is None:
            continue
        fn = raw.__func__ if isinstance(raw, classmethod) else raw
        result = fn(cls)
        if result:
            header = f"## Notes from class {klass.__name__}"
            if klass is cls and parent_names:
                header += (
                    f" (inherits {', '.join(parent_names)}; "
                    "if notes conflict, these take precedence)"
                )
            notes.append(header + "\n\n" + result.strip())
            if klass is not cls:
                parent_names.append(klass.__name__)
    return notes


def _format_constructor(cls: type) -> str | None:
    try:
        signature = inspect.signature(cls)
    except (TypeError, ValueError):
        return None

    return f"{cls.__name__}{signature}"


def _collect_public_api(cls: type) -> list[str]:
    lines: list[str] = []

    for name, _ in inspect.getmembers(cls):
        if name.startswith("_"):
            continue

        try:
            raw = inspect.getattr_static(cls, name)
        except AttributeError:
            continue

        if isinstance(raw, property):
            summary = _first_doc_line(raw)
            line = f"- `{name}` property"
            if summary:
                line += f": {summary}"
            lines.append(line)
            continue

        if isinstance(raw, staticmethod):
            fn = raw.__func__
            kind = "staticmethod"
        elif isinstance(raw, classmethod):
            fn = raw.__func__
            kind = "classmethod"
        elif inspect.isfunction(raw) or (callable(raw) and not isinstance(raw, type)):
            fn = raw
            kind = "method"
        else:
            continue

        if kind in ("method", "classmethod"):
            sig = _signature_without_first_param(fn)
        else:
            sig = _safe_signature(fn)
        summary = _first_doc_line(fn)

        line = f"- `{name}{sig}` {kind}"
        if summary:
            line += f": {summary}"

        lines.append(line)

    return lines


def _safe_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "(...)"


def _signature_without_first_param(fn: Any) -> str:
    """Render ``fn``'s signature with its leading ``self``/``cls`` removed.

    Dropping the parameter through the ``Signature`` object instead of by string
    surgery keeps positional-only markers correct: a positional-only ``self`` no
    longer leaves a dangling ``/`` (e.g. ``(self, /, target)`` -> ``(target)``).
    Return annotations are preserved automatically.
    """
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return "(...)"
    params = list(sig.parameters.values())
    return str(sig.replace(parameters=params[1:]))


def _first_doc_line(obj: Any) -> str:
    doc = inspect.getdoc(obj)
    if not doc:
        return ""

    paragraph: list[str] = []
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped:
            paragraph.append(stripped)
        elif paragraph:
            break

    return " ".join(paragraph)
