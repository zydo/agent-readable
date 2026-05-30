"""Markdown renderer for the :class:`HelpDoc` model.

This is the only place that knows about Markdown syntax. Adding another output
format (plain text, HTML, JSON for MCP servers) means adding a sibling renderer
that consumes the same :mod:`._model` types — the introspection layer stays
untouched.
"""

from __future__ import annotations

from ._model import HelpDoc, Member, Notes


def render_markdown(doc: HelpDoc) -> str:
    """Render a :class:`HelpDoc` as the compact Markdown ``agent_help()`` returns.

    Sections are emitted in a fixed order and only when their data is present,
    so a class (constructor + notes), a module (neither), and a function
    (signature) all flow through the same path.
    """
    sections: list[str] = [f"# {doc.title}"]

    if doc.constructor is not None:
        sections.append(_code_section("Constructor", doc.constructor))

    if doc.signature is not None:
        sections.append(_code_section("Signature", doc.signature))

    if doc.purpose:
        sections.append(f"## Purpose\n\n{doc.purpose}")

    if doc.members:
        body = "\n".join(_render_member(member) for member in doc.members)
        sections.append(f"## Public API\n\n{body}")

    if doc.usage_rules:
        body = "\n".join(doc.usage_rules)
        sections.append(f"## Agent usage rules\n\n{body}")

    for note in doc.notes:
        sections.append(_render_notes(note))

    return "\n\n".join(sections)


def _code_section(heading: str, code: str) -> str:
    return f"## {heading}\n\n```python\n{code}\n```"


def _render_member(member: Member) -> str:
    line = f"- `{member.name}{member.signature or ''}` {member.kind}"
    if member.summary:
        line += f": {member.summary}"
    return line


def _render_notes(note: Notes) -> str:
    header = f"## Notes from class {note.class_name}"
    if note.inherited:
        header += (
            f" (inherits {', '.join(note.inherited)}; "
            "if notes conflict, these take precedence)"
        )
    return f"{header}\n\n{note.body}"
