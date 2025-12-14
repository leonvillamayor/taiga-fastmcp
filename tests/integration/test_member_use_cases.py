"""
Tests de integración para casos de uso de members.
Implementa tests para la capa de aplicación.
"""

from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.member_use_cases import (
    BulkCreateMembersRequest,
    CreateMemberRequest,
    ListMembersRequest,
    MemberUseCases,
    UpdateMemberRequest,
)
from src.domain.entities.member import Member
from src.domain.exceptions import ResourceNotFoundError
from src.domain.value_objects.email import Email


@pytest.fixture
def mock_member_repository() -> AsyncMock:
    """Crea un mock del repositorio de members."""
    return AsyncMock()


@pytest.fixture
def sample_member() -> Member:
    """Crea un member de ejemplo para tests."""
    return Member(
        id=1,
        project_id=100,
        user_id=10,
        role_id=5,
        username="testuser",
        full_name="Test User",
        email=Email(value="test@example.com"),
        is_admin=False,
    )


@pytest.fixture
def sample_members_list(sample_member: Member) -> list[Member]:
    """Lista de members de ejemplo."""
    return [
        sample_member,
        Member(
            id=2,
            project_id=100,
            user_id=11,
            username="another",
            full_name="Another User",
        ),
    ]


@pytest.mark.integration
@pytest.mark.asyncio
class TestMemberUseCases:
    """Tests de integración para casos de uso de members."""

    async def test_list_members(
        self,
        mock_member_repository: AsyncMock,
        sample_members_list: list[Member],
    ) -> None:
        """Verifica el caso de uso de listar members."""
        mock_member_repository.list.return_value = sample_members_list
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = ListMembersRequest(project_id=100, is_admin=False)

        result = await use_cases.list_members(request)

        assert len(result) == 2
        mock_member_repository.list.assert_called_once()

    async def test_list_by_project(
        self,
        mock_member_repository: AsyncMock,
        sample_members_list: list[Member],
    ) -> None:
        """Verifica el caso de uso de listar members por proyecto."""
        mock_member_repository.list_by_project.return_value = sample_members_list
        use_cases = MemberUseCases(repository=mock_member_repository)

        result = await use_cases.list_by_project(project_id=100)

        assert len(result) == 2
        mock_member_repository.list_by_project.assert_called_once_with(100)

    async def test_create_member(
        self, mock_member_repository: AsyncMock, sample_member: Member
    ) -> None:
        """Verifica el caso de uso de crear un member."""
        mock_member_repository.create.return_value = sample_member
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = CreateMemberRequest(
            project_id=100,
            user_id=10,
            role_id=5,
            username="testuser",
            full_name="Test User",
            email="test@example.com",
        )

        result = await use_cases.create_member(request)

        assert result.id == 1
        assert result.username == "testuser"
        mock_member_repository.create.assert_called_once()

    async def test_get_member_by_id(
        self, mock_member_repository: AsyncMock, sample_member: Member
    ) -> None:
        """Verifica el caso de uso de obtener member por ID."""
        mock_member_repository.get_by_id.return_value = sample_member
        use_cases = MemberUseCases(repository=mock_member_repository)

        result = await use_cases.get_member(member_id=1)

        assert result.id == 1
        mock_member_repository.get_by_id.assert_called_once_with(1)

    async def test_get_member_by_id_not_found(self, mock_member_repository: AsyncMock) -> None:
        """Verifica que se lance ResourceNotFoundError si el member no existe."""
        mock_member_repository.get_by_id.return_value = None
        use_cases = MemberUseCases(repository=mock_member_repository)

        with pytest.raises(ResourceNotFoundError, match="Member 999 not found"):
            await use_cases.get_member(member_id=999)

    async def test_get_by_user(
        self, mock_member_repository: AsyncMock, sample_member: Member
    ) -> None:
        """Verifica el caso de uso de obtener member por usuario."""
        mock_member_repository.get_by_user.return_value = sample_member
        use_cases = MemberUseCases(repository=mock_member_repository)

        result = await use_cases.get_by_user(project_id=100, user_id=10)

        assert result.user_id == 10
        mock_member_repository.get_by_user.assert_called_once_with(100, 10)

    async def test_get_by_user_not_found(self, mock_member_repository: AsyncMock) -> None:
        """Verifica que se lance ResourceNotFoundError si no se encuentra por usuario."""
        mock_member_repository.get_by_user.return_value = None
        use_cases = MemberUseCases(repository=mock_member_repository)

        with pytest.raises(ResourceNotFoundError, match="user 999 not found"):
            await use_cases.get_by_user(project_id=100, user_id=999)

    async def test_update_member(
        self, mock_member_repository: AsyncMock, sample_member: Member
    ) -> None:
        """Verifica el caso de uso de actualizar un member."""
        updated = Member(
            id=1,
            project_id=100,
            user_id=10,
            role_id=6,
            username="testuser",
            is_admin=True,
        )
        mock_member_repository.get_by_id.return_value = sample_member
        mock_member_repository.update.return_value = updated
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = UpdateMemberRequest(member_id=1, role_id=6, is_admin=True)

        result = await use_cases.update_member(request)

        assert result.role_id == 6
        assert result.is_admin is True
        mock_member_repository.update.assert_called_once()

    async def test_delete_member(self, mock_member_repository: AsyncMock) -> None:
        """Verifica el caso de uso de eliminar un member."""
        mock_member_repository.delete.return_value = True
        use_cases = MemberUseCases(repository=mock_member_repository)

        result = await use_cases.delete_member(member_id=1)

        assert result is True
        mock_member_repository.delete.assert_called_once_with(1)

    async def test_bulk_create_members(
        self,
        mock_member_repository: AsyncMock,
        sample_members_list: list[Member],
    ) -> None:
        """Verifica el caso de uso de crear múltiples members."""
        mock_member_repository.bulk_create.return_value = sample_members_list
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = BulkCreateMembersRequest(
            project_id=100,
            members=[
                CreateMemberRequest(
                    project_id=100, user_id=10, username="user1", full_name="User 1"
                ),
                CreateMemberRequest(
                    project_id=100, user_id=11, username="user2", full_name="User 2"
                ),
            ],
        )

        result = await use_cases.bulk_create_members(request)

        assert len(result) == 2
        mock_member_repository.bulk_create.assert_called_once()

    async def test_list_admins(
        self,
        mock_member_repository: AsyncMock,
        sample_members_list: list[Member],
    ) -> None:
        """Verifica el caso de uso de listar administradores."""
        mock_member_repository.list_admins.return_value = sample_members_list
        use_cases = MemberUseCases(repository=mock_member_repository)

        result = await use_cases.list_admins(project_id=100)

        assert len(result) == 2
        mock_member_repository.list_admins.assert_called_once_with(100)

    async def test_list_by_role(
        self,
        mock_member_repository: AsyncMock,
        sample_members_list: list[Member],
    ) -> None:
        """Verifica el caso de uso de listar members por rol."""
        mock_member_repository.list_by_role.return_value = sample_members_list
        use_cases = MemberUseCases(repository=mock_member_repository)

        result = await use_cases.list_by_role(project_id=100, role_id=5)

        assert len(result) == 2
        mock_member_repository.list_by_role.assert_called_once_with(100, 5)

    async def test_make_admin(
        self, mock_member_repository: AsyncMock, sample_member: Member
    ) -> None:
        """Verifica el caso de uso de hacer admin a un member."""
        admin_member = Member(id=1, project_id=100, user_id=10, username="testuser", is_admin=True)
        mock_member_repository.get_by_id.return_value = sample_member
        mock_member_repository.update.return_value = admin_member
        use_cases = MemberUseCases(repository=mock_member_repository)

        result = await use_cases.make_admin(member_id=1)

        assert result.is_admin is True
        mock_member_repository.update.assert_called_once()

    async def test_remove_admin(self, mock_member_repository: AsyncMock) -> None:
        """Verifica el caso de uso de quitar admin a un member."""
        admin_member = Member(id=1, project_id=100, user_id=10, username="testuser", is_admin=True)
        non_admin = Member(id=1, project_id=100, user_id=10, username="testuser", is_admin=False)
        mock_member_repository.get_by_id.return_value = admin_member
        mock_member_repository.update.return_value = non_admin
        use_cases = MemberUseCases(repository=mock_member_repository)

        result = await use_cases.remove_admin(member_id=1)

        assert result.is_admin is False
        mock_member_repository.update.assert_called_once()
