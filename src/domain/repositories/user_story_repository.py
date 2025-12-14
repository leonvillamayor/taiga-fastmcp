"""Interfaz de repositorio para user stories."""

from abc import abstractmethod
from typing import Any

from src.domain.entities.user_story import UserStory
from src.domain.repositories.base_repository import BaseRepository


class UserStoryRepository(BaseRepository[UserStory]):
    """
    Repositorio de user stories con operaciones específicas.

    Extiende el repositorio base con operaciones específicas para user stories
    como búsqueda por referencia, filtrado por milestone y operaciones en lote.
    """

    @abstractmethod
    async def get_by_ref(self, project_id: int, ref: int) -> UserStory | None:
        """
        Obtiene una user story por su número de referencia en el proyecto.

        Args:
            project_id: ID del proyecto
            ref: Número de referencia de la user story

        Returns:
            User story si existe, None si no
        """

    @abstractmethod
    async def list_by_milestone(self, milestone_id: int) -> list[UserStory]:
        """
        Lista user stories de un milestone específico.

        Args:
            milestone_id: ID del milestone

        Returns:
            Lista de user stories del milestone
        """

    @abstractmethod
    async def list_by_status(self, project_id: int, status_id: int) -> list[UserStory]:
        """
        Lista user stories con un estado específico.

        Args:
            project_id: ID del proyecto
            status_id: ID del estado

        Returns:
            Lista de user stories con ese estado
        """

    @abstractmethod
    async def list_backlog(self, project_id: int) -> list[UserStory]:
        """
        Lista user stories en el backlog (sin milestone asignado).

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de user stories en el backlog
        """

    @abstractmethod
    async def bulk_create(self, stories: list[UserStory]) -> list[UserStory]:
        """
        Crea múltiples user stories en lote.

        Args:
            stories: Lista de user stories a crear

        Returns:
            Lista de user stories creadas con IDs asignados
        """

    @abstractmethod
    async def bulk_update(self, story_ids: list[int], updates: dict[str, Any]) -> list[UserStory]:
        """
        Actualiza múltiples user stories en lote.

        Args:
            story_ids: Lista de IDs de user stories a actualizar
            updates: Diccionario con campos a actualizar

        Returns:
            Lista de user stories actualizadas
        """

    @abstractmethod
    async def move_to_milestone(self, story_id: int, milestone_id: int | None) -> UserStory:
        """
        Mueve una user story a un milestone diferente.

        Args:
            story_id: ID de la user story
            milestone_id: ID del nuevo milestone (None para mover al backlog)

        Returns:
            User story actualizada

        Raises:
            ResourceNotFoundError: Si la story o milestone no existen
        """

    @abstractmethod
    async def get_filters(self, project_id: int) -> dict[str, Any]:
        """
        Obtiene opciones de filtro disponibles para user stories.

        Args:
            project_id: ID del proyecto

        Returns:
            Diccionario con opciones de filtro (estados, tags, usuarios, etc.)
        """
