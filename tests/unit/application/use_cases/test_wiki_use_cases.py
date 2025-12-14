"""Tests unitarios para WikiUseCases.

Este módulo contiene tests exhaustivos para todos los métodos
de WikiUseCases, cubriendo casos de éxito, errores y edge cases.
"""

from unittest.mock import MagicMock

import pytest

from src.application.use_cases.wiki_use_cases import (
    CreateWikiPageRequest,
    ListWikiPagesRequest,
    UpdateWikiPageRequest,
    WikiUseCases,
)
from src.domain.entities.wiki_page import WikiPage
from src.domain.exceptions import ResourceNotFoundError


class TestCreateWikiPage:
    """Tests para el caso de uso create_wiki_page."""

    @pytest.mark.asyncio
    async def test_create_wiki_page_success(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe crear una wiki page exitosamente."""
        # Arrange
        mock_wiki_repository.create.return_value = sample_wiki_page
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        request = CreateWikiPageRequest(
            slug="home",
            content="# Home\n\nWelcome to the wiki",
            project_id=1,
        )

        # Act
        result = await use_cases.create_wiki_page(request)

        # Assert
        assert result == sample_wiki_page
        mock_wiki_repository.create.assert_called_once()
        created_page = mock_wiki_repository.create.call_args[0][0]
        assert created_page.slug == "home"
        assert created_page.project_id == 1

    @pytest.mark.asyncio
    async def test_create_wiki_page_with_empty_content(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe crear una wiki page con contenido vacío."""
        # Arrange
        mock_wiki_repository.create.return_value = sample_wiki_page
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        request = CreateWikiPageRequest(
            slug="empty-page",
            project_id=1,
        )

        # Act
        result = await use_cases.create_wiki_page(request)

        # Assert
        assert result == sample_wiki_page
        created_page = mock_wiki_repository.create.call_args[0][0]
        assert created_page.slug == "empty-page"
        assert created_page.content == ""

    @pytest.mark.asyncio
    async def test_create_wiki_page_with_markdown(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe crear una wiki page con contenido markdown complejo."""
        # Arrange
        mock_wiki_repository.create.return_value = sample_wiki_page
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        markdown_content = """# Getting Started

## Installation

```bash
pip install taiga
```

## Usage

1. Import the library
2. Configure credentials
3. Make API calls

> **Note**: See [API docs](./api-docs) for more information."""
        request = CreateWikiPageRequest(
            slug="getting-started",
            content=markdown_content,
            project_id=1,
        )

        # Act
        await use_cases.create_wiki_page(request)

        # Assert
        created_page = mock_wiki_repository.create.call_args[0][0]
        assert created_page.content == markdown_content


class TestGetWikiPage:
    """Tests para el caso de uso get_wiki_page."""

    @pytest.mark.asyncio
    async def test_get_wiki_page_success(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe retornar la wiki page cuando existe."""
        # Arrange
        mock_wiki_repository.get_by_id.return_value = sample_wiki_page
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Act
        result = await use_cases.get_wiki_page(page_id=1)

        # Assert
        assert result == sample_wiki_page
        mock_wiki_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_wiki_page_not_found(self, mock_wiki_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_wiki_repository.get_by_id.return_value = None
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await use_cases.get_wiki_page(page_id=999)

        assert "WikiPage 999 not found" in str(exc_info.value)
        mock_wiki_repository.get_by_id.assert_called_once_with(999)


class TestGetBySlug:
    """Tests para el caso de uso get_by_slug."""

    @pytest.mark.asyncio
    async def test_get_by_slug_success(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe retornar la wiki page cuando existe el slug."""
        # Arrange
        mock_wiki_repository.get_by_slug.return_value = sample_wiki_page
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Act
        result = await use_cases.get_by_slug(project_id=1, slug="home")

        # Assert
        assert result == sample_wiki_page
        mock_wiki_repository.get_by_slug.assert_called_once_with(1, "home")

    @pytest.mark.asyncio
    async def test_get_by_slug_not_found(self, mock_wiki_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe el slug."""
        # Arrange
        mock_wiki_repository.get_by_slug.return_value = None
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await use_cases.get_by_slug(project_id=1, slug="nonexistent")

        assert "WikiPage with slug 'nonexistent' not found in project 1" in str(exc_info.value)


class TestListWikiPages:
    """Tests para el caso de uso list_wiki_pages."""

    @pytest.mark.asyncio
    async def test_list_wiki_pages_no_filters(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe listar wiki pages sin filtros."""
        # Arrange
        mock_wiki_repository.list.return_value = [sample_wiki_page]
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        request = ListWikiPagesRequest()

        # Act
        result = await use_cases.list_wiki_pages(request)

        # Assert
        assert result == [sample_wiki_page]
        mock_wiki_repository.list.assert_called_once_with(filters={}, limit=None, offset=None)

    @pytest.mark.asyncio
    async def test_list_wiki_pages_by_project(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe filtrar wiki pages por proyecto."""
        # Arrange
        mock_wiki_repository.list.return_value = [sample_wiki_page]
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        request = ListWikiPagesRequest(project_id=1)

        # Act
        result = await use_cases.list_wiki_pages(request)

        # Assert
        assert result == [sample_wiki_page]
        mock_wiki_repository.list.assert_called_once_with(
            filters={"project": 1}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_wiki_pages_by_deleted_status(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe filtrar wiki pages por estado eliminado."""
        # Arrange
        mock_wiki_repository.list.return_value = [sample_wiki_page]
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        request = ListWikiPagesRequest(is_deleted=False)

        # Act
        await use_cases.list_wiki_pages(request)

        # Assert
        mock_wiki_repository.list.assert_called_once_with(
            filters={"is_deleted": False}, limit=None, offset=None
        )

    @pytest.mark.asyncio
    async def test_list_wiki_pages_with_pagination(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe aplicar paginación correctamente."""
        # Arrange
        mock_wiki_repository.list.return_value = [sample_wiki_page]
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        request = ListWikiPagesRequest(limit=10, offset=20)

        # Act
        await use_cases.list_wiki_pages(request)

        # Assert
        mock_wiki_repository.list.assert_called_once_with(filters={}, limit=10, offset=20)

    @pytest.mark.asyncio
    async def test_list_wiki_pages_with_all_filters(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe aplicar todos los filtros combinados."""
        # Arrange
        mock_wiki_repository.list.return_value = [sample_wiki_page]
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        request = ListWikiPagesRequest(project_id=1, is_deleted=True, limit=50, offset=10)

        # Act
        await use_cases.list_wiki_pages(request)

        # Assert
        mock_wiki_repository.list.assert_called_once_with(
            filters={"project": 1, "is_deleted": True}, limit=50, offset=10
        )

    @pytest.mark.asyncio
    async def test_list_wiki_pages_empty_result(self, mock_wiki_repository: MagicMock) -> None:
        """Debe retornar lista vacía cuando no hay wiki pages."""
        # Arrange
        mock_wiki_repository.list.return_value = []
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        request = ListWikiPagesRequest()

        # Act
        result = await use_cases.list_wiki_pages(request)

        # Assert
        assert result == []


class TestListByProject:
    """Tests para el caso de uso list_by_project."""

    @pytest.mark.asyncio
    async def test_list_by_project_success(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe listar wiki pages de un proyecto."""
        # Arrange
        mock_wiki_repository.list_by_project.return_value = [sample_wiki_page]
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Act
        result = await use_cases.list_by_project(project_id=1)

        # Assert
        assert result == [sample_wiki_page]
        mock_wiki_repository.list_by_project.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_by_project_empty(self, mock_wiki_repository: MagicMock) -> None:
        """Debe retornar lista vacía si el proyecto no tiene wiki pages."""
        # Arrange
        mock_wiki_repository.list_by_project.return_value = []
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Act
        result = await use_cases.list_by_project(project_id=1)

        # Assert
        assert result == []


class TestListActive:
    """Tests para el caso de uso list_active."""

    @pytest.mark.asyncio
    async def test_list_active_success(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe listar wiki pages activas de un proyecto."""
        # Arrange
        mock_wiki_repository.list_active.return_value = [sample_wiki_page]
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Act
        result = await use_cases.list_active(project_id=1)

        # Assert
        assert result == [sample_wiki_page]
        mock_wiki_repository.list_active.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_active_empty(self, mock_wiki_repository: MagicMock) -> None:
        """Debe retornar lista vacía si no hay wiki pages activas."""
        # Arrange
        mock_wiki_repository.list_active.return_value = []
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Act
        result = await use_cases.list_active(project_id=1)

        # Assert
        assert result == []


class TestListDeleted:
    """Tests para el caso de uso list_deleted."""

    @pytest.mark.asyncio
    async def test_list_deleted_success(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe listar wiki pages eliminadas de un proyecto."""
        # Arrange
        deleted_page = WikiPage(
            id=2,
            slug="old-page",
            content="Old content",
            project_id=1,
            is_deleted=True,
        )
        mock_wiki_repository.list_deleted.return_value = [deleted_page]
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Act
        result = await use_cases.list_deleted(project_id=1)

        # Assert
        assert result == [deleted_page]
        mock_wiki_repository.list_deleted.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_deleted_empty(self, mock_wiki_repository: MagicMock) -> None:
        """Debe retornar lista vacía si no hay wiki pages eliminadas."""
        # Arrange
        mock_wiki_repository.list_deleted.return_value = []
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Act
        result = await use_cases.list_deleted(project_id=1)

        # Assert
        assert result == []


class TestUpdateWikiPage:
    """Tests para el caso de uso update_wiki_page."""

    @pytest.mark.asyncio
    async def test_update_wiki_page_success(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe actualizar la wiki page exitosamente."""
        # Arrange
        mock_wiki_repository.get_by_id.return_value = sample_wiki_page
        updated_page = WikiPage(
            id=1,
            slug="home-updated",
            content="# Home Updated\n\nNew content",
            project_id=1,
        )
        mock_wiki_repository.update.return_value = updated_page
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        request = UpdateWikiPageRequest(
            page_id=1, slug="home-updated", content="# Home Updated\n\nNew content"
        )

        # Act
        result = await use_cases.update_wiki_page(request)

        # Assert
        assert result == updated_page
        mock_wiki_repository.get_by_id.assert_called_once_with(1)
        mock_wiki_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_wiki_page_not_found(self, mock_wiki_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_wiki_repository.get_by_id.return_value = None
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        request = UpdateWikiPageRequest(page_id=999, slug="new-slug")

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.update_wiki_page(request)

        mock_wiki_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_wiki_page_slug_only(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe actualizar solo el slug."""
        # Arrange
        mock_wiki_repository.get_by_id.return_value = sample_wiki_page
        mock_wiki_repository.update.return_value = sample_wiki_page
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        request = UpdateWikiPageRequest(page_id=1, slug="new-slug")

        # Act
        await use_cases.update_wiki_page(request)

        # Assert
        updated_page = mock_wiki_repository.update.call_args[0][0]
        assert updated_page.slug == "new-slug"

    @pytest.mark.asyncio
    async def test_update_wiki_page_content_only(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe actualizar solo el contenido."""
        # Arrange
        mock_wiki_repository.get_by_id.return_value = sample_wiki_page
        mock_wiki_repository.update.return_value = sample_wiki_page
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        request = UpdateWikiPageRequest(page_id=1, content="# New Content")

        # Act
        await use_cases.update_wiki_page(request)

        # Assert
        updated_page = mock_wiki_repository.update.call_args[0][0]
        assert updated_page.content == "# New Content"


class TestDeleteWikiPage:
    """Tests para el caso de uso delete_wiki_page."""

    @pytest.mark.asyncio
    async def test_delete_wiki_page_success(self, mock_wiki_repository: MagicMock) -> None:
        """Debe eliminar la wiki page exitosamente (hard delete)."""
        # Arrange
        mock_wiki_repository.delete.return_value = True
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Act
        result = await use_cases.delete_wiki_page(page_id=1)

        # Assert
        assert result is True
        mock_wiki_repository.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_wiki_page_not_found(self, mock_wiki_repository: MagicMock) -> None:
        """Debe retornar False cuando la wiki page no existe."""
        # Arrange
        mock_wiki_repository.delete.return_value = False
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Act
        result = await use_cases.delete_wiki_page(page_id=999)

        # Assert
        assert result is False


class TestSoftDeleteWikiPage:
    """Tests para el caso de uso soft_delete_wiki_page."""

    @pytest.mark.asyncio
    async def test_soft_delete_wiki_page_success(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe marcar la wiki page como eliminada."""
        # Arrange
        sample_wiki_page.is_deleted = False
        mock_wiki_repository.get_by_id.return_value = sample_wiki_page
        mock_wiki_repository.update.return_value = sample_wiki_page
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Act
        await use_cases.soft_delete_wiki_page(page_id=1)

        # Assert
        mock_wiki_repository.get_by_id.assert_called_once_with(1)
        mock_wiki_repository.update.assert_called_once()
        # Verify page.delete() was called (sets is_deleted=True)
        updated_page = mock_wiki_repository.update.call_args[0][0]
        assert updated_page.is_deleted is True

    @pytest.mark.asyncio
    async def test_soft_delete_wiki_page_not_found(self, mock_wiki_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_wiki_repository.get_by_id.return_value = None
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.soft_delete_wiki_page(page_id=999)

        mock_wiki_repository.update.assert_not_called()


class TestRestoreWikiPage:
    """Tests para el caso de uso restore_wiki_page."""

    @pytest.mark.asyncio
    async def test_restore_wiki_page_success(
        self, mock_wiki_repository: MagicMock, sample_wiki_page: WikiPage
    ) -> None:
        """Debe restaurar la wiki page eliminada."""
        # Arrange
        sample_wiki_page.is_deleted = True
        mock_wiki_repository.get_by_id.return_value = sample_wiki_page
        mock_wiki_repository.update.return_value = sample_wiki_page
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Act
        await use_cases.restore_wiki_page(page_id=1)

        # Assert
        mock_wiki_repository.get_by_id.assert_called_once_with(1)
        mock_wiki_repository.update.assert_called_once()
        # Verify page.restore() was called (sets is_deleted=False)
        updated_page = mock_wiki_repository.update.call_args[0][0]
        assert updated_page.is_deleted is False

    @pytest.mark.asyncio
    async def test_restore_wiki_page_not_found(self, mock_wiki_repository: MagicMock) -> None:
        """Debe lanzar ResourceNotFoundError cuando no existe."""
        # Arrange
        mock_wiki_repository.get_by_id.return_value = None
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            await use_cases.restore_wiki_page(page_id=999)

        mock_wiki_repository.update.assert_not_called()


class TestWikiUseCasesInitialization:
    """Tests para la inicialización de WikiUseCases."""

    def test_initialization_with_repository(self, mock_wiki_repository: MagicMock) -> None:
        """Debe inicializarse correctamente con el repositorio."""
        # Act
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        # Assert
        assert use_cases.repository == mock_wiki_repository
