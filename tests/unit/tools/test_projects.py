"""
Unit tests for ProjectTools class.

Testing strategy:
1. Test initialization
2. Test each tool method with success cases
3. Test each tool method with error cases
4. Mock all external dependencies (TaigaAPIClient, TaigaConfig)
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError as MCPError

from src.application.tools.project_tools import ProjectTools
from src.domain.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    ResourceNotFoundError,
    TaigaAPIError,
)


@pytest.fixture
def mock_mcp() -> None:
    """Create a mock FastMCP instance."""
    mcp = Mock(spec=FastMCP)
    mcp.tool = Mock(side_effect=lambda **kwargs: lambda func: func)
    return mcp


@pytest.fixture
def mock_config() -> None:
    """Create a mock TaigaConfig."""
    with patch("src.application.tools.project_tools.TaigaConfig") as mock:
        config = Mock()
        mock.return_value = config
        yield config


@pytest.fixture
def project_tools(mock_mcp, mock_config) -> None:
    """Create a ProjectTools instance with mocked dependencies."""
    tools = ProjectTools(mock_mcp)
    tools.register_tools()
    return tools


class TestProjectToolsInitialization:
    """Tests for ProjectTools initialization."""

    def test_init(self, mock_mcp) -> None:
        """Test ProjectTools initialization."""
        tools = ProjectTools(mock_mcp)
        assert tools.mcp == mock_mcp
        assert tools.config is not None

    def test_register_tools(self, project_tools, mock_mcp) -> None:
        """Test that register_tools registers all expected tools."""
        # Verify tool decorator was called for each tool
        assert mock_mcp.tool.call_count >= 6  # At least 6 tools should be registered

        # Verify tool methods are accessible
        assert hasattr(project_tools, "list_projects")
        assert hasattr(project_tools, "get_project")
        assert hasattr(project_tools, "create_project")
        assert hasattr(project_tools, "update_project")
        assert hasattr(project_tools, "delete_project")
        assert hasattr(project_tools, "get_project_stats")


class TestListProjects:
    """Tests for list_projects tool."""

    @pytest.mark.asyncio
    async def test_list_projects_success(self, project_tools) -> None:
        """Test successful project listing."""
        # Mock API response
        mock_projects = [
            {
                "id": 1,
                "name": "Project 1",
                "slug": "project-1",
                "description": "Description 1",
                "is_private": True,
                "owner": {"username": "user1"},
                "created_date": "2024-01-01",
                "modified_date": "2024-01-02",
                "total_story_points": 100,
                "total_milestones": 5,
            },
            {
                "id": 2,
                "name": "Project 2",
                "slug": "project-2",
                "description": "Description 2",
                "is_private": False,
                "owner": {"username": "user2"},
                "created_date": "2024-01-03",
                "modified_date": "2024-01-04",
                "total_story_points": 50,
                "total_milestones": 3,
            },
        ]

        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_projects
            mock_client_class.return_value = mock_client

            result = await project_tools.list_projects(
                auth_token="test-token", member_id=1, is_private=True, is_backlog_activated=True
            )

            # Verify API call
            mock_client.get.assert_called_once_with(
                "/projects",
                params={
                    "member": 1,
                    "is_private": True,
                    "is_backlog_activated": True,
                    "page": 1,
                    "page_size": 100,
                },
            )

            # Verify result
            assert len(result) == 2
            assert result[0]["id"] == 1
            assert result[0]["name"] == "Project 1"
            assert result[0]["owner"] == {"username": "user1"}
            assert result[1]["id"] == 2
            assert result[1]["is_private"] is False

    @pytest.mark.asyncio
    async def test_list_projects_with_member_filter(self, project_tools) -> None:
        """Test listing projects filtered by member."""
        mock_projects = []

        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_projects
            mock_client_class.return_value = mock_client

            result = await project_tools.list_projects(auth_token="test-token", member_id=2)

            # Verify API call with member filter
            mock_client.get.assert_called_once_with(
                "/projects", params={"member": 2, "page": 1, "page_size": 100}
            )

            assert result == []

    @pytest.mark.asyncio
    async def test_list_projects_no_filters(self, project_tools) -> None:
        """Test listing projects without filters."""
        mock_projects = [{"id": 1, "name": "Project", "owner": {}}]

        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_projects
            mock_client_class.return_value = mock_client

            result = await project_tools.list_projects(auth_token="test-token")

            mock_client.get.assert_called_once_with(
                "/projects", params={"page": 1, "page_size": 100}
            )

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_projects_authentication_error(self, project_tools) -> None:
        """Test list_projects with authentication error."""
        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = AuthenticationError("Invalid token")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Authentication failed"):
                await project_tools.list_projects(auth_token="invalid-token")

    @pytest.mark.asyncio
    async def test_list_projects_api_error(self, project_tools) -> None:
        """Test list_projects with API error."""
        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = TaigaAPIError("Server error")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="API error: Server error"):
                await project_tools.list_projects(auth_token="test-token")

    @pytest.mark.asyncio
    async def test_list_projects_unexpected_error(self, project_tools) -> None:
        """Test list_projects with unexpected error."""
        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = Exception("Unexpected")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Unexpected error: Unexpected"):
                await project_tools.list_projects(auth_token="test-token")


class TestGetProject:
    """Tests for get_project tool."""

    @pytest.mark.asyncio
    async def test_get_project_success(self, project_tools) -> None:
        """Test successful project retrieval."""
        mock_project = {
            "id": 1,
            "name": "Test Project",
            "slug": "test-project",
            "description": "A test project",
            "is_private": True,
            "owner": {"username": "owner1"},
            "created_date": "2024-01-01",
            "modified_date": "2024-01-02",
            "is_backlog_activated": True,
            "is_kanban_activated": False,
            "is_wiki_activated": True,
            "is_issues_activated": True,
            "total_story_points": 100,
            "total_milestones": 5,
            "tags": ["tag1", "tag2"],
            "members": [
                {
                    "id": 1,
                    "username": "user1",
                    "full_name_display": "User One",
                    "role_name": "Developer",
                },
                {
                    "id": 2,
                    "username": "user2",
                    "full_name_display": "User Two",
                    "role_name": "Designer",
                },
            ],
        }

        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_project
            mock_client_class.return_value = mock_client

            result = await project_tools.get_project(auth_token="test-token", project_id=1)

            mock_client.get.assert_called_once_with("/projects/1")

            assert result["id"] == 1
            assert result["name"] == "Test Project"
            assert result["owner"] == {"username": "owner1"}
            assert result["is_backlog_activated"] is True
            assert result["is_kanban_activated"] is False
            assert len(result["members"]) == 2
            assert result["tags"] == ["tag1", "tag2"]

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, project_tools) -> None:
        """Test get_project with non-existent project."""
        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = ResourceNotFoundError("Not found")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Project not found"):
                await project_tools.get_project(auth_token="test-token", project_id=999)

    @pytest.mark.asyncio
    async def test_get_project_permission_denied(self, project_tools) -> None:
        """Test get_project with permission denied."""
        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = PermissionDeniedError("No access")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="No permission to access project"):
                await project_tools.get_project(auth_token="test-token", project_id=1)

    @pytest.mark.asyncio
    async def test_get_project_authentication_error(self, project_tools) -> None:
        """Test get_project with authentication error."""
        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = AuthenticationError("Invalid token")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Authentication failed"):
                await project_tools.get_project(auth_token="invalid-token", project_id=1)


class TestCreateProject:
    """Tests for create_project tool."""

    @pytest.mark.asyncio
    async def test_create_project_minimal(self, project_tools) -> None:
        """Test creating a project with minimal data."""
        mock_response = {
            "id": 1,
            "name": "New Project",
            "slug": "new-project",
            "description": "",
            "is_private": True,
        }

        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await project_tools.create_project(auth_token="test-token", name="New Project")

            # Verify post was called with project data
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "/projects"
            assert call_args[1]["data"]["name"] == "New Project"

            assert result["id"] == 1
            assert result["name"] == "New Project"
            assert "Successfully created project" in result["message"]

    @pytest.mark.asyncio
    async def test_create_project_full(self, project_tools) -> None:
        """Test creating a project with all fields."""
        mock_response = {
            "id": 2,
            "name": "Full Project",
            "slug": "full-project",
            "description": "Full description",
            "is_private": False,
        }

        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await project_tools.create_project(
                auth_token="test-token",
                name="Full Project",
                description="Full description",
                is_private=False,
                is_backlog_activated=False,
                is_kanban_activated=True,
                is_wiki_activated=False,
                is_issues_activated=True,
                tags=["tag1", "tag2"],
            )

            # Verify post was called
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "/projects"
            assert call_args[1]["data"]["name"] == "Full Project"
            assert call_args[1]["data"]["description"] == "Full description"
            assert call_args[1]["data"]["is_private"] is False

            assert result["id"] == 2
            assert result["is_private"] is False

    @pytest.mark.asyncio
    async def test_create_project_auth_error(self, project_tools) -> None:
        """Test create_project with authentication error."""
        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.side_effect = AuthenticationError("Invalid token")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Authentication failed"):
                await project_tools.create_project(auth_token="invalid-token", name="Project")

    @pytest.mark.asyncio
    async def test_create_project_api_error(self, project_tools) -> None:
        """Test create_project with API error."""
        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.side_effect = TaigaAPIError("Validation error")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Failed to create project: Validation error"):
                await project_tools.create_project(auth_token="test-token", name="Project")


class TestUpdateProject:
    """Tests for update_project tool."""

    @pytest.mark.asyncio
    async def test_update_project_single_field(self, project_tools) -> None:
        """Test updating a single field."""
        mock_response = {
            "id": 1,
            "name": "Updated Name",
            "slug": "updated-name",
            "description": "Original description",
            "is_private": True,
        }

        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.patch.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await project_tools.update_project(
                auth_token="test-token", project_id=1, name="Updated Name"
            )

            mock_client.patch.assert_called_once_with("/projects/1", data={"name": "Updated Name"})

            assert result["name"] == "Updated Name"
            assert "Successfully updated project" in result["message"]

    @pytest.mark.asyncio
    async def test_update_project_multiple_fields(self, project_tools) -> None:
        """Test updating multiple fields."""
        mock_response = {
            "id": 1,
            "name": "New Name",
            "slug": "new-name",
            "description": "New description",
            "is_private": False,
        }

        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.patch.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await project_tools.update_project(
                auth_token="test-token",
                project_id=1,
                name="New Name",
                description="New description",
                is_private=False,
                is_backlog_activated=True,
                is_kanban_activated=False,
                is_wiki_activated=True,
                is_issues_activated=False,
            )

            expected_data = {
                "name": "New Name",
                "description": "New description",
                "is_private": False,
                "is_backlog_activated": True,
                "is_kanban_activated": False,
                "is_wiki_activated": True,
                "is_issues_activated": False,
            }

            mock_client.patch.assert_called_once_with("/projects/1", data=expected_data)

            assert result["is_private"] is False

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, project_tools) -> None:
        """Test update_project with non-existent project."""
        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.patch.side_effect = ResourceNotFoundError("Not found")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Project 999 not found"):
                await project_tools.update_project(
                    auth_token="test-token", project_id=999, name="New"
                )

    @pytest.mark.asyncio
    async def test_update_project_permission_denied(self, project_tools) -> None:
        """Test update_project with permission denied."""
        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.patch.side_effect = PermissionDeniedError("No access")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="No permission to update project 1"):
                await project_tools.update_project(
                    auth_token="test-token", project_id=1, name="New"
                )


class TestDeleteProject:
    """Tests for delete_project tool."""

    @pytest.mark.asyncio
    async def test_delete_project_success(self, project_tools) -> None:
        """Test successful project deletion."""
        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.delete.return_value = True
            mock_client_class.return_value = mock_client

            result = await project_tools.delete_project(auth_token="test-token", project_id=1)

            mock_client.delete.assert_called_once_with("/projects/1")
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, project_tools) -> None:
        """Test delete_project with non-existent project."""
        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.delete.side_effect = ResourceNotFoundError("Not found")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Project 999 not found"):
                await project_tools.delete_project(auth_token="test-token", project_id=999)

    @pytest.mark.asyncio
    async def test_delete_project_permission_denied(self, project_tools) -> None:
        """Test delete_project with permission denied."""
        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.delete.side_effect = PermissionDeniedError("No access")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="No permission to delete project 1"):
                await project_tools.delete_project(auth_token="test-token", project_id=1)


class TestGetProjectStats:
    """Tests for get_project_stats tool."""

    @pytest.mark.asyncio
    async def test_get_project_stats_success(self, project_tools) -> None:
        """Test successful project stats retrieval."""
        mock_stats = {
            "total_milestones": 10,
            "total_points": 200,
            "closed_points": 150,
            "defined_points": {"UX": 50, "Backend": 100},
            "assigned_points": {"UX": 40, "Backend": 80},
            "total_userstories": 50,
            "total_issues": 30,
            "closed_issues": 20,
            "speed": 25,
        }

        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_stats
            mock_client_class.return_value = mock_client

            result = await project_tools.get_project_stats(auth_token="test-token", project_id=1)

            mock_client.get.assert_called_once_with("/projects/1/stats")

            assert result["total_milestones"] == 10
            assert result["total_points"] == 200
            assert result["closed_points"] == 150
            assert result["total_userstories"] == 50
            assert result["total_issues"] == 30

    @pytest.mark.asyncio
    async def test_get_project_stats_with_missing_fields(self, project_tools) -> None:
        """Test get_project_stats with missing fields in response."""
        mock_stats = {
            "total_milestones": 5,
            "total_points": 100,
            # Other fields missing
        }

        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_stats
            mock_client_class.return_value = mock_client

            result = await project_tools.get_project_stats(auth_token="test-token", project_id=1)

            # Present fields are included
            assert result["total_milestones"] == 5
            assert result["total_points"] == 100
            # Missing fields are excluded by model_dump(exclude_none=True)
            assert "closed_points" not in result
            assert "defined_points" not in result
            assert "total_issues" not in result

    @pytest.mark.asyncio
    async def test_get_project_stats_not_found(self, project_tools) -> None:
        """Test get_project_stats with non-existent project."""
        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = ResourceNotFoundError("Not found")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Project 999 not found"):
                await project_tools.get_project_stats(auth_token="test-token", project_id=999)

    @pytest.mark.asyncio
    async def test_get_project_stats_unexpected_error(self, project_tools) -> None:
        """Test get_project_stats with unexpected error."""
        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = Exception("Unexpected error")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Unexpected error"):
                await project_tools.get_project_stats(auth_token="test-token", project_id=1)

    @pytest.mark.asyncio
    async def test_get_project_stats_authentication_error(self, project_tools) -> None:
        """Test get_project_stats with authentication error."""
        with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = AuthenticationError("Invalid token")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Authentication failed"):
                await project_tools.get_project_stats(auth_token="invalid-token", project_id=1)
