"""Responses estructurados para operaciones de proyectos en Taiga.

Este módulo define las clases de respuesta Pydantic para todas las
operaciones relacionadas con proyectos en la API de Taiga.
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from src.application.responses.base import BaseResponse


class ProjectOwnerResponse(BaseResponse):
    """Información del propietario del proyecto.

    Attributes:
        id: ID del usuario propietario.
        username: Nombre de usuario del propietario.
        full_name: Nombre completo del propietario.
        photo: URL de la foto del usuario.
    """

    id: int
    username: str | None = None
    full_name: str | None = Field(default=None, alias="full_name_display")
    photo: str | None = None


class ProjectResponse(BaseResponse):
    """Response para un proyecto individual de Taiga.

    Contiene toda la información de un proyecto incluyendo
    configuración de módulos y metadatos.

    Attributes:
        id: ID único del proyecto.
        name: Nombre del proyecto.
        slug: Slug URL-friendly del proyecto.
        description: Descripción del proyecto.
        created_date: Fecha de creación.
        modified_date: Fecha de última modificación.
        owner: Información del propietario.
        is_private: Si el proyecto es privado.
        is_backlog_activated: Si el backlog está activo.
        is_kanban_activated: Si el kanban está activo.
        is_wiki_activated: Si la wiki está activa.
        is_issues_activated: Si los issues están activos.
        is_epics_activated: Si los epics están activos.
        total_milestones: Total de milestones.
        total_story_points: Total de story points.
        tags: Lista de tags del proyecto.
        tags_colors: Colores asignados a los tags.
        version: Versión para control de concurrencia.
        milestones: Lista de milestones del proyecto.
    """

    id: int
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    created_date: datetime | str | None = None
    modified_date: datetime | str | None = None
    owner: ProjectOwnerResponse | dict[str, Any] | None = None
    is_private: bool | None = None
    is_backlog_activated: bool | None = None
    is_kanban_activated: bool | None = None
    is_wiki_activated: bool | None = None
    is_issues_activated: bool | None = None
    is_epics_activated: bool | None = None
    total_milestones: int | None = None
    total_story_points: float | None = None
    tags: list[str] | None = None
    tags_colors: dict[str, str | None] | None = None
    videoconferences: str | None = None
    videoconferences_extra_data: str | None = None
    members: list[Any] | None = None
    total_fans: int | None = None
    total_watchers: int | None = None
    is_fan: bool | None = None
    is_watcher: bool | None = None
    i_am_owner: bool | None = None
    i_am_admin: bool | None = None
    i_am_member: bool | None = None
    version: int | None = None
    milestones: list[dict[str, Any]] | None = None


class ProjectListResponse(BaseResponse):
    """Response para una lista de proyectos.

    Attributes:
        projects: Lista de proyectos.
        count: Número total de proyectos.
    """

    projects: list[ProjectResponse]
    count: int

    @classmethod
    def from_api_response(cls, projects_data: list[dict[str, Any]]) -> "ProjectListResponse":
        """Crea una respuesta de lista desde datos de la API.

        Args:
            projects_data: Lista de diccionarios con datos de proyectos.

        Returns:
            ProjectListResponse con los proyectos validados.
        """
        projects = [ProjectResponse.model_validate(proj) for proj in projects_data]
        return cls(projects=projects, count=len(projects))


class ProjectStatsResponse(BaseResponse):
    """Response para estadísticas de un proyecto.

    Contiene métricas y estadísticas detalladas del proyecto.

    Attributes:
        name: Nombre del proyecto.
        total_milestones: Total de milestones.
        total_points: Total de puntos.
        closed_points: Puntos cerrados.
        defined_points: Puntos definidos (puede ser float o dict por rol).
        assigned_points: Puntos asignados (puede ser float o dict por rol).
        total_userstories: Total de historias de usuario.
        total_issues: Total de issues.
        closed_issues: Issues cerrados.
        speed: Velocidad del equipo.
        total_activity_last_month: Actividad del último mes.
        total_activity_last_week: Actividad de la última semana.
        total_activity_last_year: Actividad del último año.
    """

    name: str | None = None
    total_milestones: int | None = None
    total_points: float | None = None
    closed_points: float | None = None
    defined_points: float | dict[str, Any] | None = None
    assigned_points: float | dict[str, Any] | None = None
    total_userstories: int | None = None
    total_issues: int | None = None
    closed_issues: int | None = None
    speed: float | None = None
    total_activity_last_month: int | None = None
    total_activity_last_week: int | None = None
    total_activity_last_year: int | None = None


class ProjectTagResponse(BaseResponse):
    """Response para un tag de proyecto.

    Attributes:
        tag: Nombre del tag.
        color: Color del tag en formato hexadecimal.
    """

    tag: str
    color: str | None = None


class ProjectMemberResponse(BaseResponse):
    """Response para un miembro del proyecto.

    Attributes:
        id: ID del membership.
        user: ID del usuario.
        project: ID del proyecto.
        role: ID del rol.
        role_name: Nombre del rol.
        full_name: Nombre completo del usuario.
        is_admin: Si es administrador.
        is_owner: Si es propietario.
        email: Email del usuario.
    """

    id: int
    user: int | None = None
    project: int | None = None
    role: int | None = None
    role_name: str | None = None
    full_name: str | None = None
    is_admin: bool | None = None
    is_owner: bool | None = None
    email: str | None = None


class ProjectModulesResponse(BaseResponse):
    """Response para configuración de módulos del proyecto.

    Attributes:
        github: Configuración del módulo GitHub.
        gitlab: Configuración del módulo GitLab.
        bitbucket: Configuración del módulo Bitbucket.
        gogs: Configuración del módulo Gogs.
    """

    github: dict[str, Any] | None = None
    gitlab: dict[str, Any] | None = None
    bitbucket: dict[str, Any] | None = None
    gogs: dict[str, Any] | None = None


class ProjectIssuesStatsResponse(BaseResponse):
    """Response para estadísticas de issues del proyecto.

    Attributes:
        total_issues: Total de issues.
        opened_issues: Issues abiertos.
        closed_issues: Issues cerrados.
        issues_per_type: Issues por tipo.
        issues_per_status: Issues por estado.
        issues_per_priority: Issues por prioridad.
        issues_per_severity: Issues por severidad.
        issues_per_assigned_to: Issues por asignado.
        last_four_weeks_days: Días de las últimas 4 semanas.
        created_vs_closed: Creados vs cerrados.
    """

    total_issues: int | None = None
    opened_issues: int | None = None
    closed_issues: int | None = None
    issues_per_type: dict[str, Any] | None = None
    issues_per_status: dict[str, Any] | None = None
    issues_per_priority: dict[str, Any] | None = None
    issues_per_severity: dict[str, Any] | None = None
    issues_per_assigned_to: dict[str, Any] | None = None
    last_four_weeks_days: dict[str, Any] | None = None
    created_vs_closed: list[dict[str, Any]] | None = None
