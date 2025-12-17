"""
MCP Resources para Taiga.

Este módulo implementa los recursos MCP que exponen datos
de Taiga de forma estructurada y accesible.

Los recursos MCP son endpoints de solo lectura que proporcionan
acceso a datos sin efectos secundarios.
"""

from typing import Any

from fastmcp import FastMCP

from src.config import TaigaConfig
from src.infrastructure.logging import get_logger
from src.taiga_client import TaigaAPIClient


class TaigaResources:
    """
    Recursos MCP para acceso a datos de Taiga.

    Esta clase proporciona recursos para:
    - Estadísticas de proyectos
    - Configuración de proyectos (módulos habilitados)
    - Información del usuario actual
    - Timeline de actividad de proyectos

    Los recursos son endpoints de solo lectura que exponen
    datos de Taiga de forma estructurada.

    Attributes:
        mcp: Instancia de FastMCP para registrar recursos
        config: Configuración de conexión a Taiga API
        client: Cliente de API para tests (inyectable)
    """

    def __init__(self, mcp: FastMCP) -> None:
        """
        Inicializa TaigaResources.

        Args:
            mcp: Instancia de FastMCP
        """
        self.mcp = mcp
        self.config = TaigaConfig()
        self._logger = get_logger("taiga_resources")
        self.client = None

    def set_client(self, client: Any) -> None:
        """Inyecta un cliente para testing."""
        self.client = client

    def register_resources(self) -> None:
        """Registra todos los recursos MCP."""
        self._register_project_resources()
        self._register_user_resources()

    def _register_project_resources(self) -> None:
        """Registra recursos relacionados con proyectos."""

        @self.mcp.resource(
            uri="taiga://projects/{project_id}/stats",
            name="project_stats",
            description="Get comprehensive statistics for a Taiga project including user stories, tasks, issues counts and completion rates",
        )
        async def get_project_stats(project_id: int) -> dict[str, Any]:
            """
            Get project statistics.

            Provides comprehensive statistics about a project including:
            - Total user stories, tasks, and issues
            - Completion rates and progress
            - Points information
            - Sprint statistics

            Args:
                project_id: ID of the project

            Returns:
                Dict with project statistics
            """
            self._logger.debug(f"[resource:project_stats] Fetching stats for project {project_id}")

            if self.client:
                result = await self.client.get(f"/projects/{project_id}/stats")
            else:
                async with TaigaAPIClient(self.config) as client:
                    result = await client.get(f"/projects/{project_id}/stats")

            self._logger.info(f"[resource:project_stats] Retrieved stats for project {project_id}")
            return result

        # Store reference for testing
        self.get_project_stats = get_project_stats

        @self.mcp.resource(
            uri="taiga://projects/{project_id}/modules",
            name="project_modules",
            description="Get enabled modules configuration for a Taiga project (scrum, kanban, issues, wiki, etc.)",
        )
        async def get_project_modules(project_id: int) -> dict[str, Any]:
            """
            Get project modules configuration.

            Returns which modules are enabled for the project:
            - is_backlog_activated (Scrum backlog)
            - is_kanban_activated (Kanban board)
            - is_wiki_activated (Wiki pages)
            - is_issues_activated (Issue tracker)
            - is_epics_activated (Epics support)
            - videoconferences configuration
            - other module settings

            Args:
                project_id: ID of the project

            Returns:
                Dict with modules configuration
            """
            self._logger.debug(
                f"[resource:project_modules] Fetching modules for project {project_id}"
            )

            if self.client:
                result = await self.client.get(f"/projects/{project_id}")
            else:
                async with TaigaAPIClient(self.config) as client:
                    result = await client.get(f"/projects/{project_id}")

            # Extract module configuration
            modules = {
                "is_backlog_activated": result.get("is_backlog_activated", False),
                "is_kanban_activated": result.get("is_kanban_activated", False),
                "is_wiki_activated": result.get("is_wiki_activated", False),
                "is_issues_activated": result.get("is_issues_activated", False),
                "is_epics_activated": result.get("is_epics_activated", False),
                "videoconferences": result.get("videoconferences"),
                "videoconferences_extra_data": result.get("videoconferences_extra_data"),
                "total_milestones": result.get("total_milestones", 0),
                "total_story_points": result.get("total_story_points", 0),
            }

            self._logger.info(
                f"[resource:project_modules] Retrieved modules for project {project_id}"
            )
            return modules

        # Store reference for testing
        self.get_project_modules = get_project_modules

        @self.mcp.resource(
            uri="taiga://projects/{project_id}/timeline",
            name="project_timeline",
            description="Get recent activity timeline for a Taiga project",
        )
        async def get_project_timeline_resource(project_id: int) -> list[dict[str, Any]]:
            """
            Get project activity timeline.

            Returns recent activity in the project including:
            - User story changes
            - Task updates
            - Issue modifications
            - Comments and attachments
            - Sprint changes

            Args:
                project_id: ID of the project

            Returns:
                List of timeline events
            """
            self._logger.debug(
                f"[resource:project_timeline] Fetching timeline for project {project_id}"
            )

            if self.client:
                result = await self.client.get(f"/timeline/project/{project_id}")
            else:
                async with TaigaAPIClient(self.config) as client:
                    result = await client.get(f"/timeline/project/{project_id}")

            # Process timeline events
            if isinstance(result, list):
                events = [
                    {
                        "id": event.get("id"),
                        "content_type": (
                            event.get("content_type", {}).get("model")
                            if isinstance(event.get("content_type"), dict)
                            else event.get("content_type")
                        ),
                        "event_type": event.get("event_type"),
                        "created": event.get("created"),
                        "data": event.get("data"),
                    }
                    for event in result[:50]  # Limit to 50 events
                ]
                self._logger.info(
                    f"[resource:project_timeline] Retrieved {len(events)} events for project {project_id}"
                )
                return events

            return []

        # Store reference for testing
        self.get_project_timeline_resource = get_project_timeline_resource

        @self.mcp.resource(
            uri="taiga://projects/{project_id}/members",
            name="project_members",
            description="Get list of members and their roles in a Taiga project",
        )
        async def get_project_members(project_id: int) -> list[dict[str, Any]]:
            """
            Get project members.

            Returns list of project members with:
            - User information (id, username, full name)
            - Role in the project
            - Permission level

            Args:
                project_id: ID of the project

            Returns:
                List of project members
            """
            self._logger.debug(
                f"[resource:project_members] Fetching members for project {project_id}"
            )

            if self.client:
                result = await self.client.get("/memberships", params={"project": project_id})
            else:
                async with TaigaAPIClient(self.config) as client:
                    result = await client.get("/memberships", params={"project": project_id})

            if isinstance(result, list):
                members = [
                    {
                        "id": member.get("id"),
                        "user": member.get("user"),
                        "role": member.get("role"),
                        "role_name": member.get("role_name"),
                        "full_name": member.get("full_name"),
                        "is_admin": member.get("is_admin", False),
                        "is_active": member.get("is_active", True),
                    }
                    for member in result
                ]
                self._logger.info(
                    f"[resource:project_members] Retrieved {len(members)} members for project {project_id}"
                )
                return members

            return []

        # Store reference for testing
        self.get_project_members = get_project_members

    def _register_user_resources(self) -> None:
        """Registra recursos relacionados con usuarios."""

        @self.mcp.resource(
            uri="taiga://users/me",
            name="current_user",
            description="Get information about the currently authenticated Taiga user",
        )
        async def get_current_user() -> dict[str, Any]:
            """
            Get current authenticated user information.

            Returns information about the authenticated user:
            - User ID and username
            - Full name and email
            - Bio and photo
            - Language and timezone settings
            - Roles in projects

            Returns:
                Dict with user information
            """
            self._logger.debug("[resource:current_user] Fetching current user info")

            if self.client:
                result = await self.client.get("/users/me")
            else:
                async with TaigaAPIClient(self.config) as client:
                    result = await client.get("/users/me")

            user_info = {
                "id": result.get("id"),
                "username": result.get("username"),
                "full_name": result.get("full_name"),
                "full_name_display": result.get("full_name_display"),
                "email": result.get("email"),
                "bio": result.get("bio"),
                "photo": result.get("photo"),
                "lang": result.get("lang"),
                "timezone": result.get("timezone"),
                "is_active": result.get("is_active", True),
                "max_private_projects": result.get("max_private_projects"),
                "max_public_projects": result.get("max_public_projects"),
                "total_private_projects": result.get("total_private_projects"),
                "total_public_projects": result.get("total_public_projects"),
            }

            self._logger.info(
                f"[resource:current_user] Retrieved user: {user_info.get('username')}"
            )
            return user_info

        # Store reference for testing
        self.get_current_user = get_current_user

        @self.mcp.resource(
            uri="taiga://users/{user_id}/stats",
            name="user_stats",
            description="Get statistics for a specific Taiga user",
        )
        async def get_user_stats(user_id: int) -> dict[str, Any]:
            """
            Get user statistics.

            Returns statistics about a user's activity:
            - Projects participated
            - Total user stories, tasks, issues
            - Activity metrics

            Args:
                user_id: ID of the user

            Returns:
                Dict with user statistics
            """
            self._logger.debug(f"[resource:user_stats] Fetching stats for user {user_id}")

            if self.client:
                result = await self.client.get(f"/users/{user_id}/stats")
            else:
                async with TaigaAPIClient(self.config) as client:
                    result = await client.get(f"/users/{user_id}/stats")

            self._logger.info(f"[resource:user_stats] Retrieved stats for user {user_id}")
            return result

        # Store reference for testing
        self.get_user_stats = get_user_stats
