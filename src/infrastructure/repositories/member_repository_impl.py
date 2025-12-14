"""
Member repository implementation for Taiga MCP Server.

Concrete implementation using TaigaAPIClient for member persistence.
"""

from typing import Any

from src.domain.entities.member import Member
from src.domain.repositories.member_repository import MemberRepository
from src.infrastructure.repositories.base_repository_impl import BaseRepositoryImpl
from src.taiga_client import TaigaAPIClient


class MemberRepositoryImpl(BaseRepositoryImpl[Member], MemberRepository):
    """
    Concrete implementation of Member repository using Taiga API client.

    Extends BaseRepositoryImpl with member-specific operations like
    project listing, user lookup, and role filtering.
    """

    def __init__(self, client: TaigaAPIClient) -> None:
        """
        Initialize the member repository.

        Args:
            client: TaigaAPIClient instance for API communication
        """
        super().__init__(client=client, entity_class=Member, endpoint="memberships")

    def _to_entity(self, data: dict[str, Any]) -> Member:
        """
        Convert API response dictionary to Member entity.

        Handles field mapping between API response and entity.

        Args:
            data: Dictionary from API response

        Returns:
            Member entity instance
        """
        # Map API fields to entity fields
        mapped_data = dict(data)
        if "project" in mapped_data and "project_id" not in mapped_data:
            mapped_data["project_id"] = mapped_data.pop("project")
        if "user" in mapped_data and "user_id" not in mapped_data:
            mapped_data["user_id"] = mapped_data.pop("user")
        if "role" in mapped_data and "role_id" not in mapped_data:
            mapped_data["role_id"] = mapped_data.pop("role")
        return self.entity_class.model_validate(mapped_data)

    def _to_dict(self, entity: Member, exclude_none: bool = True) -> dict[str, Any]:
        """
        Convert Member entity to dictionary for API request.

        Maps entity fields to API field names.

        Args:
            entity: Member entity instance
            exclude_none: Whether to exclude None values

        Returns:
            Dictionary for API request
        """
        data = entity.model_dump(exclude_none=exclude_none)
        # Map entity fields to API fields
        if "project_id" in data:
            data["project"] = data.pop("project_id")
        if "user_id" in data:
            data["user"] = data.pop("user_id")
        if "role_id" in data:
            data["role"] = data.pop("role_id")
        # Handle email value object
        if "email" in data and data["email"] is not None and hasattr(data["email"], "value"):
            data["email"] = data["email"].value
        return data

    async def list_by_project(self, project_id: int) -> list[Member]:
        """
        List members for a specific project.

        Args:
            project_id: Project ID

        Returns:
            List of members in the project
        """
        return await self.list(filters={"project": project_id})

    async def get_by_user(self, project_id: int, user_id: int) -> Member | None:
        """
        Get a specific member by user ID in a project.

        Args:
            project_id: Project ID
            user_id: User ID

        Returns:
            Member if found, None otherwise
        """
        members = await self.list(filters={"project": project_id, "user": user_id})
        return members[0] if members else None

    async def list_admins(self, project_id: int) -> list[Member]:
        """
        List admin members for a project.

        Args:
            project_id: Project ID

        Returns:
            List of admin members
        """
        members = await self.list_by_project(project_id)
        return [m for m in members if m.is_admin]

    async def list_by_role(self, project_id: int, role_id: int) -> list[Member]:
        """
        List members with a specific role.

        Args:
            project_id: Project ID
            role_id: Role ID

        Returns:
            List of members with that role
        """
        return await self.list(filters={"project": project_id, "role": role_id})

    async def bulk_create(self, members: list[Member]) -> list[Member]:
        """
        Create multiple members in bulk.

        Args:
            members: List of members to create

        Returns:
            List of created members with assigned IDs
        """
        if not members:
            return []

        # Extract project_id from first member
        project_id = members[0].project_id

        # Prepare bulk data
        members_data = [self._to_dict(member) for member in members]
        for data in members_data:
            data.pop("id", None)
            data.pop("version", None)

        try:
            response = await self.client.post(
                f"{self.endpoint}/bulk_create",
                data={"project_id": project_id, "bulk_memberships": members_data},
            )
            if isinstance(response, list):
                return [self._to_entity(item) for item in response]
            return []
        except Exception:
            return []
