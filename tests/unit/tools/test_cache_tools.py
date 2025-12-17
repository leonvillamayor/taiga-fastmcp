"""Tests for cache management tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.tools.cache_tools import CacheTools


class TestCacheTools:
    """Tests for CacheTools class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_mcp = MagicMock()
        # Mock the tool decorator to capture registered functions
        self.registered_tools = {}

        def mock_tool(**kwargs):
            def decorator(func):
                self.registered_tools[kwargs.get("name")] = {
                    "func": func,
                    "kwargs": kwargs,
                }
                return func

            return decorator

        self.mock_mcp.tool = mock_tool
        self.cache_tools = CacheTools(self.mock_mcp)
        self.cache_tools.register_tools()

    def test_registers_all_tools(self):
        """Should register all cache management tools."""
        expected_tools = [
            "taiga_cache_stats",
            "taiga_cache_clear",
            "taiga_cache_invalidate_project",
            "taiga_cache_invalidate_pattern",
        ]
        for tool_name in expected_tools:
            assert tool_name in self.registered_tools, f"Tool {tool_name} not registered"

    def test_cache_stats_tool_has_correct_description(self):
        """taiga_cache_stats should have appropriate description."""
        tool = self.registered_tools["taiga_cache_stats"]
        assert "statistics" in tool["kwargs"]["description"].lower()

    def test_cache_clear_tool_has_correct_description(self):
        """taiga_cache_clear should have appropriate description."""
        tool = self.registered_tools["taiga_cache_clear"]
        assert "clear" in tool["kwargs"]["description"].lower()

    def test_invalidate_project_tool_has_correct_description(self):
        """taiga_cache_invalidate_project should have appropriate description."""
        tool = self.registered_tools["taiga_cache_invalidate_project"]
        assert "project" in tool["kwargs"]["description"].lower()

    def test_invalidate_pattern_tool_has_correct_description(self):
        """taiga_cache_invalidate_pattern should have appropriate description."""
        tool = self.registered_tools["taiga_cache_invalidate_pattern"]
        assert "pattern" in tool["kwargs"]["description"].lower()


class TestCacheStatsExecution:
    """Tests for taiga_cache_stats tool execution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_mcp = MagicMock()
        self.registered_tools = {}

        def mock_tool(**kwargs):
            def decorator(func):
                self.registered_tools[kwargs.get("name")] = func
                return func

            return decorator

        self.mock_mcp.tool = mock_tool
        self.cache_tools = CacheTools(self.mock_mcp)
        self.cache_tools.register_tools()

    @pytest.mark.asyncio
    @patch("src.application.tools.cache_tools.get_global_cache")
    async def test_returns_cache_stats(self, mock_get_cache):
        """Should return cache statistics."""
        mock_cache = MagicMock()
        mock_cache.get_stats = AsyncMock(
            return_value={
                "size": 10,
                "max_size": 1000,
                "default_ttl": 3600,
                "metrics": {
                    "hits": 100,
                    "misses": 20,
                    "hit_rate": 0.83,
                },
            }
        )
        mock_get_cache.return_value = mock_cache

        tool_func = self.registered_tools["taiga_cache_stats"]
        result = await tool_func()

        assert result["size"] == 10
        assert result["metrics"]["hits"] == 100
        mock_cache.get_stats.assert_called_once()


class TestCacheClearExecution:
    """Tests for taiga_cache_clear tool execution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_mcp = MagicMock()
        self.registered_tools = {}

        def mock_tool(**kwargs):
            def decorator(func):
                self.registered_tools[kwargs.get("name")] = func
                return func

            return decorator

        self.mock_mcp.tool = mock_tool
        self.cache_tools = CacheTools(self.mock_mcp)
        self.cache_tools.register_tools()

    @pytest.mark.asyncio
    @patch("src.application.tools.cache_tools.clear_all_cache")
    async def test_clears_cache_and_returns_count(self, mock_clear):
        """Should clear cache and return count of cleared entries."""
        mock_clear.return_value = 25

        tool_func = self.registered_tools["taiga_cache_clear"]
        result = await tool_func()

        assert result["success"] is True
        assert result["cleared_entries"] == 25
        assert "25" in result["message"]
        mock_clear.assert_called_once()


class TestInvalidateProjectCacheExecution:
    """Tests for taiga_cache_invalidate_project tool execution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_mcp = MagicMock()
        self.registered_tools = {}

        def mock_tool(**kwargs):
            def decorator(func):
                self.registered_tools[kwargs.get("name")] = func
                return func

            return decorator

        self.mock_mcp.tool = mock_tool
        self.cache_tools = CacheTools(self.mock_mcp)
        self.cache_tools.register_tools()

    @pytest.mark.asyncio
    @patch("src.application.tools.cache_tools.invalidate_project_cache")
    async def test_invalidates_project_cache(self, mock_invalidate):
        """Should invalidate project cache and return count."""
        mock_invalidate.return_value = 5

        tool_func = self.registered_tools["taiga_cache_invalidate_project"]
        result = await tool_func(project_id=123)

        assert result["success"] is True
        assert result["project_id"] == 123
        assert result["invalidated_entries"] == 5
        mock_invalidate.assert_called_once_with(123)


class TestInvalidateCachePatternExecution:
    """Tests for taiga_cache_invalidate_pattern tool execution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_mcp = MagicMock()
        self.registered_tools = {}

        def mock_tool(**kwargs):
            def decorator(func):
                self.registered_tools[kwargs.get("name")] = func
                return func

            return decorator

        self.mock_mcp.tool = mock_tool
        self.cache_tools = CacheTools(self.mock_mcp)
        self.cache_tools.register_tools()

    @pytest.mark.asyncio
    @patch("src.application.tools.cache_tools.invalidate_cache_by_pattern")
    async def test_invalidates_cache_by_pattern(self, mock_invalidate):
        """Should invalidate cache by pattern and return count."""
        mock_invalidate.return_value = 8

        tool_func = self.registered_tools["taiga_cache_invalidate_pattern"]
        result = await tool_func(pattern="epic_")

        assert result["success"] is True
        assert result["pattern"] == "epic_"
        assert result["invalidated_entries"] == 8
        mock_invalidate.assert_called_once_with("epic_")
