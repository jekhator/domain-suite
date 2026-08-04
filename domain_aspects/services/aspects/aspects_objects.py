"""Aspect entry value objects for decorator composition."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Optional

from domain_aspects.services.aspects.aspects_logged_builders import _LoggedBuilders
from domain_aspects.services.aspects.aspects_require_mixins import RequireMixins
from domain_aspects.services.aspects.aspects_retried_builders import _RetriedBuilders
from domain_aspects.services.constants import aspects as const

if TYPE_CHECKING:
    from mixin_retry import RetryPolicy

    from domain_monitoring.services.metrics.metrics_client import MetricSink


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
                return _LoggedBuilders.decorate_class_logged(
                    target,
                    event,
                    payload_from_request,
                    payload_from_result,
                    payload_from_exc,
                    timed,
                )
            return _LoggedBuilders.build_logged_wrapper(
                target,
                event,
                payload_from_request,
                payload_from_result,
                payload_from_exc,
                timed,
            )

        return decorator


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
        except ImportError as error:
            raise ImportError(const.ERR_ASPECT_REQUIRES_IMPORT_MISSING) from error
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
        except ImportError as error:
            raise ImportError(const.ERR_ASPECT_TENANT_SCOPED_IMPORT_MISSING) from error
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
        except ImportError as error:
            raise ImportError(const.ERR_ASPECT_THROTTLED_IMPORT_MISSING) from error
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
        except ImportError as error:
            raise ImportError(const.ERR_ASPECT_WRAP_ERRORS_IMPORT_MISSING) from error
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
        except ImportError as error:  # pragma: no cover
            raise ImportError(const.ERR_ASPECT_MONITORED_IMPORT_MISSING) from error
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
                return _RetriedBuilders.decorate_class_retried(
                    target,
                    policy,
                    policy_from_request,
                )
            return _RetriedBuilders.build_retried_wrapper(
                target,
                policy,
                policy_from_request,
            )

        return decorator


AspectEntry = (
    Logged
    | Requires
    | TenantScoped
    | Throttled
    | Monitored
    | WrapErrors
    | Retried
    | RequireMixins
)
"""Union type alias for all aspect entry types."""
