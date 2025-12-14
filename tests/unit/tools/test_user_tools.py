"""
Tests unitarios para las herramientas de Usuarios del servidor MCP.
Cubre las funcionalidades USER-002 según Documentacion/taiga.md.
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.application.tools.user_tools import UserTools


class TestGetUserStatsTool:
    """Tests para la herramienta get_user_stats - USER-002."""

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_get_user_stats_tool_is_registered(self) -> None:
        """
        USER-002: Obtener estadísticas de usuario.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)

        # Act
        user_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_get_user_stats" in tool_names

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_get_user_stats_success(self, mock_taiga_api) -> None:
        """
        Verifica que obtiene estadísticas de usuario correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)
        user_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/users/12345/stats").mock(
            return_value=httpx.Response(
                200,
                json={
                    "total_num_projects": 15,
                    "total_num_closed_userstories": 125,
                    "total_num_contacts": 23,
                    "roles": ["Product Owner", "Developer", "Scrum Master"],
                    "projects_with_most_activity": [
                        {
                            "id": 1,
                            "name": "Main Project",
                            "slug": "main-project",
                            "total_activity": 250,
                        },
                        {
                            "id": 2,
                            "name": "Side Project",
                            "slug": "side-project",
                            "total_activity": 150,
                        },
                    ],
                    "total_activity": {"last_week": 45, "last_month": 180, "last_year": 2000},
                },
            )
        )

        # Act
        result = await user_tools.get_user_stats(auth_token="valid_token", user_id=12345)

        # Assert
        assert result["total_num_projects"] == 15
        assert result["total_num_closed_userstories"] == 125
        assert result["total_num_contacts"] == 23
        assert "Product Owner" in result["roles"]
        assert len(result["projects_with_most_activity"]) == 2
        assert result["total_activity"]["last_week"] == 45

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_get_user_stats_not_found(self, mock_taiga_api) -> None:
        """
        Verifica manejo de usuario no encontrado.
        """
        # Arrange
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)
        user_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/users/99999/stats").mock(
            return_value=httpx.Response(404, json={"detail": "User not found"})
        )

        # Act & Assert
        with pytest.raises(ToolError, match="User not found"):
            await user_tools.get_user_stats(auth_token="valid_token", user_id=99999)

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_get_user_stats_permission_denied(self, mock_taiga_api) -> None:
        """
        Verifica manejo de permisos insuficientes.
        """
        # Arrange
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)
        user_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/users/12345/stats").mock(
            return_value=httpx.Response(
                403, json={"detail": "You do not have permission to access user stats"}
            )
        )

        # Act & Assert
        with pytest.raises(ToolError, match="permission"):
            await user_tools.get_user_stats(auth_token="valid_token", user_id=12345)

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_get_user_stats_empty_stats(self, mock_taiga_api) -> None:
        """
        Verifica manejo de usuario sin estadísticas.
        """
        # Arrange
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)
        user_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/users/12345/stats").mock(
            return_value=httpx.Response(
                200,
                json={
                    "total_num_projects": 0,
                    "total_num_closed_userstories": 0,
                    "total_num_contacts": 0,
                    "roles": [],
                    "projects_with_most_activity": [],
                    "total_activity": {"last_week": 0, "last_month": 0, "last_year": 0},
                },
            )
        )

        # Act
        result = await user_tools.get_user_stats(auth_token="valid_token", user_id=12345)

        # Assert
        assert result["total_num_projects"] == 0
        assert result["roles"] == []
        assert result["projects_with_most_activity"] == []
        assert result["total_activity"]["last_week"] == 0


class TestUserToolsBestPractices:
    """Tests para verificar buenas prácticas en herramientas de Usuarios."""

    @pytest.mark.unit
    @pytest.mark.users
    def test_user_tools_use_async_await(self) -> None:
        """
        RNF-001: Usar async/await para operaciones I/O.
        Verifica que las herramientas de usuarios son asíncronas.
        """
        # Arrange
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)
        user_tools.register_tools()

        # Act
        import inspect

        # Assert
        assert inspect.iscoroutinefunction(user_tools.get_user_stats)

    @pytest.mark.unit
    @pytest.mark.users
    def test_user_tools_have_docstrings(self) -> None:
        """
        RNF-006: El código DEBE tener docstrings descriptivos.
        Verifica que las herramientas tienen documentación.
        """
        # Arrange
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)
        user_tools.register_tools()

        # Act & Assert
        assert user_tools.get_user_stats.__doc__ is not None
        assert (
            "stats" in user_tools.get_user_stats.__doc__.lower()
            or "statistics" in user_tools.get_user_stats.__doc__.lower()
        )

    @pytest.mark.unit
    @pytest.mark.users
    def test_user_tools_use_type_hints(self) -> None:
        """
        RNF-005: El código DEBE usar type hints completos.
        Verifica que las herramientas tienen type hints.
        """
        # Arrange
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)
        user_tools.register_tools()

        # Act
        import inspect

        # Assert
        sig = inspect.signature(user_tools.get_user_stats)
        assert sig.parameters["auth_token"].annotation is str
        assert sig.parameters["user_id"].annotation is int
        assert sig.return_annotation != inspect.Signature.empty

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_user_tools_handle_errors_properly(self) -> None:
        """
        RF-026: El servidor DEBE implementar manejo de errores con ToolError.
        Verifica que las herramientas manejan errores correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)
        user_tools.register_tools()

        # Test varios tipos de errores
        test_cases = [
            (httpx.NetworkError("Network error"), "Network error"),
            (httpx.TimeoutException("Timeout"), "Timeout"),
            (ValueError("Invalid data"), "Invalid data"),
            (Exception("Unknown error"), "Unknown error"),
        ]

        for error, expected_message in test_cases:
            with patch("httpx.AsyncClient.get") as mock_get:
                mock_get.side_effect = error

                # Act & Assert
                with pytest.raises(ToolError) as exc_info:
                    await user_tools.get_user_stats("token", 123)

                assert expected_message in str(exc_info.value)


class TestUserToolsExceptionHandling:
    """Tests para manejo de excepciones en UserTools."""

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_get_user_stats_authentication_error(self) -> None:
        """
        Verifica que se maneja correctamente AuthenticationError.
        """
        from src.domain.exceptions import AuthenticationError

        # Arrange
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)
        user_tools.register_tools()

        # Mock TaigaAPIClient para lanzar AuthenticationError
        with patch("src.application.tools.user_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.side_effect = AuthenticationError("Invalid token")

            # Act & Assert
            with pytest.raises(ToolError, match="Authentication failed"):
                await user_tools.get_user_stats(auth_token="invalid_token", user_id=123)

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_get_user_stats_taiga_api_error(self) -> None:
        """
        Verifica que se maneja correctamente TaigaAPIError.
        """
        from src.domain.exceptions import TaigaAPIError

        # Arrange
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)
        user_tools.register_tools()

        # Mock TaigaAPIClient para lanzar TaigaAPIError
        with patch("src.application.tools.user_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.side_effect = TaigaAPIError("API rate limit exceeded")

            # Act & Assert
            with pytest.raises(ToolError, match="API error: API rate limit exceeded"):
                await user_tools.get_user_stats(auth_token="valid_token", user_id=123)

    @pytest.mark.unit
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_get_user_stats_unexpected_error(self) -> None:
        """
        Verifica que se manejan correctamente errores inesperados.
        """
        # Arrange
        mcp = FastMCP("Test")
        user_tools = UserTools(mcp)
        user_tools.register_tools()

        # Mock TaigaAPIClient para lanzar excepción genérica
        with patch("src.application.tools.user_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.side_effect = RuntimeError("Unexpected server error")

            # Act & Assert
            with pytest.raises(ToolError, match="Unexpected error: Unexpected server error"):
                await user_tools.get_user_stats(auth_token="valid_token", user_id=123)
