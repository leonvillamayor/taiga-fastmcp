"""
Unit tests for SearchTools.

Tests for search and timeline functionality including:
- Global search across project items
- User activity timeline
- Project activity timeline
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastmcp import FastMCP

from src.application.tools.search_tools import SearchTools


@pytest.fixture
def mock_mcp():
    """Create a mock FastMCP instance."""
    mcp = MagicMock(spec=FastMCP)
    mcp.tool = MagicMock(return_value=lambda func: func)
    return mcp


@pytest.fixture
def search_tools(mock_mcp):
    """Create SearchTools instance with mock MCP."""
    tools = SearchTools(mock_mcp)
    return tools


@pytest.fixture
def mock_client():
    """Create mock Taiga client."""
    return AsyncMock()


class TestSearchToolsInit:
    """Tests for SearchTools initialization."""

    def test_init_creates_instance(self, mock_mcp):
        """Test that SearchTools initializes correctly."""
        tools = SearchTools(mock_mcp)
        assert tools.mcp == mock_mcp
        assert tools.client is None

    def test_register_tools_calls_registrations(self, mock_mcp):
        """Test that register_tools registers all tools."""
        tools = SearchTools(mock_mcp)
        tools.register_tools()

        # Should have called mcp.tool 3 times (search + 2 timeline tools)
        assert mock_mcp.tool.call_count >= 3


class TestSearchTool:
    """Tests for the search tool."""

    @pytest.mark.asyncio
    async def test_search_success(self, search_tools, mock_client):
        """Test successful search."""
        search_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value={
                "userstories": [
                    {"id": 1, "ref": 10, "subject": "Login feature"},
                    {"id": 2, "ref": 11, "subject": "Login validation"},
                ],
                "issues": [
                    {"id": 3, "ref": 5, "subject": "Login bug"},
                ],
                "tasks": [],
                "wikipages": [],
                "epics": [],
            }
        )

        search_tools.register_tools()
        result = await search_tools.search(auth_token="test-token", project_id=123, text="login")

        assert result["count"] == 3
        assert len(result["userstories"]) == 2
        assert len(result["issues"]) == 1
        assert len(result["tasks"]) == 0
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_empty_results(self, search_tools, mock_client):
        """Test search with no results."""
        search_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value={
                "userstories": [],
                "issues": [],
                "tasks": [],
                "wikipages": [],
                "epics": [],
            }
        )

        search_tools.register_tools()
        result = await search_tools.search(
            auth_token="test-token", project_id=123, text="nonexistent"
        )

        assert result["count"] == 0
        for category in ["userstories", "issues", "tasks", "wikipages", "epics"]:
            assert result[category] == []

    @pytest.mark.asyncio
    async def test_search_with_count_limit(self, search_tools, mock_client):
        """Test search respects count limit."""
        search_tools.set_client(mock_client)
        # Return many results
        mock_client.get = AsyncMock(
            return_value={
                "userstories": [{"id": i} for i in range(50)],
                "issues": [],
                "tasks": [],
                "wikipages": [],
                "epics": [],
            }
        )

        search_tools.register_tools()
        result = await search_tools.search(
            auth_token="test-token", project_id=123, text="test", count=5
        )

        # Should be limited to 5 results per category
        assert len(result["userstories"]) == 5

    @pytest.mark.asyncio
    async def test_search_handles_missing_categories(self, search_tools, mock_client):
        """Test search handles response with missing categories."""
        search_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value={
                "userstories": [{"id": 1}],
                # Other categories missing from response
            }
        )

        search_tools.register_tools()
        result = await search_tools.search(auth_token="test-token", project_id=123, text="test")

        assert len(result["userstories"]) == 1
        assert result["issues"] == []
        assert result["tasks"] == []


class TestUserTimelineTool:
    """Tests for user timeline tool."""

    @pytest.mark.asyncio
    async def test_get_user_timeline_success(self, search_tools, mock_client):
        """Test getting user timeline successfully."""
        search_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value=[
                {
                    "id": 1,
                    "content_type": {"model": "userstory"},
                    "object_id": 123,
                    "event_type": "create",
                    "data": {"project": {"id": 1, "name": "Test Project"}},
                    "created": "2025-01-15T10:00:00Z",
                },
                {
                    "id": 2,
                    "content_type": {"model": "issue"},
                    "object_id": 456,
                    "event_type": "change",
                    "data": {"project": {"id": 1, "name": "Test Project"}},
                    "created": "2025-01-15T11:00:00Z",
                },
            ]
        )

        search_tools.register_tools()
        result = await search_tools.get_user_timeline(auth_token="test-token", user_id=789)

        assert len(result) == 2
        assert result[0]["content_type"] == "userstory"
        assert result[0]["event_type"] == "create"
        assert result[1]["content_type"] == "issue"
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_timeline_empty(self, search_tools, mock_client):
        """Test getting empty user timeline."""
        search_tools.set_client(mock_client)
        mock_client.get = AsyncMock(return_value=[])

        search_tools.register_tools()
        result = await search_tools.get_user_timeline(auth_token="test-token", user_id=789)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_user_timeline_with_pagination(self, search_tools, mock_client):
        """Test getting user timeline with pagination."""
        search_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value=[
                {
                    "id": 10,
                    "content_type": "task",
                    "object_id": 100,
                    "event_type": "create",
                    "data": {},
                    "created": "2025-01-15",
                },
            ]
        )

        search_tools.register_tools()
        result = await search_tools.get_user_timeline(auth_token="test-token", user_id=789, page=2)

        assert len(result) == 1
        mock_client.get.assert_called_once_with("/timeline/user/789", params={"page": 2})


class TestProjectTimelineTool:
    """Tests for project timeline tool."""

    @pytest.mark.asyncio
    async def test_get_project_timeline_success(self, search_tools, mock_client):
        """Test getting project timeline successfully."""
        search_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value=[
                {
                    "id": 1,
                    "content_type": {"model": "userstory"},
                    "object_id": 123,
                    "event_type": "create",
                    "data": {"user": {"id": 1, "username": "developer1"}},
                    "created": "2025-01-15T10:00:00Z",
                },
                {
                    "id": 2,
                    "content_type": {"model": "task"},
                    "object_id": 456,
                    "event_type": "comment",
                    "data": {"user": {"id": 2, "username": "manager1"}},
                    "created": "2025-01-15T11:00:00Z",
                },
            ]
        )

        search_tools.register_tools()
        result = await search_tools.get_project_timeline(auth_token="test-token", project_id=100)

        assert len(result) == 2
        assert result[0]["content_type"] == "userstory"
        assert result[0]["event_type"] == "create"
        assert result[1]["content_type"] == "task"
        assert result[1]["event_type"] == "comment"
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_project_timeline_empty(self, search_tools, mock_client):
        """Test getting empty project timeline."""
        search_tools.set_client(mock_client)
        mock_client.get = AsyncMock(return_value=[])

        search_tools.register_tools()
        result = await search_tools.get_project_timeline(auth_token="test-token", project_id=100)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_project_timeline_with_pagination(self, search_tools, mock_client):
        """Test getting project timeline with pagination."""
        search_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value=[
                {
                    "id": 5,
                    "content_type": "epic",
                    "object_id": 50,
                    "event_type": "delete",
                    "data": {},
                    "created": "2025-01-15",
                },
            ]
        )

        search_tools.register_tools()
        result = await search_tools.get_project_timeline(
            auth_token="test-token", project_id=100, page=3
        )

        assert len(result) == 1
        mock_client.get.assert_called_once_with("/timeline/project/100", params={"page": 3})

    @pytest.mark.asyncio
    async def test_get_project_timeline_handles_string_content_type(
        self, search_tools, mock_client
    ):
        """Test timeline handles string content_type instead of dict."""
        search_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value=[
                {
                    "id": 1,
                    "content_type": "userstory",  # String instead of dict
                    "object_id": 123,
                    "event_type": "create",
                    "data": {},
                    "created": "2025-01-15T10:00:00Z",
                },
            ]
        )

        search_tools.register_tools()
        result = await search_tools.get_project_timeline(auth_token="test-token", project_id=100)

        assert len(result) == 1
        assert result[0]["content_type"] == "userstory"


class TestSetClient:
    """Tests for the set_client method."""

    def test_set_client(self, search_tools, mock_client):
        """Test that set_client injects the client."""
        assert search_tools.client is None
        search_tools.set_client(mock_client)
        assert search_tools.client == mock_client
