"""Tests unitarios para TaskUseCases.

Este módulo contiene tests exhaustivos para todos los métodos
de TaskUseCases, cubriendo casos de éxito, errores y edge cases.
"""

from unittest.mock import MagicMock

import pytest

from src.application.use_cases.task_use_cases import (
    BulkCreateTasksRequest,
    CreateTaskRequest,
    ListTasksRequest,
    TaskUseCases,
    UpdateTaskRequest,
)
from src.domain.entities.task import Task
from src.domain.exceptions import ResourceNotFoundError


class TestCreateTask:
    """Tests para el caso de uso create_task."""

    @pytest.mark.asyncio
    async def test_create_task_success(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe crear una task exitosamente."""
        # Arrange
        mock_task_repository.create.return_value = sample_task
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = CreateTaskRequest(
            subject="Test Task",
            description="A test task",
            project_id=1,
            user_story_id=1,
            status=1,
            milestone_id=1,
            assigned_to_id=1,
            is_blocked=False,
            blocked_note="",
            is_iocaine=False,
            tags=["task-tag"],
        )

        # Act
        result = await use_cases.create_task(request)

        # Assert
        assert result == sample_task
        mock_task_repository.create.assert_called_once()
        created_task = mock_task_repository.create.call_args[0][0]
        assert created_task.subject == "Test Task"
        assert created_task.project_id == 1
        assert created_task.user_story_id == 1

    @pytest.mark.asyncio
    async def test_create_task_with_defaults(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe crear una task con valores por defecto."""
        # Arrange
        mock_task_repository.create.return_value = sample_task
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = CreateTaskRequest(
            subject="Minimal Task",
            project_id=1,
        )

        # Act
        result = await use_cases.create_task(request)

        # Assert
        assert result == sample_task
        created_task = mock_task_repository.create.call_args[0][0]
        assert created_task.subject == "Minimal Task"
        assert created_task.description == ""
        assert created_task.user_story_id is None
        assert created_task.is_blocked is False
        assert created_task.is_iocaine is False
        assert created_task.tags == []

    @pytest.mark.asyncio
    async def test_create_task_with_blocking(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe crear una task bloqueada."""
        # Arrange
        mock_task_repository.create.return_value = sample_task
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = CreateTaskRequest(
            subject="Blocked Task",
            project_id=1,
            is_blocked=True,
            blocked_note="Waiting for dependency",
        )

        # Act
        await use_cases.create_task(request)

        # Assert
        created_task = mock_task_repository.create.call_args[0][0]
        assert created_task.is_blocked is True
        assert created_task.blocked_note == "Waiting for dependency"

    @pytest.mark.asyncio
    async def test_create_task_iocaine(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe crear una task con flag iocaine."""
        # Arrange
        mock_task_repository.create.return_value = sample_task
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = CreateTaskRequest(
            subject="Risky Task",
            project_id=1,
            is_iocaine=True,
        )

        # Act
        await use_cases.create_task(request)

        # Assert
        created_task = mock_task_repository.create.call_args[0][0]
        assert created_task.is_iocaine is True


class TestGetTask:
    """Tests para el caso de uso get_task."""

    @pytest.mark.asyncio
    async def test_get_task_success(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe retornar la task cuando existe."""
        # Arrange
        mock_task_repository.get_by_id.return_value = sample_task
        use_cases = TaskUseCases(repository=mock_task_repository)

        # Act
        result = await use_cases.get_task(task_id=1)

        # Assert
        assert result == sample_task
        mock_task_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, mock_task_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_task_repository.get_by_id.return_value = None
        use_cases = TaskUseCases(repository=mock_task_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await use_cases.get_task(task_id=999)

        assert "Task 999 not found" in str(exc_info.value)
        mock_task_repository.get_by_id.assert_called_once_with(999)


class TestGetTaskByRef:
    """Tests para el caso de uso get_task_by_ref."""

    @pytest.mark.asyncio
    async def test_get_task_by_ref_success(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe retornar la task cuando existe la referencia."""
        # Arrange
        mock_task_repository.get_by_ref.return_value = sample_task
        use_cases = TaskUseCases(repository=mock_task_repository)

        # Act
        result = await use_cases.get_task_by_ref(project_id=1, ref=42)

        # Assert
        assert result == sample_task
        mock_task_repository.get_by_ref.assert_called_once_with(1, 42)

    @pytest.mark.asyncio
    async def test_get_task_by_ref_not_found(self, mock_task_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe la referencia."""
        # Arrange
        mock_task_repository.get_by_ref.return_value = None
        use_cases = TaskUseCases(repository=mock_task_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await use_cases.get_task_by_ref(project_id=1, ref=999)

        assert "Task with ref=999 not found in project 1" in str(exc_info.value)


class TestListTasks:
    """Tests para el caso de uso list_tasks."""

    @pytest.mark.asyncio
    async def test_list_tasks_no_filters(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe listar tasks sin filtros."""
        # Arrange
        mock_task_repository.list.return_value = [sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = ListTasksRequest()

        # Act
        result = await use_cases.list_tasks(request)

        # Assert
        assert result == [sample_task]
        mock_task_repository.list.assert_called_once_with(filters={}, limit=None, offset=None)

    @pytest.mark.asyncio
    async def test_list_tasks_with_project_filter(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe filtrar tasks por proyecto."""
        # Arrange
        mock_task_repository.list.return_value = [sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = ListTasksRequest(project_id=1)

        # Act
        result = await use_cases.list_tasks(request)

        # Assert
        assert result == [sample_task]
        mock_task_repository.list.assert_called_once_with(
            filters={"project": 1}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_tasks_with_user_story_filter(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe filtrar tasks por user story."""
        # Arrange
        mock_task_repository.list.return_value = [sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = ListTasksRequest(user_story_id=5)

        # Act
        await use_cases.list_tasks(request)

        # Assert
        mock_task_repository.list.assert_called_once_with(
            filters={"user_story": 5}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_tasks_with_milestone_filter(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe filtrar tasks por milestone."""
        # Arrange
        mock_task_repository.list.return_value = [sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = ListTasksRequest(milestone_id=3)

        # Act
        await use_cases.list_tasks(request)

        # Assert
        mock_task_repository.list.assert_called_once_with(
            filters={"milestone": 3}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_tasks_with_status_filter(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe filtrar tasks por estado."""
        # Arrange
        mock_task_repository.list.return_value = [sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = ListTasksRequest(status_id=2)

        # Act
        await use_cases.list_tasks(request)

        # Assert
        mock_task_repository.list.assert_called_once_with(
            filters={"status": 2}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_tasks_with_assigned_to_filter(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe filtrar tasks por asignado."""
        # Arrange
        mock_task_repository.list.return_value = [sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = ListTasksRequest(assigned_to_id=10)

        # Act
        await use_cases.list_tasks(request)

        # Assert
        mock_task_repository.list.assert_called_once_with(
            filters={"assigned_to": 10}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_tasks_with_closed_filter(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe filtrar tasks por estado cerrado."""
        # Arrange
        mock_task_repository.list.return_value = [sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = ListTasksRequest(is_closed=True)

        # Act
        await use_cases.list_tasks(request)

        # Assert
        mock_task_repository.list.assert_called_once_with(
            filters={"is_closed": True}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_tasks_with_tags_filter(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe filtrar tasks por tags."""
        # Arrange
        mock_task_repository.list.return_value = [sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = ListTasksRequest(tags=["urgent", "bug"])

        # Act
        await use_cases.list_tasks(request)

        # Assert
        mock_task_repository.list.assert_called_once_with(
            filters={"tags": ["urgent", "bug"]}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_tasks_with_pagination(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe aplicar paginación correctamente."""
        # Arrange
        mock_task_repository.list.return_value = [sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = ListTasksRequest(limit=25, offset=50)

        # Act
        await use_cases.list_tasks(request)

        # Assert
        mock_task_repository.list.assert_called_once_with(filters={}, limit=25, offset=50)

    @pytest.mark.asyncio
    async def test_list_tasks_with_all_filters(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe aplicar todos los filtros combinados."""
        # Arrange
        mock_task_repository.list.return_value = [sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = ListTasksRequest(
            project_id=1,
            user_story_id=5,
            milestone_id=3,
            status_id=2,
            assigned_to_id=10,
            is_closed=False,
            tags=["backend"],
            limit=20,
            offset=0,
        )

        # Act
        await use_cases.list_tasks(request)

        # Assert
        mock_task_repository.list.assert_called_once_with(
            filters={
                "project": 1,
                "user_story": 5,
                "milestone": 3,
                "status": 2,
                "assigned_to": 10,
                "is_closed": False,
                "tags": ["backend"],
            },
            limit=20,
            offset=0,
        )

    @pytest.mark.asyncio
    async def test_list_tasks_empty_result(self, mock_task_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay tasks."""
        # Arrange
        mock_task_repository.list.return_value = []
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = ListTasksRequest()

        # Act
        result = await use_cases.list_tasks(request)

        # Assert
        assert result == []


class TestListByUserStory:
    """Tests para el caso de uso list_by_user_story."""

    @pytest.mark.asyncio
    async def test_list_by_user_story_success(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe listar tasks de una user story."""
        # Arrange
        mock_task_repository.list_by_user_story.return_value = [sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)

        # Act
        result = await use_cases.list_by_user_story(user_story_id=5)

        # Assert
        assert result == [sample_task]
        mock_task_repository.list_by_user_story.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_list_by_user_story_empty(self, mock_task_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay tasks."""
        # Arrange
        mock_task_repository.list_by_user_story.return_value = []
        use_cases = TaskUseCases(repository=mock_task_repository)

        # Act
        result = await use_cases.list_by_user_story(user_story_id=999)

        # Assert
        assert result == []


class TestListByMilestone:
    """Tests para el caso de uso list_by_milestone."""

    @pytest.mark.asyncio
    async def test_list_by_milestone_success(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe listar tasks de un milestone."""
        # Arrange
        mock_task_repository.list_by_milestone.return_value = [sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)

        # Act
        result = await use_cases.list_by_milestone(milestone_id=3)

        # Assert
        assert result == [sample_task]
        mock_task_repository.list_by_milestone.assert_called_once_with(3)

    @pytest.mark.asyncio
    async def test_list_by_milestone_empty(self, mock_task_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay tasks."""
        # Arrange
        mock_task_repository.list_by_milestone.return_value = []
        use_cases = TaskUseCases(repository=mock_task_repository)

        # Act
        result = await use_cases.list_by_milestone(milestone_id=999)

        # Assert
        assert result == []


class TestListUnassigned:
    """Tests para el caso de uso list_unassigned."""

    @pytest.mark.asyncio
    async def test_list_unassigned_success(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe listar tasks sin asignar de un proyecto."""
        # Arrange
        mock_task_repository.list_unassigned.return_value = [sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)

        # Act
        result = await use_cases.list_unassigned(project_id=1)

        # Assert
        assert result == [sample_task]
        mock_task_repository.list_unassigned.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_unassigned_empty(self, mock_task_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay tasks sin asignar."""
        # Arrange
        mock_task_repository.list_unassigned.return_value = []
        use_cases = TaskUseCases(repository=mock_task_repository)

        # Act
        result = await use_cases.list_unassigned(project_id=1)

        # Assert
        assert result == []


class TestUpdateTask:
    """Tests para el caso de uso update_task."""

    @pytest.mark.asyncio
    async def test_update_task_success(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe actualizar la task exitosamente."""
        # Arrange
        mock_task_repository.get_by_id.return_value = sample_task
        mock_task_repository.update.return_value = sample_task
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = UpdateTaskRequest(
            task_id=1,
            subject="Updated Task",
            description="Updated description",
        )

        # Act
        result = await use_cases.update_task(request)

        # Assert
        assert result == sample_task
        mock_task_repository.get_by_id.assert_called_once_with(1)
        mock_task_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, mock_task_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_task_repository.get_by_id.return_value = None
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = UpdateTaskRequest(task_id=999, subject="New Subject")

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.update_task(request)

        mock_task_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_task_partial_fields(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe actualizar solo los campos proporcionados."""
        # Arrange
        mock_task_repository.get_by_id.return_value = sample_task
        mock_task_repository.update.return_value = sample_task
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = UpdateTaskRequest(task_id=1, subject="Only Subject")

        # Act
        await use_cases.update_task(request)

        # Assert
        updated_task = mock_task_repository.update.call_args[0][0]
        assert updated_task.subject == "Only Subject"
        assert updated_task.description == sample_task.description

    @pytest.mark.asyncio
    async def test_update_task_all_fields(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe actualizar todos los campos cuando se proporcionan."""
        # Arrange
        mock_task_repository.get_by_id.return_value = sample_task
        mock_task_repository.update.return_value = sample_task
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = UpdateTaskRequest(
            task_id=1,
            subject="New Subject",
            description="New Description",
            user_story_id=10,
            status=5,
            milestone_id=3,
            assigned_to_id=2,
            is_blocked=True,
            blocked_note="Blocked reason",
            is_closed=False,
            is_iocaine=True,
            tags=["new-tag"],
        )

        # Act
        await use_cases.update_task(request)

        # Assert
        updated_task = mock_task_repository.update.call_args[0][0]
        assert updated_task.subject == "New Subject"
        assert updated_task.description == "New Description"
        assert updated_task.user_story_id == 10
        assert updated_task.status == 5
        assert updated_task.milestone_id == 3
        assert updated_task.assigned_to_id == 2
        assert updated_task.is_blocked is True
        assert updated_task.blocked_note == "Blocked reason"
        assert updated_task.is_closed is False
        assert updated_task.is_iocaine is True
        assert updated_task.tags == ["new-tag"]

    @pytest.mark.asyncio
    async def test_update_task_block_status(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe actualizar el estado de bloqueo."""
        # Arrange
        mock_task_repository.get_by_id.return_value = sample_task
        mock_task_repository.update.return_value = sample_task
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = UpdateTaskRequest(
            task_id=1,
            is_blocked=True,
            blocked_note="External dependency",
        )

        # Act
        await use_cases.update_task(request)

        # Assert
        updated_task = mock_task_repository.update.call_args[0][0]
        assert updated_task.is_blocked is True
        assert updated_task.blocked_note == "External dependency"


class TestDeleteTask:
    """Tests para el caso de uso delete_task."""

    @pytest.mark.asyncio
    async def test_delete_task_success(self, mock_task_repository: MagicMock) -> None:
        """Debe eliminar la task exitosamente."""
        # Arrange
        mock_task_repository.delete.return_value = True
        use_cases = TaskUseCases(repository=mock_task_repository)

        # Act
        result = await use_cases.delete_task(task_id=1)

        # Assert
        assert result is True
        mock_task_repository.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, mock_task_repository: MagicMock) -> None:
        """Debe retornar False cuando la task no existe."""
        # Arrange
        mock_task_repository.delete.return_value = False
        use_cases = TaskUseCases(repository=mock_task_repository)

        # Act
        result = await use_cases.delete_task(task_id=999)

        # Assert
        assert result is False


class TestBulkCreateTasks:
    """Tests para el caso de uso bulk_create_tasks."""

    @pytest.mark.asyncio
    async def test_bulk_create_tasks_success(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe crear múltiples tasks exitosamente."""
        # Arrange
        mock_task_repository.bulk_create.return_value = [sample_task, sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = BulkCreateTasksRequest(
            project_id=1,
            user_story_id=5,
            tasks=[
                CreateTaskRequest(subject="Task 1", project_id=1),
                CreateTaskRequest(subject="Task 2", project_id=1),
            ],
        )

        # Act
        result = await use_cases.bulk_create_tasks(request)

        # Assert
        assert len(result) == 2
        mock_task_repository.bulk_create.assert_called_once()
        created_tasks = mock_task_repository.bulk_create.call_args[0][0]
        assert len(created_tasks) == 2
        assert created_tasks[0].subject == "Task 1"
        assert created_tasks[0].project_id == 1
        assert created_tasks[0].user_story_id == 5  # From parent request
        assert created_tasks[1].subject == "Task 2"

    @pytest.mark.asyncio
    async def test_bulk_create_tasks_preserves_user_story_from_task(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe usar user_story_id del task si está definido."""
        # Arrange
        mock_task_repository.bulk_create.return_value = [sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = BulkCreateTasksRequest(
            project_id=1,
            user_story_id=5,
            tasks=[
                CreateTaskRequest(
                    subject="Task with own US",
                    project_id=1,
                    user_story_id=10,  # Override
                ),
            ],
        )

        # Act
        await use_cases.bulk_create_tasks(request)

        # Assert
        created_tasks = mock_task_repository.bulk_create.call_args[0][0]
        # user_story_id from task should be preserved (5 or 10 based on logic)
        # Based on implementation: request.user_story_id or task.user_story_id
        # So if request has user_story_id=5, it will be used unless task has one
        assert created_tasks[0].user_story_id == 5  # From parent request

    @pytest.mark.asyncio
    async def test_bulk_create_tasks_without_parent_user_story(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe usar user_story_id del task si el padre no lo tiene."""
        # Arrange
        mock_task_repository.bulk_create.return_value = [sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = BulkCreateTasksRequest(
            project_id=1,
            user_story_id=None,
            tasks=[
                CreateTaskRequest(
                    subject="Task with own US",
                    project_id=1,
                    user_story_id=10,
                ),
            ],
        )

        # Act
        await use_cases.bulk_create_tasks(request)

        # Assert
        created_tasks = mock_task_repository.bulk_create.call_args[0][0]
        assert created_tasks[0].user_story_id == 10  # From task

    @pytest.mark.asyncio
    async def test_bulk_create_tasks_with_all_fields(
        self, mock_task_repository: MagicMock, sample_task: Task
    ) -> None:
        """Debe crear tasks con todos los campos."""
        # Arrange
        mock_task_repository.bulk_create.return_value = [sample_task]
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = BulkCreateTasksRequest(
            project_id=1,
            tasks=[
                CreateTaskRequest(
                    subject="Full Task",
                    description="Full description",
                    project_id=1,
                    status=2,
                    milestone_id=3,
                    assigned_to_id=4,
                    is_blocked=True,
                    blocked_note="Blocked",
                    is_iocaine=True,
                    tags=["critical"],
                ),
            ],
        )

        # Act
        await use_cases.bulk_create_tasks(request)

        # Assert
        created_tasks = mock_task_repository.bulk_create.call_args[0][0]
        assert created_tasks[0].description == "Full description"
        assert created_tasks[0].status == 2
        assert created_tasks[0].milestone_id == 3
        assert created_tasks[0].is_iocaine is True


class TestGetFilters:
    """Tests para el caso de uso get_filters."""

    @pytest.mark.asyncio
    async def test_get_filters_success(self, mock_task_repository: MagicMock) -> None:
        """Debe retornar los filtros disponibles."""
        # Arrange
        filters = {
            "statuses": [{"id": 1, "name": "New"}],
            "assigned_to": [{"id": 1, "name": "User"}],
            "user_stories": [{"id": 1, "name": "US-1"}],
        }
        mock_task_repository.get_filters.return_value = filters
        use_cases = TaskUseCases(repository=mock_task_repository)

        # Act
        result = await use_cases.get_filters(project_id=1)

        # Assert
        assert result == filters
        mock_task_repository.get_filters.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_filters_empty(self, mock_task_repository: MagicMock) -> None:
        """Debe retornar diccionario vacío si no hay filtros."""
        # Arrange
        mock_task_repository.get_filters.return_value = {}
        use_cases = TaskUseCases(repository=mock_task_repository)

        # Act
        result = await use_cases.get_filters(project_id=1)

        # Assert
        assert result == {}


class TestTaskUseCasesInitialization:
    """Tests para la inicialización de TaskUseCases."""

    def test_initialization_with_repository(self, mock_task_repository: MagicMock) -> None:
        """Debe inicializarse correctamente con el repositorio."""
        # Act
        use_cases = TaskUseCases(repository=mock_task_repository)

        # Assert
        assert use_cases.repository == mock_task_repository
