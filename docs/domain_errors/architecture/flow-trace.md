# domain_errors: Flow-Trace

## Overview

Domain error classification and wrapping for typed exception hierarchies. The `DomainError` base class establishes contract-based error metadata; `@wrap_errors` catches foreign exceptions and translates them into domain-specific errors. ErrorChain tracks causation and domain crossings.

## Entry Unit

`DomainError` [FROZEN,slots] base class + `wrap_errors(as_=TargetError)` decorator.

## Flow-Trace Diagram

```
1. CONSTRUCT DomainError Subclass
   class ValidationError(DomainError)  <- [FROZEN,slots], inherits base
      code: str = "validation_failed"
      domain: str = "validation"
      http_status: int = 422
      default_message: str = "Validation failed."
      retryable: bool = False

2. DECORATE @wrap_errors
   @wrap_errors(as_=ValidationError)  --> WrapErrorsClient(as_=ValidationError, catch=(Exception,), message=None, capture=True)
      |- callable (function or async) --> _decorate_callable(func)
      |  |- inspect.iscoroutinefunction(func)?
      |  |  |- YES --> async_wrapper <- preserves async/await
      |  |  `- NO  --> sync wrapper
      |  `- setattr(wrapper, "__wrap_errors_applied__", True)
      |- _decorate_class(cls) [class-level fan-out]
      |  |- iterate cls.__dict__ (public methods only, skip _-prefixed)
      |  |- preserve classmethod/staticmethod via unwrap/rewrap
      |  `- skip if already marked with __wrap_errors_applied__
      `- returns wrapped callable or cls

3. RUNTIME Call --> wrapper(*args, **kwargs)
      |- try:  return func(*args, **kwargs)  <- happy path
      |- except DomainError as e:  raise  <- pass-through (never-swallow)
      `- except (Exception, ...) as e  [matched by catch tuple]
         |- _as_domain(e, func, args, kwargs)  <- classify + wrap
         |  |- _capture(func, args, kwargs)  <- bind call args to names (capture=True)
         |  |  `- returns {param_name: value, ...} | {} if capture=False
         |  `- ErrorChain.wrap(e, as_=ValidationError, message=None, **context)
         |     `- return as_(message=message, **context)  <- instantiate target DomainError
         `- raise ValidationError(...) from e  <- preserve causation

4. ERROR CHAIN (on raise, or later inspection)
   ErrorChain.history(err, classifiers=())  <- walk __cause__ and __context__
      `- returns tuple[ChainLink, ...]
         |- [0] ValidationError (domain="validation", via=ChainVia.ROOT)
         `- [1] ValueError (domain="python", via=ChainVia.CAUSE)  <- resolved via DomainClassifier

REAL OUTPUT:
   CAUGHT ValidationError: ValidationError
     message: Validation failed.
     domain: validation
     http_status: 422
     retryable: False
     chain links: 2
       [0] ValidationError (domain=validation, via=root)
       [1] ValueError (domain=python, via=cause)
```

## Key Constants

- `DEFAULT_CODE` = "domain_error"
- `DEFAULT_DOMAIN` = "application"
- `DEFAULT_HTTP_STATUS` = 500
- `DEFAULT_MESSAGE` = "An unspecified domain error occurred."
- `ChainVia.ROOT` / `ChainVia.CAUSE` / `ChainVia.CONTEXT` <- exception causation enum
- `WRAP_ERRORS_MARKER` = "__wrap_errors_applied__" <- skip marker on decorated

## Core Classes

- `DomainError` <- frozen slots; code, domain, http_status, default_message, retryable, message (init), context (init)
- `WrapErrorsClient(as_, catch, message, capture)` <- frozen slots; __call__, _decorate_callable, _decorate_class, _as_domain, _capture
- `ErrorChain` <- stateless; wrap(), history(), crossings(), _domain_of()
- `ChainLink` <- frozen slots; type_name, message, code, domain, via, context
- `ChainVia` <- StrEnum: ROOT, CAUSE, CONTEXT
- `DomainClassifier` <- Protocol; classify(err) -> str | None
