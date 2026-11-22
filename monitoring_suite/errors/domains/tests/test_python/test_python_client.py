"""Tests for the stdlib domain classifier."""

from monitoring_suite.errors.domains.constants import python as const
from monitoring_suite.errors.domains.python.python_client import (
    PythonClassifier,
    python,
)


class TestPythonClassifierNetworkFamily:
    """Tests for PythonClassifier mapping NETWORK-family exceptions."""

    def test_connection_error_maps_to_network(self) -> None:
        """ConnectionError is classified as NETWORK domain."""
        err = ConnectionError("connection failed")
        classifier = PythonClassifier()
        assert classifier.classify(err) == const.NETWORK

    def test_timeout_error_maps_to_network(self) -> None:
        """TimeoutError is classified as NETWORK domain."""
        err = TimeoutError("request timed out")
        classifier = PythonClassifier()
        assert classifier.classify(err) == const.NETWORK


class TestPythonClassifierOSFamily:
    """Tests for PythonClassifier mapping OS-family exceptions."""

    def test_file_not_found_error_maps_to_os(self) -> None:
        """FileNotFoundError is classified as OS domain."""
        err = FileNotFoundError("file not found")
        classifier = PythonClassifier()
        assert classifier.classify(err) == const.OS

    def test_permission_error_maps_to_os(self) -> None:
        """PermissionError is classified as OS domain."""
        err = PermissionError("access denied")
        classifier = PythonClassifier()
        assert classifier.classify(err) == const.OS

    def test_oserror_maps_to_os(self) -> None:
        """OSError is classified as OS domain."""
        err = OSError("os-level error")
        classifier = PythonClassifier()
        assert classifier.classify(err) == const.OS

    def test_file_not_found_is_oserror_subtype_maps_to_os(self) -> None:
        """FileNotFoundError subtype of OSError routes to OS via isinstance."""
        err = FileNotFoundError("missing file")
        classifier = PythonClassifier()
        assert classifier.classify(err) == const.OS
        assert isinstance(err, OSError)


class TestPythonClassifierLogicFamily:
    """Tests for PythonClassifier mapping LOGIC-family exceptions."""

    def test_value_error_maps_to_logic(self) -> None:
        """ValueError is classified as LOGIC domain."""
        err = ValueError("invalid value")
        classifier = PythonClassifier()
        assert classifier.classify(err) == const.LOGIC

    def test_key_error_maps_to_logic(self) -> None:
        """KeyError is classified as LOGIC domain."""
        err = KeyError("missing key")
        classifier = PythonClassifier()
        assert classifier.classify(err) == const.LOGIC

    def test_type_error_maps_to_logic(self) -> None:
        """TypeError is classified as LOGIC domain."""
        err = TypeError("wrong type")
        classifier = PythonClassifier()
        assert classifier.classify(err) == const.LOGIC


class TestPythonClassifierAssertionFamily:
    """Tests for PythonClassifier mapping ASSERTION-family exceptions."""

    def test_assertion_error_maps_to_assertion(self) -> None:
        """AssertionError is classified as ASSERTION domain."""
        err = AssertionError("assertion failed")
        classifier = PythonClassifier()
        assert classifier.classify(err) == const.ASSERTION


class TestPythonClassifierUnrecognized:
    """Tests for PythonClassifier handling unrecognized exceptions."""

    def test_runtime_error_returns_none(self) -> None:
        """RuntimeError (unrecognized) returns None."""
        err = RuntimeError("runtime issue")
        classifier = PythonClassifier()
        assert classifier.classify(err) is None

    def test_generic_exception_returns_none(self) -> None:
        """Generic Exception (unrecognized) returns None."""
        err = Exception("generic error")
        classifier = PythonClassifier()
        assert classifier.classify(err) is None

    def test_custom_error_returns_none(self) -> None:
        """Custom error not in families returns None."""

        class CustomException(Exception):
            pass

        err = CustomException("custom")
        classifier = PythonClassifier()
        assert classifier.classify(err) is None


class TestPythonClassifierStateless:
    """Tests for PythonClassifier purity and statefulness."""

    def test_classify_is_stateless(self) -> None:
        """classify() returns same result on repeated calls (no mutation)."""
        err = ValueError("test error")
        classifier = PythonClassifier()
        result1 = classifier.classify(err)
        result2 = classifier.classify(err)
        assert result1 == result2
        assert result1 == const.LOGIC


class TestPythonSingleton:
    """Tests for the module-level python singleton."""

    def test_python_singleton_is_instance_of_classifier(self) -> None:
        """python is an instance of PythonClassifier."""
        assert isinstance(python, PythonClassifier)

    def test_python_singleton_classifies_correctly(self) -> None:
        """python singleton classify() works as expected."""
        err = ConnectionError("connection failed")
        assert python.classify(err) == const.NETWORK
