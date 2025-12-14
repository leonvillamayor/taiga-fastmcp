"""Use cases para gestión de milestones."""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from src.domain.entities.milestone import Milestone
from src.domain.exceptions import ResourceNotFoundError
from src.domain.repositories.milestone_repository import MilestoneRepository


# DTOs (Data Transfer Objects)


class CreateMilestoneRequest(BaseModel):
    """Request para crear milestone."""

    name: str = Field(..., min_length=1, max_length=255, description="Nombre")
    project_id: int = Field(..., gt=0, description="ID del proyecto")
    estimated_start: date | None = Field(None, description="Fecha inicio estimada")
    estimated_finish: date | None = Field(None, description="Fecha fin estimada")
    disponibility: float = Field(1.0, ge=0, le=1, description="Disponibilidad (0-1)")
    order: int = Field(1, ge=1, description="Orden de visualización")


class UpdateMilestoneRequest(BaseModel):
    """Request para actualizar milestone."""

    milestone_id: int = Field(..., gt=0, description="ID del milestone")
    name: str | None = Field(None, min_length=1, max_length=255, description="Nombre")
    estimated_start: date | None = Field(None, description="Fecha inicio estimada")
    estimated_finish: date | None = Field(None, description="Fecha fin estimada")
    is_closed: bool | None = Field(None, description="¿Está cerrado?")
    disponibility: float | None = Field(None, ge=0, le=1, description="Disponibilidad")
    order: int | None = Field(None, ge=1, description="Orden de visualización")


class ListMilestonesRequest(BaseModel):
    """Request para listar milestones."""

    project_id: int | None = Field(None, gt=0, description="Filtrar por proyecto")
    is_closed: bool | None = Field(None, description="Filtrar por cerrados")
    limit: int | None = Field(None, gt=0, le=100, description="Límite de resultados")
    offset: int | None = Field(None, ge=0, description="Offset para paginación")


# Use Cases


class MilestoneUseCases:
    """
    Casos de uso para gestión de milestones.

    Coordina operaciones de negocio usando el repositorio.
    NO accede directamente a TaigaAPIClient.
    """

    def __init__(self, repository: MilestoneRepository) -> None:
        """
        Inicializa los casos de uso.

        Args:
            repository: Repositorio de milestones
        """
        self.repository = repository

    async def create_milestone(self, request: CreateMilestoneRequest) -> Milestone:
        """
        Crea un nuevo milestone.

        Args:
            request: Datos del milestone a crear

        Returns:
            Milestone creado con ID asignado

        Raises:
            ValidationError: Si los datos son inválidos
        """
        milestone = Milestone(
            name=request.name,
            project_id=request.project_id,
            estimated_start=request.estimated_start,
            estimated_finish=request.estimated_finish,
            disponibility=request.disponibility,
            order=request.order,
        )

        return await self.repository.create(milestone)

    async def get_milestone(self, milestone_id: int) -> Milestone:
        """
        Obtiene un milestone por ID.

        Args:
            milestone_id: ID del milestone

        Returns:
            Milestone encontrado

        Raises:
            ResourceNotFoundError: Si el milestone no existe
        """
        milestone = await self.repository.get_by_id(milestone_id)
        if milestone is None:
            raise ResourceNotFoundError(f"Milestone {milestone_id} not found")
        return milestone

    async def list_milestones(self, request: ListMilestonesRequest) -> list[Milestone]:
        """
        Lista milestones con filtros opcionales.

        Args:
            request: Filtros de búsqueda

        Returns:
            Lista de milestones que cumplen los filtros
        """
        filters: dict[str, Any] = {}
        if request.project_id is not None:
            filters["project"] = request.project_id
        if request.is_closed is not None:
            filters["closed"] = request.is_closed

        return await self.repository.list(
            filters=filters,
            limit=request.limit,
            offset=request.offset,
        )

    async def list_by_project(self, project_id: int) -> list[Milestone]:
        """
        Lista milestones de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de milestones del proyecto
        """
        return await self.repository.list_by_project(project_id)

    async def list_open(self, project_id: int) -> list[Milestone]:
        """
        Lista milestones abiertos de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de milestones abiertos
        """
        return await self.repository.list_open(project_id)

    async def list_closed(self, project_id: int) -> list[Milestone]:
        """
        Lista milestones cerrados de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de milestones cerrados
        """
        return await self.repository.list_closed(project_id)

    async def get_current(self, project_id: int) -> Milestone | None:
        """
        Obtiene el milestone actual (activo) de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Milestone actual si existe, None si no hay ninguno activo
        """
        return await self.repository.get_current(project_id)

    async def update_milestone(self, request: UpdateMilestoneRequest) -> Milestone:
        """
        Actualiza un milestone existente.

        Args:
            request: Datos del milestone a actualizar

        Returns:
            Milestone actualizado

        Raises:
            ResourceNotFoundError: Si el milestone no existe
        """
        milestone = await self.get_milestone(request.milestone_id)

        if request.name is not None:
            milestone.name = request.name
        if request.estimated_start is not None:
            milestone.estimated_start = request.estimated_start
        if request.estimated_finish is not None:
            milestone.estimated_finish = request.estimated_finish
        if request.is_closed is not None:
            milestone.is_closed = request.is_closed
        if request.disponibility is not None:
            milestone.disponibility = request.disponibility
        if request.order is not None:
            milestone.order = request.order

        return await self.repository.update(milestone)

    async def delete_milestone(self, milestone_id: int) -> bool:
        """
        Elimina un milestone.

        Args:
            milestone_id: ID del milestone a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        return await self.repository.delete(milestone_id)

    async def close_milestone(self, milestone_id: int) -> Milestone:
        """
        Cierra un milestone.

        Args:
            milestone_id: ID del milestone

        Returns:
            Milestone cerrado

        Raises:
            ResourceNotFoundError: Si el milestone no existe
        """
        milestone = await self.get_milestone(milestone_id)
        milestone.close()
        return await self.repository.update(milestone)

    async def reopen_milestone(self, milestone_id: int) -> Milestone:
        """
        Reabre un milestone cerrado.

        Args:
            milestone_id: ID del milestone

        Returns:
            Milestone reabierto

        Raises:
            ResourceNotFoundError: Si el milestone no existe
        """
        milestone = await self.get_milestone(milestone_id)
        milestone.reopen()
        return await self.repository.update(milestone)

    async def get_stats(self, milestone_id: int) -> dict[str, Any]:
        """
        Obtiene estadísticas del milestone.

        Args:
            milestone_id: ID del milestone

        Returns:
            Diccionario con estadísticas

        Raises:
            ResourceNotFoundError: Si el milestone no existe
        """
        await self.get_milestone(milestone_id)
        return await self.repository.get_stats(milestone_id)
