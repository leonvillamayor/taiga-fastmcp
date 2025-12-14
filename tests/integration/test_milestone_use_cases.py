"""
Tests de integración para casos de uso de milestones.
Implementa tests para la capa de aplicación.
"""

from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.milestone_use_cases import (
    CreateMilestoneRequest,
    ListMilestonesRequest,
    MilestoneUseCases,
    UpdateMilestoneRequest,
)
from src.domain.entities.milestone import Milestone
from src.domain.exceptions import ResourceNotFoundError


@pytest.fixture
def mock_milestone_repository() -> AsyncMock:
    """Crea un mock del repositorio de milestones."""
    return AsyncMock()


@pytest.fixture
def sample_milestone() -> Milestone:
    """Crea un milestone de ejemplo para tests."""
    return Milestone(
        id=1,
        project_id=100,
        name="Sprint 1",
        is_closed=False,
        slug="sprint-1",
    )


@pytest.fixture
def sample_milestones_list(sample_milestone: Milestone) -> list[Milestone]:
    """Lista de milestones de ejemplo."""
    return [
        sample_milestone,
        Milestone(id=2, project_id=100, name="Sprint 2", slug="sprint-2"),
    ]


@pytest.mark.integration
@pytest.mark.asyncio
class TestMilestoneUseCases:
    """Tests de integración para casos de uso de milestones."""

    async def test_list_milestones(
        self,
        mock_milestone_repository: AsyncMock,
        sample_milestones_list: list[Milestone],
    ) -> None:
        """Verifica el caso de uso de listar milestones."""
        mock_milestone_repository.list.return_value = sample_milestones_list
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        request = ListMilestonesRequest(project_id=100, is_closed=False)

        result = await use_cases.list_milestones(request)

        assert len(result) == 2
        mock_milestone_repository.list.assert_called_once()

    async def test_list_by_project(
        self,
        mock_milestone_repository: AsyncMock,
        sample_milestones_list: list[Milestone],
    ) -> None:
        """Verifica el caso de uso de listar milestones por proyecto."""
        mock_milestone_repository.list_by_project.return_value = sample_milestones_list
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        result = await use_cases.list_by_project(project_id=100)

        assert len(result) == 2
        mock_milestone_repository.list_by_project.assert_called_once_with(100)

    async def test_create_milestone(
        self, mock_milestone_repository: AsyncMock, sample_milestone: Milestone
    ) -> None:
        """Verifica el caso de uso de crear un milestone."""
        mock_milestone_repository.create.return_value = sample_milestone
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        request = CreateMilestoneRequest(
            name="Sprint 1",
            project_id=100,
        )

        result = await use_cases.create_milestone(request)

        assert result.id == 1
        assert result.name == "Sprint 1"
        mock_milestone_repository.create.assert_called_once()

    async def test_get_milestone_by_id(
        self, mock_milestone_repository: AsyncMock, sample_milestone: Milestone
    ) -> None:
        """Verifica el caso de uso de obtener milestone por ID."""
        mock_milestone_repository.get_by_id.return_value = sample_milestone
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        result = await use_cases.get_milestone(milestone_id=1)

        assert result.id == 1
        mock_milestone_repository.get_by_id.assert_called_once_with(1)

    async def test_get_milestone_by_id_not_found(
        self, mock_milestone_repository: AsyncMock
    ) -> None:
        """Verifica que se lance ResourceNotFoundError si el milestone no existe."""
        mock_milestone_repository.get_by_id.return_value = None
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        with pytest.raises(ResourceNotFoundError, match="Milestone 999 not found"):
            await use_cases.get_milestone(milestone_id=999)

    async def test_get_current(
        self, mock_milestone_repository: AsyncMock, sample_milestone: Milestone
    ) -> None:
        """Verifica el caso de uso de obtener milestone actual."""
        mock_milestone_repository.get_current.return_value = sample_milestone
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        result = await use_cases.get_current(project_id=100)

        assert result is not None
        assert result.id == 1
        mock_milestone_repository.get_current.assert_called_once_with(100)

    async def test_get_current_none(self, mock_milestone_repository: AsyncMock) -> None:
        """Verifica que get_current devuelva None si no hay milestone activo."""
        mock_milestone_repository.get_current.return_value = None
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        result = await use_cases.get_current(project_id=100)

        assert result is None

    async def test_update_milestone(
        self, mock_milestone_repository: AsyncMock, sample_milestone: Milestone
    ) -> None:
        """Verifica el caso de uso de actualizar un milestone."""
        updated = Milestone(
            id=1,
            project_id=100,
            name="Updated Sprint",
            is_closed=True,
            slug="sprint-1",
        )
        mock_milestone_repository.get_by_id.return_value = sample_milestone
        mock_milestone_repository.update.return_value = updated
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        request = UpdateMilestoneRequest(milestone_id=1, name="Updated Sprint", is_closed=True)

        result = await use_cases.update_milestone(request)

        assert result.name == "Updated Sprint"
        assert result.is_closed is True
        mock_milestone_repository.update.assert_called_once()

    async def test_update_milestone_not_found(self, mock_milestone_repository: AsyncMock) -> None:
        """Verifica que update lance ResourceNotFoundError si no existe."""
        mock_milestone_repository.get_by_id.return_value = None
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)
        request = UpdateMilestoneRequest(milestone_id=999, name="Updated")

        with pytest.raises(ResourceNotFoundError, match="Milestone 999 not found"):
            await use_cases.update_milestone(request)

    async def test_delete_milestone(self, mock_milestone_repository: AsyncMock) -> None:
        """Verifica el caso de uso de eliminar un milestone."""
        mock_milestone_repository.delete.return_value = True
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        result = await use_cases.delete_milestone(milestone_id=1)

        assert result is True
        mock_milestone_repository.delete.assert_called_once_with(1)

    async def test_delete_milestone_not_found(self, mock_milestone_repository: AsyncMock) -> None:
        """Verifica que delete devuelva False si no existe."""
        mock_milestone_repository.delete.return_value = False
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        result = await use_cases.delete_milestone(milestone_id=999)

        assert result is False

    async def test_list_open(
        self,
        mock_milestone_repository: AsyncMock,
        sample_milestones_list: list[Milestone],
    ) -> None:
        """Verifica el caso de uso de listar milestones abiertos."""
        mock_milestone_repository.list_open.return_value = sample_milestones_list
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        result = await use_cases.list_open(project_id=100)

        assert len(result) == 2
        mock_milestone_repository.list_open.assert_called_once_with(100)

    async def test_list_closed(
        self,
        mock_milestone_repository: AsyncMock,
        sample_milestones_list: list[Milestone],
    ) -> None:
        """Verifica el caso de uso de listar milestones cerrados."""
        mock_milestone_repository.list_closed.return_value = sample_milestones_list
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        result = await use_cases.list_closed(project_id=100)

        assert len(result) == 2
        mock_milestone_repository.list_closed.assert_called_once_with(100)

    async def test_get_stats(
        self, mock_milestone_repository: AsyncMock, sample_milestone: Milestone
    ) -> None:
        """Verifica el caso de uso de obtener estadísticas del milestone."""
        stats = {"total_points": 100, "completed_points": 50}
        mock_milestone_repository.get_by_id.return_value = sample_milestone
        mock_milestone_repository.get_stats.return_value = stats
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        result = await use_cases.get_stats(milestone_id=1)

        assert "total_points" in result
        mock_milestone_repository.get_stats.assert_called_once_with(1)

    async def test_close_milestone(
        self, mock_milestone_repository: AsyncMock, sample_milestone: Milestone
    ) -> None:
        """Verifica el caso de uso de cerrar un milestone."""
        closed = Milestone(id=1, project_id=100, name="Sprint 1", is_closed=True, slug="sprint-1")
        mock_milestone_repository.get_by_id.return_value = sample_milestone
        mock_milestone_repository.update.return_value = closed
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        result = await use_cases.close_milestone(milestone_id=1)

        assert result.is_closed is True
        mock_milestone_repository.update.assert_called_once()

    async def test_reopen_milestone(self, mock_milestone_repository: AsyncMock) -> None:
        """Verifica el caso de uso de reabrir un milestone."""
        closed_milestone = Milestone(
            id=1, project_id=100, name="Sprint 1", is_closed=True, slug="sprint-1"
        )
        reopened = Milestone(
            id=1, project_id=100, name="Sprint 1", is_closed=False, slug="sprint-1"
        )
        mock_milestone_repository.get_by_id.return_value = closed_milestone
        mock_milestone_repository.update.return_value = reopened
        use_cases = MilestoneUseCases(repository=mock_milestone_repository)

        result = await use_cases.reopen_milestone(milestone_id=1)

        assert result.is_closed is False
        mock_milestone_repository.update.assert_called_once()
