"""
Membership management tools for Taiga MCP Server - Application layer.
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
    ValidationError,
)
from src.domain.validators import (
    MembershipCreateValidator,
    MembershipUpdateValidator,
    validate_input,
)
from src.infrastructure.logging import get_logger
from src.infrastructure.pagination import AutoPaginator, PaginationConfig
from src.taiga_client import TaigaAPIClient


class MembershipTools:
    """
    Membership management tools for Taiga MCP Server.

    Provides MCP tools for managing project memberships in Taiga.
    """

    def __init__(self, mcp: FastMCP) -> None:
        """
        Initialize membership tools.

        Args:
            mcp: FastMCP server instance
        """
        self.mcp = mcp
        self.config = TaigaConfig()
        self.client = None  # For backward compatibility
        self._logger = get_logger("membership_tools")

    def set_client(self, client: Any) -> None:
        """Inject Taiga client for backward compatibility."""
        self.client = client

    def register_tools(self) -> None:
        """Register membership tools with the MCP server."""

        # List memberships
        @self.mcp.tool(
            name="taiga_list_memberships",
            annotations={"readOnlyHint": True},
            description="List project memberships",
        )
        async def list_memberships(
            auth_token: str,
            project_id: int,
            auto_paginate: bool = True,
        ) -> list[dict[str, Any]]:
            """
            List memberships for a project.

            Esta herramienta lista todos los miembros de un proyecto en Taiga,
            incluyendo sus roles, permisos y estado de administrador.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto del que se quieren listar los miembros
                auto_paginate: Si True (default), obtiene automáticamente todas
                    las páginas de resultados. Si False, retorna solo la primera
                    página (útil para listas grandes donde solo se necesita
                    una muestra).

            Returns:
                Lista de diccionarios con información de membresías, cada uno conteniendo:
                - id: ID de la membresía
                - user: ID del usuario
                - role: ID del rol asignado
                - project: ID del proyecto
                - created_at: Fecha de creación
                - is_admin: Si es administrador del proyecto
                - is_owner: Si es propietario del proyecto
                - color: Color asignado al miembro
                - photo: URL de la foto de perfil

            Raises:
                MCPError: Si la autenticación falla o hay error en la API

            Example:
                >>> memberships = await taiga_list_memberships(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print(memberships)
                [
                    {
                        "id": 1,
                        "user": 42,
                        "role": 5,
                        "project": 123,
                        "created_at": "2024-01-15T10:30:00Z",
                        "is_admin": True,
                        "is_owner": True,
                        "color": "#FC8EAC",
                        "photo": "https://taiga.io/photo.jpg"
                    }
                ]
            """
            self._logger.debug(f"[list_memberships] Starting | project_id={project_id}")
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    paginator = AutoPaginator(client, PaginationConfig())
                    params = {"project": project_id}

                    if auto_paginate:
                        memberships = await paginator.paginate("/memberships", params=params)
                    else:
                        memberships = await paginator.paginate_first_page(
                            "/memberships", params=params
                        )

                    if isinstance(memberships, list):
                        result = [
                            {
                                "id": m.get("id"),
                                "user": m.get("user"),
                                "role": m.get("role"),
                                "project": m.get("project"),
                                "created_at": m.get("created_at"),
                                "is_admin": m.get("is_admin", False),
                                "is_owner": m.get("is_owner", False),
                                "color": m.get("color"),
                                "photo": m.get("photo"),
                            }
                            for m in memberships
                        ]
                        self._logger.info(
                            f"[list_memberships] Success | project_id={project_id}, count={len(result)}"
                        )
                        return result
                    self._logger.info(
                        f"[list_memberships] Success | project_id={project_id}, count=0"
                    )
                    return []

            except AuthenticationError:
                self._logger.error(
                    f"[list_memberships] Authentication failed | project_id={project_id}"
                )
                raise MCPError("Authentication failed. Please authenticate first") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[list_memberships] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Failed to list memberships: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[list_memberships] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.list_memberships = (
            list_memberships.fn if hasattr(list_memberships, "fn") else list_memberships
        )

        # Create membership
        @self.mcp.tool(name="taiga_create_membership", description="Add a member to a project")
        async def create_membership(
            auth_token: str,
            project_id: int,
            role: int,
            username: str | None = None,
            email: str | None = None,
        ) -> dict[str, Any]:
            """
            Create a new project membership.

            Esta herramienta agrega un nuevo miembro a un proyecto en Taiga,
            asignándole un rol específico. Se puede identificar al usuario
            por su nombre de usuario o email.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto al que agregar el miembro
                role: ID del rol a asignar al nuevo miembro
                username: Nombre de usuario a agregar (opcional si se proporciona email)
                email: Email del usuario a agregar (opcional si se proporciona username)

            Returns:
                Dict con los siguientes campos:
                - id: ID de la membresía creada
                - user: ID del usuario agregado
                - role: ID del rol asignado
                - project: ID del proyecto
                - is_admin: Si es administrador del proyecto
                - message: Mensaje de confirmación

            Raises:
                MCPError: Si no hay permisos, el usuario ya es miembro, o falla la API

            Example:
                >>> membership = await taiga_create_membership(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     role=5,
                ...     email="newmember@example.com"
                ... )
                >>> print(membership)
                {
                    "id": 456,
                    "user": 78,
                    "role": 5,
                    "project": 123,
                    "is_admin": False,
                    "message": "Successfully added newmember@example.com to project"
                }
            """
            user_identifier = email or username
            self._logger.debug(
                f"[create_membership] Starting | project_id={project_id}, role={role}, user={user_identifier}"
            )
            try:
                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {
                    "project_id": project_id,
                    "role": role,
                    "username": username,
                    "email": email,
                }
                validate_input(MembershipCreateValidator, validation_data)

                if not username and not email:
                    raise MCPError("Either username or email is required")

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token

                    membership_data: dict[str, Any] = {
                        "project": project_id,
                        "role": role,
                    }  # API expects 'project'

                    # Prefer email over username if both provided
                    if email:
                        membership_data["username"] = email
                    elif username:
                        membership_data["username"] = username

                    membership = await client.post("/memberships", data=membership_data)

                    result = {
                        "id": membership.get("id"),
                        "user": membership.get("user"),
                        "role": membership.get("role"),
                        "project": membership.get("project"),
                        "is_admin": membership.get("is_admin", False),
                        "message": f"Successfully added {email or username} to project",
                    }
                    self._logger.info(
                        f"[create_membership] Success | project_id={project_id}, membership_id={result.get('id')}"
                    )
                    return result

            except ValidationError as e:
                self._logger.warning(
                    f"[create_membership] Validation error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(str(e)) from e
            except PermissionDeniedError:
                self._logger.error(
                    f"[create_membership] Permission denied | project_id={project_id}"
                )
                raise MCPError("No permission to add members to this project") from None
            except AuthenticationError:
                self._logger.error(
                    f"[create_membership] Authentication failed | project_id={project_id}"
                )
                raise MCPError("Authentication failed. Please authenticate first") from None
            except TaigaAPIError as e:
                if "already" in str(e).lower() and "member" in str(e).lower():
                    self._logger.error(
                        f"[create_membership] User already member | project_id={project_id}, user={user_identifier}"
                    )
                    raise MCPError(f"User {username} is already a member of the project") from e
                self._logger.error(
                    f"[create_membership] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Failed to create membership: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[create_membership] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.create_membership = (
            create_membership.fn if hasattr(create_membership, "fn") else create_membership
        )

        # Get membership
        @self.mcp.tool(
            name="taiga_get_membership",
            annotations={"readOnlyHint": True},
            description="Get membership details",
        )
        async def get_membership(auth_token: str, membership_id: int) -> dict[str, Any]:
            """
            Get membership details.

            Esta herramienta obtiene los detalles de una membresía específica
            en un proyecto de Taiga.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                membership_id: ID de la membresía a consultar

            Returns:
                Dict con los siguientes campos:
                - id: ID de la membresía
                - user: ID del usuario
                - role: ID del rol asignado
                - project: ID del proyecto
                - created_at: Fecha de creación
                - is_admin: Si es administrador del proyecto
                - is_owner: Si es propietario del proyecto
                - color: Color asignado al miembro
                - photo: URL de la foto de perfil
                - user_order: Orden del usuario en la lista

            Raises:
                MCPError: Si la membresía no existe o falla la API

            Example:
                >>> membership = await taiga_get_membership(
                ...     auth_token="eyJ0eXAiOi...",
                ...     membership_id=456
                ... )
                >>> print(membership)
                {
                    "id": 456,
                    "user": 78,
                    "role": 5,
                    "project": 123,
                    "created_at": "2024-01-15T10:30:00Z",
                    "is_admin": False,
                    "is_owner": False,
                    "color": "#FC8EAC",
                    "photo": "https://taiga.io/photo.jpg",
                    "user_order": 2
                }
            """
            self._logger.debug(f"[get_membership] Starting | membership_id={membership_id}")
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    membership = await client.get(f"/memberships/{membership_id}")

                    result = {
                        "id": membership.get("id"),
                        "user": membership.get("user"),
                        "role": membership.get("role"),
                        "project": membership.get("project"),
                        "created_at": membership.get("created_at"),
                        "is_admin": membership.get("is_admin", False),
                        "is_owner": membership.get("is_owner", False),
                        "color": membership.get("color"),
                        "photo": membership.get("photo"),
                        "user_order": membership.get("user_order"),
                    }
                    self._logger.info(f"[get_membership] Success | membership_id={membership_id}")
                    return result

            except ResourceNotFoundError:
                self._logger.error(f"[get_membership] Not found | membership_id={membership_id}")
                raise MCPError("Membership not found") from None
            except AuthenticationError:
                self._logger.error(
                    f"[get_membership] Authentication failed | membership_id={membership_id}"
                )
                raise MCPError("Authentication failed. Please authenticate first") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[get_membership] API error | membership_id={membership_id}, error={e!s}"
                )
                raise MCPError(f"Failed to get membership: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[get_membership] Unexpected error | membership_id={membership_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.get_membership = get_membership.fn if hasattr(get_membership, "fn") else get_membership

        # Update membership
        @self.mcp.tool(
            name="taiga_update_membership",
            annotations={"idempotentHint": True},
            description="Update membership role",
        )
        async def update_membership(
            auth_token: str,
            membership_id: int,
            role: int | None = None,
            is_admin: bool | None = None,
        ) -> dict[str, Any]:
            """
            Update membership (e.g., change role or admin status).

            Esta herramienta permite actualizar una membresía existente,
            modificando el rol asignado o el estado de administrador.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                membership_id: ID de la membresía a actualizar
                role: Nuevo ID de rol a asignar (opcional)
                is_admin: Nuevo estado de administrador (opcional)

            Returns:
                Dict con los siguientes campos:
                - id: ID de la membresía
                - user: ID del usuario
                - role: ID del rol actual
                - project: ID del proyecto
                - is_admin: Estado de administrador actual
                - message: Mensaje de confirmación

            Raises:
                MCPError: Si no hay permisos, la membresía no existe, o falla la API

            Example:
                >>> membership = await taiga_update_membership(
                ...     auth_token="eyJ0eXAiOi...",
                ...     membership_id=456,
                ...     role=6,
                ...     is_admin=True
                ... )
                >>> print(membership)
                {
                    "id": 456,
                    "user": 78,
                    "role": 6,
                    "project": 123,
                    "is_admin": True,
                    "message": "Successfully updated membership 456"
                }
            """
            self._logger.debug(
                f"[update_membership] Starting | membership_id={membership_id}, role={role}, is_admin={is_admin}"
            )
            try:
                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {
                    "membership_id": membership_id,
                    "role": role,
                    "is_admin": is_admin,
                }
                validate_input(MembershipUpdateValidator, validation_data)

                update_data = {}
                if role is not None:
                    update_data["role"] = role
                if is_admin is not None:
                    update_data["is_admin"] = is_admin

                if not update_data:
                    raise MCPError("No update data provided")

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    membership = await client.patch(
                        f"/memberships/{membership_id}", data=update_data
                    )

                    result = {
                        "id": membership.get("id"),
                        "user": membership.get("user"),
                        "role": membership.get("role"),
                        "project": membership.get("project"),
                        "is_admin": membership.get("is_admin", False),
                        "message": f"Successfully updated membership {membership_id}",
                    }
                    self._logger.info(
                        f"[update_membership] Success | membership_id={membership_id}"
                    )
                    return result

            except ValidationError as e:
                self._logger.warning(
                    f"[update_membership] Validation error | membership_id={membership_id}, error={e!s}"
                )
                raise MCPError(str(e)) from e
            except ResourceNotFoundError:
                self._logger.error(f"[update_membership] Not found | membership_id={membership_id}")
                raise MCPError("Membership not found") from None
            except PermissionDeniedError:
                self._logger.error(
                    f"[update_membership] Permission denied | membership_id={membership_id}"
                )
                raise MCPError("No permission to update this membership") from None
            except AuthenticationError:
                self._logger.error(
                    f"[update_membership] Authentication failed | membership_id={membership_id}"
                )
                raise MCPError("Authentication failed. Please authenticate first") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[update_membership] API error | membership_id={membership_id}, error={e!s}"
                )
                raise MCPError(f"Failed to update membership: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[update_membership] Unexpected error | membership_id={membership_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.update_membership = (
            update_membership.fn if hasattr(update_membership, "fn") else update_membership
        )

        # Delete membership
        @self.mcp.tool(
            name="taiga_delete_membership",
            annotations={"destructiveHint": True},
            description="Remove a member from project",
        )
        async def delete_membership(auth_token: str, membership_id: int) -> bool:
            """
            Delete (remove) a membership from project.

            Esta herramienta elimina una membresía de un proyecto, quitando
            efectivamente al usuario del proyecto. No se puede eliminar
            al propietario del proyecto.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                membership_id: ID de la membresía a eliminar

            Returns:
                True si la eliminación fue exitosa

            Raises:
                MCPError: Si no hay permisos, es el propietario, o falla la API

            Example:
                >>> result = await taiga_delete_membership(
                ...     auth_token="eyJ0eXAiOi...",
                ...     membership_id=456
                ... )
                >>> print(result)
                True
            """
            self._logger.debug(f"[delete_membership] Starting | membership_id={membership_id}")
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    result = await client.delete(f"/memberships/{membership_id}")
                    self._logger.info(
                        f"[delete_membership] Success | membership_id={membership_id}"
                    )
                    return result

            except ResourceNotFoundError:
                self._logger.error(f"[delete_membership] Not found | membership_id={membership_id}")
                raise MCPError("Membership not found") from None
            except PermissionDeniedError:
                self._logger.error(
                    f"[delete_membership] Permission denied | membership_id={membership_id}"
                )
                raise MCPError("No permission to remove this membership") from None
            except AuthenticationError:
                self._logger.error(
                    f"[delete_membership] Authentication failed | membership_id={membership_id}"
                )
                raise MCPError("Authentication failed. Please authenticate first") from None
            except TaigaAPIError as e:
                # Check for owner error in the exception message or response body
                error_msg = str(e).lower()
                response_body = (
                    getattr(e, "response_body", "").lower() if hasattr(e, "response_body") else ""
                )
                if (
                    "owner" in error_msg
                    or "cannot remove" in error_msg
                    or "owner" in response_body
                    or "cannot remove" in response_body
                ):
                    self._logger.error(
                        f"[delete_membership] Cannot remove owner | membership_id={membership_id}"
                    )
                    raise MCPError("Cannot remove project owner") from e
                self._logger.error(
                    f"[delete_membership] API error | membership_id={membership_id}, error={e!s}"
                )
                raise MCPError(f"Failed to delete membership: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[delete_membership] Unexpected error | membership_id={membership_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.delete_membership = (
            delete_membership.fn if hasattr(delete_membership, "fn") else delete_membership
        )

    # Legacy methods for backward compatibility
    def _register_tools(self) -> None:
        """Legacy registration method."""
        self.register_tools()
