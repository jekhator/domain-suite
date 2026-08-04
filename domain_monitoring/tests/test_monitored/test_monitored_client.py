"""Tests for @monitored decorator."""

import asyncio
from dataclasses import dataclass

import pytest
from mixin_logging import clear_correlation_id, set_correlation_id

from domain_monitoring.decorators.monitored.monitored_client import monitored
from domain_monitoring.errors.monitoring_errors import MonitoringDeclarationError
from domain_monitoring.services.metrics.metrics_client import CollectingSink
from domain_monitoring.services.metrics.metrics_objects import Outcome
from domain_monitoring.services.registry.registry_client import MonitorRegistry


class TestMonitoredOnCallable:
    """@monitored on functions and methods."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MonitorRegistry.clear_default_sink()

    def test_monitored_sync_callable_success(self) -> None:
        """@monitored on sync callable emits SUCCESS event."""
        sink = CollectingSink()

        @monitored("test.operation", sink=sink)
        def sync_fn() -> str:
            return "result"

        result = sync_fn()

        assert result == "result"
        assert len(sink.events) == 1
        assert sink.events[0].event == "test.operation"
        assert sink.events[0].outcome == Outcome.SUCCESS
        assert sink.events[0].duration_ms >= 0

    def test_monitored_sync_callable_failure(self) -> None:
        """@monitored on sync callable emits FAILURE event on exception."""
        sink = CollectingSink()

        @monitored("test.operation", sink=sink)
        def sync_fn() -> None:
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            sync_fn()

        assert len(sink.events) == 1
        assert sink.events[0].event == "test.operation"
        assert sink.events[0].outcome == Outcome.FAILURE
        assert sink.events[0].is_failure

    def test_monitored_async_callable_success(self) -> None:
        """@monitored on async callable emits SUCCESS event."""
        sink = CollectingSink()

        @monitored("test.async_operation", sink=sink)
        async def async_fn() -> str:
            await asyncio.sleep(0.01)
            return "async_result"

        result = asyncio.run(async_fn())

        assert result == "async_result"
        assert len(sink.events) == 1
        assert sink.events[0].event == "test.async_operation"
        assert sink.events[0].outcome == Outcome.SUCCESS

    def test_monitored_async_callable_failure(self) -> None:
        """@monitored on async callable emits FAILURE event on exception."""
        sink = CollectingSink()

        @monitored("test.async_operation", sink=sink)
        async def async_fn() -> None:
            await asyncio.sleep(0.01)
            raise RuntimeError("async error")

        with pytest.raises(RuntimeError, match="async error"):
            asyncio.run(async_fn())

        assert len(sink.events) == 1
        assert sink.events[0].event == "test.async_operation"
        assert sink.events[0].outcome == Outcome.FAILURE

    def test_monitored_with_registry_sink(self) -> None:
        """@monitored resolves sink from registry when None."""
        registry_sink = CollectingSink()
        MonitorRegistry.set_default_sink(registry_sink)

        @monitored("test.registry_operation")
        def sync_fn() -> str:
            return "result"

        result = sync_fn()

        assert result == "result"
        assert len(registry_sink.events) == 1
        assert registry_sink.events[0].event == "test.registry_operation"

    def test_monitored_with_args_and_kwargs(self) -> None:
        """@monitored preserves function args and kwargs."""
        sink = CollectingSink()

        @monitored("test.with_args", sink=sink)
        def fn_with_args(a: int, b: str, c: float = 1.0) -> str:
            return f"{a}-{b}-{c}"

        result = fn_with_args(42, "test", c=3.5)

        assert result == "42-test-3.5"
        assert len(sink.events) == 1


class TestMonitoredOnClass:
    """@monitored on classes fans out to public methods."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MonitorRegistry.clear_default_sink()

    def test_monitored_class_public_methods(self) -> None:
        """@monitored on class fans out to public methods."""
        sink = CollectingSink()

        @monitored("documents", sink=sink)
        @dataclass(frozen=True, slots=True)
        class DocumentService:
            """Document processing service."""

            name: str

            def process(self) -> str:
                return f"processing {self.name}"

            def analyze(self) -> str:
                return f"analyzing {self.name}"

            def _private_method(self) -> str:
                return "private"

        service = DocumentService(name="test.pdf")

        process_result = service.process()
        analyze_result = service.analyze()
        private_result = service._private_method()

        assert process_result == "processing test.pdf"
        assert analyze_result == "analyzing test.pdf"
        assert private_result == "private"
        assert len(sink.events) == 2
        assert sink.events[0].event == "documents.process"
        assert sink.events[1].event == "documents.analyze"

    def test_monitored_class_failure_on_method(self) -> None:
        """@monitored on class emits failure event from method exception."""
        sink = CollectingSink()

        @monitored("service", sink=sink)
        @dataclass(frozen=True, slots=True)
        class Service:
            """Test service."""

            fail: bool

            def execute(self) -> str:
                if self.fail:
                    raise RuntimeError("execution failed")
                return "success"

        service = Service(fail=True)

        with pytest.raises(RuntimeError, match="execution failed"):
            service.execute()

        assert len(sink.events) == 1
        assert sink.events[0].event == "service.execute"
        assert sink.events[0].is_failure

    def test_monitored_empty_class_raises(self) -> None:
        """@monitored on class with no public methods raises."""
        with pytest.raises(MonitoringDeclarationError):

            @monitored("empty")
            @dataclass(frozen=True, slots=True)
            class EmptyService:
                """Service with no public methods."""

                _private: str = ""

    def test_monitored_invalid_target_raises(self) -> None:
        """@monitored on invalid target raises."""
        with pytest.raises(MonitoringDeclarationError):
            monitored("test")(42)  # type: ignore


class TestMonitoredLabels:
    """@monitored with label injection callbacks."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MonitorRegistry.clear_default_sink()

    def test_monitored_labels_from_result_success(self) -> None:
        """@monitored with labels_from_result populates labels on success."""
        sink = CollectingSink()

        def extract_labels(result: object) -> tuple[tuple[str, str], ...]:
            if isinstance(result, dict):
                return (("status", result.get("status", "unknown")),)
            return ()

        @monitored(
            "test.with_labels",
            sink=sink,
            labels_from_result=extract_labels,
        )
        def fn_success() -> dict:
            return {"status": "completed", "items": 5}

        result = fn_success()
        assert result == {"status": "completed", "items": 5}
        assert len(sink.events) == 1
        assert sink.events[0].outcome == Outcome.SUCCESS
        assert sink.events[0].labels == (("status", "completed"),)

    def test_monitored_labels_from_exc_failure(self) -> None:
        """@monitored with labels_from_exc populates labels on failure."""
        sink = CollectingSink()

        def extract_error_labels(exc: BaseException) -> tuple[tuple[str, str], ...]:
            return (("error_type", type(exc).__name__),)

        @monitored(
            "test.with_error_labels",
            sink=sink,
            labels_from_exc=extract_error_labels,
        )
        def fn_failure() -> None:
            raise ValueError("test error message")

        with pytest.raises(ValueError):
            fn_failure()

        assert len(sink.events) == 1
        assert sink.events[0].outcome == Outcome.FAILURE
        assert sink.events[0].labels == (("error_type", "ValueError"),)

    def test_monitored_labels_default_empty(self) -> None:
        """@monitored without label callbacks has empty labels by default."""
        sink = CollectingSink()

        @monitored("test.no_labels", sink=sink)
        def fn_no_labels() -> str:
            return "result"

        fn_no_labels()
        assert len(sink.events) == 1
        assert sink.events[0].labels == ()

    def test_monitored_labels_async_success(self) -> None:
        """@monitored with async function and labels_from_result."""
        sink = CollectingSink()

        def extract_labels(result: object) -> tuple[tuple[str, str], ...]:
            if isinstance(result, str):
                return (("length", str(len(result))),)
            return ()

        @monitored(
            "test.async_labels",
            sink=sink,
            labels_from_result=extract_labels,
        )
        async def async_fn() -> str:
            await asyncio.sleep(0.001)
            return "hello"

        result = asyncio.run(async_fn())
        assert result == "hello"
        assert len(sink.events) == 1
        assert sink.events[0].labels == (("length", "5"),)

    def test_monitored_labels_async_failure(self) -> None:
        """@monitored with async function and labels_from_exc."""
        sink = CollectingSink()

        def extract_error_labels(exc: BaseException) -> tuple[tuple[str, str], ...]:
            return (("error_type", type(exc).__name__),)

        @monitored(
            "test.async_error_labels",
            sink=sink,
            labels_from_exc=extract_error_labels,
        )
        async def async_fn_failure() -> None:
            await asyncio.sleep(0.001)
            raise RuntimeError("async error")

        with pytest.raises(RuntimeError):
            asyncio.run(async_fn_failure())

        assert len(sink.events) == 1
        assert sink.events[0].labels == (("error_type", "RuntimeError"),)

    def test_monitored_labels_on_class_methods(self) -> None:
        """@monitored on class passes label callbacks to methods."""
        sink = CollectingSink()

        def extract_labels(result: object) -> tuple[tuple[str, str], ...]:
            if isinstance(result, str) and result.startswith("success"):
                return (("status", "ok"),)
            return ()

        @monitored(
            "service",
            sink=sink,
            labels_from_result=extract_labels,
        )
        @dataclass(frozen=True, slots=True)
        class Service:
            """Service with label extraction."""

            name: str

            def execute(self) -> str:
                return f"success: {self.name}"

        service = Service(name="test_op")
        result = service.execute()

        assert result == "success: test_op"
        assert len(sink.events) == 1
        assert sink.events[0].event == "service.execute"
        assert sink.events[0].labels == (("status", "ok"),)


class TestMonitoredEdgeCases:
    """Edge cases and special scenarios."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MonitorRegistry.clear_default_sink()

    def test_monitored_preserves_function_name(self) -> None:
        """@monitored preserves original function name."""

        @monitored("test")
        def my_function() -> str:
            return "result"

        assert my_function.__name__ == "my_function"

    def test_monitored_with_return_value_and_exception(self) -> None:
        """Multiple calls track separate success/failure events."""
        sink = CollectingSink()

        @monitored("test.toggle", sink=sink)
        def toggle_fn(should_fail: bool) -> str:
            if should_fail:
                raise ValueError("intentional")
            return "ok"

        result1 = toggle_fn(False)
        assert result1 == "ok"
        assert len(sink.events) == 1
        assert sink.events[0].outcome == Outcome.SUCCESS

        with pytest.raises(ValueError):
            toggle_fn(True)

        assert len(sink.events) == 2
        assert sink.events[1].outcome == Outcome.FAILURE

    def test_monitored_class_with_classmethod(self) -> None:
        """@monitored on class with classmethod includes it in public methods."""
        sink = CollectingSink()

        @monitored("factory", sink=sink)
        class FactoryService:
            """Service with classmethod."""

            @classmethod
            def create(cls) -> "FactoryService":
                """Factory method."""
                return cls()

        obj = FactoryService.create()
        assert obj is not None
        assert len(sink.events) == 1
        assert sink.events[0].event == "factory.create"
        assert sink.events[0].outcome == Outcome.SUCCESS

    def test_monitored_class_with_staticmethod(self) -> None:
        """@monitored on class with staticmethod includes it in public methods."""
        sink = CollectingSink()

        @monitored("utils", sink=sink)
        class UtilService:
            """Service with staticmethod."""

            @staticmethod
            def helper() -> str:
                """Helper function."""
                return "helper_result"

        result = UtilService.helper()
        assert result == "helper_result"
        assert len(sink.events) == 1
        assert sink.events[0].event == "utils.helper"
        assert sink.events[0].outcome == Outcome.SUCCESS


class TestCorrelationStamping:
    """Test correlation id stamping in metrics."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MonitorRegistry.clear_default_sink()

    def test_correlation_stamping_with_ambient_id(self) -> None:
        """@monitored stamps correlation labels from ambient ContextVar."""
        sink = CollectingSink()
        scenario_id = "scn-abc123def456"
        set_correlation_id(scenario_id)

        try:

            @monitored("test.operation", sink=sink)
            def fn_with_correlation() -> str:
                return "result"

            fn_with_correlation()

            assert len(sink.events) == 1
            labels_dict = dict(sink.events[0].labels)
            assert labels_dict.get("correlation_id") == scenario_id
            assert (
                labels_dict.get("domain_correlation_id") == f"{scenario_id}/monitoring"
            )
        finally:
            clear_correlation_id()

    def test_correlation_stamping_without_ambient_id(self) -> None:
        """@monitored without ambient id does not stamp correlation labels."""
        sink = CollectingSink()

        @monitored("test.operation", sink=sink)
        def fn_no_correlation() -> str:
            return "result"

        fn_no_correlation()

        assert len(sink.events) == 1
        labels_dict = dict(sink.events[0].labels)
        assert "correlation_id" not in labels_dict
        assert "domain_correlation_id" not in labels_dict

    def test_correlation_stamping_consumer_labels_win(self) -> None:
        """Consumer-provided labels take precedence over stamped correlation."""
        sink = CollectingSink()
        scenario_id = "scn-abc123def456"
        set_correlation_id(scenario_id)

        try:

            def labels_from_result(result: object) -> tuple[tuple[str, str], ...]:
                return (
                    ("correlation_id", "consumer-value"),
                    ("custom_key", "custom_value"),
                )

            @monitored(
                "test.operation", sink=sink, labels_from_result=labels_from_result
            )
            def fn_with_labels() -> str:
                return "result"

            fn_with_labels()

            assert len(sink.events) == 1
            labels_dict = dict(sink.events[0].labels)
            assert labels_dict.get("correlation_id") == "consumer-value"
            assert (
                labels_dict.get("domain_correlation_id") == f"{scenario_id}/monitoring"
            )
            assert labels_dict.get("custom_key") == "custom_value"
        finally:
            clear_correlation_id()

    def test_correlation_stamping_on_async(self) -> None:
        """@monitored stamps correlation on async functions."""
        sink = CollectingSink()
        scenario_id = "scn-xyz789abc123"
        set_correlation_id(scenario_id)

        try:

            @monitored("test.async_operation", sink=sink)
            async def async_fn_with_correlation() -> str:
                await asyncio.sleep(0.01)
                return "async_result"

            asyncio.run(async_fn_with_correlation())

            assert len(sink.events) == 1
            labels_dict = dict(sink.events[0].labels)
            assert labels_dict.get("correlation_id") == scenario_id
            assert (
                labels_dict.get("domain_correlation_id") == f"{scenario_id}/monitoring"
            )
        finally:
            clear_correlation_id()

    def test_correlation_stamping_on_failure(self) -> None:
        """@monitored stamps correlation on failure metrics."""
        sink = CollectingSink()
        scenario_id = "scn-failure123456789"
        set_correlation_id(scenario_id)

        try:

            @monitored("test.failing_operation", sink=sink)
            def fn_that_fails() -> None:
                raise ValueError("intentional error")

            with pytest.raises(ValueError):
                fn_that_fails()

            assert len(sink.events) == 1
            labels_dict = dict(sink.events[0].labels)
            assert labels_dict.get("correlation_id") == scenario_id
            assert (
                labels_dict.get("domain_correlation_id") == f"{scenario_id}/monitoring"
            )
            assert sink.events[0].outcome == Outcome.FAILURE
        finally:
            clear_correlation_id()
