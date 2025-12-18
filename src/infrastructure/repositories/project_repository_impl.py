"""
Project repository implementation for Taiga MCP Server.

Concrete implementation using TaigaAPIClient for project persistence.
"""

from typing import Any

from src.domain.entities.project import Project
from src.domain.repositories.project_repository import ProjectRepository
from src.infrastructure.repositories.base_repository_impl import BaseRepositoryImpl
from src.taiga_client import TaigaAPIClient


class ProjectRepositoryImpl(BaseRepositoryImpl[Project], ProjectRepository):
    """
    Concrete implementation of Project repository using Taiga API client.

    Extends BaseRepositoryImpl with project-specific operations like
    slug lookup, member filtering, and project statistics.
    """

    def __init__(self, client: TaigaAPIClient) -> None:
        """
        Initialize the project repository.

        Args:
            client: TaigaAPIClient instance for API communication
        """
        super().__init__(client=client, entity_class=Project, endpoint="projects")

    async def get_by_slug(self, slug: str) -> Project | None:
        """
        Get a project by its slug.

        Args:
            slug: Project slug (URL-friendly identifier)

        Returns:
            Project if found, None otherwise
        """
        try:
            response = await self.client.get(f"{self.endpoint}/by_slug", params={"slug": slug})
            if response and isinstance(response, dict):
                return self._to_entity(response)
            return None
        except Exception:
            return None

    async def list_by_member(self, member_id: int) -> list[Project]:
        """
        List projects for a specific member.

        Args:
            member_id: ID of the member

        Returns:
            List of projects the member belongs to
        """
        return await self.list(filters={"member": member_id})

    async def list_private(self) -> list[Project]:
        """
        List only private projects.

        Returns:
            List of private projects
        """
        return await self.list(filters={"is_private": True})

    async def list_public(self) -> list[Project]:
        """
        List only public projects.

        Returns:
            List of public projects
        """
        return await self.list(filters={"is_private": False})

    async def list_with_backlog(self) -> list[Project]:
        """
        List projects with backlog activated.

        Returns:
            List of projects with backlog enabled
        """
        return await self.list(filters={"is_backlog_activated": True})

    async def get_stats(self, project_id: int) -> dict[str, Any]:
        """
        Get project statistics.

        Args:
            project_id: Project ID

        Returns:
            Dictionary with project statistics, empty dict on error
        """
        try:
            response = await self.client.get(f"{self.endpoint}/{project_id}/stats")
            if response and isinstance(response, dict):
                return dict(response)
            return {}
        except Exception:
            return {}
