"""Entidad de task."""

from datetime import datetime

from pydantic import Field, field_validator

from src.domain.entities.base import BaseEntity


class Task(BaseEntity):
    """
    Entidad de Task en Taiga.

    Representa una tarea asociada a una user story o independiente.

    Attributes:
        subject: Título de la tarea
        description: Descripción detallada
        project_id: ID del proyecto al que pertenece
        user_story_id: ID de la user story asociada (opcional)
        status: ID del estado actual
        milestone_id: ID del sprint/milestone asignado
        assigned_to_id: ID del usuario asignado
        ref: Número de referencia en el proyecto
        is_closed: Indica si está cerrada
        is_blocked: Indica si está bloqueada
        blocked_note: Razón del bloqueo
        is_iocaine: Indica si es una tarea difícil/riesgosa
        tags: Lista de tags
        created_date: Fecha de creación
        modified_date: Última modificación
        finished_date: Fecha de finalización
    """

    subject: str = Field(..., min_length=1, max_length=500, description="Título de la tarea")
    description: str = Field("", description="Descripción detallada")
    project_id: int = Field(..., gt=0, description="ID del proyecto")
    user_story_id: int | None = Field(None, description="ID de la user story asociada")
    status: int | None = Field(None, description="ID del estado")
    milestone_id: int | None = Field(None, description="ID del sprint/milestone")
    assigned_to_id: int | None = Field(None, description="ID del usuario asignado")
    ref: int | None = Field(None, description="Número de referencia")
    is_closed: bool = Field(False, description="¿Está cerrada?")
    is_blocked: bool = Field(False, description="¿Está bloqueada?")
    blocked_note: str = Field("", description="Razón del bloqueo")
    is_iocaine: bool = Field(False, description="¿Es tarea difícil/riesgosa?")
    tags: list[str] = Field(default_factory=list, description="Tags")
    created_date: datetime | None = Field(None, description="Fecha de creación")
    modified_date: datetime | None = Field(None, description="Última modificación")
    finished_date: datetime | None = Field(None, description="Fecha de finalización")

    @field_validator("subject", mode="before")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Valida que el título no esté vacío."""
        if isinstance(v, str) and not v.strip():
            raise ValueError("El título de la tarea no puede estar vacío")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Normaliza tags."""
        return list({tag.lower().strip() for tag in v if tag.strip()})

    def block(self, reason: str) -> None:
        """
        Bloquea la tarea.

        Args:
            reason: Razón del bloqueo
        """
        self.is_blocked = True
        self.blocked_note = reason

    def unblock(self) -> None:
        """Desbloquea la tarea."""
        self.is_blocked = False
        self.blocked_note = ""

    def mark_as_iocaine(self) -> None:
        """Marca la tarea como difícil/riesgosa."""
        self.is_iocaine = True

    def unmark_as_iocaine(self) -> None:
        """Desmarca la tarea como difícil/riesgosa."""
        self.is_iocaine = False

    def finish(self) -> None:
        """Marca la tarea como finalizada."""
        self.is_closed = True
        self.finished_date = datetime.now()

    def reopen(self) -> None:
        """Reabre una tarea cerrada."""
        self.is_closed = False
        self.finished_date = None
