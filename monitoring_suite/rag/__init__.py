"""Domain RAG library: vendor-neutral retrieval provenance tracking."""

from monitoring_suite.rag.config._version import __version__
from monitoring_suite.rag.decorators.traced_retrieval.traced_retrieval_client import traced_retrieval
from monitoring_suite.rag.errors.retrieval_errors import RetrievalDeclarationError, RetrievalError
from monitoring_suite.rag.services.provenance.provenance_client import (
    CollectingProvenanceSink,
    NullProvenanceSink,
    ProvenanceSink,
)
from monitoring_suite.rag.services.provenance.provenance_objects import ProvenanceOutcome, RetrievalProvenance
from monitoring_suite.rag.services.registry.registry_client import ProvenanceRegistry

__all__ = [
    "__version__", "CollectingProvenanceSink", "NullProvenanceSink", "ProvenanceOutcome", "ProvenanceRegistry",
    "ProvenanceSink", "RetrievalDeclarationError", "RetrievalError", "RetrievalProvenance", "traced_retrieval"
]
