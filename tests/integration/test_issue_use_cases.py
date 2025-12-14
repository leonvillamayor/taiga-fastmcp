"""
Tests de integración para casos de uso de issues.
Implementa tests para la capa de aplicación.
"""

from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.issue_use_cases import (
    BulkCreateIssuesRequest,
    CreateIssueRequest,
    IssueUseCases,
    ListIssuesRequest,
    UpdateIssueRequest,
)
from src.domain.entities.issue import Issue
from src.domain.exceptions import ResourceNotFoundError


@pytest.fixture
def mock_issue_repository() -> AsyncMock:
    """Crea un mock del repositorio de issues."""
    return AsyncMock()


@pytest.fixture
def sample_issue() -> Issue:
    """Crea un issue de ejemplo para tests."""
    return Issue(
        id=1,
        project_id=100,
        subject="Test Issue",
        description="Test description",
        status=1,
        priority=2,
        severity=3,
        type=1,
        assigned_to_id=10,
        ref=5,
        tags=["bug"],
    )


@pytest.fixture
def sample_issues_list(sample_issue: Issue) -> list[Issue]:
    """Lista de issues de ejemplo."""
    return [
        sample_issue,
        Issue(id=2, project_id=100, subject="Second Issue", ref=6),
    ]


@pytest.mark.integration
@pytest.mark.asyncio
class TestIssueUseCases:
    """Tests de integración para casos de uso de issues."""

    async def test_list_issues(
        self, mock_issue_repository: AsyncMock, sample_issues_list: list[Issue]
    ) -> None:
        """Verifica el caso de uso de listar issues."""
        mock_issue_repository.list.return_value = sample_issues_list
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = ListIssuesRequest(project_id=100, status_id=1)

        result = await use_cases.list_issues(request)

        assert len(result) == 2
        mock_issue_repository.list.assert_called_once()

    async def test_create_issue(
        self, mock_issue_repository: AsyncMock, sample_issue: Issue
    ) -> None:
        """Verifica el caso de uso de crear un issue."""
        mock_issue_repository.create.return_value = sample_issue
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = CreateIssueRequest(
            subject="Test Issue",
            project_id=100,
            description="Test description",
        )

        result = await use_cases.create_issue(request)

        assert result.id == 1
        assert result.subject == "Test Issue"
        mock_issue_repository.create.assert_called_once()

    async def test_get_issue_by_id(
        self, mock_issue_repository: AsyncMock, sample_issue: Issue
    ) -> None:
        """Verifica el caso de uso de obtener issue por ID."""
        mock_issue_repository.get_by_id.return_value = sample_issue
        use_cases = IssueUseCases(repository=mock_issue_repository)

        result = await use_cases.get_issue(issue_id=1)

        assert result.id == 1
        mock_issue_repository.get_by_id.assert_called_once_with(1)

    async def test_get_issue_by_id_not_found(self, mock_issue_repository: AsyncMock) -> None:
        """Verifica que se lance ResourceNotFoundError si el issue no existe."""
        mock_issue_repository.get_by_id.return_value = None
        use_cases = IssueUseCases(repository=mock_issue_repository)

        with pytest.raises(ResourceNotFoundError, match="Issue 999 not found"):
            await use_cases.get_issue(issue_id=999)

    async def test_get_issue_by_ref(
        self, mock_issue_repository: AsyncMock, sample_issue: Issue
    ) -> None:
        """Verifica el caso de uso de obtener issue por referencia."""
        mock_issue_repository.get_by_ref.return_value = sample_issue
        use_cases = IssueUseCases(repository=mock_issue_repository)

        result = await use_cases.get_issue_by_ref(project_id=100, ref=5)

        assert result.ref == 5
        mock_issue_repository.get_by_ref.assert_called_once_with(100, 5)

    async def test_get_issue_by_ref_not_found(self, mock_issue_repository: AsyncMock) -> None:
        """Verifica que se lance ResourceNotFoundError si no se encuentra por ref."""
        mock_issue_repository.get_by_ref.return_value = None
        use_cases = IssueUseCases(repository=mock_issue_repository)

        with pytest.raises(ResourceNotFoundError, match="ref=5 not found"):
            await use_cases.get_issue_by_ref(project_id=100, ref=5)

    async def test_update_issue(
        self, mock_issue_repository: AsyncMock, sample_issue: Issue
    ) -> None:
        """Verifica el caso de uso de actualizar un issue."""
        updated = Issue(id=1, project_id=100, subject="Updated Subject", status=2, ref=5)
        mock_issue_repository.get_by_id.return_value = sample_issue
        mock_issue_repository.update.return_value = updated
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = UpdateIssueRequest(issue_id=1, subject="Updated Subject", status=2)

        result = await use_cases.update_issue(request)

        assert result.subject == "Updated Subject"
        mock_issue_repository.update.assert_called_once()

    async def test_update_issue_not_found(self, mock_issue_repository: AsyncMock) -> None:
        """Verifica que update lance ResourceNotFoundError si no existe."""
        mock_issue_repository.get_by_id.return_value = None
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = UpdateIssueRequest(issue_id=999, subject="Updated Subject")

        with pytest.raises(ResourceNotFoundError, match="Issue 999 not found"):
            await use_cases.update_issue(request)

    async def test_delete_issue(self, mock_issue_repository: AsyncMock) -> None:
        """Verifica el caso de uso de eliminar un issue."""
        mock_issue_repository.delete.return_value = True
        use_cases = IssueUseCases(repository=mock_issue_repository)

        result = await use_cases.delete_issue(issue_id=1)

        assert result is True
        mock_issue_repository.delete.assert_called_once_with(1)

    async def test_delete_issue_not_found(self, mock_issue_repository: AsyncMock) -> None:
        """Verifica que delete devuelva False si no existe."""
        mock_issue_repository.delete.return_value = False
        use_cases = IssueUseCases(repository=mock_issue_repository)

        result = await use_cases.delete_issue(issue_id=999)

        assert result is False

    async def test_bulk_create_issues(
        self, mock_issue_repository: AsyncMock, sample_issues_list: list[Issue]
    ) -> None:
        """Verifica el caso de uso de crear múltiples issues."""
        mock_issue_repository.bulk_create.return_value = sample_issues_list
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = BulkCreateIssuesRequest(
            project_id=100,
            issues=[
                CreateIssueRequest(subject="Issue 1", project_id=100),
                CreateIssueRequest(subject="Issue 2", project_id=100),
            ],
        )

        result = await use_cases.bulk_create_issues(request)

        assert len(result) == 2
        mock_issue_repository.bulk_create.assert_called_once()

    async def test_list_by_type(
        self, mock_issue_repository: AsyncMock, sample_issues_list: list[Issue]
    ) -> None:
        """Verifica el caso de uso de listar issues por tipo."""
        mock_issue_repository.list_by_type.return_value = sample_issues_list
        use_cases = IssueUseCases(repository=mock_issue_repository)

        result = await use_cases.list_by_type(project_id=100, type_id=1)

        assert len(result) == 2
        mock_issue_repository.list_by_type.assert_called_once_with(100, 1)

    async def test_list_by_priority(
        self, mock_issue_repository: AsyncMock, sample_issues_list: list[Issue]
    ) -> None:
        """Verifica el caso de uso de listar issues por prioridad."""
        mock_issue_repository.list_by_priority.return_value = sample_issues_list
        use_cases = IssueUseCases(repository=mock_issue_repository)

        result = await use_cases.list_by_priority(project_id=100, priority_id=2)

        assert len(result) == 2
        mock_issue_repository.list_by_priority.assert_called_once_with(100, 2)

    async def test_list_by_severity(
        self, mock_issue_repository: AsyncMock, sample_issues_list: list[Issue]
    ) -> None:
        """Verifica el caso de uso de listar issues por severidad."""
        mock_issue_repository.list_by_severity.return_value = sample_issues_list
        use_cases = IssueUseCases(repository=mock_issue_repository)

        result = await use_cases.list_by_severity(project_id=100, severity_id=3)

        assert len(result) == 2
        mock_issue_repository.list_by_severity.assert_called_once_with(100, 3)

    async def test_list_by_milestone(
        self, mock_issue_repository: AsyncMock, sample_issues_list: list[Issue]
    ) -> None:
        """Verifica el caso de uso de listar issues por milestone."""
        mock_issue_repository.list_by_milestone.return_value = sample_issues_list
        use_cases = IssueUseCases(repository=mock_issue_repository)

        result = await use_cases.list_by_milestone(milestone_id=10)

        assert len(result) == 2
        mock_issue_repository.list_by_milestone.assert_called_once_with(10)

    async def test_list_open(
        self, mock_issue_repository: AsyncMock, sample_issues_list: list[Issue]
    ) -> None:
        """Verifica el caso de uso de listar issues abiertos."""
        mock_issue_repository.list_open.return_value = sample_issues_list
        use_cases = IssueUseCases(repository=mock_issue_repository)

        result = await use_cases.list_open(project_id=100)

        assert len(result) == 2
        mock_issue_repository.list_open.assert_called_once_with(100)

    async def test_list_closed(
        self, mock_issue_repository: AsyncMock, sample_issues_list: list[Issue]
    ) -> None:
        """Verifica el caso de uso de listar issues cerrados."""
        mock_issue_repository.list_closed.return_value = sample_issues_list
        use_cases = IssueUseCases(repository=mock_issue_repository)

        result = await use_cases.list_closed(project_id=100)

        assert len(result) == 2
        mock_issue_repository.list_closed.assert_called_once_with(100)

    async def test_get_filters(self, mock_issue_repository: AsyncMock) -> None:
        """Verifica el caso de uso de obtener filtros."""
        filters = {"statuses": [{"id": 1, "name": "New"}]}
        mock_issue_repository.get_filters.return_value = filters
        use_cases = IssueUseCases(repository=mock_issue_repository)

        result = await use_cases.get_filters(project_id=100)

        assert "statuses" in result
        mock_issue_repository.get_filters.assert_called_once_with(100)
