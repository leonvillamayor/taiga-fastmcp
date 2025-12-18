"""Authentication token cache for Taiga MCP Server.

This module provides a specialized cache for authentication tokens
with automatic refresh capabilities.
"""

import asyncio
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime, timedelta
from typing import Any

from src.infrastructure.logging import get_logger


logger = get_logger("auth_cache")


class AuthTokenCache:
    """Cache for authentication tokens with automatic refresh.

    This cache stores authentication tokens and handles automatic refresh
    before expiration to ensure seamless authentication.

    Features:
    - TTL based on token expiration
    - Automatic refresh before expiration
    - Thread-safe operations with asyncio Lock
    - Metrics for cache hits/misses

    Attributes:
        refresh_threshold_seconds: Time before expiration to trigger refresh.
    """

    def __init__(
        self,
        refresh_threshold_seconds: int = 300,
        default_ttl_seconds: int = 86400,
    ) -> None:
        """Initialize the authentication token cache.

        Args:
            refresh_threshold_seconds: Time in seconds before expiration
                to trigger a proactive refresh. Default is 5 minutes.
            default_ttl_seconds: Default TTL for tokens when expiration
                is not provided. Default is 24 hours.
        """
        self._token: str | None = None
        self._refresh_token: str | None = None
        self._user_id: int | None = None
        self._expires_at: datetime | None = None
        self._refresh_threshold = timedelta(seconds=refresh_threshold_seconds)
        self._default_ttl = timedelta(seconds=default_ttl_seconds)
        self._lock = asyncio.Lock()

        # Metrics
        self._hits = 0
        self._misses = 0
        self._refreshes = 0
        self._last_refresh: datetime | None = None

    @property
    def token(self) -> str | None:
        """Get the current token (may be expired)."""
        return self._token

    @property
    def refresh_token(self) -> str | None:
        """Get the current refresh token."""
        return self._refresh_token

    @property
    def user_id(self) -> int | None:
        """Get the current user ID."""
        return self._user_id

    @property
    def is_valid(self) -> bool:
        """Check if the current token is valid (not expired)."""
        if not self._token or not self._expires_at:
            return False
        return datetime.now(UTC) < self._expires_at

    @property
    def needs_refresh(self) -> bool:
        """Check if the token needs to be refreshed proactively."""
        if not self._token or not self._expires_at:
            return True
        threshold_time = datetime.now(UTC) + self._refresh_threshold
        return threshold_time > self._expires_at

    def set_token(
        self,
        token: str,
        refresh_token: str | None = None,
        user_id: int | None = None,
        expires_at: datetime | None = None,
        ttl_seconds: int | None = None,
    ) -> None:
        """Store a new authentication token.

        Args:
            token: The authentication token.
            refresh_token: Optional refresh token for renewal.
            user_id: Optional user ID associated with the token.
            expires_at: Optional expiration datetime.
            ttl_seconds: Optional TTL in seconds (used if expires_at not provided).
        """
        self._token = token
        self._refresh_token = refresh_token
        self._user_id = user_id

        if expires_at:
            # Ensure timezone awareness
            if expires_at.tzinfo is None:
                self._expires_at = expires_at.replace(tzinfo=UTC)
            else:
                self._expires_at = expires_at
        elif ttl_seconds:
            self._expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        else:
            self._expires_at = datetime.now(UTC) + self._default_ttl

        self._last_refresh = datetime.now(UTC)
        logger.debug(
            "Token cached",
            extra={
                "user_id": user_id,
                "expires_at": self._expires_at.isoformat() if self._expires_at else None,
            },
        )

    async def get_valid_token(
        self,
        refresh_func: Callable[[], Coroutine[Any, Any, dict[str, Any]]] | None = None,
    ) -> str | None:
        """Get a valid token, refreshing if necessary.

        If the token is about to expire and a refresh function is provided,
        this method will automatically refresh the token.

        Args:
            refresh_func: Optional async function that refreshes the token.
                Should return a dict with 'auth_token', 'refresh_token',
                and optionally 'id' (user_id).

        Returns:
            A valid authentication token, or None if unavailable.

        Raises:
            Exception: If refresh fails and no valid token is available.
        """
        async with self._lock:
            # Check if we have a valid token
            if self.is_valid and not self.needs_refresh:
                self._hits += 1
                return self._token

            # Need to refresh or get new token
            self._misses += 1

            if self.needs_refresh and refresh_func and self._refresh_token:
                try:
                    await self._refresh(refresh_func)
                    return self._token
                except Exception as e:
                    logger.warning(f"Token refresh failed: {e}")
                    # If refresh fails but token is still valid, return it
                    if self.is_valid:
                        return self._token
                    raise

            # Return current token if valid (even if refresh failed)
            if self.is_valid:
                return self._token

            return None

    async def _refresh(
        self,
        refresh_func: Callable[[], Coroutine[Any, Any, dict[str, Any]]],
    ) -> None:
        """Refresh the authentication token.

        Args:
            refresh_func: Async function that performs the refresh.
        """
        logger.debug("Refreshing authentication token")
        self._refreshes += 1

        result = await refresh_func()

        # Update cached values
        self._token = result.get("auth_token")
        if "refresh_token" in result:
            self._refresh_token = result.get("refresh_token")
        if "id" in result:
            self._user_id = result.get("id")

        # Set new expiration (assume default TTL if not provided)
        self._expires_at = datetime.now(UTC) + self._default_ttl
        self._last_refresh = datetime.now(UTC)

        logger.info(
            "Token refreshed successfully",
            extra={"user_id": self._user_id},
        )

    def invalidate(self) -> None:
        """Invalidate the cached token.

        Call this on logout or when the token is known to be invalid.
        """
        logger.debug("Invalidating cached token", extra={"user_id": self._user_id})
        self._token = None
        self._refresh_token = None
        self._user_id = None
        self._expires_at = None

    def get_metrics(self) -> dict[str, Any]:
        """Get cache metrics.

        Returns:
            Dictionary with cache metrics including hits, misses, and refresh count.
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "refreshes": self._refreshes,
            "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
            "token_valid": self.is_valid,
            "needs_refresh": self.needs_refresh,
            "expires_at": self._expires_at.isoformat() if self._expires_at else None,
        }

    def reset_metrics(self) -> None:
        """Reset cache metrics."""
        self._hits = 0
        self._misses = 0
        self._refreshes = 0


class AuthTokenCacheManager:
    """Manager for multiple authentication token caches.

    Supports caching tokens for multiple users or contexts.
    """

    def __init__(
        self,
        refresh_threshold_seconds: int = 300,
        default_ttl_seconds: int = 86400,
    ) -> None:
        """Initialize the cache manager.

        Args:
            refresh_threshold_seconds: Default refresh threshold for caches.
            default_ttl_seconds: Default TTL for tokens.
        """
        self._caches: dict[str, AuthTokenCache] = {}
        self._refresh_threshold = refresh_threshold_seconds
        self._default_ttl = default_ttl_seconds
        self._lock = asyncio.Lock()

    async def get_cache(self, key: str = "default") -> AuthTokenCache:
        """Get or create a cache for the given key.

        Args:
            key: Cache key (e.g., username or client ID).

        Returns:
            AuthTokenCache instance for the key.
        """
        async with self._lock:
            if key not in self._caches:
                self._caches[key] = AuthTokenCache(
                    refresh_threshold_seconds=self._refresh_threshold,
                    default_ttl_seconds=self._default_ttl,
                )
            return self._caches[key]

    async def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache.

        Args:
            key: Cache key to invalidate.

        Returns:
            True if cache was found and invalidated, False otherwise.
        """
        async with self._lock:
            if key in self._caches:
                self._caches[key].invalidate()
                return True
            return False

    async def invalidate_all(self) -> int:
        """Invalidate all caches.

        Returns:
            Number of caches invalidated.
        """
        async with self._lock:
            count = len(self._caches)
            for cache in self._caches.values():
                cache.invalidate()
            return count

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """Get metrics for all caches.

        Returns:
            Dictionary mapping cache keys to their metrics.
        """
        return {key: cache.get_metrics() for key, cache in self._caches.items()}
