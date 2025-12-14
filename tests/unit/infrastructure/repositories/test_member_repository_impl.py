"""Unit tests for MemberRepositoryImpl."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.member import Member
from src.infrastructure.repositories.member_repository_impl import MemberRepositoryImpl
from src.taiga_client import TaigaAPIClient


@pytest.fixture
def mock_client() -> MagicMock:
    """Create a mock TaigaAPIClient."""
    client = MagicMock(spec=TaigaAPIClient)
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.patch = AsyncMock()
    client.delete = AsyncMock()
    return client


@pytest.fixture
def repository(mock_client: MagicMock) -> MemberRepositoryImpl:
    """Create a MemberRepositoryImpl instance."""
    return MemberRepositoryImpl(client=mock_client)


@pytest.fixture
def sample_member_data() -> dict:
    """Create sample member data from API."""
    return {
        "id": 1,
        "project": 5,
        "user": 10,
        "role": 2,
        "full_name": "John Doe",
        "username": "johndoe",
        "email": "john@example.com",
        "is_admin": False,
        "version": 1,
    }


class TestMemberRepositoryInit:
    """Tests for MemberRepositoryImpl initialization."""

    def test_init_sets_correct_endpoint(self, repository: MemberRepositoryImpl) -> None:
        """Test that the repository is initialized with correct endpoint."""
        assert repository.endpoint == "memberships"

    def test_init_sets_correct_entity_class(self, repository: MemberRepositoryImpl) -> None:
        """Test that the repository uses Member entity class."""
        assert repository.entity_class == Member


class TestToEntity:
    """Tests for _to_entity field mapping."""

    def test_to_entity_maps_project_to_project_id(
        self, repository: MemberRepositoryImpl, sample_member_data: dict
    ) -> None:
        """Test that API 'project' field is mapped to 'project_id'."""
        entity = repository._to_entity(sample_member_data)
        assert entity.project_id == 5

    def test_to_entity_maps_user_to_user_id(
        self, repository: MemberRepositoryImpl, sample_member_data: dict
    ) -> None:
        """Test that API 'user' field is mapped to 'user_id'."""
        entity = repository._to_entity(sample_member_data)
        assert entity.user_id == 10

    def test_to_entity_maps_role_to_role_id(
        self, repository: MemberRepositoryImpl, sample_member_data: dict
    ) -> None:
        """Test that API 'role' field is mapped to 'role_id'."""
        entity = repository._to_entity(sample_member_data)
        assert entity.role_id == 2

    def test_to_entity_preserves_other_fields(
        self, repository: MemberRepositoryImpl, sample_member_data: dict
    ) -> None:
        """Test that other fields are preserved correctly."""
        entity = repository._to_entity(sample_member_data)
        assert entity.full_name == "John Doe"
        assert entity.username == "johndoe"
        assert entity.is_admin is False


class TestToDict:
    """Tests for _to_dict field mapping."""

    def test_to_dict_maps_project_id_to_project(self, repository: MemberRepositoryImpl) -> None:
        """Test that entity 'project_id' field is mapped to 'project'."""
        entity = Member(id=1, project_id=5, user_id=10, username="johndoe", version=1)
        data = repository._to_dict(entity)
        assert "project" in data
        assert data["project"] == 5
        assert "project_id" not in data

    def test_to_dict_maps_user_id_to_user(self, repository: MemberRepositoryImpl) -> None:
        """Test that entity 'user_id' field is mapped to 'user'."""
        entity = Member(id=1, project_id=5, user_id=10, username="johndoe", version=1)
        data = repository._to_dict(entity)
        assert "user" in data
        assert data["user"] == 10
        assert "user_id" not in data

    def test_to_dict_maps_role_id_to_role(self, repository: MemberRepositoryImpl) -> None:
        """Test that entity 'role_id' field is mapped to 'role'."""
        entity = Member(id=1, project_id=5, user_id=10, role_id=2, username="johndoe", version=1)
        data = repository._to_dict(entity)
        assert "role" in data
        assert data["role"] == 2
        assert "role_id" not in data


class TestListByProject:
    """Tests for list_by_project method."""

    @pytest.mark.asyncio
    async def test_list_by_project_returns_members(
        self,
        repository: MemberRepositoryImpl,
        mock_client: MagicMock,
        sample_member_data: dict,
    ) -> None:
        """Test that list_by_project returns members for project."""
        mock_client.get.return_value = [sample_member_data]

        members = await repository.list_by_project(project_id=5)

        assert len(members) == 1
        mock_client.get.assert_called_once_with("memberships", params={"project": 5})


class TestGetByUser:
    """Tests for get_by_user method."""

    @pytest.mark.asyncio
    async def test_get_by_user_returns_member_when_found(
        self,
        repository: MemberRepositoryImpl,
        mock_client: MagicMock,
        sample_member_data: dict,
    ) -> None:
        """Test that get_by_user returns member when found."""
        mock_client.get.return_value = [sample_member_data]

        member = await repository.get_by_user(project_id=5, user_id=10)

        assert member is not None
        assert member.user_id == 10
        mock_client.get.assert_called_once_with("memberships", params={"project": 5, "user": 10})

    @pytest.mark.asyncio
    async def test_get_by_user_returns_none_when_not_found(
        self, repository: MemberRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_by_user returns None when not found."""
        mock_client.get.return_value = []

        member = await repository.get_by_user(project_id=5, user_id=999)

        assert member is None


class TestListAdmins:
    """Tests for list_admins method."""

    @pytest.mark.asyncio
    async def test_list_admins_returns_only_admins(
        self,
        repository: MemberRepositoryImpl,
        mock_client: MagicMock,
        sample_member_data: dict,
    ) -> None:
        """Test that list_admins returns only admin members."""
        admin_data = dict(sample_member_data)
        admin_data["id"] = 2
        admin_data["is_admin"] = True
        mock_client.get.return_value = [sample_member_data, admin_data]

        admins = await repository.list_admins(project_id=5)

        assert len(admins) == 1
        assert admins[0].is_admin is True

    @pytest.mark.asyncio
    async def test_list_admins_returns_empty_when_no_admins(
        self,
        repository: MemberRepositoryImpl,
        mock_client: MagicMock,
        sample_member_data: dict,
    ) -> None:
        """Test that list_admins returns empty list when no admins."""
        mock_client.get.return_value = [sample_member_data]

        admins = await repository.list_admins(project_id=5)

        assert admins == []


class TestListByRole:
    """Tests for list_by_role method."""

    @pytest.mark.asyncio
    async def test_list_by_role_returns_members_with_role(
        self,
        repository: MemberRepositoryImpl,
        mock_client: MagicMock,
        sample_member_data: dict,
    ) -> None:
        """Test that list_by_role returns members with specific role."""
        mock_client.get.return_value = [sample_member_data]

        members = await repository.list_by_role(project_id=5, role_id=2)

        assert len(members) == 1
        mock_client.get.assert_called_once_with("memberships", params={"project": 5, "role": 2})


class TestBulkCreate:
    """Tests for bulk_create method."""

    @pytest.mark.asyncio
    async def test_bulk_create_creates_multiple_members(
        self,
        repository: MemberRepositoryImpl,
        mock_client: MagicMock,
        sample_member_data: dict,
    ) -> None:
        """Test that bulk_create creates multiple members."""
        mock_client.post.return_value = [sample_member_data]
        members = [
            Member(project_id=5, user_id=10, username="user1"),
            Member(project_id=5, user_id=11, username="user2"),
        ]

        created = await repository.bulk_create(members)

        assert len(created) == 1
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "memberships/bulk_create"

    @pytest.mark.asyncio
    async def test_bulk_create_returns_empty_for_empty_input(
        self, repository: MemberRepositoryImpl
    ) -> None:
        """Test that bulk_create returns empty list for empty input."""
        created = await repository.bulk_create([])
        assert created == []

    @pytest.mark.asyncio
    async def test_bulk_create_returns_empty_on_error(
        self, repository: MemberRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that bulk_create returns empty list on error."""
        mock_client.post.side_effect = Exception("API error")
        members = [Member(project_id=5, user_id=10, username="user1")]

        created = await repository.bulk_create(members)

        assert created == []
