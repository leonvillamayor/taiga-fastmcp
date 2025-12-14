"""Entidad de wiki page."""

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from src.domain.entities.base import BaseEntity


class WikiPage(BaseEntity):
    """
    Entidad de Wiki Page en Taiga.

    Representa una página de la wiki del proyecto.

    Attributes:
        slug: Slug único de la página
        content: Contenido en formato markdown
        project_id: ID del proyecto
        owner_id: ID del propietario de la página
        is_deleted: Indica si está eliminada (soft delete)
        created_date: Fecha de creación
        modified_date: Última modificación
    """

    slug: str = Field(..., min_length=1, max_length=255, description="Slug de la página")
    content: str = Field("", description="Contenido en markdown")
    project_id: int = Field(..., gt=0, description="ID del proyecto")
    owner_id: int | None = Field(None, description="ID del propietario")
    is_deleted: bool = Field(False, description="¿Está eliminada?")
    created_date: datetime | None = Field(None, description="Fecha de creación")
    modified_date: datetime | None = Field(None, description="Última modificación")

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v: Any) -> Any:
        """Valida y normaliza el slug (strip + lowercase)."""
        if isinstance(v, str):
            stripped = v.strip().lower()
            if not stripped:
                raise ValueError("El slug de la página wiki no puede estar vacío")
            return stripped
        return v

    def update_content(self, content: str) -> None:
        """
        Actualiza el contenido de la página.

        Args:
            content: Nuevo contenido en markdown
        """
        self.content = content
        self.modified_date = datetime.now()

    def delete(self) -> None:
        """Marca la página como eliminada (soft delete)."""
        self.is_deleted = True

    def restore(self) -> None:
        """Restaura una página eliminada."""
        self.is_deleted = False
