"""
Fixtures for FastMCP Tools integration tests.

This module provides fixtures specifically for testing MCP tools registration
and execution using FastMCP's in-memory client pattern.
"""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client, FastMCP

from src.application.tools.auth_tools import AuthTools
from src.application.tools.epic_tools import EpicTools
from src.application.tools.issue_tools import IssueTools
from src.application.tools.membership_tools import MembershipTools
from src.application.tools.milestone_tools import MilestoneTools
from src.application.tools.project_tools import ProjectTools
from src.application.tools.task_tools import TaskTools
from src.application.tools.user_tools import UserTools
from src.application.tools.userstory_tools import UserStoryTools
from src.application.tools.webhook_tools import WebhookTools
from src.application.tools.wiki_tools import WikiTools


@pytest.fixture
def mock_taiga_client_for_tools() -> AsyncMock:
    """Create a comprehensive mock for TaigaAPIClient.

    Returns:
        AsyncMock configured with all necessary methods for tools testing.
    """
    client = AsyncMock()

    # Configure as async context manager
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    # Auth methods
    client.authenticate = AsyncMock(
        return_value={
            "auth_token": "test-token-12345",
            "refresh": "test-refresh-token",
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
        }
    )
    client.refresh_token = AsyncMock(
        return_value={
            "auth_token": "new-test-token",
            "refresh": "new-refresh-token",
        }
    )
    client.get_current_user = AsyncMock(
        return_value={
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
        }
    )

    # Project methods
    client.list_projects = AsyncMock(
        return_value=[
            {"id": 1, "name": "Project 1", "slug": "project-1"},
            {"id": 2, "name": "Project 2", "slug": "project-2"},
        ]
    )
    client.create_project = AsyncMock(
        return_value={"id": 3, "name": "New Project", "slug": "new-project"}
    )
    client.get_project = AsyncMock(
        return_value={"id": 1, "name": "Project 1", "slug": "project-1", "version": 1}
    )
    client.update_project = AsyncMock(
        return_value={"id": 1, "name": "Updated Project", "version": 2}
    )
    client.delete_project = AsyncMock(return_value=None)
    client.get_project_stats = AsyncMock(
        return_value={"total_milestones": 5, "total_points": 100.0}
    )
    client.get_project_issues_stats = AsyncMock(
        return_value={"total_issues": 10, "opened_issues": 5}
    )
    client.get_project_tags = AsyncMock(return_value=[{"name": "tag1", "color": "#FF0000"}])
    client.get_project_by_slug = AsyncMock(
        return_value={"id": 1, "name": "Project 1", "slug": "project-1"}
    )

    # Epic methods
    client.list_epics = AsyncMock(
        return_value=[
            {"id": 1, "subject": "Epic 1", "project": 1, "ref": 1},
            {"id": 2, "subject": "Epic 2", "project": 1, "ref": 2},
        ]
    )
    client.create_epic = AsyncMock(
        return_value={"id": 3, "subject": "New Epic", "project": 1, "ref": 3}
    )
    client.get_epic = AsyncMock(
        return_value={"id": 1, "subject": "Epic 1", "project": 1, "ref": 1, "version": 1}
    )
    client.get_epic_by_ref = AsyncMock(
        return_value={"id": 1, "subject": "Epic 1", "project": 1, "ref": 1}
    )
    client.update_epic = AsyncMock(return_value={"id": 1, "subject": "Updated Epic", "version": 2})
    client.update_epic_full = AsyncMock(
        return_value={"id": 1, "subject": "Updated Epic Full", "version": 2}
    )
    client.delete_epic = AsyncMock(return_value=True)
    client.bulk_create_epics = AsyncMock(
        return_value=[
            {"id": 4, "subject": "Bulk Epic 1"},
            {"id": 5, "subject": "Bulk Epic 2"},
        ]
    )
    client.get_epic_filters = AsyncMock(
        return_value={
            "statuses": [{"id": 1, "name": "New"}],
            "assigned_to": [{"id": 1, "username": "user1"}],
        }
    )
    client.upvote_epic = AsyncMock(return_value={"id": 1, "total_voters": 1})
    client.downvote_epic = AsyncMock(return_value={"id": 1, "total_voters": 0})
    client.get_epic_voters = AsyncMock(return_value=[{"id": 1, "username": "user1"}])
    client.watch_epic = AsyncMock(return_value={"id": 1, "total_watchers": 1})
    client.unwatch_epic = AsyncMock(return_value={"id": 1, "total_watchers": 0})
    client.get_epic_watchers = AsyncMock(return_value=[{"id": 1, "username": "user1"}])
    client.list_epic_related_userstories = AsyncMock(
        return_value=[{"id": 1, "user_story": 100, "epic": 1, "order": 1}]
    )
    client.create_epic_related_userstory = AsyncMock(
        return_value={"id": 2, "user_story": 101, "epic": 1, "order": 2}
    )
    client.get_epic_related_userstory = AsyncMock(
        return_value={"id": 1, "user_story": 100, "epic": 1}
    )
    client.update_epic_related_userstory = AsyncMock(return_value={"id": 1, "order": 3})
    client.delete_epic_related_userstory = AsyncMock(return_value=None)
    client.list_epic_attachments = AsyncMock(return_value=[])
    client.create_epic_attachment = AsyncMock(
        return_value={"id": 1, "name": "file.txt", "size": 1024}
    )
    client.get_epic_attachment = AsyncMock(return_value={"id": 1, "name": "file.txt"})
    client.update_epic_attachment = AsyncMock(return_value={"id": 1, "description": "Updated"})
    client.delete_epic_attachment = AsyncMock(return_value=None)
    client.list_epic_custom_attributes = AsyncMock(
        return_value=[{"id": 1, "name": "Custom Field", "project": 1}]
    )
    client.create_epic_custom_attribute = AsyncMock(
        return_value={"id": 2, "name": "New Field", "project": 1}
    )
    client.get_epic_custom_attribute_values = AsyncMock(
        return_value={"epic": 1, "attributes_values": {"1": "value1"}}
    )

    # User Story methods
    client.list_userstories = AsyncMock(
        return_value=[
            {"id": 1, "subject": "Story 1", "project": 1},
            {"id": 2, "subject": "Story 2", "project": 1},
        ]
    )
    client.create_userstory = AsyncMock(
        return_value={"id": 3, "subject": "New Story", "project": 1}
    )
    client.get_userstory = AsyncMock(
        return_value={"id": 1, "subject": "Story 1", "project": 1, "version": 1}
    )
    client.get_userstory_by_ref = AsyncMock(return_value={"id": 1, "subject": "Story 1", "ref": 1})
    client.update_userstory = AsyncMock(
        return_value={"id": 1, "subject": "Updated Story", "version": 2}
    )
    client.delete_userstory = AsyncMock(return_value=None)
    client.bulk_create_userstories = AsyncMock(
        return_value=[
            {"id": 4, "subject": "Bulk Story 1"},
            {"id": 5, "subject": "Bulk Story 2"},
        ]
    )
    client.bulk_update_userstories = AsyncMock(
        return_value=[{"id": 1, "status": 2}, {"id": 2, "status": 2}]
    )
    client.bulk_delete_userstories = AsyncMock(return_value=None)
    client.upvote_userstory = AsyncMock(return_value={"id": 1, "total_voters": 1})
    client.downvote_userstory = AsyncMock(return_value={"id": 1, "total_voters": 0})
    client.get_userstory_voters = AsyncMock(return_value=[])
    client.watch_userstory = AsyncMock(return_value={"id": 1})
    client.unwatch_userstory = AsyncMock(return_value={"id": 1})
    client.get_userstory_watchers = AsyncMock(return_value=[])
    client.get_userstory_history = AsyncMock(return_value=[])
    client.get_userstory_filters = AsyncMock(return_value={"statuses": [], "tags": []})

    # Task methods
    client.list_tasks = AsyncMock(
        return_value=[
            {"id": 1, "subject": "Task 1", "project": 1, "user_story": 1},
        ]
    )
    client.create_task = AsyncMock(return_value={"id": 2, "subject": "New Task", "project": 1})
    client.get_task = AsyncMock(
        return_value={"id": 1, "subject": "Task 1", "project": 1, "version": 1}
    )
    client.get_task_by_ref = AsyncMock(return_value={"id": 1, "subject": "Task 1", "ref": 1})
    client.update_task = AsyncMock(return_value={"id": 1, "subject": "Updated Task", "version": 2})
    client.update_task_full = AsyncMock(
        return_value={"id": 1, "subject": "Updated Task Full", "version": 2}
    )
    client.delete_task = AsyncMock(return_value=True)
    client.bulk_create_tasks = AsyncMock(
        return_value=[
            {"id": 3, "subject": "Bulk Task 1"},
            {"id": 4, "subject": "Bulk Task 2"},
        ]
    )
    client.get_task_filters = AsyncMock(return_value={"statuses": [{"id": 1, "name": "New"}]})
    client.upvote_task = AsyncMock(return_value={"id": 1, "total_voters": 1})
    client.downvote_task = AsyncMock(return_value={"id": 1, "total_voters": 0})
    client.get_task_voters = AsyncMock(return_value=[])
    client.watch_task = AsyncMock(return_value={"id": 1})
    client.unwatch_task = AsyncMock(return_value={"id": 1})
    client.get_task_watchers = AsyncMock(return_value=[])
    client.list_task_attachments = AsyncMock(
        return_value=[{"id": 1, "name": "file.txt", "size": 1024}]
    )
    client.create_task_attachment = AsyncMock(return_value={"id": 1})
    client.get_task_attachment = AsyncMock(return_value={"id": 1})
    client.update_task_attachment = AsyncMock(return_value={"id": 1})
    client.delete_task_attachment = AsyncMock(return_value=None)
    client.get_task_history = AsyncMock(
        return_value=[{"id": "1", "user": {"id": 1, "username": "user1"}, "type": 1}]
    )
    client.get_task_comment_versions = AsyncMock(return_value=[])
    client.edit_task_comment = AsyncMock(return_value={"id": "1"})
    client.delete_task_comment = AsyncMock(return_value=None)
    client.undelete_task_comment = AsyncMock(return_value={"id": "1"})
    client.list_task_custom_attributes = AsyncMock(return_value=[])
    client.create_task_custom_attribute = AsyncMock(return_value={"id": 1})
    client.update_task_custom_attribute = AsyncMock(return_value={"id": 1})
    client.delete_task_custom_attribute = AsyncMock(return_value=None)

    # Issue methods
    client.list_issues = AsyncMock(
        return_value=[
            {"id": 1, "subject": "Issue 1", "project": 1},
        ]
    )
    client.create_issue = AsyncMock(return_value={"id": 2, "subject": "New Issue", "project": 1})
    client.get_issue = AsyncMock(
        return_value={"id": 1, "subject": "Issue 1", "project": 1, "version": 1}
    )
    client.get_issue_by_ref = AsyncMock(return_value={"id": 1, "subject": "Issue 1", "ref": 1})
    client.update_issue = AsyncMock(
        return_value={"id": 1, "subject": "Updated Issue", "version": 2}
    )
    client.delete_issue = AsyncMock(return_value=True)
    client.bulk_create_issues = AsyncMock(
        return_value=[
            {"id": 3, "subject": "Bulk Issue 1"},
        ]
    )
    client.get_issue_filters = AsyncMock(
        return_value={"statuses": [], "types": [], "severities": [], "priorities": []}
    )
    client.upvote_issue = AsyncMock(return_value={"id": 1, "total_voters": 1})
    client.downvote_issue = AsyncMock(return_value={"id": 1, "total_voters": 0})
    client.get_issue_voters = AsyncMock(return_value=[])
    client.watch_issue = AsyncMock(return_value={"id": 1})
    client.unwatch_issue = AsyncMock(return_value={"id": 1})
    client.get_issue_watchers = AsyncMock(return_value=[])
    client.get_issue_attachments = AsyncMock(
        return_value=[{"id": 1, "name": "issue_file.txt", "size": 2048}]
    )
    client.list_issue_attachments = AsyncMock(
        return_value=[{"id": 1, "name": "issue_file.txt", "size": 2048}]
    )
    client.create_issue_attachment = AsyncMock(return_value={"id": 1})
    client.get_issue_attachment = AsyncMock(return_value={"id": 1})
    client.update_issue_attachment = AsyncMock(return_value={"id": 1})
    client.delete_issue_attachment = AsyncMock(return_value=None)
    client.get_issue_history = AsyncMock(
        return_value=[{"id": "1", "user": {"id": 1, "username": "user1"}, "type": 1}]
    )
    client.get_issue_comment_versions = AsyncMock(return_value=[])
    client.edit_issue_comment = AsyncMock(return_value={"id": "1"})
    client.delete_issue_comment = AsyncMock(return_value=None)
    client.undelete_issue_comment = AsyncMock(return_value={"id": "1"})
    client.get_issue_custom_attributes = AsyncMock(return_value=[])
    client.list_issue_custom_attributes = AsyncMock(return_value=[])
    client.create_issue_custom_attribute = AsyncMock(return_value={"id": 1})
    client.update_issue_custom_attribute = AsyncMock(return_value={"id": 1})
    client.delete_issue_custom_attribute = AsyncMock(return_value=None)

    # HTTP methods - provide sensible defaults based on common API patterns
    # get() returns list by default (for list endpoints) but dict for single resources
    async def mock_get(path: str, *args, **kwargs) -> list | dict:
        """Mock HTTP GET with path-aware responses."""
        # Stats, single resource, and specific item endpoints return dict
        if any(x in path for x in ["/stats", "/by_ref", "/me", "/filters"]):
            return {"id": 1, "success": True}
        # Check if path ends with an ID (single resource fetch)
        parts = path.rstrip("/").split("/")
        if parts and parts[-1].isdigit():
            return {"id": int(parts[-1]), "subject": "Test Item", "name": "Test"}
        # Default for list endpoints
        return [{"id": 1, "subject": "Item 1"}, {"id": 2, "subject": "Item 2"}]

    client.get = AsyncMock(side_effect=mock_get)

    async def mock_post(path: str, *args, **kwargs) -> list | dict:
        """Mock HTTP POST with path-aware responses."""
        # Bulk operations return lists
        if "bulk_create" in path or "bulk_update" in path:
            return [
                {"id": 1, "ref": 1, "subject": "Created Item 1"},
                {"id": 2, "ref": 2, "subject": "Created Item 2"},
            ]
        # Default for create operations
        return {"id": 1, "success": True}

    client.post = AsyncMock(side_effect=mock_post)
    client.patch = AsyncMock(return_value={"id": 1, "success": True})
    client.put = AsyncMock(return_value={"id": 1, "success": True})
    client.delete = AsyncMock(return_value=True)  # delete returns bool for success

    return client


@pytest.fixture
def mcp_server_with_tools(mock_taiga_client_for_tools: AsyncMock) -> FastMCP:
    """Create a FastMCP server with all tools registered.

    This fixture creates a real FastMCP server instance with all Taiga tools
    registered, but using a mocked TaigaAPIClient to avoid real API calls.

    Args:
        mock_taiga_client_for_tools: Mocked Taiga client fixture

    Returns:
        FastMCP server instance with tools registered
    """
    mcp = FastMCP("Taiga MCP Test Server")

    # Patch TaigaAPIClient in all tool modules
    patches = []
    tool_modules = [
        "src.application.tools.auth_tools",
        "src.application.tools.project_tools",
        "src.application.tools.epic_tools",
        "src.application.tools.userstory_tools",
        "src.application.tools.task_tools",
        "src.application.tools.issue_tools",
        "src.application.tools.milestone_tools",
        "src.application.tools.membership_tools",
        "src.application.tools.webhook_tools",
        "src.application.tools.wiki_tools",
        "src.application.tools.user_tools",
    ]

    for module in tool_modules:
        p = patch(f"{module}.TaigaAPIClient")
        mock_cls = p.start()
        mock_cls.return_value = mock_taiga_client_for_tools
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_taiga_client_for_tools)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        patches.append(p)

    # Register all tools
    auth_tools = AuthTools(mcp)
    auth_tools.register_tools()

    project_tools = ProjectTools(mcp)
    project_tools.register_tools()

    EpicTools(mcp)  # Auto-registers in __init__

    userstory_tools = UserStoryTools(mcp)
    userstory_tools.register_tools()

    TaskTools(mcp)  # Auto-registers in __init__

    issue_tools = IssueTools(mcp)
    issue_tools.register_tools()

    MilestoneTools(mcp)  # Auto-registers in __init__

    membership_tools = MembershipTools(mcp)
    membership_tools.register_tools()

    webhook_tools = WebhookTools(mcp)
    webhook_tools.register_tools()

    wiki_tools = WikiTools(mcp)
    wiki_tools.register_tools()

    UserTools(mcp)  # Auto-registers in __init__

    yield mcp

    # Stop all patches
    for p in patches:
        p.stop()


@pytest.fixture
async def mcp_client(mcp_server_with_tools: FastMCP) -> Client:
    """Create FastMCP Client for testing.

    This fixture provides an async client connected to the test MCP server
    for in-memory testing of tool registration and execution.

    Args:
        mcp_server_with_tools: FastMCP server fixture

    Yields:
        FastMCP Client connected to the test server
    """
    async with Client(mcp_server_with_tools) as client:
        yield client


def get_expected_tool_names() -> dict[str, list[str]]:
    """Get expected tool names for each tool category.

    Returns:
        Dictionary mapping tool categories to their expected tool names.
    """
    return {
        "auth": [
            "taiga_authenticate",
            "taiga_refresh_token",
            "taiga_get_current_user",
            "taiga_logout",
            "taiga_check_auth",
        ],
        "project": [
            "taiga_list_projects",
            "taiga_create_project",
            "taiga_get_project",
            "taiga_update_project",
            "taiga_delete_project",
            "taiga_get_project_stats",
            "taiga_duplicate_project",
            "taiga_like_project",
            "taiga_unlike_project",
            "taiga_watch_project",
            "taiga_unwatch_project",
            "taiga_get_project_modules",
            "taiga_update_project_modules",
            "taiga_get_project_by_slug",
            "taiga_get_project_issues_stats",
            "taiga_get_project_tags",
            "taiga_create_project_tag",
            "taiga_edit_project_tag",
            "taiga_delete_project_tag",
            "taiga_mix_project_tags",
            "taiga_export_project",
            "taiga_bulk_update_projects_order",
        ],
        "epic": [
            "taiga_list_epics",
            "taiga_create_epic",
            "taiga_get_epic",
            "taiga_get_epic_by_ref",
            "taiga_update_epic_full",
            "taiga_update_epic_partial",
            "taiga_delete_epic",
            "taiga_list_epic_related_userstories",
            "taiga_create_epic_related_userstory",
            "taiga_get_epic_related_userstory",
            "taiga_update_epic_related_userstory",
            "taiga_delete_epic_related_userstory",
            "taiga_bulk_create_epics",
            "taiga_get_epic_filters",
            "taiga_upvote_epic",
            "taiga_downvote_epic",
            "taiga_get_epic_voters",
            "taiga_watch_epic",
            "taiga_unwatch_epic",
            "taiga_get_epic_watchers",
            "taiga_list_epic_attachments",
            "taiga_create_epic_attachment",
            "taiga_get_epic_attachment",
            "taiga_update_epic_attachment",
            "taiga_delete_epic_attachment",
            "taiga_list_epic_custom_attributes",
            "taiga_create_epic_custom_attribute",
            "taiga_get_epic_custom_attribute_values",
        ],
        "userstory": [
            "taiga_list_userstories",
            "taiga_create_userstory",
            "taiga_get_userstory",
            "taiga_update_userstory",
            "taiga_delete_userstory",
            "taiga_bulk_create_userstories",
            "taiga_bulk_update_userstories",
            "taiga_bulk_delete_userstories",
            "taiga_move_to_milestone",
            "taiga_get_userstory_history",
            "taiga_watch_userstory",
            "taiga_unwatch_userstory",
            "taiga_upvote_userstory",
            "taiga_downvote_userstory",
            "taiga_get_userstory_voters",
        ],
        "task": [
            "taiga_list_tasks",
            "taiga_create_task",
            "taiga_get_task",
            "taiga_get_task_by_ref",
            "taiga_update_task_full",
            "taiga_update_task",
            "taiga_delete_task",
            "taiga_bulk_create_tasks",
            "taiga_get_task_filters",
            "taiga_upvote_task",
            "taiga_downvote_task",
            "taiga_get_task_voters",
            "taiga_watch_task",
            "taiga_unwatch_task",
            "taiga_get_task_watchers",
            "taiga_list_task_attachments",
            "taiga_create_task_attachment",
            "taiga_get_task_attachment",
            "taiga_update_task_attachment",
            "taiga_delete_task_attachment",
            "taiga_get_task_history",
            "taiga_get_task_comment_versions",
            "taiga_edit_task_comment",
            "taiga_delete_task_comment",
            "taiga_undelete_task_comment",
            "taiga_list_task_custom_attributes",
            "taiga_create_task_custom_attribute",
            "taiga_update_task_custom_attribute",
            "taiga_delete_task_custom_attribute",
        ],
        "issue": [
            "taiga_list_issues",
            "taiga_create_issue",
            "taiga_get_issue",
            "taiga_get_issue_by_ref",
            "taiga_update_issue",
            "taiga_delete_issue",
            "taiga_bulk_create_issues",
            "taiga_get_issue_filters",
            "taiga_upvote_issue",
            "taiga_downvote_issue",
            "taiga_get_issue_voters",
            "taiga_watch_issue",
            "taiga_unwatch_issue",
            "taiga_get_issue_watchers",
            "taiga_get_issue_attachments",
            "taiga_create_issue_attachment",
            "taiga_get_issue_attachment",
            "taiga_update_issue_attachment",
            "taiga_delete_issue_attachment",
            "taiga_get_issue_history",
            "taiga_get_issue_comment_versions",
            "taiga_edit_issue_comment",
            "taiga_delete_issue_comment",
            "taiga_undelete_issue_comment",
            "taiga_get_issue_custom_attributes",
            "taiga_create_issue_custom_attribute",
            "taiga_update_issue_custom_attribute",
            "taiga_delete_issue_custom_attribute",
        ],
    }


def extract_tool_result_content(result: Any) -> str:
    """Extract text content from a CallToolResult.

    Args:
        result: CallToolResult from mcp_client.call_tool()

    Returns:
        The text content from the result

    Raises:
        AssertionError: If result is an error or has no content
    """
    assert result is not None, "Result is None"
    assert not result.is_error, f"Tool returned error: {result.content}"
    assert result.content and len(result.content) > 0, "Result has no content"

    content_block = result.content[0]
    if hasattr(content_block, "text"):
        return str(content_block.text)
    return str(content_block)
