"""Internal builders for @logged aspect wrapper generation (containerized per R004/R009)."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from typing import Optional

LOGGED_MARKER = "__logged_applied__"


class _LoggedBuilders:
    """Container for @logged aspect builder/decorator functions per strict-module R004/R009."""

    @staticmethod
    def build_logged_wrapper(
        target: Callable,
        event: str,
        payload_from_request: Optional[Callable[..., dict]],
        payload_from_result: Optional[Callable[[object], dict]],
        payload_from_exc: Optional[Callable[[BaseException], dict]],
        timed: bool,
    ) -> Callable:
        """Build native wrapper for logging entry/exit/error events.

        Emits via instance's LoggingMixin.log_* if available, else ambient log_* functions.
        Extractions are guarded: errors log WARNING, operation continues.
        When timed=True, measures operation duration via mixin_latency.LatencyClock.
        """
        from mixin_logging import LoggingMixin, log_error, log_info

        if timed:
            from mixin_latency import LatencyClock

        if asyncio.iscoroutinefunction(target):

            @functools.wraps(target)
            async def async_logged(*args: object, **kwargs: object) -> object:
                logger = None
                if args and isinstance(args[0], LoggingMixin):
                    logger = args[0]

                start_payload: dict = {}
                if payload_from_request:
                    try:
                        start_payload = payload_from_request(*args, **kwargs) or {}
                    except Exception as error:
                        log_error(
                            f"Logged: extraction failed for {event}.start",
                            error=str(error),
                        )
                        start_payload = {}

                if logger:
                    logger.log_info(f"{event}.start", **start_payload)
                else:
                    log_info(f"{event}.start", **start_payload)

                clock = LatencyClock.start() if timed else None
                try:
                    result = await target(*args, **kwargs)
                    end_payload: dict = {}
                    if payload_from_result:
                        try:
                            end_payload = payload_from_result(result) or {}
                        except Exception as error:
                            log_error(
                                f"Logged: extraction failed for {event}.end",
                                error=str(error),
                            )
                            end_payload = {}

                    if clock:
                        measurement = clock.stop()
                        end_payload["latency_ms"] = measurement.duration_ms

                    if logger:
                        logger.log_info(f"{event}.end", **end_payload)
                    else:
                        log_info(f"{event}.end", **end_payload)

                    return result
                except BaseException as error:
                    error_payload: dict = {
                        "error_type": type(error).__name__,
                    }
                    if clock:
                        measurement = clock.stop()
                        error_payload["latency_ms"] = measurement.duration_ms

                    if payload_from_exc:
                        try:
                            error_payload.update(payload_from_exc(error) or {})
                        except Exception as extraction_error:
                            log_error(
                                f"Logged: extraction failed for {event}.error",
                                error=str(extraction_error),
                            )

                    if logger:
                        logger.log_error(f"{event}.error", **error_payload)
                    else:
                        log_error(f"{event}.error", **error_payload)

                    raise

            return async_logged

        @functools.wraps(target)
        def sync_logged(*args: object, **kwargs: object) -> object:
            logger = None
            if args and isinstance(args[0], LoggingMixin):
                logger = args[0]

            start_payload: dict = {}
            if payload_from_request:
                try:
                    start_payload = payload_from_request(*args, **kwargs) or {}
                except Exception as error:
                    log_error(
                        f"Logged: extraction failed for {event}.start",
                        error=str(error),
                    )
                    start_payload = {}

            if logger:
                logger.log_info(f"{event}.start", **start_payload)
            else:
                log_info(f"{event}.start", **start_payload)

            clock = LatencyClock.start() if timed else None
            try:
                result = target(*args, **kwargs)
                end_payload: dict = {}
                if payload_from_result:
                    try:
                        end_payload = payload_from_result(result) or {}
                    except Exception as error:
                        log_error(
                            f"Logged: extraction failed for {event}.end",
                            error=str(error),
                        )
                        end_payload = {}

                if clock:
                    measurement = clock.stop()
                    end_payload["latency_ms"] = measurement.duration_ms

                if logger:
                    logger.log_info(f"{event}.end", **end_payload)
                else:
                    log_info(f"{event}.end", **end_payload)

                return result
            except BaseException as error:
                error_payload: dict = {
                    "error_type": type(error).__name__,
                }
                if clock:
                    measurement = clock.stop()
                    error_payload["latency_ms"] = measurement.duration_ms

                if payload_from_exc:
                    try:
                        error_payload.update(payload_from_exc(error) or {})
                    except Exception as extraction_error:
                        log_error(
                            f"Logged: extraction failed for {event}.error",
                            error=str(extraction_error),
                        )

                if logger:
                    logger.log_error(f"{event}.error", **error_payload)
                else:
                    log_error(f"{event}.error", **error_payload)

                raise

        return sync_logged

    @staticmethod
    def decorate_class_logged(
        cls: type[object],
        event: str,
        payload_from_request: Optional[Callable[..., dict]],
        payload_from_result: Optional[Callable[[object], dict]],
        payload_from_exc: Optional[Callable[[BaseException], dict]],
        timed: bool,
    ) -> type[object]:
        """Fan out @logged over all public methods in the class.

        Rules:
        - Only methods in cls.__dict__ (not inherited)
        - Skip: _-prefixed, dunders, properties, nested classes
        - Preserve: classmethod/staticmethod via unwrap/rewrap
        - Override: methods already marked with LOGGED_MARKER are left untouched
        """
        for name, method in list(cls.__dict__.items()):
            if name.startswith("_"):
                continue
            if isinstance(method, property):
                continue
            if isinstance(method, type):
                continue

            is_classmethod = isinstance(method, classmethod)
            is_staticmethod = isinstance(method, staticmethod)

            if is_classmethod or is_staticmethod:
                unwrapped = method.__func__
            else:
                unwrapped = method

            if not callable(unwrapped):
                continue

            if hasattr(unwrapped, LOGGED_MARKER):
                continue

            decorated = _LoggedBuilders.build_logged_wrapper(
                unwrapped,
                event,
                payload_from_request,
                payload_from_result,
                payload_from_exc,
                timed,
            )
            setattr(decorated, LOGGED_MARKER, True)

            if is_classmethod:
                setattr(cls, name, classmethod(decorated))
            elif is_staticmethod:
                setattr(cls, name, staticmethod(decorated))
            else:
                setattr(cls, name, decorated)

        return cls
