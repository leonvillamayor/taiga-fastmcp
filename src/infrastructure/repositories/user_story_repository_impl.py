"""
User Story repository implementation for Taiga MCP Server.

Concrete implementation using TaigaAPIClient for user story persistence.
"""

from typing import Any, cast

from src.domain.entities.user_story import UserStory
from src.domain.exceptions import ResourceNotFoundError
from src.domain.repositories.user_story_repository import UserStoryRepository
from src.infrastructure.repositories.base_repository_impl import \
    BaseRepositoryImpl
from src.taiga_client import TaigaAPIClient


class UserStoryRepositoryImpl(BaseRepositoryImpl[UserStory], UserStoryRepository):
    """
    Concrete implementation of UserStory repository using Taiga API client.

    Extends BaseRepositoryImpl with user story-specific operations like
    reference lookup, milestone filtering, and bulk operations.
    """

    def __init__(self, client: TaigaAPIClient) -> None:
        """
        Initialize the user story repository.

        Args:
            client: TaigaAPIClient instance for API communication
        """
        super().__init__(client=client, entity_class=UserStory, endpoint="userstories")

    def _to_entity(self, data: dict[str, Any]) -> UserStory:
        """
        Convert API response dictionary to UserStory entity.

        Handles field mapping between API response and entity.

        Args:
            data: Dictionary from API response

        Returns:
            UserStory entity instance
        """
        # Map API fields to entity fields
        mapped_data = dict(data)
        if "project" in mapped_data and "project_id" not in mapped_data:
            mapped_data["project_id"] = mapped_data.pop("project")
        if "assigned_to" in mapped_data and "assigned_to_id" not in mapped_data:
            mapped_data["assigned_to_id"] = mapped_data.pop("assigned_to")
        if "milestone" in mapped_data and "milestone_id" not in mapped_data:
            mapped_data["milestone_id"] = mapped_data.pop("milestone")
        return self.entity_class.model_validate(mapped_data)

    def _to_dict(self, entity: UserStory, exclude_none: bool = True) -> dict[str, Any]:
        """
        Convert UserStory entity to dictionary for API request.

        Maps entity fields to API field names.

        Args:
            entity: UserStory entity instance
            exclude_none: Whether to exclude None values

        Returns:
            Dictionary for API request
        """
        data = entity.model_dump(exclude_none=exclude_none)
        # Map entity fields to API fields
        if "project_id" in data:
            data["project"] = data.pop("project_id")
        if "assigned_to_id" in data:
            data["assigned_to"] = data.pop("assigned_to_id")
        if "milestone_id" in data:
            data["milestone"] = data.pop("milestone_id")
        return data

    async def get_by_ref(self, project_id: int, ref: int) -> UserStory | None:
        """
        Get a user story by its reference number within a project.

        Args:
            project_id: Project ID
            ref: Reference number

        Returns:
            UserStory if found, None otherwise
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

    async def list_by_milestone(self, milestone_id: int) -> list[UserStory]:
        """
        List user stories for a specific milestone.

        Args:
            milestone_id: Milestone ID

        Returns:
            List of user stories in the milestone
        """
        return await self.list(filters={"milestone": milestone_id})

    async def list_by_status(self, project_id: int, status_id: int) -> list[UserStory]:
        """
        List user stories with a specific status.

        Args:
            project_id: Project ID
            status_id: Status ID

        Returns:
            List of user stories with that status
        """
        return await self.list(filters={"project": project_id, "status": status_id})

    async def list_backlog(self, project_id: int) -> list[UserStory]:
        """
        List user stories in the backlog (no milestone assigned).

        Args:
            project_id: Project ID

        Returns:
            List of user stories in the backlog
        """
        return await self.list(filters={"project": project_id, "milestone__isnull": True})

    async def bulk_create(self, stories: list[UserStory]) -> list[UserStory]:
        """
        Create multiple user stories in bulk.

        Args:
            stories: List of user stories to create

        Returns:
            List of created user stories with assigned IDs
        """
        if not stories:
            return []

        # Extract project_id from first story
        project_id = stories[0].project_id

        # Prepare bulk data - convert stories to subjects string
        subjects = "\n".join(story.subject for story in stories)

        try:
            response = await self.client.post(
                f"{self.endpoint}/bulk_create",
                data={"project_id": project_id, "bulk_stories": subjects},
            )
            if isinstance(response, list):
                return [self._to_entity(item) for item in response]
            return []
        except Exception:
            return []

    async def bulk_update(self, story_ids: list[int], updates: dict[str, Any]) -> list[UserStory]:
        """
        Update multiple user stories in bulk.

        Args:
            story_ids: List of user story IDs to update
            updates: Dictionary with fields to update

        Returns:
            List of updated user stories
        """
        if not story_ids:
            return []

        # Map entity field names to API field names
        api_updates = dict(updates)
        if "project_id" in api_updates:
            api_updates["project"] = api_updates.pop("project_id")
        if "assigned_to_id" in api_updates:
            api_updates["assigned_to"] = api_updates.pop("assigned_to_id")
        if "milestone_id" in api_updates:
            api_updates["milestone"] = api_updates.pop("milestone_id")

        try:
            response = await self.client.post(
                f"{self.endpoint}/bulk_update_order",
                data={"story_ids": story_ids, **api_updates},
            )
            if isinstance(response, list):
                return [self._to_entity(item) for item in response]

            # Fetch updated stories if bulk update doesn't return them
            updated_stories = []
            for story_id in story_ids:
                story = await self.get_by_id(story_id)
                if story:
                    updated_stories.append(story)
            return updated_stories
        except Exception:
            return []

    async def move_to_milestone(self, story_id: int, milestone_id: int | None) -> UserStory:
        """
        Move a user story to a different milestone.

        Args:
            story_id: User story ID
            milestone_id: Target milestone ID (None to move to backlog)

        Returns:
            Updated user story

        Raises:
            ResourceNotFoundError: If story doesn't exist
        """
        story = await self.get_by_id(story_id)
        if story is None:
            raise ResourceNotFoundError(f"UserStory with id {story_id} not found")

        try:
            response = await self.client.patch(
                f"{self.endpoint}/{story_id}",
                data={"milestone": milestone_id, "version": story.version},
            )
            return self._to_entity(cast("dict[str, Any]", response))
        except Exception as e:
            error_message = str(e).lower()
            if "404" in error_message or "not found" in error_message:
                raise ResourceNotFoundError(f"UserStory with id {story_id} not found") from e
            raise

    async def get_filters(self, project_id: int) -> dict[str, Any]:
        """
        Get available filter options for user stories.

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
