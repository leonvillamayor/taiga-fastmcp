"""
Logging decorators for automatic operation logging.

Provides decorators to automatically log function calls, results,
and errors with correlation ID tracing.
"""

import functools
import time
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from src.infrastructure.logging.correlation import CorrelationIdManager
from src.infrastructure.logging.logger import get_logger


P = ParamSpec("P")
R = TypeVar("R")


def _mask_sensitive_args(
    args: tuple[Any, ...], kwargs: dict[str, Any], sensitive_keys: list[str]
) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Mask sensitive arguments for logging."""
    sensitive_lower = [k.lower() for k in sensitive_keys]

    # Mask kwargs
    masked_kwargs = {}
    for k, v in kwargs.items():
        if k.lower() in sensitive_lower:
            masked_kwargs[k] = "***MASKED***"
        else:
            masked_kwargs[k] = v

    return args, masked_kwargs


def log_operation(
    operation_name: str | None = None,
    log_args: bool = True,
    log_result: bool = False,
    log_execution_time: bool = True,
    sensitive_args: list[str] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to log function operations with correlation ID.

    This decorator automatically:
    - Creates/uses correlation ID for tracing
    - Logs operation start, completion, and errors
    - Optionally logs arguments and results
    - Tracks execution time

    Args:
        operation_name: Custom name for the operation. If None, uses function name.
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        log_execution_time: Whether to log execution time
        sensitive_args: List of argument names to mask in logs

    Returns:
        Decorated function

    Example:
        >>> @log_operation(operation_name="create_project")
        ... async def create_project(name: str, auth_token: str):
        ...     # Function implementation
        ...     pass
    """
    sensitive_keys = sensitive_args or ["password", "auth_token", "token", "secret"]

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        logger = get_logger(func.__module__)
        op_name = operation_name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Ensure correlation ID exists
            CorrelationIdManager.ensure_correlation_id()

            # Mask sensitive arguments for logging
            _, masked_kwargs = _mask_sensitive_args(args, kwargs, sensitive_keys)

            # Log operation start
            log_msg = f"[{op_name}] Starting operation"
            if log_args and masked_kwargs:
                # Only log non-sensitive kwargs
                safe_kwargs = {k: v for k, v in masked_kwargs.items() if v != "***MASKED***"}
                if safe_kwargs:
                    log_msg += f" | params={safe_kwargs}"
            logger.info(log_msg)

            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)  # type: ignore[misc]

                # Calculate execution time
                execution_time = time.perf_counter() - start_time

                # Log success
                success_msg = f"[{op_name}] Completed successfully"
                if log_execution_time:
                    success_msg += f" | duration={execution_time:.3f}s"
                if log_result and result is not None:
                    # Truncate large results
                    result_str = str(result)
                    if len(result_str) > 200:
                        result_str = result_str[:200] + "..."
                    success_msg += f" | result={result_str}"
                logger.info(success_msg)

                return result  # type: ignore[no-any-return]

            except Exception as e:
                # Calculate execution time even on error
                execution_time = time.perf_counter() - start_time

                # Log error with full details
                logger.error(
                    f"[{op_name}] Failed | error={type(e).__name__}: {e!s} | duration={execution_time:.3f}s",
                    exc_info=True,
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Ensure correlation ID exists
            CorrelationIdManager.ensure_correlation_id()

            # Mask sensitive arguments for logging
            _, masked_kwargs = _mask_sensitive_args(args, kwargs, sensitive_keys)

            # Log operation start
            log_msg = f"[{op_name}] Starting operation"
            if log_args and masked_kwargs:
                safe_kwargs = {k: v for k, v in masked_kwargs.items() if v != "***MASKED***"}
                if safe_kwargs:
                    log_msg += f" | params={safe_kwargs}"
            logger.info(log_msg)

            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)

                execution_time = time.perf_counter() - start_time

                success_msg = f"[{op_name}] Completed successfully"
                if log_execution_time:
                    success_msg += f" | duration={execution_time:.3f}s"
                if log_result and result is not None:
                    result_str = str(result)
                    if len(result_str) > 200:
                        result_str = result_str[:200] + "..."
                    success_msg += f" | result={result_str}"
                logger.info(success_msg)

                return result

            except Exception as e:
                execution_time = time.perf_counter() - start_time
                logger.error(
                    f"[{op_name}] Failed | error={type(e).__name__}: {e!s} | duration={execution_time:.3f}s",
                    exc_info=True,
                )
                raise

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper

    return decorator


def log_api_call(
    method: str | None = None,
    endpoint: str | None = None,
    log_response: bool = False,
    log_request_body: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator specifically for API calls with HTTP-specific logging.

    This decorator is optimized for logging HTTP API calls and includes:
    - HTTP method and endpoint logging
    - Request/response status tracking
    - Error response logging

    Args:
        method: HTTP method (GET, POST, etc.). If None, extracted from function name.
        endpoint: API endpoint. If None, extracted from arguments.
        log_response: Whether to log response body
        log_request_body: Whether to log request body

    Returns:
        Decorated function

    Example:
        >>> @log_api_call(method="POST", endpoint="/auth")
        ... async def authenticate(username: str, password: str):
        ...     # API call implementation
        ...     pass
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        logger = get_logger("api")
        http_method = method or func.__name__.upper().split("_")[0]

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            CorrelationIdManager.ensure_correlation_id()

            # Try to extract endpoint from kwargs or first string arg
            api_endpoint: str | None = endpoint
            if not api_endpoint:
                endpoint_val = kwargs.get("endpoint") or kwargs.get("path")
                api_endpoint = str(endpoint_val) if endpoint_val else "unknown"
                if api_endpoint == "unknown" and args:
                    for arg in args:
                        if isinstance(arg, str) and arg.startswith("/"):
                            api_endpoint = arg
                            break

            # Log request start
            log_msg = f"[API] {http_method} {api_endpoint}"
            if log_request_body:
                body = kwargs.get("json", kwargs.get("data", kwargs.get("body")))
                if body and isinstance(body, dict):
                    # Mask sensitive data in body
                    safe_body = {
                        k: "***" if k.lower() in ["password", "token", "secret"] else v
                        for k, v in body.items()
                    }
                    log_msg += f" | body={safe_body}"
            logger.debug(log_msg)

            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)  # type: ignore[misc]
                execution_time = time.perf_counter() - start_time

                # Log success
                status = "200 OK"  # Default success status
                if isinstance(result, dict):
                    status = f"200 OK (items: {len(result)})"
                elif isinstance(result, list):
                    status = f"200 OK ({len(result)} items)"

                success_msg = f"[API] {http_method} {api_endpoint} | status={status} | duration={execution_time:.3f}s"
                logger.info(success_msg)

                if log_response and result:
                    result_str = str(result)
                    if len(result_str) > 500:
                        result_str = result_str[:500] + "..."
                    logger.debug(f"[API] Response: {result_str}")

                return result  # type: ignore[no-any-return]

            except Exception as e:
                execution_time = time.perf_counter() - start_time

                # Try to extract status code from exception
                status_code = getattr(e, "status_code", getattr(e, "code", "error"))
                logger.error(
                    f"[API] {http_method} {api_endpoint} | status={status_code} | "
                    f"error={type(e).__name__}: {e!s} | duration={execution_time:.3f}s"
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            CorrelationIdManager.ensure_correlation_id()
            endpoint_val = kwargs.get("endpoint") or kwargs.get("path")
            api_endpoint = endpoint or (str(endpoint_val) if endpoint_val else "unknown")

            logger.debug(f"[API] {http_method} {api_endpoint}")

            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time
                logger.info(
                    f"[API] {http_method} {api_endpoint} | status=200 OK | duration={execution_time:.3f}s"
                )
                return result

            except Exception as e:
                execution_time = time.perf_counter() - start_time
                status_code = getattr(e, "status_code", getattr(e, "code", "error"))
                logger.error(
                    f"[API] {http_method} {api_endpoint} | status={status_code} | "
                    f"error={type(e).__name__}: {e!s} | duration={execution_time:.3f}s"
                )
                raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper

    return decorator


class LogContext:
    """
    Context manager for adding extra context to logs within a scope.

    Example:
        >>> with LogContext(user_id=123, project_id=456):
        ...     logger.info("Processing request")  # Will include user_id and project_id
    """

    def __init__(self, **context: Any) -> None:
        """Initialize with context key-value pairs."""
        self.context = context
        self._old_factory: Any = None

    def __enter__(self) -> "LogContext":
        """Enter context and set up log record factory."""
        import logging

        old_factory = logging.getLogRecordFactory()
        self._old_factory = old_factory
        context = self.context

        def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
            record = old_factory(*args, **kwargs)
            record.extra_data = context
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context and restore original factory."""
        import logging

        if self._old_factory:
            logging.setLogRecordFactory(self._old_factory)
