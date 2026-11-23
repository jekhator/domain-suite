"""Cloud classifier domain name and recognized libraries. Imported as const."""

from __future__ import annotations

from typing import Final

__all__ = ["CLOUD", "CLOUD_LIBRARIES", "MODULE_SEPARATOR"]


"""Cloud-layer domain the classifier maps AWS-SDK (botocore/boto3) errors to."""

CLOUD: Final[str] = "cloud"


"""Top-level package names of the AWS-SDK libraries classified by origin."""

CLOUD_LIBRARIES: Final[frozenset[str]] = frozenset({"botocore", "boto3"})


"""Separators and format pieces."""

MODULE_SEPARATOR: Final[str] = "."
