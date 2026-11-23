"""Tests for the rate-limit error hierarchy."""

from __future__ import annotations

from monitoring_suite.api_limiter.errors.api_limiter_errors import (
    RateLimitExceeded,
    ThrottleDeclarationError,
    ThrottleError,
)
from monitoring_suite.api_limiter.errors.constants import api_limiter_errors as const
from monitoring_suite.errors import DomainError


class TestThrottleError:
    """ThrottleError is the base rate-limit domain error."""

    def test_inheritance_from_domain_error(self) -> None:
        """ThrottleError inherits from DomainError."""
        assert issubclass(ThrottleError, DomainError)

    def test_domain_attribute(self) -> None:
        """ThrottleError has domain api_limiter."""
        assert ThrottleError.domain == "api_limiter"

    def test_code_attribute(self) -> None:
        """ThrottleError has code throttle_error."""
        assert ThrottleError.code == "throttle_error"

    def test_http_status_attribute(self) -> None:
        """ThrottleError has http_status 429."""
        assert ThrottleError.http_status == 429

    def test_retryable_attribute(self) -> None:
        """ThrottleError is retryable."""
        assert ThrottleError.retryable is True

    def test_default_message_attribute(self) -> None:
        """ThrottleError has default_message."""
        assert (ThrottleError.default_message == const.ERR_API_LIMITER_CONSTRAINT_VIOLATED)

    def test_constructor_with_message(self) -> None:
        """ThrottleError constructor accepts message."""
        error = ThrottleError(message="Custom message")
        assert error.message == "Custom message"

    def test_constructor_with_context(self) -> None:
        """ThrottleError constructor captures context."""
        error = ThrottleError(message="Test", key="value", number=42)
        assert error.context == {"key": "value", "number": 42}

    def test_constructor_without_message_uses_default(self) -> None:
        """ThrottleError constructor uses default_message when none provided."""
        error = ThrottleError()
        assert error.message == const.ERR_API_LIMITER_CONSTRAINT_VIOLATED


class TestRateLimitExceeded:
    """RateLimitExceeded indicates a rate limit was exceeded."""

    def test_inheritance_from_throttle_error(self) -> None:
        """RateLimitExceeded inherits from ThrottleError."""
        assert issubclass(RateLimitExceeded, ThrottleError)

    def test_inheritance_from_domain_error(self) -> None:
        """RateLimitExceeded inherits from DomainError."""
        assert issubclass(RateLimitExceeded, DomainError)

    def test_code_attribute(self) -> None:
        """RateLimitExceeded has code rate_limit_exceeded."""
        assert RateLimitExceeded.code == "rate_limit_exceeded"

    def test_http_status_inherited(self) -> None:
        """RateLimitExceeded inherits http_status 429 from ThrottleError."""
        assert RateLimitExceeded.http_status == 429

    def test_retryable_inherited(self) -> None:
        """RateLimitExceeded inherits retryable True from ThrottleError."""
        assert RateLimitExceeded.retryable is True

    def test_domain_inherited(self) -> None:
        """RateLimitExceeded inherits domain from ThrottleError."""
        assert RateLimitExceeded.domain == "api_limiter"

    def test_default_message_attribute(self) -> None:
        """RateLimitExceeded has default_message."""
        assert RateLimitExceeded.default_message == const.ERR_API_LIMITER_RATE_EXCEEDED

    def test_constructor_with_message_and_context(self) -> None:
        """RateLimitExceeded captures message and context."""
        error = RateLimitExceeded(message="Limit exceeded", scope="test_scope")
        assert error.message == "Limit exceeded"
        assert error.context == {"scope": "test_scope"}


class TestThrottleDeclarationError:
    """ThrottleDeclarationError indicates an invalid throttle declaration."""

    def test_inheritance_from_throttle_error(self) -> None:
        """ThrottleDeclarationError inherits from ThrottleError."""
        assert issubclass(ThrottleDeclarationError, ThrottleError)

    def test_inheritance_from_domain_error(self) -> None:
        """ThrottleDeclarationError inherits from DomainError."""
        assert issubclass(ThrottleDeclarationError, DomainError)

    def test_code_attribute(self) -> None:
        """ThrottleDeclarationError has code throttle_declaration_invalid."""
        assert ThrottleDeclarationError.code == "throttle_declaration_invalid"

    def test_http_status_attribute(self) -> None:
        """ThrottleDeclarationError has http_status 500."""
        assert ThrottleDeclarationError.http_status == 500

    def test_retryable_attribute(self) -> None:
        """ThrottleDeclarationError is not retryable."""
        assert ThrottleDeclarationError.retryable is False

    def test_domain_inherited(self) -> None:
        """ThrottleDeclarationError inherits domain from ThrottleError."""
        assert ThrottleDeclarationError.domain == "api_limiter"

    def test_default_message_attribute(self) -> None:
        """ThrottleDeclarationError has default_message."""
        assert (ThrottleDeclarationError.default_message == const.ERR_API_LIMITER_DECLARATION_INVALID)

    def test_constructor_with_message_and_context(self) -> None:
        """ThrottleDeclarationError captures message and context."""
        error = ThrottleDeclarationError(message="Bad rate", rate="invalid", period="unknown")
        assert error.message == "Bad rate"
        assert error.context == {"rate": "invalid", "period": "unknown"}

    def test_constructor_preserves_context_keys(self) -> None:
        """ThrottleDeclarationError preserves all context keys."""
        error = ThrottleDeclarationError(message="Test", requests=0, scope="", tier="")
        assert "requests" in error.context
        assert "scope" in error.context
        assert "tier" in error.context
