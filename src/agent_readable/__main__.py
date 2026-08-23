"""CLI: ``agent-readable package.module:ClassName``,
``agent-readable package.module.ClassName``,
``agent-readable package.module:Class.method``,
or ``agent-readable package.module`` (also ``python -m agent_readable ...``)."""

from __future__ import annotations

import argparse
import importlib
import inspect
import sys
import types
from typing import Any

from . import __version__, agent_help


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-readable",
        description=(
            "Print agent-oriented documentation for a Python class, module, "
            "function, or method."
        ),
    )
    parser.add_argument(
        "target",
        help=(
            "import path: package.module, package.module:Target, "
            "package.module.Target, or package.module:Class.method"
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


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


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    try:
        target = _resolve(args.target)
    except (ImportError, AttributeError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    print(agent_help(target))


if __name__ == "__main__":
    main()
