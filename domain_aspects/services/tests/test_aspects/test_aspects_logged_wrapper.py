"""Tests for native Logged aspect wrapper implementation."""

from __future__ import annotations

import asyncio

import pytest

from domain_aspects.services.aspects import aspects_objects as objs


class TestLoggedWrapperSync:
    """Test synchronous Logged aspect wrapper."""

    def test_logged_wrapper_preserves_function_result(self) -> None:
        """Logged wrapper preserves function return value."""
        logged = objs.Logged(event="test.operation")
        wrapper_factory = logged.build()

        def operation(value: int) -> int:
            return value * 2

        wrapped = wrapper_factory(operation)
        result = wrapped(5)

        assert result == 10

    def test_logged_wrapper_propagates_exceptions(self) -> None:
        """Logged wrapper propagates exceptions from wrapped function."""
        logged = objs.Logged(event="test.operation")
        wrapper_factory = logged.build()

        def operation(value: int) -> int:
            raise ValueError("test error")

        wrapped = wrapper_factory(operation)

        with pytest.raises(ValueError, match="test error"):
            wrapped(5)

    def test_logged_wrapper_with_payload_extractors(self) -> None:
        """Logged wrapper processes payload extractors without errors."""

        def extract_request(x: object) -> dict:
            return {"input": x}

        def extract_result(result: object) -> dict:
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

    def test_logged_wrapper_guards_extraction_failures(self) -> None:
        """Logged wrapper guards against extraction errors and continues."""

        def bad_extractor(x: int) -> dict:
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


class TestLoggedWrapperAsync:
    """Test asynchronous Logged aspect wrapper."""

    def test_logged_wrapper_async_preserves_result(self) -> None:
        """Logged wrapper preserves async function return value."""
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

    def test_logged_wrapper_async_propagates_exceptions(self) -> None:
        """Logged wrapper propagates exceptions from async function."""
        logged = objs.Logged(event="test.operation")
        wrapper_factory = logged.build()

        async def operation(value: int) -> int:
            raise ValueError("test error")

        wrapped = wrapper_factory(operation)

        async def run_test() -> None:
            with pytest.raises(ValueError, match="test error"):
                await wrapped(5)

        asyncio.run(run_test())
