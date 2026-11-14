"""Tests for MetricEvent objects."""

import pytest

from domain_monitoring.services.constants import metrics as const
from domain_monitoring.services.metrics.metrics_objects import MetricEvent, Outcome


class TestMetricEvent:
    """MetricEvent immutability and validation."""

    def test_frozen_prevents_mutation(self) -> None:
        """Event is immutable after creation."""
        event = MetricEvent(
            event="test.method",
            outcome=Outcome.SUCCESS,
            duration_ms=100.5,
            occurred_at="2026-07-07T12:00:00Z",
        )

        with pytest.raises(AttributeError):
            event.duration_ms = 200.0  # type: ignore

    def test_hashable_for_set_membership(self) -> None:
        """Event can be added to sets."""
        event1 = MetricEvent(
            event="test.method",
            outcome=Outcome.SUCCESS,
            duration_ms=100.0,
            occurred_at="2026-07-07T12:00:00Z",
        )
        event2 = MetricEvent(
            event="test.method",
            outcome=Outcome.SUCCESS,
            duration_ms=100.0,
            occurred_at="2026-07-07T12:00:00Z",
        )
        event3 = MetricEvent(
            event="test.other",
            outcome=Outcome.SUCCESS,
            duration_ms=100.0,
            occurred_at="2026-07-07T12:00:00Z",
        )

        event_set = {event1, event2, event3}
        assert len(event_set) == 2

    def test_validation_empty_event_name(self) -> None:
        """Empty event name raises ValueError."""
        with pytest.raises(ValueError, match=const.ERR_METRIC_EVENT_EMPTY):
            MetricEvent(
                event="",
                outcome=Outcome.SUCCESS,
                duration_ms=100.0,
                occurred_at="2026-07-07T12:00:00Z",
            )

    def test_validation_negative_duration(self) -> None:
        """Negative duration raises ValueError."""
        with pytest.raises(ValueError, match=const.ERR_METRIC_DURATION_NEGATIVE):
            MetricEvent(
                event="test.method",
                outcome=Outcome.SUCCESS,
                duration_ms=-1.0,
                occurred_at="2026-07-07T12:00:00Z",
            )

    def test_validation_empty_occurred_at(self) -> None:
        """Empty occurred_at raises ValueError."""
        with pytest.raises(ValueError, match=const.ERR_METRIC_OCCURRED_AT_EMPTY):
            MetricEvent(
                event="test.method",
                outcome=Outcome.SUCCESS,
                duration_ms=100.0,
                occurred_at="",
            )

    def test_factory_for_success(self) -> None:
        """for_success factory creates SUCCESS event."""
        event = MetricEvent.for_success(
            event="test.method",
            duration_ms=50.0,
            occurred_at="2026-07-07T12:00:00Z",
        )

        assert event.outcome == Outcome.SUCCESS
        assert event.duration_ms == 50.0
        assert not event.is_failure

    def test_factory_for_failure(self) -> None:
        """for_failure factory creates FAILURE event."""
        event = MetricEvent.for_failure(
            event="test.method",
            duration_ms=75.0,
            occurred_at="2026-07-07T12:00:00Z",
        )

        assert event.outcome == Outcome.FAILURE
        assert event.duration_ms == 75.0
        assert event.is_failure

    def test_labels_stored_as_tuple(self) -> None:
        """Labels are stored as a tuple for hashability."""
        labels = (("tenant_id", "123"), ("user_id", "456"))
        event = MetricEvent(
            event="test.method",
            outcome=Outcome.SUCCESS,
            duration_ms=100.0,
            occurred_at="2026-07-07T12:00:00Z",
            labels=labels,
        )

        assert event.labels == labels
        assert isinstance(event.labels, tuple)

    def test_outcome_enum_values(self) -> None:
        """Outcome enum has expected string values."""
        assert Outcome.SUCCESS.value == "success"
        assert Outcome.FAILURE.value == "failure"
