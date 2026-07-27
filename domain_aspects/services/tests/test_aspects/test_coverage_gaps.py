"""Tests for coverage gaps: ambient logging, extraction failures, async retried None."""

from __future__ import annotations

import asyncio

import pytest
from mixin_logging import LoggingMixin
from mixin_retry import RetryPolicy

from domain_aspects.services.aspects import aspects_objects as objs

ERR_ASYNC_RETRIED_NO_RETRY = "async.retried.none.policy"


class TestAsyncRetriedNonePolicy:
    """Test async Retried selector returning None (line 258)."""

    def test_async_retried_dynamic_none_policy_no_retry(self) -> None:
        """Async retried with None policy returns immediately without retry."""

        def policy_selector(value: int) -> RetryPolicy | None:
            return None

        retried = objs.Retried(policy_from_request=policy_selector)
        wrapper_factory = retried.build()

        call_count = 0

        async def async_op(value: int) -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError(ERR_ASYNC_RETRIED_NO_RETRY)
            await asyncio.sleep(0.001)
            return value * 10

        wrapped = wrapper_factory(async_op)

        async def run() -> None:
            with pytest.raises(ValueError, match=ERR_ASYNC_RETRIED_NO_RETRY):
                await wrapped(5)
            assert call_count == 1

        asyncio.run(run())

    def test_async_retried_dynamic_none_raises_immediately(self) -> None:
        """Async retried with None policy propagates exception on first call."""

        def policy_selector(*args, **kwargs) -> None:
            return None

        retried = objs.Retried(policy_from_request=policy_selector)
        wrapper_factory = retried.build()

        async def failing_op() -> int:
            raise RuntimeError("immediate failure")

        wrapped = wrapper_factory(failing_op)

        async def run() -> None:
            with pytest.raises(RuntimeError, match="immediate failure"):
                await wrapped()

        asyncio.run(run())


class TestAmbientLoggingAsync:
    """Test Logged aspect on non-LoggingMixin async targets (lines 295, 309, 327, 346)."""

    def test_logged_async_ambient_start_end_success(self) -> None:
        """Logged async on plain function uses ambient log_info for start/end."""
        logged = objs.Logged(event="ambient.async.start.end")
        wrapper_factory = logged.build()

        async def plain_async_fn(value: int) -> int:
            await asyncio.sleep(0.001)
            return value * 2

        wrapped = wrapper_factory(plain_async_fn)

        async def run() -> None:
            result = await wrapped(5)
            assert result == 10

        asyncio.run(run())

    def test_logged_async_ambient_error_path(self) -> None:
        """Logged async on plain function uses ambient log_error for exceptions."""
        logged = objs.Logged(event="ambient.async.error")
        wrapper_factory = logged.build()

        async def failing_async_fn() -> int:
            await asyncio.sleep(0.001)
            raise ValueError("test error")

        wrapped = wrapper_factory(failing_async_fn)

        async def run() -> None:
            with pytest.raises(ValueError):
                await wrapped()

        asyncio.run(run())


class TestAmbientLoggingSync:
    """Test Logged aspect on non-LoggingMixin sync targets (lines 358, 372, 390, 409)."""

    def test_logged_sync_ambient_start_end_success(self) -> None:
        """Logged sync on plain function uses ambient log_info for start/end."""
        logged = objs.Logged(event="ambient.sync.start.end")
        wrapper_factory = logged.build()

        def plain_fn(value: int) -> int:
            return value * 2

        wrapped = wrapper_factory(plain_fn)
        result = wrapped(5)
        assert result == 10

    def test_logged_sync_ambient_error_path(self) -> None:
        """Logged sync on plain function uses ambient log_error for exceptions."""
        logged = objs.Logged(event="ambient.sync.error")
        wrapper_factory = logged.build()

        def failing_fn() -> int:
            raise ValueError("test error")

        wrapped = wrapper_factory(failing_fn)

        with pytest.raises(ValueError):
            wrapped()

    def test_logged_sync_ambient_with_bad_result_extractor(self) -> None:
        """Logged sync ambient logs extraction failure in .end path."""

        def extract_result(result) -> dict:
            raise RuntimeError("extraction broke")

        logged = objs.Logged(
            event="ambient.sync.result.extract",
            payload_from_result=extract_result,
        )
        wrapper_factory = logged.build()

        def plain_fn(value: int) -> int:
            return value * 2

        wrapped = wrapper_factory(plain_fn)
        result = wrapped(5)
        assert result == 10

    def test_logged_sync_ambient_with_bad_error_extractor(self) -> None:
        """Logged sync ambient logs extraction failure in .error path."""

        def extract_exc(exc: BaseException) -> dict:
            raise RuntimeError("error extraction broke")

        logged = objs.Logged(
            event="ambient.sync.error.extract",
            payload_from_exc=extract_exc,
        )
        wrapper_factory = logged.build()

        def failing_fn() -> int:
            raise ValueError("base error")

        wrapped = wrapper_factory(failing_fn)

        with pytest.raises(ValueError):
            wrapped()


class TestSyncExtractionFailures:
    """Test sync wrapper extraction failure paths (lines 382-387, 390, 409)."""

    def test_logged_sync_result_extraction_failure_continues(self) -> None:
        """Sync logged handles payload_from_result exception and continues (lines 382-387)."""

        def bad_result_extractor(result) -> dict:
            raise RuntimeError("extraction failure")

        logged = objs.Logged(
            event="sync.result.extract",
            payload_from_result=bad_result_extractor,
        )
        wrapper_factory = logged.build()

        def op(value: int) -> int:
            return value * 2

        wrapped = wrapper_factory(op)

        result = wrapped(42)
        assert result == 84

    def test_logged_sync_result_extraction_failure_end_logged_ambient(self) -> None:
        """Sync logged .end emitted even when payload_from_result fails (line 390 ambient)."""

        def bad_extractor(result) -> dict:
            raise RuntimeError("extraction error")

        logged = objs.Logged(
            event="sync.end.ambient",
            payload_from_result=bad_extractor,
        )
        wrapper_factory = logged.build()

        def op(value: int) -> int:
            return value * 2

        wrapped = wrapper_factory(op)

        result = wrapped(42)
        assert result == 84

    def test_logged_sync_error_extraction_failure_ambient(self) -> None:
        """Sync logged .error emitted even when payload_from_exc fails (line 409 ambient)."""

        def bad_error_extractor(exc: BaseException) -> dict:
            raise RuntimeError("error extraction error")

        logged = objs.Logged(
            event="sync.error.ambient",
            payload_from_exc=bad_error_extractor,
        )
        wrapper_factory = logged.build()

        def failing_op() -> int:
            raise ValueError("original error")

        wrapped = wrapper_factory(failing_op)

        with pytest.raises(ValueError):
            wrapped()


class TestLoggedWithMixinInstance:
    """Test Logged aspect on LoggingMixin instances for logger.log_* paths."""

    def test_logged_sync_with_mixin_instance(self) -> None:
        """Logged sync on mixin instance calls logger.log_info (lines 372, 390, 409)."""

        service = LoggingMixin()

        def operation(svc: LoggingMixin, value: int) -> int:
            return value * 3

        logged = objs.Logged(event="mixin.sync")
        wrapper_factory = logged.build()

        wrapped = wrapper_factory(operation)
        result = wrapped(service, 5)
        assert result == 15

    def test_logged_async_with_mixin_instance(self) -> None:
        """Logged async on mixin instance calls logger.log_info."""

        service = LoggingMixin()

        async def operation(svc: LoggingMixin, value: int) -> int:
            await asyncio.sleep(0.001)
            return value * 3

        logged = objs.Logged(event="mixin.async")
        wrapper_factory = logged.build()

        wrapped = wrapper_factory(operation)

        async def run() -> None:
            result = await wrapped(service, 5)
            assert result == 15

        asyncio.run(run())

    def test_logged_sync_mixin_error_path_logger_error(self) -> None:
        """Logged sync mixin error path calls logger.log_error (line 409)."""

        service = LoggingMixin()

        def failing_op(svc: LoggingMixin, value: int) -> int:
            raise ValueError("error in mixin")

        logged = objs.Logged(event="mixin.error")
        wrapper_factory = logged.build()

        wrapped = wrapper_factory(failing_op)

        with pytest.raises(ValueError):
            wrapped(service, 5)

    def test_logged_async_mixin_error_path_logger_error(self) -> None:
        """Logged async mixin error path calls logger.log_error (line 346)."""

        service = LoggingMixin()

        async def failing_op(svc: LoggingMixin, value: int) -> int:
            await asyncio.sleep(0.001)
            raise ValueError("error in async mixin")

        logged = objs.Logged(event="mixin.async.error")
        wrapper_factory = logged.build()

        wrapped = wrapper_factory(failing_op)

        async def run() -> None:
            with pytest.raises(ValueError):
                await wrapped(service, 5)

        asyncio.run(run())


class TestAsyncExtractionFailures:
    """Test async wrapper extraction failure paths."""

    def test_logged_async_result_extraction_failure(self) -> None:
        """Async logged handles payload_from_result exception (lines 316-324)."""

        def bad_result_extractor(result) -> dict:
            raise RuntimeError("result extraction failed")

        logged = objs.Logged(
            event="async.result.extract",
            payload_from_result=bad_result_extractor,
        )
        wrapper_factory = logged.build()

        async def op(value: int) -> int:
            await asyncio.sleep(0.001)
            return value * 2

        wrapped = wrapper_factory(op)

        async def run() -> None:
            result = await wrapped(42)
            assert result == 84

        asyncio.run(run())

    def test_logged_async_error_extraction_failure(self) -> None:
        """Async logged handles payload_from_exc exception."""

        def bad_error_extractor(exc: BaseException) -> dict:
            raise RuntimeError("error extraction failed")

        logged = objs.Logged(
            event="async.error.extract",
            payload_from_exc=bad_error_extractor,
        )
        wrapper_factory = logged.build()

        async def failing_op() -> int:
            await asyncio.sleep(0.001)
            raise ValueError("original error")

        wrapped = wrapper_factory(failing_op)

        async def run() -> None:
            with pytest.raises(ValueError):
                await wrapped()

        asyncio.run(run())
