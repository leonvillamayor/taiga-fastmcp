"""
Authentication tools for Taiga MCP Server - Application layer.
"""

from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError as MCPError

from src.config import TaigaConfig
from src.domain.exceptions import AuthenticationError, TaigaAPIError
from src.infrastructure.logging import get_logger
from src.taiga_client import TaigaAPIClient


class AuthTools:
    """
    Authentication tools for Taiga MCP Server.

    Provides MCP tools for authenticating with Taiga API.
    """

    def __init__(self, mcp: FastMCP) -> None:
        """
        Initialize authentication tools.

        Args:
            mcp: FastMCP server instance
        """
        self.mcp = mcp
        self.config = TaigaConfig()
        self._auth_token: str | None = None
        self._refresh_token: str | None = None
        self._user_data: dict[str, Any] | None = None
        self._logger = get_logger("auth_tools")

        # Initialize context for storing auth state
        if not hasattr(self.mcp, "context"):
            self.mcp.context = {}

        # Initialize client if provided (for testing)
        self.client = None

    def set_client(self, client: Any) -> None:
        """Set the Taiga API client (for testing purposes)."""
        self.client = client

    async def authenticate(
        self, username: str | None = None, password: str | None = None
    ) -> dict[str, Any]:
        """Direct authenticate method for integration tests."""
        # Use provided credentials or fall back to config
        final_username = username or self.config.taiga_username
        final_password = password or self.config.taiga_password

        self._logger.debug(f"[authenticate] Starting | user={final_username}")

        if not final_username or not final_password:
            self._logger.error("[authenticate] Missing credentials")
            raise MCPError("Username and password are required for authentication")

        # Check if we have a mock client (for testing)
        if hasattr(self, "client") and self.client:
            return await self.client.authenticate(final_username, final_password)

        # Production path - use TaigaAPIClient (imported at top of module)
        try:
            async with TaigaAPIClient(self.config) as client:
                result = await client.authenticate(final_username, final_password)
                # Store tokens for reuse
                self._auth_token = result.get("auth_token")
                self._refresh_token = result.get("refresh_token")
                self._user_data = result
                # Store in context for other tools
                self.mcp.context["auth_token"] = self._auth_token
                self.mcp.context["user_data"] = self._user_data
                self._logger.info(f"[authenticate] Success | user={final_username}")
                return result
        except Exception as e:
            self._logger.error(f"[authenticate] Failed | user={final_username}, error={e!s}")
            raise

    def register_tools(self) -> None:
        """Register authentication tools with the MCP server."""

        @self.mcp.tool(
            name="taiga_authenticate",
            description="Authenticate with Taiga using username and password",
        )
        async def authenticate(
            username: str | None = None, password: str | None = None
        ) -> dict[str, Any]:
            """
            Authenticate with Taiga API.

            Esta herramienta permite autenticarse con Taiga para obtener un token
            de autenticación que se utiliza en todas las demás operaciones.

            Args:
                username: Taiga username (email). If not provided, uses TAIGA_USERNAME from config
                password: Taiga password. If not provided, uses TAIGA_PASSWORD from config

            Returns:
                Dict con los siguientes campos:
                - auth_token: Token de autenticación para usar en otras herramientas
                - refresh: Token de refresco para renovar la autenticación
                - username: Nombre de usuario autenticado
                - id: ID del usuario
                - email: Email del usuario
                - full_name: Nombre completo del usuario
                - authenticated: True si la autenticación fue exitosa
                - message: Mensaje de confirmación

            Raises:
                MCPError: Si la autenticación falla (credenciales inválidas, error de red)

            Example:
                >>> result = await taiga_authenticate(
                ...     username="user@example.com",
                ...     password="securepassword123"
                ... )
                >>> print(result)
                {
                    "auth_token": "eyJ0eXAiOi...",
                    "refresh": "eyJ0eXAiOi...",
                    "username": "myuser",
                    "id": 42,
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "authenticated": True,
                    "message": "Successfully authenticated as myuser"
                }
            """
            try:
                # Use provided credentials or fall back to config
                final_username = username or self.config.taiga_username
                final_password = password or self.config.taiga_password

                self._logger.debug(f"[taiga_authenticate] Starting | user={final_username}")

                if not final_username or not final_password:
                    self._logger.error("[taiga_authenticate] Missing credentials")
                    raise MCPError(
                        "Username and password are required. "
                        "Provide them as parameters or set TAIGA_USERNAME "
                        "and TAIGA_PASSWORD environment variables."
                    )

                async with TaigaAPIClient(self.config) as client:
                    result = await client.authenticate(final_username, final_password)

                    # Store tokens for future use
                    self._auth_token = result.get("auth_token")
                    self._refresh_token = result.get("refresh")
                    self._user_data = {
                        "id": result.get("id"),
                        "username": result.get("username"),
                        "email": result.get("email"),
                        "full_name": result.get("full_name"),
                    }

                    # Store in MCP context using context wrapper
                    ctx = self.get_context()
                    ctx.set_state("auth_token", self._auth_token)
                    ctx.set_state("refresh_token", self._refresh_token)
                    ctx.set_state("user_data", self._user_data)

                    self._logger.info(
                        f"[taiga_authenticate] Success | user={result.get('username')}, id={result.get('id')}"
                    )
                    return {
                        "auth_token": self._auth_token,
                        "refresh": self._refresh_token,
                        "username": result.get("username"),
                        "id": result.get("id"),
                        "email": result.get("email"),
                        "full_name": result.get("full_name"),
                        "authenticated": True,
                        "message": f"Successfully authenticated as {result.get('username')}",
                    }

            except AuthenticationError as e:
                self._logger.error(f"[taiga_authenticate] Auth failed | error={e!s}")
                raise MCPError(f"Invalid username or password: {e!s}") from e
            except Exception as e:
                # Check for network errors
                if "Network" in str(e.__class__.__name__) or "Connection" in str(e):
                    self._logger.error(f"[taiga_authenticate] Network error | error={e!s}")
                    raise MCPError(f"Network error: {e!s}") from e
                self._logger.error(f"[taiga_authenticate] Unexpected error | error={e!s}")
                raise MCPError(f"Unexpected error during authentication: {e!s}") from e

        # Store reference for direct test access - get the actual function
        # Check if it's wrapped by the decorator and extract the inner function
        if hasattr(authenticate, "__wrapped__"):
            self.authenticate = authenticate.__wrapped__
        elif hasattr(authenticate, "fn"):
            self.authenticate = authenticate.fn
        else:
            self.authenticate = authenticate

        @self.mcp.tool(name="taiga_refresh_token", description="Refresh the authentication token")
        async def refresh_token(refresh_token: str | None = None) -> dict[str, Any]:
            """
            Refresh authentication token.

            Esta herramienta renueva el token de autenticación usando el refresh token,
            permitiendo mantener la sesión activa sin necesidad de volver a autenticarse.

            Args:
                refresh_token: Token de refresco para renovar. Si no se proporciona,
                    usa el token almacenado de la autenticación anterior.

            Returns:
                Dict con los siguientes campos:
                - auth_token: Nuevo token de autenticación
                - refresh: Nuevo token de refresco
                - authenticated: True si el refresh fue exitoso
                - message: Mensaje de confirmación

            Raises:
                MCPError: Si el refresh falla (token expirado, inválido o no disponible)

            Example:
                >>> result = await taiga_refresh_token(
                ...     refresh_token="eyJ0eXAiOi..."
                ... )
                >>> print(result)
                {
                    "auth_token": "eyJ0eXAiOi...",
                    "refresh": "eyJ0eXAiOi...",
                    "authenticated": True,
                    "message": "Successfully refreshed authentication token"
                }
            """
            try:
                self._logger.debug("[taiga_refresh_token] Starting")
                # Try to get refresh token from context if not provided
                if not refresh_token:
                    ctx = self.get_context()
                    refresh_token = ctx.get_state("refresh_token")

                token_to_use = refresh_token or self._refresh_token
                if not token_to_use:
                    self._logger.error("[taiga_refresh_token] No refresh token available")
                    raise MCPError("No refresh token available. Please authenticate first")

                async with TaigaAPIClient(self.config) as client:
                    # Set the current tokens
                    client.refresh_token = token_to_use

                    result = await client.refresh_auth_token()

                    # Update stored tokens
                    self._auth_token = result.get("auth_token")
                    self._refresh_token = result.get("refresh")

                    # Update MCP context using context wrapper
                    ctx = self.get_context()
                    ctx.set_state("auth_token", self._auth_token)
                    ctx.set_state("refresh_token", self._refresh_token)

                    self._logger.info("[taiga_refresh_token] Success | token refreshed")
                    return {
                        "auth_token": self._auth_token,
                        "refresh": self._refresh_token,
                        "authenticated": True,
                        "message": "Successfully refreshed authentication token",
                    }

            except AuthenticationError as e:
                self._logger.error(f"[taiga_refresh_token] Failed | error={e!s}")
                raise MCPError(f"Token refresh failed: {e!s}") from e
            except Exception as e:
                self._logger.error(f"[taiga_refresh_token] Unexpected error | error={e!s}")
                raise MCPError(f"Unexpected error during token refresh: {e!s}") from e

        # Store reference for direct test access - get the actual function
        if hasattr(refresh_token, "__wrapped__"):
            self.refresh_token = refresh_token.__wrapped__
        elif hasattr(refresh_token, "fn"):
            self.refresh_token = refresh_token.fn
        else:
            self.refresh_token = refresh_token

        @self.mcp.tool(
            name="taiga_get_current_user",
            description="Get information about the currently authenticated user",
        )
        async def get_current_user(auth_token: str | None = None) -> dict[str, Any]:
            """
            Get current user information.

            Esta herramienta obtiene la información del usuario actualmente autenticado
            en Taiga, incluyendo su perfil, roles y estadísticas de proyectos.

            Args:
                auth_token: Token de autenticación. Si no se proporciona,
                    usa el token almacenado de la autenticación anterior.

            Returns:
                Dict con los siguientes campos:
                - id: ID del usuario
                - username: Nombre de usuario
                - email: Email del usuario
                - full_name: Nombre completo
                - bio: Biografía del usuario
                - lang: Idioma preferido
                - timezone: Zona horaria
                - is_active: Si el usuario está activo
                - roles: Lista de roles del usuario
                - total_private_projects: Número de proyectos privados
                - total_public_projects: Número de proyectos públicos

            Raises:
                MCPError: Si no está autenticado o la solicitud falla

            Example:
                >>> result = await taiga_get_current_user(auth_token="eyJ0eXAiOi...")
                >>> print(result)
                {
                    "id": 42,
                    "username": "myuser",
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "bio": "Software developer",
                    "lang": "en",
                    "timezone": "UTC",
                    "is_active": True,
                    "roles": ["Developer", "Admin"],
                    "total_private_projects": 5,
                    "total_public_projects": 2
                }
            """
            try:
                self._logger.debug("[taiga_get_current_user] Starting")
                # Use provided token or fall back to stored token or context
                token = auth_token or self._auth_token

                if not token:
                    # Try to get from context
                    ctx = self.get_context()
                    token = ctx.get_state("auth_token")

                if not token:
                    self._logger.error("[taiga_get_current_user] No auth token available")
                    raise MCPError("Not authenticated. Please authenticate first")

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = token
                    result = await client.get("/users/me")

                    self._logger.info(
                        f"[taiga_get_current_user] Success | user={result.get('username')}, id={result.get('id')}"
                    )
                    return {
                        "id": result.get("id"),
                        "username": result.get("username"),
                        "email": result.get("email"),
                        "full_name": result.get("full_name"),
                        "bio": result.get("bio"),
                        "lang": result.get("lang"),
                        "timezone": result.get("timezone"),
                        "is_active": result.get("is_active"),
                        "roles": result.get("roles", []),
                        "total_private_projects": result.get("total_private_projects"),
                        "total_public_projects": result.get("total_public_projects"),
                    }

            except AuthenticationError as e:
                self._logger.error(f"[taiga_get_current_user] Auth error | error={e!s}")
                raise MCPError(f"Authentication error: {e!s}") from e
            except TaigaAPIError as e:
                self._logger.error(f"[taiga_get_current_user] API error | error={e!s}")
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(f"[taiga_get_current_user] Unexpected error | error={e!s}")
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access - get the actual function
        if hasattr(get_current_user, "__wrapped__"):
            self.get_current_user = get_current_user.__wrapped__
        elif hasattr(get_current_user, "fn"):
            self.get_current_user = get_current_user.fn
        else:
            self.get_current_user = get_current_user

        @self.mcp.tool(name="taiga_logout", description="Clear authentication tokens and logout")
        async def logout() -> dict[str, Any]:
            """
            Clear authentication tokens.

            Esta herramienta cierra la sesión del usuario eliminando todos los tokens
            de autenticación almacenados. Después de llamar a esta herramienta,
            será necesario volver a autenticarse para realizar operaciones.

            Args:
                No requiere argumentos. La operación afecta a la sesión actual.

            Returns:
                Dict con los siguientes campos:
                - authenticated: False indicando que la sesión está cerrada
                - message: Mensaje de confirmación

            Raises:
                MCPError: Si el logout falla por algún error interno

            Example:
                >>> result = await taiga_logout()
                >>> print(result)
                {
                    "authenticated": False,
                    "message": "Successfully logged out"
                }
            """
            try:
                self._logger.debug("[taiga_logout] Starting")
                # Clear stored tokens
                self._auth_token = None
                self._refresh_token = None
                self._user_data = None

                # Clear MCP context
                if hasattr(self.mcp, "context"):
                    self.mcp.context.pop("auth_token", None)
                    self.mcp.context.pop("refresh_token", None)
                    self.mcp.context.pop("user_data", None)

                self._logger.info("[taiga_logout] Success | session cleared")
                return {"authenticated": False, "message": "Successfully logged out"}

            except Exception as e:
                self._logger.error(f"[taiga_logout] Failed | error={e!s}")
                raise MCPError(f"Logout failed: {e!s}") from e

        # Store reference for direct test access - get the actual function
        if hasattr(logout, "__wrapped__"):
            self.logout = logout.__wrapped__
        elif hasattr(logout, "fn"):
            self.logout = logout.fn
        else:
            self.logout = logout

        @self.mcp.tool(name="taiga_check_auth", description="Check current authentication status")
        async def check_auth() -> dict[str, Any]:
            """
            Check authentication status.

            Esta herramienta verifica si hay una sesión de autenticación activa,
            mostrando información sobre el estado de los tokens almacenados.

            Args:
                No requiere argumentos. Verifica el estado de la sesión actual.

            Returns:
                Dict con los siguientes campos:
                - authenticated: True si hay una sesión activa
                - has_token: True si hay un token de autenticación almacenado
                - has_refresh_token: True si hay un token de refresco almacenado
                - username: Nombre del usuario autenticado (o None)
                - user_id: ID del usuario autenticado (o None)

            Raises:
                MCPError: Si la verificación falla por algún error interno

            Example:
                >>> result = await taiga_check_auth()
                >>> print(result)
                {
                    "authenticated": True,
                    "has_token": True,
                    "has_refresh_token": True,
                    "username": "myuser",
                    "user_id": 42
                }
            """
            try:
                self._logger.debug("[taiga_check_auth] Starting")
                is_authenticated = bool(self._auth_token)
                self._logger.info(f"[taiga_check_auth] Success | authenticated={is_authenticated}")
                return {
                    "authenticated": is_authenticated,
                    "has_token": bool(self._auth_token),
                    "has_refresh_token": bool(self._refresh_token),
                    "username": self._user_data.get("username") if self._user_data else None,
                    "user_id": self._user_data.get("id") if self._user_data else None,
                }

            except Exception as e:
                self._logger.error(f"[taiga_check_auth] Failed | error={e!s}")
                raise MCPError(f"Authentication check failed: {e!s}") from e

        # Store reference for direct test access - get the actual function
        if hasattr(check_auth, "__wrapped__"):
            self.check_auth = check_auth.__wrapped__
        elif hasattr(check_auth, "fn"):
            self.check_auth = check_auth.fn
        else:
            self.check_auth = check_auth

    def get_context(self) -> Any:
        """Get context for storing auth state."""

        # Return a context-like object that wraps mcp.context
        class ContextWrapper:
            def __init__(self, mcp_context):
                self.context = mcp_context

            def set_state(self, key, value) -> Any:
                """Set state in context."""
                self.context[key] = value

            def get_state(self, key, default=None) -> Any:
                """Get state from context."""
                return self.context.get(key, default)

        if not hasattr(self.mcp, "context"):
            self.mcp.context = {}

        return ContextWrapper(self.mcp.context)

    def get_auth_token(self) -> str | None:
        """Get the current authentication token.

        Returns:
            The current auth token or None if not authenticated
        """
        return self._auth_token

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self._auth_token is not None
