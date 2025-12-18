"""
Project settings tools for Taiga MCP Server - Application layer.

Provides tools for managing project configuration including:
- Points (Story Points)
- Statuses (User Story, Task, Issue, Epic)
- Priorities
- Severities
- Issue Types
- Roles
"""

from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError as MCPError

from src.config import TaigaConfig
from src.domain.exceptions import (
    AuthenticationError,
    ResourceNotFoundError,
    TaigaAPIError,
    ValidationError,
)
from src.infrastructure.logging import get_logger
from src.taiga_client import TaigaAPIClient


class SettingsTools:
    """
    Project settings tools for Taiga MCP Server.

    Provides MCP tools for managing project configuration like
    points, statuses, priorities, severities, issue types, and roles.
    """

    def __init__(self, mcp: FastMCP) -> None:
        """
        Initialize settings tools.

        Args:
            mcp: FastMCP server instance
        """
        self.mcp = mcp
        self.config = TaigaConfig()
        self._logger = get_logger("settings_tools")
        self.client = None

    def set_client(self, client: Any) -> None:
        """Set the Taiga API client (for testing purposes)."""
        self.client = client

    def _get_auth_token(self) -> str:
        """Get auth token from context or raise error."""
        if hasattr(self.mcp, "context") and self.mcp.context.get("auth_token"):
            return self.mcp.context["auth_token"]
        raise MCPError("Not authenticated. Call taiga_authenticate first.")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        auth_token: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Make an authenticated request to Taiga API.

        Note: Converts 'json' kwarg to 'data' for compatibility with TaigaAPIClient.
        """
        token = auth_token or self._get_auth_token()

        # Convert 'json' to 'data' for TaigaAPIClient compatibility
        if "json" in kwargs:
            kwargs["data"] = kwargs.pop("json")

        if self.client:
            # Testing path
            if method == "GET":
                return await self.client.get(endpoint, **kwargs)
            if method == "POST":
                return await self.client.post(endpoint, **kwargs)
            if method == "PUT":
                return await self.client.put(endpoint, **kwargs)
            if method == "PATCH":
                return await self.client.patch(endpoint, **kwargs)
            if method == "DELETE":
                return await self.client.delete(endpoint, **kwargs)

        # Production path
        async with TaigaAPIClient(self.config) as client:
            client.auth_token = token
            if method == "GET":
                return await client.get(endpoint, **kwargs)
            if method == "POST":
                return await client.post(endpoint, **kwargs)
            if method == "PUT":
                return await client.put(endpoint, **kwargs)
            if method == "PATCH":
                return await client.patch(endpoint, **kwargs)
            if method == "DELETE":
                return await client.delete(endpoint, **kwargs)
        return None  # Explicit return for unsupported methods

    def register_tools(self) -> None:
        """Register all settings tools with the MCP server."""
        self._register_points_tools()
        self._register_userstory_status_tools()
        self._register_task_status_tools()
        self._register_issue_status_tools()
        self._register_epic_status_tools()
        self._register_priority_tools()
        self._register_severity_tools()
        self._register_issue_type_tools()
        self._register_role_tools()

    # =========================================================================
    # POINTS (STORY POINTS) TOOLS
    # =========================================================================

    def _register_points_tools(self) -> None:
        """Register points management tools."""

        @self.mcp.tool(
            name="taiga_list_points",
            description="List all point values configured for a project",
            tags={"settings", "points", "read"},
            annotations={"readOnlyHint": True},
        )
        async def list_points(
            auth_token: str,
            project_id: int,
        ) -> list[dict[str, Any]]:
            """
            List all point values for a project.

            Points are used for story point estimation in user stories.

            Args:
                auth_token: Authentication token
                project_id: Project ID

            Returns:
                List of point configurations with id, name, value, order
            """
            self._logger.debug(f"[list_points] project={project_id}")
            try:
                result = await self._make_request(
                    "GET",
                    "/points",
                    auth_token=auth_token,
                    params={"project": project_id},
                )
                self._logger.info(f"[list_points] Found {len(result)} points")
                return result
            except AuthenticationError as e:
                raise MCPError(f"Authentication failed: {e}") from e
            except TaigaAPIError as e:
                raise MCPError(f"API error listing points: {e}") from e

        @self.mcp.tool(
            name="taiga_create_point",
            description="Create a new point value for story estimation",
            tags={"settings", "points", "write"},
            annotations={"readOnlyHint": False},
        )
        async def create_point(
            auth_token: str,
            project_id: int,
            name: str,
            value: float | None = None,
            order: int = 10,
        ) -> dict[str, Any]:
            """
            Create a new point value for a project.

            Args:
                auth_token: Authentication token
                project_id: Project ID
                name: Point name (e.g., "1", "2", "3", "5", "8", "13", "?")
                value: Numeric value (None for non-numeric like "?")
                order: Display order

            Returns:
                Created point configuration
            """
            self._logger.debug(f"[create_point] project={project_id}, name={name}")
            try:
                data = {
                    "project": project_id,
                    "name": name,
                    "order": order,
                }
                if value is not None:
                    data["value"] = value

                result = await self._make_request(
                    "POST",
                    "/points",
                    auth_token=auth_token,
                    json=data,
                )
                self._logger.info(f"[create_point] Created point id={result.get('id')}")
                return result
            except ValidationError as e:
                raise MCPError(f"Validation error: {e}") from e
            except TaigaAPIError as e:
                raise MCPError(f"API error creating point: {e}") from e

        @self.mcp.tool(
            name="taiga_get_point",
            description="Get a specific point configuration by ID",
            tags={"settings", "points", "read"},
            annotations={"readOnlyHint": True},
        )
        async def get_point(
            auth_token: str,
            point_id: int,
        ) -> dict[str, Any]:
            """
            Get a point configuration by ID.

            Args:
                auth_token: Authentication token
                point_id: Point ID

            Returns:
                Point configuration details
            """
            self._logger.debug(f"[get_point] id={point_id}")
            try:
                return await self._make_request(
                    "GET",
                    f"/points/{point_id}",
                    auth_token=auth_token,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"Point {point_id} not found") from e
            except TaigaAPIError as e:
                raise MCPError(f"API error getting point: {e}") from e

        @self.mcp.tool(
            name="taiga_update_point",
            description="Update a point configuration",
            tags={"settings", "points", "write"},
            annotations={"readOnlyHint": False},
        )
        async def update_point(
            auth_token: str,
            point_id: int,
            name: str | None = None,
            value: float | None = None,
            order: int | None = None,
        ) -> dict[str, Any]:
            """
            Update a point configuration.

            Args:
                auth_token: Authentication token
                point_id: Point ID
                name: New name (optional)
                value: New value (optional)
                order: New order (optional)

            Returns:
                Updated point configuration
            """
            self._logger.debug(f"[update_point] id={point_id}")
            try:
                data = {}
                if name is not None:
                    data["name"] = name
                if value is not None:
                    data["value"] = value
                if order is not None:
                    data["order"] = order

                result = await self._make_request(
                    "PATCH",
                    f"/points/{point_id}",
                    auth_token=auth_token,
                    json=data,
                )
                self._logger.info(f"[update_point] Updated point id={point_id}")
                return result
            except ResourceNotFoundError as e:
                raise MCPError(f"Point {point_id} not found") from e
            except TaigaAPIError as e:
                raise MCPError(f"API error updating point: {e}") from e

        @self.mcp.tool(
            name="taiga_delete_point",
            description="Delete a point configuration",
            tags={"settings", "points", "write", "destructive"},
            annotations={"readOnlyHint": False, "destructiveHint": True},
        )
        async def delete_point(
            auth_token: str,
            point_id: int,
            moveto: int | None = None,
        ) -> dict[str, Any]:
            """
            Delete a point configuration.

            Args:
                auth_token: Authentication token
                point_id: Point ID to delete
                moveto: Point ID to move existing stories to (optional)

            Returns:
                Confirmation of deletion
            """
            self._logger.debug(f"[delete_point] id={point_id}")
            try:
                params = {}
                if moveto:
                    params["moveTo"] = moveto

                await self._make_request(
                    "DELETE",
                    f"/points/{point_id}",
                    auth_token=auth_token,
                    params=params if params else None,
                )
                self._logger.info(f"[delete_point] Deleted point id={point_id}")
                return {"deleted": True, "point_id": point_id}
            except ResourceNotFoundError as e:
                raise MCPError(f"Point {point_id} not found") from e
            except TaigaAPIError as e:
                raise MCPError(f"API error deleting point: {e}") from e

        @self.mcp.tool(
            name="taiga_bulk_update_points_order",
            description="Update the order of multiple points at once",
            tags={"settings", "points", "write"},
            annotations={"readOnlyHint": False},
        )
        async def bulk_update_points_order(
            auth_token: str,
            project_id: int,
            bulk_points: list[list[int]],
        ) -> dict[str, Any]:
            """
            Update the order of multiple points.

            Args:
                auth_token: Authentication token
                project_id: Project ID
                bulk_points: List of [point_id, order] pairs

            Returns:
                Dict with success confirmation and count of updated points
            """
            self._logger.debug(f"[bulk_update_points_order] project={project_id}")
            try:
                await self._make_request(
                    "POST",
                    "/points/bulk_update_order",
                    auth_token=auth_token,
                    json={
                        "project": project_id,
                        "bulk_points": bulk_points,
                    },
                )
                self._logger.info(f"[bulk_update_points_order] Updated {len(bulk_points)} points")
                return {
                    "success": True,
                    "updated_count": len(bulk_points),
                    "project_id": project_id,
                }
            except TaigaAPIError as e:
                raise MCPError(f"API error updating points order: {e}") from e

    # =========================================================================
    # USER STORY STATUS TOOLS
    # =========================================================================

    def _register_userstory_status_tools(self) -> None:
        """Register user story status management tools."""

        @self.mcp.tool(
            name="taiga_list_userstory_statuses",
            description="List all user story statuses for a project",
            tags={"settings", "statuses", "userstory", "read"},
            annotations={"readOnlyHint": True},
        )
        async def list_userstory_statuses(
            auth_token: str,
            project_id: int,
        ) -> list[dict[str, Any]]:
            """
            List all user story statuses for a project.

            Args:
                auth_token: Authentication token
                project_id: Project ID

            Returns:
                List of user story statuses
            """
            self._logger.debug(f"[list_userstory_statuses] project={project_id}")
            try:
                return await self._make_request(
                    "GET",
                    "/userstory-statuses",
                    auth_token=auth_token,
                    params={"project": project_id},
                )
            except TaigaAPIError as e:
                raise MCPError(f"API error listing user story statuses: {e}") from e

        @self.mcp.tool(
            name="taiga_create_userstory_status",
            description="Create a new user story status",
            tags={"settings", "statuses", "userstory", "write"},
            annotations={"readOnlyHint": False},
        )
        async def create_userstory_status(
            auth_token: str,
            project_id: int,
            name: str,
            color: str = "#999999",
            is_closed: bool = False,
            is_archived: bool = False,
            wip_limit: int | None = None,
            order: int = 10,
        ) -> dict[str, Any]:
            """
            Create a new user story status.

            Args:
                auth_token: Authentication token
                project_id: Project ID
                name: Status name
                color: Hex color code
                is_closed: Whether status represents closed state
                is_archived: Whether status represents archived state
                wip_limit: Work in progress limit (for kanban)
                order: Display order

            Returns:
                Created status
            """
            self._logger.debug(f"[create_userstory_status] project={project_id}, name={name}")
            try:
                data = {
                    "project": project_id,
                    "name": name,
                    "color": color,
                    "is_closed": is_closed,
                    "is_archived": is_archived,
                    "order": order,
                }
                if wip_limit is not None:
                    data["wip_limit"] = wip_limit

                result = await self._make_request(
                    "POST",
                    "/userstory-statuses",
                    auth_token=auth_token,
                    json=data,
                )
                self._logger.info(f"[create_userstory_status] Created status id={result.get('id')}")
                return result
            except TaigaAPIError as e:
                raise MCPError(f"API error creating user story status: {e}") from e

        @self.mcp.tool(
            name="taiga_get_userstory_status",
            description="Get a user story status by ID",
            tags={"settings", "statuses", "userstory", "read"},
            annotations={"readOnlyHint": True},
        )
        async def get_userstory_status(
            auth_token: str,
            status_id: int,
        ) -> dict[str, Any]:
            """Get a user story status by ID."""
            try:
                return await self._make_request(
                    "GET",
                    f"/userstory-statuses/{status_id}",
                    auth_token=auth_token,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"User story status {status_id} not found") from e

        @self.mcp.tool(
            name="taiga_update_userstory_status",
            description="Update a user story status",
            tags={"settings", "statuses", "userstory", "write"},
            annotations={"readOnlyHint": False},
        )
        async def update_userstory_status(
            auth_token: str,
            status_id: int,
            name: str | None = None,
            color: str | None = None,
            is_closed: bool | None = None,
            is_archived: bool | None = None,
            wip_limit: int | None = None,
            order: int | None = None,
        ) -> dict[str, Any]:
            """Update a user story status."""
            try:
                data = {}
                if name is not None:
                    data["name"] = name
                if color is not None:
                    data["color"] = color
                if is_closed is not None:
                    data["is_closed"] = is_closed
                if is_archived is not None:
                    data["is_archived"] = is_archived
                if wip_limit is not None:
                    data["wip_limit"] = wip_limit
                if order is not None:
                    data["order"] = order

                return await self._make_request(
                    "PATCH",
                    f"/userstory-statuses/{status_id}",
                    auth_token=auth_token,
                    json=data,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"User story status {status_id} not found") from e

        @self.mcp.tool(
            name="taiga_delete_userstory_status",
            description="Delete a user story status",
            tags={"settings", "statuses", "userstory", "write", "destructive"},
            annotations={"readOnlyHint": False, "destructiveHint": True},
        )
        async def delete_userstory_status(
            auth_token: str,
            status_id: int,
            moveto: int | None = None,
        ) -> dict[str, Any]:
            """Delete a user story status."""
            try:
                params = {"moveTo": moveto} if moveto else None
                await self._make_request(
                    "DELETE",
                    f"/userstory-statuses/{status_id}",
                    auth_token=auth_token,
                    params=params,
                )
                return {"deleted": True, "status_id": status_id}
            except ResourceNotFoundError as e:
                raise MCPError(f"User story status {status_id} not found") from e

    # =========================================================================
    # TASK STATUS TOOLS
    # =========================================================================

    def _register_task_status_tools(self) -> None:
        """Register task status management tools."""

        @self.mcp.tool(
            name="taiga_list_task_statuses",
            description="List all task statuses for a project",
            tags={"settings", "statuses", "task", "read"},
            annotations={"readOnlyHint": True},
        )
        async def list_task_statuses(
            auth_token: str,
            project_id: int,
        ) -> list[dict[str, Any]]:
            """List all task statuses for a project."""
            try:
                return await self._make_request(
                    "GET",
                    "/task-statuses",
                    auth_token=auth_token,
                    params={"project": project_id},
                )
            except TaigaAPIError as e:
                raise MCPError(f"API error listing task statuses: {e}") from e

        @self.mcp.tool(
            name="taiga_create_task_status",
            description="Create a new task status",
            tags={"settings", "statuses", "task", "write"},
            annotations={"readOnlyHint": False},
        )
        async def create_task_status(
            auth_token: str,
            project_id: int,
            name: str,
            color: str = "#999999",
            is_closed: bool = False,
            order: int = 10,
        ) -> dict[str, Any]:
            """Create a new task status."""
            try:
                return await self._make_request(
                    "POST",
                    "/task-statuses",
                    auth_token=auth_token,
                    json={
                        "project": project_id,
                        "name": name,
                        "color": color,
                        "is_closed": is_closed,
                        "order": order,
                    },
                )
            except TaigaAPIError as e:
                raise MCPError(f"API error creating task status: {e}") from e

        @self.mcp.tool(
            name="taiga_get_task_status",
            description="Get a task status by ID",
            tags={"settings", "statuses", "task", "read"},
            annotations={"readOnlyHint": True},
        )
        async def get_task_status(
            auth_token: str,
            status_id: int,
        ) -> dict[str, Any]:
            """Get a task status by ID."""
            try:
                return await self._make_request(
                    "GET",
                    f"/task-statuses/{status_id}",
                    auth_token=auth_token,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"Task status {status_id} not found") from e

        @self.mcp.tool(
            name="taiga_update_task_status",
            description="Update a task status",
            tags={"settings", "statuses", "task", "write"},
            annotations={"readOnlyHint": False},
        )
        async def update_task_status(
            auth_token: str,
            status_id: int,
            name: str | None = None,
            color: str | None = None,
            is_closed: bool | None = None,
            order: int | None = None,
        ) -> dict[str, Any]:
            """Update a task status."""
            try:
                data = {}
                if name is not None:
                    data["name"] = name
                if color is not None:
                    data["color"] = color
                if is_closed is not None:
                    data["is_closed"] = is_closed
                if order is not None:
                    data["order"] = order

                return await self._make_request(
                    "PATCH",
                    f"/task-statuses/{status_id}",
                    auth_token=auth_token,
                    json=data,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"Task status {status_id} not found") from e

        @self.mcp.tool(
            name="taiga_delete_task_status",
            description="Delete a task status",
            tags={"settings", "statuses", "task", "write", "destructive"},
            annotations={"readOnlyHint": False, "destructiveHint": True},
        )
        async def delete_task_status(
            auth_token: str,
            status_id: int,
            moveto: int | None = None,
        ) -> dict[str, Any]:
            """Delete a task status."""
            try:
                params = {"moveTo": moveto} if moveto else None
                await self._make_request(
                    "DELETE",
                    f"/task-statuses/{status_id}",
                    auth_token=auth_token,
                    params=params,
                )
                return {"deleted": True, "status_id": status_id}
            except ResourceNotFoundError as e:
                raise MCPError(f"Task status {status_id} not found") from e

    # =========================================================================
    # ISSUE STATUS TOOLS
    # =========================================================================

    def _register_issue_status_tools(self) -> None:
        """Register issue status management tools."""

        @self.mcp.tool(
            name="taiga_list_issue_statuses",
            description="List all issue statuses for a project",
            tags={"settings", "statuses", "issue", "read"},
            annotations={"readOnlyHint": True},
        )
        async def list_issue_statuses(
            auth_token: str,
            project_id: int,
        ) -> list[dict[str, Any]]:
            """List all issue statuses for a project."""
            try:
                return await self._make_request(
                    "GET",
                    "/issue-statuses",
                    auth_token=auth_token,
                    params={"project": project_id},
                )
            except TaigaAPIError as e:
                raise MCPError(f"API error listing issue statuses: {e}") from e

        @self.mcp.tool(
            name="taiga_create_issue_status",
            description="Create a new issue status",
            tags={"settings", "statuses", "issue", "write"},
            annotations={"readOnlyHint": False},
        )
        async def create_issue_status(
            auth_token: str,
            project_id: int,
            name: str,
            color: str = "#999999",
            is_closed: bool = False,
            order: int = 10,
        ) -> dict[str, Any]:
            """Create a new issue status."""
            try:
                return await self._make_request(
                    "POST",
                    "/issue-statuses",
                    auth_token=auth_token,
                    json={
                        "project": project_id,
                        "name": name,
                        "color": color,
                        "is_closed": is_closed,
                        "order": order,
                    },
                )
            except TaigaAPIError as e:
                raise MCPError(f"API error creating issue status: {e}") from e

        @self.mcp.tool(
            name="taiga_get_issue_status",
            description="Get an issue status by ID",
            tags={"settings", "statuses", "issue", "read"},
            annotations={"readOnlyHint": True},
        )
        async def get_issue_status(
            auth_token: str,
            status_id: int,
        ) -> dict[str, Any]:
            """Get an issue status by ID."""
            try:
                return await self._make_request(
                    "GET",
                    f"/issue-statuses/{status_id}",
                    auth_token=auth_token,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"Issue status {status_id} not found") from e

        @self.mcp.tool(
            name="taiga_update_issue_status",
            description="Update an issue status",
            tags={"settings", "statuses", "issue", "write"},
            annotations={"readOnlyHint": False},
        )
        async def update_issue_status(
            auth_token: str,
            status_id: int,
            name: str | None = None,
            color: str | None = None,
            is_closed: bool | None = None,
            order: int | None = None,
        ) -> dict[str, Any]:
            """Update an issue status."""
            try:
                data = {}
                if name is not None:
                    data["name"] = name
                if color is not None:
                    data["color"] = color
                if is_closed is not None:
                    data["is_closed"] = is_closed
                if order is not None:
                    data["order"] = order

                return await self._make_request(
                    "PATCH",
                    f"/issue-statuses/{status_id}",
                    auth_token=auth_token,
                    json=data,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"Issue status {status_id} not found") from e

        @self.mcp.tool(
            name="taiga_delete_issue_status",
            description="Delete an issue status",
            tags={"settings", "statuses", "issue", "write", "destructive"},
            annotations={"readOnlyHint": False, "destructiveHint": True},
        )
        async def delete_issue_status(
            auth_token: str,
            status_id: int,
            moveto: int | None = None,
        ) -> dict[str, Any]:
            """Delete an issue status."""
            try:
                params = {"moveTo": moveto} if moveto else None
                await self._make_request(
                    "DELETE",
                    f"/issue-statuses/{status_id}",
                    auth_token=auth_token,
                    params=params,
                )
                return {"deleted": True, "status_id": status_id}
            except ResourceNotFoundError as e:
                raise MCPError(f"Issue status {status_id} not found") from e

    # =========================================================================
    # EPIC STATUS TOOLS
    # =========================================================================

    def _register_epic_status_tools(self) -> None:
        """Register epic status management tools."""

        @self.mcp.tool(
            name="taiga_list_epic_statuses",
            description="List all epic statuses for a project",
            tags={"settings", "statuses", "epic", "read"},
            annotations={"readOnlyHint": True},
        )
        async def list_epic_statuses(
            auth_token: str,
            project_id: int,
        ) -> list[dict[str, Any]]:
            """List all epic statuses for a project."""
            try:
                return await self._make_request(
                    "GET",
                    "/epic-statuses",
                    auth_token=auth_token,
                    params={"project": project_id},
                )
            except TaigaAPIError as e:
                raise MCPError(f"API error listing epic statuses: {e}") from e

        @self.mcp.tool(
            name="taiga_create_epic_status",
            description="Create a new epic status",
            tags={"settings", "statuses", "epic", "write"},
            annotations={"readOnlyHint": False},
        )
        async def create_epic_status(
            auth_token: str,
            project_id: int,
            name: str,
            color: str = "#999999",
            is_closed: bool = False,
            order: int = 10,
        ) -> dict[str, Any]:
            """Create a new epic status."""
            try:
                return await self._make_request(
                    "POST",
                    "/epic-statuses",
                    auth_token=auth_token,
                    json={
                        "project": project_id,
                        "name": name,
                        "color": color,
                        "is_closed": is_closed,
                        "order": order,
                    },
                )
            except TaigaAPIError as e:
                raise MCPError(f"API error creating epic status: {e}") from e

        @self.mcp.tool(
            name="taiga_get_epic_status",
            description="Get an epic status by ID",
            tags={"settings", "statuses", "epic", "read"},
            annotations={"readOnlyHint": True},
        )
        async def get_epic_status(
            auth_token: str,
            status_id: int,
        ) -> dict[str, Any]:
            """Get an epic status by ID."""
            try:
                return await self._make_request(
                    "GET",
                    f"/epic-statuses/{status_id}",
                    auth_token=auth_token,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"Epic status {status_id} not found") from e

        @self.mcp.tool(
            name="taiga_update_epic_status",
            description="Update an epic status",
            tags={"settings", "statuses", "epic", "write"},
            annotations={"readOnlyHint": False},
        )
        async def update_epic_status(
            auth_token: str,
            status_id: int,
            name: str | None = None,
            color: str | None = None,
            is_closed: bool | None = None,
            order: int | None = None,
        ) -> dict[str, Any]:
            """Update an epic status."""
            try:
                data = {}
                if name is not None:
                    data["name"] = name
                if color is not None:
                    data["color"] = color
                if is_closed is not None:
                    data["is_closed"] = is_closed
                if order is not None:
                    data["order"] = order

                return await self._make_request(
                    "PATCH",
                    f"/epic-statuses/{status_id}",
                    auth_token=auth_token,
                    json=data,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"Epic status {status_id} not found") from e

        @self.mcp.tool(
            name="taiga_delete_epic_status",
            description="Delete an epic status",
            tags={"settings", "statuses", "epic", "write", "destructive"},
            annotations={"readOnlyHint": False, "destructiveHint": True},
        )
        async def delete_epic_status(
            auth_token: str,
            status_id: int,
            moveto: int | None = None,
        ) -> dict[str, Any]:
            """Delete an epic status."""
            try:
                params = {"moveTo": moveto} if moveto else None
                await self._make_request(
                    "DELETE",
                    f"/epic-statuses/{status_id}",
                    auth_token=auth_token,
                    params=params,
                )
                return {"deleted": True, "status_id": status_id}
            except ResourceNotFoundError as e:
                raise MCPError(f"Epic status {status_id} not found") from e

    # =========================================================================
    # PRIORITY TOOLS
    # =========================================================================

    def _register_priority_tools(self) -> None:
        """Register priority management tools."""

        @self.mcp.tool(
            name="taiga_list_priorities",
            description="List all priorities for issues in a project",
            tags={"settings", "priorities", "read"},
            annotations={"readOnlyHint": True},
        )
        async def list_priorities(
            auth_token: str,
            project_id: int,
        ) -> list[dict[str, Any]]:
            """List all priorities for a project."""
            try:
                return await self._make_request(
                    "GET",
                    "/priorities",
                    auth_token=auth_token,
                    params={"project": project_id},
                )
            except TaigaAPIError as e:
                raise MCPError(f"API error listing priorities: {e}") from e

        @self.mcp.tool(
            name="taiga_create_priority",
            description="Create a new priority for issues",
            tags={"settings", "priorities", "write"},
            annotations={"readOnlyHint": False},
        )
        async def create_priority(
            auth_token: str,
            project_id: int,
            name: str,
            color: str = "#999999",
            order: int = 10,
        ) -> dict[str, Any]:
            """Create a new priority."""
            try:
                return await self._make_request(
                    "POST",
                    "/priorities",
                    auth_token=auth_token,
                    json={
                        "project": project_id,
                        "name": name,
                        "color": color,
                        "order": order,
                    },
                )
            except TaigaAPIError as e:
                raise MCPError(f"API error creating priority: {e}") from e

        @self.mcp.tool(
            name="taiga_get_priority",
            description="Get a priority by ID",
            tags={"settings", "priorities", "read"},
            annotations={"readOnlyHint": True},
        )
        async def get_priority(
            auth_token: str,
            priority_id: int,
        ) -> dict[str, Any]:
            """Get a priority by ID."""
            try:
                return await self._make_request(
                    "GET",
                    f"/priorities/{priority_id}",
                    auth_token=auth_token,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"Priority {priority_id} not found") from e

        @self.mcp.tool(
            name="taiga_update_priority",
            description="Update a priority",
            tags={"settings", "priorities", "write"},
            annotations={"readOnlyHint": False},
        )
        async def update_priority(
            auth_token: str,
            priority_id: int,
            name: str | None = None,
            color: str | None = None,
            order: int | None = None,
        ) -> dict[str, Any]:
            """Update a priority."""
            try:
                data = {}
                if name is not None:
                    data["name"] = name
                if color is not None:
                    data["color"] = color
                if order is not None:
                    data["order"] = order

                return await self._make_request(
                    "PATCH",
                    f"/priorities/{priority_id}",
                    auth_token=auth_token,
                    json=data,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"Priority {priority_id} not found") from e

        @self.mcp.tool(
            name="taiga_delete_priority",
            description="Delete a priority",
            tags={"settings", "priorities", "write", "destructive"},
            annotations={"readOnlyHint": False, "destructiveHint": True},
        )
        async def delete_priority(
            auth_token: str,
            priority_id: int,
            moveto: int | None = None,
        ) -> dict[str, Any]:
            """Delete a priority."""
            try:
                params = {"moveTo": moveto} if moveto else None
                await self._make_request(
                    "DELETE",
                    f"/priorities/{priority_id}",
                    auth_token=auth_token,
                    params=params,
                )
                return {"deleted": True, "priority_id": priority_id}
            except ResourceNotFoundError as e:
                raise MCPError(f"Priority {priority_id} not found") from e

    # =========================================================================
    # SEVERITY TOOLS
    # =========================================================================

    def _register_severity_tools(self) -> None:
        """Register severity management tools."""

        @self.mcp.tool(
            name="taiga_list_severities",
            description="List all severities for issues in a project",
            tags={"settings", "severities", "read"},
            annotations={"readOnlyHint": True},
        )
        async def list_severities(
            auth_token: str,
            project_id: int,
        ) -> list[dict[str, Any]]:
            """List all severities for a project."""
            try:
                return await self._make_request(
                    "GET",
                    "/severities",
                    auth_token=auth_token,
                    params={"project": project_id},
                )
            except TaigaAPIError as e:
                raise MCPError(f"API error listing severities: {e}") from e

        @self.mcp.tool(
            name="taiga_create_severity",
            description="Create a new severity for issues",
            tags={"settings", "severities", "write"},
            annotations={"readOnlyHint": False},
        )
        async def create_severity(
            auth_token: str,
            project_id: int,
            name: str,
            color: str = "#999999",
            order: int = 10,
        ) -> dict[str, Any]:
            """Create a new severity."""
            try:
                return await self._make_request(
                    "POST",
                    "/severities",
                    auth_token=auth_token,
                    json={
                        "project": project_id,
                        "name": name,
                        "color": color,
                        "order": order,
                    },
                )
            except TaigaAPIError as e:
                raise MCPError(f"API error creating severity: {e}") from e

        @self.mcp.tool(
            name="taiga_get_severity",
            description="Get a severity by ID",
            tags={"settings", "severities", "read"},
            annotations={"readOnlyHint": True},
        )
        async def get_severity(
            auth_token: str,
            severity_id: int,
        ) -> dict[str, Any]:
            """Get a severity by ID."""
            try:
                return await self._make_request(
                    "GET",
                    f"/severities/{severity_id}",
                    auth_token=auth_token,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"Severity {severity_id} not found") from e

        @self.mcp.tool(
            name="taiga_update_severity",
            description="Update a severity",
            tags={"settings", "severities", "write"},
            annotations={"readOnlyHint": False},
        )
        async def update_severity(
            auth_token: str,
            severity_id: int,
            name: str | None = None,
            color: str | None = None,
            order: int | None = None,
        ) -> dict[str, Any]:
            """Update a severity."""
            try:
                data = {}
                if name is not None:
                    data["name"] = name
                if color is not None:
                    data["color"] = color
                if order is not None:
                    data["order"] = order

                return await self._make_request(
                    "PATCH",
                    f"/severities/{severity_id}",
                    auth_token=auth_token,
                    json=data,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"Severity {severity_id} not found") from e

        @self.mcp.tool(
            name="taiga_delete_severity",
            description="Delete a severity",
            tags={"settings", "severities", "write", "destructive"},
            annotations={"readOnlyHint": False, "destructiveHint": True},
        )
        async def delete_severity(
            auth_token: str,
            severity_id: int,
            moveto: int | None = None,
        ) -> dict[str, Any]:
            """Delete a severity."""
            try:
                params = {"moveTo": moveto} if moveto else None
                await self._make_request(
                    "DELETE",
                    f"/severities/{severity_id}",
                    auth_token=auth_token,
                    params=params,
                )
                return {"deleted": True, "severity_id": severity_id}
            except ResourceNotFoundError as e:
                raise MCPError(f"Severity {severity_id} not found") from e

    # =========================================================================
    # ISSUE TYPE TOOLS
    # =========================================================================

    def _register_issue_type_tools(self) -> None:
        """Register issue type management tools."""

        @self.mcp.tool(
            name="taiga_list_issue_types",
            description="List all issue types for a project",
            tags={"settings", "issue-types", "read"},
            annotations={"readOnlyHint": True},
        )
        async def list_issue_types(
            auth_token: str,
            project_id: int,
        ) -> list[dict[str, Any]]:
            """List all issue types for a project."""
            try:
                return await self._make_request(
                    "GET",
                    "/issue-types",
                    auth_token=auth_token,
                    params={"project": project_id},
                )
            except TaigaAPIError as e:
                raise MCPError(f"API error listing issue types: {e}") from e

        @self.mcp.tool(
            name="taiga_create_issue_type",
            description="Create a new issue type",
            tags={"settings", "issue-types", "write"},
            annotations={"readOnlyHint": False},
        )
        async def create_issue_type(
            auth_token: str,
            project_id: int,
            name: str,
            color: str = "#999999",
            order: int = 10,
        ) -> dict[str, Any]:
            """Create a new issue type."""
            try:
                return await self._make_request(
                    "POST",
                    "/issue-types",
                    auth_token=auth_token,
                    json={
                        "project": project_id,
                        "name": name,
                        "color": color,
                        "order": order,
                    },
                )
            except TaigaAPIError as e:
                raise MCPError(f"API error creating issue type: {e}") from e

        @self.mcp.tool(
            name="taiga_get_issue_type",
            description="Get an issue type by ID",
            tags={"settings", "issue-types", "read"},
            annotations={"readOnlyHint": True},
        )
        async def get_issue_type(
            auth_token: str,
            type_id: int,
        ) -> dict[str, Any]:
            """Get an issue type by ID."""
            try:
                return await self._make_request(
                    "GET",
                    f"/issue-types/{type_id}",
                    auth_token=auth_token,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"Issue type {type_id} not found") from e

        @self.mcp.tool(
            name="taiga_update_issue_type",
            description="Update an issue type",
            tags={"settings", "issue-types", "write"},
            annotations={"readOnlyHint": False},
        )
        async def update_issue_type(
            auth_token: str,
            type_id: int,
            name: str | None = None,
            color: str | None = None,
            order: int | None = None,
        ) -> dict[str, Any]:
            """Update an issue type."""
            try:
                data = {}
                if name is not None:
                    data["name"] = name
                if color is not None:
                    data["color"] = color
                if order is not None:
                    data["order"] = order

                return await self._make_request(
                    "PATCH",
                    f"/issue-types/{type_id}",
                    auth_token=auth_token,
                    json=data,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"Issue type {type_id} not found") from e

        @self.mcp.tool(
            name="taiga_delete_issue_type",
            description="Delete an issue type",
            tags={"settings", "issue-types", "write", "destructive"},
            annotations={"readOnlyHint": False, "destructiveHint": True},
        )
        async def delete_issue_type(
            auth_token: str,
            type_id: int,
            moveto: int | None = None,
        ) -> dict[str, Any]:
            """Delete an issue type."""
            try:
                params = {"moveTo": moveto} if moveto else None
                await self._make_request(
                    "DELETE",
                    f"/issue-types/{type_id}",
                    auth_token=auth_token,
                    params=params,
                )
                return {"deleted": True, "type_id": type_id}
            except ResourceNotFoundError as e:
                raise MCPError(f"Issue type {type_id} not found") from e

    # =========================================================================
    # ROLE TOOLS
    # =========================================================================

    def _register_role_tools(self) -> None:
        """Register role management tools."""

        @self.mcp.tool(
            name="taiga_list_roles",
            description="List all roles for a project",
            tags={"settings", "roles", "read"},
            annotations={"readOnlyHint": True},
        )
        async def list_roles(
            auth_token: str,
            project_id: int,
        ) -> list[dict[str, Any]]:
            """List all roles for a project."""
            try:
                return await self._make_request(
                    "GET",
                    "/roles",
                    auth_token=auth_token,
                    params={"project": project_id},
                )
            except TaigaAPIError as e:
                raise MCPError(f"API error listing roles: {e}") from e

        @self.mcp.tool(
            name="taiga_create_role",
            description="Create a new role for a project",
            tags={"settings", "roles", "write"},
            annotations={"readOnlyHint": False},
        )
        async def create_role(
            auth_token: str,
            project_id: int,
            name: str,
            permissions: list[str] | None = None,
            order: int = 10,
            computable: bool = True,
        ) -> dict[str, Any]:
            """
            Create a new role.

            Args:
                auth_token: Authentication token
                project_id: Project ID
                name: Role name
                permissions: List of permission codenames
                order: Display order
                computable: Whether role counts in project stats

            Returns:
                Created role
            """
            try:
                data = {
                    "project": project_id,
                    "name": name,
                    "order": order,
                    "computable": computable,
                }
                if permissions:
                    data["permissions"] = permissions

                return await self._make_request(
                    "POST",
                    "/roles",
                    auth_token=auth_token,
                    json=data,
                )
            except TaigaAPIError as e:
                raise MCPError(f"API error creating role: {e}") from e

        @self.mcp.tool(
            name="taiga_get_role",
            description="Get a role by ID",
            tags={"settings", "roles", "read"},
            annotations={"readOnlyHint": True},
        )
        async def get_role(
            auth_token: str,
            role_id: int,
        ) -> dict[str, Any]:
            """Get a role by ID."""
            try:
                return await self._make_request(
                    "GET",
                    f"/roles/{role_id}",
                    auth_token=auth_token,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"Role {role_id} not found") from e

        @self.mcp.tool(
            name="taiga_update_role",
            description="Update a role",
            tags={"settings", "roles", "write"},
            annotations={"readOnlyHint": False},
        )
        async def update_role(
            auth_token: str,
            role_id: int,
            name: str | None = None,
            permissions: list[str] | None = None,
            order: int | None = None,
            computable: bool | None = None,
        ) -> dict[str, Any]:
            """Update a role."""
            try:
                data = {}
                if name is not None:
                    data["name"] = name
                if permissions is not None:
                    data["permissions"] = permissions
                if order is not None:
                    data["order"] = order
                if computable is not None:
                    data["computable"] = computable

                return await self._make_request(
                    "PATCH",
                    f"/roles/{role_id}",
                    auth_token=auth_token,
                    json=data,
                )
            except ResourceNotFoundError as e:
                raise MCPError(f"Role {role_id} not found") from e

        @self.mcp.tool(
            name="taiga_delete_role",
            description="Delete a role",
            tags={"settings", "roles", "write", "destructive"},
            annotations={"readOnlyHint": False, "destructiveHint": True},
        )
        async def delete_role(
            auth_token: str,
            role_id: int,
            moveto: int | None = None,
        ) -> dict[str, Any]:
            """Delete a role."""
            try:
                params = {"moveTo": moveto} if moveto else None
                await self._make_request(
                    "DELETE",
                    f"/roles/{role_id}",
                    auth_token=auth_token,
                    params=params,
                )
                return {"deleted": True, "role_id": role_id}
            except ResourceNotFoundError as e:
                raise MCPError(f"Role {role_id} not found") from e
