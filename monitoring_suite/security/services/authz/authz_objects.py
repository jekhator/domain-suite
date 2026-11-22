"""Authorization value objects: permissions and policy decisions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Permission:
    """Named permission evaluated against a principal's scopes."""

    value: str


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """Allow-or-deny outcome with an optional denial rationale."""

    allowed: bool
    reason: str | None = None
