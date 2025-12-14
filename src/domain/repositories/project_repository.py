"""Interfaz de repositorio para proyectos."""

from abc import abstractmethod
from typing import Any

from src.domain.entities.project import Project
from src.domain.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """
    Repositorio de proyectos con operaciones específicas.

    Extiende el repositorio base con operaciones específicas para proyectos
    como búsqueda por slug, filtrado por privacidad y estadísticas.
    """

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Project | None:
        """
        Obtiene un proyecto por su slug.

        Args:
            slug: Slug del proyecto

        Returns:
            Proyecto si existe, None si no
        """

    @abstractmethod
    async def list_by_member(self, member_id: int) -> list[Project]:
        """
        Lista proyectos de un miembro específico.

        Args:
            member_id: ID del miembro

        Returns:
            Lista de proyectos del miembro
        """

    @abstractmethod
    async def list_private(self) -> list[Project]:
        """
        Lista solo proyectos privados.

        Returns:
            Lista de proyectos privados
        """

    @abstractmethod
    async def list_public(self) -> list[Project]:
        """
        Lista solo proyectos públicos.

        Returns:
            Lista de proyectos públicos
        """

    @abstractmethod
    async def list_with_backlog(self) -> list[Project]:
        """
        Lista proyectos con backlog activado.

        Returns:
            Lista de proyectos con backlog habilitado
        """

    @abstractmethod
    async def get_stats(self, project_id: int) -> dict[str, Any]:
        """
        Obtiene estadísticas del proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Diccionario con estadísticas del proyecto, dict vacío si hay error
        """
