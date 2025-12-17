"""Use cases para gestión de proyectos."""

from typing import Any

from pydantic import BaseModel, Field

from src.domain.entities.project import Project
from src.domain.exceptions import ResourceNotFoundError
from src.domain.repositories.project_repository import ProjectRepository

# DTOs (Data Transfer Objects)


class CreateProjectRequest(BaseModel):
    """Request para crear proyecto."""

    name: str = Field(..., min_length=1, max_length=255, description="Nombre del proyecto")
    description: str = Field("", description="Descripción del proyecto")
    is_private: bool = Field(True, description="¿Es proyecto privado?")
    is_backlog_activated: bool = Field(True, description="¿Módulo backlog activado?")
    is_kanban_activated: bool = Field(True, description="¿Módulo kanban activado?")
    is_wiki_activated: bool = Field(True, description="¿Módulo wiki activado?")
    is_issues_activated: bool = Field(True, description="¿Módulo issues activado?")
    tags: list[str] = Field(default_factory=list, description="Tags del proyecto")


class UpdateProjectRequest(BaseModel):
    """Request para actualizar proyecto."""

    project_id: int = Field(..., gt=0, description="ID del proyecto")
    name: str | None = Field(None, min_length=1, max_length=255, description="Nombre")
    description: str | None = Field(None, description="Descripción")
    is_private: bool | None = Field(None, description="¿Es privado?")
    is_backlog_activated: bool | None = Field(None, description="¿Backlog activado?")
    is_kanban_activated: bool | None = Field(None, description="¿Kanban activado?")
    is_wiki_activated: bool | None = Field(None, description="¿Wiki activado?")
    is_issues_activated: bool | None = Field(None, description="¿Issues activado?")
    tags: list[str] | None = Field(None, description="Tags del proyecto")


class ListProjectsRequest(BaseModel):
    """Request para listar proyectos."""

    member_id: int | None = Field(None, gt=0, description="Filtrar por ID de miembro")
    is_private: bool | None = Field(None, description="Filtrar por privacidad")
    limit: int | None = Field(None, gt=0, le=100, description="Límite de resultados")
    offset: int | None = Field(None, ge=0, description="Offset para paginación")


# Use Cases


class ProjectUseCases:
    """
    Casos de uso para gestión de proyectos.

    Coordina operaciones de negocio usando el repositorio.
    NO accede directamente a TaigaAPIClient.
    """

    def __init__(self, repository: ProjectRepository) -> None:
        """
        Inicializa los casos de uso.

        Args:
            repository: Repositorio de proyectos
        """
        self.repository = repository

    async def create_project(self, request: CreateProjectRequest) -> Project:
        """
        Crea un nuevo proyecto.

        Args:
            request: Datos del proyecto a crear

        Returns:
            Proyecto creado con ID asignado

        Raises:
            ValidationError: Si los datos son inválidos
        """
        project = Project(
            name=request.name,
            description=request.description,
            is_private=request.is_private,
            is_backlog_activated=request.is_backlog_activated,
            is_kanban_activated=request.is_kanban_activated,
            is_wiki_activated=request.is_wiki_activated,
            is_issues_activated=request.is_issues_activated,
            tags=request.tags,
        )

        return await self.repository.create(project)

    async def get_project(self, project_id: int) -> Project:
        """
        Obtiene un proyecto por ID.

        Args:
            project_id: ID del proyecto

        Returns:
            Proyecto encontrado

        Raises:
            ResourceNotFoundError: Si el proyecto no existe
        """
        project = await self.repository.get_by_id(project_id)
        if project is None:
            raise ResourceNotFoundError(f"Project {project_id} not found")
        return project

    async def get_project_by_slug(self, slug: str) -> Project:
        """
        Obtiene un proyecto por slug.

        Args:
            slug: Slug del proyecto

        Returns:
            Proyecto encontrado

        Raises:
            ResourceNotFoundError: Si el proyecto no existe
        """
        project = await self.repository.get_by_slug(slug)
        if project is None:
            raise ResourceNotFoundError(f"Project with slug '{slug}' not found")
        return project

    async def list_projects(self, request: ListProjectsRequest) -> list[Project]:
        """
        Lista proyectos con filtros opcionales.

        Args:
            request: Filtros de búsqueda

        Returns:
            Lista de proyectos que cumplen los filtros
        """
        filters: dict[str, Any] = {}
        if request.member_id is not None:
            filters["member"] = request.member_id
        if request.is_private is not None:
            filters["is_private"] = request.is_private

        return await self.repository.list(
            filters=filters,
            limit=request.limit,
            offset=request.offset,
        )

    async def update_project(self, request: UpdateProjectRequest) -> Project:
        """
        Actualiza un proyecto existente.

        Args:
            request: Datos del proyecto a actualizar

        Returns:
            Proyecto actualizado

        Raises:
            ResourceNotFoundError: Si el proyecto no existe
            ConcurrencyError: Si hubo conflicto de versión
        """
        project = await self.get_project(request.project_id)

        if request.name is not None:
            project.name = request.name
        if request.description is not None:
            project.description = request.description
        if request.is_private is not None:
            project.is_private = request.is_private
        if request.is_backlog_activated is not None:
            project.is_backlog_activated = request.is_backlog_activated
        if request.is_kanban_activated is not None:
            project.is_kanban_activated = request.is_kanban_activated
        if request.is_wiki_activated is not None:
            project.is_wiki_activated = request.is_wiki_activated
        if request.is_issues_activated is not None:
            project.is_issues_activated = request.is_issues_activated
        if request.tags is not None:
            project.tags = request.tags

        return await self.repository.update(project)

    async def delete_project(self, project_id: int) -> bool:
        """
        Elimina un proyecto.

        Args:
            project_id: ID del proyecto a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        return await self.repository.delete(project_id)

    async def get_project_stats(self, project_id: int) -> dict[str, Any]:
        """
        Obtiene estadísticas del proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Diccionario con estadísticas

        Raises:
            ResourceNotFoundError: Si el proyecto no existe
        """
        await self.get_project(project_id)
        return await self.repository.get_stats(project_id)
