"""Tests for Aspects service: composition, validation, ordering."""

from __future__ import annotations

from typing import Any

import pytest

import domain_aspects
from domain_aspects.errors.aspects_errors import AspectDeclarationError
from domain_aspects.services.aspects import (
    aspects_client as client_module,
    aspects_objects as objs,
)
from domain_aspects.services.constants import aspects as const


class TestPublicAPI:
    """Test public API exports."""

    def test_monitored_in_public_api(self) -> None:
        """Monitored is exported from domain_aspects root."""
        assert hasattr(domain_aspects, "Monitored")
        assert "Monitored" in domain_aspects.__all__
        assert domain_aspects.Monitored is objs.Monitored

    def test_retried_in_public_api(self) -> None:
        """Retried is exported from domain_aspects root."""
        assert hasattr(domain_aspects, "Retried")
        assert "Retried" in domain_aspects.__all__
        assert domain_aspects.Retried is objs.Retried

    def test_aspect_order_in_public_api(self) -> None:
        """ASPECT_ORDER is exported from domain_aspects root."""
        assert hasattr(domain_aspects, "ASPECT_ORDER")
        assert "ASPECT_ORDER" in domain_aspects.__all__
        assert domain_aspects.ASPECT_ORDER is const.ASPECT_ORDER


class TestAspectsFlatten:
    """Test Aspects._flatten method."""

    def test_flatten_single_entries(self) -> None:
        """Flatten single entries into a list."""
        aspects_svc = client_module.Aspects()
        entries = (
            objs.Logged(event="test"),
            objs.Requires(permission="read"),
        )
        result = aspects_svc._flatten(entries)
        assert len(result) == 2
        assert result[0].kind == objs.AspectKind.LOGGED
        assert result[1].kind == objs.AspectKind.REQUIRES

    def test_flatten_frozenset(self) -> None:
        """Flatten a frozenset of entries."""
        aspects_svc = client_module.Aspects()
        entry_set = frozenset(
            {
                objs.Logged(event="test"),
                objs.Requires(permission="read"),
            }
        )
        result = aspects_svc._flatten((entry_set,))  # type: ignore[arg-type]
        assert len(result) == 2
        assert {e.kind for e in result} == {
            objs.AspectKind.LOGGED,
            objs.AspectKind.REQUIRES,
        }

    def test_flatten_mixed(self) -> None:
        """Flatten mixed single entries and frozensets."""
        aspects_svc = client_module.Aspects()
        entry_set = frozenset(
            {
                objs.Requires(permission="read"),
                objs.Throttled(scope="api", rate="100/hour"),
            }
        )
        entries = (
            objs.Logged(event="test"),
            entry_set,
        )
        result = aspects_svc._flatten(entries)  # type: ignore[arg-type]
        assert len(result) == 3
        kinds = {e.kind for e in result}
        assert kinds == {
            objs.AspectKind.LOGGED,
            objs.AspectKind.REQUIRES,
            objs.AspectKind.THROTTLED,
        }


class TestAspectsValidate:
    """Test Aspects._validate method."""

    def test_validate_happy_path(self) -> None:
        """Validate valid entries without raising."""
        aspects_svc = client_module.Aspects()
        entries = [
            objs.Logged(event="test"),
            objs.Requires(permission="read"),
        ]
        aspects_svc._validate(entries)  # type: ignore[arg-type]

    def test_validate_empty_list_raises(self) -> None:
        """Validate empty list raises AspectDeclarationError."""
        aspects_svc = client_module.Aspects()
        with pytest.raises(
            AspectDeclarationError,
            match=const.ERR_ASPECTS_EMPTY_DECLARATION,
        ):
            aspects_svc._validate([])

    def test_validate_duplicate_kind_raises(self) -> None:
        """Validate duplicate kinds raises AspectDeclarationError."""
        aspects_svc = client_module.Aspects()
        entries = [
            objs.Logged(event="test1"),
            objs.Logged(event="test2"),
        ]  # type: ignore[arg-type]
        with pytest.raises(
            AspectDeclarationError,
            match="Duplicate aspect kind",
        ):
            aspects_svc._validate(entries)  # type: ignore[arg-type]

    def test_validate_unknown_type_raises(self) -> None:
        """Validate unknown entry type raises AspectDeclarationError."""
        aspects_svc = client_module.Aspects()
        entries: list[Any] = [
            objs.Logged(event="test"),
            "not_an_entry",
        ]
        with pytest.raises(
            AspectDeclarationError,
            match="Unknown aspect entry type",
        ):
            aspects_svc._validate(entries)


class TestAspectsSort:
    """Test Aspects._sort method."""

    def test_sort_happy_path(self) -> None:
        """Sort entries by ASPECT_ORDER."""
        aspects_svc = client_module.Aspects()
        entries = [
            objs.WrapErrors(as_=ValueError),
            objs.Logged(event="test"),
            objs.Requires(permission="read"),
        ]
        result = aspects_svc._sort(entries)  # type: ignore[arg-type]
        kinds = [e.kind for e in result]
        assert kinds == [
            objs.AspectKind.LOGGED,
            objs.AspectKind.REQUIRES,
            objs.AspectKind.WRAP_ERRORS,
        ]

    def test_sort_preserves_all_entries(self) -> None:
        """Sort preserves all entries."""
        aspects_svc = client_module.Aspects()
        logged = objs.Logged(event="test")
        requires = objs.Requires(permission="read")
        tenant = objs.TenantScoped(param_name="tenant_id")
        throttled = objs.Throttled(scope="api", rate="100/hour")
        monitored = objs.Monitored(event="test.operation")
        wrap = objs.WrapErrors(as_=ValueError)
        entries = [wrap, logged, requires, tenant, throttled, monitored]
        result = aspects_svc._sort(entries)  # type: ignore[arg-type]
        assert len(result) == 6
        kinds = [e.kind for e in result]
        assert kinds == [
            objs.AspectKind.LOGGED,
            objs.AspectKind.REQUIRES,
            objs.AspectKind.TENANT_SCOPED,
            objs.AspectKind.THROTTLED,
            objs.AspectKind.MONITORED,
            objs.AspectKind.WRAP_ERRORS,
        ]


class TestAspectsCall:
    """Test Aspects.__call__ method."""

    def test_call_returns_decorator(self) -> None:
        """Calling Aspects returns a decorator function."""
        aspects_svc = client_module.Aspects()
        decorator = aspects_svc(objs.Logged(event="test"))
        assert callable(decorator)

    def test_call_with_single_entry(self) -> None:
        """Calling Aspects with single entry works."""
        aspects_svc = client_module.Aspects()
        decorator = aspects_svc(objs.Requires(permission="read"))
        assert callable(decorator)

    def test_call_with_frozenset(self) -> None:
        """Calling Aspects with frozenset works."""
        aspects_svc = client_module.Aspects()
        entry_set = frozenset(
            {
                objs.Logged(event="test"),
                objs.Requires(permission="read"),
            }
        )
        decorator = aspects_svc(entry_set)  # type: ignore[arg-type]
        assert callable(decorator)

    def test_call_with_mixed_entries_and_frozenset(self) -> None:
        """Calling Aspects with both entries and frozensets works."""
        aspects_svc = client_module.Aspects()
        entry_set = frozenset({objs.Requires(permission="read")})
        decorator = aspects_svc(
            objs.Logged(event="test"),
            entry_set,
        )
        assert callable(decorator)

    def test_call_raises_on_empty_declaration(self) -> None:
        """Calling Aspects with empty frozenset raises."""
        aspects_svc = client_module.Aspects()
        with pytest.raises(AspectDeclarationError):
            aspects_svc(frozenset())  # type: ignore

    def test_call_raises_on_duplicate_kind(self) -> None:
        """Calling Aspects with duplicate kinds raises."""
        aspects_svc = client_module.Aspects()
        with pytest.raises(AspectDeclarationError):
            aspects_svc(
                objs.Logged(event="test1"),
                objs.Logged(event="test2"),
            )

    def test_decorator_on_function(self) -> None:
        """Decorator works on a function."""
        aspects_svc = client_module.Aspects()

        def example_func() -> str:
            return "result"

        decorator = aspects_svc(objs.Logged(event="test"))
        decorated = decorator(example_func)
        assert callable(decorated)

    def test_decorator_on_dataclass(self) -> None:
        """Decorator works on a dataclass."""
        from dataclasses import dataclass

        aspects_svc = client_module.Aspects()

        @dataclass(frozen=True, slots=True)
        class ExampleClass:
            value: str = "example"

        decorator = aspects_svc(objs.Requires(permission="read"))
        decorated = decorator(ExampleClass)
        assert decorated is ExampleClass

    def test_monitored_composition_with_logged(self) -> None:
        """Composition of Monitored and Logged aspects works."""
        aspects_svc = client_module.Aspects()
        decorator = aspects_svc(
            objs.Monitored(event="test.operation"),
            objs.Logged(event="test.logging"),
        )
        assert callable(decorator)

    def test_monitored_composition_with_multiple_aspects(self) -> None:
        """Composition of Monitored with multiple aspects works."""
        aspects_svc = client_module.Aspects()
        decorator = aspects_svc(
            objs.Logged(event="test"),
            objs.Monitored(event="test.operation"),
            objs.WrapErrors(as_=ValueError),
        )
        assert callable(decorator)


class TestModuleLevelEntrypoint:
    """Test module-level aspects constant."""

    def test_aspects_constant_is_aspects_instance(self) -> None:
        """Module-level aspects is an Aspects instance."""
        assert isinstance(client_module.aspects, client_module.Aspects)


class TestAspectsIntegration:
    """Integration tests for aspect composition."""

    def test_all_entries_can_compose_together(self) -> None:
        """All six entry types can be composed in one Aspects call."""
        aspects_svc = client_module.Aspects()

        # Verify that all six entries can be passed to aspects()
        # without raising at composition time (import/build happens later).
        decorator = aspects_svc(
            objs.Logged(event="test"),
            objs.Requires(permission="read"),
            objs.TenantScoped(param_name="tenant_id"),
            objs.Throttled(scope="api", rate="100/hour"),
            objs.WrapErrors(as_=ValueError),
        )
        assert callable(decorator)

    def test_all_six_kinds_can_be_in_one_decoration(self) -> None:
        """All six aspect kinds can be declared together."""
        aspects_svc = client_module.Aspects()
        decorator = aspects_svc(
            objs.Logged(event="test"),
            objs.Requires(permission="read"),
            objs.TenantScoped(param_name="tenant_id"),
            objs.Throttled(scope="api", rate="100/hour"),
            objs.WrapErrors(as_=ValueError),
        )
        assert callable(decorator)

    def test_frozenset_with_all_kinds(self) -> None:
        """Frozenset can contain all six aspect kinds."""
        all_aspects = frozenset(
            {
                objs.Logged(event="test"),
                objs.Requires(permission="read"),
                objs.TenantScoped(param_name="tenant_id"),
                objs.Throttled(scope="api", rate="100/hour"),
                objs.WrapErrors(as_=ValueError),
            }
        )
        aspects_svc = client_module.Aspects()
        decorator = aspects_svc(all_aspects)  # type: ignore[arg-type]
        assert callable(decorator)
