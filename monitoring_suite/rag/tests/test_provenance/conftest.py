"""Fixtures for provenance tests."""

import pytest

from monitoring_suite.rag.services.provenance.provenance_client import CollectingProvenanceSink


@pytest.fixture
def collecting_sink() -> CollectingProvenanceSink:
    """
    Provide a collecting provenance sink.

    Used by: no test class yet.
    """
    return CollectingProvenanceSink()
