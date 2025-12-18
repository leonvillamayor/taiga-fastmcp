"""
Wiki repository implementation for Taiga MCP Server.

Concrete implementation using TaigaAPIClient for wiki page persistence.
"""

from typing import Any

from src.domain.entities.wiki_page import WikiPage
from src.domain.repositories.wiki_repository import WikiRepository
from src.infrastructure.repositories.base_repository_impl import \
    BaseRepositoryImpl
from src.taiga_client import TaigaAPIClient


class WikiRepositoryImpl(BaseRepositoryImpl[WikiPage], WikiRepository):
    """
    Concrete implementation of Wiki repository using Taiga API client.

    Extends BaseRepositoryImpl with wiki-specific operations like
    slug lookup and deleted page filtering.
    """

    def __init__(self, client: TaigaAPIClient) -> None:
        """
        Initialize the wiki repository.

        Args:
            client: TaigaAPIClient instance for API communication
        """
        super().__init__(client=client, entity_class=WikiPage, endpoint="wiki")

    def _to_entity(self, data: dict[str, Any]) -> WikiPage:
        """
        Convert API response dictionary to WikiPage entity.

        Handles field mapping between API response and entity.

        Args:
            data: Dictionary from API response

        Returns:
            WikiPage entity instance
        """
        # Map API fields to entity fields
        mapped_data = dict(data)
        if "project" in mapped_data and "project_id" not in mapped_data:
            mapped_data["project_id"] = mapped_data.pop("project")
        if "owner" in mapped_data and "owner_id" not in mapped_data:
            mapped_data["owner_id"] = mapped_data.pop("owner")
        return self.entity_class.model_validate(mapped_data)

    def _to_dict(self, entity: WikiPage, exclude_none: bool = True) -> dict[str, Any]:
        """
        Convert WikiPage entity to dictionary for API request.

        Maps entity fields to API field names.

        Args:
            entity: WikiPage entity instance
            exclude_none: Whether to exclude None values

        Returns:
            Dictionary for API request
        """
        data = entity.model_dump(exclude_none=exclude_none)
        # Map entity fields to API fields
        if "project_id" in data:
            data["project"] = data.pop("project_id")
        if "owner_id" in data:
            data["owner"] = data.pop("owner_id")
        return data

    async def get_by_slug(self, project_id: int, slug: str) -> WikiPage | None:
        """
        Get a wiki page by its slug in a project.

        Args:
            project_id: Project ID
            slug: Page slug

        Returns:
            WikiPage if found, None otherwise
        """
        try:
            response = await self.client.get(
                f"{self.endpoint}/by_slug", params={"project": project_id, "slug": slug}
            )
            if response and isinstance(response, dict):
                return self._to_entity(response)
            return None
        except Exception:
            return None

    async def list_by_project(self, project_id: int) -> list[WikiPage]:
        """
        List all wiki pages for a project.

        Args:
            project_id: Project ID

        Returns:
            List of wiki pages in the project
        """
        return await self.list(filters={"project": project_id})

    async def list_active(self, project_id: int) -> list[WikiPage]:
        """
        List active (not deleted) wiki pages for a project.

        Args:
            project_id: Project ID

        Returns:
            List of active wiki pages
        """
        all_pages = await self.list_by_project(project_id)
        return [page for page in all_pages if not page.is_deleted]

    async def list_deleted(self, project_id: int) -> list[WikiPage]:
        """
        List deleted (soft delete) wiki pages for a project.

        Args:
            project_id: Project ID

        Returns:
            List of deleted wiki pages
        """
        all_pages = await self.list_by_project(project_id)
        return [page for page in all_pages if page.is_deleted]
