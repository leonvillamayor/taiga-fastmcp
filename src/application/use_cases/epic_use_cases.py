"""Use cases para gestión de epics."""

from typing import Any

from pydantic import BaseModel, Field

from src.domain.entities.epic import Epic
from src.domain.exceptions import ResourceNotFoundError
from src.domain.repositories.epic_repository import EpicRepository

# DTOs (Data Transfer Objects)


class CreateEpicRequest(BaseModel):
    """Request para crear epic."""

    subject: str = Field(..., min_length=1, max_length=500, description="Título")
    description: str | None = Field(None, description="Descripción detallada")
    project_id: int = Field(..., gt=0, description="ID del proyecto")
    status: int | None = Field(None, gt=0, description="ID del estado")
    assigned_to_id: int | None = Field(None, gt=0, description="ID usuario asignado")
    color: str = Field("#A5694F", description="Color en hexadecimal")
    tags: list[str] = Field(default_factory=list, description="Tags")
    client_requirement: bool = Field(False, description="¿Requerimiento de cliente?")
    team_requirement: bool = Field(False, description="¿Requerimiento de equipo?")


class UpdateEpicRequest(BaseModel):
    """Request para actualizar epic."""

    epic_id: int = Field(..., gt=0, description="ID del epic")
    subject: str | None = Field(None, min_length=1, max_length=500, description="Título")
    description: str | None = Field(None, description="Descripción")
    status: int | None = Field(None, gt=0, description="ID del estado")
    assigned_to_id: int | None = Field(None, description="ID usuario asignado")
    color: str | None = Field(None, description="Color en hexadecimal")
    tags: list[str] | None = Field(None, description="Tags")
    client_requirement: bool | None = Field(None, description="¿Requerimiento cliente?")
    team_requirement: bool | None = Field(None, description="¿Requerimiento equipo?")


class ListEpicsRequest(BaseModel):
    """Request para listar epics."""

    project_id: int | None = Field(None, gt=0, description="Filtrar por proyecto")
    status_id: int | None = Field(None, gt=0, description="Filtrar por estado")
    assigned_to_id: int | None = Field(None, gt=0, description="Filtrar por asignado")
    tags: list[str] | None = Field(None, description="Filtrar por tags")
    limit: int | None = Field(None, gt=0, le=100, description="Límite de resultados")
    offset: int | None = Field(None, ge=0, description="Offset para paginación")


class BulkCreateEpicsRequest(BaseModel):
    """Request para crear múltiples epics."""

    project_id: int = Field(..., gt=0, description="ID del proyecto")
    epics: list[CreateEpicRequest] = Field(..., min_length=1, description="Lista de epics a crear")


# Use Cases


class EpicUseCases:
    """
    Casos de uso para gestión de epics.

    Coordina operaciones de negocio usando el repositorio.
    NO accede directamente a TaigaAPIClient.
    """

    def __init__(self, repository: EpicRepository) -> None:
        """
        Inicializa los casos de uso.

        Args:
            repository: Repositorio de epics
        """
        self.repository = repository

    async def create_epic(self, request: CreateEpicRequest) -> Epic:
        """
        Crea un nuevo epic.

        Args:
            request: Datos del epic a crear

        Returns:
            Epic creado con ID asignado

        Raises:
            ValidationError: Si los datos son inválidos
        """
        epic = Epic(
            subject=request.subject,
            description=request.description,
            project=request.project_id,
            status=request.status,
            assigned_to=request.assigned_to_id,
            color=request.color,
            tags=request.tags,
            client_requirement=request.client_requirement,
            team_requirement=request.team_requirement,
        )

        return await self.repository.create(epic)

    async def get_epic(self, epic_id: int) -> Epic:
        """
        Obtiene un epic por ID.

        Args:
            epic_id: ID del epic

        Returns:
            Epic encontrado

        Raises:
            ResourceNotFoundError: Si el epic no existe
        """
        epic = await self.repository.get_by_id(epic_id)
        if epic is None:
            raise ResourceNotFoundError(f"Epic {epic_id} not found")
        return epic

    async def get_epic_by_ref(self, project_id: int, ref: int) -> Epic:
        """
        Obtiene un epic por referencia en proyecto.

        Args:
            project_id: ID del proyecto
            ref: Número de referencia

        Returns:
            Epic encontrado

        Raises:
            ResourceNotFoundError: Si el epic no existe
        """
        epic = await self.repository.get_by_ref(project_id, ref)
        if epic is None:
            raise ResourceNotFoundError(f"Epic with ref={ref} not found in project {project_id}")
        return epic

    async def list_epics(self, request: ListEpicsRequest) -> list[Epic]:
        """
        Lista epics con filtros opcionales.

        Args:
            request: Filtros de búsqueda

        Returns:
            Lista de epics que cumplen los filtros
        """
        filters: dict[str, Any] = {}
        if request.project_id is not None:
            filters["project"] = request.project_id
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

    async def list_by_project(self, project_id: int) -> list[Epic]:
        """
        Lista epics de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de epics del proyecto
        """
        return await self.repository.list_by_project(project_id)

    async def list_by_status(self, project_id: int, status_id: int) -> list[Epic]:
        """
        Lista epics con un estado específico.

        Args:
            project_id: ID del proyecto
            status_id: ID del estado

        Returns:
            Lista de epics con ese estado
        """
        return await self.repository.list_by_status(project_id, status_id)

    async def update_epic(self, request: UpdateEpicRequest) -> Epic:
        """
        Actualiza un epic existente.

        Args:
            request: Datos del epic a actualizar

        Returns:
            Epic actualizado

        Raises:
            ResourceNotFoundError: Si el epic no existe
        """
        epic = await self.get_epic(request.epic_id)

        if request.subject is not None:
            epic.subject = request.subject
        if request.description is not None:
            epic.description = request.description
        if request.status is not None:
            epic.status = request.status
        if request.assigned_to_id is not None:
            epic.assigned_to = request.assigned_to_id
        if request.color is not None:
            epic.color = request.color
        if request.tags is not None:
            epic.tags = request.tags
        if request.client_requirement is not None:
            epic.client_requirement = request.client_requirement
        if request.team_requirement is not None:
            epic.team_requirement = request.team_requirement

        return await self.repository.update(epic)

    async def delete_epic(self, epic_id: int) -> bool:
        """
        Elimina un epic.

        Args:
            epic_id: ID del epic a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        return await self.repository.delete(epic_id)

    async def bulk_create_epics(self, request: BulkCreateEpicsRequest) -> list[Epic]:
        """
        Crea múltiples epics en lote.

        Args:
            request: Datos de los epics a crear

        Returns:
            Lista de epics creados
        """
        epics = [
            Epic(
                subject=epic.subject,
                description=epic.description,
                project=request.project_id,
                status=epic.status,
                assigned_to=epic.assigned_to_id,
                color=epic.color,
                tags=epic.tags,
                client_requirement=epic.client_requirement,
                team_requirement=epic.team_requirement,
            )
            for epic in request.epics
        ]

        return await self.repository.bulk_create(epics)

    async def get_filters(self, project_id: int) -> dict[str, Any]:
        """
        Obtiene filtros disponibles para epics.

        Args:
            project_id: ID del proyecto

        Returns:
            Diccionario con opciones de filtro
        """
        return await self.repository.get_filters(project_id)

    async def upvote_epic(self, epic_id: int) -> Epic:
        """
        Añade un voto positivo a un epic.

        Args:
            epic_id: ID del epic

        Returns:
            Epic actualizado

        Raises:
            ResourceNotFoundError: Si el epic no existe
        """
        await self.get_epic(epic_id)
        return await self.repository.upvote(epic_id)

    async def downvote_epic(self, epic_id: int) -> Epic:
        """
        Quita un voto de un epic.

        Args:
            epic_id: ID del epic

        Returns:
            Epic actualizado

        Raises:
            ResourceNotFoundError: Si el epic no existe
        """
        await self.get_epic(epic_id)
        return await self.repository.downvote(epic_id)

    async def watch_epic(self, epic_id: int) -> Epic:
        """
        Añade el usuario actual como observador del epic.

        Args:
            epic_id: ID del epic

        Returns:
            Epic actualizado

        Raises:
            ResourceNotFoundError: Si el epic no existe
        """
        await self.get_epic(epic_id)
        return await self.repository.watch(epic_id)

    async def unwatch_epic(self, epic_id: int) -> Epic:
        """
        Quita el usuario actual como observador del epic.

        Args:
            epic_id: ID del epic

        Returns:
            Epic actualizado

        Raises:
            ResourceNotFoundError: Si el epic no existe
        """
        await self.get_epic(epic_id)
        return await self.repository.unwatch(epic_id)
