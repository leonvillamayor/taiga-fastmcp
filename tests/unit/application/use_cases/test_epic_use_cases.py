"""Tests unitarios para EpicUseCases.

Este módulo contiene tests exhaustivos para todos los métodos
de EpicUseCases, cubriendo casos de éxito, errores y edge cases.
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.application.use_cases.epic_use_cases import (
    BulkCreateEpicsRequest,
    CreateEpicRequest,
    EpicUseCases,
    ListEpicsRequest,
    UpdateEpicRequest,
)
from src.domain.entities.epic import Epic
from src.domain.exceptions import ResourceNotFoundError


class TestCreateEpic:
    """Tests para el caso de uso create_epic."""

    @pytest.mark.asyncio
    async def test_create_epic_success(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe crear un epic exitosamente."""
        # Arrange
        mock_epic_repository.create.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = CreateEpicRequest(
            subject="Test Epic",
            description="A test epic",
            project_id=1,
            status=1,
            assigned_to_id=1,
            color="#FF0000",
            tags=["test", "sample"],
        )

        # Act
        result = await use_cases.create_epic(request)

        # Assert
        assert result == sample_epic
        mock_epic_repository.create.assert_called_once()
        created_epic = mock_epic_repository.create.call_args[0][0]
        assert created_epic.subject == "Test Epic"
        assert created_epic.description == "A test epic"
        assert created_epic.project == 1

    @pytest.mark.asyncio
    async def test_create_epic_with_defaults(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe crear un epic con valores por defecto."""
        # Arrange
        mock_epic_repository.create.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = CreateEpicRequest(
            subject="Minimal Epic",
            project_id=1,
        )

        # Act
        result = await use_cases.create_epic(request)

        # Assert
        assert result == sample_epic
        created_epic = mock_epic_repository.create.call_args[0][0]
        assert created_epic.subject == "Minimal Epic"
        assert created_epic.color == "#A5694F"
        assert created_epic.tags == []
        assert created_epic.client_requirement is False
        assert created_epic.team_requirement is False

    @pytest.mark.asyncio
    async def test_create_epic_with_requirements(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe crear epic con client_requirement y team_requirement."""
        # Arrange
        mock_epic_repository.create.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = CreateEpicRequest(
            subject="Requirements Epic",
            project_id=1,
            client_requirement=True,
            team_requirement=True,
        )

        # Act
        await use_cases.create_epic(request)

        # Assert
        created_epic = mock_epic_repository.create.call_args[0][0]
        assert created_epic.client_requirement is True
        assert created_epic.team_requirement is True


class TestGetEpic:
    """Tests para el caso de uso get_epic."""

    @pytest.mark.asyncio
    async def test_get_epic_success(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe retornar el epic cuando existe."""
        # Arrange
        mock_epic_repository.get_by_id.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.get_epic(epic_id=1)

        # Assert
        assert result == sample_epic
        mock_epic_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_epic_not_found(self, mock_epic_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_epic_repository.get_by_id.return_value = None
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await use_cases.get_epic(epic_id=999)

        assert "Epic 999 not found" in str(exc_info.value)
        mock_epic_repository.get_by_id.assert_called_once_with(999)


class TestGetEpicByRef:
    """Tests para el caso de uso get_epic_by_ref."""

    @pytest.mark.asyncio
    async def test_get_epic_by_ref_success(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe retornar el epic cuando existe la referencia."""
        # Arrange
        mock_epic_repository.get_by_ref.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.get_epic_by_ref(project_id=1, ref=5)

        # Assert
        assert result == sample_epic
        mock_epic_repository.get_by_ref.assert_called_once_with(1, 5)

    @pytest.mark.asyncio
    async def test_get_epic_by_ref_not_found(self, mock_epic_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe la referencia."""
        # Arrange
        mock_epic_repository.get_by_ref.return_value = None
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await use_cases.get_epic_by_ref(project_id=1, ref=999)

        assert "Epic with ref=999 not found in project 1" in str(exc_info.value)


class TestListEpics:
    """Tests para el caso de uso list_epics."""

    @pytest.mark.asyncio
    async def test_list_epics_no_filters(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe listar epics sin filtros."""
        # Arrange
        mock_epic_repository.list.return_value = [sample_epic]
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = ListEpicsRequest()

        # Act
        result = await use_cases.list_epics(request)

        # Assert
        assert result == [sample_epic]
        mock_epic_repository.list.assert_called_once_with(filters={}, limit=None, offset=None)

    @pytest.mark.asyncio
    async def test_list_epics_with_project_filter(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe filtrar epics por project_id."""
        # Arrange
        mock_epic_repository.list.return_value = [sample_epic]
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = ListEpicsRequest(project_id=5)

        # Act
        result = await use_cases.list_epics(request)

        # Assert
        assert result == [sample_epic]
        mock_epic_repository.list.assert_called_once_with(
            filters={"project": 5}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_epics_with_status_filter(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe filtrar epics por status_id."""
        # Arrange
        mock_epic_repository.list.return_value = [sample_epic]
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = ListEpicsRequest(status_id=2)

        # Act
        await use_cases.list_epics(request)

        # Assert
        mock_epic_repository.list.assert_called_once_with(
            filters={"status": 2}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_epics_with_assigned_to_filter(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe filtrar epics por assigned_to_id."""
        # Arrange
        mock_epic_repository.list.return_value = [sample_epic]
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = ListEpicsRequest(assigned_to_id=3)

        # Act
        await use_cases.list_epics(request)

        # Assert
        mock_epic_repository.list.assert_called_once_with(
            filters={"assigned_to": 3}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_epics_with_tags_filter(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe filtrar epics por tags."""
        # Arrange
        mock_epic_repository.list.return_value = [sample_epic]
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = ListEpicsRequest(tags=["urgent", "backend"])

        # Act
        await use_cases.list_epics(request)

        # Assert
        mock_epic_repository.list.assert_called_once_with(
            filters={"tags": ["urgent", "backend"]}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_epics_with_pagination(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe aplicar paginación correctamente."""
        # Arrange
        mock_epic_repository.list.return_value = [sample_epic]
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = ListEpicsRequest(limit=10, offset=20)

        # Act
        await use_cases.list_epics(request)

        # Assert
        mock_epic_repository.list.assert_called_once_with(filters={}, limit=10, offset=20)

    @pytest.mark.asyncio
    async def test_list_epics_with_all_filters(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe aplicar todos los filtros combinados."""
        # Arrange
        mock_epic_repository.list.return_value = [sample_epic]
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = ListEpicsRequest(
            project_id=1,
            status_id=2,
            assigned_to_id=3,
            tags=["tag1"],
            limit=50,
            offset=10,
        )

        # Act
        await use_cases.list_epics(request)

        # Assert
        mock_epic_repository.list.assert_called_once_with(
            filters={
                "project": 1,
                "status": 2,
                "assigned_to": 3,
                "tags": ["tag1"],
            },
            limit=50,
            offset=10,
        )

    @pytest.mark.asyncio
    async def test_list_epics_empty_result(self, mock_epic_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay epics."""
        # Arrange
        mock_epic_repository.list.return_value = []
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = ListEpicsRequest()

        # Act
        result = await use_cases.list_epics(request)

        # Assert
        assert result == []


class TestListByProject:
    """Tests para el caso de uso list_by_project."""

    @pytest.mark.asyncio
    async def test_list_by_project_success(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe listar epics de un proyecto."""
        # Arrange
        mock_epic_repository.list_by_project.return_value = [sample_epic]
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.list_by_project(project_id=1)

        # Assert
        assert result == [sample_epic]
        mock_epic_repository.list_by_project.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_by_project_empty(self, mock_epic_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando el proyecto no tiene epics."""
        # Arrange
        mock_epic_repository.list_by_project.return_value = []
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.list_by_project(project_id=999)

        # Assert
        assert result == []


class TestListByStatus:
    """Tests para el caso de uso list_by_status."""

    @pytest.mark.asyncio
    async def test_list_by_status_success(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe listar epics con un estado específico."""
        # Arrange
        mock_epic_repository.list_by_status.return_value = [sample_epic]
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.list_by_status(project_id=1, status_id=2)

        # Assert
        assert result == [sample_epic]
        mock_epic_repository.list_by_status.assert_called_once_with(1, 2)

    @pytest.mark.asyncio
    async def test_list_by_status_empty(self, mock_epic_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay epics con ese estado."""
        # Arrange
        mock_epic_repository.list_by_status.return_value = []
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.list_by_status(project_id=1, status_id=99)

        # Assert
        assert result == []


class TestUpdateEpic:
    """Tests para el caso de uso update_epic."""

    @pytest.mark.asyncio
    async def test_update_epic_success(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe actualizar el epic exitosamente."""
        # Arrange
        mock_epic_repository.get_by_id.return_value = sample_epic
        updated_epic = Epic(
            id=1,
            ref=1,
            subject="Updated Subject",
            description="Updated description",
            project=1,
            status=2,
            color="#00FF00",
            assigned_to=2,
            tags=["updated"],
            created_date=datetime(2024, 1, 1, 12, 0, 0),
            modified_date=datetime(2024, 1, 2, 12, 0, 0),
        )
        mock_epic_repository.update.return_value = updated_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = UpdateEpicRequest(
            epic_id=1,
            subject="Updated Subject",
            description="Updated description",
        )

        # Act
        result = await use_cases.update_epic(request)

        # Assert
        assert result == updated_epic
        mock_epic_repository.get_by_id.assert_called_once_with(1)
        mock_epic_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_epic_not_found(self, mock_epic_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_epic_repository.get_by_id.return_value = None
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = UpdateEpicRequest(epic_id=999, subject="New Subject")

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.update_epic(request)

        mock_epic_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_epic_partial_fields(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe actualizar solo los campos proporcionados."""
        # Arrange
        mock_epic_repository.get_by_id.return_value = sample_epic
        mock_epic_repository.update.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = UpdateEpicRequest(epic_id=1, subject="Only Subject Updated")

        # Act
        await use_cases.update_epic(request)

        # Assert
        updated_epic = mock_epic_repository.update.call_args[0][0]
        assert updated_epic.subject == "Only Subject Updated"
        assert updated_epic.description == sample_epic.description

    @pytest.mark.asyncio
    async def test_update_epic_all_fields(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe actualizar todos los campos cuando se proporcionan."""
        # Arrange
        mock_epic_repository.get_by_id.return_value = sample_epic
        mock_epic_repository.update.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = UpdateEpicRequest(
            epic_id=1,
            subject="New Subject",
            description="New Description",
            status=3,
            assigned_to_id=5,
            color="#0000FF",
            tags=["new-tag"],
            client_requirement=True,
            team_requirement=True,
        )

        # Act
        await use_cases.update_epic(request)

        # Assert
        updated_epic = mock_epic_repository.update.call_args[0][0]
        assert updated_epic.subject == "New Subject"
        assert updated_epic.description == "New Description"
        assert updated_epic.status == 3
        assert updated_epic.assigned_to == 5
        assert updated_epic.color == "#0000FF"
        assert updated_epic.tags == ["new-tag"]
        assert updated_epic.client_requirement is True
        assert updated_epic.team_requirement is True


class TestDeleteEpic:
    """Tests para el caso de uso delete_epic."""

    @pytest.mark.asyncio
    async def test_delete_epic_success(self, mock_epic_repository: MagicMock) -> None:
        """Debe eliminar el epic exitosamente."""
        # Arrange
        mock_epic_repository.delete.return_value = True
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.delete_epic(epic_id=1)

        # Assert
        assert result is True
        mock_epic_repository.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_epic_not_found(self, mock_epic_repository: MagicMock) -> None:
        """Debe retornar False cuando el epic no existe."""
        # Arrange
        mock_epic_repository.delete.return_value = False
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.delete_epic(epic_id=999)

        # Assert
        assert result is False


class TestBulkCreateEpics:
    """Tests para el caso de uso bulk_create_epics."""

    @pytest.mark.asyncio
    async def test_bulk_create_epics_success(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe crear múltiples epics exitosamente."""
        # Arrange
        epics_created = [sample_epic, sample_epic]
        mock_epic_repository.bulk_create.return_value = epics_created
        use_cases = EpicUseCases(repository=mock_epic_repository)

        epic_requests = [
            CreateEpicRequest(subject="Epic 1", project_id=1),
            CreateEpicRequest(subject="Epic 2", project_id=1),
        ]
        request = BulkCreateEpicsRequest(project_id=1, epics=epic_requests)

        # Act
        result = await use_cases.bulk_create_epics(request)

        # Assert
        assert result == epics_created
        mock_epic_repository.bulk_create.assert_called_once()
        created_epics = mock_epic_repository.bulk_create.call_args[0][0]
        assert len(created_epics) == 2
        assert created_epics[0].subject == "Epic 1"
        assert created_epics[1].subject == "Epic 2"
        assert all(e.project == 1 for e in created_epics)

    @pytest.mark.asyncio
    async def test_bulk_create_epics_with_full_data(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe crear epics con todos los campos especificados."""
        # Arrange
        mock_epic_repository.bulk_create.return_value = [sample_epic]
        use_cases = EpicUseCases(repository=mock_epic_repository)

        epic_requests = [
            CreateEpicRequest(
                subject="Full Epic",
                description="Full description",
                project_id=1,
                status=2,
                assigned_to_id=3,
                color="#123456",
                tags=["tag1", "tag2"],
                client_requirement=True,
                team_requirement=True,
            ),
        ]
        request = BulkCreateEpicsRequest(project_id=1, epics=epic_requests)

        # Act
        await use_cases.bulk_create_epics(request)

        # Assert
        created_epics = mock_epic_repository.bulk_create.call_args[0][0]
        epic = created_epics[0]
        assert epic.subject == "Full Epic"
        assert epic.description == "Full description"
        assert epic.status == 2
        assert epic.assigned_to == 3
        assert epic.color == "#123456"
        assert set(epic.tags) == {"tag1", "tag2"}
        assert epic.client_requirement is True
        assert epic.team_requirement is True


class TestGetFilters:
    """Tests para el caso de uso get_filters."""

    @pytest.mark.asyncio
    async def test_get_filters_success(self, mock_epic_repository: MagicMock) -> None:
        """Debe retornar los filtros disponibles."""
        # Arrange
        filters: dict[str, Any] = {
            "statuses": [{"id": 1, "name": "New"}, {"id": 2, "name": "In Progress"}],
            "assigned_to": [{"id": 1, "name": "User 1"}],
            "tags": ["tag1", "tag2"],
        }
        mock_epic_repository.get_filters.return_value = filters
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.get_filters(project_id=1)

        # Assert
        assert result == filters
        mock_epic_repository.get_filters.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_filters_empty(self, mock_epic_repository: MagicMock) -> None:
        """Debe retornar diccionario vacío cuando no hay filtros."""
        # Arrange
        mock_epic_repository.get_filters.return_value = {}
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.get_filters(project_id=1)

        # Assert
        assert result == {}


class TestUpvoteEpic:
    """Tests para el caso de uso upvote_epic."""

    @pytest.mark.asyncio
    async def test_upvote_epic_success(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe añadir voto positivo exitosamente."""
        # Arrange
        mock_epic_repository.get_by_id.return_value = sample_epic
        mock_epic_repository.upvote.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.upvote_epic(epic_id=1)

        # Assert
        assert result == sample_epic
        mock_epic_repository.get_by_id.assert_called_once_with(1)
        mock_epic_repository.upvote.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_upvote_epic_not_found(self, mock_epic_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando el epic no existe."""
        # Arrange
        mock_epic_repository.get_by_id.return_value = None
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.upvote_epic(epic_id=999)

        mock_epic_repository.upvote.assert_not_called()


class TestDownvoteEpic:
    """Tests para el caso de uso downvote_epic."""

    @pytest.mark.asyncio
    async def test_downvote_epic_success(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe quitar voto exitosamente."""
        # Arrange
        mock_epic_repository.get_by_id.return_value = sample_epic
        mock_epic_repository.downvote.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.downvote_epic(epic_id=1)

        # Assert
        assert result == sample_epic
        mock_epic_repository.get_by_id.assert_called_once_with(1)
        mock_epic_repository.downvote.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_downvote_epic_not_found(self, mock_epic_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando el epic no existe."""
        # Arrange
        mock_epic_repository.get_by_id.return_value = None
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.downvote_epic(epic_id=999)

        mock_epic_repository.downvote.assert_not_called()


class TestWatchEpic:
    """Tests para el caso de uso watch_epic."""

    @pytest.mark.asyncio
    async def test_watch_epic_success(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe añadir observador exitosamente."""
        # Arrange
        mock_epic_repository.get_by_id.return_value = sample_epic
        mock_epic_repository.watch.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.watch_epic(epic_id=1)

        # Assert
        assert result == sample_epic
        mock_epic_repository.get_by_id.assert_called_once_with(1)
        mock_epic_repository.watch.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_watch_epic_not_found(self, mock_epic_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando el epic no existe."""
        # Arrange
        mock_epic_repository.get_by_id.return_value = None
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.watch_epic(epic_id=999)

        mock_epic_repository.watch.assert_not_called()


class TestUnwatchEpic:
    """Tests para el caso de uso unwatch_epic."""

    @pytest.mark.asyncio
    async def test_unwatch_epic_success(
        self, mock_epic_repository: MagicMock, sample_epic: Epic
    ) -> None:
        """Debe quitar observador exitosamente."""
        # Arrange
        mock_epic_repository.get_by_id.return_value = sample_epic
        mock_epic_repository.unwatch.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.unwatch_epic(epic_id=1)

        # Assert
        assert result == sample_epic
        mock_epic_repository.get_by_id.assert_called_once_with(1)
        mock_epic_repository.unwatch.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_unwatch_epic_not_found(self, mock_epic_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando el epic no existe."""
        # Arrange
        mock_epic_repository.get_by_id.return_value = None
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.unwatch_epic(epic_id=999)

        mock_epic_repository.unwatch.assert_not_called()


class TestEpicUseCasesInitialization:
    """Tests para la inicialización de EpicUseCases."""

    def test_initialization_with_repository(self, mock_epic_repository: MagicMock) -> None:
        """Debe inicializarse correctamente con el repositorio."""
        # Act
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Assert
        assert use_cases.repository == mock_epic_repository
