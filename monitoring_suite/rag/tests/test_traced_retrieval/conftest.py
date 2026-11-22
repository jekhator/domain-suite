"""Fixtures for traced retrieval tests."""

from collections.abc import Generator

import pytest

from monitoring_suite.rag.services.provenance.provenance_client import (
    CollectingProvenanceSink,
)
from monitoring_suite.rag.services.registry.registry_client import ProvenanceRegistry


@pytest.fixture
def collecting_sink() -> CollectingProvenanceSink:
    """
    Provide a collecting provenance sink.

    Used by: TestTracedRetrievalAsyncEdgeCases, TestTracedRetrievalEdgeCases, TestTracedRetrievalOnCallable,
    TestTracedRetrievalOnClass.
    """
    return CollectingProvenanceSink()


@pytest.fixture(autouse=True)
def clear_registry() -> Generator[None, None, None]:
    """
    Clear registry before and after each test.

    Used by: every test class under monitoring_suite/rag/tests/test_traced_retrieval/ (autouse).
    """
    ProvenanceRegistry.clear_default_sink()
    yield
    ProvenanceRegistry.clear_default_sink()
