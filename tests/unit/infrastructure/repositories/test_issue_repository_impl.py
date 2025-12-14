"""Unit tests for IssueRepositoryImpl."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.issue import Issue
from src.infrastructure.repositories.issue_repository_impl import IssueRepositoryImpl
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
def repository(mock_client: MagicMock) -> IssueRepositoryImpl:
    """Create an IssueRepositoryImpl instance."""
    return IssueRepositoryImpl(client=mock_client)


@pytest.fixture
def sample_issue_data() -> dict:
    """Create sample issue data from API."""
    return {
        "id": 1,
        "ref": 25,
        "subject": "Test Issue",
        "description": "A test issue",
        "project": 5,
        "assigned_to": 3,
        "milestone": 2,
        "status": 1,
        "type": 1,
        "severity": 2,
        "priority": 3,
        "is_closed": False,
        "is_blocked": False,
        "version": 1,
    }


class TestIssueRepositoryInit:
    """Tests for IssueRepositoryImpl initialization."""

    def test_init_sets_correct_endpoint(self, repository: IssueRepositoryImpl) -> None:
        """Test that the repository is initialized with correct endpoint."""
        assert repository.endpoint == "issues"

    def test_init_sets_correct_entity_class(self, repository: IssueRepositoryImpl) -> None:
        """Test that the repository uses Issue entity class."""
        assert repository.entity_class == Issue


class TestToEntity:
    """Tests for _to_entity field mapping."""

    def test_to_entity_maps_project_to_project_id(
        self, repository: IssueRepositoryImpl, sample_issue_data: dict
    ) -> None:
        """Test that API 'project' field is mapped to 'project_id'."""
        entity = repository._to_entity(sample_issue_data)
        assert entity.project_id == 5

    def test_to_entity_maps_assigned_to_to_assigned_to_id(
        self, repository: IssueRepositoryImpl, sample_issue_data: dict
    ) -> None:
        """Test that API 'assigned_to' field is mapped to 'assigned_to_id'."""
        entity = repository._to_entity(sample_issue_data)
        assert entity.assigned_to_id == 3

    def test_to_entity_maps_milestone_to_milestone_id(
        self, repository: IssueRepositoryImpl, sample_issue_data: dict
    ) -> None:
        """Test that API 'milestone' field is mapped to 'milestone_id'."""
        entity = repository._to_entity(sample_issue_data)
        assert entity.milestone_id == 2

    def test_to_entity_preserves_type_severity_priority(
        self, repository: IssueRepositoryImpl, sample_issue_data: dict
    ) -> None:
        """Test that type, severity, and priority are preserved."""
        entity = repository._to_entity(sample_issue_data)
        assert entity.type == 1
        assert entity.severity == 2
        assert entity.priority == 3


class TestToDict:
    """Tests for _to_dict field mapping."""

    def test_to_dict_maps_project_id_to_project(self, repository: IssueRepositoryImpl) -> None:
        """Test that entity 'project_id' field is mapped to 'project'."""
        entity = Issue(id=1, subject="Test", project_id=5, version=1)
        data = repository._to_dict(entity)
        assert "project" in data
        assert data["project"] == 5
        assert "project_id" not in data

    def test_to_dict_maps_assigned_to_id_to_assigned_to(
        self, repository: IssueRepositoryImpl
    ) -> None:
        """Test that entity 'assigned_to_id' field is mapped to 'assigned_to'."""
        entity = Issue(id=1, subject="Test", project_id=5, assigned_to_id=3, version=1)
        data = repository._to_dict(entity)
        assert "assigned_to" in data
        assert data["assigned_to"] == 3
        assert "assigned_to_id" not in data

    def test_to_dict_maps_milestone_id_to_milestone(self, repository: IssueRepositoryImpl) -> None:
        """Test that entity 'milestone_id' field is mapped to 'milestone'."""
        entity = Issue(id=1, subject="Test", project_id=5, milestone_id=2, version=1)
        data = repository._to_dict(entity)
        assert "milestone" in data
        assert data["milestone"] == 2
        assert "milestone_id" not in data


class TestGetByRef:
    """Tests for get_by_ref method."""

    @pytest.mark.asyncio
    async def test_get_by_ref_returns_issue_when_found(
        self,
        repository: IssueRepositoryImpl,
        mock_client: MagicMock,
        sample_issue_data: dict,
    ) -> None:
        """Test that get_by_ref returns an issue when found."""
        mock_client.get.return_value = sample_issue_data

        issue = await repository.get_by_ref(project_id=5, ref=25)

        assert issue is not None
        assert issue.id == 1
        assert issue.ref == 25
        mock_client.get.assert_called_once_with("issues/by_ref", params={"project": 5, "ref": 25})

    @pytest.mark.asyncio
    async def test_get_by_ref_returns_none_when_not_found(
        self, repository: IssueRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_by_ref returns None when not found."""
        mock_client.get.side_effect = Exception("Not found")

        issue = await repository.get_by_ref(project_id=5, ref=999)

        assert issue is None


class TestListByType:
    """Tests for list_by_type method."""

    @pytest.mark.asyncio
    async def test_list_by_type_returns_issues(
        self,
        repository: IssueRepositoryImpl,
        mock_client: MagicMock,
        sample_issue_data: dict,
    ) -> None:
        """Test that list_by_type returns issues of a specific type."""
        mock_client.get.return_value = [sample_issue_data]

        issues = await repository.list_by_type(project_id=5, type_id=1)

        assert len(issues) == 1
        mock_client.get.assert_called_once_with("issues", params={"project": 5, "type": 1})


class TestListBySeverity:
    """Tests for list_by_severity method."""

    @pytest.mark.asyncio
    async def test_list_by_severity_returns_issues(
        self,
        repository: IssueRepositoryImpl,
        mock_client: MagicMock,
        sample_issue_data: dict,
    ) -> None:
        """Test that list_by_severity returns issues with specific severity."""
        mock_client.get.return_value = [sample_issue_data]

        issues = await repository.list_by_severity(project_id=5, severity_id=2)

        assert len(issues) == 1
        mock_client.get.assert_called_once_with("issues", params={"project": 5, "severity": 2})


class TestListByPriority:
    """Tests for list_by_priority method."""

    @pytest.mark.asyncio
    async def test_list_by_priority_returns_issues(
        self,
        repository: IssueRepositoryImpl,
        mock_client: MagicMock,
        sample_issue_data: dict,
    ) -> None:
        """Test that list_by_priority returns issues with specific priority."""
        mock_client.get.return_value = [sample_issue_data]

        issues = await repository.list_by_priority(project_id=5, priority_id=3)

        assert len(issues) == 1
        mock_client.get.assert_called_once_with("issues", params={"project": 5, "priority": 3})


class TestListByMilestone:
    """Tests for list_by_milestone method."""

    @pytest.mark.asyncio
    async def test_list_by_milestone_returns_issues(
        self,
        repository: IssueRepositoryImpl,
        mock_client: MagicMock,
        sample_issue_data: dict,
    ) -> None:
        """Test that list_by_milestone returns issues in milestone."""
        mock_client.get.return_value = [sample_issue_data]

        issues = await repository.list_by_milestone(milestone_id=2)

        assert len(issues) == 1
        mock_client.get.assert_called_once_with("issues", params={"milestone": 2})


class TestListOpen:
    """Tests for list_open method."""

    @pytest.mark.asyncio
    async def test_list_open_returns_open_issues(
        self,
        repository: IssueRepositoryImpl,
        mock_client: MagicMock,
        sample_issue_data: dict,
    ) -> None:
        """Test that list_open returns only open issues."""
        mock_client.get.return_value = [sample_issue_data]

        issues = await repository.list_open(project_id=5)

        assert len(issues) == 1
        mock_client.get.assert_called_once_with("issues", params={"project": 5, "is_closed": False})


class TestListClosed:
    """Tests for list_closed method."""

    @pytest.mark.asyncio
    async def test_list_closed_returns_closed_issues(
        self,
        repository: IssueRepositoryImpl,
        mock_client: MagicMock,
        sample_issue_data: dict,
    ) -> None:
        """Test that list_closed returns only closed issues."""
        sample_issue_data["is_closed"] = True
        mock_client.get.return_value = [sample_issue_data]

        issues = await repository.list_closed(project_id=5)

        assert len(issues) == 1
        assert issues[0].is_closed is True
        mock_client.get.assert_called_once_with("issues", params={"project": 5, "is_closed": True})


class TestBulkCreate:
    """Tests for bulk_create method."""

    @pytest.mark.asyncio
    async def test_bulk_create_creates_multiple_issues(
        self,
        repository: IssueRepositoryImpl,
        mock_client: MagicMock,
        sample_issue_data: dict,
    ) -> None:
        """Test that bulk_create creates multiple issues."""
        mock_client.post.return_value = [sample_issue_data]
        issues = [
            Issue(subject="Issue 1", project_id=5),
            Issue(subject="Issue 2", project_id=5),
        ]

        created = await repository.bulk_create(issues)

        assert len(created) == 1
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "issues/bulk_create"

    @pytest.mark.asyncio
    async def test_bulk_create_returns_empty_for_empty_input(
        self, repository: IssueRepositoryImpl
    ) -> None:
        """Test that bulk_create returns empty list for empty input."""
        created = await repository.bulk_create([])
        assert created == []

    @pytest.mark.asyncio
    async def test_bulk_create_returns_empty_on_error(
        self, repository: IssueRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that bulk_create returns empty list on error."""
        mock_client.post.side_effect = Exception("API error")
        issues = [Issue(subject="Issue 1", project_id=5)]

        created = await repository.bulk_create(issues)

        assert created == []


class TestGetFilters:
    """Tests for get_filters method."""

    @pytest.mark.asyncio
    async def test_get_filters_returns_filter_options(
        self, repository: IssueRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_filters returns filter options."""
        mock_client.get.return_value = {
            "types": [{"id": 1, "name": "Bug"}],
            "severities": [{"id": 1, "name": "Normal"}],
            "priorities": [{"id": 1, "name": "Normal"}],
        }

        filters = await repository.get_filters(project_id=5)

        assert "types" in filters
        assert "severities" in filters
        assert "priorities" in filters
        mock_client.get.assert_called_once_with("issues/filters_data", params={"project": 5})

    @pytest.mark.asyncio
    async def test_get_filters_returns_empty_on_error(
        self, repository: IssueRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_filters returns empty dict on error."""
        mock_client.get.side_effect = Exception("API error")

        filters = await repository.get_filters(project_id=5)

        assert filters == {}
