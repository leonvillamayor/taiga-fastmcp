"""Unit tests for UserStoryRepositoryImpl."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.user_story import UserStory
from src.domain.exceptions import ResourceNotFoundError
from src.infrastructure.repositories.user_story_repository_impl import (
    UserStoryRepositoryImpl,
)
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
def repository(mock_client: MagicMock) -> UserStoryRepositoryImpl:
    """Create a UserStoryRepositoryImpl instance."""
    return UserStoryRepositoryImpl(client=mock_client)


@pytest.fixture
def sample_userstory_data() -> dict:
    """Create sample user story data from API."""
    return {
        "id": 1,
        "ref": 10,
        "subject": "Test User Story",
        "description": "A test user story",
        "project": 5,
        "assigned_to": 3,
        "milestone": 2,
        "status": 1,
        "is_closed": False,
        "version": 1,
    }


class TestUserStoryRepositoryInit:
    """Tests for UserStoryRepositoryImpl initialization."""

    def test_init_sets_correct_endpoint(self, repository: UserStoryRepositoryImpl) -> None:
        """Test that the repository is initialized with correct endpoint."""
        assert repository.endpoint == "userstories"

    def test_init_sets_correct_entity_class(self, repository: UserStoryRepositoryImpl) -> None:
        """Test that the repository uses UserStory entity class."""
        assert repository.entity_class == UserStory


class TestToEntity:
    """Tests for _to_entity field mapping."""

    @pytest.mark.asyncio
    async def test_to_entity_maps_project_to_project_id(
        self, repository: UserStoryRepositoryImpl, sample_userstory_data: dict
    ) -> None:
        """Test that API 'project' field is mapped to 'project_id'."""
        entity = repository._to_entity(sample_userstory_data)
        assert entity.project_id == 5

    @pytest.mark.asyncio
    async def test_to_entity_maps_assigned_to_to_assigned_to_id(
        self, repository: UserStoryRepositoryImpl, sample_userstory_data: dict
    ) -> None:
        """Test that API 'assigned_to' field is mapped to 'assigned_to_id'."""
        entity = repository._to_entity(sample_userstory_data)
        assert entity.assigned_to_id == 3

    @pytest.mark.asyncio
    async def test_to_entity_maps_milestone_to_milestone_id(
        self, repository: UserStoryRepositoryImpl, sample_userstory_data: dict
    ) -> None:
        """Test that API 'milestone' field is mapped to 'milestone_id'."""
        entity = repository._to_entity(sample_userstory_data)
        assert entity.milestone_id == 2


class TestToDict:
    """Tests for _to_dict field mapping."""

    def test_to_dict_maps_project_id_to_project(self, repository: UserStoryRepositoryImpl) -> None:
        """Test that entity 'project_id' field is mapped to 'project'."""
        entity = UserStory(id=1, subject="Test", project_id=5, version=1)
        data = repository._to_dict(entity)
        assert "project" in data
        assert data["project"] == 5
        assert "project_id" not in data

    def test_to_dict_maps_assigned_to_id_to_assigned_to(
        self, repository: UserStoryRepositoryImpl
    ) -> None:
        """Test that entity 'assigned_to_id' field is mapped to 'assigned_to'."""
        entity = UserStory(id=1, subject="Test", project_id=5, assigned_to_id=3, version=1)
        data = repository._to_dict(entity)
        assert "assigned_to" in data
        assert data["assigned_to"] == 3
        assert "assigned_to_id" not in data

    def test_to_dict_maps_milestone_id_to_milestone(
        self, repository: UserStoryRepositoryImpl
    ) -> None:
        """Test that entity 'milestone_id' field is mapped to 'milestone'."""
        entity = UserStory(id=1, subject="Test", project_id=5, milestone_id=2, version=1)
        data = repository._to_dict(entity)
        assert "milestone" in data
        assert data["milestone"] == 2
        assert "milestone_id" not in data


class TestGetByRef:
    """Tests for get_by_ref method."""

    @pytest.mark.asyncio
    async def test_get_by_ref_returns_userstory_when_found(
        self,
        repository: UserStoryRepositoryImpl,
        mock_client: MagicMock,
        sample_userstory_data: dict,
    ) -> None:
        """Test that get_by_ref returns a user story when found."""
        mock_client.get.return_value = sample_userstory_data

        userstory = await repository.get_by_ref(project_id=5, ref=10)

        assert userstory is not None
        assert userstory.id == 1
        assert userstory.ref == 10
        mock_client.get.assert_called_once_with(
            "userstories/by_ref", params={"project": 5, "ref": 10}
        )

    @pytest.mark.asyncio
    async def test_get_by_ref_returns_none_when_not_found(
        self, repository: UserStoryRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_by_ref returns None when not found."""
        mock_client.get.side_effect = Exception("Not found")

        userstory = await repository.get_by_ref(project_id=5, ref=999)

        assert userstory is None


class TestListByMilestone:
    """Tests for list_by_milestone method."""

    @pytest.mark.asyncio
    async def test_list_by_milestone_returns_userstories(
        self,
        repository: UserStoryRepositoryImpl,
        mock_client: MagicMock,
        sample_userstory_data: dict,
    ) -> None:
        """Test that list_by_milestone returns user stories in milestone."""
        mock_client.get.return_value = [sample_userstory_data]

        userstories = await repository.list_by_milestone(milestone_id=2)

        assert len(userstories) == 1
        mock_client.get.assert_called_once_with("userstories", params={"milestone": 2})


class TestListByStatus:
    """Tests for list_by_status method."""

    @pytest.mark.asyncio
    async def test_list_by_status_returns_userstories(
        self,
        repository: UserStoryRepositoryImpl,
        mock_client: MagicMock,
        sample_userstory_data: dict,
    ) -> None:
        """Test that list_by_status returns user stories with status."""
        mock_client.get.return_value = [sample_userstory_data]

        userstories = await repository.list_by_status(project_id=5, status_id=1)

        assert len(userstories) == 1
        mock_client.get.assert_called_once_with("userstories", params={"project": 5, "status": 1})


class TestListBacklog:
    """Tests for list_backlog method."""

    @pytest.mark.asyncio
    async def test_list_backlog_returns_userstories_without_milestone(
        self,
        repository: UserStoryRepositoryImpl,
        mock_client: MagicMock,
        sample_userstory_data: dict,
    ) -> None:
        """Test that list_backlog returns user stories without milestone."""
        sample_userstory_data["milestone"] = None
        mock_client.get.return_value = [sample_userstory_data]

        userstories = await repository.list_backlog(project_id=5)

        assert len(userstories) == 1
        mock_client.get.assert_called_once_with(
            "userstories", params={"project": 5, "milestone__isnull": True}
        )


class TestBulkCreate:
    """Tests for bulk_create method."""

    @pytest.mark.asyncio
    async def test_bulk_create_creates_multiple_userstories(
        self,
        repository: UserStoryRepositoryImpl,
        mock_client: MagicMock,
        sample_userstory_data: dict,
    ) -> None:
        """Test that bulk_create creates multiple user stories."""
        mock_client.post.return_value = [sample_userstory_data]
        stories = [
            UserStory(subject="Story 1", project_id=5),
            UserStory(subject="Story 2", project_id=5),
        ]

        created = await repository.bulk_create(stories)

        assert len(created) == 1
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "userstories/bulk_create"

    @pytest.mark.asyncio
    async def test_bulk_create_returns_empty_for_empty_input(
        self, repository: UserStoryRepositoryImpl
    ) -> None:
        """Test that bulk_create returns empty list for empty input."""
        created = await repository.bulk_create([])
        assert created == []

    @pytest.mark.asyncio
    async def test_bulk_create_returns_empty_on_error(
        self, repository: UserStoryRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that bulk_create returns empty list on error."""
        mock_client.post.side_effect = Exception("API error")
        stories = [UserStory(subject="Story 1", project_id=5)]

        created = await repository.bulk_create(stories)

        assert created == []


class TestBulkUpdate:
    """Tests for bulk_update method."""

    @pytest.mark.asyncio
    async def test_bulk_update_updates_multiple_userstories(
        self,
        repository: UserStoryRepositoryImpl,
        mock_client: MagicMock,
        sample_userstory_data: dict,
    ) -> None:
        """Test that bulk_update updates multiple user stories."""
        mock_client.post.return_value = [sample_userstory_data]

        updated = await repository.bulk_update([1, 2], {"status": 2})

        assert len(updated) == 1
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_update_returns_empty_for_empty_ids(
        self, repository: UserStoryRepositoryImpl
    ) -> None:
        """Test that bulk_update returns empty list for empty IDs."""
        updated = await repository.bulk_update([], {"status": 2})
        assert updated == []

    @pytest.mark.asyncio
    async def test_bulk_update_maps_field_names(
        self,
        repository: UserStoryRepositoryImpl,
        mock_client: MagicMock,
    ) -> None:
        """Test that bulk_update maps entity field names to API fields."""
        mock_client.post.return_value = []

        await repository.bulk_update([1], {"milestone_id": 5})

        call_args = mock_client.post.call_args
        assert "milestone" in call_args[1]["data"]
        assert "milestone_id" not in call_args[1]["data"]


class TestMoveToMilestone:
    """Tests for move_to_milestone method."""

    @pytest.mark.asyncio
    async def test_move_to_milestone_updates_story(
        self,
        repository: UserStoryRepositoryImpl,
        mock_client: MagicMock,
        sample_userstory_data: dict,
    ) -> None:
        """Test that move_to_milestone moves story to new milestone."""
        mock_client.get.return_value = sample_userstory_data
        mock_client.patch.return_value = {**sample_userstory_data, "milestone": 3}

        updated = await repository.move_to_milestone(story_id=1, milestone_id=3)

        assert updated.milestone_id == 3
        mock_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_move_to_milestone_raises_when_not_found(
        self, repository: UserStoryRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that move_to_milestone raises error when story not found."""
        mock_client.get.return_value = None

        with pytest.raises(ResourceNotFoundError):
            await repository.move_to_milestone(story_id=999, milestone_id=3)


class TestGetFilters:
    """Tests for get_filters method."""

    @pytest.mark.asyncio
    async def test_get_filters_returns_filter_options(
        self, repository: UserStoryRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_filters returns filter options."""
        mock_client.get.return_value = {"statuses": [{"id": 1, "name": "New"}]}

        filters = await repository.get_filters(project_id=5)

        assert "statuses" in filters
        mock_client.get.assert_called_once_with("userstories/filters_data", params={"project": 5})

    @pytest.mark.asyncio
    async def test_get_filters_returns_empty_on_error(
        self, repository: UserStoryRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_filters returns empty dict on error."""
        mock_client.get.side_effect = Exception("API error")

        filters = await repository.get_filters(project_id=5)

        assert filters == {}
