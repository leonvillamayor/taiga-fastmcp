"""
Tests unitarios para herramientas de autenticación.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError as MCPError

from src.application.tools.auth_tools import AuthTools
from src.domain.exceptions import AuthenticationError, TaigaAPIError


class TestAuthTools:
    """Tests para la clase AuthTools."""

    @pytest.fixture
    def mcp_mock(self) -> None:
        """Mock del servidor MCP."""
        mcp = Mock(spec=FastMCP)
        mcp.tool = Mock(side_effect=lambda **kwargs: lambda fn: fn)
        return mcp

    @pytest.fixture
    def auth_tools(self, mcp_mock) -> None:
        """Instancia de AuthTools con mocks."""
        with patch("src.application.tools.auth_tools.TaigaConfig") as mock_config:
            config_instance = Mock()
            config_instance.taiga_username = "test@example.com"
            config_instance.taiga_password = "testpass"
            mock_config.return_value = config_instance

            tools = AuthTools(mcp_mock)
            tools.register_tools()
            return tools

    @pytest.mark.asyncio
    async def test_authenticate_with_provided_credentials(self, auth_tools) -> None:
        """Verifica autenticación con credenciales proporcionadas."""
        # Setup
        expected_result = {
            "id": 123,
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True,
            "auth_token": "test_token",
            "refresh": "refresh_token",
        }

        with patch("src.application.tools.auth_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate = AsyncMock(return_value=expected_result)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Act
            result = await auth_tools.authenticate("user@test.com", "password123")

            # Assert
            assert result["authenticated"] is True
            assert result["id"] == 123
            assert result["username"] == "testuser"
            assert result["email"] == "test@example.com"
            assert result["auth_token"] == "test_token"
            assert result["refresh"] == "refresh_token"
            assert "Successfully authenticated" in result["message"]

            # Verify tokens stored
            assert auth_tools._auth_token == "test_token"
            assert auth_tools._refresh_token == "refresh_token"
            # Note: _user_data only stores user profile (no tokens for security)
            assert auth_tools._user_data == {
                "id": expected_result["id"],
                "username": expected_result["username"],
                "email": expected_result["email"],
                "full_name": expected_result["full_name"],
            }

            mock_client.authenticate.assert_called_once_with("user@test.com", "password123")

    @pytest.mark.asyncio
    async def test_authenticate_with_config_credentials(self, auth_tools) -> None:
        """Verifica autenticación usando credenciales de configuración."""
        # Setup
        expected_result = {
            "id": 456,
            "username": "configuser",
            "email": "config@example.com",
            "full_name": "Config User",
            "is_active": True,
            "auth_token": "config_token",
            "refresh": "config_refresh",
        }

        with patch("src.application.tools.auth_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate = AsyncMock(return_value=expected_result)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Act - sin credenciales, usa las del config
            result = await auth_tools.authenticate()

            # Assert
            assert result["authenticated"] is True
            assert result["id"] == 456
            assert result["auth_token"] == "config_token"

            # Should use config credentials
            mock_client.authenticate.assert_called_once_with("test@example.com", "testpass")

    @pytest.mark.asyncio
    async def test_authenticate_without_any_credentials(self, auth_tools) -> None:
        """Verifica que falla sin credenciales."""
        # Setup - remove config credentials
        auth_tools.config.taiga_username = None
        auth_tools.config.taiga_password = None

        # Act & Assert
        with pytest.raises(MCPError) as exc:
            await auth_tools.authenticate()

        assert "Username and password are required" in str(exc.value)

    @pytest.mark.asyncio
    async def test_authenticate_with_authentication_error(self, auth_tools) -> None:
        """Verifica manejo de error de autenticación."""
        # Setup
        with patch("src.application.tools.auth_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate = AsyncMock(
                side_effect=AuthenticationError("Invalid credentials")
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Act & Assert
            with pytest.raises(MCPError) as exc:
                await auth_tools.authenticate("user@test.com", "wrong_pass")

            assert "Invalid username or password: Invalid credentials" in str(exc.value)

    @pytest.mark.asyncio
    async def test_authenticate_with_api_error(self, auth_tools) -> None:
        """Verifica manejo de error de API."""
        # Setup
        with patch("src.application.tools.auth_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate = AsyncMock(side_effect=TaigaAPIError("Server error"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Act & Assert
            with pytest.raises(MCPError) as exc:
                await auth_tools.authenticate("user@test.com", "password")

            assert "Unexpected error during authentication: Server error" in str(exc.value)

    @pytest.mark.asyncio
    async def test_authenticate_with_unexpected_error(self, auth_tools) -> None:
        """Verifica manejo de error inesperado."""
        # Setup
        with patch("src.application.tools.auth_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate = AsyncMock(side_effect=Exception("Unexpected error"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Act & Assert
            with pytest.raises(MCPError) as exc:
                await auth_tools.authenticate("user@test.com", "password")

            assert "Unexpected error during authentication: Unexpected error" in str(exc.value)

    @pytest.mark.asyncio
    async def test_refresh_token_tool(self, auth_tools) -> None:
        """Verifica la herramienta de refresh token."""
        # Setup token inicial
        auth_tools._refresh_token = "old_refresh_token"

        expected_result = {"auth_token": "new_auth_token", "refresh": "new_refresh_token"}

        with patch("src.application.tools.auth_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.refresh_auth_token = AsyncMock(return_value=expected_result)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Act
            result = await auth_tools.refresh_token()

            # Assert
            assert result["auth_token"] == "new_auth_token"
            assert result["refresh"] == "new_refresh_token"
            assert result["authenticated"] is True
            assert "Successfully refreshed" in result["message"]

            # Verify tokens updated
            assert auth_tools._auth_token == "new_auth_token"
            assert auth_tools._refresh_token == "new_refresh_token"

    @pytest.mark.asyncio
    async def test_refresh_token_without_token(self, auth_tools) -> None:
        """Verifica que refresh token falla sin token previo."""
        # Setup - no refresh token
        auth_tools._refresh_token = None

        # Act & Assert
        with pytest.raises(MCPError) as exc:
            await auth_tools.refresh_token()

        assert "No refresh token available" in str(exc.value)

    @pytest.mark.asyncio
    async def test_get_current_user(self, auth_tools) -> None:
        """Verifica obtener usuario actual."""
        # Setup
        auth_tools._auth_token = "valid_token"

        expected_user = {
            "id": 789,
            "username": "currentuser",
            "email": "current@example.com",
            "full_name": "Current User",
            "bio": "Test bio",
            "lang": "en",
            "timezone": "UTC",
            "is_active": True,
            "roles": ["admin"],
            "total_private_projects": 5,
            "total_public_projects": 10,
        }

        with patch("src.application.tools.auth_tools.TaigaAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=expected_user)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Act
            result = await auth_tools.get_current_user()

            # Assert
            assert result["id"] == 789
            assert result["username"] == "currentuser"
            assert result["email"] == "current@example.com"
            mock_client.get.assert_called_once_with("/users/me")

    @pytest.mark.asyncio
    async def test_get_current_user_without_auth(self, auth_tools) -> None:
        """Verifica que get_current_user falla sin autenticación."""
        # Setup - no auth token
        auth_tools._auth_token = None

        # Act & Assert
        with pytest.raises(MCPError) as exc:
            await auth_tools.get_current_user()

        assert "Not authenticated" in str(exc.value)

    @pytest.mark.asyncio
    async def test_logout(self, auth_tools) -> None:
        """Verifica logout exitoso."""
        # Setup
        auth_tools._auth_token = "token"
        auth_tools._refresh_token = "refresh"
        auth_tools._user_data = {"user": "data"}

        # Act
        result = await auth_tools.logout()

        # Assert
        assert result["authenticated"] is False
        assert "Successfully logged out" in result["message"]
        assert auth_tools._auth_token is None
        assert auth_tools._refresh_token is None
        assert auth_tools._user_data is None

    def test_register_tools(self, mcp_mock) -> None:
        """Verifica que los tools se registran correctamente."""
        # Setup
        with patch("src.application.tools.auth_tools.TaigaConfig"):
            tools = AuthTools(mcp_mock)

            # Act
            tools.register_tools()

            # Assert - verificar que se registraron los tools
            calls = mcp_mock.tool.call_args_list
            tool_names = [call[1]["name"] for call in calls]

            assert "taiga_authenticate" in tool_names
            assert "taiga_refresh_token" in tool_names
            assert "taiga_get_current_user" in tool_names
            assert "taiga_logout" in tool_names

    def test_get_auth_token(self, auth_tools) -> None:
        """Verifica obtener el token de autenticación actual."""
        # Sin token
        assert auth_tools.get_auth_token() is None

        # Con token
        auth_tools._auth_token = "test_token"
        assert auth_tools.get_auth_token() == "test_token"

    def test_is_authenticated(self, auth_tools) -> None:
        """Verifica el estado de autenticación."""
        # Sin token
        assert auth_tools.is_authenticated() is False

        # Con token
        auth_tools._auth_token = "test_token"
        assert auth_tools.is_authenticated() is True

        # Token removido
        auth_tools._auth_token = None
        assert auth_tools.is_authenticated() is False
