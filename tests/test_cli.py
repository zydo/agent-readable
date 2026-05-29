import sys

import pytest

from agent_readable import AgentReadableMixin
from agent_readable.__main__ import main

# -- Test fixtures -----------------------------------------------------------


class Cache(AgentReadableMixin):
    """An in-memory cache with TTL support."""

    def get(self, key: str):
        """Retrieve a value by key."""

    def set(self, key: str, value, ttl: int = 300):
        """Store a value with an optional TTL."""


class WithCustomDoc:
    """A class with custom agent docs."""

    @classmethod
    def __agent_help__(cls) -> str:
        return "Custom agent docs for WithCustomDoc."


# -- In-process CLI tests -----------------------------------------------------


def test_cli_mixin_class_with_colon(capsys):
    code = _run_main("tests.test_cli:Cache")
    assert code == 0
    out = capsys.readouterr().out
    assert "# Cache" in out
    assert "get" in out
    assert "set" in out
    assert "## Agent usage rules" in out


def test_cli_mixin_class_with_dot(capsys):
    code = _run_main("tests.test_cli.Cache")
    assert code == 0
    out = capsys.readouterr().out
    assert "# Cache" in out
    assert "get" in out


def test_cli_custom_doc_class(capsys):
    code = _run_main("tests.test_cli:WithCustomDoc")
    assert code == 0
    out = capsys.readouterr().out
    assert "Custom agent docs for WithCustomDoc." in out


def test_cli_no_args(capsys):
    code = _run_main()
    assert code == 1
    err = capsys.readouterr().err
    assert "Usage" in err


def test_cli_nonexistent_module():
    with pytest.raises(ModuleNotFoundError):
        _run_main("does_not_exist:Foo")


def test_cli_nonexistent_attribute():
    with pytest.raises(AttributeError):
        _run_main("tests.test_cli:NonExistent")


def test_cli_function_target(capsys):
    code = _run_main("agent_readable:agent_help")
    assert code == 0
    out = capsys.readouterr().out
    assert "agent_help" in out
    assert "## Signature" in out


def test_cli_method_target(capsys):
    code = _run_main("tests.test_cli:Cache.get")
    assert code == 0
    out = capsys.readouterr().out
    assert "Cache.get" in out
    assert "## Signature" in out
    assert "Retrieve a value by key." in out


def test_cli_invalid_target_type():
    with pytest.raises(TypeError, match="expected a class, module, function"):
        _run_main("agent_readable:__version__")


def test_cli_module(capsys):
    code = _run_main("pathlib")
    assert code == 0
    out = capsys.readouterr().out
    assert "# pathlib" in out
    assert "## Public API" in out


def _run_main(*args: str):
    """Run main() in-process, capturing stdout/stderr."""
    orig = sys.argv
    sys.argv = ["agent_readable", *args]
    try:
        main()
    except SystemExit as e:  # NOSONAR
        return e.code
    finally:
        sys.argv = orig
    return 0
