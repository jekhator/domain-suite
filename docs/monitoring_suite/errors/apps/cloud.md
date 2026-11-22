# monitoring_suite.errors. AWS Cloud Classifier

> **Location:** `monitoring_suite/errors/docs/apps/cloud.md`
> **Status:** Living reference. Cloud classifier fully implemented in v0.1.0+.
> **Code location:** `monitoring_suite/errors/domains/cloud/cloud_client.py`
> **Constants:** `monitoring_suite/errors/domains/constants/cloud.py`
> **Sibling docs:** `docs/apps/domain_error.md`, `docs/apps/chain.md`, `docs/apps/diagrams.md`

## Purpose

`CloudClassifier` maps AWS SDK exception families to a coarse semantic domain. It adapts foreign (non-DomainError) exceptions from botocore and boto3 so they can be classified alongside domain-specific errors in exception chains, enabling unified tracing when cloud infrastructure exceptions cross domain boundaries (e.g., an S3 client error in the storage layer propagates to an application layer).

## Core Design

The classifier is **stateless** and **composable**. It satisfies the `DomainClassifier` protocol: given a caught exception, it returns the exception's domain string or None.

```python
class DomainClassifier(Protocol):
    def classify(self, err: BaseException) -> str | None:
        """Return the error's domain, or None when it is not this family."""
```

## The CloudClassifier Class

### Instance

```python
from monitoring_suite.errors.domains.cloud import cloud

cloud: CloudClassifier = CloudClassifier()
```

The module exports a singleton `cloud` instance; there is no need to instantiate CloudClassifier yourself.

### By-Origin Design

The classifier identifies exceptions by their **origin module**, not by base class. This strategy covers each AWS SDK library's entire exception surface, including exceptions that sit outside the main error hierarchy.

By checking `type(err).__module__`, the classifier captures all AWS SDK exceptions from both botocore and boto3, regardless of their position in the exception class tree.

```python
CLOUD_LIBRARIES: frozenset = {"botocore", "boto3"}
```

The classifier maintains a frozenset of top-level package names for the recognized AWS SDK libraries.

### No Runtime Dependency

The classifier imports **none** of the AWS SDK libraries. It inspects exception objects by name only (checking the module path string). This means:

- No optional-dependency machinery needed; both libraries (botocore, boto3) are dev-only for tests.
- The classifier is robust to library version changes and alternative AWS clients.

## The classify() Method

```python
def classify(self, err: BaseException) -> str | None:
    """Return err's cloud domain, or None when no library match."""
```

### Parameters

- `err`: any caught exception

### Returns

The domain string `"cloud"` if the exception originated in one of the recognized AWS SDK libraries (botocore, boto3), or `None` if the exception's module is not recognized.

### Behavior

Extracts the top-level package name from `type(err).__module__` (the first element when split on `.`). If that package is in `CLOUD_LIBRARIES`, returns `const.CLOUD`. Otherwise, returns `None`.

When returned from `ErrorChain.history()` or `ErrorChain.crossings()`, a `None` result falls back to the fallback domain `"application"`.

### Example

```python
from monitoring_suite.errors.domains.cloud import cloud
import botocore.exceptions

# Matches botocore exception -> "cloud"
result = cloud.classify(botocore.exceptions.ClientError({"Error": {"Code": "NoSuchBucket"}}, "GetObject"))
assert result == "cloud"

# Matches boto3 exception -> "cloud"
import boto3
try:
    s3 = boto3.client("s3")
except Exception as e:
    result = cloud.classify(e)
    assert result == "cloud"

# No match
result = cloud.classify(ValueError("Invalid input"))
assert result is None
```

## Usage with ErrorChain

Pass the `cloud` classifier to `history()` or `crossings()` to resolve domains for AWS SDK exceptions in the exception chain:

```python
from monitoring_suite.errors import ErrorChain, DomainError
from monitoring_suite.errors.domains.cloud import cloud
import boto3

class StorageError(DomainError):
    code = "storage_error"
    domain = "storage"
    http_status = 503

try:
    s3 = boto3.client("s3")
    s3.get_object(Bucket="my-bucket", Key="data.json")
except Exception as e:
    storage_error = ErrorChain.wrap(
        e,
        as_=StorageError,
        message="Failed to retrieve object from S3"
    )
    
    # Walk the chain and classify foreign exceptions
    links = ErrorChain.history(storage_error, classifiers=(cloud,))
    for link in links:
        print(f"{link.type_name} ({link.domain}): {link.message}")
        # Output:
        # StorageError (storage): Failed to retrieve object from S3
        # ClientError (cloud): An error occurred
    
    raise storage_error from e
```

## Composing Multiple Classifiers

Classifiers compose; pass multiple to the same call. The first classifier whose verdict is not `None` wins:

```python
from monitoring_suite.errors import ErrorChain
from monitoring_suite.errors.domains.python import python
from monitoring_suite.errors.domains.http import http
from monitoring_suite.errors.domains.cloud import cloud

try:
    result = await process_with_aws()
except Exception as e:
    # Try python first, then http, then cloud, then other classifiers
    links = ErrorChain.history(e, classifiers=(python, http, cloud))
    for link in links:
        logger.error("Exception", extra=link.to_log_extra())
```

## Design Notes

- **Singleton export:** Instantiate once per module as `cloud = CloudClassifier()`. Stateless, safe to share.
- **By-origin not by-base-class:** Inspects `type(err).__module__` to catch the entire AWS SDK surface, not just the main exception tree.
- **No runtime imports:** Both botocore and boto3 are development dependencies for testing; they are never imported by the classifier itself.
- **None means not recognized:** If `classify()` returns `None`, `ErrorChain._domain_of()` falls back to the sentinel domain `"application"`.
- **No exceptions raised:** The classifier never raises; all return paths are valid.

## See Also

- **ErrorChain:** `docs/apps/chain.md`: how to use classifiers with history/crossings
- **DomainError Base:** `docs/apps/domain_error.md`: how to define domain-specific errors
- **Architecture:** `docs/apps/diagrams.md`: system diagram with classifier placement
