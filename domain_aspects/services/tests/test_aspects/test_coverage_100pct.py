"""Coverage-driven tests: async paths, error cases, ordering integration."""

from __future__ import annotations

import asyncio

import pytest
from mixin_retry import RetryPolicy

from domain_aspects.services.aspects import aspects_objects as objs
from domain_aspects.services.aspects.aspects_client import Aspects


class TestLoggedAsyncPaths:
    """Test async legs of Logged wrapper for 100% coverage."""

    def test_logged_async_all_payload_types(self) -> None:
        """Logged async with all payload extraction types exercised."""

        def extract_request(*args, **kwargs) -> dict:
            return {"req_key": "req_val"}

        def extract_result(result) -> dict:
            return {"res_key": result}

        def extract_exc(exc: BaseException) -> dict:
            return {"exc_msg": str(exc)}

        logged = objs.Logged(
            event="test.async",
            payload_from_request=extract_request,
            payload_from_result=extract_result,
            payload_from_exc=extract_exc,
        )
        wrapper = logged.build()

        async def async_op(value: int) -> int:
            await asyncio.sleep(0.001)
            return value * 2

        wrapped = wrapper(async_op)

        async def run() -> None:
            result = await wrapped(5)
            assert result == 10

        asyncio.run(run())

    def test_logged_async_exception_with_payloads(self) -> None:
        """Logged async exception path with payload extraction."""

        def extract_exc(exc: BaseException) -> dict:
            return {"error_msg": str(exc)}

        logged = objs.Logged(
            event="test.async.error",
            payload_from_exc=extract_exc,
        )
        wrapper = logged.build()

        async def async_op_fail() -> None:
            await asyncio.sleep(0.001)
            raise ValueError("async error")

        wrapped = wrapper(async_op_fail)

        async def run() -> None:
            with pytest.raises(ValueError, match="async error"):
                await wrapped()

        asyncio.run(run())

    def test_logged_async_bad_payload_extractor_guards(self) -> None:
        """Logged async guarded extraction in all paths."""

        def bad_request(*args, **kwargs) -> dict:
            raise RuntimeError("request extract failed")

        def bad_result(result) -> dict:
            raise RuntimeError("result extract failed")

        def bad_exc(exc: BaseException) -> dict:
            raise RuntimeError("exc extract failed")

        logged = objs.Logged(
            event="test.guards",
            payload_from_request=bad_request,
            payload_from_result=bad_result,
            payload_from_exc=bad_exc,
        )
        wrapper = logged.build()

        async def async_op(value: int) -> int:
            await asyncio.sleep(0.001)
            return value

        wrapped = wrapper(async_op)

        async def run() -> None:
            result = await wrapped(42)
            assert result == 42

        asyncio.run(run())

    def test_logged_async_bad_exc_extractor_during_exception(self) -> None:
        """Logged async exception with bad extraction in exception handler."""

        def bad_exc(exc: BaseException) -> dict:
            raise RuntimeError("double fault")

        logged = objs.Logged(
            event="test.double.fault",
            payload_from_exc=bad_exc,
        )
        wrapper = logged.build()

        async def async_op_fail() -> None:
            await asyncio.sleep(0.001)
            raise ValueError("initial error")

        wrapped = wrapper(async_op_fail)

        async def run() -> None:
            with pytest.raises(ValueError, match="initial error"):
                await wrapped()

        asyncio.run(run())


class TestRetriedBothForms:
    """Test both static and dynamic Retried forms for full coverage."""

    def test_retried_static_on_callable(self) -> None:
        """Retried static policy applied to callable."""
        policy = RetryPolicy(
            max_attempts=2,
            backoff_base_seconds=0.001,
            backoff_multiplier=1.0,
            backoff_max_seconds=1.0,
            jitter=False,
            should_retry=lambda e: isinstance(e, ValueError),
        )
        retried = objs.Retried(policy=policy)
        wrapper = retried.build()

        call_count = 0

        def op() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("retry")
            return 99

        wrapped = wrapper(op)
        result = wrapped()
        assert result == 99
        assert call_count == 2

    def test_retried_dynamic_with_none_policy(self) -> None:
        """Retried dynamic selector returns None, no retry."""

        def selector(*args, **kwargs) -> None:
            return None

        retried = objs.Retried(policy_from_request=selector)
        wrapper = retried.build()

        call_count = 0

        def op() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail")
            return 99

        wrapped = wrapper(op)

        with pytest.raises(ValueError, match="fail"):
            wrapped()

        assert call_count == 1

    def test_retried_dynamic_async(self) -> None:
        """Retried dynamic policy for async function."""

        def selector(value: int):
            if value > 0:
                return RetryPolicy(
                    max_attempts=2,
                    backoff_base_seconds=0.001,
                    backoff_multiplier=1.0,
                    backoff_max_seconds=1.0,
                    jitter=False,
                    should_retry=lambda e: isinstance(e, ValueError),
                )
            return None

        retried = objs.Retried(policy_from_request=selector)
        wrapper = retried.build()

        call_count = 0

        async def async_op(value: int) -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("retry")
            await asyncio.sleep(0.001)
            return value * 10

        wrapped = wrapper(async_op)

        async def run() -> None:
            result = await wrapped(5)
            assert result == 50
            assert call_count == 2

        asyncio.run(run())


class TestOrderingIntegration:
    """Test aspect ordering: retries see raw exceptions before wrap_errors."""

    def test_retried_and_logged_composition(self) -> None:
        """Retried and Logged aspects compose correctly."""
        aspects_svc = Aspects()

        def should_retry(exc: BaseException) -> bool:
            return isinstance(exc, ValueError)

        policy = RetryPolicy(
            max_attempts=2,
            backoff_base_seconds=0.001,
            backoff_multiplier=1.0,
            backoff_max_seconds=1.0,
            jitter=False,
            should_retry=should_retry,
        )

        call_count = 0

        @aspects_svc(
            objs.Logged(event="composition.test"),
            objs.Retried(policy=policy),
        )
        def op() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("retry")
            return 100

        result = op()
        assert result == 100
        assert call_count == 2


class TestSyncExceptionPaths:
    """Test sync wrapper exception handling paths for 100% coverage."""

    def test_logged_sync_exception_without_extractors(self) -> None:
        """Logged sync exception without payload extractors."""
        logged = objs.Logged(event="test.exc.no.extract")
        wrapper = logged.build()

        def op_fail() -> None:
            raise RuntimeError("test error")

        wrapped = wrapper(op_fail)

        with pytest.raises(RuntimeError, match="test error"):
            wrapped()

    def test_logged_sync_exception_with_bad_payload_extractors(self) -> None:
        """Logged sync exception with multiple failing extractors."""

        def extract_exc(exc: BaseException) -> dict:
            raise RuntimeError("extraction error")

        logged = objs.Logged(
            event="test.bad.extract",
            payload_from_exc=extract_exc,
        )
        wrapper = logged.build()

        def op_fail() -> None:
            raise ValueError("base error")

        wrapped = wrapper(op_fail)

        with pytest.raises(ValueError, match="base error"):
            wrapped()

    def test_logged_sync_result_extraction_error_then_bad_error_extractor(self) -> None:
        """Logged sync with bad result extractor followed by exception."""

        def extract_result(result) -> dict:
            raise RuntimeError("result error")

        def extract_exc(exc: BaseException) -> dict:
            raise RuntimeError("exc error")

        logged = objs.Logged(
            event="test.cascade",
            payload_from_result=extract_result,
            payload_from_exc=extract_exc,
        )
        wrapper = logged.build()

        def op_fail() -> None:
            raise TypeError("type error")

        wrapped = wrapper(op_fail)

        with pytest.raises(TypeError, match="type error"):
            wrapped()
