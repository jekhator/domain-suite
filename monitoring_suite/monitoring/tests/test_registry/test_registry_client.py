"""Tests for MonitorRegistry."""

from monitoring_suite.monitoring.services.metrics.metrics_client import (
    CollectingSink,
    NullSink,
)
from monitoring_suite.monitoring.services.registry.registry_client import (
    MonitorRegistry,
)


class TestMonitorRegistry:
    """Global monitoring registry for sink binding."""

    def setup_method(self) -> None:
        """Clear default sink before each test."""
        MonitorRegistry.clear_default_sink()

    def test_get_default_sink_returns_null_sink_when_unset(self) -> None:
        """Unset registry returns NullSink."""
        sink = MonitorRegistry.get_default_sink()
        assert isinstance(sink, NullSink)

    def test_set_and_get_default_sink(self) -> None:
        """Set and retrieve custom default sink."""
        custom_sink = CollectingSink()
        MonitorRegistry.set_default_sink(custom_sink)

        sink = MonitorRegistry.get_default_sink()
        assert sink is custom_sink

    def test_clear_default_sink(self) -> None:
        """Clear reverts to NullSink."""
        custom_sink = CollectingSink()
        MonitorRegistry.set_default_sink(custom_sink)

        MonitorRegistry.clear_default_sink()

        sink = MonitorRegistry.get_default_sink()
        assert isinstance(sink, NullSink)

    def test_set_new_sink_overwrites_previous(self) -> None:
        """New set_default_sink overwrites previous."""
        sink1 = CollectingSink()
        sink2 = CollectingSink()

        MonitorRegistry.set_default_sink(sink1)
        MonitorRegistry.set_default_sink(sink2)

        sink = MonitorRegistry.get_default_sink()
        assert sink is sink2
