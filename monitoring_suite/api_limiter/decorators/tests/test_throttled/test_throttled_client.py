"""Tests for the throttled decorator."""

from __future__ import annotations

import re

import pytest

from monitoring_suite.api_limiter.decorators.throttled.throttled_client import throttled
from monitoring_suite.api_limiter.errors.api_limiter_errors import ThrottleDeclarationError
from monitoring_suite.api_limiter.services.constants import policy as const
from monitoring_suite.api_limiter.services.policy.policy_objects import Period, ThrottlePolicy


class TestThrottledDecoratorIdentityContract:
    """Throttled decorator does not wrap the function."""

    def test_decorator_returns_original_function_object(self) -> None:
        """Throttled decorator returns the exact same function object."""

        def my_function() -> None:
            pass

        original_id = id(my_function)
        decorated = throttled(scope="test", rate="100/hour")(my_function)

        assert id(decorated) == original_id
        assert decorated is my_function

    def test_decorator_preserves_function_identity_with_args(self) -> None:
        """Throttled decorator preserves identity for functions with arguments."""

        def add(a: int, b: int) -> int:
            return a + b

        original_id = id(add)
        decorated = throttled(scope="math.add", rate="1000/second")(add)

        assert id(decorated) == original_id
        assert decorated is add
        assert decorated(2, 3) == 5

    def test_decorator_preserves_return_value(self) -> None:
        """Throttled decorator does not affect function behavior."""

        def get_value() -> str:
            return "test_value"

        decorated = throttled(scope="test", rate="100/hour")(get_value)
        result = decorated()
        assert result == "test_value"

    def test_decorator_preserves_function_name(self) -> None:
        """Throttled decorator preserves function __name__."""

        def original_name() -> None:
            pass

        decorated = throttled(scope="test", rate="100/hour")(original_name)
        assert decorated.__name__ == "original_name"

    def test_decorator_preserves_function_docstring(self) -> None:
        """Throttled decorator preserves function docstring."""

        def documented_func() -> None:
            """This is the docstring."""
            pass

        decorated = throttled(scope="test", rate="100/hour")(documented_func)
        assert decorated.__doc__ == "This is the docstring."


class TestThrottledDecoratorPolicyAttachment:
    """Throttled decorator attaches a throttle policy."""

    def test_policy_attached_to_function(self) -> None:
        """Throttled decorator attaches const.THROTTLE_POLICY_ATTR attribute."""

        def my_function() -> None:
            pass

        decorated = throttled(scope="test.scope", rate="100/hour")(my_function)
        policy = getattr(decorated, const.THROTTLE_POLICY_ATTR, None)

        assert policy is not None
        assert isinstance(policy, ThrottlePolicy)

    def test_policy_has_correct_scope(self) -> None:
        """Throttled decorator attaches policy with correct scope."""

        def my_function() -> None:
            pass

        decorated = throttled(scope="api.users.list", rate="100/hour")(my_function)
        policy = getattr(decorated, const.THROTTLE_POLICY_ATTR)

        assert policy.scope == "api.users.list"

    def test_policy_has_correct_rate(self) -> None:
        """Throttled decorator attaches policy with correct rate."""

        def my_function() -> None:
            pass

        decorated = throttled(scope="test", rate="250/minute")(my_function)
        policy = getattr(decorated, const.THROTTLE_POLICY_ATTR)

        assert policy.rate.requests == 250
        assert policy.rate.period == Period.MINUTE

    def test_policy_no_tiers_by_default(self) -> None:
        """Throttled decorator creates policy with empty tier_rates."""

        def my_function() -> None:
            pass

        decorated = throttled(scope="test", rate="100/hour")(my_function)
        policy = getattr(decorated, const.THROTTLE_POLICY_ATTR)

        assert policy.tier_rates == ()
        assert policy.has_tiers is False

    def test_policy_readable_via_attribute(self) -> None:
        """Throttled decorator policy is accessible via const.THROTTLE_POLICY_ATTR."""

        def my_function() -> None:
            pass

        decorated = throttled(scope="test.endpoint", rate="50/second")(my_function)
        policy = getattr(decorated, const.THROTTLE_POLICY_ATTR)  # type: ignore

        assert isinstance(policy, ThrottlePolicy)
        assert policy.scope == "test.endpoint"


class TestThrottledDecoratorWithTiers:
    """Throttled decorator handles tier rate mappings."""

    def test_decorator_with_single_tier(self) -> None:
        """Throttled decorator accepts single tier override."""

        def my_function() -> None:
            pass

        tiers = {"premium": "500/hour"}
        decorated = throttled(scope="test", rate="100/hour", tiers=tiers)(my_function)
        policy = getattr(decorated, const.THROTTLE_POLICY_ATTR)

        assert len(policy.tier_rates) == 1
        assert policy.tier_rates[0].tier == "premium"
        assert policy.tier_rates[0].rate.requests == 500
        assert policy.tier_rates[0].rate.period == Period.HOUR

    def test_decorator_with_multiple_tiers(self) -> None:
        """Throttled decorator accepts multiple tier overrides."""

        def my_function() -> None:
            pass

        tiers = {"premium": "500/hour", "enterprise": "5000/hour"}
        decorated = throttled(scope="test", rate="100/hour", tiers=tiers)(my_function)
        policy = getattr(decorated, const.THROTTLE_POLICY_ATTR)

        assert len(policy.tier_rates) == 2

    def test_decorator_with_none_tiers(self) -> None:
        """Throttled decorator converts None tiers to empty tuple."""

        def my_function() -> None:
            pass

        decorated = throttled(scope="test", rate="100/hour", tiers=None)(my_function)
        policy = getattr(decorated, const.THROTTLE_POLICY_ATTR)

        assert policy.tier_rates == ()

    def test_decorator_builds_tier_rates_correctly(self) -> None:
        """Throttled decorator builds TierRate objects from mapping."""

        def my_function() -> None:
            pass

        tiers = {"basic": "100/hour", "pro": "1000/hour"}
        decorated = throttled(scope="api.data", rate="10/hour", tiers=tiers)(my_function)
        policy = getattr(decorated, const.THROTTLE_POLICY_ATTR)

        tier_dict = {tr.tier: tr.rate.requests for tr in policy.tier_rates}
        assert tier_dict["basic"] == 100
        assert tier_dict["pro"] == 1000


class TestThrottledDecoratorValidation:
    """Throttled decorator validates at decoration time."""

    def test_invalid_rate_raises_at_decoration(self) -> None:
        """Throttled decorator raises on invalid rate format."""

        def my_function() -> None:
            pass

        match = re.escape(const.ERR_POLICY_RATE_FORMAT)
        with pytest.raises(ThrottleDeclarationError, match=match):
            throttled(scope="test", rate="invalid")(my_function)

    def test_unknown_period_raises_at_decoration(self) -> None:
        """Throttled decorator raises on unknown period."""

        def my_function() -> None:
            pass

        match = re.escape(const.ERR_POLICY_UNKNOWN_PERIOD)
        with pytest.raises(ThrottleDeclarationError, match=match):
            throttled(scope="test", rate="100/week")(my_function)

    def test_zero_rate_raises_at_decoration(self) -> None:
        """Throttled decorator raises on zero request count."""

        def my_function() -> None:
            pass

        match = re.escape(const.ERR_POLICY_REQUESTS_NOT_POSITIVE)
        with pytest.raises(ThrottleDeclarationError, match=match):
            throttled(scope="test", rate="0/hour")(my_function)

    def test_invalid_tier_rate_raises_at_decoration(self) -> None:
        """Throttled decorator raises on invalid tier rate format."""

        def my_function() -> None:
            pass

        match = re.escape(const.ERR_POLICY_RATE_FORMAT)
        with pytest.raises(ThrottleDeclarationError, match=match):
            throttled(scope="test", rate="100/hour", tiers={"premium": "bad_rate"})(my_function)

    def test_empty_scope_raises_at_decoration(self) -> None:
        """Throttled decorator raises on empty scope."""

        def my_function() -> None:
            pass

        match = re.escape(const.ERR_POLICY_EMPTY_SCOPE)
        with pytest.raises(ThrottleDeclarationError, match=match):
            throttled(scope="", rate="100/hour")(my_function)

    def test_all_tier_rate_periods_validated(self) -> None:
        """Throttled decorator validates all tier rates at decoration."""

        def my_function() -> None:
            pass

        tiers = {"premium": "100/second", "enterprise": "1000/minute"}

        decorated = throttled(scope="test", rate="100/hour", tiers=tiers)(my_function)
        policy = getattr(decorated, const.THROTTLE_POLICY_ATTR)

        assert len(policy.tier_rates) == 2

    def test_empty_tier_label_raises_at_decoration(self) -> None:
        """Throttled decorator raises on empty tier label."""

        def my_function() -> None:
            pass

        tiers = {"": "500/hour"}

        match = re.escape(const.ERR_POLICY_EMPTY_TIER)
        with pytest.raises(ThrottleDeclarationError, match=match):
            throttled(scope="test", rate="100/hour", tiers=tiers)(my_function)


class TestThrottledModuleHandle:
    """The throttled module handle is usable directly."""

    def test_throttled_module_handle_is_callable(self) -> None:
        """The throttled module object is callable as a decorator."""

        def my_function() -> None:
            pass

        decorated = throttled(scope="test", rate="100/hour")(my_function)
        assert decorated is my_function

    def test_throttled_handle_can_be_used_multiple_times(self) -> None:
        """The throttled module handle can decorate multiple functions."""

        def func1() -> None:
            pass

        def func2() -> None:
            pass

        decorated1 = throttled(scope="scope1", rate="100/hour")(func1)
        decorated2 = throttled(scope="scope2", rate="200/hour")(func2)

        policy1 = getattr(decorated1, const.THROTTLE_POLICY_ATTR)
        policy2 = getattr(decorated2, const.THROTTLE_POLICY_ATTR)

        assert policy1.scope == "scope1"
        assert policy2.scope == "scope2"
        assert policy1.rate.requests == 100
        assert policy2.rate.requests == 200


class TestThrottledMultipleDecorations:
    """Multiple decorations on different methods are independent."""

    def test_multiple_decorations_on_class_methods(self) -> None:
        """Multiple method decorations create independent policies."""

        class MyClass:
            @throttled(scope="method1", rate="100/hour")
            def method1(self) -> None:
                pass

            @throttled(scope="method2", rate="200/hour")
            def method2(self) -> None:
                pass

        policy1 = getattr(MyClass.method1, const.THROTTLE_POLICY_ATTR)
        policy2 = getattr(MyClass.method2, const.THROTTLE_POLICY_ATTR)

        assert policy1.scope == "method1"
        assert policy2.scope == "method2"
        assert policy1.rate.requests == 100
        assert policy2.rate.requests == 200

    def test_multiple_decorations_on_functions(self) -> None:
        """Multiple function decorations create independent policies."""

        @throttled(scope="first", rate="100/hour")
        def first_func() -> None:
            pass

        @throttled(scope="second", rate="200/hour")
        def second_func() -> None:
            pass

        policy1 = getattr(first_func, const.THROTTLE_POLICY_ATTR)
        policy2 = getattr(second_func, const.THROTTLE_POLICY_ATTR)

        assert policy1.scope == "first"
        assert policy2.scope == "second"

    def test_decorated_methods_maintain_individual_policies(self) -> None:
        """Decorated methods in a class maintain individual policies."""

        class Service:
            @throttled(scope="list", rate="1000/hour")
            def list_items(self) -> list[str]:
                return []

            @throttled(scope="create", rate="100/hour")
            def create_item(self, name: str) -> str:
                return name

            @throttled(scope="delete", rate="50/hour")
            def delete_item(self, item_id: int) -> bool:
                return True

        service = Service()

        policy_list = getattr(Service.list_items, const.THROTTLE_POLICY_ATTR)
        policy_create = getattr(Service.create_item, const.THROTTLE_POLICY_ATTR)
        policy_delete = getattr(Service.delete_item, const.THROTTLE_POLICY_ATTR)

        assert policy_list.scope == "list"
        assert policy_create.scope == "create"
        assert policy_delete.scope == "delete"

        assert service.list_items() == []
        assert service.create_item("test") == "test"
        assert service.delete_item(1) is True


class TestThrottledComplexScenarios:
    """Complex decoration scenarios work correctly."""

    def test_decoration_with_all_parameters(self) -> None:
        """Throttled decorator works with all parameters."""

        def complex_func(x: int, y: str) -> tuple[int, str]:
            return x, y

        tiers = {"free": "100/day", "premium": "10000/day", "enterprise": "unlimited_practically"}

        match = re.escape(const.ERR_POLICY_RATE_FORMAT)
        with pytest.raises(ThrottleDeclarationError, match=match):
            throttled(scope="api.complex", rate="1000/hour", tiers=tiers)(complex_func)

    def test_valid_complex_decoration(self) -> None:
        """Throttled decorator works with all valid parameters."""

        def complex_func(x: int, y: str) -> tuple[int, str]:
            return x, y

        tiers = {"free": "100/day", "premium": "10000/day", "enterprise": "100000/day"}

        decorated = throttled(scope="api.complex", rate="1000/hour", tiers=tiers)(complex_func)

        policy = getattr(decorated, const.THROTTLE_POLICY_ATTR)

        assert policy.scope == "api.complex"
        assert policy.rate.requests == 1000
        assert policy.rate.period == Period.HOUR
        assert len(policy.tier_rates) == 3
        assert policy.has_tiers is True

        assert decorated(42, "test") == (42, "test")

    def test_decoration_stacking_on_same_function(self) -> None:
        """Last decoration wins when applied multiple times."""

        def my_func() -> None:
            pass

        decorated1 = throttled(scope="first", rate="100/hour")(my_func)
        decorated2 = throttled(scope="second", rate="200/hour")(decorated1)

        policy = getattr(decorated2, const.THROTTLE_POLICY_ATTR)
        assert policy.scope == "second"
        assert policy.rate.requests == 200

    def test_tier_rates_all_periods(self) -> None:
        """Tiers with different periods are handled correctly."""

        def my_func() -> None:
            pass

        tiers = {
            "per_second": "10/second", "per_minute": "600/minute", "per_hour": "36000/hour", "per_day": "864000/day"
        }

        decorated = throttled(scope="multi_period", rate="1/second", tiers=tiers)(my_func)

        policy = getattr(decorated, const.THROTTLE_POLICY_ATTR)
        assert len(policy.tier_rates) == 4

        assert policy.rate_for("per_second").period == Period.SECOND
        assert policy.rate_for("per_minute").period == Period.MINUTE
        assert policy.rate_for("per_hour").period == Period.HOUR
        assert policy.rate_for("per_day").period == Period.DAY


class TestThrottledClassLevelDecoration:
    """Class-level @throttled decorator fans out policies to methods."""

    def test_class_decoration_returns_class_unchanged(self) -> None:
        """Class-level @throttled returns the class object unchanged."""

        @throttled(scope="docs", rate="100/hour")
        class DocumentService:
            def list_documents(self) -> list[str]:
                return []

        assert isinstance(DocumentService, type)
        assert DocumentService.__name__ == "DocumentService"

    def test_class_decoration_fans_out_to_methods(self) -> None:
        """Class-level @throttled attaches policy to each public method."""

        @throttled(scope="docs", rate="100/hour")
        class DocumentService:
            def list_documents(self) -> list[str]:
                return []

            def create_document(self, name: str) -> str:
                return name

        list_policy = getattr(DocumentService.list_documents, const.THROTTLE_POLICY_ATTR)
        create_policy = getattr(DocumentService.create_document, const.THROTTLE_POLICY_ATTR)

        assert list_policy is not None
        assert create_policy is not None

    def test_class_decoration_derives_scope_with_colon_separator(self) -> None:
        """Class-level @throttled derives scopes as root:method_name."""

        @throttled(scope="docs", rate="100/hour")
        class DocumentService:
            def list_documents(self) -> list[str]:
                return []

            def create_document(self, name: str) -> str:
                return name

        list_policy = getattr(DocumentService.list_documents, const.THROTTLE_POLICY_ATTR)
        create_policy = getattr(DocumentService.create_document, const.THROTTLE_POLICY_ATTR)

        assert list_policy.scope == "docs:list_documents"
        assert create_policy.scope == "docs:create_document"

    def test_class_decoration_propagates_rate_to_methods(self) -> None:
        """Class-level @throttled rate applies uniformly to all methods."""

        @throttled(scope="docs", rate="250/minute")
        class DocumentService:
            def list_documents(self) -> list[str]:
                return []

            def create_document(self, name: str) -> str:
                return name

        list_policy = getattr(DocumentService.list_documents, const.THROTTLE_POLICY_ATTR)
        create_policy = getattr(DocumentService.create_document, const.THROTTLE_POLICY_ATTR)

        assert list_policy.rate.requests == 250
        assert list_policy.rate.period == Period.MINUTE
        assert create_policy.rate.requests == 250
        assert create_policy.rate.period == Period.MINUTE

    def test_class_decoration_propagates_tiers_to_methods(self) -> None:
        """Class-level @throttled tiers apply uniformly to all methods."""

        tiers = {"free": "100/hour", "premium": "1000/hour"}

        @throttled(scope="docs", rate="100/hour", tiers=tiers)
        class DocumentService:
            def list_documents(self) -> list[str]:
                return []

            def create_document(self, name: str) -> str:
                return name

        list_policy = getattr(DocumentService.list_documents, const.THROTTLE_POLICY_ATTR)
        create_policy = getattr(DocumentService.create_document, const.THROTTLE_POLICY_ATTR)

        assert len(list_policy.tier_rates) == 2
        assert len(create_policy.tier_rates) == 2
        assert list_policy.rate_for("free").requests == 100
        assert list_policy.rate_for("premium").requests == 1000

    def test_class_decoration_skips_underscore_prefixed_methods(self) -> None:
        """Class-level @throttled skips _-prefixed methods."""

        @throttled(scope="docs", rate="100/hour")
        class DocumentService:
            def list_documents(self) -> list[str]:
                return []

            def _internal_helper(self) -> None:
                pass

        list_policy = getattr(DocumentService.list_documents, const.THROTTLE_POLICY_ATTR)
        helper_policy = getattr(DocumentService._internal_helper, const.THROTTLE_POLICY_ATTR, None)

        assert list_policy is not None
        assert helper_policy is None

    def test_class_decoration_skips_dunder_methods(self) -> None:
        """Class-level @throttled skips dunder methods."""

        @throttled(scope="docs", rate="100/hour")
        class DocumentService:
            def list_documents(self) -> list[str]:
                return []

            def __str__(self) -> str:
                return "DocumentService"

        list_policy = getattr(DocumentService.list_documents, const.THROTTLE_POLICY_ATTR)
        str_policy = getattr(DocumentService.__str__, const.THROTTLE_POLICY_ATTR, None)

        assert list_policy is not None
        assert str_policy is None

    def test_class_decoration_skips_nested_classes(self) -> None:
        """Class-level @throttled skips nested class definitions."""

        @throttled(scope="docs", rate="100/hour")
        class DocumentService:
            class Config:
                pass

            def list_documents(self) -> list[str]:
                return []

        list_policy = getattr(DocumentService.list_documents, const.THROTTLE_POLICY_ATTR)

        assert list_policy is not None
        assert not hasattr(DocumentService.Config, const.THROTTLE_POLICY_ATTR)

    def test_class_decoration_respects_existing_policies(self) -> None:
        """Class-level @throttled skips methods already decorated."""

        @throttled(scope="docs", rate="100/hour")
        class DocumentService:
            @throttled(scope="custom", rate="50/hour")
            def list_documents(self) -> list[str]:
                return []

            def create_document(self, name: str) -> str:
                return name

        list_policy = getattr(DocumentService.list_documents, const.THROTTLE_POLICY_ATTR)
        create_policy = getattr(DocumentService.create_document, const.THROTTLE_POLICY_ATTR)

        assert list_policy.scope == "custom"
        assert create_policy.scope == "docs:create_document"

    def test_class_decoration_with_classmethod(self) -> None:
        """Class-level @throttled handles classmethod decorators."""

        @throttled(scope="docs", rate="100/hour")
        class DocumentService:
            @classmethod
            def from_config(cls, config: dict) -> DocumentService:
                return cls()

            def list_documents(self) -> list[str]:
                return []

        from_policy = getattr(
            DocumentService.from_config.__func__, const.THROTTLE_POLICY_ATTR, None  # type: ignore[attr-defined]
        )
        list_policy = getattr(DocumentService.list_documents, const.THROTTLE_POLICY_ATTR)

        assert from_policy is not None
        assert from_policy.scope == "docs:from_config"
        assert list_policy.scope == "docs:list_documents"

    def test_class_decoration_with_staticmethod(self) -> None:
        """Class-level @throttled handles staticmethod decorators."""

        @throttled(scope="docs", rate="100/hour")
        class DocumentService:
            @staticmethod
            def validate_name(name: str) -> bool:
                return bool(name)

            def list_documents(self) -> list[str]:
                return []

        validate_policy = getattr(DocumentService.validate_name, const.THROTTLE_POLICY_ATTR, None)
        list_policy = getattr(DocumentService.list_documents, const.THROTTLE_POLICY_ATTR)

        assert validate_policy is not None
        assert validate_policy.scope == "docs:validate_name"
        assert list_policy.scope == "docs:list_documents"

    def test_class_decoration_skips_properties(self) -> None:
        """Class-level @throttled skips property descriptors."""

        @throttled(scope="docs", rate="100/hour")
        class DocumentService:
            @property
            def count(self) -> int:
                return 0

            def list_documents(self) -> list[str]:
                return []

        list_policy = getattr(DocumentService.list_documents, const.THROTTLE_POLICY_ATTR)

        assert list_policy is not None
        assert not hasattr(DocumentService.count.fget, const.THROTTLE_POLICY_ATTR)  # type: ignore[attr-defined]

    def test_class_decoration_raises_on_empty_class(self) -> None:
        """Class-level @throttled raises ThrottleDeclarationError for empty class."""

        match = re.escape(const.ERR_POLICY_NO_PUBLIC_METHODS)
        with pytest.raises(ThrottleDeclarationError, match=match):

            @throttled(scope="docs", rate="100/hour")
            class DocumentService:
                pass

    def test_class_decoration_raises_on_private_only_class(self) -> None:
        """Class-level @throttled raises if class has only private methods."""

        match = re.escape(const.ERR_POLICY_NO_PUBLIC_METHODS)
        with pytest.raises(ThrottleDeclarationError, match=match):

            @throttled(scope="docs", rate="100/hour")
            class DocumentService:
                def _internal(self) -> None:
                    pass

    def test_class_decoration_on_frozen_dataclass(self) -> None:
        """Class-level @throttled works with frozen dataclasses."""
        from dataclasses import dataclass

        @throttled(scope="docs", rate="100/hour")
        @dataclass(frozen=True)
        class DocumentRequest:
            name: str

            def validate(self) -> bool:
                return bool(self.name)

        validate_policy = getattr(DocumentRequest.validate, const.THROTTLE_POLICY_ATTR, None)
        assert validate_policy is not None
        assert validate_policy.scope == "docs:validate"

    def test_class_decoration_on_slots_dataclass(self) -> None:
        """Class-level @throttled works with frozen slots dataclasses."""
        from dataclasses import dataclass

        @throttled(scope="docs", rate="100/hour")
        @dataclass(frozen=True, slots=True)
        class DocumentRequest:
            name: str

            def validate(self) -> bool:
                return bool(self.name)

        validate_policy = getattr(DocumentRequest.validate, const.THROTTLE_POLICY_ATTR, None)
        assert validate_policy is not None
        assert validate_policy.scope == "docs:validate"

    def test_callable_regression_with_class_decorator_present(self) -> None:
        """Callable @throttled still works when class decorator is used elsewhere."""

        def standalone_func() -> None:
            pass

        @throttled(scope="docs", rate="100/hour")
        class DocumentService:
            def list_documents(self) -> list[str]:
                return []

        decorated_func = throttled(scope="func", rate="200/hour")(standalone_func)

        func_policy = getattr(decorated_func, const.THROTTLE_POLICY_ATTR)
        class_policy = getattr(DocumentService.list_documents, const.THROTTLE_POLICY_ATTR)

        assert func_policy.scope == "func"
        assert class_policy.scope == "docs:list_documents"
        assert decorated_func is standalone_func
