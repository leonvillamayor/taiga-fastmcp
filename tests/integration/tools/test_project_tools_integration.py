"""
Integration tests for ProjectTools.

These tests validate that project tools are correctly registered
in the FastMCP server and can be called through the MCP protocol.
"""

import pytest
from fastmcp import Client

from tests.integration.tools.conftest import get_expected_tool_names


@pytest.mark.asyncio
class TestProjectToolsRegistration:
    """Test ProjectTools registration in FastMCP server."""

    async def test_project_tools_are_registered(self, mcp_client: Client) -> None:
        """Verify all project tools are registered with correct names."""
        tools = await mcp_client.list_tools()
        tool_names = [tool.name for tool in tools]

        expected_project_tools = get_expected_tool_names()["project"]
        for tool_name in expected_project_tools:
            assert tool_name in tool_names, f"Tool {tool_name} not registered"

    async def test_project_tools_have_taiga_prefix(self, mcp_client: Client) -> None:
        """Verify all project tools follow taiga_ naming convention."""
        tools = await mcp_client.list_tools()
        project_tools = [t for t in tools if "project" in t.name.lower()]

        for tool in project_tools:
            assert tool.name.startswith("taiga_"), f"Tool {tool.name} does not have taiga_ prefix"

    async def test_core_project_tools_count(self, mcp_client: Client) -> None:
        """Verify minimum number of project tools are registered."""
        tools = await mcp_client.list_tools()
        project_tools = [t for t in tools if "project" in t.name.lower()]

        # Should have at least CRUD operations + extras
        assert len(project_tools) >= 5, (
            f"Expected at least 5 project tools, got {len(project_tools)}"
        )


@pytest.mark.asyncio
class TestProjectToolsParameters:
    """Test ProjectTools have correct parameter definitions."""

    async def test_list_projects_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_list_projects has auth_token parameter."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_list_projects"), None)

        assert tool is not None, "taiga_list_projects tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "auth_token" in required, "auth_token should be required"

    async def test_create_project_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_create_project has required parameters."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_create_project"), None)

        assert tool is not None, "taiga_create_project tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "name" in properties, "name parameter not defined"
        assert "auth_token" in required, "auth_token should be required"
        assert "name" in required, "name should be required"

    async def test_get_project_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_get_project has project_id or slug parameter."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_get_project"), None)

        assert tool is not None, "taiga_get_project tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})

        assert "auth_token" in properties, "auth_token parameter not defined"
        # Should have project_id or slug
        has_project_id = "project_id" in properties
        has_slug = "slug" in properties
        assert has_project_id or has_slug, "project_id or slug parameter required"

    async def test_update_project_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_update_project has required parameters."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_update_project"), None)

        assert tool is not None, "taiga_update_project tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "project_id" in properties, "project_id parameter not defined"
        assert "auth_token" in required, "auth_token should be required"
        assert "project_id" in required, "project_id should be required"


@pytest.mark.asyncio
class TestProjectToolsExecution:
    """Test ProjectTools execution through MCP protocol."""

    async def test_call_list_projects(self, mcp_client: Client) -> None:
        """Test calling taiga_list_projects tool."""
        result = await mcp_client.call_tool(
            "taiga_list_projects",
            {"auth_token": "test-token"},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Should return list of projects
        assert "project" in content.lower() or "[" in content

    async def test_call_create_project(self, mcp_client: Client) -> None:
        """Test calling taiga_create_project tool."""
        result = await mcp_client.call_tool(
            "taiga_create_project",
            {"auth_token": "test-token", "name": "Test Project"},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Should return created project info
        assert any(field in content.lower() for field in ["id", "name", "project", "slug"])

    async def test_call_get_project(self, mcp_client: Client) -> None:
        """Test calling taiga_get_project tool."""
        result = await mcp_client.call_tool(
            "taiga_get_project",
            {"auth_token": "test-token", "project_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        assert any(field in content.lower() for field in ["id", "name", "project"])

    async def test_call_get_project_stats(self, mcp_client: Client) -> None:
        """Test calling taiga_get_project_stats tool."""
        result = await mcp_client.call_tool(
            "taiga_get_project_stats",
            {"auth_token": "test-token", "project_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0


@pytest.mark.asyncio
class TestProjectToolsResponseFormat:
    """Test ProjectTools return consistent response format."""

    async def test_list_projects_returns_array(self, mcp_client: Client) -> None:
        """Verify list_projects returns an array format."""
        result = await mcp_client.call_tool(
            "taiga_list_projects",
            {"auth_token": "test-token"},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0
        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Response should be a list or contain list representation
        assert "[" in content or "project" in content.lower()

    async def test_get_project_returns_dict(self, mcp_client: Client) -> None:
        """Verify get_project returns a dict format."""
        result = await mcp_client.call_tool(
            "taiga_get_project",
            {"auth_token": "test-token", "project_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0
        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Response should be a dict or contain dict representation
        assert "{" in content or "id" in content.lower()

    async def test_delete_project_returns_confirmation(self, mcp_client: Client) -> None:
        """Verify delete_project returns confirmation."""
        result = await mcp_client.call_tool(
            "taiga_delete_project",
            {"auth_token": "test-token", "project_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0
