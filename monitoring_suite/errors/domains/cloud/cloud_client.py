"""AWS cloud-SDK exception-family domain classifier."""

from __future__ import annotations

from monitoring_suite.errors.domains.constants import cloud as const


class CloudClassifier:
    """Classify botocore and boto3 exceptions into the cloud domain."""

    def classify(self, err: BaseException) -> str | None:
        """Return const.CLOUD when err originates in an AWS-SDK library, else None."""
        if type(err).__module__.split(".")[0] in const.CLOUD_LIBRARIES:
            return const.CLOUD
        return None


cloud = CloudClassifier()
