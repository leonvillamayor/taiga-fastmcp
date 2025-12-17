"""
Herramientas de búsqueda y timeline para Taiga.

Este módulo implementa las herramientas MCP para búsqueda global
y acceso a timelines de usuario y proyecto.
"""

from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError as MCPError

from src.config import TaigaConfig
from src.domain.exceptions import (
    AuthenticationError,
    ResourceNotFoundError,
    TaigaAPIError,
)
from src.infrastructure.logging import get_logger
from src.taiga_client import TaigaAPIClient


class SearchTools:
    """
    Herramientas MCP para búsqueda y timeline en Taiga.

    Esta clase proporciona herramientas para:
    - Búsqueda global en proyectos
    - Timeline de actividad de usuarios
    - Timeline de actividad de proyectos

    Attributes:
        mcp: Instancia de FastMCP para registrar herramientas
        config: Configuración de conexión a Taiga API
        client: Cliente de API para tests (inyectable)
    """

    def __init__(self, mcp: FastMCP) -> None:
        """
        Inicializa SearchTools.

        Args:
            mcp: Instancia de FastMCP
        """
        self.mcp = mcp
        self.config = TaigaConfig()
        self._logger = get_logger("search_tools")
        self.client = None

    def set_client(self, client: Any) -> None:
        """Inyecta un cliente para testing."""
        self.client = client

    def register_tools(self) -> None:
        """Registra todas las herramientas de búsqueda y timeline."""
        self._register_search_tools()
        self._register_timeline_tools()

    def _register_search_tools(self) -> None:
        """Registra herramientas de búsqueda."""

        @self.mcp.tool(
            name="taiga_search",
            description="Search for items across a Taiga project (user stories, issues, tasks, wiki, etc.)",
            tags={"search", "read", "project"},
            annotations={"readOnlyHint": True, "openWorldHint": True},
        )
        async def search(
            auth_token: str,
            project_id: int,
            text: str,
            count: int = 20,
        ) -> dict[str, Any]:
            """
            Search for items in a Taiga project.

            Busca en todos los elementos del proyecto: historias de usuario,
            issues, tareas, páginas wiki, épicas, etc.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde buscar
                text: Texto a buscar
                count: Número máximo de resultados por categoría (default: 20)

            Returns:
                Dict con resultados por categoría:
                - userstories: Lista de historias de usuario encontradas
                - issues: Lista de issues encontradas
                - tasks: Lista de tareas encontradas
                - wikipages: Lista de páginas wiki encontradas
                - epics: Lista de épicas encontradas
                - count: Conteo total de resultados

            Raises:
                MCPError: Si la autenticación falla o hay error en la API

            Example:
                >>> results = await taiga_search(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     text="login feature"
                ... )
                >>> print(results["userstories"])
                [{"id": 456, "ref": 10, "subject": "User login feature"}, ...]
            """
            try:
                self._logger.debug(
                    f"[search] Starting | project={project_id}, text='{text}', count={count}"
                )

                params = {
                    "project": project_id,
                    "text": text,
                }

                if self.client:
                    result = await self.client.get("/search", params=params)
                else:
                    async with TaigaAPIClient(self.config) as client:
                        client.auth_token = auth_token
                        result = await client.get("/search", params=params)

                # Limitar resultados por categoría
                categories = ["userstories", "issues", "tasks", "wikipages", "epics"]
                limited_result = {"count": 0}

                for category in categories:
                    if category in result and isinstance(result[category], list):
                        limited_result[category] = result[category][:count]
                        limited_result["count"] += len(limited_result[category])
                    else:
                        limited_result[category] = []

                self._logger.info(
                    f"[search] Success | project={project_id}, total_results={limited_result['count']}"
                )
                return limited_result

            except AuthenticationError:
                self._logger.warning("[search] Auth failed")
                raise MCPError("Authentication failed") from None
            except ResourceNotFoundError:
                self._logger.warning(f"[search] Project not found | project={project_id}")
                raise MCPError(f"Project {project_id} not found") from None
            except TaigaAPIError as e:
                self._logger.error(f"[search] API error | error={e!s}")
                raise MCPError(f"Failed to search: {e!s}") from e
            except Exception as e:
                self._logger.error(f"[search] Unexpected error | error={e!s}")
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.search = search.fn if hasattr(search, "fn") else search

    def _register_timeline_tools(self) -> None:
        """Registra herramientas de timeline."""

        @self.mcp.tool(
            name="taiga_get_user_timeline",
            description="Get activity timeline for a specific user",
            tags={"timeline", "read", "user", "activity"},
            annotations={"readOnlyHint": True, "openWorldHint": True},
        )
        async def get_user_timeline(
            auth_token: str,
            user_id: int,
            page: int = 1,
        ) -> list[dict[str, Any]]:
            """
            Get activity timeline for a user.

            Obtiene el historial de actividad de un usuario, incluyendo
            creaciones, actualizaciones, comentarios, etc.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                user_id: ID del usuario
                page: Número de página para paginación (default: 1)

            Returns:
                Lista de eventos de actividad, cada uno con:
                - id: ID del evento
                - content_type: Tipo de contenido (userstory, issue, etc.)
                - object_id: ID del objeto afectado
                - event_type: Tipo de evento (create, change, delete, comment)
                - data: Datos del evento
                - created: Fecha de creación
                - project: Información del proyecto

            Raises:
                MCPError: Si la autenticación falla o hay error en la API

            Example:
                >>> timeline = await taiga_get_user_timeline(
                ...     auth_token="eyJ0eXAiOi...",
                ...     user_id=456
                ... )
                >>> for event in timeline:
                ...     print(f"{event['event_type']}: {event['content_type']}")
            """
            try:
                self._logger.debug(f"[get_user_timeline] Starting | user={user_id}, page={page}")

                if self.client:
                    result = await self.client.get(
                        f"/timeline/user/{user_id}", params={"page": page}
                    )
                else:
                    async with TaigaAPIClient(self.config) as client:
                        client.auth_token = auth_token
                        result = await client.get(
                            f"/timeline/user/{user_id}", params={"page": page}
                        )

                if isinstance(result, list):
                    events = [
                        {
                            "id": event.get("id"),
                            "content_type": (
                                event.get("content_type", {}).get("model")
                                if isinstance(event.get("content_type"), dict)
                                else event.get("content_type")
                            ),
                            "object_id": event.get("object_id"),
                            "event_type": event.get("event_type"),
                            "data": event.get("data"),
                            "created": event.get("created"),
                            "project": (
                                event.get("data", {}).get("project")
                                if isinstance(event.get("data"), dict)
                                else None
                            ),
                        }
                        for event in result
                    ]
                    self._logger.info(
                        f"[get_user_timeline] Success | user={user_id}, events={len(events)}"
                    )
                    return events

                self._logger.info(f"[get_user_timeline] Success | user={user_id}, events=0")
                return []

            except AuthenticationError:
                self._logger.warning("[get_user_timeline] Auth failed")
                raise MCPError("Authentication failed") from None
            except ResourceNotFoundError:
                self._logger.warning(f"[get_user_timeline] User not found | user={user_id}")
                raise MCPError(f"User {user_id} not found") from None
            except TaigaAPIError as e:
                self._logger.error(f"[get_user_timeline] API error | error={e!s}")
                raise MCPError(f"Failed to get user timeline: {e!s}") from e
            except Exception as e:
                self._logger.error(f"[get_user_timeline] Unexpected error | error={e!s}")
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.get_user_timeline = (
            get_user_timeline.fn if hasattr(get_user_timeline, "fn") else get_user_timeline
        )

        @self.mcp.tool(
            name="taiga_get_project_timeline",
            description="Get activity timeline for a specific project",
            tags={"timeline", "read", "project", "activity"},
            annotations={"readOnlyHint": True, "openWorldHint": True},
        )
        async def get_project_timeline(
            auth_token: str,
            project_id: int,
            page: int = 1,
        ) -> list[dict[str, Any]]:
            """
            Get activity timeline for a project.

            Obtiene el historial de actividad de un proyecto, incluyendo
            todas las acciones realizadas por los miembros del equipo.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto
                page: Número de página para paginación (default: 1)

            Returns:
                Lista de eventos de actividad, cada uno con:
                - id: ID del evento
                - content_type: Tipo de contenido (userstory, issue, etc.)
                - object_id: ID del objeto afectado
                - event_type: Tipo de evento (create, change, delete, comment)
                - data: Datos del evento
                - created: Fecha de creación
                - user: Información del usuario que realizó la acción

            Raises:
                MCPError: Si la autenticación falla o hay error en la API

            Example:
                >>> timeline = await taiga_get_project_timeline(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> for event in timeline:
                ...     print(f"{event['user']['username']}: {event['event_type']}")
            """
            try:
                self._logger.debug(
                    f"[get_project_timeline] Starting | project={project_id}, page={page}"
                )

                if self.client:
                    result = await self.client.get(
                        f"/timeline/project/{project_id}", params={"page": page}
                    )
                else:
                    async with TaigaAPIClient(self.config) as client:
                        client.auth_token = auth_token
                        result = await client.get(
                            f"/timeline/project/{project_id}", params={"page": page}
                        )

                if isinstance(result, list):
                    events = [
                        {
                            "id": event.get("id"),
                            "content_type": (
                                event.get("content_type", {}).get("model")
                                if isinstance(event.get("content_type"), dict)
                                else event.get("content_type")
                            ),
                            "object_id": event.get("object_id"),
                            "event_type": event.get("event_type"),
                            "data": event.get("data"),
                            "created": event.get("created"),
                            "user": (
                                event.get("data", {}).get("user")
                                if isinstance(event.get("data"), dict)
                                else None
                            ),
                        }
                        for event in result
                    ]
                    self._logger.info(
                        f"[get_project_timeline] Success | project={project_id}, events={len(events)}"
                    )
                    return events

                self._logger.info(
                    f"[get_project_timeline] Success | project={project_id}, events=0"
                )
                return []

            except AuthenticationError:
                self._logger.warning("[get_project_timeline] Auth failed")
                raise MCPError("Authentication failed") from None
            except ResourceNotFoundError:
                self._logger.warning(
                    f"[get_project_timeline] Project not found | project={project_id}"
                )
                raise MCPError(f"Project {project_id} not found") from None
            except TaigaAPIError as e:
                self._logger.error(f"[get_project_timeline] API error | error={e!s}")
                raise MCPError(f"Failed to get project timeline: {e!s}") from e
            except Exception as e:
                self._logger.error(f"[get_project_timeline] Unexpected error | error={e!s}")
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.get_project_timeline = (
            get_project_timeline.fn if hasattr(get_project_timeline, "fn") else get_project_timeline
        )
