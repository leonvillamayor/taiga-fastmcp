"""
Tests de integración para casos de uso de tasks.
Implementa tests para la capa de aplicación.
"""

from unittest.mock import AsyncMock

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


@pytest.fixture
def mock_task_repository() -> AsyncMock:
    """Crea un mock del repositorio de tasks."""
    return AsyncMock()


@pytest.fixture
def sample_task() -> Task:
    """Crea una task de ejemplo para tests."""
    return Task(
        id=1,
        project_id=100,
        subject="Test Task",
        description="Test description",
        status=1,
        assigned_to_id=10,
        user_story_id=50,
        ref=5,
        tags=["bug"],
    )


@pytest.fixture
def sample_tasks_list(sample_task: Task) -> list[Task]:
    """Lista de tasks de ejemplo."""
    return [
        sample_task,
        Task(id=2, project_id=100, subject="Second Task", ref=6),
    ]


@pytest.mark.integration
@pytest.mark.asyncio
class TestTaskUseCases:
    """Tests de integración para casos de uso de tasks."""

    async def test_list_tasks(
        self, mock_task_repository: AsyncMock, sample_tasks_list: list[Task]
    ) -> None:
        """Verifica el caso de uso de listar tasks."""
        mock_task_repository.list.return_value = sample_tasks_list
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = ListTasksRequest(project_id=100, status_id=1)

        result = await use_cases.list_tasks(request)

        assert len(result) == 2
        mock_task_repository.list.assert_called_once()

    async def test_list_unassigned(
        self, mock_task_repository: AsyncMock, sample_tasks_list: list[Task]
    ) -> None:
        """Verifica el caso de uso de listar tasks sin asignar."""
        mock_task_repository.list_unassigned.return_value = sample_tasks_list
        use_cases = TaskUseCases(repository=mock_task_repository)

        result = await use_cases.list_unassigned(project_id=100)

        assert len(result) == 2
        mock_task_repository.list_unassigned.assert_called_once_with(100)

    async def test_create_task(self, mock_task_repository: AsyncMock, sample_task: Task) -> None:
        """Verifica el caso de uso de crear una task."""
        mock_task_repository.create.return_value = sample_task
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = CreateTaskRequest(
            subject="Test Task",
            project_id=100,
            description="Test description",
        )

        result = await use_cases.create_task(request)

        assert result.id == 1
        assert result.subject == "Test Task"
        mock_task_repository.create.assert_called_once()

    async def test_get_task_by_id(self, mock_task_repository: AsyncMock, sample_task: Task) -> None:
        """Verifica el caso de uso de obtener task por ID."""
        mock_task_repository.get_by_id.return_value = sample_task
        use_cases = TaskUseCases(repository=mock_task_repository)

        result = await use_cases.get_task(task_id=1)

        assert result.id == 1
        mock_task_repository.get_by_id.assert_called_once_with(1)

    async def test_get_task_by_id_not_found(self, mock_task_repository: AsyncMock) -> None:
        """Verifica que se lance ResourceNotFoundError si la task no existe."""
        mock_task_repository.get_by_id.return_value = None
        use_cases = TaskUseCases(repository=mock_task_repository)

        with pytest.raises(ResourceNotFoundError, match="Task 999 not found"):
            await use_cases.get_task(task_id=999)

    async def test_get_task_by_ref(
        self, mock_task_repository: AsyncMock, sample_task: Task
    ) -> None:
        """Verifica el caso de uso de obtener task por referencia."""
        mock_task_repository.get_by_ref.return_value = sample_task
        use_cases = TaskUseCases(repository=mock_task_repository)

        result = await use_cases.get_task_by_ref(project_id=100, ref=5)

        assert result.ref == 5
        mock_task_repository.get_by_ref.assert_called_once_with(100, 5)

    async def test_get_task_by_ref_not_found(self, mock_task_repository: AsyncMock) -> None:
        """Verifica que se lance ResourceNotFoundError si no se encuentra por ref."""
        mock_task_repository.get_by_ref.return_value = None
        use_cases = TaskUseCases(repository=mock_task_repository)

        with pytest.raises(ResourceNotFoundError, match="ref=5 not found"):
            await use_cases.get_task_by_ref(project_id=100, ref=5)

    async def test_update_task(self, mock_task_repository: AsyncMock, sample_task: Task) -> None:
        """Verifica el caso de uso de actualizar una task."""
        updated = Task(id=1, project_id=100, subject="Updated Subject", status=2, ref=5)
        mock_task_repository.get_by_id.return_value = sample_task
        mock_task_repository.update.return_value = updated
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = UpdateTaskRequest(task_id=1, subject="Updated Subject", status=2)

        result = await use_cases.update_task(request)

        assert result.subject == "Updated Subject"
        mock_task_repository.update.assert_called_once()

    async def test_update_task_not_found(self, mock_task_repository: AsyncMock) -> None:
        """Verifica que update lance ResourceNotFoundError si no existe."""
        mock_task_repository.get_by_id.return_value = None
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = UpdateTaskRequest(task_id=999, subject="Updated Subject")

        with pytest.raises(ResourceNotFoundError, match="Task 999 not found"):
            await use_cases.update_task(request)

    async def test_delete_task(self, mock_task_repository: AsyncMock) -> None:
        """Verifica el caso de uso de eliminar una task."""
        mock_task_repository.delete.return_value = True
        use_cases = TaskUseCases(repository=mock_task_repository)

        result = await use_cases.delete_task(task_id=1)

        assert result is True
        mock_task_repository.delete.assert_called_once_with(1)

    async def test_delete_task_not_found(self, mock_task_repository: AsyncMock) -> None:
        """Verifica que delete devuelva False si no existe."""
        mock_task_repository.delete.return_value = False
        use_cases = TaskUseCases(repository=mock_task_repository)

        result = await use_cases.delete_task(task_id=999)

        assert result is False

    async def test_bulk_create_tasks(
        self, mock_task_repository: AsyncMock, sample_tasks_list: list[Task]
    ) -> None:
        """Verifica el caso de uso de crear múltiples tasks."""
        mock_task_repository.bulk_create.return_value = sample_tasks_list
        use_cases = TaskUseCases(repository=mock_task_repository)
        request = BulkCreateTasksRequest(
            project_id=100,
            tasks=[
                CreateTaskRequest(subject="Task 1", project_id=100),
                CreateTaskRequest(subject="Task 2", project_id=100),
            ],
        )

        result = await use_cases.bulk_create_tasks(request)

        assert len(result) == 2
        mock_task_repository.bulk_create.assert_called_once()

    async def test_list_by_user_story(
        self, mock_task_repository: AsyncMock, sample_tasks_list: list[Task]
    ) -> None:
        """Verifica el caso de uso de listar tasks por user story."""
        mock_task_repository.list_by_user_story.return_value = sample_tasks_list
        use_cases = TaskUseCases(repository=mock_task_repository)

        result = await use_cases.list_by_user_story(user_story_id=50)

        assert len(result) == 2
        mock_task_repository.list_by_user_story.assert_called_once_with(50)

    async def test_list_by_milestone(
        self, mock_task_repository: AsyncMock, sample_tasks_list: list[Task]
    ) -> None:
        """Verifica el caso de uso de listar tasks por milestone."""
        mock_task_repository.list_by_milestone.return_value = sample_tasks_list
        use_cases = TaskUseCases(repository=mock_task_repository)

        result = await use_cases.list_by_milestone(milestone_id=10)

        assert len(result) == 2
        mock_task_repository.list_by_milestone.assert_called_once_with(10)

    async def test_get_filters(self, mock_task_repository: AsyncMock) -> None:
        """Verifica el caso de uso de obtener filtros."""
        filters = {"statuses": [{"id": 1, "name": "New"}]}
        mock_task_repository.get_filters.return_value = filters
        use_cases = TaskUseCases(repository=mock_task_repository)

        result = await use_cases.get_filters(project_id=100)

        assert "statuses" in result
        mock_task_repository.get_filters.assert_called_once_with(100)
