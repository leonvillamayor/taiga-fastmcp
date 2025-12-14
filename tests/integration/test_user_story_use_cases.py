"""
Tests de integración para casos de uso de user stories.
Implementa tests para la capa de aplicación.
"""

from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.user_story_use_cases import (
    BulkCreateUserStoriesRequest,
    BulkUpdateUserStoriesRequest,
    CreateUserStoryRequest,
    ListUserStoriesRequest,
    MoveToMilestoneRequest,
    UpdateUserStoryRequest,
    UserStoryUseCases,
)
from src.domain.entities.user_story import UserStory
from src.domain.exceptions import ResourceNotFoundError


@pytest.fixture
def mock_userstory_repository() -> AsyncMock:
    """Crea un mock del repositorio de user stories."""
    return AsyncMock()


@pytest.fixture
def sample_userstory() -> UserStory:
    """Crea una user story de ejemplo para tests."""
    return UserStory(
        id=1,
        project_id=100,
        subject="Test User Story",
        description="Test description",
        status=1,
        assigned_to_id=10,
        ref=5,
        tags=["feature"],
    )


@pytest.fixture
def sample_userstories_list(sample_userstory: UserStory) -> list[UserStory]:
    """Lista de user stories de ejemplo."""
    return [
        sample_userstory,
        UserStory(id=2, project_id=100, subject="Second Story", ref=6),
    ]


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserStoryUseCases:
    """Tests de integración para casos de uso de user stories."""

    async def test_list_userstories(
        self,
        mock_userstory_repository: AsyncMock,
        sample_userstories_list: list[UserStory],
    ) -> None:
        """Verifica el caso de uso de listar user stories."""
        mock_userstory_repository.list.return_value = sample_userstories_list
        use_cases = UserStoryUseCases(repository=mock_userstory_repository)
        request = ListUserStoriesRequest(project_id=100, status_id=1)

        result = await use_cases.list_user_stories(request)

        assert len(result) == 2
        mock_userstory_repository.list.assert_called_once()

    async def test_list_backlog(
        self,
        mock_userstory_repository: AsyncMock,
        sample_userstories_list: list[UserStory],
    ) -> None:
        """Verifica el caso de uso de listar user stories en backlog."""
        mock_userstory_repository.list_backlog.return_value = sample_userstories_list
        use_cases = UserStoryUseCases(repository=mock_userstory_repository)

        result = await use_cases.list_backlog(project_id=100)

        assert len(result) == 2
        mock_userstory_repository.list_backlog.assert_called_once_with(100)

    async def test_create_userstory(
        self, mock_userstory_repository: AsyncMock, sample_userstory: UserStory
    ) -> None:
        """Verifica el caso de uso de crear una user story."""
        mock_userstory_repository.create.return_value = sample_userstory
        use_cases = UserStoryUseCases(repository=mock_userstory_repository)
        request = CreateUserStoryRequest(
            subject="Test User Story",
            project_id=100,
            description="Test description",
        )

        result = await use_cases.create_user_story(request)

        assert result.id == 1
        assert result.subject == "Test User Story"
        mock_userstory_repository.create.assert_called_once()

    async def test_get_userstory_by_id(
        self, mock_userstory_repository: AsyncMock, sample_userstory: UserStory
    ) -> None:
        """Verifica el caso de uso de obtener user story por ID."""
        mock_userstory_repository.get_by_id.return_value = sample_userstory
        use_cases = UserStoryUseCases(repository=mock_userstory_repository)

        result = await use_cases.get_user_story(story_id=1)

        assert result.id == 1
        mock_userstory_repository.get_by_id.assert_called_once_with(1)

    async def test_get_userstory_by_id_not_found(
        self, mock_userstory_repository: AsyncMock
    ) -> None:
        """Verifica que se lance ResourceNotFoundError si la user story no existe."""
        mock_userstory_repository.get_by_id.return_value = None
        use_cases = UserStoryUseCases(repository=mock_userstory_repository)

        with pytest.raises(ResourceNotFoundError, match="UserStory 999 not found"):
            await use_cases.get_user_story(story_id=999)

    async def test_get_userstory_by_ref(
        self, mock_userstory_repository: AsyncMock, sample_userstory: UserStory
    ) -> None:
        """Verifica el caso de uso de obtener user story por referencia."""
        mock_userstory_repository.get_by_ref.return_value = sample_userstory
        use_cases = UserStoryUseCases(repository=mock_userstory_repository)

        result = await use_cases.get_user_story_by_ref(project_id=100, ref=5)

        assert result.ref == 5
        mock_userstory_repository.get_by_ref.assert_called_once_with(100, 5)

    async def test_get_userstory_by_ref_not_found(
        self, mock_userstory_repository: AsyncMock
    ) -> None:
        """Verifica que se lance ResourceNotFoundError si no se encuentra por ref."""
        mock_userstory_repository.get_by_ref.return_value = None
        use_cases = UserStoryUseCases(repository=mock_userstory_repository)

        with pytest.raises(ResourceNotFoundError, match="ref=5 not found"):
            await use_cases.get_user_story_by_ref(project_id=100, ref=5)

    async def test_update_userstory(
        self, mock_userstory_repository: AsyncMock, sample_userstory: UserStory
    ) -> None:
        """Verifica el caso de uso de actualizar una user story."""
        updated = UserStory(id=1, project_id=100, subject="Updated Subject", status=2, ref=5)
        mock_userstory_repository.get_by_id.return_value = sample_userstory
        mock_userstory_repository.update.return_value = updated
        use_cases = UserStoryUseCases(repository=mock_userstory_repository)
        request = UpdateUserStoryRequest(story_id=1, subject="Updated Subject", status=2)

        result = await use_cases.update_user_story(request)

        assert result.subject == "Updated Subject"
        mock_userstory_repository.update.assert_called_once()

    async def test_update_userstory_not_found(self, mock_userstory_repository: AsyncMock) -> None:
        """Verifica que update lance ResourceNotFoundError si no existe."""
        mock_userstory_repository.get_by_id.return_value = None
        use_cases = UserStoryUseCases(repository=mock_userstory_repository)
        request = UpdateUserStoryRequest(story_id=999, subject="Updated Subject")

        with pytest.raises(ResourceNotFoundError, match="UserStory 999 not found"):
            await use_cases.update_user_story(request)

    async def test_delete_userstory(self, mock_userstory_repository: AsyncMock) -> None:
        """Verifica el caso de uso de eliminar una user story."""
        mock_userstory_repository.delete.return_value = True
        use_cases = UserStoryUseCases(repository=mock_userstory_repository)

        result = await use_cases.delete_user_story(story_id=1)

        assert result is True
        mock_userstory_repository.delete.assert_called_once_with(1)

    async def test_delete_userstory_not_found(self, mock_userstory_repository: AsyncMock) -> None:
        """Verifica que delete devuelva False si no existe."""
        mock_userstory_repository.delete.return_value = False
        use_cases = UserStoryUseCases(repository=mock_userstory_repository)

        result = await use_cases.delete_user_story(story_id=999)

        assert result is False

    async def test_bulk_create_userstories(
        self,
        mock_userstory_repository: AsyncMock,
        sample_userstories_list: list[UserStory],
    ) -> None:
        """Verifica el caso de uso de crear múltiples user stories."""
        mock_userstory_repository.bulk_create.return_value = sample_userstories_list
        use_cases = UserStoryUseCases(repository=mock_userstory_repository)
        request = BulkCreateUserStoriesRequest(
            project_id=100,
            stories=[
                CreateUserStoryRequest(subject="Story 1", project_id=100),
                CreateUserStoryRequest(subject="Story 2", project_id=100),
            ],
        )

        result = await use_cases.bulk_create_user_stories(request)

        assert len(result) == 2
        mock_userstory_repository.bulk_create.assert_called_once()

    async def test_bulk_update_userstories(
        self,
        mock_userstory_repository: AsyncMock,
        sample_userstories_list: list[UserStory],
    ) -> None:
        """Verifica el caso de uso de actualizar múltiples user stories."""
        mock_userstory_repository.bulk_update.return_value = sample_userstories_list
        use_cases = UserStoryUseCases(repository=mock_userstory_repository)
        request = BulkUpdateUserStoriesRequest(story_ids=[1, 2], status=2, milestone_id=10)

        result = await use_cases.bulk_update_user_stories(request)

        assert len(result) == 2
        mock_userstory_repository.bulk_update.assert_called_once()

    async def test_list_by_milestone(
        self,
        mock_userstory_repository: AsyncMock,
        sample_userstories_list: list[UserStory],
    ) -> None:
        """Verifica el caso de uso de listar user stories por milestone."""
        mock_userstory_repository.list_by_milestone.return_value = sample_userstories_list
        use_cases = UserStoryUseCases(repository=mock_userstory_repository)

        result = await use_cases.list_by_milestone(milestone_id=10)

        assert len(result) == 2
        mock_userstory_repository.list_by_milestone.assert_called_once_with(10)

    async def test_move_to_milestone(
        self, mock_userstory_repository: AsyncMock, sample_userstory: UserStory
    ) -> None:
        """Verifica el caso de uso de mover a milestone."""
        mock_userstory_repository.move_to_milestone.return_value = sample_userstory
        use_cases = UserStoryUseCases(repository=mock_userstory_repository)
        request = MoveToMilestoneRequest(story_id=1, milestone_id=10)

        result = await use_cases.move_to_milestone(request)

        assert result.id == 1
        mock_userstory_repository.move_to_milestone.assert_called_once_with(1, 10)

    async def test_get_filters(self, mock_userstory_repository: AsyncMock) -> None:
        """Verifica el caso de uso de obtener filtros."""
        filters = {"statuses": [{"id": 1, "name": "New"}]}
        mock_userstory_repository.get_filters.return_value = filters
        use_cases = UserStoryUseCases(repository=mock_userstory_repository)

        result = await use_cases.get_filters(project_id=100)

        assert "statuses" in result
        mock_userstory_repository.get_filters.assert_called_once_with(100)
