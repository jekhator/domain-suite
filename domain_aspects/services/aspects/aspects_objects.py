"""Aspect entry value objects for decorator composition."""

from __future__ import annotations

import asyncio
import functools
import inspect
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Optional, TypeVar

from domain_aspects.services.constants import aspects as const

if TYPE_CHECKING:
    from mixin_retry import RetryPolicy

    from domain_monitoring.services.metrics.metrics_client import MetricSink

T = TypeVar("T")

LOGGED_MARKER = "__logged_applied__"
RETRIED_MARKER = "__retried_applied__"


class AspectKind(StrEnum):
    """Aspect classification kinds."""

    LOGGED = "LOGGED"
    REQUIRES = "REQUIRES"
    TENANT_SCOPED = "TENANT_SCOPED"
    THROTTLED = "THROTTLED"
    MONITORED = "MONITORED"
    WRAP_ERRORS = "WRAP_ERRORS"
    RETRIED = "RETRIED"


@dataclass(frozen=True, slots=True)
class Logged:
    """Native event logging with entry/exit/error emissions and optional timing.

    Emits structured events via instance LoggingMixin.log_* or ambient mixin_logging functions.
    """

    event: str
    payload_from_request: Optional[Callable[..., dict]] = None
    payload_from_result: Optional[Callable[[object], dict]] = None
    payload_from_exc: Optional[Callable[[BaseException], dict]] = None
    timed: bool = False

    def __post_init__(self) -> None:
        if not self.event or not isinstance(self.event, str):
            raise ValueError(const.ERR_ASPECT_LOGGED_EVENT_EMPTY)

    @property
    def kind(self) -> AspectKind:
        return AspectKind.LOGGED

    def build(self) -> Callable:
        """Build native logged wrapper for function/method or class targets."""
        event = self.event
        payload_from_request = self.payload_from_request
        payload_from_result = self.payload_from_result
        payload_from_exc = self.payload_from_exc
        timed = self.timed

        def decorator(target: Callable) -> Callable:
            if inspect.isclass(target):
                return self._decorate_class_logged(
                    target,
                    event,
                    payload_from_request,
                    payload_from_result,
                    payload_from_exc,
                    timed,
                )
            return self._build_logged_wrapper(
                target,
                event,
                payload_from_request,
                payload_from_result,
                payload_from_exc,
                timed,
            )

        return decorator

    @staticmethod
    def _build_logged_wrapper(
        target: Callable,
        event: str,
        payload_from_request: Optional[Callable[..., dict]],
        payload_from_result: Optional[Callable[[object], dict]],
        payload_from_exc: Optional[Callable[[BaseException], dict]],
        timed: bool,
    ) -> Callable:
        """Build native wrapper for logging entry/exit/error events.

        Emits via instance's LoggingMixin.log_* if available, else ambient log_* functions.
        Extractions are guarded: errors log WARNING, operation continues.
        """
        from mixin_logging import LoggingMixin, log_error, log_info

        if asyncio.iscoroutinefunction(target):

            @functools.wraps(target)
            async def async_logged(*args: object, **kwargs: object) -> object:
                logger = None
                if args and isinstance(args[0], LoggingMixin):
                    logger = args[0]

                start_payload: dict = {}
                if payload_from_request:
                    try:
                        start_payload = payload_from_request(*args, **kwargs) or {}
                    except Exception as e:
                        log_error(
                            f"Logged: extraction failed for {event}.start",
                            error=str(e),
                        )
                        start_payload = {}

                if logger:
                    logger.log_info(f"{event}.start", **start_payload)
                else:
                    log_info(f"{event}.start", **start_payload)

                try:
                    result = await target(*args, **kwargs)
                    end_payload: dict = {}
                    if payload_from_result:
                        try:
                            end_payload = payload_from_result(result) or {}
                        except Exception as e:
                            log_error(
                                f"Logged: extraction failed for {event}.end",
                                error=str(e),
                            )
                            end_payload = {}

                    if logger:
                        logger.log_info(f"{event}.end", **end_payload)
                    else:
                        log_info(f"{event}.end", **end_payload)

                    return result
                except BaseException as e:
                    error_payload: dict = {
                        "error_type": type(e).__name__,
                    }
                    if payload_from_exc:
                        try:
                            error_payload.update(payload_from_exc(e) or {})
                        except Exception as extraction_error:
                            log_error(
                                f"Logged: extraction failed for {event}.error",
                                error=str(extraction_error),
                            )

                    if logger:
                        logger.log_error(f"{event}.error", **error_payload)
                    else:
                        log_error(f"{event}.error", **error_payload)

                    raise

            return async_logged
        else:

            @functools.wraps(target)
            def sync_logged(*args: object, **kwargs: object) -> object:
                logger = None
                if args and isinstance(args[0], LoggingMixin):
                    logger = args[0]

                start_payload: dict = {}
                if payload_from_request:
                    try:
                        start_payload = payload_from_request(*args, **kwargs) or {}
                    except Exception as e:
                        log_error(
                            f"Logged: extraction failed for {event}.start",
                            error=str(e),
                        )
                        start_payload = {}

                if logger:
                    logger.log_info(f"{event}.start", **start_payload)
                else:
                    log_info(f"{event}.start", **start_payload)

                try:
                    result = target(*args, **kwargs)
                    end_payload: dict = {}
                    if payload_from_result:
                        try:
                            end_payload = payload_from_result(result) or {}
                        except Exception as e:
                            log_error(
                                f"Logged: extraction failed for {event}.end",
                                error=str(e),
                            )
                            end_payload = {}

                    if logger:
                        logger.log_info(f"{event}.end", **end_payload)
                    else:
                        log_info(f"{event}.end", **end_payload)

                    return result
                except BaseException as e:
                    error_payload: dict = {
                        "error_type": type(e).__name__,
                    }
                    if payload_from_exc:
                        try:
                            error_payload.update(payload_from_exc(e) or {})
                        except Exception as extraction_error:
                            log_error(
                                f"Logged: extraction failed for {event}.error",
                                error=str(extraction_error),
                            )

                    if logger:
                        logger.log_error(f"{event}.error", **error_payload)
                    else:
                        log_error(f"{event}.error", **error_payload)

                    raise

            return sync_logged

    @staticmethod
    def _decorate_class_logged(
        cls: type[object],
        event: str,
        payload_from_request: Optional[Callable[..., dict]],
        payload_from_result: Optional[Callable[[object], dict]],
        payload_from_exc: Optional[Callable[[BaseException], dict]],
        timed: bool,
    ) -> type[object]:
        """Fan out @logged over all public methods in the class.

        Rules:
        - Only methods in cls.__dict__ (not inherited)
        - Skip: _-prefixed, dunders, properties, nested classes
        - Preserve: classmethod/staticmethod via unwrap/rewrap
        - Override: methods already marked with LOGGED_MARKER are left untouched
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

            if hasattr(unwrapped, LOGGED_MARKER):
                continue

            decorated = Logged._build_logged_wrapper(
                unwrapped,
                event,
                payload_from_request,
                payload_from_result,
                payload_from_exc,
                timed,
            )
            setattr(decorated, LOGGED_MARKER, True)

            if is_classmethod:
                setattr(cls, name, classmethod(decorated))
            elif is_staticmethod:
                setattr(cls, name, staticmethod(decorated))
            else:
                setattr(cls, name, decorated)

        return cls


@dataclass(frozen=True, slots=True)
class Requires:
    """Permission check via domain-security."""

    permission: str

    def __post_init__(self) -> None:
        if not self.permission or not isinstance(self.permission, str):
            raise ValueError(const.ERR_ASPECT_REQUIRES_PERMISSION_EMPTY)

    @property
    def kind(self) -> AspectKind:
        return AspectKind.REQUIRES

    def build(self) -> Callable:
        """Lazily import and apply requires decorator."""
        try:
            from domain_security.decorators.requires import requires
        except ImportError as e:
            raise ImportError(const.ERR_ASPECT_REQUIRES_IMPORT_MISSING) from e
        return requires(self.permission)


@dataclass(frozen=True, slots=True)
class TenantScoped:
    """Tenant isolation enforcement via domain-security."""

    param_name: str = "tenant_id"

    def __post_init__(self) -> None:
        if not self.param_name or not isinstance(self.param_name, str):
            raise ValueError(const.ERR_ASPECT_TENANT_SCOPED_PARAM_EMPTY)

    @property
    def kind(self) -> AspectKind:
        return AspectKind.TENANT_SCOPED

    def build(self) -> Callable:
        """Lazily import and apply tenant_scoped decorator."""
        try:
            from domain_security.decorators.tenant_scoped import tenant_scoped
        except ImportError as e:
            raise ImportError(const.ERR_ASPECT_TENANT_SCOPED_IMPORT_MISSING) from e
        return tenant_scoped(self.param_name)


@dataclass(frozen=True, slots=True)
class Throttled:
    """Rate limiting via domain-api-limiter."""

    scope: str
    rate: str
    tiers: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.scope or not isinstance(self.scope, str):
            raise ValueError(const.ERR_ASPECT_THROTTLED_SCOPE_EMPTY)
        if not self.rate or not isinstance(self.rate, str):
            raise ValueError(const.ERR_ASPECT_THROTTLED_RATE_EMPTY)
        if not isinstance(self.tiers, tuple):
            raise ValueError(const.ERR_ASPECT_THROTTLED_TIERS_NOT_TUPLE)

    @property
    def kind(self) -> AspectKind:
        return AspectKind.THROTTLED

    def build(self) -> Callable:
        """Lazily import and apply throttled decorator."""
        try:
            from domain_api_limiter.decorators.throttled import throttled
        except ImportError as e:
            raise ImportError(const.ERR_ASPECT_THROTTLED_IMPORT_MISSING) from e
        tiers_dict = dict(self.tiers) if self.tiers else None
        return throttled(self.scope, self.rate, tiers=tiers_dict)


@dataclass(frozen=True, slots=True)
class WrapErrors:
    """Exception wrapping and translation via domain-errors."""

    as_: type
    catch: tuple[type[BaseException], ...] = (Exception,)

    def __post_init__(self) -> None:
        if not isinstance(self.as_, type):
            raise ValueError(const.ERR_ASPECT_WRAP_ERRORS_AS_NOT_CLASS)
        if not self.catch or not isinstance(self.catch, tuple):
            raise ValueError(const.ERR_ASPECT_WRAP_ERRORS_CATCH_INVALID)

    @property
    def kind(self) -> AspectKind:
        return AspectKind.WRAP_ERRORS

    def build(self) -> Callable:
        """Import and apply wrap_errors decorator."""
        try:
            from domain_errors import wrap_errors
        except ImportError as e:
            raise ImportError(const.ERR_ASPECT_WRAP_ERRORS_IMPORT_MISSING) from e
        return wrap_errors(as_=self.as_, catch=self.catch)  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class Monitored:
    """Metric emission via domain-monitoring."""

    event: str
    sink: Optional[MetricSink] = None
    labels_from_result: Optional[Callable[[object], tuple[tuple[str, str], ...]]] = None
    labels_from_exc: Optional[
        Callable[[BaseException], tuple[tuple[str, str], ...]]
    ] = None

    def __post_init__(self) -> None:
        if not self.event or not isinstance(self.event, str):
            raise ValueError(const.ERR_ASPECT_MONITORED_EVENT_EMPTY)

    @property
    def kind(self) -> AspectKind:
        return AspectKind.MONITORED

    def build(self) -> Callable:
        """Lazily import and apply monitored decorator."""
        try:
            from domain_monitoring.decorators.monitored.monitored_client import (
                monitored,
            )
        except ImportError as e:  # pragma: no cover
            raise ImportError(const.ERR_ASPECT_MONITORED_IMPORT_MISSING) from e
        return monitored(
            self.event,
            sink=self.sink,
            labels_from_result=self.labels_from_result,
            labels_from_exc=self.labels_from_exc,
        )


@dataclass(frozen=True, slots=True)
class Retried:
    """Exponential backoff retry with static or dynamic policy selection.

    Exactly one of policy or policy_from_request must be provided (not both, not neither).
    Retries see raw exceptions for predicate matching before WRAP_ERRORS converts them.
    """

    policy: Optional[RetryPolicy] = None
    policy_from_request: Optional[Callable[..., Optional[RetryPolicy]]] = None

    def __post_init__(self) -> None:
        has_policy = self.policy is not None
        has_selector = self.policy_from_request is not None

        if not has_policy and not has_selector:
            raise ValueError(const.ERR_ASPECT_RETRIED_POLICY_REQUIRED)
        if has_policy and has_selector:
            raise ValueError(const.ERR_ASPECT_RETRIED_BOTH_POLICIES_PROVIDED)

    @property
    def kind(self) -> AspectKind:
        return AspectKind.RETRIED

    def build(self) -> Callable:
        """Build retry wrapper via RetryExecutor with optional dynamic policy."""
        policy = self.policy
        policy_from_request = self.policy_from_request

        def decorator(target: Callable) -> Callable:
            if inspect.isclass(target):
                return self._decorate_class_retried(
                    target,
                    policy,
                    policy_from_request,
                )
            return self._build_retried_wrapper(
                target,
                policy,
                policy_from_request,
            )

        return decorator

    @staticmethod
    def _build_retried_wrapper(
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
    def _decorate_class_retried(
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

            decorated = Retried._build_retried_wrapper(
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


AspectEntry = (
    Logged | Requires | TenantScoped | Throttled | Monitored | WrapErrors | Retried
)
"""Union type alias for all aspect entry types."""
