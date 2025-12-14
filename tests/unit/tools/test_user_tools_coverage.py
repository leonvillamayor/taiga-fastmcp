"""
Tests adicionales para cobertura completa de user_tools.py.
Cubre las herramientas MCP registradas, excepciones y branches no cubiertos.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.application.tools.user_tools import UserTools
from src.domain.exceptions import AuthenticationError, TaigaAPIError


@pytest.fixture
def user_tools_instance():
    """Fixture que crea una instancia de UserTools con mocks."""
    mcp = FastMCP("Test")
    with patch("src.application.tools.user_tools.TaigaAPIClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client
        tools = UserTools(mcp)
        tools.register_tools()
        tools._mock_client = mock_client
        tools._mock_client_cls = mock_client_cls
        yield tools


class TestUserToolsSetClient:
    """Tests para el método set_client."""

    @pytest.mark.unit
    @pytest.mark.users
    def test_set_client_success(self):
        """Verifica que set_client establece el cliente correctamente."""
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)

        mock_client = MagicMock()
        user_tools.set_client(mock_client)

        assert user_tools.client is mock_client

    @pytest.mark.unit
    @pytest.mark.users
    def test_set_client_with_none(self):
        """Verifica que set_client puede establecer None."""
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)
        user_tools.client = MagicMock()  # Set something first

        user_tools.set_client(None)

        assert user_tools.client is None


class TestUserToolsLegacyRegisterTools:
    """Tests para el método legacy _register_tools."""

    @pytest.mark.unit
    @pytest.mark.users
    def test_legacy_register_tools_calls_register_tools(self):
        """Verifica que _register_tools llama a register_tools."""
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)

        with patch.object(user_tools, "register_tools") as mock_register:
            user_tools._register_tools()
            mock_register.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_legacy_register_tools_registers_all_tools(self):
        """Verifica que _register_tools registra todas las herramientas."""
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)

        user_tools._register_tools()
        tools = await mcp.get_tools()

        assert "taiga_get_user_stats" in tools
        assert "taiga_list_users" in tools


class TestListUsersRegisteredTool:
    """Tests para la herramienta registrada taiga_list_users."""

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_list_users_tool_is_registered(self):
        """Verifica que la herramienta list_users está registrada."""
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)
        user_tools.register_tools()

        tools = await mcp.get_tools()

        assert "taiga_list_users" in tools

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_list_users_success_auto_paginate_true(self, user_tools_instance):
        """Verifica list_users con auto_paginate=True (default)."""
        expected_users = [
            {"id": 1, "username": "user1", "full_name": "User One"},
            {"id": 2, "username": "user2", "full_name": "User Two"},
        ]

        with patch("src.application.tools.user_tools.AutoPaginator") as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.paginate = AsyncMock(return_value=expected_users)
            mock_paginator_cls.return_value = mock_paginator

            tools = await user_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_users"]

            result = await tool.fn(
                auth_token="valid_token",
                auto_paginate=True,
            )

            assert result == expected_users
            mock_paginator.paginate.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_list_users_success_auto_paginate_false(self, user_tools_instance):
        """Verifica list_users con auto_paginate=False."""
        expected_users = [{"id": 1, "username": "user1"}]

        with patch("src.application.tools.user_tools.AutoPaginator") as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.paginate_first_page = AsyncMock(return_value=expected_users)
            mock_paginator_cls.return_value = mock_paginator

            tools = await user_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_users"]

            result = await tool.fn(
                auth_token="valid_token",
                auto_paginate=False,
            )

            assert result == expected_users
            mock_paginator.paginate_first_page.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_list_users_with_project_id(self, user_tools_instance):
        """Verifica list_users con project_id especificado."""
        expected_users = [{"id": 1, "username": "project_member"}]

        with patch("src.application.tools.user_tools.AutoPaginator") as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.paginate = AsyncMock(return_value=expected_users)
            mock_paginator_cls.return_value = mock_paginator

            tools = await user_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_users"]

            result = await tool.fn(
                auth_token="valid_token",
                project_id=123,
            )

            assert result == expected_users
            # Verify params include project
            call_args = mock_paginator.paginate.call_args
            assert call_args[1]["params"]["project"] == 123

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_list_users_without_project_id(self, user_tools_instance):
        """Verifica list_users sin project_id (None)."""
        expected_users = [{"id": 1, "username": "all_user"}]

        with patch("src.application.tools.user_tools.AutoPaginator") as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.paginate = AsyncMock(return_value=expected_users)
            mock_paginator_cls.return_value = mock_paginator

            tools = await user_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_users"]

            result = await tool.fn(
                auth_token="valid_token",
                project_id=None,
            )

            assert result == expected_users
            # Verify params don't include project
            call_args = mock_paginator.paginate.call_args
            assert "project" not in call_args[1]["params"]

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_list_users_returns_empty_list_when_not_list(self, user_tools_instance):
        """Verifica que list_users retorna lista vacía si el resultado no es lista."""
        with patch("src.application.tools.user_tools.AutoPaginator") as mock_paginator_cls:
            mock_paginator = MagicMock()
            # Return non-list (e.g., dict or None)
            mock_paginator.paginate = AsyncMock(return_value={"error": "unexpected"})
            mock_paginator_cls.return_value = mock_paginator

            tools = await user_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_users"]

            result = await tool.fn(auth_token="valid_token")

            assert result == []

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_list_users_returns_empty_list_when_none(self, user_tools_instance):
        """Verifica que list_users retorna lista vacía si el resultado es None."""
        with patch("src.application.tools.user_tools.AutoPaginator") as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.paginate = AsyncMock(return_value=None)
            mock_paginator_cls.return_value = mock_paginator

            tools = await user_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_users"]

            result = await tool.fn(auth_token="valid_token")

            assert result == []


class TestListUsersExceptionHandling:
    """Tests para manejo de excepciones en list_users."""

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_list_users_authentication_error(self, user_tools_instance):
        """Verifica manejo de AuthenticationError en list_users."""
        with patch("src.application.tools.user_tools.AutoPaginator") as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.paginate = AsyncMock(side_effect=AuthenticationError("Token expired"))
            mock_paginator_cls.return_value = mock_paginator

            tools = await user_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_users"]

            with pytest.raises(ToolError, match="Authentication failed"):
                await tool.fn(auth_token="expired_token")

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_list_users_taiga_api_error(self, user_tools_instance):
        """Verifica manejo de TaigaAPIError en list_users."""
        with patch("src.application.tools.user_tools.AutoPaginator") as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.paginate = AsyncMock(side_effect=TaigaAPIError("Rate limit exceeded"))
            mock_paginator_cls.return_value = mock_paginator

            tools = await user_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_users"]

            with pytest.raises(ToolError, match="Failed to list users: Rate limit exceeded"):
                await tool.fn(auth_token="valid_token")

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_list_users_unexpected_error(self, user_tools_instance):
        """Verifica manejo de excepciones inesperadas en list_users."""
        with patch("src.application.tools.user_tools.AutoPaginator") as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.paginate = AsyncMock(side_effect=RuntimeError("Connection failed"))
            mock_paginator_cls.return_value = mock_paginator

            tools = await user_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_users"]

            with pytest.raises(ToolError, match="Unexpected error: Connection failed"):
                await tool.fn(auth_token="valid_token")


class TestListUsersDirectMethod:
    """Tests para el método directo list_users (referencia almacenada)."""

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_list_users_direct_method_exists(self, user_tools_instance):
        """Verifica que el método directo list_users existe."""
        assert hasattr(user_tools_instance, "list_users")
        assert callable(user_tools_instance.list_users)

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_list_users_direct_method_is_async(self, user_tools_instance):
        """Verifica que el método directo list_users es async."""
        import inspect

        assert inspect.iscoroutinefunction(user_tools_instance.list_users)

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_list_users_direct_method_success(self, user_tools_instance):
        """Verifica que el método directo list_users funciona."""
        expected_users = [{"id": 1, "username": "direct_user"}]

        with patch("src.application.tools.user_tools.AutoPaginator") as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.paginate = AsyncMock(return_value=expected_users)
            mock_paginator_cls.return_value = mock_paginator

            result = await user_tools_instance.list_users(auth_token="valid_token")

            assert result == expected_users


class TestGetUserStatsRegisteredTool:
    """Tests adicionales para la herramienta registrada taiga_get_user_stats."""

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_get_user_stats_via_registered_tool(self, user_tools_instance):
        """Verifica get_user_stats a través de la herramienta registrada."""
        expected_stats = {
            "total_num_projects": 5,
            "total_num_closed_userstories": 50,
            "total_num_contacts": 10,
            "roles": ["Developer"],
            "created_date": "2024-01-01",
            "projects_with_me": {"1": "Project A"},
            "projects_with_most_activity": [{"id": 1}],
            "total_activity": {"total": 100},
        }

        user_tools_instance._mock_client.get = AsyncMock(return_value=expected_stats)

        tools = await user_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_user_stats"]

        result = await tool.fn(auth_token="valid_token", user_id=42)

        assert result["total_num_projects"] == 5
        assert result["total_num_closed_userstories"] == 50
        assert result["message"] == "Retrieved stats for user 42"

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_get_user_stats_with_missing_fields(self, user_tools_instance):
        """Verifica get_user_stats con campos faltantes usa valores por defecto."""
        # Return empty dict to test default values
        user_tools_instance._mock_client.get = AsyncMock(return_value={})

        tools = await user_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_user_stats"]

        result = await tool.fn(auth_token="valid_token", user_id=42)

        assert result["total_num_projects"] == 0
        assert result["total_num_closed_userstories"] == 0
        assert result["total_num_contacts"] == 0
        assert result["roles"] == []
        assert result["created_date"] is None
        assert result["projects_with_me"] == {}
        assert result["projects_with_most_activity"] == []
        assert result["total_activity"] == {}


class TestUserToolsInitialization:
    """Tests para la inicialización de UserTools."""

    @pytest.mark.unit
    @pytest.mark.users
    def test_user_tools_init_sets_mcp(self):
        """Verifica que __init__ establece el MCP server."""
        mcp = FastMCP("TestServer")
        user_tools = UserTools(mcp)

        assert user_tools.mcp is mcp

    @pytest.mark.unit
    @pytest.mark.users
    def test_user_tools_init_sets_config(self):
        """Verifica que __init__ crea la configuración."""
        mcp = FastMCP("TestServer")
        user_tools = UserTools(mcp)

        assert user_tools.config is not None

    @pytest.mark.unit
    @pytest.mark.users
    def test_user_tools_init_client_is_none(self):
        """Verifica que __init__ establece client como None."""
        mcp = FastMCP("TestServer")
        user_tools = UserTools(mcp)

        assert user_tools.client is None


class TestListUsersEdgeCases:
    """Tests para casos edge en list_users."""

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_list_users_empty_list_response(self, user_tools_instance):
        """Verifica list_users con respuesta de lista vacía."""
        with patch("src.application.tools.user_tools.AutoPaginator") as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.paginate = AsyncMock(return_value=[])
            mock_paginator_cls.return_value = mock_paginator

            tools = await user_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_users"]

            result = await tool.fn(auth_token="valid_token")

            assert result == []
            assert isinstance(result, list)

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_list_users_large_response(self, user_tools_instance):
        """Verifica list_users con muchos usuarios."""
        large_user_list = [{"id": i, "username": f"user{i}"} for i in range(100)]

        with patch("src.application.tools.user_tools.AutoPaginator") as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.paginate = AsyncMock(return_value=large_user_list)
            mock_paginator_cls.return_value = mock_paginator

            tools = await user_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_users"]

            result = await tool.fn(auth_token="valid_token")

            assert len(result) == 100
            assert result[0]["id"] == 0
            assert result[99]["id"] == 99


class TestUserToolsDocstrings:
    """Tests para verificar docstrings en UserTools."""

    @pytest.mark.unit
    @pytest.mark.users
    def test_list_users_has_docstring(self):
        """Verifica que list_users tiene docstring."""
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)
        user_tools.register_tools()

        assert user_tools.list_users.__doc__ is not None
        assert len(user_tools.list_users.__doc__) > 50

    @pytest.mark.unit
    @pytest.mark.users
    def test_get_user_stats_has_docstring(self):
        """Verifica que get_user_stats tiene docstring."""
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)
        user_tools.register_tools()

        assert user_tools.get_user_stats.__doc__ is not None
        assert len(user_tools.get_user_stats.__doc__) > 50

    @pytest.mark.unit
    @pytest.mark.users
    def test_usertools_class_has_docstring(self):
        """Verifica que la clase UserTools tiene docstring."""
        assert UserTools.__doc__ is not None
        assert "User" in UserTools.__doc__
