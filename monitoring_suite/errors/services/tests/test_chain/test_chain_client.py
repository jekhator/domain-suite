"""Tests for ErrorChain client operations."""

from monitoring_suite.errors.domains.domain_error.domain_error import DomainError
from monitoring_suite.errors.services.chain.chain_client import ErrorChain
from monitoring_suite.errors.services.chain.chain_objects import ChainVia
from monitoring_suite.errors.services.tests.test_chain.conftest import FakeDomainClassifier


class CustomDomainError(DomainError):
    """A custom domain error for testing."""

    code = "CUSTOM"
    domain = "custom"
    http_status = 400
    retryable = True
    default_message = "Custom error occurred."


class TestErrorChainWrap:
    """Tests for ErrorChain.wrap()."""

    def test_wrap_returns_target_class(self) -> None:
        """wrap() returns an instance of the specified as_ class."""
        cause = ValueError("oops")
        result = ErrorChain.wrap(cause, as_=CustomDomainError)
        assert isinstance(result, CustomDomainError)

    def test_wrap_with_explicit_message(self) -> None:
        """wrap() uses the provided message."""
        cause = ValueError("oops")
        result = ErrorChain.wrap(cause, as_=CustomDomainError, message="custom msg")
        assert result.message == "custom msg"
        assert str(result) == "custom msg"

    def test_wrap_with_none_message_uses_default(self) -> None:
        """wrap() with message=None uses the class default_message."""
        cause = ValueError("oops")
        result = ErrorChain.wrap(cause, as_=CustomDomainError, message=None)
        assert result.message == CustomDomainError.default_message

    def test_wrap_with_no_message_arg_uses_default(self) -> None:
        """wrap() without message arg uses the class default_message."""
        cause = ValueError("oops")
        result = ErrorChain.wrap(cause, as_=CustomDomainError)
        assert result.message == CustomDomainError.default_message

    def test_wrap_stores_context_kwargs(self) -> None:
        """wrap() passes context kwargs to the domain error."""
        cause = ValueError("oops")
        result = ErrorChain.wrap(cause, as_=CustomDomainError, user_id=123, request_id="abc")
        assert result.context["user_id"] == 123
        assert result.context["request_id"] == "abc"

    def test_wrap_intended_for_raise_from(self) -> None:
        """wrap() returns an object ready to be raised with 'from err'."""
        original = ValueError("bad")
        wrapped = ErrorChain.wrap(original, as_=CustomDomainError, message="wrapped")
        try:
            raise wrapped from original
        except CustomDomainError as error:
            assert error.__cause__ is original


class TestErrorChainHistory:
    """Tests for ErrorChain.history()."""

    def test_single_error_is_root(self) -> None:
        """history() of a single error returns one ROOT link."""
        cause = ValueError("oops")
        classifier = FakeDomainClassifier()
        links = ErrorChain.history(cause, classifiers=(classifier,))
        assert len(links) == 1
        assert links[0].type_name == "ValueError"
        assert links[0].message == "oops"
        assert links[0].via == ChainVia.ROOT
        assert links[0].domain == "validation"

    def test_explicit_cause_chain(self) -> None:
        """history() walks __cause__ chain, marking links as ROOT then CAUSE."""
        inner = ValueError("inner")
        outer = RuntimeError("outer")
        try:
            raise outer from inner
        except RuntimeError as error:
            links = ErrorChain.history(error)
        assert len(links) == 2
        assert links[0].type_name == "RuntimeError"
        assert links[0].via == ChainVia.ROOT
        assert links[1].type_name == "ValueError"
        assert links[1].via == ChainVia.CAUSE

    def test_implicit_context_chain(self) -> None:
        """history() walks __context__ chain when __suppress_context__ is False."""
        inner = ValueError("inner")
        outer = RuntimeError("outer")
        try:
            try:
                raise inner
            except ValueError:
                raise outer
        except RuntimeError as error:
            links = ErrorChain.history(error)
        assert len(links) == 2
        assert links[0].type_name == "RuntimeError"
        assert links[0].via == ChainVia.ROOT
        assert links[1].type_name == "ValueError"
        assert links[1].via == ChainVia.CONTEXT

    def test_suppress_context_stops_chain(self) -> None:
        """history() stops at __context__ when __suppress_context__ is True."""
        inner = ValueError("inner")
        outer = RuntimeError("outer")
        try:
            try:
                raise inner
            except ValueError:
                raise outer from None
        except RuntimeError as error:
            links = ErrorChain.history(error)
        assert len(links) == 1
        assert links[0].type_name == "RuntimeError"

    def test_cycle_guard(self) -> None:
        """history() terminates on cycles and does not infinite loop."""
        e1: BaseException = ValueError("e1")
        e2: BaseException = RuntimeError("e2")
        e1.__cause__ = e2
        e2.__cause__ = e1
        links = ErrorChain.history(e1)
        assert len(links) == 2
        assert links[0].type_name == "ValueError"
        assert links[1].type_name == "RuntimeError"

    def test_domain_resolution_from_classvar(self) -> None:
        """history() resolves domain from DomainError.domain classvar."""
        cause = CustomDomainError()
        links = ErrorChain.history(cause)
        assert links[0].domain == "custom"

    def test_domain_resolution_from_classifier(self) -> None:
        """history() uses the first matching classifier to resolve domain."""
        cause = ValueError("test")
        classifier = FakeDomainClassifier()
        links = ErrorChain.history(cause, classifiers=(classifier,))
        assert links[0].domain == "validation"

    def test_domain_resolution_classvar_takes_precedence(self) -> None:
        """history() prefers classvar domain over classifier."""
        cause = CustomDomainError()
        classifier = FakeDomainClassifier()
        links = ErrorChain.history(cause, classifiers=(classifier,))
        assert links[0].domain == "custom"

    def test_context_propagation_from_domain_error(self) -> None:
        """history() propagates DomainError.context into ChainLink.context."""
        cause = CustomDomainError(user_id=123, request_id="abc")
        links = ErrorChain.history(cause)
        assert links[0].context == {"user_id": 123, "request_id": "abc"}

    def test_context_in_log_extra_for_domain_error(self) -> None:
        """to_log_extra() includes the propagated context from history()."""
        cause = CustomDomainError(user_id=123, request_id="abc")
        links = ErrorChain.history(cause)
        extra = links[0].to_log_extra()
        assert extra["context"] == {"user_id": 123, "request_id": "abc"}

    def test_context_empty_dict_for_foreign_error(self) -> None:
        """history() assigns empty dict context to foreign errors."""
        cause = ValueError("test")
        links = ErrorChain.history(cause)
        assert links[0].context == {}

    def test_domain_fallback_to_python(self) -> None:
        """history() falls back to 'python' when no classifier matches."""
        cause = KeyError("key")
        links = ErrorChain.history(cause)
        assert links[0].domain == "python"

    def test_code_attribute_extracted(self) -> None:
        """history() extracts code attribute from DomainError."""
        cause = CustomDomainError()
        links = ErrorChain.history(cause)
        assert links[0].code == "CUSTOM"

    def test_code_none_when_absent(self) -> None:
        """history() sets code to None when error has no code attribute."""
        cause = ValueError("test")
        links = ErrorChain.history(cause)
        assert links[0].code is None

    def test_multiple_classifiers_first_match_wins(self) -> None:
        """history() uses the first classifier that returns non-None."""
        classifier1 = FakeDomainClassifier()
        classifier2 = FakeDomainClassifier()
        cause = TypeError("test")
        links = ErrorChain.history(cause, classifiers=(classifier1, classifier2))
        assert links[0].domain == "typing"


class TestErrorChainCrossings:
    """Tests for ErrorChain.crossings()."""

    def test_no_crossings_single_error(self) -> None:
        """crossings() returns empty tuple for a single error."""
        cause = ValueError("oops")
        crossings = ErrorChain.crossings(cause)
        assert crossings == ()

    def test_no_crossings_same_domain(self) -> None:
        """crossings() returns empty when all links have the same domain."""
        cause = KeyError("same domain")
        try:
            raise RuntimeError("also python domain") from cause
        except RuntimeError as error:
            classifier = FakeDomainClassifier()
            crossings = ErrorChain.crossings(error, classifiers=(classifier,))
        assert len(crossings) == 0

    def test_crossing_on_domain_change(self) -> None:
        """crossings() returns DomainCrossing when adjacent links differ in domain."""
        inner = ValueError("validation failed")
        outer = RuntimeError("app failed")
        try:
            raise outer from inner
        except RuntimeError as error:
            classifier = FakeDomainClassifier()
            crossings = ErrorChain.crossings(error, classifiers=(classifier,))
        assert len(crossings) == 1
        assert crossings[0].cause.domain == "validation"
        assert crossings[0].effect.domain == "python"

    def test_crossing_cause_effect_pairing(self) -> None:
        """crossings() correctly pairs cause and effect in DomainCrossing."""
        inner = CustomDomainError()
        outer = ValueError("oops")
        try:
            raise outer from inner
        except ValueError as error:
            classifier = FakeDomainClassifier()
            crossings = ErrorChain.crossings(error, classifiers=(classifier,))
        assert len(crossings) == 1
        assert crossings[0].cause.type_name == "CustomDomainError"
        assert crossings[0].cause.domain == "custom"
        assert crossings[0].effect.type_name == "ValueError"
        assert crossings[0].effect.domain == "validation"

    def test_multiple_crossings(self) -> None:
        """crossings() returns multiple DomainCrossing for multi-hop chains."""
        classifier = FakeDomainClassifier()
        e1 = CustomDomainError()
        e2 = ValueError("oops")
        e3 = KeyError("key")
        try:
            try:
                try:
                    raise e1
                except CustomDomainError:
                    raise e2 from e1
            except ValueError:
                raise e3 from e2
        except KeyError as error:
            crossings = ErrorChain.crossings(error, classifiers=(classifier,))
        assert len(crossings) == 2


class TestErrorChainDomainOf:
    """Tests for ErrorChain._domain_of()."""

    def test_domain_from_classvar(self) -> None:
        """_domain_of returns the domain classvar if it is a string."""
        cause = CustomDomainError()
        domain = ErrorChain._domain_of(cause, classifiers=())
        assert domain == "custom"

    def test_domain_from_first_matching_classifier(self) -> None:
        """_domain_of uses the first classifier that returns non-None."""
        classifier = FakeDomainClassifier()
        cause = ValueError("test")
        domain = ErrorChain._domain_of(cause, classifiers=(classifier,))
        assert domain == "validation"

    def test_domain_fallback_python(self) -> None:
        """_domain_of defaults to 'python' when no classifier matches."""
        classifier = FakeDomainClassifier()
        cause = KeyError("test")
        domain = ErrorChain._domain_of(cause, classifiers=(classifier,))
        assert domain == "python"

    def test_domain_ignores_non_string_attribute(self) -> None:
        """_domain_of ignores a domain attribute that is not a string."""
        cause = ValueError("test")
        cause.domain = 123  # type: ignore
        classifier = FakeDomainClassifier()
        domain = ErrorChain._domain_of(cause, classifiers=(classifier,))
        assert domain == "validation"
