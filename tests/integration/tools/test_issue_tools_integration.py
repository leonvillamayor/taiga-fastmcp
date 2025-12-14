"""
Integration tests for IssueTools.

These tests validate that issue tools are correctly registered
in the FastMCP server and can be called through the MCP protocol.
"""

import pytest
from fastmcp import Client

from tests.integration.tools.conftest import get_expected_tool_names


@pytest.mark.asyncio
class TestIssueToolsRegistration:
    """Test IssueTools registration in FastMCP server."""

    async def test_issue_tools_are_registered(self, mcp_client: Client) -> None:
        """Verify all issue tools are registered with correct names."""
        tools = await mcp_client.list_tools()
        tool_names = [tool.name for tool in tools]

        expected_issue_tools = get_expected_tool_names()["issue"]
        for tool_name in expected_issue_tools:
            assert tool_name in tool_names, f"Tool {tool_name} not registered"

    async def test_issue_tools_have_taiga_prefix(self, mcp_client: Client) -> None:
        """Verify all issue tools follow taiga_ naming convention."""
        tools = await mcp_client.list_tools()
        issue_tools = [t for t in tools if "issue" in t.name.lower()]

        for tool in issue_tools:
            assert tool.name.startswith("taiga_"), f"Tool {tool.name} does not have taiga_ prefix"

    async def test_core_issue_tools_count(self, mcp_client: Client) -> None:
        """Verify minimum number of issue tools are registered."""
        tools = await mcp_client.list_tools()
        issue_tools = [t for t in tools if "issue" in t.name.lower()]

        # Should have CRUD + attachments + comments + voting/watching
        assert len(issue_tools) >= 10, f"Expected at least 10 issue tools, got {len(issue_tools)}"


@pytest.mark.asyncio
class TestIssueToolsParameters:
    """Test IssueTools have correct parameter definitions."""

    async def test_list_issues_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_list_issues has auth_token parameter."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_list_issues"), None)

        assert tool is not None, "taiga_list_issues tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "auth_token" in required, "auth_token should be required"

    async def test_create_issue_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_create_issue has required parameters."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_create_issue"), None)

        assert tool is not None, "taiga_create_issue tool not found"
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

    async def test_get_issue_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_get_issue has issue_id parameter."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_get_issue"), None)

        assert tool is not None, "taiga_get_issue tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "issue_id" in properties, "issue_id parameter not defined"
        assert "issue_id" in required, "issue_id should be required"

    async def test_get_issue_by_ref_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_get_issue_by_ref has required parameters."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_get_issue_by_ref"), None)

        assert tool is not None, "taiga_get_issue_by_ref tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "project_id" in properties, "project_id parameter not defined"
        assert "ref" in properties, "ref parameter not defined"

    async def test_update_issue_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_update_issue has required parameters."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_update_issue"), None)

        assert tool is not None, "taiga_update_issue tool not found"
        assert tool.inputSchema is not None

        schema = tool.inputSchema
        properties = schema.get("properties", {})
        schema.get("required", [])

        assert "auth_token" in properties, "auth_token parameter not defined"
        assert "issue_id" in properties, "issue_id parameter not defined"


@pytest.mark.asyncio
class TestIssueToolsExecution:
    """Test IssueTools execution through MCP protocol."""

    async def test_call_list_issues(self, mcp_client: Client) -> None:
        """Test calling taiga_list_issues tool."""
        result = await mcp_client.call_tool(
            "taiga_list_issues",
            {"auth_token": "test-token"},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Should return list of issues
        assert "issue" in content.lower() or "[" in content

    async def test_call_create_issue(self, mcp_client: Client) -> None:
        """Test calling taiga_create_issue tool."""
        result = await mcp_client.call_tool(
            "taiga_create_issue",
            {
                "auth_token": "test-token",
                "project_id": 1,
                "subject": "Test Issue",
                "type": 1,
                "priority": 2,
                "severity": 3,
            },
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Should return created issue info
        assert any(field in content.lower() for field in ["id", "subject", "issue", "project"])

    async def test_call_get_issue(self, mcp_client: Client) -> None:
        """Test calling taiga_get_issue tool."""
        result = await mcp_client.call_tool(
            "taiga_get_issue",
            {"auth_token": "test-token", "issue_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        assert any(field in content.lower() for field in ["id", "subject", "issue"])

    async def test_call_get_issue_by_ref(self, mcp_client: Client) -> None:
        """Test calling taiga_get_issue_by_ref tool."""
        result = await mcp_client.call_tool(
            "taiga_get_issue_by_ref",
            {"auth_token": "test-token", "project_id": 1, "ref": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_delete_issue(self, mcp_client: Client) -> None:
        """Test calling taiga_delete_issue tool."""
        result = await mcp_client.call_tool(
            "taiga_delete_issue",
            {"auth_token": "test-token", "issue_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0


@pytest.mark.asyncio
class TestIssueAttachmentTools:
    """Test Issue attachment tools."""

    async def test_call_get_issue_attachments(self, mcp_client: Client) -> None:
        """Test calling taiga_get_issue_attachments tool."""
        result = await mcp_client.call_tool(
            "taiga_get_issue_attachments",
            {"auth_token": "test-token", "issue_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_get_issue_attachments_parameters(self, mcp_client: Client) -> None:
        """Verify taiga_get_issue_attachments has correct parameters."""
        tools = await mcp_client.list_tools()
        tool = next((t for t in tools if t.name == "taiga_get_issue_attachments"), None)

        assert tool is not None
        schema = tool.inputSchema
        properties = schema.get("properties", {})

        assert "auth_token" in properties
        assert "issue_id" in properties


@pytest.mark.asyncio
class TestIssueVotingWatchingTools:
    """Test Issue voting and watching tools."""

    async def test_call_upvote_issue(self, mcp_client: Client) -> None:
        """Test calling taiga_upvote_issue tool."""
        result = await mcp_client.call_tool(
            "taiga_upvote_issue",
            {"auth_token": "test-token", "issue_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_downvote_issue(self, mcp_client: Client) -> None:
        """Test calling taiga_downvote_issue tool."""
        result = await mcp_client.call_tool(
            "taiga_downvote_issue",
            {"auth_token": "test-token", "issue_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_watch_issue(self, mcp_client: Client) -> None:
        """Test calling taiga_watch_issue tool."""
        result = await mcp_client.call_tool(
            "taiga_watch_issue",
            {"auth_token": "test-token", "issue_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_unwatch_issue(self, mcp_client: Client) -> None:
        """Test calling taiga_unwatch_issue tool."""
        result = await mcp_client.call_tool(
            "taiga_unwatch_issue",
            {"auth_token": "test-token", "issue_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0


@pytest.mark.asyncio
class TestIssueCommentTools:
    """Test Issue comment tools."""

    async def test_call_get_issue_history(self, mcp_client: Client) -> None:
        """Test calling taiga_get_issue_history tool."""
        result = await mcp_client.call_tool(
            "taiga_get_issue_history",
            {"auth_token": "test-token", "issue_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0

    async def test_call_edit_issue_comment(self, mcp_client: Client) -> None:
        """Test calling taiga_edit_issue_comment tool."""
        result = await mcp_client.call_tool(
            "taiga_edit_issue_comment",
            {
                "auth_token": "test-token",
                "issue_id": 1,
                "comment_id": "comment-uuid",
                "comment": "Updated comment",
            },
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0


@pytest.mark.asyncio
class TestIssueFiltersTools:
    """Test Issue filter tools."""

    async def test_call_get_issue_filters(self, mcp_client: Client) -> None:
        """Test calling taiga_get_issue_filters tool."""
        result = await mcp_client.call_tool(
            "taiga_get_issue_filters",
            {"auth_token": "test-token", "project_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0


@pytest.mark.asyncio
class TestIssueToolsResponseFormat:
    """Test IssueTools return consistent response format."""

    async def test_list_issues_returns_array(self, mcp_client: Client) -> None:
        """Verify list_issues returns an array format."""
        result = await mcp_client.call_tool(
            "taiga_list_issues",
            {"auth_token": "test-token"},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0
        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Response should be a list or contain list representation
        assert "[" in content or "issue" in content.lower()

    async def test_get_issue_returns_dict(self, mcp_client: Client) -> None:
        """Verify get_issue returns a dict format."""
        result = await mcp_client.call_tool(
            "taiga_get_issue",
            {"auth_token": "test-token", "issue_id": 1},
        )

        assert result is not None
        assert not result.is_error, f"Tool returned error: {result.content}"
        assert result.content and len(result.content) > 0
        content = (
            result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        )
        # Response should be a dict or contain dict representation
        assert "{" in content or "id" in content.lower()
