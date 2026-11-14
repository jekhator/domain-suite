"""Tests for ProvenanceRegistry."""

from domain_rag.services.provenance.provenance_client import (
    CollectingProvenanceSink,
    NullProvenanceSink,
)
from domain_rag.services.registry.registry_client import ProvenanceRegistry


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

    def test_falsy_sink_is_kept(self) -> None:
        """A bound sink that evaluates as falsy is returned, not replaced by the null sink."""

        class EmptySink:
            """Sink that reports itself as empty."""

            def __len__(self) -> int:
                return 0

            def record(self, event: object) -> None:
                """Discard the event."""

        falsy_sink = EmptySink()
        ProvenanceRegistry.set_default_sink(falsy_sink)  # type: ignore[arg-type]

        assert ProvenanceRegistry.get_default_sink() is falsy_sink
