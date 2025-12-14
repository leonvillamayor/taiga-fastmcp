"""Unit tests for MilestoneRepositoryImpl."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.milestone import Milestone
from src.domain.exceptions import ResourceNotFoundError
from src.infrastructure.repositories.milestone_repository_impl import (
    MilestoneRepositoryImpl,
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
def repository(mock_client: MagicMock) -> MilestoneRepositoryImpl:
    """Create a MilestoneRepositoryImpl instance."""
    return MilestoneRepositoryImpl(client=mock_client)


@pytest.fixture
def sample_milestone_data() -> dict:
    """Create sample milestone data from API."""
    return {
        "id": 1,
        "name": "Sprint 1",
        "slug": "sprint-1",
        "project": 5,
        "estimated_start": "2024-01-01",
        "estimated_finish": "2024-01-14",
        "is_closed": False,
        "disponibility": 1.0,
        "order": 1,
        "version": 1,
    }


class TestMilestoneRepositoryInit:
    """Tests for MilestoneRepositoryImpl initialization."""

    def test_init_sets_correct_endpoint(self, repository: MilestoneRepositoryImpl) -> None:
        """Test that the repository is initialized with correct endpoint."""
        assert repository.endpoint == "milestones"

    def test_init_sets_correct_entity_class(self, repository: MilestoneRepositoryImpl) -> None:
        """Test that the repository uses Milestone entity class."""
        assert repository.entity_class == Milestone


class TestToEntity:
    """Tests for _to_entity field mapping."""

    def test_to_entity_maps_project_to_project_id(
        self, repository: MilestoneRepositoryImpl, sample_milestone_data: dict
    ) -> None:
        """Test that API 'project' field is mapped to 'project_id'."""
        entity = repository._to_entity(sample_milestone_data)
        assert entity.project_id == 5

    def test_to_entity_preserves_dates(
        self, repository: MilestoneRepositoryImpl, sample_milestone_data: dict
    ) -> None:
        """Test that dates are preserved correctly."""
        entity = repository._to_entity(sample_milestone_data)
        assert entity.estimated_start == date(2024, 1, 1)
        assert entity.estimated_finish == date(2024, 1, 14)


class TestToDict:
    """Tests for _to_dict field mapping."""

    def test_to_dict_maps_project_id_to_project(self, repository: MilestoneRepositoryImpl) -> None:
        """Test that entity 'project_id' field is mapped to 'project'."""
        entity = Milestone(id=1, name="Sprint 1", project_id=5, version=1)
        data = repository._to_dict(entity)
        assert "project" in data
        assert data["project"] == 5
        assert "project_id" not in data

    def test_to_dict_converts_dates_to_iso_strings(
        self, repository: MilestoneRepositoryImpl
    ) -> None:
        """Test that date objects are converted to ISO strings."""
        entity = Milestone(
            id=1,
            name="Sprint 1",
            project_id=5,
            estimated_start=date(2024, 1, 1),
            estimated_finish=date(2024, 1, 14),
            version=1,
        )
        data = repository._to_dict(entity)
        assert data["estimated_start"] == "2024-01-01"
        assert data["estimated_finish"] == "2024-01-14"


class TestListByProject:
    """Tests for list_by_project method."""

    @pytest.mark.asyncio
    async def test_list_by_project_returns_milestones(
        self,
        repository: MilestoneRepositoryImpl,
        mock_client: MagicMock,
        sample_milestone_data: dict,
    ) -> None:
        """Test that list_by_project returns milestones for project."""
        mock_client.get.return_value = [sample_milestone_data]

        milestones = await repository.list_by_project(project_id=5)

        assert len(milestones) == 1
        mock_client.get.assert_called_once_with("milestones", params={"project": 5})


class TestListOpen:
    """Tests for list_open method."""

    @pytest.mark.asyncio
    async def test_list_open_returns_open_milestones(
        self,
        repository: MilestoneRepositoryImpl,
        mock_client: MagicMock,
        sample_milestone_data: dict,
    ) -> None:
        """Test that list_open returns only open milestones."""
        mock_client.get.return_value = [sample_milestone_data]

        milestones = await repository.list_open(project_id=5)

        assert len(milestones) == 1
        mock_client.get.assert_called_once_with(
            "milestones", params={"project": 5, "closed": False}
        )


class TestListClosed:
    """Tests for list_closed method."""

    @pytest.mark.asyncio
    async def test_list_closed_returns_closed_milestones(
        self,
        repository: MilestoneRepositoryImpl,
        mock_client: MagicMock,
        sample_milestone_data: dict,
    ) -> None:
        """Test that list_closed returns only closed milestones."""
        sample_milestone_data["is_closed"] = True
        mock_client.get.return_value = [sample_milestone_data]

        milestones = await repository.list_closed(project_id=5)

        assert len(milestones) == 1
        mock_client.get.assert_called_once_with("milestones", params={"project": 5, "closed": True})


class TestGetCurrent:
    """Tests for get_current method."""

    @pytest.mark.asyncio
    async def test_get_current_returns_first_open_milestone(
        self,
        repository: MilestoneRepositoryImpl,
        mock_client: MagicMock,
        sample_milestone_data: dict,
    ) -> None:
        """Test that get_current returns the first open milestone."""
        second_milestone = dict(sample_milestone_data)
        second_milestone["id"] = 2
        second_milestone["name"] = "Sprint 2"
        second_milestone["estimated_start"] = "2024-01-15"
        mock_client.get.return_value = [second_milestone, sample_milestone_data]

        milestone = await repository.get_current(project_id=5)

        assert milestone is not None
        assert milestone.id == 1  # First by estimated_start

    @pytest.mark.asyncio
    async def test_get_current_returns_none_when_no_open_milestones(
        self, repository: MilestoneRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_current returns None when no open milestones."""
        mock_client.get.return_value = []

        milestone = await repository.get_current(project_id=5)

        assert milestone is None

    @pytest.mark.asyncio
    async def test_get_current_handles_milestones_without_start_date(
        self,
        repository: MilestoneRepositoryImpl,
        mock_client: MagicMock,
        sample_milestone_data: dict,
    ) -> None:
        """Test that get_current handles milestones without estimated_start."""
        sample_milestone_data["estimated_start"] = None
        mock_client.get.return_value = [sample_milestone_data]

        milestone = await repository.get_current(project_id=5)

        assert milestone is not None
        assert milestone.id == 1


class TestGetStats:
    """Tests for get_stats method."""

    @pytest.mark.asyncio
    async def test_get_stats_returns_statistics(
        self, repository: MilestoneRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_stats returns milestone statistics."""
        mock_client.get.return_value = {
            "total_points": 100,
            "completed_points": 75,
            "total_userstories": 10,
            "completed_userstories": 7,
        }

        stats = await repository.get_stats(milestone_id=1)

        assert "total_points" in stats
        assert stats["completed_points"] == 75
        mock_client.get.assert_called_once_with("milestones/1/stats")

    @pytest.mark.asyncio
    async def test_get_stats_raises_when_not_found(
        self, repository: MilestoneRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_stats raises ResourceNotFoundError when not found."""
        mock_client.get.side_effect = Exception("404 Not found")

        with pytest.raises(ResourceNotFoundError) as exc_info:
            await repository.get_stats(milestone_id=999)

        assert "Milestone with id 999 not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_stats_raises_when_response_is_none(
        self, repository: MilestoneRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_stats raises ResourceNotFoundError when response is None."""
        mock_client.get.return_value = None

        with pytest.raises(ResourceNotFoundError) as exc_info:
            await repository.get_stats(milestone_id=1)

        assert "Milestone with id 1 not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_stats_propagates_other_exceptions(
        self, repository: MilestoneRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_stats propagates non-404 exceptions."""
        mock_client.get.side_effect = RuntimeError("Server error")

        with pytest.raises(RuntimeError) as exc_info:
            await repository.get_stats(milestone_id=1)

        assert "Server error" in str(exc_info.value)
