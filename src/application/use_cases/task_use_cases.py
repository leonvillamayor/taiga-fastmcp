"""Use cases para gestión de tasks."""

from typing import Any

from pydantic import BaseModel, Field

from src.domain.entities.task import Task
from src.domain.exceptions import ResourceNotFoundError
from src.domain.repositories.task_repository import TaskRepository

# DTOs (Data Transfer Objects)


class CreateTaskRequest(BaseModel):
    """Request para crear task."""

    subject: str = Field(..., min_length=1, max_length=500, description="Título")
    description: str = Field("", description="Descripción detallada")
    project_id: int = Field(..., gt=0, description="ID del proyecto")
    user_story_id: int | None = Field(None, gt=0, description="ID de la user story")
    status: int | None = Field(None, gt=0, description="ID del estado")
    milestone_id: int | None = Field(None, gt=0, description="ID del milestone")
    assigned_to_id: int | None = Field(None, gt=0, description="ID usuario asignado")
    is_blocked: bool = Field(False, description="¿Está bloqueada?")
    blocked_note: str = Field("", description="Razón del bloqueo")
    is_iocaine: bool = Field(False, description="¿Es tarea difícil/riesgosa?")
    tags: list[str] = Field(default_factory=list, description="Tags")


class UpdateTaskRequest(BaseModel):
    """Request para actualizar task."""

    task_id: int = Field(..., gt=0, description="ID de la task")
    subject: str | None = Field(None, min_length=1, max_length=500, description="Título")
    description: str | None = Field(None, description="Descripción")
    user_story_id: int | None = Field(None, description="ID de la user story")
    status: int | None = Field(None, gt=0, description="ID del estado")
    milestone_id: int | None = Field(None, description="ID del milestone")
    assigned_to_id: int | None = Field(None, description="ID usuario asignado")
    is_blocked: bool | None = Field(None, description="¿Está bloqueada?")
    blocked_note: str | None = Field(None, description="Razón del bloqueo")
    is_closed: bool | None = Field(None, description="¿Está cerrada?")
    is_iocaine: bool | None = Field(None, description="¿Es difícil/riesgosa?")
    tags: list[str] | None = Field(None, description="Tags")


class ListTasksRequest(BaseModel):
    """Request para listar tasks."""

    project_id: int | None = Field(None, gt=0, description="Filtrar por proyecto")
    user_story_id: int | None = Field(None, gt=0, description="Filtrar por user story")
    milestone_id: int | None = Field(None, gt=0, description="Filtrar por milestone")
    status_id: int | None = Field(None, gt=0, description="Filtrar por estado")
    assigned_to_id: int | None = Field(None, gt=0, description="Filtrar por asignado")
    is_closed: bool | None = Field(None, description="Filtrar por cerradas")
    tags: list[str] | None = Field(None, description="Filtrar por tags")
    limit: int | None = Field(None, gt=0, le=100, description="Límite de resultados")
    offset: int | None = Field(None, ge=0, description="Offset para paginación")


class BulkCreateTasksRequest(BaseModel):
    """Request para crear múltiples tasks."""

    project_id: int = Field(..., gt=0, description="ID del proyecto")
    user_story_id: int | None = Field(None, gt=0, description="ID de la user story")
    tasks: list[CreateTaskRequest] = Field(..., min_length=1, description="Lista de tasks a crear")


# Use Cases


class TaskUseCases:
    """
    Casos de uso para gestión de tasks.

    Coordina operaciones de negocio usando el repositorio.
    NO accede directamente a TaigaAPIClient.
    """

    def __init__(self, repository: TaskRepository) -> None:
        """
        Inicializa los casos de uso.

        Args:
            repository: Repositorio de tasks
        """
        self.repository = repository

    async def create_task(self, request: CreateTaskRequest) -> Task:
        """
        Crea una nueva task.

        Args:
            request: Datos de la task a crear

        Returns:
            Task creada con ID asignado

        Raises:
            ValidationError: Si los datos son inválidos
        """
        task = Task(
            subject=request.subject,
            description=request.description,
            project_id=request.project_id,
            user_story_id=request.user_story_id,
            status=request.status,
            milestone_id=request.milestone_id,
            assigned_to_id=request.assigned_to_id,
            is_blocked=request.is_blocked,
            blocked_note=request.blocked_note,
            is_iocaine=request.is_iocaine,
            tags=request.tags,
        )

        return await self.repository.create(task)

    async def get_task(self, task_id: int) -> Task:
        """
        Obtiene una task por ID.

        Args:
            task_id: ID de la task

        Returns:
            Task encontrada

        Raises:
            ResourceNotFoundError: Si la task no existe
        """
        task = await self.repository.get_by_id(task_id)
        if task is None:
            raise ResourceNotFoundError(f"Task {task_id} not found")
        return task

    async def get_task_by_ref(self, project_id: int, ref: int) -> Task:
        """
        Obtiene una task por referencia en proyecto.

        Args:
            project_id: ID del proyecto
            ref: Número de referencia

        Returns:
            Task encontrada

        Raises:
            ResourceNotFoundError: Si la task no existe
        """
        task = await self.repository.get_by_ref(project_id, ref)
        if task is None:
            raise ResourceNotFoundError(f"Task with ref={ref} not found in project {project_id}")
        return task

    async def list_tasks(self, request: ListTasksRequest) -> list[Task]:
        """
        Lista tasks con filtros opcionales.

        Args:
            request: Filtros de búsqueda

        Returns:
            Lista de tasks que cumplen los filtros
        """
        filters: dict[str, Any] = {}
        if request.project_id is not None:
            filters["project"] = request.project_id
        if request.user_story_id is not None:
            filters["user_story"] = request.user_story_id
        if request.milestone_id is not None:
            filters["milestone"] = request.milestone_id
        if request.status_id is not None:
            filters["status"] = request.status_id
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

    async def list_by_user_story(self, user_story_id: int) -> list[Task]:
        """
        Lista tasks de una user story.

        Args:
            user_story_id: ID de la user story

        Returns:
            Lista de tasks de la user story
        """
        return await self.repository.list_by_user_story(user_story_id)

    async def list_by_milestone(self, milestone_id: int) -> list[Task]:
        """
        Lista tasks de un milestone.

        Args:
            milestone_id: ID del milestone

        Returns:
            Lista de tasks del milestone
        """
        return await self.repository.list_by_milestone(milestone_id)

    async def list_unassigned(self, project_id: int) -> list[Task]:
        """
        Lista tasks sin asignar de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de tasks sin asignar
        """
        return await self.repository.list_unassigned(project_id)

    async def update_task(self, request: UpdateTaskRequest) -> Task:
        """
        Actualiza una task existente.

        Args:
            request: Datos de la task a actualizar

        Returns:
            Task actualizada

        Raises:
            ResourceNotFoundError: Si la task no existe
        """
        task = await self.get_task(request.task_id)

        if request.subject is not None:
            task.subject = request.subject
        if request.description is not None:
            task.description = request.description
        if request.user_story_id is not None:
            task.user_story_id = request.user_story_id
        if request.status is not None:
            task.status = request.status
        if request.milestone_id is not None:
            task.milestone_id = request.milestone_id
        if request.assigned_to_id is not None:
            task.assigned_to_id = request.assigned_to_id
        if request.is_blocked is not None:
            task.is_blocked = request.is_blocked
        if request.blocked_note is not None:
            task.blocked_note = request.blocked_note
        if request.is_closed is not None:
            task.is_closed = request.is_closed
        if request.is_iocaine is not None:
            task.is_iocaine = request.is_iocaine
        if request.tags is not None:
            task.tags = request.tags

        return await self.repository.update(task)

    async def delete_task(self, task_id: int) -> bool:
        """
        Elimina una task.

        Args:
            task_id: ID de la task a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        return await self.repository.delete(task_id)

    async def bulk_create_tasks(self, request: BulkCreateTasksRequest) -> list[Task]:
        """
        Crea múltiples tasks en lote.

        Args:
            request: Datos de las tasks a crear

        Returns:
            Lista de tasks creadas
        """
        tasks = [
            Task(
                subject=task.subject,
                description=task.description,
                project_id=request.project_id,
                user_story_id=request.user_story_id or task.user_story_id,
                status=task.status,
                milestone_id=task.milestone_id,
                assigned_to_id=task.assigned_to_id,
                is_blocked=task.is_blocked,
                blocked_note=task.blocked_note,
                is_iocaine=task.is_iocaine,
                tags=task.tags,
            )
            for task in request.tasks
        ]

        return await self.repository.bulk_create(tasks)

    async def get_filters(self, project_id: int) -> dict[str, Any]:
        """
        Obtiene filtros disponibles para tasks.

        Args:
            project_id: ID del proyecto

        Returns:
            Diccionario con opciones de filtro
        """
        return await self.repository.get_filters(project_id)
