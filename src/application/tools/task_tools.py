"""
Herramientas para gestión de Tasks en Taiga.

Este módulo implementa todas las operaciones relacionadas con tareas (tasks)
siguiendo los principios de Domain Driven Design (DDD).

Funcionalidades implementadas:
- TASK-001: Listar tareas con filtros opcionales
- TASK-002: Crear nueva tarea
- TASK-003: Obtener tarea por ID
- TASK-004: Obtener tarea por referencia y proyecto
- TASK-005: Actualizar tarea (reemplazo completo)
- TASK-006: Actualizar tarea (parcial)
- TASK-007: Eliminar tarea
- TASK-008: Crear tareas en lote
- TASK-009: Obtener filtros de datos de tareas
- TASK-010: Votar positivo en tarea
- TASK-011: Votar negativo en tarea
- TASK-012: Obtener votantes de tarea
- TASK-013: Seguir tarea
- TASK-014: Dejar de seguir tarea
- TASK-015: Obtener observadores de tarea
- TASK-016: Listar adjuntos de tarea
- TASK-017: Crear adjunto en tarea
- TASK-018: Obtener adjunto de tarea
- TASK-019: Actualizar adjunto de tarea
- TASK-020: Eliminar adjunto de tarea
- TASK-021: Obtener historial de tarea
- TASK-022: Obtener versiones de comentario de tarea
- TASK-023: Editar comentario de tarea
- TASK-024: Eliminar comentario de tarea
- TASK-025: Recuperar comentario de tarea
- TASK-026: Listar atributos personalizados de tarea
- TASK-027: Crear atributo personalizado de tarea
- TASK-028: Actualizar atributo personalizado de tarea
- TASK-029: Eliminar atributo personalizado de tarea
"""

from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError as MCPError

from src.config import TaigaConfig
from src.domain.exceptions import ValidationError
from src.domain.validators import TaskCreateValidator, TaskUpdateValidator, validate_input
from src.infrastructure.logging import get_logger
from src.infrastructure.pagination import AutoPaginator, PaginationConfig
from src.taiga_client import TaigaAPIClient


class TaskTools:
    """
    Herramientas para gestión de Tasks en Taiga.

    Esta clase implementa la capa de aplicación para las operaciones de tareas,
    actuando como intermediario entre la capa de presentación (MCP) y el cliente
    de dominio de Taiga.
    """

    def __init__(self, mcp: FastMCP) -> None:
        """
        Inicializa las herramientas de tareas.

        Args:
            mcp: Instancia del servidor MCP para registro de herramientas
        """
        self.mcp = mcp
        self.config = TaigaConfig()
        self._logger = get_logger("task_tools")
        self._register_tools()

    def _register_tools(self) -> None:
        """Registra todas las herramientas de tareas en el servidor MCP."""

        # TASK-001: Listar tareas
        @self.mcp.tool(
            name="taiga_list_tasks",
            annotations={"readOnlyHint": True},
            description="List all tasks in a Taiga project with optional filters",
        )
        async def list_tasks_tool(
            auth_token: str,
            project_id: int | None = None,
            user_story_id: int | None = None,
            milestone_id: int | None = None,
            status: int | None = None,
            assigned_to: int | None = None,
            tags: list[str] | None = None,
            is_closed: bool | None = None,
            exclude_status: int | None = None,
            exclude_assigned_to: int | None = None,
            exclude_tags: list[str] | None = None,
            auto_paginate: bool = True,
        ) -> list[dict[str, Any]]:
            """
            List all tasks in a Taiga project with optional filters.

            Esta herramienta lista todas las tareas de un proyecto con soporte
            para múltiples filtros de búsqueda. Permite filtrar por proyecto,
            historia de usuario, milestone, estado, asignación y etiquetas.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto para filtrar tareas (opcional)
                user_story_id: ID de la historia de usuario asociada (opcional)
                milestone_id: ID del milestone/sprint para filtrar (opcional)
                status: ID del estado para filtrar (opcional)
                assigned_to: ID del usuario asignado para filtrar (opcional)
                tags: Lista de etiquetas para filtrar (opcional)
                is_closed: Filtrar por tareas cerradas/abiertas (opcional)
                exclude_status: ID de estado a excluir de resultados (opcional)
                exclude_assigned_to: ID de usuario asignado a excluir (opcional)
                exclude_tags: Lista de etiquetas a excluir (opcional)
                auto_paginate: Si True (default), obtiene todos los resultados
                    automáticamente. Si False, retorna solo la primera página.

            Returns:
                Lista de diccionarios con información de tareas, cada uno conteniendo:
                - id: ID de la tarea
                - ref: Número de referencia
                - subject: Título de la tarea
                - description: Descripción detallada
                - status: ID del estado
                - user_story: ID de la historia de usuario asociada
                - milestone: ID del milestone
                - assigned_to: ID del usuario asignado
                - is_closed: Si la tarea está cerrada
                - tags: Lista de etiquetas

            Raises:
                ToolError: Si la autenticación falla o hay error en la API

            Example:
                >>> tasks = await taiga_list_tasks(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     is_closed=False
                ... )
                >>> print(tasks[0]["subject"])
                "Implementar validación de formulario"
            """
            return await self.list_tasks(
                auth_token=auth_token,
                project=project_id,  # API expects 'project'
                user_story=user_story_id,  # API expects 'user_story'
                milestone=milestone_id,  # API expects 'milestone'
                status=status,
                assigned_to=assigned_to,
                tags=tags,
                is_closed=is_closed,
                exclude_status=exclude_status,
                exclude_assigned_to=exclude_assigned_to,
                exclude_tags=exclude_tags,
                auto_paginate=auto_paginate,
            )

        # TASK-002: Crear tarea
        @self.mcp.tool(name="taiga_create_task", description="Create a new task in a Taiga project")
        async def create_task_tool(
            auth_token: str,
            project_id: int,
            subject: str,
            description: str | None = None,
            user_story_id: int | None = None,
            milestone_id: int | None = None,
            status: int | None = None,
            assigned_to: int | None = None,
            tags: list[str] | None = None,
            is_blocked: bool | None = None,
            blocked_note: str | None = None,
        ) -> dict[str, Any]:
            """
            Create a new task in a Taiga project.

            Esta herramienta crea una nueva tarea asociada a un proyecto
            y opcionalmente a una historia de usuario. Las tareas representan
            unidades de trabajo técnico dentro del contexto de una historia.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde crear la tarea (requerido)
                subject: Título o asunto de la tarea (requerido)
                description: Descripción detallada de la tarea (opcional)
                user_story_id: ID de la historia de usuario asociada (opcional)
                milestone_id: ID del milestone/sprint asignado (opcional)
                status: ID del estado inicial (opcional, usa default del proyecto)
                assigned_to: ID del usuario responsable de la tarea (opcional)
                tags: Lista de etiquetas para categorizar (opcional)
                is_blocked: Marcar como bloqueada inicialmente (opcional)
                blocked_note: Razón del bloqueo si is_blocked=True (opcional)

            Returns:
                Dict con los datos de la tarea creada conteniendo:
                - id: ID de la tarea creada
                - ref: Número de referencia único en el proyecto
                - subject: Título de la tarea
                - description: Descripción
                - status: ID del estado asignado
                - user_story: ID de la historia asociada
                - project: ID del proyecto
                - assigned_to: ID del usuario asignado
                - created_date: Fecha de creación

            Raises:
                ToolError: Si faltan campos requeridos, no hay permisos,
                    o falla la API

            Example:
                >>> task = await taiga_create_task(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     subject="Configurar CI/CD",
                ...     user_story_id=456,
                ...     assigned_to=78
                ... )
                >>> print(task["id"])
                789
            """
            try:
                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {
                    "project_id": project_id,
                    "subject": subject,
                    "description": description,
                    "status": status,
                    "assigned_to": assigned_to,
                    "tags": tags,
                }
                validate_input(TaskCreateValidator, validation_data)

                return await self.create_task(
                    auth_token=auth_token,
                    project=project_id,  # API expects 'project'
                    subject=subject,
                    description=description,
                    user_story=user_story_id,  # API expects 'user_story'
                    milestone=milestone_id,  # API expects 'milestone'
                    status=status,
                    assigned_to=assigned_to,
                    tags=tags,
                    is_blocked=is_blocked,
                    blocked_note=blocked_note,
                )
            except ValidationError as e:
                self._logger.warning(f"[create_task_tool] Validation error | error={e!s}")
                raise MCPError(str(e)) from e

        # TASK-003: Obtener tarea por ID
        @self.mcp.tool(
            name="taiga_get_task",
            annotations={"readOnlyHint": True},
            description="Get a specific task by its ID",
        )
        async def get_task_tool(auth_token: str, task_id: int) -> dict[str, Any]:
            """
            Get a specific task by its ID.

            Esta herramienta obtiene los detalles completos de una tarea
            específica usando su ID único. Devuelve toda la información
            incluyendo estado, asignaciones, historia asociada y metadatos.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                task_id: ID único de la tarea a obtener

            Returns:
                Dict con los datos completos de la tarea conteniendo:
                - id: ID de la tarea
                - ref: Número de referencia
                - subject: Título de la tarea
                - description: Descripción detallada
                - status: ID del estado
                - status_extra_info: Información adicional del estado
                - user_story: ID de la historia asociada
                - milestone: ID del milestone
                - assigned_to: ID del usuario asignado
                - assigned_to_extra_info: Info del usuario asignado
                - is_blocked: Si está bloqueada
                - blocked_note: Razón de bloqueo
                - is_closed: Si está cerrada
                - tags: Lista de etiquetas
                - watchers: Lista de IDs de observadores
                - total_voters: Número de votantes
                - version: Versión para control de concurrencia

            Raises:
                ToolError: Si la tarea no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> task = await taiga_get_task(
                ...     auth_token="eyJ0eXAiOi...",
                ...     task_id=789
                ... )
                >>> print(task["subject"])
                "Configurar CI/CD"
            """
            return await self.get_task(auth_token=auth_token, task_id=task_id)

        # TASK-004: Obtener tarea por referencia
        @self.mcp.tool(
            name="taiga_get_task_by_ref",
            annotations={"readOnlyHint": True},
            description="Get a specific task by its reference and project",
        )
        async def get_task_by_ref_tool(
            auth_token: str, project_id: int, ref: int
        ) -> dict[str, Any]:
            """
            Get a specific task by its reference number and project.

            Esta herramienta obtiene una tarea usando su número de referencia
            dentro de un proyecto específico. Útil cuando se conoce el ref
            (ej: #123) mostrado en la interfaz de Taiga.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde buscar la tarea
                ref: Número de referencia de la tarea dentro del proyecto

            Returns:
                Dict con los datos completos de la tarea conteniendo:
                - id: ID de la tarea
                - ref: Número de referencia (coincide con el buscado)
                - subject: Título de la tarea
                - description: Descripción detallada
                - status: ID del estado
                - user_story: ID de la historia asociada
                - project: ID del proyecto
                - assigned_to: ID del usuario asignado
                - is_closed: Si está cerrada
                - version: Versión para control de concurrencia

            Raises:
                ToolError: Si la tarea no existe con ese ref en el proyecto,
                    no hay permisos, o la autenticación falla

            Example:
                >>> task = await taiga_get_task_by_ref(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     ref=45
                ... )
                >>> print(task["id"])
                789
            """
            return await self.get_task_by_ref(auth_token=auth_token, project=project_id, ref=ref)

        # TASK-005: Actualizar tarea (completo)
        @self.mcp.tool(
            name="taiga_update_task_full",
            annotations={"idempotentHint": True},
            description="Update a task (full replacement)",
        )
        async def update_task_full_tool(
            auth_token: str,
            task_id: int,
            subject: str,
            project_id: int,
            description: str | None = None,
            user_story_id: int | None = None,
            milestone_id: int | None = None,
            status: int | None = None,
            assigned_to: int | None = None,
            tags: list[str] | None = None,
            is_blocked: bool | None = None,
            blocked_note: str | None = None,
        ) -> dict[str, Any]:
            """
            Update a task with full replacement (PUT).

            Esta herramienta actualiza una tarea reemplazando todos sus campos.
            Los campos no especificados se establecerán a sus valores por defecto.
            Usar taiga_update_task para actualizaciones parciales.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                task_id: ID de la tarea a actualizar
                subject: Nuevo título de la tarea (requerido)
                project_id: ID del proyecto (requerido)
                description: Nueva descripción (opcional)
                user_story_id: Nueva historia de usuario asociada (opcional)
                milestone_id: Nuevo milestone asignado (opcional)
                status: Nuevo ID de estado (opcional)
                assigned_to: Nuevo usuario asignado (opcional)
                tags: Nueva lista de etiquetas (opcional)
                is_blocked: Nuevo estado de bloqueo (opcional)
                blocked_note: Nueva razón de bloqueo (opcional)

            Returns:
                Dict con los datos actualizados de la tarea conteniendo:
                - id: ID de la tarea
                - ref: Número de referencia
                - subject: Título actualizado
                - description: Descripción actualizada
                - status: ID del estado
                - user_story: ID de la historia asociada
                - project: ID del proyecto
                - assigned_to: ID del usuario asignado
                - version: Nueva versión para control de concurrencia

            Raises:
                ToolError: Si la tarea no existe, no hay permisos,
                    hay conflicto de versión, o falla la API

            Example:
                >>> task = await taiga_update_task_full(
                ...     auth_token="eyJ0eXAiOi...",
                ...     task_id=789,
                ...     subject="Configurar CI/CD [Actualizado]",
                ...     project_id=123,
                ...     status=2
                ... )
            """
            try:
                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {
                    "task_id": task_id,
                    "subject": subject,
                    "description": description,
                    "status": status,
                    "assigned_to": assigned_to,
                    "tags": tags,
                }
                validate_input(TaskUpdateValidator, validation_data)

                return await self.update_task_full(
                    auth_token=auth_token,
                    task_id=task_id,
                    subject=subject,
                    project=project_id,  # API expects 'project'
                    description=description,
                    user_story=user_story_id,  # API expects 'user_story'
                    milestone=milestone_id,  # API expects 'milestone'
                    status=status,
                    assigned_to=assigned_to,
                    tags=tags,
                    is_blocked=is_blocked,
                    blocked_note=blocked_note,
                )
            except ValidationError as e:
                self._logger.warning(f"[update_task_full_tool] Validation error | error={e!s}")
                raise MCPError(str(e)) from e

        # TASK-006: Actualizar tarea (parcial)
        @self.mcp.tool(
            name="taiga_update_task",
            annotations={"idempotentHint": True},
            description="Update specific fields of a task (partial update)",
        )
        async def update_task_partial_tool(
            auth_token: str,
            task_id: int,
            subject: str | None = None,
            description: str | None = None,
            user_story_id: int | None = None,
            milestone_id: int | None = None,
            status: int | None = None,
            assigned_to: int | None = None,
            tags: list[str] | None = None,
            is_blocked: bool | None = None,
            blocked_note: str | None = None,
            version: int | None = None,
        ) -> dict[str, Any]:
            """
            Update specific fields of a task (partial update - PATCH).

            Esta herramienta actualiza solo los campos especificados de una tarea,
            manteniendo los demás campos sin cambios. Más eficiente que la
            actualización completa cuando solo se modifican algunos campos.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                task_id: ID de la tarea a actualizar
                subject: Nuevo título de la tarea (opcional)
                description: Nueva descripción (opcional)
                user_story_id: Nueva historia de usuario asociada (opcional)
                milestone_id: Nuevo milestone asignado (opcional)
                status: Nuevo ID de estado (opcional)
                assigned_to: Nuevo usuario asignado (opcional)
                tags: Nueva lista de etiquetas (opcional)
                is_blocked: Nuevo estado de bloqueo (opcional)
                blocked_note: Nueva razón de bloqueo (opcional)
                version: Versión actual para control de concurrencia optimista (opcional)

            Returns:
                Dict con los datos actualizados de la tarea conteniendo:
                - id: ID de la tarea
                - ref: Número de referencia
                - subject: Título (actualizado si se especificó)
                - description: Descripción
                - status: ID del estado
                - user_story: ID de la historia asociada
                - project: ID del proyecto
                - assigned_to: ID del usuario asignado
                - version: Nueva versión para control de concurrencia

            Raises:
                ToolError: Si la tarea no existe, no hay permisos,
                    hay conflicto de versión, o falla la API

            Example:
                >>> task = await taiga_update_task(
                ...     auth_token="eyJ0eXAiOi...",
                ...     task_id=789,
                ...     status=3,
                ...     assigned_to=42
                ... )
                >>> print(task["status"])
                3
            """
            try:
                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {
                    "task_id": task_id,
                    "subject": subject,
                    "description": description,
                    "status": status,
                    "assigned_to": assigned_to,
                    "tags": tags,
                }
                validate_input(TaskUpdateValidator, validation_data)

                return await self.update_task_partial(
                    auth_token=auth_token,
                    task_id=task_id,
                    subject=subject,
                    description=description,
                    user_story=user_story_id,  # API expects 'user_story'
                    milestone=milestone_id,  # API expects 'milestone'
                    status=status,
                    assigned_to=assigned_to,
                    tags=tags,
                    is_blocked=is_blocked,
                    blocked_note=blocked_note,
                    version=version,
                )
            except ValidationError as e:
                self._logger.warning(f"[update_task_partial_tool] Validation error | error={e!s}")
                raise MCPError(str(e)) from e

        # TASK-007: Eliminar tarea
        @self.mcp.tool(
            name="taiga_delete_task",
            annotations={"destructiveHint": True},
            description="Delete a task",
        )
        async def delete_task_tool(auth_token: str, task_id: int) -> dict[str, Any]:
            """
            Delete a task from a project.

            Esta herramienta elimina permanentemente una tarea de Taiga.
            La eliminación es irreversible, por lo que se recomienda
            precaución al usar esta herramienta.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                task_id: ID de la tarea a eliminar

            Returns:
                Dict con confirmación de eliminación conteniendo:
                - success: True si se eliminó correctamente
                - status: "deleted" indicando éxito

            Raises:
                ToolError: Si la tarea no existe, no hay permisos de
                    eliminación, o falla la API

            Example:
                >>> result = await taiga_delete_task(
                ...     auth_token="eyJ0eXAiOi...",
                ...     task_id=789
                ... )
                >>> print(result["success"])
                True
            """
            return await self.delete_task(auth_token=auth_token, task_id=task_id)

        # TASK-008: Crear tareas en lote
        @self.mcp.tool(name="taiga_bulk_create_tasks", description="Create multiple tasks at once")
        async def bulk_create_tasks_tool(
            auth_token: str, project_id: int, bulk_tasks: str
        ) -> list[dict[str, Any]]:
            """
            Create multiple tasks at once from a text block.

            Esta herramienta permite crear múltiples tareas en un solo
            llamado a la API. Cada línea del texto se convierte en una
            tarea independiente. Eficiente para importación masiva.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde crear las tareas
                bulk_tasks: Texto con múltiples tareas, una por línea.
                    Cada línea se convierte en el subject de una tarea.

            Returns:
                Lista de diccionarios con las tareas creadas, cada uno conteniendo:
                - id: ID de la tarea creada
                - ref: Número de referencia
                - subject: Título de la tarea (de la línea de texto)
                - status: ID del estado inicial
                - project: ID del proyecto

            Raises:
                ToolError: Si no hay permisos, el proyecto no existe,
                    o falla la API

            Example:
                >>> tasks = await taiga_bulk_create_tasks(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     bulk_tasks="Tarea 1\\nTarea 2\\nTarea 3"
                ... )
                >>> print(len(tasks))
                3
            """
            return await self.bulk_create_tasks(
                auth_token=auth_token, project_id=project_id, bulk_tasks=bulk_tasks
            )

        # TASK-009: Obtener filtros
        @self.mcp.tool(
            name="taiga_get_task_filters",
            annotations={"readOnlyHint": True},
            description="Get available filters for tasks",
        )
        async def get_task_filters_tool(auth_token: str, project_id: int) -> dict[str, Any]:
            """
            Get available filters for tasks in a project.

            Esta herramienta obtiene todos los valores posibles para filtrar
            tareas en un proyecto específico. Incluye estados, usuarios
            asignados, etiquetas y otros filtros disponibles.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto para obtener los filtros

            Returns:
                Dict con los filtros disponibles conteniendo:
                - statuses: Lista de estados con id y nombre
                - assigned_to: Lista de usuarios asignables
                - owners: Lista de propietarios
                - tags: Lista de etiquetas disponibles
                - roles: Lista de roles disponibles

            Raises:
                ToolError: Si el proyecto no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> filters = await taiga_get_task_filters(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print(filters["statuses"])
                [{"id": 1, "name": "New"}, {"id": 2, "name": "In Progress"}]
            """
            return await self.get_task_filters(auth_token=auth_token, project=project_id)

        # TASK-010: Votar positivo
        @self.mcp.tool(
            name="taiga_upvote_task",
            annotations={"idempotentHint": True},
            description="Add a positive vote to a task",
        )
        async def upvote_task_tool(auth_token: str, task_id: int) -> dict[str, Any]:
            """
            Add a positive vote to a task.

            Esta herramienta añade un voto positivo del usuario autenticado
            a una tarea específica. Los votos ayudan a priorizar tareas
            según el interés del equipo.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                task_id: ID de la tarea a votar

            Returns:
                Dict con información del voto conteniendo:
                - id: ID de la tarea
                - total_voters: Nuevo total de votantes

            Raises:
                ToolError: Si la tarea no existe, ya se votó anteriormente,
                    no hay permisos, o la autenticación falla

            Example:
                >>> result = await taiga_upvote_task(
                ...     auth_token="eyJ0eXAiOi...",
                ...     task_id=789
                ... )
                >>> print(result["total_voters"])
                5
            """
            return await self.upvote_task(auth_token=auth_token, task_id=task_id)

        # TASK-011: Votar negativo
        @self.mcp.tool(
            name="taiga_downvote_task",
            annotations={"idempotentHint": True},
            description="Remove vote from a task",
        )
        async def downvote_task_tool(auth_token: str, task_id: int) -> dict[str, Any]:
            """
            Remove vote from a task.

            Esta herramienta elimina el voto positivo del usuario autenticado
            de una tarea específica. Solo funciona si el usuario había
            votado previamente por la tarea.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                task_id: ID de la tarea de la cual remover el voto

            Returns:
                Dict con información actualizada conteniendo:
                - id: ID de la tarea
                - total_voters: Nuevo total de votantes

            Raises:
                ToolError: Si la tarea no existe, no había voto previo,
                    o la autenticación falla

            Example:
                >>> result = await taiga_downvote_task(
                ...     auth_token="eyJ0eXAiOi...",
                ...     task_id=789
                ... )
                >>> print(result["total_voters"])
                4
            """
            return await self.downvote_task(auth_token=auth_token, task_id=task_id)

        # TASK-012: Obtener votantes
        @self.mcp.tool(
            name="taiga_get_task_voters",
            annotations={"readOnlyHint": True},
            description="Get list of users who voted on a task",
        )
        async def get_task_voters_tool(auth_token: str, task_id: int) -> list[dict[str, Any]]:
            """
            Get list of users who voted on a task.

            Esta herramienta obtiene la lista completa de usuarios que
            han votado positivamente por una tarea específica.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                task_id: ID de la tarea para consultar votantes

            Returns:
                Lista de diccionarios con información de votantes conteniendo:
                - id: ID del usuario
                - username: Nombre de usuario
                - full_name: Nombre completo
                - photo: URL del avatar

            Raises:
                ToolError: Si la tarea no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> voters = await taiga_get_task_voters(
                ...     auth_token="eyJ0eXAiOi...",
                ...     task_id=789
                ... )
                >>> for voter in voters:
                ...     print(voter["username"])
                "alice"
                "bob"
            """
            return await self.get_task_voters(auth_token=auth_token, task_id=task_id)

        # TASK-013: Seguir tarea
        @self.mcp.tool(
            name="taiga_watch_task",
            annotations={"idempotentHint": True},
            description="Start watching a task for updates",
        )
        async def watch_task_tool(auth_token: str, task_id: int) -> dict[str, Any]:
            """
            Start watching a task for updates.

            Esta herramienta suscribe al usuario autenticado para recibir
            notificaciones de cambios en una tarea específica. Los watchers
            son notificados de cualquier modificación en la tarea.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                task_id: ID de la tarea a seguir

            Returns:
                Dict con información de la suscripción conteniendo:
                - id: ID de la tarea
                - total_watchers: Nuevo total de observadores

            Raises:
                ToolError: Si la tarea no existe, ya se está observando,
                    o la autenticación falla

            Example:
                >>> result = await taiga_watch_task(
                ...     auth_token="eyJ0eXAiOi...",
                ...     task_id=789
                ... )
                >>> print(result["total_watchers"])
                3
            """
            return await self.watch_task(auth_token=auth_token, task_id=task_id)

        # TASK-014: Dejar de seguir
        @self.mcp.tool(
            name="taiga_unwatch_task",
            annotations={"idempotentHint": True},
            description="Stop watching a task",
        )
        async def unwatch_task_tool(auth_token: str, task_id: int) -> dict[str, Any]:
            """
            Stop watching a task.

            Esta herramienta cancela la suscripción del usuario autenticado
            para dejar de recibir notificaciones de cambios en una tarea.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                task_id: ID de la tarea a dejar de seguir

            Returns:
                Dict con información actualizada conteniendo:
                - id: ID de la tarea
                - total_watchers: Nuevo total de observadores

            Raises:
                ToolError: Si la tarea no existe, no se estaba observando,
                    o la autenticación falla

            Example:
                >>> result = await taiga_unwatch_task(
                ...     auth_token="eyJ0eXAiOi...",
                ...     task_id=789
                ... )
                >>> print(result["total_watchers"])
                2
            """
            return await self.unwatch_task(auth_token=auth_token, task_id=task_id)

        # TASK-015: Obtener observadores
        @self.mcp.tool(
            name="taiga_get_task_watchers",
            annotations={"readOnlyHint": True},
            description="Get list of users watching a task",
        )
        async def get_task_watchers_tool(auth_token: str, task_id: int) -> list[dict[str, Any]]:
            """
            Get list of users watching a task.

            Esta herramienta obtiene la lista completa de usuarios que
            están observando una tarea y reciben notificaciones de cambios.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                task_id: ID de la tarea para consultar observadores

            Returns:
                Lista de diccionarios con información de watchers conteniendo:
                - id: ID del usuario
                - username: Nombre de usuario
                - full_name: Nombre completo
                - photo: URL del avatar

            Raises:
                ToolError: Si la tarea no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> watchers = await taiga_get_task_watchers(
                ...     auth_token="eyJ0eXAiOi...",
                ...     task_id=789
                ... )
                >>> for watcher in watchers:
                ...     print(watcher["username"])
                "alice"
                "bob"
            """
            return await self.get_task_watchers(auth_token=auth_token, task_id=task_id)

        # TASK-016: Listar adjuntos
        @self.mcp.tool(
            name="taiga_list_task_attachments",
            annotations={"readOnlyHint": True},
            description="List all attachments of a task",
        )
        async def list_task_attachments_tool(
            auth_token: str, project_id: int, task_id: int
        ) -> list[dict[str, Any]]:
            """
            List all attachments of a task.

            Esta herramienta obtiene la lista de todos los archivos adjuntos
            asociados a una tarea específica. Los adjuntos pueden incluir
            imágenes, documentos, archivos de código, etc.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto al que pertenece la tarea
                task_id: ID de la tarea para listar sus adjuntos

            Returns:
                Lista de diccionarios con información de adjuntos conteniendo:
                - id: ID del adjunto
                - name: Nombre del archivo
                - size: Tamaño en bytes
                - url: URL para descargar el archivo
                - description: Descripción del adjunto
                - is_deprecated: Si está marcado como obsoleto
                - created_date: Fecha de creación

            Raises:
                ToolError: Si la tarea no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> attachments = await taiga_list_task_attachments(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     task_id=789
                ... )
                >>> for att in attachments:
                ...     print(att["name"])
                "spec.pdf"
                "mockup.png"
            """
            return await self.list_task_attachments(
                auth_token=auth_token,
                project=project_id,
                task_id=task_id,  # API expects 'project'
            )

        # TASK-017: Crear adjunto
        @self.mcp.tool(
            name="taiga_create_task_attachment", description="Create a new attachment for a task"
        )
        async def create_task_attachment_tool(
            auth_token: str,
            project_id: int,
            task_id: int,
            attached_file: str,
            description: str | None = None,
            is_deprecated: bool | None = False,
        ) -> dict[str, Any]:
            """
            Create a new attachment for a task.

            Esta herramienta permite adjuntar un archivo a una tarea específica.
            Los adjuntos ayudan a documentar la tarea con archivos relevantes
            como especificaciones, mockups, resultados de pruebas, etc.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto al que pertenece la tarea
                task_id: ID de la tarea donde adjuntar el archivo
                attached_file: Ruta o contenido del archivo a adjuntar
                description: Descripción opcional del adjunto
                is_deprecated: Marcar como obsoleto desde el inicio (default: False)

            Returns:
                Dict con información del adjunto creado conteniendo:
                - id: ID del adjunto creado
                - name: Nombre del archivo
                - size: Tamaño en bytes
                - url: URL para descargar el archivo
                - description: Descripción del adjunto
                - created_date: Fecha de creación
                - object_id: ID de la tarea asociada

            Raises:
                ToolError: Si la tarea no existe, no hay permisos,
                    el archivo es inválido, o falla la API

            Example:
                >>> attachment = await taiga_create_task_attachment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     task_id=789,
                ...     attached_file="/path/to/spec.pdf",
                ...     description="Especificación técnica"
                ... )
                >>> print(attachment["id"])
                456
            """
            return await self.create_task_attachment(
                auth_token=auth_token,
                project=project_id,
                task_id=task_id,
                attached_file=attached_file,
                description=description,
                is_deprecated=is_deprecated,
            )

        # TASK-018: Obtener adjunto
        @self.mcp.tool(
            name="taiga_get_task_attachment",
            annotations={"readOnlyHint": True},
            description="Get a specific task attachment",
        )
        async def get_task_attachment_tool(auth_token: str, attachment_id: int) -> dict[str, Any]:
            """
            Get a specific task attachment by ID.

            Esta herramienta obtiene los detalles de un adjunto específico
            de una tarea usando su ID único.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                attachment_id: ID del adjunto a obtener

            Returns:
                Dict con información del adjunto conteniendo:
                - id: ID del adjunto
                - name: Nombre del archivo
                - size: Tamaño en bytes
                - url: URL para descargar el archivo
                - description: Descripción del adjunto
                - is_deprecated: Si está marcado como obsoleto
                - created_date: Fecha de creación
                - modified_date: Fecha de última modificación
                - object_id: ID de la tarea asociada

            Raises:
                ToolError: Si el adjunto no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> attachment = await taiga_get_task_attachment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     attachment_id=456
                ... )
                >>> print(attachment["name"])
                "spec.pdf"
            """
            return await self.get_task_attachment(
                auth_token=auth_token, attachment_id=attachment_id
            )

        # TASK-019: Actualizar adjunto
        @self.mcp.tool(
            name="taiga_update_task_attachment",
            annotations={"idempotentHint": True},
            description="Update a task attachment",
        )
        async def update_task_attachment_tool(
            auth_token: str,
            attachment_id: int,
            description: str | None = None,
            is_deprecated: bool | None = None,
        ) -> dict[str, Any]:
            """
            Update a task attachment.

            Esta herramienta actualiza los metadatos de un adjunto existente.
            Se puede modificar la descripción o marcar el adjunto como obsoleto.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                attachment_id: ID del adjunto a actualizar
                description: Nueva descripción del adjunto (opcional)
                is_deprecated: Marcar como obsoleto (opcional)

            Returns:
                Dict con información del adjunto actualizado conteniendo:
                - id: ID del adjunto
                - name: Nombre del archivo
                - description: Descripción actualizada
                - is_deprecated: Estado de obsolescencia
                - modified_date: Nueva fecha de modificación

            Raises:
                ToolError: Si el adjunto no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> attachment = await taiga_update_task_attachment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     attachment_id=456,
                ...     description="Especificación técnica v2",
                ...     is_deprecated=False
                ... )
            """
            return await self.update_task_attachment(
                auth_token=auth_token,
                attachment_id=attachment_id,
                description=description,
                is_deprecated=is_deprecated,
            )

        # TASK-020: Eliminar adjunto
        @self.mcp.tool(
            name="taiga_delete_task_attachment",
            annotations={"destructiveHint": True},
            description="Delete a task attachment",
        )
        async def delete_task_attachment_tool(
            auth_token: str, attachment_id: int
        ) -> dict[str, Any]:
            """
            Delete a task attachment.

            Esta herramienta elimina permanentemente un adjunto de una tarea.
            La eliminación es irreversible.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                attachment_id: ID del adjunto a eliminar

            Returns:
                Dict con confirmación de eliminación conteniendo:
                - status: "deleted" indicando éxito
                - attachment_id: ID del adjunto eliminado

            Raises:
                ToolError: Si el adjunto no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> result = await taiga_delete_task_attachment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     attachment_id=456
                ... )
                >>> print(result["status"])
                "deleted"
            """
            return await self.delete_task_attachment(
                auth_token=auth_token, attachment_id=attachment_id
            )

        # TASK-021: Obtener historial
        @self.mcp.tool(
            name="taiga_get_task_history",
            annotations={"readOnlyHint": True},
            description="Get the history of changes for a task",
        )
        async def get_task_history_tool(auth_token: str, task_id: int) -> list[dict[str, Any]]:
            """
            Get the history of changes for a task.

            Esta herramienta obtiene el registro completo de todos los cambios
            realizados en una tarea, incluyendo modificaciones de campos,
            comentarios y asignaciones.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                task_id: ID de la tarea para consultar su historial

            Returns:
                Lista de diccionarios con entradas del historial conteniendo:
                - id: ID de la entrada en el historial
                - user: Información del usuario que hizo el cambio
                - created_at: Fecha y hora del cambio
                - type: Tipo de cambio (1=modificación, 2=comentario)
                - values_diff: Diccionario con los campos modificados
                - comment: Texto del comentario si aplica
                - delete_comment_date: Fecha de eliminación si fue borrado

            Raises:
                ToolError: Si la tarea no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> history = await taiga_get_task_history(
                ...     auth_token="eyJ0eXAiOi...",
                ...     task_id=789
                ... )
                >>> for entry in history:
                ...     print(entry["created_at"], entry["type"])
            """
            return await self.get_task_history(auth_token=auth_token, task_id=task_id)

        # TASK-022: Obtener versiones de comentario
        @self.mcp.tool(
            name="taiga_get_task_comment_versions",
            annotations={"readOnlyHint": True},
            description="Get all versions of a task comment",
        )
        async def get_task_comment_versions_tool(
            auth_token: str, task_id: int, comment_id: str
        ) -> list[dict[str, Any]]:
            """
            Get all versions of a task comment.

            Esta herramienta obtiene el historial completo de ediciones
            de un comentario específico en una tarea. Cada edición se
            guarda como una versión independiente.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                task_id: ID de la tarea que contiene el comentario
                comment_id: ID del comentario para consultar sus versiones

            Returns:
                Lista de diccionarios con versiones del comentario conteniendo:
                - id: ID de la versión
                - comment: Texto del comentario en esa versión
                - created_at: Fecha de creación de la versión
                - user: Información del usuario que editó

            Raises:
                ToolError: Si la tarea o comentario no existen, no hay permisos,
                    o la autenticación falla

            Example:
                >>> versions = await taiga_get_task_comment_versions(
                ...     auth_token="eyJ0eXAiOi...",
                ...     task_id=789,
                ...     comment_id="abc123"
                ... )
                >>> for v in versions:
                ...     print(v["created_at"], v["comment"][:50])
            """
            return await self.get_task_comment_versions(
                auth_token=auth_token, task_id=task_id, comment_id=comment_id
            )

        # TASK-023: Editar comentario
        @self.mcp.tool(name="taiga_edit_task_comment", description="Edit a task comment")
        async def edit_task_comment_tool(
            auth_token: str, task_id: int, comment_id: str, comment: str
        ) -> dict[str, Any]:
            """
            Edit a task comment.

            Esta herramienta permite modificar el texto de un comentario
            existente en una tarea. La versión anterior se guarda en el
            historial de versiones del comentario.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                task_id: ID de la tarea que contiene el comentario
                comment_id: ID del comentario a editar
                comment: Nuevo texto del comentario

            Returns:
                Dict con información del comentario editado conteniendo:
                - id: ID del comentario
                - comment: Nuevo texto del comentario
                - modified_date: Fecha de la modificación
                - user: Usuario que editó

            Raises:
                ToolError: Si la tarea o comentario no existen, no hay permisos
                    para editar, o la autenticación falla

            Example:
                >>> result = await taiga_edit_task_comment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     task_id=789,
                ...     comment_id="abc123",
                ...     comment="Texto corregido del comentario"
                ... )
            """
            return await self.edit_task_comment(
                auth_token=auth_token, task_id=task_id, comment_id=comment_id, comment=comment
            )

        # TASK-024: Eliminar comentario
        @self.mcp.tool(
            name="taiga_delete_task_comment",
            annotations={"destructiveHint": True},
            description="Delete a task comment",
        )
        async def delete_task_comment_tool(
            auth_token: str, task_id: int, comment_id: str
        ) -> dict[str, Any]:
            """
            Delete a task comment.

            Esta herramienta elimina un comentario de una tarea. El comentario
            puede ser recuperado posteriormente usando taiga_undelete_task_comment
            mientras no se elimine permanentemente.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                task_id: ID de la tarea que contiene el comentario
                comment_id: ID del comentario a eliminar

            Returns:
                Dict con confirmación de eliminación conteniendo:
                - status: "deleted" indicando éxito
                - comment_id: ID del comentario eliminado

            Raises:
                ToolError: Si la tarea o comentario no existen, no hay permisos,
                    o la autenticación falla

            Example:
                >>> result = await taiga_delete_task_comment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     task_id=789,
                ...     comment_id="abc123"
                ... )
                >>> print(result["status"])
                "deleted"
            """
            return await self.delete_task_comment(
                auth_token=auth_token, task_id=task_id, comment_id=comment_id
            )

        # TASK-025: Recuperar comentario
        @self.mcp.tool(
            name="taiga_undelete_task_comment",
            description="Undelete a previously deleted task comment",
        )
        async def undelete_task_comment_tool(
            auth_token: str, task_id: int, comment_id: str
        ) -> dict[str, Any]:
            """
            Undelete a previously deleted task comment.

            Esta herramienta recupera un comentario que fue eliminado
            previamente usando taiga_delete_task_comment. Restaura el
            comentario con todo su historial de versiones.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                task_id: ID de la tarea que contiene el comentario
                comment_id: ID del comentario a recuperar

            Returns:
                Dict con información del comentario recuperado conteniendo:
                - id: ID del comentario
                - comment: Texto del comentario restaurado
                - created_at: Fecha original de creación
                - user: Usuario que creó el comentario

            Raises:
                ToolError: Si la tarea o comentario no existen, el comentario
                    no estaba eliminado, no hay permisos, o falla la autenticación

            Example:
                >>> result = await taiga_undelete_task_comment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     task_id=789,
                ...     comment_id="abc123"
                ... )
                >>> print(result["comment"])
                "Comentario restaurado"
            """
            return await self.undelete_task_comment(
                auth_token=auth_token, task_id=task_id, comment_id=comment_id
            )

        # TASK-026: Listar atributos personalizados
        @self.mcp.tool(
            name="taiga_list_task_custom_attributes",
            annotations={"readOnlyHint": True},
            description="List custom attributes for tasks in a project",
        )
        async def list_task_custom_attributes_tool(
            auth_token: str, project_id: int
        ) -> dict[str, Any]:
            """
            List custom attributes for tasks in a project.

            Esta herramienta obtiene todos los atributos personalizados
            definidos para las tareas de un proyecto. Los atributos
            personalizados permiten extender el modelo de datos.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto para listar sus atributos

            Returns:
                Dict o lista con los atributos personalizados conteniendo:
                - id: ID del atributo
                - name: Nombre del atributo
                - description: Descripción del atributo
                - type: Tipo de campo (text, url, date, etc.)
                - order: Orden de visualización
                - project: ID del proyecto

            Raises:
                ToolError: Si el proyecto no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> attrs = await taiga_list_task_custom_attributes(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> for attr in attrs:
                ...     print(attr["name"], attr["type"])
            """
            return await self.list_task_custom_attributes(auth_token=auth_token, project=project_id)

        # TASK-027: Crear atributo personalizado
        @self.mcp.tool(
            name="taiga_create_task_custom_attribute",
            description="Create a new custom attribute for tasks",
        )
        async def create_task_custom_attribute_tool(
            auth_token: str,
            project_id: int,
            name: str,
            description: str | None = None,
            field_type: str | None = "text",
        ) -> dict[str, Any]:
            """
            Create a new custom attribute for tasks.

            Esta herramienta crea un nuevo atributo personalizado que
            estará disponible para todas las tareas del proyecto.
            Permite extender el modelo de datos según necesidades específicas.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde crear el atributo
                name: Nombre del nuevo atributo (requerido)
                description: Descripción del propósito del atributo (opcional)
                field_type: Tipo de campo (text, url, date, number, etc.)
                    Por defecto es "text"

            Returns:
                Dict con información del atributo creado conteniendo:
                - id: ID del atributo creado
                - name: Nombre del atributo
                - description: Descripción
                - type: Tipo de campo
                - order: Orden de visualización
                - project: ID del proyecto

            Raises:
                ToolError: Si el proyecto no existe, no hay permisos de admin,
                    o la autenticación falla

            Example:
                >>> attr = await taiga_create_task_custom_attribute(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     name="Tiempo Estimado",
                ...     description="Horas estimadas para completar",
                ...     field_type="number"
                ... )
                >>> print(attr["id"])
                456
            """
            return await self.create_task_custom_attribute(
                auth_token=auth_token,
                project=project_id,  # API expects 'project'
                name=name,
                description=description,
                field_type=field_type,
            )

        # TASK-028: Actualizar atributo personalizado
        @self.mcp.tool(
            name="taiga_update_task_custom_attribute",
            annotations={"idempotentHint": True},
            description="Update a custom attribute for tasks",
        )
        async def update_task_custom_attribute_tool(
            auth_token: str,
            attribute_id: int,
            name: str | None = None,
            description: str | None = None,
        ) -> dict[str, Any]:
            """
            Update a custom attribute for tasks.

            Esta herramienta actualiza los metadatos de un atributo
            personalizado existente. Se puede modificar el nombre y/o
            la descripción del atributo.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                attribute_id: ID del atributo a actualizar
                name: Nuevo nombre del atributo (opcional)
                description: Nueva descripción del atributo (opcional)

            Returns:
                Dict con información del atributo actualizado conteniendo:
                - id: ID del atributo
                - name: Nombre actualizado
                - description: Descripción actualizada
                - type: Tipo de campo
                - order: Orden de visualización

            Raises:
                ToolError: Si el atributo no existe, no hay permisos de admin,
                    o la autenticación falla

            Example:
                >>> attr = await taiga_update_task_custom_attribute(
                ...     auth_token="eyJ0eXAiOi...",
                ...     attribute_id=456,
                ...     name="Tiempo Estimado (horas)",
                ...     description="Horas de trabajo estimadas"
                ... )
            """
            return await self.update_task_custom_attribute(
                auth_token=auth_token, attribute_id=attribute_id, name=name, description=description
            )

        # TASK-029: Eliminar atributo personalizado
        @self.mcp.tool(
            name="taiga_delete_task_custom_attribute",
            annotations={"destructiveHint": True},
            description="Delete a custom attribute for tasks",
        )
        async def delete_task_custom_attribute_tool(
            auth_token: str, attribute_id: int
        ) -> dict[str, Any]:
            """
            Delete a custom attribute for tasks.

            Esta herramienta elimina permanentemente un atributo personalizado
            del proyecto. También elimina todos los valores de ese atributo
            en las tareas existentes.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                attribute_id: ID del atributo a eliminar

            Returns:
                Dict con confirmación de eliminación conteniendo:
                - status: "deleted" indicando éxito
                - attribute_id: ID del atributo eliminado

            Raises:
                ToolError: Si el atributo no existe, no hay permisos de admin,
                    o la autenticación falla

            Example:
                >>> result = await taiga_delete_task_custom_attribute(
                ...     auth_token="eyJ0eXAiOi...",
                ...     attribute_id=456
                ... )
                >>> print(result["status"])
                "deleted"
            """
            return await self.delete_task_custom_attribute(
                auth_token=auth_token, attribute_id=attribute_id
            )

    # Métodos de implementación

    async def list_tasks(self, auth_token: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Lista todas las tareas con filtros opcionales."""
        kwargs.pop("auth_token", None)
        auto_paginate = kwargs.pop("auto_paginate", True)
        project = kwargs.get("project")
        self._logger.debug(f"[list_tasks] Starting | project={project}")
        try:
            # Remove None values from kwargs
            params = {k: v for k, v in kwargs.items() if v is not None}

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                paginator = AutoPaginator(client, PaginationConfig())

                if auto_paginate:
                    result = await paginator.paginate("/tasks", params=params)
                else:
                    result = await paginator.paginate_first_page("/tasks", params=params)
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(f"[list_tasks] Success | project={project}, count={count}")
            return result
        except Exception as e:
            self._logger.error(f"[list_tasks] Error | project={project}, error={e!s}")
            raise

    async def create_task(self, auth_token: str, **kwargs: Any) -> dict[str, Any]:
        """Crea una nueva tarea."""
        kwargs.pop("auth_token", None)
        project = kwargs.get("project")
        subject = kwargs.get("subject")
        self._logger.debug(f"[create_task] Starting | project={project}, subject={subject}")
        # Según los tests, project, user_story y subject son requeridos
        if "project" not in kwargs or "user_story" not in kwargs or "subject" not in kwargs:
            self._logger.warning("[create_task] Missing required fields")
            raise ValueError("project, user_story and subject are required")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.create_task(**kwargs)
            task_id = result.get("id") if isinstance(result, dict) else None
            self._logger.info(f"[create_task] Success | project={project}, task_id={task_id}")
            return result
        except Exception as e:
            self._logger.error(f"[create_task] Error | project={project}, error={e!s}")
            raise

    async def get_task(self, auth_token: str, task_id: int) -> dict[str, Any]:
        """Obtiene una tarea por ID."""
        self._logger.debug(f"[get_task] Starting | task_id={task_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.get_task(task_id=task_id)
            self._logger.info(f"[get_task] Success | task_id={task_id}")
            return result
        except Exception as e:
            self._logger.error(f"[get_task] Error | task_id={task_id}, error={e!s}")
            raise

    async def get_task_by_ref(self, auth_token: str, project: int, ref: int) -> dict[str, Any]:
        """Obtiene una tarea por referencia y proyecto."""
        self._logger.debug(f"[get_task_by_ref] Starting | project={project}, ref={ref}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.get_task_by_ref(ref=ref, project=project)
            self._logger.info(f"[get_task_by_ref] Success | project={project}, ref={ref}")
            return result
        except Exception as e:
            self._logger.error(
                f"[get_task_by_ref] Error | project={project}, ref={ref}, error={e!s}"
            )
            raise

    async def update_task_full(
        self, auth_token: str, task_id: int, **kwargs: Any
    ) -> dict[str, Any]:
        """Actualiza una tarea (reemplazo completo)."""
        kwargs.pop("auth_token", None)
        kwargs.pop("task_id", None)
        self._logger.debug(f"[update_task_full] Starting | task_id={task_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                # El test no requiere project y subject como obligatorios
                result = await client.update_task_full(task_id=task_id, **kwargs)
            self._logger.info(f"[update_task_full] Success | task_id={task_id}")
            return result
        except Exception as e:
            self._logger.error(f"[update_task_full] Error | task_id={task_id}, error={e!s}")
            raise

    async def update_task_partial(
        self, auth_token: str, task_id: int, **kwargs: Any
    ) -> dict[str, Any]:
        """Actualiza campos específicos de una tarea."""
        kwargs.pop("auth_token", None)
        kwargs.pop("task_id", None)
        self._logger.debug(f"[update_task_partial] Starting | task_id={task_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                # Remove None values for partial update
                update_data = {k: v for k, v in kwargs.items() if v is not None}
                result = await client.update_task(task_id=task_id, **update_data)
            self._logger.info(f"[update_task_partial] Success | task_id={task_id}")
            return result
        except Exception as e:
            self._logger.error(f"[update_task_partial] Error | task_id={task_id}, error={e!s}")
            raise

    # Alias para update_task_partial
    async def update_task(self, auth_token: str, task_id: int, **kwargs: Any) -> dict[str, Any]:
        """Alias para update_task_partial."""
        return await self.update_task_partial(auth_token, task_id, **kwargs)

    async def delete_task(self, auth_token: str, task_id: int) -> dict[str, Any]:
        """Elimina una tarea."""
        self._logger.debug(f"[delete_task] Starting | task_id={task_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.delete_task(task_id=task_id)
            self._logger.info(f"[delete_task] Success | task_id={task_id}")
            # Si el cliente devuelve un dict, retornarlo; si no, devolver un dict de confirmación
            if isinstance(result, dict):
                return result
            return {"success": "true", "message": f"Task {task_id} deleted successfully"}
        except Exception as e:
            self._logger.error(f"[delete_task] Error | task_id={task_id}, error={e!s}")
            raise

    async def bulk_create_tasks(
        self, auth_token: str, project_id: int, **kwargs
    ) -> list[dict[str, Any]]:
        """Crea múltiples tareas desde un bloque de texto o lista."""
        kwargs.pop("auth_token", None)
        self._logger.debug(f"[bulk_create_tasks] Starting | project_id={project_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                # Soportar tanto bulk_tasks como lista simple
                result = await client.bulk_create_tasks(project_id=project_id, **kwargs)
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(
                f"[bulk_create_tasks] Success | project_id={project_id}, count={count}"
            )
            return result
        except Exception as e:
            self._logger.error(f"[bulk_create_tasks] Error | project_id={project_id}, error={e!s}")
            raise

    async def get_task_filters(self, auth_token: str, project: int) -> dict[str, Any]:
        """Obtiene los filtros disponibles para tareas."""
        self._logger.debug(f"[get_task_filters] Starting | project={project}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.get_task_filters(project=project)
            self._logger.info(f"[get_task_filters] Success | project={project}")
            return result
        except Exception as e:
            self._logger.error(f"[get_task_filters] Error | project={project}, error={e!s}")
            raise

    async def upvote_task(self, auth_token: str, task_id: int) -> dict[str, Any]:
        """Añade un voto positivo a una tarea."""
        self._logger.debug(f"[upvote_task] Starting | task_id={task_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.upvote_task(task_id=task_id)
            self._logger.info(f"[upvote_task] Success | task_id={task_id}")
            return result
        except Exception as e:
            self._logger.error(f"[upvote_task] Error | task_id={task_id}, error={e!s}")
            raise

    async def downvote_task(self, auth_token: str, task_id: int) -> dict[str, Any]:
        """Elimina el voto de una tarea."""
        self._logger.debug(f"[downvote_task] Starting | task_id={task_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.downvote_task(task_id=task_id)
            self._logger.info(f"[downvote_task] Success | task_id={task_id}")
            return result
        except Exception as e:
            self._logger.error(f"[downvote_task] Error | task_id={task_id}, error={e!s}")
            raise

    async def get_task_voters(self, auth_token: str, task_id: int) -> list[dict[str, Any]]:
        """Obtiene la lista de votantes de una tarea."""
        self._logger.debug(f"[get_task_voters] Starting | task_id={task_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.get_task_voters(task_id=task_id)
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(f"[get_task_voters] Success | task_id={task_id}, count={count}")
            return result
        except Exception as e:
            self._logger.error(f"[get_task_voters] Error | task_id={task_id}, error={e!s}")
            raise

    async def watch_task(self, auth_token: str, task_id: int) -> dict[str, Any]:
        """Comienza a seguir una tarea."""
        self._logger.debug(f"[watch_task] Starting | task_id={task_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.watch_task(task_id=task_id)
            self._logger.info(f"[watch_task] Success | task_id={task_id}")
            return result
        except Exception as e:
            self._logger.error(f"[watch_task] Error | task_id={task_id}, error={e!s}")
            raise

    async def unwatch_task(self, auth_token: str, task_id: int) -> dict[str, Any]:
        """Deja de seguir una tarea."""
        self._logger.debug(f"[unwatch_task] Starting | task_id={task_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.unwatch_task(task_id=task_id)
            self._logger.info(f"[unwatch_task] Success | task_id={task_id}")
            return result
        except Exception as e:
            self._logger.error(f"[unwatch_task] Error | task_id={task_id}, error={e!s}")
            raise

    async def get_task_watchers(self, auth_token: str, task_id: int) -> list[dict[str, Any]]:
        """Obtiene la lista de observadores de una tarea."""
        self._logger.debug(f"[get_task_watchers] Starting | task_id={task_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.get_task_watchers(task_id=task_id)
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(f"[get_task_watchers] Success | task_id={task_id}, count={count}")
            return result
        except Exception as e:
            self._logger.error(f"[get_task_watchers] Error | task_id={task_id}, error={e!s}")
            raise

    async def list_task_attachments(self, auth_token: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Lista todos los adjuntos de una tarea."""
        kwargs.pop("auth_token", None)
        # Soportar task_id como alias de object_id
        if "task_id" in kwargs:
            kwargs["object_id"] = kwargs.pop("task_id")
        task_id = kwargs.get("object_id")
        self._logger.debug(f"[list_task_attachments] Starting | task_id={task_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.list_task_attachments(**kwargs)
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(f"[list_task_attachments] Success | task_id={task_id}, count={count}")
            return result
        except Exception as e:
            self._logger.error(f"[list_task_attachments] Error | task_id={task_id}, error={e!s}")
            raise

    async def create_task_attachment(self, auth_token: str, **kwargs: Any) -> dict[str, Any]:
        """Crea un nuevo adjunto para una tarea."""
        kwargs.pop("auth_token", None)
        # Soportar task_id como alias de object_id
        if "task_id" in kwargs:
            kwargs["object_id"] = kwargs.pop("task_id")
        task_id = kwargs.get("object_id")
        self._logger.debug(f"[create_task_attachment] Starting | task_id={task_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.create_task_attachment(**kwargs)
            attachment_id = result.get("id") if isinstance(result, dict) else None
            self._logger.info(
                f"[create_task_attachment] Success | task_id={task_id}, attachment_id={attachment_id}"
            )
            return result
        except Exception as e:
            self._logger.error(f"[create_task_attachment] Error | task_id={task_id}, error={e!s}")
            raise

    async def get_task_attachment(self, auth_token: str, attachment_id: int) -> dict[str, Any]:
        """Obtiene un adjunto específico de tarea."""
        self._logger.debug(f"[get_task_attachment] Starting | attachment_id={attachment_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.get_task_attachment(attachment_id=attachment_id)
            self._logger.info(f"[get_task_attachment] Success | attachment_id={attachment_id}")
            return result
        except Exception as e:
            self._logger.error(
                f"[get_task_attachment] Error | attachment_id={attachment_id}, error={e!s}"
            )
            raise

    async def update_task_attachment(
        self, auth_token: str, attachment_id: int, **kwargs
    ) -> dict[str, Any]:
        """Actualiza un adjunto de tarea."""
        kwargs.pop("auth_token", None)
        kwargs.pop("attachment_id", None)
        self._logger.debug(f"[update_task_attachment] Starting | attachment_id={attachment_id}")
        try:
            update_data = {k: v for k, v in kwargs.items() if v is not None}
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.update_task_attachment(
                    attachment_id=attachment_id, **update_data
                )
            self._logger.info(f"[update_task_attachment] Success | attachment_id={attachment_id}")
            return result
        except Exception as e:
            self._logger.error(
                f"[update_task_attachment] Error | attachment_id={attachment_id}, error={e!s}"
            )
            raise

    async def delete_task_attachment(self, auth_token: str, attachment_id: int) -> dict[str, Any]:
        """Elimina un adjunto de tarea."""
        self._logger.debug(f"[delete_task_attachment] Starting | attachment_id={attachment_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                await client.delete_task_attachment(attachment_id=attachment_id)
            self._logger.info(f"[delete_task_attachment] Success | attachment_id={attachment_id}")
            return {"status": "deleted", "attachment_id": str(attachment_id)}
        except Exception as e:
            self._logger.error(
                f"[delete_task_attachment] Error | attachment_id={attachment_id}, error={e!s}"
            )
            raise

    async def get_task_history(self, auth_token: str, task_id: int) -> list[dict[str, Any]]:
        """Obtiene el historial de cambios de una tarea."""
        self._logger.debug(f"[get_task_history] Starting | task_id={task_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.get_task_history(task_id=task_id)
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(f"[get_task_history] Success | task_id={task_id}, count={count}")
            return result
        except Exception as e:
            self._logger.error(f"[get_task_history] Error | task_id={task_id}, error={e!s}")
            raise

    async def get_task_comment_versions(
        self, auth_token: str, task_id: int, comment_id: str
    ) -> list[dict[str, Any]]:
        """Obtiene todas las versiones de un comentario."""
        self._logger.debug(
            f"[get_task_comment_versions] Starting | task_id={task_id}, comment_id={comment_id}"
        )
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.get_task_comment_versions(
                    task_id=task_id, comment_id=comment_id
                )
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(
                f"[get_task_comment_versions] Success | task_id={task_id}, count={count}"
            )
            return result
        except Exception as e:
            self._logger.error(
                f"[get_task_comment_versions] Error | task_id={task_id}, comment_id={comment_id}, error={e!s}"
            )
            raise

    async def edit_task_comment(
        self, auth_token: str, task_id: int, comment_id: str, comment: str
    ) -> dict[str, Any]:
        """Edita un comentario de tarea."""
        self._logger.debug(
            f"[edit_task_comment] Starting | task_id={task_id}, comment_id={comment_id}"
        )
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.edit_task_comment(
                    task_id=task_id, comment_id=comment_id, comment=comment
                )
            self._logger.info(
                f"[edit_task_comment] Success | task_id={task_id}, comment_id={comment_id}"
            )
            return result
        except Exception as e:
            self._logger.error(
                f"[edit_task_comment] Error | task_id={task_id}, comment_id={comment_id}, error={e!s}"
            )
            raise

    async def delete_task_comment(
        self, auth_token: str, task_id: int, comment_id: str
    ) -> dict[str, Any]:
        """Elimina un comentario de tarea."""
        self._logger.debug(
            f"[delete_task_comment] Starting | task_id={task_id}, comment_id={comment_id}"
        )
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                await client.delete_task_comment(task_id=task_id, comment_id=comment_id)
            self._logger.info(
                f"[delete_task_comment] Success | task_id={task_id}, comment_id={comment_id}"
            )
            return {"status": "deleted", "comment_id": comment_id}
        except Exception as e:
            self._logger.error(
                f"[delete_task_comment] Error | task_id={task_id}, comment_id={comment_id}, error={e!s}"
            )
            raise

    async def undelete_task_comment(
        self, auth_token: str, task_id: int, comment_id: str
    ) -> dict[str, Any]:
        """Recupera un comentario eliminado."""
        self._logger.debug(
            f"[undelete_task_comment] Starting | task_id={task_id}, comment_id={comment_id}"
        )
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.undelete_task_comment(task_id=task_id, comment_id=comment_id)
            self._logger.info(
                f"[undelete_task_comment] Success | task_id={task_id}, comment_id={comment_id}"
            )
            return result
        except Exception as e:
            self._logger.error(
                f"[undelete_task_comment] Error | task_id={task_id}, comment_id={comment_id}, error={e!s}"
            )
            raise

    async def list_task_custom_attributes(self, auth_token: str, project: int) -> dict[str, Any]:
        """Lista los atributos personalizados de tareas."""
        self._logger.debug(f"[list_task_custom_attributes] Starting | project={project}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.list_task_custom_attributes(project=project)
            self._logger.info(f"[list_task_custom_attributes] Success | project={project}")
            return result
        except Exception as e:
            self._logger.error(
                f"[list_task_custom_attributes] Error | project={project}, error={e!s}"
            )
            raise

    async def create_task_custom_attribute(self, auth_token: str, **kwargs: Any) -> dict[str, Any]:
        """Crea un nuevo atributo personalizado."""
        kwargs.pop("auth_token", None)
        project = kwargs.get("project")
        name = kwargs.get("name")
        self._logger.debug(
            f"[create_task_custom_attribute] Starting | project={project}, name={name}"
        )
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.create_task_custom_attribute(**kwargs)
            attr_id = result.get("id") if isinstance(result, dict) else None
            self._logger.info(
                f"[create_task_custom_attribute] Success | project={project}, attribute_id={attr_id}"
            )
            return result
        except Exception as e:
            self._logger.error(
                f"[create_task_custom_attribute] Error | project={project}, error={e!s}"
            )
            raise

    async def update_task_custom_attribute(
        self, auth_token: str, attribute_id: int, **kwargs
    ) -> dict[str, Any]:
        """Actualiza un atributo personalizado."""
        kwargs.pop("auth_token", None)
        kwargs.pop("attribute_id", None)
        self._logger.debug(f"[update_task_custom_attribute] Starting | attribute_id={attribute_id}")
        try:
            update_data = {k: v for k, v in kwargs.items() if v is not None}
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                result = await client.update_task_custom_attribute(attribute_id, **update_data)
            self._logger.info(
                f"[update_task_custom_attribute] Success | attribute_id={attribute_id}"
            )
            return result
        except Exception as e:
            self._logger.error(
                f"[update_task_custom_attribute] Error | attribute_id={attribute_id}, error={e!s}"
            )
            raise

    async def delete_task_custom_attribute(
        self, auth_token: str, attribute_id: int
    ) -> dict[str, Any]:
        """Elimina un atributo personalizado."""
        self._logger.debug(f"[delete_task_custom_attribute] Starting | attribute_id={attribute_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                await client.delete_task_custom_attribute(attribute_id)
            self._logger.info(
                f"[delete_task_custom_attribute] Success | attribute_id={attribute_id}"
            )
            return {"status": "deleted", "attribute_id": str(attribute_id)}
        except Exception as e:
            self._logger.error(
                f"[delete_task_custom_attribute] Error | attribute_id={attribute_id}, error={e!s}"
            )
            raise
