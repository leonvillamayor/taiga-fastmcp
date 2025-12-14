"""Use cases para gestión de members (miembros del proyecto)."""

from typing import Any

from pydantic import BaseModel, Field

from src.domain.entities.member import Member
from src.domain.exceptions import ResourceNotFoundError
from src.domain.repositories.member_repository import MemberRepository
from src.domain.value_objects.email import Email


# DTOs (Data Transfer Objects)


class CreateMemberRequest(BaseModel):
    """Request para crear member."""

    project_id: int = Field(..., gt=0, description="ID del proyecto")
    user_id: int = Field(..., gt=0, description="ID del usuario")
    role_id: int | None = Field(None, gt=0, description="ID del rol")
    username: str = Field(..., min_length=1, max_length=150, description="Username")
    full_name: str = Field("", max_length=255, description="Nombre completo")
    email: str | None = Field(None, description="Email del usuario")
    is_admin: bool = Field(False, description="¿Es administrador?")


class UpdateMemberRequest(BaseModel):
    """Request para actualizar member."""

    member_id: int = Field(..., gt=0, description="ID del member")
    role_id: int | None = Field(None, gt=0, description="ID del nuevo rol")
    is_admin: bool | None = Field(None, description="¿Es administrador?")


class ListMembersRequest(BaseModel):
    """Request para listar members."""

    project_id: int | None = Field(None, gt=0, description="Filtrar por proyecto")
    role_id: int | None = Field(None, gt=0, description="Filtrar por rol")
    is_admin: bool | None = Field(None, description="Filtrar por admin")
    limit: int | None = Field(None, gt=0, le=100, description="Límite de resultados")
    offset: int | None = Field(None, ge=0, description="Offset para paginación")


class BulkCreateMembersRequest(BaseModel):
    """Request para crear múltiples members."""

    project_id: int = Field(..., gt=0, description="ID del proyecto")
    members: list[CreateMemberRequest] = Field(
        ..., min_length=1, description="Lista de members a crear"
    )


# Use Cases


class MemberUseCases:
    """
    Casos de uso para gestión de members.

    Coordina operaciones de negocio usando el repositorio.
    NO accede directamente a TaigaAPIClient.
    """

    def __init__(self, repository: MemberRepository) -> None:
        """
        Inicializa los casos de uso.

        Args:
            repository: Repositorio de members
        """
        self.repository = repository

    async def create_member(self, request: CreateMemberRequest) -> Member:
        """
        Crea un nuevo member en un proyecto.

        Args:
            request: Datos del member a crear

        Returns:
            Member creado con ID asignado

        Raises:
            ValidationError: Si los datos son inválidos
        """
        email = Email(value=request.email) if request.email else None
        member = Member(
            project_id=request.project_id,
            user_id=request.user_id,
            role_id=request.role_id,
            username=request.username,
            full_name=request.full_name,
            email=email,
            is_admin=request.is_admin,
        )

        return await self.repository.create(member)

    async def get_member(self, member_id: int) -> Member:
        """
        Obtiene un member por ID.

        Args:
            member_id: ID del member

        Returns:
            Member encontrado

        Raises:
            ResourceNotFoundError: Si el member no existe
        """
        member = await self.repository.get_by_id(member_id)
        if member is None:
            raise ResourceNotFoundError(f"Member {member_id} not found")
        return member

    async def get_by_user(self, project_id: int, user_id: int) -> Member:
        """
        Obtiene un member por usuario en un proyecto.

        Args:
            project_id: ID del proyecto
            user_id: ID del usuario

        Returns:
            Member encontrado

        Raises:
            ResourceNotFoundError: Si el member no existe
        """
        member = await self.repository.get_by_user(project_id, user_id)
        if member is None:
            raise ResourceNotFoundError(
                f"Member for user {user_id} not found in project {project_id}"
            )
        return member

    async def list_members(self, request: ListMembersRequest) -> list[Member]:
        """
        Lista members con filtros opcionales.

        Args:
            request: Filtros de búsqueda

        Returns:
            Lista de members que cumplen los filtros
        """
        filters: dict[str, Any] = {}
        if request.project_id is not None:
            filters["project"] = request.project_id
        if request.role_id is not None:
            filters["role"] = request.role_id
        if request.is_admin is not None:
            filters["is_admin"] = request.is_admin

        return await self.repository.list(
            filters=filters,
            limit=request.limit,
            offset=request.offset,
        )

    async def list_by_project(self, project_id: int) -> list[Member]:
        """
        Lista members de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de members del proyecto
        """
        return await self.repository.list_by_project(project_id)

    async def list_admins(self, project_id: int) -> list[Member]:
        """
        Lista administradores de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de members administradores
        """
        return await self.repository.list_admins(project_id)

    async def list_by_role(self, project_id: int, role_id: int) -> list[Member]:
        """
        Lista members con un rol específico.

        Args:
            project_id: ID del proyecto
            role_id: ID del rol

        Returns:
            Lista de members con ese rol
        """
        return await self.repository.list_by_role(project_id, role_id)

    async def update_member(self, request: UpdateMemberRequest) -> Member:
        """
        Actualiza un member existente.

        Args:
            request: Datos del member a actualizar

        Returns:
            Member actualizado

        Raises:
            ResourceNotFoundError: Si el member no existe
        """
        member = await self.get_member(request.member_id)

        if request.role_id is not None:
            member.change_role(request.role_id)
        if request.is_admin is not None:
            if request.is_admin:
                member.make_admin()
            else:
                member.remove_admin()

        return await self.repository.update(member)

    async def delete_member(self, member_id: int) -> bool:
        """
        Elimina un member de un proyecto.

        Args:
            member_id: ID del member a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        return await self.repository.delete(member_id)

    async def bulk_create_members(self, request: BulkCreateMembersRequest) -> list[Member]:
        """
        Crea múltiples members en lote.

        Args:
            request: Datos de los members a crear

        Returns:
            Lista de members creados
        """
        members = [
            Member(
                project_id=request.project_id,
                user_id=m.user_id,
                role_id=m.role_id,
                username=m.username,
                full_name=m.full_name,
                email=Email(value=m.email) if m.email else None,
                is_admin=m.is_admin,
            )
            for m in request.members
        ]

        return await self.repository.bulk_create(members)

    async def make_admin(self, member_id: int) -> Member:
        """
        Convierte un member en administrador.

        Args:
            member_id: ID del member

        Returns:
            Member actualizado

        Raises:
            ResourceNotFoundError: Si el member no existe
        """
        member = await self.get_member(member_id)
        member.make_admin()
        return await self.repository.update(member)

    async def remove_admin(self, member_id: int) -> Member:
        """
        Quita permisos de administrador a un member.

        Args:
            member_id: ID del member

        Returns:
            Member actualizado

        Raises:
            ResourceNotFoundError: Si el member no existe
        """
        member = await self.get_member(member_id)
        member.remove_admin()
        return await self.repository.update(member)
