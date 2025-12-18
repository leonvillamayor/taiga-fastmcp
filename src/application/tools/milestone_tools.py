"""
Herramientas para gestión de Milestones/Sprints en Taiga.

Este módulo implementa todas las operaciones relacionadas con hitos/sprints
siguiendo los principios de Domain Driven Design (DDD).

Funcionalidades implementadas:
- MILE-001: Listar milestones con filtros opcionales
- MILE-002: Crear nuevo milestone
- MILE-003: Obtener milestone por ID
- MILE-004: Actualizar milestone (reemplazo completo)
- MILE-005: Actualizar milestone (parcial)
- MILE-006: Eliminar milestone
- MILE-007: Obtener estadísticas del milestone
- MILE-008: Seguir milestone
- MILE-009: Dejar de seguir milestone
- MILE-010: Obtener observadores del milestone
"""

from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError as MCPError

from src.config import TaigaConfig
from src.domain.exceptions import ValidationError
from src.domain.validators import MilestoneCreateValidator, MilestoneUpdateValidator, validate_input
from src.infrastructure.logging import get_logger
from src.infrastructure.pagination import AutoPaginator, PaginationConfig
from src.taiga_client import TaigaAPIClient


class MilestoneTools:
    """
    Herramientas para gestión de Milestones/Sprints en Taiga.

    Esta clase implementa la capa de aplicación para las operaciones de milestones,
    actuando como intermediario entre la capa de presentación (MCP) y el cliente
    de dominio de Taiga.
    """

    def __init__(self, mcp: FastMCP) -> None:
        """
        Inicializa las herramientas de milestones.

        Args:
            mcp: Instancia del servidor MCP para registro de herramientas
        """
        self.mcp = mcp
        self.config = TaigaConfig()
        self._logger = get_logger("milestone_tools")
        self._register_tools()

    def _register_tools(self) -> None:
        """Registra todas las herramientas de milestones en el servidor MCP."""

        # MILE-001: Listar milestones
        @self.mcp.tool(
            name="taiga_list_milestones",
            annotations={"readOnlyHint": True},
            description="List all milestones/sprints in a Taiga project with optional filters",
        )
        async def list_milestones_tool(
            auth_token: str,
            project_id: int | None = None,
            closed: bool | None = None,
            auto_paginate: bool = True,
        ) -> list[dict[str, Any]]:
            """
            List all milestones/sprints with optional filters.

            Esta herramienta lista todos los milestones (sprints) de un proyecto
            en Taiga, con filtros opcionales por proyecto y estado de cierre.
            Los milestones organizan el trabajo en iteraciones temporales.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto para filtrar milestones (opcional)
                closed: Filtrar por estado cerrado/abierto (opcional).
                    True para solo cerrados, False para solo abiertos.
                auto_paginate: Si True (default), obtiene todos los resultados
                    automáticamente. Si False, retorna solo la primera página.

            Returns:
                Lista de diccionarios con información de milestones, cada uno
                conteniendo:
                - id: ID del milestone
                - name: Nombre del sprint
                - slug: Slug único del milestone
                - project: ID del proyecto
                - estimated_start: Fecha de inicio planificada
                - estimated_finish: Fecha de fin planificada
                - closed: True si el sprint está cerrado
                - disponibility: Disponibilidad del equipo (horas/puntos)
                - total_points: Puntos totales asignados
                - closed_points: Puntos completados

            Raises:
                ToolError: Si el proyecto no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> milestones = await taiga_list_milestones(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     closed=False
                ... )
                >>> print(milestones)
                [
                    {
                        "id": 1,
                        "name": "Sprint 1",
                        "estimated_start": "2024-01-01",
                        "estimated_finish": "2024-01-15",
                        "closed": False,
                        "total_points": 50
                    }
                ]
            """
            return await self.list_milestones(
                auth_token=auth_token,
                project=project_id,
                closed=closed,
                auto_paginate=auto_paginate,
            )

        # MILE-002: Crear milestone
        @self.mcp.tool(
            name="taiga_create_milestone",
            description="Create a new milestone/sprint in a Taiga project",
        )
        async def create_milestone_tool(
            auth_token: str,
            project_id: int,
            name: str,
            estimated_start: str,
            estimated_finish: str,
            disponibility: float | None = 0.0,
            watchers: list[int] | None = None,
        ) -> dict[str, Any]:
            """
            Create a new milestone/sprint in a Taiga project.

            Esta herramienta crea un nuevo milestone (sprint) en un proyecto,
            definiendo el período de tiempo y la capacidad del equipo para
            esa iteración de desarrollo.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde crear el milestone
                name: Nombre del sprint (ej: "Sprint 1", "Enero 2024")
                estimated_start: Fecha de inicio en formato YYYY-MM-DD
                estimated_finish: Fecha de fin en formato YYYY-MM-DD
                disponibility: Disponibilidad del equipo en horas o puntos
                    (opcional, por defecto 0.0)
                watchers: Lista de IDs de usuarios que seguirán el milestone
                    (opcional)

            Returns:
                Dict con el milestone creado conteniendo:
                - id: ID del milestone creado
                - name: Nombre del sprint
                - slug: Slug generado automáticamente
                - project: ID del proyecto
                - estimated_start: Fecha de inicio
                - estimated_finish: Fecha de fin
                - disponibility: Disponibilidad configurada
                - closed: False (nuevo milestone está abierto)
                - created_date: Fecha de creación

            Raises:
                ToolError: Si el proyecto no existe, las fechas son inválidas,
                    no hay permisos de creación, o la autenticación falla

            Example:
                >>> milestone = await taiga_create_milestone(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     name="Sprint 5",
                ...     estimated_start="2024-02-01",
                ...     estimated_finish="2024-02-15",
                ...     disponibility=80.0
                ... )
                >>> print(milestone)
                {
                    "id": 45,
                    "name": "Sprint 5",
                    "estimated_start": "2024-02-01",
                    "estimated_finish": "2024-02-15",
                    "disponibility": 80.0,
                    "closed": False
                }
            """
            try:
                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {
                    "project_id": project_id,
                    "name": name,
                    "estimated_start": estimated_start,
                    "estimated_finish": estimated_finish,
                    "disponibility": disponibility,
                    "watchers": watchers,
                }
                validate_input(MilestoneCreateValidator, validation_data)

                return await self.create_milestone(
                    auth_token=auth_token,
                    project=project_id,  # API expects 'project'
                    name=name,
                    estimated_start=estimated_start,
                    estimated_finish=estimated_finish,
                    disponibility=disponibility,
                    watchers=watchers,
                )
            except ValidationError as e:
                self._logger.warning(f"[create_milestone_tool] Validation error | error={e!s}")
                raise MCPError(str(e)) from e

        # MILE-003: Obtener milestone por ID
        @self.mcp.tool(
            name="taiga_get_milestone",
            annotations={"readOnlyHint": True},
            description="Get a specific milestone by its ID",
        )
        async def get_milestone_tool(auth_token: str, milestone_id: int) -> dict[str, Any]:
            """
            Get a specific milestone by its ID.

            Esta herramienta obtiene los detalles completos de un milestone
            específico, incluyendo su configuración, fechas, estado y
            estadísticas de progreso.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                milestone_id: ID del milestone a obtener

            Returns:
                Dict con los detalles del milestone conteniendo:
                - id: ID del milestone
                - name: Nombre del sprint
                - slug: Slug único
                - project: ID del proyecto
                - estimated_start: Fecha de inicio planificada
                - estimated_finish: Fecha de fin planificada
                - created_date: Fecha de creación
                - modified_date: Última modificación
                - closed: True si está cerrado
                - disponibility: Disponibilidad del equipo
                - total_points: Puntos totales del sprint
                - closed_points: Puntos completados
                - user_stories: Lista de historias de usuario asignadas

            Raises:
                ToolError: Si el milestone no existe, no hay permisos de acceso,
                    o la autenticación falla

            Example:
                >>> milestone = await taiga_get_milestone(
                ...     auth_token="eyJ0eXAiOi...",
                ...     milestone_id=45
                ... )
                >>> print(milestone)
                {
                    "id": 45,
                    "name": "Sprint 5",
                    "estimated_start": "2024-02-01",
                    "estimated_finish": "2024-02-15",
                    "closed": False,
                    "total_points": 50,
                    "closed_points": 30
                }
            """
            return await self.get_milestone(auth_token=auth_token, milestone_id=milestone_id)

        # MILE-004: Actualizar milestone (completo)
        @self.mcp.tool(
            name="taiga_update_milestone_full",
            annotations={"idempotentHint": True},
            description="Update a milestone (full replacement)",
        )
        async def update_milestone_full_tool(
            auth_token: str,
            milestone_id: int,
            project_id: int,
            name: str,
            estimated_start: str,
            estimated_finish: str,
            disponibility: float | None = 0.0,
            closed: bool | None = False,
            watchers: list[int] | None = None,
        ) -> dict[str, Any]:
            """
            Update a milestone with full replacement (PUT).

            Esta herramienta actualiza un milestone reemplazando todos sus
            campos. Todos los campos obligatorios deben ser proporcionados
            incluso si no cambian.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                milestone_id: ID del milestone a actualizar
                project_id: ID del proyecto (requerido para PUT)
                name: Nombre del sprint (requerido)
                estimated_start: Fecha de inicio en formato YYYY-MM-DD (requerido)
                estimated_finish: Fecha de fin en formato YYYY-MM-DD (requerido)
                disponibility: Disponibilidad del equipo (opcional, default 0.0)
                closed: Estado cerrado del sprint (opcional, default False)
                watchers: Lista de IDs de usuarios observadores (opcional)

            Returns:
                Dict con el milestone actualizado conteniendo:
                - id: ID del milestone
                - name: Nombre actualizado
                - slug: Slug (puede cambiar con el nombre)
                - project: ID del proyecto
                - estimated_start: Nueva fecha de inicio
                - estimated_finish: Nueva fecha de fin
                - disponibility: Disponibilidad actualizada
                - closed: Estado de cierre
                - modified_date: Fecha de modificación

            Raises:
                ToolError: Si el milestone no existe, faltan campos requeridos,
                    no hay permisos de modificación, o la autenticación falla

            Example:
                >>> milestone = await taiga_update_milestone_full(
                ...     auth_token="eyJ0eXAiOi...",
                ...     milestone_id=45,
                ...     project_id=123,
                ...     name="Sprint 5 - Extendido",
                ...     estimated_start="2024-02-01",
                ...     estimated_finish="2024-02-20",
                ...     disponibility=100.0,
                ...     closed=False
                ... )
                >>> print(milestone)
                {
                    "id": 45,
                    "name": "Sprint 5 - Extendido",
                    "estimated_finish": "2024-02-20",
                    "disponibility": 100.0
                }
            """
            try:
                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {
                    "milestone_id": milestone_id,
                    "name": name,
                    "estimated_start": estimated_start,
                    "estimated_finish": estimated_finish,
                    "disponibility": disponibility,
                    "closed": closed,
                }
                validate_input(MilestoneUpdateValidator, validation_data)

                return await self.update_milestone_full(
                    auth_token=auth_token,
                    milestone_id=milestone_id,
                    project=project_id,  # API expects 'project'
                    name=name,
                    estimated_start=estimated_start,
                    estimated_finish=estimated_finish,
                    disponibility=disponibility,
                    closed=closed,
                    watchers=watchers,
                )
            except ValidationError as e:
                self._logger.warning(f"[update_milestone_full_tool] Validation error | error={e!s}")
                raise MCPError(str(e)) from e

        # MILE-005: Actualizar milestone (parcial)
        @self.mcp.tool(
            name="taiga_update_milestone",
            annotations={"idempotentHint": True},
            description="Update specific fields of a milestone (partial update)",
        )
        async def update_milestone_partial_tool(
            auth_token: str,
            milestone_id: int,
            name: str | None = None,
            estimated_start: str | None = None,
            estimated_finish: str | None = None,
            disponibility: float | None = None,
            closed: bool | None = None,
            watchers: list[int] | None = None,
        ) -> dict[str, Any]:
            """
            Update specific fields of a milestone (partial update - PATCH).

            Esta herramienta permite actualizar solo los campos específicos
            de un milestone sin necesidad de proporcionar todos los valores.
            Solo los campos con valor serán modificados.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                milestone_id: ID del milestone a actualizar
                name: Nuevo nombre del sprint (opcional)
                estimated_start: Nueva fecha de inicio YYYY-MM-DD (opcional)
                estimated_finish: Nueva fecha de fin YYYY-MM-DD (opcional)
                disponibility: Nueva disponibilidad del equipo (opcional)
                closed: Nuevo estado cerrado/abierto (opcional)
                watchers: Nueva lista de IDs de observadores (opcional)

            Returns:
                Dict con el milestone actualizado conteniendo:
                - id: ID del milestone
                - name: Nombre (actualizado si se proporcionó)
                - estimated_start: Fecha de inicio
                - estimated_finish: Fecha de fin
                - disponibility: Disponibilidad
                - closed: Estado de cierre
                - modified_date: Fecha de última modificación

            Raises:
                ToolError: Si el milestone no existe, los valores son inválidos,
                    no hay permisos de modificación, o la autenticación falla

            Example:
                >>> milestone = await taiga_update_milestone(
                ...     auth_token="eyJ0eXAiOi...",
                ...     milestone_id=45,
                ...     closed=True
                ... )
                >>> print(milestone)
                {
                    "id": 45,
                    "name": "Sprint 5",
                    "closed": True,
                    "modified_date": "2024-02-15T18:00:00Z"
                }
            """
            try:
                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {
                    "milestone_id": milestone_id,
                    "name": name,
                    "estimated_start": estimated_start,
                    "estimated_finish": estimated_finish,
                    "disponibility": disponibility,
                    "closed": closed,
                }
                validate_input(MilestoneUpdateValidator, validation_data)

                return await self.update_milestone_partial(
                    auth_token=auth_token,
                    milestone_id=milestone_id,
                    name=name,
                    estimated_start=estimated_start,
                    estimated_finish=estimated_finish,
                    disponibility=disponibility,
                    closed=closed,
                    watchers=watchers,
                )
            except ValidationError as e:
                self._logger.warning(
                    f"[update_milestone_partial_tool] Validation error | error={e!s}"
                )
                raise MCPError(str(e)) from e

        # MILE-006: Eliminar milestone
        @self.mcp.tool(
            name="taiga_delete_milestone",
            annotations={"destructiveHint": True},
            description="Delete a milestone",
        )
        async def delete_milestone_tool(auth_token: str, milestone_id: int) -> dict[str, Any]:
            """
            Delete a milestone.

            Esta herramienta elimina permanentemente un milestone de un proyecto.
            Las historias de usuario asignadas al milestone NO se eliminan,
            pero quedarán sin milestone asignado. Esta acción no se puede deshacer.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                milestone_id: ID del milestone a eliminar

            Returns:
                Dict con confirmación de eliminación conteniendo:
                - success: True si se eliminó correctamente
                - message: Mensaje descriptivo de la operación

            Raises:
                ToolError: Si el milestone no existe, no hay permisos de
                    eliminación, o la autenticación falla

            Example:
                >>> result = await taiga_delete_milestone(
                ...     auth_token="eyJ0eXAiOi...",
                ...     milestone_id=45
                ... )
                >>> print(result)
                {
                    "success": True,
                    "message": "Milestone deleted successfully"
                }
            """
            return await self.delete_milestone(auth_token=auth_token, milestone_id=milestone_id)

        # MILE-007: Obtener estadísticas
        @self.mcp.tool(
            name="taiga_get_milestone_stats",
            annotations={"readOnlyHint": True},
            description="Get statistics for a specific milestone",
        )
        async def get_milestone_stats_tool(auth_token: str, milestone_id: int) -> dict[str, Any]:
            """
            Get statistics for a specific milestone.

            Esta herramienta obtiene estadísticas detalladas del progreso
            de un milestone, incluyendo burndown, puntos completados por día,
            y métricas de velocidad del equipo.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                milestone_id: ID del milestone

            Returns:
                Dict con estadísticas del milestone conteniendo:
                - name: Nombre del milestone
                - estimated_start: Fecha de inicio
                - estimated_finish: Fecha de fin
                - total_points: Puntos totales del sprint
                - completed_points: Puntos completados
                - total_userstories: Número de historias de usuario
                - completed_userstories: Historias completadas
                - total_tasks: Número de tareas
                - completed_tasks: Tareas completadas
                - days: Lista de datos diarios para burndown
                - iocaine_doses: Dosis de iocaína usadas (si aplica)

            Raises:
                ToolError: Si el milestone no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> stats = await taiga_get_milestone_stats(
                ...     auth_token="eyJ0eXAiOi...",
                ...     milestone_id=45
                ... )
                >>> print(stats)
                {
                    "name": "Sprint 5",
                    "total_points": 50.0,
                    "completed_points": 35.0,
                    "total_userstories": 10,
                    "completed_userstories": 7,
                    "days": [{"day": "2024-02-01", "open_points": 50.0}]
                }
            """
            return await self.get_milestone_stats(auth_token=auth_token, milestone_id=milestone_id)

        # MILE-008: Seguir milestone
        @self.mcp.tool(
            name="taiga_watch_milestone",
            annotations={"idempotentHint": True},
            description="Start watching a milestone for updates",
        )
        async def watch_milestone_tool(auth_token: str, milestone_id: int) -> dict[str, Any]:
            """
            Start watching a milestone for updates.

            Esta herramienta suscribe al usuario actual para recibir
            notificaciones sobre cambios en un milestone específico,
            incluyendo cambios de estado, nuevas historias asignadas,
            y actualizaciones de progreso.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                milestone_id: ID del milestone a seguir

            Returns:
                Dict con confirmación de suscripción conteniendo:
                - id: ID del milestone
                - watchers: Lista actualizada de IDs de observadores
                - total_watchers: Número total de observadores

            Raises:
                ToolError: Si el milestone no existe, ya se está siguiendo,
                    no hay permisos, o la autenticación falla

            Example:
                >>> result = await taiga_watch_milestone(
                ...     auth_token="eyJ0eXAiOi...",
                ...     milestone_id=45
                ... )
                >>> print(result)
                {
                    "id": 45,
                    "watchers": [1, 2, 42],
                    "total_watchers": 3
                }
            """
            return await self.watch_milestone(auth_token=auth_token, milestone_id=milestone_id)

        # MILE-009: Dejar de seguir milestone
        @self.mcp.tool(
            name="taiga_unwatch_milestone",
            annotations={"idempotentHint": True},
            description="Stop watching a milestone",
        )
        async def unwatch_milestone_tool(auth_token: str, milestone_id: int) -> dict[str, Any]:
            """
            Stop watching a milestone.

            Esta herramienta cancela la suscripción del usuario actual
            a las notificaciones de un milestone. El usuario dejará
            de recibir actualizaciones sobre cambios en el sprint.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                milestone_id: ID del milestone a dejar de seguir

            Returns:
                Dict con confirmación de cancelación conteniendo:
                - id: ID del milestone
                - watchers: Lista actualizada de IDs de observadores
                - total_watchers: Número total de observadores restantes

            Raises:
                ToolError: Si el milestone no existe, no se estaba siguiendo,
                    no hay permisos, o la autenticación falla

            Example:
                >>> result = await taiga_unwatch_milestone(
                ...     auth_token="eyJ0eXAiOi...",
                ...     milestone_id=45
                ... )
                >>> print(result)
                {
                    "id": 45,
                    "watchers": [1, 2],
                    "total_watchers": 2
                }
            """
            return await self.unwatch_milestone(auth_token=auth_token, milestone_id=milestone_id)

        # MILE-010: Obtener observadores
        @self.mcp.tool(
            name="taiga_get_milestone_watchers",
            annotations={"readOnlyHint": True},
            description="Get list of users watching a milestone",
        )
        async def get_milestone_watchers_tool(
            auth_token: str, milestone_id: int
        ) -> list[dict[str, Any]]:
            """
            Get list of users watching a milestone.

            Esta herramienta obtiene la lista completa de usuarios que
            están siguiendo un milestone específico. Útil para saber
            quiénes recibirán notificaciones sobre cambios en el sprint.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                milestone_id: ID del milestone

            Returns:
                Lista de diccionarios con información de observadores,
                cada uno conteniendo:
                - id: ID del usuario
                - username: Nombre de usuario
                - full_name: Nombre completo
                - photo: URL de la foto de perfil
                - is_active: Si el usuario está activo

            Raises:
                ToolError: Si el milestone no existe, no hay permisos
                    de acceso, o la autenticación falla

            Example:
                >>> watchers = await taiga_get_milestone_watchers(
                ...     auth_token="eyJ0eXAiOi...",
                ...     milestone_id=45
                ... )
                >>> print(watchers)
                [
                    {
                        "id": 1,
                        "username": "admin",
                        "full_name": "Admin User",
                        "is_active": True
                    },
                    {
                        "id": 42,
                        "username": "developer",
                        "full_name": "Dev User",
                        "is_active": True
                    }
                ]
            """
            return await self.get_milestone_watchers(
                auth_token=auth_token, milestone_id=milestone_id
            )

    # Métodos de implementación

    async def list_milestones(self, auth_token: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Lista todos los milestones con filtros opcionales."""
        kwargs.pop("auth_token", None)
        auto_paginate = kwargs.pop("auto_paginate", True)
        project_id = kwargs.get("project")
        self._logger.debug(f"[list_milestones] Starting | project_id={project_id}")

        # Remove None values from kwargs
        params = {k: v for k, v in kwargs.items() if v is not None}

        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            paginator = AutoPaginator(client, PaginationConfig())

            if auto_paginate:
                result = await paginator.paginate("/milestones", params=params)
            else:
                result = await paginator.paginate_first_page("/milestones", params=params)
        self._logger.info(
            f"[list_milestones] Success | project_id={project_id}, count={len(result)}"
        )
        return result

    async def create_milestone(self, auth_token: str, **kwargs: Any) -> dict[str, Any]:
        """Crea un nuevo milestone."""
        project_id = kwargs.get("project")
        name = kwargs.get("name")
        self._logger.debug(f"[create_milestone] Starting | project_id={project_id}, name={name}")
        kwargs.pop("auth_token", None)
        # Según los tests, project, name, estimated_start y estimated_finish son requeridos
        if "project" not in kwargs or "name" not in kwargs:
            raise ValueError("project and name are required")
        if "estimated_start" not in kwargs or "estimated_finish" not in kwargs:
            raise ValueError("estimated_start and estimated_finish are required")
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            result = await client.create_milestone(**kwargs)
        self._logger.info(
            f"[create_milestone] Success | project_id={project_id}, milestone_id={result.get('id')}"
        )
        return result

    async def get_milestone(self, auth_token: str, milestone_id: int) -> dict[str, Any]:
        """Obtiene un milestone por ID."""
        self._logger.debug(f"[get_milestone] Starting | milestone_id={milestone_id}")
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            result = await client.get_milestone(milestone_id=milestone_id)
        self._logger.info(f"[get_milestone] Success | milestone_id={milestone_id}")
        return result

    async def update_milestone_full(
        self, auth_token: str, milestone_id: int, **kwargs
    ) -> dict[str, Any]:
        """Actualiza un milestone (reemplazo completo)."""
        self._logger.debug(f"[update_milestone_full] Starting | milestone_id={milestone_id}")
        kwargs.pop("auth_token", None)
        kwargs.pop("milestone_id", None)
        # Para update completo necesitamos estos campos obligatorios
        if "name" not in kwargs:
            raise ValueError("name is required for full update")
        if "estimated_start" not in kwargs or "estimated_finish" not in kwargs:
            raise ValueError("estimated_start and estimated_finish are required for full update")
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            result = await client.update_milestone_full(milestone_id=milestone_id, **kwargs)
        self._logger.info(f"[update_milestone_full] Success | milestone_id={milestone_id}")
        return result

    async def update_milestone_partial(
        self, auth_token: str, milestone_id: int, **kwargs
    ) -> dict[str, Any]:
        """Actualiza campos específicos de un milestone."""
        self._logger.debug(f"[update_milestone_partial] Starting | milestone_id={milestone_id}")
        kwargs.pop("auth_token", None)
        kwargs.pop("milestone_id", None)
        # Remove None values for partial update
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            result = await client.update_milestone(milestone_id=milestone_id, **update_data)
        self._logger.info(f"[update_milestone_partial] Success | milestone_id={milestone_id}")
        return result

    # Alias para update_milestone_partial
    async def update_milestone(
        self, auth_token: str, milestone_id: int, **kwargs
    ) -> dict[str, Any]:
        """Alias para update_milestone_partial."""
        self._logger.debug(f"[update_milestone] Starting (alias) | milestone_id={milestone_id}")
        return await self.update_milestone_partial(auth_token, milestone_id, **kwargs)

    async def delete_milestone(self, auth_token: str, milestone_id: int) -> dict[str, Any]:
        """Elimina un milestone."""
        self._logger.debug(f"[delete_milestone] Starting | milestone_id={milestone_id}")
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            result = await client.delete_milestone(milestone_id=milestone_id)
        self._logger.info(f"[delete_milestone] Success | milestone_id={milestone_id}")
        # Si el cliente devuelve un dict, retornarlo; si no, devolver un dict de confirmación
        if isinstance(result, dict):
            return result
        return {"success": "true", "message": f"Milestone {milestone_id} deleted successfully"}

    async def get_milestone_stats(self, auth_token: str, milestone_id: int) -> dict[str, Any]:
        """Obtiene las estadísticas de un milestone."""
        self._logger.debug(f"[get_milestone_stats] Starting | milestone_id={milestone_id}")
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            result = await client.get_milestone_stats(milestone_id=milestone_id)
        self._logger.info(f"[get_milestone_stats] Success | milestone_id={milestone_id}")
        return result

    async def watch_milestone(self, auth_token: str, milestone_id: int) -> dict[str, Any]:
        """Comienza a seguir un milestone."""
        self._logger.debug(f"[watch_milestone] Starting | milestone_id={milestone_id}")
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            result = await client.watch_milestone(milestone_id=milestone_id)
        self._logger.info(f"[watch_milestone] Success | milestone_id={milestone_id}")
        return result

    async def unwatch_milestone(self, auth_token: str, milestone_id: int) -> dict[str, Any]:
        """Deja de seguir un milestone."""
        self._logger.debug(f"[unwatch_milestone] Starting | milestone_id={milestone_id}")
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            result = await client.unwatch_milestone(milestone_id=milestone_id)
        self._logger.info(f"[unwatch_milestone] Success | milestone_id={milestone_id}")
        return result

    async def get_milestone_watchers(
        self, auth_token: str, milestone_id: int
    ) -> list[dict[str, Any]]:
        """Obtiene la lista de observadores de un milestone."""
        self._logger.debug(f"[get_milestone_watchers] Starting | milestone_id={milestone_id}")
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = auth_token
            result = await client.get_milestone_watchers(milestone_id=milestone_id)
        self._logger.info(
            f"[get_milestone_watchers] Success | milestone_id={milestone_id}, count={len(result) if result else 0}"
        )
        return result
