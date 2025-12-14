"""
Tests de integración para casos de uso de wiki pages.
Implementa tests para la capa de aplicación.
"""

from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.wiki_use_cases import (
    CreateWikiPageRequest,
    ListWikiPagesRequest,
    UpdateWikiPageRequest,
    WikiUseCases,
)
from src.domain.entities.wiki_page import WikiPage
from src.domain.exceptions import ResourceNotFoundError


@pytest.fixture
def mock_wiki_repository() -> AsyncMock:
    """Crea un mock del repositorio de wiki pages."""
    return AsyncMock()


@pytest.fixture
def sample_wiki_page() -> WikiPage:
    """Crea una wiki page de ejemplo para tests."""
    return WikiPage(
        id=1,
        project_id=100,
        slug="test-page",
        content="# Test Content\n\nThis is test content.",
    )


@pytest.fixture
def sample_wiki_pages_list(sample_wiki_page: WikiPage) -> list[WikiPage]:
    """Lista de wiki pages de ejemplo."""
    return [
        sample_wiki_page,
        WikiPage(id=2, project_id=100, slug="another-page", content="Another page"),
    ]


@pytest.mark.integration
@pytest.mark.asyncio
class TestWikiUseCases:
    """Tests de integración para casos de uso de wiki pages."""

    async def test_list_wiki_pages(
        self,
        mock_wiki_repository: AsyncMock,
        sample_wiki_pages_list: list[WikiPage],
    ) -> None:
        """Verifica el caso de uso de listar wiki pages."""
        mock_wiki_repository.list.return_value = sample_wiki_pages_list
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        request = ListWikiPagesRequest(project_id=100)

        result = await use_cases.list_wiki_pages(request)

        assert len(result) == 2
        mock_wiki_repository.list.assert_called_once()

    async def test_list_by_project(
        self,
        mock_wiki_repository: AsyncMock,
        sample_wiki_pages_list: list[WikiPage],
    ) -> None:
        """Verifica el caso de uso de listar wiki pages por proyecto."""
        mock_wiki_repository.list_by_project.return_value = sample_wiki_pages_list
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        result = await use_cases.list_by_project(project_id=100)

        assert len(result) == 2
        mock_wiki_repository.list_by_project.assert_called_once_with(100)

    async def test_list_active(
        self,
        mock_wiki_repository: AsyncMock,
        sample_wiki_pages_list: list[WikiPage],
    ) -> None:
        """Verifica el caso de uso de listar wiki pages activas."""
        mock_wiki_repository.list_active.return_value = sample_wiki_pages_list
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        result = await use_cases.list_active(project_id=100)

        assert len(result) == 2
        mock_wiki_repository.list_active.assert_called_once_with(100)

    async def test_list_deleted(
        self,
        mock_wiki_repository: AsyncMock,
        sample_wiki_pages_list: list[WikiPage],
    ) -> None:
        """Verifica el caso de uso de listar wiki pages eliminadas."""
        mock_wiki_repository.list_deleted.return_value = sample_wiki_pages_list
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        result = await use_cases.list_deleted(project_id=100)

        assert len(result) == 2
        mock_wiki_repository.list_deleted.assert_called_once_with(100)

    async def test_create_wiki_page(
        self, mock_wiki_repository: AsyncMock, sample_wiki_page: WikiPage
    ) -> None:
        """Verifica el caso de uso de crear una wiki page."""
        mock_wiki_repository.create.return_value = sample_wiki_page
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        request = CreateWikiPageRequest(
            project_id=100,
            slug="test-page",
            content="# Test Content\n\nThis is test content.",
        )

        result = await use_cases.create_wiki_page(request)

        assert result.id == 1
        assert result.slug == "test-page"
        mock_wiki_repository.create.assert_called_once()

    async def test_get_wiki_page_by_id(
        self, mock_wiki_repository: AsyncMock, sample_wiki_page: WikiPage
    ) -> None:
        """Verifica el caso de uso de obtener wiki page por ID."""
        mock_wiki_repository.get_by_id.return_value = sample_wiki_page
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        result = await use_cases.get_wiki_page(page_id=1)

        assert result.id == 1
        mock_wiki_repository.get_by_id.assert_called_once_with(1)

    async def test_get_wiki_page_by_id_not_found(self, mock_wiki_repository: AsyncMock) -> None:
        """Verifica que se lance ResourceNotFoundError si la wiki page no existe."""
        mock_wiki_repository.get_by_id.return_value = None
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        with pytest.raises(ResourceNotFoundError, match="WikiPage 999 not found"):
            await use_cases.get_wiki_page(page_id=999)

    async def test_get_by_slug(
        self, mock_wiki_repository: AsyncMock, sample_wiki_page: WikiPage
    ) -> None:
        """Verifica el caso de uso de obtener wiki page por slug."""
        mock_wiki_repository.get_by_slug.return_value = sample_wiki_page
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        result = await use_cases.get_by_slug(project_id=100, slug="test-page")

        assert result.slug == "test-page"
        mock_wiki_repository.get_by_slug.assert_called_once_with(100, "test-page")

    async def test_get_by_slug_not_found(self, mock_wiki_repository: AsyncMock) -> None:
        """Verifica que se lance ResourceNotFoundError si no se encuentra por slug."""
        mock_wiki_repository.get_by_slug.return_value = None
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        with pytest.raises(ResourceNotFoundError, match="slug 'unknown' not found"):
            await use_cases.get_by_slug(project_id=100, slug="unknown")

    async def test_update_wiki_page(
        self, mock_wiki_repository: AsyncMock, sample_wiki_page: WikiPage
    ) -> None:
        """Verifica el caso de uso de actualizar una wiki page."""
        updated = WikiPage(
            id=1,
            project_id=100,
            slug="test-page",
            content="# Updated Content",
        )
        mock_wiki_repository.get_by_id.return_value = sample_wiki_page
        mock_wiki_repository.update.return_value = updated
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        request = UpdateWikiPageRequest(page_id=1, content="# Updated Content")

        result = await use_cases.update_wiki_page(request)

        assert result.content == "# Updated Content"
        mock_wiki_repository.update.assert_called_once()

    async def test_update_wiki_page_not_found(self, mock_wiki_repository: AsyncMock) -> None:
        """Verifica que update lance ResourceNotFoundError si no existe."""
        mock_wiki_repository.get_by_id.return_value = None
        use_cases = WikiUseCases(repository=mock_wiki_repository)
        request = UpdateWikiPageRequest(page_id=999, content="# Updated")

        with pytest.raises(ResourceNotFoundError, match="WikiPage 999 not found"):
            await use_cases.update_wiki_page(request)

    async def test_delete_wiki_page(self, mock_wiki_repository: AsyncMock) -> None:
        """Verifica el caso de uso de eliminar una wiki page (hard delete)."""
        mock_wiki_repository.delete.return_value = True
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        result = await use_cases.delete_wiki_page(page_id=1)

        assert result is True
        mock_wiki_repository.delete.assert_called_once_with(1)

    async def test_delete_wiki_page_not_found(self, mock_wiki_repository: AsyncMock) -> None:
        """Verifica que delete devuelva False si la wiki page no existe."""
        mock_wiki_repository.delete.return_value = False
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        result = await use_cases.delete_wiki_page(page_id=999)

        assert result is False

    async def test_soft_delete_wiki_page(
        self, mock_wiki_repository: AsyncMock, sample_wiki_page: WikiPage
    ) -> None:
        """Verifica el caso de uso de soft delete de wiki page."""
        deleted_page = WikiPage(
            id=1,
            project_id=100,
            slug="test-page",
            content="# Test Content",
            is_deleted=True,
        )
        mock_wiki_repository.get_by_id.return_value = sample_wiki_page
        mock_wiki_repository.update.return_value = deleted_page
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        result = await use_cases.soft_delete_wiki_page(page_id=1)

        assert result.is_deleted is True
        mock_wiki_repository.update.assert_called_once()

    async def test_soft_delete_wiki_page_not_found(self, mock_wiki_repository: AsyncMock) -> None:
        """Verifica que soft delete lance ResourceNotFoundError si no existe."""
        mock_wiki_repository.get_by_id.return_value = None
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        with pytest.raises(ResourceNotFoundError, match="WikiPage 999 not found"):
            await use_cases.soft_delete_wiki_page(page_id=999)

    async def test_restore_wiki_page(self, mock_wiki_repository: AsyncMock) -> None:
        """Verifica el caso de uso de restaurar wiki page."""
        deleted_page = WikiPage(
            id=1,
            project_id=100,
            slug="test-page",
            content="# Test Content",
            is_deleted=True,
        )
        restored_page = WikiPage(
            id=1,
            project_id=100,
            slug="test-page",
            content="# Test Content",
            is_deleted=False,
        )
        mock_wiki_repository.get_by_id.return_value = deleted_page
        mock_wiki_repository.update.return_value = restored_page
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        result = await use_cases.restore_wiki_page(page_id=1)

        assert result.is_deleted is False
        mock_wiki_repository.update.assert_called_once()

    async def test_restore_wiki_page_not_found(self, mock_wiki_repository: AsyncMock) -> None:
        """Verifica que restore lance ResourceNotFoundError si no existe."""
        mock_wiki_repository.get_by_id.return_value = None
        use_cases = WikiUseCases(repository=mock_wiki_repository)

        with pytest.raises(ResourceNotFoundError, match="WikiPage 999 not found"):
            await use_cases.restore_wiki_page(page_id=999)
