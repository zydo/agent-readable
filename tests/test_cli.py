from agent_readable import AgentReadableMixin, __version__
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
    assert code == 2
    err = capsys.readouterr().err
    assert "usage:" in err.lower()
    assert "target" in err


def test_cli_version(capsys):
    code = _run_main("--version")
    assert code == 0
    out = capsys.readouterr().out
    assert __version__ in out


def test_cli_nonexistent_module(capsys):
    code = _run_main("does_not_exist:Foo")
    assert code == 2
    err = capsys.readouterr().err
    assert "error:" in err
    assert "does_not_exist" in err


def test_cli_nonexistent_attribute(capsys):
    code = _run_main("tests.test_cli:NonExistent")
    assert code == 2
    err = capsys.readouterr().err
    assert "error:" in err
    assert "NonExistent" in err


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


def test_cli_invalid_target_type(capsys):
    code = _run_main("agent_readable:__version__")
    assert code == 2
    err = capsys.readouterr().err
    assert "expected a class, module, function" in err


def test_cli_module(capsys):
    code = _run_main("pathlib")
    assert code == 0
    out = capsys.readouterr().out
    assert "# pathlib" in out
    assert "## Public API" in out


def _run_main(*args: str) -> int:
    """Run main() in-process, capturing stdout/stderr."""
    try:
        main(list(args))
    except SystemExit as e:  # NOSONAR
        return int(e.code) if isinstance(e.code, int) else 0
    return 0
