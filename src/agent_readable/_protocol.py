from __future__ import annotations

import inspect
import types
import warnings
from typing import Any, Protocol, runtime_checkable

from ._model import (
    build_class_doc,
    build_function_doc,
    build_module_doc,
    collect_agent_notes,
)
from ._render import render_markdown

_MISSING = object()


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
       output. If such a class also defines ``__agent_notes__()``, a
       ``UserWarning`` is emitted because those notes are silently dropped.
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
        result = _MISSING
        try:
            result = fn()
        except Exception:
            pass
        if result is not _MISSING:
            if _custom_help_drops_notes(target, fn):
                warnings.warn(
                    f"{target.__name__} defines both a custom __agent_help__() and "
                    "__agent_notes__(), but the notes are silently dropped: a custom "
                    "__agent_help__() owns the full output, so agent_help() never "
                    "appends notes. Fold the notes into __agent_help__(), or remove "
                    "the custom __agent_help__() to use the auto-generated docs "
                    "(which do append notes).",
                    stacklevel=2,
                )
            if isinstance(result, str):
                return result
            return str(result)

    return _base_agent_doc(target)


def _custom_help_drops_notes(cls: type, fn: Any) -> bool:
    """True when a custom ``__agent_help__`` will silently discard ``__agent_notes__``.

    A custom (non-mixin) ``__agent_help__`` owns the full output and never reaches
    ``_base_agent_doc``, so any ``__agent_notes__`` the class defines is dropped. The
    mixin default appends notes, so it returns False; classes with no effective notes
    also return False.
    """
    mixin_help = AgentReadableMixin.__agent_help__.__func__
    if getattr(fn, "__func__", None) is mixin_help:
        return False
    return bool(collect_agent_notes(cls))


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
