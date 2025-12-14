"""Entidad de member (miembro del proyecto)."""

from datetime import datetime

from pydantic import Field, field_validator

from src.domain.entities.base import BaseEntity
from src.domain.value_objects.email import Email


class Member(BaseEntity):
    """
    Entidad de Member (miembro del proyecto) en Taiga.

    Representa un miembro del equipo de un proyecto con su rol y permisos.

    Attributes:
        project_id: ID del proyecto
        user_id: ID del usuario
        role_id: ID del rol asignado
        full_name: Nombre completo del usuario
        username: Nombre de usuario
        email: Email del usuario
        is_admin: Indica si es administrador del proyecto
        created_date: Fecha de creación
        modified_date: Última modificación
    """

    project_id: int = Field(..., gt=0, description="ID del proyecto")
    user_id: int = Field(..., gt=0, description="ID del usuario")
    role_id: int | None = Field(None, description="ID del rol")
    full_name: str = Field("", max_length=255, description="Nombre completo")
    username: str = Field(..., min_length=1, max_length=150, description="Nombre de usuario")
    email: Email | None = Field(None, description="Email del usuario")
    is_admin: bool = Field(False, description="¿Es administrador?")
    created_date: datetime | None = Field(None, description="Fecha de creación")
    modified_date: datetime | None = Field(None, description="Última modificación")

    @field_validator("email", mode="before")
    @classmethod
    def convert_email(cls, v: object) -> Email | None:
        """
        Convierte string a Email automáticamente.

        Permite crear miembros desde datos del API que envían email como string.

        Args:
            v: Valor del email (string, Email o None)

        Returns:
            Email o None
        """
        if v is None:
            return None
        if isinstance(v, Email):
            return v
        if isinstance(v, str):
            return Email(value=v)
        return None

    @field_validator("username", mode="before")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Valida que el username no esté vacío."""
        if isinstance(v, str) and not v.strip():
            raise ValueError("El nombre de usuario no puede estar vacío")
        return v

    def make_admin(self) -> None:
        """Convierte al miembro en administrador del proyecto."""
        self.is_admin = True

    def remove_admin(self) -> None:
        """Quita permisos de administrador al miembro."""
        self.is_admin = False

    def change_role(self, role_id: int) -> None:
        """
        Cambia el rol del miembro.

        Args:
            role_id: ID del nuevo rol

        Raises:
            ValueError: Si el role_id no es válido
        """
        if role_id <= 0:
            raise ValueError("ID de rol inválido")
        self.role_id = role_id
