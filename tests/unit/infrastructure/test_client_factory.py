"""Tests for client factory with caching."""

from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.cache import MemoryCache
from src.infrastructure.cached_client import CachedTaigaClient
from src.infrastructure.client_factory import (
    clear_all_cache,
    get_cached_taiga_client,
    get_global_cache,
    get_taiga_client,
    invalidate_cache_by_pattern,
    invalidate_project_cache,
    reset_global_cache,
)
from src.taiga_client import TaigaAPIClient


class TestGetGlobalCache:
    """Tests for get_global_cache function."""

    def setup_method(self):
        """Reset global cache before each test."""
        reset_global_cache()

    def teardown_method(self):
        """Reset global cache after each test."""
        reset_global_cache()

    def test_returns_memory_cache_instance(self):
        """Should return a MemoryCache instance."""
        cache = get_global_cache()
        assert isinstance(cache, MemoryCache)

    def test_is_singleton(self):
        """Should return the same instance on multiple calls."""
        cache1 = get_global_cache()
        cache2 = get_global_cache()
        assert cache1 is cache2

    def test_has_correct_default_ttl(self):
        """Should have 3600 seconds (1 hour) default TTL."""
        cache = get_global_cache()
        assert cache.default_ttl == 3600

    def test_has_correct_max_size(self):
        """Should have max_size of 1000."""
        cache = get_global_cache()
        assert cache.max_size == 1000


class TestResetGlobalCache:
    """Tests for reset_global_cache function."""

    def test_creates_new_instance_after_reset(self):
        """Should create a new cache instance after reset."""
        cache1 = get_global_cache()
        reset_global_cache()
        cache2 = get_global_cache()
        assert cache1 is not cache2


class TestGetTaigaClient:
    """Tests for get_taiga_client function (without cache)."""

    def setup_method(self):
        """Reset global cache before each test."""
        reset_global_cache()

    @patch("src.infrastructure.client_factory.TaigaConfig")
    @patch("src.infrastructure.client_factory.TaigaAPIClient")
    def test_returns_taiga_api_client(self, mock_client_class, mock_config_class):
        """Should return a TaigaAPIClient instance."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        mock_client = MagicMock(spec=TaigaAPIClient)
        mock_client_class.return_value = mock_client

        client = get_taiga_client()

        mock_client_class.assert_called_once_with(mock_config)
        assert client is mock_client

    @patch("src.infrastructure.client_factory.TaigaConfig")
    @patch("src.infrastructure.client_factory.TaigaAPIClient")
    def test_sets_auth_token_when_provided(self, mock_client_class, mock_config_class):
        """Should set auth_token on client when provided."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        mock_client = MagicMock(spec=TaigaAPIClient)
        mock_client_class.return_value = mock_client

        get_taiga_client(auth_token="test_token")

        assert mock_client.auth_token == "test_token"

    @patch("src.infrastructure.client_factory.TaigaConfig")
    @patch("src.infrastructure.client_factory.TaigaAPIClient")
    def test_does_not_set_auth_token_when_none(self, mock_client_class, mock_config_class):
        """Should not set auth_token when not provided."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        mock_client = MagicMock(spec=TaigaAPIClient)
        mock_client.auth_token = None
        mock_client_class.return_value = mock_client

        get_taiga_client()

        # auth_token should remain None (not be set)
        assert mock_client.auth_token is None


class TestGetCachedTaigaClient:
    """Tests for get_cached_taiga_client function."""

    def setup_method(self):
        """Reset global cache before each test."""
        reset_global_cache()

    def teardown_method(self):
        """Reset global cache after each test."""
        reset_global_cache()

    @patch("src.infrastructure.client_factory.TaigaConfig")
    @patch("src.infrastructure.client_factory.TaigaAPIClient")
    def test_returns_cached_taiga_client(self, mock_client_class, mock_config_class):
        """Should return a CachedTaigaClient instance."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        mock_client = MagicMock(spec=TaigaAPIClient)
        mock_client_class.return_value = mock_client

        cached_client = get_cached_taiga_client()

        assert isinstance(cached_client, CachedTaigaClient)

    @patch("src.infrastructure.client_factory.TaigaConfig")
    @patch("src.infrastructure.client_factory.TaigaAPIClient")
    def test_uses_global_cache(self, mock_client_class, mock_config_class):
        """Should use the global cache instance."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        mock_client = MagicMock(spec=TaigaAPIClient)
        mock_client_class.return_value = mock_client

        global_cache = get_global_cache()
        cached_client = get_cached_taiga_client()

        assert cached_client.cache is global_cache

    @patch("src.infrastructure.client_factory.TaigaConfig")
    @patch("src.infrastructure.client_factory.TaigaAPIClient")
    def test_sets_auth_token_when_provided(self, mock_client_class, mock_config_class):
        """Should set auth_token on underlying client."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        mock_client = MagicMock(spec=TaigaAPIClient)
        mock_client_class.return_value = mock_client

        get_cached_taiga_client(auth_token="test_token")

        assert mock_client.auth_token == "test_token"

    @patch("src.infrastructure.client_factory.TaigaConfig")
    @patch("src.infrastructure.client_factory.TaigaAPIClient")
    def test_multiple_clients_share_same_cache(self, mock_client_class, mock_config_class):
        """Multiple cached clients should share the same cache."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        mock_client = MagicMock(spec=TaigaAPIClient)
        mock_client_class.return_value = mock_client

        client1 = get_cached_taiga_client()
        client2 = get_cached_taiga_client()

        assert client1.cache is client2.cache


class TestInvalidateProjectCache:
    """Tests for invalidate_project_cache function."""

    def setup_method(self):
        """Reset global cache before each test."""
        reset_global_cache()

    def teardown_method(self):
        """Reset global cache after each test."""
        reset_global_cache()

    @pytest.mark.asyncio
    async def test_invalidates_project_entries(self):
        """Should invalidate cache entries for the project."""
        cache = get_global_cache()
        await cache.set("epic_filters:project_id=123", {"filters": []})
        await cache.set("issue_filters:project_id=123", {"filters": []})
        await cache.set("epic_filters:project_id=456", {"filters": []})

        count = await invalidate_project_cache(123)

        assert count == 2
        assert await cache.get("epic_filters:project_id=123") is None
        assert await cache.get("issue_filters:project_id=123") is None
        assert await cache.get("epic_filters:project_id=456") is not None

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_entries_match(self):
        """Should return 0 when no entries match."""
        count = await invalidate_project_cache(999)
        assert count == 0


class TestInvalidateCacheByPattern:
    """Tests for invalidate_cache_by_pattern function."""

    def setup_method(self):
        """Reset global cache before each test."""
        reset_global_cache()

    def teardown_method(self):
        """Reset global cache after each test."""
        reset_global_cache()

    @pytest.mark.asyncio
    async def test_invalidates_matching_entries(self):
        """Should invalidate entries matching the pattern."""
        cache = get_global_cache()
        await cache.set("epic_filters:project_id=123", {"data": 1})
        await cache.set("epic_custom_attributes:project_id=123", {"data": 2})
        await cache.set("issue_filters:project_id=123", {"data": 3})

        count = await invalidate_cache_by_pattern("epic_")

        assert count == 2
        assert await cache.get("epic_filters:project_id=123") is None
        assert await cache.get("epic_custom_attributes:project_id=123") is None
        assert await cache.get("issue_filters:project_id=123") is not None


class TestClearAllCache:
    """Tests for clear_all_cache function."""

    def setup_method(self):
        """Reset global cache before each test."""
        reset_global_cache()

    def teardown_method(self):
        """Reset global cache after each test."""
        reset_global_cache()

    @pytest.mark.asyncio
    async def test_clears_all_entries(self):
        """Should clear all cache entries."""
        cache = get_global_cache()
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        count = await clear_all_cache()

        assert count == 3
        assert await cache.size() == 0

    @pytest.mark.asyncio
    async def test_returns_zero_when_empty(self):
        """Should return 0 when cache is empty."""
        count = await clear_all_cache()
        assert count == 0
