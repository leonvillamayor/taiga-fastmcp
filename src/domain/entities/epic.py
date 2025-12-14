"""Epic entity for Taiga MCP Server."""

import re
from datetime import datetime
from typing import ClassVar

from pydantic import Field, field_validator

from src.domain.entities.base import BaseEntity


class Epic(BaseEntity):
    """
    Epic entity representing a collection of related user stories.

    An epic is a large body of work that can be broken down into smaller user stories.
    It has identity (ID), version control for concurrency, and various business attributes.

    Attributes:
        project: Project ID where the epic belongs
        subject: Title of the epic
        description: Detailed description
        color: Color in hexadecimal format (e.g., "#A5694F")
        assigned_to: User ID assigned to the epic
        status: Status ID of the epic
        tags: List of tags for categorization
        client_requirement: Flag if it's a client requirement
        team_requirement: Flag if it's a team requirement
        ref: Reference number within the project
        created_date: Creation timestamp
        modified_date: Last modification timestamp
        watchers: List of user IDs watching the epic
        voters: List of user IDs who voted for the epic
        total_voters: Total number of voters
        owner: User ID of the epic owner
    """

    # Default color for epics in hexadecimal format
    DEFAULT_COLOR: ClassVar[str] = "#A5694F"

    # Color validation regex pattern
    COLOR_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^#[0-9A-Fa-f]{6}$")

    project: int = Field(..., gt=0, description="Project ID where the epic belongs")
    subject: str = Field(..., min_length=1, max_length=500, description="Title of the epic")
    description: str | None = Field(None, description="Detailed description")
    color: str = Field(DEFAULT_COLOR, description="Color in hexadecimal format")
    assigned_to: int | None = Field(None, description="User ID assigned to the epic")
    status: int | None = Field(None, description="Status ID of the epic")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    client_requirement: bool = Field(False, description="Is client requirement")
    team_requirement: bool = Field(False, description="Is team requirement")
    ref: int | None = Field(None, description="Reference number within the project")
    created_date: datetime | None = Field(None, description="Creation timestamp")
    modified_date: datetime | None = Field(None, description="Last modification timestamp")
    watchers: list[int] = Field(default_factory=list, description="User IDs watching the epic")
    voters: list[int] = Field(default_factory=list, description="User IDs who voted")
    total_voters: int = Field(0, ge=0, description="Total number of voters")
    owner: int | None = Field(None, description="User ID of the epic owner")

    @field_validator("subject", mode="before")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Valida que el subject no esté vacío."""
        if isinstance(v, str) and not v.strip():
            raise ValueError("Subject cannot be empty")
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Valida formato de color hexadecimal."""
        if not cls.COLOR_PATTERN.match(v):
            raise ValueError(f"Invalid color format: {v}. Must be hexadecimal (e.g., #FF0000)")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Normaliza tags."""
        return list({tag.lower().strip() for tag in v if tag.strip()})

    def increment_version(self) -> None:
        """Increment version for optimistic locking."""
        if self.version is None:
            self.version = 1
        else:
            self.version += 1

    def validate_version_match(self, expected_version: int) -> None:
        """
        Validate version for concurrency control.

        Args:
            expected_version: The expected version number

        Raises:
            ValueError: If version doesn't match (conflict)
        """
        if self.version != expected_version:
            raise ValueError(f"Version conflict: expected {expected_version}, got {self.version}")

    def add_tag(self, tag: str) -> None:
        """Add a tag to the epic."""
        normalized_tag = tag.lower().strip()
        if normalized_tag and normalized_tag not in self.tags:
            self.tags.append(normalized_tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the epic."""
        normalized_tag = tag.lower().strip()
        if normalized_tag in self.tags:
            self.tags.remove(normalized_tag)

    def add_watcher(self, user_id: int) -> None:
        """Add a user as watcher."""
        if user_id not in self.watchers:
            self.watchers.append(user_id)

    def remove_watcher(self, user_id: int) -> None:
        """
        Remove a user from watchers.

        Raises:
            ValueError: If user is not watching
        """
        if user_id not in self.watchers:
            raise ValueError(f"User is not watching this epic: {user_id}")
        self.watchers.remove(user_id)

    def add_voter(self, user_id: int) -> None:
        """Add a user as voter (upvote)."""
        if user_id not in self.voters:
            self.voters.append(user_id)
            self.total_voters += 1

    def remove_voter(self, user_id: int) -> None:
        """
        Remove a user from voters (downvote).

        Raises:
            ValueError: If user has not voted
        """
        if user_id not in self.voters:
            raise ValueError(f"User has not voted for this epic: {user_id}")
        self.voters.remove(user_id)
        self.total_voters = max(0, self.total_voters - 1)

    def toggle_client_requirement(self) -> None:
        """Toggle the client requirement flag."""
        self.client_requirement = not self.client_requirement

    def toggle_team_requirement(self) -> None:
        """Toggle the team requirement flag."""
        self.team_requirement = not self.team_requirement

    def set_created_date(self, date: datetime) -> None:
        """Set the creation date."""
        self.created_date = date

    def set_modified_date(self, date: datetime) -> None:
        """Set the modification date."""
        self.modified_date = date
