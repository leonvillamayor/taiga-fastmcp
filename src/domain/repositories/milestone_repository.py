"""Interfaz de repositorio para milestones."""

from abc import abstractmethod
from typing import Any

from src.domain.entities.milestone import Milestone
from src.domain.repositories.base_repository import BaseRepository


class MilestoneRepository(BaseRepository[Milestone]):
    """
    Repositorio de milestones con operaciones específicas.

    Extiende el repositorio base con operaciones específicas para milestones
    como listado por proyecto, filtrado por estado y obtención de estadísticas.
    """

    @abstractmethod
    async def list_by_project(self, project_id: int) -> list[Milestone]:
        """
        Lista milestones de un proyecto específico.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de milestones del proyecto
        """

    @abstractmethod
    async def list_open(self, project_id: int) -> list[Milestone]:
        """
        Lista milestones abiertos de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de milestones abiertos
        """

    @abstractmethod
    async def list_closed(self, project_id: int) -> list[Milestone]:
        """
        Lista milestones cerrados de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de milestones cerrados
        """

    @abstractmethod
    async def get_current(self, project_id: int) -> Milestone | None:
        """
        Obtiene el milestone actual (activo) de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Milestone actual si existe, None si no hay ninguno activo
        """

    @abstractmethod
    async def get_stats(self, milestone_id: int) -> dict[str, Any]:
        """
        Obtiene estadísticas del milestone.

        Args:
            milestone_id: ID del milestone

        Returns:
            Diccionario con estadísticas (story points, tareas completadas, etc.)

        Raises:
            ResourceNotFoundError: Si el milestone no existe
        """
