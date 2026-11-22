"""Root conftest for monitoring_suite.monitoring tests."""

from collections.abc import Generator

import pytest

from monitoring_suite.monitoring.services.registry.registry_client import MonitorRegistry


@pytest.fixture(autouse=True)
def reset_registry() -> Generator[None, None, None]:
    """
    Reset registry between tests.

    Used by: every test class under monitoring_suite/monitoring/ (autouse).
    """
    MonitorRegistry.clear_default_sink()
    yield
    MonitorRegistry.clear_default_sink()
