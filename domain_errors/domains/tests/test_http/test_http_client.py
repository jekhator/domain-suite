"""Tests for the HTTP domain classifier."""

from __future__ import annotations

from domain_errors.domains.constants import http as const
from domain_errors.domains.http.http_client import HttpClassifier, http


class TestHttpClassifierHTTPErrorTree:
    """Tests for HttpClassifier coverage of the httpx HTTPError exception tree."""

    def test_httpx_httperror_returns_http(self) -> None:
        """httpx.HTTPError is classified as http."""
        import httpx

        err = httpx.HTTPError("test")
        result = HttpClassifier().classify(err)
        assert result == const.HTTP

    def test_httpx_connecttimeout_returns_http(self) -> None:
        """httpx.ConnectTimeout is classified as http."""
        import httpx

        err = httpx.ConnectTimeout("test")
        result = HttpClassifier().classify(err)
        assert result == const.HTTP

    def test_httpx_connecterror_returns_http(self) -> None:
        """httpx.ConnectError is classified as http."""
        import httpx

        err = httpx.ConnectError("test")
        result = HttpClassifier().classify(err)
        assert result == const.HTTP

    def test_httpx_httpstatuserror_returns_http(self) -> None:
        """httpx.HTTPStatusError is classified as http."""
        import httpx

        err = httpx.HTTPStatusError("test", request=None, response=None)  # type: ignore[arg-type]
        result = HttpClassifier().classify(err)
        assert result == const.HTTP

    def test_httpx_toomanyredirects_returns_http(self) -> None:
        """httpx.TooManyRedirects is classified as http."""
        import httpx

        err = httpx.TooManyRedirects("test")
        result = HttpClassifier().classify(err)
        assert result == const.HTTP


class TestHttpClassifierHttpxOutliers:
    """Tests for HttpClassifier coverage of httpx exceptions outside HTTPError tree."""

    def test_httpx_invalidurl_returns_http(self) -> None:
        """httpx.InvalidURL is classified as http (not an HTTPError subclass, origin-based)."""
        import httpx

        err = httpx.InvalidURL("test")
        result = HttpClassifier().classify(err)
        assert result == const.HTTP

    def test_httpx_cookieconflict_returns_http(self) -> None:
        """httpx.CookieConflict is classified as http (not an HTTPError subclass)."""
        import httpx

        err = httpx.CookieConflict("test")
        result = HttpClassifier().classify(err)
        assert result == const.HTTP

    def test_httpx_streamerror_returns_http(self) -> None:
        """httpx.StreamError subclasses RuntimeError; classified as http by origin."""
        import httpx

        err = httpx.StreamError("test")
        result = HttpClassifier().classify(err)
        assert result == const.HTTP

    def test_httpx_streamconsumed_returns_http(self) -> None:
        """httpx.StreamConsumed is classified as http (origin-based, guards regression to base-class matching)."""
        import httpx

        err = httpx.StreamConsumed()
        result = HttpClassifier().classify(err)
        assert result == const.HTTP

    def test_httpx_responsenotread_returns_http(self) -> None:
        """httpx.ResponseNotRead is classified as http."""
        import httpx

        err = httpx.ResponseNotRead()
        result = HttpClassifier().classify(err)
        assert result == const.HTTP


class TestHttpClassifierRequests:
    """Tests for HttpClassifier coverage of requests library exceptions."""

    def test_requests_requestexception_returns_http(self) -> None:
        """requests.RequestException is classified as http."""
        import requests

        err = requests.RequestException("test")
        result = HttpClassifier().classify(err)
        assert result == const.HTTP

    def test_requests_invalidurl_returns_http(self) -> None:
        """requests.exceptions.InvalidURL is classified as http (__module__ is requests.exceptions, top-level requests)."""
        from requests.exceptions import InvalidURL

        err = InvalidURL("test")
        result = HttpClassifier().classify(err)
        assert result == const.HTTP


class TestHttpClassifierAiohttp:
    """Tests for HttpClassifier coverage of aiohttp library exceptions."""

    def test_aiohttp_clienterror_returns_http(self) -> None:
        """aiohttp.ClientError is classified as http (__module__ is aiohttp.client_exceptions, top-level aiohttp)."""
        import aiohttp

        err = aiohttp.ClientError("test")
        result = HttpClassifier().classify(err)
        assert result == const.HTTP


class TestHttpClassifierUnrecognized:
    """Tests for HttpClassifier handling of unrecognized exceptions."""

    def test_valueerror_returns_none(self) -> None:
        """ValueError from builtins is not an HTTP library; classified as None."""
        err = ValueError("test")
        result = HttpClassifier().classify(err)
        assert result is None

    def test_runtimeerror_returns_none(self) -> None:
        """RuntimeError from builtins is not an HTTP library; classified as None."""
        err = RuntimeError("test")
        result = HttpClassifier().classify(err)
        assert result is None

    def test_custom_exception_returns_none(self) -> None:
        """Custom exception defined in the test module (not from a lib) is classified as None."""

        class CustomException(Exception):
            """Custom exception for testing."""

        err = CustomException("test")
        result = HttpClassifier().classify(err)
        assert result is None


class TestHttpClassifierSingleton:
    """Tests for the http singleton instance and stateless behavior."""

    def test_http_is_httpclassifier_instance(self) -> None:
        """The http module-level singleton is an HttpClassifier instance."""
        assert isinstance(http, HttpClassifier)

    def test_classify_is_stateless(self) -> None:
        """Repeated classify() calls on the same error return the same result."""
        import httpx

        err = httpx.HTTPError("test")
        result1 = http.classify(err)
        result2 = http.classify(err)
        assert result1 == result2 == const.HTTP

    def test_singleton_classify_httpx(self) -> None:
        """The http singleton classifies httpx.HTTPError correctly."""
        import httpx

        err = httpx.HTTPError("test")
        result = http.classify(err)
        assert result == const.HTTP

    def test_singleton_classify_unrecognized(self) -> None:
        """The http singleton returns None for unrecognized exceptions."""
        err = ValueError("test")
        result = http.classify(err)
        assert result is None
