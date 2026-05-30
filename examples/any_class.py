"""
Example: Using agent_help() on any class — no setup required.

Even without duck-typing or the mixin, ``agent_help()`` still generates
structured Markdown from introspection — a curated public-API list with
current signatures, free of inherited dunders and MRO clutter. You cannot
add custom ``__agent_notes__()``, but the output is still more
agent-friendly than Python's built-in ``help()``.

Uses logging.Logger — a stdlib class every Python developer knows.

Run this file to see both outputs:
    python examples/any_class.py
"""

import logging
import os

from agent_readable import agent_help

if __name__ == "__main__":
    print("=== help(logging.Logger) — every inherited dunder and MRO detail ===")
    print()
    os.environ["PAGER"] = "cat"
    help(logging.Logger)  # NOSONAR

    print()
    print("=" * 72)
    print()
    print("=== agent_help(logging.Logger) — curated public API, structured sections ===")
    print()
    print(agent_help(logging.Logger))
