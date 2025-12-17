"""
Correlation ID management for request tracing.

Provides thread-safe correlation ID management using contextvars,
enabling request tracing across async operations.
"""

import uuid
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar

# Context variable for storing correlation ID
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class CorrelationIdManager:
    """
    Manager for correlation IDs to trace requests through the system.

    Uses Python's contextvars to maintain correlation IDs across
    async operations, enabling end-to-end request tracing.

    Example:
        >>> with CorrelationIdManager.context() as correlation_id:
        ...     logger.info(f"Processing request: {correlation_id}")
        ...     # All logs within this context will have the same correlation_id
    """

    @staticmethod
    def generate() -> str:
        """Generate a new correlation ID."""
        return str(uuid.uuid4())[:8]  # Short UUID for readability

    @staticmethod
    def get() -> str:
        """
        Get the current correlation ID.

        Returns:
            Current correlation ID or empty string if not set
        """
        return correlation_id_var.get()

    @staticmethod
    def set(correlation_id: str) -> None:
        """
        Set the correlation ID for the current context.

        Args:
            correlation_id: The correlation ID to set
        """
        correlation_id_var.set(correlation_id)

    @staticmethod
    def reset() -> None:
        """Reset the correlation ID to empty."""
        correlation_id_var.set("")

    @classmethod
    @contextmanager
    def context(cls, correlation_id: str | None = None) -> Generator[str, None, None]:
        """
        Context manager for correlation ID scope.

        Args:
            correlation_id: Optional correlation ID to use. If not provided,
                           a new one will be generated.

        Yields:
            The correlation ID for this context

        Example:
            >>> with CorrelationIdManager.context() as cid:
            ...     print(f"Request ID: {cid}")
        """
        cid = correlation_id or cls.generate()
        token = correlation_id_var.set(cid)
        try:
            yield cid
        finally:
            correlation_id_var.reset(token)

    @classmethod
    def ensure_correlation_id(cls) -> str:
        """
        Ensure a correlation ID exists, creating one if needed.

        Returns:
            Existing or newly created correlation ID
        """
        current = cls.get()
        if not current:
            current = cls.generate()
            cls.set(current)
        return current
