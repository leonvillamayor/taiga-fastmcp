"""Tests unitarios para ProjectUseCases.

Este módulo contiene tests exhaustivos para todos los métodos
de ProjectUseCases, cubriendo casos de éxito, errores y edge cases.
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.application.use_cases.project_use_cases import (
    CreateProjectRequest,
    ListProjectsRequest,
    ProjectUseCases,
    UpdateProjectRequest,
)
from src.domain.entities.project import Project
from src.domain.exceptions import ResourceNotFoundError


class TestCreateProject:
    """Tests para el caso de uso create_project."""

    @pytest.mark.asyncio
    async def test_create_project_success(
        self, mock_project_repository: MagicMock, sample_project: Project
    ) -> None:
        """Debe crear un proyecto exitosamente."""
        # Arrange
        mock_project_repository.create.return_value = sample_project
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = CreateProjectRequest(
            name="Test Project",
            description="A test project",
            is_private=True,
            is_backlog_activated=True,
            is_kanban_activated=True,
            is_wiki_activated=True,
            is_issues_activated=True,
            tags=["test", "sample"],
        )

        # Act
        result = await use_cases.create_project(request)

        # Assert
        assert result == sample_project
        mock_project_repository.create.assert_called_once()
        created_project = mock_project_repository.create.call_args[0][0]
        assert created_project.name == "Test Project"
        assert created_project.description == "A test project"
        assert created_project.is_private is True

    @pytest.mark.asyncio
    async def test_create_project_with_defaults(
        self, mock_project_repository: MagicMock, sample_project: Project
    ) -> None:
        """Debe crear un proyecto con valores por defecto."""
        # Arrange
        mock_project_repository.create.return_value = sample_project
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = CreateProjectRequest(name="Minimal Project")

        # Act
        result = await use_cases.create_project(request)

        # Assert
        assert result == sample_project
        created_project = mock_project_repository.create.call_args[0][0]
        assert created_project.name == "Minimal Project"
        assert created_project.description == ""
        assert created_project.is_private is True
        assert created_project.tags == []

    @pytest.mark.asyncio
    async def test_create_project_passes_all_fields(
        self, mock_project_repository: MagicMock, sample_project: Project
    ) -> None:
        """Debe pasar todos los campos al repositorio."""
        # Arrange
        mock_project_repository.create.return_value = sample_project
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = CreateProjectRequest(
            name="Full Project",
            description="Full description",
            is_private=False,
            is_backlog_activated=False,
            is_kanban_activated=True,
            is_wiki_activated=False,
            is_issues_activated=True,
            tags=["tag1", "tag2", "tag3"],
        )

        # Act
        await use_cases.create_project(request)

        # Assert
        created_project = mock_project_repository.create.call_args[0][0]
        assert created_project.is_backlog_activated is False
        assert created_project.is_kanban_activated is True
        assert created_project.is_wiki_activated is False
        assert created_project.is_issues_activated is True
        assert set(created_project.tags) == {"tag1", "tag2", "tag3"}


class TestGetProject:
    """Tests para el caso de uso get_project."""

    @pytest.mark.asyncio
    async def test_get_project_success(
        self, mock_project_repository: MagicMock, sample_project: Project
    ) -> None:
        """Debe retornar el proyecto cuando existe."""
        # Arrange
        mock_project_repository.get_by_id.return_value = sample_project
        use_cases = ProjectUseCases(repository=mock_project_repository)

        # Act
        result = await use_cases.get_project(project_id=1)

        # Assert
        assert result == sample_project
        mock_project_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, mock_project_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_project_repository.get_by_id.return_value = None
        use_cases = ProjectUseCases(repository=mock_project_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await use_cases.get_project(project_id=999)

        assert "Project 999 not found" in str(exc_info.value)
        mock_project_repository.get_by_id.assert_called_once_with(999)


class TestGetProjectBySlug:
    """Tests para el caso de uso get_project_by_slug."""

    @pytest.mark.asyncio
    async def test_get_project_by_slug_success(
        self, mock_project_repository: MagicMock, sample_project: Project
    ) -> None:
        """Debe retornar el proyecto cuando existe el slug."""
        # Arrange
        mock_project_repository.get_by_slug.return_value = sample_project
        use_cases = ProjectUseCases(repository=mock_project_repository)

        # Act
        result = await use_cases.get_project_by_slug(slug="test-project")

        # Assert
        assert result == sample_project
        mock_project_repository.get_by_slug.assert_called_once_with("test-project")

    @pytest.mark.asyncio
    async def test_get_project_by_slug_not_found(self, mock_project_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe el slug."""
        # Arrange
        mock_project_repository.get_by_slug.return_value = None
        use_cases = ProjectUseCases(repository=mock_project_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await use_cases.get_project_by_slug(slug="nonexistent-slug")

        assert "Project with slug 'nonexistent-slug' not found" in str(exc_info.value)


class TestListProjects:
    """Tests para el caso de uso list_projects."""

    @pytest.mark.asyncio
    async def test_list_projects_no_filters(
        self, mock_project_repository: MagicMock, sample_project: Project
    ) -> None:
        """Debe listar proyectos sin filtros."""
        # Arrange
        mock_project_repository.list.return_value = [sample_project]
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = ListProjectsRequest()

        # Act
        result = await use_cases.list_projects(request)

        # Assert
        assert result == [sample_project]
        mock_project_repository.list.assert_called_once_with(filters={}, limit=None, offset=None)

    @pytest.mark.asyncio
    async def test_list_projects_with_member_filter(
        self, mock_project_repository: MagicMock, sample_project: Project
    ) -> None:
        """Debe filtrar proyectos por member_id."""
        # Arrange
        mock_project_repository.list.return_value = [sample_project]
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = ListProjectsRequest(member_id=5)

        # Act
        result = await use_cases.list_projects(request)

        # Assert
        assert result == [sample_project]
        mock_project_repository.list.assert_called_once_with(
            filters={"member": 5}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_projects_with_privacy_filter(
        self, mock_project_repository: MagicMock, sample_project: Project
    ) -> None:
        """Debe filtrar proyectos por is_private."""
        # Arrange
        mock_project_repository.list.return_value = [sample_project]
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = ListProjectsRequest(is_private=True)

        # Act
        await use_cases.list_projects(request)

        # Assert
        mock_project_repository.list.assert_called_once_with(
            filters={"is_private": True}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_projects_with_pagination(
        self, mock_project_repository: MagicMock, sample_project: Project
    ) -> None:
        """Debe aplicar paginación correctamente."""
        # Arrange
        mock_project_repository.list.return_value = [sample_project]
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = ListProjectsRequest(limit=10, offset=20)

        # Act
        await use_cases.list_projects(request)

        # Assert
        mock_project_repository.list.assert_called_once_with(filters={}, limit=10, offset=20)

    @pytest.mark.asyncio
    async def test_list_projects_with_all_filters(
        self, mock_project_repository: MagicMock, sample_project: Project
    ) -> None:
        """Debe aplicar todos los filtros combinados."""
        # Arrange
        mock_project_repository.list.return_value = [sample_project]
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = ListProjectsRequest(member_id=5, is_private=False, limit=50, offset=10)

        # Act
        await use_cases.list_projects(request)

        # Assert
        mock_project_repository.list.assert_called_once_with(
            filters={"member": 5, "is_private": False}, limit=50, offset=10
        )

    @pytest.mark.asyncio
    async def test_list_projects_empty_result(self, mock_project_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay proyectos."""
        # Arrange
        mock_project_repository.list.return_value = []
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = ListProjectsRequest()

        # Act
        result = await use_cases.list_projects(request)

        # Assert
        assert result == []


class TestUpdateProject:
    """Tests para el caso de uso update_project."""

    @pytest.mark.asyncio
    async def test_update_project_success(
        self, mock_project_repository: MagicMock, sample_project: Project
    ) -> None:
        """Debe actualizar el proyecto exitosamente."""
        # Arrange
        mock_project_repository.get_by_id.return_value = sample_project
        updated_project = Project(
            id=1,
            name="Updated Name",
            slug="test-project",
            description="Updated description",
            is_private=True,
            is_backlog_activated=True,
            is_kanban_activated=True,
            is_wiki_activated=True,
            is_issues_activated=True,
            tags=["test", "sample"],
            created_date=datetime(2024, 1, 1, 12, 0, 0),
            modified_date=datetime(2024, 1, 2, 12, 0, 0),
        )
        mock_project_repository.update.return_value = updated_project
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = UpdateProjectRequest(
            project_id=1, name="Updated Name", description="Updated description"
        )

        # Act
        result = await use_cases.update_project(request)

        # Assert
        assert result == updated_project
        mock_project_repository.get_by_id.assert_called_once_with(1)
        mock_project_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, mock_project_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_project_repository.get_by_id.return_value = None
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = UpdateProjectRequest(project_id=999, name="New Name")

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.update_project(request)

        mock_project_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_project_partial_fields(
        self, mock_project_repository: MagicMock, sample_project: Project
    ) -> None:
        """Debe actualizar solo los campos proporcionados."""
        # Arrange
        mock_project_repository.get_by_id.return_value = sample_project
        mock_project_repository.update.return_value = sample_project
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = UpdateProjectRequest(project_id=1, name="Only Name Updated")

        # Act
        await use_cases.update_project(request)

        # Assert
        updated_project = mock_project_repository.update.call_args[0][0]
        assert updated_project.name == "Only Name Updated"
        assert updated_project.description == sample_project.description

    @pytest.mark.asyncio
    async def test_update_project_all_fields(
        self, mock_project_repository: MagicMock, sample_project: Project
    ) -> None:
        """Debe actualizar todos los campos cuando se proporcionan."""
        # Arrange
        mock_project_repository.get_by_id.return_value = sample_project
        mock_project_repository.update.return_value = sample_project
        use_cases = ProjectUseCases(repository=mock_project_repository)
        request = UpdateProjectRequest(
            project_id=1,
            name="New Name",
            description="New Description",
            is_private=False,
            is_backlog_activated=False,
            is_kanban_activated=False,
            is_wiki_activated=False,
            is_issues_activated=False,
            tags=["new-tag"],
        )

        # Act
        await use_cases.update_project(request)

        # Assert
        updated_project = mock_project_repository.update.call_args[0][0]
        assert updated_project.name == "New Name"
        assert updated_project.description == "New Description"
        assert updated_project.is_private is False
        assert updated_project.is_backlog_activated is False
        assert updated_project.tags == ["new-tag"]


class TestDeleteProject:
    """Tests para el caso de uso delete_project."""

    @pytest.mark.asyncio
    async def test_delete_project_success(self, mock_project_repository: MagicMock) -> None:
        """Debe eliminar el proyecto exitosamente."""
        # Arrange
        mock_project_repository.delete.return_value = True
        use_cases = ProjectUseCases(repository=mock_project_repository)

        # Act
        result = await use_cases.delete_project(project_id=1)

        # Assert
        assert result is True
        mock_project_repository.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, mock_project_repository: MagicMock) -> None:
        """Debe retornar False cuando el proyecto no existe."""
        # Arrange
        mock_project_repository.delete.return_value = False
        use_cases = ProjectUseCases(repository=mock_project_repository)

        # Act
        result = await use_cases.delete_project(project_id=999)

        # Assert
        assert result is False


class TestGetProjectStats:
    """Tests para el caso de uso get_project_stats."""

    @pytest.mark.asyncio
    async def test_get_project_stats_success(
        self, mock_project_repository: MagicMock, sample_project: Project
    ) -> None:
        """Debe retornar estadísticas del proyecto."""
        # Arrange
        stats: dict[str, Any] = {
            "total_milestones": 5,
            "total_user_stories": 20,
            "total_tasks": 50,
            "total_issues": 10,
            "closed_user_stories": 15,
            "closed_tasks": 40,
        }
        mock_project_repository.get_by_id.return_value = sample_project
        mock_project_repository.get_stats.return_value = stats
        use_cases = ProjectUseCases(repository=mock_project_repository)

        # Act
        result = await use_cases.get_project_stats(project_id=1)

        # Assert
        assert result == stats
        mock_project_repository.get_by_id.assert_called_once_with(1)
        mock_project_repository.get_stats.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_project_stats_not_found(self, mock_project_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando el proyecto no existe."""
        # Arrange
        mock_project_repository.get_by_id.return_value = None
        use_cases = ProjectUseCases(repository=mock_project_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.get_project_stats(project_id=999)

        mock_project_repository.get_stats.assert_not_called()


class TestProjectUseCasesInitialization:
    """Tests para la inicialización de ProjectUseCases."""

    def test_initialization_with_repository(self, mock_project_repository: MagicMock) -> None:
        """Debe inicializarse correctamente con el repositorio."""
        # Act
        use_cases = ProjectUseCases(repository=mock_project_repository)

        # Assert
        assert use_cases.repository == mock_project_repository
