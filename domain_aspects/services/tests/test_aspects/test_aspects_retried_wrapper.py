"""Tests for Retried aspect wrapper implementation."""

from __future__ import annotations

import pytest
from mixin_retry import RetryPolicy

from domain_aspects.services.aspects import aspects_objects as objs


def _make_policy() -> RetryPolicy:
    """Create a test retry policy."""
    return RetryPolicy(
        max_attempts=3,
        backoff_base_seconds=0.1,
        backoff_multiplier=2.0,
        backoff_max_seconds=10.0,
        jitter=False,
    )


class TestRetriedWrapperSync:
    """Test synchronous Retried aspect wrapper."""

    def test_retried_wrapper_succeeds_on_first_attempt(self) -> None:
        """Retried wrapper returns result on first successful attempt."""
        policy = _make_policy()
        retried = objs.Retried(policy=policy)
        wrapper_factory = retried.build()

        def operation(value: int) -> int:
            return value * 2

        wrapped = wrapper_factory(operation)
        result = wrapped(5)

        assert result == 10

    def test_retried_wrapper_retries_on_predicate_match(self) -> None:
        """Retried wrapper retries when predicate matches."""

        def should_retry(exc: BaseException) -> bool:
            return isinstance(exc, ValueError)

        policy = RetryPolicy(
            max_attempts=3,
            backoff_base_seconds=0.001,
            backoff_multiplier=1.0,
            backoff_max_seconds=1.0,
            jitter=False,
            should_retry=should_retry,
        )
        retried = objs.Retried(policy=policy)
        wrapper_factory = retried.build()

        call_count = 0

        def operation(value: int) -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("retry me")
            return value * 2

        wrapped = wrapper_factory(operation)
        result = wrapped(5)

        assert result == 10
        assert call_count == 3

    def test_retried_wrapper_exhausts_retries(self) -> None:
        """Retried wrapper raises after exhausting retries."""

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
        retried = objs.Retried(policy=policy)
        wrapper_factory = retried.build()

        def operation(value: int) -> int:
            raise ValueError("always fails")

        wrapped = wrapper_factory(operation)

        with pytest.raises(ValueError, match="always fails"):
            wrapped(5)

    def test_retried_wrapper_with_dynamic_policy_selector(self) -> None:
        """Retried wrapper uses dynamic policy from selector."""

        def policy_selector(value: int) -> RetryPolicy | None:
            if value > 0:
                return RetryPolicy(
                    max_attempts=3,
                    backoff_base_seconds=0.001,
                    backoff_multiplier=1.0,
                    backoff_max_seconds=1.0,
                    jitter=False,
                    should_retry=lambda e: isinstance(e, ValueError),
                )
            return None

        retried = objs.Retried(policy_from_request=policy_selector)
        wrapper_factory = retried.build()

        call_count = 0

        def operation(value: int) -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("retry me")
            return value * 2

        wrapped = wrapper_factory(operation)
        result = wrapped(5)

        assert result == 10
        assert call_count == 2

    def test_retried_wrapper_with_selector_returns_none(self) -> None:
        """Retried wrapper skips retries when selector returns None."""

        def policy_selector(value: int) -> RetryPolicy | None:
            return None

        retried = objs.Retried(policy_from_request=policy_selector)
        wrapper_factory = retried.build()

        def operation(value: int) -> int:
            raise ValueError("no retry")

        wrapped = wrapper_factory(operation)

        with pytest.raises(ValueError, match="no retry"):
            wrapped(5)
