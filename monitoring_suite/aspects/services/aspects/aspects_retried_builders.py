"""Internal builders for @retried aspect wrapper generation (containerized per R004/R009)."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from mixin_retry import RetryPolicy

RETRIED_MARKER = "__retried_applied__"


class _RetriedBuilders:
    """Container for @retried aspect builder/decorator functions per strict-module R004/R009."""

    @staticmethod
    def build_retried_wrapper(
        target: Callable,
        policy: Optional[RetryPolicy],
        policy_from_request: Optional[Callable[..., Optional[RetryPolicy]]],
    ) -> Callable:
        """Build retry wrapper for a single callable with optional dynamic policy."""
        from mixin_retry import RetryExecutor

        executor = RetryExecutor()

        if policy is not None:
            wrapped_fn = executor.wrap(target, policy)
            setattr(wrapped_fn, RETRIED_MARKER, True)
            return wrapped_fn

        assert policy_from_request is not None
        if asyncio.iscoroutinefunction(target):

            @functools.wraps(target)
            async def async_wrapper_dynamic(*args: object, **kwargs: object) -> object:
                call_policy = policy_from_request(*args, **kwargs)
                if call_policy is None:
                    return await target(*args, **kwargs)
                wrapped_fn = executor.wrap(target, call_policy)
                return await wrapped_fn(*args, **kwargs)

            setattr(async_wrapper_dynamic, RETRIED_MARKER, True)
            return async_wrapper_dynamic

        @functools.wraps(target)
        def sync_wrapper_dynamic(*args: object, **kwargs: object) -> object:
            call_policy = policy_from_request(*args, **kwargs)
            if call_policy is None:
                return target(*args, **kwargs)
            wrapped_fn = executor.wrap(target, call_policy)
            return wrapped_fn(*args, **kwargs)

        setattr(sync_wrapper_dynamic, RETRIED_MARKER, True)
        return sync_wrapper_dynamic

    @staticmethod
    def decorate_class_retried(
        cls: type[object],
        policy: Optional[RetryPolicy],
        policy_from_request: Optional[Callable[..., Optional[RetryPolicy]]],
    ) -> type[object]:
        """Fan out @retried over all public methods in the class.

        Rules:
        - Only methods in cls.__dict__ (not inherited)
        - Skip: _-prefixed, dunders, properties, nested classes
        - Preserve: classmethod/staticmethod via unwrap/rewrap
        - Override: methods already marked with RETRIED_MARKER are left untouched
        """
        for name, method in list(cls.__dict__.items()):
            if name.startswith("_"):
                continue
            if isinstance(method, property):
                continue
            if isinstance(method, type):
                continue

            is_classmethod = isinstance(method, classmethod)
            is_staticmethod = isinstance(method, staticmethod)

            if is_classmethod or is_staticmethod:
                unwrapped = method.__func__
            else:
                unwrapped = method

            if not callable(unwrapped):
                continue

            if hasattr(unwrapped, RETRIED_MARKER):
                continue

            decorated = _RetriedBuilders.build_retried_wrapper(
                unwrapped,
                policy,
                policy_from_request,
            )

            if is_classmethod:
                setattr(cls, name, classmethod(decorated))
            elif is_staticmethod:
                setattr(cls, name, staticmethod(decorated))
            else:
                setattr(cls, name, decorated)

        return cls
