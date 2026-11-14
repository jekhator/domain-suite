"""Internal builders for @retried aspect wrapper generation (containerized per R004/R009)."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from typing import TYPE_CHECKING

from domain_aspects.services.aspects.aspects_class_fanout import ClassFanout
from domain_aspects.services.constants import aspects as const

if TYPE_CHECKING:
    from mixin_retry import RetryPolicy


class _RetriedBuilders:
    """Container for @retried aspect builder/decorator functions per strict-module R004/R009."""

    @staticmethod
    def build_retried_wrapper(
        target: Callable,
        policy: RetryPolicy | None,
        policy_from_request: Callable[..., RetryPolicy | None] | None,
    ) -> Callable:
        """Build retry wrapper for a single callable with optional dynamic policy."""
        from mixin_retry import RetryExecutor

        executor = RetryExecutor()

        if policy is not None:
            wrapped_fn = executor.wrap(target, policy)
            setattr(wrapped_fn, const.RETRIED_APPLIED_MARKER, True)
            return wrapped_fn

        if policy_from_request is None:  # pragma: no cover
            # Retried.__post_init__ guarantees exactly one policy source.
            raise ValueError(const.ERR_ASPECT_RETRIED_POLICY_FROM_REQUEST_REQUIRED)

        selector = policy_from_request
        if asyncio.iscoroutinefunction(target):

            @functools.wraps(target)
            async def async_wrapper_dynamic(*args: object, **kwargs: object) -> object:
                call_policy = selector(*args, **kwargs)
                if call_policy is None:
                    return await target(*args, **kwargs)
                wrapped_fn = executor.wrap(target, call_policy)
                return await wrapped_fn(*args, **kwargs)

            setattr(async_wrapper_dynamic, const.RETRIED_APPLIED_MARKER, True)
            return async_wrapper_dynamic

        @functools.wraps(target)
        def sync_wrapper_dynamic(*args: object, **kwargs: object) -> object:
            call_policy = selector(*args, **kwargs)
            if call_policy is None:
                return target(*args, **kwargs)
            wrapped_fn = executor.wrap(target, call_policy)
            return wrapped_fn(*args, **kwargs)

        setattr(sync_wrapper_dynamic, const.RETRIED_APPLIED_MARKER, True)
        return sync_wrapper_dynamic

    @staticmethod
    def decorate_class_retried(
        target_class: type,
        policy: RetryPolicy | None,
        policy_from_request: Callable[..., RetryPolicy | None] | None,
    ) -> type:
        """Fan out @retried over all public methods in the class.

        Rules:
        - Only methods in the class dict (not inherited)
        - Skip: _-prefixed, dunders, properties, nested classes
        - Preserve: classmethod/staticmethod via unwrap/rewrap
        - Override: methods already marked with RETRIED_APPLIED_MARKER are left untouched
        """

        def decorate(method: Callable[..., object]) -> Callable[..., object]:
            return _RetriedBuilders.build_retried_wrapper(
                method, policy, policy_from_request
            )

        return ClassFanout.decorate_class(
            target_class, const.RETRIED_APPLIED_MARKER, decorate
        )
