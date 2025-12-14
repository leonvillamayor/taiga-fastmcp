"""
Tests de integración para casos de uso de proyectos.
Implementa tests para la capa de aplicación.
"""

from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.project_use_cases import (
    CreateProjectRequest,
    ListProjectsRequest,
    ProjectUseCases,
    UpdateProjectRequest,
)
from src.domain.entities.project import Project
from src.domain.exceptions import ResourceNotFoundError


@pytest.fixture
def mock_project_repository() -> AsyncMock:
    """Crea un mock del repositorio de proyectos."""
    return AsyncMock()


@pytest.fixture
def sample_project() -> Project:
    """Crea un proyecto de ejemplo para tests."""
    return Project(
        id=1,
        name="Test Project",
        description="Test description",
        is_private=True,
        is_backlog_activated=True,
        is_kanban_activated=True,
        is_wiki_activated=True,
        is_issues_activated=True,
        tags=["test", "sample"],
        slug="test-project",
    )


@pytest.fixture
def sample_projects_list(sample_project: Project) -> list[Project]:
    """Lista de proyectos de ejemplo."""
    return [
        sample_project,
        Project(
            id=2,
            name="Second Project",
            slug="second-project",
        ),
    ]


@pytest.mark.integration
@pytest.mark.asyncio
class TestProjectUseCases:
    """Tests de integración para casos de uso de proyectos."""

    async def test_list_projects(
        self, mock_project_repository: AsyncMock, sample_projects_list: list[Project]
    ) -> None:
        """Verifica el caso de uso de listar proyectos."""
        mock_project_repository.list.return_value = sample_projects_list
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = ListProjectsRequest(member_id=1, is_private=True)

        result = await use_cases.list_projects(request)

        assert len(result) == 2
        mock_project_repository.list.assert_called_once()

    async def test_create_project(
        self, mock_project_repository: AsyncMock, sample_project: Project
    ) -> None:
        """Verifica el caso de uso de crear un proyecto."""
        mock_project_repository.create.return_value = sample_project
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = CreateProjectRequest(
            name="Test Project",
            description="Test description",
            is_private=True,
        )

        result = await use_cases.create_project(request)

        assert result.id == 1
        assert result.name == "Test Project"
        mock_project_repository.create.assert_called_once()

    async def test_get_project_by_id(
        self, mock_project_repository: AsyncMock, sample_project: Project
    ) -> None:
        """Verifica el caso de uso de obtener proyecto por ID."""
        mock_project_repository.get_by_id.return_value = sample_project
        use_cases = ProjectUseCases(repository=mock_project_repository)

        result = await use_cases.get_project(project_id=1)

        assert result.id == 1
        mock_project_repository.get_by_id.assert_called_once_with(1)

    async def test_get_project_by_id_not_found(self, mock_project_repository: AsyncMock) -> None:
        """Verifica que se lance ResourceNotFoundError si el proyecto no existe."""
        mock_project_repository.get_by_id.return_value = None
        use_cases = ProjectUseCases(repository=mock_project_repository)

        with pytest.raises(ResourceNotFoundError, match="Project 999 not found"):
            await use_cases.get_project(project_id=999)

    async def test_get_project_by_slug(
        self, mock_project_repository: AsyncMock, sample_project: Project
    ) -> None:
        """Verifica el caso de uso de obtener proyecto por slug."""
        mock_project_repository.get_by_slug.return_value = sample_project
        use_cases = ProjectUseCases(repository=mock_project_repository)

        result = await use_cases.get_project_by_slug(slug="test-project")

        assert str(result.slug) == "test-project"
        mock_project_repository.get_by_slug.assert_called_once_with("test-project")

    async def test_get_project_by_slug_not_found(self, mock_project_repository: AsyncMock) -> None:
        """Verifica que se lance ResourceNotFoundError si no se encuentra por slug."""
        mock_project_repository.get_by_slug.return_value = None
        use_cases = ProjectUseCases(repository=mock_project_repository)

        with pytest.raises(ResourceNotFoundError, match="slug 'unknown' not found"):
            await use_cases.get_project_by_slug(slug="unknown")

    async def test_update_project(
        self, mock_project_repository: AsyncMock, sample_project: Project
    ) -> None:
        """Verifica el caso de uso de actualizar un proyecto."""
        updated_project = Project(
            id=1,
            name="Updated Name",
            description="Updated description",
            slug="test-project",
        )
        mock_project_repository.get_by_id.return_value = sample_project
        mock_project_repository.update.return_value = updated_project
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = UpdateProjectRequest(
            project_id=1,
            name="Updated Name",
            description="Updated description",
        )

        result = await use_cases.update_project(request)

        assert result.name == "Updated Name"
        mock_project_repository.update.assert_called_once()

    async def test_update_project_not_found(self, mock_project_repository: AsyncMock) -> None:
        """Verifica que update lance ResourceNotFoundError si el proyecto no existe."""
        mock_project_repository.get_by_id.return_value = None
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = UpdateProjectRequest(project_id=999, name="Updated")

        with pytest.raises(ResourceNotFoundError, match="Project 999 not found"):
            await use_cases.update_project(request)

    async def test_delete_project(self, mock_project_repository: AsyncMock) -> None:
        """Verifica el caso de uso de eliminar un proyecto."""
        mock_project_repository.delete.return_value = True
        use_cases = ProjectUseCases(repository=mock_project_repository)

        result = await use_cases.delete_project(project_id=1)

        assert result is True
        mock_project_repository.delete.assert_called_once_with(1)

    async def test_delete_project_not_found(self, mock_project_repository: AsyncMock) -> None:
        """Verifica que delete devuelva False si el proyecto no existe."""
        mock_project_repository.delete.return_value = False
        use_cases = ProjectUseCases(repository=mock_project_repository)

        result = await use_cases.delete_project(project_id=999)

        assert result is False

    async def test_get_project_stats(
        self, mock_project_repository: AsyncMock, sample_project: Project
    ) -> None:
        """Verifica el caso de uso de obtener estadísticas del proyecto."""
        stats = {"total_stories": 10, "total_tasks": 25}
        mock_project_repository.get_by_id.return_value = sample_project
        mock_project_repository.get_stats.return_value = stats
        use_cases = ProjectUseCases(repository=mock_project_repository)

        result = await use_cases.get_project_stats(project_id=1)

        assert "total_stories" in result
        mock_project_repository.get_stats.assert_called_once_with(1)
