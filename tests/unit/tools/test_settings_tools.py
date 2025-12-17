"""
Unit tests for SettingsTools.

Tests for project configuration tools including:
- Points (Story Points)
- Statuses (User Story, Task, Issue, Epic)
- Priorities
- Severities
- Issue Types
- Roles
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import FastMCP

from src.application.tools.settings_tools import SettingsTools


@pytest.fixture
def mock_mcp():
    """Create a mock FastMCP instance."""
    mcp = MagicMock(spec=FastMCP)
    mcp.tool = MagicMock(return_value=lambda func: func)
    return mcp


@pytest.fixture
def settings_tools(mock_mcp):
    """Create SettingsTools instance with mock MCP."""
    tools = SettingsTools(mock_mcp)
    return tools


class TestSettingsToolsInit:
    """Tests for SettingsTools initialization."""

    def test_init_creates_instance(self, mock_mcp):
        """Test that SettingsTools initializes correctly."""
        tools = SettingsTools(mock_mcp)
        assert tools.mcp == mock_mcp
        assert tools.client is None

    def test_register_tools_calls_all_registrations(self, mock_mcp):
        """Test that register_tools registers all tool categories."""
        tools = SettingsTools(mock_mcp)
        tools.register_tools()

        # Should have called mcp.tool multiple times (46 tools total)
        assert mock_mcp.tool.call_count >= 40


class TestPointsTools:
    """Tests for points management tools."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Taiga client."""
        client = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_list_points_success(self, settings_tools, mock_client):
        """Test listing points successfully."""
        settings_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value=[
                {"id": 1, "name": "1", "value": 1.0, "order": 1},
                {"id": 2, "name": "2", "value": 2.0, "order": 2},
            ]
        )

        # Register tools first
        settings_tools.register_tools()

        # Call the internal method
        result = await settings_tools._make_request(
            "GET",
            "/points",
            auth_token="test-token",
            params={"project": 123},
        )

        assert len(result) == 2
        assert result[0]["name"] == "1"

    @pytest.mark.asyncio
    async def test_create_point_success(self, settings_tools, mock_client):
        """Test creating a point successfully."""
        settings_tools.set_client(mock_client)
        mock_client.post = AsyncMock(
            return_value={
                "id": 3,
                "name": "5",
                "value": 5.0,
                "order": 3,
            }
        )

        result = await settings_tools._make_request(
            "POST",
            "/points",
            auth_token="test-token",
            json={"project": 123, "name": "5", "value": 5.0, "order": 3},
        )

        assert result["id"] == 3
        assert result["name"] == "5"

    @pytest.mark.asyncio
    async def test_get_point_success(self, settings_tools, mock_client):
        """Test getting a single point."""
        settings_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value={
                "id": 1,
                "name": "1",
                "value": 1.0,
            }
        )

        result = await settings_tools._make_request(
            "GET",
            "/points/1",
            auth_token="test-token",
        )

        assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_update_point_success(self, settings_tools, mock_client):
        """Test updating a point."""
        settings_tools.set_client(mock_client)
        mock_client.patch = AsyncMock(
            return_value={
                "id": 1,
                "name": "updated",
                "value": 10.0,
            }
        )

        result = await settings_tools._make_request(
            "PATCH",
            "/points/1",
            auth_token="test-token",
            json={"name": "updated", "value": 10.0},
        )

        assert result["name"] == "updated"

    @pytest.mark.asyncio
    async def test_delete_point_success(self, settings_tools, mock_client):
        """Test deleting a point."""
        settings_tools.set_client(mock_client)
        mock_client.delete = AsyncMock(return_value=None)

        result = await settings_tools._make_request(
            "DELETE",
            "/points/1",
            auth_token="test-token",
        )

        mock_client.delete.assert_called_once()


class TestUserStoryStatusTools:
    """Tests for user story status tools."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Taiga client."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_list_userstory_statuses_success(self, settings_tools, mock_client):
        """Test listing user story statuses."""
        settings_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value=[
                {"id": 1, "name": "New", "is_closed": False},
                {"id": 2, "name": "Done", "is_closed": True},
            ]
        )

        result = await settings_tools._make_request(
            "GET",
            "/userstory-statuses",
            auth_token="test-token",
            params={"project": 123},
        )

        assert len(result) == 2
        assert result[0]["name"] == "New"

    @pytest.mark.asyncio
    async def test_create_userstory_status_success(self, settings_tools, mock_client):
        """Test creating a user story status."""
        settings_tools.set_client(mock_client)
        mock_client.post = AsyncMock(
            return_value={
                "id": 3,
                "name": "In Progress",
                "color": "#3498db",
                "is_closed": False,
            }
        )

        result = await settings_tools._make_request(
            "POST",
            "/userstory-statuses",
            auth_token="test-token",
            json={
                "project": 123,
                "name": "In Progress",
                "color": "#3498db",
                "is_closed": False,
            },
        )

        assert result["name"] == "In Progress"


class TestTaskStatusTools:
    """Tests for task status tools."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Taiga client."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_list_task_statuses_success(self, settings_tools, mock_client):
        """Test listing task statuses."""
        settings_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value=[
                {"id": 1, "name": "To Do", "is_closed": False},
                {"id": 2, "name": "Complete", "is_closed": True},
            ]
        )

        result = await settings_tools._make_request(
            "GET",
            "/task-statuses",
            auth_token="test-token",
            params={"project": 123},
        )

        assert len(result) == 2


class TestIssueStatusTools:
    """Tests for issue status tools."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Taiga client."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_list_issue_statuses_success(self, settings_tools, mock_client):
        """Test listing issue statuses."""
        settings_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value=[
                {"id": 1, "name": "Open", "is_closed": False},
                {"id": 2, "name": "Closed", "is_closed": True},
            ]
        )

        result = await settings_tools._make_request(
            "GET",
            "/issue-statuses",
            auth_token="test-token",
            params={"project": 123},
        )

        assert len(result) == 2


class TestEpicStatusTools:
    """Tests for epic status tools."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Taiga client."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_list_epic_statuses_success(self, settings_tools, mock_client):
        """Test listing epic statuses."""
        settings_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value=[
                {"id": 1, "name": "Draft", "is_closed": False},
                {"id": 2, "name": "Published", "is_closed": True},
            ]
        )

        result = await settings_tools._make_request(
            "GET",
            "/epic-statuses",
            auth_token="test-token",
            params={"project": 123},
        )

        assert len(result) == 2


class TestPriorityTools:
    """Tests for priority tools."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Taiga client."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_list_priorities_success(self, settings_tools, mock_client):
        """Test listing priorities."""
        settings_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value=[
                {"id": 1, "name": "Low", "color": "#27ae60"},
                {"id": 2, "name": "Normal", "color": "#f39c12"},
                {"id": 3, "name": "High", "color": "#e74c3c"},
            ]
        )

        result = await settings_tools._make_request(
            "GET",
            "/priorities",
            auth_token="test-token",
            params={"project": 123},
        )

        assert len(result) == 3
        assert result[2]["name"] == "High"


class TestSeverityTools:
    """Tests for severity tools."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Taiga client."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_list_severities_success(self, settings_tools, mock_client):
        """Test listing severities."""
        settings_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value=[
                {"id": 1, "name": "Minor", "color": "#27ae60"},
                {"id": 2, "name": "Major", "color": "#e74c3c"},
                {"id": 3, "name": "Critical", "color": "#8e44ad"},
            ]
        )

        result = await settings_tools._make_request(
            "GET",
            "/severities",
            auth_token="test-token",
            params={"project": 123},
        )

        assert len(result) == 3


class TestIssueTypeTools:
    """Tests for issue type tools."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Taiga client."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_list_issue_types_success(self, settings_tools, mock_client):
        """Test listing issue types."""
        settings_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value=[
                {"id": 1, "name": "Bug", "color": "#e74c3c"},
                {"id": 2, "name": "Enhancement", "color": "#3498db"},
                {"id": 3, "name": "Question", "color": "#9b59b6"},
            ]
        )

        result = await settings_tools._make_request(
            "GET",
            "/issue-types",
            auth_token="test-token",
            params={"project": 123},
        )

        assert len(result) == 3
        assert result[0]["name"] == "Bug"


class TestRoleTools:
    """Tests for role tools."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Taiga client."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_list_roles_success(self, settings_tools, mock_client):
        """Test listing roles."""
        settings_tools.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value=[
                {"id": 1, "name": "Developer", "permissions": ["view_project"]},
                {"id": 2, "name": "Manager", "permissions": ["view_project", "admin_project"]},
            ]
        )

        result = await settings_tools._make_request(
            "GET",
            "/roles",
            auth_token="test-token",
            params={"project": 123},
        )

        assert len(result) == 2
        assert result[0]["name"] == "Developer"

    @pytest.mark.asyncio
    async def test_create_role_success(self, settings_tools, mock_client):
        """Test creating a role."""
        settings_tools.set_client(mock_client)
        mock_client.post = AsyncMock(
            return_value={
                "id": 3,
                "name": "QA",
                "permissions": ["view_project", "add_issue"],
            }
        )

        result = await settings_tools._make_request(
            "POST",
            "/roles",
            auth_token="test-token",
            json={
                "project": 123,
                "name": "QA",
                "permissions": ["view_project", "add_issue"],
            },
        )

        assert result["name"] == "QA"


class TestMakeRequest:
    """Tests for the _make_request method."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Taiga client."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_make_request_with_test_client(self, settings_tools, mock_client):
        """Test _make_request uses test client when set."""
        settings_tools.set_client(mock_client)
        mock_client.get = AsyncMock(return_value={"data": "test"})

        result = await settings_tools._make_request(
            "GET",
            "/test-endpoint",
            auth_token="test-token",
        )

        mock_client.get.assert_called_once_with("/test-endpoint")
        assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_make_request_post(self, settings_tools, mock_client):
        """Test _make_request with POST method."""
        settings_tools.set_client(mock_client)
        mock_client.post = AsyncMock(return_value={"created": True})

        result = await settings_tools._make_request(
            "POST",
            "/test-endpoint",
            auth_token="test-token",
            json={"name": "test"},
        )

        mock_client.post.assert_called_once()
        assert result["created"] is True

    @pytest.mark.asyncio
    async def test_make_request_put(self, settings_tools, mock_client):
        """Test _make_request with PUT method."""
        settings_tools.set_client(mock_client)
        mock_client.put = AsyncMock(return_value={"updated": True})

        result = await settings_tools._make_request(
            "PUT",
            "/test-endpoint",
            auth_token="test-token",
            json={"name": "updated"},
        )

        mock_client.put.assert_called_once()
        assert result["updated"] is True

    @pytest.mark.asyncio
    async def test_make_request_patch(self, settings_tools, mock_client):
        """Test _make_request with PATCH method."""
        settings_tools.set_client(mock_client)
        mock_client.patch = AsyncMock(return_value={"patched": True})

        result = await settings_tools._make_request(
            "PATCH",
            "/test-endpoint",
            auth_token="test-token",
            json={"field": "value"},
        )

        mock_client.patch.assert_called_once()
        assert result["patched"] is True

    @pytest.mark.asyncio
    async def test_make_request_delete(self, settings_tools, mock_client):
        """Test _make_request with DELETE method."""
        settings_tools.set_client(mock_client)
        mock_client.delete = AsyncMock(return_value=None)

        result = await settings_tools._make_request(
            "DELETE",
            "/test-endpoint",
            auth_token="test-token",
        )

        mock_client.delete.assert_called_once()
