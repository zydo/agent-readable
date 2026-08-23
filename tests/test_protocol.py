import enum
import functools
import types
import warnings

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
    def validate(config):
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


def test_agent_help_duck_typed_appends_notes():
    """Duck-typed __agent_help__ replaces the base; notes are still appended."""

    class DuckTyped:
        """A class with both duck-typed help and notes."""

        @classmethod
        def __agent_help__(cls) -> str:
            return "Duck-typed base."

        @classmethod
        def __agent_notes__(cls) -> str:
            return "Duck-typed rule."

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = agent_help(DuckTyped)
    assert result.startswith("Duck-typed base.")
    assert "## Notes from class DuckTyped" in result
    assert "Duck-typed rule." in result


def test_agent_help_custom_help_appends_inherited_notes():
    """Notes from a parent class survive a child's custom __agent_help__."""

    class NotesParent:
        @classmethod
        def __agent_notes__(cls) -> str:
            return "Parent rule."

    class CustomChild(NotesParent):
        """Custom child."""

        @classmethod
        def __agent_help__(cls) -> str:
            return "Child custom base."

    result = agent_help(CustomChild)
    assert result.startswith("Child custom base.")
    assert "## Notes from class NotesParent" in result
    assert "Parent rule." in result


def test_agent_help_mixin_notes_not_duplicated():
    """The mixin default already embeds notes; the append step must not repeat them."""
    result = agent_help(MixinWithNotes)
    assert result.count("## Notes from class MixinWithNotes") == 1


def test_agent_help_skips_notes_that_raise():
    """A raising __agent_notes__ is skipped, not fatal (like __agent_help__)."""

    class BoomNotes:
        """A class whose notes explode."""

        def ok(self):
            """Ok."""

        @classmethod
        def __agent_notes__(cls) -> str:
            raise RuntimeError("boom")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = agent_help(BoomNotes)
    assert "# BoomNotes" in result
    assert "ok" in result
    assert "## Notes from class BoomNotes" not in result


def test_agent_help_skips_parent_notes_that_raise():
    """One broken parent notes method must not take down help for subclasses."""

    class ParentBoom:
        @classmethod
        def __agent_notes__(cls) -> str:
            raise RuntimeError("parent boom")

    class ChildBoom(ParentBoom):
        """Child."""

        def go(self):
            """Go."""

    result = agent_help(ChildBoom)
    assert "# ChildBoom" in result
    assert "go" in result


def test_agent_help_keeps_child_notes_when_parent_notes_raise():
    """The leaf's own notes still render when a parent's notes raise."""

    class ParentBoom:
        @classmethod
        def __agent_notes__(cls) -> str:
            raise RuntimeError("parent boom")

    class ChildKept(ParentBoom):
        """Child."""

        @classmethod
        def __agent_notes__(cls) -> str:
            return "Child rule."

    result = agent_help(ChildKept)
    assert "## Notes from class ChildKept" in result
    assert "Child rule." in result


def test_agent_help_no_warning_for_mixin_with_notes():
    """The mixin default appends notes, so combining it with notes must not warn."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = agent_help(MixinWithNotes)
    assert "## Notes from class MixinWithNotes" in result


def test_agent_help_no_warning_for_duck_typed_without_notes():
    """A custom __agent_help__ with no notes has nothing to drop, so must not warn."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = agent_help(HasAgentDocButNotMixin)
    assert result == "Duck-typed agent doc."


def test_agent_help_no_warning_when_custom_help_raises():
    """If a custom __agent_help__ raises, we fall back to auto-doc (keeping notes)."""

    class BrokenHelp:
        """Custom help that raises, plus notes."""

        @classmethod
        def __agent_help__(cls) -> str:
            raise RuntimeError("boom")

        @classmethod
        def __agent_notes__(cls) -> str:
            return "Kept notes."

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = agent_help(BrokenHelp)
    assert "## Notes from class BrokenHelp" in result
    assert "Kept notes." in result


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


# -- Attributes, cached properties, enums -------------------------------------


def test_agent_help_includes_public_constants():
    class WithConstants:
        """Test class."""

        MAX_RETRIES = 5
        LABEL = "v1"
        ENABLED = True
        NOTHING = None

    result = agent_help(WithConstants)
    assert "`MAX_RETRIES` attribute: 5" in result
    assert "`LABEL` attribute: 'v1'" in result
    assert "`ENABLED` attribute: True" in result
    assert "`NOTHING` attribute: None" in result


def test_agent_help_attribute_without_safe_repr_shows_type_name():
    class Guard:
        pass

    class WithObject:
        """Test class."""

        guard = Guard()

    result = agent_help(WithObject)
    assert "`guard` attribute: Guard" in result


def test_agent_help_does_not_execute_custom_repr():
    """Only exact primitive types are repr'd; subclasses never run __repr__."""

    class EvilStr(str):
        def __repr__(self):
            raise AssertionError("custom repr must not run")

    class WithEvil:
        """Test class."""

        value = EvilStr("x")

    result = agent_help(WithEvil)
    assert "`value` attribute: EvilStr" in result


def test_agent_help_truncates_long_attribute_repr():
    class WithLong:
        """Test class."""

        TEXT = "x" * 100

    result = agent_help(WithLong)
    assert "…" in result
    assert "x" * 60 not in result


def test_agent_help_includes_cached_property():
    class WithCached:
        """Test class."""

        @functools.cached_property
        def cached(self) -> int:
            """A cached value."""
            return 1

    result = agent_help(WithCached)
    assert "`cached` property: A cached value." in result


def test_agent_help_enum_lists_members_without_metaclass_constructor():
    class Color(enum.Enum):
        """Colors."""

        RED = 1
        GREEN = "green"

    result = agent_help(Color)
    assert "## Constructor" not in result
    assert "names=None" not in result
    assert "`RED` member: 1" in result
    assert "`GREEN` member: 'green'" in result
    # Per-member accessors are not class-level API.
    assert "`name`" not in result
    assert "`value`" not in result


def test_agent_help_enum_member_with_non_primitive_value():
    class Flags(enum.Enum):
        """Flags."""

        CONFIG = ("a", "b")

    result = agent_help(Flags)
    assert "`CONFIG` member" in result
    assert "`CONFIG` member:" not in result


def test_agent_help_constructor_falls_back_behind_metaclass_call():
    """A metaclass __call__ masks the real signature; __init__ recovers it."""

    class Meta(type):
        def __call__(cls, *args, **kwargs):
            return super().__call__(*args, **kwargs)

    class Config(metaclass=Meta):
        """Config."""

        def __init__(self, path: str, retries: int = 3):
            """Initialize."""

    result = agent_help(Config)
    assert "Config(path: str, retries: int = 3)" in result
    assert "Config(*args, **kwargs)" not in result


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
    # typing.Callable renders without a module prefix; collections.abc.Callable
    # would render as "collections.abc.Callable", which this test asserts against.
    from typing import Callable  # noqa: UP035

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


def test_agent_help_method_positional_only_self_drops_slash():
    """Regression: a positional-only ``self`` must not leave a dangling ``/``."""

    class PosOnlySelf:
        """Test class."""

        def backup(self, /, target, *, pages=-1):
            """Back up to target."""

    result = agent_help(PosOnlySelf)
    assert "`backup(target, *, pages=-1)`" in result
    assert "(/, target" not in result


def test_agent_help_method_keeps_remaining_positional_only():
    """A positional-only marker is kept when a positional-only param remains."""

    class KeepsSlash:
        """Test class."""

        def at(self, index, /, default=None):
            """Look up by index."""

    result = agent_help(KeepsSlash)
    assert "`at(index, /, default=None)`" in result


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
            return [*super().__dir__(), "visible"]

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

    BadSig.method.__signature__ = "not a signature"  # type: ignore[attr-defined, assignment]

    result = agent_help(BadSig)
    assert "method" in result
    assert "(...)" in result


def test_agent_help_staticmethod_with_broken_signature():
    """Staticmethods route through _safe_signature; bad signatures fall back."""

    class BadStaticSig:
        """Test class."""

        @staticmethod
        def helper():
            """A static helper."""

    BadStaticSig.helper.__signature__ = "not a signature"  # type: ignore[attr-defined]

    result = agent_help(BadStaticSig)
    assert "helper" in result
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


def test_agent_help_module_all_includes_reexported_symbol():
    """__all__ is authoritative: a symbol re-exported from another module shows."""
    mod = _make_module("mymod", "A module.")

    class Foo:
        """A re-exported class."""

    Foo.__module__ = "external_lib"  # simulate `from external_lib import Foo`
    mod.Foo = Foo  # type: ignore[attr-defined]
    mod.__all__ = ["Foo"]  # type: ignore[attr-defined]

    result = agent_help(mod)
    assert "`Foo` class" in result
    assert "A re-exported class." in result


def test_agent_help_module_all_restricts_to_listed_names():
    """When __all__ is defined, public members not listed are excluded."""
    mod = _make_module("mymod", "A module.")

    def shown(x: int) -> int:
        """Shown function."""
        return x

    def hidden():
        """Hidden function."""

    shown.__module__ = "mymod"
    hidden.__module__ = "mymod"
    mod.shown = shown  # type: ignore[attr-defined]
    mod.hidden = hidden  # type: ignore[attr-defined]
    mod.__all__ = ["shown"]  # type: ignore[attr-defined]

    result = agent_help(mod)
    assert "shown" in result
    assert "hidden" not in result


def test_agent_help_module_all_skips_missing_names():
    """Names in __all__ that don't resolve are skipped, not raised."""
    mod = _make_module("mymod", "A module.")

    class Real:
        """Real class."""

    Real.__module__ = "mymod"
    mod.Real = Real  # type: ignore[attr-defined]
    mod.__all__ = ["Real", "does_not_exist"]  # type: ignore[attr-defined]

    result = agent_help(mod)
    assert "`Real` class" in result
    assert "does_not_exist" not in result


def test_agent_help_module_all_ignores_non_string_entries():
    """Non-string entries in __all__ are skipped without error."""
    mod = _make_module("mymod", "A module.")

    class Real:
        """Real class."""

    Real.__module__ = "mymod"
    mod.Real = Real  # type: ignore[attr-defined]
    mod.__all__ = ["Real", 123]  # type: ignore[attr-defined,list-item]

    result = agent_help(mod)
    assert "`Real` class" in result


def test_agent_help_module_heuristic_excludes_foreign_symbol():
    """Without __all__, symbols defined in another module are filtered out."""
    mod = _make_module("mymod", "A module.")

    class Foreign:
        """Imported from elsewhere."""

    Foreign.__module__ = "other_lib"
    mod.Foreign = Foreign  # type: ignore[attr-defined]

    result = agent_help(mod)
    assert "Foreign" not in result


def test_agent_help_module_includes_constants():
    """Module-level constants pass the origin filter (their __module__ is the
    type's, not the binding's) and show with their repr."""
    mod = _make_module("mymod", "A module.")
    mod.PI = 3.25  # type: ignore[attr-defined]
    mod.NAME = "mymod-name"  # type: ignore[attr-defined]

    result = agent_help(mod)
    assert "`PI` attribute: 3.25" in result
    assert "`NAME` attribute: 'mymod-name'" in result


def test_agent_help_module_all_includes_constant():
    mod = _make_module("mymod", "A module.")
    mod.LIMIT = 7  # type: ignore[attr-defined]
    mod.__all__ = ["LIMIT"]  # type: ignore[attr-defined]

    result = agent_help(mod)
    assert "`LIMIT` attribute: 7" in result


def test_agent_help_module_includes_builtin_functions():
    """C builtins (isfunction is False for them) are part of a module's API."""
    mod = _make_module("mymod", "A module.")
    mod.sizeof = len  # type: ignore[attr-defined]
    mod.__all__ = ["sizeof"]  # type: ignore[attr-defined]

    result = agent_help(mod)
    assert "`sizeof(obj, /)` function" in result
    assert "Return the number of items" in result


def test_agent_help_math_module_lists_c_functions_and_constants():
    """Integration: the stdlib C module math shows its functions and constants."""
    import math

    result = agent_help(math)
    assert "`sin(" in result
    assert "`pi` attribute" in result


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


# -- Function / method tests -------------------------------------------------


def test_agent_help_function_basic():
    def greet(name: str) -> str:
        """Say hello to someone."""
        return f"Hello, {name}"

    result = agent_help(greet)
    assert result.startswith("#") and "greet" in result.splitlines()[0]
    assert "## Signature" in result
    assert "greet(name: str) -> str" in result
    assert "## Purpose" in result
    assert "Say hello to someone." in result
    assert "## Agent usage rules" in result


def test_agent_help_unbound_method_keeps_self():
    class Pool:
        def rotated(self, n: int) -> "Pool":
            """Rotate the pool by n positions."""
            return self

    result = agent_help(Pool.rotated)
    assert "Pool.rotated" in result.splitlines()[0]
    assert "rotated(self, n: int)" in result
    assert "Rotate the pool by n positions." in result


def test_agent_help_bound_method_strips_self():
    class Pool:
        def rotated(self, n: int) -> "Pool":
            """Rotate the pool by n positions."""
            return self

    result = agent_help(Pool().rotated)
    assert "rotated(n: int)" in result
    assert "self" not in result.split("## Signature", 1)[1].split("##", 1)[0]


def test_agent_help_classmethod_strips_cls():
    class Pool:
        @classmethod
        def of(cls, n: int) -> "Pool":
            """Construct a pool of size n."""
            return cls()

    result = agent_help(Pool.of)
    assert "of(n: int)" in result
    assert "Construct a pool of size n." in result


def test_agent_help_function_without_docstring():
    def f(x: int) -> int:
        return x

    result = agent_help(f)
    assert result.startswith("#") and "f" in result.splitlines()[0]
    assert "## Purpose" not in result
    assert "## Agent usage rules" in result


def test_agent_help_function_custom_callable_override():
    def f():
        """Auto doc."""

    f.__agent_help__ = lambda: "Custom function help."  # type: ignore[attr-defined]
    assert agent_help(f) == "Custom function help."


def test_agent_help_function_custom_string_override():
    def f():
        """Auto doc."""

    f.__agent_help__ = "String function help."  # type: ignore[attr-defined]
    assert agent_help(f) == "String function help."


def test_agent_help_function_non_string_return():
    def f():
        """Auto doc."""

    f.__agent_help__ = lambda: 99  # type: ignore[attr-defined]
    assert agent_help(f) == "99"


def test_agent_help_function_override_exception_falls_back():
    def f():
        """Fallback doc."""

    def boom():
        raise RuntimeError("boom")

    f.__agent_help__ = boom  # type: ignore[attr-defined]
    result = agent_help(f)
    assert "Fallback doc." in result
    assert "## Signature" in result


def test_agent_help_builtin_function():
    result = agent_help(len)
    assert "# len" in result
    assert "## Signature" in result
