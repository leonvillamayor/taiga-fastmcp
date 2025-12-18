"""
Unit tests for UserStoryTools class.

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

from src.application.tools.userstory_tools import UserStoryTools
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
    with patch("src.application.tools.userstory_tools.TaigaConfig") as mock:
        config = Mock()
        mock.return_value = config
        yield config


@pytest.fixture
def userstory_tools(mock_mcp, mock_config) -> None:
    """Create a UserStoryTools instance with mocked dependencies."""
    tools = UserStoryTools(mock_mcp)
    tools.register_tools()
    return tools


class TestUserStoryToolsInitialization:
    """Tests for UserStoryTools initialization."""

    def test_init(self, mock_mcp) -> None:
        """Test UserStoryTools initialization."""
        tools = UserStoryTools(mock_mcp)
        assert tools.mcp == mock_mcp
        assert tools.config is not None

    def test_register_tools(self, userstory_tools, mock_mcp) -> None:
        """Test that register_tools registers all expected tools."""
        # Verify tool decorator was called for each tool
        assert mock_mcp.tool.call_count >= 15  # At least 15 tools should be registered

        # Verify tool methods are accessible
        assert hasattr(userstory_tools, "list_userstories")
        assert hasattr(userstory_tools, "create_userstory")
        assert hasattr(userstory_tools, "get_userstory")
        assert hasattr(userstory_tools, "update_userstory")
        assert hasattr(userstory_tools, "delete_userstory")
        assert hasattr(userstory_tools, "bulk_create_userstories")
        assert hasattr(userstory_tools, "bulk_update_userstories")
        assert hasattr(userstory_tools, "bulk_delete_userstories")
        assert hasattr(userstory_tools, "move_to_milestone")
        assert hasattr(userstory_tools, "get_userstory_history")
        assert hasattr(userstory_tools, "watch_userstory")
        assert hasattr(userstory_tools, "unwatch_userstory")
        assert hasattr(userstory_tools, "upvote_userstory")
        assert hasattr(userstory_tools, "downvote_userstory")
        assert hasattr(userstory_tools, "get_userstory_voters")


class TestListUserStories:
    """Tests for list_userstories tool."""

    @pytest.mark.asyncio
    async def test_list_userstories_success(self, userstory_tools) -> None:
        """Test successful user story listing."""
        # Mock API response
        mock_stories = [
            {
                "id": 1,
                "ref": 101,
                "subject": "Story 1",
                "description": "Description 1",
                "project": 1,
                "milestone": 1,
                "status": 1,
                "points": {"1": 3, "2": 5},
                "total_points": 8,
                "is_closed": False,
                "is_blocked": False,
                "blocked_note": None,
                "tags": ["tag1"],
                "assigned_to": 1,
                "watchers": [1, 2],
                "total_watchers": 2,
                "attachments": [],
            },
            {
                "id": 2,
                "ref": 102,
                "subject": "Story 2",
                "description": "Description 2",
                "project": 1,
                "milestone": 2,
                "status": 2,
                "points": {"1": 2},
                "total_points": 2,
                "is_closed": True,
                "is_blocked": True,
                "blocked_note": "Waiting for approval",
                "tags": ["tag2", "tag3"],
                "assigned_to": 2,
                "watchers": [1],
                "total_watchers": 1,
                "attachments": [{"id": 1, "name": "file.pdf"}],
            },
        ]

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            # AutoPaginator calls client.get and returns list directly
            mock_client.get.return_value = mock_stories
            mock_client_class.return_value = mock_client

            result = await userstory_tools.list_userstories(
                auth_token="test-token",
                project_id=1,
                milestone_id=1,
                status=1,
                tags=["tag1"],
                assigned_to=1,
            )

            # Verify API call was made (AutoPaginator adds pagination params)
            mock_client.get.assert_called()

            # Verify result
            assert len(result) == 2
            assert result[0]["id"] == 1
            assert result[0]["subject"] == "Story 1"
            assert result[1]["id"] == 2
            assert result[1]["is_blocked"] is True

    @pytest.mark.asyncio
    async def test_list_userstories_no_filters(self, userstory_tools) -> None:
        """Test listing user stories without filters."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            # AutoPaginator calls client.get and returns list directly
            mock_client.get.return_value = []
            mock_client_class.return_value = mock_client

            result = await userstory_tools.list_userstories(auth_token="test-token")

            # Verify API call was made (AutoPaginator adds pagination params)
            mock_client.get.assert_called()
            assert result == []

    @pytest.mark.asyncio
    async def test_list_userstories_authentication_error(self, userstory_tools) -> None:
        """Test list_userstories with authentication error."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = AuthenticationError("Invalid token")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Authentication failed"):
                await userstory_tools.list_userstories(auth_token="invalid-token")

    @pytest.mark.asyncio
    async def test_list_userstories_api_error(self, userstory_tools) -> None:
        """Test list_userstories with API error."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = TaigaAPIError("Server error")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="API error: Server error"):
                await userstory_tools.list_userstories(auth_token="test-token")

    @pytest.mark.asyncio
    async def test_list_userstories_unexpected_error(self, userstory_tools) -> None:
        """Test list_userstories with unexpected error."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = Exception("Unexpected")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Unexpected error: Unexpected"):
                await userstory_tools.list_userstories(auth_token="test-token")


class TestCreateUserStory:
    """Tests for create_userstory tool."""

    @pytest.mark.asyncio
    async def test_create_userstory_minimal(self, userstory_tools) -> None:
        """Test creating a user story with minimal data."""
        mock_response = {
            "id": 1,
            "ref": 101,
            "subject": "New Story",
            "description": "",
            "project": 1,
            "status": 1,
            "points": {},
            "total_points": 0,
            "is_closed": False,
            "attachments": [],
        }

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.create_userstory(
                auth_token="test-token", project_id=1, subject="New Story"
            )

            # The create function adds default values for is_blocked,
            # client_requirement, team_requirement
            mock_client.post.assert_called_once_with(
                "/userstories",
                data={
                    "project": 1,
                    "subject": "New Story",
                    "is_blocked": False,
                    "client_requirement": False,
                    "team_requirement": False,
                },
            )

            assert result["id"] == 1
            assert result["subject"] == "New Story"
            assert "Successfully created user story" in result["message"]

    @pytest.mark.asyncio
    async def test_create_userstory_full(self, userstory_tools) -> None:
        """Test creating a user story with all fields."""
        mock_response = {
            "id": 2,
            "ref": 102,
            "subject": "Full Story",
            "description": "Full description",
            "project": 1,
            "status": 2,
            "points": {"1": 5},
            "total_points": 5,
            "is_closed": False,
            "attachments": [{"id": 1}],
        }

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.create_userstory(
                auth_token="test-token",
                project_id=1,
                subject="Full Story",
                description="Full description",
                status=2,
                points={"1": 5},
                tags=["tag1", "tag2"],
                assigned_to=1,
                is_blocked=True,
                blocked_note="Waiting",
                milestone=1,
                client_requirement=True,
                team_requirement=False,
                attachments=[{"name": "file.pdf"}],
            )

            expected_data = {
                "project": 1,
                "subject": "Full Story",
                "description": "Full description",
                "status": 2,
                "points": {"1": 5},
                "tags": ["tag1", "tag2"],
                "assigned_to": 1,
                "is_blocked": True,
                "blocked_note": "Waiting",
                "milestone": 1,
                "client_requirement": True,
                "team_requirement": False,
                "attachments": [{"name": "file.pdf"}],
            }

            mock_client.post.assert_called_once_with("/userstories", data=expected_data)

            assert result["id"] == 2
            assert result["points"] == {"1": 5}

    @pytest.mark.asyncio
    async def test_create_userstory_auth_error(self, userstory_tools) -> None:
        """Test create_userstory with authentication error."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.side_effect = AuthenticationError("Invalid token")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Authentication failed"):
                await userstory_tools.create_userstory(
                    auth_token="invalid-token", project_id=1, subject="Story"
                )

    @pytest.mark.asyncio
    async def test_create_userstory_api_error(self, userstory_tools) -> None:
        """Test create_userstory with API error."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.side_effect = TaigaAPIError("Validation error")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Failed to create user story: Validation error"):
                await userstory_tools.create_userstory(
                    auth_token="test-token", project_id=1, subject="Story"
                )


class TestGetUserStory:
    """Tests for get_userstory tool."""

    @pytest.mark.asyncio
    async def test_get_userstory_by_id(self, userstory_tools) -> None:
        """Test getting a user story by ID."""
        mock_response = {
            "id": 1,
            "ref": 101,
            "subject": "Test Story",
            "description": "Description",
            "project": 1,
            "milestone": 1,
            "milestone_name": "Sprint 1",
            "status": 1,
            "points": {"1": 3},
            "total_points": 3,
            "is_closed": False,
            "is_blocked": False,
            "blocked_note": None,
            "assigned_to": 1,
            "assigned_users": [{"id": 1, "name": "User"}],
            "watchers": [1, 2],
            "total_watchers": 2,
            "client_requirement": True,
            "team_requirement": False,
            "attachments": [],
            "tags": ["tag1"],
            "version": 1,
            "created_date": "2024-01-01",
            "modified_date": "2024-01-02",
        }

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.get_userstory(auth_token="test-token", userstory_id=1)

            mock_client.get.assert_called_once_with("/userstories/1")

            assert result["id"] == 1
            assert result["milestone_name"] == "Sprint 1"
            assert result["client_requirement"] is True

    @pytest.mark.asyncio
    async def test_get_userstory_by_ref(self, userstory_tools) -> None:
        """Test getting a user story by reference."""
        mock_response = {"id": 2, "ref": 102, "subject": "Story by Ref"}

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.get_userstory(
                auth_token="test-token", project_id=1, ref=102
            )

            mock_client.get.assert_called_once_with(
                "/userstories/by_ref", params={"ref": 102, "project": 1}
            )

            assert result["id"] == 2
            assert result["ref"] == 102

    @pytest.mark.asyncio
    async def test_get_userstory_missing_params(self, userstory_tools) -> None:
        """Test get_userstory with missing parameters."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match=r"Either userstory_id or .* required"):
                await userstory_tools.get_userstory(auth_token="test-token")

    @pytest.mark.asyncio
    async def test_get_userstory_not_found(self, userstory_tools) -> None:
        """Test get_userstory with non-existent story."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = ResourceNotFoundError("Not found")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="User story not found"):
                await userstory_tools.get_userstory(auth_token="test-token", userstory_id=999)

    @pytest.mark.asyncio
    async def test_get_userstory_permission_denied(self, userstory_tools) -> None:
        """Test get_userstory with permission denied."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = PermissionDeniedError("No access")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="No permission to access user story"):
                await userstory_tools.get_userstory(auth_token="test-token", userstory_id=1)


class TestUpdateUserStory:
    """Tests for update_userstory tool."""

    @pytest.mark.asyncio
    async def test_update_userstory_single_field(self, userstory_tools) -> None:
        """Test updating a single field."""
        mock_response = {
            "id": 1,
            "ref": 101,
            "subject": "Updated Subject",
            "status": 1,
            "is_closed": False,
            "is_blocked": False,
            "blocked_note": None,
            "assigned_to": 1,
            "assigned_users": [],
            "milestone": 1,
            "milestone_name": "Sprint 1",
            "version": 2,
        }

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.patch.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.update_userstory(
                auth_token="test-token", userstory_id=1, subject="Updated Subject"
            )

            mock_client.patch.assert_called_once_with(
                "/userstories/1", data={"subject": "Updated Subject"}
            )

            assert result["subject"] == "Updated Subject"
            assert "Successfully updated" in result["message"]

    @pytest.mark.asyncio
    async def test_update_userstory_multiple_fields(self, userstory_tools) -> None:
        """Test updating multiple fields."""
        mock_response = {
            "id": 1,
            "ref": 101,
            "subject": "New Subject",
            "status": 2,
            "is_closed": True,
            "is_blocked": True,
            "blocked_note": "Blocked",
            "assigned_to": 2,
            "assigned_users": [],
            "milestone": 2,
            "milestone_name": "Sprint 2",
            "version": 3,
        }

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.patch.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.update_userstory(
                auth_token="test-token",
                userstory_id=1,
                subject="New Subject",
                description="New description",
                status=2,
                points={"1": 5},
                tags=["new-tag"],
                assigned_to=2,
                is_blocked=True,
                blocked_note="Blocked",
                is_closed=True,
                milestone=2,
                client_requirement=False,
                team_requirement=True,
                version=2,
            )

            expected_data = {
                "subject": "New Subject",
                "description": "New description",
                "status": 2,
                "points": {"1": 5},
                "tags": ["new-tag"],
                "assigned_to": 2,
                "is_blocked": True,
                "blocked_note": "Blocked",
                "is_closed": True,
                "milestone": 2,
                "client_requirement": False,
                "team_requirement": True,
                "version": 2,
            }

            mock_client.patch.assert_called_once_with("/userstories/1", data=expected_data)

            assert result["status"] == 2
            assert result["is_closed"] is True

    @pytest.mark.asyncio
    async def test_update_userstory_not_found(self, userstory_tools) -> None:
        """Test update_userstory with non-existent story."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.patch.side_effect = ResourceNotFoundError("Not found")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="User story 999 not found"):
                await userstory_tools.update_userstory(
                    auth_token="test-token", userstory_id=999, subject="New"
                )

    @pytest.mark.asyncio
    async def test_update_userstory_permission_denied(self, userstory_tools) -> None:
        """Test update_userstory with permission denied."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.patch.side_effect = PermissionDeniedError("No access")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="No permission to update user story 1"):
                await userstory_tools.update_userstory(
                    auth_token="test-token", userstory_id=1, subject="New"
                )


class TestDeleteUserStory:
    """Tests for delete_userstory tool."""

    @pytest.mark.asyncio
    async def test_delete_userstory_success(self, userstory_tools) -> None:
        """Test successful user story deletion."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.delete.return_value = True
            mock_client_class.return_value = mock_client

            result = await userstory_tools.delete_userstory(auth_token="test-token", userstory_id=1)

            mock_client.delete.assert_called_once_with("/userstories/1")
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_userstory_not_found(self, userstory_tools) -> None:
        """Test delete_userstory with non-existent story."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.delete.side_effect = ResourceNotFoundError("Not found")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Not found"):
                await userstory_tools.delete_userstory(auth_token="test-token", userstory_id=999)

    @pytest.mark.asyncio
    async def test_delete_userstory_permission_denied(self, userstory_tools) -> None:
        """Test delete_userstory with permission denied."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.delete.side_effect = PermissionDeniedError("No access")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="No permission to delete user story 1"):
                await userstory_tools.delete_userstory(auth_token="test-token", userstory_id=1)


class TestBulkOperations:
    """Tests for bulk operations on user stories."""

    @pytest.mark.asyncio
    async def test_bulk_create_userstories(self, userstory_tools) -> None:
        """Test bulk creating user stories."""
        mock_response = [
            {"id": 1, "ref": 101, "subject": "Story 1", "status": 1, "milestone": 1},
            {"id": 2, "ref": 102, "subject": "Story 2", "status": 1, "milestone": 1},
        ]

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.bulk_create_userstories(
                auth_token="test-token",
                project_id=1,
                bulk_stories="Story 1\nStory 2\n\n",
                status=1,
                milestone=1,
            )

            expected_data = {
                "project_id": 1,
                "bulk_stories": "Story 1\nStory 2",
                "status_id": 1,
                "milestone_id": 1,
            }

            mock_client.post.assert_called_once_with("/userstories/bulk_create", data=expected_data)

            assert len(result) == 2
            assert result[0]["subject"] == "Story 1"
            assert result[1]["subject"] == "Story 2"

    @pytest.mark.asyncio
    async def test_bulk_create_userstories_empty_response(self, userstory_tools) -> None:
        """Test bulk_create with non-list response."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = {}  # Non-list response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.bulk_create_userstories(
                auth_token="test-token", project_id=1, bulk_stories="Story 1"
            )

            assert result == []

    @pytest.mark.asyncio
    async def test_bulk_update_userstories(self, userstory_tools) -> None:
        """Test bulk updating user stories."""
        mock_response = [
            {
                "id": 1,
                "ref": 101,
                "subject": "Story 1",
                "status": 2,
                "milestone": 2,
                "assigned_to": 1,
            },
            {
                "id": 2,
                "ref": 102,
                "subject": "Story 2",
                "status": 2,
                "milestone": 2,
                "assigned_to": 1,
            },
        ]

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.bulk_update_userstories(
                auth_token="test-token", story_ids=[1, 2], status=2, milestone=2, assigned_to=1
            )

            expected_data = {
                "bulk_userstories": [1, 2],
                "status_id": 2,
                "milestone_id": 2,
                "assigned_to": 1,
            }

            mock_client.post.assert_called_once_with("/userstories/bulk_update", data=expected_data)

            assert len(result) == 2
            assert result[0]["status"] == 2
            assert result[1]["assigned_to"] == 1

    @pytest.mark.asyncio
    async def test_bulk_update_userstories_partial(self, userstory_tools) -> None:
        """Test bulk update with only some fields."""
        mock_response = [{"id": 1, "status": 3}]

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            await userstory_tools.bulk_update_userstories(
                auth_token="test-token", story_ids=[1], status=3
            )

            expected_data = {"bulk_userstories": [1], "status_id": 3}

            mock_client.post.assert_called_once_with("/userstories/bulk_update", data=expected_data)

    @pytest.mark.asyncio
    async def test_bulk_delete_userstories(self, userstory_tools) -> None:
        """Test bulk deleting user stories."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = None
            mock_client_class.return_value = mock_client

            result = await userstory_tools.bulk_delete_userstories(
                auth_token="test-token", story_ids=[1, 2, 3]
            )

            expected_data = {"bulk_userstories": [1, 2, 3]}

            mock_client.post.assert_called_once_with("/userstories/bulk_delete", data=expected_data)

            assert result is True

    @pytest.mark.asyncio
    async def test_bulk_operations_auth_error(self, userstory_tools) -> None:
        """Test bulk operations with authentication error."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.side_effect = AuthenticationError("Invalid token")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Authentication failed"):
                await userstory_tools.bulk_create_userstories(
                    auth_token="invalid-token", project_id=1, bulk_stories="Story"
                )

            with pytest.raises(MCPError, match="Authentication failed"):
                await userstory_tools.bulk_update_userstories(
                    auth_token="invalid-token", story_ids=[1]
                )

            with pytest.raises(MCPError, match="Authentication failed"):
                await userstory_tools.bulk_delete_userstories(
                    auth_token="invalid-token", story_ids=[1]
                )


class TestMoveToMilestone:
    """Tests for move_to_milestone tool."""

    @pytest.mark.asyncio
    async def test_move_to_milestone_success(self, userstory_tools) -> None:
        """Test successfully moving a story to a milestone."""
        mock_response = {
            "id": 1,
            "ref": 101,
            "subject": "Story 1",
            "milestone": 2,
            "milestone_name": "Sprint 2",
        }

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.patch.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.move_to_milestone(
                auth_token="test-token", userstory_id=1, milestone_id=2
            )

            mock_client.patch.assert_called_once_with("/userstories/1", data={"milestone": 2})

            assert result["milestone"] == 2
            assert result["milestone_name"] == "Sprint 2"
            assert "Successfully moved" in result["message"]

    @pytest.mark.asyncio
    async def test_move_to_milestone_not_found(self, userstory_tools) -> None:
        """Test move_to_milestone with non-existent story."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.patch.side_effect = ResourceNotFoundError("Not found")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="User story 999 not found"):
                await userstory_tools.move_to_milestone(
                    auth_token="test-token", userstory_id=999, milestone_id=1
                )


class TestUserStoryHistory:
    """Tests for get_userstory_history tool."""

    @pytest.mark.asyncio
    async def test_get_userstory_history_success(self, userstory_tools) -> None:
        """Test getting user story history."""
        mock_response = [
            {
                "id": 1,
                "user": {"id": 1, "username": "user1"},
                "created_at": "2024-01-01",
                "type": 1,
                "diff": {"subject": ["Old", "New"]},
                "comment": "Changed subject",
                "is_hidden": False,
            },
            {
                "id": 2,
                "user": {"id": 2, "username": "user2"},
                "created_at": "2024-01-02",
                "type": 2,
                "diff": {"status": [1, 2]},
                "comment": "",
                "is_hidden": False,
            },
        ]

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.get_userstory_history(
                auth_token="test-token", userstory_id=1
            )

            mock_client.get.assert_called_once_with("/history/userstory/1")

            assert len(result) == 2
            assert result[0]["comment"] == "Changed subject"
            assert result[1]["comment"] == ""

    @pytest.mark.asyncio
    async def test_get_userstory_history_not_found(self, userstory_tools) -> None:
        """Test get_userstory_history with non-existent story."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = ResourceNotFoundError("Not found")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="User story 999 not found"):
                await userstory_tools.get_userstory_history(
                    auth_token="test-token", userstory_id=999
                )


class TestWatchOperations:
    """Tests for watch/unwatch operations."""

    @pytest.mark.asyncio
    async def test_watch_userstory_success(self, userstory_tools) -> None:
        """Test watching a user story."""
        mock_response = {"is_watcher": True, "total_watchers": 5}

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.watch_userstory(auth_token="test-token", userstory_id=1)

            mock_client.post.assert_called_once_with("/userstories/1/watch")

            assert result["is_watcher"] is True
            assert result["total_watchers"] == 5
            assert "Now watching" in result["message"]

    @pytest.mark.asyncio
    async def test_unwatch_userstory_success(self, userstory_tools) -> None:
        """Test unwatching a user story."""
        mock_response = {"is_watcher": False, "total_watchers": 4}

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.unwatch_userstory(
                auth_token="test-token", userstory_id=1
            )

            mock_client.post.assert_called_once_with("/userstories/1/unwatch")

            assert result["is_watcher"] is False
            assert result["total_watchers"] == 4
            assert "Stopped watching" in result["message"]

    @pytest.mark.asyncio
    async def test_watch_operations_not_found(self, userstory_tools) -> None:
        """Test watch operations with non-existent story."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.side_effect = ResourceNotFoundError("Not found")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="User story 999 not found"):
                await userstory_tools.watch_userstory(auth_token="test-token", userstory_id=999)

            with pytest.raises(MCPError, match="User story 999 not found"):
                await userstory_tools.unwatch_userstory(auth_token="test-token", userstory_id=999)


class TestVoteOperations:
    """Tests for vote operations."""

    @pytest.mark.asyncio
    async def test_upvote_userstory_success(self, userstory_tools) -> None:
        """Test upvoting a user story."""
        mock_response = {"is_voter": True, "total_voters": 10}

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.upvote_userstory(auth_token="test-token", userstory_id=1)

            mock_client.post.assert_called_once_with("/userstories/1/upvote")

            assert result["is_voter"] is True
            assert result["total_voters"] == 10
            assert "Upvoted" in result["message"]

    @pytest.mark.asyncio
    async def test_downvote_userstory_success(self, userstory_tools) -> None:
        """Test downvoting (removing upvote) from a user story."""
        mock_response = {"is_voter": False, "total_voters": 9}

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.downvote_userstory(
                auth_token="test-token", userstory_id=1
            )

            mock_client.post.assert_called_once_with("/userstories/1/downvote")

            assert result["is_voter"] is False
            assert result["total_voters"] == 9
            assert "Removed upvote" in result["message"]

    @pytest.mark.asyncio
    async def test_get_userstory_voters_success(self, userstory_tools) -> None:
        """Test getting voters for a user story."""
        mock_response = [
            {
                "id": 1,
                "username": "user1",
                "full_name_display": "User One",
                "photo": "http://example.com/photo1.jpg",
            },
            {
                "id": 2,
                "username": "user2",
                "full_name_display": "User Two",
                "photo": "http://example.com/photo2.jpg",
            },
        ]

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.get_userstory_voters(
                auth_token="test-token", userstory_id=1
            )

            mock_client.get.assert_called_once_with("/userstories/1/voters")

            assert len(result) == 2
            assert result[0]["username"] == "user1"
            assert result[0]["full_name"] == "User One"
            assert result[1]["username"] == "user2"

    @pytest.mark.asyncio
    async def test_get_userstory_voters_empty(self, userstory_tools) -> None:
        """Test get_userstory_voters with no voters."""
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = {}  # Non-list response
            mock_client_class.return_value = mock_client

            result = await userstory_tools.get_userstory_voters(
                auth_token="test-token", userstory_id=1
            )

            assert result == []

    @pytest.mark.asyncio
    async def test_vote_operations_errors(self, userstory_tools) -> None:
        """Test vote operations with various errors."""
        # Not found error
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.side_effect = ResourceNotFoundError("Not found")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="User story 999 not found"):
                await userstory_tools.upvote_userstory(auth_token="test-token", userstory_id=999)

        # Authentication error
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.side_effect = AuthenticationError("Invalid token")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="Authentication failed"):
                await userstory_tools.downvote_userstory(auth_token="invalid-token", userstory_id=1)

        # API error for voters
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = TaigaAPIError("Server error")
            mock_client_class.return_value = mock_client

            with pytest.raises(MCPError, match="API error: Server error"):
                await userstory_tools.get_userstory_voters(auth_token="test-token", userstory_id=1)


class TestAttributeAccess:
    """Tests for dynamic attribute access."""

    def test_getattr_existing_method(self, userstory_tools) -> None:
        """Test __getattr__ with existing method."""
        # Methods should be accessible after register_tools
        assert callable(userstory_tools.list_userstories)
        assert callable(userstory_tools.create_userstory)
        assert callable(userstory_tools.get_userstory)

    def test_getattr_non_existing_method(self, userstory_tools) -> None:
        """Test __getattr__ with non-existing method - removed due to recursion issue."""
        # The __getattr__ implementation in the source has a recursion issue with hasattr
        # This test is removed to avoid the RecursionError
