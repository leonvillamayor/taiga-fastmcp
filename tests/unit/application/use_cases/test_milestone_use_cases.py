"""Tests unitarios para MilestoneUseCases.

Este módulo contiene tests exhaustivos para todos los métodos
de MilestoneUseCases, cubriendo casos de éxito, errores y edge cases.
"""

from datetime import date, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.application.use_cases.milestone_use_cases import (
    CreateMilestoneRequest,
    ListMilestonesRequest,
    MilestoneUseCases,
    UpdateMilestoneRequest,
)
from src.domain.entities.milestone import Milestone
from src.domain.exceptions import ResourceNotFoundError


class TestCreateMilestone:
    """Tests para el caso de uso create_milestone."""

    @pytest.mark.asyncio
    async def test_create_milestone_success(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe crear un milestone exitosamente."""
        # Arrange
        mock_milestone_repository.create.return_value = sample_milestone
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        request = CreateMilestoneRequest(
            name="Sprint 1",
            project_id=1,
            estimated_start=date(2024, 1, 1),
            estimated_finish=date(2024, 1, 15),
            disponibility=0.8,
            order=1,
        )

        # Act
        result = await use_cases.create_milestone(request)

        # Assert
        assert result == sample_milestone
        mock_milestone_repository.create.assert_called_once()
        created_milestone = mock_milestone_repository.create.call_args[0][0]
        assert created_milestone.name == "Sprint 1"
        assert created_milestone.project_id == 1

    @pytest.mark.asyncio
    async def test_create_milestone_with_defaults(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe crear un milestone con valores por defecto."""
        # Arrange
        mock_milestone_repository.create.return_value = sample_milestone
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        request = CreateMilestoneRequest(
            name="Sprint 2",
            project_id=1,
        )

        # Act
        result = await use_cases.create_milestone(request)

        # Assert
        assert result == sample_milestone
        created_milestone = mock_milestone_repository.create.call_args[0][0]
        assert created_milestone.name == "Sprint 2"
        assert created_milestone.disponibility == 1.0  # Default
        assert created_milestone.order == 1  # Default

    @pytest.mark.asyncio
    async def test_create_milestone_with_dates(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe crear un milestone con fechas estimadas."""
        # Arrange
        mock_milestone_repository.create.return_value = sample_milestone
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        start_date = date(2024, 2, 1)
        finish_date = date(2024, 2, 28)
        request = CreateMilestoneRequest(
            name="Sprint 3",
            project_id=1,
            estimated_start=start_date,
            estimated_finish=finish_date,
        )

        # Act
        await use_cases.create_milestone(request)

        # Assert
        created_milestone = mock_milestone_repository.create.call_args[0][0]
        assert created_milestone.estimated_start == start_date
        assert created_milestone.estimated_finish == finish_date


class TestGetMilestone:
    """Tests para el caso de uso get_milestone."""

    @pytest.mark.asyncio
    async def test_get_milestone_success(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe retornar el milestone cuando existe."""
        # Arrange
        mock_milestone_repository.get_by_id.return_value = sample_milestone
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act
        result = await use_cases.get_milestone(milestone_id=1)

        # Assert
        assert result == sample_milestone
        mock_milestone_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_milestone_not_found(self, mock_milestone_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_milestone_repository.get_by_id.return_value = None
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await use_cases.get_milestone(milestone_id=999)

        assert "Milestone 999 not found" in str(exc_info.value)
        mock_milestone_repository.get_by_id.assert_called_once_with(999)


class TestListMilestones:
    """Tests para el caso de uso list_milestones."""

    @pytest.mark.asyncio
    async def test_list_milestones_no_filters(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe listar milestones sin filtros."""
        # Arrange
        mock_milestone_repository.list.return_value = [sample_milestone]
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        request = ListMilestonesRequest()

        # Act
        result = await use_cases.list_milestones(request)

        # Assert
        assert result == [sample_milestone]
        mock_milestone_repository.list.assert_called_once_with(filters={}, limit=None, offset=None)

    @pytest.mark.asyncio
    async def test_list_milestones_by_project(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe filtrar milestones por proyecto."""
        # Arrange
        mock_milestone_repository.list.return_value = [sample_milestone]
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        request = ListMilestonesRequest(project_id=1)

        # Act
        result = await use_cases.list_milestones(request)

        # Assert
        assert result == [sample_milestone]
        mock_milestone_repository.list.assert_called_once_with(
            filters={"project": 1}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_milestones_by_closed_status(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe filtrar milestones por estado cerrado."""
        # Arrange
        mock_milestone_repository.list.return_value = [sample_milestone]
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        request = ListMilestonesRequest(is_closed=True)

        # Act
        await use_cases.list_milestones(request)

        # Assert
        mock_milestone_repository.list.assert_called_once_with(
            filters={"closed": True}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_milestones_with_pagination(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe aplicar paginación correctamente."""
        # Arrange
        mock_milestone_repository.list.return_value = [sample_milestone]
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        request = ListMilestonesRequest(limit=10, offset=20)

        # Act
        await use_cases.list_milestones(request)

        # Assert
        mock_milestone_repository.list.assert_called_once_with(filters={}, limit=10, offset=20)

    @pytest.mark.asyncio
    async def test_list_milestones_with_all_filters(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe aplicar todos los filtros combinados."""
        # Arrange
        mock_milestone_repository.list.return_value = [sample_milestone]
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        request = ListMilestonesRequest(project_id=1, is_closed=False, limit=50, offset=10)

        # Act
        await use_cases.list_milestones(request)

        # Assert
        mock_milestone_repository.list.assert_called_once_with(
            filters={"project": 1, "closed": False}, limit=50, offset=10
        )

    @pytest.mark.asyncio
    async def test_list_milestones_empty_result(self, mock_milestone_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay milestones."""
        # Arrange
        mock_milestone_repository.list.return_value = []
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        request = ListMilestonesRequest()

        # Act
        result = await use_cases.list_milestones(request)

        # Assert
        assert result == []


class TestListByProject:
    """Tests para el caso de uso list_by_project."""

    @pytest.mark.asyncio
    async def test_list_by_project_success(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe listar milestones de un proyecto."""
        # Arrange
        mock_milestone_repository.list_by_project.return_value = [sample_milestone]
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act
        result = await use_cases.list_by_project(project_id=1)

        # Assert
        assert result == [sample_milestone]
        mock_milestone_repository.list_by_project.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_by_project_empty(self, mock_milestone_repository: MagicMock) -> None:
        """Debe retornar lista vacía si el proyecto no tiene milestones."""
        # Arrange
        mock_milestone_repository.list_by_project.return_value = []
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act
        result = await use_cases.list_by_project(project_id=1)

        # Assert
        assert result == []


class TestListOpen:
    """Tests para el caso de uso list_open."""

    @pytest.mark.asyncio
    async def test_list_open_success(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe listar milestones abiertos de un proyecto."""
        # Arrange
        mock_milestone_repository.list_open.return_value = [sample_milestone]
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act
        result = await use_cases.list_open(project_id=1)

        # Assert
        assert result == [sample_milestone]
        mock_milestone_repository.list_open.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_open_empty(self, mock_milestone_repository: MagicMock) -> None:
        """Debe retornar lista vacía si no hay milestones abiertos."""
        # Arrange
        mock_milestone_repository.list_open.return_value = []
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act
        result = await use_cases.list_open(project_id=1)

        # Assert
        assert result == []


class TestListClosed:
    """Tests para el caso de uso list_closed."""

    @pytest.mark.asyncio
    async def test_list_closed_success(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe listar milestones cerrados de un proyecto."""
        # Arrange
        closed_milestone = Milestone(
            id=2,
            name="Sprint 0",
            slug="sprint-0",
            project_id=1,
            estimated_start=datetime(2023, 12, 1),
            estimated_finish=datetime(2023, 12, 15),
            is_closed=True,
            disponibility=1.0,
            order=1,
        )
        mock_milestone_repository.list_closed.return_value = [closed_milestone]
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act
        result = await use_cases.list_closed(project_id=1)

        # Assert
        assert result == [closed_milestone]
        mock_milestone_repository.list_closed.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_closed_empty(self, mock_milestone_repository: MagicMock) -> None:
        """Debe retornar lista vacía si no hay milestones cerrados."""
        # Arrange
        mock_milestone_repository.list_closed.return_value = []
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act
        result = await use_cases.list_closed(project_id=1)

        # Assert
        assert result == []


class TestGetCurrent:
    """Tests para el caso de uso get_current."""

    @pytest.mark.asyncio
    async def test_get_current_success(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe retornar el milestone actual cuando existe."""
        # Arrange
        mock_milestone_repository.get_current.return_value = sample_milestone
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act
        result = await use_cases.get_current(project_id=1)

        # Assert
        assert result == sample_milestone
        mock_milestone_repository.get_current.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_current_none(self, mock_milestone_repository: MagicMock) -> None:
        """Debe retornar None si no hay milestone activo."""
        # Arrange
        mock_milestone_repository.get_current.return_value = None
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act
        result = await use_cases.get_current(project_id=1)

        # Assert
        assert result is None
        mock_milestone_repository.get_current.assert_called_once_with(1)


class TestUpdateMilestone:
    """Tests para el caso de uso update_milestone."""

    @pytest.mark.asyncio
    async def test_update_milestone_success(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe actualizar el milestone exitosamente."""
        # Arrange
        mock_milestone_repository.get_by_id.return_value = sample_milestone
        updated_milestone = Milestone(
            id=1,
            name="Sprint 1 - Updated",
            slug="sprint-1",
            project_id=1,
            estimated_start=datetime(2024, 1, 1),
            estimated_finish=datetime(2024, 1, 15),
            is_closed=False,
            disponibility=1.0,
            order=1,
        )
        mock_milestone_repository.update.return_value = updated_milestone
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        request = UpdateMilestoneRequest(milestone_id=1, name="Sprint 1 - Updated")

        # Act
        result = await use_cases.update_milestone(request)

        # Assert
        assert result == updated_milestone
        mock_milestone_repository.get_by_id.assert_called_once_with(1)
        mock_milestone_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_milestone_not_found(self, mock_milestone_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_milestone_repository.get_by_id.return_value = None
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        request = UpdateMilestoneRequest(milestone_id=999, name="New Name")

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.update_milestone(request)

        mock_milestone_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_milestone_partial_fields(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe actualizar solo los campos proporcionados."""
        # Arrange
        mock_milestone_repository.get_by_id.return_value = sample_milestone
        mock_milestone_repository.update.return_value = sample_milestone
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        request = UpdateMilestoneRequest(milestone_id=1, name="Only Name Updated")

        # Act
        await use_cases.update_milestone(request)

        # Assert
        updated_milestone = mock_milestone_repository.update.call_args[0][0]
        assert updated_milestone.name == "Only Name Updated"
        # Other fields remain unchanged
        assert updated_milestone.project_id == sample_milestone.project_id

    @pytest.mark.asyncio
    async def test_update_milestone_all_fields(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe actualizar todos los campos cuando se proporcionan."""
        # Arrange
        mock_milestone_repository.get_by_id.return_value = sample_milestone
        mock_milestone_repository.update.return_value = sample_milestone
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        new_start = date(2024, 3, 1)
        new_finish = date(2024, 3, 15)
        request = UpdateMilestoneRequest(
            milestone_id=1,
            name="New Name",
            estimated_start=new_start,
            estimated_finish=new_finish,
            is_closed=True,
            disponibility=0.5,
            order=2,
        )

        # Act
        await use_cases.update_milestone(request)

        # Assert
        updated_milestone = mock_milestone_repository.update.call_args[0][0]
        assert updated_milestone.name == "New Name"
        assert updated_milestone.estimated_start == new_start
        assert updated_milestone.estimated_finish == new_finish
        assert updated_milestone.is_closed is True
        assert updated_milestone.disponibility == 0.5
        assert updated_milestone.order == 2


class TestDeleteMilestone:
    """Tests para el caso de uso delete_milestone."""

    @pytest.mark.asyncio
    async def test_delete_milestone_success(self, mock_milestone_repository: MagicMock) -> None:
        """Debe eliminar el milestone exitosamente."""
        # Arrange
        mock_milestone_repository.delete.return_value = True
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act
        result = await use_cases.delete_milestone(milestone_id=1)

        # Assert
        assert result is True
        mock_milestone_repository.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_milestone_not_found(self, mock_milestone_repository: MagicMock) -> None:
        """Debe retornar False cuando el milestone no existe."""
        # Arrange
        mock_milestone_repository.delete.return_value = False
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act
        result = await use_cases.delete_milestone(milestone_id=999)

        # Assert
        assert result is False


class TestCloseMilestone:
    """Tests para el caso de uso close_milestone."""

    @pytest.mark.asyncio
    async def test_close_milestone_success(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe cerrar el milestone exitosamente."""
        # Arrange
        # Ensure milestone is open initially
        sample_milestone.is_closed = False
        mock_milestone_repository.get_by_id.return_value = sample_milestone
        mock_milestone_repository.update.return_value = sample_milestone
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act
        await use_cases.close_milestone(milestone_id=1)

        # Assert
        mock_milestone_repository.get_by_id.assert_called_once_with(1)
        mock_milestone_repository.update.assert_called_once()
        # Verify milestone.close() was called (sets is_closed=True)
        updated_milestone = mock_milestone_repository.update.call_args[0][0]
        assert updated_milestone.is_closed is True

    @pytest.mark.asyncio
    async def test_close_milestone_not_found(self, mock_milestone_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_milestone_repository.get_by_id.return_value = None
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.close_milestone(milestone_id=999)

        mock_milestone_repository.update.assert_not_called()


class TestReopenMilestone:
    """Tests para el caso de uso reopen_milestone."""

    @pytest.mark.asyncio
    async def test_reopen_milestone_success(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe reabrir el milestone exitosamente."""
        # Arrange
        # Ensure milestone is closed initially
        sample_milestone.is_closed = True
        mock_milestone_repository.get_by_id.return_value = sample_milestone
        mock_milestone_repository.update.return_value = sample_milestone
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act
        await use_cases.reopen_milestone(milestone_id=1)

        # Assert
        mock_milestone_repository.get_by_id.assert_called_once_with(1)
        mock_milestone_repository.update.assert_called_once()
        # Verify milestone.reopen() was called (sets is_closed=False)
        updated_milestone = mock_milestone_repository.update.call_args[0][0]
        assert updated_milestone.is_closed is False

    @pytest.mark.asyncio
    async def test_reopen_milestone_not_found(self, mock_milestone_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_milestone_repository.get_by_id.return_value = None
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.reopen_milestone(milestone_id=999)

        mock_milestone_repository.update.assert_not_called()


class TestGetStats:
    """Tests para el caso de uso get_stats."""

    @pytest.mark.asyncio
    async def test_get_stats_success(
        self, mock_milestone_repository: MagicMock, sample_milestone: Milestone
    ) -> None:
        """Debe retornar estadísticas del milestone."""
        # Arrange
        stats: dict[str, Any] = {
            "total_user_stories": 10,
            "completed_user_stories": 7,
            "total_tasks": 25,
            "completed_tasks": 20,
            "total_points": 50.0,
            "completed_points": 35.0,
        }
        mock_milestone_repository.get_by_id.return_value = sample_milestone
        mock_milestone_repository.get_stats.return_value = stats
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act
        result = await use_cases.get_stats(milestone_id=1)

        # Assert
        assert result == stats
        mock_milestone_repository.get_by_id.assert_called_once_with(1)
        mock_milestone_repository.get_stats.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_stats_not_found(self, mock_milestone_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando el milestone no existe."""
        # Arrange
        mock_milestone_repository.get_by_id.return_value = None
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.get_stats(milestone_id=999)

        mock_milestone_repository.get_stats.assert_not_called()


class TestMilestoneUseCasesInitialization:
    """Tests para la inicialización de MilestoneUseCases."""

    def test_initialization_with_repository(self, mock_milestone_repository: MagicMock) -> None:
        """Debe inicializarse correctamente con el repositorio."""
        # Act
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        # Assert
        assert use_cases.repository == mock_milestone_repository
