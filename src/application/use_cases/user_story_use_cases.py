"""Use cases para gestión de user stories."""

from typing import Any

from pydantic import BaseModel, Field

from src.domain.entities.user_story import UserStory
from src.domain.exceptions import ResourceNotFoundError
from src.domain.repositories.user_story_repository import UserStoryRepository

# DTOs (Data Transfer Objects)


class CreateUserStoryRequest(BaseModel):
    """Request para crear user story."""

    subject: str = Field(..., min_length=1, max_length=500, description="Título")
    description: str = Field("", description="Descripción detallada")
    project_id: int = Field(..., gt=0, description="ID del proyecto")
    status: int | None = Field(None, gt=0, description="ID del estado")
    milestone_id: int | None = Field(None, gt=0, description="ID del milestone")
    assigned_to_id: int | None = Field(None, gt=0, description="ID usuario asignado")
    is_blocked: bool = Field(False, description="¿Está bloqueada?")
    blocked_note: str = Field("", description="Razón del bloqueo")
    client_requirement: bool = Field(False, description="¿Requerimiento de cliente?")
    team_requirement: bool = Field(False, description="¿Requerimiento de equipo?")
    tags: list[str] = Field(default_factory=list, description="Tags")
    points: dict[str, float] = Field(default_factory=dict, description="Story points por rol")


class UpdateUserStoryRequest(BaseModel):
    """Request para actualizar user story."""

    story_id: int = Field(..., gt=0, description="ID de la user story")
    subject: str | None = Field(None, min_length=1, max_length=500, description="Título")
    description: str | None = Field(None, description="Descripción")
    status: int | None = Field(None, gt=0, description="ID del estado")
    milestone_id: int | None = Field(None, description="ID del milestone")
    assigned_to_id: int | None = Field(None, description="ID usuario asignado")
    is_blocked: bool | None = Field(None, description="¿Está bloqueada?")
    blocked_note: str | None = Field(None, description="Razón del bloqueo")
    is_closed: bool | None = Field(None, description="¿Está cerrada?")
    tags: list[str] | None = Field(None, description="Tags")
    points: dict[str, float] | None = Field(None, description="Story points por rol")


class ListUserStoriesRequest(BaseModel):
    """Request para listar user stories."""

    project_id: int | None = Field(None, gt=0, description="Filtrar por proyecto")
    milestone_id: int | None = Field(None, gt=0, description="Filtrar por milestone")
    status_id: int | None = Field(None, gt=0, description="Filtrar por estado")
    assigned_to_id: int | None = Field(None, gt=0, description="Filtrar por asignado")
    tags: list[str] | None = Field(None, description="Filtrar por tags")
    limit: int | None = Field(None, gt=0, le=100, description="Límite de resultados")
    offset: int | None = Field(None, ge=0, description="Offset para paginación")


class BulkCreateUserStoriesRequest(BaseModel):
    """Request para crear múltiples user stories."""

    project_id: int = Field(..., gt=0, description="ID del proyecto")
    stories: list[CreateUserStoryRequest] = Field(
        ..., min_length=1, description="Lista de user stories a crear"
    )


class BulkUpdateUserStoriesRequest(BaseModel):
    """Request para actualizar múltiples user stories."""

    story_ids: list[int] = Field(..., min_length=1, description="IDs de user stories")
    status: int | None = Field(None, gt=0, description="Nuevo estado")
    milestone_id: int | None = Field(None, description="Nuevo milestone")
    assigned_to_id: int | None = Field(None, description="Nuevo asignado")


class MoveToMilestoneRequest(BaseModel):
    """Request para mover user story a milestone."""

    story_id: int = Field(..., gt=0, description="ID de la user story")
    milestone_id: int | None = Field(None, ge=0, description="ID del milestone (None=backlog)")


# Use Cases


class UserStoryUseCases:
    """
    Casos de uso para gestión de user stories.

    Coordina operaciones de negocio usando el repositorio.
    NO accede directamente a TaigaAPIClient.
    """

    def __init__(self, repository: UserStoryRepository) -> None:
        """
        Inicializa los casos de uso.

        Args:
            repository: Repositorio de user stories
        """
        self.repository = repository

    async def create_user_story(self, request: CreateUserStoryRequest) -> UserStory:
        """
        Crea una nueva user story.

        Args:
            request: Datos de la user story a crear

        Returns:
            User story creada con ID asignado

        Raises:
            ValidationError: Si los datos son inválidos
        """
        story = UserStory(
            subject=request.subject,
            description=request.description,
            project_id=request.project_id,
            status=request.status,
            milestone_id=request.milestone_id,
            assigned_to_id=request.assigned_to_id,
            is_blocked=request.is_blocked,
            blocked_note=request.blocked_note,
            client_requirement=request.client_requirement,
            team_requirement=request.team_requirement,
            tags=request.tags,
            points=request.points,
        )

        return await self.repository.create(story)

    async def get_user_story(self, story_id: int) -> UserStory:
        """
        Obtiene una user story por ID.

        Args:
            story_id: ID de la user story

        Returns:
            User story encontrada

        Raises:
            ResourceNotFoundError: Si la user story no existe
        """
        story = await self.repository.get_by_id(story_id)
        if story is None:
            raise ResourceNotFoundError(f"UserStory {story_id} not found")
        return story

    async def get_user_story_by_ref(self, project_id: int, ref: int) -> UserStory:
        """
        Obtiene una user story por referencia en proyecto.

        Args:
            project_id: ID del proyecto
            ref: Número de referencia

        Returns:
            User story encontrada

        Raises:
            ResourceNotFoundError: Si la user story no existe
        """
        story = await self.repository.get_by_ref(project_id, ref)
        if story is None:
            raise ResourceNotFoundError(
                f"UserStory with ref={ref} not found in project {project_id}"
            )
        return story

    async def list_user_stories(self, request: ListUserStoriesRequest) -> list[UserStory]:
        """
        Lista user stories con filtros opcionales.

        Args:
            request: Filtros de búsqueda

        Returns:
            Lista de user stories que cumplen los filtros
        """
        filters: dict[str, Any] = {}
        if request.project_id is not None:
            filters["project"] = request.project_id
        if request.milestone_id is not None:
            filters["milestone"] = request.milestone_id
        if request.status_id is not None:
            filters["status"] = request.status_id
        if request.assigned_to_id is not None:
            filters["assigned_to"] = request.assigned_to_id
        if request.tags is not None:
            filters["tags"] = request.tags

        return await self.repository.list(
            filters=filters,
            limit=request.limit,
            offset=request.offset,
        )

    async def list_backlog(self, project_id: int) -> list[UserStory]:
        """
        Lista user stories en el backlog (sin milestone).

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de user stories en el backlog
        """
        return await self.repository.list_backlog(project_id)

    async def list_by_milestone(self, milestone_id: int) -> list[UserStory]:
        """
        Lista user stories de un milestone.

        Args:
            milestone_id: ID del milestone

        Returns:
            Lista de user stories del milestone
        """
        return await self.repository.list_by_milestone(milestone_id)

    async def update_user_story(self, request: UpdateUserStoryRequest) -> UserStory:
        """
        Actualiza una user story existente.

        Args:
            request: Datos de la user story a actualizar

        Returns:
            User story actualizada

        Raises:
            ResourceNotFoundError: Si la user story no existe
        """
        story = await self.get_user_story(request.story_id)

        if request.subject is not None:
            story.subject = request.subject
        if request.description is not None:
            story.description = request.description
        if request.status is not None:
            story.status = request.status
        if request.milestone_id is not None:
            story.milestone_id = request.milestone_id
        if request.assigned_to_id is not None:
            story.assigned_to_id = request.assigned_to_id
        if request.is_blocked is not None:
            story.is_blocked = request.is_blocked
        if request.blocked_note is not None:
            story.blocked_note = request.blocked_note
        if request.is_closed is not None:
            story.is_closed = request.is_closed
        if request.tags is not None:
            story.tags = request.tags
        if request.points is not None:
            story.points = request.points

        return await self.repository.update(story)

    async def delete_user_story(self, story_id: int) -> bool:
        """
        Elimina una user story.

        Args:
            story_id: ID de la user story a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        return await self.repository.delete(story_id)

    async def bulk_create_user_stories(
        self, request: BulkCreateUserStoriesRequest
    ) -> list[UserStory]:
        """
        Crea múltiples user stories en lote.

        Args:
            request: Datos de las user stories a crear

        Returns:
            Lista de user stories creadas
        """
        stories = [
            UserStory(
                subject=story.subject,
                description=story.description,
                project_id=request.project_id,
                status=story.status,
                milestone_id=story.milestone_id,
                assigned_to_id=story.assigned_to_id,
                is_blocked=story.is_blocked,
                blocked_note=story.blocked_note,
                client_requirement=story.client_requirement,
                team_requirement=story.team_requirement,
                tags=story.tags,
                points=story.points,
            )
            for story in request.stories
        ]

        return await self.repository.bulk_create(stories)

    async def bulk_update_user_stories(
        self, request: BulkUpdateUserStoriesRequest
    ) -> list[UserStory]:
        """
        Actualiza múltiples user stories en lote.

        Args:
            request: Datos de actualización

        Returns:
            Lista de user stories actualizadas
        """
        updates: dict[str, Any] = {}
        if request.status is not None:
            updates["status"] = request.status
        if request.milestone_id is not None:
            updates["milestone_id"] = request.milestone_id
        if request.assigned_to_id is not None:
            updates["assigned_to_id"] = request.assigned_to_id

        return await self.repository.bulk_update(request.story_ids, updates)

    async def move_to_milestone(self, request: MoveToMilestoneRequest) -> UserStory:
        """
        Mueve una user story a un milestone.

        Args:
            request: Datos de la operación

        Returns:
            User story actualizada

        Raises:
            ResourceNotFoundError: Si la story o milestone no existen
        """
        return await self.repository.move_to_milestone(request.story_id, request.milestone_id)

    async def get_filters(self, project_id: int) -> dict[str, Any]:
        """
        Obtiene filtros disponibles para user stories.

        Args:
            project_id: ID del proyecto

        Returns:
            Diccionario con opciones de filtro
        """
        return await self.repository.get_filters(project_id)
