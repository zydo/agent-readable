import types

from agent_readable import AgentReadable, AgentReadableMixin, agent_help

# -- Test fixtures -----------------------------------------------------------


class WithAgentDoc:
    """A class with custom agent documentation."""

    @classmethod
    def __agent_help__(cls) -> str:
        return "Custom agent documentation."


class WithoutAgentDoc:
    """A plain class with only docstrings."""

    def __init__(self, name: str, value: int = 0):
        """Initialize with name and value."""

    def do_thing(self, x: int) -> str:
        """Do a thing with x."""
        return ""

    @classmethod
    def from_config(cls, path: str):
        """Create from a config file."""

    @staticmethod
    def validate(config):  # noqa: S1186
        """Validate the given config."""

    @property
    def healthy_count(self) -> int:
        """Number of healthy items."""
        return 0

    def _private_helper(self):
        """Should not appear in public API."""


class MixinSub(AgentReadableMixin):
    """A subclass of the mixin."""

    def run(self):
        """Run the thing."""


class MixinWithNotes(AgentReadableMixin):
    """A subclass with custom notes."""

    def go(self):
        """Go."""

    @classmethod
    def __agent_notes__(cls) -> str:
        return "## Extra\n\n- Do something."


class MixinWithNotesChild(MixinWithNotes):
    """A further subclass with its own notes."""

    def stop(self):
        """Stop."""

    @classmethod
    def __agent_notes__(cls) -> str:
        return "## Child notes\n\n- Child rule."


class HasAgentDocButNotMixin:
    """Duck-typed: implements __agent_help__ without the mixin."""

    @classmethod
    def __agent_help__(cls) -> str:
        return "Duck-typed agent doc."


# -- agent_help dispatch tests -----------------------------------------------


def test_agent_help_with_class_implementing_agent_doc():
    result = agent_help(WithAgentDoc)
    assert result == "Custom agent documentation."


def test_agent_help_with_instance():
    result = agent_help(WithAgentDoc())
    assert result == "Custom agent documentation."


def test_agent_help_duck_typed():
    result = agent_help(HasAgentDocButNotMixin)
    assert result == "Duck-typed agent doc."


def test_agent_help_mixin_default():
    result = agent_help(MixinSub)
    assert "# MixinSub" in result
    assert "run" in result
    assert "## Extra" not in result


def test_agent_help_mixin_with_notes():
    result = agent_help(MixinWithNotes)
    assert "# MixinWithNotes" in result
    assert "go" in result
    assert "## Notes from class MixinWithNotes" in result
    assert "Do something." in result


def test_agent_help_notes_accumulate_with_inheritance():
    result = agent_help(MixinWithNotesChild)
    assert "# MixinWithNotesChild" in result
    assert "## Notes from class MixinWithNotes" in result
    assert "Do something." in result
    assert "inherits MixinWithNotes; if notes conflict, these take precedence" in result
    assert "## Notes from class MixinWithNotesChild" in result
    assert "Child rule." in result


def test_agent_help_collects_notes_without_mixin():
    """Classes that define __agent_notes__ get auto-collection without the mixin."""

    class NotesOnly:
        """A plain class that only defines __agent_notes__."""

        def method(self):
            """Do something."""

        @classmethod
        def __agent_notes__(cls) -> str:
            return "## Custom\n\n- A custom rule."

    result = agent_help(NotesOnly)
    assert "# NotesOnly" in result
    assert "## Public API" in result
    assert "## Notes from class NotesOnly" in result
    assert "A custom rule." in result


def test_agent_help_accumulates_notes_without_mixin():
    """Note inheritance works for plain classes too."""

    class Parent:
        """Parent."""

        @classmethod
        def __agent_notes__(cls) -> str:
            return "Parent rule."

    class Child(Parent):
        """Child."""

        @classmethod
        def __agent_notes__(cls) -> str:
            return "Child rule."

    result = agent_help(Child)
    assert "## Notes from class Parent" in result
    assert "Parent rule." in result
    assert "## Notes from class Child (inherits Parent;" in result
    assert "Child rule." in result


def test_agent_help_duck_typed_skips_notes():
    """Duck-typed __agent_help__ controls full output; notes are NOT auto-appended."""

    class DuckTyped:
        """A class with both duck-typed help and notes."""

        @classmethod
        def __agent_help__(cls) -> str:
            return "Duck-typed verbatim."

        @classmethod
        def __agent_notes__(cls) -> str:
            return "These notes should be ignored."

    result = agent_help(DuckTyped)
    assert result == "Duck-typed verbatim."
    assert "should be ignored" not in result


def test_agent_help_plain_class_fallback():
    result = agent_help(WithoutAgentDoc)
    assert isinstance(result, str)
    assert "# WithoutAgentDoc" in result
    assert "## Purpose" in result
    assert "A plain class with only docstrings." in result


def test_agent_help_does_not_print(capsys):
    agent_help(WithoutAgentDoc)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


# -- agent_help fallback (plain class) tests ---------------------------------


def test_agent_help_includes_class_name():
    result = agent_help(WithoutAgentDoc)
    assert "# WithoutAgentDoc" in result


def test_agent_help_includes_constructor():
    result = agent_help(WithoutAgentDoc)
    assert "## Constructor" in result
    assert "```python" in result
    assert "WithoutAgentDoc" in result


def test_agent_help_includes_purpose():
    result = agent_help(WithoutAgentDoc)
    assert "## Purpose" in result
    assert "A plain class with only docstrings." in result


def test_agent_help_includes_public_api():
    result = agent_help(WithoutAgentDoc)
    assert "## Public API" in result
    assert "do_thing" in result
    assert "from_config" in result
    assert "classmethod" in result
    assert "validate" in result
    assert "staticmethod" in result
    assert "`healthy_count`" in result
    assert "property" in result


def test_agent_help_excludes_private():
    result = agent_help(WithoutAgentDoc)
    assert "_private_helper" not in result


def test_agent_help_includes_usage_rules():
    result = agent_help(WithoutAgentDoc)
    assert "## Agent usage rules" in result
    assert "Prefer the public API listed above." in result


def test_agent_help_method_summary_uses_first_paragraph():
    result = agent_help(WithoutAgentDoc)
    assert "Do a thing with x." in result


def test_agent_help_method_summary_collapses_wrapped_paragraph():
    """First paragraph (lines until a blank line) is joined with spaces."""

    class WrappedDoc:
        """Test class."""

        def method(self):
            """First sentence wrapped
            across two lines.

            Second paragraph should not appear in the summary.
            """

    result = agent_help(WrappedDoc)
    assert "First sentence wrapped across two lines." in result
    assert "Second paragraph" not in result


def test_agent_help_no_constructor_for_builtin():
    result = agent_help(int)
    assert "# int" in result
    assert "## Constructor" not in result


def test_agent_help_instance_of_plain_class():
    result = agent_help(WithoutAgentDoc("test"))
    assert "# WithoutAgentDoc" in result
    assert "## Purpose" in result
    assert "do_thing" in result


def test_agent_help_excludes_callable_class_attributes():
    class WithCallableAttr:
        """Test class."""

        def method(self):
            """A real method."""

        helper = WithoutAgentDoc  # type: ignore[assignment]

    result = agent_help(WithCallableAttr)
    assert "method" in result
    assert "helper" not in result


# -- AgentReadable protocol tests --------------------------------------------


def test_protocol_check():
    assert isinstance(WithAgentDoc, AgentReadable)
    assert isinstance(HasAgentDocButNotMixin, AgentReadable)


def test_protocol_check_negative():
    assert not isinstance(WithoutAgentDoc, AgentReadable)


# -- Method signature handling (via agent_help) ------------------------------


def test_agent_help_strips_self_from_method_sig():
    result = agent_help(WithoutAgentDoc)
    assert "do_thing(x: int) -> str" in result
    assert "do_thing(self," not in result


def test_agent_help_strips_cls_from_classmethod_sig():
    result = agent_help(WithoutAgentDoc)
    assert "from_config(path: str)" in result
    assert "from_config(cls," not in result


def test_agent_help_keeps_staticmethod_sig():
    result = agent_help(WithoutAgentDoc)
    assert "validate(config)" in result


def test_agent_help_method_self_only():
    class SelfOnly:
        """Test class."""

        def method(self):
            """A method."""

    result = agent_help(SelfOnly)
    assert "`method()` method" in result


def test_agent_help_method_self_only_with_return_annotation():
    """Regression: ``(self) -> T`` must render as ``() -> T``, not ``(-> T``."""

    class StatusReporter:
        """Test class."""

        def status(self) -> bool:
            """Return health status."""
            return True

    result = agent_help(StatusReporter)
    assert "`status() -> bool`" in result
    assert "`status(-> bool`" not in result


def test_agent_help_method_nested_generics():
    from typing import Callable

    class Nested:
        """Test class."""

        def apply(self, fn: Callable[[int], str], x: int) -> str:
            """Apply fn to x."""
            return fn(x)

    result = agent_help(Nested)
    assert "apply" in result
    assert "fn: Callable[[int], str]" in result
    assert "self," not in result


def test_agent_help_method_with_annotated_self():
    """Depth tracking handles bracketed annotations on the first parameter."""
    from typing import Generic, TypeVar

    T = TypeVar("T")

    class Box(Generic[T]):
        """A generic container."""

    class Container(Box[int]):
        """Test class."""

        def swap(self: "Box[int]", other: int) -> str:
            """Swap."""
            return str(other)

    result = agent_help(Container)
    public_api = result.split("## Agent usage")[0].split("## Public API")[1]
    assert "`swap(other: int) -> str`" in public_api
    assert "self" not in public_api


# -- Edge-case coverage (tested through public API only) ---------------------


def test_agent_help_non_string_agent_help():
    class NonStringDoc:
        @classmethod
        def __agent_help__(cls):  # type: ignore[override]
            return 42

    result = agent_help(NonStringDoc)
    assert result == "42"


def test_agent_help_exception_falls_back_to_base_doc():
    class ExplodingDoc:
        @classmethod
        def __agent_help__(cls) -> str:
            raise RuntimeError("boom")

    result = agent_help(ExplodingDoc)
    assert "ExplodingDoc" in result


def test_agent_help_skips_dynamic_attributes():
    class _Meta(type):
        def __dir__(cls):
            return list(super().__dir__()) + ["visible"]

        def __getattr__(cls, name):  # type: ignore[override]
            if name == "visible":
                return lambda: None
            raise AttributeError(name)

    class DynamicAttrs(metaclass=_Meta):
        """Test class."""

    result = agent_help(DynamicAttrs)
    assert "# DynamicAttrs" in result
    assert "visible" not in result


def test_agent_help_method_with_broken_signature():
    class BadSig:
        """Test class."""

        def method(self):
            """A method."""

    BadSig.method.__signature__ = "not a signature"  # type: ignore[assignment]

    result = agent_help(BadSig)
    assert "method" in result
    assert "(...)" in result


def test_agent_help_method_without_docstring():
    class NoDoc:
        """Test class."""

        def method(self):
            pass  # noqa: S1186

    result = agent_help(NoDoc)
    assert "method" in result


def test_agent_help_method_with_blank_only_docstring():
    class BlankDoc:
        """Test class."""

        def method(self):
            """x"""

    BlankDoc.method.__doc__ = "  \n  \n  "

    result = agent_help(BlankDoc)
    assert "method" in result


# -- Module support tests ----------------------------------------------------


def _make_module(name: str, doc: str | None = None) -> types.ModuleType:
    mod = types.ModuleType(name, doc)
    return mod


def test_agent_help_module_basic():
    mod = _make_module("mymod", "A test module.")
    result = agent_help(mod)
    assert "# mymod" in result
    assert "## Purpose" in result
    assert "A test module." in result
    assert "## Agent usage rules" in result


def test_agent_help_module_with_functions():
    mod = _make_module("mymod", "A module.")

    def greet(name: str) -> str:
        """Say hello."""
        return f"Hello, {name}"

    greet.__module__ = "mymod"
    mod.greet = greet  # type: ignore[attr-defined]
    result = agent_help(mod)
    assert "## Public API" in result
    assert "greet" in result
    assert "function" in result
    assert "Say hello." in result


def test_agent_help_module_with_classes():
    mod = _make_module("mymod", "A module.")

    class Foo:
        """A foo class."""

    Foo.__module__ = "mymod"
    mod.Foo = Foo  # type: ignore[attr-defined]
    result = agent_help(mod)
    assert "`Foo` class" in result
    assert "A foo class." in result


def test_agent_help_module_excludes_private():
    mod = _make_module("mymod")

    def _hidden():  # noqa: S1186
        pass

    mod._hidden = _hidden  # type: ignore[attr-defined]
    result = agent_help(mod)
    assert "_hidden" not in result


def test_agent_help_module_excludes_submodules():
    mod = _make_module("mymod")
    sub = _make_module("mymod.sub")
    mod.submod = sub  # type: ignore[attr-defined]
    result = agent_help(mod)
    assert "submod" not in result


def test_agent_help_module_custom_callable():
    mod = _make_module("mymod")

    def custom_help():
        return "Custom module help."

    mod.__agent_help__ = custom_help  # type: ignore[attr-defined]
    assert agent_help(mod) == "Custom module help."


def test_agent_help_module_custom_string():
    mod = _make_module("mymod")
    mod.__agent_help__ = "String module help."  # type: ignore[attr-defined]
    assert agent_help(mod) == "String module help."


def test_agent_help_module_no_doc():
    mod = _make_module("mymod")
    result = agent_help(mod)
    assert "# mymod" in result
    assert "## Purpose" not in result


def test_agent_help_module_exception_falls_back():
    mod = _make_module("mymod", "Fallback doc.")

    def bad_help():
        raise RuntimeError("boom")

    mod.__agent_help__ = bad_help  # type: ignore[attr-defined]
    result = agent_help(mod)
    assert "# mymod" in result
    assert "Fallback doc." in result


def test_agent_help_module_non_string_return():
    mod = _make_module("mymod")

    def custom_help():
        return 99

    mod.__agent_help__ = custom_help  # type: ignore[attr-defined]
    assert agent_help(mod) == "99"


def test_agent_help_module_invalid_attr_falls_back():
    """__agent_help__ that is neither callable nor string falls through to auto-doc."""
    mod = _make_module("mymod", "Fallback doc.")
    mod.__agent_help__ = 42  # type: ignore[attr-defined]
    result = agent_help(mod)
    assert "# mymod" in result
    assert "Fallback doc." in result
