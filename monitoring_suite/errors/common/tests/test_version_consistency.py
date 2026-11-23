"""Test that all domain roots report consistent versions."""

from __future__ import annotations


class TestVersionConsistency:
    """Test version consistency across all domain roots."""

    def test_all_roots_same_version(self) -> None:
        """All 6 domain roots should report identical __version__."""
        import monitoring_suite.api_limiter
        import monitoring_suite.aspects
        import monitoring_suite.errors
        import monitoring_suite.monitoring
        import monitoring_suite.rag
        import monitoring_suite.security

        versions = {
            "monitoring_suite.api_limiter": monitoring_suite.api_limiter.__version__,
            "monitoring_suite.aspects": monitoring_suite.aspects.__version__,
            "monitoring_suite.errors": monitoring_suite.errors.__version__,
            "monitoring_suite.monitoring": monitoring_suite.monitoring.__version__,
            "monitoring_suite.rag": monitoring_suite.rag.__version__,
            "monitoring_suite.security": monitoring_suite.security.__version__
        }

        unique_versions = set(versions.values())
        assert unique_versions == {monitoring_suite.errors.__version__}, (
            f"Version mismatch: {versions}"
        )
