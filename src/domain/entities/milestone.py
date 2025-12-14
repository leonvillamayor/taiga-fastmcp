"""Entidad de milestone."""

from datetime import date, datetime

from pydantic import Field, field_validator

from src.domain.entities.base import BaseEntity


class Milestone(BaseEntity):
    """
    Entidad de Milestone (Sprint) en Taiga.

    Representa un sprint o hito temporal en el proyecto.

    Attributes:
        name: Nombre del milestone
        slug: Slug único del milestone
        project_id: ID del proyecto
        estimated_start: Fecha estimada de inicio
        estimated_finish: Fecha estimada de finalización
        is_closed: Indica si está cerrado
        disponibility: Disponibilidad del equipo (0-1)
        order: Orden de visualización
        created_date: Fecha de creación
        modified_date: Última modificación
    """

    name: str = Field(..., min_length=1, max_length=255, description="Nombre del milestone")
    slug: str | None = Field(None, max_length=255, description="Slug del milestone")
    project_id: int = Field(..., gt=0, description="ID del proyecto")
    estimated_start: date | None = Field(None, description="Fecha estimada de inicio")
    estimated_finish: date | None = Field(None, description="Fecha estimada de finalización")
    is_closed: bool = Field(False, description="¿Está cerrado?")
    disponibility: float = Field(1.0, ge=0, le=1, description="Disponibilidad del equipo")
    order: int = Field(1, ge=1, description="Orden de visualización")
    created_date: datetime | None = Field(None, description="Fecha de creación")
    modified_date: datetime | None = Field(None, description="Última modificación")

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valida que el nombre no esté vacío."""
        if isinstance(v, str) and not v.strip():
            raise ValueError("El nombre del milestone no puede estar vacío")
        return v

    def close(self) -> None:
        """Cierra el milestone."""
        self.is_closed = True

    def reopen(self) -> None:
        """Reabre el milestone."""
        self.is_closed = False

    def set_dates(self, start: date, finish: date) -> None:
        """
        Establece las fechas del milestone.

        Args:
            start: Fecha de inicio
            finish: Fecha de finalización

        Raises:
            ValueError: Si la fecha de fin es anterior a la de inicio
        """
        if finish < start:
            raise ValueError("La fecha de finalización debe ser posterior a la de inicio")
        self.estimated_start = start
        self.estimated_finish = finish
