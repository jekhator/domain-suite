"""Monitored decorator for automatic metric emission."""

import asyncio
import functools
import inspect
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Optional, cast

from domain_monitoring.errors.constants import monitoring as const
from domain_monitoring.errors.monitoring_errors import MonitoringDeclarationError
from domain_monitoring.services.metrics.metrics_client import MetricSink
from domain_monitoring.services.metrics.metrics_objects import MetricEvent
from domain_monitoring.services.registry.registry_client import MonitorRegistry


def _stamp_correlation_labels(
    labels: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    """Stamp correlation labels from ambient ContextVar; consumer labels win.

    Derives domain lane id as scenario_id/monitoring (if scenario id present).
    Returns merged labels with consumer-provided labels taking precedence.
    """
    try:
        from mixin_logging import get_correlation_id
    except ImportError:
        return labels

    scenario_id = get_correlation_id()
    if not scenario_id:
        return labels

    label_dict = dict(labels) if labels else {}
    correlation_label = "correlation_id"
    domain_correlation_label = "domain_correlation_id"

    if correlation_label not in label_dict:
        label_dict[correlation_label] = scenario_id

    if domain_correlation_label not in label_dict:
        label_dict[domain_correlation_label] = f"{scenario_id}/monitoring"

    return tuple(sorted(label_dict.items()))


class MonitoredClient:
    """Container for monitored decorator and helper methods."""

    @staticmethod
    def monitored[Target](
        event: str,
        sink: Optional[MetricSink] = None,
        labels_from_result: Optional[
            Callable[[object], tuple[tuple[str, str], ...]]
        ] = None,
        labels_from_exc: Optional[
            Callable[[BaseException], tuple[tuple[str, str], ...]]
        ] = None,
    ) -> Callable[[Target], Target]:
        """Apply metric tracking to callables and classes."""

        def decorator(target: Target) -> Target:
            """Apply monitoring to target."""
            if inspect.isclass(target):
                return cast(
                    Target,
                    MonitoredClient._monitor_class(
                        target,
                        event,
                        sink,
                        labels_from_result,
                        labels_from_exc,
                    ),
                )
            elif callable(target):
                return cast(
                    Target,
                    MonitoredClient._monitor_callable(
                        target,
                        event,
                        sink,
                        labels_from_result,
                        labels_from_exc,
                    ),
                )
            else:
                raise MonitoringDeclarationError(const.ERR_MONITORING_INVALID_TARGET)

        return decorator

    @staticmethod
    def _monitor_callable(
        fn: Callable[..., Any],
        event: str,
        sink: Optional[MetricSink],
        labels_from_result: Optional[
            Callable[[object], tuple[tuple[str, str], ...]]
        ] = None,
        labels_from_exc: Optional[
            Callable[[BaseException], tuple[tuple[str, str], ...]]
        ] = None,
    ) -> Callable[..., Any]:
        """Wrap a callable with monitoring."""
        if asyncio.iscoroutinefunction(fn):
            return MonitoredClient._wrap_async(
                fn, event, sink, labels_from_result, labels_from_exc
            )
        else:
            return MonitoredClient._wrap_sync(
                fn, event, sink, labels_from_result, labels_from_exc
            )

    @staticmethod
    def _wrap_sync(
        fn: Callable[..., Any],
        event: str,
        sink: Optional[MetricSink],
        labels_from_result: Optional[
            Callable[[object], tuple[tuple[str, str], ...]]
        ] = None,
        labels_from_exc: Optional[
            Callable[[BaseException], tuple[tuple[str, str], ...]]
        ] = None,
    ) -> Callable[..., Any]:
        """Wrap synchronous callable."""

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute with metric tracking."""
            start_time = datetime.now(timezone.utc)
            actual_sink = sink or MonitorRegistry.get_default_sink()

            try:
                result = fn(*args, **kwargs)
                end_time = datetime.now(timezone.utc)
                duration_ms = (end_time - start_time).total_seconds() * 1000
                labels = labels_from_result(result) if labels_from_result else ()
                labels = _stamp_correlation_labels(labels)
                metric_event = MetricEvent.for_success(
                    event=event,
                    duration_ms=duration_ms,
                    occurred_at=end_time.isoformat(),
                    labels=labels,
                )
                actual_sink.emit(metric_event)
                return result
            except Exception as error:
                end_time = datetime.now(timezone.utc)
                duration_ms = (end_time - start_time).total_seconds() * 1000
                labels = labels_from_exc(error) if labels_from_exc else ()
                labels = _stamp_correlation_labels(labels)
                metric_event = MetricEvent.for_failure(
                    event=event,
                    duration_ms=duration_ms,
                    occurred_at=end_time.isoformat(),
                    labels=labels,
                )
                actual_sink.emit(metric_event)
                raise

        return wrapper

    @staticmethod
    def _wrap_async(
        fn: Callable[..., Any],
        event: str,
        sink: Optional[MetricSink],
        labels_from_result: Optional[
            Callable[[object], tuple[tuple[str, str], ...]]
        ] = None,
        labels_from_exc: Optional[
            Callable[[BaseException], tuple[tuple[str, str], ...]]
        ] = None,
    ) -> Callable[..., Any]:
        """Wrap asynchronous callable."""

        @functools.wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute async with metric tracking."""
            start_time = datetime.now(timezone.utc)
            actual_sink = sink or MonitorRegistry.get_default_sink()

            try:
                result = await fn(*args, **kwargs)
                end_time = datetime.now(timezone.utc)
                duration_ms = (end_time - start_time).total_seconds() * 1000
                labels = labels_from_result(result) if labels_from_result else ()
                labels = _stamp_correlation_labels(labels)
                metric_event = MetricEvent.for_success(
                    event=event,
                    duration_ms=duration_ms,
                    occurred_at=end_time.isoformat(),
                    labels=labels,
                )
                actual_sink.emit(metric_event)
                return result
            except Exception as error:
                end_time = datetime.now(timezone.utc)
                duration_ms = (end_time - start_time).total_seconds() * 1000
                labels = labels_from_exc(error) if labels_from_exc else ()
                labels = _stamp_correlation_labels(labels)
                metric_event = MetricEvent.for_failure(
                    event=event,
                    duration_ms=duration_ms,
                    occurred_at=end_time.isoformat(),
                    labels=labels,
                )
                actual_sink.emit(metric_event)
                raise

        return async_wrapper

    @staticmethod
    def _monitor_class(
        cls: type,
        event: str,
        sink: Optional[MetricSink],
        labels_from_result: Optional[
            Callable[[object], tuple[tuple[str, str], ...]]
        ] = None,
        labels_from_exc: Optional[
            Callable[[BaseException], tuple[tuple[str, str], ...]]
        ] = None,
    ) -> type:
        """Fan out monitoring to public methods on a class."""
        public_methods = MonitoredClient._get_public_methods(cls)

        if not public_methods:
            raise MonitoringDeclarationError(const.ERR_MONITORING_EMPTY_CLASS)

        for method_name in public_methods:
            original_method = getattr(cls, method_name)
            derived_event = f"{event}.{method_name}"
            monitored_method = MonitoredClient._monitor_callable(
                original_method,
                derived_event,
                sink,
                labels_from_result,
                labels_from_exc,
            )
            setattr(cls, method_name, monitored_method)

        return cls

    @staticmethod
    def _get_public_methods(cls: type) -> list[str]:
        """Get public method names from class, excluding inherited and special methods."""
        public = []

        for name, value in inspect.getmembers(cls):
            if name.startswith("_"):
                continue
            if inspect.ismethod(value) or inspect.isfunction(value):
                if not hasattr(cls, "__bases__") or name not in dir(cls.__bases__[0]):
                    public.append(name)
            elif isinstance(value, classmethod):  # pragma: no cover
                public.append(name)
            elif isinstance(value, staticmethod):  # pragma: no cover
                public.append(name)

        return public


monitored = MonitoredClient.monitored
