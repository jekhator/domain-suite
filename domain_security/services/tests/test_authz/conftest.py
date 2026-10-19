"""Fixtures for authorization tests."""

from __future__ import annotations

import pytest

from domain_security.context.security_context.security_context_objects import (
    Principal,
)
from domain_security.services.authz.authz_objects import Permission


@pytest.fixture
def permission() -> Permission:  # noqa: R004
    """Create a permission."""
    return Permission(value="read")


@pytest.fixture
def write_permission() -> Permission:  # noqa: R004
    """Create a write permission."""
    return Permission(value="write")


@pytest.fixture
def principal_with_read_scope() -> Principal:  # noqa: R004
    """Create a principal with read scope."""
    return Principal(id="user:reader", roles=frozenset(), scopes=frozenset(["read"]))


@pytest.fixture
def principal_with_multiple_scopes() -> Principal:  # noqa: R004
    """Create a principal with multiple scopes."""
    return Principal(
        id="user:admin",
        roles=frozenset(["admin"]),
        scopes=frozenset(["read", "write", "delete"]),
    )
