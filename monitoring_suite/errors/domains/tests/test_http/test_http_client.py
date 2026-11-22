"""Tests for the HTTP domain classifier."""

from __future__ import annotations

from monitoring_suite.errors.domains.constants import http as const
from monitoring_suite.errors.domains.http.http_client import HttpClassifier, http


class TestHttpClassifierHTTPErrorTree:
    """Tests for HttpClassifier coverage of the httpx HTTPError exception tree."""

    def test_httpx_httperror_returns_http(self) -> None:
        """httpx.HTTPError is classified as http."""
        import httpx

        error = httpx.HTTPError("test")
        result = HttpClassifier().classify(error)
        assert result == const.HTTP

    def test_httpx_connecttimeout_returns_http(self) -> None:
        """httpx.ConnectTimeout is classified as http."""
        import httpx

        error = httpx.ConnectTimeout("test")
        result = HttpClassifier().classify(error)
        assert result == const.HTTP

    def test_httpx_connecterror_returns_http(self) -> None:
        """httpx.ConnectError is classified as http."""
        import httpx

        error = httpx.ConnectError("test")
        result = HttpClassifier().classify(error)
        assert result == const.HTTP

    def test_httpx_httpstatuserror_returns_http(self) -> None:
        """httpx.HTTPStatusError is classified as http."""
        import httpx

        error = httpx.HTTPStatusError("test", request=None, response=None)  # type: ignore[arg-type]
        result = HttpClassifier().classify(error)
        assert result == const.HTTP

    def test_httpx_toomanyredirects_returns_http(self) -> None:
        """httpx.TooManyRedirects is classified as http."""
        import httpx

        error = httpx.TooManyRedirects("test")
        result = HttpClassifier().classify(error)
        assert result == const.HTTP


class TestHttpClassifierHttpxOutliers:
    """Tests for HttpClassifier coverage of httpx exceptions outside HTTPError tree."""

    def test_httpx_invalidurl_returns_http(self) -> None:
        """httpx.InvalidURL is classified as http (not an HTTPError subclass, origin-based)."""
        import httpx

        error = httpx.InvalidURL("test")
        result = HttpClassifier().classify(error)
        assert result == const.HTTP

    def test_httpx_cookieconflict_returns_http(self) -> None:
        """httpx.CookieConflict is classified as http (not an HTTPError subclass)."""
        import httpx

        error = httpx.CookieConflict("test")
        result = HttpClassifier().classify(error)
        assert result == const.HTTP

    def test_httpx_streamerror_returns_http(self) -> None:
        """httpx.StreamError subclasses RuntimeError; classified as http by origin."""
        import httpx

        error = httpx.StreamError("test")
        result = HttpClassifier().classify(error)
        assert result == const.HTTP

    def test_httpx_streamconsumed_returns_http(self) -> None:
        """httpx.StreamConsumed is classified as http (origin-based, guards regression to base-class matching)."""
        import httpx

        error = httpx.StreamConsumed()
        result = HttpClassifier().classify(error)
        assert result == const.HTTP

    def test_httpx_responsenotread_returns_http(self) -> None:
        """httpx.ResponseNotRead is classified as http."""
        import httpx

        error = httpx.ResponseNotRead()
        result = HttpClassifier().classify(error)
        assert result == const.HTTP


class TestHttpClassifierRequests:
    """Tests for HttpClassifier coverage of requests library exceptions."""

    def test_requests_requestexception_returns_http(self) -> None:
        """requests.RequestException is classified as http."""
        import requests

        error = requests.RequestException("test")
        result = HttpClassifier().classify(error)
        assert result == const.HTTP

    def test_requests_invalidurl_returns_http(self) -> None:
        """
        requests.exceptions.InvalidURL is classified as http (__module__ is requests.exceptions → top-level requests).
        """
        from requests.exceptions import InvalidURL

        error = InvalidURL("test")
        result = HttpClassifier().classify(error)
        assert result == const.HTTP


class TestHttpClassifierAiohttp:
    """Tests for HttpClassifier coverage of aiohttp library exceptions."""

    def test_aiohttp_clienterror_returns_http(self) -> None:
        """aiohttp.ClientError is classified as http (__module__ is aiohttp.client_exceptions → top-level aiohttp)."""
        import aiohttp

        error = aiohttp.ClientError("test")
        result = HttpClassifier().classify(error)
        assert result == const.HTTP


class TestHttpClassifierUnrecognized:
    """Tests for HttpClassifier handling of unrecognized exceptions."""

    def test_valueerror_returns_none(self) -> None:
        """ValueError from builtins is not an HTTP library; classified as None."""
        error = ValueError("test")
        result = HttpClassifier().classify(error)
        assert result is None

    def test_runtimeerror_returns_none(self) -> None:
        """RuntimeError from builtins is not an HTTP library; classified as None."""
        error = RuntimeError("test")
        result = HttpClassifier().classify(error)
        assert result is None

    def test_custom_exception_returns_none(self) -> None:
        """Custom exception defined in the test module (not from a lib) is classified as None."""

        class CustomException(Exception):
            """Custom exception for testing."""

        error = CustomException("test")
        result = HttpClassifier().classify(error)
        assert result is None


class TestHttpClassifierSingleton:
    """Tests for the http singleton instance and stateless behavior."""

    def test_http_is_httpclassifier_instance(self) -> None:
        """The http module-level singleton is an HttpClassifier instance."""
        assert isinstance(http, HttpClassifier)

    def test_classify_is_stateless(self) -> None:
        """Repeated classify() calls on the same error return the same result."""
        import httpx

        error = httpx.HTTPError("test")
        result1 = http.classify(error)
        result2 = http.classify(error)
        assert result1 == result2 == const.HTTP

    def test_singleton_classify_httpx(self) -> None:
        """The http singleton classifies httpx.HTTPError correctly."""
        import httpx

        error = httpx.HTTPError("test")
        result = http.classify(error)
        assert result == const.HTTP

    def test_singleton_classify_unrecognized(self) -> None:
        """The http singleton returns None for unrecognized exceptions."""
        error = ValueError("test")
        result = http.classify(error)
        assert result is None
