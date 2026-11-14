"""Retrieval provenance service with sink protocol."""

from domain_rag.services.provenance.provenance_client import (
    CollectingProvenanceSink,
    NullProvenanceSink,
    ProvenanceSink,
)
from domain_rag.services.provenance.provenance_objects import (
    ProvenanceOutcome,
    RetrievalProvenance,
)

__all__ = [
    "CollectingProvenanceSink",
    "NullProvenanceSink",
    "ProvenanceOutcome",
    "ProvenanceSink",
    "RetrievalProvenance",
]
