"""
Milestone repository implementation for Taiga MCP Server.

Concrete implementation using TaigaAPIClient for milestone persistence.
"""

from datetime import date
from typing import Any

from src.domain.entities.milestone import Milestone
from src.domain.exceptions import ResourceNotFoundError
from src.domain.repositories.milestone_repository import MilestoneRepository
from src.infrastructure.repositories.base_repository_impl import \
    BaseRepositoryImpl
from src.taiga_client import TaigaAPIClient


class MilestoneRepositoryImpl(BaseRepositoryImpl[Milestone], MilestoneRepository):
    """
    Concrete implementation of Milestone repository using Taiga API client.

    Extends BaseRepositoryImpl with milestone-specific operations like
    project listing, status filtering, and statistics retrieval.
    """

    def __init__(self, client: TaigaAPIClient) -> None:
        """
        Initialize the milestone repository.

        Args:
            client: TaigaAPIClient instance for API communication
        """
        super().__init__(client=client, entity_class=Milestone, endpoint="milestones")

    def _to_entity(self, data: dict[str, Any]) -> Milestone:
        """
        Convert API response dictionary to Milestone entity.

        Handles field mapping between API response and entity.

        Args:
            data: Dictionary from API response

        Returns:
            Milestone entity instance
        """
        # Map API fields to entity fields
        mapped_data = dict(data)
        if "project" in mapped_data and "project_id" not in mapped_data:
            mapped_data["project_id"] = mapped_data.pop("project")
        return self.entity_class.model_validate(mapped_data)

    def _to_dict(self, entity: Milestone, exclude_none: bool = True) -> dict[str, Any]:
        """
        Convert Milestone entity to dictionary for API request.

        Maps entity fields to API field names.

        Args:
            entity: Milestone entity instance
            exclude_none: Whether to exclude None values

        Returns:
            Dictionary for API request
        """
        data = entity.model_dump(exclude_none=exclude_none)
        # Map entity fields to API fields
        if "project_id" in data:
            data["project"] = data.pop("project_id")
        # Convert date objects to strings for API
        if "estimated_start" in data and isinstance(data["estimated_start"], date):
            data["estimated_start"] = data["estimated_start"].isoformat()
        if "estimated_finish" in data and isinstance(data["estimated_finish"], date):
            data["estimated_finish"] = data["estimated_finish"].isoformat()
        return data

    async def list_by_project(self, project_id: int) -> list[Milestone]:
        """
        List milestones for a specific project.

        Args:
            project_id: Project ID

        Returns:
            List of milestones in the project
        """
        return await self.list(filters={"project": project_id})

    async def list_open(self, project_id: int) -> list[Milestone]:
        """
        List open milestones for a project.

        Args:
            project_id: Project ID

        Returns:
            List of open milestones
        """
        return await self.list(filters={"project": project_id, "closed": False})

    async def list_closed(self, project_id: int) -> list[Milestone]:
        """
        List closed milestones for a project.

        Args:
            project_id: Project ID

        Returns:
            List of closed milestones
        """
        return await self.list(filters={"project": project_id, "closed": True})

    async def get_current(self, project_id: int) -> Milestone | None:
        """
        Get the current (active) milestone for a project.

        Returns the first open milestone ordered by estimated_start.

        Args:
            project_id: Project ID

        Returns:
            Current milestone if exists, None otherwise
        """
        open_milestones = await self.list_open(project_id)
        if not open_milestones:
            return None
        # Sort by estimated_start and return the first (current) one
        sorted_milestones = sorted(
            open_milestones,
            key=lambda m: m.estimated_start or date.max,
        )
        return sorted_milestones[0] if sorted_milestones else None

    async def get_stats(self, milestone_id: int) -> dict[str, Any]:
        """
        Get milestone statistics.

        Args:
            milestone_id: Milestone ID

        Returns:
            Dictionary with statistics (story points, completed tasks, etc.)

        Raises:
            ResourceNotFoundError: If milestone doesn't exist
        """
        try:
            response = await self.client.get(f"{self.endpoint}/{milestone_id}/stats")
            if response and isinstance(response, dict):
                return dict(response)
            raise ResourceNotFoundError(f"Milestone with id {milestone_id} not found")
        except ResourceNotFoundError:
            raise
        except Exception as e:
            error_message = str(e).lower()
            if "404" in error_message or "not found" in error_message:
                raise ResourceNotFoundError(f"Milestone with id {milestone_id} not found") from e
            raise
