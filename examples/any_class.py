"""
Example: Using agent_help() on any class — no setup required.

Even without duck-typing or the mixin, ``agent_help()`` still generates
compact, structured Markdown from introspection. You cannot add custom
``__agent_notes__()``, but the output is still more agent-friendly than
Python's built-in ``help()``.

Uses logging.Logger — a stdlib class every Python developer knows.

Run this file to see both outputs:
    python examples/any_class.py
"""

import logging
import os

from agent_readable import agent_help

if __name__ == "__main__":
    print("=== help(logging.Logger) — verbose, not agent-friendly ===")
    print()
    os.environ["PAGER"] = "cat"
    help(logging.Logger)  # NOSONAR

    print()
    print("=" * 72)
    print()
    print("=== agent_help(logging.Logger) — compact, structured, agent-friendly ===")
    print()
    print(agent_help(logging.Logger))
