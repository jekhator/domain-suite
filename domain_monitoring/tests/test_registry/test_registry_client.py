"""Tests for MonitorRegistry."""

from domain_monitoring.services.metrics.metrics_client import CollectingSink, NullSink
from domain_monitoring.services.registry.registry_client import MonitorRegistry


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

    def test_falsy_sink_is_kept(self) -> None:
        """A bound sink that evaluates as falsy is returned, not replaced by NullSink."""

        class EmptySink:
            """Sink that reports itself as empty."""

            def __len__(self) -> int:
                return 0

            def emit(self, event: object) -> None:
                """Discard the event."""

        falsy_sink = EmptySink()
        MonitorRegistry.set_default_sink(falsy_sink)  # type: ignore[arg-type]

        assert MonitorRegistry.get_default_sink() is falsy_sink
