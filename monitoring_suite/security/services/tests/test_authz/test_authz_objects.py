"""Tests for authorization value objects."""

from __future__ import annotations

import dataclasses

import pytest

from monitoring_suite.security.services.authz.authz_objects import Permission, PolicyDecision


class TestPermission:
    """Permission value object behavior."""

    def test_permission_frozen(self) -> None:
        """Permission is immutable after construction."""
        perm = Permission(value="read")
        with pytest.raises(dataclasses.FrozenInstanceError):
            perm.value = "write"  # type: ignore[misc]

    def test_permission_value_stored(self) -> None:
        """Permission stores the value correctly."""
        perm = Permission(value="read:documents")
        assert perm.value == "read:documents"

    def test_permission_equality(self) -> None:
        """Permissions with same value are equal."""
        p1 = Permission(value="read")
        p2 = Permission(value="read")
        assert p1 == p2

    def test_permission_inequality(self) -> None:
        """Permissions with different values are not equal."""
        p1 = Permission(value="read")
        p2 = Permission(value="write")
        assert p1 != p2


class TestPolicyDecision:
    """PolicyDecision value object behavior."""

    def test_decision_frozen(self) -> None:
        """PolicyDecision is immutable after construction."""
        decision = PolicyDecision(allowed=True, reason=None)
        with pytest.raises(dataclasses.FrozenInstanceError):
            decision.allowed = False  # type: ignore[misc]

    def test_decision_allowed_true(self) -> None:
        """PolicyDecision stores allowed=True correctly."""
        decision = PolicyDecision(allowed=True)
        assert decision.allowed is True

    def test_decision_allowed_false(self) -> None:
        """PolicyDecision stores allowed=False correctly."""
        decision = PolicyDecision(allowed=False)
        assert decision.allowed is False

    def test_decision_reason_none_by_default(self) -> None:
        """PolicyDecision reason defaults to None."""
        decision = PolicyDecision(allowed=True)
        assert decision.reason is None

    def test_decision_reason_stored(self) -> None:
        """PolicyDecision stores reason when provided."""
        reason = "missing scope read"
        decision = PolicyDecision(allowed=False, reason=reason)
        assert decision.reason == reason

    def test_decision_equality(self) -> None:
        """Decisions with same data are equal."""
        d1 = PolicyDecision(allowed=True, reason="granted")
        d2 = PolicyDecision(allowed=True, reason="granted")
        assert d1 == d2

    def test_decision_inequality_allowed(self) -> None:
        """Decisions with different allowed status are not equal."""
        d1 = PolicyDecision(allowed=True)
        d2 = PolicyDecision(allowed=False)
        assert d1 != d2

    def test_decision_inequality_reason(self) -> None:
        """Decisions with different reasons are not equal."""
        d1 = PolicyDecision(allowed=False, reason="reason1")
        d2 = PolicyDecision(allowed=False, reason="reason2")
        assert d1 != d2
