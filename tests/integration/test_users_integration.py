"""
Tests de integración para las herramientas de Usuarios del servidor MCP.
Prueba la integración completa de las funcionalidades de Usuarios.
"""

import httpx
import pytest
from fastmcp import FastMCP

from src.application.tools.auth_tools import AuthTools
from src.application.tools.user_tools import UserTools


class TestUsersIntegration:
    """Tests de integración para Usuarios."""

    @pytest.mark.integration
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_get_user_stats_after_authentication(self, mock_taiga_api) -> None:
        """
        Test que verifica obtención de estadísticas de usuario después de autenticación.
        1. Autenticar usuario
        2. Obtener información del usuario actual
        3. Obtener estadísticas del usuario
        """
        # Arrange
        mcp = FastMCP("Test Users Integration")
        auth_tools = AuthTools(mcp)
        user_tools = UserTools(mcp)
        auth_tools.register_tools()
        user_tools.register_tools()

        # 1. Autenticar usuario
        mock_taiga_api.post("https://api.taiga.io/api/v1/auth").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 12345,
                    "username": "testuser",
                    "full_name": "Test User",
                    "email": "test@example.com",
                    "auth_token": "valid_token_123",
                    "refresh": "refresh_token_123",
                },
            )
        )

        auth_result = await auth_tools.authenticate(
            username="test@example.com", password="password123"
        )

        assert auth_result["auth_token"] == "valid_token_123"
        user_id = auth_result["id"]

        # 2. Obtener información del usuario actual
        mock_taiga_api.get("https://api.taiga.io/api/v1/users/me").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": user_id,
                    "username": "testuser",
                    "full_name": "Test User",
                    "email": "test@example.com",
                    "total_private_projects": 5,
                    "total_public_projects": 3,
                    "roles": ["Product Owner", "Developer"],
                },
            )
        )

        current_user = await auth_tools.get_current_user(auth_token=auth_result["auth_token"])

        assert current_user["id"] == user_id
        assert current_user["username"] == "testuser"

        # 3. Obtener estadísticas del usuario
        mock_taiga_api.get(f"https://api.taiga.io/api/v1/users/{user_id}/stats").mock(
            return_value=httpx.Response(
                200,
                json={
                    "total_num_projects": 8,
                    "total_num_closed_userstories": 150,
                    "total_num_contacts": 25,
                    "roles": ["Product Owner", "Developer"],
                    "projects_with_most_activity": [
                        {
                            "id": 1,
                            "name": "Main Project",
                            "slug": "main-project",
                            "total_activity": 300,
                        },
                        {
                            "id": 2,
                            "name": "Secondary Project",
                            "slug": "secondary-project",
                            "total_activity": 200,
                        },
                    ],
                    "total_activity": {"last_week": 50, "last_month": 200, "last_year": 2500},
                },
            )
        )

        stats_result = await user_tools.get_user_stats(
            auth_token=auth_result["auth_token"], user_id=user_id
        )

        # Assert
        assert stats_result["total_num_projects"] == 8
        assert stats_result["total_num_closed_userstories"] == 150
        assert stats_result["total_num_contacts"] == 25
        assert len(stats_result["projects_with_most_activity"]) == 2
        assert stats_result["total_activity"]["last_week"] == 50

    @pytest.mark.integration
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_get_different_user_stats(self, mock_taiga_api, auth_token) -> None:
        """
        Test que verifica obtención de estadísticas de otro usuario.
        """
        # Arrange
        mcp = FastMCP("Test Users Integration")
        user_tools = UserTools(mcp)
        user_tools.register_tools()
        other_user_id = 67890

        # Obtener estadísticas de otro usuario
        mock_taiga_api.get(f"https://api.taiga.io/api/v1/users/{other_user_id}/stats").mock(
            return_value=httpx.Response(
                200,
                json={
                    "total_num_projects": 3,
                    "total_num_closed_userstories": 45,
                    "total_num_contacts": 10,
                    "roles": ["Developer"],
                    "projects_with_most_activity": [
                        {
                            "id": 5,
                            "name": "Dev Project",
                            "slug": "dev-project",
                            "total_activity": 100,
                        }
                    ],
                    "total_activity": {"last_week": 15, "last_month": 60, "last_year": 500},
                },
            )
        )

        # Act
        result = await user_tools.get_user_stats(auth_token=auth_token, user_id=other_user_id)

        # Assert
        assert result["total_num_projects"] == 3
        assert result["total_num_closed_userstories"] == 45
        assert result["roles"] == ["Developer"]
        assert len(result["projects_with_most_activity"]) == 1
        assert result["projects_with_most_activity"][0]["name"] == "Dev Project"

    @pytest.mark.integration
    @pytest.mark.users
    @pytest.mark.asyncio
    async def test_user_stats_with_no_activity(self, mock_taiga_api, auth_token) -> None:
        """
        Test de estadísticas de usuario sin actividad.
        """
        # Arrange
        mcp = FastMCP("Test Users Integration")
        user_tools = UserTools(mcp)
        user_tools.register_tools()
        new_user_id = 11111

        mock_taiga_api.get(f"https://api.taiga.io/api/v1/users/{new_user_id}/stats").mock(
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
        result = await user_tools.get_user_stats(auth_token=auth_token, user_id=new_user_id)

        # Assert
        assert result["total_num_projects"] == 0
        assert result["total_num_closed_userstories"] == 0
        assert result["total_num_contacts"] == 0
        assert result["roles"] == []
        assert result["projects_with_most_activity"] == []
        assert result["total_activity"]["last_week"] == 0
        assert result["total_activity"]["last_month"] == 0
        assert result["total_activity"]["last_year"] == 0
