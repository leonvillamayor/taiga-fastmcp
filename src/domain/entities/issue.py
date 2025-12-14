"""Entidad de issue."""

from datetime import datetime

from pydantic import Field, field_validator

from src.domain.entities.base import BaseEntity


class Issue(BaseEntity):
    """
    Entidad de Issue en Taiga.

    Representa un bug, incidencia o problema reportado en el proyecto.

    Attributes:
        subject: Título del issue
        description: Descripción detallada
        project_id: ID del proyecto
        status: ID del estado actual
        type: ID del tipo de issue
        severity: ID de la severidad
        priority: ID de la prioridad
        milestone_id: ID del sprint/milestone asignado
        assigned_to_id: ID del usuario asignado
        ref: Número de referencia
        is_closed: Indica si está cerrado
        is_blocked: Indica si está bloqueado
        blocked_note: Razón del bloqueo
        tags: Lista de tags
        created_date: Fecha de creación
        modified_date: Última modificación
        finished_date: Fecha de finalización
    """

    subject: str = Field(..., min_length=1, max_length=500, description="Título del issue")
    description: str = Field("", description="Descripción detallada")
    project_id: int = Field(..., gt=0, description="ID del proyecto")
    status: int | None = Field(None, description="ID del estado")
    type: int | None = Field(None, description="ID del tipo")
    severity: int | None = Field(None, description="ID de la severidad")
    priority: int | None = Field(None, description="ID de la prioridad")
    milestone_id: int | None = Field(None, description="ID del sprint/milestone")
    assigned_to_id: int | None = Field(None, description="ID del usuario asignado")
    ref: int | None = Field(None, description="Número de referencia")
    is_closed: bool = Field(False, description="¿Está cerrado?")
    is_blocked: bool = Field(False, description="¿Está bloqueado?")
    blocked_note: str = Field("", description="Razón del bloqueo")
    tags: list[str] = Field(default_factory=list, description="Tags")
    created_date: datetime | None = Field(None, description="Fecha de creación")
    modified_date: datetime | None = Field(None, description="Última modificación")
    finished_date: datetime | None = Field(None, description="Fecha de finalización")

    @field_validator("subject", mode="before")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Valida que el título no esté vacío."""
        if isinstance(v, str) and not v.strip():
            raise ValueError("El título del issue no puede estar vacío")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Normaliza tags."""
        return list({tag.lower().strip() for tag in v if tag.strip()})

    def block(self, reason: str) -> None:
        """Bloquea el issue."""
        self.is_blocked = True
        self.blocked_note = reason

    def unblock(self) -> None:
        """Desbloquea el issue."""
        self.is_blocked = False
        self.blocked_note = ""

    def close(self) -> None:
        """Cierra el issue."""
        self.is_closed = True
        self.finished_date = datetime.now()

    def reopen(self) -> None:
        """Reabre el issue."""
        self.is_closed = False
        self.finished_date = None
