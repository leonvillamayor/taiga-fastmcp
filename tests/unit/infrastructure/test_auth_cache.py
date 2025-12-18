"""Tests for authentication token cache."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from src.infrastructure.auth_cache import AuthTokenCache, AuthTokenCacheManager


class TestAuthTokenCache:
    """Tests for AuthTokenCache class."""

    def test_init_default_values(self) -> None:
        """Test initialization with default values."""
        cache = AuthTokenCache()

        assert cache.token is None
        assert cache.refresh_token is None
        assert cache.user_id is None
        assert cache.is_valid is False
        assert cache.needs_refresh is True

    def test_init_custom_values(self) -> None:
        """Test initialization with custom values."""
        cache = AuthTokenCache(
            refresh_threshold_seconds=600,
            default_ttl_seconds=3600,
        )

        assert cache._refresh_threshold == timedelta(seconds=600)
        assert cache._default_ttl == timedelta(seconds=3600)

    def test_set_token_basic(self) -> None:
        """Test setting a token with basic parameters."""
        cache = AuthTokenCache()

        cache.set_token(
            token="test_token",
            refresh_token="test_refresh",
            user_id=123,
        )

        assert cache.token == "test_token"
        assert cache.refresh_token == "test_refresh"
        assert cache.user_id == 123
        assert cache.is_valid is True
        # Token should not need refresh yet (just set)
        assert cache.needs_refresh is False

    def test_set_token_with_ttl(self) -> None:
        """Test setting a token with TTL."""
        cache = AuthTokenCache()

        cache.set_token(token="test_token", ttl_seconds=60)

        assert cache.is_valid is True
        assert cache._expires_at is not None
        # Should expire in ~60 seconds
        expected_expiry = datetime.now(UTC) + timedelta(seconds=60)
        assert abs((cache._expires_at - expected_expiry).total_seconds()) < 2

    def test_set_token_with_expires_at(self) -> None:
        """Test setting a token with explicit expiration."""
        cache = AuthTokenCache()
        expiry = datetime.now(UTC) + timedelta(hours=1)

        cache.set_token(token="test_token", expires_at=expiry)

        assert cache._expires_at == expiry

    def test_is_valid_expired_token(self) -> None:
        """Test is_valid with expired token."""
        cache = AuthTokenCache()

        # Set token that expires in the past
        cache._token = "expired_token"
        cache._expires_at = datetime.now(UTC) - timedelta(minutes=1)

        assert cache.is_valid is False

    def test_is_valid_valid_token(self) -> None:
        """Test is_valid with valid token."""
        cache = AuthTokenCache()

        # Set token that expires in the future
        cache._token = "valid_token"
        cache._expires_at = datetime.now(UTC) + timedelta(hours=1)

        assert cache.is_valid is True

    def test_needs_refresh_no_token(self) -> None:
        """Test needs_refresh when no token is set."""
        cache = AuthTokenCache()

        assert cache.needs_refresh is True

    def test_needs_refresh_approaching_expiry(self) -> None:
        """Test needs_refresh when token is about to expire."""
        cache = AuthTokenCache(refresh_threshold_seconds=300)  # 5 minutes

        # Token expires in 2 minutes (less than threshold)
        cache._token = "test_token"
        cache._expires_at = datetime.now(UTC) + timedelta(minutes=2)

        assert cache.needs_refresh is True

    def test_needs_refresh_not_approaching_expiry(self) -> None:
        """Test needs_refresh when token has plenty of time."""
        cache = AuthTokenCache(refresh_threshold_seconds=300)  # 5 minutes

        # Token expires in 1 hour (more than threshold)
        cache._token = "test_token"
        cache._expires_at = datetime.now(UTC) + timedelta(hours=1)

        assert cache.needs_refresh is False

    def test_invalidate(self) -> None:
        """Test invalidating the cache."""
        cache = AuthTokenCache()

        cache.set_token(
            token="test_token",
            refresh_token="test_refresh",
            user_id=123,
        )

        cache.invalidate()

        assert cache.token is None
        assert cache.refresh_token is None
        assert cache.user_id is None
        assert cache.is_valid is False

    @pytest.mark.asyncio
    async def test_get_valid_token_cached(self) -> None:
        """Test getting a valid token from cache."""
        cache = AuthTokenCache()

        cache.set_token(token="test_token", ttl_seconds=3600)

        token = await cache.get_valid_token()

        assert token == "test_token"
        assert cache._hits == 1
        assert cache._misses == 0

    @pytest.mark.asyncio
    async def test_get_valid_token_expired(self) -> None:
        """Test getting token when expired without refresh func."""
        cache = AuthTokenCache()

        # Set expired token
        cache._token = "expired_token"
        cache._expires_at = datetime.now(UTC) - timedelta(minutes=1)

        token = await cache.get_valid_token()

        assert token is None
        assert cache._misses == 1

    @pytest.mark.asyncio
    async def test_get_valid_token_with_refresh(self) -> None:
        """Test automatic token refresh."""
        cache = AuthTokenCache(refresh_threshold_seconds=600)

        # Set token that needs refresh
        cache._token = "old_token"
        cache._refresh_token = "refresh_token"
        cache._expires_at = datetime.now(UTC) + timedelta(minutes=2)

        async def mock_refresh() -> dict:
            return {
                "auth_token": "new_token",
                "refresh_token": "new_refresh",
                "id": 456,
            }

        token = await cache.get_valid_token(refresh_func=mock_refresh)

        assert token == "new_token"
        assert cache.refresh_token == "new_refresh"
        assert cache.user_id == 456
        assert cache._refreshes == 1

    @pytest.mark.asyncio
    async def test_get_valid_token_refresh_fails(self) -> None:
        """Test handling of refresh failure with still-valid token."""
        cache = AuthTokenCache(refresh_threshold_seconds=600)

        # Set token that needs refresh but is still valid
        cache._token = "still_valid_token"
        cache._refresh_token = "refresh_token"
        cache._expires_at = datetime.now(UTC) + timedelta(minutes=2)

        async def failing_refresh() -> dict:
            raise Exception("Refresh failed")

        token = await cache.get_valid_token(refresh_func=failing_refresh)

        # Should return the still-valid token
        assert token == "still_valid_token"

    def test_get_metrics(self) -> None:
        """Test getting cache metrics."""
        cache = AuthTokenCache()

        cache.set_token(token="test_token", ttl_seconds=3600)
        cache._hits = 10
        cache._misses = 2
        cache._refreshes = 1

        metrics = cache.get_metrics()

        assert metrics["hits"] == 10
        assert metrics["misses"] == 2
        assert metrics["refreshes"] == 1
        assert metrics["hit_rate"] == pytest.approx(10 / 12)
        assert metrics["token_valid"] is True

    def test_reset_metrics(self) -> None:
        """Test resetting cache metrics."""
        cache = AuthTokenCache()

        cache._hits = 10
        cache._misses = 5
        cache._refreshes = 2

        cache.reset_metrics()

        assert cache._hits == 0
        assert cache._misses == 0
        assert cache._refreshes == 0


class TestAuthTokenCacheManager:
    """Tests for AuthTokenCacheManager class."""

    @pytest.mark.asyncio
    async def test_get_cache_creates_new(self) -> None:
        """Test getting a new cache creates it."""
        manager = AuthTokenCacheManager()

        cache = await manager.get_cache("user1")

        assert cache is not None
        assert isinstance(cache, AuthTokenCache)

    @pytest.mark.asyncio
    async def test_get_cache_returns_existing(self) -> None:
        """Test getting same cache returns existing instance."""
        manager = AuthTokenCacheManager()

        cache1 = await manager.get_cache("user1")
        cache1.set_token(token="test_token")

        cache2 = await manager.get_cache("user1")

        assert cache1 is cache2
        assert cache2.token == "test_token"

    @pytest.mark.asyncio
    async def test_get_cache_different_keys(self) -> None:
        """Test different keys get different caches."""
        manager = AuthTokenCacheManager()

        cache1 = await manager.get_cache("user1")
        cache2 = await manager.get_cache("user2")

        assert cache1 is not cache2

    @pytest.mark.asyncio
    async def test_invalidate_specific_cache(self) -> None:
        """Test invalidating a specific cache."""
        manager = AuthTokenCacheManager()

        cache1 = await manager.get_cache("user1")
        cache2 = await manager.get_cache("user2")

        cache1.set_token(token="token1")
        cache2.set_token(token="token2")

        result = await manager.invalidate("user1")

        assert result is True
        assert cache1.token is None
        assert cache2.token == "token2"

    @pytest.mark.asyncio
    async def test_invalidate_nonexistent(self) -> None:
        """Test invalidating a nonexistent cache."""
        manager = AuthTokenCacheManager()

        result = await manager.invalidate("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_all(self) -> None:
        """Test invalidating all caches."""
        manager = AuthTokenCacheManager()

        cache1 = await manager.get_cache("user1")
        cache2 = await manager.get_cache("user2")

        cache1.set_token(token="token1")
        cache2.set_token(token="token2")

        count = await manager.invalidate_all()

        assert count == 2
        assert cache1.token is None
        assert cache2.token is None

    @pytest.mark.asyncio
    async def test_get_all_metrics(self) -> None:
        """Test getting metrics for all caches."""
        manager = AuthTokenCacheManager()

        cache1 = await manager.get_cache("user1")
        _cache2 = await manager.get_cache("user2")

        cache1.set_token(token="token1")
        cache1._hits = 5

        metrics = manager.get_all_metrics()

        assert "user1" in metrics
        assert "user2" in metrics
        assert metrics["user1"]["hits"] == 5

    @pytest.mark.asyncio
    async def test_concurrent_access(self) -> None:
        """Test concurrent access to cache manager."""
        manager = AuthTokenCacheManager()

        async def get_and_set(key: str, token: str) -> AuthTokenCache:
            cache = await manager.get_cache(key)
            cache.set_token(token=token)
            return cache

        # Create tasks that access the same cache concurrently
        tasks = [get_and_set(f"user{i % 3}", f"token{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)

        # Should have created exactly 3 caches
        assert len(manager._caches) == 3

        # All results should be AuthTokenCache instances
        assert all(isinstance(r, AuthTokenCache) for r in results)
