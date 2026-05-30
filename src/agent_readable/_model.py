"""Structured, format-neutral model of agent-oriented documentation.

This module owns **extraction**: turning a class, module, function, or method
into a :class:`HelpDoc` — a renderer-agnostic intermediate representation. A
renderer (see ``_render.py`` for the Markdown one) turns a ``HelpDoc`` into a
concrete string. Keeping the two apart means new output formats (plain text,
HTML, JSON for MCP servers) only need a new renderer; the introspection logic
here is shared by all of them.
"""

from __future__ import annotations

import inspect
import types
from dataclasses import dataclass, field
from typing import Any

_CLASS_USAGE_RULES = (
    "- Prefer the public API listed above.",
    "- Do not use private methods or attributes starting with `_`.",
    "- Do not invent unsupported behavior.",
    "- If usage is ambiguous, prefer the simplest documented usage pattern.",
)
_MODULE_USAGE_RULES = (
    "- Prefer the public API listed above.",
    "- Do not use private names starting with `_`.",
    "- Do not invent unsupported behavior.",
    "- If usage is ambiguous, prefer the simplest documented usage pattern.",
)
_FUNCTION_USAGE_RULES = (
    "- Call with the documented signature.",
    "- Do not invent unsupported behavior.",
    "- If usage is ambiguous, prefer the simplest documented usage pattern.",
)


@dataclass(frozen=True)
class Member:
    """One public member of a class or module.

    ``signature`` is the call signature (e.g. ``"(offset: float)"``) and is
    ``None`` for members that are not called positionally — properties and
    classes. ``kind`` is one of ``method``, ``classmethod``, ``staticmethod``,
    ``property``, ``function``, or ``class``.
    """

    name: str
    kind: str
    summary: str = ""
    signature: str | None = None


@dataclass(frozen=True)
class Notes:
    """One class's ``__agent_notes__()`` contribution.

    ``inherited`` is non-empty only for the leaf class when it overrides notes
    from ancestors; it lists those ancestor names so a renderer can mark that
    the leaf's notes take precedence.
    """

    class_name: str
    body: str
    inherited: tuple[str, ...] = ()


@dataclass(frozen=True)
class HelpDoc:
    """Format-neutral model of an object's agent-oriented documentation.

    A single shape covers classes, modules, and functions: each populates the
    fields that apply to it (a class has a ``constructor`` and ``notes``; a
    function has a ``signature``; a module has neither) and leaves the rest at
    their empty defaults. Renderers walk these fields in a fixed order.
    """

    title: str
    constructor: str | None = None
    signature: str | None = None
    purpose: str | None = None
    members: tuple[Member, ...] = ()
    usage_rules: tuple[str, ...] = ()
    notes: tuple[Notes, ...] = field(default_factory=tuple)


def build_class_doc(cls: type) -> HelpDoc:
    """Extract a :class:`HelpDoc` from a class via introspection.

    Notes from ``__agent_notes__()`` are collected from every class in
    ``cls.__mro__``, whether or not the class uses ``AgentReadableMixin``.
    """
    return HelpDoc(
        title=cls.__name__,
        constructor=_format_constructor(cls),
        purpose=inspect.getdoc(cls),
        members=tuple(_collect_public_api(cls)),
        usage_rules=_CLASS_USAGE_RULES,
        notes=tuple(collect_agent_notes(cls)),
    )


def build_module_doc(module: types.ModuleType) -> HelpDoc:
    """Extract a :class:`HelpDoc` from a module's docstring and public members."""
    return HelpDoc(
        title=module.__name__,
        purpose=inspect.getdoc(module),
        members=tuple(_collect_module_api(module)),
        usage_rules=_MODULE_USAGE_RULES,
    )


def build_function_doc(fn: Any) -> HelpDoc:
    """Extract a :class:`HelpDoc` from a function or method.

    The title is the qualified name (e.g. ``Pool.rotated``) while the rendered
    signature uses the short name, matching how Python introspection presents
    callables.
    """
    short_name = getattr(fn, "__name__", None) or "function"
    display_name = getattr(fn, "__qualname__", None) or short_name
    return HelpDoc(
        title=display_name,
        signature=f"{short_name}{_safe_signature(fn)}",
        purpose=inspect.getdoc(fn),
        usage_rules=_FUNCTION_USAGE_RULES,
    )


def collect_agent_notes(cls: type) -> list[Notes]:
    """Collect ``__agent_notes__()`` from every class in ``cls.__mro__``.

    Each class that defines its own ``__agent_notes__`` contributes one
    :class:`Notes`. The leaf class records the ancestor names it overrides so a
    renderer can mark that the leaf's notes win on conflict.
    """
    notes: list[Notes] = []
    parent_names: list[str] = []
    for klass in reversed(cls.__mro__):
        raw = klass.__dict__.get("__agent_notes__")
        if raw is None:
            continue
        fn = raw.__func__ if isinstance(raw, classmethod) else raw
        result = fn(cls)
        if result:
            inherited = tuple(parent_names) if klass is cls and parent_names else ()
            notes.append(
                Notes(
                    class_name=klass.__name__, body=result.strip(), inherited=inherited
                )
            )
            if klass is not cls:
                parent_names.append(klass.__name__)
    return notes


def _collect_module_api(module: types.ModuleType) -> list[Member]:
    members: list[Member] = []
    for name, obj in _module_members(module):
        if inspect.isclass(obj):
            members.append(
                Member(name=name, kind="class", summary=_first_doc_line(obj))
            )
        elif inspect.isfunction(obj):
            members.append(
                Member(
                    name=name,
                    kind="function",
                    summary=_first_doc_line(obj),
                    signature=_safe_signature(obj),
                )
            )
    return members


def _module_members(module: types.ModuleType) -> list[tuple[str, Any]]:
    """Return the ``(name, obj)`` pairs that make up a module's public surface.

    A module's ``__all__`` is the authoritative export list, so when it is
    defined those names win verbatim — including symbols re-exported from other
    modules (``from other import Foo``), which the ``__module__`` heuristic below
    would otherwise discard. Without ``__all__`` we fall back to the heuristic:
    skip private names and anything defined outside this module or its
    submodules.
    """
    explicit = getattr(module, "__all__", None)
    if explicit is not None:
        members: list[tuple[str, Any]] = []
        for name in explicit:
            if not isinstance(name, str):
                continue
            try:
                members.append((name, getattr(module, name)))
            except AttributeError:
                continue
        members.sort(key=lambda item: item[0])
        return members

    mod_name = module.__name__
    members = []
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
        members.append((name, obj))
    return members


def _format_constructor(cls: type) -> str | None:
    try:
        signature = inspect.signature(cls)
    except (TypeError, ValueError):
        return None

    return f"{cls.__name__}{signature}"


def _collect_public_api(cls: type) -> list[Member]:
    members: list[Member] = []

    for name, _ in inspect.getmembers(cls):
        if name.startswith("_"):
            continue

        try:
            raw = inspect.getattr_static(cls, name)
        except AttributeError:
            continue

        if isinstance(raw, property):
            members.append(
                Member(name=name, kind="property", summary=_first_doc_line(raw))
            )
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

        members.append(
            Member(name=name, kind=kind, summary=_first_doc_line(fn), signature=sig)
        )

    return members


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
