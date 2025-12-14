"""Unit tests for TaskRepositoryImpl."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.task import Task
from src.infrastructure.repositories.task_repository_impl import TaskRepositoryImpl
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
def repository(mock_client: MagicMock) -> TaskRepositoryImpl:
    """Create a TaskRepositoryImpl instance."""
    return TaskRepositoryImpl(client=mock_client)


@pytest.fixture
def sample_task_data() -> dict:
    """Create sample task data from API."""
    return {
        "id": 1,
        "ref": 15,
        "subject": "Test Task",
        "description": "A test task",
        "project": 5,
        "user_story": 10,
        "assigned_to": 3,
        "milestone": 2,
        "status": 1,
        "is_closed": False,
        "version": 1,
    }


class TestTaskRepositoryInit:
    """Tests for TaskRepositoryImpl initialization."""

    def test_init_sets_correct_endpoint(self, repository: TaskRepositoryImpl) -> None:
        """Test that the repository is initialized with correct endpoint."""
        assert repository.endpoint == "tasks"

    def test_init_sets_correct_entity_class(self, repository: TaskRepositoryImpl) -> None:
        """Test that the repository uses Task entity class."""
        assert repository.entity_class == Task


class TestToEntity:
    """Tests for _to_entity field mapping."""

    def test_to_entity_maps_project_to_project_id(
        self, repository: TaskRepositoryImpl, sample_task_data: dict
    ) -> None:
        """Test that API 'project' field is mapped to 'project_id'."""
        entity = repository._to_entity(sample_task_data)
        assert entity.project_id == 5

    def test_to_entity_maps_user_story_to_user_story_id(
        self, repository: TaskRepositoryImpl, sample_task_data: dict
    ) -> None:
        """Test that API 'user_story' field is mapped to 'user_story_id'."""
        entity = repository._to_entity(sample_task_data)
        assert entity.user_story_id == 10

    def test_to_entity_maps_assigned_to_to_assigned_to_id(
        self, repository: TaskRepositoryImpl, sample_task_data: dict
    ) -> None:
        """Test that API 'assigned_to' field is mapped to 'assigned_to_id'."""
        entity = repository._to_entity(sample_task_data)
        assert entity.assigned_to_id == 3

    def test_to_entity_maps_milestone_to_milestone_id(
        self, repository: TaskRepositoryImpl, sample_task_data: dict
    ) -> None:
        """Test that API 'milestone' field is mapped to 'milestone_id'."""
        entity = repository._to_entity(sample_task_data)
        assert entity.milestone_id == 2


class TestToDict:
    """Tests for _to_dict field mapping."""

    def test_to_dict_maps_project_id_to_project(self, repository: TaskRepositoryImpl) -> None:
        """Test that entity 'project_id' field is mapped to 'project'."""
        entity = Task(id=1, subject="Test", project_id=5, version=1)
        data = repository._to_dict(entity)
        assert "project" in data
        assert data["project"] == 5
        assert "project_id" not in data

    def test_to_dict_maps_user_story_id_to_user_story(self, repository: TaskRepositoryImpl) -> None:
        """Test that entity 'user_story_id' field is mapped to 'user_story'."""
        entity = Task(id=1, subject="Test", project_id=5, user_story_id=10, version=1)
        data = repository._to_dict(entity)
        assert "user_story" in data
        assert data["user_story"] == 10
        assert "user_story_id" not in data


class TestGetByRef:
    """Tests for get_by_ref method."""

    @pytest.mark.asyncio
    async def test_get_by_ref_returns_task_when_found(
        self,
        repository: TaskRepositoryImpl,
        mock_client: MagicMock,
        sample_task_data: dict,
    ) -> None:
        """Test that get_by_ref returns a task when found."""
        mock_client.get.return_value = sample_task_data

        task = await repository.get_by_ref(project_id=5, ref=15)

        assert task is not None
        assert task.id == 1
        assert task.ref == 15
        mock_client.get.assert_called_once_with("tasks/by_ref", params={"project": 5, "ref": 15})

    @pytest.mark.asyncio
    async def test_get_by_ref_returns_none_when_not_found(
        self, repository: TaskRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_by_ref returns None when not found."""
        mock_client.get.side_effect = Exception("Not found")

        task = await repository.get_by_ref(project_id=5, ref=999)

        assert task is None


class TestListByUserStory:
    """Tests for list_by_user_story method."""

    @pytest.mark.asyncio
    async def test_list_by_user_story_returns_tasks(
        self,
        repository: TaskRepositoryImpl,
        mock_client: MagicMock,
        sample_task_data: dict,
    ) -> None:
        """Test that list_by_user_story returns tasks for user story."""
        mock_client.get.return_value = [sample_task_data]

        tasks = await repository.list_by_user_story(user_story_id=10)

        assert len(tasks) == 1
        mock_client.get.assert_called_once_with("tasks", params={"user_story": 10})


class TestListByMilestone:
    """Tests for list_by_milestone method."""

    @pytest.mark.asyncio
    async def test_list_by_milestone_returns_tasks(
        self,
        repository: TaskRepositoryImpl,
        mock_client: MagicMock,
        sample_task_data: dict,
    ) -> None:
        """Test that list_by_milestone returns tasks in milestone."""
        mock_client.get.return_value = [sample_task_data]

        tasks = await repository.list_by_milestone(milestone_id=2)

        assert len(tasks) == 1
        mock_client.get.assert_called_once_with("tasks", params={"milestone": 2})


class TestListByStatus:
    """Tests for list_by_status method."""

    @pytest.mark.asyncio
    async def test_list_by_status_returns_tasks(
        self,
        repository: TaskRepositoryImpl,
        mock_client: MagicMock,
        sample_task_data: dict,
    ) -> None:
        """Test that list_by_status returns tasks with status."""
        mock_client.get.return_value = [sample_task_data]

        tasks = await repository.list_by_status(project_id=5, status_id=1)

        assert len(tasks) == 1
        mock_client.get.assert_called_once_with("tasks", params={"project": 5, "status": 1})


class TestListUnassigned:
    """Tests for list_unassigned method."""

    @pytest.mark.asyncio
    async def test_list_unassigned_returns_tasks_without_assignee(
        self,
        repository: TaskRepositoryImpl,
        mock_client: MagicMock,
        sample_task_data: dict,
    ) -> None:
        """Test that list_unassigned returns tasks without assignee."""
        sample_task_data["assigned_to"] = None
        mock_client.get.return_value = [sample_task_data]

        tasks = await repository.list_unassigned(project_id=5)

        assert len(tasks) == 1
        mock_client.get.assert_called_once_with(
            "tasks", params={"project": 5, "assigned_to__isnull": True}
        )


class TestBulkCreate:
    """Tests for bulk_create method."""

    @pytest.mark.asyncio
    async def test_bulk_create_creates_multiple_tasks(
        self,
        repository: TaskRepositoryImpl,
        mock_client: MagicMock,
        sample_task_data: dict,
    ) -> None:
        """Test that bulk_create creates multiple tasks."""
        mock_client.post.return_value = [sample_task_data]
        tasks = [
            Task(subject="Task 1", project_id=5),
            Task(subject="Task 2", project_id=5),
        ]

        created = await repository.bulk_create(tasks)

        assert len(created) == 1
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "tasks/bulk_create"

    @pytest.mark.asyncio
    async def test_bulk_create_returns_empty_for_empty_input(
        self, repository: TaskRepositoryImpl
    ) -> None:
        """Test that bulk_create returns empty list for empty input."""
        created = await repository.bulk_create([])
        assert created == []

    @pytest.mark.asyncio
    async def test_bulk_create_returns_empty_on_error(
        self, repository: TaskRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that bulk_create returns empty list on error."""
        mock_client.post.side_effect = Exception("API error")
        tasks = [Task(subject="Task 1", project_id=5)]

        created = await repository.bulk_create(tasks)

        assert created == []


class TestGetFilters:
    """Tests for get_filters method."""

    @pytest.mark.asyncio
    async def test_get_filters_returns_filter_options(
        self, repository: TaskRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_filters returns filter options."""
        mock_client.get.return_value = {"statuses": [{"id": 1, "name": "New"}]}

        filters = await repository.get_filters(project_id=5)

        assert "statuses" in filters
        mock_client.get.assert_called_once_with("tasks/filters_data", params={"project": 5})

    @pytest.mark.asyncio
    async def test_get_filters_returns_empty_on_error(
        self, repository: TaskRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_filters returns empty dict on error."""
        mock_client.get.side_effect = Exception("API error")

        filters = await repository.get_filters(project_id=5)

        assert filters == {}
