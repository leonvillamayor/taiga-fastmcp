"""Tests unitarios para IssueUseCases.

Este módulo contiene tests exhaustivos para todos los métodos
de IssueUseCases, cubriendo casos de éxito, errores y edge cases.
"""

from unittest.mock import MagicMock

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


class TestCreateIssue:
    """Tests para el caso de uso create_issue."""

    @pytest.mark.asyncio
    async def test_create_issue_success(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe crear un issue exitosamente."""
        # Arrange
        mock_issue_repository.create.return_value = sample_issue
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = CreateIssueRequest(
            subject="Test Issue",
            description="A test issue",
            project_id=1,
            status=1,
            type=1,
            severity=3,
            priority=3,
            milestone_id=1,
            assigned_to_id=1,
            is_blocked=False,
            blocked_note="",
            tags=["issue-tag"],
        )

        # Act
        result = await use_cases.create_issue(request)

        # Assert
        assert result == sample_issue
        mock_issue_repository.create.assert_called_once()
        created_issue = mock_issue_repository.create.call_args[0][0]
        assert created_issue.subject == "Test Issue"
        assert created_issue.project_id == 1
        assert created_issue.type == 1
        assert created_issue.severity == 3
        assert created_issue.priority == 3

    @pytest.mark.asyncio
    async def test_create_issue_with_defaults(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe crear un issue con valores por defecto."""
        # Arrange
        mock_issue_repository.create.return_value = sample_issue
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = CreateIssueRequest(
            subject="Minimal Issue",
            project_id=1,
        )

        # Act
        result = await use_cases.create_issue(request)

        # Assert
        assert result == sample_issue
        created_issue = mock_issue_repository.create.call_args[0][0]
        assert created_issue.subject == "Minimal Issue"
        assert created_issue.description == ""
        assert created_issue.type is None
        assert created_issue.severity is None
        assert created_issue.priority is None
        assert created_issue.is_blocked is False
        assert created_issue.tags == []

    @pytest.mark.asyncio
    async def test_create_issue_with_blocking(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe crear un issue bloqueado."""
        # Arrange
        mock_issue_repository.create.return_value = sample_issue
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = CreateIssueRequest(
            subject="Blocked Issue",
            project_id=1,
            is_blocked=True,
            blocked_note="Waiting for more info",
        )

        # Act
        await use_cases.create_issue(request)

        # Assert
        created_issue = mock_issue_repository.create.call_args[0][0]
        assert created_issue.is_blocked is True
        assert created_issue.blocked_note == "Waiting for more info"


class TestGetIssue:
    """Tests para el caso de uso get_issue."""

    @pytest.mark.asyncio
    async def test_get_issue_success(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe retornar el issue cuando existe."""
        # Arrange
        mock_issue_repository.get_by_id.return_value = sample_issue
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.get_issue(issue_id=1)

        # Assert
        assert result == sample_issue
        mock_issue_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_issue_not_found(self, mock_issue_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_issue_repository.get_by_id.return_value = None
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await use_cases.get_issue(issue_id=999)

        assert "Issue 999 not found" in str(exc_info.value)
        mock_issue_repository.get_by_id.assert_called_once_with(999)


class TestGetIssueByRef:
    """Tests para el caso de uso get_issue_by_ref."""

    @pytest.mark.asyncio
    async def test_get_issue_by_ref_success(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe retornar el issue cuando existe la referencia."""
        # Arrange
        mock_issue_repository.get_by_ref.return_value = sample_issue
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.get_issue_by_ref(project_id=1, ref=42)

        # Assert
        assert result == sample_issue
        mock_issue_repository.get_by_ref.assert_called_once_with(1, 42)

    @pytest.mark.asyncio
    async def test_get_issue_by_ref_not_found(self, mock_issue_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe la referencia."""
        # Arrange
        mock_issue_repository.get_by_ref.return_value = None
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await use_cases.get_issue_by_ref(project_id=1, ref=999)

        assert "Issue with ref=999 not found in project 1" in str(exc_info.value)


class TestListIssues:
    """Tests para el caso de uso list_issues."""

    @pytest.mark.asyncio
    async def test_list_issues_no_filters(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe listar issues sin filtros."""
        # Arrange
        mock_issue_repository.list.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = ListIssuesRequest()

        # Act
        result = await use_cases.list_issues(request)

        # Assert
        assert result == [sample_issue]
        mock_issue_repository.list.assert_called_once_with(filters={}, limit=None, offset=None)

    @pytest.mark.asyncio
    async def test_list_issues_with_project_filter(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe filtrar issues por proyecto."""
        # Arrange
        mock_issue_repository.list.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = ListIssuesRequest(project_id=1)

        # Act
        await use_cases.list_issues(request)

        # Assert
        mock_issue_repository.list.assert_called_once_with(
            filters={"project": 1}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_issues_with_type_filter(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe filtrar issues por tipo."""
        # Arrange
        mock_issue_repository.list.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = ListIssuesRequest(type_id=2)

        # Act
        await use_cases.list_issues(request)

        # Assert
        mock_issue_repository.list.assert_called_once_with(
            filters={"type": 2}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_issues_with_severity_filter(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe filtrar issues por severidad."""
        # Arrange
        mock_issue_repository.list.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = ListIssuesRequest(severity_id=4)

        # Act
        await use_cases.list_issues(request)

        # Assert
        mock_issue_repository.list.assert_called_once_with(
            filters={"severity": 4}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_issues_with_priority_filter(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe filtrar issues por prioridad."""
        # Arrange
        mock_issue_repository.list.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = ListIssuesRequest(priority_id=5)

        # Act
        await use_cases.list_issues(request)

        # Assert
        mock_issue_repository.list.assert_called_once_with(
            filters={"priority": 5}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_issues_with_status_filter(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe filtrar issues por estado."""
        # Arrange
        mock_issue_repository.list.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = ListIssuesRequest(status_id=1)

        # Act
        await use_cases.list_issues(request)

        # Assert
        mock_issue_repository.list.assert_called_once_with(
            filters={"status": 1}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_issues_with_milestone_filter(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe filtrar issues por milestone."""
        # Arrange
        mock_issue_repository.list.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = ListIssuesRequest(milestone_id=3)

        # Act
        await use_cases.list_issues(request)

        # Assert
        mock_issue_repository.list.assert_called_once_with(
            filters={"milestone": 3}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_issues_with_assigned_to_filter(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe filtrar issues por asignado."""
        # Arrange
        mock_issue_repository.list.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = ListIssuesRequest(assigned_to_id=10)

        # Act
        await use_cases.list_issues(request)

        # Assert
        mock_issue_repository.list.assert_called_once_with(
            filters={"assigned_to": 10}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_issues_with_closed_filter(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe filtrar issues por estado cerrado."""
        # Arrange
        mock_issue_repository.list.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = ListIssuesRequest(is_closed=False)

        # Act
        await use_cases.list_issues(request)

        # Assert
        mock_issue_repository.list.assert_called_once_with(
            filters={"is_closed": False}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_issues_with_tags_filter(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe filtrar issues por tags."""
        # Arrange
        mock_issue_repository.list.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = ListIssuesRequest(tags=["bug", "critical"])

        # Act
        await use_cases.list_issues(request)

        # Assert
        mock_issue_repository.list.assert_called_once_with(
            filters={"tags": ["bug", "critical"]}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_issues_with_pagination(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe aplicar paginación correctamente."""
        # Arrange
        mock_issue_repository.list.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = ListIssuesRequest(limit=25, offset=50)

        # Act
        await use_cases.list_issues(request)

        # Assert
        mock_issue_repository.list.assert_called_once_with(filters={}, limit=25, offset=50)

    @pytest.mark.asyncio
    async def test_list_issues_with_all_filters(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe aplicar todos los filtros combinados."""
        # Arrange
        mock_issue_repository.list.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = ListIssuesRequest(
            project_id=1,
            type_id=2,
            severity_id=3,
            priority_id=4,
            status_id=1,
            milestone_id=5,
            assigned_to_id=10,
            is_closed=False,
            tags=["bug"],
            limit=20,
            offset=0,
        )

        # Act
        await use_cases.list_issues(request)

        # Assert
        mock_issue_repository.list.assert_called_once_with(
            filters={
                "project": 1,
                "type": 2,
                "severity": 3,
                "priority": 4,
                "status": 1,
                "milestone": 5,
                "assigned_to": 10,
                "is_closed": False,
                "tags": ["bug"],
            },
            limit=20,
            offset=0,
        )

    @pytest.mark.asyncio
    async def test_list_issues_empty_result(self, mock_issue_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay issues."""
        # Arrange
        mock_issue_repository.list.return_value = []
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = ListIssuesRequest()

        # Act
        result = await use_cases.list_issues(request)

        # Assert
        assert result == []


class TestListByType:
    """Tests para el caso de uso list_by_type."""

    @pytest.mark.asyncio
    async def test_list_by_type_success(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe listar issues de un tipo específico."""
        # Arrange
        mock_issue_repository.list_by_type.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.list_by_type(project_id=1, type_id=2)

        # Assert
        assert result == [sample_issue]
        mock_issue_repository.list_by_type.assert_called_once_with(1, 2)

    @pytest.mark.asyncio
    async def test_list_by_type_empty(self, mock_issue_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay issues de ese tipo."""
        # Arrange
        mock_issue_repository.list_by_type.return_value = []
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.list_by_type(project_id=1, type_id=999)

        # Assert
        assert result == []


class TestListBySeverity:
    """Tests para el caso de uso list_by_severity."""

    @pytest.mark.asyncio
    async def test_list_by_severity_success(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe listar issues de una severidad específica."""
        # Arrange
        mock_issue_repository.list_by_severity.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.list_by_severity(project_id=1, severity_id=3)

        # Assert
        assert result == [sample_issue]
        mock_issue_repository.list_by_severity.assert_called_once_with(1, 3)

    @pytest.mark.asyncio
    async def test_list_by_severity_empty(self, mock_issue_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay issues de esa severidad."""
        # Arrange
        mock_issue_repository.list_by_severity.return_value = []
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.list_by_severity(project_id=1, severity_id=5)

        # Assert
        assert result == []


class TestListByPriority:
    """Tests para el caso de uso list_by_priority."""

    @pytest.mark.asyncio
    async def test_list_by_priority_success(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe listar issues de una prioridad específica."""
        # Arrange
        mock_issue_repository.list_by_priority.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.list_by_priority(project_id=1, priority_id=4)

        # Assert
        assert result == [sample_issue]
        mock_issue_repository.list_by_priority.assert_called_once_with(1, 4)

    @pytest.mark.asyncio
    async def test_list_by_priority_empty(self, mock_issue_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay issues de esa prioridad."""
        # Arrange
        mock_issue_repository.list_by_priority.return_value = []
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.list_by_priority(project_id=1, priority_id=1)

        # Assert
        assert result == []


class TestListByMilestone:
    """Tests para el caso de uso list_by_milestone."""

    @pytest.mark.asyncio
    async def test_list_by_milestone_success(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe listar issues de un milestone."""
        # Arrange
        mock_issue_repository.list_by_milestone.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.list_by_milestone(milestone_id=3)

        # Assert
        assert result == [sample_issue]
        mock_issue_repository.list_by_milestone.assert_called_once_with(3)

    @pytest.mark.asyncio
    async def test_list_by_milestone_empty(self, mock_issue_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay issues en el milestone."""
        # Arrange
        mock_issue_repository.list_by_milestone.return_value = []
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.list_by_milestone(milestone_id=999)

        # Assert
        assert result == []


class TestListOpen:
    """Tests para el caso de uso list_open."""

    @pytest.mark.asyncio
    async def test_list_open_success(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe listar issues abiertos de un proyecto."""
        # Arrange
        mock_issue_repository.list_open.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.list_open(project_id=1)

        # Assert
        assert result == [sample_issue]
        mock_issue_repository.list_open.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_open_empty(self, mock_issue_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay issues abiertos."""
        # Arrange
        mock_issue_repository.list_open.return_value = []
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.list_open(project_id=1)

        # Assert
        assert result == []


class TestListClosed:
    """Tests para el caso de uso list_closed."""

    @pytest.mark.asyncio
    async def test_list_closed_success(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe listar issues cerrados de un proyecto."""
        # Arrange
        mock_issue_repository.list_closed.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.list_closed(project_id=1)

        # Assert
        assert result == [sample_issue]
        mock_issue_repository.list_closed.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_closed_empty(self, mock_issue_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay issues cerrados."""
        # Arrange
        mock_issue_repository.list_closed.return_value = []
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.list_closed(project_id=1)

        # Assert
        assert result == []


class TestUpdateIssue:
    """Tests para el caso de uso update_issue."""

    @pytest.mark.asyncio
    async def test_update_issue_success(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe actualizar el issue exitosamente."""
        # Arrange
        mock_issue_repository.get_by_id.return_value = sample_issue
        mock_issue_repository.update.return_value = sample_issue
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = UpdateIssueRequest(
            issue_id=1,
            subject="Updated Issue",
            description="Updated description",
        )

        # Act
        result = await use_cases.update_issue(request)

        # Assert
        assert result == sample_issue
        mock_issue_repository.get_by_id.assert_called_once_with(1)
        mock_issue_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_issue_not_found(self, mock_issue_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_issue_repository.get_by_id.return_value = None
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = UpdateIssueRequest(issue_id=999, subject="New Subject")

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.update_issue(request)

        mock_issue_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_issue_partial_fields(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe actualizar solo los campos proporcionados."""
        # Arrange
        mock_issue_repository.get_by_id.return_value = sample_issue
        mock_issue_repository.update.return_value = sample_issue
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = UpdateIssueRequest(issue_id=1, subject="Only Subject")

        # Act
        await use_cases.update_issue(request)

        # Assert
        updated_issue = mock_issue_repository.update.call_args[0][0]
        assert updated_issue.subject == "Only Subject"
        assert updated_issue.description == sample_issue.description

    @pytest.mark.asyncio
    async def test_update_issue_all_fields(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe actualizar todos los campos cuando se proporcionan."""
        # Arrange
        mock_issue_repository.get_by_id.return_value = sample_issue
        mock_issue_repository.update.return_value = sample_issue
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = UpdateIssueRequest(
            issue_id=1,
            subject="New Subject",
            description="New Description",
            status=5,
            type=2,
            severity=4,
            priority=5,
            milestone_id=3,
            assigned_to_id=2,
            is_blocked=True,
            blocked_note="Blocked reason",
            is_closed=True,
            tags=["new-tag"],
        )

        # Act
        await use_cases.update_issue(request)

        # Assert
        updated_issue = mock_issue_repository.update.call_args[0][0]
        assert updated_issue.subject == "New Subject"
        assert updated_issue.description == "New Description"
        assert updated_issue.status == 5
        assert updated_issue.type == 2
        assert updated_issue.severity == 4
        assert updated_issue.priority == 5
        assert updated_issue.milestone_id == 3
        assert updated_issue.assigned_to_id == 2
        assert updated_issue.is_blocked is True
        assert updated_issue.blocked_note == "Blocked reason"
        assert updated_issue.is_closed is True
        assert updated_issue.tags == ["new-tag"]

    @pytest.mark.asyncio
    async def test_update_issue_block_status(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe actualizar el estado de bloqueo."""
        # Arrange
        mock_issue_repository.get_by_id.return_value = sample_issue
        mock_issue_repository.update.return_value = sample_issue
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = UpdateIssueRequest(
            issue_id=1,
            is_blocked=True,
            blocked_note="Need clarification",
        )

        # Act
        await use_cases.update_issue(request)

        # Assert
        updated_issue = mock_issue_repository.update.call_args[0][0]
        assert updated_issue.is_blocked is True
        assert updated_issue.blocked_note == "Need clarification"


class TestDeleteIssue:
    """Tests para el caso de uso delete_issue."""

    @pytest.mark.asyncio
    async def test_delete_issue_success(self, mock_issue_repository: MagicMock) -> None:
        """Debe eliminar el issue exitosamente."""
        # Arrange
        mock_issue_repository.delete.return_value = True
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.delete_issue(issue_id=1)

        # Assert
        assert result is True
        mock_issue_repository.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_issue_not_found(self, mock_issue_repository: MagicMock) -> None:
        """Debe retornar False cuando el issue no existe."""
        # Arrange
        mock_issue_repository.delete.return_value = False
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.delete_issue(issue_id=999)

        # Assert
        assert result is False


class TestBulkCreateIssues:
    """Tests para el caso de uso bulk_create_issues."""

    @pytest.mark.asyncio
    async def test_bulk_create_issues_success(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe crear múltiples issues exitosamente."""
        # Arrange
        mock_issue_repository.bulk_create.return_value = [sample_issue, sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = BulkCreateIssuesRequest(
            project_id=1,
            issues=[
                CreateIssueRequest(subject="Issue 1", project_id=1),
                CreateIssueRequest(subject="Issue 2", project_id=1),
            ],
        )

        # Act
        result = await use_cases.bulk_create_issues(request)

        # Assert
        assert len(result) == 2
        mock_issue_repository.bulk_create.assert_called_once()
        created_issues = mock_issue_repository.bulk_create.call_args[0][0]
        assert len(created_issues) == 2
        assert created_issues[0].subject == "Issue 1"
        assert created_issues[0].project_id == 1
        assert created_issues[1].subject == "Issue 2"

    @pytest.mark.asyncio
    async def test_bulk_create_issues_with_all_fields(
        self, mock_issue_repository: MagicMock, sample_issue: Issue
    ) -> None:
        """Debe crear issues con todos los campos."""
        # Arrange
        mock_issue_repository.bulk_create.return_value = [sample_issue]
        use_cases = IssueUseCases(repository=mock_issue_repository)
        request = BulkCreateIssuesRequest(
            project_id=1,
            issues=[
                CreateIssueRequest(
                    subject="Full Issue",
                    description="Full description",
                    project_id=1,
                    status=2,
                    type=1,
                    severity=3,
                    priority=4,
                    milestone_id=5,
                    assigned_to_id=6,
                    is_blocked=True,
                    blocked_note="Blocked",
                    tags=["critical"],
                ),
            ],
        )

        # Act
        await use_cases.bulk_create_issues(request)

        # Assert
        created_issues = mock_issue_repository.bulk_create.call_args[0][0]
        assert created_issues[0].description == "Full description"
        assert created_issues[0].type == 1
        assert created_issues[0].severity == 3
        assert created_issues[0].priority == 4


class TestGetFilters:
    """Tests para el caso de uso get_filters."""

    @pytest.mark.asyncio
    async def test_get_filters_success(self, mock_issue_repository: MagicMock) -> None:
        """Debe retornar los filtros disponibles."""
        # Arrange
        filters = {
            "statuses": [{"id": 1, "name": "New"}],
            "types": [{"id": 1, "name": "Bug"}],
            "severities": [{"id": 3, "name": "Normal"}],
            "priorities": [{"id": 3, "name": "Normal"}],
            "assigned_to": [{"id": 1, "name": "User"}],
        }
        mock_issue_repository.get_filters.return_value = filters
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.get_filters(project_id=1)

        # Assert
        assert result == filters
        mock_issue_repository.get_filters.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_filters_empty(self, mock_issue_repository: MagicMock) -> None:
        """Debe retornar diccionario vacío si no hay filtros."""
        # Arrange
        mock_issue_repository.get_filters.return_value = {}
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Act
        result = await use_cases.get_filters(project_id=1)

        # Assert
        assert result == {}


class TestIssueUseCasesInitialization:
    """Tests para la inicialización de IssueUseCases."""

    def test_initialization_with_repository(self, mock_issue_repository: MagicMock) -> None:
        """Debe inicializarse correctamente con el repositorio."""
        # Act
        use_cases = IssueUseCases(repository=mock_issue_repository)

        # Assert
        assert use_cases.repository == mock_issue_repository
