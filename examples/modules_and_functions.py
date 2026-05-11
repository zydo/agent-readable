"""
Example: Using agent_help() on modules, functions, and methods.

Demonstrates non-class targets:
  1. A custom module (this file itself).
  2. A stdlib module (pathlib).
  3. A function (connect, defined below).
  4. A method (Query.execute, defined below).

Run this file to see all outputs:
    python examples/modules_and_functions.py
"""

import os
import pathlib
import sys

from agent_readable import agent_help


def connect(host: str, port: int = 5432) -> str:
    """Connect to a database server."""
    return f"{host}:{port}"


def disconnect():
    """Close the connection."""


class Query:
    """Build and execute a query."""

    def execute(self, sql: str) -> list:  # noqa: S1172
        """Execute a SQL statement."""
        return []


if __name__ == "__main__":
    os.environ["PAGER"] = "cat"

    print("=== agent_help(this_module) — custom module ===")
    print()
    print(agent_help(sys.modules[__name__]))

    print()
    print("=" * 72)
    print()

    print("=== agent_help(pathlib) — stdlib module ===")
    print()
    print(agent_help(pathlib))

    print()
    print("=" * 72)
    print()

    print("=== agent_help(connect) — function ===")
    print()
    print(agent_help(connect))

    print()
    print("=" * 72)
    print()

    print("=== agent_help(Query.execute) — method ===")
    print()
    print(agent_help(Query.execute))
