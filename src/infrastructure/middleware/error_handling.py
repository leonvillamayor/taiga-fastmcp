"""Error handling middleware for Taiga MCP Server.

This middleware provides centralized error handling with retry logic
and proper error responses for the MCP server.
"""

import asyncio
from typing import Any

from fastmcp.server.middleware import Middleware

from src.domain.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
    ResourceNotFoundError,
    TaigaAPIError,
    ValidationError,
)
from src.infrastructure.logging import get_logger


logger = get_logger("middleware.error_handling")


class ErrorHandlingMiddleware(Middleware):
    """Middleware for centralized error handling.

    Catches exceptions and converts them to appropriate MCP error responses.
    Supports retry logic for transient failures.

    Attributes:
        max_retries: Maximum number of retry attempts for transient errors.
        retry_delay: Base delay between retries in seconds.
        mask_details: Whether to mask detailed error info in production.
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        mask_details: bool = True,
    ) -> None:
        """Initialize error handling middleware.

        Args:
            max_retries: Maximum retry attempts for transient errors.
            retry_delay: Base delay between retries in seconds.
            mask_details: Whether to mask stack traces in error responses.
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.mask_details = mask_details
        self._error_counts: dict[str, int] = {}

    async def on_call_tool(
        self,
        context: Any,
        call_next: Any,
    ) -> Any:
        """Handle tool calls with error handling and retry logic.

        Args:
            context: The middleware context.
            call_next: Function to call the next middleware.

        Returns:
            The result from the tool or an error response.
        """
        tool_name = getattr(context.request, "params", {})
        tool_name = tool_name.name if hasattr(tool_name, "name") else str(tool_name)

        last_error: Exception | None = None
        retry_count = 0

        while retry_count <= self.max_retries:
            try:
                result = await call_next(context)
                # Reset error count on success
                self._error_counts[tool_name] = 0
                return result

            except RateLimitError as e:
                # Rate limit errors should be retried with exponential backoff
                retry_count += 1
                last_error = e
                if retry_count <= self.max_retries:
                    delay = self.retry_delay * (2 ** (retry_count - 1))
                    logger.warning(
                        f"Rate limited on {tool_name}, retry {retry_count}/{self.max_retries} "
                        f"after {delay}s"
                    )
                    await asyncio.sleep(delay)
                continue

            except TaigaAPIError as e:
                # API errors may be transient, retry a few times
                if self._is_transient_error(e) and retry_count < self.max_retries:
                    retry_count += 1
                    last_error = e
                    delay = self.retry_delay * retry_count
                    logger.warning(
                        f"Transient API error on {tool_name}, retry {retry_count}/{self.max_retries}"
                    )
                    await asyncio.sleep(delay)
                    continue
                # Non-transient API errors are raised immediately
                self._track_error(tool_name, e)
                raise

            except (
                AuthenticationError,
                PermissionDeniedError,
                ResourceNotFoundError,
                ValidationError,
            ) as e:
                # These errors should not be retried
                self._track_error(tool_name, e)
                raise

            except Exception as e:
                # Unknown errors, log and re-raise
                self._track_error(tool_name, e)
                logger.exception(f"Unexpected error in {tool_name}: {e}")
                raise

        # All retries exhausted
        if last_error:
            self._track_error(tool_name, last_error)
            raise last_error

        # Should not reach here
        return await call_next(context)

    def _is_transient_error(self, error: TaigaAPIError) -> bool:
        """Check if an error is transient and can be retried.

        Args:
            error: The error to check.

        Returns:
            True if the error is transient.
        """
        # Network errors, timeouts, 5xx errors are transient
        error_str = str(error).lower()
        transient_indicators = [
            "timeout",
            "connection",
            "network",
            "502",
            "503",
            "504",
        ]
        return any(indicator in error_str for indicator in transient_indicators)

    def _track_error(self, tool_name: str, error: Exception) -> None:
        """Track error occurrence for monitoring.

        Args:
            tool_name: Name of the tool that failed.
            error: The exception that occurred.
        """
        if tool_name not in self._error_counts:
            self._error_counts[tool_name] = 0
        self._error_counts[tool_name] += 1

        logger.error(
            f"Error in {tool_name}",
            extra={
                "tool_name": tool_name,
                "error_type": type(error).__name__,
                "error_count": self._error_counts[tool_name],
            },
        )

    def get_error_stats(self) -> dict[str, int]:
        """Get error statistics by tool name.

        Returns:
            Dictionary mapping tool names to error counts.
        """
        return dict(self._error_counts)

    def reset_stats(self) -> None:
        """Reset error statistics."""
        self._error_counts.clear()
