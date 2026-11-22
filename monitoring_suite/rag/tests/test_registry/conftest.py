"""Fixtures for registry tests."""

from collections.abc import Generator

import pytest

from monitoring_suite.rag.services.registry.registry_client import ProvenanceRegistry


@pytest.fixture(autouse=True)
def clean_registry() -> Generator[None, None, None]:
    """Clear registry before and after each test."""
    ProvenanceRegistry.clear_default_sink()
    yield
    ProvenanceRegistry.clear_default_sink()
