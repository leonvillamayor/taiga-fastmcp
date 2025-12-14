"""
Integration tests for TaskTools.

These tests validate that task tools are correctly registered
in the FastMCP server and can be called through the MCP protocol.
"""

import pytest
from fastmcp import Client

from tests.integration.tools.conftest import get_expected_tool_names


@pytest.mark.asyncio
class TestTaskToolsRegistration:
    """Test TaskTools registration in FastMCP server."""

    async def test_task_tools_are_registered(self, mcp_client: Client) -> None:
        """Verify all task tools are registered with correct names."""
        tools = await mcp_client.list_tools()
        tool_names = [tool.name for tool in tools]

        expected_task_tools = get_expected_tool_names()["task"]
        for tool_name in expected_task_tools:
            assert tool_name in tool_names, f"Tool {tool_name} not registered"

    async def test_task_tools_have_taiga_prefix(self, mcp_client: Client) -> None:
        """Verify all task tools follow taiga_ naming convention."""
        tools = await mcp_client.list_tools()
        task_tools = [t for t in tools if "task" in t.name.lower()]

        for tool in task_tools:
            assert tool.name.startswith("taiga_"), f"Tool {tool.name} does not have taiga_ prefix"

    async def test_core_task_tools_count(self, mcp_client: Client) -> None:
        """Verify minimum number of task tools are registered."""
        tools = await mcp_client.list_tools()
        task_tools = [t for t in tools if "task" in t.name.lower()]

        # Should have CRUD + attachments + comments + voting/watching
        assert len(task_tools) >= 10, f"Expected at least 10 task tools, got {len(task_tools)}"


@pytest.mark.asyncio
class TestTaskToolsParameters:
    """Test TaskTools have correct parameter definitions."""

    async def test_list_tasks_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_list_tasks has auth_token parameter."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_list_tasks"), None)

        assert tool is not None, "taiga_list_tasks tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "auth_token" in required, "auth_token should be required"

    async def test_create_task_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_create_task has required parameters."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_create_task"), None)

        assert tool is not None, "taiga_create_task tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "project_id" in properties, "project_id parameter not defined"
        assert "subject" in properties, "subject parameter not defined"
        assert "auth_token" in required, "auth_token should be required"
        assert "project_id" in required, "project_id should be required"
        assert "subject" in required, "subject should be required"

    async def test_get_task_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_get_task has task_id parameter."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_get_task"), None)

        assert tool is not None, "taiga_get_task tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "task_id" in properties, "task_id parameter not defined"
        assert "task_id" in required, "task_id should be required"

    async def test_get_task_by_ref_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_get_task_by_ref has required parameters."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_get_task_by_ref"), None)

        assert tool is not None, "taiga_get_task_by_ref tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "project_id" in properties, "project_id parameter not defined"
        assert "ref" in properties, "ref parameter not defined"

    async def test_update_task_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_update_task has required parameters."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_update_task"), None)

        assert tool is not None, "taiga_update_task tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "task_id" in properties, "task_id parameter not defined"


@pytest.mark.asyncio
class TestTaskToolsExecution:
    """Test TaskTools execution through MCP protocol."""

    async def test_call_list_tasks(self, mcp_client: Client) -> None:
        """Test calling taiga_list_tasks tool."""
        result = await mcp_client.call_tool(
            "taiga_list_tasks",
            {"auth_token": "test-token"},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Should return list of tasks
        assert "task" in content.lower() or "[" in content

    async def test_call_create_task(self, mcp_client: Client) -> None:
        """Test calling taiga_create_task tool."""
        result = await mcp_client.call_tool(
            "taiga_create_task",
            {
                "auth_token": "test-token",
                "project_id": 1,
                "subject": "Test Task",
            },
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Should return created task info
        assert any(field in content.lower() for field in ["id", "subject", "task", "project"])

    async def test_call_get_task(self, mcp_client: Client) -> None:
        """Test calling taiga_get_task tool."""
        result = await mcp_client.call_tool(
            "taiga_get_task",
            {"auth_token": "test-token", "task_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        assert any(field in content.lower() for field in ["id", "subject", "task"])

    async def test_call_get_task_by_ref(self, mcp_client: Client) -> None:
        """Test calling taiga_get_task_by_ref tool."""
        result = await mcp_client.call_tool(
            "taiga_get_task_by_ref",
            {"auth_token": "test-token", "project_id": 1, "ref": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_delete_task(self, mcp_client: Client) -> None:
        """Test calling taiga_delete_task tool."""
        result = await mcp_client.call_tool(
            "taiga_delete_task",
            {"auth_token": "test-token", "task_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0


@pytest.mark.asyncio
class TestTaskAttachmentTools:
    """Test Task attachment tools."""

    async def test_call_list_task_attachments(self, mcp_client: Client) -> None:
        """Test calling taiga_list_task_attachments tool."""
        result = await mcp_client.call_tool(
            "taiga_list_task_attachments",
            {
                "auth_token": "test-token",
                "project_id": 1,
                "task_id": 1,
            },
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_list_task_attachments_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_list_task_attachments has correct parameters."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_list_task_attachments"), None)

        assert tool is not None
        schema = tool.inputSchema
        properties = schema.get("properties", {})

        assert "auth_token" in properties
        assert "task_id" in properties


@pytest.mark.asyncio
class TestTaskVotingWatchingTools:
    """Test Task voting and watching tools."""

    async def test_call_upvote_task(self, mcp_client: Client) -> None:
        """Test calling taiga_upvote_task tool."""
        result = await mcp_client.call_tool(
            "taiga_upvote_task",
            {"auth_token": "test-token", "task_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_downvote_task(self, mcp_client: Client) -> None:
        """Test calling taiga_downvote_task tool."""
        result = await mcp_client.call_tool(
            "taiga_downvote_task",
            {"auth_token": "test-token", "task_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_watch_task(self, mcp_client: Client) -> None:
        """Test calling taiga_watch_task tool."""
        result = await mcp_client.call_tool(
            "taiga_watch_task",
            {"auth_token": "test-token", "task_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_unwatch_task(self, mcp_client: Client) -> None:
        """Test calling taiga_unwatch_task tool."""
        result = await mcp_client.call_tool(
            "taiga_unwatch_task",
            {"auth_token": "test-token", "task_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0


@pytest.mark.asyncio
class TestTaskCommentTools:
    """Test Task comment tools."""

    async def test_call_get_task_history(self, mcp_client: Client) -> None:
        """Test calling taiga_get_task_history tool."""
        result = await mcp_client.call_tool(
            "taiga_get_task_history",
            {"auth_token": "test-token", "task_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_edit_task_comment(self, mcp_client: Client) -> None:
        """Test calling taiga_edit_task_comment tool."""
        result = await mcp_client.call_tool(
            "taiga_edit_task_comment",
            {
                "auth_token": "test-token",
                "task_id": 1,
                "comment_id": "comment-uuid",
                "comment": "Updated comment",
            },
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0


@pytest.mark.asyncio
class TestTaskToolsResponseFormat:
    """Test TaskTools return consistent response format."""

    async def test_list_tasks_returns_array(self, mcp_client: Client) -> None:
        """Verify list_tasks returns an array format."""
        result = await mcp_client.call_tool(
            "taiga_list_tasks",
            {"auth_token": "test-token"},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0
        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Response should be a list or contain list representation
        assert "[" in content or "task" in content.lower()

    async def test_get_task_returns_dict(self, mcp_client: Client) -> None:
        """Verify get_task returns a dict format."""
        result = await mcp_client.call_tool(
            "taiga_get_task",
            {"auth_token": "test-token", "task_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0
        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Response should be a dict or contain dict representation
        assert "{" in content or "id" in content.lower()
