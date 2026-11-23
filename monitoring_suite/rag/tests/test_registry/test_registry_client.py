"""Tests for ProvenanceRegistry."""

from monitoring_suite.rag.services.provenance.provenance_client import CollectingProvenanceSink, NullProvenanceSink
from monitoring_suite.rag.services.registry.registry_client import ProvenanceRegistry


class TestProvenanceRegistry:
    """ProvenanceRegistry for sink binding."""

    def test_get_default_sink_unset_returns_null(self) -> None:
        """get_default_sink returns NullProvenanceSink when unset."""
        sink = ProvenanceRegistry.get_default_sink()

        assert isinstance(sink, NullProvenanceSink)

    def test_set_default_sink(self) -> None:
        """set_default_sink stores sink."""
        collecting_sink = CollectingProvenanceSink()
        ProvenanceRegistry.set_default_sink(collecting_sink)

        sink = ProvenanceRegistry.get_default_sink()

        assert sink is collecting_sink

    def test_clear_default_sink(self) -> None:
        """clear_default_sink resets to None."""
        collecting_sink = CollectingProvenanceSink()
        ProvenanceRegistry.set_default_sink(collecting_sink)

        ProvenanceRegistry.clear_default_sink()

        sink = ProvenanceRegistry.get_default_sink()
        assert isinstance(sink, NullProvenanceSink)

    def test_set_and_retrieve_same_sink(self) -> None:
        """Set and retrieve the same sink."""
        collecting_sink = CollectingProvenanceSink()
        ProvenanceRegistry.set_default_sink(collecting_sink)

        retrieved_sink = ProvenanceRegistry.get_default_sink()

        assert retrieved_sink is collecting_sink
