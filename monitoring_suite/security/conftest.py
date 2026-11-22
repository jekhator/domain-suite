"""Root pytest configuration for monitoring_suite.security package."""

from __future__ import annotations

import pytest

from monitoring_suite.security.context.security_context.security_context_client import (
    SecurityContextManager,
)


@pytest.fixture(autouse=True)
def reset_security_context() -> None:
    """Reset security context to clean state before each test."""
    SecurityContextManager._context.set(None)
