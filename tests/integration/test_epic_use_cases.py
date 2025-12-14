"""
Tests de integración para casos de uso de épicas.
Implementa tests para la capa de aplicación.
"""

from unittest.mock import AsyncMock

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


@pytest.fixture
def mock_epic_repository() -> AsyncMock:
    """Crea un mock del repositorio de épicas."""
    return AsyncMock()


@pytest.fixture
def sample_epic() -> Epic:
    """Crea una épica de ejemplo para tests."""
    return Epic(
        id=456789,
        version=1,
        project=309804,
        subject="Test Epic",
        description="Test description",
        color="#A5694F",
        status=1,
        assigned_to=888691,
        tags=["test", "auth"],
        ref=5,
    )


@pytest.fixture
def sample_epics_list(sample_epic: Epic) -> list[Epic]:
    """Lista de épicas de ejemplo."""
    return [
        sample_epic,
        Epic(
            id=456790,
            version=1,
            project=309804,
            subject="Second Epic",
            color="#FF0000",
            ref=6,
        ),
    ]


@pytest.mark.integration
@pytest.mark.asyncio
class TestEpicUseCases:
    """Tests de integración para casos de uso de épicas"""

    async def test_list_epics(
        self, mock_epic_repository: AsyncMock, sample_epics_list: list[Epic]
    ) -> None:
        """
        Verifica el caso de uso de listar épicas con filtros.
        """
        # Arrange
        mock_epic_repository.list.return_value = sample_epics_list
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = ListEpicsRequest(
            project_id=309804,
            status_id=1,
            assigned_to_id=888691,
        )

        # Act
        result = await use_cases.list_epics(request)

        # Assert
        assert len(result) == 2
        assert result[0].id == 456789
        mock_epic_repository.list.assert_called_once()

    async def test_list_epics_by_project(
        self, mock_epic_repository: AsyncMock, sample_epics_list: list[Epic]
    ) -> None:
        """
        Verifica el caso de uso de listar épicas de un proyecto.
        """
        # Arrange
        mock_epic_repository.list_by_project.return_value = sample_epics_list
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.list_by_project(project_id=309804)

        # Assert
        assert len(result) == 2
        mock_epic_repository.list_by_project.assert_called_once_with(309804)

    async def test_create_epic(self, mock_epic_repository: AsyncMock, sample_epic: Epic) -> None:
        """
        Verifica el caso de uso de crear una épica.
        """
        # Arrange
        mock_epic_repository.create.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = CreateEpicRequest(
            subject="Test Epic",
            description="Test description",
            project_id=309804,
            status=1,
            assigned_to_id=888691,
            color="#A5694F",
            tags=["test", "auth"],
        )

        # Act
        result = await use_cases.create_epic(request)

        # Assert
        assert result.id == 456789
        assert result.subject == "Test Epic"
        mock_epic_repository.create.assert_called_once()

    async def test_get_epic_by_id(self, mock_epic_repository: AsyncMock, sample_epic: Epic) -> None:
        """
        Verifica el caso de uso de obtener épica por ID.
        """
        # Arrange
        mock_epic_repository.get_by_id.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.get_epic(epic_id=456789)

        # Assert
        assert result.id == 456789
        assert result.subject == "Test Epic"
        mock_epic_repository.get_by_id.assert_called_once_with(456789)

    async def test_get_epic_by_id_not_found(self, mock_epic_repository: AsyncMock) -> None:
        """
        Verifica que se lance ResourceNotFoundError si la épica no existe.
        """
        # Arrange
        mock_epic_repository.get_by_id.return_value = None
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError, match="Epic 999999 not found"):
            await use_cases.get_epic(epic_id=999999)

    async def test_get_epic_by_ref(
        self, mock_epic_repository: AsyncMock, sample_epic: Epic
    ) -> None:
        """
        Verifica el caso de uso de obtener épica por referencia.
        """
        # Arrange
        mock_epic_repository.get_by_ref.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.get_epic_by_ref(project_id=309804, ref=5)

        # Assert
        assert result.id == 456789
        assert result.ref == 5
        mock_epic_repository.get_by_ref.assert_called_once_with(309804, 5)

    async def test_get_epic_by_ref_not_found(self, mock_epic_repository: AsyncMock) -> None:
        """
        Verifica que se lance ResourceNotFoundError si no se encuentra por ref.
        """
        # Arrange
        mock_epic_repository.get_by_ref.return_value = None
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError, match="ref=5 not found"):
            await use_cases.get_epic_by_ref(project_id=309804, ref=5)

    async def test_update_epic(self, mock_epic_repository: AsyncMock, sample_epic: Epic) -> None:
        """
        Verifica el caso de uso de actualizar una épica.
        """
        # Arrange
        updated_epic = Epic(
            id=456789,
            version=2,
            project=309804,
            subject="Updated Subject",
            status=2,
            ref=5,
        )
        mock_epic_repository.get_by_id.return_value = sample_epic
        mock_epic_repository.update.return_value = updated_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = UpdateEpicRequest(
            epic_id=456789,
            subject="Updated Subject",
            status=2,
        )

        # Act
        result = await use_cases.update_epic(request)

        # Assert
        assert result.subject == "Updated Subject"
        assert result.status == 2
        mock_epic_repository.update.assert_called_once()

    async def test_update_epic_not_found(self, mock_epic_repository: AsyncMock) -> None:
        """
        Verifica que update lance ResourceNotFoundError si la épica no existe.
        """
        # Arrange
        mock_epic_repository.get_by_id.return_value = None
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = UpdateEpicRequest(
            epic_id=999999,
            subject="Updated Subject",
        )

        # Act & Assert
        with pytest.raises(ResourceNotFoundError, match="Epic 999999 not found"):
            await use_cases.update_epic(request)

    async def test_delete_epic(self, mock_epic_repository: AsyncMock) -> None:
        """
        Verifica el caso de uso de eliminar una épica.
        """
        # Arrange
        mock_epic_repository.delete.return_value = True
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.delete_epic(epic_id=456789)

        # Assert
        assert result is True
        mock_epic_repository.delete.assert_called_once_with(456789)

    async def test_delete_epic_not_found(self, mock_epic_repository: AsyncMock) -> None:
        """
        Verifica que delete devuelva False si la épica no existe.
        """
        # Arrange
        mock_epic_repository.delete.return_value = False
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.delete_epic(epic_id=999999)

        # Assert
        assert result is False

    async def test_bulk_create_epics(
        self, mock_epic_repository: AsyncMock, sample_epics_list: list[Epic]
    ) -> None:
        """
        Verifica el caso de uso de crear múltiples épicas.
        """
        # Arrange
        mock_epic_repository.bulk_create.return_value = sample_epics_list
        use_cases = EpicUseCases(repository=mock_epic_repository)
        request = BulkCreateEpicsRequest(
            project_id=309804,
            epics=[
                CreateEpicRequest(
                    subject="Epic 1",
                    project_id=309804,
                ),
                CreateEpicRequest(
                    subject="Epic 2",
                    project_id=309804,
                ),
            ],
        )

        # Act
        result = await use_cases.bulk_create_epics(request)

        # Assert
        assert len(result) == 2
        mock_epic_repository.bulk_create.assert_called_once()

    async def test_get_filters(self, mock_epic_repository: AsyncMock) -> None:
        """
        Verifica el caso de uso de obtener filtros disponibles.
        """
        # Arrange
        filters_data = {
            "statuses": [{"id": 1, "name": "New"}],
            "assigned_to": [{"id": 888691, "name": "User"}],
            "tags": ["auth", "test"],
        }
        mock_epic_repository.get_filters.return_value = filters_data
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.get_filters(project_id=309804)

        # Assert
        assert "statuses" in result
        assert "assigned_to" in result
        assert "tags" in result
        mock_epic_repository.get_filters.assert_called_once_with(309804)

    async def test_upvote_epic(self, mock_epic_repository: AsyncMock, sample_epic: Epic) -> None:
        """
        Verifica el caso de uso de votar positivamente una épica.
        """
        # Arrange
        voted_epic = Epic(
            id=456789,
            version=1,
            project=309804,
            subject="Test Epic",
            total_voters=1,
            ref=5,
        )
        mock_epic_repository.get_by_id.return_value = sample_epic
        mock_epic_repository.upvote.return_value = voted_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.upvote_epic(epic_id=456789)

        # Assert
        assert result.total_voters == 1
        mock_epic_repository.upvote.assert_called_once_with(456789)

    async def test_downvote_epic(self, mock_epic_repository: AsyncMock, sample_epic: Epic) -> None:
        """
        Verifica el caso de uso de quitar voto de una épica.
        """
        # Arrange
        mock_epic_repository.get_by_id.return_value = sample_epic
        mock_epic_repository.downvote.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.downvote_epic(epic_id=456789)

        # Assert
        assert result is not None
        mock_epic_repository.downvote.assert_called_once_with(456789)

    async def test_watch_epic(self, mock_epic_repository: AsyncMock, sample_epic: Epic) -> None:
        """
        Verifica el caso de uso de observar una épica.
        """
        # Arrange
        mock_epic_repository.get_by_id.return_value = sample_epic
        mock_epic_repository.watch.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.watch_epic(epic_id=456789)

        # Assert
        assert result is not None
        mock_epic_repository.watch.assert_called_once_with(456789)

    async def test_unwatch_epic(self, mock_epic_repository: AsyncMock, sample_epic: Epic) -> None:
        """
        Verifica el caso de uso de dejar de observar una épica.
        """
        # Arrange
        mock_epic_repository.get_by_id.return_value = sample_epic
        mock_epic_repository.unwatch.return_value = sample_epic
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.unwatch_epic(epic_id=456789)

        # Assert
        assert result is not None
        mock_epic_repository.unwatch.assert_called_once_with(456789)

    async def test_list_by_status(
        self, mock_epic_repository: AsyncMock, sample_epics_list: list[Epic]
    ) -> None:
        """
        Verifica el caso de uso de listar épicas por estado.
        """
        # Arrange
        mock_epic_repository.list_by_status.return_value = sample_epics_list
        use_cases = EpicUseCases(repository=mock_epic_repository)

        # Act
        result = await use_cases.list_by_status(project_id=309804, status_id=1)

        # Assert
        assert len(result) == 2
        mock_epic_repository.list_by_status.assert_called_once_with(309804, 1)
