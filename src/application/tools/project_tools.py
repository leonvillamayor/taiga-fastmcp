"""
Project management tools for Taiga MCP Server - Application layer.
"""

from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError as MCPError

from src.application.responses.project_responses import (
    ProjectIssuesStatsResponse,
    ProjectResponse,
    ProjectStatsResponse,
)
from src.config import TaigaConfig
from src.domain.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    ResourceNotFoundError,
    TaigaAPIError,
    ValidationError,
)
from src.domain.validators import (
    ProjectCreateValidator,
    ProjectDuplicateValidator,
    ProjectTagEditValidator,
    ProjectTagValidator,
    ProjectUpdateValidator,
    validate_input,
)
from src.infrastructure.client_factory import get_taiga_client
from src.infrastructure.logging import get_logger
from src.infrastructure.pagination import AutoPaginator, PaginationConfig
from src.taiga_client import TaigaAPIClient


class ProjectTools:
    """
    Project management tools for Taiga MCP Server.

    Provides MCP tools for managing projects in Taiga.
    """

    def __init__(self, mcp: FastMCP) -> None:
        """
        Initialize project tools.

        Args:
            mcp: FastMCP server instance
        """
        self.mcp = mcp
        self.config = TaigaConfig()
        self._client = None
        self.client = None  # For testing
        self._logger = get_logger("project_tools")

    def set_client(self, client: Any) -> None:
        """Set the Taiga API client (for testing purposes)."""
        self.client = client
        self._client = client

    def list_projects(self, **kwargs: Any) -> dict[str, Any]:
        """List projects - synchronous wrapper for testing."""
        try:
            client = get_taiga_client()  # This will be patched in tests
            result = client.list_projects(**kwargs)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_project(self, project_id: int, **kwargs: Any) -> dict[str, Any]:
        """Get project - synchronous wrapper for testing."""
        try:
            client = get_taiga_client()
            result = client.get_project(project_id, **kwargs)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_project(self, **kwargs: Any) -> dict[str, Any]:
        """Create project - synchronous wrapper for testing."""
        try:
            client = get_taiga_client()
            result = client.create_project(**kwargs)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def register_tools(self) -> None:
        """Register project tools with the MCP server."""

        # List projects
        @self.mcp.tool(
            name="taiga_list_projects",
            description="List all projects accessible to the authenticated user",
            tags={"projects", "read", "list"},
            annotations={"readOnlyHint": True, "openWorldHint": True},
        )
        async def list_projects(
            auth_token: str,
            member_id: int | None = None,
            is_private: bool | None = None,
            is_featured: bool | None = None,
            is_backlog_activated: bool | None = None,
            is_kanban_activated: bool | None = None,
            order_by: str | None = None,
            auto_paginate: bool = True,
        ) -> list[dict[str, Any]]:
            """
            List projects with optional filters.

            Esta herramienta lista todos los proyectos en Taiga a los que el
            usuario tiene acceso, con filtros opcionales.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                member_id: Filtrar por proyectos donde este usuario es miembro (opcional)
                is_private: Filtrar por proyectos privados (True) o públicos (False) (opcional)
                is_featured: Filtrar por proyectos destacados (opcional)
                is_backlog_activated: Filtrar por proyectos con backlog activo (opcional)
                is_kanban_activated: Filtrar por proyectos con kanban activo (opcional)
                order_by: Campo por el cual ordenar (ej: "name", "-created_date") (opcional)
                auto_paginate: Si True, obtiene automáticamente todas las páginas.
                    Si False, solo retorna la primera página. Default: True.

            Returns:
                Lista de diccionarios con información de proyectos, cada uno conteniendo:
                - id: ID del proyecto
                - name: Nombre del proyecto
                - slug: Slug único del proyecto
                - description: Descripción del proyecto
                - is_private: Si es privado
                - is_featured: Si está destacado
                - total_fans: Número de seguidores
                - total_watchers: Número de observadores
                - total_activity: Nivel de actividad total
                - owner: ID del propietario
                - members: Lista de IDs de miembros

            Raises:
                MCPError: Si la autenticación falla o hay error en la API

            Example:
                >>> projects = await taiga_list_projects(
                ...     auth_token="eyJ0eXAiOi...",
                ...     is_private=False,
                ...     order_by="-created_date"
                ... )
                >>> print(projects)
                [
                    {
                        "id": 1,
                        "name": "Mi Proyecto",
                        "slug": "mi-proyecto",
                        "description": "Descripción del proyecto",
                        "is_private": False,
                        "is_featured": True,
                        "total_fans": 10,
                        "total_watchers": 5,
                        "total_activity": 150,
                        "owner": 42,
                        "members": [42, 43, 44]
                    }
                ]
            """
            try:
                self._logger.debug(
                    f"[list_projects] Starting | filters={bool(member_id or is_private is not None)}"
                )
                params = {}
                if member_id is not None:
                    params["member"] = member_id
                if is_private is not None:
                    params["is_private"] = is_private
                if is_featured is not None:
                    params["is_featured"] = is_featured
                if is_backlog_activated is not None:
                    params["is_backlog_activated"] = is_backlog_activated
                if is_kanban_activated is not None:
                    params["is_kanban_activated"] = is_kanban_activated
                if order_by:
                    params["order_by"] = order_by

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    paginator = AutoPaginator(client, PaginationConfig())

                    if auto_paginate:
                        projects = await paginator.paginate("/projects", params=params)
                    else:
                        projects = await paginator.paginate_first_page("/projects", params=params)

                    # Validate each project with Pydantic
                    result = [
                        ProjectResponse.model_validate(project).model_dump(exclude_none=True)
                        for project in projects
                    ]
                    self._logger.info(f"[list_projects] Success | count={len(result)}")
                    return result

            except AuthenticationError:
                self._logger.error("[list_projects] Authentication failed")
                raise MCPError("Authentication failed. Please authenticate first") from None
            except TaigaAPIError as e:
                self._logger.error(f"[list_projects] API error | error={e!s}")
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(f"[list_projects] Unexpected error | error={e!s}")
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        if hasattr(list_projects, "__wrapped__"):
            self.list_projects = list_projects.__wrapped__
        elif hasattr(list_projects, "fn"):
            self.list_projects = list_projects.fn
        else:
            self.list_projects = list_projects

        # Create project
        @self.mcp.tool(
            name="taiga_create_project",
            description="Create a new Taiga project with specified settings",
            tags={"projects", "write", "create"},
            annotations={"readOnlyHint": False, "openWorldHint": True},
        )
        async def create_project(
            auth_token: str,
            name: str,
            description: str | None = None,
            is_private: bool | None = True,
            is_backlog_activated: bool | None = True,
            is_issues_activated: bool | None = True,
            is_kanban_activated: bool | None = False,
            is_wiki_activated: bool | None = False,
            is_epics_activated: bool | None = False,
            videoconferences: str | None = None,
            videoconferences_extra_data: str | None = None,
            total_milestones: int | None = None,
            total_story_points: float | None = None,
            tags: list[str] | None = None,
        ) -> dict[str, Any]:
            """
            Create a new project.

            Esta herramienta crea un nuevo proyecto en Taiga con la configuración
            especificada para módulos, visibilidad y características.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                name: Nombre del proyecto (requerido)
                description: Descripción del proyecto (opcional)
                is_private: Si el proyecto es privado (default: True)
                is_backlog_activated: Activar módulo de backlog (default: True)
                is_issues_activated: Activar módulo de issues (default: True)
                is_kanban_activated: Activar módulo kanban (default: False)
                is_wiki_activated: Activar módulo wiki (default: False)
                is_epics_activated: Activar módulo epics (default: False)
                videoconferences: Tipo de videoconferencia ("whereby-com", "jitsi", etc.)
                videoconferences_extra_data: Datos adicionales para videoconferencia
                total_milestones: Número total de milestones planificados
                total_story_points: Puntos de historia totales planificados
                tags: Lista de etiquetas iniciales para el proyecto

            Returns:
                Dict con los siguientes campos:
                - id: ID del proyecto creado
                - name: Nombre del proyecto
                - slug: Slug único generado
                - description: Descripción del proyecto
                - is_private: Si es privado
                - is_backlog_activated: Si backlog está activo
                - is_issues_activated: Si issues está activo
                - is_kanban_activated: Si kanban está activo
                - is_wiki_activated: Si wiki está activo
                - is_epics_activated: Si epics está activo
                - videoconferences: Configuración de videoconferencia
                - tags: Lista de etiquetas
                - message: Mensaje de confirmación

            Raises:
                MCPError: Si la autenticación falla, el nombre ya existe, o hay error en la API

            Example:
                >>> project = await taiga_create_project(
                ...     auth_token="eyJ0eXAiOi...",
                ...     name="Nuevo Proyecto",
                ...     description="Mi nuevo proyecto de desarrollo",
                ...     is_private=True,
                ...     is_backlog_activated=True,
                ...     is_kanban_activated=True,
                ...     tags=["desarrollo", "python"]
                ... )
                >>> print(project)
                {
                    "id": 123,
                    "name": "Nuevo Proyecto",
                    "slug": "nuevo-proyecto",
                    "description": "Mi nuevo proyecto de desarrollo",
                    "is_private": True,
                    "is_backlog_activated": True,
                    "is_issues_activated": True,
                    "is_kanban_activated": True,
                    "is_wiki_activated": False,
                    "videoconferences": None,
                    "tags": ["desarrollo", "python"],
                    "message": "Successfully created project 'Nuevo Proyecto'"
                }
            """
            try:
                self._logger.debug(f"[create_project] Starting | name={name}")
                project_data = {"name": name}

                if description is not None:
                    project_data["description"] = description
                if is_private is not None:
                    project_data["is_private"] = is_private
                if is_backlog_activated is not None:
                    project_data["is_backlog_activated"] = is_backlog_activated
                if is_issues_activated is not None:
                    project_data["is_issues_activated"] = is_issues_activated
                if is_kanban_activated is not None:
                    project_data["is_kanban_activated"] = is_kanban_activated
                if is_wiki_activated is not None:
                    project_data["is_wiki_activated"] = is_wiki_activated
                if is_epics_activated is not None:
                    project_data["is_epics_activated"] = is_epics_activated
                if videoconferences:
                    project_data["videoconferences"] = videoconferences
                if videoconferences_extra_data:
                    project_data["videoconferences_extra_data"] = videoconferences_extra_data
                if total_milestones is not None:
                    project_data["total_milestones"] = total_milestones
                if total_story_points is not None:
                    project_data["total_story_points"] = total_story_points
                if tags:
                    project_data["tags"] = tags

                # Validar datos de entrada ANTES de llamar a la API
                validate_input(ProjectCreateValidator, project_data)

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    project = await client.post("/projects", data=project_data)

                    # Validate response with Pydantic
                    validated_project = ProjectResponse.model_validate(project).model_dump(
                        exclude_none=True
                    )
                    validated_project["message"] = f"Successfully created project '{name}'"
                    self._logger.info(
                        f"[create_project] Success | id={validated_project.get('id')}, name={name}"
                    )
                    return validated_project

            except ValidationError as e:
                self._logger.warning(f"[create_project] Validation error | error={e!s}")
                raise MCPError(str(e)) from e
            except AuthenticationError:
                self._logger.error("[create_project] Authentication failed")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                if "duplicate" in str(e).lower():
                    self._logger.warning(f"[create_project] Duplicate name | name={name}")
                    raise MCPError(f"Project with name '{name}' already exists") from e
                self._logger.error(f"[create_project] API error | error={e!s}")
                raise MCPError(f"Failed to create project: {e!s}") from e
            except Exception as e:
                self._logger.error(f"[create_project] Unexpected error | error={e!s}")
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        if hasattr(create_project, "__wrapped__"):
            self.create_project = create_project.__wrapped__
        elif hasattr(create_project, "fn"):
            self.create_project = create_project.fn
        else:
            self.create_project = create_project

        # Get project
        @self.mcp.tool(
            name="taiga_get_project",
            description="Get detailed information about a specific project",
            tags={"projects", "read", "get"},
            annotations={"readOnlyHint": True, "openWorldHint": True},
        )
        async def get_project(
            auth_token: str, project_id: int | None = None, slug: str | None = None
        ) -> dict[str, Any]:
            """
            Get project details.

            Esta herramienta obtiene los detalles completos de un proyecto
            específico en Taiga, identificado por ID o slug.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto a consultar (opcional si se proporciona slug)
                slug: Slug único del proyecto (opcional si se proporciona project_id)

            Returns:
                Dict con los siguientes campos:
                - id: ID del proyecto
                - name: Nombre del proyecto
                - slug: Slug único
                - description: Descripción del proyecto
                - is_private: Si es privado
                - is_backlog_activated: Si backlog está activo
                - is_issues_activated: Si issues está activo
                - is_kanban_activated: Si kanban está activo
                - is_wiki_activated: Si wiki está activo
                - owner: ID del propietario
                - members: Lista de IDs de miembros
                - total_fans: Número de seguidores
                - total_watchers: Número de observadores
                - total_activity: Nivel de actividad
                - created_date: Fecha de creación
                - modified_date: Fecha de última modificación
                - tags: Lista de etiquetas
                - tags_colors: Diccionario de colores de etiquetas
                - us_statuses: Estados de historias de usuario
                - task_statuses: Estados de tareas
                - issue_statuses: Estados de issues
                - priorities: Prioridades definidas
                - severities: Severidades definidas
                - issue_types: Tipos de issues
                - milestones: Lista de milestones

            Raises:
                MCPError: Si el proyecto no existe, no hay permisos, o falla la API

            Example:
                >>> project = await taiga_get_project(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print(project)
                {
                    "id": 123,
                    "name": "Mi Proyecto",
                    "slug": "mi-proyecto",
                    "description": "Descripción del proyecto",
                    "is_private": True,
                    "is_backlog_activated": True,
                    "owner": 42,
                    "members": [42, 43],
                    "created_date": "2024-01-15T10:30:00Z",
                    "tags": ["backend", "api"],
                    "milestones": [{"id": 1, "name": "Sprint 1"}]
                }
            """
            try:
                identifier = f"id={project_id}" if project_id else f"slug={slug}"
                self._logger.debug(f"[get_project] Starting | {identifier}")

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token

                    if project_id:
                        project = await client.get(f"/projects/{project_id}")
                    elif slug:
                        project = await client.get(f"/projects/by_slug?slug={slug}")
                    else:
                        self._logger.error("[get_project] Missing required parameter")
                        raise MCPError("Either project_id or slug is required")

                    # Validate response with Pydantic
                    result = ProjectResponse.model_validate(project).model_dump(exclude_none=True)
                    self._logger.info(f"[get_project] Success | {identifier}")
                    return result

            except ResourceNotFoundError:
                self._logger.warning(f"[get_project] Not found | {identifier}")
                raise MCPError("Project not found") from None
            except PermissionDeniedError:
                self._logger.warning(f"[get_project] Permission denied | {identifier}")
                raise MCPError("No permission to access project") from None
            except AuthenticationError:
                self._logger.error("[get_project] Authentication failed")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(f"[get_project] API error | {identifier}, error={e!s}")
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(f"[get_project] Unexpected error | {identifier}, error={e!s}")
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        if hasattr(get_project, "__wrapped__"):
            self.get_project = get_project.__wrapped__
        elif hasattr(get_project, "fn"):
            self.get_project = get_project.fn
        else:
            self.get_project = get_project

        # Update project
        @self.mcp.tool(
            name="taiga_update_project",
            description="Update an existing project's settings and metadata",
            tags={"projects", "write", "update"},
            annotations={"readOnlyHint": False, "openWorldHint": True},
        )
        async def update_project(
            auth_token: str,
            project_id: int,
            name: str | None = None,
            description: str | None = None,
            is_private: bool | None = None,
            is_backlog_activated: bool | None = None,
            is_issues_activated: bool | None = None,
            is_kanban_activated: bool | None = None,
            is_wiki_activated: bool | None = None,
            is_epics_activated: bool | None = None,
            version: int | None = None,
        ) -> dict[str, Any]:
            """
            Update project details.

            Esta herramienta permite actualizar los detalles de un proyecto
            existente en Taiga, incluyendo nombre, descripción y módulos.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto a actualizar
                name: Nuevo nombre del proyecto (opcional)
                description: Nueva descripción (opcional)
                is_private: Cambiar visibilidad privada/pública (opcional)
                is_backlog_activated: Activar/desactivar backlog (opcional)
                is_issues_activated: Activar/desactivar issues (opcional)
                is_kanban_activated: Activar/desactivar kanban (opcional)
                is_wiki_activated: Activar/desactivar wiki (opcional)
                is_epics_activated: Activar/desactivar epics (opcional)
                version: Versión actual para control de concurrencia (opcional)

            Returns:
                Dict con los siguientes campos:
                - id: ID del proyecto
                - name: Nombre actualizado
                - slug: Slug del proyecto
                - description: Descripción actualizada
                - is_private: Estado de privacidad
                - is_backlog_activated: Estado de backlog
                - is_issues_activated: Estado de issues
                - is_kanban_activated: Estado de kanban
                - is_wiki_activated: Estado de wiki
                - is_epics_activated: Estado de epics
                - version: Nueva versión del proyecto
                - message: Mensaje de confirmación

            Raises:
                MCPError: Si el proyecto no existe, no hay permisos, conflicto de versión, o falla la API

            Example:
                >>> project = await taiga_update_project(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     name="Proyecto Renombrado",
                ...     is_kanban_activated=True
                ... )
                >>> print(project)
                {
                    "id": 123,
                    "name": "Proyecto Renombrado",
                    "slug": "proyecto-renombrado",
                    "description": "Descripción original",
                    "is_private": True,
                    "is_backlog_activated": True,
                    "is_issues_activated": True,
                    "is_kanban_activated": True,
                    "is_wiki_activated": False,
                    "version": 2,
                    "message": "Successfully updated project 123"
                }
            """
            try:
                self._logger.debug(f"[update_project] Starting | project_id={project_id}")

                update_data = {}
                if name is not None:
                    update_data["name"] = name
                if description is not None:
                    update_data["description"] = description
                if is_private is not None:
                    update_data["is_private"] = is_private
                if is_backlog_activated is not None:
                    update_data["is_backlog_activated"] = is_backlog_activated
                if is_issues_activated is not None:
                    update_data["is_issues_activated"] = is_issues_activated
                if is_kanban_activated is not None:
                    update_data["is_kanban_activated"] = is_kanban_activated
                if is_wiki_activated is not None:
                    update_data["is_wiki_activated"] = is_wiki_activated
                if is_epics_activated is not None:
                    update_data["is_epics_activated"] = is_epics_activated
                if version is not None:
                    update_data["version"] = version

                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {"project_id": project_id, **update_data}
                validate_input(ProjectUpdateValidator, validation_data)

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    project = await client.patch(f"/projects/{project_id}", data=update_data)

                    # Validate response with Pydantic
                    validated = ProjectResponse.model_validate(project).model_dump(
                        exclude_none=True
                    )
                    validated["message"] = f"Successfully updated project {project_id}"
                    self._logger.info(
                        f"[update_project] Success | project_id={project_id}, fields_updated={list(update_data.keys())}"
                    )
                    return validated

            except ValidationError as e:
                self._logger.warning(f"[update_project] Validation error | error={e!s}")
                raise MCPError(str(e)) from e
            except ResourceNotFoundError:
                self._logger.warning(f"[update_project] Not found | project_id={project_id}")
                raise MCPError(f"Project {project_id} not found") from None
            except PermissionDeniedError:
                self._logger.warning(
                    f"[update_project] Permission denied | project_id={project_id}"
                )
                raise MCPError(f"No permission to update project {project_id}") from None
            except AuthenticationError:
                self._logger.error("[update_project] Authentication failed")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                if "version" in str(e).lower() and "conflict" in str(e).lower():
                    self._logger.warning(
                        f"[update_project] Version conflict | project_id={project_id}"
                    )
                    raise MCPError(
                        "Version conflict. Please refresh project details and try again"
                    ) from e
                self._logger.error(
                    f"[update_project] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Failed to update project: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[update_project] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        if hasattr(update_project, "__wrapped__"):
            self.update_project = update_project.__wrapped__
        elif hasattr(update_project, "fn"):
            self.update_project = update_project.fn
        else:
            self.update_project = update_project

        # Delete project
        @self.mcp.tool(
            name="taiga_delete_project",
            description="Permanently delete a project and all its data",
            tags={"projects", "delete"},
            annotations={"destructiveHint": True, "openWorldHint": True, "title": "Delete Project"},
        )
        async def delete_project(auth_token: str, project_id: int) -> bool:
            """
            Delete a project.

            Esta herramienta elimina permanentemente un proyecto de Taiga.
            Esta acción no se puede deshacer.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto a eliminar

            Returns:
                True si la eliminación fue exitosa

            Raises:
                MCPError: Si el proyecto no existe, no hay permisos, o falla la API

            Example:
                >>> result = await taiga_delete_project(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print(result)
                True
            """
            try:
                self._logger.debug(f"[delete_project] Starting | project_id={project_id}")

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    result = await client.delete(f"/projects/{project_id}")
                    self._logger.info(f"[delete_project] Success | project_id={project_id}")
                    return result

            except ResourceNotFoundError:
                self._logger.warning(f"[delete_project] Not found | project_id={project_id}")
                raise MCPError(f"Project {project_id} not found") from None
            except PermissionDeniedError:
                self._logger.warning(
                    f"[delete_project] Permission denied | project_id={project_id}"
                )
                raise MCPError(f"No permission to delete project {project_id}") from None
            except AuthenticationError:
                self._logger.error("[delete_project] Authentication failed")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[delete_project] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Failed to delete project: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[delete_project] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        if hasattr(delete_project, "__wrapped__"):
            self.delete_project = delete_project.__wrapped__
        elif hasattr(delete_project, "fn"):
            self.delete_project = delete_project.fn
        else:
            self.delete_project = delete_project

        # Get project stats
        @self.mcp.tool(
            name="taiga_get_project_stats",
            description="Get comprehensive statistics for a project",
            tags={"projects", "read", "stats"},
            annotations={"readOnlyHint": True, "openWorldHint": True},
        )
        async def get_project_stats(auth_token: str, project_id: int) -> dict[str, Any]:
            """
            Get project statistics.

            Esta herramienta obtiene estadísticas detalladas de un proyecto,
            incluyendo puntos, milestones, historias, tareas e issues.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto del que obtener estadísticas

            Returns:
                Dict con los siguientes campos:
                - total_points: Puntos totales del proyecto
                - closed_points: Puntos cerrados
                - total_milestones: Número total de milestones
                - completed_milestones: Milestones completados
                - total_userstories: Historias de usuario totales
                - completed_userstories: Historias completadas
                - total_tasks: Tareas totales
                - completed_tasks: Tareas completadas
                - total_issues: Issues totales
                - closed_issues: Issues cerrados
                - assigned_points: Puntos asignados por usuario
                - defined_points: Puntos definidos por rol
                - speed: Velocidad del equipo

            Raises:
                MCPError: Si el proyecto no existe, la autenticación falla, o hay error en la API

            Example:
                >>> stats = await taiga_get_project_stats(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print(stats)
                {
                    "total_points": 100,
                    "closed_points": 75,
                    "total_milestones": 5,
                    "completed_milestones": 3,
                    "total_userstories": 50,
                    "completed_userstories": 35,
                    "total_tasks": 200,
                    "completed_tasks": 150,
                    "total_issues": 30,
                    "closed_issues": 25,
                    "assigned_points": {"42": 50, "43": 50},
                    "defined_points": {"UX": 30, "Backend": 70},
                    "speed": 15
                }
            """
            try:
                self._logger.debug(f"[get_project_stats] Starting | project_id={project_id}")

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    stats = await client.get(f"/projects/{project_id}/stats")

                    # Validate response with Pydantic
                    result = ProjectStatsResponse.model_validate(stats).model_dump(
                        exclude_none=True
                    )
                    self._logger.info(f"[get_project_stats] Success | project_id={project_id}")
                    return result

            except ResourceNotFoundError:
                self._logger.warning(f"[get_project_stats] Not found | project_id={project_id}")
                raise MCPError(f"Project {project_id} not found") from None
            except AuthenticationError:
                self._logger.error("[get_project_stats] Authentication failed")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[get_project_stats] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[get_project_stats] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        if hasattr(get_project_stats, "__wrapped__"):
            self.get_project_stats = get_project_stats.__wrapped__
        elif hasattr(get_project_stats, "fn"):
            self.get_project_stats = get_project_stats.fn
        else:
            self.get_project_stats = get_project_stats

        # Duplicate project
        @self.mcp.tool(
            name="taiga_duplicate_project",
            description="Create a copy of an existing project with optional settings",
            tags={"projects", "write", "create"},
            annotations={"readOnlyHint": False, "openWorldHint": True},
        )
        async def duplicate_project(
            auth_token: str,
            project_id: int,
            name: str,
            description: str | None = None,
            is_private: bool | None = True,
            users: list[str] | None = None,
        ) -> dict[str, Any]:
            """
            Duplicate a project.

            Esta herramienta crea una copia de un proyecto existente con un
            nuevo nombre, opcionalmente incluyendo usuarios seleccionados.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto original a duplicar
                name: Nombre para el nuevo proyecto duplicado
                description: Nueva descripción (opcional, usa la original si no se proporciona)
                is_private: Si el duplicado es privado (default: True)
                users: Lista de usernames a incluir en el duplicado (opcional)

            Returns:
                Dict con los siguientes campos:
                - id: ID del proyecto duplicado
                - name: Nombre del nuevo proyecto
                - slug: Slug único generado
                - description: Descripción del proyecto
                - message: Mensaje de confirmación

            Raises:
                MCPError: Si el proyecto original no existe, la autenticación falla, o hay error en la API

            Example:
                >>> project = await taiga_duplicate_project(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     name="Copia de Mi Proyecto",
                ...     is_private=True,
                ...     users=["user1", "user2"]
                ... )
                >>> print(project)
                {
                    "id": 456,
                    "name": "Copia de Mi Proyecto",
                    "slug": "copia-de-mi-proyecto",
                    "description": "Descripción original",
                    "message": "Successfully duplicated project as 'Copia de Mi Proyecto'"
                }
            """
            try:
                self._logger.debug(
                    f"[duplicate_project] Starting | source_id={project_id}, new_name={name}"
                )

                duplicate_data = {"name": name, "is_private": is_private}

                if description:
                    duplicate_data["description"] = description
                if users:
                    duplicate_data["users"] = users

                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {"project_id": project_id, **duplicate_data}
                validate_input(ProjectDuplicateValidator, validation_data)

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    project = await client.post(
                        f"/projects/{project_id}/duplicate", data=duplicate_data
                    )

                    # Validate response with Pydantic
                    validated = ProjectResponse.model_validate(project).model_dump(
                        exclude_none=True
                    )
                    validated["message"] = f"Successfully duplicated project as '{name}'"
                    self._logger.info(
                        f"[duplicate_project] Success | source_id={project_id}, new_id={validated.get('id')}, new_name={name}"
                    )
                    return validated

            except ValidationError as e:
                self._logger.warning(f"[duplicate_project] Validation error | error={e!s}")
                raise MCPError(str(e)) from e
            except ResourceNotFoundError:
                self._logger.warning(
                    f"[duplicate_project] Source not found | source_id={project_id}"
                )
                raise MCPError(f"Project {project_id} not found") from None
            except AuthenticationError:
                self._logger.error("[duplicate_project] Authentication failed")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[duplicate_project] API error | source_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Failed to duplicate project: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[duplicate_project] Unexpected error | source_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        if hasattr(duplicate_project, "__wrapped__"):
            self.duplicate_project = duplicate_project.__wrapped__
        elif hasattr(duplicate_project, "fn"):
            self.duplicate_project = duplicate_project.fn
        else:
            self.duplicate_project = duplicate_project

        # Like project
        @self.mcp.tool(
            name="taiga_like_project",
            description="Add a like to a project",
            tags={"projects", "write", "social"},
            annotations={"readOnlyHint": False, "idempotentHint": True, "openWorldHint": True},
        )
        async def like_project(auth_token: str, project_id: int) -> dict[str, Any]:
            """
            Like a project.

            Esta herramienta marca un proyecto como favorito ("me gusta") para el
            usuario actual, incrementando el contador de fans del proyecto.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto a marcar como favorito

            Returns:
                Dict con los siguientes campos:
                - is_fan: True si el usuario es ahora fan del proyecto
                - total_fans: Número total de fans del proyecto
                - message: Mensaje de confirmación

            Raises:
                MCPError: Si el proyecto no existe, la autenticación falla, o hay error en la API

            Example:
                >>> result = await taiga_like_project(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print(result)
                {
                    "is_fan": True,
                    "total_fans": 15,
                    "message": "Successfully liked project 123"
                }
            """
            try:
                self._logger.debug(f"[like_project] Starting | project_id={project_id}")

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    result = await client.post(f"/projects/{project_id}/like")

                    self._logger.info(
                        f"[like_project] Success | project_id={project_id}, total_fans={result.get('total_fans', 0)}"
                    )
                    return {
                        "is_fan": result.get("is_fan", True),
                        "total_fans": result.get("total_fans", 0),
                        "message": f"Successfully liked project {project_id}",
                    }

            except ResourceNotFoundError:
                self._logger.warning(f"[like_project] Not found | project_id={project_id}")
                raise MCPError(f"Project {project_id} not found") from None
            except AuthenticationError:
                self._logger.error("[like_project] Authentication failed")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[like_project] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Failed to like project: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[like_project] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        if hasattr(like_project, "__wrapped__"):
            self.like_project = like_project.__wrapped__
        elif hasattr(like_project, "fn"):
            self.like_project = like_project.fn
        else:
            self.like_project = like_project

        # Unlike project
        @self.mcp.tool(
            name="taiga_unlike_project",
            description="Remove a like from a project",
            tags={"projects", "write", "social"},
            annotations={"readOnlyHint": False, "idempotentHint": True, "openWorldHint": True},
        )
        async def unlike_project(auth_token: str, project_id: int) -> dict[str, Any]:
            """
            Unlike a project.

            Esta herramienta quita la marca de favorito ("me gusta") de un proyecto
            para el usuario actual, decrementando el contador de fans.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto a quitar de favoritos

            Returns:
                Dict con los siguientes campos:
                - is_fan: False indicando que ya no es fan
                - total_fans: Número total de fans del proyecto
                - message: Mensaje de confirmación

            Raises:
                MCPError: Si el proyecto no existe, la autenticación falla, o hay error en la API

            Example:
                >>> result = await taiga_unlike_project(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print(result)
                {
                    "is_fan": False,
                    "total_fans": 14,
                    "message": "Successfully unliked project 123"
                }
            """
            try:
                self._logger.debug(f"[unlike_project] Starting | project_id={project_id}")

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    result = await client.post(f"/projects/{project_id}/unlike")

                    self._logger.info(
                        f"[unlike_project] Success | project_id={project_id}, total_fans={result.get('total_fans', 0)}"
                    )
                    return {
                        "is_fan": result.get("is_fan", False),
                        "total_fans": result.get("total_fans", 0),
                        "message": f"Successfully unliked project {project_id}",
                    }

            except ResourceNotFoundError:
                self._logger.warning(f"[unlike_project] Not found | project_id={project_id}")
                raise MCPError(f"Project {project_id} not found") from None
            except AuthenticationError:
                self._logger.error("[unlike_project] Authentication failed")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[unlike_project] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Failed to unlike project: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[unlike_project] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        if hasattr(unlike_project, "__wrapped__"):
            self.unlike_project = unlike_project.__wrapped__
        elif hasattr(unlike_project, "fn"):
            self.unlike_project = unlike_project.fn
        else:
            self.unlike_project = unlike_project

        # Watch project
        @self.mcp.tool(
            name="taiga_watch_project",
            description="Start watching a project to receive notifications",
            tags={"projects", "write", "notifications"},
            annotations={"readOnlyHint": False, "idempotentHint": True, "openWorldHint": True},
        )
        async def watch_project(auth_token: str, project_id: int) -> dict[str, Any]:
            """
            Watch a project.

            Esta herramienta suscribe al usuario actual a las notificaciones
            del proyecto, recibiendo alertas sobre cambios y actividad.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto a observar

            Returns:
                Dict con los siguientes campos:
                - is_watcher: True si el usuario es ahora observador
                - total_watchers: Número total de observadores
                - message: Mensaje de confirmación

            Raises:
                MCPError: Si el proyecto no existe, la autenticación falla, o hay error en la API

            Example:
                >>> result = await taiga_watch_project(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print(result)
                {
                    "is_watcher": True,
                    "total_watchers": 8,
                    "message": "Now watching project 123"
                }
            """
            try:
                self._logger.debug(f"[watch_project] Starting | project_id={project_id}")

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    result = await client.post(f"/projects/{project_id}/watch")

                    self._logger.info(
                        f"[watch_project] Success | project_id={project_id}, total_watchers={result.get('total_watchers', 0)}"
                    )
                    return {
                        "is_watcher": result.get("is_watcher", True),
                        "total_watchers": result.get("total_watchers", 0),
                        "message": f"Now watching project {project_id}",
                    }

            except ResourceNotFoundError:
                self._logger.warning(f"[watch_project] Not found | project_id={project_id}")
                raise MCPError(f"Project {project_id} not found") from None
            except AuthenticationError:
                self._logger.error("[watch_project] Authentication failed")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[watch_project] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Failed to watch project: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[watch_project] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        if hasattr(watch_project, "__wrapped__"):
            self.watch_project = watch_project.__wrapped__
        elif hasattr(watch_project, "fn"):
            self.watch_project = watch_project.fn
        else:
            self.watch_project = watch_project

        # Unwatch project
        @self.mcp.tool(
            name="taiga_unwatch_project",
            description="Stop watching a project and receiving notifications",
            tags={"projects", "write", "notifications"},
            annotations={"readOnlyHint": False, "idempotentHint": True, "openWorldHint": True},
        )
        async def unwatch_project(auth_token: str, project_id: int) -> dict[str, Any]:
            """
            Unwatch a project.

            Esta herramienta cancela la suscripción del usuario actual a las
            notificaciones del proyecto, dejando de recibir alertas.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto a dejar de observar

            Returns:
                Dict con los siguientes campos:
                - is_watcher: False indicando que ya no es observador
                - total_watchers: Número total de observadores
                - message: Mensaje de confirmación

            Raises:
                MCPError: Si el proyecto no existe, la autenticación falla, o hay error en la API

            Example:
                >>> result = await taiga_unwatch_project(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print(result)
                {
                    "is_watcher": False,
                    "total_watchers": 7,
                    "message": "Stopped watching project 123"
                }
            """
            try:
                self._logger.debug(f"[unwatch_project] Starting | project_id={project_id}")

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    result = await client.post(f"/projects/{project_id}/unwatch")

                    self._logger.info(
                        f"[unwatch_project] Success | project_id={project_id}, total_watchers={result.get('total_watchers', 0)}"
                    )
                    return {
                        "is_watcher": result.get("is_watcher", False),
                        "total_watchers": result.get("total_watchers", 0),
                        "message": f"Stopped watching project {project_id}",
                    }

            except ResourceNotFoundError:
                self._logger.warning(f"[unwatch_project] Not found | project_id={project_id}")
                raise MCPError(f"Project {project_id} not found") from None
            except AuthenticationError:
                self._logger.error("[unwatch_project] Authentication failed")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[unwatch_project] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Failed to unwatch project: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[unwatch_project] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        if hasattr(unwatch_project, "__wrapped__"):
            self.unwatch_project = unwatch_project.__wrapped__
        elif hasattr(unwatch_project, "fn"):
            self.unwatch_project = unwatch_project.fn
        else:
            self.unwatch_project = unwatch_project

        # Get project modules
        @self.mcp.tool(
            name="taiga_get_project_modules", description="Get project modules configuration"
        )
        async def get_project_modules(auth_token: str, project_id: int) -> dict[str, Any]:
            """
            Get project modules configuration.

            Esta herramienta obtiene la configuración de módulos activos de un
            proyecto, incluyendo backlog, kanban, wiki, issues y videoconferencias.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto del que obtener la configuración

            Returns:
                Dict con los siguientes campos:
                - is_backlog_activated: Si el módulo backlog está activo
                - is_issues_activated: Si el módulo issues está activo
                - is_kanban_activated: Si el módulo kanban está activo
                - is_wiki_activated: Si el módulo wiki está activo
                - videoconferences: Tipo de videoconferencia configurada
                - videoconferences_extra_data: Datos adicionales de videoconferencia

            Raises:
                MCPError: Si el proyecto no existe, la autenticación falla, o hay error en la API

            Example:
                >>> modules = await taiga_get_project_modules(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print(modules)
                {
                    "is_backlog_activated": True,
                    "is_issues_activated": True,
                    "is_kanban_activated": False,
                    "is_wiki_activated": True,
                    "videoconferences": "jitsi",
                    "videoconferences_extra_data": "room-123"
                }
            """
            try:
                self._logger.debug(f"[get_project_modules] Starting | project_id={project_id}")
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    modules = await client.get(f"/projects/{project_id}/modules")

                    result = {
                        "is_backlog_activated": modules.get("backlog", False),
                        "is_issues_activated": modules.get("issues", False),
                        "is_kanban_activated": modules.get("kanban", False),
                        "is_wiki_activated": modules.get("wiki", False),
                        "videoconferences": modules.get("videoconferences"),
                        "videoconferences_extra_data": modules.get("videoconferences_extra_data"),
                    }
                    self._logger.info(f"[get_project_modules] Success | project_id={project_id}")
                    return result

            except ResourceNotFoundError:
                self._logger.warning(f"[get_project_modules] Not found | project_id={project_id}")
                raise MCPError(f"Project {project_id} not found") from None
            except AuthenticationError:
                self._logger.warning(f"[get_project_modules] Auth failed | project_id={project_id}")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[get_project_modules] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[get_project_modules] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        if hasattr(get_project_modules, "__wrapped__"):
            self.get_project_modules = get_project_modules.__wrapped__
        elif hasattr(get_project_modules, "fn"):
            self.get_project_modules = get_project_modules.fn
        else:
            self.get_project_modules = get_project_modules

        # Update project modules
        @self.mcp.tool(
            name="taiga_update_project_modules", description="Update project modules configuration"
        )
        async def update_project_modules(
            auth_token: str,
            project_id: int,
            is_backlog_activated: bool | None = None,
            is_issues_activated: bool | None = None,
            is_kanban_activated: bool | None = None,
            is_wiki_activated: bool | None = None,
            videoconferences: str | None = None,
            videoconferences_extra_data: str | None = None,
        ) -> dict[str, Any]:
            """
            Update project modules configuration.

            Esta herramienta permite activar o desactivar módulos de un proyecto,
            así como configurar opciones de videoconferencia.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto a actualizar
                is_backlog_activated: Activar/desactivar módulo backlog (opcional)
                is_issues_activated: Activar/desactivar módulo issues (opcional)
                is_kanban_activated: Activar/desactivar módulo kanban (opcional)
                is_wiki_activated: Activar/desactivar módulo wiki (opcional)
                videoconferences: Tipo de videoconferencia ("whereby-com", "jitsi", None)
                videoconferences_extra_data: Datos adicionales (nombre de sala, etc.)

            Returns:
                Dict con los siguientes campos:
                - is_backlog_activated: Estado actual del backlog
                - is_issues_activated: Estado actual de issues
                - is_kanban_activated: Estado actual del kanban
                - is_wiki_activated: Estado actual del wiki
                - videoconferences: Tipo de videoconferencia configurada
                - videoconferences_extra_data: Datos de videoconferencia
                - message: Mensaje de confirmación

            Raises:
                MCPError: Si el proyecto no existe, no hay permisos, o falla la API

            Example:
                >>> result = await taiga_update_project_modules(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     is_kanban_activated=True,
                ...     is_wiki_activated=True,
                ...     videoconferences="jitsi"
                ... )
                >>> print(result)
                {
                    "is_backlog_activated": True,
                    "is_issues_activated": True,
                    "is_kanban_activated": True,
                    "is_wiki_activated": True,
                    "videoconferences": "jitsi",
                    "videoconferences_extra_data": None,
                    "message": "Successfully updated modules for project 123"
                }
            """
            try:
                self._logger.debug(f"[update_project_modules] Starting | project_id={project_id}")
                modules_data = {}
                if is_backlog_activated is not None:
                    modules_data["backlog"] = is_backlog_activated
                if is_issues_activated is not None:
                    modules_data["issues"] = is_issues_activated
                if is_kanban_activated is not None:
                    modules_data["kanban"] = is_kanban_activated
                if is_wiki_activated is not None:
                    modules_data["wiki"] = is_wiki_activated
                if videoconferences is not None:
                    modules_data["videoconferences"] = videoconferences
                if videoconferences_extra_data is not None:
                    modules_data["videoconferences_extra_data"] = videoconferences_extra_data

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    result = await client.patch(
                        f"/projects/{project_id}/modules", data=modules_data
                    )

                    response = {
                        "is_backlog_activated": result.get("backlog", False),
                        "is_issues_activated": result.get("issues", False),
                        "is_kanban_activated": result.get("kanban", False),
                        "is_wiki_activated": result.get("wiki", False),
                        "videoconferences": result.get("videoconferences"),
                        "videoconferences_extra_data": result.get("videoconferences_extra_data"),
                        "message": f"Successfully updated modules for project {project_id}",
                    }
                    self._logger.info(
                        f"[update_project_modules] Success | project_id={project_id}, modules_updated={list(modules_data.keys())}"
                    )
                    return response

            except ResourceNotFoundError:
                self._logger.warning(
                    f"[update_project_modules] Not found | project_id={project_id}"
                )
                raise MCPError(f"Project {project_id} not found") from None
            except PermissionDeniedError:
                self._logger.warning(
                    f"[update_project_modules] Permission denied | project_id={project_id}"
                )
                raise MCPError("You don't have permission to update project modules") from None
            except AuthenticationError:
                self._logger.warning(
                    f"[update_project_modules] Auth failed | project_id={project_id}"
                )
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[update_project_modules] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[update_project_modules] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        if hasattr(update_project_modules, "__wrapped__"):
            self.update_project_modules = update_project_modules.__wrapped__
        elif hasattr(update_project_modules, "fn"):
            self.update_project_modules = update_project_modules.fn
        else:
            self.update_project_modules = update_project_modules

        # Get project by slug
        @self.mcp.tool(
            name="taiga_get_project_by_slug",
            description="Get project details using its unique slug identifier",
            tags={"projects", "read", "get"},
            annotations={"readOnlyHint": True, "openWorldHint": True},
        )
        async def get_project_by_slug(auth_token: str, slug: str) -> dict[str, Any]:
            """
            Get project details by slug.

            Esta herramienta obtiene los detalles de un proyecto usando su slug
            único en lugar del ID numérico. El slug es una versión amigable
            del nombre del proyecto que aparece en las URLs.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                slug: Slug único del proyecto (ej: "mi-proyecto")

            Returns:
                Dict con los siguientes campos:
                - id: ID del proyecto
                - name: Nombre del proyecto
                - slug: Slug del proyecto
                - description: Descripción del proyecto
                - is_private: Si es privado
                - tags: Lista de etiquetas
                - owner: ID del propietario

            Raises:
                MCPError: Si el proyecto no existe, la autenticación falla, o hay error en la API

            Example:
                >>> project = await taiga_get_project_by_slug(
                ...     auth_token="eyJ0eXAiOi...",
                ...     slug="mi-proyecto-api"
                ... )
                >>> print(project)
                {
                    "id": 123,
                    "name": "Mi Proyecto API",
                    "slug": "mi-proyecto-api",
                    "description": "Proyecto de desarrollo de API",
                    "is_private": True,
                    "tags": ["api", "backend"],
                    "owner": 42
                }
            """
            try:
                self._logger.debug(f"[get_project_by_slug] Starting | slug={slug}")
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    project = await client.get(f"/projects/by_slug?slug={slug}")

                    # Validate response with Pydantic
                    result = ProjectResponse.model_validate(project).model_dump(exclude_none=True)
                    self._logger.info(
                        f"[get_project_by_slug] Success | slug={slug}, project_id={result.get('id')}"
                    )
                    return result
            except ResourceNotFoundError:
                self._logger.warning(f"[get_project_by_slug] Not found | slug={slug}")
                raise MCPError(f"Project with slug '{slug}' not found") from None
            except AuthenticationError:
                self._logger.warning(f"[get_project_by_slug] Auth failed | slug={slug}")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(f"[get_project_by_slug] API error | slug={slug}, error={e!s}")
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[get_project_by_slug] Unexpected error | slug={slug}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.get_project_by_slug = (
            get_project_by_slug.fn if hasattr(get_project_by_slug, "fn") else get_project_by_slug
        )

        # Get project issues stats
        @self.mcp.tool(
            name="taiga_get_project_issues_stats", description="Get issues statistics for a project"
        )
        async def get_project_issues_stats(auth_token: str, project_id: int) -> dict[str, Any]:
            """
            Get issues statistics for a project.

            Esta herramienta obtiene estadísticas detalladas de los issues de un
            proyecto, incluyendo distribución por estado, prioridad, severidad
            y asignación.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto del que obtener estadísticas de issues

            Returns:
                Dict con los siguientes campos:
                - total_issues: Número total de issues
                - opened_issues: Issues abiertos
                - closed_issues: Issues cerrados
                - issues_per_status: Distribución por estado
                - issues_per_priority: Distribución por prioridad
                - issues_per_severity: Distribución por severidad
                - issues_per_assigned_to: Distribución por usuario asignado
                - issues_per_owner: Distribución por creador

            Raises:
                MCPError: Si el proyecto no existe, la autenticación falla, o hay error en la API

            Example:
                >>> stats = await taiga_get_project_issues_stats(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print(stats)
                {
                    "total_issues": 50,
                    "opened_issues": 15,
                    "closed_issues": 35,
                    "issues_per_status": {"New": 5, "In Progress": 10, "Closed": 35},
                    "issues_per_priority": {"High": 10, "Normal": 30, "Low": 10},
                    "issues_per_severity": {"Critical": 5, "Normal": 40, "Minor": 5},
                    "issues_per_assigned_to": {"42": 25, "43": 25},
                    "issues_per_owner": {"42": 30, "43": 20}
                }
            """
            try:
                self._logger.debug(f"[get_project_issues_stats] Starting | project_id={project_id}")
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    stats = await client.get(f"/projects/{project_id}/issues_stats")

                    # Validate response with Pydantic
                    result = ProjectIssuesStatsResponse.model_validate(stats).model_dump(
                        exclude_none=True
                    )
                    total = result.get("total_issues", 0)
                    self._logger.info(
                        f"[get_project_issues_stats] Success | project_id={project_id}, total_issues={total}"
                    )
                    return result
            except ResourceNotFoundError:
                self._logger.warning(
                    f"[get_project_issues_stats] Not found | project_id={project_id}"
                )
                raise MCPError(f"Project {project_id} not found") from None
            except AuthenticationError:
                self._logger.warning(
                    f"[get_project_issues_stats] Auth failed | project_id={project_id}"
                )
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[get_project_issues_stats] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[get_project_issues_stats] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.get_project_issues_stats = (
            get_project_issues_stats.fn
            if hasattr(get_project_issues_stats, "fn")
            else get_project_issues_stats
        )

        # Get project tags
        @self.mcp.tool(
            name="taiga_get_project_tags",
            description="Get all available tags defined in a project",
            tags={"projects", "read", "tags"},
            annotations={"readOnlyHint": True, "openWorldHint": True},
        )
        async def get_project_tags(auth_token: str, project_id: int) -> list[list[str]]:
            """
            Get all tags in a project.

            Esta herramienta obtiene todas las etiquetas definidas en un proyecto,
            incluyendo su nombre y color asociado.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto del que obtener las etiquetas

            Returns:
                Lista de listas con pares [nombre_tag, color], donde:
                - nombre_tag: Nombre de la etiqueta
                - color: Color en formato hexadecimal (ej: "#FF0000")

            Raises:
                MCPError: Si el proyecto no existe, la autenticación falla, o hay error en la API

            Example:
                >>> tags = await taiga_get_project_tags(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print(tags)
                [
                    ["bug", "#FF0000"],
                    ["feature", "#00FF00"],
                    ["documentation", "#0000FF"],
                    ["urgent", "#FFA500"]
                ]
            """
            try:
                self._logger.debug(f"[get_project_tags] Starting | project_id={project_id}")
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    # Get project details which includes tags_colors
                    project = await client.get(f"/projects/{project_id}")

                    # Extract tags from project's tags_colors field
                    tags_colors = project.get("tags_colors", {})
                    if isinstance(tags_colors, dict):
                        result = [[tag, color] for tag, color in tags_colors.items()]
                    elif isinstance(tags_colors, list):
                        result = tags_colors
                    else:
                        result = []
                    self._logger.info(
                        f"[get_project_tags] Success | project_id={project_id}, tag_count={len(result)}"
                    )
                    return result
            except ResourceNotFoundError:
                self._logger.warning(f"[get_project_tags] Not found | project_id={project_id}")
                raise MCPError(f"Project {project_id} not found") from None
            except AuthenticationError:
                self._logger.warning(f"[get_project_tags] Auth failed | project_id={project_id}")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[get_project_tags] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[get_project_tags] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.get_project_tags = (
            get_project_tags.fn if hasattr(get_project_tags, "fn") else get_project_tags
        )

        # Create project tag
        @self.mcp.tool(
            name="taiga_create_project_tag",
            description="Create a new tag in a project with optional color",
            tags={"projects", "write", "tags"},
            annotations={"readOnlyHint": False, "openWorldHint": True},
        )
        async def create_project_tag(
            auth_token: str, project_id: int, tag: str, color: str | None = None
        ) -> list[str]:
            """
            Create a new tag in a project.

            Esta herramienta crea una nueva etiqueta en un proyecto con el nombre
            y color especificados. Las etiquetas se usan para categorizar historias
            de usuario, tareas e issues.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde crear la etiqueta
                tag: Nombre de la nueva etiqueta
                color: Color en formato hexadecimal (default: "#000000")

            Returns:
                Lista con [nombre_tag, color] de la etiqueta creada

            Raises:
                MCPError: Si el proyecto no existe, no hay permisos, o falla la API

            Example:
                >>> result = await taiga_create_project_tag(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     tag="priority-high",
                ...     color="#FF5733"
                ... )
                >>> print(result)
                ["priority-high", "#FF5733"]
            """
            try:
                self._logger.debug(
                    f"[create_project_tag] Starting | project_id={project_id}, tag={tag}"
                )

                tag_data = {"tag": tag, "color": color or "#000000"}

                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {"project_id": project_id, **tag_data}
                validate_input(ProjectTagValidator, validation_data)

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    result = await client.post(f"/projects/{project_id}/create_tag", data=tag_data)

                    # Return as [tag, color] list
                    if isinstance(result, list):
                        self._logger.info(
                            f"[create_project_tag] Success | project_id={project_id}, tag={tag}"
                        )
                        return result
                    self._logger.info(
                        f"[create_project_tag] Success | project_id={project_id}, tag={tag}"
                    )
                    return [tag, color or "#000000"]
            except ValidationError as e:
                self._logger.warning(f"[create_project_tag] Validation error | error={e!s}")
                raise MCPError(str(e)) from e
            except ResourceNotFoundError:
                self._logger.warning(f"[create_project_tag] Not found | project_id={project_id}")
                raise MCPError(f"Project {project_id} not found") from None
            except PermissionDeniedError:
                self._logger.warning(
                    f"[create_project_tag] Permission denied | project_id={project_id}"
                )
                raise MCPError("You don't have permission to create tags") from None
            except AuthenticationError:
                self._logger.warning(f"[create_project_tag] Auth failed | project_id={project_id}")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[create_project_tag] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[create_project_tag] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.create_project_tag = (
            create_project_tag.fn if hasattr(create_project_tag, "fn") else create_project_tag
        )

        # Edit project tag
        @self.mcp.tool(
            name="taiga_edit_project_tag", description="Edit an existing tag in a project"
        )
        async def edit_project_tag(
            auth_token: str, project_id: int, from_tag: str, to_tag: str, color: str | None = None
        ) -> list[str]:
            """
            Edit an existing tag in a project.

            Esta herramienta permite renombrar una etiqueta existente y cambiar
            su color. Todos los elementos que usen la etiqueta original serán
            actualizados automáticamente.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto que contiene la etiqueta
                from_tag: Nombre actual de la etiqueta a editar
                to_tag: Nuevo nombre para la etiqueta
                color: Nuevo color en formato hexadecimal (default: "#000000")

            Returns:
                Lista con [nuevo_nombre_tag, color] de la etiqueta editada

            Raises:
                MCPError: Si el proyecto o etiqueta no existe, no hay permisos, o falla la API

            Example:
                >>> result = await taiga_edit_project_tag(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     from_tag="bug",
                ...     to_tag="defect",
                ...     color="#DC143C"
                ... )
                >>> print(result)
                ["defect", "#DC143C"]
            """
            try:
                self._logger.debug(
                    f"[edit_project_tag] Starting | project_id={project_id}, from_tag={from_tag}, to_tag={to_tag}"
                )

                tag_data = {"from_tag": from_tag, "to_tag": to_tag, "color": color or "#000000"}

                # Validar datos de entrada ANTES de llamar a la API
                validate_input(ProjectTagEditValidator, tag_data)

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    result = await client.post(f"/projects/{project_id}/edit_tag", data=tag_data)

                    # Return as [tag, color] list
                    if isinstance(result, list):
                        self._logger.info(
                            f"[edit_project_tag] Success | project_id={project_id}, from_tag={from_tag}, to_tag={to_tag}"
                        )
                        return result
                    self._logger.info(
                        f"[edit_project_tag] Success | project_id={project_id}, from_tag={from_tag}, to_tag={to_tag}"
                    )
                    return [to_tag, color or "#000000"]
            except ValidationError as e:
                self._logger.warning(f"[edit_project_tag] Validation error | error={e!s}")
                raise MCPError(str(e)) from e
            except ResourceNotFoundError:
                self._logger.warning(f"[edit_project_tag] Not found | project_id={project_id}")
                raise MCPError(f"Project {project_id} not found") from None
            except PermissionDeniedError:
                self._logger.warning(
                    f"[edit_project_tag] Permission denied | project_id={project_id}"
                )
                raise MCPError("You don't have permission to edit tags") from None
            except AuthenticationError:
                self._logger.warning(f"[edit_project_tag] Auth failed | project_id={project_id}")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[edit_project_tag] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[edit_project_tag] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.edit_project_tag = (
            edit_project_tag.fn if hasattr(edit_project_tag, "fn") else edit_project_tag
        )

        # Delete project tag
        @self.mcp.tool(
            name="taiga_delete_project_tag",
            description="Permanently delete a tag from a project",
            tags={"projects", "delete", "tags"},
            annotations={
                "destructiveHint": True,
                "openWorldHint": True,
                "title": "Delete Project Tag",
            },
        )
        async def delete_project_tag(auth_token: str, project_id: int, tag: str) -> bool:
            """
            Delete a tag from a project.

            Esta herramienta elimina una etiqueta del proyecto. La etiqueta será
            removida de todos los elementos que la usen (historias, tareas, issues).

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto que contiene la etiqueta
                tag: Nombre de la etiqueta a eliminar

            Returns:
                True si la eliminación fue exitosa

            Raises:
                MCPError: Si el proyecto no existe, no hay permisos, o falla la API

            Example:
                >>> result = await taiga_delete_project_tag(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     tag="deprecated-tag"
                ... )
                >>> print(result)
                True
            """
            try:
                self._logger.debug(
                    f"[delete_project_tag] Starting | project_id={project_id}, tag={tag}"
                )
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token

                    tag_data = {"tag": tag}

                    await client.post(f"/projects/{project_id}/delete_tag", data=tag_data)

                    self._logger.info(
                        f"[delete_project_tag] Success | project_id={project_id}, tag={tag}"
                    )
                    return True
            except ResourceNotFoundError:
                self._logger.warning(f"[delete_project_tag] Not found | project_id={project_id}")
                raise MCPError(f"Project {project_id} not found") from None
            except PermissionDeniedError:
                self._logger.warning(
                    f"[delete_project_tag] Permission denied | project_id={project_id}"
                )
                raise MCPError("You don't have permission to delete tags") from None
            except AuthenticationError:
                self._logger.warning(f"[delete_project_tag] Auth failed | project_id={project_id}")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[delete_project_tag] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[delete_project_tag] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.delete_project_tag = (
            delete_project_tag.fn if hasattr(delete_project_tag, "fn") else delete_project_tag
        )

        # Mix project tags
        @self.mcp.tool(
            name="taiga_mix_project_tags", description="Mix multiple tags into one in a project"
        )
        async def mix_project_tags(
            auth_token: str, project_id: int, from_tags: list[str], to_tag: str
        ) -> list[str]:
            """
            Mix (merge) multiple tags into one.

            Esta herramienta combina múltiples etiquetas en una sola. Las etiquetas
            originales se eliminarán y todos los elementos que las usaban serán
            actualizados para usar la etiqueta destino.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto que contiene las etiquetas
                from_tags: Lista de nombres de etiquetas a combinar
                to_tag: Nombre de la etiqueta destino (puede existir o ser nueva)

            Returns:
                Lista con [nombre_tag, color] de la etiqueta resultante

            Raises:
                MCPError: Si el proyecto no existe, no hay permisos, o falla la API

            Example:
                >>> result = await taiga_mix_project_tags(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     from_tags=["bug-critical", "bug-major", "bug-minor"],
                ...     to_tag="bug"
                ... )
                >>> print(result)
                ["bug", "#000000"]
            """
            try:
                self._logger.debug(
                    f"[mix_project_tags] Starting | project_id={project_id}, from_tags_count={len(from_tags)}, to_tag={to_tag}"
                )
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token

                    # Send mix request
                    mix_data = {"from_tags": from_tags, "to_tag": to_tag}

                    result = await client.post(f"/projects/{project_id}/mix_tags", data=mix_data)

                    # Return as [tag, color] list
                    if isinstance(result, list):
                        self._logger.info(
                            f"[mix_project_tags] Success | project_id={project_id}, merged_count={len(from_tags)}, to_tag={to_tag}"
                        )
                        return result
                    self._logger.info(
                        f"[mix_project_tags] Success | project_id={project_id}, merged_count={len(from_tags)}, to_tag={to_tag}"
                    )
                    return [to_tag, "#000000"]
            except ResourceNotFoundError:
                self._logger.warning(f"[mix_project_tags] Not found | project_id={project_id}")
                raise MCPError(f"Project {project_id} not found") from None
            except PermissionDeniedError:
                self._logger.warning(
                    f"[mix_project_tags] Permission denied | project_id={project_id}"
                )
                raise MCPError("You don't have permission to mix tags") from None
            except AuthenticationError:
                self._logger.warning(f"[mix_project_tags] Auth failed | project_id={project_id}")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[mix_project_tags] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[mix_project_tags] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.mix_project_tags = (
            mix_project_tags.fn if hasattr(mix_project_tags, "fn") else mix_project_tags
        )

        # Export project
        @self.mcp.tool(
            name="taiga_export_project",
            description="Export all project data for backup or migration",
            tags={"projects", "read", "export"},
            annotations={"readOnlyHint": True, "openWorldHint": True},
        )
        async def export_project(auth_token: str, project_id: int) -> bytes:
            """
            Export project data.

            Esta herramienta exporta todos los datos de un proyecto en formato
            JSON comprimido. Incluye historias de usuario, tareas, issues,
            milestones, wiki y configuración del proyecto.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto a exportar

            Returns:
                Datos del proyecto exportado en bytes (JSON comprimido)

            Raises:
                MCPError: Si el proyecto no existe, no hay permisos, o falla la API

            Example:
                >>> data = await taiga_export_project(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> # Guardar a archivo
                >>> with open("project_backup.json", "wb") as f:
                ...     f.write(data)
            """
            try:
                self._logger.debug(f"[export_project] Starting | project_id={project_id}")
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token

                    # Get export data
                    result = await client.get_raw(f"/exporter/{project_id}")
                    self._logger.info(
                        f"[export_project] Success | project_id={project_id}, size_bytes={len(result) if result else 0}"
                    )
                    return result
            except ResourceNotFoundError:
                self._logger.warning(f"[export_project] Not found | project_id={project_id}")
                raise MCPError(f"Project {project_id} not found") from None
            except PermissionDeniedError:
                self._logger.warning(
                    f"[export_project] Permission denied | project_id={project_id}"
                )
                raise MCPError("You don't have permission to export this project") from None
            except AuthenticationError:
                self._logger.warning(f"[export_project] Auth failed | project_id={project_id}")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[export_project] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[export_project] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.export_project = export_project.fn if hasattr(export_project, "fn") else export_project

        # Bulk update projects order
        @self.mcp.tool(
            name="taiga_bulk_update_projects_order",
            description="Update the order of multiple projects",
        )
        async def bulk_update_projects_order(
            auth_token: str, projects_order: list[list[int]]
        ) -> list[dict[str, Any]]:
            """
            Update the order of multiple projects.

            Esta herramienta permite reordenar múltiples proyectos a la vez,
            definiendo la posición de cada proyecto en la lista del usuario.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                projects_order: Lista de pares [project_id, order] indicando
                    el nuevo orden de cada proyecto

            Returns:
                Lista de diccionarios con el resultado, cada uno conteniendo:
                - id: ID del proyecto
                - order: Nueva posición del proyecto

            Raises:
                MCPError: Si la autenticación falla o hay error en la API

            Example:
                >>> result = await taiga_bulk_update_projects_order(
                ...     auth_token="eyJ0eXAiOi...",
                ...     projects_order=[[123, 1], [456, 2], [789, 3]]
                ... )
                >>> print(result)
                [
                    {"id": 123, "order": 1},
                    {"id": 456, "order": 2},
                    {"id": 789, "order": 3}
                ]
            """
            try:
                self._logger.debug(
                    f"[bulk_update_projects_order] Starting | projects_count={len(projects_order)}"
                )
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token

                    # Send bulk update request
                    order_data = {"bulk_projects": projects_order}

                    result = await client.post("/projects/bulk_update_order", data=order_data)

                    # Return the list of updated projects
                    if isinstance(result, list):
                        self._logger.info(
                            f"[bulk_update_projects_order] Success | projects_count={len(projects_order)}"
                        )
                        return result
                    # Convert projects_order to expected format if API returns success
                    self._logger.info(
                        f"[bulk_update_projects_order] Success | projects_count={len(projects_order)}"
                    )
                    return [{"id": proj[0], "order": proj[1]} for proj in projects_order]
            except AuthenticationError:
                self._logger.warning(
                    f"[bulk_update_projects_order] Auth failed | projects_count={len(projects_order)}"
                )
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[bulk_update_projects_order] API error | projects_count={len(projects_order)}, error={e!s}"
                )
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[bulk_update_projects_order] Unexpected error | projects_count={len(projects_order)}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.bulk_update_projects_order = (
            bulk_update_projects_order.fn
            if hasattr(bulk_update_projects_order, "fn")
            else bulk_update_projects_order
        )
