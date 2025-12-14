"""Tests unitarios para MemberUseCases.

Este módulo contiene tests exhaustivos para todos los métodos
de MemberUseCases, cubriendo casos de éxito, errores y edge cases.
"""

from unittest.mock import MagicMock

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


class TestCreateMember:
    """Tests para el caso de uso create_member."""

    @pytest.mark.asyncio
    async def test_create_member_success(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe crear un member exitosamente."""
        # Arrange
        mock_member_repository.create.return_value = sample_member
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = CreateMemberRequest(
            project_id=1,
            user_id=1,
            role_id=1,
            username="testuser",
            full_name="Test User",
            email="user@example.com",
            is_admin=False,
        )

        # Act
        result = await use_cases.create_member(request)

        # Assert
        assert result == sample_member
        mock_member_repository.create.assert_called_once()
        created_member = mock_member_repository.create.call_args[0][0]
        assert created_member.username == "testuser"
        assert created_member.project_id == 1

    @pytest.mark.asyncio
    async def test_create_member_with_defaults(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe crear un member con valores por defecto."""
        # Arrange
        mock_member_repository.create.return_value = sample_member
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = CreateMemberRequest(
            project_id=1,
            user_id=1,
            username="minimaluser",
        )

        # Act
        result = await use_cases.create_member(request)

        # Assert
        assert result == sample_member
        created_member = mock_member_repository.create.call_args[0][0]
        assert created_member.username == "minimaluser"
        assert created_member.is_admin is False
        assert created_member.full_name == ""

    @pytest.mark.asyncio
    async def test_create_member_as_admin(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe crear un member como administrador."""
        # Arrange
        mock_member_repository.create.return_value = sample_member
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = CreateMemberRequest(
            project_id=1,
            user_id=1,
            username="adminuser",
            is_admin=True,
        )

        # Act
        await use_cases.create_member(request)

        # Assert
        created_member = mock_member_repository.create.call_args[0][0]
        assert created_member.is_admin is True

    @pytest.mark.asyncio
    async def test_create_member_without_email(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe crear un member sin email."""
        # Arrange
        mock_member_repository.create.return_value = sample_member
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = CreateMemberRequest(
            project_id=1,
            user_id=1,
            username="noemailer",
        )

        # Act
        await use_cases.create_member(request)

        # Assert
        created_member = mock_member_repository.create.call_args[0][0]
        assert created_member.email is None


class TestGetMember:
    """Tests para el caso de uso get_member."""

    @pytest.mark.asyncio
    async def test_get_member_success(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe retornar el member cuando existe."""
        # Arrange
        mock_member_repository.get_by_id.return_value = sample_member
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Act
        result = await use_cases.get_member(member_id=1)

        # Assert
        assert result == sample_member
        mock_member_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_member_not_found(self, mock_member_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_member_repository.get_by_id.return_value = None
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await use_cases.get_member(member_id=999)

        assert "Member 999 not found" in str(exc_info.value)
        mock_member_repository.get_by_id.assert_called_once_with(999)


class TestGetByUser:
    """Tests para el caso de uso get_by_user."""

    @pytest.mark.asyncio
    async def test_get_by_user_success(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe retornar el member cuando existe el usuario en el proyecto."""
        # Arrange
        mock_member_repository.get_by_user.return_value = sample_member
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Act
        result = await use_cases.get_by_user(project_id=1, user_id=1)

        # Assert
        assert result == sample_member
        mock_member_repository.get_by_user.assert_called_once_with(1, 1)

    @pytest.mark.asyncio
    async def test_get_by_user_not_found(self, mock_member_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe el usuario."""
        # Arrange
        mock_member_repository.get_by_user.return_value = None
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await use_cases.get_by_user(project_id=1, user_id=999)

        assert "Member for user 999 not found in project 1" in str(exc_info.value)


class TestListMembers:
    """Tests para el caso de uso list_members."""

    @pytest.mark.asyncio
    async def test_list_members_no_filters(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe listar members sin filtros."""
        # Arrange
        mock_member_repository.list.return_value = [sample_member]
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = ListMembersRequest()

        # Act
        result = await use_cases.list_members(request)

        # Assert
        assert result == [sample_member]
        mock_member_repository.list.assert_called_once_with(filters={}, limit=None, offset=None)

    @pytest.mark.asyncio
    async def test_list_members_by_project(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe filtrar members por proyecto."""
        # Arrange
        mock_member_repository.list.return_value = [sample_member]
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = ListMembersRequest(project_id=1)

        # Act
        result = await use_cases.list_members(request)

        # Assert
        assert result == [sample_member]
        mock_member_repository.list.assert_called_once_with(
            filters={"project": 1}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_members_by_role(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe filtrar members por rol."""
        # Arrange
        mock_member_repository.list.return_value = [sample_member]
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = ListMembersRequest(role_id=2)

        # Act
        await use_cases.list_members(request)

        # Assert
        mock_member_repository.list.assert_called_once_with(
            filters={"role": 2}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_members_by_admin_status(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe filtrar members por estado admin."""
        # Arrange
        mock_member_repository.list.return_value = [sample_member]
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = ListMembersRequest(is_admin=True)

        # Act
        await use_cases.list_members(request)

        # Assert
        mock_member_repository.list.assert_called_once_with(
            filters={"is_admin": True}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_members_with_pagination(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe aplicar paginación correctamente."""
        # Arrange
        mock_member_repository.list.return_value = [sample_member]
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = ListMembersRequest(limit=10, offset=20)

        # Act
        await use_cases.list_members(request)

        # Assert
        mock_member_repository.list.assert_called_once_with(filters={}, limit=10, offset=20)

    @pytest.mark.asyncio
    async def test_list_members_with_all_filters(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe aplicar todos los filtros combinados."""
        # Arrange
        mock_member_repository.list.return_value = [sample_member]
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = ListMembersRequest(project_id=1, role_id=2, is_admin=False, limit=50, offset=10)

        # Act
        await use_cases.list_members(request)

        # Assert
        mock_member_repository.list.assert_called_once_with(
            filters={"project": 1, "role": 2, "is_admin": False}, limit=50, offset=10
        )

    @pytest.mark.asyncio
    async def test_list_members_empty_result(self, mock_member_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay members."""
        # Arrange
        mock_member_repository.list.return_value = []
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = ListMembersRequest()

        # Act
        result = await use_cases.list_members(request)

        # Assert
        assert result == []


class TestListByProject:
    """Tests para el caso de uso list_by_project."""

    @pytest.mark.asyncio
    async def test_list_by_project_success(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe listar members de un proyecto."""
        # Arrange
        mock_member_repository.list_by_project.return_value = [sample_member]
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Act
        result = await use_cases.list_by_project(project_id=1)

        # Assert
        assert result == [sample_member]
        mock_member_repository.list_by_project.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_by_project_empty(self, mock_member_repository: MagicMock) -> None:
        """Debe retornar lista vacía si el proyecto no tiene members."""
        # Arrange
        mock_member_repository.list_by_project.return_value = []
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Act
        result = await use_cases.list_by_project(project_id=1)

        # Assert
        assert result == []


class TestListAdmins:
    """Tests para el caso de uso list_admins."""

    @pytest.mark.asyncio
    async def test_list_admins_success(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe listar administradores de un proyecto."""
        # Arrange
        admin_member = Member(
            id=2,
            user_id=2,
            project_id=1,
            role_id=1,
            role_name="Admin",
            is_admin=True,
            is_owner=False,
            email="admin@example.com",
            full_name="Admin User",
            username="adminuser",
        )
        mock_member_repository.list_admins.return_value = [admin_member]
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Act
        result = await use_cases.list_admins(project_id=1)

        # Assert
        assert result == [admin_member]
        mock_member_repository.list_admins.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_admins_empty(self, mock_member_repository: MagicMock) -> None:
        """Debe retornar lista vacía si no hay administradores."""
        # Arrange
        mock_member_repository.list_admins.return_value = []
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Act
        result = await use_cases.list_admins(project_id=1)

        # Assert
        assert result == []


class TestListByRole:
    """Tests para el caso de uso list_by_role."""

    @pytest.mark.asyncio
    async def test_list_by_role_success(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe listar members con un rol específico."""
        # Arrange
        mock_member_repository.list_by_role.return_value = [sample_member]
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Act
        result = await use_cases.list_by_role(project_id=1, role_id=2)

        # Assert
        assert result == [sample_member]
        mock_member_repository.list_by_role.assert_called_once_with(1, 2)

    @pytest.mark.asyncio
    async def test_list_by_role_empty(self, mock_member_repository: MagicMock) -> None:
        """Debe retornar lista vacía si no hay members con ese rol."""
        # Arrange
        mock_member_repository.list_by_role.return_value = []
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Act
        result = await use_cases.list_by_role(project_id=1, role_id=99)

        # Assert
        assert result == []


class TestUpdateMember:
    """Tests para el caso de uso update_member."""

    @pytest.mark.asyncio
    async def test_update_member_success(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe actualizar el member exitosamente."""
        # Arrange
        mock_member_repository.get_by_id.return_value = sample_member
        updated_member = Member(
            id=1,
            user_id=1,
            project_id=1,
            role_id=2,
            role_name="Senior Developer",
            is_admin=False,
            is_owner=False,
            email="user@example.com",
            full_name="Test User",
            username="testuser",
        )
        mock_member_repository.update.return_value = updated_member
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = UpdateMemberRequest(member_id=1, role_id=2)

        # Act
        result = await use_cases.update_member(request)

        # Assert
        assert result == updated_member
        mock_member_repository.get_by_id.assert_called_once_with(1)
        mock_member_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_member_not_found(self, mock_member_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_member_repository.get_by_id.return_value = None
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = UpdateMemberRequest(member_id=999, role_id=2)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.update_member(request)

        mock_member_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_member_make_admin(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe convertir member en admin."""
        # Arrange
        sample_member.is_admin = False
        mock_member_repository.get_by_id.return_value = sample_member
        mock_member_repository.update.return_value = sample_member
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = UpdateMemberRequest(member_id=1, is_admin=True)

        # Act
        await use_cases.update_member(request)

        # Assert
        updated_member = mock_member_repository.update.call_args[0][0]
        assert updated_member.is_admin is True

    @pytest.mark.asyncio
    async def test_update_member_remove_admin(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe quitar permisos de admin."""
        # Arrange
        sample_member.is_admin = True
        mock_member_repository.get_by_id.return_value = sample_member
        mock_member_repository.update.return_value = sample_member
        use_cases = MemberUseCases(repository=mock_member_repository)
        request = UpdateMemberRequest(member_id=1, is_admin=False)

        # Act
        await use_cases.update_member(request)

        # Assert
        updated_member = mock_member_repository.update.call_args[0][0]
        assert updated_member.is_admin is False


class TestDeleteMember:
    """Tests para el caso de uso delete_member."""

    @pytest.mark.asyncio
    async def test_delete_member_success(self, mock_member_repository: MagicMock) -> None:
        """Debe eliminar el member exitosamente."""
        # Arrange
        mock_member_repository.delete.return_value = True
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Act
        result = await use_cases.delete_member(member_id=1)

        # Assert
        assert result is True
        mock_member_repository.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_member_not_found(self, mock_member_repository: MagicMock) -> None:
        """Debe retornar False cuando el member no existe."""
        # Arrange
        mock_member_repository.delete.return_value = False
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Act
        result = await use_cases.delete_member(member_id=999)

        # Assert
        assert result is False


class TestBulkCreateMembers:
    """Tests para el caso de uso bulk_create_members."""

    @pytest.mark.asyncio
    async def test_bulk_create_members_success(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe crear múltiples members exitosamente."""
        # Arrange
        member1 = sample_member
        member2 = Member(
            id=2,
            user_id=2,
            project_id=1,
            role_id=1,
            role_name="Developer",
            is_admin=False,
            is_owner=False,
            email="user2@example.com",
            full_name="Test User 2",
            username="testuser2",
        )
        mock_member_repository.bulk_create.return_value = [member1, member2]
        use_cases = MemberUseCases(repository=mock_member_repository)

        request = BulkCreateMembersRequest(
            project_id=1,
            members=[
                CreateMemberRequest(project_id=1, user_id=1, username="testuser1"),
                CreateMemberRequest(project_id=1, user_id=2, username="testuser2"),
            ],
        )

        # Act
        result = await use_cases.bulk_create_members(request)

        # Assert
        assert len(result) == 2
        mock_member_repository.bulk_create.assert_called_once()
        created_members = mock_member_repository.bulk_create.call_args[0][0]
        assert len(created_members) == 2
        assert created_members[0].project_id == 1
        assert created_members[1].project_id == 1

    @pytest.mark.asyncio
    async def test_bulk_create_members_with_admin(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe crear members incluyendo administradores."""
        # Arrange
        mock_member_repository.bulk_create.return_value = [sample_member]
        use_cases = MemberUseCases(repository=mock_member_repository)

        request = BulkCreateMembersRequest(
            project_id=1,
            members=[
                CreateMemberRequest(project_id=1, user_id=1, username="admin", is_admin=True),
            ],
        )

        # Act
        await use_cases.bulk_create_members(request)

        # Assert
        created_members = mock_member_repository.bulk_create.call_args[0][0]
        assert created_members[0].is_admin is True


class TestMakeAdmin:
    """Tests para el caso de uso make_admin."""

    @pytest.mark.asyncio
    async def test_make_admin_success(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe convertir member en administrador."""
        # Arrange
        sample_member.is_admin = False
        mock_member_repository.get_by_id.return_value = sample_member
        mock_member_repository.update.return_value = sample_member
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Act
        await use_cases.make_admin(member_id=1)

        # Assert
        mock_member_repository.get_by_id.assert_called_once_with(1)
        mock_member_repository.update.assert_called_once()
        updated_member = mock_member_repository.update.call_args[0][0]
        assert updated_member.is_admin is True

    @pytest.mark.asyncio
    async def test_make_admin_not_found(self, mock_member_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_member_repository.get_by_id.return_value = None
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.make_admin(member_id=999)

        mock_member_repository.update.assert_not_called()


class TestRemoveAdmin:
    """Tests para el caso de uso remove_admin."""

    @pytest.mark.asyncio
    async def test_remove_admin_success(
        self, mock_member_repository: MagicMock, sample_member: Member
    ) -> None:
        """Debe quitar permisos de administrador."""
        # Arrange
        sample_member.is_admin = True
        mock_member_repository.get_by_id.return_value = sample_member
        mock_member_repository.update.return_value = sample_member
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Act
        await use_cases.remove_admin(member_id=1)

        # Assert
        mock_member_repository.get_by_id.assert_called_once_with(1)
        mock_member_repository.update.assert_called_once()
        updated_member = mock_member_repository.update.call_args[0][0]
        assert updated_member.is_admin is False

    @pytest.mark.asyncio
    async def test_remove_admin_not_found(self, mock_member_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_member_repository.get_by_id.return_value = None
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.remove_admin(member_id=999)

        mock_member_repository.update.assert_not_called()


class TestMemberUseCasesInitialization:
    """Tests para la inicialización de MemberUseCases."""

    def test_initialization_with_repository(self, mock_member_repository: MagicMock) -> None:
        """Debe inicializarse correctamente con el repositorio."""
        # Act
        use_cases = MemberUseCases(repository=mock_member_repository)

        # Assert
        assert use_cases.repository == mock_member_repository
