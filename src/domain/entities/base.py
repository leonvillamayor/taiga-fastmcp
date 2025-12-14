"""Entidad base del dominio."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseEntity(BaseModel):
    """
    Clase base para todas las entidades del dominio.

    Las entidades son objetos que tienen identidad única (ID) y son mutables.
    Dos entidades son iguales si tienen el mismo ID.

    Attributes:
        id: Identificador único de la entidad
        version: Versión para control de concurrencia optimista
    """

    model_config = ConfigDict(
        frozen=False,  # Entidades son mutables
        validate_assignment=True,  # Validar al asignar valores
        arbitrary_types_allowed=True,  # Permitir tipos arbitrarios
        str_strip_whitespace=True,  # Eliminar espacios en strings
    )

    id: int | None = Field(None, description="ID único de la entidad")
    version: int | None = Field(None, description="Versión para control de concurrencia")

    def __eq__(self, other: object) -> bool:
        """
        Dos entidades son iguales si tienen el mismo ID.

        Args:
            other: Objeto a comparar

        Returns:
            True si ambas entidades tienen el mismo ID, False en caso contrario
        """
        if not isinstance(other, BaseEntity):
            return False
        return self.id is not None and self.id == other.id

    def __hash__(self) -> int:
        """
        Hash basado en ID.

        Returns:
            Hash del ID si existe, hash del objeto en caso contrario
        """
        return hash(self.id) if self.id else id(self)

    def to_dict(self) -> dict[str, Any]:
        """
        Convierte la entidad a diccionario.

        Returns:
            Diccionario con los datos de la entidad
        """
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseEntity":
        """
        Crea una entidad desde un diccionario.

        Args:
            data: Diccionario con los datos de la entidad

        Returns:
            Nueva instancia de la entidad
        """
        return cls.model_validate(data)

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """
        Actualiza campos de la entidad desde un diccionario.

        Solo actualiza los campos presentes en el diccionario.

        Args:
            data: Diccionario con los campos a actualizar
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
