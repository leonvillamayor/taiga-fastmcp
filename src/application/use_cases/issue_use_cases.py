"""Use cases para gestión de issues."""

from typing import Any

from pydantic import BaseModel, Field

from src.domain.entities.issue import Issue
from src.domain.exceptions import ResourceNotFoundError
from src.domain.repositories.issue_repository import IssueRepository


# DTOs (Data Transfer Objects)


class CreateIssueRequest(BaseModel):
    """Request para crear issue."""

    subject: str = Field(..., min_length=1, max_length=500, description="Título")
    description: str = Field("", description="Descripción detallada")
    project_id: int = Field(..., gt=0, description="ID del proyecto")
    status: int | None = Field(None, gt=0, description="ID del estado")
    type: int | None = Field(None, gt=0, description="ID del tipo")
    severity: int | None = Field(None, gt=0, description="ID de la severidad")
    priority: int | None = Field(None, gt=0, description="ID de la prioridad")
    milestone_id: int | None = Field(None, gt=0, description="ID del milestone")
    assigned_to_id: int | None = Field(None, gt=0, description="ID usuario asignado")
    is_blocked: bool = Field(False, description="¿Está bloqueado?")
    blocked_note: str = Field("", description="Razón del bloqueo")
    tags: list[str] = Field(default_factory=list, description="Tags")


class UpdateIssueRequest(BaseModel):
    """Request para actualizar issue."""

    issue_id: int = Field(..., gt=0, description="ID del issue")
    subject: str | None = Field(None, min_length=1, max_length=500, description="Título")
    description: str | None = Field(None, description="Descripción")
    status: int | None = Field(None, gt=0, description="ID del estado")
    type: int | None = Field(None, gt=0, description="ID del tipo")
    severity: int | None = Field(None, gt=0, description="ID de la severidad")
    priority: int | None = Field(None, gt=0, description="ID de la prioridad")
    milestone_id: int | None = Field(None, description="ID del milestone")
    assigned_to_id: int | None = Field(None, description="ID usuario asignado")
    is_blocked: bool | None = Field(None, description="¿Está bloqueado?")
    blocked_note: str | None = Field(None, description="Razón del bloqueo")
    is_closed: bool | None = Field(None, description="¿Está cerrado?")
    tags: list[str] | None = Field(None, description="Tags")


class ListIssuesRequest(BaseModel):
    """Request para listar issues."""

    project_id: int | None = Field(None, gt=0, description="Filtrar por proyecto")
    type_id: int | None = Field(None, gt=0, description="Filtrar por tipo")
    severity_id: int | None = Field(None, gt=0, description="Filtrar por severidad")
    priority_id: int | None = Field(None, gt=0, description="Filtrar por prioridad")
    status_id: int | None = Field(None, gt=0, description="Filtrar por estado")
    milestone_id: int | None = Field(None, gt=0, description="Filtrar por milestone")
    assigned_to_id: int | None = Field(None, gt=0, description="Filtrar por asignado")
    is_closed: bool | None = Field(None, description="Filtrar por cerrados")
    tags: list[str] | None = Field(None, description="Filtrar por tags")
    limit: int | None = Field(None, gt=0, le=100, description="Límite de resultados")
    offset: int | None = Field(None, ge=0, description="Offset para paginación")


class BulkCreateIssuesRequest(BaseModel):
    """Request para crear múltiples issues."""

    project_id: int = Field(..., gt=0, description="ID del proyecto")
    issues: list[CreateIssueRequest] = Field(
        ..., min_length=1, description="Lista de issues a crear"
    )


# Use Cases


class IssueUseCases:
    """
    Casos de uso para gestión de issues.

    Coordina operaciones de negocio usando el repositorio.
    NO accede directamente a TaigaAPIClient.
    """

    def __init__(self, repository: IssueRepository) -> None:
        """
        Inicializa los casos de uso.

        Args:
            repository: Repositorio de issues
        """
        self.repository = repository

    async def create_issue(self, request: CreateIssueRequest) -> Issue:
        """
        Crea un nuevo issue.

        Args:
            request: Datos del issue a crear

        Returns:
            Issue creado con ID asignado

        Raises:
            ValidationError: Si los datos son inválidos
        """
        issue = Issue(
            subject=request.subject,
            description=request.description,
            project_id=request.project_id,
            status=request.status,
            type=request.type,
            severity=request.severity,
            priority=request.priority,
            milestone_id=request.milestone_id,
            assigned_to_id=request.assigned_to_id,
            is_blocked=request.is_blocked,
            blocked_note=request.blocked_note,
            tags=request.tags,
        )

        return await self.repository.create(issue)

    async def get_issue(self, issue_id: int) -> Issue:
        """
        Obtiene un issue por ID.

        Args:
            issue_id: ID del issue

        Returns:
            Issue encontrado

        Raises:
            ResourceNotFoundError: Si el issue no existe
        """
        issue = await self.repository.get_by_id(issue_id)
        if issue is None:
            raise ResourceNotFoundError(f"Issue {issue_id} not found")
        return issue

    async def get_issue_by_ref(self, project_id: int, ref: int) -> Issue:
        """
        Obtiene un issue por referencia en proyecto.

        Args:
            project_id: ID del proyecto
            ref: Número de referencia

        Returns:
            Issue encontrado

        Raises:
            ResourceNotFoundError: Si el issue no existe
        """
        issue = await self.repository.get_by_ref(project_id, ref)
        if issue is None:
            raise ResourceNotFoundError(f"Issue with ref={ref} not found in project {project_id}")
        return issue

    async def list_issues(self, request: ListIssuesRequest) -> list[Issue]:
        """
        Lista issues con filtros opcionales.

        Args:
            request: Filtros de búsqueda

        Returns:
            Lista de issues que cumplen los filtros
        """
        filters: dict[str, Any] = {}
        if request.project_id is not None:
            filters["project"] = request.project_id
        if request.type_id is not None:
            filters["type"] = request.type_id
        if request.severity_id is not None:
            filters["severity"] = request.severity_id
        if request.priority_id is not None:
            filters["priority"] = request.priority_id
        if request.status_id is not None:
            filters["status"] = request.status_id
        if request.milestone_id is not None:
            filters["milestone"] = request.milestone_id
        if request.assigned_to_id is not None:
            filters["assigned_to"] = request.assigned_to_id
        if request.is_closed is not None:
            filters["is_closed"] = request.is_closed
        if request.tags is not None:
            filters["tags"] = request.tags

        return await self.repository.list(
            filters=filters,
            limit=request.limit,
            offset=request.offset,
        )

    async def list_by_type(self, project_id: int, type_id: int) -> list[Issue]:
        """
        Lista issues de un tipo específico.

        Args:
            project_id: ID del proyecto
            type_id: ID del tipo

        Returns:
            Lista de issues del tipo
        """
        return await self.repository.list_by_type(project_id, type_id)

    async def list_by_severity(self, project_id: int, severity_id: int) -> list[Issue]:
        """
        Lista issues con una severidad específica.

        Args:
            project_id: ID del proyecto
            severity_id: ID de la severidad

        Returns:
            Lista de issues con esa severidad
        """
        return await self.repository.list_by_severity(project_id, severity_id)

    async def list_by_priority(self, project_id: int, priority_id: int) -> list[Issue]:
        """
        Lista issues con una prioridad específica.

        Args:
            project_id: ID del proyecto
            priority_id: ID de la prioridad

        Returns:
            Lista de issues con esa prioridad
        """
        return await self.repository.list_by_priority(project_id, priority_id)

    async def list_by_milestone(self, milestone_id: int) -> list[Issue]:
        """
        Lista issues de un milestone.

        Args:
            milestone_id: ID del milestone

        Returns:
            Lista de issues del milestone
        """
        return await self.repository.list_by_milestone(milestone_id)

    async def list_open(self, project_id: int) -> list[Issue]:
        """
        Lista issues abiertos de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de issues abiertos
        """
        return await self.repository.list_open(project_id)

    async def list_closed(self, project_id: int) -> list[Issue]:
        """
        Lista issues cerrados de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de issues cerrados
        """
        return await self.repository.list_closed(project_id)

    async def update_issue(self, request: UpdateIssueRequest) -> Issue:
        """
        Actualiza un issue existente.

        Args:
            request: Datos del issue a actualizar

        Returns:
            Issue actualizado

        Raises:
            ResourceNotFoundError: Si el issue no existe
        """
        issue = await self.get_issue(request.issue_id)

        if request.subject is not None:
            issue.subject = request.subject
        if request.description is not None:
            issue.description = request.description
        if request.status is not None:
            issue.status = request.status
        if request.type is not None:
            issue.type = request.type
        if request.severity is not None:
            issue.severity = request.severity
        if request.priority is not None:
            issue.priority = request.priority
        if request.milestone_id is not None:
            issue.milestone_id = request.milestone_id
        if request.assigned_to_id is not None:
            issue.assigned_to_id = request.assigned_to_id
        if request.is_blocked is not None:
            issue.is_blocked = request.is_blocked
        if request.blocked_note is not None:
            issue.blocked_note = request.blocked_note
        if request.is_closed is not None:
            issue.is_closed = request.is_closed
        if request.tags is not None:
            issue.tags = request.tags

        return await self.repository.update(issue)

    async def delete_issue(self, issue_id: int) -> bool:
        """
        Elimina un issue.

        Args:
            issue_id: ID del issue a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        return await self.repository.delete(issue_id)

    async def bulk_create_issues(self, request: BulkCreateIssuesRequest) -> list[Issue]:
        """
        Crea múltiples issues en lote.

        Args:
            request: Datos de los issues a crear

        Returns:
            Lista de issues creados
        """
        issues = [
            Issue(
                subject=issue.subject,
                description=issue.description,
                project_id=request.project_id,
                status=issue.status,
                type=issue.type,
                severity=issue.severity,
                priority=issue.priority,
                milestone_id=issue.milestone_id,
                assigned_to_id=issue.assigned_to_id,
                is_blocked=issue.is_blocked,
                blocked_note=issue.blocked_note,
                tags=issue.tags,
            )
            for issue in request.issues
        ]

        return await self.repository.bulk_create(issues)

    async def get_filters(self, project_id: int) -> dict[str, Any]:
        """
        Obtiene filtros disponibles para issues.

        Args:
            project_id: ID del proyecto

        Returns:
            Diccionario con opciones de filtro
        """
        return await self.repository.get_filters(project_id)
