"""Aspects test fixtures."""

from __future__ import annotations

import pytest

from domain_aspects.services.aspects import aspects_objects as objs


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
