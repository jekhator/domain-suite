"""Aspect kind enumeration shared by the entry objects."""

from __future__ import annotations

from enum import StrEnum


class AspectKind(StrEnum):
    """Aspect classification kinds."""

    LOGGED = "LOGGED"
    REQUIRES = "REQUIRES"
    TENANT_SCOPED = "TENANT_SCOPED"
    THROTTLED = "THROTTLED"
    MONITORED = "MONITORED"
    WRAP_ERRORS = "WRAP_ERRORS"
    RETRIED = "RETRIED"
    REQUIRE_MIXINS = "REQUIRE_MIXINS"
