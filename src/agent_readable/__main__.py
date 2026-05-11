"""CLI: ``python -m agent_readable package.module:ClassName``,
``python -m agent_readable package.module.ClassName``,
``python -m agent_readable package.module:Class.method``,
or ``python -m agent_readable package.module``."""

from __future__ import annotations

import importlib
import inspect
import sys
import types
from typing import Any

from . import agent_help


def _resolve(dotted_path: str) -> Any:
    """Import and resolve a target path to a class, module, function, or method.

    Accepts ``package.module:ClassName``, ``package.module.ClassName``,
    ``package.module:Class.method``, or ``package.module``.
    """
    if ":" in dotted_path:
        module_path, _, attr = dotted_path.partition(":")
    elif "." in dotted_path:
        module_path, _, attr = dotted_path.rpartition(".")
    else:
        return importlib.import_module(dotted_path)

    target: Any = importlib.import_module(module_path)

    for part in attr.split(".") if attr else []:
        target = getattr(target, part)

    if not (isinstance(target, (type, types.ModuleType)) or inspect.isroutine(target)):
        raise TypeError(
            f"{dotted_path!r} resolved to {type(target).__name__}, "
            "expected a class, module, function, or method"
        )

    return target


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: python -m agent_readable "
            "(package.module:Target | package.module.Target | package.module) "
            "where Target is a class, function, or Class.method",
            file=sys.stderr,
        )
        sys.exit(1)

    target = _resolve(sys.argv[1])
    print(agent_help(target))


if __name__ == "__main__":
    main()
