"""Interfaz de repositorio para wiki pages."""

from abc import abstractmethod

from src.domain.entities.wiki_page import WikiPage
from src.domain.repositories.base_repository import BaseRepository


class WikiRepository(BaseRepository[WikiPage]):
    """
    Repositorio de wiki pages con operaciones específicas.

    Extiende el repositorio base con operaciones específicas para páginas wiki
    como búsqueda por slug y listado por proyecto.
    """

    @abstractmethod
    async def get_by_slug(self, project_id: int, slug: str) -> WikiPage | None:
        """
        Obtiene una página wiki por su slug en un proyecto.

        Args:
            project_id: ID del proyecto
            slug: Slug de la página

        Returns:
            Página wiki si existe, None si no
        """

    @abstractmethod
    async def list_by_project(self, project_id: int) -> list[WikiPage]:
        """
        Lista todas las páginas wiki de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de páginas wiki del proyecto
        """

    @abstractmethod
    async def list_active(self, project_id: int) -> list[WikiPage]:
        """
        Lista páginas wiki activas (no eliminadas) de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de páginas wiki activas
        """

    @abstractmethod
    async def list_deleted(self, project_id: int) -> list[WikiPage]:
        """
        Lista páginas wiki eliminadas (soft delete) de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de páginas wiki eliminadas
        """
