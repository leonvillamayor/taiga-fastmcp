"""Entidad de user story."""

from datetime import datetime

from pydantic import Field, field_validator

from src.domain.entities.base import BaseEntity


class UserStory(BaseEntity):
    """
    Entidad de User Story en Taiga.

    Representa una historia de usuario en el backlog o sprint del proyecto.

    Attributes:
        subject: Título de la user story
        description: Descripción detallada
        project_id: ID del proyecto al que pertenece
        status: ID del estado actual
        milestone_id: ID del sprint/milestone asignado
        assigned_to_id: ID del usuario asignado
        ref: Número de referencia en el proyecto
        is_closed: Indica si está cerrada
        is_blocked: Indica si está bloqueada
        blocked_note: Razón del bloqueo
        client_requirement: Es un requerimiento del cliente
        team_requirement: Es un requerimiento del equipo
        tags: Lista de tags
        created_date: Fecha de creación
        modified_date: Última modificación
        points: Diccionario de story points por rol
    """

    subject: str = Field(..., min_length=1, max_length=500, description="Título de la user story")
    description: str = Field("", description="Descripción detallada")
    project_id: int = Field(..., gt=0, description="ID del proyecto")
    status: int | None = Field(None, description="ID del estado")
    milestone_id: int | None = Field(None, description="ID del sprint/milestone")
    assigned_to_id: int | None = Field(None, description="ID del usuario asignado")
    ref: int | None = Field(None, description="Número de referencia")
    is_closed: bool = Field(False, description="¿Está cerrada?")
    is_blocked: bool = Field(False, description="¿Está bloqueada?")
    blocked_note: str = Field("", description="Razón del bloqueo")
    client_requirement: bool = Field(False, description="¿Es requerimiento del cliente?")
    team_requirement: bool = Field(False, description="¿Es requerimiento del equipo?")
    tags: list[str] = Field(default_factory=list, description="Tags")
    created_date: datetime | None = Field(None, description="Fecha de creación")
    modified_date: datetime | None = Field(None, description="Última modificación")
    points: dict[str, float] = Field(default_factory=dict, description="Story points por rol")

    @field_validator("subject", mode="before")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Valida que el título no esté vacío."""
        if isinstance(v, str) and not v.strip():
            raise ValueError("El título de la user story no puede estar vacío")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Normaliza tags."""
        return list({tag.lower().strip() for tag in v if tag.strip()})

    def block(self, reason: str) -> None:
        """
        Bloquea la user story.

        Args:
            reason: Razón del bloqueo
        """
        self.is_blocked = True
        self.blocked_note = reason

    def unblock(self) -> None:
        """Desbloquea la user story."""
        self.is_blocked = False
        self.blocked_note = ""

    def assign_to(self, user_id: int) -> None:
        """
        Asigna la user story a un usuario.

        Args:
            user_id: ID del usuario

        Raises:
            ValueError: Si el user_id no es válido
        """
        if user_id <= 0:
            raise ValueError("ID de usuario inválido")
        self.assigned_to_id = user_id

    def unassign(self) -> None:
        """Desasigna la user story."""
        self.assigned_to_id = None
