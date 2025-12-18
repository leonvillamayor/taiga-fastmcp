"""
Epic repository implementation for Taiga MCP Server.

Concrete implementation using TaigaAPIClient for epic persistence.
"""

from typing import Any

from src.domain.entities.epic import Epic
from src.domain.exceptions import ResourceNotFoundError
from src.domain.repositories.epic_repository import EpicRepository
from src.infrastructure.repositories.base_repository_impl import BaseRepositoryImpl
from src.taiga_client import TaigaAPIClient


class EpicRepositoryImpl(BaseRepositoryImpl[Epic], EpicRepository):
    """
    Concrete implementation of Epic repository using Taiga API client.

    Extends BaseRepositoryImpl with epic-specific operations like
    reference lookup, bulk creation, voting, and watching.
    """

    def __init__(self, client: TaigaAPIClient) -> None:
        """
        Initialize the epic repository.

        Args:
            client: TaigaAPIClient instance for API communication
        """
        super().__init__(client=client, entity_class=Epic, endpoint="epics")

    async def get_by_ref(self, project_id: int, ref: int) -> Epic | None:
        """
        Get an epic by its reference number within a project.

        Args:
            project_id: Project ID
            ref: Reference number

        Returns:
            Epic if found, None otherwise
        """
        try:
            response = await self.client.get(
                f"{self.endpoint}/by_ref", params={"project": project_id, "ref": ref}
            )
            if response and isinstance(response, dict):
                return self._to_entity(response)
            return None
        except Exception:
            return None

    async def bulk_create(self, epics: list[Epic]) -> list[Epic]:
        """
        Create multiple epics in bulk.

        Args:
            epics: List of epics to create

        Returns:
            List of created epics with assigned IDs
        """
        if not epics:
            return []

        # Extract project_id from first epic
        project_id = epics[0].project

        # Prepare bulk data
        epics_data = [self._to_dict(epic) for epic in epics]
        for data in epics_data:
            data.pop("id", None)
            data.pop("version", None)

        try:
            response = await self.client.post(
                f"{self.endpoint}/bulk_create",
                data={"project_id": project_id, "bulk_epics": epics_data},
            )
            if isinstance(response, list):
                return [self._to_entity(item) for item in response]
            return []
        except Exception:
            return []

    async def get_filters(self, project_id: int) -> dict[str, Any]:
        """
        Get available filter options for epics.

        Args:
            project_id: Project ID

        Returns:
            Dictionary with filter options (statuses, tags, assigned_to)
        """
        try:
            response = await self.client.get(
                f"{self.endpoint}/filters_data", params={"project": project_id}
            )
            if response and isinstance(response, dict):
                return dict(response)
            return {}
        except Exception:
            return {}

    async def upvote(self, epic_id: int) -> Epic:
        """
        Upvote an epic.

        Args:
            epic_id: Epic ID

        Returns:
            Updated epic with vote data

        Raises:
            ResourceNotFoundError: If epic doesn't exist
        """
        try:
            await self.client.post(f"{self.endpoint}/{epic_id}/upvote", data={})
            epic = await self.get_by_id(epic_id)
            if epic is None:
                raise ResourceNotFoundError(f"Epic with id {epic_id} not found")
            return epic
        except ResourceNotFoundError:
            raise
        except Exception as e:
            error_message = str(e).lower()
            if "404" in error_message or "not found" in error_message:
                raise ResourceNotFoundError(f"Epic with id {epic_id} not found") from e
            raise

    async def downvote(self, epic_id: int) -> Epic:
        """
        Downvote an epic.

        Args:
            epic_id: Epic ID

        Returns:
            Updated epic with vote data

        Raises:
            ResourceNotFoundError: If epic doesn't exist
        """
        try:
            await self.client.post(f"{self.endpoint}/{epic_id}/downvote", data={})
            epic = await self.get_by_id(epic_id)
            if epic is None:
                raise ResourceNotFoundError(f"Epic with id {epic_id} not found")
            return epic
        except ResourceNotFoundError:
            raise
        except Exception as e:
            error_message = str(e).lower()
            if "404" in error_message or "not found" in error_message:
                raise ResourceNotFoundError(f"Epic with id {epic_id} not found") from e
            raise

    async def watch(self, epic_id: int) -> Epic:
        """
        Watch an epic.

        Args:
            epic_id: Epic ID

        Returns:
            Updated epic with watcher data

        Raises:
            ResourceNotFoundError: If epic doesn't exist
        """
        try:
            await self.client.post(f"{self.endpoint}/{epic_id}/watch", data={})
            epic = await self.get_by_id(epic_id)
            if epic is None:
                raise ResourceNotFoundError(f"Epic with id {epic_id} not found")
            return epic
        except ResourceNotFoundError:
            raise
        except Exception as e:
            error_message = str(e).lower()
            if "404" in error_message or "not found" in error_message:
                raise ResourceNotFoundError(f"Epic with id {epic_id} not found") from e
            raise

    async def unwatch(self, epic_id: int) -> Epic:
        """
        Stop watching an epic.

        Args:
            epic_id: Epic ID

        Returns:
            Updated epic with watcher data

        Raises:
            ResourceNotFoundError: If epic doesn't exist
        """
        try:
            await self.client.post(f"{self.endpoint}/{epic_id}/unwatch", data={})
            epic = await self.get_by_id(epic_id)
            if epic is None:
                raise ResourceNotFoundError(f"Epic with id {epic_id} not found")
            return epic
        except ResourceNotFoundError:
            raise
        except Exception as e:
            error_message = str(e).lower()
            if "404" in error_message or "not found" in error_message:
                raise ResourceNotFoundError(f"Epic with id {epic_id} not found") from e
            raise

    async def list_by_project(self, project_id: int) -> list[Epic]:
        """
        List all epics from a specific project.

        Args:
            project_id: Project ID

        Returns:
            List of epics from the project
        """
        return await self.list(filters={"project": project_id})

    async def list_by_status(self, project_id: int, status_id: int) -> list[Epic]:
        """
        List epics with a specific status.

        Args:
            project_id: Project ID
            status_id: Status ID

        Returns:
            List of epics with that status
        """
        return await self.list(filters={"project": project_id, "status": status_id})
