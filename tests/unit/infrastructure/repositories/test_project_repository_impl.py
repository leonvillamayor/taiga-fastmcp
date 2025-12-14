"""Unit tests for ProjectRepositoryImpl."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.project import Project
from src.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl
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
def repository(mock_client: MagicMock) -> ProjectRepositoryImpl:
    """Create a ProjectRepositoryImpl instance."""
    return ProjectRepositoryImpl(client=mock_client)


@pytest.fixture
def sample_project_data() -> dict:
    """Create sample project data from API."""
    return {
        "id": 1,
        "name": "Test Project",
        "slug": "test-project",
        "description": "A test project",
        "is_private": True,
        "is_backlog_activated": True,
        "is_kanban_activated": False,
        "is_wiki_activated": True,
        "is_issues_activated": True,
        "version": 1,
    }


class TestProjectRepositoryInit:
    """Tests for ProjectRepositoryImpl initialization."""

    def test_init_sets_correct_endpoint(self, repository: ProjectRepositoryImpl) -> None:
        """Test that the repository is initialized with correct endpoint."""
        assert repository.endpoint == "projects"

    def test_init_sets_correct_entity_class(self, repository: ProjectRepositoryImpl) -> None:
        """Test that the repository uses Project entity class."""
        assert repository.entity_class == Project


class TestGetBySlug:
    """Tests for get_by_slug method."""

    @pytest.mark.asyncio
    async def test_get_by_slug_returns_project_when_found(
        self,
        repository: ProjectRepositoryImpl,
        mock_client: MagicMock,
        sample_project_data: dict,
    ) -> None:
        """Test that get_by_slug returns a project when found."""
        mock_client.get.return_value = sample_project_data

        project = await repository.get_by_slug("test-project")

        assert project is not None
        assert project.id == 1
        assert project.slug is not None
        assert str(project.slug) == "test-project"
        mock_client.get.assert_called_once_with("projects/by_slug", params={"slug": "test-project"})

    @pytest.mark.asyncio
    async def test_get_by_slug_returns_none_when_not_found(
        self, repository: ProjectRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_by_slug returns None when project is not found."""
        mock_client.get.side_effect = Exception("Not found")

        project = await repository.get_by_slug("non-existent")

        assert project is None

    @pytest.mark.asyncio
    async def test_get_by_slug_returns_none_for_list_response(
        self, repository: ProjectRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_by_slug returns None for list response."""
        mock_client.get.return_value = [{"id": 1}]

        project = await repository.get_by_slug("test-project")

        assert project is None


class TestListByMember:
    """Tests for list_by_member method."""

    @pytest.mark.asyncio
    async def test_list_by_member_returns_projects(
        self,
        repository: ProjectRepositoryImpl,
        mock_client: MagicMock,
        sample_project_data: dict,
    ) -> None:
        """Test that list_by_member returns projects for the member."""
        mock_client.get.return_value = [sample_project_data]

        projects = await repository.list_by_member(member_id=5)

        assert len(projects) == 1
        assert projects[0].id == 1
        mock_client.get.assert_called_once_with("projects", params={"member": 5})


class TestListPrivate:
    """Tests for list_private method."""

    @pytest.mark.asyncio
    async def test_list_private_returns_private_projects(
        self,
        repository: ProjectRepositoryImpl,
        mock_client: MagicMock,
        sample_project_data: dict,
    ) -> None:
        """Test that list_private returns only private projects."""
        mock_client.get.return_value = [sample_project_data]

        projects = await repository.list_private()

        assert len(projects) == 1
        mock_client.get.assert_called_once_with("projects", params={"is_private": True})


class TestListPublic:
    """Tests for list_public method."""

    @pytest.mark.asyncio
    async def test_list_public_returns_public_projects(
        self,
        repository: ProjectRepositoryImpl,
        mock_client: MagicMock,
        sample_project_data: dict,
    ) -> None:
        """Test that list_public returns only public projects."""
        sample_project_data["is_private"] = False
        mock_client.get.return_value = [sample_project_data]

        projects = await repository.list_public()

        assert len(projects) == 1
        mock_client.get.assert_called_once_with("projects", params={"is_private": False})


class TestListWithBacklog:
    """Tests for list_with_backlog method."""

    @pytest.mark.asyncio
    async def test_list_with_backlog_returns_backlog_projects(
        self,
        repository: ProjectRepositoryImpl,
        mock_client: MagicMock,
        sample_project_data: dict,
    ) -> None:
        """Test that list_with_backlog returns projects with backlog activated."""
        mock_client.get.return_value = [sample_project_data]

        projects = await repository.list_with_backlog()

        assert len(projects) == 1
        mock_client.get.assert_called_once_with("projects", params={"is_backlog_activated": True})


class TestGetStats:
    """Tests for get_stats method."""

    @pytest.mark.asyncio
    async def test_get_stats_returns_project_statistics(
        self, repository: ProjectRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_stats returns project statistics."""
        mock_client.get.return_value = {
            "total_milestones": 5,
            "total_points": 100,
            "closed_points": 60,
            "defined_points": 40,
        }

        stats = await repository.get_stats(project_id=1)

        assert stats["total_milestones"] == 5
        assert stats["total_points"] == 100
        mock_client.get.assert_called_once_with("projects/1/stats")

    @pytest.mark.asyncio
    async def test_get_stats_returns_empty_on_error(
        self, repository: ProjectRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_stats returns empty dict on error."""
        mock_client.get.side_effect = Exception("API error")

        stats = await repository.get_stats(project_id=1)

        assert stats == {}

    @pytest.mark.asyncio
    async def test_get_stats_returns_empty_for_list_response(
        self, repository: ProjectRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_stats returns empty dict for list response."""
        mock_client.get.return_value = [{"unexpected": "list"}]

        stats = await repository.get_stats(project_id=1)

        assert stats == {}
