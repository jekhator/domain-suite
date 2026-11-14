"""Global monitoring registry for sink resolution."""

from typing import ClassVar, Optional

from domain_monitoring.services.metrics.metrics_client import MetricSink, NullSink


class MonitorRegistry:
    """Global registry for metric sink binding."""

    _default_sink: ClassVar[Optional[MetricSink]] = None
    _fallback_sink: ClassVar[MetricSink] = NullSink()

    @classmethod
    def set_default_sink(cls, sink: MetricSink) -> None:
        """Set the default sink for all unbound monitoring."""
        cls._default_sink = sink

    @classmethod
    def get_default_sink(cls) -> MetricSink:
        """Get the current default sink, or NullSink if unset."""
        if cls._default_sink is None:
            return cls._fallback_sink
        return cls._default_sink

    @classmethod
    def clear_default_sink(cls) -> None:
        """Clear the default sink."""
        cls._default_sink = None
