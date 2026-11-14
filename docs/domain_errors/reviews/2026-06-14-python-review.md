# Python Classifier Review

**Date:** 2026-06-14  
**Feature:** python (domains/python)  
**Scope:** Stdlib exception-family classification, tuple-based family ordering, isinstance handling

## Findings

### Classification Correctness

**Sound.** PythonClassifier uses a tuple-of-tuples, _FAMILIES, where each pair maps exception types -> domain string. The classify() method iterates _FAMILIES in order and returns the domain of the first matching type via isinstance(). This approach is correct for stdlib exceptions because some families have subtype relationships: ConnectionError and TimeoutError are both subclasses of OSError. Ordering them **BEFORE** OSError in the tuple ensures they match first. Reversing the order would cause ConnectionError to match OSError first, collapsing them into the OS domain: a correctness failure. The tuple structure correctly encodes that order is load-bearing.

### Frozenset vs. Tuple Rationale

**Correct choice.** The _FAMILIES tuple is NOT a frozenset, and it must not be. A frozenset would eliminate ordering entirely, breaking the classification for subtypes. The exception hierarchy requires specificity-first matching: NETWORK (ConnectionError, TimeoutError) before OS (their parent class). Standard Python libraries have this containment by design (network timeouts are OS-level but semantically distinct), and the classifier respects it.

### Docstrings and Naming

**Standards compliant.** The class has a one-line docstring ("Classify stdlib exceptions into coarse domains."), the classify method has a one-line docstring ("Return err's stdlib domain, or None when no family matches."), and the module docstring is one-line ("Stdlib exception-family domain classifier."). The _FAMILIES constant is self-documenting; no inline comments are needed.

### Constants

**Standards compliant.** Constants are imported as `from domain_errors.domains.constants import python as const`, and all domain strings (NETWORK, OS, LOGIC, ASSERTION) are correctly scoped to the constant module. No string literals in the classifier itself.

### Imports

**Standards compliant.** Combined-absolute imports per ruff TID252; no relative imports or from-future annotations except the standard `from __future__ import annotations` at the top.

### Singleton Export

**Correct.** The module exports `python = PythonClassifier()` at the bottom, providing a stateless singleton instance for module-level use. Tests verify this works.

### Test Coverage

**Complete: 100%.** Tests cover all four families (NETWORK, OS, LOGIC, ASSERTION), all unrecognized exceptions (RuntimeError, Exception, custom), singleton instantiation, and stateless behavior (repeated calls return the same result). Test organization uses descriptive class names (TestPythonClassifierNetworkFamily, etc.) and clear test names (test_connection_error_maps_to_network, etc.).

### Residual Observations

- The isinstance check against a tuple of tuples is idiomatic; list(zip(types, domain)) would be clearer only if domains varied, but they do not.
- Frozen+slots is not applicable here; PythonClassifier is stateless and has no attributes.
- No type: ignore comments or mypy suppressions are needed; the code is fully typed.

## Verdict

Python classifier is correct, standards-conformant, and ready. Exception family ordering is sound; tuple-based handling is the right choice; test coverage is complete. No defects or divergences.
