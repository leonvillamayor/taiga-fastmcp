"""
Tests adicionales para cobertura completa de userstory_tools.py.
Cubre funciones, metodos sincronicos, herramientas MCP y manejadores de excepciones.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.application.tools.userstory_tools import UserStoryTools, get_taiga_client
from src.domain.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    ResourceNotFoundError,
    TaigaAPIError,
    ValidationError,
)


@pytest.fixture
def userstory_tools_instance():
    """Fixture que crea una instancia de UserStoryTools con mocks."""
    mcp = FastMCP("Test")
    with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client
        tools = UserStoryTools(mcp)
        tools.register_tools()
        tools._mock_client = mock_client
        tools._mock_client_cls = mock_client_cls
        yield tools


class TestGetTaigaClientFunction:
    """Tests para la funcion get_taiga_client."""

    @pytest.mark.unit
    @pytest.mark.userstories
    def test_get_taiga_client_without_auth_token(self):
        """Verifica que get_taiga_client funciona sin token."""
        with patch("src.application.tools.userstory_tools.TaigaConfig"):
            with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client:
                mock_instance = MagicMock(spec=["some_method"])
                mock_client.return_value = mock_instance

                client = get_taiga_client()

                assert client is mock_instance

    @pytest.mark.unit
    @pytest.mark.userstories
    def test_get_taiga_client_with_auth_token(self):
        """Verifica que get_taiga_client establece el token."""
        with patch("src.application.tools.userstory_tools.TaigaConfig"):
            with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance

                client = get_taiga_client(auth_token="test_token")

                assert client.auth_token == "test_token"


class TestSetClient:
    """Tests para el metodo set_client."""

    @pytest.mark.unit
    @pytest.mark.userstories
    def test_set_client_success(self):
        """Verifica que set_client establece el cliente."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()

        tools.set_client(mock_client)

        assert tools.client is mock_client
        assert tools._client is mock_client


class TestSyncWrapperMethods:
    """Tests para los metodos sincronicos wrapper."""

    @pytest.mark.unit
    @pytest.mark.userstories
    def test_sync_list_user_stories_success(self):
        """Verifica list_user_stories con exito."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)

        with patch("src.application.tools.userstory_tools.get_taiga_client") as mock_get:
            mock_client = MagicMock()
            mock_client.list_user_stories.return_value = [{"id": 1}]
            mock_get.return_value = mock_client

            result = tools.list_user_stories(project_id=1)

            assert result["success"] is True
            assert result["data"] == [{"id": 1}]

    @pytest.mark.unit
    @pytest.mark.userstories
    def test_sync_list_user_stories_error(self):
        """Verifica list_user_stories con error."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)

        with patch("src.application.tools.userstory_tools.get_taiga_client") as mock_get:
            mock_get.side_effect = Exception("API error")

            result = tools.list_user_stories(project_id=1)

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.unit
    @pytest.mark.userstories
    def test_sync_get_user_story_success(self):
        """Verifica get_user_story con exito."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)

        with patch("src.application.tools.userstory_tools.get_taiga_client") as mock_get:
            mock_client = MagicMock()
            mock_client.get_user_story.return_value = {"id": 1}
            mock_get.return_value = mock_client

            result = tools.get_user_story(user_story_id=1)

            assert result["success"] is True
            assert result["data"] == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    def test_sync_get_user_story_error(self):
        """Verifica get_user_story con error."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)

        with patch("src.application.tools.userstory_tools.get_taiga_client") as mock_get:
            mock_get.side_effect = Exception("Not found")

            result = tools.get_user_story(user_story_id=999)

            assert result["success"] is False

    @pytest.mark.unit
    @pytest.mark.userstories
    def test_sync_create_user_story_success(self):
        """Verifica create_user_story con exito."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)

        with patch("src.application.tools.userstory_tools.get_taiga_client") as mock_get:
            mock_client = MagicMock()
            mock_client.create_user_story.return_value = {"id": 1}
            mock_get.return_value = mock_client

            result = tools.create_user_story(project_id=1, subject="Test")

            assert result["success"] is True

    @pytest.mark.unit
    @pytest.mark.userstories
    def test_sync_create_user_story_error(self):
        """Verifica create_user_story con error."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)

        with patch("src.application.tools.userstory_tools.get_taiga_client") as mock_get:
            mock_get.side_effect = Exception("Create failed")

            result = tools.create_user_story(project_id=1, subject="Test")

            assert result["success"] is False


class TestListUserstoriesExceptionHandlers:
    """Tests para exception handlers en list_userstories."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_validation_error(self, userstory_tools_instance):
        """Verifica manejo de ValidationError - cae en Exception general."""
        userstory_tools_instance._mock_client.get = AsyncMock(
            side_effect=ValidationError("Invalid data")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_list_userstories"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(auth_token="token", project_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_permission_denied(self, userstory_tools_instance):
        """Verifica manejo de PermissionDeniedError - cae en Exception general."""
        userstory_tools_instance._mock_client.get = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_list_userstories"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(auth_token="token", project_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_authentication_error(self):
        """Verifica manejo de AuthenticationError en list_userstories sin cliente."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            with patch("src.application.tools.userstory_tools.AutoPaginator") as mock_paginator_cls:
                mock_paginator = MagicMock()
                mock_paginator.paginate = AsyncMock(side_effect=AuthenticationError("Auth failed"))
                mock_paginator_cls.return_value = mock_paginator

                tools = UserStoryTools(mcp)
                tools.register_tools()
                registered = await tools.mcp.get_tools()
                tool = registered["taiga_list_userstories"]

                with pytest.raises(ToolError, match="Authentication failed"):
                    await tool.fn(auth_token="token", project_id=1)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_taiga_api_error(self):
        """Verifica manejo de TaigaAPIError en list_userstories sin cliente."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            with patch("src.application.tools.userstory_tools.AutoPaginator") as mock_paginator_cls:
                mock_paginator = MagicMock()
                mock_paginator.paginate = AsyncMock(side_effect=TaigaAPIError("API failed"))
                mock_paginator_cls.return_value = mock_paginator

                tools = UserStoryTools(mcp)
                tools.register_tools()
                registered = await tools.mcp.get_tools()
                tool = registered["taiga_list_userstories"]

                with pytest.raises(ToolError, match="API error"):
                    await tool.fn(auth_token="token", project_id=1)


class TestCreateUserstoryExceptionHandlers:
    """Tests para exception handlers en create_userstory."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_create_userstory_validation_error(self, userstory_tools_instance):
        """Verifica manejo de ValidationError en create."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=ValidationError("Invalid subject")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_userstory"]

        with pytest.raises(ToolError, match="Invalid"):
            await tool.fn(
                auth_token="token",
                project_id=123,
                subject="Test",
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_create_userstory_not_found(self, userstory_tools_instance):
        """Verifica manejo de ResourceNotFoundError - cae en Exception general."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Project not found")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_userstory"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(auth_token="token", project_id=999, subject="Test")

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_create_userstory_permission_denied(self, userstory_tools_instance):
        """Verifica manejo de PermissionDeniedError - cae en Exception general."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_userstory"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(auth_token="token", project_id=123, subject="Test")

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_create_userstory_taiga_api_error(self, userstory_tools_instance):
        """Verifica manejo de TaigaAPIError en create."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_userstory"]

        with pytest.raises(ToolError, match="API"):
            await tool.fn(auth_token="token", project_id=123, subject="Test")

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_create_userstory_unexpected_error(self, userstory_tools_instance):
        """Verifica manejo de Exception en create."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=Exception("Unexpected")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_userstory"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(auth_token="token", project_id=123, subject="Test")


class TestGetUserstoryExceptionHandlers:
    """Tests para exception handlers en get_userstory."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_validation_error(self, userstory_tools_instance):
        """Verifica manejo de ValidationError - cae en Exception general."""
        userstory_tools_instance._mock_client.get = AsyncMock(
            side_effect=ValidationError("Invalid ID")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_userstory"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(auth_token="token", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_permission_denied(self, userstory_tools_instance):
        """Verifica manejo de PermissionDeniedError en get."""
        userstory_tools_instance._mock_client.get = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_userstory"]

        with pytest.raises(ToolError, match="permission"):
            await tool.fn(auth_token="token", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_taiga_api_error(self, userstory_tools_instance):
        """Verifica manejo de TaigaAPIError en get."""
        userstory_tools_instance._mock_client.get = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_userstory"]

        with pytest.raises(ToolError, match="API"):
            await tool.fn(auth_token="token", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_unexpected_error(self, userstory_tools_instance):
        """Verifica manejo de Exception en get."""
        userstory_tools_instance._mock_client.get = AsyncMock(
            side_effect=Exception("Unexpected")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_userstory"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(auth_token="token", userstory_id=123)


class TestUpdateUserstoryExceptionHandlers:
    """Tests para exception handlers en update_userstory."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_validation_error(self, userstory_tools_instance):
        """Verifica manejo de ValidationError en update."""
        userstory_tools_instance._mock_client.patch = AsyncMock(
            side_effect=ValidationError("Invalid data")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_userstory"]

        with pytest.raises(ToolError, match="Invalid"):
            await tool.fn(auth_token="token", userstory_id=123, subject="Updated")

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_not_found(self, userstory_tools_instance):
        """Verifica manejo de ResourceNotFoundError en update."""
        userstory_tools_instance._mock_client.patch = AsyncMock(
            side_effect=ResourceNotFoundError("Not found")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_userstory"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", userstory_id=999, subject="Updated")

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_permission_denied(self, userstory_tools_instance):
        """Verifica manejo de PermissionDeniedError en update."""
        userstory_tools_instance._mock_client.patch = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_userstory"]

        with pytest.raises(ToolError, match="permission"):
            await tool.fn(auth_token="token", userstory_id=123, subject="Updated")

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_unexpected_error(self, userstory_tools_instance):
        """Verifica manejo de Exception en update."""
        userstory_tools_instance._mock_client.patch = AsyncMock(
            side_effect=Exception("Unexpected")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_userstory"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(auth_token="token", userstory_id=123, subject="Updated")


class TestDeleteUserstoryExceptionHandlers:
    """Tests para exception handlers en delete_userstory."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_delete_userstory_authentication_error(self, userstory_tools_instance):
        """Verifica manejo de AuthenticationError en delete."""
        userstory_tools_instance._mock_client.delete = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_userstory"]

        with pytest.raises(ToolError, match="Authentication"):
            await tool.fn(auth_token="bad", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_delete_userstory_taiga_api_error(self, userstory_tools_instance):
        """Verifica manejo de TaigaAPIError en delete."""
        userstory_tools_instance._mock_client.delete = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_userstory"]

        with pytest.raises(ToolError, match="API"):
            await tool.fn(auth_token="token", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_delete_userstory_unexpected_error(self, userstory_tools_instance):
        """Verifica manejo de Exception en delete."""
        userstory_tools_instance._mock_client.delete = AsyncMock(
            side_effect=Exception("Unexpected")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_userstory"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(auth_token="token", userstory_id=123)


class TestBulkCreateUserstoriesExceptionHandlers:
    """Tests para exception handlers en bulk_create_userstories."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_create_userstories_validation_error(self, userstory_tools_instance):
        """Verifica manejo de ValidationError - cae en Exception general."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=ValidationError("Invalid data")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_create_userstories"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(
                auth_token="token",
                project_id=123,
                bulk_stories="Story 1\nStory 2",
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_create_userstories_not_found(self, userstory_tools_instance):
        """Verifica manejo de ResourceNotFoundError - cae en Exception general."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Not found")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_create_userstories"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(
                auth_token="token",
                project_id=999,
                bulk_stories="Story 1",
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_create_userstories_permission_denied(self, userstory_tools_instance):
        """Verifica manejo de PermissionDeniedError - cae en Exception general."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_create_userstories"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(
                auth_token="token",
                project_id=123,
                bulk_stories="Story 1",
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_create_userstories_authentication_error(self, userstory_tools_instance):
        """Verifica manejo de AuthenticationError en bulk create."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_create_userstories"]

        with pytest.raises(ToolError, match="Authentication"):
            await tool.fn(
                auth_token="bad",
                project_id=123,
                bulk_stories="Story 1",
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_create_userstories_taiga_api_error(self, userstory_tools_instance):
        """Verifica manejo de TaigaAPIError en bulk create."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_create_userstories"]

        with pytest.raises(ToolError, match="API"):
            await tool.fn(
                auth_token="token",
                project_id=123,
                bulk_stories="Story 1",
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_create_userstories_unexpected_error(self, userstory_tools_instance):
        """Verifica manejo de Exception en bulk create."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=Exception("Unexpected")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_create_userstories"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(
                auth_token="token",
                project_id=123,
                bulk_stories="Story 1",
            )


class TestBulkUpdateUserstoriesExceptionHandlers:
    """Tests para exception handlers en bulk_update_userstories."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_update_userstories_validation_error(self, userstory_tools_instance):
        """Verifica manejo de ValidationError - cae en Exception general."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=ValidationError("Invalid data")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_update_userstories"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(
                auth_token="token",
                story_ids=[1, 2],
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_update_userstories_not_found(self, userstory_tools_instance):
        """Verifica manejo de ResourceNotFoundError - cae en Exception general."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Not found")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_update_userstories"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(
                auth_token="token",
                story_ids=[1, 2],
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_update_userstories_permission_denied(self, userstory_tools_instance):
        """Verifica manejo de PermissionDeniedError - cae en Exception general."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_update_userstories"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(
                auth_token="token",
                story_ids=[1, 2],
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_update_userstories_authentication_error(self, userstory_tools_instance):
        """Verifica manejo de AuthenticationError en bulk update."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_update_userstories"]

        with pytest.raises(ToolError, match="Authentication"):
            await tool.fn(
                auth_token="bad",
                story_ids=[1, 2],
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_update_userstories_taiga_api_error(self, userstory_tools_instance):
        """Verifica manejo de TaigaAPIError en bulk update."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_update_userstories"]

        with pytest.raises(ToolError, match="API"):
            await tool.fn(
                auth_token="token",
                story_ids=[1, 2],
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_update_userstories_unexpected_error(self, userstory_tools_instance):
        """Verifica manejo de Exception en bulk update."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=Exception("Unexpected")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_update_userstories"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(
                auth_token="token",
                story_ids=[1, 2],
            )


class TestBulkDeleteUserstoriesExceptionHandlers:
    """Tests para exception handlers en bulk_delete_userstories."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_delete_userstories_validation_error(self, userstory_tools_instance):
        """Verifica manejo de ValidationError - cae en Exception general."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=ValidationError("Invalid data")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_delete_userstories"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(
                auth_token="token",
                story_ids=[1, 2, 3],
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_delete_userstories_not_found(self, userstory_tools_instance):
        """Verifica manejo de ResourceNotFoundError - cae en Exception general."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Not found")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_delete_userstories"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(
                auth_token="token",
                story_ids=[1, 2],
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_delete_userstories_permission_denied(self, userstory_tools_instance):
        """Verifica manejo de PermissionDeniedError - cae en Exception general."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_delete_userstories"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(
                auth_token="token",
                story_ids=[1, 2],
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_delete_userstories_authentication_error(self, userstory_tools_instance):
        """Verifica manejo de AuthenticationError en bulk delete."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_delete_userstories"]

        with pytest.raises(ToolError, match="Authentication"):
            await tool.fn(
                auth_token="bad",
                story_ids=[1, 2],
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_delete_userstories_taiga_api_error(self, userstory_tools_instance):
        """Verifica manejo de TaigaAPIError en bulk delete."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_delete_userstories"]

        with pytest.raises(ToolError, match="API"):
            await tool.fn(
                auth_token="token",
                story_ids=[1, 2],
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_delete_userstories_unexpected_error(self, userstory_tools_instance):
        """Verifica manejo de Exception en bulk delete."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=Exception("Unexpected")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_delete_userstories"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(
                auth_token="token",
                story_ids=[1, 2],
            )


class TestMoveToMilestoneExceptionHandlers:
    """Tests para exception handlers en move_to_milestone."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_move_to_milestone_validation_error(self, userstory_tools_instance):
        """Verifica manejo de ValidationError - cae en Exception general."""
        userstory_tools_instance._mock_client.patch = AsyncMock(
            side_effect=ValidationError("Invalid data")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_move_to_milestone"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(
                auth_token="token",
                userstory_id=123,
                milestone_id=456,
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_move_to_milestone_not_found(self, userstory_tools_instance):
        """Verifica manejo de ResourceNotFoundError en move_to_milestone."""
        userstory_tools_instance._mock_client.patch = AsyncMock(
            side_effect=ResourceNotFoundError("Not found")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_move_to_milestone"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(
                auth_token="token",
                userstory_id=999,
                milestone_id=456,
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_move_to_milestone_permission_denied(self, userstory_tools_instance):
        """Verifica manejo de PermissionDeniedError - cae en Exception general."""
        userstory_tools_instance._mock_client.patch = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_move_to_milestone"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(
                auth_token="token",
                userstory_id=123,
                milestone_id=456,
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_move_to_milestone_authentication_error(self, userstory_tools_instance):
        """Verifica manejo de AuthenticationError en move_to_milestone."""
        userstory_tools_instance._mock_client.patch = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_move_to_milestone"]

        with pytest.raises(ToolError, match="Authentication"):
            await tool.fn(
                auth_token="bad",
                userstory_id=123,
                milestone_id=456,
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_move_to_milestone_taiga_api_error(self, userstory_tools_instance):
        """Verifica manejo de TaigaAPIError en move_to_milestone."""
        userstory_tools_instance._mock_client.patch = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_move_to_milestone"]

        with pytest.raises(ToolError, match="API"):
            await tool.fn(
                auth_token="token",
                userstory_id=123,
                milestone_id=456,
            )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_move_to_milestone_unexpected_error(self, userstory_tools_instance):
        """Verifica manejo de Exception en move_to_milestone."""
        userstory_tools_instance._mock_client.patch = AsyncMock(
            side_effect=Exception("Unexpected")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_move_to_milestone"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(
                auth_token="token",
                userstory_id=123,
                milestone_id=456,
            )


class TestGetUserstoryHistoryExceptionHandlers:
    """Tests para exception handlers en get_userstory_history."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_history_not_found(self, userstory_tools_instance):
        """Verifica manejo de ResourceNotFoundError en get_userstory_history."""
        userstory_tools_instance._mock_client.get = AsyncMock(
            side_effect=ResourceNotFoundError("Not found")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_userstory_history"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", userstory_id=999)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_history_authentication_error(self, userstory_tools_instance):
        """Verifica manejo de AuthenticationError en get_userstory_history."""
        userstory_tools_instance._mock_client.get = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_userstory_history"]

        with pytest.raises(ToolError, match="Authentication"):
            await tool.fn(auth_token="bad", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_history_taiga_api_error(self, userstory_tools_instance):
        """Verifica manejo de TaigaAPIError en get_userstory_history."""
        userstory_tools_instance._mock_client.get = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_userstory_history"]

        with pytest.raises(ToolError, match="API"):
            await tool.fn(auth_token="token", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_history_unexpected_error(self, userstory_tools_instance):
        """Verifica manejo de Exception en get_userstory_history."""
        userstory_tools_instance._mock_client.get = AsyncMock(
            side_effect=Exception("Unexpected")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_userstory_history"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(auth_token="token", userstory_id=123)


class TestWatchUserstoryExceptionHandlers:
    """Tests para exception handlers en watch_userstory."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_watch_userstory_not_found(self, userstory_tools_instance):
        """Verifica manejo de ResourceNotFoundError en watch_userstory."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Not found")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_watch_userstory"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", userstory_id=999)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_watch_userstory_authentication_error(self, userstory_tools_instance):
        """Verifica manejo de AuthenticationError en watch_userstory."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_watch_userstory"]

        with pytest.raises(ToolError, match="Authentication"):
            await tool.fn(auth_token="bad", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_watch_userstory_taiga_api_error(self, userstory_tools_instance):
        """Verifica manejo de TaigaAPIError en watch_userstory."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_watch_userstory"]

        with pytest.raises(ToolError, match="API"):
            await tool.fn(auth_token="token", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_watch_userstory_unexpected_error(self, userstory_tools_instance):
        """Verifica manejo de Exception en watch_userstory."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=Exception("Unexpected")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_watch_userstory"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(auth_token="token", userstory_id=123)


class TestUnwatchUserstoryExceptionHandlers:
    """Tests para exception handlers en unwatch_userstory."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_unwatch_userstory_not_found(self, userstory_tools_instance):
        """Verifica manejo de ResourceNotFoundError en unwatch_userstory."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Not found")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_unwatch_userstory"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", userstory_id=999)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_unwatch_userstory_authentication_error(self, userstory_tools_instance):
        """Verifica manejo de AuthenticationError en unwatch_userstory."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_unwatch_userstory"]

        with pytest.raises(ToolError, match="Authentication"):
            await tool.fn(auth_token="bad", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_unwatch_userstory_taiga_api_error(self, userstory_tools_instance):
        """Verifica manejo de TaigaAPIError en unwatch_userstory."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_unwatch_userstory"]

        with pytest.raises(ToolError, match="API"):
            await tool.fn(auth_token="token", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_unwatch_userstory_unexpected_error(self, userstory_tools_instance):
        """Verifica manejo de Exception en unwatch_userstory."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=Exception("Unexpected")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_unwatch_userstory"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(auth_token="token", userstory_id=123)


class TestUpvoteUserstoryExceptionHandlers:
    """Tests para exception handlers en upvote_userstory."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_upvote_userstory_not_found(self, userstory_tools_instance):
        """Verifica manejo de ResourceNotFoundError en upvote_userstory."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Not found")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_upvote_userstory"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", userstory_id=999)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_upvote_userstory_authentication_error(self, userstory_tools_instance):
        """Verifica manejo de AuthenticationError en upvote_userstory."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_upvote_userstory"]

        with pytest.raises(ToolError, match="Authentication"):
            await tool.fn(auth_token="bad", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_upvote_userstory_taiga_api_error(self, userstory_tools_instance):
        """Verifica manejo de TaigaAPIError en upvote_userstory."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_upvote_userstory"]

        with pytest.raises(ToolError, match="API"):
            await tool.fn(auth_token="token", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_upvote_userstory_unexpected_error(self, userstory_tools_instance):
        """Verifica manejo de Exception en upvote_userstory."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=Exception("Unexpected")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_upvote_userstory"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(auth_token="token", userstory_id=123)


class TestDownvoteUserstoryExceptionHandlers:
    """Tests para exception handlers en downvote_userstory."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_downvote_userstory_not_found(self, userstory_tools_instance):
        """Verifica manejo de ResourceNotFoundError en downvote_userstory."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Not found")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_downvote_userstory"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", userstory_id=999)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_downvote_userstory_authentication_error(self, userstory_tools_instance):
        """Verifica manejo de AuthenticationError en downvote_userstory."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_downvote_userstory"]

        with pytest.raises(ToolError, match="Authentication"):
            await tool.fn(auth_token="bad", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_downvote_userstory_taiga_api_error(self, userstory_tools_instance):
        """Verifica manejo de TaigaAPIError en downvote_userstory."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_downvote_userstory"]

        with pytest.raises(ToolError, match="API"):
            await tool.fn(auth_token="token", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_downvote_userstory_unexpected_error(self, userstory_tools_instance):
        """Verifica manejo de Exception en downvote_userstory."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            side_effect=Exception("Unexpected")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_downvote_userstory"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(auth_token="token", userstory_id=123)


class TestGetUserstoryVotersExceptionHandlers:
    """Tests para exception handlers en get_userstory_voters."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_voters_not_found(self, userstory_tools_instance):
        """Verifica manejo de ResourceNotFoundError en get_userstory_voters."""
        userstory_tools_instance._mock_client.get = AsyncMock(
            side_effect=ResourceNotFoundError("Not found")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_userstory_voters"]

        with pytest.raises(ToolError, match="not found"):
            await tool.fn(auth_token="token", userstory_id=999)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_voters_authentication_error(self, userstory_tools_instance):
        """Verifica manejo de AuthenticationError en get_userstory_voters."""
        userstory_tools_instance._mock_client.get = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_userstory_voters"]

        with pytest.raises(ToolError, match="Authentication"):
            await tool.fn(auth_token="bad", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_voters_taiga_api_error(self, userstory_tools_instance):
        """Verifica manejo de TaigaAPIError en get_userstory_voters."""
        userstory_tools_instance._mock_client.get = AsyncMock(
            side_effect=TaigaAPIError("API error")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_userstory_voters"]

        with pytest.raises(ToolError, match="API"):
            await tool.fn(auth_token="token", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_voters_unexpected_error(self, userstory_tools_instance):
        """Verifica manejo de Exception en get_userstory_voters."""
        userstory_tools_instance._mock_client.get = AsyncMock(
            side_effect=Exception("Unexpected")
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_userstory_voters"]

        with pytest.raises(ToolError, match="Unexpected"):
            await tool.fn(auth_token="token", userstory_id=123)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_voters_success_with_list(self, userstory_tools_instance):
        """Verifica get_userstory_voters devuelve lista correctamente."""
        mock_voters = [
            {"id": 1, "username": "user1", "full_name_display": "User One", "photo": "http://photo1.jpg"},
            {"id": 2, "username": "user2", "full_name_display": "User Two", "photo": "http://photo2.jpg"},
        ]
        userstory_tools_instance._mock_client.get = AsyncMock(return_value=mock_voters)

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_userstory_voters"]

        result = await tool.fn(auth_token="token", userstory_id=123)
        assert len(result) == 2
        assert result[0]["username"] == "user1"

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_voters_success_empty(self, userstory_tools_instance):
        """Verifica get_userstory_voters devuelve lista vacia cuando no es lista."""
        userstory_tools_instance._mock_client.get = AsyncMock(return_value=None)

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_userstory_voters"]

        result = await tool.fn(auth_token="token", userstory_id=123)
        assert result == []


class TestAttachmentMethods:
    """Tests para metodos de attachments."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstory_attachments_with_client(self):
        """Verifica list_userstory_attachments con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.list_userstory_attachments = AsyncMock(return_value=[{"id": 1}])
        tools.client = mock_client

        result = await tools.list_userstory_attachments(userstory_id=123)
        assert result == [{"id": 1}]

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstory_attachments_without_client(self):
        """Verifica list_userstory_attachments sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=[{"id": 1}])
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.list_userstory_attachments(auth_token="token", userstory_id=123)
            assert result == [{"id": 1}]

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstory_attachments_empty_result(self):
        """Verifica list_userstory_attachments con resultado no-lista."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.list_userstory_attachments(auth_token="token", userstory_id=123)
            assert result == []

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_create_userstory_attachment_with_client(self):
        """Verifica create_userstory_attachment con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.create_userstory_attachment = AsyncMock(return_value={"id": 1})
        tools.client = mock_client

        result = await tools.create_userstory_attachment(project=1, object_id=123)
        assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_create_userstory_attachment_without_client(self):
        """Verifica create_userstory_attachment sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value={"id": 1})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.create_userstory_attachment(
                auth_token="token", project=1, object_id=123, attached_file="file.txt"
            )
            assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_attachment_with_client(self):
        """Verifica get_userstory_attachment con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.get_userstory_attachment = AsyncMock(return_value={"id": 1})
        tools.client = mock_client

        result = await tools.get_userstory_attachment(attachment_id=1)
        assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_attachment_without_client(self):
        """Verifica get_userstory_attachment sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value={"id": 1})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.get_userstory_attachment(auth_token="token", attachment_id=1)
            assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_attachment_with_client(self):
        """Verifica update_userstory_attachment con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.update_userstory_attachment = AsyncMock(return_value={"id": 1})
        tools.client = mock_client

        result = await tools.update_userstory_attachment(1, description="new desc")
        assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_attachment_without_client(self):
        """Verifica update_userstory_attachment sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(return_value={"id": 1})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.update_userstory_attachment(
                1, auth_token="token", description="new", is_deprecated=True
            )
            assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_delete_userstory_attachment_with_client(self):
        """Verifica delete_userstory_attachment con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.delete_userstory_attachment = AsyncMock(return_value={"success": True})
        tools.client = mock_client

        result = await tools.delete_userstory_attachment(attachment_id=1)
        assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_delete_userstory_attachment_without_client(self):
        """Verifica delete_userstory_attachment sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.delete_userstory_attachment(auth_token="token", attachment_id=1)
            assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_create_attachments(self):
        """Verifica bulk_create_attachments."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)

        result = await tools.bulk_create_attachments(project=1)
        assert result == []


class TestCommentMethods:
    """Tests para metodos de comentarios."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_history_with_client(self):
        """Verifica get_userstory_history con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.get_userstory_history = MagicMock(return_value=[{"id": 1}])
        tools.client = mock_client

        result = await tools.get_userstory_history(userstory_id=123)
        assert result == [{"id": 1}]

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_history_with_async_client(self):
        """Verifica get_userstory_history con cliente async mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.get_userstory_history = AsyncMock(return_value=[{"id": 1}])
        tools.client = mock_client

        result = await tools.get_userstory_history(userstory_id=123)
        assert result == [{"id": 1}]

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_history_without_client(self):
        """Verifica get_userstory_history sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=[{"id": 1}])
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.get_userstory_history(auth_token="token", userstory_id=123)
            assert result == [{"id": 1}]

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_history_empty_result(self):
        """Verifica get_userstory_history con resultado vacio."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.get_userstory_history(auth_token="token", userstory_id=123)
            assert result == []

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_comment_versions_with_client(self):
        """Verifica get_userstory_comment_versions con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.get_userstory_comment_versions = MagicMock(return_value=[{"v": 1}])
        tools.client = mock_client

        result = await tools.get_userstory_comment_versions(userstory_id=123, comment_id="abc")
        assert result == [{"v": 1}]

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_comment_versions_async_client(self):
        """Verifica get_userstory_comment_versions con cliente async."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.get_userstory_comment_versions = AsyncMock(return_value=[{"v": 1}])
        tools.client = mock_client

        result = await tools.get_userstory_comment_versions(userstory_id=123, comment_id="abc")
        assert result == [{"v": 1}]

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_comment_versions_without_client(self):
        """Verifica get_userstory_comment_versions sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=[{"v": 1}])
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.get_userstory_comment_versions(
                auth_token="token", userstory_id=123, comment_id="abc"
            )
            assert result == [{"v": 1}]

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_comment_versions_empty(self):
        """Verifica get_userstory_comment_versions con resultado vacio."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.get_userstory_comment_versions(
                auth_token="token", userstory_id=123, comment_id="abc"
            )
            assert result == []

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_edit_userstory_comment_with_client(self):
        """Verifica edit_userstory_comment con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.edit_userstory_comment = MagicMock(return_value={"success": True})
        tools.client = mock_client

        result = await tools.edit_userstory_comment(userstory_id=123, comment_id="abc", comment="new")
        assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_edit_userstory_comment_async_client(self):
        """Verifica edit_userstory_comment con cliente async."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.edit_userstory_comment = AsyncMock(return_value={"success": True})
        tools.client = mock_client

        result = await tools.edit_userstory_comment(userstory_id=123, comment_id="abc", comment="new")
        assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_edit_userstory_comment_without_client(self):
        """Verifica edit_userstory_comment sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(return_value={"success": True})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.edit_userstory_comment(
                auth_token="token", userstory_id=123, comment_id="abc", comment="new"
            )
            assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_delete_userstory_comment_with_client(self):
        """Verifica delete_userstory_comment con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.delete_userstory_comment = MagicMock(return_value={"success": True})
        tools.client = mock_client

        result = await tools.delete_userstory_comment(userstory_id=123, comment_id="abc")
        assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_delete_userstory_comment_async_client(self):
        """Verifica delete_userstory_comment con cliente async."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.delete_userstory_comment = AsyncMock(return_value={"success": True})
        tools.client = mock_client

        result = await tools.delete_userstory_comment(userstory_id=123, comment_id="abc")
        assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_delete_userstory_comment_without_client(self):
        """Verifica delete_userstory_comment sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.delete_userstory_comment(
                auth_token="token", userstory_id=123, comment_id="abc"
            )
            assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_undelete_userstory_comment_with_client(self):
        """Verifica undelete_userstory_comment con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.undelete_userstory_comment = MagicMock(return_value={"success": True})
        tools.client = mock_client

        result = await tools.undelete_userstory_comment(userstory_id=123, comment_id="abc")
        assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_undelete_userstory_comment_async_client(self):
        """Verifica undelete_userstory_comment con cliente async."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.undelete_userstory_comment = AsyncMock(return_value={"success": True})
        tools.client = mock_client

        result = await tools.undelete_userstory_comment(userstory_id=123, comment_id="abc")
        assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_undelete_userstory_comment_without_client(self):
        """Verifica undelete_userstory_comment sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value={"success": True})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.undelete_userstory_comment(
                auth_token="token", userstory_id=123, comment_id="abc"
            )
            assert result == {"success": True}


class TestOtherMethods:
    """Tests para otros metodos auxiliares."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_by_ref_with_client(self):
        """Verifica get_userstory_by_ref con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.get_userstory_by_ref = MagicMock(return_value={"id": 1})
        tools.client = mock_client

        result = await tools.get_userstory_by_ref(project=1, ref=10)
        assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_by_ref_async_client(self):
        """Verifica get_userstory_by_ref con cliente async."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.get_userstory_by_ref = AsyncMock(return_value={"id": 1})
        tools.client = mock_client

        result = await tools.get_userstory_by_ref(project=1, ref=10)
        assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_by_ref_without_client(self):
        """Verifica get_userstory_by_ref sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value={"id": 1})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.get_userstory_by_ref(auth_token="token", project=1, ref=10)
            assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_full_with_client(self):
        """Verifica update_userstory_full con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.update_userstory_full = AsyncMock(return_value={"id": 1})
        tools.client = mock_client

        result = await tools.update_userstory_full(1, subject="new subject")
        assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_full_without_client(self):
        """Verifica update_userstory_full sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.put = AsyncMock(return_value={"id": 1})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.update_userstory_full(1, auth_token="token", subject="new")
            assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_update_backlog_order_with_client(self):
        """Verifica bulk_update_backlog_order con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.bulk_update_backlog_order = AsyncMock(return_value={"success": True})
        tools.client = mock_client

        result = await tools.bulk_update_backlog_order(project_id=1, bulk_stories=[1, 2])
        assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_update_backlog_order_without_client(self):
        """Verifica bulk_update_backlog_order sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value={"success": True})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.bulk_update_backlog_order(
                auth_token="token", project_id=1, bulk_stories=[1, 2]
            )
            assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_update_kanban_order_with_client(self):
        """Verifica bulk_update_kanban_order con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.bulk_update_kanban_order = MagicMock(return_value={"success": True})
        tools.client = mock_client

        result = await tools.bulk_update_kanban_order(project_id=1, bulk_stories=[1], status=2)
        assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_update_kanban_order_async_client(self):
        """Verifica bulk_update_kanban_order con cliente async."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.bulk_update_kanban_order = AsyncMock(return_value={"success": True})
        tools.client = mock_client

        result = await tools.bulk_update_kanban_order(project_id=1, bulk_stories=[1], status=2)
        assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_update_kanban_order_without_client(self):
        """Verifica bulk_update_kanban_order sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value={"success": True})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.bulk_update_kanban_order(
                auth_token="token", project_id=1, bulk_stories=[1], status=2
            )
            assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_update_sprint_order_with_client(self):
        """Verifica bulk_update_sprint_order con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.bulk_update_sprint_order = AsyncMock(return_value={"success": True})
        tools.client = mock_client

        result = await tools.bulk_update_sprint_order(project_id=1, milestone_id=2, bulk_stories=[1])
        assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_update_sprint_order_without_client(self):
        """Verifica bulk_update_sprint_order sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value={"success": True})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.bulk_update_sprint_order(
                auth_token="token", project_id=1, milestone_id=2, bulk_stories=[1]
            )
            assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_filters_with_client(self):
        """Verifica get_userstory_filters con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.get_userstory_filters = MagicMock(return_value={"statuses": []})
        tools.client = mock_client

        result = await tools.get_userstory_filters(project=1)
        assert result == {"statuses": []}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_filters_async_client(self):
        """Verifica get_userstory_filters con cliente async."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.get_userstory_filters = AsyncMock(return_value={"statuses": []})
        tools.client = mock_client

        result = await tools.get_userstory_filters(project=1)
        assert result == {"statuses": []}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_filters_without_client(self):
        """Verifica get_userstory_filters sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value={"statuses": []})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.get_userstory_filters(auth_token="token", project=1)
            assert result == {"statuses": []}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_watchers_with_client(self):
        """Verifica get_userstory_watchers con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.get_userstory_watchers = AsyncMock(return_value=[{"id": 1}])
        tools.client = mock_client

        result = await tools.get_userstory_watchers(userstory_id=123)
        assert result == [{"id": 1}]

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_watchers_without_client(self):
        """Verifica get_userstory_watchers sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=[{"id": 1}])
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.get_userstory_watchers(auth_token="token", userstory_id=123)
            assert result == [{"id": 1}]

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_watchers_empty(self):
        """Verifica get_userstory_watchers con resultado vacio."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.get_userstory_watchers(auth_token="token", userstory_id=123)
            assert result == []


class TestCustomAttributeMethods:
    """Tests para metodos de atributos personalizados."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstory_custom_attributes_with_client(self):
        """Verifica list_userstory_custom_attributes con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.list_userstory_custom_attributes = MagicMock(return_value=[{"id": 1}])
        tools.client = mock_client

        result = await tools.list_userstory_custom_attributes(project=1)
        assert result == [{"id": 1}]

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstory_custom_attributes_async_client(self):
        """Verifica list_userstory_custom_attributes con cliente async."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.list_userstory_custom_attributes = AsyncMock(return_value=[{"id": 1}])
        tools.client = mock_client

        result = await tools.list_userstory_custom_attributes(project=1)
        assert result == [{"id": 1}]

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstory_custom_attributes_without_client(self):
        """Verifica list_userstory_custom_attributes sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=[{"id": 1}])
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.list_userstory_custom_attributes(auth_token="token", project=1)
            assert result == [{"id": 1}]

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstory_custom_attributes_empty(self):
        """Verifica list_userstory_custom_attributes con resultado vacio."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.list_userstory_custom_attributes(auth_token="token", project=1)
            assert result == []

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_create_userstory_custom_attribute_with_client(self):
        """Verifica create_userstory_custom_attribute con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.create_userstory_custom_attribute = AsyncMock(return_value={"id": 1})
        tools.client = mock_client

        result = await tools.create_userstory_custom_attribute(name="attr", project=1)
        assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_create_userstory_custom_attribute_without_client(self):
        """Verifica create_userstory_custom_attribute sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value={"id": 1})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.create_userstory_custom_attribute(auth_token="token", name="attr")
            assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_custom_attribute_with_client(self):
        """Verifica get_userstory_custom_attribute con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.get_userstory_custom_attribute = AsyncMock(return_value={"id": 1})
        tools.client = mock_client

        result = await tools.get_userstory_custom_attribute(attribute_id=1)
        assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_custom_attribute_without_client(self):
        """Verifica get_userstory_custom_attribute sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value={"id": 1})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.get_userstory_custom_attribute(auth_token="token", attribute_id=1)
            assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_custom_attribute_with_client(self):
        """Verifica update_userstory_custom_attribute con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.update_userstory_custom_attribute = AsyncMock(return_value={"id": 1})
        tools.client = mock_client

        result = await tools.update_userstory_custom_attribute(1, name="new")
        assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_custom_attribute_without_client(self):
        """Verifica update_userstory_custom_attribute sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(return_value={"id": 1})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.update_userstory_custom_attribute(1, auth_token="token", name="new")
            assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_delete_userstory_custom_attribute_with_client(self):
        """Verifica delete_userstory_custom_attribute con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.delete_userstory_custom_attribute = AsyncMock(return_value={"success": True})
        tools.client = mock_client

        result = await tools.delete_userstory_custom_attribute(attribute_id=1)
        assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_delete_userstory_custom_attribute_without_client(self):
        """Verifica delete_userstory_custom_attribute sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.delete_userstory_custom_attribute(auth_token="token", attribute_id=1)
            assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_custom_attribute_full_with_client(self):
        """Verifica update_userstory_custom_attribute_full con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.update_userstory_custom_attribute_full = AsyncMock(return_value={"id": 1})
        tools.client = mock_client

        result = await tools.update_userstory_custom_attribute_full(1, name="new")
        assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_custom_attribute_full_without_client(self):
        """Verifica update_userstory_custom_attribute_full sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.put = AsyncMock(return_value={"id": 1})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.update_userstory_custom_attribute_full(1, auth_token="token", name="new")
            assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_custom_attribute_partial_with_client(self):
        """Verifica update_userstory_custom_attribute_partial con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.update_userstory_custom_attribute_partial = AsyncMock(return_value={"id": 1})
        tools.client = mock_client

        result = await tools.update_userstory_custom_attribute_partial(1, name="new")
        assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_custom_attribute_partial_without_client(self):
        """Verifica update_userstory_custom_attribute_partial sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(return_value={"id": 1})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.update_userstory_custom_attribute_partial(
                1, auth_token="token", name="new"
            )
            assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_set_custom_attribute_values_with_client(self):
        """Verifica set_custom_attribute_values con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        tools.client = mock_client

        result = await tools.set_custom_attribute_values(userstory_id=1, attributes={"1": "val"})
        assert result == {"success": True}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_set_custom_attribute_values_without_client(self):
        """Verifica set_custom_attribute_values sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(return_value={"id": 1})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.set_custom_attribute_values(
                auth_token="token", userstory_id=1, attributes={"1": "val"}
            )
            assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_custom_attribute_validation(self):
        """Verifica custom_attribute_validation."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)

        result = await tools.custom_attribute_validation()
        assert result == {"valid": True}


class TestUpdateUserstoryMethod:
    """Tests para el metodo update_userstory."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_method_with_client(self):
        """Verifica update_userstory metodo con cliente mock."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.update_userstory = MagicMock(return_value={"id": 1})
        tools.client = mock_client

        result = await tools.update_userstory(1, subject="new subject")
        assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_method_async_client(self):
        """Verifica update_userstory metodo con cliente async."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.update_userstory = AsyncMock(return_value={"id": 1})
        tools.client = mock_client

        result = await tools.update_userstory(1, subject="new subject")
        assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_method_without_client(self):
        """Verifica update_userstory metodo sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(return_value={"id": 1})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            result = await tools.update_userstory(1, auth_token="token", subject="new")
            assert result == {"id": 1}

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_method_validation_error(self):
        """Verifica update_userstory con error de validacion."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)

        with patch(
            "src.application.tools.userstory_tools.validate_input",
            side_effect=ValidationError("Invalid"),
        ):
            from fastmcp.exceptions import ToolError as MCPError

            with pytest.raises(MCPError, match="Invalid"):
                await tools.update_userstory(1, subject="x")

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_method_with_custom_attributes(self):
        """Verifica update_userstory con atributos personalizados."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)
        mock_client = MagicMock()
        mock_client.update_userstory = MagicMock(return_value={"id": 1})
        tools.client = mock_client

        result = await tools.update_userstory(
            1, subject="new", project=1, custom_attributes={"1": "value"}
        )
        assert result == {"id": 1}


class TestValidateCustomAttributes:
    """Tests para el metodo _validate_custom_attributes."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_validate_custom_attributes_number_valid(self):
        """Verifica validacion de atributo numerico valido."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)

        # Should not raise
        await tools._validate_custom_attributes("token", 1, {"2": 42})

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_validate_custom_attributes_number_string_valid(self):
        """Verifica validacion de atributo numerico como string valido."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)

        # Should not raise
        await tools._validate_custom_attributes("token", 1, {"2": "42.5"})

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_validate_custom_attributes_number_invalid(self):
        """Verifica validacion de atributo numerico invalido."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)

        with pytest.raises(ValueError, match="number"):
            await tools._validate_custom_attributes("token", 1, {"2": "not a number"})

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_validate_custom_attributes_dropdown_valid(self):
        """Verifica validacion de atributo dropdown valido."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)

        # Should not raise
        await tools._validate_custom_attributes("token", 1, {"3": "High"})

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_validate_custom_attributes_dropdown_invalid(self):
        """Verifica validacion de atributo dropdown invalido."""
        mcp = FastMCP("Test")
        tools = UserStoryTools(mcp)

        with pytest.raises(ValueError, match="Invalid option"):
            await tools._validate_custom_attributes("token", 1, {"3": "InvalidOption"})


class TestListUserstoriesOptionalParams:
    """Tests para parametros opcionales en list_userstories."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_with_assigned_to(self, userstory_tools_instance):
        """Verifica list_userstories con assigned_to."""
        userstory_tools_instance._mock_client.get = AsyncMock(return_value=[{"id": 1}])

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_list_userstories"]

        result = await tool.fn(auth_token="token", project_id=1, assigned_to=5)
        assert len(result) == 1

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_with_milestone(self, userstory_tools_instance):
        """Verifica list_userstories con milestone_id."""
        userstory_tools_instance._mock_client.get = AsyncMock(return_value=[{"id": 1}])

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_list_userstories"]

        result = await tool.fn(auth_token="token", project_id=1, milestone_id=10)
        assert len(result) == 1

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_with_status(self, userstory_tools_instance):
        """Verifica list_userstories con status."""
        userstory_tools_instance._mock_client.get = AsyncMock(return_value=[{"id": 1}])

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_list_userstories"]

        result = await tool.fn(auth_token="token", project_id=1, status=2)
        assert len(result) == 1

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_with_tags_list(self, userstory_tools_instance):
        """Verifica list_userstories con tags como lista."""
        userstory_tools_instance._mock_client.get = AsyncMock(return_value=[{"id": 1}])

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_list_userstories"]

        result = await tool.fn(auth_token="token", project_id=1, tags=["tag1", "tag2"])
        assert len(result) == 1

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_with_tags_string(self, userstory_tools_instance):
        """Verifica list_userstories con tags como string."""
        userstory_tools_instance._mock_client.get = AsyncMock(return_value=[{"id": 1}])

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_list_userstories"]

        result = await tool.fn(auth_token="token", project_id=1, tags="tag1,tag2")
        assert len(result) == 1

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_with_all_filters(self, userstory_tools_instance):
        """Verifica list_userstories con todos los filtros opcionales."""
        userstory_tools_instance._mock_client.get = AsyncMock(return_value=[{"id": 1}])

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_list_userstories"]

        result = await tool.fn(
            auth_token="token",
            project_id=1,
            milestone_id=10,
            status=2,
            tags=["tag1"],
            assigned_to=5,
        )
        assert len(result) == 1

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_without_client_no_paginate(self):
        """Verifica list_userstories sin cliente y sin auto_paginate."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            with patch("src.application.tools.userstory_tools.AutoPaginator") as mock_paginator_cls:
                mock_paginator = MagicMock()
                mock_paginator.paginate_first_page = AsyncMock(return_value=[{"id": 1}])
                mock_paginator_cls.return_value = mock_paginator

                tools = UserStoryTools(mcp)
                tools.register_tools()
                registered = await tools.mcp.get_tools()
                tool = registered["taiga_list_userstories"]

                result = await tool.fn(auth_token="token", project_id=1, auto_paginate=False)
                assert len(result) == 1

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_without_client_with_paginate(self):
        """Verifica list_userstories sin cliente con auto_paginate=True."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            with patch("src.application.tools.userstory_tools.AutoPaginator") as mock_paginator_cls:
                mock_paginator = MagicMock()
                mock_paginator.paginate = AsyncMock(return_value=[{"id": 1}, {"id": 2}])
                mock_paginator_cls.return_value = mock_paginator

                tools = UserStoryTools(mcp)
                tools.register_tools()
                registered = await tools.mcp.get_tools()
                tool = registered["taiga_list_userstories"]

                result = await tool.fn(auth_token="token", project_id=1, auto_paginate=True)
                assert len(result) == 2

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_non_list_result(self, userstory_tools_instance):
        """Verifica list_userstories cuando el cliente retorna algo que no es lista."""
        userstory_tools_instance._mock_client.get = AsyncMock(return_value={"single": "value"})

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_list_userstories"]

        result = await tool.fn(auth_token="token", project_id=1)
        assert result == []


class TestCreateUserstoryOptionalParams:
    """Tests para parametros opcionales en create_userstory."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_create_userstory_with_all_params(self, userstory_tools_instance):
        """Verifica create_userstory con todos los parametros opcionales."""
        userstory_tools_instance._mock_client.post = AsyncMock(
            return_value={"id": 1, "ref": 1, "subject": "Test"}
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_userstory"]

        result = await tool.fn(
            auth_token="token",
            project_id=1,
            subject="Test Story",
            description="Description",
            status=1,
            points={"role1": 3},
            tags=["tag1", "tag2"],
            assigned_to=5,
            is_blocked=True,
            blocked_note="Blocked for reason",
            milestone=10,
            client_requirement=True,
            team_requirement=False,
        )
        assert result["id"] == 1

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_create_userstory_without_client(self):
        """Verifica create_userstory sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value={"id": 1, "ref": 1, "subject": "Test"})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            tools.register_tools()
            registered = await tools.mcp.get_tools()
            tool = registered["taiga_create_userstory"]

            result = await tool.fn(
                auth_token="token",
                project_id=1,
                subject="Test Story",
            )
            assert result["id"] == 1


class TestGetUserstoryOptionalParams:
    """Tests para get_userstory con parametros opcionales."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_without_client(self):
        """Verifica get_userstory sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value={"id": 1, "subject": "Test"})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            tools.register_tools()
            registered = await tools.mcp.get_tools()
            tool = registered["taiga_get_userstory"]

            result = await tool.fn(auth_token="token", userstory_id=1)
            assert result["id"] == 1


class TestUpdateUserstoryOptionalParams:
    """Tests para update_userstory con parametros opcionales."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_with_all_params(self, userstory_tools_instance):
        """Verifica update_userstory con todos los parametros opcionales."""
        userstory_tools_instance._mock_client.patch = AsyncMock(
            return_value={"id": 1, "subject": "Updated"}
        )

        tools = await userstory_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_userstory"]

        result = await tool.fn(
            auth_token="token",
            userstory_id=1,
            subject="Updated Story",
            description="New description",
            status=2,
            points={"role1": 5},
            tags=["tag3"],
            assigned_to=3,
            is_blocked=False,
            blocked_note=None,
            milestone=None,
            client_requirement=False,
            team_requirement=True,
            version=1,
        )
        assert result["id"] == 1

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_without_client(self):
        """Verifica update_userstory sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(return_value={"id": 1, "subject": "Updated"})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            tools.register_tools()
            registered = await tools.mcp.get_tools()
            tool = registered["taiga_update_userstory"]

            result = await tool.fn(
                auth_token="token",
                userstory_id=1,
                subject="Updated",
            )
            assert result["id"] == 1


class TestDeleteUserstoryOptionalParams:
    """Tests para delete_userstory sin cliente mock."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_delete_userstory_without_client(self):
        """Verifica delete_userstory sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete = AsyncMock(return_value=True)
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            tools.register_tools()
            registered = await tools.mcp.get_tools()
            tool = registered["taiga_delete_userstory"]

            result = await tool.fn(auth_token="token", userstory_id=1)
            assert result is True


class TestBulkOperationsWithoutClient:
    """Tests para operaciones bulk sin cliente mock."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_create_without_client(self):
        """Verifica bulk_create_userstories sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=[{"id": 1}])
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            tools.register_tools()
            registered = await tools.mcp.get_tools()
            tool = registered["taiga_bulk_create_userstories"]

            result = await tool.fn(
                auth_token="token",
                project_id=1,
                bulk_stories="Story 1\nStory 2",
            )
            assert len(result) >= 0

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_update_without_client(self):
        """Verifica bulk_update_userstories sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=[{"id": 1}])
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            tools.register_tools()
            registered = await tools.mcp.get_tools()
            tool = registered["taiga_bulk_update_userstories"]

            result = await tool.fn(
                auth_token="token",
                story_ids=[1, 2],
            )
            assert result is not None

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_delete_without_client(self):
        """Verifica bulk_delete_userstories sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            tools.register_tools()
            registered = await tools.mcp.get_tools()
            tool = registered["taiga_bulk_delete_userstories"]

            result = await tool.fn(
                auth_token="token",
                story_ids=[1, 2],
            )
            assert result is True


class TestMoveAndWatchWithoutClient:
    """Tests para move_to_milestone y watch/unwatch sin cliente mock."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_move_to_milestone_without_client(self):
        """Verifica move_to_milestone sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(
                return_value={"id": 1, "milestone": 5, "milestone_name": "Sprint 1"}
            )
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            tools.register_tools()
            registered = await tools.mcp.get_tools()
            tool = registered["taiga_move_to_milestone"]

            result = await tool.fn(auth_token="token", userstory_id=1, milestone_id=5)
            assert result["milestone"] == 5

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_watch_userstory_without_client(self):
        """Verifica watch_userstory sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value={"is_watcher": True, "total_watchers": 1})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            tools.register_tools()
            registered = await tools.mcp.get_tools()
            tool = registered["taiga_watch_userstory"]

            result = await tool.fn(auth_token="token", userstory_id=1)
            assert result["is_watcher"] is True

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_unwatch_userstory_without_client(self):
        """Verifica unwatch_userstory sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value={"is_watcher": False, "total_watchers": 0})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            tools.register_tools()
            registered = await tools.mcp.get_tools()
            tool = registered["taiga_unwatch_userstory"]

            result = await tool.fn(auth_token="token", userstory_id=1)
            assert result["is_watcher"] is False

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_upvote_userstory_without_client(self):
        """Verifica upvote_userstory sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value={"is_voter": True, "total_voters": 1})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            tools.register_tools()
            registered = await tools.mcp.get_tools()
            tool = registered["taiga_upvote_userstory"]

            result = await tool.fn(auth_token="token", userstory_id=1)
            assert result["is_voter"] is True

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_downvote_userstory_without_client(self):
        """Verifica downvote_userstory sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value={"is_voter": False, "total_voters": 0})
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            tools.register_tools()
            registered = await tools.mcp.get_tools()
            tool = registered["taiga_downvote_userstory"]

            result = await tool.fn(auth_token="token", userstory_id=1)
            assert result["is_voter"] is False


class TestHistoryAndVotersWithoutClient:
    """Tests para history y voters sin cliente mock."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_history_tool_without_client(self):
        """Verifica get_userstory_history tool sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=[{"id": 1}])
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            tools.register_tools()
            registered = await tools.mcp.get_tools()
            tool = registered["taiga_get_userstory_history"]

            result = await tool.fn(auth_token="token", userstory_id=1)
            assert len(result) >= 0

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_voters_tool_without_client(self):
        """Verifica get_userstory_voters tool sin cliente mock."""
        mcp = FastMCP("Test")
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(
                return_value=[{"id": 1, "username": "u", "full_name_display": "U", "photo": None}]
            )
            mock_cls.return_value = mock_client

            tools = UserStoryTools(mcp)
            tools.register_tools()
            registered = await tools.mcp.get_tools()
            tool = registered["taiga_get_userstory_voters"]

            result = await tool.fn(auth_token="token", userstory_id=1)
            assert len(result) == 1
