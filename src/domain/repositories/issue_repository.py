"""Interfaz de repositorio para issues."""

from abc import abstractmethod
from typing import Any

from src.domain.entities.issue import Issue
from src.domain.repositories.base_repository import BaseRepository


class IssueRepository(BaseRepository[Issue]):
    """
    Repositorio de issues con operaciones específicas.

    Extiende el repositorio base con operaciones específicas para issues
    como búsqueda por referencia, filtrado por tipo/severidad/prioridad.
    """

    @abstractmethod
    async def get_by_ref(self, project_id: int, ref: int) -> Issue | None:
        """
        Obtiene un issue por su número de referencia en el proyecto.

        Args:
            project_id: ID del proyecto
            ref: Número de referencia del issue

        Returns:
            Issue si existe, None si no
        """

    @abstractmethod
    async def list_by_type(self, project_id: int, type_id: int) -> list[Issue]:
        """
        Lista issues de un tipo específico.

        Args:
            project_id: ID del proyecto
            type_id: ID del tipo de issue

        Returns:
            Lista de issues del tipo especificado
        """

    @abstractmethod
    async def list_by_severity(self, project_id: int, severity_id: int) -> list[Issue]:
        """
        Lista issues con una severidad específica.

        Args:
            project_id: ID del proyecto
            severity_id: ID de la severidad

        Returns:
            Lista de issues con esa severidad
        """

    @abstractmethod
    async def list_by_priority(self, project_id: int, priority_id: int) -> list[Issue]:
        """
        Lista issues con una prioridad específica.

        Args:
            project_id: ID del proyecto
            priority_id: ID de la prioridad

        Returns:
            Lista de issues con esa prioridad
        """

    @abstractmethod
    async def list_by_milestone(self, milestone_id: int) -> list[Issue]:
        """
        Lista issues de un milestone específico.

        Args:
            milestone_id: ID del milestone

        Returns:
            Lista de issues del milestone
        """

    @abstractmethod
    async def list_open(self, project_id: int) -> list[Issue]:
        """
        Lista issues abiertos de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de issues abiertos
        """

    @abstractmethod
    async def list_closed(self, project_id: int) -> list[Issue]:
        """
        Lista issues cerrados de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de issues cerrados
        """

    @abstractmethod
    async def bulk_create(self, issues: list[Issue]) -> list[Issue]:
        """
        Crea múltiples issues en lote.

        Args:
            issues: Lista de issues a crear

        Returns:
            Lista de issues creados con IDs asignados
        """

    @abstractmethod
    async def get_filters(self, project_id: int) -> dict[str, Any]:
        """
        Obtiene opciones de filtro disponibles para issues.

        Args:
            project_id: ID del proyecto

        Returns:
            Diccionario con opciones de filtro (tipos, severidades, prioridades, etc.)
        """
