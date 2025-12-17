"""
Integration tests for UserStoryTools.

These tests validate that user story tools are correctly registered
in the FastMCP server and can be called through the MCP protocol.
"""

import pytest
from fastmcp import Client

from tests.integration.tools.conftest import get_expected_tool_names


@pytest.mark.asyncio
class TestUserStoryToolsRegistration:
    """Test UserStoryTools registration in FastMCP server."""

    async def test_userstory_tools_are_registered(self, mcp_client: Client) -> None:
        """Verify all userstory tools are registered with correct names."""
        tools = await mcp_client.list_tools()
        tool_names = [tool.name for tool in tools]

        expected_userstory_tools = get_expected_tool_names()["userstory"]
        for tool_name in expected_userstory_tools:
            assert tool_name in tool_names, f"Tool {tool_name} not registered"

    async def test_userstory_tools_have_taiga_prefix(self, mcp_client: Client) -> None:
        """Verify all userstory tools follow taiga_ naming convention."""
        tools = await mcp_client.list_tools()
        userstory_tools = [t for t in tools if "userstor" in t.name.lower()]

        for tool in userstory_tools:
            assert tool.name.startswith("taiga_"), f"Tool {tool.name} does not have taiga_ prefix"

    async def test_core_userstory_tools_count(self, mcp_client: Client) -> None:
        """Verify minimum number of userstory tools are registered."""
        tools = await mcp_client.list_tools()
        userstory_tools = [t for t in tools if "userstor" in t.name.lower()]

        # Should have CRUD + bulk + voting/watching operations
        assert (
            len(userstory_tools) >= 5
        ), f"Expected at least 5 userstory tools, got {len(userstory_tools)}"


@pytest.mark.asyncio
class TestUserStoryToolsParameters:
    """Test UserStoryTools have correct parameter definitions."""

    async def test_list_userstories_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_list_userstories has auth_token parameter."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_list_userstories"), None)

        assert tool is not None, "taiga_list_userstories tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "auth_token" in required, "auth_token should be required"

    async def test_create_userstory_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_create_userstory has required parameters."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_create_userstory"), None)

        assert tool is not None, "taiga_create_userstory tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "project_id" in properties, "project_id parameter not defined"
        assert "subject" in properties, "subject parameter not defined"
        assert "auth_token" in required, "auth_token should be required"

    async def test_get_userstory_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_get_userstory has userstory_id parameter."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_get_userstory"), None)

        assert tool is not None, "taiga_get_userstory tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        # Either userstory_id or ref should be available
        has_id = "userstory_id" in properties
        has_ref = "ref" in properties
        assert has_id or has_ref, "userstory_id or ref parameter required"

    async def test_update_userstory_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_update_userstory has required parameters."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_update_userstory"), None)

        assert tool is not None, "taiga_update_userstory tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "userstory_id" in properties, "userstory_id parameter not defined"


@pytest.mark.asyncio
class TestUserStoryToolsExecution:
    """Test UserStoryTools execution through MCP protocol."""

    async def test_call_list_userstories(self, mcp_client: Client) -> None:
        """Test calling taiga_list_userstories tool."""
        result = await mcp_client.call_tool(
            "taiga_list_userstories",
            {"auth_token": "test-token"},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Should return list of user stories
        assert "story" in content.lower() or "[" in content

    async def test_call_create_userstory(self, mcp_client: Client) -> None:
        """Test calling taiga_create_userstory tool."""
        result = await mcp_client.call_tool(
            "taiga_create_userstory",
            {
                "auth_token": "test-token",
                "project_id": 1,
                "subject": "Test User Story",
            },
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Should return created userstory info
        assert any(field in content.lower() for field in ["id", "subject", "story", "project"])

    async def test_call_get_userstory(self, mcp_client: Client) -> None:
        """Test calling taiga_get_userstory tool."""
        result = await mcp_client.call_tool(
            "taiga_get_userstory",
            {"auth_token": "test-token", "userstory_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        assert any(field in content.lower() for field in ["id", "subject", "story"])

    async def test_call_delete_userstory(self, mcp_client: Client) -> None:
        """Test calling taiga_delete_userstory tool."""
        result = await mcp_client.call_tool(
            "taiga_delete_userstory",
            {"auth_token": "test-token", "userstory_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0


@pytest.mark.asyncio
class TestUserStoryBulkOperations:
    """Test UserStory bulk operation tools."""

    async def test_call_bulk_create_userstories(self, mcp_client: Client) -> None:
        """Test calling taiga_bulk_create_userstories tool."""
        result = await mcp_client.call_tool(
            "taiga_bulk_create_userstories",
            {
                "auth_token": "test-token",
                "project_id": 1,
                "bulk_stories": "Story 1\nStory 2",
            },
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_bulk_update_userstories(self, mcp_client: Client) -> None:
        """Test calling taiga_bulk_update_userstories tool."""
        result = await mcp_client.call_tool(
            "taiga_bulk_update_userstories",
            {
                "auth_token": "test-token",
                "story_ids": [1, 2],
            },
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_bulk_delete_userstories(self, mcp_client: Client) -> None:
        """Test calling taiga_bulk_delete_userstories tool."""
        result = await mcp_client.call_tool(
            "taiga_bulk_delete_userstories",
            {
                "auth_token": "test-token",
                "story_ids": [1, 2],
            },
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0


@pytest.mark.asyncio
class TestUserStoryVotingWatchingTools:
    """Test UserStory voting and watching tools."""

    async def test_call_upvote_userstory(self, mcp_client: Client) -> None:
        """Test calling taiga_upvote_userstory tool."""
        result = await mcp_client.call_tool(
            "taiga_upvote_userstory",
            {"auth_token": "test-token", "userstory_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_downvote_userstory(self, mcp_client: Client) -> None:
        """Test calling taiga_downvote_userstory tool."""
        result = await mcp_client.call_tool(
            "taiga_downvote_userstory",
            {"auth_token": "test-token", "userstory_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_watch_userstory(self, mcp_client: Client) -> None:
        """Test calling taiga_watch_userstory tool."""
        result = await mcp_client.call_tool(
            "taiga_watch_userstory",
            {"auth_token": "test-token", "userstory_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_unwatch_userstory(self, mcp_client: Client) -> None:
        """Test calling taiga_unwatch_userstory tool."""
        result = await mcp_client.call_tool(
            "taiga_unwatch_userstory",
            {"auth_token": "test-token", "userstory_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0


@pytest.mark.asyncio
class TestUserStoryToolsResponseFormat:
    """Test UserStoryTools return consistent response format."""

    async def test_list_userstories_returns_array(self, mcp_client: Client) -> None:
        """Verify list_userstories returns an array format."""
        result = await mcp_client.call_tool(
            "taiga_list_userstories",
            {"auth_token": "test-token"},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0
        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Response should be a list or contain list representation
        assert "[" in content or "story" in content.lower()

    async def test_get_userstory_returns_dict(self, mcp_client: Client) -> None:
        """Verify get_userstory returns a dict format."""
        result = await mcp_client.call_tool(
            "taiga_get_userstory",
            {"auth_token": "test-token", "userstory_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0
        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Response should be a dict or contain dict representation
        assert "{" in content or "id" in content.lower()
