"""Tests for policy client and registry."""

from __future__ import annotations

from types import ModuleType

from domain_api_limiter.decorators.throttled import throttled
from domain_api_limiter.services.constants import policy as const
from domain_api_limiter.services.policy.policy_client import PolicyRegistry
from domain_api_limiter.services.policy.policy_objects import (
    Period,
    RateLimit,
    ThrottlePolicy,
)


class TestPolicyRegistry:
    """PolicyRegistry reads and collects throttle policies."""

    def test_policy_of_returns_declared_policy(self, registry: PolicyRegistry) -> None:
        """PolicyRegistry.policy_of returns policy when declared."""

        def decorated_func() -> None:
            pass

        policy = ThrottlePolicy(
            scope="test.scope", rate=RateLimit(requests=100, period=Period.HOUR)
        )
        setattr(decorated_func, const.THROTTLE_POLICY_ATTR, policy)

        result = registry.policy_of(decorated_func)
        assert result == policy

    def test_policy_of_returns_none_when_not_declared(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.policy_of returns None when policy not declared."""

        def undecorated_func() -> None:
            pass

        result = registry.policy_of(undecorated_func)
        assert result is None

    def test_policy_of_returns_none_for_non_policy_attribute(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.policy_of returns None when attribute is not a policy."""

        def func_with_string_attr() -> None:
            pass

        setattr(func_with_string_attr, const.THROTTLE_POLICY_ATTR, "not a policy")

        result = registry.policy_of(func_with_string_attr)
        assert result is None

    def test_policy_of_returns_none_for_dict_attribute(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.policy_of returns None when attribute is a dict."""

        def func_with_dict_attr() -> None:
            pass

        setattr(func_with_dict_attr, const.THROTTLE_POLICY_ATTR, {"scope": "test"})

        result = registry.policy_of(func_with_dict_attr)
        assert result is None

    def test_collect_on_class_with_decorated_methods(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.collect returns policies from class methods."""

        class TestClass:
            def method1(self) -> None:
                pass

            def method2(self) -> None:
                pass

            def method3(self) -> None:
                pass

        policy1 = ThrottlePolicy(
            scope="method1", rate=RateLimit(requests=100, period=Period.HOUR)
        )
        policy2 = ThrottlePolicy(
            scope="method2", rate=RateLimit(requests=200, period=Period.HOUR)
        )

        setattr(TestClass.method1, const.THROTTLE_POLICY_ATTR, policy1)
        setattr(TestClass.method2, const.THROTTLE_POLICY_ATTR, policy2)

        result = registry.collect(TestClass)
        assert len(result) == 2
        assert policy1 in result
        assert policy2 in result

    def test_collect_on_class_definition_order_preserved(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.collect preserves method definition order."""

        class TestClass:
            def first_method(self) -> None:
                pass

            def second_method(self) -> None:
                pass

            def third_method(self) -> None:
                pass

        policy1 = ThrottlePolicy(
            scope="first", rate=RateLimit(requests=100, period=Period.HOUR)
        )
        policy2 = ThrottlePolicy(
            scope="second", rate=RateLimit(requests=200, period=Period.HOUR)
        )
        policy3 = ThrottlePolicy(
            scope="third", rate=RateLimit(requests=300, period=Period.HOUR)
        )

        setattr(TestClass.first_method, const.THROTTLE_POLICY_ATTR, policy1)
        setattr(TestClass.second_method, const.THROTTLE_POLICY_ATTR, policy2)
        setattr(TestClass.third_method, const.THROTTLE_POLICY_ATTR, policy3)

        result = registry.collect(TestClass)
        assert result == (policy1, policy2, policy3)

    def test_collect_on_class_skips_undecorated_methods(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.collect skips methods without policies."""

        class TestClass:
            def decorated_method(self) -> None:
                pass

            def undecorated_method(self) -> None:
                pass

        policy = ThrottlePolicy(
            scope="decorated", rate=RateLimit(requests=100, period=Period.HOUR)
        )
        setattr(TestClass.decorated_method, const.THROTTLE_POLICY_ATTR, policy)

        result = registry.collect(TestClass)
        assert len(result) == 1
        assert policy in result

    def test_collect_on_class_skips_non_callable_members(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.collect skips non-callable class members."""

        class TestClass:
            class_var = "value"

            def decorated_method(self) -> None:
                pass

        policy = ThrottlePolicy(
            scope="method", rate=RateLimit(requests=100, period=Period.HOUR)
        )
        setattr(TestClass.decorated_method, const.THROTTLE_POLICY_ATTR, policy)

        result = registry.collect(TestClass)
        assert len(result) == 1
        assert policy in result

    def test_collect_on_class_empty_when_no_policies(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.collect returns empty tuple when no policies."""

        class TestClass:
            def method1(self) -> None:
                pass

            def method2(self) -> None:
                pass

        result = registry.collect(TestClass)
        assert result == ()

    def test_collect_on_module_with_decorated_functions(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.collect returns policies from module functions."""
        module = ModuleType("test_module")

        def func1() -> None:
            pass

        def func2() -> None:
            pass

        policy1 = ThrottlePolicy(
            scope="func1", rate=RateLimit(requests=100, period=Period.HOUR)
        )
        policy2 = ThrottlePolicy(
            scope="func2", rate=RateLimit(requests=200, period=Period.HOUR)
        )

        setattr(func1, const.THROTTLE_POLICY_ATTR, policy1)
        setattr(func2, const.THROTTLE_POLICY_ATTR, policy2)

        setattr(module, "func1", func1)
        setattr(module, "func2", func2)

        result = registry.collect(module)
        assert len(result) == 2
        assert policy1 in result
        assert policy2 in result

    def test_collect_on_module_definition_order_preserved(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.collect preserves function order in module."""
        module = ModuleType("test_module")

        def first_func() -> None:
            pass

        def second_func() -> None:
            pass

        policy1 = ThrottlePolicy(
            scope="first", rate=RateLimit(requests=100, period=Period.HOUR)
        )
        policy2 = ThrottlePolicy(
            scope="second", rate=RateLimit(requests=200, period=Period.HOUR)
        )

        setattr(first_func, const.THROTTLE_POLICY_ATTR, policy1)
        setattr(second_func, const.THROTTLE_POLICY_ATTR, policy2)

        setattr(module, "first_func", first_func)
        setattr(module, "second_func", second_func)

        result = registry.collect(module)
        assert result == (policy1, policy2)

    def test_collect_on_module_skips_undecorated_functions(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.collect skips undecorated functions."""
        module = ModuleType("test_module")

        def decorated_func() -> None:
            pass

        def undecorated_func() -> None:
            pass

        policy = ThrottlePolicy(
            scope="decorated", rate=RateLimit(requests=100, period=Period.HOUR)
        )
        setattr(decorated_func, const.THROTTLE_POLICY_ATTR, policy)

        setattr(module, "decorated_func", decorated_func)
        setattr(module, "undecorated_func", undecorated_func)

        result = registry.collect(module)
        assert len(result) == 1
        assert policy in result

    def test_collect_on_module_skips_non_callable_members(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.collect skips non-callable module members."""
        module = ModuleType("test_module")

        def decorated_func() -> None:
            pass

        policy = ThrottlePolicy(
            scope="func", rate=RateLimit(requests=100, period=Period.HOUR)
        )
        setattr(decorated_func, const.THROTTLE_POLICY_ATTR, policy)

        setattr(module, "decorated_func", decorated_func)
        setattr(module, "module_var", "value")
        setattr(module, "module_dict", {"key": "value"})

        result = registry.collect(module)
        assert len(result) == 1
        assert policy in result

    def test_collect_on_module_empty_when_no_policies(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.collect returns empty tuple when no policies in module."""
        module = ModuleType("test_module")

        def func1() -> None:
            pass

        def func2() -> None:
            pass

        setattr(module, "func1", func1)
        setattr(module, "func2", func2)

        result = registry.collect(module)
        assert result == ()

    def test_collect_on_empty_class(self, registry: PolicyRegistry) -> None:
        """PolicyRegistry.collect handles empty class."""

        class EmptyClass:
            pass

        result = registry.collect(EmptyClass)
        assert result == ()

    def test_collect_on_empty_module(self, registry: PolicyRegistry) -> None:
        """PolicyRegistry.collect handles empty module."""
        module = ModuleType("empty_module")
        result = registry.collect(module)
        assert result == ()

    def test_collect_on_class_level_decorated_class(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.collect collects policies from class-level @throttled."""

        @throttled(scope="docs", rate="100/hour")
        class DocumentService:
            def list_documents(self) -> list[str]:
                return []

            def create_document(self, name: str) -> str:
                return name

        result = registry.collect(DocumentService)
        assert len(result) == 2
        assert result[0].scope == "docs:list_documents"
        assert result[1].scope == "docs:create_document"

    def test_collect_on_class_level_decorated_preserves_order(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.collect preserves method order from class decorator."""

        @throttled(scope="docs", rate="100/hour")
        class DocumentService:
            def first_method(self) -> None:
                pass

            def second_method(self) -> None:
                pass

            def third_method(self) -> None:
                pass

        result = registry.collect(DocumentService)
        assert len(result) == 3
        assert result[0].scope == "docs:first_method"
        assert result[1].scope == "docs:second_method"
        assert result[2].scope == "docs:third_method"

    def test_collect_on_class_level_decorated_with_classmethod(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.collect includes classmethod from class decorator."""

        @throttled(scope="docs", rate="100/hour")
        class DocumentService:
            @classmethod
            def from_config(cls, config: dict) -> DocumentService:
                return cls()

            def list_documents(self) -> list[str]:
                return []

        result = registry.collect(DocumentService)
        assert len(result) == 2
        assert result[0].scope == "docs:from_config"
        assert result[1].scope == "docs:list_documents"

    def test_collect_on_class_level_decorated_with_staticmethod(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.collect includes staticmethod from class decorator."""

        @throttled(scope="docs", rate="100/hour")
        class DocumentService:
            @staticmethod
            def validate_name(name: str) -> bool:
                return bool(name)

            def list_documents(self) -> list[str]:
                return []

        result = registry.collect(DocumentService)
        assert len(result) == 2
        assert result[0].scope == "docs:validate_name"
        assert result[1].scope == "docs:list_documents"

    def test_collect_on_mixed_method_decorations(
        self, registry: PolicyRegistry
    ) -> None:
        """PolicyRegistry.collect handles mix of method and class decorations."""

        @throttled(scope="docs", rate="100/hour")
        class DocumentService:
            @throttled(scope="custom", rate="50/hour")
            def list_documents(self) -> list[str]:
                return []

            def create_document(self, name: str) -> str:
                return name

        result = registry.collect(DocumentService)
        assert len(result) == 2
        assert result[0].scope == "custom"
        assert result[1].scope == "docs:create_document"
