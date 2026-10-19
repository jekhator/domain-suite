"""Version consistency checks across the domain roots."""

from importlib.metadata import version as distribution_version

import domain_api_limiter
import domain_aspects
import domain_errors
import domain_monitoring
import domain_rag
import domain_security


class TestVersionConsistency:
    """Every domain root reports the installed distribution version."""

    def test_all_roots_match_distribution_version(self) -> None:
        """Each root __version__ equals the domain-suite distribution version."""
        versions = {
            "domain_api_limiter": domain_api_limiter.__version__,
            "domain_aspects": domain_aspects.__version__,
            "domain_errors": domain_errors.__version__,
            "domain_monitoring": domain_monitoring.__version__,
            "domain_rag": domain_rag.__version__,
            "domain_security": domain_security.__version__,
        }
        expected = distribution_version("domain-suite")

        assert versions == dict.fromkeys(versions, expected)
