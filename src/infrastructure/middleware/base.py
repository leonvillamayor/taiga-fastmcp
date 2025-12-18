"""Base middleware utilities for Taiga MCP Server.

This module provides base classes and utilities for middleware implementations.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar


T = TypeVar("T")
R = TypeVar("R")

# Type alias for call_next function
CallNext = Callable[[T], R]


class MiddlewareContext:
    """Context object passed to middleware.

    Contains the request/notification being processed and metadata about it.
    """

    def __init__(self, message: Any, metadata: dict[str, Any] | None = None) -> None:
        """Initialize middleware context.

        Args:
            message: The incoming message/request.
            metadata: Additional metadata about the request.
        """
        self.message = message
        self.metadata = metadata or {}

    @property
    def request_type(self) -> str:
        """Get the type of request being processed."""
        return type(self.message).__name__


class BaseMiddleware(ABC):
    """Base class for all middleware implementations.

    Provides a common interface for middleware that can intercept
    and modify requests/responses.
    """

    @abstractmethod
    async def process(
        self,
        context: MiddlewareContext,
        call_next: CallNext[MiddlewareContext, Any],
    ) -> Any:
        """Process a request through the middleware.

        Args:
            context: The middleware context containing the request.
            call_next: Function to call the next middleware in the chain.

        Returns:
            The result after processing through the chain.
        """
