"""Tests for native Logged aspect wrapper implementation."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from domain_aspects.services.aspects import aspects_objects as objs

START_EVENT = "test.operation.start"
END_EVENT = "test.operation.end"
ERROR_EVENT = "test.operation.error"


class TestLoggedWrapperSync:
    """Test synchronous Logged aspect wrapper."""

    def test_logged_wrapper_preserves_function_result(
        self, captured_logs: list[tuple[str, str, dict[str, Any]]]
    ) -> None:
        """Logged wrapper preserves function return value and emits start and end events."""
        logged = objs.Logged(event="test.operation")
        wrapper_factory = logged.build()

        def operation(value: int) -> int:
            return value * 2

        wrapped = wrapper_factory(operation)
        result = wrapped(5)

        assert result == 10
        assert [(level, event) for level, event, _ in captured_logs] == [
            ("info", START_EVENT),
            ("info", END_EVENT),
        ]

    def test_logged_wrapper_propagates_exceptions(
        self, captured_logs: list[tuple[str, str, dict[str, Any]]]
    ) -> None:
        """Logged wrapper re-raises the original exception and emits an error event."""
        logged = objs.Logged(event="test.operation")
        wrapper_factory = logged.build()

        def operation(value: int) -> int:
            raise ValueError("test error")

        wrapped = wrapper_factory(operation)

        with pytest.raises(ValueError, match="test error"):
            wrapped(5)
        assert captured_logs[-1][:2] == ("error", ERROR_EVENT)
        assert captured_logs[-1][2]["error_type"] == "ValueError"

    def test_logged_wrapper_with_payload_extractors(
        self, captured_logs: list[tuple[str, str, dict[str, Any]]]
    ) -> None:
        """Logged wrapper passes request and result payloads into the start and end events."""

        def extract_request(x: object) -> dict[str, object]:
            return {"input": x}

        def extract_result(result: object) -> dict[str, object]:
            return {"output": result}

        logged = objs.Logged(
            event="test.operation",
            payload_from_request=extract_request,
            payload_from_result=extract_result,
        )
        wrapper_factory = logged.build()

        def operation(x: int) -> int:
            return x * 2

        wrapped = wrapper_factory(operation)
        result = wrapped(5)

        assert result == 10
        assert captured_logs[0][2] == {"input": 5}
        assert captured_logs[1][2] == {"output": 10}

    def test_logged_wrapper_guards_extraction_failures(
        self, captured_logs: list[tuple[str, str, dict[str, Any]]]
    ) -> None:
        """Logged wrapper logs an extraction failure, then keeps running and emits the end event."""

        def bad_extractor(x: int) -> dict[str, object]:
            raise RuntimeError("extraction failed")

        logged = objs.Logged(
            event="test.operation",
            payload_from_request=bad_extractor,
        )
        wrapper_factory = logged.build()

        def operation(x: int) -> int:
            return x * 2

        wrapped = wrapper_factory(operation)
        result = wrapped(5)

        assert result == 10
        assert captured_logs[0] == (
            "error",
            "Logged: extraction failed for " + START_EVENT,
            {"error": "extraction failed"},
        )
        assert captured_logs[-1][:2] == ("info", END_EVENT)


class TestLoggedWrapperAsync:
    """Test asynchronous Logged aspect wrapper."""

    def test_logged_wrapper_async_preserves_result(
        self, captured_logs: list[tuple[str, str, dict[str, Any]]]
    ) -> None:
        """Logged wrapper preserves async function return value and emits start and end events."""
        logged = objs.Logged(event="test.operation")
        wrapper_factory = logged.build()

        async def operation(value: int) -> int:
            await asyncio.sleep(0.001)
            return value * 2

        wrapped = wrapper_factory(operation)

        async def run_test() -> None:
            result = await wrapped(5)
            assert result == 10

        asyncio.run(run_test())
        assert [event for _, event, _ in captured_logs] == [START_EVENT, END_EVENT]

    def test_logged_wrapper_async_propagates_exceptions(
        self, captured_logs: list[tuple[str, str, dict[str, Any]]]
    ) -> None:
        """Logged wrapper propagates exceptions from async function and logs the error."""
        logged = objs.Logged(event="test.operation")
        wrapper_factory = logged.build()

        async def operation(value: int) -> int:
            raise ValueError("test error")

        wrapped = wrapper_factory(operation)

        async def run_test() -> None:
            with pytest.raises(ValueError, match="test error"):
                await wrapped(5)

        asyncio.run(run_test())
        assert captured_logs[-1][:2] == ("error", ERROR_EVENT)


class TestLoggedWrapperTimed:
    """Test Logged aspect wrapper with timing enabled."""

    def test_logged_wrapper_sync_timed_includes_latency_ms_on_success(
        self, captured_logs: list[tuple[str, str, dict[str, Any]]]
    ) -> None:
        """Logged wrapper with timed=True includes latency_ms in the end payload."""
        logged = objs.Logged(event="test.operation", timed=True)
        wrapper_factory = logged.build()

        def operation(x: int) -> int:
            return x * 2

        wrapped = wrapper_factory(operation)
        result = wrapped(5)

        assert result == 10
        end_fields = captured_logs[-1][2]
        assert captured_logs[-1][:2] == ("info", END_EVENT)
        assert isinstance(end_fields["latency_ms"], float)
        assert end_fields["latency_ms"] >= 0

    def test_logged_wrapper_sync_timed_includes_latency_ms_on_error(
        self, captured_logs: list[tuple[str, str, dict[str, Any]]]
    ) -> None:
        """Logged wrapper with timed=True includes latency_ms in the error payload."""
        logged = objs.Logged(event="test.operation", timed=True)
        wrapper_factory = logged.build()

        def operation(value: int) -> int:
            raise ValueError("test error")

        wrapped = wrapper_factory(operation)

        with pytest.raises(ValueError, match="test error"):
            wrapped(5)
        error_fields = captured_logs[-1][2]
        assert captured_logs[-1][:2] == ("error", ERROR_EVENT)
        assert error_fields["latency_ms"] >= 0

    def test_logged_wrapper_async_timed_includes_latency_ms(
        self, captured_logs: list[tuple[str, str, dict[str, Any]]]
    ) -> None:
        """Logged wrapper async with timed=True includes latency_ms in the end payload."""
        logged = objs.Logged(event="test.operation", timed=True)
        wrapper_factory = logged.build()

        async def operation(value: int) -> int:
            await asyncio.sleep(0.001)
            return value * 2

        wrapped = wrapper_factory(operation)

        async def run_test() -> None:
            result = await wrapped(5)
            assert result == 10

        asyncio.run(run_test())
        assert "latency_ms" in captured_logs[-1][2]

    def test_logged_wrapper_async_timed_includes_latency_ms_on_error(
        self, captured_logs: list[tuple[str, str, dict[str, Any]]]
    ) -> None:
        """Logged wrapper async with timed=True includes latency_ms on error."""
        logged = objs.Logged(event="test.operation", timed=True)
        wrapper_factory = logged.build()

        async def operation(value: int) -> int:
            await asyncio.sleep(0.001)
            raise ValueError("test error")

        wrapped = wrapper_factory(operation)

        async def run_test() -> None:
            with pytest.raises(ValueError, match="test error"):
                await wrapped(5)

        asyncio.run(run_test())
        assert "latency_ms" in captured_logs[-1][2]
