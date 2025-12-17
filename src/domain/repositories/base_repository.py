"""Repositorio base con operaciones CRUD."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from src.domain.entities.base import BaseEntity


T = TypeVar("T", bound=BaseEntity)


class BaseRepository(ABC, Generic[T]):
    """
    Repositorio base con operaciones CRUD estándar.

    Todas las operaciones son asíncronas para soportar I/O no bloqueante.

    Type Parameters:
        T: Tipo de entidad que maneja este repositorio, debe heredar de BaseEntity
    """

    @abstractmethod
    async def get_by_id(self, entity_id: int) -> T | None:
        """
        Obtiene una entidad por su ID.

        Args:
            entity_id: ID de la entidad

        Returns:
            Entidad si existe, None si no existe
        """

    @abstractmethod
    async def list(
        self,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[T]:
        """
        Lista entidades con filtros opcionales.

        Args:
            filters: Diccionario de filtros
            limit: Máximo número de resultados
            offset: Número de resultados a saltar (paginación)

        Returns:
            Lista de entidades que cumplen los filtros
        """

    @abstractmethod
    async def create(self, entity: T) -> T:
        """
        Crea una nueva entidad.

        Args:
            entity: Entidad a crear (sin ID)

        Returns:
            Entidad creada con ID asignado
        """

    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        Actualiza una entidad existente.

        Args:
            entity: Entidad con cambios (debe tener ID)

        Returns:
            Entidad actualizada

        Raises:
            ResourceNotFoundError: Si la entidad no existe
            ConcurrencyError: Si la versión ha cambiado (conflict)
        """

    @abstractmethod
    async def delete(self, entity_id: int) -> bool:
        """
        Elimina una entidad.

        Args:
            entity_id: ID de la entidad a eliminar

        Returns:
            True si se eliminó, False si no existía
        """

    @abstractmethod
    async def exists(self, entity_id: int) -> bool:
        """
        Verifica si una entidad existe.

        Args:
            entity_id: ID de la entidad

        Returns:
            True si existe, False si no
        """
