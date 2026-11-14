"""Aspects test fixtures."""

from __future__ import annotations

from typing import Any

import mixin_logging
import pytest

from domain_aspects.services.aspects import aspects_objects as objs


@pytest.fixture
def captured_logs(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[str, str, dict[str, Any]]]:
    """Record ambient log_info and log_error calls as (level, event, fields) tuples.

    Used by TestLoggedWrapperSync, TestLoggedWrapperAsync and TestLoggedWrapperTimed.
    """
    records: list[tuple[str, str, dict[str, Any]]] = []

    def record_info(event: str, **fields: Any) -> None:
        records.append(("info", event, fields))

    def record_error(event: str, **fields: Any) -> None:
        records.append(("error", event, fields))

    monkeypatch.setattr(mixin_logging, "log_info", record_info)
    monkeypatch.setattr(mixin_logging, "log_error", record_error)
    return records


@pytest.fixture
def stub_logged() -> objs.Logged:
    """Logged entry fixture."""
    return objs.Logged(event="test.event")


@pytest.fixture
def stub_requires() -> objs.Requires:
    """Requires entry fixture."""
    return objs.Requires(permission="admin.read")


@pytest.fixture
def stub_tenant_scoped() -> objs.TenantScoped:
    """TenantScoped entry fixture."""
    return objs.TenantScoped(param_name="tenant_id")


@pytest.fixture
def stub_throttled() -> objs.Throttled:
    """Throttled entry fixture."""
    return objs.Throttled(scope="api.documents", rate="100/hour")


@pytest.fixture
def stub_wrap_errors() -> objs.WrapErrors:
    """WrapErrors entry fixture."""
    return objs.WrapErrors(
        as_=ValueError,
        catch=(RuntimeError, TypeError),
    )


@pytest.fixture
def stub_monitored() -> objs.Monitored:
    """Monitored entry fixture."""
    return objs.Monitored(event="test.operation")


@pytest.fixture
def stub_require_mixins() -> objs.RequireMixins:
    """RequireMixins entry fixture."""

    class MixinA:
        pass

    class MixinB:
        pass

    return objs.RequireMixins(bases=(MixinA, MixinB))
