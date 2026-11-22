# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-07-06

### Added

- **@wrap_errors class-level decoration:** Decorator can now be applied to classes. Fans out over all public callables in `cls.__dict__`, preserving sync/async dispatch per method. Skips private methods, dunder methods, properties, nested classes, and already-decorated methods. Unwraps and rewraps classmethod/staticmethod to preserve semantics. Config (catch, as_, message, capture) applies uniformly to all fanned methods.

## [0.1.0] - 2026-06-15

### Added

- **DomainError base class:** Typed exception hierarchy with class contract (code, domain, http_status, retryable, default_message).
- **Instance state:** message (string) and context (dict) for structured logging.
- **ErrorChain service:** Static methods for wrapping, walking, and analyzing exception chains.
  - `wrap(err, as_=ErrorType, message=None, **context)`: construct typed domain errors.
  - `history(err, classifiers=())`: walk exception cascade into ChainLink objects.
  - `crossings(err, classifiers=())`: identify domain boundary crossings.
- **ChainLink value object:** Structured representation of one exception chain hop, with `to_log_extra()` for JSON-ready logging.
- **DomainCrossing value object:** Causation hop where errors cross domain boundaries, with `to_log_extra()` for logging.
- **ChainVia enum:** Tags for how a link entered the chain (ROOT, CAUSE, CONTEXT).
- **DomainClassifier protocol:** Contract for resolving domains of foreign (non-DomainError) exceptions.
- **Python stdlib domain classifier:** Built-in `python` classifier for mapping stdlib exception families (network, OS, logic, assertion) to domain strings.
- **HTTP-client domain classifier:** Built-in `http` classifier for mapping httpx, requests, and aiohttp exceptions to the http domain. By-origin design (type(err).__module__) catches the entire library surface including exceptions outside main error trees; no runtime dependency on the libraries.
- **AWS cloud domain classifier:** Built-in `cloud` classifier for mapping botocore and boto3 exceptions to the cloud domain. By-origin design (type(err).__module__) catches the entire AWS SDK surface; no runtime dependency on the libraries.
- **@wrap_errors decorator:** Declarative error wrapping for functions and async callables. Catches specified exceptions, wraps them into a target DomainError via ErrorChain.wrap(), and preserves causation via raise-from. Captures function arguments into error context for structured logging (disable via capture=False). DomainError instances pass through unchanged. Works on both sync and async functions.
- **Logging payload DTOs:** LinkLogExtra and CrossingLogExtra for structured audit trails.
