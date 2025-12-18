"""Structured logging middleware for Taiga MCP Server.

This middleware provides structured logging for all MCP requests
with correlation IDs and context information.
"""

import time
import uuid
from typing import Any

from fastmcp.server.middleware import Middleware

from src.infrastructure.logging import CorrelationIdManager, LogContext, get_logger


logger = get_logger("middleware.logging")


class StructuredLoggingMiddleware(Middleware):
    """Middleware for structured request logging.

    Logs all requests with structured data including timing,
    correlation IDs, and request/response details.

    Attributes:
        log_request_body: Whether to log request parameters.
        log_response_body: Whether to log response data.
        sensitive_fields: Fields to mask in logs.
    """

    def __init__(
        self,
        log_request_body: bool = True,
        log_response_body: bool = False,
        sensitive_fields: list[str] | None = None,
        include_correlation_id: bool = True,
    ) -> None:
        """Initialize logging middleware.

        Args:
            log_request_body: Whether to log request parameters.
            log_response_body: Whether to log response data.
            sensitive_fields: Fields to mask in logs.
            include_correlation_id: Whether to generate correlation IDs.
        """
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.sensitive_fields = sensitive_fields or [
            "auth_token",
            "password",
            "token",
            "secret",
            "api_key",
            "authorization",
        ]
        self.include_correlation_id = include_correlation_id

    async def on_call_tool(
        self,
        context: Any,
        call_next: Any,
    ) -> Any:
        """Handle tool calls with structured logging.

        Args:
            context: The middleware context.
            call_next: Function to call the next middleware.

        Returns:
            The result from the tool.
        """
        # Generate correlation ID
        if self.include_correlation_id:
            correlation_id = str(uuid.uuid4())[:8]
            CorrelationIdManager.set_correlation_id(correlation_id)
        else:
            correlation_id = CorrelationIdManager.get_correlation_id() or "none"

        # Extract tool info
        tool_name = "unknown"
        params = getattr(context.request, "params", None)
        if params and hasattr(params, "name"):
            tool_name = params.name

        # Get arguments (masked)
        arguments = {}
        if self.log_request_body and params and hasattr(params, "arguments"):
            arguments = self._mask_sensitive(params.arguments or {})

        start_time = time.perf_counter()
        error_occurred = False
        error_message = ""

        with LogContext(
            correlation_id=correlation_id,
            tool_name=tool_name,
        ):
            logger.info(
                f"Tool call started: {tool_name}",
                extra={
                    "event": "tool_call_start",
                    "tool_name": tool_name,
                    "correlation_id": correlation_id,
                    "arguments": arguments if self.log_request_body else {},
                },
            )

            try:
                result = await call_next(context)

                if self.log_response_body:
                    logger.debug(
                        f"Tool response: {tool_name}",
                        extra={
                            "event": "tool_call_response",
                            "tool_name": tool_name,
                            "response": self._mask_sensitive(result) if result else None,
                        },
                    )

                return result

            except Exception as e:
                error_occurred = True
                error_message = str(e)
                logger.error(
                    f"Tool call failed: {tool_name} - {e}",
                    extra={
                        "event": "tool_call_error",
                        "tool_name": tool_name,
                        "correlation_id": correlation_id,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    },
                )
                raise

            finally:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000

                logger.info(
                    f"Tool call completed: {tool_name} ({duration_ms:.2f}ms)",
                    extra={
                        "event": "tool_call_end",
                        "tool_name": tool_name,
                        "correlation_id": correlation_id,
                        "duration_ms": duration_ms,
                        "success": not error_occurred,
                        "error_message": error_message if error_occurred else None,
                    },
                )

    async def on_list_tools(
        self,
        context: Any,
        call_next: Any,
    ) -> Any:
        """Log list tools requests.

        Args:
            context: The middleware context.
            call_next: Function to call the next middleware.

        Returns:
            The list of tools.
        """
        logger.debug("Listing available tools")
        result = await call_next(context)
        if result:
            logger.debug(f"Listed {len(result)} tools")
        return result

    async def on_read_resource(
        self,
        context: Any,
        call_next: Any,
    ) -> Any:
        """Log resource read requests.

        Args:
            context: The middleware context.
            call_next: Function to call the next middleware.

        Returns:
            The resource contents.
        """
        params = getattr(context.request, "params", None)
        uri = getattr(params, "uri", "unknown") if params else "unknown"

        logger.info(
            f"Reading resource: {uri}",
            extra={"event": "resource_read", "uri": str(uri)},
        )

        return await call_next(context)

    async def on_get_prompt(
        self,
        context: Any,
        call_next: Any,
    ) -> Any:
        """Log prompt requests.

        Args:
            context: The middleware context.
            call_next: Function to call the next middleware.

        Returns:
            The prompt result.
        """
        params = getattr(context.request, "params", None)
        prompt_name = getattr(params, "name", "unknown") if params else "unknown"

        logger.info(
            f"Getting prompt: {prompt_name}",
            extra={"event": "prompt_get", "prompt_name": prompt_name},
        )

        return await call_next(context)

    def _mask_sensitive(self, data: Any) -> Any:
        """Mask sensitive fields in data.

        Args:
            data: Data to mask.

        Returns:
            Data with sensitive fields masked.
        """
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                key_lower = key.lower()
                if any(field in key_lower for field in self.sensitive_fields):
                    masked[key] = "***MASKED***"
                else:
                    masked[key] = self._mask_sensitive(value)
            return masked
        if isinstance(data, list):
            return [self._mask_sensitive(item) for item in data]
        return data
