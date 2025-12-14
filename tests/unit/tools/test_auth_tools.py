"""
Tests unitarios para las herramientas de autenticación del servidor MCP.
Verifica las herramientas de auth según RF-010.
"""

from unittest.mock import Mock, patch

import httpx
import pytest
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError

from src.application.tools.auth_tools import AuthTools


class TestAuthenticateTool:
    """Tests para la herramienta de autenticación - RF-010."""

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_authenticate_tool_is_registered(self) -> None:
        """
        RF-010: Las herramientas DEBEN cubrir autenticación de Taiga.
        Verifica que la herramienta authenticate está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)

        # Act
        auth_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_authenticate" in tool_names

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_authenticate_with_valid_credentials(self, mock_taiga_api) -> None:
        """
        Verifica que authenticate funciona con credenciales válidas.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Mock de respuesta exitosa
        mock_taiga_api.post("https://api.taiga.io/api/v1/auth").mock(
            return_value=httpx.Response(
                200,
                json={
                    "auth_token": "valid_token_123",
                    "refresh": "refresh_token_456",
                    "id": 12345,
                    "username": "testuser",
                },
            )
        )

        # Act
        result = await auth_tools.authenticate(username="test@example.com", password="testpass123")

        # Assert
        assert result is not None
        assert result["auth_token"] == "valid_token_123"
        assert result["refresh"] == "refresh_token_456"
        assert result["username"] == "testuser"

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_authenticate_with_invalid_credentials(self, mock_taiga_api) -> None:
        """
        RF-041: El servidor DEBE manejar errores de autenticación.
        Verifica que authenticate maneja credenciales inválidas.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Mock de respuesta de error
        mock_taiga_api.post("https://api.taiga.io/api/v1/auth").mock(
            return_value=httpx.Response(401, json={"detail": "Invalid username or password"})
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Invalid username or password"):
            await auth_tools.authenticate(username="invalid@example.com", password="wrongpass")

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_authenticate_handles_network_errors(self) -> None:
        """
        Verifica que authenticate maneja errores de red.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = httpx.NetworkError("Connection refused")

            # Act & Assert
            with pytest.raises(ToolError, match="Network error"):
                await auth_tools.authenticate(username="test@example.com", password="testpass")

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_authenticate_stores_token_in_context(self) -> None:
        """
        Verifica que authenticate almacena el token en el contexto.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        ctx = Mock(spec=Context)
        ctx.set_state = Mock()

        with (
            patch.object(auth_tools, "get_context", return_value=ctx),
            patch("httpx.AsyncClient.post") as mock_post,
        ):
            # Create a mock request
            mock_request = httpx.Request("POST", "https://api.taiga.io/api/v1/auth")
            mock_post.return_value = httpx.Response(
                200,
                json={"auth_token": "token123", "refresh": "refresh456"},
                request=mock_request,
            )

            # Act
            await auth_tools.authenticate(username="test@example.com", password="testpass")

            # Assert
            ctx.set_state.assert_any_call("auth_token", "token123")
            ctx.set_state.assert_any_call("refresh_token", "refresh456")

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_authenticate_has_correct_parameters(self) -> None:
        """
        Verifica que authenticate tiene los parámetros correctos con tipos.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Act
        tool = await mcp.get_tool("taiga_authenticate")

        # Assert
        assert tool is not None
        assert "properties" in tool.parameters
        assert "username" in tool.parameters["properties"]
        assert "password" in tool.parameters["properties"]

        # Check that both parameters allow null (are optional)
        assert "anyOf" in tool.parameters["properties"]["username"]
        assert "anyOf" in tool.parameters["properties"]["password"]

        # Check that string type is allowed
        username_types = [t.get("type") for t in tool.parameters["properties"]["username"]["anyOf"]]
        password_types = [t.get("type") for t in tool.parameters["properties"]["password"]["anyOf"]]
        assert "string" in username_types
        assert "string" in password_types


class TestRefreshTokenTool:
    """Tests para la herramienta de refresh token."""

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_refresh_token_tool_is_registered(self) -> None:
        """
        RF-010: Las herramientas DEBEN cubrir autenticación de Taiga.
        Verifica que la herramienta refresh_token está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)

        # Act
        auth_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_refresh_token" in tool_names

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_refresh_token_with_valid_token(self, mock_taiga_api) -> None:
        """
        Verifica que refresh_token funciona con token válido.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Mock de respuesta exitosa
        mock_taiga_api.post("https://api.taiga.io/api/v1/auth/refresh").mock(
            return_value=httpx.Response(
                200, json={"auth_token": "new_token_789", "refresh": "new_refresh_012"}
            )
        )

        # Act
        result = await auth_tools.refresh_token(refresh_token="old_refresh_456")

        # Assert
        assert result is not None
        assert result["auth_token"] == "new_token_789"
        assert result["refresh"] == "new_refresh_012"

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_refresh_token_with_expired_token(self, mock_taiga_api) -> None:
        """
        Verifica que refresh_token maneja tokens expirados.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Mock de respuesta de error
        mock_taiga_api.post("https://api.taiga.io/api/v1/auth/refresh").mock(
            return_value=httpx.Response(401, json={"detail": "Token has expired"})
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Token has expired"):
            await auth_tools.refresh_token(refresh_token="expired_token")

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_refresh_token_updates_stored_token(self) -> None:
        """
        Verifica que refresh_token actualiza el token almacenado.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        ctx = Mock(spec=Context)
        ctx.set_state = Mock()
        ctx.get_state = Mock(return_value="old_refresh_456")

        with (
            patch.object(auth_tools, "get_context", return_value=ctx),
            patch("httpx.AsyncClient.post") as mock_post,
        ):
            # Create a mock request
            mock_request = httpx.Request("POST", "https://api.taiga.io/api/v1/auth/refresh")
            mock_post.return_value = httpx.Response(
                200,
                json={"auth_token": "new_token", "refresh": "new_refresh"},
                request=mock_request,
            )

            # Act
            await auth_tools.refresh_token()

            # Assert
            ctx.get_state.assert_called_with("refresh_token")
            ctx.set_state.assert_any_call("auth_token", "new_token")
            ctx.set_state.assert_any_call("refresh_token", "new_refresh")


class TestGetCurrentUserTool:
    """Tests para la herramienta get_current_user."""

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_get_current_user_tool_is_registered(self) -> None:
        """
        RF-010: Las herramientas DEBEN cubrir autenticación de Taiga.
        Verifica que la herramienta get_current_user está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)

        # Act
        auth_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_get_current_user" in tool_names

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_token(self, mock_taiga_api) -> None:
        """
        Verifica que get_current_user funciona con token válido.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Mock de respuesta exitosa
        mock_taiga_api.get("https://api.taiga.io/api/v1/users/me").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 12345,
                    "username": "testuser",
                    "email": "test@example.com",
                    "full_name": "Test User",
                    "bio": "Test bio",
                    "lang": "en",
                    "timezone": "UTC",
                    "is_active": True,
                    "roles": ["Product Owner", "Developer"],
                },
            )
        )

        # Act
        result = await auth_tools.get_current_user(auth_token="valid_token")

        # Assert
        assert result is not None
        assert result["id"] == 12345
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        assert result["full_name"] == "Test User"
        assert result["is_active"] is True

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_get_current_user_without_token(self) -> None:
        """
        Verifica que get_current_user requiere token.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Act & Assert
        with pytest.raises(ToolError, match="Not authenticated"):
            await auth_tools.get_current_user(auth_token=None)

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_get_current_user_with_invalid_token(self, mock_taiga_api) -> None:
        """
        Verifica que get_current_user maneja tokens inválidos.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Mock de respuesta de error
        mock_taiga_api.get("https://api.taiga.io/api/v1/users/me").mock(
            return_value=httpx.Response(401, json={"detail": "Invalid authentication token"})
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Authentication"):
            await auth_tools.get_current_user(auth_token="invalid_token")

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_get_current_user_uses_stored_token(self) -> None:
        """
        Verifica que get_current_user usa el token almacenado si no se proporciona.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        ctx = Mock(spec=Context)
        ctx.get_state = Mock(return_value="stored_token_123")

        with (
            patch.object(auth_tools, "get_context", return_value=ctx),
            patch("httpx.AsyncClient.get") as mock_get,
        ):
            # Create a mock request
            mock_request = httpx.Request("GET", "https://api.taiga.io/api/v1/users/me")
            mock_get.return_value = httpx.Response(
                200, json={"id": 12345, "username": "testuser"}, request=mock_request
            )

            # Act
            await auth_tools.get_current_user()

            # Assert
            ctx.get_state.assert_called_with("auth_token")
            mock_get.assert_called_once()
            headers = mock_get.call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer stored_token_123"


class TestAuthToolsBestPractices:
    """Tests para verificar buenas prácticas en herramientas de auth."""

    @pytest.mark.unit
    @pytest.mark.auth
    def test_auth_tools_use_async_await(self) -> None:
        """
        RF-007, RNF-001: Usar async/await para operaciones I/O.
        Verifica que las herramientas de auth son asíncronas.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Act
        import inspect

        # Assert
        assert inspect.iscoroutinefunction(auth_tools.authenticate)
        assert inspect.iscoroutinefunction(auth_tools.refresh_token)
        assert inspect.iscoroutinefunction(auth_tools.get_current_user)

    @pytest.mark.unit
    @pytest.mark.auth
    def test_auth_tools_have_docstrings(self) -> None:
        """
        RNF-006: El código DEBE tener docstrings descriptivos.
        Verifica que las herramientas de auth tienen documentación.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Act & Assert
        assert auth_tools.authenticate.__doc__ is not None
        assert "authenticate" in auth_tools.authenticate.__doc__.lower()

        assert auth_tools.refresh_token.__doc__ is not None
        assert "refresh" in auth_tools.refresh_token.__doc__.lower()

        assert auth_tools.get_current_user.__doc__ is not None
        assert "current user" in auth_tools.get_current_user.__doc__.lower()

    @pytest.mark.unit
    @pytest.mark.auth
    def test_auth_tools_use_type_hints(self) -> None:
        """
        RNF-005: El código DEBE usar type hints completos.
        Verifica que las herramientas de auth tienen type hints.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()  # Need to register tools first

        # Act
        import inspect

        # Assert - authenticate
        sig = inspect.signature(auth_tools.authenticate)
        assert sig.parameters["username"].annotation == str | None
        assert sig.parameters["password"].annotation == str | None
        assert sig.return_annotation != inspect.Signature.empty

        # Assert - refresh_token
        sig = inspect.signature(auth_tools.refresh_token)
        assert "refresh_token" in sig.parameters
        assert sig.return_annotation != inspect.Signature.empty

        # Assert - get_current_user
        sig = inspect.signature(auth_tools.get_current_user)
        assert sig.return_annotation != inspect.Signature.empty

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_auth_tools_handle_errors_properly(self) -> None:
        """
        RF-026: El servidor DEBE implementar manejo de errores con ToolError.
        Verifica que las herramientas manejan errores correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Test varios tipos de errores
        test_cases = [
            (httpx.NetworkError("Network error"), "Network error"),
            (httpx.TimeoutException("Timeout"), "Timeout"),
            (ValueError("Invalid data"), "Invalid data"),
            (Exception("Unknown error"), "Unknown error"),
        ]

        for error, expected_message in test_cases:
            with patch("httpx.AsyncClient.post") as mock_post:
                mock_post.side_effect = error

                # Act & Assert
                with pytest.raises(ToolError) as exc_info:
                    await auth_tools.authenticate("user", "pass")

                assert expected_message in str(exc_info.value)
