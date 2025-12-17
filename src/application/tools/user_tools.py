"""
User management tools for Taiga MCP Server - Application layer.
"""

from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError as MCPError

from src.config import TaigaConfig
from src.domain.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    ResourceNotFoundError,
    TaigaAPIError,
)
from src.infrastructure.pagination import AutoPaginator, PaginationConfig
from src.taiga_client import TaigaAPIClient


class UserTools:
    """
    User management tools for Taiga MCP Server.

    Provides MCP tools for managing users in Taiga.
    """

    def __init__(self, mcp: FastMCP) -> None:
        """
        Initialize user tools.

        Args:
            mcp: FastMCP server instance
        """
        self.mcp = mcp
        self.config = TaigaConfig()
        self.client = None  # For backward compatibility

    def set_client(self, client: Any) -> None:
        """Inject Taiga client for backward compatibility."""
        self.client = client

    def register_tools(self) -> None:
        """Register user tools with the MCP server."""

        # Get user stats
        @self.mcp.tool(
            name="taiga_get_user_stats", description="Get statistics for a specific user"
        )
        async def get_user_stats(auth_token: str, user_id: int) -> dict[str, Any]:
            """
            Get user statistics.

            Esta herramienta obtiene estadísticas detalladas de un usuario específico
            en Taiga, incluyendo proyectos, actividad y roles.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                user_id: ID del usuario del que se quieren obtener las estadísticas

            Returns:
                Dict con los siguientes campos:
                - total_num_projects: Número total de proyectos
                - total_num_closed_userstories: Historias de usuario cerradas
                - total_num_contacts: Número de contactos
                - roles: Lista de roles del usuario
                - created_date: Fecha de creación del usuario
                - projects_with_me: Proyectos compartidos
                - projects_with_most_activity: Proyectos con más actividad
                - total_activity: Estadísticas de actividad total
                - message: Mensaje de confirmación

            Raises:
                MCPError: Si el usuario no existe, no hay permisos, o falla la API

            Example:
                >>> result = await taiga_get_user_stats(
                ...     auth_token="eyJ0eXAiOi...",
                ...     user_id=42
                ... )
                >>> print(result)
                {
                    "total_num_projects": 10,
                    "total_num_closed_userstories": 156,
                    "total_num_contacts": 8,
                    "roles": ["Developer", "Product Owner"],
                    "created_date": "2024-01-15T10:30:00Z",
                    "projects_with_me": {"123": "Project A"},
                    "projects_with_most_activity": [{"id": 1, "name": "Active Project"}],
                    "total_activity": {"total": 500},
                    "message": "Retrieved stats for user 42"
                }
            """
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    stats = await client.get(f"/users/{user_id}/stats")

                    return {
                        "total_num_projects": stats.get("total_num_projects", 0),
                        "total_num_closed_userstories": stats.get(
                            "total_num_closed_userstories", 0
                        ),
                        "total_num_contacts": stats.get("total_num_contacts", 0),
                        "roles": stats.get("roles", []),
                        "created_date": stats.get("created_date"),
                        "projects_with_me": stats.get("projects_with_me", {}),
                        "projects_with_most_activity": stats.get("projects_with_most_activity", []),
                        "total_activity": stats.get("total_activity", {}),
                        "message": f"Retrieved stats for user {user_id}",
                    }

            except ResourceNotFoundError:
                raise MCPError("User not found") from None
            except PermissionDeniedError:
                raise MCPError(f"No permission to access user {user_id} stats") from None
            except AuthenticationError:
                raise MCPError("Authentication failed. Please authenticate first") from None
            except TaigaAPIError as e:
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.get_user_stats = get_user_stats.fn if hasattr(get_user_stats, "fn") else get_user_stats

        # List users (if needed, based on old implementation)
        @self.mcp.tool(name="taiga_list_users", description="List users in a project")
        async def list_users(
            auth_token: str,
            project_id: int | None = None,
            auto_paginate: bool = True,
        ) -> list[dict[str, Any]]:
            """
            List users.

            Esta herramienta lista los usuarios de Taiga, opcionalmente filtrados
            por proyecto. Útil para obtener información de miembros del equipo.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto para filtrar usuarios (opcional).
                    Si se proporciona, solo devuelve usuarios de ese proyecto.
                auto_paginate: Si True (default), obtiene automáticamente todas
                    las páginas de resultados. Si False, retorna solo la primera
                    página (útil para listas grandes donde solo se necesita
                    una muestra).

            Returns:
                Lista de diccionarios con información de usuarios, cada uno conteniendo:
                - id: ID del usuario
                - username: Nombre de usuario
                - full_name: Nombre completo
                - email: Email del usuario
                - photo: URL de la foto de perfil
                - is_active: Si el usuario está activo

            Raises:
                MCPError: Si la autenticación falla o hay error en la API

            Example:
                >>> users = await taiga_list_users(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print(users)
                [
                    {
                        "id": 1,
                        "username": "admin",
                        "full_name": "Admin User",
                        "email": "admin@example.com",
                        "photo": "https://taiga.io/photo.jpg",
                        "is_active": True
                    },
                    {
                        "id": 2,
                        "username": "developer",
                        "full_name": "Dev User",
                        "email": "dev@example.com",
                        "photo": None,
                        "is_active": True
                    }
                ]
            """
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    paginator = AutoPaginator(client, PaginationConfig())
                    params: dict[str, Any] = {}
                    if project_id is not None:
                        params["project"] = project_id  # API expects 'project'

                    if auto_paginate:
                        users = await paginator.paginate("/users", params=params)
                    else:
                        users = await paginator.paginate_first_page("/users", params=params)

                    if isinstance(users, list):
                        return users
                    return []

            except AuthenticationError:
                raise MCPError("Authentication failed. Please authenticate first") from None
            except TaigaAPIError as e:
                raise MCPError(f"Failed to list users: {e!s}") from e
            except Exception as e:
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.list_users = list_users.fn if hasattr(list_users, "fn") else list_users

        # Get user by ID
        @self.mcp.tool(name="taiga_get_user", description="Get a user by their ID")
        async def get_user(auth_token: str, user_id: int) -> dict[str, Any]:
            """
            Get a user by their ID.

            Esta herramienta obtiene los detalles de un usuario específico de Taiga
            por su ID, incluyendo información de perfil y configuración.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                user_id: ID del usuario a obtener

            Returns:
                Dict con información del usuario:
                - id: ID del usuario
                - username: Nombre de usuario
                - full_name: Nombre completo
                - full_name_display: Nombre para mostrar
                - email: Email del usuario
                - bio: Biografía
                - photo: URL de la foto de perfil
                - big_photo: URL de la foto grande
                - is_active: Si el usuario está activo
                - lang: Idioma preferido
                - theme: Tema visual preferido
                - timezone: Zona horaria
                - date_joined: Fecha de registro
                - max_private_projects: Límite de proyectos privados
                - max_public_projects: Límite de proyectos públicos
                - max_memberships_private_projects: Límite de membresías privadas
                - max_memberships_public_projects: Límite de membresías públicas

            Raises:
                MCPError: Si el usuario no existe, no hay permisos, o falla la API

            Example:
                >>> user = await taiga_get_user(
                ...     auth_token="eyJ0eXAiOi...",
                ...     user_id=42
                ... )
                >>> print(user["username"])
                "johndoe"
            """
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    return await client.get(f"/users/{user_id}")

            except ResourceNotFoundError:
                raise MCPError(f"User {user_id} not found") from None
            except PermissionDeniedError:
                raise MCPError(f"No permission to access user {user_id}") from None
            except AuthenticationError:
                raise MCPError("Authentication failed. Please authenticate first") from None
            except TaigaAPIError as e:
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.get_user = get_user.fn if hasattr(get_user, "fn") else get_user

    # Legacy methods for backward compatibility
    def _register_tools(self) -> None:
        """Legacy registration method."""
        self.register_tools()
