"""
Example: Adding agent-readable docs to a class you don't own.

Uses sqlite3.Connection — a stdlib class every Python developer knows.
Just subclass + AgentReadableMixin, no overrides needed.

Run this file to see both outputs:
    python examples/sqlite_connection.py
"""

import os
import sqlite3

from agent_readable import AgentReadableMixin, agent_help


class Connection(sqlite3.Connection, AgentReadableMixin):
    """
    An agent-friendly wrapper around sqlite3.Connection. A simple mixin subclass that
    adds agent-readable markdown automatically, with no overrides needed.

    Message for coding Agents:
        Run ``agent_help(Connection)`` before using this class in generated code.
    """

    @classmethod
    def __agent_notes__(cls) -> str:
        # Overriding this method is optional, leave it out if you don't have any extra
        # notes to add beyond the auto-generated docs.
        return (
            "Additional notes about using Connection here. "
            "For example, common pitfalls, best practices, etc."
        )


if __name__ == "__main__":
    print("=== help(sqlite3.Connection) — every inherited dunder and MRO detail ===")
    print()
    os.environ["PAGER"] = "cat"
    help(sqlite3.Connection)  # NOSONAR

    print()
    print("=" * 72)
    print()
    print("=== agent_help(Connection) — structured, agent-friendly ===")
    print()
    print(agent_help(Connection))

    # This will also print the same agent-friendly docs, but without the additional
    # notes from Connection.__agent_notes__() override:
    #
    # print(agent_help(sqlite3.Connection))
