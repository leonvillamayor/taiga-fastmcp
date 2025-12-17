"""
Unit tests for TaigaResources.

Tests for MCP resources including:
- Project statistics
- Project modules configuration
- Project timeline
- Project members
- User information
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastmcp import FastMCP

from src.application.resources.taiga_resources import TaigaResources


@pytest.fixture
def mock_mcp():
    """Create a mock FastMCP instance."""
    mcp = MagicMock(spec=FastMCP)
    mcp.resource = MagicMock(return_value=lambda func: func)
    return mcp


@pytest.fixture
def taiga_resources(mock_mcp):
    """Create TaigaResources instance with mock MCP."""
    resources = TaigaResources(mock_mcp)
    return resources


@pytest.fixture
def mock_client():
    """Create mock Taiga client."""
    return AsyncMock()


class TestTaigaResourcesInit:
    """Tests for TaigaResources initialization."""

    def test_init_creates_instance(self, mock_mcp):
        """Test that TaigaResources initializes correctly."""
        resources = TaigaResources(mock_mcp)
        assert resources.mcp == mock_mcp
        assert resources.client is None

    def test_register_resources_calls_registrations(self, mock_mcp):
        """Test that register_resources registers all resources."""
        resources = TaigaResources(mock_mcp)
        resources.register_resources()

        # Should have called mcp.resource multiple times
        assert mock_mcp.resource.call_count >= 5


class TestProjectStatsResource:
    """Tests for project stats resource."""

    @pytest.mark.asyncio
    async def test_get_project_stats_success(self, taiga_resources, mock_client):
        """Test getting project statistics successfully."""
        taiga_resources.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value={
                "total_points": 100,
                "closed_points": 75,
                "total_userstories": 20,
                "closed_userstories": 15,
                "total_tasks": 50,
                "closed_tasks": 40,
                "total_issues": 10,
                "closed_issues": 8,
            }
        )

        taiga_resources.register_resources()
        result = await taiga_resources.get_project_stats(project_id=123)

        assert result["total_points"] == 100
        assert result["closed_points"] == 75
        mock_client.get.assert_called_once_with("/projects/123/stats")


class TestProjectModulesResource:
    """Tests for project modules resource."""

    @pytest.mark.asyncio
    async def test_get_project_modules_success(self, taiga_resources, mock_client):
        """Test getting project modules configuration."""
        taiga_resources.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value={
                "is_backlog_activated": True,
                "is_kanban_activated": False,
                "is_wiki_activated": True,
                "is_issues_activated": True,
                "is_epics_activated": True,
                "videoconferences": "jitsi",
                "videoconferences_extra_data": None,
                "total_milestones": 5,
                "total_story_points": 200,
            }
        )

        taiga_resources.register_resources()
        result = await taiga_resources.get_project_modules(project_id=123)

        assert result["is_backlog_activated"] is True
        assert result["is_kanban_activated"] is False
        assert result["is_wiki_activated"] is True
        assert result["total_milestones"] == 5
        mock_client.get.assert_called_once_with("/projects/123")

    @pytest.mark.asyncio
    async def test_get_project_modules_with_defaults(self, taiga_resources, mock_client):
        """Test modules with missing values uses defaults."""
        taiga_resources.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value={
                "name": "Test Project",
                # Missing module flags
            }
        )

        taiga_resources.register_resources()
        result = await taiga_resources.get_project_modules(project_id=123)

        assert result["is_backlog_activated"] is False
        assert result["is_kanban_activated"] is False
        assert result["total_milestones"] == 0


class TestProjectTimelineResource:
    """Tests for project timeline resource."""

    @pytest.mark.asyncio
    async def test_get_project_timeline_success(self, taiga_resources, mock_client):
        """Test getting project timeline."""
        taiga_resources.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value=[
                {
                    "id": 1,
                    "content_type": {"model": "userstory"},
                    "event_type": "create",
                    "created": "2025-01-15T10:00:00Z",
                    "data": {"subject": "New feature"},
                },
                {
                    "id": 2,
                    "content_type": {"model": "task"},
                    "event_type": "change",
                    "created": "2025-01-15T11:00:00Z",
                    "data": {"subject": "Task update"},
                },
            ]
        )

        taiga_resources.register_resources()
        result = await taiga_resources.get_project_timeline_resource(project_id=123)

        assert len(result) == 2
        assert result[0]["content_type"] == "userstory"
        assert result[0]["event_type"] == "create"
        assert result[1]["content_type"] == "task"

    @pytest.mark.asyncio
    async def test_get_project_timeline_empty(self, taiga_resources, mock_client):
        """Test getting empty project timeline."""
        taiga_resources.set_client(mock_client)
        mock_client.get = AsyncMock(return_value=[])

        taiga_resources.register_resources()
        result = await taiga_resources.get_project_timeline_resource(project_id=123)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_project_timeline_limits_results(self, taiga_resources, mock_client):
        """Test timeline limits to 50 events."""
        taiga_resources.set_client(mock_client)
        # Return more than 50 events
        mock_client.get = AsyncMock(
            return_value=[
                {
                    "id": i,
                    "content_type": "task",
                    "event_type": "change",
                    "created": "2025-01-15",
                    "data": {},
                }
                for i in range(100)
            ]
        )

        taiga_resources.register_resources()
        result = await taiga_resources.get_project_timeline_resource(project_id=123)

        assert len(result) == 50


class TestProjectMembersResource:
    """Tests for project members resource."""

    @pytest.mark.asyncio
    async def test_get_project_members_success(self, taiga_resources, mock_client):
        """Test getting project members."""
        taiga_resources.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value=[
                {
                    "id": 1,
                    "user": 10,
                    "role": 1,
                    "role_name": "Product Owner",
                    "full_name": "John Doe",
                    "is_admin": True,
                    "is_active": True,
                },
                {
                    "id": 2,
                    "user": 20,
                    "role": 2,
                    "role_name": "Developer",
                    "full_name": "Jane Smith",
                    "is_admin": False,
                    "is_active": True,
                },
            ]
        )

        taiga_resources.register_resources()
        result = await taiga_resources.get_project_members(project_id=123)

        assert len(result) == 2
        assert result[0]["full_name"] == "John Doe"
        assert result[0]["is_admin"] is True
        assert result[1]["role_name"] == "Developer"
        mock_client.get.assert_called_once_with("/memberships", params={"project": 123})

    @pytest.mark.asyncio
    async def test_get_project_members_empty(self, taiga_resources, mock_client):
        """Test getting empty members list."""
        taiga_resources.set_client(mock_client)
        mock_client.get = AsyncMock(return_value=[])

        taiga_resources.register_resources()
        result = await taiga_resources.get_project_members(project_id=123)

        assert result == []


class TestCurrentUserResource:
    """Tests for current user resource."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, taiga_resources, mock_client):
        """Test getting current user info."""
        taiga_resources.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value={
                "id": 1,
                "username": "testuser",
                "full_name": "Test User",
                "full_name_display": "Test User (@testuser)",
                "email": "test@example.com",
                "bio": "Developer",
                "photo": "https://example.com/photo.jpg",
                "lang": "en",
                "timezone": "UTC",
                "is_active": True,
                "max_private_projects": 10,
                "max_public_projects": 100,
                "total_private_projects": 2,
                "total_public_projects": 5,
            }
        )

        taiga_resources.register_resources()
        result = await taiga_resources.get_current_user()

        assert result["username"] == "testuser"
        assert result["full_name"] == "Test User"
        assert result["email"] == "test@example.com"
        assert result["is_active"] is True
        mock_client.get.assert_called_once_with("/users/me")


class TestUserStatsResource:
    """Tests for user stats resource."""

    @pytest.mark.asyncio
    async def test_get_user_stats_success(self, taiga_resources, mock_client):
        """Test getting user statistics."""
        taiga_resources.set_client(mock_client)
        mock_client.get = AsyncMock(
            return_value={
                "total_num_projects": 5,
                "total_num_contacts": 20,
                "total_num_closed_userstories": 100,
                "roles": ["Developer", "Product Owner"],
            }
        )

        taiga_resources.register_resources()
        result = await taiga_resources.get_user_stats(user_id=123)

        assert result["total_num_projects"] == 5
        assert result["total_num_closed_userstories"] == 100
        mock_client.get.assert_called_once_with("/users/123/stats")


class TestSetClient:
    """Tests for the set_client method."""

    def test_set_client(self, taiga_resources, mock_client):
        """Test that set_client injects the client."""
        assert taiga_resources.client is None
        taiga_resources.set_client(mock_client)
        assert taiga_resources.client == mock_client
