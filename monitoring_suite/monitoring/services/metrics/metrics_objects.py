"""Metric event DTO. Frozen, hashable, immutable."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from monitoring_suite.monitoring.services.constants import metrics as const


class Outcome(StrEnum):
    """Metric outcome enumeration."""

    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True, slots=True)
class MetricEvent:
    """Immutable metric event with outcome tracking."""

    event: str
    outcome: Outcome
    duration_ms: float
    occurred_at: str
    labels: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Validate metric event invariants."""
        if not self.event:
            raise ValueError(const.ERR_METRIC_EVENT_EMPTY)
        if self.duration_ms < 0:
            raise ValueError(const.ERR_METRIC_DURATION_NEGATIVE)
        if not self.occurred_at:
            raise ValueError(const.ERR_METRIC_OCCURRED_AT_EMPTY)

    @classmethod
    def for_success(
        cls,
        event: str,
        duration_ms: float,
        occurred_at: str,
        labels: tuple[tuple[str, str], ...] = (),
    ) -> Self:
        """Create a success metric event."""
        return cls(
            event=event,
            outcome=Outcome.SUCCESS,
            duration_ms=duration_ms,
            occurred_at=occurred_at,
            labels=labels,
        )

    @classmethod
    def for_failure(
        cls,
        event: str,
        duration_ms: float,
        occurred_at: str,
        labels: tuple[tuple[str, str], ...] = (),
    ) -> Self:
        """Create a failure metric event."""
        return cls(
            event=event,
            outcome=Outcome.FAILURE,
            duration_ms=duration_ms,
            occurred_at=occurred_at,
            labels=labels,
        )

    @property
    def is_failure(self) -> bool:
        """Check if metric represents a failure."""
        return self.outcome == Outcome.FAILURE
