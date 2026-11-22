"""Safe import-missing tests via monkeypatch.setitem(sys.modules, name, None)."""

from __future__ import annotations

import sys

import pytest

from monitoring_suite.aspects.services.aspects import aspects_objects as objs


class TestImportMissingSafe:
    """Test lazy-import ImportError paths with safe monkeypatch (no __import__ leak)."""

    def test_logged_build_missing_logging_suite_logging(self, monkeypatch) -> None:
        """Logged decorator raises when applying to function with logging_suite.logging missing."""
        entry = objs.Logged(event="test")
        decorator = entry.build()

        monkeypatch.setitem(sys.modules, "logging_suite.logging", None)

        def op() -> int:
            return 42

        with pytest.raises(ModuleNotFoundError, match="logging_suite.logging"):
            decorator(op)

    def test_requires_build_missing_security(self, monkeypatch) -> None:
        """Requires.build() raises ImportError when monitoring_suite.security missing."""
        entry = objs.Requires(permission="read")

        monkeypatch.setitem(sys.modules, "monitoring_suite.security", None)
        monkeypatch.setitem(sys.modules, "monitoring_suite.security.decorators", None)
        monkeypatch.setitem(
            sys.modules, "monitoring_suite.security.decorators.requires", None
        )

        with pytest.raises(
            ImportError, match="monitoring_suite.security not installed"
        ):
            entry.build()

    def test_tenant_scoped_build_missing_security(self, monkeypatch) -> None:
        """TenantScoped.build() raises ImportError when monitoring_suite.security missing."""
        entry = objs.TenantScoped(param_name="tenant_id")

        monkeypatch.setitem(sys.modules, "monitoring_suite.security", None)
        monkeypatch.setitem(sys.modules, "monitoring_suite.security.decorators", None)
        monkeypatch.setitem(
            sys.modules, "monitoring_suite.security.decorators.tenant_scoped", None
        )

        with pytest.raises(
            ImportError, match="monitoring_suite.security not installed"
        ):
            entry.build()

    def test_throttled_build_missing_api_limiter(self, monkeypatch) -> None:
        """Throttled.build() raises ImportError when monitoring_suite.api_limiter missing."""
        entry = objs.Throttled(scope="api", rate="100/hour")

        monkeypatch.setitem(sys.modules, "monitoring_suite.api_limiter", None)
        monkeypatch.setitem(
            sys.modules, "monitoring_suite.api_limiter.decorators", None
        )
        monkeypatch.setitem(
            sys.modules, "monitoring_suite.api_limiter.decorators.throttled", None
        )

        with pytest.raises(
            ImportError, match="monitoring_suite.api_limiter not installed"
        ):
            entry.build()

    def test_wrap_errors_build_missing_errors(self, monkeypatch) -> None:
        """WrapErrors.build() raises ImportError when monitoring_suite.errors missing."""
        entry = objs.WrapErrors(as_=ValueError)

        monkeypatch.setitem(sys.modules, "monitoring_suite.errors", None)

        with pytest.raises(ImportError, match="monitoring_suite.errors not installed"):
            entry.build()

    def test_monitored_build_missing_monitoring(self, monkeypatch) -> None:
        """Monitored.build() raises ImportError when monitoring_suite.monitoring missing."""
        entry = objs.Monitored(event="test.operation")

        monkeypatch.setitem(sys.modules, "monitoring_suite.monitoring", None)
        monkeypatch.setitem(sys.modules, "monitoring_suite.monitoring.decorators", None)
        monkeypatch.setitem(
            sys.modules, "monitoring_suite.monitoring.decorators.monitored", None
        )
        monkeypatch.setitem(
            sys.modules,
            "monitoring_suite.monitoring.decorators.monitored.monitored_client",
            None,
        )

        with pytest.raises(
            ImportError, match="monitoring_suite.monitoring not installed"
        ):
            entry.build()

    def test_retried_build_missing_logging_suite_retry(self, monkeypatch) -> None:
        """Retried decorator raises when applying with logging_suite.retry missing."""
        from logging_suite.retry import RetryPolicy

        policy = RetryPolicy(
            max_attempts=2,
            backoff_base_seconds=0.1,
            backoff_multiplier=2.0,
            backoff_max_seconds=10.0,
            jitter=False,
        )
        entry = objs.Retried(policy=policy)
        decorator = entry.build()

        monkeypatch.setitem(sys.modules, "logging_suite.retry", None)

        def op() -> int:
            return 42

        with pytest.raises(ModuleNotFoundError, match="logging_suite.retry"):
            decorator(op)
