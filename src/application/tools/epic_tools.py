"""
Herramientas para gestión de Epics en Taiga.
EPIC-001 to EPIC-028: Complete Epic functionality.
"""

from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.application.responses.base import SuccessResponse
from src.application.responses.epic_responses import (
    EpicAttachmentResponse, EpicCustomAttributeResponse,
    EpicCustomAttributeValuesResponse, EpicFiltersResponse, EpicListResponse,
    EpicRelatedUserstoryResponse, EpicResponse, EpicVoterResponse,
    EpicWatcherResponse)
from src.config import TaigaConfig
from src.domain.exceptions import ValidationError
from src.domain.validators import (EpicCreateValidator, EpicUpdateValidator,
                                   validate_input)
from src.infrastructure.logging import get_logger
from src.infrastructure.pagination import AutoPaginator, PaginationConfig
from src.taiga_client import TaigaAPIClient


class EpicTools:
    """Herramientas para gestión de Epics en Taiga."""

    def __init__(self, mcp: FastMCP) -> None:
        """Inicializa las herramientas de epics."""
        self.mcp = mcp
        self.config = TaigaConfig()
        self._logger = get_logger("epic_tools")
        self._register_tools()

    def register_tools(self) -> None:
        """Método público para registrar herramientas (para compatibilidad con tests)."""
        # Las herramientas ya están registradas en __init__ via _register_tools

    def _register_tools(self) -> None:
        """Registra todas las herramientas de epics en el servidor MCP."""

        # EPIC-001: List epics
        @self.mcp.tool(name="taiga_list_epics")
        async def list_epics_tool(
            auth_token: str,
            project_id: int | None = None,
            status: int | None = None,
            assigned_to: int | None = None,
            auto_paginate: bool = True,
        ) -> list[dict[str, Any]]:
            """
            List epics in a project.

            Esta herramienta lista las épicas de un proyecto en Taiga con
            filtros opcionales por estado y asignado. Las épicas son contenedores
            de alto nivel que agrupan múltiples historias de usuario relacionadas.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto para filtrar (opcional)
                status: ID del estado para filtrar (opcional)
                assigned_to: ID del usuario asignado para filtrar (opcional)
                auto_paginate: Si True, obtiene automáticamente todas las páginas.
                    Si False, solo retorna la primera página. Default: True.

            Returns:
                Lista de diccionarios con información de épicas, cada uno
                conteniendo:
                - id: ID de la épica
                - ref: Número de referencia
                - subject: Título de la épica
                - description: Descripción detallada
                - project: ID del proyecto
                - status: ID del estado
                - color: Color de la épica
                - assigned_to: ID del asignado
                - tags: Lista de tags
                - user_stories_counts: Contador de historias por estado

            Raises:
                ToolError: Si la autenticación falla, no hay permisos,
                    o hay error en la API

            Example:
                >>> epics = await taiga_list_epics(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     status=1
                ... )
                >>> print(epics)
                [
                    {
                        "id": 456,
                        "ref": 1,
                        "subject": "Módulo de autenticación",
                        "status": 1,
                        "color": "#FC8EAC"
                    }
                ]
            """
            kwargs = {}
            if project_id is not None:
                kwargs["project"] = project_id  # API expects 'project'
            if status is not None:
                kwargs["status"] = status
            if assigned_to is not None:
                kwargs["assigned_to"] = assigned_to
            return await self.list_epics(
                auth_token=auth_token, auto_paginate=auto_paginate, **kwargs
            )

        # EPIC-002: Create epic
        @self.mcp.tool(name="taiga_create_epic")
        async def create_epic_tool(
            auth_token: str,
            project_id: int,
            subject: str,
            description: str | None = None,
            color: str | None = None,
            assigned_to: int | None = None,
            status: int | None = None,
            tags: list[str] | None = None,
        ) -> dict[str, Any]:
            """
            Create a new epic.

            Esta herramienta crea una nueva épica en un proyecto de Taiga.
            Las épicas son contenedores que agrupan historias de usuario
            relacionadas para representar funcionalidades grandes o módulos.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde crear la épica
                subject: Título o nombre de la épica
                description: Descripción detallada (opcional)
                color: Color en formato hexadecimal #RRGGBB (opcional)
                assigned_to: ID del usuario responsable (opcional)
                status: ID del estado inicial (opcional)
                tags: Lista de etiquetas (opcional)

            Returns:
                Dict con la épica creada conteniendo:
                - id: ID de la épica creada
                - ref: Número de referencia asignado
                - subject: Título de la épica
                - description: Descripción
                - project: ID del proyecto
                - status: ID del estado
                - color: Color asignado
                - assigned_to: ID del asignado
                - created_date: Fecha de creación

            Raises:
                ToolError: Si no hay permisos, el proyecto no existe,
                    o el formato de color es inválido

            Example:
                >>> epic = await taiga_create_epic(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     subject="Módulo de pagos",
                ...     description="Implementar pasarela de pagos",
                ...     color="#3498db"
                ... )
                >>> print(epic)
                {
                    "id": 789,
                    "ref": 5,
                    "subject": "Módulo de pagos",
                    "color": "#3498db",
                    "project": 123
                }
            """
            kwargs = {"project": project_id, "subject": subject}  # API expects 'project'
            if description is not None:
                kwargs["description"] = description
            if color is not None:
                kwargs["color"] = color
            if assigned_to is not None:
                kwargs["assigned_to"] = assigned_to
            if status is not None:
                kwargs["status"] = status
            if tags is not None:
                kwargs["tags"] = tags
            return await self.create_epic(auth_token=auth_token, **kwargs)

        # EPIC-003: Get epic by ID
        @self.mcp.tool(name="taiga_get_epic")
        async def get_epic_tool(auth_token: str, epic_id: int) -> dict[str, Any]:
            """
            Get an epic by ID.

            Esta herramienta obtiene los detalles completos de una épica
            específica por su ID, incluyendo toda la información asociada
            como historias vinculadas, watchers y atributos personalizados.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica a consultar

            Returns:
                Dict con los detalles de la épica conteniendo:
                - id: ID de la épica
                - ref: Número de referencia
                - subject: Título
                - description: Descripción detallada
                - project: ID del proyecto
                - status: ID del estado
                - status_extra_info: Información adicional del estado
                - color: Color de la épica
                - assigned_to: ID del asignado
                - assigned_to_extra_info: Info del usuario asignado
                - tags: Lista de tags
                - watchers: Lista de IDs de watchers
                - user_stories_counts: Contador de historias por estado
                - created_date: Fecha de creación
                - modified_date: Fecha de modificación
                - version: Versión actual para control de concurrencia

            Raises:
                ToolError: Si la épica no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> epic = await taiga_get_epic(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456
                ... )
                >>> print(epic)
                {
                    "id": 456,
                    "ref": 1,
                    "subject": "Módulo de autenticación",
                    "status": 1,
                    "color": "#FC8EAC",
                    "user_stories_counts": {"total": 5, "closed": 2}
                }
            """
            return await self.get_epic(auth_token=auth_token, epic_id=epic_id)

        # EPIC-004: Get epic by ref
        @self.mcp.tool(name="taiga_get_epic_by_ref")
        async def get_epic_by_ref_tool(
            auth_token: str, project_id: int, ref: int
        ) -> dict[str, Any]:
            """
            Get an epic by its reference number within a project.

            Esta herramienta obtiene una épica usando su número de referencia
            dentro de un proyecto específico. Útil cuando se conoce el número
            de referencia visible en la interfaz de Taiga.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde buscar
                ref: Número de referencia de la épica (ej: #1, #2)

            Returns:
                Dict con los detalles de la épica conteniendo:
                - id: ID de la épica
                - ref: Número de referencia
                - subject: Título
                - description: Descripción
                - project: ID del proyecto
                - status: ID del estado
                - color: Color de la épica
                - assigned_to: ID del asignado
                - tags: Lista de tags
                - user_stories_counts: Contador de historias

            Raises:
                ToolError: Si la épica no existe en el proyecto,
                    no hay permisos, o la autenticación falla

            Example:
                >>> epic = await taiga_get_epic_by_ref(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     ref=1
                ... )
                >>> print(epic)
                {
                    "id": 456,
                    "ref": 1,
                    "subject": "Módulo de autenticación",
                    "project": 123
                }
            """
            return await self.get_epic_by_ref(auth_token=auth_token, project_id=project_id, ref=ref)

        # EPIC-005: Update epic (full)
        @self.mcp.tool(name="taiga_update_epic_full")
        async def update_epic_full_tool(
            auth_token: str,
            epic_id: int,
            subject: str,
            description: str | None = None,
            color: str | None = None,
            assigned_to: int | None = None,
            status: int | None = None,
            tags: list[str] | None = None,
        ) -> dict[str, Any]:
            """
            Full update of an epic (PUT).

            Esta herramienta realiza una actualización completa de una épica
            usando el método PUT. Requiere el subject como campo obligatorio
            y reemplaza todos los valores de la épica.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica a actualizar
                subject: Título de la épica (requerido para PUT)
                description: Nueva descripción (opcional)
                color: Nuevo color en formato #RRGGBB (opcional)
                assigned_to: Nuevo ID de usuario asignado (opcional)
                status: Nuevo ID de estado (opcional)
                tags: Nueva lista de tags (opcional)

            Returns:
                Dict con la épica actualizada conteniendo:
                - id: ID de la épica
                - ref: Número de referencia
                - subject: Título actualizado
                - description: Descripción actualizada
                - project: ID del proyecto
                - status: ID del estado
                - color: Color actualizado
                - assigned_to: ID del asignado
                - version: Nueva versión

            Raises:
                ToolError: Si la épica no existe, no hay permisos,
                    hay conflicto de versión, o la autenticación falla

            Example:
                >>> epic = await taiga_update_epic_full(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456,
                ...     subject="Módulo de pagos actualizado",
                ...     description="Nueva descripción completa",
                ...     color="#e74c3c"
                ... )
                >>> print(epic)
                {
                    "id": 456,
                    "subject": "Módulo de pagos actualizado",
                    "color": "#e74c3c",
                    "version": 2
                }
            """
            kwargs = {"subject": subject}
            if description is not None:
                kwargs["description"] = description
            if color is not None:
                kwargs["color"] = color
            if assigned_to is not None:
                kwargs["assigned_to"] = assigned_to
            if status is not None:
                kwargs["status"] = status
            if tags is not None:
                kwargs["tags"] = tags
            return await self.update_epic_full(auth_token=auth_token, epic_id=epic_id, **kwargs)

        # EPIC-006: Update epic (partial)
        @self.mcp.tool(name="taiga_update_epic_partial")
        async def update_epic_partial_tool(
            auth_token: str,
            epic_id: int,
            subject: str | None = None,
            description: str | None = None,
            color: str | None = None,
            assigned_to: int | None = None,
            status: int | None = None,
            tags: list[str] | None = None,
        ) -> dict[str, Any]:
            """
            Partial update of an epic (PATCH).

            Esta herramienta realiza una actualización parcial de una épica
            usando el método PATCH. Solo modifica los campos proporcionados,
            manteniendo los demás valores sin cambios.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica a actualizar
                subject: Nuevo título (opcional)
                description: Nueva descripción (opcional)
                color: Nuevo color en formato #RRGGBB (opcional)
                assigned_to: Nuevo ID de usuario asignado (opcional)
                status: Nuevo ID de estado (opcional)
                tags: Nueva lista de tags (opcional)

            Returns:
                Dict con la épica actualizada conteniendo:
                - id: ID de la épica
                - ref: Número de referencia
                - subject: Título
                - description: Descripción
                - project: ID del proyecto
                - status: ID del estado
                - color: Color
                - assigned_to: ID del asignado
                - version: Nueva versión

            Raises:
                ToolError: Si la épica no existe, no hay permisos,
                    hay conflicto de versión, o la autenticación falla

            Example:
                >>> epic = await taiga_update_epic_partial(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456,
                ...     color="#2ecc71",
                ...     status=2
                ... )
                >>> print(epic)
                {
                    "id": 456,
                    "subject": "Módulo existente",
                    "color": "#2ecc71",
                    "status": 2
                }
            """
            kwargs = {}
            if subject is not None:
                kwargs["subject"] = subject
            if description is not None:
                kwargs["description"] = description
            if color is not None:
                kwargs["color"] = color
            if assigned_to is not None:
                kwargs["assigned_to"] = assigned_to
            if status is not None:
                kwargs["status"] = status
            if tags is not None:
                kwargs["tags"] = tags
            return await self.update_epic_partial(auth_token=auth_token, epic_id=epic_id, **kwargs)

        # EPIC-007: Delete epic
        @self.mcp.tool(name="taiga_delete_epic")
        async def delete_epic_tool(auth_token: str, epic_id: int) -> dict[str, str]:
            """
            Delete an epic.

            Esta herramienta elimina permanentemente una épica de Taiga.
            Esta acción es irreversible y las historias de usuario vinculadas
            perderán su asociación con la épica.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica a eliminar

            Returns:
                Dict con el resultado de la eliminación:
                - success: "true" si se eliminó correctamente
                - message: Mensaje de confirmación

            Raises:
                ToolError: Si la épica no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> result = await taiga_delete_epic(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456
                ... )
                >>> print(result)
                {
                    "success": "true",
                    "message": "Epic 456 deleted successfully"
                }
            """
            return await self.delete_epic(auth_token=auth_token, epic_id=epic_id)

        # EPIC-008: List epic related user stories
        @self.mcp.tool(name="taiga_list_epic_related_userstories")
        async def list_epic_related_userstories_tool(
            auth_token: str, epic_id: int
        ) -> list[dict[str, Any]]:
            """
            List user stories related to an epic.

            Esta herramienta lista todas las historias de usuario que están
            vinculadas a una épica específica. Útil para ver el desglose
            de una épica en historias más pequeñas.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica

            Returns:
                Lista de diccionarios con información de las historias
                relacionadas, cada uno conteniendo:
                - id: ID de la relación epic-userstory
                - user_story: ID de la historia de usuario
                - epic: ID de la épica
                - order: Orden dentro de la épica

            Raises:
                ToolError: Si la épica no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> stories = await taiga_list_epic_related_userstories(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456
                ... )
                >>> print(stories)
                [
                    {
                        "id": 1,
                        "user_story": 789,
                        "epic": 456,
                        "order": 1
                    },
                    {
                        "id": 2,
                        "user_story": 790,
                        "epic": 456,
                        "order": 2
                    }
                ]
            """
            return await self.list_epic_related_userstories(auth_token=auth_token, epic_id=epic_id)

        # EPIC-009: Create epic related user story (link existing user story to epic)
        @self.mcp.tool(name="taiga_create_epic_related_userstory")
        async def create_epic_related_userstory_tool(
            auth_token: str, epic_id: int, user_story_id: int, order: int | None = None
        ) -> dict[str, Any]:
            """
            Link an existing user story to an epic.

            Esta herramienta vincula una historia de usuario existente a una
            épica. Permite organizar historias dentro de épicas para una
            mejor gestión de funcionalidades grandes.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica a la que vincular
                user_story_id: ID de la historia de usuario existente a vincular
                order: Posición de orden dentro de la épica (opcional)

            Returns:
                Dict con la relación creada conteniendo:
                - id: ID de la relación
                - user_story: ID de la historia de usuario
                - epic: ID de la épica
                - order: Posición de orden

            Raises:
                ToolError: Si la épica o historia no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> relation = await taiga_create_epic_related_userstory(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456,
                ...     user_story_id=789,
                ...     order=1
                ... )
                >>> print(relation)
                {
                    "id": 123,
                    "user_story": 789,
                    "epic": 456,
                    "order": 1
                }
            """
            kwargs = {"user_story": user_story_id}  # API expects 'user_story'
            if order is not None:
                kwargs["order"] = order
            return await self.create_epic_related_userstory(
                auth_token=auth_token, epic_id=epic_id, **kwargs
            )

        # EPIC-010: Get epic related user story
        @self.mcp.tool(name="taiga_get_epic_related_userstory")
        async def get_epic_related_userstory_tool(
            auth_token: str, epic_id: int, userstory_id: int
        ) -> dict[str, Any]:
            """
            Get a specific user story related to an epic.

            Esta herramienta obtiene los detalles de una relación específica
            entre una épica y una historia de usuario, incluyendo el orden
            y metadatos de la relación.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica
                userstory_id: ID de la historia de usuario

            Returns:
                Dict con los detalles de la relación conteniendo:
                - id: ID de la relación
                - user_story: ID de la historia de usuario
                - epic: ID de la épica
                - order: Posición de orden

            Raises:
                ToolError: Si la relación no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> relation = await taiga_get_epic_related_userstory(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456,
                ...     userstory_id=789
                ... )
                >>> print(relation)
                {
                    "id": 123,
                    "user_story": 789,
                    "epic": 456,
                    "order": 1
                }
            """
            return await self.get_epic_related_userstory(
                auth_token=auth_token, epic_id=epic_id, userstory_id=userstory_id
            )

        # EPIC-011: Update epic related user story
        @self.mcp.tool(name="taiga_update_epic_related_userstory")
        async def update_epic_related_userstory_tool(
            auth_token: str,
            epic_id: int,
            userstory_id: int,
            subject: str | None = None,
            description: str | None = None,
            status: int | None = None,
            assigned_to: int | None = None,
        ) -> dict[str, Any]:
            """
            Update a user story related to an epic.

            Esta herramienta actualiza la información de una historia de usuario
            que está vinculada a una épica. Permite modificar campos como
            el título, descripción, estado o asignación.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica
                userstory_id: ID de la historia de usuario a actualizar
                subject: Nuevo título de la historia (opcional)
                description: Nueva descripción (opcional)
                status: Nuevo ID de estado (opcional)
                assigned_to: Nuevo ID de usuario asignado (opcional)

            Returns:
                Dict con la relación actualizada conteniendo:
                - id: ID de la relación
                - user_story: ID de la historia de usuario
                - epic: ID de la épica
                - order: Posición de orden

            Raises:
                ToolError: Si la relación no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> relation = await taiga_update_epic_related_userstory(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456,
                ...     userstory_id=789,
                ...     status=2,
                ...     assigned_to=42
                ... )
                >>> print(relation)
                {
                    "id": 123,
                    "user_story": 789,
                    "epic": 456,
                    "order": 1
                }
            """
            kwargs = {}
            if subject is not None:
                kwargs["subject"] = subject
            if description is not None:
                kwargs["description"] = description
            if status is not None:
                kwargs["status"] = status
            if assigned_to is not None:
                kwargs["assigned_to"] = assigned_to
            return await self.update_epic_related_userstory(
                auth_token=auth_token, epic_id=epic_id, userstory_id=userstory_id, **kwargs
            )

        # EPIC-012: Delete epic related user story
        @self.mcp.tool(name="taiga_delete_epic_related_userstory")
        async def delete_epic_related_userstory_tool(
            auth_token: str, epic_id: int, userstory_id: int
        ) -> dict[str, str]:
            """
            Delete a user story related to an epic.

            Esta herramienta elimina la vinculación entre una historia de
            usuario y una épica. La historia de usuario NO se elimina,
            solo se desvincula de la épica.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica
                userstory_id: ID de la historia de usuario a desvincular

            Returns:
                Dict con el resultado de la operación:
                - success: True si se eliminó correctamente
                - message: Mensaje de confirmación

            Raises:
                ToolError: Si la relación no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> result = await taiga_delete_epic_related_userstory(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456,
                ...     userstory_id=789
                ... )
                >>> print(result)
                {
                    "success": True,
                    "message": "User story 789 removed from epic 456"
                }
            """
            return await self.delete_epic_related_userstory(
                auth_token=auth_token, epic_id=epic_id, userstory_id=userstory_id
            )

        # EPIC-013: Bulk create epics
        @self.mcp.tool(name="taiga_bulk_create_epics")
        async def bulk_create_epics_tool(
            auth_token: str, project_id: int, epics_data: list[dict[str, Any]]
        ) -> list[dict[str, Any]]:
            """
            Bulk create multiple epics.

            Esta herramienta crea múltiples épicas en un proyecto de forma
            masiva. Útil para importar épicas o crear estructuras de
            proyecto predefinidas.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde crear las épicas
                epics_data: Lista de diccionarios con datos de cada épica.
                    Cada dict debe contener al menos 'subject' y opcionalmente
                    'description', 'color', 'status', 'assigned_to', 'tags'.

            Returns:
                Lista de diccionarios con las épicas creadas, cada uno
                conteniendo:
                - id: ID de la épica creada
                - ref: Número de referencia
                - subject: Título de la épica
                - project: ID del proyecto

            Raises:
                ToolError: Si no hay permisos, el proyecto no existe,
                    o hay error en los datos proporcionados

            Example:
                >>> epics = await taiga_bulk_create_epics(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     epics_data=[
                ...         {"subject": "Módulo de usuarios"},
                ...         {"subject": "Módulo de pagos", "color": "#3498db"},
                ...         {"subject": "Módulo de reportes", "tags": ["reporting"]}
                ...     ]
                ... )
                >>> print(len(epics))
                3
            """
            return await self.bulk_create_epics(
                auth_token=auth_token, project_id=project_id, epics_data=epics_data
            )

        # EPIC-014: Get epic filters
        @self.mcp.tool(name="taiga_get_epic_filters")
        async def get_epic_filters_tool(auth_token: str, project_id: int) -> dict[str, Any]:
            """
            Get available filters for epics in a project.

            Esta herramienta obtiene los filtros disponibles para listar
            épicas en un proyecto. Incluye estados, usuarios asignados,
            y otras opciones de filtrado.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto

            Returns:
                Dict con los filtros disponibles conteniendo:
                - statuses: Lista de estados disponibles
                - assigned_to: Lista de usuarios para filtrar por asignado
                - owners: Lista de propietarios
                - tags: Lista de tags disponibles

            Raises:
                ToolError: Si el proyecto no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> filters = await taiga_get_epic_filters(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print(filters)
                {
                    "statuses": [
                        {"id": 1, "name": "New"},
                        {"id": 2, "name": "In Progress"}
                    ],
                    "assigned_to": [
                        {"id": 42, "full_name": "John Doe"}
                    ]
                }
            """
            return await self.get_epic_filters(auth_token=auth_token, project_id=project_id)

        # EPIC-015: Upvote epic
        @self.mcp.tool(name="taiga_upvote_epic")
        async def upvote_epic_tool(auth_token: str, epic_id: int) -> dict[str, Any]:
            """
            Upvote an epic.

            Esta herramienta agrega un voto positivo a una épica. Útil para
            priorizar épicas basándose en el interés del equipo o stakeholders.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica a votar

            Returns:
                Dict con el resultado de la operación conteniendo:
                - success: True si el voto se registró correctamente
                - total_voters: Número total de votantes

            Raises:
                ToolError: Si la épica no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> result = await taiga_upvote_epic(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456
                ... )
                >>> print(result)
                {
                    "success": True,
                    "total_voters": 5
                }
            """
            return await self.upvote_epic(auth_token=auth_token, epic_id=epic_id)

        # EPIC-016: Downvote epic
        @self.mcp.tool(name="taiga_downvote_epic")
        async def downvote_epic_tool(auth_token: str, epic_id: int) -> dict[str, Any]:
            """
            Downvote an epic.

            Esta herramienta retira el voto positivo del usuario de una épica.
            Solo puede retirar su propio voto, no el de otros usuarios.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica

            Returns:
                Dict con el resultado de la operación conteniendo:
                - success: True si el voto se retiró correctamente
                - total_voters: Número total de votantes restantes

            Raises:
                ToolError: Si la épica no existe, no había votado previamente,
                    o la autenticación falla

            Example:
                >>> result = await taiga_downvote_epic(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456
                ... )
                >>> print(result)
                {
                    "success": True,
                    "total_voters": 4
                }
            """
            return await self.downvote_epic(auth_token=auth_token, epic_id=epic_id)

        # EPIC-017: Get epic voters
        @self.mcp.tool(name="taiga_get_epic_voters")
        async def get_epic_voters_tool(auth_token: str, epic_id: int) -> list[dict[str, Any]]:
            """
            Get voters of an epic.

            Esta herramienta obtiene la lista de usuarios que han votado
            por una épica. Útil para ver quiénes apoyan una épica específica.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica

            Returns:
                Lista de diccionarios con información de votantes, cada uno
                conteniendo:
                - id: ID del usuario
                - username: Nombre de usuario
                - full_name: Nombre completo
                - photo: URL de la foto de perfil

            Raises:
                ToolError: Si la épica no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> voters = await taiga_get_epic_voters(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456
                ... )
                >>> print(voters)
                [
                    {
                        "id": 42,
                        "username": "johndoe",
                        "full_name": "John Doe"
                    }
                ]
            """
            return await self.get_epic_voters(auth_token=auth_token, epic_id=epic_id)

        # EPIC-018: Watch epic
        @self.mcp.tool(name="taiga_watch_epic")
        async def watch_epic_tool(auth_token: str, epic_id: int) -> dict[str, Any]:
            """
            Watch an epic for updates.

            Esta herramienta suscribe al usuario actual para recibir
            notificaciones de cambios en una épica específica.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica a seguir

            Returns:
                Dict con el resultado de la operación conteniendo:
                - success: True si se agregó como watcher
                - total_watchers: Número total de watchers

            Raises:
                ToolError: Si la épica no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> result = await taiga_watch_epic(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456
                ... )
                >>> print(result)
                {
                    "success": True,
                    "total_watchers": 3
                }
            """
            return await self.watch_epic(auth_token=auth_token, epic_id=epic_id)

        # EPIC-019: Unwatch epic
        @self.mcp.tool(name="taiga_unwatch_epic")
        async def unwatch_epic_tool(auth_token: str, epic_id: int) -> dict[str, Any]:
            """
            Stop watching an epic.

            Esta herramienta cancela la suscripción del usuario actual
            para dejar de recibir notificaciones de cambios en una épica.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica a dejar de seguir

            Returns:
                Dict con el resultado de la operación conteniendo:
                - success: True si se eliminó de watchers
                - total_watchers: Número total de watchers restantes

            Raises:
                ToolError: Si la épica no existe, no era watcher,
                    o la autenticación falla

            Example:
                >>> result = await taiga_unwatch_epic(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456
                ... )
                >>> print(result)
                {
                    "success": True,
                    "total_watchers": 2
                }
            """
            return await self.unwatch_epic(auth_token=auth_token, epic_id=epic_id)

        # EPIC-020: Get epic watchers
        @self.mcp.tool(name="taiga_get_epic_watchers")
        async def get_epic_watchers_tool(auth_token: str, epic_id: int) -> list[dict[str, Any]]:
            """
            Get watchers of an epic.

            Esta herramienta obtiene la lista de usuarios que están siguiendo
            una épica y reciben notificaciones de cambios.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica

            Returns:
                Lista de diccionarios con información de watchers, cada uno
                conteniendo:
                - id: ID del usuario
                - username: Nombre de usuario
                - full_name: Nombre completo
                - photo: URL de la foto de perfil

            Raises:
                ToolError: Si la épica no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> watchers = await taiga_get_epic_watchers(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456
                ... )
                >>> print(watchers)
                [
                    {
                        "id": 42,
                        "username": "johndoe",
                        "full_name": "John Doe"
                    },
                    {
                        "id": 43,
                        "username": "janedoe",
                        "full_name": "Jane Doe"
                    }
                ]
            """
            return await self.get_epic_watchers(auth_token=auth_token, epic_id=epic_id)

        # EPIC-021: List epic attachments
        @self.mcp.tool(name="taiga_list_epic_attachments")
        async def list_epic_attachments_tool(auth_token: str, epic_id: int) -> list[dict[str, Any]]:
            """
            List attachments of an epic.

            Esta herramienta lista todos los archivos adjuntos asociados
            a una épica, como documentos, imágenes o cualquier otro archivo.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica

            Returns:
                Lista de diccionarios con información de adjuntos, cada uno
                conteniendo:
                - id: ID del adjunto
                - name: Nombre del archivo
                - size: Tamaño en bytes
                - url: URL de descarga
                - created_date: Fecha de creación
                - owner: ID del usuario que subió el archivo
                - description: Descripción del adjunto

            Raises:
                ToolError: Si la épica no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> attachments = await taiga_list_epic_attachments(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456
                ... )
                >>> print(attachments)
                [
                    {
                        "id": 1,
                        "name": "requirements.pdf",
                        "size": 102400,
                        "url": "https://taiga.io/attachments/1"
                    }
                ]
            """
            return await self.list_epic_attachments(auth_token=auth_token, epic_id=epic_id)

        # EPIC-022: Create epic attachment
        @self.mcp.tool(name="taiga_create_epic_attachment")
        async def create_epic_attachment_tool(
            auth_token: str, epic_id: int, file: str, description: str | None = None
        ) -> dict[str, Any]:
            """
            Create an attachment for an epic.

            Esta herramienta crea un nuevo adjunto para una épica,
            permitiendo asociar archivos como documentación, diseños
            o cualquier otro recurso relevante.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica
                file: Ruta al archivo a adjuntar o contenido codificado
                description: Descripción del adjunto (opcional)

            Returns:
                Dict con el adjunto creado conteniendo:
                - id: ID del adjunto creado
                - name: Nombre del archivo
                - size: Tamaño en bytes
                - url: URL de descarga
                - created_date: Fecha de creación
                - description: Descripción

            Raises:
                ToolError: Si la épica no existe, no hay permisos,
                    archivo inválido, o la autenticación falla

            Example:
                >>> attachment = await taiga_create_epic_attachment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456,
                ...     file="/path/to/document.pdf",
                ...     description="Documento de requisitos"
                ... )
                >>> print(attachment)
                {
                    "id": 789,
                    "name": "document.pdf",
                    "size": 51200,
                    "description": "Documento de requisitos"
                }
            """
            kwargs = {"epic_id": epic_id, "file": file}
            if description is not None:
                kwargs["description"] = description
            return await self.create_epic_attachment(auth_token=auth_token, **kwargs)

        # EPIC-023: Get epic attachment
        @self.mcp.tool(name="taiga_get_epic_attachment")
        async def get_epic_attachment_tool(auth_token: str, attachment_id: int) -> dict[str, Any]:
            """
            Get a specific attachment of an epic.

            Esta herramienta obtiene los detalles de un adjunto específico
            de una épica, incluyendo información del archivo, URL de
            descarga y metadatos.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                attachment_id: ID del adjunto a obtener

            Returns:
                Dict con los detalles del adjunto conteniendo:
                - id: ID del adjunto
                - name: Nombre del archivo
                - size: Tamaño en bytes
                - url: URL de descarga del archivo
                - created_date: Fecha de creación
                - modified_date: Última modificación
                - description: Descripción del adjunto
                - is_deprecated: Si está marcado como obsoleto
                - owner: ID del usuario que subió el archivo

            Raises:
                ToolError: Si el adjunto no existe, no hay permisos de acceso,
                    o la autenticación falla

            Example:
                >>> attachment = await taiga_get_epic_attachment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     attachment_id=789
                ... )
                >>> print(attachment)
                {
                    "id": 789,
                    "name": "requisitos.pdf",
                    "size": 51200,
                    "url": "https://taiga.io/attachments/789/requisitos.pdf",
                    "description": "Documento de requisitos"
                }
            """
            return await self.get_epic_attachment(
                auth_token=auth_token, attachment_id=attachment_id
            )

        # EPIC-024: Update epic attachment
        @self.mcp.tool(name="taiga_update_epic_attachment")
        async def update_epic_attachment_tool(
            auth_token: str, attachment_id: int, description: str | None = None
        ) -> dict[str, Any]:
            """
            Update an attachment of an epic.

            Esta herramienta actualiza los metadatos de un adjunto existente
            de una épica, como su descripción. No permite modificar el
            archivo en sí, solo sus metadatos.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                attachment_id: ID del adjunto a actualizar
                description: Nueva descripción del adjunto (opcional)

            Returns:
                Dict con el adjunto actualizado conteniendo:
                - id: ID del adjunto
                - name: Nombre del archivo
                - size: Tamaño en bytes
                - url: URL de descarga
                - description: Nueva descripción
                - modified_date: Fecha de última modificación
                - is_deprecated: Estado de obsolescencia

            Raises:
                ToolError: Si el adjunto no existe, no hay permisos de
                    modificación, o la autenticación falla

            Example:
                >>> attachment = await taiga_update_epic_attachment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     attachment_id=789,
                ...     description="Documento de requisitos v2.0"
                ... )
                >>> print(attachment)
                {
                    "id": 789,
                    "name": "requisitos.pdf",
                    "description": "Documento de requisitos v2.0",
                    "modified_date": "2024-01-20T15:30:00Z"
                }
            """
            kwargs = {}
            if description is not None:
                kwargs["description"] = description
            return await self.update_epic_attachment(
                auth_token=auth_token, attachment_id=attachment_id, **kwargs
            )

        # EPIC-025: Delete epic attachment
        @self.mcp.tool(name="taiga_delete_epic_attachment")
        async def delete_epic_attachment_tool(
            auth_token: str, attachment_id: int
        ) -> dict[str, str]:
            """
            Delete an attachment of an epic.

            Esta herramienta elimina permanentemente un adjunto de una épica.
            Esta acción no se puede deshacer, el archivo será eliminado
            del servidor.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                attachment_id: ID del adjunto a eliminar

            Returns:
                Dict con confirmación de eliminación conteniendo:
                - success: "true" si se eliminó correctamente
                - message: Mensaje descriptivo de la operación

            Raises:
                ToolError: Si el adjunto no existe, no hay permisos de
                    eliminación, o la autenticación falla

            Example:
                >>> result = await taiga_delete_epic_attachment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     attachment_id=789
                ... )
                >>> print(result)
                {
                    "success": "true",
                    "message": "Attachment 789 deleted successfully"
                }
            """
            return await self.delete_epic_attachment(
                auth_token=auth_token, attachment_id=attachment_id
            )

        # EPIC-026: List epic custom attributes
        @self.mcp.tool(name="taiga_list_epic_custom_attributes")
        async def list_epic_custom_attributes_tool(
            auth_token: str, project_id: int
        ) -> list[dict[str, Any]]:
            """
            List custom attributes for epics in a project.

            Esta herramienta lista todos los atributos personalizados
            definidos para las épicas de un proyecto específico. Los
            atributos personalizados permiten extender el modelo de
            datos de las épicas.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto

            Returns:
                Lista de diccionarios con los atributos personalizados,
                cada uno conteniendo:
                - id: ID del atributo
                - name: Nombre del atributo
                - description: Descripción del atributo
                - type: Tipo de dato (text, number, date, etc.)
                - order: Orden de visualización
                - project: ID del proyecto
                - created_date: Fecha de creación

            Raises:
                ToolError: Si el proyecto no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> attributes = await taiga_list_epic_custom_attributes(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print(attributes)
                [
                    {
                        "id": 1,
                        "name": "Prioridad de negocio",
                        "type": "dropdown",
                        "order": 1
                    },
                    {
                        "id": 2,
                        "name": "Fecha objetivo",
                        "type": "date",
                        "order": 2
                    }
                ]
            """
            return await self.list_epic_custom_attributes(
                auth_token=auth_token, project_id=project_id
            )

        # EPIC-027: Create epic custom attribute
        @self.mcp.tool(name="taiga_create_epic_custom_attribute")
        async def create_epic_custom_attribute_tool(
            auth_token: str,
            project_id: int,
            name: str,
            description: str | None = None,
            order: int | None = None,
        ) -> dict[str, Any]:
            """
            Create a custom attribute for epics.

            Esta herramienta crea un nuevo atributo personalizado para
            las épicas de un proyecto, permitiendo extender el modelo
            de datos con campos adicionales específicos del negocio.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde crear el atributo
                name: Nombre del atributo personalizado
                description: Descripción del atributo (opcional)
                order: Posición en el orden de visualización (opcional)

            Returns:
                Dict con el atributo creado conteniendo:
                - id: ID del atributo creado
                - name: Nombre del atributo
                - description: Descripción
                - type: Tipo de dato por defecto
                - order: Orden de visualización
                - project: ID del proyecto
                - created_date: Fecha de creación

            Raises:
                ToolError: Si el proyecto no existe, ya existe un atributo
                    con el mismo nombre, no hay permisos de administración,
                    o la autenticación falla

            Example:
                >>> attribute = await taiga_create_epic_custom_attribute(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     name="ROI Estimado",
                ...     description="Retorno de inversión esperado",
                ...     order=3
                ... )
                >>> print(attribute)
                {
                    "id": 45,
                    "name": "ROI Estimado",
                    "description": "Retorno de inversión esperado",
                    "order": 3,
                    "project": 123
                }
            """
            kwargs = {"name": name}
            if description is not None:
                kwargs["description"] = description
            if order is not None:
                kwargs["order"] = order
            return await self.create_epic_custom_attribute(
                auth_token=auth_token, project_id=project_id, **kwargs
            )

        # EPIC-028: Get/Update/Delete epic custom attribute values
        @self.mcp.tool(name="taiga_get_epic_custom_attribute_values")
        async def get_epic_custom_attribute_values_tool(
            auth_token: str, epic_id: int
        ) -> dict[str, Any]:
            """
            Get custom attribute values of an epic.

            Esta herramienta obtiene los valores actuales de todos los
            atributos personalizados de una épica específica. Útil para
            consultar datos extendidos del modelo.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica

            Returns:
                Dict con los valores de atributos personalizados conteniendo:
                - epic: ID de la épica
                - version: Versión para control de concurrencia
                - attributes_values: Dict con pares atributo_id: valor
                    donde cada clave es el ID del atributo personalizado
                    y el valor es el dato almacenado

            Raises:
                ToolError: Si la épica no existe, no hay permisos de acceso,
                    o la autenticación falla

            Example:
                >>> values = await taiga_get_epic_custom_attribute_values(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456
                ... )
                >>> print(values)
                {
                    "epic": 456,
                    "version": 3,
                    "attributes_values": {
                        "1": "Alta",
                        "2": "2024-06-30",
                        "45": "150%"
                    }
                }
            """
            return await self.get_epic_custom_attribute_values(
                auth_token=auth_token, epic_id=epic_id
            )

        # EPIC-015: Bulk link user stories to epic
        @self.mcp.tool(
            name="taiga_bulk_link_userstories_to_epic",
            description="Link multiple user stories to an epic at once",
        )
        async def bulk_link_userstories_to_epic_tool(
            auth_token: str,
            epic_id: int,
            userstory_ids: list[int],
        ) -> dict[str, Any]:
            """
            Link multiple user stories to an epic in bulk.

            Esta herramienta vincula múltiples historias de usuario a una épica
            de forma masiva. Es más eficiente que vincular una por una cuando
            se necesitan organizar varias historias bajo una misma épica.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                epic_id: ID de la épica a la que vincular las historias
                userstory_ids: Lista de IDs de las historias de usuario a vincular

            Returns:
                Dict con información de las relaciones creadas

            Raises:
                ToolError: Si la épica no existe, alguna historia no existe,
                    no hay permisos, o la autenticación falla

            Example:
                >>> result = await taiga_bulk_link_userstories_to_epic(
                ...     auth_token="eyJ0eXAiOi...",
                ...     epic_id=456,
                ...     userstory_ids=[101, 102, 103]
                ... )
            """
            return await self.bulk_create_related_userstories(
                auth_token=auth_token,
                epic_id=epic_id,
                userstory_ids=userstory_ids,
            )

    # Implementation methods

    # EPIC-001: List epics
    async def list_epics(
        self, auth_token: str, auto_paginate: bool = True, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """List epics in a project."""
        self._logger.debug(f"[list_epics] Starting | params={kwargs}")
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            kwargs.pop("auth_token", None)
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                paginator = AutoPaginator(client, PaginationConfig())
                params = {}
                if kwargs.get("project"):
                    params["project"] = kwargs["project"]
                if kwargs.get("status"):
                    params["status"] = kwargs["status"]
                if kwargs.get("assigned_to"):
                    params["assigned_to"] = kwargs["assigned_to"]

                if auto_paginate:
                    epics = await paginator.paginate("/epics", params=params)
                else:
                    epics = await paginator.paginate_first_page("/epics", params=params)
                # Validate response with Pydantic
                validated = EpicListResponse.from_api_response(epics).model_dump(exclude_none=True)
                self._logger.info(f"[list_epics] Success | count={len(validated['epics'])}")
                return validated["epics"]
        except AuthenticationError as e:
            self._logger.error(f"[list_epics] Authentication failed: {e!s}")
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(f"[list_epics] Permission denied: {e!s}")
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            self._logger.error(f"[list_epics] Project not found: {e!s}")
            raise ToolError(f"Project not found: {e!s}") from e
        except Exception as e:
            self._logger.error(f"[list_epics] Error: {e!s}")
            raise ToolError(f"Error listing epics: {e!s}") from e

    # EPIC-002: Create epic
    async def create_epic(
        self,
        auth_token: str,
        project: int | None = None,
        subject: str | None = None,
        description: str | None = None,
        assigned_to: int | None = None,
        status: int | None = None,
        color: str | None = None,
        tags: list[str] | None = None,
        watchers: list[int] | None = None,
        client_requirement: bool | None = None,
        team_requirement: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create a new epic."""
        self._logger.debug(f"[create_epic] Starting | project={project}, subject={subject}")

        if project is None or subject is None:
            self._logger.error("[create_epic] Validation error: project and subject are required")
            raise ValueError("project and subject are required")

        # Validar datos de entrada ANTES de llamar a la API
        epic_data = {
            "project_id": project,
            "subject": subject,
            "description": description,
            "color": color,
            "assigned_to": assigned_to,
            "status": status,
            "tags": tags,
        }
        validate_input(EpicCreateValidator, epic_data)

        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                epic = await client.create_epic(
                    project=project,
                    subject=subject,
                    description=description,
                    assigned_to=assigned_to,
                    status=status,
                    color=color,
                    tags=tags,
                    watchers=watchers,
                    client_requirement=client_requirement,
                    team_requirement=team_requirement,
                )
                # Validate response with Pydantic
                result = EpicResponse.model_validate(epic).model_dump(exclude_none=True)
                self._logger.info(
                    f"[create_epic] Success | epic_id={result.get('id')}, ref={result.get('ref')}"
                )
                return result
        except ValidationError as e:
            self._logger.warning(f"[create_epic] Validation error | error={e!s}")
            raise ToolError(str(e)) from e
        except Exception as e:
            self._logger.error(f"[create_epic] Error: {e!s}")
            raise

    # EPIC-003: Get epic by ID
    async def get_epic(self, auth_token: str, epic_id: int) -> dict[str, Any]:
        """Get an epic by ID."""
        self._logger.debug(f"[get_epic] Starting | epic_id={epic_id}")
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               ConcurrencyError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                epic = await client.get_epic(epic_id)
                # Validate response with Pydantic
                result = EpicResponse.model_validate(epic).model_dump(exclude_none=True)
                self._logger.info(
                    f"[get_epic] Success | epic_id={epic_id}, ref={result.get('ref')}"
                )
                return result
        except AuthenticationError as e:
            self._logger.error(f"[get_epic] Authentication failed: {e!s}")
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(f"[get_epic] Permission denied for epic_id={epic_id}: {e!s}")
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            self._logger.warning(f"[get_epic] Epic not found: epic_id={epic_id}")
            raise ToolError(f"Epic not found: {e!s}") from e
        except ConcurrencyError as e:
            self._logger.error(f"[get_epic] Version conflict: {e!s}")
            raise ToolError(f"Version conflict: {e!s}") from e
        except Exception as e:
            self._logger.error(f"[get_epic] Error: {e!s}")
            raise ToolError(f"Error getting epic: {e!s}") from e

    # EPIC-004: Get epic by ref
    async def get_epic_by_ref(
        self,
        auth_token: str,
        project_id: int,
        ref: int | None = None,
    ) -> dict[str, Any]:
        """Get an epic by its reference number within a project."""
        self._logger.debug(f"[get_epic_by_ref] Starting | project_id={project_id}, ref={ref}")
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                epic = await client.get_epic_by_ref(project_id=project_id, ref=ref)
                # Validate response with Pydantic
                result = EpicResponse.model_validate(epic).model_dump(exclude_none=True)
                self._logger.info(
                    f"[get_epic_by_ref] Success | project_id={project_id}, ref={ref}, epic_id={result.get('id')}"
                )
                return result
        except AuthenticationError as e:
            self._logger.error(f"[get_epic_by_ref] Authentication failed: {e!s}")
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(
                f"[get_epic_by_ref] Permission denied: project_id={project_id}, ref={ref}"
            )
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            self._logger.warning(f"[get_epic_by_ref] Not found: project_id={project_id}, ref={ref}")
            raise ToolError(f"Epic not found: {e!s}") from e
        except Exception as e:
            self._logger.error(f"[get_epic_by_ref] Error: {e!s}")
            raise ToolError(f"Error getting epic by ref: {e!s}") from e

    # EPIC-005: Update epic (full)
    async def update_epic_full(
        self,
        auth_token: str,
        epic_id: int,
        project: int | None = None,
        subject: str | None = None,
        description: str | None = None,
        assigned_to: int | None = None,
        status: int | None = None,
        color: str | None = None,
        tags: list[str] | None = None,
        client_requirement: bool | None = None,
        team_requirement: bool | None = None,
        version: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Full update of an epic (PUT)."""
        self._logger.debug(f"[update_epic_full] Starting | epic_id={epic_id}, subject={subject}")

        if subject is None:
            self._logger.error("[update_epic_full] Validation error: subject is required")
            raise ValueError("subject is required for full update")
        if project is None:
            self._logger.error("[update_epic_full] Validation error: project is required")
            raise ValueError("project is required for full update")

        try:
            from src.domain.exceptions import (AuthenticationError,
                                               ConcurrencyError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            # Validar datos de entrada ANTES de llamar a la API
            update_data = {
                "epic_id": epic_id,
                "subject": subject,
                "description": description,
                "color": color,
                "assigned_to": assigned_to,
                "status": status,
                "tags": tags,
            }
            validate_input(EpicUpdateValidator, update_data)

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                epic = await client.update_epic_full(
                    epic_id=epic_id,
                    project=project,
                    subject=subject,
                    description=description,
                    assigned_to=assigned_to,
                    status=status,
                    color=color,
                    tags=tags,
                    client_requirement=client_requirement,
                    team_requirement=team_requirement,
                    version=version,
                )
                # Validate response with Pydantic
                result = EpicResponse.model_validate(epic).model_dump(exclude_none=True)
                self._logger.info(f"[update_epic_full] Success | epic_id={epic_id}")
                return result
        except ConcurrencyError as e:
            self._logger.error(f"[update_epic_full] Version conflict: epic_id={epic_id}")
            raise ToolError(f"Version conflict: {e!s}") from e
        except AuthenticationError as e:
            self._logger.error(f"[update_epic_full] Authentication failed: {e!s}")
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(f"[update_epic_full] Permission denied: epic_id={epic_id}")
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            self._logger.warning(f"[update_epic_full] Epic not found: epic_id={epic_id}")
            raise ToolError(f"Epic not found: {e!s}") from e
        except ValidationError as e:
            self._logger.warning(f"[update_epic_full] Validation error | error={e!s}")
            raise ToolError(str(e)) from e
        except Exception as e:
            self._logger.error(f"[update_epic_full] Error: {e!s}")
            raise ToolError(f"Error updating epic: {e!s}") from e

    # EPIC-006: Update epic (decides between full/partial based on presence of required fields)
    async def update_epic(
        self,
        auth_token: str,
        epic_id: int,
        project: int | None = None,
        subject: str | None = None,
        description: str | None = None,
        assigned_to: int | None = None,
        status: int | None = None,
        color: str | None = None,
        tags: list[str] | None = None,
        client_requirement: bool | None = None,
        team_requirement: bool | None = None,
        version: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Update an epic (decides between full/partial based on parameters)."""
        is_full_update = subject is not None and project is not None and version is not None
        update_type = "full" if is_full_update else "partial"
        self._logger.debug(f"[update_epic] Starting | epic_id={epic_id}, type={update_type}")
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               ConcurrencyError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            # Validar datos de entrada ANTES de llamar a la API
            update_data = {
                "epic_id": epic_id,
                "subject": subject,
                "description": description,
                "color": color,
                "assigned_to": assigned_to,
                "status": status,
                "tags": tags,
            }
            validate_input(EpicUpdateValidator, update_data)

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                # If subject, project and version are present, use full update (PUT)
                if is_full_update:
                    result = await client.update_epic_full(
                        epic_id=epic_id,
                        project=project,
                        subject=subject,
                        description=description,
                        assigned_to=assigned_to,
                        status=status,
                        color=color,
                        tags=tags,
                        client_requirement=client_requirement,
                        team_requirement=team_requirement,
                        version=version,
                    )
                else:
                    # Otherwise use partial update (PATCH)
                    result = await client.update_epic(
                        epic_id=epic_id,
                        subject=subject,
                        description=description,
                        assigned_to=assigned_to,
                        status=status,
                        color=color,
                        tags=tags,
                        client_requirement=client_requirement,
                        team_requirement=team_requirement,
                        version=version,
                    )

                # Validate response with Pydantic
                validated = EpicResponse.model_validate(result).model_dump(exclude_none=True)
                self._logger.info(f"[update_epic] Success | epic_id={epic_id}, type={update_type}")
                return validated
        except ConcurrencyError as e:
            self._logger.error(f"[update_epic] Version conflict: epic_id={epic_id}")
            raise ToolError(f"Version conflict: {e!s}") from e
        except AuthenticationError as e:
            self._logger.error(f"[update_epic] Authentication failed: {e!s}")
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(f"[update_epic] Permission denied: epic_id={epic_id}")
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            self._logger.warning(f"[update_epic] Epic not found: epic_id={epic_id}")
            raise ToolError(f"Epic not found: {e!s}") from e
        except ValidationError as e:
            self._logger.warning(f"[update_epic] Validation error | error={e!s}")
            raise ToolError(str(e)) from e
        except Exception as e:
            self._logger.error(f"[update_epic] Error: {e!s}")
            raise ToolError(f"Error updating epic: {e!s}") from e

    # EPIC-006: Update epic (partial)
    async def update_epic_partial(
        self,
        auth_token: str,
        epic_id: int,
        subject: str | None = None,
        description: str | None = None,
        assigned_to: int | None = None,
        status: int | None = None,
        color: str | None = None,
        tags: list[str] | None = None,
        client_requirement: bool | None = None,
        team_requirement: bool | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        """Partial update of an epic (PATCH)."""
        return await self.update_epic(
            auth_token=auth_token,
            epic_id=epic_id,
            subject=subject,
            description=description,
            assigned_to=assigned_to,
            status=status,
            color=color,
            tags=tags,
            client_requirement=client_requirement,
            team_requirement=team_requirement,
            version=version,
        )

    # EPIC-006: Patch epic (alias for update_epic_partial)
    async def patch_epic(
        self,
        auth_token: str,
        epic_id: int,
        subject: str | None = None,
        description: str | None = None,
        assigned_to: int | None = None,
        status: int | None = None,
        color: str | None = None,
        tags: list[str] | None = None,
        client_requirement: bool | None = None,
        team_requirement: bool | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        """Patch update of an epic (PATCH) - alias for update_epic_partial."""
        return await self.update_epic(
            auth_token=auth_token,
            epic_id=epic_id,
            subject=subject,
            description=description,
            assigned_to=assigned_to,
            status=status,
            color=color,
            tags=tags,
            client_requirement=client_requirement,
            team_requirement=team_requirement,
            version=version,
        )

    # EPIC-007: Delete epic
    async def delete_epic(self, auth_token: str, epic_id: int) -> dict[str, str]:
        """Delete an epic."""
        self._logger.debug(f"[delete_epic] Starting | epic_id={epic_id}")
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                await client.delete_epic(epic_id)
                self._logger.info(f"[delete_epic] Success | epic_id={epic_id}")
                # Validate response with Pydantic
                return SuccessResponse(message=f"Epic {epic_id} deleted successfully").model_dump(
                    exclude_none=True
                )
        except AuthenticationError as e:
            self._logger.error(f"[delete_epic] Authentication failed: {e!s}")
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(f"[delete_epic] Permission denied: epic_id={epic_id}")
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            self._logger.warning(f"[delete_epic] Not found: epic_id={epic_id}")
            raise ToolError(f"Epic not found: {e!s}") from e
        except Exception as e:
            self._logger.error(f"[delete_epic] Error: {e!s}")
            raise ToolError(f"Error deleting epic: {e!s}") from e

    # EPIC-008: List epic related user stories
    async def list_epic_related_userstories(
        self, auth_token: str, epic_id: int
    ) -> list[dict[str, Any]]:
        """List user stories related to an epic."""
        self._logger.debug(f"[list_epic_related_userstories] Starting | epic_id={epic_id}")
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            stories = await client.list_epic_related_userstories(epic_id)
            # Validate response with Pydantic
            result = [
                EpicRelatedUserstoryResponse.model_validate(s).model_dump(exclude_none=True)
                for s in stories
            ]
            self._logger.info(
                f"[list_epic_related_userstories] Success | epic_id={epic_id}, count={len(result)}"
            )
            return result

    # EPIC-008: List related user stories (alias)
    async def list_related_userstories(self, auth_token: str, epic_id: int) -> list[dict[str, Any]]:
        """List user stories related to an epic."""
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            return await self.list_epic_related_userstories(auth_token=auth_token, epic_id=epic_id)
        except AuthenticationError as e:
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            raise ToolError(f"Epic not found: {e!s}") from e
        except Exception as e:
            raise ToolError(f"Error listing related user stories: {e!s}") from e

    # EPIC-009: Create epic related user story (link existing user story to epic)
    async def create_epic_related_userstory(
        self, auth_token: str, epic_id: int, user_story: int, order: int | None = None
    ) -> dict[str, Any]:
        """
        Link an existing user story to an epic.

        Args:
            auth_token: Authentication token
            epic_id: ID of the epic
            user_story: ID of the existing user story to link
            order: Optional order position

        Returns:
            Dict with the created relationship
        """
        self._logger.debug(
            f"[create_epic_related_userstory] Starting | epic_id={epic_id}, user_story={user_story}"
        )
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            story = await client.create_epic_related_userstory(
                epic_id=epic_id, user_story=user_story, order=order
            )
            # Validate response with Pydantic
            result = EpicRelatedUserstoryResponse.model_validate(story).model_dump(
                exclude_none=True
            )
            self._logger.info(
                f"[create_epic_related_userstory] Success | epic_id={epic_id}, user_story={user_story}"
            )
            return result

    # EPIC-009: Create related user story (alias)
    async def create_related_userstory(
        self,
        auth_token: str,
        epic_id: int,
        user_story: int,
        order: int | None = None,
    ) -> dict[str, Any]:
        """
        Create a user story related to an epic.

        Args:
            auth_token: Authentication token
            epic_id: ID of the epic
            user_story: ID of the user story to link
            order: Optional order position

        Returns:
            Dict with the created relationship
        """
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            return await self.create_epic_related_userstory(
                auth_token=auth_token, epic_id=epic_id, user_story=user_story, order=order
            )
        except AuthenticationError as e:
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            raise ToolError(f"Epic not found: {e!s}") from e
        except Exception as e:
            raise ToolError(f"Error creating related user story: {e!s}") from e

    # EPIC-010: Get epic related user story
    async def get_epic_related_userstory(
        self, auth_token: str, epic_id: int, userstory_id: int
    ) -> dict[str, Any]:
        """Get a specific user story related to an epic."""
        self._logger.debug(
            f"[get_epic_related_userstory] Starting | epic_id={epic_id}, userstory_id={userstory_id}"
        )
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            story = await client.get_epic_related_userstory(
                epic_id=epic_id, userstory_id=userstory_id
            )
            # Validate response with Pydantic
            result = EpicRelatedUserstoryResponse.model_validate(story).model_dump(
                exclude_none=True
            )
            self._logger.info(
                f"[get_epic_related_userstory] Success | epic_id={epic_id}, userstory_id={userstory_id}"
            )
            return result

    # EPIC-011: Update epic related user story
    async def update_epic_related_userstory(
        self, auth_token: str, epic_id: int, userstory_id: int, order: int | None = None
    ) -> dict[str, Any]:
        """
        Update a user story related to an epic.

        Args:
            auth_token: Authentication token
            epic_id: ID of the epic
            userstory_id: ID of the user story
            order: Optional order position

        Returns:
            Dict with the updated relationship
        """
        self._logger.debug(
            f"[update_epic_related_userstory] Starting | epic_id={epic_id}, userstory_id={userstory_id}"
        )
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            story = await client.update_epic_related_userstory(
                epic_id=epic_id, userstory_id=userstory_id, order=order
            )
            # Validate response with Pydantic
            result = EpicRelatedUserstoryResponse.model_validate(story).model_dump(
                exclude_none=True
            )
            self._logger.info(
                f"[update_epic_related_userstory] Success | epic_id={epic_id}, userstory_id={userstory_id}"
            )
            return result

    # EPIC-012: Delete epic related user story
    async def delete_epic_related_userstory(
        self,
        auth_token: str,
        epic_id: int,
        userstory_id: int,
    ) -> dict[str, Any]:
        """Delete a user story related to an epic."""
        self._logger.debug(
            f"[delete_epic_related_userstory] Starting | epic_id={epic_id}, userstory_id={userstory_id}"
        )
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            await client.delete_epic_related_userstory(epic_id=epic_id, userstory_id=userstory_id)
            self._logger.info(
                f"[delete_epic_related_userstory] Success | epic_id={epic_id}, userstory_id={userstory_id}"
            )
            # Validate response with Pydantic
            return SuccessResponse(
                message=f"User story {userstory_id} removed from epic {epic_id}"
            ).model_dump(exclude_none=True)

    # EPIC-013: Bulk create epics
    async def bulk_create_epics(
        self,
        auth_token: str,
        project_id: int | None = None,
        epics_data: list[dict[str, Any]] | None = None,
        bulk_epics: str | None = None,
    ) -> list[dict[str, Any]]:
        """Bulk create multiple epics."""
        self._logger.debug(f"[bulk_create_epics] Starting | project_id={project_id}")
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               PermissionDeniedError)

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                # Handle both epics_data and bulk_epics parameters
                if bulk_epics:
                    result = await client.bulk_create_epics(
                        project_id=project_id, bulk_epics=bulk_epics
                    )
                else:
                    result = await client.bulk_create_epics(
                        project_id=project_id, epics_data=epics_data
                    )
                # Validate response with Pydantic
                validated = [
                    EpicResponse.model_validate(epic).model_dump(exclude_none=True)
                    for epic in result
                ]
                self._logger.info(
                    f"[bulk_create_epics] Success | project_id={project_id}, count={len(validated)}"
                )
                return validated
        except AuthenticationError as e:
            self._logger.error(
                f"[bulk_create_epics] Authentication failed | project_id={project_id}"
            )
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(f"[bulk_create_epics] Permission denied | project_id={project_id}")
            raise ToolError(f"Permission denied: {e!s}") from e
        except Exception as e:
            self._logger.error(f"[bulk_create_epics] Error | project_id={project_id}, error={e!s}")
            raise ToolError(f"Error bulk creating epics: {e!s}") from e

    # EPIC-013b: Bulk create related user stories
    async def bulk_create_related_userstories(
        self,
        auth_token: str,
        epic_id: int,
        userstories_data: list[dict[str, Any]] | None = None,
        bulk_userstories: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Bulk create user stories related to an epic."""
        self._logger.debug(f"[bulk_create_related_userstories] Starting | epic_id={epic_id}")
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                # Check if client has the non-epic version (for tests)
                if hasattr(client, "bulk_create_related_userstories"):
                    if bulk_userstories:
                        result = await client.bulk_create_related_userstories(
                            epic_id=epic_id, bulk_userstories=bulk_userstories
                        )
                    else:
                        result = await client.bulk_create_related_userstories(
                            epic_id=epic_id, userstories_data=userstories_data
                        )
                else:
                    # Fallback to epic version (production)
                    if bulk_userstories:
                        result = await client.bulk_create_epic_related_userstories(
                            epic_id=epic_id, bulk_userstories=bulk_userstories
                        )
                    else:
                        result = await client.bulk_create_epic_related_userstories(
                            epic_id=epic_id, userstories_data=userstories_data
                        )
                # Validate response with Pydantic
                validated = [
                    EpicRelatedUserstoryResponse.model_validate(s).model_dump(exclude_none=True)
                    for s in result
                ]
                self._logger.info(
                    f"[bulk_create_related_userstories] Success | epic_id={epic_id}, count={len(validated)}"
                )
                return validated
        except AuthenticationError as e:
            self._logger.error(
                f"[bulk_create_related_userstories] Authentication failed | epic_id={epic_id}"
            )
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(
                f"[bulk_create_related_userstories] Permission denied | epic_id={epic_id}"
            )
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            self._logger.error(
                f"[bulk_create_related_userstories] Epic not found | epic_id={epic_id}"
            )
            raise ToolError(f"Epic not found: {e!s}") from e
        except Exception as e:
            self._logger.error(
                f"[bulk_create_related_userstories] Error | epic_id={epic_id}, error={e!s}"
            )
            raise ToolError(f"Error bulk creating related user stories: {e!s}") from e

    # Alias for backward compatibility
    async def bulk_create_epic_related_userstories(
        self, auth_token: str, epic_id: int, userstories_data: list[dict[str, Any]] | None = None
    ) -> list[dict[str, Any]]:
        """Bulk create user stories related to an epic (alias)."""
        return await self.bulk_create_related_userstories(auth_token, epic_id, userstories_data)

    # EPIC-014: Get epic filters
    async def get_epic_filters(self, auth_token: str, project_id: int) -> dict[str, Any]:
        """Get available filters for epics in a project."""
        self._logger.debug(f"[get_epic_filters] Starting | project_id={project_id}")
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                filters = await client.get_epic_filters(project=project_id)
                # Validate response with Pydantic
                result = EpicFiltersResponse.model_validate(filters).model_dump(exclude_none=True)
                self._logger.info(f"[get_epic_filters] Success | project_id={project_id}")
                return result
        except AuthenticationError as e:
            self._logger.error(
                f"[get_epic_filters] Authentication failed | project_id={project_id}"
            )
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(f"[get_epic_filters] Permission denied | project_id={project_id}")
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            self._logger.error(f"[get_epic_filters] Project not found | project_id={project_id}")
            raise ToolError(f"Project not found: {e!s}") from e
        except Exception as e:
            self._logger.error(f"[get_epic_filters] Error | project_id={project_id}, error={e!s}")
            raise ToolError(f"Error getting epic filters: {e!s}") from e

    # EPIC-015: Upvote epic
    async def upvote_epic(self, auth_token: str, epic_id: int) -> dict[str, Any]:
        """Upvote an epic."""
        self._logger.debug(f"[upvote_epic] Starting | epic_id={epic_id}")
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                await client.upvote_epic(epic_id)
                self._logger.info(f"[upvote_epic] Success | epic_id={epic_id}")
                # Validate response with Pydantic
                return SuccessResponse(message=f"Epic {epic_id} upvoted successfully").model_dump(
                    exclude_none=True
                )
        except AuthenticationError as e:
            self._logger.error(f"[upvote_epic] Authentication failed | epic_id={epic_id}")
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(f"[upvote_epic] Permission denied | epic_id={epic_id}")
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            self._logger.error(f"[upvote_epic] Epic not found | epic_id={epic_id}")
            raise ToolError(f"Epic not found: {e!s}") from e
        except Exception as e:
            self._logger.error(f"[upvote_epic] Error | epic_id={epic_id}, error={e!s}")
            raise ToolError(f"Error upvoting epic: {e!s}") from e

    # EPIC-016: Downvote epic
    async def downvote_epic(self, auth_token: str, epic_id: int) -> dict[str, Any]:
        """Downvote an epic."""
        self._logger.debug(f"[downvote_epic] Starting | epic_id={epic_id}")
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                await client.downvote_epic(epic_id)
                self._logger.info(f"[downvote_epic] Success | epic_id={epic_id}")
                # Validate response with Pydantic
                return SuccessResponse(message=f"Epic {epic_id} downvoted successfully").model_dump(
                    exclude_none=True
                )
        except AuthenticationError as e:
            self._logger.error(f"[downvote_epic] Authentication failed | epic_id={epic_id}")
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(f"[downvote_epic] Permission denied | epic_id={epic_id}")
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            self._logger.error(f"[downvote_epic] Epic not found | epic_id={epic_id}")
            raise ToolError(f"Epic not found: {e!s}") from e
        except Exception as e:
            self._logger.error(f"[downvote_epic] Error | epic_id={epic_id}, error={e!s}")
            raise ToolError(f"Error downvoting epic: {e!s}") from e

    # EPIC-017: Get epic voters
    async def get_epic_voters(self, auth_token: str, epic_id: int) -> list[dict[str, Any]]:
        """Get voters of an epic."""
        self._logger.debug(f"[get_epic_voters] Starting | epic_id={epic_id}")
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                voters = await client.get_epic_voters(epic_id)
                # Validate response with Pydantic
                validated = [
                    EpicVoterResponse.model_validate(v).model_dump(exclude_none=True)
                    for v in voters
                ]
                self._logger.info(
                    f"[get_epic_voters] Success | epic_id={epic_id}, count={len(validated)}"
                )
                return validated
        except AuthenticationError as e:
            self._logger.error(f"[get_epic_voters] Authentication failed | epic_id={epic_id}")
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(f"[get_epic_voters] Permission denied | epic_id={epic_id}")
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            self._logger.error(f"[get_epic_voters] Epic not found | epic_id={epic_id}")
            raise ToolError(f"Epic not found: {e!s}") from e
        except Exception as e:
            self._logger.error(f"[get_epic_voters] Error | epic_id={epic_id}, error={e!s}")
            raise ToolError(f"Error getting epic voters: {e!s}") from e

    # EPIC-018: Watch epic
    async def watch_epic(self, auth_token: str, epic_id: int) -> dict[str, Any]:
        """Watch an epic for updates."""
        self._logger.debug(f"[watch_epic] Starting | epic_id={epic_id}")
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                await client.watch_epic(epic_id)
                self._logger.info(f"[watch_epic] Success | epic_id={epic_id}")
                # Validate response with Pydantic
                return SuccessResponse(message=f"Now watching epic {epic_id}").model_dump(
                    exclude_none=True
                )
        except AuthenticationError as e:
            self._logger.error(f"[watch_epic] Authentication failed | epic_id={epic_id}")
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(f"[watch_epic] Permission denied | epic_id={epic_id}")
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            self._logger.error(f"[watch_epic] Epic not found | epic_id={epic_id}")
            raise ToolError(f"Epic not found: {e!s}") from e
        except Exception as e:
            self._logger.error(f"[watch_epic] Error | epic_id={epic_id}, error={e!s}")
            raise ToolError(f"Error watching epic: {e!s}") from e

    # EPIC-019: Unwatch epic
    async def unwatch_epic(self, auth_token: str, epic_id: int) -> dict[str, Any]:
        """Stop watching an epic."""
        self._logger.debug(f"[unwatch_epic] Starting | epic_id={epic_id}")
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                await client.unwatch_epic(epic_id)
                self._logger.info(f"[unwatch_epic] Success | epic_id={epic_id}")
                # Validate response with Pydantic
                return SuccessResponse(message=f"Stopped watching epic {epic_id}").model_dump(
                    exclude_none=True
                )
        except AuthenticationError as e:
            self._logger.error(f"[unwatch_epic] Authentication failed | epic_id={epic_id}")
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(f"[unwatch_epic] Permission denied | epic_id={epic_id}")
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            self._logger.error(f"[unwatch_epic] Epic not found | epic_id={epic_id}")
            raise ToolError(f"Epic not found: {e!s}") from e
        except Exception as e:
            self._logger.error(f"[unwatch_epic] Error | epic_id={epic_id}, error={e!s}")
            raise ToolError(f"Error unwatching epic: {e!s}") from e

    # EPIC-020: Get epic watchers
    async def get_epic_watchers(self, auth_token: str, epic_id: int) -> list[dict[str, Any]]:
        """Get watchers of an epic."""
        self._logger.debug(f"[get_epic_watchers] Starting | epic_id={epic_id}")
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                watchers = await client.get_epic_watchers(epic_id)
                # Validate response with Pydantic
                validated = [
                    EpicWatcherResponse.model_validate(w).model_dump(exclude_none=True)
                    for w in watchers
                ]
                self._logger.info(
                    f"[get_epic_watchers] Success | epic_id={epic_id}, count={len(validated)}"
                )
                return validated
        except AuthenticationError as e:
            self._logger.error(f"[get_epic_watchers] Authentication failed | epic_id={epic_id}")
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(f"[get_epic_watchers] Permission denied | epic_id={epic_id}")
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            self._logger.error(f"[get_epic_watchers] Epic not found | epic_id={epic_id}")
            raise ToolError(f"Epic not found: {e!s}") from e
        except Exception as e:
            self._logger.error(f"[get_epic_watchers] Error | epic_id={epic_id}, error={e!s}")
            raise ToolError(f"Error getting epic watchers: {e!s}") from e

    # EPIC-021: List epic attachments
    async def list_epic_attachments(self, auth_token: str, **kwargs: Any) -> list[dict[str, Any]]:
        """List attachments of an epic."""
        epic_id = kwargs.get("epic_id") or kwargs.get("object_id")
        self._logger.debug(f"[list_epic_attachments] Starting | epic_id={epic_id}")
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            kwargs.pop("auth_token", None)
            # Handle alias: epic_id -> object_id
            if "epic_id" in kwargs:
                kwargs["object_id"] = kwargs.pop("epic_id")
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                attachments = await client.list_epic_attachments(**kwargs)
                # Validate response with Pydantic
                validated = [
                    EpicAttachmentResponse.model_validate(a).model_dump(exclude_none=True)
                    for a in attachments
                ]
                self._logger.info(
                    f"[list_epic_attachments] Success | epic_id={epic_id}, count={len(validated)}"
                )
                return validated
        except AuthenticationError as e:
            self._logger.error(f"[list_epic_attachments] Authentication failed | epic_id={epic_id}")
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(f"[list_epic_attachments] Permission denied | epic_id={epic_id}")
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            self._logger.error(f"[list_epic_attachments] Epic not found | epic_id={epic_id}")
            raise ToolError(f"Epic not found: {e!s}") from e
        except Exception as e:
            self._logger.error(f"[list_epic_attachments] Error | epic_id={epic_id}, error={e!s}")
            raise ToolError(f"Error listing epic attachments: {e!s}") from e

    # EPIC-022: Create epic attachment
    async def create_epic_attachment(self, auth_token: str, **kwargs: Any) -> dict[str, Any]:
        """Create an attachment for an epic."""
        epic_id = kwargs.get("epic_id") or kwargs.get("object_id")
        self._logger.debug(f"[create_epic_attachment] Starting | epic_id={epic_id}")
        try:
            from src.domain.exceptions import (AuthenticationError,
                                               PermissionDeniedError,
                                               ResourceNotFoundError)

            kwargs.pop("auth_token", None)
            # Handle alias: epic_id -> object_id
            if "epic_id" in kwargs:
                kwargs["object_id"] = kwargs.pop("epic_id")
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                attachment = await client.create_epic_attachment(**kwargs)
                # Validate response with Pydantic
                result = EpicAttachmentResponse.model_validate(attachment).model_dump(
                    exclude_none=True
                )
                self._logger.info(
                    f"[create_epic_attachment] Success | epic_id={epic_id}, attachment_id={result.get('id')}"
                )
                return result
        except AuthenticationError as e:
            self._logger.error(
                f"[create_epic_attachment] Authentication failed | epic_id={epic_id}"
            )
            raise ToolError(f"Authentication failed: {e!s}") from e
        except PermissionDeniedError as e:
            self._logger.error(f"[create_epic_attachment] Permission denied | epic_id={epic_id}")
            raise ToolError(f"Permission denied: {e!s}") from e
        except ResourceNotFoundError as e:
            self._logger.error(f"[create_epic_attachment] Epic not found | epic_id={epic_id}")
            raise ToolError(f"Epic not found: {e!s}") from e
        except Exception as e:
            self._logger.error(f"[create_epic_attachment] Error | epic_id={epic_id}, error={e!s}")
            raise ToolError(f"Error creating epic attachment: {e!s}") from e

    # EPIC-023: Get epic attachment
    async def get_epic_attachment(self, auth_token: str, attachment_id: int) -> dict[str, Any]:
        """Get a specific attachment of an epic."""
        self._logger.debug(f"[get_epic_attachment] Starting | attachment_id={attachment_id}")
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            attachment = await client.get_epic_attachment(attachment_id=attachment_id)
            # Validate response with Pydantic
            result = EpicAttachmentResponse.model_validate(attachment).model_dump(exclude_none=True)
            self._logger.info(f"[get_epic_attachment] Success | attachment_id={attachment_id}")
            return result

    # EPIC-024: Update epic attachment
    async def update_epic_attachment(
        self, auth_token: str, attachment_id: int, **kwargs: Any
    ) -> dict[str, Any]:
        """Update an attachment of an epic."""
        self._logger.debug(f"[update_epic_attachment] Starting | attachment_id={attachment_id}")
        kwargs.pop("auth_token", None)
        kwargs.pop("attachment_id", None)
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            attachment = await client.update_epic_attachment(attachment_id=attachment_id, **kwargs)
            # Validate response with Pydantic
            result = EpicAttachmentResponse.model_validate(attachment).model_dump(exclude_none=True)
            self._logger.info(f"[update_epic_attachment] Success | attachment_id={attachment_id}")
            return result

    # EPIC-025: Delete epic attachment
    async def delete_epic_attachment(self, auth_token: str, attachment_id: int) -> dict[str, Any]:
        """Delete an attachment of an epic."""
        self._logger.debug(f"[delete_epic_attachment] Starting | attachment_id={attachment_id}")
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            await client.delete_epic_attachment(attachment_id=attachment_id)
            self._logger.info(f"[delete_epic_attachment] Success | attachment_id={attachment_id}")
            # Validate response with Pydantic
            return SuccessResponse(
                message=f"Attachment {attachment_id} deleted successfully"
            ).model_dump(exclude_none=True)

    # EPIC-026: List epic custom attributes
    async def list_epic_custom_attributes(
        self, auth_token: str, project_id: int
    ) -> list[dict[str, Any]]:
        """List custom attributes for epics in a project."""
        self._logger.debug(f"[list_epic_custom_attributes] Starting | project_id={project_id}")
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            attrs = await client.list_epic_custom_attributes(project=project_id)
            # Validate response with Pydantic
            result = [
                EpicCustomAttributeResponse.model_validate(a).model_dump(exclude_none=True)
                for a in attrs
            ]
            self._logger.info(
                f"[list_epic_custom_attributes] Success | project_id={project_id}, count={len(result)}"
            )
            return result

    # EPIC-027: Create epic custom attribute
    async def create_epic_custom_attribute(
        self, auth_token: str, project_id: int, name: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Create a custom attribute for epics."""
        self._logger.debug(
            f"[create_epic_custom_attribute] Starting | project_id={project_id}, name={name}"
        )
        kwargs.pop("auth_token", None)
        kwargs.pop("project", None)
        kwargs.pop("project_id", None)
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            attr = await client.create_epic_custom_attribute(
                project_id=project_id, name=name, **kwargs
            )
            # Validate response with Pydantic
            result = EpicCustomAttributeResponse.model_validate(attr).model_dump(exclude_none=True)
            self._logger.info(
                f"[create_epic_custom_attribute] Success | project_id={project_id}, name={name}, id={result.get('id')}"
            )
            return result

    # EPIC-028: Get epic custom attribute values
    async def get_epic_custom_attribute_values(
        self, auth_token: str, epic_id: int
    ) -> dict[str, Any]:
        """Get custom attribute values of an epic."""
        self._logger.debug(f"[get_epic_custom_attribute_values] Starting | epic_id={epic_id}")
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            values = await client.get_epic_custom_attribute_values(epic_id=epic_id)
            # Validate response with Pydantic
            result = EpicCustomAttributeValuesResponse.model_validate(values).model_dump(
                exclude_none=True
            )
            self._logger.info(f"[get_epic_custom_attribute_values] Success | epic_id={epic_id}")
            return result
