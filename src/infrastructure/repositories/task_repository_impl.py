"""
Task repository implementation for Taiga MCP Server.

Concrete implementation using TaigaAPIClient for task persistence.
"""

from typing import Any

from src.domain.entities.task import Task
from src.domain.repositories.task_repository import TaskRepository
from src.infrastructure.repositories.base_repository_impl import BaseRepositoryImpl
from src.taiga_client import TaigaAPIClient


class TaskRepositoryImpl(BaseRepositoryImpl[Task], TaskRepository):
    """
    Concrete implementation of Task repository using Taiga API client.

    Extends BaseRepositoryImpl with task-specific operations like
    reference lookup, user story filtering, and bulk operations.
    """

    def __init__(self, client: TaigaAPIClient) -> None:
        """
        Initialize the task repository.

        Args:
            client: TaigaAPIClient instance for API communication
        """
        super().__init__(client=client, entity_class=Task, endpoint="tasks")

    def _to_entity(self, data: dict[str, Any]) -> Task:
        """
        Convert API response dictionary to Task entity.

        Handles field mapping between API response and entity.

        Args:
            data: Dictionary from API response

        Returns:
            Task entity instance
        """
        # Map API fields to entity fields
        mapped_data = dict(data)
        if "project" in mapped_data and "project_id" not in mapped_data:
            mapped_data["project_id"] = mapped_data.pop("project")
        if "user_story" in mapped_data and "user_story_id" not in mapped_data:
            mapped_data["user_story_id"] = mapped_data.pop("user_story")
        if "assigned_to" in mapped_data and "assigned_to_id" not in mapped_data:
            mapped_data["assigned_to_id"] = mapped_data.pop("assigned_to")
        if "milestone" in mapped_data and "milestone_id" not in mapped_data:
            mapped_data["milestone_id"] = mapped_data.pop("milestone")
        return self.entity_class.model_validate(mapped_data)

    def _to_dict(self, entity: Task, exclude_none: bool = True) -> dict[str, Any]:
        """
        Convert Task entity to dictionary for API request.

        Maps entity fields to API field names.

        Args:
            entity: Task entity instance
            exclude_none: Whether to exclude None values

        Returns:
            Dictionary for API request
        """
        data = entity.model_dump(exclude_none=exclude_none)
        # Map entity fields to API fields
        if "project_id" in data:
            data["project"] = data.pop("project_id")
        if "user_story_id" in data:
            data["user_story"] = data.pop("user_story_id")
        if "assigned_to_id" in data:
            data["assigned_to"] = data.pop("assigned_to_id")
        if "milestone_id" in data:
            data["milestone"] = data.pop("milestone_id")
        return data

    async def get_by_ref(self, project_id: int, ref: int) -> Task | None:
        """
        Get a task by its reference number within a project.

        Args:
            project_id: Project ID
            ref: Reference number

        Returns:
            Task if found, None otherwise
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

    async def list_by_user_story(self, user_story_id: int) -> list[Task]:
        """
        List tasks for a specific user story.

        Args:
            user_story_id: User story ID

        Returns:
            List of tasks for the user story
        """
        return await self.list(filters={"user_story": user_story_id})

    async def list_by_milestone(self, milestone_id: int) -> list[Task]:
        """
        List tasks for a specific milestone.

        Args:
            milestone_id: Milestone ID

        Returns:
            List of tasks in the milestone
        """
        return await self.list(filters={"milestone": milestone_id})

    async def list_by_status(self, project_id: int, status_id: int) -> list[Task]:
        """
        List tasks with a specific status.

        Args:
            project_id: Project ID
            status_id: Status ID

        Returns:
            List of tasks with that status
        """
        return await self.list(filters={"project": project_id, "status": status_id})

    async def list_unassigned(self, project_id: int) -> list[Task]:
        """
        List unassigned tasks.

        Args:
            project_id: Project ID

        Returns:
            List of unassigned tasks
        """
        return await self.list(filters={"project": project_id, "assigned_to__isnull": True})

    async def bulk_create(self, tasks: list[Task]) -> list[Task]:
        """
        Create multiple tasks in bulk.

        Args:
            tasks: List of tasks to create

        Returns:
            List of created tasks with assigned IDs
        """
        if not tasks:
            return []

        # Prepare bulk data
        tasks_data = [self._to_dict(task) for task in tasks]
        for data in tasks_data:
            data.pop("id", None)
            data.pop("version", None)

        try:
            response = await self.client.post(
                f"{self.endpoint}/bulk_create",
                data={"bulk_tasks": tasks_data},
            )
            if isinstance(response, list):
                return [self._to_entity(item) for item in response]
            return []
        except Exception:
            return []

    async def get_filters(self, project_id: int) -> dict[str, Any]:
        """
        Get available filter options for tasks.

        Args:
            project_id: Project ID

        Returns:
            Dictionary with filter options (statuses, tags, users, etc.)
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
