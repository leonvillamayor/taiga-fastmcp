"""Unit tests for EpicRepositoryImpl."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.epic import Epic
from src.domain.exceptions import ResourceNotFoundError
from src.infrastructure.repositories.epic_repository_impl import EpicRepositoryImpl
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
def repository(mock_client: MagicMock) -> EpicRepositoryImpl:
    """Create an EpicRepositoryImpl instance."""
    return EpicRepositoryImpl(client=mock_client)


@pytest.fixture
def sample_epic_data() -> dict:
    """Create sample epic data from API."""
    return {
        "id": 1,
        "ref": 42,
        "project": 10,
        "subject": "Test Epic",
        "description": "Epic description",
        "status": 1,
        "color": "#ff0000",
        "version": 1,
    }


class TestEpicRepositoryInit:
    """Tests for EpicRepositoryImpl initialization."""

    def test_init_sets_correct_endpoint(self, repository: EpicRepositoryImpl) -> None:
        """Test that the repository is initialized with correct endpoint."""
        assert repository.endpoint == "epics"

    def test_init_sets_correct_entity_class(self, repository: EpicRepositoryImpl) -> None:
        """Test that the repository uses Epic entity class."""
        assert repository.entity_class == Epic


class TestGetByRef:
    """Tests for get_by_ref method."""

    @pytest.mark.asyncio
    async def test_get_by_ref_returns_epic_when_found(
        self,
        repository: EpicRepositoryImpl,
        mock_client: MagicMock,
        sample_epic_data: dict,
    ) -> None:
        """Test that get_by_ref returns an epic when found."""
        mock_client.get.return_value = sample_epic_data

        epic = await repository.get_by_ref(project_id=10, ref=42)

        assert epic is not None
        assert epic.id == 1
        assert epic.ref == 42
        assert epic.subject == "Test Epic"
        mock_client.get.assert_called_once_with("epics/by_ref", params={"project": 10, "ref": 42})

    @pytest.mark.asyncio
    async def test_get_by_ref_returns_none_when_not_found(
        self, repository: EpicRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_by_ref returns None when epic is not found."""
        mock_client.get.side_effect = Exception("Not found")

        epic = await repository.get_by_ref(project_id=10, ref=999)

        assert epic is None

    @pytest.mark.asyncio
    async def test_get_by_ref_returns_none_for_list_response(
        self, repository: EpicRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_by_ref returns None for list response."""
        mock_client.get.return_value = [{"id": 1}]

        epic = await repository.get_by_ref(project_id=10, ref=42)

        assert epic is None


class TestBulkCreate:
    """Tests for bulk_create method."""

    @pytest.mark.asyncio
    async def test_bulk_create_creates_multiple_epics(
        self, repository: EpicRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that bulk_create creates multiple epics."""
        epics = [
            Epic(project=10, subject="Epic 1"),
            Epic(project=10, subject="Epic 2"),
        ]
        mock_client.post.return_value = [
            {"id": 1, "project": 10, "subject": "Epic 1", "version": 1},
            {"id": 2, "project": 10, "subject": "Epic 2", "version": 1},
        ]

        result = await repository.bulk_create(epics)

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_create_returns_empty_for_empty_input(
        self, repository: EpicRepositoryImpl
    ) -> None:
        """Test that bulk_create returns empty list for empty input."""
        result = await repository.bulk_create([])

        assert result == []

    @pytest.mark.asyncio
    async def test_bulk_create_returns_empty_on_error(
        self, repository: EpicRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that bulk_create returns empty list on error."""
        epics = [Epic(project=10, subject="Epic 1")]
        mock_client.post.side_effect = Exception("API error")

        result = await repository.bulk_create(epics)

        assert result == []


class TestGetFilters:
    """Tests for get_filters method."""

    @pytest.mark.asyncio
    async def test_get_filters_returns_filter_options(
        self, repository: EpicRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_filters returns filter options."""
        mock_client.get.return_value = {
            "statuses": [{"id": 1, "name": "New"}],
            "assigned_to": [{"id": 1, "username": "user1"}],
        }

        filters = await repository.get_filters(project_id=10)

        assert "statuses" in filters
        assert "assigned_to" in filters
        mock_client.get.assert_called_once_with("epics/filters_data", params={"project": 10})

    @pytest.mark.asyncio
    async def test_get_filters_returns_empty_on_error(
        self, repository: EpicRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_filters returns empty dict on error."""
        mock_client.get.side_effect = Exception("API error")

        filters = await repository.get_filters(project_id=10)

        assert filters == {}


class TestUpvote:
    """Tests for upvote method."""

    @pytest.mark.asyncio
    async def test_upvote_returns_updated_epic(
        self,
        repository: EpicRepositoryImpl,
        mock_client: MagicMock,
        sample_epic_data: dict,
    ) -> None:
        """Test that upvote returns the updated epic."""
        mock_client.post.return_value = {}
        mock_client.get.return_value = sample_epic_data

        epic = await repository.upvote(epic_id=1)

        assert epic.id == 1
        mock_client.post.assert_called_once_with("epics/1/upvote", data={})

    @pytest.mark.asyncio
    async def test_upvote_raises_not_found_error(
        self, repository: EpicRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that upvote raises ResourceNotFoundError when epic not found."""
        mock_client.post.return_value = {}
        mock_client.get.return_value = None  # Epic not found after upvote

        with pytest.raises(ResourceNotFoundError):
            await repository.upvote(epic_id=999)


class TestDownvote:
    """Tests for downvote method."""

    @pytest.mark.asyncio
    async def test_downvote_returns_updated_epic(
        self,
        repository: EpicRepositoryImpl,
        mock_client: MagicMock,
        sample_epic_data: dict,
    ) -> None:
        """Test that downvote returns the updated epic."""
        mock_client.post.return_value = {}
        mock_client.get.return_value = sample_epic_data

        epic = await repository.downvote(epic_id=1)

        assert epic.id == 1
        mock_client.post.assert_called_once_with("epics/1/downvote", data={})

    @pytest.mark.asyncio
    async def test_downvote_raises_not_found_error(
        self, repository: EpicRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that downvote raises ResourceNotFoundError when epic not found."""
        mock_client.post.return_value = {}
        mock_client.get.return_value = None

        with pytest.raises(ResourceNotFoundError):
            await repository.downvote(epic_id=999)


class TestWatch:
    """Tests for watch method."""

    @pytest.mark.asyncio
    async def test_watch_returns_updated_epic(
        self,
        repository: EpicRepositoryImpl,
        mock_client: MagicMock,
        sample_epic_data: dict,
    ) -> None:
        """Test that watch returns the updated epic."""
        mock_client.post.return_value = {}
        mock_client.get.return_value = sample_epic_data

        epic = await repository.watch(epic_id=1)

        assert epic.id == 1
        mock_client.post.assert_called_once_with("epics/1/watch", data={})


class TestUnwatch:
    """Tests for unwatch method."""

    @pytest.mark.asyncio
    async def test_unwatch_returns_updated_epic(
        self,
        repository: EpicRepositoryImpl,
        mock_client: MagicMock,
        sample_epic_data: dict,
    ) -> None:
        """Test that unwatch returns the updated epic."""
        mock_client.post.return_value = {}
        mock_client.get.return_value = sample_epic_data

        epic = await repository.unwatch(epic_id=1)

        assert epic.id == 1
        mock_client.post.assert_called_once_with("epics/1/unwatch", data={})
