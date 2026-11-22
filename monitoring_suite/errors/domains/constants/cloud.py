"""Cloud classifier domain name and recognized libraries. Imported as const."""

from __future__ import annotations

from typing import Final

__all__ = [
    "CLOUD",
    "CLOUD_LIBRARIES",
]


"""Cloud-layer domain the classifier maps AWS-SDK (botocore/boto3) errors to."""

CLOUD: Final = "cloud"


"""Top-level package names of the AWS-SDK libraries classified by origin."""

CLOUD_LIBRARIES: Final = frozenset({"botocore", "boto3"})
