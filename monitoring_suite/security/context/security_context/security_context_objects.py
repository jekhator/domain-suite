"""Security context value objects: principal identity and the context pairing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Principal:
    """Authenticated identity with role and scope membership."""

    id: str
    roles: frozenset[str] = frozenset()
    scopes: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class SecurityContext:
    """Immutable pairing of acting principal and tenant boundary."""

    principal: Principal | None
    tenant_id: str | None
