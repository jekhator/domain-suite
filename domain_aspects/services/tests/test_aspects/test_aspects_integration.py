"""Integration tests for aspect composition with real dependencies.

Tests all six aspects with REAL packages from [all] extra. Verifies aspects compose
correctly on function and class targets, catching the bug that existed in 0.1.0
(WrapErrors.build() passing catch incorrectly).
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from domain_aspects import aspects
from domain_aspects.services.aspects import aspects_objects as objs


class TestRealDepsIntegration:
    """Integration tests using real decorator packages."""

    def test_wrap_errors_real_sig_fixed(self) -> None:
        """WrapErrors now calls wrap_errors with correct keyword-only catch arg."""
        from domain_errors import DomainError

        class TestError(DomainError):
            domain = "test"
            code = "error"
            http_status = 500

        @aspects(objs.WrapErrors(as_=TestError, catch=(ValueError,)))
        @dataclass(frozen=True, slots=True)
        class Service:
            def process(self) -> None:
                raise ValueError("inner")

        service = Service()
        with pytest.raises(TestError) as exc_info:
            service.process()
        assert isinstance(exc_info.value.__cause__, ValueError)

    def test_logged_real_sig(self) -> None:
        """Logged calls logged(event) correctly via lazy import."""
        from mixin_logging import LoggingMixin

        @aspects(objs.Logged(event="test.event"))
        @dataclass(frozen=True, slots=True)
        class Service(LoggingMixin):
            def process(self) -> str:
                return "ok"

        service = Service()
        result = service.process()
        assert result == "ok"

    def test_throttled_real_sig(self) -> None:
        """Throttled calls throttled(scope, rate, tiers) correctly."""

        @aspects(objs.Throttled(scope="api", rate="100/hour"))
        @dataclass(frozen=True, slots=True)
        class Service:
            def process(self) -> str:
                return "throttled"

        service = Service()
        result = service.process()
        assert result == "throttled"

    def test_compose_multiple_aspects_no_conflict(self) -> None:
        """Multiple aspects (WrapErrors, Logged, Throttled) compose without conflict."""
        from mixin_logging import LoggingMixin

        from domain_errors import DomainError

        class TestError(DomainError):
            domain = "test"
            code = "error"
            http_status = 500

        @aspects(
            frozenset(
                {
                    objs.Logged(event="multi.test"),
                    objs.Throttled(scope="multi", rate="50/hour"),
                    objs.WrapErrors(as_=TestError),
                }
            )
        )
        @dataclass(frozen=True, slots=True)
        class Service(LoggingMixin):
            def process(self) -> str:
                return "composed"

        service = Service()
        result = service.process()
        assert result == "composed"

    def test_wrap_errors_error_chain_preserved(self) -> None:
        """Composed WrapErrors preserves error chain with __cause__."""
        from domain_errors import DomainError

        class TestError(DomainError):
            domain = "test"
            code = "error"
            http_status = 500

        @aspects(objs.WrapErrors(as_=TestError))
        @dataclass(frozen=True, slots=True)
        class Service:
            def fail(self) -> None:
                raise RuntimeError("root cause")

        service = Service()
        with pytest.raises(TestError) as exc_info:
            service.fail()

        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, RuntimeError)
        assert "root cause" in str(exc_info.value.__cause__)

    def test_requires_real_sig(self) -> None:
        """Requires calls requires(permission) correctly."""
        from domain_security.errors.security_errors import AuthzError

        @aspects(objs.Requires(permission="admin"))
        @dataclass(frozen=True, slots=True)
        class Service:
            def admin_only(self) -> str:
                return "admin_access"

        service = Service()
        with pytest.raises(AuthzError):
            service.admin_only()

    def test_tenant_scoped_real_sig(self) -> None:
        """TenantScoped calls tenant_scoped(param_name) correctly."""
        from domain_security.errors.security_errors import TenancyError

        @aspects(objs.TenantScoped(param_name="tenant_id"))
        @dataclass(frozen=True, slots=True)
        class Service:
            def tenant_method(self, tenant_id: str) -> str:
                return f"tenant:{tenant_id}"

        service = Service()
        with pytest.raises(TenancyError):
            service.tenant_method(tenant_id="test")

    def test_monitored_real_sig(self) -> None:
        """Monitored calls monitored(event, sink) correctly via real dependency."""

        @aspects(objs.Monitored(event="test.operation"))
        @dataclass(frozen=True, slots=True)
        class Service:
            def process(self) -> str:
                return "monitored"

        service = Service()
        result = service.process()
        assert result == "monitored"

    def test_monitored_with_logged_composition(self) -> None:
        """Monitored and Logged compose together without conflict."""
        from mixin_logging import LoggingMixin

        @aspects(
            objs.Logged(event="test.event"),
            objs.Monitored(event="test.operation"),
        )
        @dataclass(frozen=True, slots=True)
        class Service(LoggingMixin):
            def process(self) -> str:
                return "composed"

        service = Service()
        result = service.process()
        assert result == "composed"

    def test_monitored_aspect_labels_from_result(self) -> None:
        """Monitored aspect-path supports labels_from_result parity with decorator."""
        from domain_monitoring.services.metrics.metrics_objects import MetricEvent

        collected_events: list[MetricEvent] = []

        class CollectingSink:
            def emit(self, event: MetricEvent) -> None:
                collected_events.append(event)

        @aspects(
            objs.Monitored(
                event="test.result_labels",
                sink=CollectingSink(),
                labels_from_result=lambda r: (("tokens", str(r)),),
            )
        )
        @dataclass(frozen=True, slots=True)
        class Service:
            def process(self) -> str:
                return "result_value"

        service = Service()
        result = service.process()
        assert result == "result_value"
        assert len(collected_events) == 1
        event = collected_events[0]
        assert event.labels == (("tokens", "result_value"),)

    def test_monitored_aspect_labels_from_exc(self) -> None:
        """Monitored aspect-path supports labels_from_exc parity with decorator."""
        from domain_monitoring.services.metrics.metrics_objects import MetricEvent

        collected_events: list[MetricEvent] = []

        class CollectingSink:
            def emit(self, event: MetricEvent) -> None:
                collected_events.append(event)

        @aspects(
            objs.Monitored(
                event="test.exc_labels",
                sink=CollectingSink(),
                labels_from_exc=lambda e: (("error_type", type(e).__name__),),
            )
        )
        @dataclass(frozen=True, slots=True)
        class Service:
            def process(self) -> None:
                raise ValueError("test error")

        service = Service()
        with pytest.raises(ValueError):
            service.process()
        assert len(collected_events) == 1
        event = collected_events[0]
        assert event.labels == (("error_type", "ValueError"),)

    def test_monitored_aspect_no_callbacks_empty_labels(self) -> None:
        """Monitored aspect without callbacks produces empty labels tuple."""
        from domain_monitoring.services.metrics.metrics_objects import MetricEvent

        collected_events: list[MetricEvent] = []

        class CollectingSink:
            def emit(self, event: MetricEvent) -> None:
                collected_events.append(event)

        @aspects(objs.Monitored(event="test.no_labels", sink=CollectingSink()))
        @dataclass(frozen=True, slots=True)
        class Service:
            def process(self) -> str:
                return "value"

        service = Service()
        result = service.process()
        assert result == "value"
        assert len(collected_events) == 1
        event = collected_events[0]
        assert event.labels == ()

    def test_stacked_retried_wrap_errors_plain_class(self) -> None:
        """Stacked Retried+WrapErrors on plain class: retries succeed, exhaustion wraps.

        Verifies the composition defect fix: Retried must wrap class methods, not
        replace the class. Retried sees raw ValueError, retries succeed on attempt 3,
        WrapErrors sits outside and would convert final exception to DomainError if
        retries exhausted.
        """
        from mixin_retry import RetryPolicy

        from domain_errors import DomainError

        class TestError(DomainError):
            domain = "test"
            code = "retried_fail"
            http_status = 500

        policy = RetryPolicy(
            max_attempts=3,
            backoff_base_seconds=0.0,
            backoff_multiplier=1.0,
            backoff_max_seconds=0.0,
            jitter=False,
            should_retry=lambda e: isinstance(e, ValueError),
        )
        calls = {"n": 0}

        @aspects(
            objs.Logged("test_retried"),
            objs.Retried(policy=policy),
            objs.WrapErrors(as_=TestError, catch=(ValueError,)),
        )
        class Service:
            def flaky(self) -> str:
                calls["n"] += 1
                if calls["n"] < 3:
                    raise ValueError("transient")
                return "ok"

        service = Service()
        result = service.flaky()
        assert result == "ok"
        assert calls["n"] == 3

    def test_stacked_retried_wrap_errors_exhaustion(self) -> None:
        """Stacked Retried+WrapErrors: retries exhausted -> ValueError wrapped to DomainError."""
        from mixin_retry import RetryPolicy

        from domain_errors import DomainError

        class TestError(DomainError):
            domain = "test"
            code = "retried_exhaust"
            http_status = 500

        policy = RetryPolicy(
            max_attempts=2,
            backoff_base_seconds=0.0,
            backoff_multiplier=1.0,
            backoff_max_seconds=0.0,
            jitter=False,
            should_retry=lambda e: isinstance(e, ValueError),
        )
        calls = {"n": 0}

        @aspects(
            objs.Retried(policy=policy),
            objs.WrapErrors(as_=TestError, catch=(ValueError,)),
        )
        class Service:
            def always_fails(self) -> str:
                calls["n"] += 1
                raise ValueError("permanent")

        service = Service()
        with pytest.raises(TestError) as exc_info:
            service.always_fails()
        assert isinstance(exc_info.value.__cause__, ValueError)
        assert calls["n"] == 2

    def test_stacked_logged_retried_async(self) -> None:
        """Stacked Logged+Retried on async class method."""
        import asyncio

        from mixin_logging import LoggingMixin
        from mixin_retry import RetryPolicy

        policy = RetryPolicy(
            max_attempts=3,
            backoff_base_seconds=0.0,
            backoff_multiplier=1.0,
            backoff_max_seconds=0.0,
            jitter=False,
            should_retry=lambda e: isinstance(e, ValueError),
        )
        calls = {"n": 0}

        @aspects(
            objs.Logged("async_test"),
            objs.Retried(policy=policy),
        )
        class Service(LoggingMixin):
            async def flaky_async(self) -> str:
                calls["n"] += 1
                if calls["n"] < 3:
                    raise ValueError("transient")
                return "async_ok"

        service = Service()
        result = asyncio.run(service.flaky_async())
        assert result == "async_ok"
        assert calls["n"] == 3

    def test_retried_selector_none_passthrough_class(self) -> None:
        """Retried with policy_from_request=None on class: single-attempt passthrough."""
        calls = {"n": 0}

        @aspects(
            objs.Retried(policy_from_request=lambda *a, **k: None),
        )
        class Service:
            def no_retry(self) -> str:
                calls["n"] += 1
                if calls["n"] < 3:
                    raise ValueError("should not retry")
                return "ok"

        service = Service()
        with pytest.raises(ValueError):
            service.no_retry()
        assert calls["n"] == 1

    def test_logged_class_skips_privates_properties_nested(self) -> None:
        """Logged on class: skips _-prefixed methods, properties, nested classes."""
        from mixin_logging import LoggingMixin

        @aspects(objs.Logged(event="test.skips"))
        class Service(LoggingMixin):
            public_value = 42

            def public_method(self) -> str:
                return "public"

            def _private_method(self) -> str:
                return "private"

            @property
            def prop(self) -> str:
                return "property"

            class NestedClass:
                pass

        service = Service()
        assert service.public_method() == "public"
        assert service._private_method() == "private"
        assert service.prop == "property"
        assert isinstance(service.NestedClass, type)

    def test_logged_class_preserves_classmethod_staticmethod(self) -> None:
        """Logged on class: preserves classmethod/staticmethod wrappers."""

        @aspects(objs.Logged(event="test.class_static"))
        class Service:
            @classmethod
            def class_method(cls) -> str:
                return "classmethod"

            @staticmethod
            def static_method() -> str:
                return "staticmethod"

        assert Service.class_method() == "classmethod"
        assert Service.static_method() == "staticmethod"

    def test_retried_class_skips_privates_properties_nested(self) -> None:
        """Retried on class: skips _-prefixed methods, properties, nested classes."""
        from mixin_retry import RetryPolicy

        policy = RetryPolicy(
            max_attempts=1,
            backoff_base_seconds=0.0,
            backoff_multiplier=1.0,
            backoff_max_seconds=0.0,
            jitter=False,
            should_retry=lambda e: False,
        )

        @aspects(objs.Retried(policy=policy))
        class Service:
            public_value = 42

            def public_method(self) -> str:
                return "public"

            def _private_method(self) -> str:
                return "private"

            @property
            def prop(self) -> str:
                return "property"

            class NestedClass:
                pass

        service = Service()
        assert service.public_method() == "public"
        assert service._private_method() == "private"
        assert service.prop == "property"
        assert isinstance(service.NestedClass, type)

    def test_retried_class_preserves_classmethod_staticmethod(self) -> None:
        """Retried on class: preserves classmethod/staticmethod wrappers."""
        from mixin_retry import RetryPolicy

        policy = RetryPolicy(
            max_attempts=1,
            backoff_base_seconds=0.0,
            backoff_multiplier=1.0,
            backoff_max_seconds=0.0,
            jitter=False,
            should_retry=lambda e: False,
        )

        @aspects(objs.Retried(policy=policy))
        class Service:
            @classmethod
            def class_method(cls) -> str:
                return "classmethod"

            @staticmethod
            def static_method() -> str:
                return "staticmethod"

        assert Service.class_method() == "classmethod"
        assert Service.static_method() == "staticmethod"

    def test_logged_skips_already_marked_methods(self) -> None:
        """Logged on class: skips methods already marked with LOGGED_MARKER."""
        from mixin_logging import LoggingMixin

        @aspects(objs.Logged(event="test.second"))
        @aspects(objs.Logged(event="test.first"))
        class Service(LoggingMixin):
            def method(self) -> str:
                return "ok"

        service = Service()
        result = service.method()
        assert result == "ok"

    def test_retried_skips_already_marked_methods(self) -> None:
        """Retried on class: skips methods already marked with RETRIED_MARKER."""
        from mixin_retry import RetryPolicy

        policy = RetryPolicy(
            max_attempts=1,
            backoff_base_seconds=0.0,
            backoff_multiplier=1.0,
            backoff_max_seconds=0.0,
            jitter=False,
            should_retry=lambda e: False,
        )

        @aspects(objs.Retried(policy=policy))
        @aspects(objs.Retried(policy=policy))
        class Service:
            def method(self) -> str:
                return "ok"

        service = Service()
        result = service.method()
        assert result == "ok"
