"""Tests unitarios para UserStoryUseCases.

Este módulo contiene tests exhaustivos para todos los métodos
de UserStoryUseCases, cubriendo casos de éxito, errores y edge cases.
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

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


class TestCreateUserStory:
    """Tests para el caso de uso create_user_story."""

    @pytest.mark.asyncio
    async def test_create_user_story_success(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe crear una user story exitosamente."""
        # Arrange
        mock_user_story_repository.create.return_value = sample_user_story
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = CreateUserStoryRequest(
            subject="Test Story",
            description="A test story",
            project_id=1,
            status=1,
            milestone_id=1,
            assigned_to_id=1,
            tags=["test"],
        )

        # Act
        result = await use_cases.create_user_story(request)

        # Assert
        assert result == sample_user_story
        mock_user_story_repository.create.assert_called_once()
        created_story = mock_user_story_repository.create.call_args[0][0]
        assert created_story.subject == "Test Story"
        assert created_story.description == "A test story"
        assert created_story.project_id == 1

    @pytest.mark.asyncio
    async def test_create_user_story_with_defaults(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe crear una user story con valores por defecto."""
        # Arrange
        mock_user_story_repository.create.return_value = sample_user_story
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = CreateUserStoryRequest(
            subject="Minimal Story",
            project_id=1,
        )

        # Act
        result = await use_cases.create_user_story(request)

        # Assert
        assert result == sample_user_story
        created_story = mock_user_story_repository.create.call_args[0][0]
        assert created_story.subject == "Minimal Story"
        assert created_story.description == ""
        assert created_story.is_blocked is False
        assert created_story.blocked_note == ""
        assert created_story.tags == []
        assert created_story.points == {}

    @pytest.mark.asyncio
    async def test_create_user_story_with_blocking(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe crear una user story bloqueada."""
        # Arrange
        mock_user_story_repository.create.return_value = sample_user_story
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = CreateUserStoryRequest(
            subject="Blocked Story",
            project_id=1,
            is_blocked=True,
            blocked_note="Waiting for dependency",
        )

        # Act
        await use_cases.create_user_story(request)

        # Assert
        created_story = mock_user_story_repository.create.call_args[0][0]
        assert created_story.is_blocked is True
        assert created_story.blocked_note == "Waiting for dependency"

    @pytest.mark.asyncio
    async def test_create_user_story_with_points(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe crear una user story con story points."""
        # Arrange
        mock_user_story_repository.create.return_value = sample_user_story
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        points = {"design": 3.0, "development": 5.0, "testing": 2.0}
        request = CreateUserStoryRequest(
            subject="Story with points",
            project_id=1,
            points=points,
        )

        # Act
        await use_cases.create_user_story(request)

        # Assert
        created_story = mock_user_story_repository.create.call_args[0][0]
        assert created_story.points == points


class TestGetUserStory:
    """Tests para el caso de uso get_user_story."""

    @pytest.mark.asyncio
    async def test_get_user_story_success(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe retornar la user story cuando existe."""
        # Arrange
        mock_user_story_repository.get_by_id.return_value = sample_user_story
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)

        # Act
        result = await use_cases.get_user_story(story_id=1)

        # Assert
        assert result == sample_user_story
        mock_user_story_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_user_story_not_found(self, mock_user_story_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_user_story_repository.get_by_id.return_value = None
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await use_cases.get_user_story(story_id=999)

        assert "UserStory 999 not found" in str(exc_info.value)


class TestGetUserStoryByRef:
    """Tests para el caso de uso get_user_story_by_ref."""

    @pytest.mark.asyncio
    async def test_get_user_story_by_ref_success(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe retornar la user story cuando existe la referencia."""
        # Arrange
        mock_user_story_repository.get_by_ref.return_value = sample_user_story
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)

        # Act
        result = await use_cases.get_user_story_by_ref(project_id=1, ref=5)

        # Assert
        assert result == sample_user_story
        mock_user_story_repository.get_by_ref.assert_called_once_with(1, 5)

    @pytest.mark.asyncio
    async def test_get_user_story_by_ref_not_found(
        self, mock_user_story_repository: MagicMock
    ) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe la referencia."""
        # Arrange
        mock_user_story_repository.get_by_ref.return_value = None
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await use_cases.get_user_story_by_ref(project_id=1, ref=999)

        assert "UserStory with ref=999 not found in project 1" in str(exc_info.value)


class TestListUserStories:
    """Tests para el caso de uso list_user_stories."""

    @pytest.mark.asyncio
    async def test_list_user_stories_no_filters(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe listar user stories sin filtros."""
        # Arrange
        mock_user_story_repository.list.return_value = [sample_user_story]
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = ListUserStoriesRequest()

        # Act
        result = await use_cases.list_user_stories(request)

        # Assert
        assert result == [sample_user_story]
        mock_user_story_repository.list.assert_called_once_with(filters={}, limit=None, offset=None)

    @pytest.mark.asyncio
    async def test_list_user_stories_with_project_filter(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe filtrar user stories por project_id."""
        # Arrange
        mock_user_story_repository.list.return_value = [sample_user_story]
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = ListUserStoriesRequest(project_id=5)

        # Act
        await use_cases.list_user_stories(request)

        # Assert
        mock_user_story_repository.list.assert_called_once_with(
            filters={"project": 5}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_user_stories_with_milestone_filter(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe filtrar user stories por milestone_id."""
        # Arrange
        mock_user_story_repository.list.return_value = [sample_user_story]
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = ListUserStoriesRequest(milestone_id=3)

        # Act
        await use_cases.list_user_stories(request)

        # Assert
        mock_user_story_repository.list.assert_called_once_with(
            filters={"milestone": 3}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_user_stories_with_status_filter(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe filtrar user stories por status_id."""
        # Arrange
        mock_user_story_repository.list.return_value = [sample_user_story]
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = ListUserStoriesRequest(status_id=2)

        # Act
        await use_cases.list_user_stories(request)

        # Assert
        mock_user_story_repository.list.assert_called_once_with(
            filters={"status": 2}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_user_stories_with_assigned_to_filter(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe filtrar user stories por assigned_to_id."""
        # Arrange
        mock_user_story_repository.list.return_value = [sample_user_story]
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = ListUserStoriesRequest(assigned_to_id=4)

        # Act
        await use_cases.list_user_stories(request)

        # Assert
        mock_user_story_repository.list.assert_called_once_with(
            filters={"assigned_to": 4}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_user_stories_with_tags_filter(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe filtrar user stories por tags."""
        # Arrange
        mock_user_story_repository.list.return_value = [sample_user_story]
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = ListUserStoriesRequest(tags=["urgent", "backend"])

        # Act
        await use_cases.list_user_stories(request)

        # Assert
        mock_user_story_repository.list.assert_called_once_with(
            filters={"tags": ["urgent", "backend"]}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_user_stories_with_pagination(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe aplicar paginación correctamente."""
        # Arrange
        mock_user_story_repository.list.return_value = [sample_user_story]
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = ListUserStoriesRequest(limit=25, offset=50)

        # Act
        await use_cases.list_user_stories(request)

        # Assert
        mock_user_story_repository.list.assert_called_once_with(filters={}, limit=25, offset=50)

    @pytest.mark.asyncio
    async def test_list_user_stories_with_all_filters(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe aplicar todos los filtros combinados."""
        # Arrange
        mock_user_story_repository.list.return_value = [sample_user_story]
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = ListUserStoriesRequest(
            project_id=1,
            milestone_id=2,
            status_id=3,
            assigned_to_id=4,
            tags=["tag1"],
            limit=10,
            offset=5,
        )

        # Act
        await use_cases.list_user_stories(request)

        # Assert
        mock_user_story_repository.list.assert_called_once_with(
            filters={
                "project": 1,
                "milestone": 2,
                "status": 3,
                "assigned_to": 4,
                "tags": ["tag1"],
            },
            limit=10,
            offset=5,
        )

    @pytest.mark.asyncio
    async def test_list_user_stories_empty_result(
        self, mock_user_story_repository: MagicMock
    ) -> None:
        """Debe retornar lista vacía cuando no hay user stories."""
        # Arrange
        mock_user_story_repository.list.return_value = []
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = ListUserStoriesRequest()

        # Act
        result = await use_cases.list_user_stories(request)

        # Assert
        assert result == []


class TestListBacklog:
    """Tests para el caso de uso list_backlog."""

    @pytest.mark.asyncio
    async def test_list_backlog_success(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe listar user stories en el backlog."""
        # Arrange
        mock_user_story_repository.list_backlog.return_value = [sample_user_story]
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)

        # Act
        result = await use_cases.list_backlog(project_id=1)

        # Assert
        assert result == [sample_user_story]
        mock_user_story_repository.list_backlog.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_backlog_empty(self, mock_user_story_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando el backlog está vacío."""
        # Arrange
        mock_user_story_repository.list_backlog.return_value = []
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)

        # Act
        result = await use_cases.list_backlog(project_id=999)

        # Assert
        assert result == []


class TestListByMilestone:
    """Tests para el caso de uso list_by_milestone."""

    @pytest.mark.asyncio
    async def test_list_by_milestone_success(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe listar user stories de un milestone."""
        # Arrange
        mock_user_story_repository.list_by_milestone.return_value = [sample_user_story]
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)

        # Act
        result = await use_cases.list_by_milestone(milestone_id=1)

        # Assert
        assert result == [sample_user_story]
        mock_user_story_repository.list_by_milestone.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_by_milestone_empty(self, mock_user_story_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando el milestone está vacío."""
        # Arrange
        mock_user_story_repository.list_by_milestone.return_value = []
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)

        # Act
        result = await use_cases.list_by_milestone(milestone_id=99)

        # Assert
        assert result == []


class TestUpdateUserStory:
    """Tests para el caso de uso update_user_story."""

    @pytest.mark.asyncio
    async def test_update_user_story_success(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe actualizar la user story exitosamente."""
        # Arrange
        mock_user_story_repository.get_by_id.return_value = sample_user_story
        updated_story = UserStory(
            id=1,
            ref=1,
            subject="Updated Subject",
            description="Updated description",
            project_id=1,
            status=2,
            milestone_id=1,
            assigned_to_id=2,
            is_blocked=False,
            blocked_note="",
            is_closed=False,
            client_requirement=False,
            team_requirement=False,
            tags=["updated"],
            points={"design": 5.0},
            created_date=datetime(2024, 1, 1, 12, 0, 0),
            modified_date=datetime(2024, 1, 2, 12, 0, 0),
        )
        mock_user_story_repository.update.return_value = updated_story
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = UpdateUserStoryRequest(
            story_id=1,
            subject="Updated Subject",
            description="Updated description",
        )

        # Act
        result = await use_cases.update_user_story(request)

        # Assert
        assert result == updated_story
        mock_user_story_repository.get_by_id.assert_called_once_with(1)
        mock_user_story_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_story_not_found(self, mock_user_story_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_user_story_repository.get_by_id.return_value = None
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = UpdateUserStoryRequest(story_id=999, subject="New Subject")

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.update_user_story(request)

        mock_user_story_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_user_story_partial_fields(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe actualizar solo los campos proporcionados."""
        # Arrange
        mock_user_story_repository.get_by_id.return_value = sample_user_story
        mock_user_story_repository.update.return_value = sample_user_story
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = UpdateUserStoryRequest(story_id=1, subject="Only Subject Updated")

        # Act
        await use_cases.update_user_story(request)

        # Assert
        updated_story = mock_user_story_repository.update.call_args[0][0]
        assert updated_story.subject == "Only Subject Updated"
        assert updated_story.description == sample_user_story.description

    @pytest.mark.asyncio
    async def test_update_user_story_all_fields(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe actualizar todos los campos cuando se proporcionan."""
        # Arrange
        mock_user_story_repository.get_by_id.return_value = sample_user_story
        mock_user_story_repository.update.return_value = sample_user_story
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = UpdateUserStoryRequest(
            story_id=1,
            subject="New Subject",
            description="New Description",
            status=3,
            milestone_id=5,
            assigned_to_id=6,
            is_blocked=True,
            blocked_note="Blocked reason",
            is_closed=True,
            tags=["new-tag"],
            points={"dev": 8.0},
        )

        # Act
        await use_cases.update_user_story(request)

        # Assert
        updated_story = mock_user_story_repository.update.call_args[0][0]
        assert updated_story.subject == "New Subject"
        assert updated_story.description == "New Description"
        assert updated_story.status == 3
        assert updated_story.milestone_id == 5
        assert updated_story.assigned_to_id == 6
        assert updated_story.is_blocked is True
        assert updated_story.blocked_note == "Blocked reason"
        assert updated_story.is_closed is True
        assert updated_story.tags == ["new-tag"]
        assert updated_story.points == {"dev": 8.0}


class TestDeleteUserStory:
    """Tests para el caso de uso delete_user_story."""

    @pytest.mark.asyncio
    async def test_delete_user_story_success(self, mock_user_story_repository: MagicMock) -> None:
        """Debe eliminar la user story exitosamente."""
        # Arrange
        mock_user_story_repository.delete.return_value = True
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)

        # Act
        result = await use_cases.delete_user_story(story_id=1)

        # Assert
        assert result is True
        mock_user_story_repository.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_user_story_not_found(self, mock_user_story_repository: MagicMock) -> None:
        """Debe retornar False cuando la user story no existe."""
        # Arrange
        mock_user_story_repository.delete.return_value = False
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)

        # Act
        result = await use_cases.delete_user_story(story_id=999)

        # Assert
        assert result is False


class TestBulkCreateUserStories:
    """Tests para el caso de uso bulk_create_user_stories."""

    @pytest.mark.asyncio
    async def test_bulk_create_user_stories_success(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe crear múltiples user stories exitosamente."""
        # Arrange
        stories_created = [sample_user_story, sample_user_story]
        mock_user_story_repository.bulk_create.return_value = stories_created
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)

        story_requests = [
            CreateUserStoryRequest(subject="Story 1", project_id=1),
            CreateUserStoryRequest(subject="Story 2", project_id=1),
        ]
        request = BulkCreateUserStoriesRequest(project_id=1, stories=story_requests)

        # Act
        result = await use_cases.bulk_create_user_stories(request)

        # Assert
        assert result == stories_created
        mock_user_story_repository.bulk_create.assert_called_once()
        created_stories = mock_user_story_repository.bulk_create.call_args[0][0]
        assert len(created_stories) == 2
        assert created_stories[0].subject == "Story 1"
        assert created_stories[1].subject == "Story 2"
        assert all(s.project_id == 1 for s in created_stories)

    @pytest.mark.asyncio
    async def test_bulk_create_user_stories_with_full_data(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe crear user stories con todos los campos especificados."""
        # Arrange
        mock_user_story_repository.bulk_create.return_value = [sample_user_story]
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)

        story_requests = [
            CreateUserStoryRequest(
                subject="Full Story",
                description="Full description",
                project_id=1,
                status=2,
                milestone_id=3,
                assigned_to_id=4,
                is_blocked=True,
                blocked_note="Blocked",
                client_requirement=True,
                team_requirement=True,
                tags=["tag1", "tag2"],
                points={"dev": 5.0},
            ),
        ]
        request = BulkCreateUserStoriesRequest(project_id=1, stories=story_requests)

        # Act
        await use_cases.bulk_create_user_stories(request)

        # Assert
        created_stories = mock_user_story_repository.bulk_create.call_args[0][0]
        story = created_stories[0]
        assert story.subject == "Full Story"
        assert story.description == "Full description"
        assert story.status == 2
        assert story.milestone_id == 3
        assert story.assigned_to_id == 4
        assert story.is_blocked is True
        assert story.blocked_note == "Blocked"


class TestBulkUpdateUserStories:
    """Tests para el caso de uso bulk_update_user_stories."""

    @pytest.mark.asyncio
    async def test_bulk_update_user_stories_success(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe actualizar múltiples user stories exitosamente."""
        # Arrange
        updated_stories = [sample_user_story, sample_user_story]
        mock_user_story_repository.bulk_update.return_value = updated_stories
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = BulkUpdateUserStoriesRequest(
            story_ids=[1, 2, 3],
            status=2,
        )

        # Act
        result = await use_cases.bulk_update_user_stories(request)

        # Assert
        assert result == updated_stories
        mock_user_story_repository.bulk_update.assert_called_once_with([1, 2, 3], {"status": 2})

    @pytest.mark.asyncio
    async def test_bulk_update_user_stories_with_milestone(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe actualizar milestone en múltiples user stories."""
        # Arrange
        mock_user_story_repository.bulk_update.return_value = [sample_user_story]
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = BulkUpdateUserStoriesRequest(
            story_ids=[1, 2],
            milestone_id=5,
        )

        # Act
        await use_cases.bulk_update_user_stories(request)

        # Assert
        mock_user_story_repository.bulk_update.assert_called_once_with([1, 2], {"milestone_id": 5})

    @pytest.mark.asyncio
    async def test_bulk_update_user_stories_with_assigned_to(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe actualizar assigned_to en múltiples user stories."""
        # Arrange
        mock_user_story_repository.bulk_update.return_value = [sample_user_story]
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = BulkUpdateUserStoriesRequest(
            story_ids=[1],
            assigned_to_id=10,
        )

        # Act
        await use_cases.bulk_update_user_stories(request)

        # Assert
        mock_user_story_repository.bulk_update.assert_called_once_with([1], {"assigned_to_id": 10})

    @pytest.mark.asyncio
    async def test_bulk_update_user_stories_all_fields(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe actualizar todos los campos en múltiples user stories."""
        # Arrange
        mock_user_story_repository.bulk_update.return_value = [sample_user_story]
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = BulkUpdateUserStoriesRequest(
            story_ids=[1, 2, 3],
            status=4,
            milestone_id=5,
            assigned_to_id=6,
        )

        # Act
        await use_cases.bulk_update_user_stories(request)

        # Assert
        mock_user_story_repository.bulk_update.assert_called_once_with(
            [1, 2, 3], {"status": 4, "milestone_id": 5, "assigned_to_id": 6}
        )


class TestMoveToMilestone:
    """Tests para el caso de uso move_to_milestone."""

    @pytest.mark.asyncio
    async def test_move_to_milestone_success(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe mover user story a milestone exitosamente."""
        # Arrange
        mock_user_story_repository.move_to_milestone.return_value = sample_user_story
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = MoveToMilestoneRequest(story_id=1, milestone_id=5)

        # Act
        result = await use_cases.move_to_milestone(request)

        # Assert
        assert result == sample_user_story
        mock_user_story_repository.move_to_milestone.assert_called_once_with(1, 5)

    @pytest.mark.asyncio
    async def test_move_to_backlog(
        self, mock_user_story_repository: MagicMock, sample_user_story: UserStory
    ) -> None:
        """Debe mover user story al backlog (milestone_id=None)."""
        # Arrange
        mock_user_story_repository.move_to_milestone.return_value = sample_user_story
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)
        request = MoveToMilestoneRequest(story_id=1, milestone_id=None)

        # Act
        result = await use_cases.move_to_milestone(request)

        # Assert
        assert result == sample_user_story
        mock_user_story_repository.move_to_milestone.assert_called_once_with(1, None)


class TestGetFilters:
    """Tests para el caso de uso get_filters."""

    @pytest.mark.asyncio
    async def test_get_filters_success(self, mock_user_story_repository: MagicMock) -> None:
        """Debe retornar los filtros disponibles."""
        # Arrange
        filters: dict[str, Any] = {
            "statuses": [{"id": 1, "name": "New"}, {"id": 2, "name": "In Progress"}],
            "milestones": [{"id": 1, "name": "Sprint 1"}],
            "assigned_to": [{"id": 1, "name": "User 1"}],
            "tags": ["tag1", "tag2"],
        }
        mock_user_story_repository.get_filters.return_value = filters
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)

        # Act
        result = await use_cases.get_filters(project_id=1)

        # Assert
        assert result == filters
        mock_user_story_repository.get_filters.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_filters_empty(self, mock_user_story_repository: MagicMock) -> None:
        """Debe retornar diccionario vacío cuando no hay filtros."""
        # Arrange
        mock_user_story_repository.get_filters.return_value = {}
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)

        # Act
        result = await use_cases.get_filters(project_id=1)

        # Assert
        assert result == {}


class TestUserStoryUseCasesInitialization:
    """Tests para la inicialización de UserStoryUseCases."""

    def test_initialization_with_repository(self, mock_user_story_repository: MagicMock) -> None:
        """Debe inicializarse correctamente con el repositorio."""
        # Act
        use_cases = UserStoryUseCases(repository=mock_user_story_repository)

        # Assert
        assert use_cases.repository == mock_user_story_repository
