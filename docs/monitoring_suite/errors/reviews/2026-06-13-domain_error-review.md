# DomainError Review

**Date:** 2026-06-13  
**Feature:** domain_error (domains/domain_error)  
**Scope:** Base class for typed exception hierarchies, classvar defaults, message/context storage, Exception subclassing design

## Findings

### Classvar Contract and Defaults

**Correctness: sound.**

DomainError declares six classvars (code, domain, http_status, default_message, retryable) with sensible const-sourced defaults from domains/constants/domain_error.py. Subclasses override these classvars to define their specific behavior. The contract is clear: each error type declares what it means (code, domain), how it maps to HTTP (http_status), what to say if no message is provided (default_message), and whether retries are safe (retryable). This is the canonical typed-error pattern.

### Message and Context Storage

**Correctness: sound.**

The __init__ method (line 18-22) stores the message (using default_message if not provided) and unpacks context kwargs into a context dict. Both are stored as instance attributes, not passed to super().__init__(context). This is intentional: Exception's args tuple is for str() output (line 22 passes self.message to super().__init__), and context lives separately for structured logging. Callers can then extract context via getattr(err, "context", {}) (as ErrorChain does) or pass it directly to logger.extra.

### Unslotted Exception Design

**Design decision: acceptable.**

DomainError does not declare __slots__. Exception is a built-in with a complex C implementation; Python docs recommend caution with slotting built-ins. The design choice to leave Exception unslotted (and thus DomainError unslotted) is reasonable: it avoids potential pitfalls with exception pickling, tracebacks, and sys.exc_info(). Value objects in the chain service (ChainLink, DomainCrossing) are slotted because they are pure data; DomainError is a lifecycle object (raised, caught, mutated by traceback machinery) and benefits from flexibility.

### Subclassing Model

**Correctness: clean.**

Subclasses of DomainError can set additional classvars and instance attributes without ceremony. The pattern is: subclass -> set code/domain/http_status/default_message/retryable classvars -> override __init__ only if you need to parse or transform the message. This is forward-compatible: if a subclass needs to add a new classvar (e.g., help_url), it just declares it and tests it.

### Constants Module

**Standards: conformant.**

The constants module (domains/constants/domain_error.py) is correctly partitioned with a module docstring, __all__ export, and one-line docstring partitions above each Final. No RST markup.

### Docstrings

**Standards: conformant.**

Class docstring and method docstring are one-line, plain prose, and accurate.

### Residual Observations

- No inline # comments.
- The default HTTP status of 500 is prudent: subclasses that are client-facing (validation, not-found) override to 4xx.
- The base retryable=False is correct: only idempotent errors (timeout, transient service) should override to True; the default is safe.

## Verdict

DomainError is correct, standards-conformant, and ready. The classvar contract is clear and extensible; message/context storage is sound; the Exception subclassing design is reasonable. No defects or divergences.
