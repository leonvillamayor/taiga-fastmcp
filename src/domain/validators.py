"""
Validadores de dominio para operaciones de Taiga.

Este módulo implementa validación temprana de parámetros ANTES de llamar
a la API, evitando desperdiciar recursos en llamadas que fallarán.

Los validadores usan Pydantic para validación declarativa con mensajes
de error descriptivos en español.
"""

import re
from datetime import date
from typing import Any

from pydantic import BaseModel, field_validator, model_validator

from src.domain.exceptions import ValidationError


# =============================================================================
# Funciones auxiliares de validación
# =============================================================================


def validate_positive_id(value: int | None, field_name: str) -> int | None:
    """
    Valida que un ID sea positivo si está presente.

    Args:
        value: El valor del ID a validar
        field_name: Nombre del campo para el mensaje de error

    Returns:
        El valor validado o None

    Raises:
        ValueError: Si el ID es negativo o cero
    """
    if value is not None and value <= 0:
        raise ValueError(f"El {field_name} debe ser un número positivo mayor que cero")
    return value


def validate_non_empty_string(value: str | None, field_name: str) -> str | None:
    """
    Valida que una cadena no esté vacía si está presente.

    Args:
        value: El valor de la cadena a validar
        field_name: Nombre del campo para el mensaje de error

    Returns:
        El valor limpio (sin espacios extra) o None

    Raises:
        ValueError: Si la cadena está vacía o solo contiene espacios
    """
    if value is not None:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"El {field_name} no puede estar vacío")
        return cleaned
    return value


def validate_hex_color(value: str | None, field_name: str = "color") -> str | None:
    """
    Valida que un color esté en formato hexadecimal #RRGGBB.

    Args:
        value: El valor del color a validar
        field_name: Nombre del campo para el mensaje de error

    Returns:
        El valor del color validado o None

    Raises:
        ValueError: Si el formato del color es inválido
    """
    if value is not None and not re.match(r"^#[0-9A-Fa-f]{6}$", value):
        raise ValueError(f"El {field_name} debe estar en formato hexadecimal #RRGGBB (ej: #FF5733)")
    return value


def validate_date_format(value: str | None, field_name: str) -> str | None:
    """
    Valida que una fecha esté en formato YYYY-MM-DD.

    Args:
        value: El valor de la fecha a validar
        field_name: Nombre del campo para el mensaje de error

    Returns:
        El valor de la fecha validado o None

    Raises:
        ValueError: Si el formato de fecha es inválido
    """
    if value is not None:
        try:
            # Intenta parsear la fecha
            parts = value.split("-")
            if len(parts) != 3:
                raise ValueError("Formato incorrecto")
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            date(year, month, day)  # Valida que sea una fecha real
        except (ValueError, IndexError):
            raise ValueError(
                f"El {field_name} debe estar en formato YYYY-MM-DD (ej: 2024-01-15)"
            ) from None
    return value


def validate_url(value: str | None, field_name: str = "url") -> str | None:
    """
    Valida que una URL tenga formato válido.

    Args:
        value: El valor de la URL a validar
        field_name: Nombre del campo para el mensaje de error

    Returns:
        El valor de la URL validado o None

    Raises:
        ValueError: Si el formato de URL es inválido
    """
    if value is not None and not re.match(r"^https?://", value):
        raise ValueError(f"La {field_name} debe comenzar con http:// o https://")
    return value


# =============================================================================
# Validadores de Proyecto
# =============================================================================


class ProjectCreateValidator(BaseModel):
    """Validador para creación de proyectos."""

    name: str
    description: str | None = None
    is_private: bool | None = None
    is_backlog_activated: bool | None = None
    is_issues_activated: bool | None = None
    is_kanban_activated: bool | None = None
    is_wiki_activated: bool | None = None
    tags: list[str] | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Valida que el nombre no esté vacío."""
        if not v or not v.strip():
            raise ValueError("El nombre del proyecto no puede estar vacío")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_strip(cls, v: str | None) -> str | None:
        """Limpia espacios de la descripción."""
        if v is not None:
            return v.strip()
        return v

    @field_validator("tags")
    @classmethod
    def tags_not_empty(cls, v: list[str] | None) -> list[str] | None:
        """Valida que los tags no estén vacíos."""
        if v is not None:
            cleaned = [tag.strip() for tag in v if tag.strip()]
            if len(cleaned) != len(v):
                raise ValueError("Los tags no pueden estar vacíos")
            return cleaned
        return v


class ProjectUpdateValidator(BaseModel):
    """Validador para actualización de proyectos."""

    project_id: int
    name: str | None = None
    description: str | None = None
    is_private: bool | None = None
    is_backlog_activated: bool | None = None
    is_issues_activated: bool | None = None
    is_kanban_activated: bool | None = None
    is_wiki_activated: bool | None = None
    version: int | None = None

    @field_validator("project_id")
    @classmethod
    def project_id_positive(cls, v: int) -> int:
        """Valida que el ID del proyecto sea positivo."""
        if v <= 0:
            raise ValueError("El ID del proyecto debe ser un número positivo mayor que cero")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        """Valida que el nombre no esté vacío si se proporciona."""
        return validate_non_empty_string(v, "nombre del proyecto")

    @field_validator("version")
    @classmethod
    def version_positive(cls, v: int | None) -> int | None:
        """Valida que la versión sea positiva si se proporciona."""
        return validate_positive_id(v, "versión")


class ProjectDuplicateValidator(BaseModel):
    """Validador para duplicación de proyectos."""

    project_id: int
    name: str
    description: str | None = None
    is_private: bool | None = None
    users: list[str] | None = None

    @field_validator("project_id")
    @classmethod
    def project_id_positive(cls, v: int) -> int:
        """Valida que el ID del proyecto sea positivo."""
        if v <= 0:
            raise ValueError("El ID del proyecto debe ser un número positivo mayor que cero")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Valida que el nombre no esté vacío."""
        if not v or not v.strip():
            raise ValueError("El nombre del proyecto no puede estar vacío")
        return v.strip()


class ProjectTagValidator(BaseModel):
    """Validador para operaciones con tags de proyecto."""

    project_id: int
    tag: str
    color: str | None = None

    @field_validator("project_id")
    @classmethod
    def project_id_positive(cls, v: int) -> int:
        """Valida que el ID del proyecto sea positivo."""
        if v <= 0:
            raise ValueError("El ID del proyecto debe ser un número positivo mayor que cero")
        return v

    @field_validator("tag")
    @classmethod
    def tag_not_empty(cls, v: str) -> str:
        """Valida que el tag no esté vacío."""
        if not v or not v.strip():
            raise ValueError("El tag no puede estar vacío")
        return v.strip()

    @field_validator("color")
    @classmethod
    def color_format(cls, v: str | None) -> str | None:
        """Valida el formato del color."""
        return validate_hex_color(v)


class ProjectTagEditValidator(BaseModel):
    """Validador para edición de tags de proyecto."""

    from_tag: str
    to_tag: str
    color: str | None = None

    @field_validator("from_tag")
    @classmethod
    def from_tag_not_empty(cls, v: str) -> str:
        """Valida que el tag original no esté vacío."""
        if not v or not v.strip():
            raise ValueError("El tag original no puede estar vacío")
        return v.strip()

    @field_validator("to_tag")
    @classmethod
    def to_tag_not_empty(cls, v: str) -> str:
        """Valida que el nuevo tag no esté vacío."""
        if not v or not v.strip():
            raise ValueError("El nuevo tag no puede estar vacío")
        return v.strip()

    @field_validator("color")
    @classmethod
    def color_format(cls, v: str | None) -> str | None:
        """Valida el formato del color."""
        return validate_hex_color(v)


# =============================================================================
# Validadores de Epic
# =============================================================================


class EpicCreateValidator(BaseModel):
    """Validador para creación de épicas."""

    project_id: int
    subject: str
    description: str | None = None
    color: str | None = None
    assigned_to: int | None = None
    status: int | None = None
    tags: list[str] | None = None

    @field_validator("project_id")
    @classmethod
    def project_id_positive(cls, v: int) -> int:
        """Valida que el ID del proyecto sea positivo."""
        if v <= 0:
            raise ValueError("El ID del proyecto debe ser un número positivo mayor que cero")
        return v

    @field_validator("subject")
    @classmethod
    def subject_not_empty(cls, v: str) -> str:
        """Valida que el asunto no esté vacío."""
        if not v or not v.strip():
            raise ValueError("El asunto de la épica no puede estar vacío")
        return v.strip()

    @field_validator("color")
    @classmethod
    def color_format(cls, v: str | None) -> str | None:
        """Valida el formato del color."""
        return validate_hex_color(v)

    @field_validator("assigned_to", "status")
    @classmethod
    def id_positive(cls, v: int | None, info: Any) -> int | None:
        """Valida que los IDs sean positivos."""
        return validate_positive_id(v, info.field_name)


class EpicUpdateValidator(BaseModel):
    """Validador para actualización de épicas."""

    epic_id: int
    subject: str | None = None
    description: str | None = None
    color: str | None = None
    assigned_to: int | None = None
    status: int | None = None
    tags: list[str] | None = None

    @field_validator("epic_id")
    @classmethod
    def epic_id_positive(cls, v: int) -> int:
        """Valida que el ID de la épica sea positivo."""
        if v <= 0:
            raise ValueError("El ID de la épica debe ser un número positivo mayor que cero")
        return v

    @field_validator("subject")
    @classmethod
    def subject_not_empty(cls, v: str | None) -> str | None:
        """Valida que el asunto no esté vacío si se proporciona."""
        return validate_non_empty_string(v, "asunto de la épica")

    @field_validator("color")
    @classmethod
    def color_format(cls, v: str | None) -> str | None:
        """Valida el formato del color."""
        return validate_hex_color(v)


# =============================================================================
# Validadores de User Story
# =============================================================================


class UserStoryCreateValidator(BaseModel):
    """Validador para creación de historias de usuario."""

    project_id: int
    subject: str
    description: str | None = None
    status: int | None = None
    assigned_to: int | None = None
    milestone: int | None = None
    tags: list[str] | None = None
    is_blocked: bool | None = None
    blocked_note: str | None = None
    client_requirement: bool | None = None
    team_requirement: bool | None = None

    @field_validator("project_id")
    @classmethod
    def project_id_positive(cls, v: int) -> int:
        """Valida que el ID del proyecto sea positivo."""
        if v <= 0:
            raise ValueError("El ID del proyecto debe ser un número positivo mayor que cero")
        return v

    @field_validator("subject")
    @classmethod
    def subject_not_empty(cls, v: str) -> str:
        """Valida que el asunto no esté vacío."""
        if not v or not v.strip():
            raise ValueError("El asunto de la historia de usuario no puede estar vacío")
        return v.strip()

    @field_validator("status", "assigned_to", "milestone")
    @classmethod
    def id_positive(cls, v: int | None, info: Any) -> int | None:
        """Valida que los IDs sean positivos."""
        return validate_positive_id(v, info.field_name)


class UserStoryUpdateValidator(BaseModel):
    """Validador para actualización de historias de usuario."""

    userstory_id: int
    subject: str | None = None
    description: str | None = None
    status: int | None = None
    assigned_to: int | None = None
    milestone: int | None = None
    tags: list[str] | None = None
    is_blocked: bool | None = None
    blocked_note: str | None = None
    version: int | None = None

    @field_validator("userstory_id")
    @classmethod
    def userstory_id_positive(cls, v: int) -> int:
        """Valida que el ID de la historia sea positivo."""
        if v <= 0:
            raise ValueError(
                "El ID de la historia de usuario debe ser un número positivo mayor que cero"
            )
        return v

    @field_validator("subject")
    @classmethod
    def subject_not_empty(cls, v: str | None) -> str | None:
        """Valida que el asunto no esté vacío si se proporciona."""
        return validate_non_empty_string(v, "asunto de la historia de usuario")


# =============================================================================
# Validadores de Issue
# =============================================================================


class IssueCreateValidator(BaseModel):
    """Validador para creación de issues."""

    project_id: int
    subject: str
    type: int
    priority: int
    severity: int
    description: str | None = None
    status: int | None = None
    assigned_to: int | None = None
    milestone_id: int | None = None
    tags: list[str] | None = None
    is_blocked: bool | None = None
    blocked_note: str | None = None
    due_date: str | None = None

    @field_validator("project_id", "type", "priority", "severity")
    @classmethod
    def required_id_positive(cls, v: int, info: Any) -> int:
        """Valida que los IDs requeridos sean positivos."""
        if v <= 0:
            field_names = {
                "project_id": "ID del proyecto",
                "type": "tipo",
                "priority": "prioridad",
                "severity": "severidad",
            }
            field_name = field_names.get(info.field_name, info.field_name)
            raise ValueError(f"El {field_name} debe ser un número positivo mayor que cero")
        return v

    @field_validator("subject")
    @classmethod
    def subject_not_empty(cls, v: str) -> str:
        """Valida que el asunto no esté vacío."""
        if not v or not v.strip():
            raise ValueError("El asunto del issue no puede estar vacío")
        return v.strip()

    @field_validator("status", "assigned_to", "milestone_id")
    @classmethod
    def optional_id_positive(cls, v: int | None, info: Any) -> int | None:
        """Valida que los IDs opcionales sean positivos."""
        return validate_positive_id(v, info.field_name)

    @field_validator("due_date")
    @classmethod
    def due_date_format(cls, v: str | None) -> str | None:
        """Valida el formato de la fecha."""
        return validate_date_format(v, "fecha límite")


class IssueUpdateValidator(BaseModel):
    """Validador para actualización de issues."""

    issue_id: int
    subject: str | None = None
    description: str | None = None
    type: int | None = None
    priority: int | None = None
    severity: int | None = None
    status: int | None = None
    assigned_to: int | None = None
    milestone_id: int | None = None
    tags: list[str] | None = None
    is_blocked: bool | None = None
    blocked_note: str | None = None
    due_date: str | None = None
    version: int | None = None

    @field_validator("issue_id")
    @classmethod
    def issue_id_positive(cls, v: int) -> int:
        """Valida que el ID del issue sea positivo."""
        if v <= 0:
            raise ValueError("El ID del issue debe ser un número positivo mayor que cero")
        return v

    @field_validator("subject")
    @classmethod
    def subject_not_empty(cls, v: str | None) -> str | None:
        """Valida que el asunto no esté vacío si se proporciona."""
        return validate_non_empty_string(v, "asunto del issue")

    @field_validator("due_date")
    @classmethod
    def due_date_format(cls, v: str | None) -> str | None:
        """Valida el formato de la fecha."""
        return validate_date_format(v, "fecha límite")


# =============================================================================
# Validadores de Task
# =============================================================================


class TaskCreateValidator(BaseModel):
    """Validador para creación de tareas."""

    project_id: int
    subject: str
    description: str | None = None
    user_story_id: int | None = None
    milestone_id: int | None = None
    status: int | None = None
    assigned_to: int | None = None
    tags: list[str] | None = None
    is_blocked: bool | None = None
    blocked_note: str | None = None

    @field_validator("project_id")
    @classmethod
    def project_id_positive(cls, v: int) -> int:
        """Valida que el ID del proyecto sea positivo."""
        if v <= 0:
            raise ValueError("El ID del proyecto debe ser un número positivo mayor que cero")
        return v

    @field_validator("subject")
    @classmethod
    def subject_not_empty(cls, v: str) -> str:
        """Valida que el asunto no esté vacío."""
        if not v or not v.strip():
            raise ValueError("El asunto de la tarea no puede estar vacío")
        return v.strip()

    @field_validator("user_story_id", "milestone_id", "status", "assigned_to")
    @classmethod
    def id_positive(cls, v: int | None, info: Any) -> int | None:
        """Valida que los IDs sean positivos."""
        return validate_positive_id(v, info.field_name)


class TaskUpdateValidator(BaseModel):
    """Validador para actualización de tareas."""

    task_id: int
    subject: str | None = None
    description: str | None = None
    user_story_id: int | None = None
    milestone_id: int | None = None
    status: int | None = None
    assigned_to: int | None = None
    tags: list[str] | None = None
    is_blocked: bool | None = None
    blocked_note: str | None = None

    @field_validator("task_id")
    @classmethod
    def task_id_positive(cls, v: int) -> int:
        """Valida que el ID de la tarea sea positivo."""
        if v <= 0:
            raise ValueError("El ID de la tarea debe ser un número positivo mayor que cero")
        return v

    @field_validator("subject")
    @classmethod
    def subject_not_empty(cls, v: str | None) -> str | None:
        """Valida que el asunto no esté vacío si se proporciona."""
        return validate_non_empty_string(v, "asunto de la tarea")


# =============================================================================
# Validadores de Milestone
# =============================================================================


class MilestoneCreateValidator(BaseModel):
    """Validador para creación de milestones/sprints."""

    project_id: int
    name: str
    estimated_start: str
    estimated_finish: str
    disponibility: float | None = None
    watchers: list[int] | None = None

    @field_validator("project_id")
    @classmethod
    def project_id_positive(cls, v: int) -> int:
        """Valida que el ID del proyecto sea positivo."""
        if v <= 0:
            raise ValueError("El ID del proyecto debe ser un número positivo mayor que cero")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Valida que el nombre no esté vacío."""
        if not v or not v.strip():
            raise ValueError("El nombre del milestone no puede estar vacío")
        return v.strip()

    @field_validator("estimated_start")
    @classmethod
    def start_date_format(cls, v: str) -> str:
        """Valida el formato de la fecha de inicio."""
        result = validate_date_format(v, "fecha de inicio")
        if result is None:
            raise ValueError("La fecha de inicio es requerida")
        return result

    @field_validator("estimated_finish")
    @classmethod
    def finish_date_format(cls, v: str) -> str:
        """Valida el formato de la fecha de fin."""
        result = validate_date_format(v, "fecha de fin")
        if result is None:
            raise ValueError("La fecha de fin es requerida")
        return result

    @field_validator("disponibility")
    @classmethod
    def disponibility_non_negative(cls, v: float | None) -> float | None:
        """Valida que la disponibilidad no sea negativa."""
        if v is not None and v < 0:
            raise ValueError("La disponibilidad no puede ser negativa")
        return v

    @model_validator(mode="after")
    def check_dates_order(self) -> "MilestoneCreateValidator":
        """Valida que la fecha de fin sea posterior a la de inicio."""
        # Parse dates - si falla el parsing, simplemente retornar (ya validado por field_validators)
        try:
            start = date.fromisoformat(self.estimated_start)
            end = date.fromisoformat(self.estimated_finish)
        except (ValueError, TypeError):
            return self

        # Validación de orden - esto SÍ debe lanzar error
        if end < start:
            raise ValueError("La fecha de inicio debe ser anterior o igual a la fecha de fin")
        return self


class MilestoneUpdateValidator(BaseModel):
    """Validador para actualización de milestones/sprints."""

    milestone_id: int
    name: str | None = None
    estimated_start: str | None = None
    estimated_finish: str | None = None
    disponibility: float | None = None
    closed: bool | None = None

    @field_validator("milestone_id")
    @classmethod
    def milestone_id_positive(cls, v: int) -> int:
        """Valida que el ID del milestone sea positivo."""
        if v <= 0:
            raise ValueError("El ID del milestone debe ser un número positivo mayor que cero")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        """Valida que el nombre no esté vacío si se proporciona."""
        return validate_non_empty_string(v, "nombre del milestone")

    @field_validator("estimated_start")
    @classmethod
    def start_date_format(cls, v: str | None) -> str | None:
        """Valida el formato de la fecha de inicio."""
        return validate_date_format(v, "fecha de inicio")

    @field_validator("estimated_finish")
    @classmethod
    def finish_date_format(cls, v: str | None) -> str | None:
        """Valida el formato de la fecha de fin."""
        return validate_date_format(v, "fecha de fin")


# =============================================================================
# Validadores de Wiki
# =============================================================================


class WikiPageCreateValidator(BaseModel):
    """Validador para creación de páginas wiki."""

    project_id: int
    slug: str
    content: str
    watchers: list[int] | None = None

    @field_validator("project_id")
    @classmethod
    def project_id_positive(cls, v: int) -> int:
        """Valida que el ID del proyecto sea positivo."""
        if v <= 0:
            raise ValueError("El ID del proyecto debe ser un número positivo mayor que cero")
        return v

    @field_validator("slug")
    @classmethod
    def slug_valid(cls, v: str) -> str:
        """Valida que el slug sea válido."""
        if not v or not v.strip():
            raise ValueError("El slug de la página wiki no puede estar vacío")
        # Validar formato de slug (solo letras, números, guiones)
        cleaned = v.strip().lower()
        if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$", cleaned):
            raise ValueError(
                "El slug debe contener solo letras minúsculas, números y guiones, "
                "y no puede empezar ni terminar con guión"
            )
        return cleaned

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Valida que el contenido no esté vacío."""
        if not v or not v.strip():
            raise ValueError("El contenido de la página wiki no puede estar vacío")
        return v


class WikiPageUpdateValidator(BaseModel):
    """Validador para actualización de páginas wiki."""

    wiki_id: int
    slug: str | None = None
    content: str | None = None
    version: int | None = None

    @field_validator("wiki_id")
    @classmethod
    def wiki_id_positive(cls, v: int) -> int:
        """Valida que el ID de la página wiki sea positivo."""
        if v <= 0:
            raise ValueError("El ID de la página wiki debe ser un número positivo mayor que cero")
        return v

    @field_validator("slug")
    @classmethod
    def slug_valid(cls, v: str | None) -> str | None:
        """Valida que el slug sea válido si se proporciona."""
        if v is not None:
            cleaned = v.strip().lower()
            if not cleaned:
                raise ValueError("El slug de la página wiki no puede estar vacío")
            if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$", cleaned):
                raise ValueError("El slug debe contener solo letras minúsculas, números y guiones")
            return cleaned
        return v


# =============================================================================
# Validadores de Webhook
# =============================================================================


class WebhookCreateValidator(BaseModel):
    """Validador para creación de webhooks."""

    project_id: int
    name: str
    url: str
    key: str
    enabled: bool | None = None

    @field_validator("project_id")
    @classmethod
    def project_id_positive(cls, v: int) -> int:
        """Valida que el ID del proyecto sea positivo."""
        if v <= 0:
            raise ValueError("El ID del proyecto debe ser un número positivo mayor que cero")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Valida que el nombre no esté vacío."""
        if not v or not v.strip():
            raise ValueError("El nombre del webhook no puede estar vacío")
        return v.strip()

    @field_validator("url")
    @classmethod
    def url_valid(cls, v: str) -> str:
        """Valida que la URL sea válida."""
        if not v or not v.strip():
            raise ValueError("La URL del webhook no puede estar vacía")
        result = validate_url(v.strip())
        if result is None:
            raise ValueError("La URL del webhook es requerida")
        return result

    @field_validator("key")
    @classmethod
    def key_not_empty(cls, v: str) -> str:
        """Valida que la clave no esté vacía."""
        if not v or not v.strip():
            raise ValueError("El campo key del webhook no puede estar vacío")
        return v.strip()


class WebhookUpdateValidator(BaseModel):
    """Validador para actualización de webhooks."""

    webhook_id: int
    name: str | None = None
    url: str | None = None
    key: str | None = None
    enabled: bool | None = None

    @field_validator("webhook_id")
    @classmethod
    def webhook_id_positive(cls, v: int) -> int:
        """Valida que el ID del webhook sea positivo."""
        if v <= 0:
            raise ValueError("El ID del webhook debe ser un número positivo mayor que cero")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        """Valida que el nombre no esté vacío si se proporciona."""
        return validate_non_empty_string(v, "nombre del webhook")

    @field_validator("url")
    @classmethod
    def url_valid(cls, v: str | None) -> str | None:
        """Valida que la URL sea válida si se proporciona."""
        if v is not None:
            return validate_url(v.strip())
        return v


# =============================================================================
# Validadores de Membership
# =============================================================================


class MembershipCreateValidator(BaseModel):
    """Validador para creación de membresías."""

    project_id: int
    role: int
    username: str | None = None
    email: str | None = None

    @field_validator("project_id", "role")
    @classmethod
    def id_positive(cls, v: int, info: Any) -> int:
        """Valida que los IDs sean positivos."""
        field_names = {"project_id": "ID del proyecto", "role": "ID del rol"}
        field_name = field_names.get(info.field_name, info.field_name)
        if v <= 0:
            raise ValueError(f"El {field_name} debe ser un número positivo mayor que cero")
        return v

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str | None) -> str | None:
        """Valida que el username no esté vacío si se proporciona."""
        return validate_non_empty_string(v, "nombre de usuario")

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str | None) -> str | None:
        """Valida el formato del email si se proporciona."""
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("El email no puede estar vacío")
            # Validación básica de email
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", cleaned):
                raise ValueError("El formato del email no es válido")
            return cleaned
        return v

    @model_validator(mode="after")
    def check_username_or_email(self) -> "MembershipCreateValidator":
        """Valida que se proporcione username o email."""
        if not self.username and not self.email:
            raise ValueError("Debe proporcionar un nombre de usuario o un email")
        return self


class MembershipUpdateValidator(BaseModel):
    """Validador para actualización de membresías."""

    membership_id: int
    role: int | None = None
    is_admin: bool | None = None

    @field_validator("membership_id")
    @classmethod
    def membership_id_positive(cls, v: int) -> int:
        """Valida que el ID de la membresía sea positivo."""
        if v <= 0:
            raise ValueError("El ID de la membresía debe ser un número positivo mayor que cero")
        return v

    @field_validator("role")
    @classmethod
    def role_positive(cls, v: int | None) -> int | None:
        """Valida que el ID del rol sea positivo si se proporciona."""
        return validate_positive_id(v, "ID del rol")


# =============================================================================
# Función auxiliar para validar y convertir a excepción de dominio
# =============================================================================


def validate_input(validator_class: type[BaseModel], data: dict[str, Any]) -> dict[str, Any]:
    """
    Valida datos de entrada usando un validador Pydantic.

    Args:
        validator_class: Clase del validador Pydantic a usar
        data: Diccionario con los datos a validar

    Returns:
        Diccionario con los datos validados y normalizados

    Raises:
        ValidationError: Si la validación falla, con mensaje descriptivo en español
    """
    try:
        validated = validator_class(**data)
        return validated.model_dump(exclude_none=True)
    except Exception as e:
        # Extraer mensajes de error de Pydantic
        if hasattr(e, "errors"):
            errors = e.errors()
            messages = []
            for error in errors:
                field = ".".join(str(loc) for loc in error.get("loc", []))
                msg = error.get("msg", "Error de validación")
                if field:
                    messages.append(f"{field}: {msg}")
                else:
                    messages.append(msg)
            raise ValidationError("; ".join(messages)) from e
        raise ValidationError(str(e)) from e
