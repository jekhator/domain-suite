"""Tests for the cloud domain classifier."""

from __future__ import annotations

from monitoring_suite.errors.domains.cloud.cloud_client import CloudClassifier, cloud
from monitoring_suite.errors.domains.constants import cloud as const


class TestCloudClassifierBotocore:
    """Tests for CloudClassifier coverage of botocore exception family."""

    def test_botocore_clienterror_returns_cloud(self) -> None:
        """botocore.exceptions.ClientError is classified as cloud."""
        from botocore.exceptions import ClientError  # type: ignore[import-untyped]

        error = ClientError({"Error": {"Code": "TestError"}}, "TestOperation")
        result = CloudClassifier().classify(error)
        assert result == const.CLOUD

    def test_botocore_botocoreerror_returns_cloud(self) -> None:
        """botocore.exceptions.BotoCoreError is classified as cloud."""
        from botocore.exceptions import BotoCoreError  # type: ignore[import-untyped]

        error = BotoCoreError()
        result = CloudClassifier().classify(error)
        assert result == const.CLOUD

    def test_botocore_connectionerror_returns_cloud(self) -> None:
        """botocore.exceptions.ConnectionError is classified as cloud."""
        from botocore.exceptions import (
            ConnectionError as BotocoreConnectionError,  # type: ignore[import-untyped]
        )

        error = BotocoreConnectionError(error="test")
        result = CloudClassifier().classify(error)
        assert result == const.CLOUD


class TestCloudClassifierBoto3:
    """Tests for CloudClassifier coverage of boto3 exception family."""

    def test_boto3_boto3error_returns_cloud(self) -> None:
        """boto3.exceptions.Boto3Error is classified as cloud."""
        from boto3.exceptions import Boto3Error  # type: ignore[import-untyped]

        error = Boto3Error()
        result = CloudClassifier().classify(error)
        assert result == const.CLOUD

    def test_boto3_s3uploadedfailederror_returns_cloud(self) -> None:
        """boto3.exceptions.S3UploadFailedError is classified as cloud."""
        from boto3.exceptions import S3UploadFailedError  # type: ignore[import-untyped]

        error = S3UploadFailedError("test")
        result = CloudClassifier().classify(error)
        assert result == const.CLOUD


class TestCloudClassifierUnrecognized:
    """Tests for CloudClassifier handling of unrecognized exceptions."""

    def test_valueerror_returns_none(self) -> None:
        """ValueError from builtins is not a cloud library; classified as None."""
        error = ValueError("test")
        result = CloudClassifier().classify(error)
        assert result is None

    def test_runtimeerror_returns_none(self) -> None:
        """RuntimeError from builtins is not a cloud library; classified as None."""
        error = RuntimeError("test")
        result = CloudClassifier().classify(error)
        assert result is None

    def test_custom_exception_returns_none(self) -> None:
        """Custom exception defined in the test module (not from a lib) is classified as None."""

        class CustomException(Exception):
            """Custom exception for testing."""

        error = CustomException("test")
        result = CloudClassifier().classify(error)
        assert result is None


class TestCloudClassifierSingleton:
    """Tests for the cloud singleton instance and stateless behavior."""

    def test_cloud_is_cloudclassifier_instance(self) -> None:
        """The cloud module-level singleton is a CloudClassifier instance."""
        assert isinstance(cloud, CloudClassifier)

    def test_classify_is_stateless(self) -> None:
        """Repeated classify() calls on the same error return the same result."""
        from botocore.exceptions import ClientError  # type: ignore[import-untyped]

        error = ClientError({"Error": {"Code": "TestError"}}, "TestOperation")
        result1 = cloud.classify(error)
        result2 = cloud.classify(error)
        assert result1 == result2 == const.CLOUD

    def test_singleton_classify_botocore(self) -> None:
        """The cloud singleton classifies botocore.exceptions.ClientError correctly."""
        from botocore.exceptions import ClientError  # type: ignore[import-untyped]

        error = ClientError({"Error": {"Code": "TestError"}}, "TestOperation")
        result = cloud.classify(error)
        assert result == const.CLOUD

    def test_singleton_classify_boto3(self) -> None:
        """The cloud singleton classifies boto3.exceptions.Boto3Error correctly."""
        from boto3.exceptions import Boto3Error  # type: ignore[import-untyped]

        error = Boto3Error()
        result = cloud.classify(error)
        assert result == const.CLOUD

    def test_singleton_classify_unrecognized(self) -> None:
        """The cloud singleton returns None for unrecognized exceptions."""
        error = ValueError("test")
        result = cloud.classify(error)
        assert result is None
