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


class TestAuthToolsAdditionalCoverage:
    """Tests for additional coverage of AuthTools."""

    @pytest.fixture
    def mock_taiga_api(self, respx_mock):
        """Fixture para mock de la API de Taiga."""
        return respx_mock

    @pytest.mark.unit
    @pytest.mark.auth
    def test_set_client(self) -> None:
        """Test set_client method."""
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        mock_client = object()
        auth_tools.set_client(mock_client)
        assert auth_tools.client is mock_client

    @pytest.mark.unit
    @pytest.mark.auth
    def test_get_auth_token(self) -> None:
        """Test get_auth_token method."""
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)

        # Initially should be None
        assert auth_tools.get_auth_token() is None

        # After setting
        auth_tools._auth_token = "test_token"
        assert auth_tools.get_auth_token() == "test_token"

    @pytest.mark.unit
    @pytest.mark.auth
    def test_is_authenticated(self) -> None:
        """Test is_authenticated method."""
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)

        # Initially should be False
        assert auth_tools.is_authenticated() is False

        # After setting token
        auth_tools._auth_token = "test_token"
        assert auth_tools.is_authenticated() is True

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_logout_tool(self, mock_taiga_api) -> None:
        """Test logout tool."""
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Set some tokens first
        auth_tools._auth_token = "token123"
        auth_tools._refresh_token = "refresh456"
        auth_tools._user_data = {"username": "testuser"}

        # Call logout
        result = await auth_tools.logout()

        # Assert
        assert result["authenticated"] is False
        assert "logged out" in result["message"].lower()
        assert auth_tools._auth_token is None
        assert auth_tools._refresh_token is None
        assert auth_tools._user_data is None

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_check_auth_tool_authenticated(self, mock_taiga_api) -> None:
        """Test check_auth tool when authenticated."""
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Set authentication state
        auth_tools._auth_token = "token123"
        auth_tools._refresh_token = "refresh456"
        auth_tools._user_data = {"username": "testuser", "id": 42}

        # Call check_auth
        result = await auth_tools.check_auth()

        # Assert
        assert result["authenticated"] is True
        assert result["has_token"] is True
        assert result["has_refresh_token"] is True
        assert result["username"] == "testuser"
        assert result["user_id"] == 42

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_check_auth_tool_not_authenticated(self, mock_taiga_api) -> None:
        """Test check_auth tool when not authenticated."""
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Don't set any authentication state

        # Call check_auth
        result = await auth_tools.check_auth()

        # Assert
        assert result["authenticated"] is False
        assert result["has_token"] is False
        assert result["has_refresh_token"] is False
        assert result["username"] is None
        assert result["user_id"] is None

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_authenticate_missing_credentials(self, mock_taiga_api) -> None:
        """Test authenticate with missing credentials from config."""
        from unittest.mock import patch

        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Mock config to return None for credentials
        with patch.object(auth_tools.config, "taiga_username", None), patch.object(
            auth_tools.config, "taiga_password", None
        ), pytest.raises(ToolError, match="Username and password are required"):
            await auth_tools.authenticate()

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_refresh_token_no_token_available(self, mock_taiga_api) -> None:
        """Test refresh_token when no token is available."""
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Don't set any refresh token

        with pytest.raises(ToolError, match="No refresh token available"):
            await auth_tools.refresh_token()

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_get_current_user_api_error(self, mock_taiga_api) -> None:
        """Test get_current_user with API error."""

        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/users/me").mock(
            return_value=httpx.Response(500, json={"detail": "Server error"})
        )

        with pytest.raises(ToolError, match="API error"):
            await auth_tools.get_current_user(auth_token="valid_token")

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_context_initialization(self, mock_taiga_api) -> None:
        """Test context initialization when mcp doesn't have context."""
        mcp = FastMCP("Test")
        # Remove context if it exists
        if hasattr(mcp, "context"):
            delattr(mcp, "context")

        AuthTools(mcp)
        # Context should be initialized
        assert hasattr(mcp, "context")

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_get_context_initializes_context(self, mock_taiga_api) -> None:
        """Test get_context initializes mcp.context if missing."""
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Remove context
        if hasattr(mcp, "context"):
            delattr(mcp, "context")

        # Call get_context - should initialize context
        ctx = auth_tools.get_context()
        assert hasattr(mcp, "context")
        assert ctx is not None

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_refresh_token_unexpected_error(self, mock_taiga_api) -> None:
        """Test refresh_token with unexpected error."""
        from unittest.mock import AsyncMock, patch

        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Set refresh token
        auth_tools._refresh_token = "refresh_token"

        # Mock to raise unexpected error
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.refresh_auth_token = AsyncMock(
            side_effect=RuntimeError("Unexpected error")
        )

        with patch(
            "src.application.tools.auth_tools.TaigaAPIClient", return_value=mock_client
        ), pytest.raises(ToolError, match="Unexpected error"):
            await auth_tools.refresh_token()

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_logout_tool_via_mcp(self, mock_taiga_api) -> None:
        """Test logout tool via MCP."""
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        tools = await mcp.get_tools()
        logout_tool = tools.get("taiga_logout")
        assert logout_tool is not None

        result = await logout_tool.fn()
        assert result["authenticated"] is False

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_check_auth_tool_via_mcp(self, mock_taiga_api) -> None:
        """Test check_auth tool via MCP."""
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        tools = await mcp.get_tools()
        check_auth_tool = tools.get("taiga_check_auth")
        assert check_auth_tool is not None

        result = await check_auth_tool.fn()
        assert "authenticated" in result

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_direct_authenticate_with_client(self, mock_taiga_api) -> None:
        """Test direct authenticate method with mock client."""
        from unittest.mock import AsyncMock

        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)

        # Create mock client
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock(
            return_value={"auth_token": "token", "refresh_token": "refresh"}
        )
        auth_tools.set_client(mock_client)

        result = await auth_tools.authenticate("user", "pass")

        assert result["auth_token"] == "token"
        mock_client.authenticate.assert_called_once_with("user", "pass")

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_direct_authenticate_production_path(self, mock_taiga_api) -> None:
        """Test direct authenticate method using TaigaAPIClient (production path)."""
        from unittest.mock import AsyncMock, patch

        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        # Don't set client, so it uses production path

        # Mock TaigaAPIClient
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.authenticate = AsyncMock(
            return_value={
                "auth_token": "production_token",
                "refresh_token": "production_refresh",
                "username": "testuser",
            }
        )

        with patch(
            "src.application.tools.auth_tools.TaigaAPIClient", return_value=mock_client
        ):
            result = await auth_tools.authenticate("user", "pass")

        assert result["auth_token"] == "production_token"
        assert auth_tools._auth_token == "production_token"
        assert auth_tools._refresh_token == "production_refresh"
        assert mcp.context.get("auth_token") == "production_token"

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_direct_authenticate_missing_credentials_direct(self) -> None:
        """Test direct authenticate method with missing credentials (direct call)."""
        from unittest.mock import patch

        from fastmcp.exceptions import ToolError as MCPError

        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)

        # Mock config to return None for credentials
        with patch.object(auth_tools.config, "taiga_username", None), patch.object(
            auth_tools.config, "taiga_password", None
        ), pytest.raises(MCPError, match="Username and password are required"):
            await auth_tools.authenticate()

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_direct_authenticate_production_error(self, mock_taiga_api) -> None:
        """Test direct authenticate method with error in production path."""
        from unittest.mock import AsyncMock, patch

        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)

        # Mock TaigaAPIClient that raises an error
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.authenticate = AsyncMock(side_effect=ValueError("Connection failed"))

        with patch(
            "src.application.tools.auth_tools.TaigaAPIClient", return_value=mock_client
        ), pytest.raises(ValueError, match="Connection failed"):
            await auth_tools.authenticate("user", "pass")

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_logout_clears_context(self, mock_taiga_api) -> None:
        """Test logout tool clears context with auth tokens."""
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Set tokens in context
        mcp.context["auth_token"] = "token_to_clear"
        mcp.context["refresh_token"] = "refresh_to_clear"
        mcp.context["user_data"] = {"username": "testuser"}

        # Set instance tokens
        auth_tools._auth_token = "token123"
        auth_tools._refresh_token = "refresh456"
        auth_tools._user_data = {"username": "testuser"}

        # Call logout
        await auth_tools.logout()

        # Assert context is cleared
        assert mcp.context.get("auth_token") is None
        assert mcp.context.get("refresh_token") is None
        assert mcp.context.get("user_data") is None

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_logout_exception(self, mock_taiga_api) -> None:
        """Test logout tool with exception during execution."""
        from unittest.mock import patch

        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Mock mcp.context to raise an error when pop is called
        class BadContext(dict):
            def pop(self, key, default=None):
                raise RuntimeError("Context error")

        with patch.object(mcp, "context", BadContext()), pytest.raises(
            ToolError, match="Logout failed"
        ):
            await auth_tools.logout()

    @pytest.mark.unit
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_check_auth_exception(self, mock_taiga_api) -> None:
        """Test check_auth tool with exception during execution."""

        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Create a patched check_auth that raises an exception
        original_check_auth = auth_tools.check_auth

        async def raising_check_auth():
            raise RuntimeError("Token error")

        auth_tools.check_auth = raising_check_auth

        # The check_auth method itself raises, but we need to trigger the exception handling
        # inside the actual check_auth tool. Let's reset and patch _user_data.get instead
        auth_tools.check_auth = original_check_auth
        auth_tools._auth_token = "token"
        auth_tools._user_data = None  # This will cause an error when .get is called if we force it

        # To trigger line 489-491, we need the try block to raise an exception
        # Let's mock _user_data to raise on access
        class RaisingDict:
            def get(self, key):
                raise RuntimeError("Token error")

        auth_tools._user_data = RaisingDict()

        with pytest.raises(ToolError, match="Authentication check failed"):
            await auth_tools.check_auth()

    @pytest.mark.unit
    @pytest.mark.auth
    def test_function_reference_fallbacks(self) -> None:
        """Test that tool functions are stored correctly with fallbacks."""
        mcp = FastMCP("Test")
        auth_tools = AuthTools(mcp)
        auth_tools.register_tools()

        # Verify all tool methods are accessible
        assert callable(auth_tools.authenticate)
        assert callable(auth_tools.refresh_token)
        assert callable(auth_tools.get_current_user)
        assert callable(auth_tools.logout)
        assert callable(auth_tools.check_auth)

        # Verify they are async functions
        import inspect
        assert inspect.iscoroutinefunction(auth_tools.authenticate)
        assert inspect.iscoroutinefunction(auth_tools.refresh_token)
        assert inspect.iscoroutinefunction(auth_tools.get_current_user)
        assert inspect.iscoroutinefunction(auth_tools.logout)
        assert inspect.iscoroutinefunction(auth_tools.check_auth)
