"""
Aspect composition and ordering constants.

Imported as const.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "ASPECT_ORDER", "ERR_ASPECTS_DUPLICATE_KIND", "ERR_ASPECTS_UNKNOWN_ENTRY_TYPE",
    "DEFAULT_TENANT_PARAM_NAME", "ERR_ASPECTS_EMPTY_DECLARATION", "ERR_ASPECTS_DECLARATION_FAILED",
    "ERR_ASPECT_LOGGED_EVENT_EMPTY", "ERR_ASPECT_MONITORED_EVENT_EMPTY", "ERR_ASPECT_LOGGED_IMPORT_MISSING",
    "ERR_ASPECT_REQUIRES_IMPORT_MISSING", "ERR_ASPECT_REQUIRES_PERMISSION_EMPTY",
    "ERR_ASPECT_TENANT_SCOPED_PARAM_EMPTY", "ERR_ASPECT_REQUIRE_MIXINS_FUNCTION_TARGET",
    "ERR_ASPECT_REQUIRE_MIXINS_MISSING_BASES", "ERR_ASPECT_RETRIED_BOTH_POLICIES_PROVIDED",
    "ERR_ASPECT_REQUIRE_MIXINS_BASES_INVALID", "ERR_ASPECT_RETRIED_POLICY_REQUIRED",
    "ERR_ASPECT_RETRIED_POLICY_FROM_REQUEST_REQUIRED", "ERR_ASPECT_TENANT_SCOPED_IMPORT_MISSING",
    "ERR_ASPECT_THROTTLED_IMPORT_MISSING", "ERR_ASPECT_THROTTLED_SCOPE_EMPTY", "ERR_ASPECT_THROTTLED_RATE_EMPTY",
    "ERR_ASPECT_THROTTLED_TIERS_NOT_TUPLE", "ERR_ASPECT_WRAP_ERRORS_AS_NOT_CLASS",
    "ERR_ASPECT_WRAP_ERRORS_CATCH_INVALID", "ERR_ASPECT_WRAP_ERRORS_IMPORT_MISSING",
    "ERR_ASPECT_MONITORED_IMPORT_MISSING", "EVENT_SUFFIX_END", "EVENT_SUFFIX_ERROR", "EVENT_SUFFIX_START",
    "KIND_LOGGED", "KIND_MONITORED", "KIND_REQUIRES", "KIND_REQUIRE_MIXINS", "KIND_RETRIED",
    "KIND_TENANT_SCOPED", "KIND_THROTTLED", "KIND_WRAP_ERRORS", "LOGGED_MARKER", "LOG_EXTRACTION_FAILED_PREFIX",
    "NAME_SEPARATOR", "PAYLOAD_KEY_LATENCY_MS", "PRIVATE_PREFIX", "RETRIED_MARKER", "UNKNOWN_KIND_ORDER"
]


"""
Aspect application order (outermost to innermost: LOGGED → REQUIRES → TENANT_SCOPED → THROTTLED → MONITORED →
WRAP_ERRORS → RETRIED innermost).

RETRIED is placed innermost so retries see raw exceptions for predicate matching, before WRAP_ERRORS converts them.
Sensitivity is adopted client-side via logging_suite.sensitivity.SensitiveRepr (not a wrapper concern).
"""

ASPECT_ORDER: Final[tuple[str, ...]] = (
    "LOGGED", "REQUIRES", "TENANT_SCOPED", "THROTTLED", "MONITORED", "WRAP_ERRORS", "RETRIED"
)


"""Aspect declaration validation error messages."""

ERR_ASPECTS_DUPLICATE_KIND: Final[str] = "Duplicate aspect kind in declaration: {kind}."

ERR_ASPECTS_UNKNOWN_ENTRY_TYPE: Final[str] = "Unknown aspect entry type: {entry_type}."

ERR_ASPECTS_EMPTY_DECLARATION: Final[str] = "Aspect declaration is empty."

ERR_ASPECTS_DECLARATION_FAILED: Final[str] = "Aspect declaration failed."


"""Aspect entry validation error messages."""

ERR_ASPECT_LOGGED_EVENT_EMPTY: Final[str] = "Logged.event must be a non-empty string."

ERR_ASPECT_REQUIRES_PERMISSION_EMPTY: Final[str] = "Requires.permission must be a non-empty string."

ERR_ASPECT_TENANT_SCOPED_PARAM_EMPTY: Final[str] = "TenantScoped.param_name must be a non-empty string."

ERR_ASPECT_THROTTLED_SCOPE_EMPTY: Final[str] = "Throttled.scope must be a non-empty string."

ERR_ASPECT_THROTTLED_RATE_EMPTY: Final[str] = "Throttled.rate must be a non-empty string."

ERR_ASPECT_THROTTLED_TIERS_NOT_TUPLE: Final[str] = "Throttled.tiers must be a tuple of pairs."

ERR_ASPECT_WRAP_ERRORS_AS_NOT_CLASS: Final[str] = "WrapErrors.as_ must be an exception class."

ERR_ASPECT_WRAP_ERRORS_CATCH_INVALID: Final[str] = "WrapErrors.catch must be a non-empty tuple of exception types."

ERR_ASPECT_MONITORED_EVENT_EMPTY: Final[str] = "Monitored.event must be a non-empty string."


"""Aspect dependency import error messages."""

ERR_ASPECT_LOGGED_IMPORT_MISSING: Final[str] = "logging-suite not installed; add [logging] extra."

ERR_ASPECT_REQUIRES_IMPORT_MISSING: Final[str] = "monitoring_suite.security not installed; reinstall monitoring-suite."

ERR_ASPECT_TENANT_SCOPED_IMPORT_MISSING: Final[str] = (
    "monitoring_suite.security not installed; reinstall monitoring-suite."
)

ERR_ASPECT_THROTTLED_IMPORT_MISSING: Final[str] = (
    "monitoring_suite.api_limiter not installed; reinstall monitoring-suite."
)

ERR_ASPECT_WRAP_ERRORS_IMPORT_MISSING: Final[str] = "monitoring_suite.errors not installed; it is a hard dependency."

ERR_ASPECT_MONITORED_IMPORT_MISSING: Final[str] = "monitoring_suite.monitoring not installed; it is a hard dependency."

ERR_ASPECT_RETRIED_POLICY_REQUIRED: Final[str] = (
    "Retried must specify exactly one of: policy (static) or policy_from_request (dynamic)."
)

ERR_ASPECT_RETRIED_POLICY_FROM_REQUEST_REQUIRED: Final[str] = (
    "Retried.policy_from_request must be a callable that returns RetryPolicy or None."
)

ERR_ASPECT_RETRIED_BOTH_POLICIES_PROVIDED: Final[str] = (
    "Retried cannot specify both policy and policy_from_request; use only one."
)


"""RequireMixins validation error messages."""

ERR_ASPECT_REQUIRE_MIXINS_BASES_INVALID: Final[str] = "RequireMixins.bases must be a non-empty tuple of types."

ERR_ASPECT_REQUIRE_MIXINS_FUNCTION_TARGET: Final[str] = (
    "RequireMixins is a class-only marker; function targets are not allowed."
)

ERR_ASPECT_REQUIRE_MIXINS_MISSING_BASES: Final[str] = "{class_name} does not inherit required mixins: {missing_bases}."


"""Ordering defaults."""

UNKNOWN_KIND_ORDER: Final[int] = 999


"""Decorator markers and member-name conventions."""

LOGGED_MARKER: Final[str] = "__logged_applied__"
PRIVATE_PREFIX: Final[str] = "_"
RETRIED_MARKER: Final[str] = "__retried_applied__"


"""Logged aspect event suffixes, payload keys and messages."""

EVENT_SUFFIX_START: Final[str] = ".start"
EVENT_SUFFIX_END: Final[str] = ".end"
EVENT_SUFFIX_ERROR: Final[str] = ".error"
PAYLOAD_KEY_LATENCY_MS: Final[str] = "latency_ms"
LOG_EXTRACTION_FAILED_PREFIX: Final[str] = "Logged: extraction failed for "


"""Enumeration member values."""

KIND_LOGGED: Final[str] = "LOGGED"
KIND_REQUIRES: Final[str] = "REQUIRES"
KIND_TENANT_SCOPED: Final[str] = "TENANT_SCOPED"
KIND_THROTTLED: Final[str] = "THROTTLED"
KIND_MONITORED: Final[str] = "MONITORED"
KIND_WRAP_ERRORS: Final[str] = "WRAP_ERRORS"
KIND_RETRIED: Final[str] = "RETRIED"
KIND_REQUIRE_MIXINS: Final[str] = "REQUIRE_MIXINS"


"""Entry defaults."""

DEFAULT_TENANT_PARAM_NAME: Final[str] = "tenant_id"


"""Separators and format pieces."""

NAME_SEPARATOR: Final[str] = ", "
