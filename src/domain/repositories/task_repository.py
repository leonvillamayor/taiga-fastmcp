"""Interfaz de repositorio para tasks."""

from abc import abstractmethod
from typing import Any

from src.domain.entities.task import Task
from src.domain.repositories.base_repository import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """
    Repositorio de tasks con operaciones específicas.

    Extiende el repositorio base con operaciones específicas para tasks
    como búsqueda por referencia, filtrado por user story y operaciones en lote.
    """

    @abstractmethod
    async def get_by_ref(self, project_id: int, ref: int) -> Task | None:
        """
        Obtiene una task por su número de referencia en el proyecto.

        Args:
            project_id: ID del proyecto
            ref: Número de referencia de la task

        Returns:
            Task si existe, None si no
        """

    @abstractmethod
    async def list_by_user_story(self, user_story_id: int) -> list[Task]:
        """
        Lista tasks de una user story específica.

        Args:
            user_story_id: ID de la user story

        Returns:
            Lista de tasks de la user story
        """

    @abstractmethod
    async def list_by_milestone(self, milestone_id: int) -> list[Task]:
        """
        Lista tasks de un milestone específico.

        Args:
            milestone_id: ID del milestone

        Returns:
            Lista de tasks del milestone
        """

    @abstractmethod
    async def list_by_status(self, project_id: int, status_id: int) -> list[Task]:
        """
        Lista tasks con un estado específico.

        Args:
            project_id: ID del proyecto
            status_id: ID del estado

        Returns:
            Lista de tasks con ese estado
        """

    @abstractmethod
    async def list_unassigned(self, project_id: int) -> list[Task]:
        """
        Lista tasks sin asignar.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de tasks sin asignar
        """

    @abstractmethod
    async def bulk_create(self, tasks: list[Task]) -> list[Task]:
        """
        Crea múltiples tasks en lote.

        Args:
            tasks: Lista de tasks a crear

        Returns:
            Lista de tasks creadas con IDs asignados
        """

    @abstractmethod
    async def get_filters(self, project_id: int) -> dict[str, Any]:
        """
        Obtiene opciones de filtro disponibles para tasks.

        Args:
            project_id: ID del proyecto

        Returns:
            Diccionario con opciones de filtro (estados, tags, usuarios, etc.)
        """
