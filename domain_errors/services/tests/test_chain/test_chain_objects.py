"""Tests for error chain ChainLink and DomainCrossing value objects."""

from dataclasses import FrozenInstanceError

import pytest

from domain_errors.services.chain.chain_objects import (
    ChainLink,
    ChainVia,
    CrossingLogExtra,
    DomainCrossing,
    LinkLogExtra,
)
from domain_errors.services.tests.test_chain.conftest import FakeDomainClassifier


class TestChainLink:
    """Tests for ChainLink value object."""

    def test_construction(self) -> None:
        """ChainLink can be constructed with all fields."""
        link = ChainLink(
            type_name="ValueError",
            message="invalid value",
            code="VAL_001",
            domain="validation",
            via=ChainVia.ROOT,
        )
        assert link.type_name == "ValueError"
        assert link.message == "invalid value"
        assert link.code == "VAL_001"
        assert link.domain == "validation"
        assert link.via == ChainVia.ROOT
        assert link.context == {}

    def test_construction_with_context(self) -> None:
        """ChainLink can be constructed with explicit context."""
        ctx = {"user_id": 123, "request_id": "abc"}
        link = ChainLink(
            type_name="ValueError",
            message="invalid value",
            code="VAL_001",
            domain="validation",
            via=ChainVia.ROOT,
            context=ctx,
        )
        assert link.context == ctx

    def test_frozen(self) -> None:
        """ChainLink is frozen and prevents assignment."""
        link = ChainLink(
            type_name="ValueError",
            message="test",
            code="X",
            domain="test",
            via=ChainVia.ROOT,
        )
        with pytest.raises(FrozenInstanceError):
            link.type_name = "TypeError"  # type: ignore

    def test_equality(self) -> None:
        """ChainLink equality compares all fields except context."""
        link1 = ChainLink(
            type_name="ValueError",
            message="test",
            code="X",
            domain="val",
            via=ChainVia.ROOT,
        )
        link2 = ChainLink(
            type_name="ValueError",
            message="test",
            code="X",
            domain="val",
            via=ChainVia.ROOT,
        )
        link3 = ChainLink(
            type_name="TypeError",
            message="test",
            code="X",
            domain="val",
            via=ChainVia.ROOT,
        )
        assert link1 == link2
        assert link1 != link3

    def test_equality_ignores_context(self) -> None:
        """ChainLink equality excludes context from comparison."""
        link1 = ChainLink(
            type_name="ValueError",
            message="test",
            code="X",
            domain="val",
            via=ChainVia.ROOT,
            context={"user_id": 1},
        )
        link2 = ChainLink(
            type_name="ValueError",
            message="test",
            code="X",
            domain="val",
            via=ChainVia.ROOT,
            context={"user_id": 999},
        )
        # Equal even though context differs, because context has compare=False
        assert link1 == link2

    def test_hash(self) -> None:
        """ChainLink is hashable."""
        link1 = ChainLink(
            type_name="ValueError",
            message="test",
            code="X",
            domain="val",
            via=ChainVia.ROOT,
        )
        link2 = ChainLink(
            type_name="ValueError",
            message="test",
            code="X",
            domain="val",
            via=ChainVia.ROOT,
        )
        # Equal objects should have equal hash
        assert hash(link1) == hash(link2)
        # Can be placed in a set
        unique_links = {link1, link2}
        assert len(unique_links) == 1

    def test_repr(self) -> None:
        """ChainLink has a repr string."""
        link = ChainLink(
            type_name="ValueError",
            message="test",
            code="X",
            domain="val",
            via=ChainVia.CAUSE,
        )
        rendered = repr(link)
        assert "ChainLink" in rendered
        assert "ValueError" in rendered

    def test_to_log_extra_with_code(self) -> None:
        """to_log_extra returns a dict with all fields, code as string."""
        link = ChainLink(
            type_name="ValueError",
            message="invalid",
            code="VAL_001",
            domain="validation",
            via=ChainVia.ROOT,
        )
        extra = link.to_log_extra()
        assert extra == {
            "type": "ValueError",
            "message": "invalid",
            "code": "VAL_001",
            "domain": "validation",
            "via": "root",
            "context": {},
        }

    def test_to_log_extra_code_none(self) -> None:
        """to_log_extra includes code as None when it is None."""
        link = ChainLink(
            type_name="RuntimeError",
            message="something",
            code=None,
            domain="python",
            via=ChainVia.CONTEXT,
        )
        extra = link.to_log_extra()
        assert extra == {
            "type": "RuntimeError",
            "message": "something",
            "code": None,
            "domain": "python",
            "via": "context",
            "context": {},
        }

    def test_to_log_extra_via_is_enum_value(self) -> None:
        """to_log_extra converts via enum to its .value string."""
        link = ChainLink(
            type_name="E",
            message="m",
            code="c",
            domain="d",
            via=ChainVia.CAUSE,
        )
        extra = link.to_log_extra()
        assert extra["via"] == "cause"
        assert isinstance(extra["via"], str)

    def test_to_log_extra_includes_context(self) -> None:
        """to_log_extra includes context field."""
        ctx = {"user_id": 123, "request_id": "abc"}
        link = ChainLink(
            type_name="ValueError",
            message="invalid",
            code="VAL_001",
            domain="validation",
            via=ChainVia.ROOT,
            context=ctx,
        )
        extra = link.to_log_extra()
        assert extra["context"] == ctx


class TestDomainCrossing:
    """Tests for DomainCrossing value object."""

    def test_construction(self) -> None:
        """DomainCrossing can be constructed with cause and effect links."""
        cause = ChainLink(
            type_name="ValueError",
            message="bad input",
            code="VAL",
            domain="validation",
            via=ChainVia.ROOT,
        )
        effect = ChainLink(
            type_name="RuntimeError",
            message="processing failed",
            code="RTE",
            domain="application",
            via=ChainVia.CAUSE,
        )
        crossing = DomainCrossing(cause=cause, effect=effect)
        assert crossing.cause == cause
        assert crossing.effect == effect

    def test_frozen(self) -> None:
        """DomainCrossing is frozen."""
        cause = ChainLink("E", "m", "c", "d1", ChainVia.ROOT)
        effect = ChainLink("E", "m", "c", "d2", ChainVia.CAUSE)
        crossing = DomainCrossing(cause=cause, effect=effect)
        with pytest.raises(FrozenInstanceError):
            crossing.cause = ChainLink("E", "m", "c", "d3", ChainVia.ROOT)  # type: ignore

    def test_equality(self) -> None:
        """DomainCrossing equality compares cause and effect."""
        cause1 = ChainLink("E1", "m1", "c1", "d1", ChainVia.ROOT)
        effect1 = ChainLink("E2", "m2", "c2", "d2", ChainVia.CAUSE)
        crossing1 = DomainCrossing(cause=cause1, effect=effect1)
        crossing2 = DomainCrossing(cause=cause1, effect=effect1)
        crossing3 = DomainCrossing(
            cause=cause1, effect=ChainLink("E3", "m3", "c3", "d2", ChainVia.CAUSE)
        )
        assert crossing1 == crossing2
        assert crossing1 != crossing3

    def test_hash(self) -> None:
        """DomainCrossing is hashable."""
        cause = ChainLink("E1", "m1", "c1", "d1", ChainVia.ROOT)
        effect = ChainLink("E2", "m2", "c2", "d2", ChainVia.CAUSE)
        crossing1 = DomainCrossing(cause=cause, effect=effect)
        crossing2 = DomainCrossing(cause=cause, effect=effect)
        assert hash(crossing1) == hash(crossing2)
        unique_crossings = {crossing1, crossing2}
        assert len(unique_crossings) == 1

    def test_to_log_extra(self) -> None:
        """to_log_extra returns cause and effect domain info."""
        cause = ChainLink(
            type_name="ValueError",
            message="bad",
            code="VAL",
            domain="validation",
            via=ChainVia.ROOT,
        )
        effect = ChainLink(
            type_name="RuntimeError",
            message="failed",
            code="RTE",
            domain="application",
            via=ChainVia.CAUSE,
        )
        crossing = DomainCrossing(cause=cause, effect=effect)
        extra = crossing.to_log_extra()
        assert extra == {
            "cause_type": "ValueError",
            "cause_domain": "validation",
            "effect_type": "RuntimeError",
            "effect_domain": "application",
        }


class TestDomainClassifier:
    """Tests for DomainClassifier protocol."""

    def test_classifier_satisfies_protocol(self) -> None:
        """FakeDomainClassifier satisfies the DomainClassifier protocol."""
        classifier = FakeDomainClassifier()
        assert hasattr(classifier, "classify")
        # Verify it can classify
        assert classifier.classify(ValueError("x")) == "validation"
        assert classifier.classify(TypeError("x")) == "typing"
        assert classifier.classify(RuntimeError("x")) is None


class TestLinkLogExtra:
    """Tests for LinkLogExtra DTO."""

    def test_construction(self) -> None:
        """LinkLogExtra can be constructed with all fields."""
        extra = LinkLogExtra(
            type="ValueError",
            message="invalid",
            code="VAL_001",
            domain="validation",
            via="root",
            context={"user_id": 123},
        )
        assert extra.type == "ValueError"
        assert extra.message == "invalid"
        assert extra.code == "VAL_001"
        assert extra.domain == "validation"
        assert extra.via == "root"
        assert extra.context == {"user_id": 123}

    def test_frozen(self) -> None:
        """LinkLogExtra is frozen."""
        extra = LinkLogExtra(
            type="ValueError",
            message="test",
            code="X",
            domain="test",
            via="root",
            context={},
        )
        with pytest.raises(FrozenInstanceError):
            extra.type = "TypeError"  # type: ignore


class TestCrossingLogExtra:
    """Tests for CrossingLogExtra DTO."""

    def test_construction(self) -> None:
        """CrossingLogExtra can be constructed with all fields."""
        extra = CrossingLogExtra(
            cause_type="ValueError",
            cause_domain="validation",
            effect_type="RuntimeError",
            effect_domain="application",
        )
        assert extra.cause_type == "ValueError"
        assert extra.cause_domain == "validation"
        assert extra.effect_type == "RuntimeError"
        assert extra.effect_domain == "application"

    def test_frozen(self) -> None:
        """CrossingLogExtra is frozen."""
        extra = CrossingLogExtra(
            cause_type="ValueError",
            cause_domain="validation",
            effect_type="RuntimeError",
            effect_domain="application",
        )
        with pytest.raises(FrozenInstanceError):
            extra.cause_type = "TypeError"  # type: ignore
