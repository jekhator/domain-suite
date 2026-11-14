"""Global provenance registry for sink resolution."""

from typing import ClassVar, Optional

from domain_rag.services.provenance.provenance_client import (
    NullProvenanceSink,
    ProvenanceSink,
)


class ProvenanceRegistry:
    """Global registry for provenance sink binding."""

    _default_sink: ClassVar[Optional[ProvenanceSink]] = None
    _fallback_sink: ClassVar[ProvenanceSink] = NullProvenanceSink()

    @classmethod
    def set_default_sink(cls, sink: ProvenanceSink) -> None:
        """Set the default sink for all unbound retrieval provenance."""
        cls._default_sink = sink

    @classmethod
    def get_default_sink(cls) -> ProvenanceSink:
        """Get the current default sink, or NullProvenanceSink if unset."""
        if cls._default_sink is None:
            return cls._fallback_sink
        return cls._default_sink

    @classmethod
    def clear_default_sink(cls) -> None:
        """Clear the default sink."""
        cls._default_sink = None
