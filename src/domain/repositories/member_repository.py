"""Interfaz de repositorio para members."""

from abc import abstractmethod

from src.domain.entities.member import Member
from src.domain.repositories.base_repository import BaseRepository


class MemberRepository(BaseRepository[Member]):
    """
    Repositorio de members con operaciones específicas.

    Extiende el repositorio base con operaciones específicas para miembros
    como listado por proyecto, búsqueda por usuario y filtrado por rol.
    """

    @abstractmethod
    async def list_by_project(self, project_id: int) -> list[Member]:
        """
        Lista miembros de un proyecto específico.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de miembros del proyecto
        """

    @abstractmethod
    async def get_by_user(self, project_id: int, user_id: int) -> Member | None:
        """
        Obtiene un miembro específico de un proyecto por su user_id.

        Args:
            project_id: ID del proyecto
            user_id: ID del usuario

        Returns:
            Miembro si existe, None si no
        """

    @abstractmethod
    async def list_admins(self, project_id: int) -> list[Member]:
        """
        Lista miembros administradores de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de miembros que son administradores
        """

    @abstractmethod
    async def list_by_role(self, project_id: int, role_id: int) -> list[Member]:
        """
        Lista miembros con un rol específico.

        Args:
            project_id: ID del proyecto
            role_id: ID del rol

        Returns:
            Lista de miembros con ese rol
        """

    @abstractmethod
    async def bulk_create(self, members: list[Member]) -> list[Member]:
        """
        Crea múltiples miembros en lote.

        Args:
            members: Lista de miembros a crear

        Returns:
            Lista de miembros creados con IDs asignados
        """
