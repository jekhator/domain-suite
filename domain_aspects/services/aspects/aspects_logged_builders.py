"""Internal builders for @logged aspect wrapper generation (containerized per R004/R009)."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING

from domain_aspects.services.aspects.aspects_class_fanout import ClassFanout
from domain_aspects.services.constants import aspects as const

if TYPE_CHECKING:
    from mixin_logging import LoggingMixin


class _LoggedEmitter:
    """Route logged events to the instance logger when present, else to the ambient functions."""

    def __init__(
        self,
        logging_mixin: type[LoggingMixin],
        log_info: Callable[..., object],
        log_error: Callable[..., object],
    ) -> None:
        """Store the mixin class and the ambient logging functions."""
        self._logging_mixin = logging_mixin
        self._log_info = log_info
        self._log_error = log_error

    def logger_for(self, args: tuple[object, ...]) -> LoggingMixin | None:
        """Return the first positional argument when it is a LoggingMixin instance."""
        if args and isinstance(args[0], self._logging_mixin):
            return args[0]
        return None

    def payload(
        self,
        extractor: Callable[..., Mapping[str, object] | None] | None,
        label: str,
        /,
        *values: object,
        **kwargs: object,
    ) -> dict[str, object]:
        """Run a payload extractor; a failing extractor is logged and yields an empty payload."""
        if extractor is None:
            return {}
        try:
            return dict(extractor(*values, **kwargs) or {})
        except Exception as error:
            self._log_error(f"Logged: extraction failed for {label}", error=str(error))
            return {}

    def info(
        self,
        logger: LoggingMixin | None,
        name: str,
        payload: Mapping[str, object],
    ) -> None:
        """Emit an info event through the logger or the ambient function."""
        if logger is not None:
            logger.log_info(name, **payload)
        else:
            self._log_info(name, **payload)

    def error(
        self,
        logger: LoggingMixin | None,
        name: str,
        payload: Mapping[str, object],
    ) -> None:
        """Emit an error event through the logger or the ambient function."""
        if logger is not None:
            logger.log_error(name, **payload)
        else:
            self._log_error(name, **payload)


class _LoggedBuilders:
    """Container for @logged aspect builder/decorator functions per strict-module R004/R009."""

    @staticmethod
    def build_logged_wrapper(
        target: Callable,
        event: str,
        payload_from_request: Callable[..., Mapping[str, object] | None] | None,
        payload_from_result: Callable[[object], Mapping[str, object] | None] | None,
        payload_from_exc: Callable[[BaseException], Mapping[str, object] | None] | None,
        timed: bool,
    ) -> Callable:
        """Build native wrapper for logging entry/exit/error events.

        Emits via instance's LoggingMixin.log_* if available, else ambient log_* functions.
        Extractions are guarded: errors log WARNING, operation continues.
        When timed=True, measures operation duration via mixin_latency.LatencyClock.
        """
        try:
            from mixin_logging import LoggingMixin, log_error, log_info
        except ImportError as error:
            raise ImportError(const.ERR_ASPECT_LOGGED_IMPORT_MISSING) from error

        if timed:
            from mixin_latency import LatencyClock

        emitter = _LoggedEmitter(LoggingMixin, log_info, log_error)
        start_name = f"{event}.start"
        end_name = f"{event}.end"
        error_name = f"{event}.error"

        if asyncio.iscoroutinefunction(target):

            @functools.wraps(target)
            async def async_logged(*args: object, **kwargs: object) -> object:
                logger = emitter.logger_for(args)
                start_payload = emitter.payload(
                    payload_from_request, start_name, *args, **kwargs
                )
                emitter.info(logger, start_name, start_payload)

                clock = LatencyClock.start() if timed else None
                try:
                    result = await target(*args, **kwargs)
                except BaseException as error:
                    error_payload: dict[str, object] = {
                        "error_type": type(error).__name__,
                    }
                    if clock is not None:
                        error_payload["latency_ms"] = clock.stop().duration_ms
                    error_payload.update(
                        emitter.payload(payload_from_exc, error_name, error)
                    )
                    emitter.error(logger, error_name, error_payload)
                    raise

                end_payload = emitter.payload(payload_from_result, end_name, result)
                if clock is not None:
                    end_payload["latency_ms"] = clock.stop().duration_ms
                emitter.info(logger, end_name, end_payload)
                return result

            return async_logged

        @functools.wraps(target)
        def sync_logged(*args: object, **kwargs: object) -> object:
            logger = emitter.logger_for(args)
            start_payload = emitter.payload(
                payload_from_request, start_name, *args, **kwargs
            )
            emitter.info(logger, start_name, start_payload)

            clock = LatencyClock.start() if timed else None
            try:
                result = target(*args, **kwargs)
            except BaseException as error:
                error_payload: dict[str, object] = {
                    "error_type": type(error).__name__,
                }
                if clock is not None:
                    error_payload["latency_ms"] = clock.stop().duration_ms
                error_payload.update(
                    emitter.payload(payload_from_exc, error_name, error)
                )
                emitter.error(logger, error_name, error_payload)
                raise

            end_payload = emitter.payload(payload_from_result, end_name, result)
            if clock is not None:
                end_payload["latency_ms"] = clock.stop().duration_ms
            emitter.info(logger, end_name, end_payload)
            return result

        return sync_logged

    @staticmethod
    def decorate_class_logged(
        target_class: type,
        event: str,
        payload_from_request: Callable[..., Mapping[str, object] | None] | None,
        payload_from_result: Callable[[object], Mapping[str, object] | None] | None,
        payload_from_exc: Callable[[BaseException], Mapping[str, object] | None] | None,
        timed: bool,
    ) -> type:
        """Fan out @logged over all public methods in the class.

        Rules:
        - Only methods in the class dict (not inherited)
        - Skip: _-prefixed, dunders, properties, nested classes
        - Preserve: classmethod/staticmethod via unwrap/rewrap
        - Override: methods already marked with LOGGED_APPLIED_MARKER are left untouched
        """

        def decorate(method: Callable[..., object]) -> Callable[..., object]:
            wrapped = _LoggedBuilders.build_logged_wrapper(
                method,
                event,
                payload_from_request,
                payload_from_result,
                payload_from_exc,
                timed,
            )
            setattr(wrapped, const.LOGGED_APPLIED_MARKER, True)
            return wrapped

        return ClassFanout.decorate_class(
            target_class, const.LOGGED_APPLIED_MARKER, decorate
        )
