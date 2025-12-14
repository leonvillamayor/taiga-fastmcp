"""
Integration tests for EpicTools.

These tests validate that epic tools are correctly registered
in the FastMCP server and can be called through the MCP protocol.
"""

import pytest
from fastmcp import Client

from tests.integration.tools.conftest import get_expected_tool_names


@pytest.mark.asyncio
class TestEpicToolsRegistration:
    """Test EpicTools registration in FastMCP server."""

    async def test_epic_tools_are_registered(self, mcp_client: Client) -> None:
        """Verify all epic tools are registered with correct names."""
        tools = await mcp_client.list_tools()
        tool_names = [tool.name for tool in tools]

        expected_epic_tools = get_expected_tool_names()["epic"]
        for tool_name in expected_epic_tools:
            assert tool_name in tool_names, f"Tool {tool_name} not registered"

    async def test_epic_tools_have_taiga_prefix(self, mcp_client: Client) -> None:
        """Verify all epic tools follow taiga_ naming convention."""
        tools = await mcp_client.list_tools()
        epic_tools = [t for t in tools if "epic" in t.name.lower()]

        for tool in epic_tools:
            assert tool.name.startswith("taiga_"), f"Tool {tool.name} does not have taiga_ prefix"

    async def test_core_epic_tools_count(self, mcp_client: Client) -> None:
        """Verify minimum number of epic tools are registered."""
        tools = await mcp_client.list_tools()
        epic_tools = [t for t in tools if "epic" in t.name.lower()]

        # Should have CRUD + attachment + voting + watching tools
        assert len(epic_tools) >= 10, f"Expected at least 10 epic tools, got {len(epic_tools)}"


@pytest.mark.asyncio
class TestEpicToolsParameters:
    """Test EpicTools have correct parameter definitions."""

    async def test_list_epics_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_list_epics has auth_token parameter."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_list_epics"), None)

        assert tool is not None, "taiga_list_epics tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "auth_token" in required, "auth_token should be required"

    async def test_create_epic_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_create_epic has required parameters."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_create_epic"), None)

        assert tool is not None, "taiga_create_epic tool not found"
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

    async def test_get_epic_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_get_epic has epic_id parameter."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_get_epic"), None)

        assert tool is not None, "taiga_get_epic tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "epic_id" in properties, "epic_id parameter not defined"
        assert "epic_id" in required, "epic_id should be required"

    async def test_get_epic_by_ref_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_get_epic_by_ref has required parameters."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_get_epic_by_ref"), None)

        assert tool is not None, "taiga_get_epic_by_ref tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "project_id" in properties, "project_id parameter not defined"
        assert "ref" in properties, "ref parameter not defined"

    async def test_update_epic_full_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_update_epic_full has required parameters."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_update_epic_full"), None)

        assert tool is not None, "taiga_update_epic_full tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "epic_id" in properties, "epic_id parameter not defined"
        assert "subject" in properties, "subject parameter not defined"


@pytest.mark.asyncio
class TestEpicToolsExecution:
    """Test EpicTools execution through MCP protocol."""

    async def test_call_list_epics(self, mcp_client: Client) -> None:
        """Test calling taiga_list_epics tool."""
        result = await mcp_client.call_tool(
            "taiga_list_epics",
            {"auth_token": "test-token"},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Should return list of epics
        assert "epic" in content.lower() or "[" in content

    async def test_call_create_epic(self, mcp_client: Client) -> None:
        """Test calling taiga_create_epic tool."""
        result = await mcp_client.call_tool(
            "taiga_create_epic",
            {
                "auth_token": "test-token",
                "project_id": 1,
                "subject": "Test Epic",
            },
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Should return created epic info
        assert any(field in content.lower() for field in ["id", "subject", "epic", "project"])

    async def test_call_get_epic(self, mcp_client: Client) -> None:
        """Test calling taiga_get_epic tool."""
        result = await mcp_client.call_tool(
            "taiga_get_epic",
            {"auth_token": "test-token", "epic_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        assert any(field in content.lower() for field in ["id", "subject", "epic"])

    async def test_call_get_epic_by_ref(self, mcp_client: Client) -> None:
        """Test calling taiga_get_epic_by_ref tool."""
        result = await mcp_client.call_tool(
            "taiga_get_epic_by_ref",
            {"auth_token": "test-token", "project_id": 1, "ref": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_delete_epic(self, mcp_client: Client) -> None:
        """Test calling taiga_delete_epic tool."""
        result = await mcp_client.call_tool(
            "taiga_delete_epic",
            {"auth_token": "test-token", "epic_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0


@pytest.mark.asyncio
class TestEpicRelatedUserstoriesTools:
    """Test Epic related user stories tools."""

    async def test_call_list_epic_related_userstories(self, mcp_client: Client) -> None:
        """Test calling taiga_list_epic_related_userstories tool."""
        result = await mcp_client.call_tool(
            "taiga_list_epic_related_userstories",
            {"auth_token": "test-token", "epic_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_create_epic_related_userstory(self, mcp_client: Client) -> None:
        """Test calling taiga_create_epic_related_userstory tool."""
        result = await mcp_client.call_tool(
            "taiga_create_epic_related_userstory",
            {
                "auth_token": "test-token",
                "epic_id": 1,
                "user_story_id": 100,
            },
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0


@pytest.mark.asyncio
class TestEpicVotingWatchingTools:
    """Test Epic voting and watching tools."""

    async def test_call_upvote_epic(self, mcp_client: Client) -> None:
        """Test calling taiga_upvote_epic tool."""
        result = await mcp_client.call_tool(
            "taiga_upvote_epic",
            {"auth_token": "test-token", "epic_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_downvote_epic(self, mcp_client: Client) -> None:
        """Test calling taiga_downvote_epic tool."""
        result = await mcp_client.call_tool(
            "taiga_downvote_epic",
            {"auth_token": "test-token", "epic_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_watch_epic(self, mcp_client: Client) -> None:
        """Test calling taiga_watch_epic tool."""
        result = await mcp_client.call_tool(
            "taiga_watch_epic",
            {"auth_token": "test-token", "epic_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_unwatch_epic(self, mcp_client: Client) -> None:
        """Test calling taiga_unwatch_epic tool."""
        result = await mcp_client.call_tool(
            "taiga_unwatch_epic",
            {"auth_token": "test-token", "epic_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0


@pytest.mark.asyncio
class TestEpicToolsResponseFormat:
    """Test EpicTools return consistent response format."""

    async def test_list_epics_returns_array(self, mcp_client: Client) -> None:
        """Verify list_epics returns an array format."""
        result = await mcp_client.call_tool(
            "taiga_list_epics",
            {"auth_token": "test-token"},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0
        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Response should be a list or contain list representation
        assert "[" in content or "epic" in content.lower()

    async def test_get_epic_returns_dict(self, mcp_client: Client) -> None:
        """Verify get_epic returns a dict format."""
        result = await mcp_client.call_tool(
            "taiga_get_epic",
            {"auth_token": "test-token", "epic_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0
        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Response should be a dict or contain dict representation
        assert "{" in content or "id" in content.lower()
