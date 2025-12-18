"""
Cache management tools for Taiga MCP Server.

Provides MCP tools for monitoring and managing the cache system.
"""

from typing import Any

from fastmcp import FastMCP

from src.infrastructure.client_factory import (
    clear_all_cache,
    get_global_cache,
    invalidate_cache_by_pattern,
    invalidate_project_cache,
)
from src.infrastructure.logging import get_logger


class CacheTools:
    """
    Cache management tools for Taiga MCP Server.

    Provides MCP tools for:
    - Viewing cache statistics
    - Clearing cache entries
    - Invalidating cache by project or pattern
    """

    def __init__(self, mcp: FastMCP) -> None:
        """
        Initialize cache tools.

        Args:
            mcp: FastMCP server instance
        """
        self.mcp = mcp
        self._logger = get_logger("cache_tools")

    def register_tools(self) -> None:
        """Register all cache management tools with the MCP server."""
        self._register_get_cache_stats()
        self._register_clear_cache()
        self._register_invalidate_project_cache()
        self._register_invalidate_cache_pattern()

    def _register_get_cache_stats(self) -> None:
        """Register the cache stats tool."""

        @self.mcp.tool(
            name="taiga_cache_stats",
            description="Get cache statistics including hit rate, miss rate, size, and performance metrics",
        )
        async def taiga_cache_stats() -> dict[str, Any]:
            """
            Get comprehensive cache statistics.

            Returns cache performance metrics including:
            - Current size and maximum size
            - Hit and miss counts
            - Hit rate (percentage of requests served from cache)
            - Eviction and invalidation counts
            """
            self._logger.info("Getting cache statistics")
            cache = get_global_cache()
            stats = await cache.get_stats()
            self._logger.debug(f"Cache stats: {stats}")
            return stats

    def _register_clear_cache(self) -> None:
        """Register the clear cache tool."""

        @self.mcp.tool(
            name="taiga_cache_clear",
            description="Clear all cache entries. Use with caution as this will reset all cached data.",
        )
        async def taiga_cache_clear() -> dict[str, Any]:
            """
            Clear all entries from the cache.

            This operation removes all cached data, forcing fresh API calls
            for subsequent requests. Use when you need to ensure all data
            is fetched fresh from Taiga.

            Returns:
                Dictionary with count of cleared entries
            """
            self._logger.info("Clearing all cache entries")
            count = await clear_all_cache()
            self._logger.info(f"Cleared {count} cache entries")
            return {
                "success": True,
                "cleared_entries": count,
                "message": f"Successfully cleared {count} cache entries",
            }

    def _register_invalidate_project_cache(self) -> None:
        """Register the invalidate project cache tool."""

        @self.mcp.tool(
            name="taiga_cache_invalidate_project",
            description="Invalidate all cached data for a specific project. Use after bulk operations or when project data may be stale.",
        )
        async def taiga_cache_invalidate_project(
            project_id: int,
        ) -> dict[str, Any]:
            """
            Invalidate all cache entries related to a project.

            This removes cached filters, stats, and other project-specific
            data, forcing fresh API calls for that project.

            Args:
                project_id: ID of the project to invalidate cache for

            Returns:
                Dictionary with count of invalidated entries
            """
            self._logger.info(f"Invalidating cache for project {project_id}")
            count = await invalidate_project_cache(project_id)
            self._logger.info(f"Invalidated {count} entries for project {project_id}")
            return {
                "success": True,
                "project_id": project_id,
                "invalidated_entries": count,
                "message": f"Successfully invalidated {count} cache entries for project {project_id}",
            }

    def _register_invalidate_cache_pattern(self) -> None:
        """Register the invalidate cache by pattern tool."""

        @self.mcp.tool(
            name="taiga_cache_invalidate_pattern",
            description="Invalidate cache entries matching a pattern. Pattern matches as substring in cache keys.",
        )
        async def taiga_cache_invalidate_pattern(
            pattern: str,
        ) -> dict[str, Any]:
            """
            Invalidate cache entries matching a pattern.

            Useful for invalidating specific types of cached data:
            - "epic_" - invalidate all epic-related cache
            - "filters" - invalidate all filter cache
            - "stats" - invalidate all statistics cache

            Args:
                pattern: Substring pattern to match in cache keys

            Returns:
                Dictionary with count of invalidated entries
            """
            self._logger.info(f"Invalidating cache entries matching pattern: {pattern}")
            count = await invalidate_cache_by_pattern(pattern)
            self._logger.info(f"Invalidated {count} entries matching '{pattern}'")
            return {
                "success": True,
                "pattern": pattern,
                "invalidated_entries": count,
                "message": f"Successfully invalidated {count} cache entries matching '{pattern}'",
            }
