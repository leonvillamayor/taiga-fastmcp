"""
Tests adicionales para cobertura completa de project_tools.py.
Cubre funciones, métodos sincrónicos, herramientas MCP y manejadores de excepciones.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.application.tools.project_tools import ProjectTools, get_taiga_client
from src.domain.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    ResourceNotFoundError,
    TaigaAPIError,
    ValidationError,
)


@pytest.fixture
def project_tools_instance():
    """Fixture que crea una instancia de ProjectTools con mocks."""
    mcp = FastMCP("Test")
    with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client
        tools = ProjectTools(mcp)
        tools.register_tools()
        tools._mock_client = mock_client
        tools._mock_client_cls = mock_client_cls
        yield tools


class TestGetTaigaClientFunction:
    """Tests para la función get_taiga_client."""

    @pytest.mark.unit
    @pytest.mark.projects
    def test_get_taiga_client_without_auth_token(self):
        """Verifica que get_taiga_client funciona sin token."""
        with patch("src.application.tools.project_tools.TaigaConfig"):
            with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client:
                mock_instance = MagicMock(spec=["some_method"])  # No auth_token attribute
                mock_client.return_value = mock_instance

                client = get_taiga_client()

                assert client is mock_instance

    @pytest.mark.unit
    @pytest.mark.projects
    def test_get_taiga_client_with_auth_token(self):
        """Verifica que get_taiga_client establece el token."""
        with patch("src.application.tools.project_tools.TaigaConfig"):
            with patch("src.application.tools.project_tools.TaigaAPIClient") as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance

                client = get_taiga_client(auth_token="test_token")

                assert client.auth_token == "test_token"


class TestProjectToolsSetClient:
    """Tests para el método set_client."""

    @pytest.mark.unit
    @pytest.mark.projects
    def test_set_client_success(self):
        """Verifica que set_client establece el cliente."""
        mcp = FastMCP("Test")
        tools = ProjectTools(mcp)
        mock_client = MagicMock()

        tools.set_client(mock_client)

        assert tools.client is mock_client
        assert tools._client is mock_client

    @pytest.mark.unit
    @pytest.mark.projects
    def test_set_client_with_none(self):
        """Verifica que set_client puede establecer None."""
        mcp = FastMCP("Test")
        tools = ProjectTools(mcp)
        tools.client = MagicMock()

        tools.set_client(None)

        assert tools.client is None


class TestSyncWrapperMethods:
    """Tests para los métodos sincrónicos wrapper."""

    @pytest.mark.unit
    @pytest.mark.projects
    def test_sync_list_projects_success(self):
        """Verifica que el wrapper list_projects sincrónico funciona."""
        mcp = FastMCP("Test")
        tools = ProjectTools(mcp)

        with patch("src.application.tools.project_tools.get_taiga_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.list_projects.return_value = [{"id": 1, "name": "Test"}]
            mock_get_client.return_value = mock_client

            result = tools.list_projects(auth_token="token")

            assert result["success"] is True
            assert result["data"] == [{"id": 1, "name": "Test"}]

    @pytest.mark.unit
    @pytest.mark.projects
    def test_sync_list_projects_error(self):
        """Verifica que list_projects maneja errores."""
        mcp = FastMCP("Test")
        tools = ProjectTools(mcp)

        with patch("src.application.tools.project_tools.get_taiga_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.list_projects.side_effect = Exception("Network error")
            mock_get_client.return_value = mock_client

            result = tools.list_projects()

            assert result["success"] is False
            assert "Network error" in result["error"]

    @pytest.mark.unit
    @pytest.mark.projects
    def test_sync_get_project_success(self):
        """Verifica que el wrapper get_project sincrónico funciona."""
        mcp = FastMCP("Test")
        tools = ProjectTools(mcp)

        with patch("src.application.tools.project_tools.get_taiga_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_project.return_value = {"id": 123, "name": "Test Project"}
            mock_get_client.return_value = mock_client

            result = tools.get_project(project_id=123)

            assert result["success"] is True
            assert result["data"]["id"] == 123

    @pytest.mark.unit
    @pytest.mark.projects
    def test_sync_get_project_error(self):
        """Verifica que get_project maneja errores."""
        mcp = FastMCP("Test")
        tools = ProjectTools(mcp)

        with patch("src.application.tools.project_tools.get_taiga_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_project.side_effect = Exception("Not found")
            mock_get_client.return_value = mock_client

            result = tools.get_project(project_id=999)

            assert result["success"] is False
            assert "Not found" in result["error"]

    @pytest.mark.unit
    @pytest.mark.projects
    def test_sync_create_project_success(self):
        """Verifica que el wrapper create_project sincrónico funciona."""
        mcp = FastMCP("Test")
        tools = ProjectTools(mcp)

        with patch("src.application.tools.project_tools.get_taiga_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.create_project.return_value = {"id": 1, "name": "New Project"}
            mock_get_client.return_value = mock_client

            result = tools.create_project(name="New Project")

            assert result["success"] is True
            assert result["data"]["id"] == 1

    @pytest.mark.unit
    @pytest.mark.projects
    def test_sync_create_project_error(self):
        """Verifica que create_project maneja errores."""
        mcp = FastMCP("Test")
        tools = ProjectTools(mcp)

        with patch("src.application.tools.project_tools.get_taiga_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.create_project.side_effect = Exception("Validation failed")
            mock_get_client.return_value = mock_client

            result = tools.create_project(name="Bad Project")

            assert result["success"] is False
            assert "Validation failed" in result["error"]


class TestCreateProjectRegisteredTool:
    """Tests para la herramienta registrada taiga_create_project."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_with_all_optional_params(self, project_tools_instance):
        """Verifica create_project con todos los parámetros opcionales."""
        project_tools_instance._mock_client.post = AsyncMock(
            return_value={
                "id": 1,
                "name": "Full Project",
                "description": "Description",
                "is_private": True,
                "is_backlog_activated": False,
                "is_issues_activated": True,
                "is_kanban_activated": True,
                "is_wiki_activated": False,
                "videoconferences": "jitsi",
                "videoconferences_extra_data": "extra",
                "total_milestones": 5,
                "total_story_points": 100,
                "tags": ["tag1", "tag2"],
            }
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_project"]

        result = await tool.fn(
            auth_token="token",
            name="Full Project",
            description="Description",
            is_private=True,
            is_backlog_activated=False,
            is_issues_activated=True,
            is_kanban_activated=True,
            is_wiki_activated=False,
            videoconferences="jitsi",
            videoconferences_extra_data="extra",
            total_milestones=5,
            total_story_points=100,
            tags=["tag1", "tag2"],
        )

        assert result["id"] == 1
        assert result["is_private"] is True
        assert "message" in result

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_validation_error(self, project_tools_instance):
        """Verifica manejo de ValidationError en create_project."""
        with patch(
            "src.application.tools.project_tools.validate_input",
            side_effect=ValidationError("Invalid project data"),
        ):
            tools = await project_tools_instance.mcp.get_tools()
            tool = tools["taiga_create_project"]

            with pytest.raises(ToolError, match="Invalid project data"):
                await tool.fn(auth_token="token", name="Test")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_duplicate_name_error(self, project_tools_instance):
        """Verifica manejo de nombre duplicado en create_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("duplicate key error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_project"]

        with pytest.raises(ToolError, match="already exists"):
            await tool.fn(auth_token="token", name="Duplicate")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en create_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=RuntimeError("Connection failed")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_project"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", name="Test")


class TestUpdateProjectExceptionHandlers:
    """Tests para manejadores de excepciones en update_project."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_update_project_validation_error(self, project_tools_instance):
        """Verifica manejo de ValidationError en update_project."""
        with patch(
            "src.application.tools.project_tools.validate_input",
            side_effect=ValidationError("Invalid update data"),
        ):
            tools = await project_tools_instance.mcp.get_tools()
            tool = tools["taiga_update_project"]

            with pytest.raises(ToolError, match="Invalid update data"):
                await tool.fn(auth_token="token", project_id=123, name="Updated")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_update_project_version_conflict(self, project_tools_instance):
        """Verifica manejo de conflicto de versión en update_project."""
        project_tools_instance._mock_client.patch = AsyncMock(
            side_effect=TaigaAPIError("version conflict detected")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_project"]

        with pytest.raises(ToolError, match="Version conflict"):
            await tool.fn(auth_token="token", project_id=123, name="Updated")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_update_project_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en update_project."""
        project_tools_instance._mock_client.patch = AsyncMock(
            side_effect=RuntimeError("Unexpected failure")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_project"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", project_id=123, name="Updated")


class TestDeleteProjectExceptionHandlers:
    """Tests para manejadores de excepciones en delete_project."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_delete_project_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en delete_project."""
        project_tools_instance._mock_client.delete = AsyncMock(
            side_effect=AuthenticationError("Token expired")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_project"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(auth_token="expired_token", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_delete_project_taiga_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en delete_project."""
        project_tools_instance._mock_client.delete = AsyncMock(
            side_effect=TaigaAPIError("Server error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_project"]

        with pytest.raises(ToolError, match="Failed to delete project"):
            await tool.fn(auth_token="token", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_delete_project_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en delete_project."""
        project_tools_instance._mock_client.delete = AsyncMock(
            side_effect=RuntimeError("Connection lost")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_project"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", project_id=123)


class TestLikeProjectExceptionHandlers:
    """Tests para manejadores de excepciones en like_project."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_like_project_not_found(self, project_tools_instance):
        """Verifica manejo de ResourceNotFoundError en like_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Project not found")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_like_project"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", project_id=999)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_like_project_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en like_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Invalid token")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_like_project"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(auth_token="invalid", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_like_project_taiga_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en like_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("Rate limit exceeded")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_like_project"]

        with pytest.raises(ToolError, match="Failed to like project"):
            await tool.fn(auth_token="token", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_like_project_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en like_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=RuntimeError("Unexpected error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_like_project"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", project_id=123)


class TestUnlikeProjectExceptionHandlers:
    """Tests para manejadores de excepciones en unlike_project."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_unlike_project_not_found(self, project_tools_instance):
        """Verifica manejo de ResourceNotFoundError en unlike_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Project not found")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_unlike_project"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", project_id=999)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_unlike_project_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en unlike_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Invalid token")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_unlike_project"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(auth_token="invalid", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_unlike_project_taiga_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en unlike_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_unlike_project"]

        with pytest.raises(ToolError, match="Failed to unlike project"):
            await tool.fn(auth_token="token", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_unlike_project_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en unlike_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=RuntimeError("Connection error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_unlike_project"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", project_id=123)


class TestWatchProjectExceptionHandlers:
    """Tests para manejadores de excepciones en watch_project."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_watch_project_not_found(self, project_tools_instance):
        """Verifica manejo de ResourceNotFoundError en watch_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Project not found")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_watch_project"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", project_id=999)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_watch_project_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en watch_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Token invalid")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_watch_project"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(auth_token="bad", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_watch_project_taiga_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en watch_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("Server unavailable")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_watch_project"]

        with pytest.raises(ToolError, match="Failed to watch project"):
            await tool.fn(auth_token="token", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_watch_project_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en watch_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=RuntimeError("Unknown error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_watch_project"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", project_id=123)


class TestUnwatchProjectExceptionHandlers:
    """Tests para manejadores de excepciones en unwatch_project."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_unwatch_project_not_found(self, project_tools_instance):
        """Verifica manejo de ResourceNotFoundError en unwatch_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Project not found")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_unwatch_project"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", project_id=999)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_unwatch_project_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en unwatch_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Expired")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_unwatch_project"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(auth_token="expired", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_unwatch_project_taiga_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en unwatch_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("API failure")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_unwatch_project"]

        with pytest.raises(ToolError, match="Failed to unwatch project"):
            await tool.fn(auth_token="token", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_unwatch_project_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en unwatch_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=RuntimeError("Network down")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_unwatch_project"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", project_id=123)


class TestDuplicateProjectExceptionHandlers:
    """Tests para manejadores de excepciones en duplicate_project."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_duplicate_project_validation_error(self, project_tools_instance):
        """Verifica manejo de ValidationError en duplicate_project."""
        with patch(
            "src.application.tools.project_tools.validate_input",
            side_effect=ValidationError("Invalid duplicate params"),
        ):
            tools = await project_tools_instance.mcp.get_tools()
            tool = tools["taiga_duplicate_project"]

            with pytest.raises(ToolError, match="Invalid duplicate params"):
                await tool.fn(auth_token="token", project_id=123, name="Copy")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_duplicate_project_not_found(self, project_tools_instance):
        """Verifica manejo de ResourceNotFoundError en duplicate_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Source not found")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_duplicate_project"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", project_id=999, name="Copy")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_duplicate_project_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en duplicate_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_duplicate_project"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(auth_token="bad", project_id=123, name="Copy")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_duplicate_project_taiga_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en duplicate_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("Duplication failed")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_duplicate_project"]

        with pytest.raises(ToolError, match="Failed to duplicate"):
            await tool.fn(auth_token="token", project_id=123, name="Copy")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_duplicate_project_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en duplicate_project."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=RuntimeError("Disk full")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_duplicate_project"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", project_id=123, name="Copy")


class TestGetProjectModulesExceptionHandlers:
    """Tests para manejadores de excepciones en get_project_modules."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_modules_not_found(self, project_tools_instance):
        """Verifica manejo de ResourceNotFoundError en get_project_modules."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=ResourceNotFoundError("Project not found")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_modules"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", project_id=999)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_modules_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en get_project_modules."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=AuthenticationError("Bad token")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_modules"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(auth_token="bad", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_modules_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en get_project_modules."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=RuntimeError("Server error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_modules"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", project_id=123)


class TestUpdateProjectModulesExceptionHandlers:
    """Tests para manejadores de excepciones en update_project_modules."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_update_project_modules_not_found(self, project_tools_instance):
        """Verifica manejo de ResourceNotFoundError en update_project_modules."""
        project_tools_instance._mock_client.patch = AsyncMock(
            side_effect=ResourceNotFoundError("Not found")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_project_modules"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", project_id=999)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_update_project_modules_permission_denied(self, project_tools_instance):
        """Verifica manejo de PermissionDeniedError en update_project_modules."""
        project_tools_instance._mock_client.patch = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_project_modules"]

        with pytest.raises(ToolError, match="permission"):
            await tool.fn(auth_token="token", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_update_project_modules_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en update_project_modules."""
        project_tools_instance._mock_client.patch = AsyncMock(
            side_effect=AuthenticationError("Auth error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_project_modules"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(auth_token="bad", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_update_project_modules_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en update_project_modules."""
        project_tools_instance._mock_client.patch = AsyncMock(
            side_effect=RuntimeError("Database error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_project_modules"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", project_id=123)


class TestGetProjectBySlugExceptionHandlers:
    """Tests para manejadores de excepciones en get_project_by_slug."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_by_slug_not_found(self, project_tools_instance):
        """Verifica manejo de ResourceNotFoundError en get_project_by_slug."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=ResourceNotFoundError("Slug not found")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_by_slug"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", slug="nonexistent-slug")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_by_slug_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en get_project_by_slug."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=AuthenticationError("Token expired")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_by_slug"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(auth_token="expired", slug="test-slug")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_by_slug_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en get_project_by_slug."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=RuntimeError("Timeout")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_by_slug"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", slug="test-slug")


class TestGetProjectIssuesStatsExceptionHandlers:
    """Tests para manejadores de excepciones en get_project_issues_stats."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_issues_stats_not_found(self, project_tools_instance):
        """Verifica manejo de ResourceNotFoundError en get_project_issues_stats."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=ResourceNotFoundError("Project not found")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_issues_stats"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", project_id=999)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_issues_stats_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en get_project_issues_stats."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=AuthenticationError("Invalid token")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_issues_stats"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(auth_token="invalid", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_issues_stats_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en get_project_issues_stats."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=RuntimeError("Database connection lost")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_issues_stats"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", project_id=123)


class TestProjectTagsExceptionHandlers:
    """Tests para manejadores de excepciones en operaciones de tags."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_tags_not_found(self, project_tools_instance):
        """Verifica manejo de ResourceNotFoundError en get_project_tags."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=ResourceNotFoundError("Not found")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_tags"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", project_id=999)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_tags_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en get_project_tags."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=RuntimeError("Error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_tags"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_tag_validation_error(self, project_tools_instance):
        """Verifica manejo de ValidationError en create_project_tag."""
        with patch(
            "src.application.tools.project_tools.validate_input",
            side_effect=ValidationError("Invalid tag"),
        ):
            tools = await project_tools_instance.mcp.get_tools()
            tool = tools["taiga_create_project_tag"]

            with pytest.raises(ToolError, match="Invalid tag"):
                await tool.fn(auth_token="token", project_id=123, tag="bad")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_tag_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en create_project_tag."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=RuntimeError("Error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_project_tag"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", project_id=123, tag="new-tag")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_edit_project_tag_validation_error(self, project_tools_instance):
        """Verifica manejo de ValidationError en edit_project_tag."""
        with patch(
            "src.application.tools.project_tools.validate_input",
            side_effect=ValidationError("Invalid edit params"),
        ):
            tools = await project_tools_instance.mcp.get_tools()
            tool = tools["taiga_edit_project_tag"]

            with pytest.raises(ToolError, match="Invalid edit params"):
                await tool.fn(
                    auth_token="token",
                    project_id=123,
                    from_tag="old",
                    to_tag="new",
                )

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_edit_project_tag_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en edit_project_tag."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=RuntimeError("Database error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_edit_project_tag"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(
                auth_token="token",
                project_id=123,
                from_tag="old",
                to_tag="new",
            )

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_delete_project_tag_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en delete_project_tag."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=RuntimeError("Error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_project_tag"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", project_id=123, tag="tag-to-delete")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_mix_project_tags_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en mix_project_tags."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=RuntimeError("Error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_mix_project_tags"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(
                auth_token="token",
                project_id=123,
                from_tags=["tag1", "tag2"],
                to_tag="merged",
            )


class TestExportProjectExceptionHandlers:
    """Tests para manejadores de excepciones en export_project."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_export_project_not_found(self, project_tools_instance):
        """Verifica manejo de ResourceNotFoundError en export_project."""
        project_tools_instance._mock_client.get_raw = AsyncMock(
            side_effect=ResourceNotFoundError("Project not found")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_export_project"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", project_id=999)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_export_project_permission_denied(self, project_tools_instance):
        """Verifica manejo de PermissionDeniedError en export_project."""
        project_tools_instance._mock_client.get_raw = AsyncMock(
            side_effect=PermissionDeniedError("No permission to export")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_export_project"]

        with pytest.raises(ToolError, match="permission"):
            await tool.fn(auth_token="token", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_export_project_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en export_project."""
        project_tools_instance._mock_client.get_raw = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_export_project"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(auth_token="bad", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_export_project_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en export_project."""
        project_tools_instance._mock_client.get_raw = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_export_project"]

        with pytest.raises(ToolError, match="API error"):
            await tool.fn(auth_token="token", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_export_project_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en export_project."""
        project_tools_instance._mock_client.get_raw = AsyncMock(
            side_effect=RuntimeError("Export failed")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_export_project"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_export_project_success(self, project_tools_instance):
        """Verifica export_project exitoso."""
        project_tools_instance._mock_client.get_raw = AsyncMock(
            return_value=b'{"project": "data"}'
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_export_project"]

        result = await tool.fn(auth_token="token", project_id=123)

        assert result == b'{"project": "data"}'


class TestBulkUpdateProjectsOrderExceptionHandlers:
    """Tests para manejadores de excepciones en bulk_update_projects_order."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_bulk_update_projects_order_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en bulk_update_projects_order."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_update_projects_order"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(auth_token="bad", projects_order=[[1, 0], [2, 1]])

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_bulk_update_projects_order_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en bulk_update_projects_order."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=RuntimeError("Bulk update error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_update_projects_order"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", projects_order=[[1, 0]])


class TestGetProjectStatsExceptionHandlers:
    """Tests para manejadores de excepciones en get_project_stats."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_stats_not_found(self, project_tools_instance):
        """Verifica manejo de ResourceNotFoundError en get_project_stats."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=ResourceNotFoundError("Project not found")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_stats"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", project_id=999)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_stats_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en get_project_stats."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=AuthenticationError("Invalid")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_stats"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(auth_token="bad", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_stats_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en get_project_stats."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=RuntimeError("Stats error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_stats"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", project_id=123)


class TestGetProjectExceptionHandlers:
    """Tests para manejadores de excepciones en get_project."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en get_project."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=RuntimeError("Connection error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project"]

        with pytest.raises(ToolError, match="Unexpected error"):
            await tool.fn(auth_token="token", project_id=123)


class TestListProjectsExceptionHandlers:
    """Tests para manejadores de excepciones en list_projects registrada."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_list_projects_registered_unexpected_error(self, project_tools_instance):
        """Verifica manejo de excepciones inesperadas en list_projects registrada."""
        with patch(
            "src.application.tools.project_tools.AutoPaginator"
        ) as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.paginate = AsyncMock(
                side_effect=RuntimeError("Pagination failed")
            )
            mock_paginator_cls.return_value = mock_paginator

            tools = await project_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_projects"]

            with pytest.raises(ToolError, match="Unexpected error"):
                await tool.fn(auth_token="token")


class TestListProjectsFilters:
    """Tests para los filtros opcionales en list_projects."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_list_projects_with_is_featured(self, project_tools_instance):
        """Verifica list_projects con filtro is_featured."""
        with patch(
            "src.application.tools.project_tools.AutoPaginator"
        ) as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.paginate = AsyncMock(return_value=[{"id": 1, "name": "Featured"}])
            mock_paginator_cls.return_value = mock_paginator

            tools = await project_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_projects"]

            result = await tool.fn(auth_token="token", is_featured=True)

            assert len(result) == 1
            call_args = mock_paginator.paginate.call_args
            assert call_args[1]["params"]["is_featured"] is True

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_list_projects_with_is_kanban_activated(self, project_tools_instance):
        """Verifica list_projects con filtro is_kanban_activated."""
        with patch(
            "src.application.tools.project_tools.AutoPaginator"
        ) as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.paginate = AsyncMock(return_value=[{"id": 1, "name": "Kanban"}])
            mock_paginator_cls.return_value = mock_paginator

            tools = await project_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_projects"]

            result = await tool.fn(auth_token="token", is_kanban_activated=True)

            assert len(result) == 1
            call_args = mock_paginator.paginate.call_args
            assert call_args[1]["params"]["is_kanban_activated"] is True

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_list_projects_with_order_by(self, project_tools_instance):
        """Verifica list_projects con parámetro order_by."""
        with patch(
            "src.application.tools.project_tools.AutoPaginator"
        ) as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.paginate = AsyncMock(return_value=[{"id": 1, "name": "Project"}])
            mock_paginator_cls.return_value = mock_paginator

            tools = await project_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_projects"]

            result = await tool.fn(auth_token="token", order_by="name")

            assert len(result) == 1
            call_args = mock_paginator.paginate.call_args
            assert call_args[1]["params"]["order_by"] == "name"

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_list_projects_auto_paginate_false(self, project_tools_instance):
        """Verifica list_projects con auto_paginate=False."""
        with patch(
            "src.application.tools.project_tools.AutoPaginator"
        ) as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.paginate_first_page = AsyncMock(
                return_value=[{"id": 1, "name": "First Page"}]
            )
            mock_paginator_cls.return_value = mock_paginator

            tools = await project_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_projects"]

            result = await tool.fn(auth_token="token", auto_paginate=False)

            assert len(result) == 1
            mock_paginator.paginate_first_page.assert_called_once()


class TestUpdateProjectWithParams:
    """Tests para update_project con diferentes parámetros."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_update_project_with_is_kanban_activated(self, project_tools_instance):
        """Verifica update_project con is_kanban_activated."""
        project_tools_instance._mock_client.patch = AsyncMock(
            return_value={"id": 1, "name": "Updated", "is_kanban_activated": True}
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_project"]

        result = await tool.fn(
            auth_token="token", project_id=1, is_kanban_activated=True
        )

        assert result["is_kanban_activated"] is True

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_update_project_with_is_wiki_activated(self, project_tools_instance):
        """Verifica update_project con is_wiki_activated."""
        project_tools_instance._mock_client.patch = AsyncMock(
            return_value={"id": 1, "name": "Updated", "is_wiki_activated": False}
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_project"]

        result = await tool.fn(
            auth_token="token", project_id=1, is_wiki_activated=False
        )

        assert result["is_wiki_activated"] is False


class TestProjectTagsWithValidation:
    """Tests adicionales para tags con validación."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_edit_project_tag_not_found(self, project_tools_instance):
        """Verifica manejo de ResourceNotFoundError en edit_project_tag."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Tag not found")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_edit_project_tag"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(
                auth_token="token",
                project_id=123,
                from_tag="old",
                to_tag="new",
            )

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_edit_project_tag_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en edit_project_tag."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_edit_project_tag"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(
                auth_token="bad",
                project_id=123,
                from_tag="old",
                to_tag="new",
            )

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_edit_project_tag_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en edit_project_tag."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_edit_project_tag"]

        with pytest.raises(ToolError, match="API error"):
            await tool.fn(
                auth_token="token",
                project_id=123,
                from_tag="old",
                to_tag="new",
            )

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_delete_project_tag_not_found(self, project_tools_instance):
        """Verifica manejo de ResourceNotFoundError en delete_project_tag."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Tag not found")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_project_tag"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", project_id=123, tag="tag")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_delete_project_tag_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en delete_project_tag."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Auth error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_project_tag"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(auth_token="bad", project_id=123, tag="tag")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_delete_project_tag_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en delete_project_tag."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_project_tag"]

        with pytest.raises(ToolError, match="API error"):
            await tool.fn(auth_token="token", project_id=123, tag="tag")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_mix_project_tags_not_found(self, project_tools_instance):
        """Verifica manejo de ResourceNotFoundError en mix_project_tags."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Not found")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_mix_project_tags"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(
                auth_token="token",
                project_id=123,
                from_tags=["tag1"],
                to_tag="merged",
            )

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_mix_project_tags_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en mix_project_tags."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Auth error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_mix_project_tags"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(
                auth_token="bad",
                project_id=123,
                from_tags=["tag1"],
                to_tag="merged",
            )

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_mix_project_tags_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en mix_project_tags."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_mix_project_tags"]

        with pytest.raises(ToolError, match="API error"):
            await tool.fn(
                auth_token="token",
                project_id=123,
                from_tags=["tag1"],
                to_tag="merged",
            )


class TestCreateProjectTagExceptions:
    """Tests para excepciones en create_project_tag."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_tag_not_found(self, project_tools_instance):
        """Verifica manejo de ResourceNotFoundError en create_project_tag."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Project not found")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_project_tag"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", project_id=999, tag="new-tag")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_tag_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en create_project_tag."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Auth error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_project_tag"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(auth_token="bad", project_id=123, tag="new-tag")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_tag_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en create_project_tag."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_project_tag"]

        with pytest.raises(ToolError, match="API error"):
            await tool.fn(auth_token="token", project_id=123, tag="new-tag")


class TestGetProjectTagsExceptions:
    """Tests para excepciones en get_project_tags."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_tags_authentication_error(self, project_tools_instance):
        """Verifica manejo de AuthenticationError en get_project_tags."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=AuthenticationError("Auth error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_tags"]

        with pytest.raises(ToolError, match="Authentication failed"):
            await tool.fn(auth_token="bad", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_tags_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en get_project_tags."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_tags"]

        with pytest.raises(ToolError, match="API error"):
            await tool.fn(auth_token="token", project_id=123)


class TestGetProjectModulesApiError:
    """Tests para TaigaAPIError en get_project_modules."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_modules_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en get_project_modules."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_modules"]

        with pytest.raises(ToolError, match="API error"):
            await tool.fn(auth_token="token", project_id=123)


class TestUpdateProjectModulesApiError:
    """Tests para TaigaAPIError en update_project_modules."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_update_project_modules_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en update_project_modules."""
        project_tools_instance._mock_client.patch = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_project_modules"]

        with pytest.raises(ToolError, match="API error"):
            await tool.fn(auth_token="token", project_id=123)


class TestBulkUpdateApiError:
    """Tests para TaigaAPIError en bulk_update_projects_order."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_bulk_update_projects_order_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en bulk_update_projects_order."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_update_projects_order"]

        with pytest.raises(ToolError, match="API error"):
            await tool.fn(auth_token="token", projects_order=[[1, 0]])


class TestGetProjectTagsResponseTypes:
    """Tests para diferentes tipos de respuesta en get_project_tags."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_tags_dict_response(self, project_tools_instance):
        """Verifica manejo cuando la API devuelve un dict."""
        project_tools_instance._mock_client.get = AsyncMock(
            return_value={"bug": "#FF0000", "feature": "#00FF00"}
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_tags"]

        result = await tool.fn(auth_token="token", project_id=123)

        assert isinstance(result, list)
        assert len(result) == 2

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_tags_other_response(self, project_tools_instance):
        """Verifica manejo cuando la API devuelve otro tipo."""
        project_tools_instance._mock_client.get = AsyncMock(return_value="unexpected")

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_tags"]

        result = await tool.fn(auth_token="token", project_id=123)

        assert result == []


class TestCreateProjectTagResponseTypes:
    """Tests para diferentes tipos de respuesta en create_project_tag."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_tag_permission_denied(self, project_tools_instance):
        """Verifica manejo de PermissionDeniedError en create_project_tag."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_project_tag"]

        with pytest.raises(ToolError, match="permission"):
            await tool.fn(auth_token="token", project_id=123, tag="new-tag")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_tag_non_list_response(self, project_tools_instance):
        """Verifica manejo cuando la API no devuelve una lista."""
        project_tools_instance._mock_client.post = AsyncMock(return_value={"success": True})

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_project_tag"]

        result = await tool.fn(
            auth_token="token", project_id=123, tag="new-tag", color="#FF5733"
        )

        assert result == ["new-tag", "#FF5733"]


class TestEditProjectTagResponseTypes:
    """Tests para diferentes tipos de respuesta en edit_project_tag."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_edit_project_tag_permission_denied(self, project_tools_instance):
        """Verifica manejo de PermissionDeniedError en edit_project_tag."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_edit_project_tag"]

        with pytest.raises(ToolError, match="permission"):
            await tool.fn(
                auth_token="token", project_id=123, from_tag="old", to_tag="new"
            )

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_edit_project_tag_non_list_response(self, project_tools_instance):
        """Verifica manejo cuando la API no devuelve una lista."""
        project_tools_instance._mock_client.post = AsyncMock(return_value={"success": True})

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_edit_project_tag"]

        result = await tool.fn(
            auth_token="token",
            project_id=123,
            from_tag="old",
            to_tag="new",
            color="#FF5733",
        )

        assert result == ["new", "#FF5733"]


class TestDeleteProjectTagPermission:
    """Tests para permisos en delete_project_tag."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_delete_project_tag_permission_denied(self, project_tools_instance):
        """Verifica manejo de PermissionDeniedError en delete_project_tag."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_project_tag"]

        with pytest.raises(ToolError, match="permission"):
            await tool.fn(auth_token="token", project_id=123, tag="old-tag")


class TestMixProjectTagsResponseTypes:
    """Tests para diferentes tipos de respuesta en mix_project_tags."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_mix_project_tags_permission_denied(self, project_tools_instance):
        """Verifica manejo de PermissionDeniedError en mix_project_tags."""
        project_tools_instance._mock_client.post = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_mix_project_tags"]

        with pytest.raises(ToolError, match="permission"):
            await tool.fn(
                auth_token="token",
                project_id=123,
                from_tags=["tag1", "tag2"],
                to_tag="merged",
            )

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_mix_project_tags_non_list_response(self, project_tools_instance):
        """Verifica manejo cuando la API no devuelve una lista."""
        project_tools_instance._mock_client.post = AsyncMock(return_value={"success": True})

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_mix_project_tags"]

        result = await tool.fn(
            auth_token="token",
            project_id=123,
            from_tags=["tag1", "tag2"],
            to_tag="merged",
        )

        assert result == ["merged", "#000000"]


class TestBulkUpdateProjectsOrderResponseTypes:
    """Tests para diferentes tipos de respuesta en bulk_update_projects_order."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_bulk_update_projects_order_non_list_response(self, project_tools_instance):
        """Verifica manejo cuando la API no devuelve una lista."""
        project_tools_instance._mock_client.post = AsyncMock(return_value={"success": True})

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_update_projects_order"]

        result = await tool.fn(
            auth_token="token", projects_order=[[123, 1], [456, 2]]
        )

        assert result == [{"id": 123, "order": 1}, {"id": 456, "order": 2}]


class TestGetProjectModulesSuccess:
    """Tests para éxito en get_project_modules."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_modules_success(self, project_tools_instance):
        """Verifica respuesta exitosa de get_project_modules."""
        project_tools_instance._mock_client.get = AsyncMock(
            return_value={
                "backlog": True,
                "issues": True,
                "kanban": False,
                "wiki": True,
                "videoconferences": "jitsi",
                "videoconferences_extra_data": "room-123",
            }
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_modules"]

        result = await tool.fn(auth_token="token", project_id=123)

        assert result["is_backlog_activated"] is True
        assert result["is_issues_activated"] is True
        assert result["is_kanban_activated"] is False
        assert result["is_wiki_activated"] is True
        assert result["videoconferences"] == "jitsi"


class TestUpdateProjectModulesSuccess:
    """Tests para éxito en update_project_modules."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_update_project_modules_with_all_params(self, project_tools_instance):
        """Verifica update_project_modules con todos los parámetros."""
        project_tools_instance._mock_client.patch = AsyncMock(
            return_value={
                "backlog": True,
                "issues": False,
                "kanban": True,
                "wiki": True,
                "videoconferences": "whereby-com",
                "videoconferences_extra_data": "extra-data",
            }
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_project_modules"]

        result = await tool.fn(
            auth_token="token",
            project_id=123,
            is_backlog_activated=True,
            is_issues_activated=False,
            is_kanban_activated=True,
            is_wiki_activated=True,
            videoconferences="whereby-com",
            videoconferences_extra_data="extra-data",
        )

        assert result["is_backlog_activated"] is True
        assert result["is_issues_activated"] is False
        assert result["is_kanban_activated"] is True
        assert result["videoconferences"] == "whereby-com"
        assert "message" in result


class TestGetProjectIssuesStatsApiError:
    """Tests para TaigaAPIError en get_project_issues_stats."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_issues_stats_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en get_project_issues_stats."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_issues_stats"]

        with pytest.raises(ToolError, match="API error"):
            await tool.fn(auth_token="token", project_id=123)


class TestGetProjectBySlugApiError:
    """Tests para TaigaAPIError en get_project_by_slug."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_by_slug_api_error(self, project_tools_instance):
        """Verifica manejo de TaigaAPIError en get_project_by_slug."""
        project_tools_instance._mock_client.get = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await project_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_project_by_slug"]

        with pytest.raises(ToolError, match="API error"):
            await tool.fn(auth_token="token", slug="my-project")
