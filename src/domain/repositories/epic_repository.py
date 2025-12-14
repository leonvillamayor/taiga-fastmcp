"""
Epic repository interface for Taiga MCP Server.
Defines the contract for epic persistence operations.
"""

from abc import abstractmethod
from typing import Any

from src.domain.entities.epic import Epic
from src.domain.repositories.base_repository import BaseRepository


class EpicRepository(BaseRepository[Epic]):
    """
    Abstract repository interface for Epic entities.

    This interface defines the contract that any epic repository
    implementation must follow, ensuring separation between domain
    and infrastructure layers.

    Extiende el repositorio base con operaciones específicas para epics.
    """

    @abstractmethod
    async def get_by_ref(self, project_id: int, ref: int) -> Epic | None:
        """
        Get an epic by its reference number within a project.

        Args:
            project_id: Project ID
            ref: Reference number

        Returns:
            Epic if found, None otherwise
        """

    @abstractmethod
    async def bulk_create(self, epics: list[Epic]) -> list[Epic]:
        """
        Create multiple epics in bulk.

        Args:
            epics: List of epics to create

        Returns:
            List of created epics with assigned IDs
        """

    @abstractmethod
    async def get_filters(self, project_id: int) -> dict[str, Any]:
        """
        Get available filter options for epics.

        Args:
            project_id: Project ID

        Returns:
            Dictionary with filter options (statuses, tags, assigned_to)
        """

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
    async def unwatch(self, epic_id: int) -> Epic:
        """
        Stop watching an epic.

        Args:
            epic_id: Epic ID

        Returns:
            Updated epic with watcher data

        Raises:
            ResourceNotFoundError: If epic doesn't exist
            ValueError: If user is not watching the epic
        """

    @abstractmethod
    async def list_by_project(self, project_id: int) -> list[Epic]:
        """
        List all epics from a specific project.

        Args:
            project_id: Project ID

        Returns:
            List of epics from the project
        """

    @abstractmethod
    async def list_by_status(self, project_id: int, status_id: int) -> list[Epic]:
        """
        List epics with a specific status.

        Args:
            project_id: Project ID
            status_id: Status ID

        Returns:
            List of epics with that status
        """
