"""Root pytest configuration for domains monorepo."""

from __future__ import annotations

from collections.abc import Generator

import pytest

from monitoring_suite.monitoring.services.registry.registry_client import (
    MonitorRegistry,
)
from monitoring_suite.security.context.security_context.security_context_client import (
    SecurityContextManager,
)


@pytest.fixture(autouse=True)
def reset_security_context() -> None:
    """
    Reset security context to clean state before each test.

    Used by: every test class in the repository (autouse).
    """
    SecurityContextManager._context.set(None)


@pytest.fixture(autouse=True)
def reset_registry() -> Generator[None, None, None]:
    """
    Reset registry between tests.

    Used by: every test class in the repository (autouse).
    """
    MonitorRegistry.clear_default_sink()
    yield
    MonitorRegistry.clear_default_sink()
