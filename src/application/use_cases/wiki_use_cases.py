"""Use cases para gestión de wiki pages."""

from typing import Any

from pydantic import BaseModel, Field

from src.domain.entities.wiki_page import WikiPage
from src.domain.exceptions import ResourceNotFoundError
from src.domain.repositories.wiki_repository import WikiRepository


# DTOs (Data Transfer Objects)


class CreateWikiPageRequest(BaseModel):
    """Request para crear wiki page."""

    slug: str = Field(..., min_length=1, max_length=255, description="Slug de la página")
    content: str = Field("", description="Contenido en markdown")
    project_id: int = Field(..., gt=0, description="ID del proyecto")


class UpdateWikiPageRequest(BaseModel):
    """Request para actualizar wiki page."""

    page_id: int = Field(..., gt=0, description="ID de la página")
    slug: str | None = Field(None, min_length=1, max_length=255, description="Slug")
    content: str | None = Field(None, description="Contenido en markdown")


class ListWikiPagesRequest(BaseModel):
    """Request para listar wiki pages."""

    project_id: int | None = Field(None, gt=0, description="Filtrar por proyecto")
    is_deleted: bool | None = Field(None, description="Filtrar por eliminadas")
    limit: int | None = Field(None, gt=0, le=100, description="Límite de resultados")
    offset: int | None = Field(None, ge=0, description="Offset para paginación")


# Use Cases


class WikiUseCases:
    """
    Casos de uso para gestión de wiki pages.

    Coordina operaciones de negocio usando el repositorio.
    NO accede directamente a TaigaAPIClient.
    """

    def __init__(self, repository: WikiRepository) -> None:
        """
        Inicializa los casos de uso.

        Args:
            repository: Repositorio de wiki pages
        """
        self.repository = repository

    async def create_wiki_page(self, request: CreateWikiPageRequest) -> WikiPage:
        """
        Crea una nueva wiki page.

        Args:
            request: Datos de la página a crear

        Returns:
            Wiki page creada con ID asignado

        Raises:
            ValidationError: Si los datos son inválidos
        """
        wiki_page = WikiPage(
            slug=request.slug,
            content=request.content,
            project_id=request.project_id,
        )

        return await self.repository.create(wiki_page)

    async def get_wiki_page(self, page_id: int) -> WikiPage:
        """
        Obtiene una wiki page por ID.

        Args:
            page_id: ID de la página

        Returns:
            Wiki page encontrada

        Raises:
            ResourceNotFoundError: Si la página no existe
        """
        page = await self.repository.get_by_id(page_id)
        if page is None:
            raise ResourceNotFoundError(f"WikiPage {page_id} not found")
        return page

    async def get_by_slug(self, project_id: int, slug: str) -> WikiPage:
        """
        Obtiene una wiki page por slug en un proyecto.

        Args:
            project_id: ID del proyecto
            slug: Slug de la página

        Returns:
            Wiki page encontrada

        Raises:
            ResourceNotFoundError: Si la página no existe
        """
        page = await self.repository.get_by_slug(project_id, slug)
        if page is None:
            raise ResourceNotFoundError(
                f"WikiPage with slug '{slug}' not found in project {project_id}"
            )
        return page

    async def list_wiki_pages(self, request: ListWikiPagesRequest) -> list[WikiPage]:
        """
        Lista wiki pages con filtros opcionales.

        Args:
            request: Filtros de búsqueda

        Returns:
            Lista de wiki pages que cumplen los filtros
        """
        filters: dict[str, Any] = {}
        if request.project_id is not None:
            filters["project"] = request.project_id
        if request.is_deleted is not None:
            filters["is_deleted"] = request.is_deleted

        return await self.repository.list(
            filters=filters,
            limit=request.limit,
            offset=request.offset,
        )

    async def list_by_project(self, project_id: int) -> list[WikiPage]:
        """
        Lista todas las wiki pages de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de wiki pages del proyecto
        """
        return await self.repository.list_by_project(project_id)

    async def list_active(self, project_id: int) -> list[WikiPage]:
        """
        Lista wiki pages activas de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de wiki pages activas
        """
        return await self.repository.list_active(project_id)

    async def list_deleted(self, project_id: int) -> list[WikiPage]:
        """
        Lista wiki pages eliminadas de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de wiki pages eliminadas
        """
        return await self.repository.list_deleted(project_id)

    async def update_wiki_page(self, request: UpdateWikiPageRequest) -> WikiPage:
        """
        Actualiza una wiki page existente.

        Args:
            request: Datos de la página a actualizar

        Returns:
            Wiki page actualizada

        Raises:
            ResourceNotFoundError: Si la página no existe
        """
        page = await self.get_wiki_page(request.page_id)

        if request.slug is not None:
            page.slug = request.slug
        if request.content is not None:
            page.update_content(request.content)

        return await self.repository.update(page)

    async def delete_wiki_page(self, page_id: int) -> bool:
        """
        Elimina una wiki page (hard delete).

        Args:
            page_id: ID de la página a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        return await self.repository.delete(page_id)

    async def soft_delete_wiki_page(self, page_id: int) -> WikiPage:
        """
        Marca una wiki page como eliminada (soft delete).

        Args:
            page_id: ID de la página

        Returns:
            Wiki page marcada como eliminada

        Raises:
            ResourceNotFoundError: Si la página no existe
        """
        page = await self.get_wiki_page(page_id)
        page.delete()
        return await self.repository.update(page)

    async def restore_wiki_page(self, page_id: int) -> WikiPage:
        """
        Restaura una wiki page eliminada (soft delete).

        Args:
            page_id: ID de la página

        Returns:
            Wiki page restaurada

        Raises:
            ResourceNotFoundError: Si la página no existe
        """
        page = await self.get_wiki_page(page_id)
        page.restore()
        return await self.repository.update(page)
