"""CLI: ``python -m agent_readable package.module:ClassName``,
``python -m agent_readable package.module.ClassName``,
or ``python -m agent_readable package.module``."""

from __future__ import annotations

import importlib
import sys
import types

from . import agent_help


def _resolve(dotted_path: str) -> type | types.ModuleType:
    """Import and resolve a target path to a class or module.

    Accepts ``package.module:ClassName``, ``package.module.ClassName``, or
    ``package.module``.
    """
    if ":" in dotted_path:
        module_path, _, attr = dotted_path.partition(":")
    elif "." in dotted_path:
        module_path, _, attr = dotted_path.rpartition(".")
    else:
        return importlib.import_module(dotted_path)

    module = importlib.import_module(module_path)

    for part in attr.split(".") if attr else []:
        module = getattr(module, part)

    if not isinstance(module, type) and not isinstance(module, types.ModuleType):
        raise TypeError(
            f"{dotted_path!r} resolved to {type(module).__name__}, "
            "expected a class or module"
        )

    return module


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: python -m agent_readable "
            "(package.module:ClassName | package.module.ClassName | package.module)",
            file=sys.stderr,
        )
        sys.exit(1)

    target = _resolve(sys.argv[1])
    print(agent_help(target))


if __name__ == "__main__":
    main()
