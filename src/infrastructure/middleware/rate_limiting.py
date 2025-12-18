"""Rate limiting middleware for Taiga MCP Server.

This middleware provides rate limiting capabilities using token bucket
algorithm to prevent overwhelming the Taiga API.
"""

import asyncio
import time
from typing import Any

from fastmcp.server.middleware import Middleware

from src.domain.exceptions import RateLimitError
from src.infrastructure.logging import get_logger


logger = get_logger("middleware.rate_limiting")


class TokenBucket:
    """Token bucket implementation for rate limiting.

    Provides smooth rate limiting by maintaining a bucket of tokens
    that refills at a constant rate.
    """

    def __init__(
        self,
        max_tokens: float,
        refill_rate: float,
    ) -> None:
        """Initialize token bucket.

        Args:
            max_tokens: Maximum tokens in the bucket.
            refill_rate: Tokens added per second.
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.tokens = max_tokens
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> bool:
        """Try to acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire.

        Returns:
            True if tokens were acquired, False if not enough tokens.
        """
        async with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def wait_for_token(self, tokens: float = 1.0, timeout: float = 30.0) -> bool:
        """Wait for tokens to become available.

        Args:
            tokens: Number of tokens needed.
            timeout: Maximum time to wait in seconds.

        Returns:
            True if tokens were acquired within timeout.
        """
        start = time.monotonic()
        while True:
            if await self.acquire(tokens):
                return True
            if time.monotonic() - start > timeout:
                return False
            # Calculate wait time for tokens to refill
            async with self._lock:
                self._refill()
                needed = tokens - self.tokens
                wait_time = needed / self.refill_rate
                wait_time = min(wait_time, 0.1)  # Cap at 100ms increments
            await asyncio.sleep(wait_time)

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    @property
    def available(self) -> float:
        """Get current available tokens (without acquiring)."""
        return self.tokens


class RateLimitingMiddleware(Middleware):
    """Middleware for rate limiting API requests.

    Uses token bucket algorithm to provide smooth rate limiting.

    Attributes:
        max_requests_per_second: Maximum requests per second.
        burst_size: Maximum burst size (tokens in bucket).
        algorithm: Rate limiting algorithm ('token_bucket' or 'sliding_window').
    """

    def __init__(
        self,
        max_requests_per_second: float = 50.0,
        burst_size: float | None = None,
        algorithm: str = "token_bucket",
        wait_for_token: bool = True,
        wait_timeout: float = 30.0,
    ) -> None:
        """Initialize rate limiting middleware.

        Args:
            max_requests_per_second: Maximum requests per second.
            burst_size: Maximum burst size. Defaults to 2x rate.
            algorithm: Rate limiting algorithm (currently only 'token_bucket').
            wait_for_token: Whether to wait for tokens or fail immediately.
            wait_timeout: Maximum time to wait for tokens.
        """
        self.max_requests_per_second = max_requests_per_second
        self.burst_size = burst_size or (max_requests_per_second * 2)
        self.algorithm = algorithm
        self.wait_for_token = wait_for_token
        self.wait_timeout = wait_timeout

        # Initialize token bucket
        self._bucket = TokenBucket(
            max_tokens=self.burst_size,
            refill_rate=max_requests_per_second,
        )

        # Statistics
        self._total_requests = 0
        self._limited_requests = 0
        self._waited_requests = 0

    async def on_call_tool(
        self,
        context: Any,
        call_next: Any,
    ) -> Any:
        """Handle tool calls with rate limiting.

        Args:
            context: The middleware context.
            call_next: Function to call the next middleware.

        Returns:
            The result from the tool.

        Raises:
            RateLimitError: If rate limit is exceeded and wait is disabled.
        """
        self._total_requests += 1

        # Try to acquire token
        acquired = await self._bucket.acquire()

        if not acquired:
            if self.wait_for_token:
                self._waited_requests += 1
                logger.debug("Rate limit reached, waiting for token...")
                acquired = await self._bucket.wait_for_token(timeout=self.wait_timeout)
                if not acquired:
                    self._limited_requests += 1
                    raise RateLimitError(
                        f"Rate limit exceeded: {self.max_requests_per_second} req/s"
                    )
            else:
                self._limited_requests += 1
                raise RateLimitError(f"Rate limit exceeded: {self.max_requests_per_second} req/s")

        return await call_next(context)

    def get_stats(self) -> dict[str, Any]:
        """Get rate limiting statistics.

        Returns:
            Dictionary with rate limiting stats.
        """
        return {
            "total_requests": self._total_requests,
            "limited_requests": self._limited_requests,
            "waited_requests": self._waited_requests,
            "available_tokens": self._bucket.available,
            "max_requests_per_second": self.max_requests_per_second,
            "burst_size": self.burst_size,
        }

    def reset_stats(self) -> None:
        """Reset rate limiting statistics."""
        self._total_requests = 0
        self._limited_requests = 0
        self._waited_requests = 0
