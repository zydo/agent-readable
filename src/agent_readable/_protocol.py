from __future__ import annotations

import inspect
import types
from typing import Any, Protocol, runtime_checkable

from ._model import (
    build_class_doc,
    build_function_doc,
    build_module_doc,
    collect_agent_notes,
)
from ._render import render_markdown, render_notes

_MISSING = object()


@runtime_checkable
class AgentReadable(Protocol):
    """Protocol for classes that expose agent-oriented documentation.

    Implementing ``__agent_help__()`` replaces the **auto-generated base
    document** (introspected public API, constructor, usage rules) with the
    returned string. ``__agent_notes__()`` sections are still appended after
    it, so notes defined anywhere in the MRO keep showing — if you want full
    verbatim control of the entire output, do not define ``__agent_notes__()``
    anywhere in the class hierarchy.
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

        Unlike ``__agent_help__`` (which replaces the auto-generated base
        document), ``__agent_notes__`` is **appended** — after the auto-doc, or
        after a custom ``__agent_help__()``'s output — and **accumulates across
        the MRO**: every class that defines its own ``__agent_notes__``
        contributes a section. The leaf class is tagged as taking precedence
        over inherited notes when they conflict.

        Do not prepend ``super().__agent_notes__()`` — collection is automatic.
        Defining this method on any class is enough; the ``AgentReadableMixin``
        is not required.
        """
        return ""


def agent_help(obj: Any) -> str:
    """
    Return agent-oriented help for a class, instance, module, function, or method.

    Dispatch for classes/instances:

    1. **``__agent_help__()`` is defined** — call it and use its result as the
       base document. ``__agent_notes__()`` sections from every class in the
       MRO are appended after it, mirroring the auto-doc path (the mixin
       default already embeds notes, so its output is used as-is; a notes
       method that raises is skipped, like a raising ``__agent_help__``).
    2. **``__agent_help__`` is missing** — fall through to
       ``_base_agent_doc(cls)``, the auto-generated document with
       ``__agent_notes__()`` from every class in the MRO appended.
    3. **``__agent_help__()`` raises** — same fallback as path 2.

    Notes always contribute when defined, regardless of path — there is no
    combination of the two dunders that silently drops notes.

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
        result = _MISSING
        try:
            result = fn()
        except Exception:
            pass
        if result is not _MISSING:
            rendered = result if isinstance(result, str) else str(result)
            return _with_appended_notes(rendered, target, fn)

    return _base_agent_doc(target)


def _with_appended_notes(rendered: str, cls: type, fn: Any) -> str:
    """Append collected ``__agent_notes__()`` sections after custom help output.

    The mixin's ``__agent_help__`` builds on ``_base_agent_doc``, which already
    embeds notes — appending again would duplicate them — so its output is
    returned unchanged. Any other implementation gets the same additive notes
    treatment as the auto-doc path.
    """
    mixin_help = AgentReadableMixin.__dict__["__agent_help__"].__func__
    if getattr(fn, "__func__", None) is mixin_help:
        return rendered
    notes = collect_agent_notes(cls)
    if not notes:
        return rendered
    return rendered + "\n\n" + render_notes(tuple(notes))


def _base_agent_doc(cls: type) -> str:
    """Render the auto-generated class docs: introspect into a model, then format.

    Appends ``__agent_notes__()`` from every class in ``cls.__mro__``, whether or
    not the class uses ``AgentReadableMixin`` — the accumulation happens in
    ``build_class_doc``.
    """
    return render_markdown(build_class_doc(cls))


def _module_doc(module: types.ModuleType) -> str:
    return render_markdown(build_module_doc(module))


def _function_doc(fn: Any) -> str:
    return render_markdown(build_function_doc(fn))
