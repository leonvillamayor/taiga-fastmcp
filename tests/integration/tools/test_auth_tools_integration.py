"""
Integration tests for AuthTools.

These tests validate that auth tools are correctly registered
in the FastMCP server and can be called through the MCP protocol.
"""

import pytest
from fastmcp import Client

from tests.integration.tools.conftest import get_expected_tool_names


@pytest.mark.asyncio
class TestAuthToolsRegistration:
    """Test AuthTools registration in FastMCP server."""

    async def test_auth_tools_are_registered(self, mcp_client: Client) -> None:
        """Verify all auth tools are registered with correct names."""
        tools = await mcp_client.list_tools()
        tool_names = [tool.name for tool in tools]

        expected_auth_tools = get_expected_tool_names()["auth"]
        for tool_name in expected_auth_tools:
            assert tool_name in tool_names, f"Tool {tool_name} not registered"

    async def test_auth_tools_have_taiga_prefix(self, mcp_client: Client) -> None:
        """Verify all auth tools follow taiga_ naming convention."""
        tools = await mcp_client.list_tools()
        auth_tools = [t for t in tools if "auth" in t.name.lower()]

        for tool in auth_tools:
            assert tool.name.startswith("taiga_"), f"Tool {tool.name} does not have taiga_ prefix"


@pytest.mark.asyncio
class TestAuthToolsParameters:
    """Test AuthTools have correct parameter definitions."""

    async def test_authenticate_has_required_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_authenticate has username and password parameters."""
        tools = await mcp_client.list_tools()
        auth_tool = next((t for t in tools if t.name == "taiga_authenticate"), None)

        assert auth_tool is not None, "taiga_authenticate tool not found"
        assert auth_tool.inputSchema is not None, "Tool has no input schema"

        schema = auth_tool.inputSchema
        properties = schema.get("properties", {})

        # username and password are optional but should be defined
        assert "username" in properties, "username parameter not defined"
        assert "password" in properties, "password parameter not defined"

    async def test_refresh_token_parameter(self, mcp_client: Client) -> None:
        """Verify taiga_refresh_token has refresh_token parameter."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_refresh_token"), None)

        assert tool is not None, "taiga_refresh_token tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})

        assert "refresh_token" in properties, "refresh_token parameter not defined"

    async def test_get_current_user_has_auth_token(self, mcp_client: Client) -> None:
        """Verify taiga_get_current_user has auth_token parameter."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_get_current_user"), None)

        assert tool is not None, "taiga_get_current_user tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})

        assert "auth_token" in properties, "auth_token parameter not defined"


@pytest.mark.asyncio
class TestAuthToolsExecution:
    """Test AuthTools execution through MCP protocol."""

    async def test_call_authenticate(self, mcp_client: Client) -> None:
        """Test calling taiga_authenticate tool."""
        result = await mcp_client.call_tool(
            "taiga_authenticate",
            {"username": "testuser", "password": "testpass"},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        # Result should contain auth token info
        assert result.content and len(result.content) > 0
        # FastMCP returns content as list of TextContent
        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        assert "auth_token" in content or "token" in content.lower()

    async def test_call_check_auth(self, mcp_client: Client) -> None:
        """Test calling taiga_check_auth tool."""
        result = await mcp_client.call_tool("taiga_check_auth", {})

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_logout(self, mcp_client: Client) -> None:
        """Test calling taiga_logout tool."""
        result = await mcp_client.call_tool("taiga_logout", {})

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0


@pytest.mark.asyncio
class TestAuthToolsResponseFormat:
    """Test AuthTools return consistent response format."""

    async def test_authenticate_returns_dict_format(self, mcp_client: Client) -> None:
        """Verify authenticate returns properly formatted response."""
        result = await mcp_client.call_tool(
            "taiga_authenticate",
            {"username": "testuser", "password": "testpass"},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        # Response should be text content with JSON-like structure
        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        assert isinstance(content, str)
        # Should contain relevant auth fields
        assert any(field in content.lower() for field in ["auth_token", "token", "username", "id"])

    async def test_get_current_user_returns_user_info(self, mcp_client: Client) -> None:
        """Verify get_current_user returns user information."""
        result = await mcp_client.call_tool(
            "taiga_get_current_user",
            {"auth_token": "test-token"},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        assert isinstance(content, str)
        # Should contain user info fields
        assert any(field in content.lower() for field in ["username", "email", "id", "full_name"])
