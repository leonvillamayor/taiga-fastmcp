"""
RelatedUserStory entity for Taiga MCP Server.
Represents a relationship between an epic and a user story.
"""

from typing import Any


class RelatedUserStory:
    """
    RelatedUserStory entity representing the relationship between an epic and a user story.

    This is an association entity that manages the many-to-many relationship
    between epics and user stories, including ordering and additional metadata.
    """

    def __init__(
        self,
        epic: int,
        user_story: int,
        order: int = 0,
        id: int | None = None,
        user_story_details: dict[str, Any] | None = None,
        epic_project: int | None = None,
        userstory_project: int | None = None,
    ):
        """
        Initialize a RelatedUserStory entity.

        Args:
            epic: Epic ID
            user_story: User Story ID
            order: Order position within the epic (0 for no specific order)
            id: Unique identifier (None for new relations)
            user_story_details: Additional details about the user story
            epic_project: Project ID of the epic (for validation)
            userstory_project: Project ID of the user story (for validation)
        """
        # Validate order
        if order < 0:
            from src.domain.exceptions import ValidationError

            raise ValidationError("Order must be positive or zero")

        self.id = id
        self.epic = epic
        self.user_story = user_story
        self.order = order
        self.user_story_details = user_story_details or {}
        self.epic_project = epic_project
        self.userstory_project = userstory_project

    def update_order(self, new_order: int) -> None:
        """
        Update the order of the relationship.

        Args:
            new_order: New order value

        Raises:
            ValidationError: If the order is negative
        """
        if new_order < 0:
            from src.domain.exceptions import ValidationError

            raise ValidationError("Order must be positive or zero")
        self.order = new_order

    def is_same_project(self) -> bool:
        """
        Check if epic and user story belong to the same project.

        Returns:
            True if both are in the same project, False otherwise.
            Returns True if project information is not available.
        """
        if self.epic_project is None or self.userstory_project is None:
            return True  # Assume valid if no project info
        return self.epic_project == self.userstory_project

    def to_dict(self) -> dict[str, Any]:
        """
        Convert relationship to dictionary representation.

        Returns:
            Dictionary with all relationship attributes
        """
        result: dict[str, Any] = {
            "id": self.id,
            "epic": self.epic,
            "user_story": self.user_story,
            "order": self.order,
        }

        if self.user_story_details:
            result["user_story_details"] = self.user_story_details

        if self.epic_project is not None:
            result["epic_project"] = self.epic_project

        if self.userstory_project is not None:
            result["userstory_project"] = self.userstory_project

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RelatedUserStory":
        """
        Create a RelatedUserStory instance from a dictionary.

        Args:
            data: Dictionary with relationship data

        Returns:
            RelatedUserStory instance
        """
        # Handle nested user_story data
        user_story_details = data.get("user_story", {})
        user_story_id = data.get("user_story")

        # If user_story is a dict, extract the ID and keep the details
        if isinstance(user_story_id, dict):
            user_story_id = user_story_details.get("id")

        # Extract project IDs if available
        epic_project = None
        userstory_project = None

        if isinstance(user_story_details, dict):
            userstory_project = user_story_details.get("project")

        # Validate required fields
        epic_value = data.get("epic")
        if epic_value is None:
            from src.domain.exceptions import ValidationError

            raise ValidationError("epic is required")

        # Determine user_story value
        final_user_story = (
            user_story_id if isinstance(user_story_id, int) else data.get("user_story_id")
        )
        if final_user_story is None:
            from src.domain.exceptions import ValidationError

            raise ValidationError("user_story is required")

        return cls(
            id=data.get("id"),
            epic=epic_value,
            user_story=final_user_story,
            order=data.get("order", 0),
            user_story_details=user_story_details if isinstance(user_story_details, dict) else None,
            epic_project=data.get("epic_project", epic_project),
            userstory_project=data.get("userstory_project", userstory_project),
        )

    def __eq__(self, other: object) -> bool:
        """
        Compare relationships by ID or by epic-userstory combination.

        Two relationships are equal if:
        1. They have the same ID (if both have IDs)
        2. They relate the same epic and user story (if no IDs)
        """
        if not isinstance(other, RelatedUserStory):
            return False

        # If both have IDs, compare by ID
        if self.id is not None and other.id is not None:
            return self.id == other.id

        # Otherwise, compare by epic and user_story
        return self.epic == other.epic and self.user_story == other.user_story

    def __hash__(self) -> int:
        """
        Hash based on ID or epic-userstory combination.

        Returns:
            Hash of the relationship
        """
        if self.id is not None:
            return hash(self.id)
        return hash((self.epic, self.user_story))

    def is_duplicate_of(self, other: "RelatedUserStory") -> bool:
        """
        Check if this relationship is a duplicate of another.

        Args:
            other: Another RelatedUserStory to compare with

        Returns:
            True if they relate the same epic and user story
        """
        return self.epic == other.epic and self.user_story == other.user_story

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"RelatedUserStory(id={self.id}, epic={self.epic}, "
            f"user_story={self.user_story}, order={self.order})"
        )
