"""Unit tests for WikiRepositoryImpl."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.wiki_page import WikiPage
from src.infrastructure.repositories.wiki_repository_impl import WikiRepositoryImpl
from src.taiga_client import TaigaAPIClient


@pytest.fixture
def mock_client() -> MagicMock:
    """Create a mock TaigaAPIClient."""
    client = MagicMock(spec=TaigaAPIClient)
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.patch = AsyncMock()
    client.delete = AsyncMock()
    return client


@pytest.fixture
def repository(mock_client: MagicMock) -> WikiRepositoryImpl:
    """Create a WikiRepositoryImpl instance."""
    return WikiRepositoryImpl(client=mock_client)


@pytest.fixture
def sample_wiki_page_data() -> dict:
    """Create sample wiki page data from API."""
    return {
        "id": 1,
        "slug": "home",
        "content": "# Welcome\n\nThis is the home page.",
        "project": 5,
        "owner": 3,
        "is_deleted": False,
        "version": 1,
    }


class TestWikiRepositoryInit:
    """Tests for WikiRepositoryImpl initialization."""

    def test_init_sets_correct_endpoint(self, repository: WikiRepositoryImpl) -> None:
        """Test that the repository is initialized with correct endpoint."""
        assert repository.endpoint == "wiki"

    def test_init_sets_correct_entity_class(self, repository: WikiRepositoryImpl) -> None:
        """Test that the repository uses WikiPage entity class."""
        assert repository.entity_class == WikiPage


class TestToEntity:
    """Tests for _to_entity field mapping."""

    def test_to_entity_maps_project_to_project_id(
        self, repository: WikiRepositoryImpl, sample_wiki_page_data: dict
    ) -> None:
        """Test that API 'project' field is mapped to 'project_id'."""
        entity = repository._to_entity(sample_wiki_page_data)
        assert entity.project_id == 5

    def test_to_entity_maps_owner_to_owner_id(
        self, repository: WikiRepositoryImpl, sample_wiki_page_data: dict
    ) -> None:
        """Test that API 'owner' field is mapped to 'owner_id'."""
        entity = repository._to_entity(sample_wiki_page_data)
        assert entity.owner_id == 3

    def test_to_entity_preserves_content_and_slug(
        self, repository: WikiRepositoryImpl, sample_wiki_page_data: dict
    ) -> None:
        """Test that content and slug are preserved correctly."""
        entity = repository._to_entity(sample_wiki_page_data)
        assert entity.slug == "home"
        assert "# Welcome" in entity.content


class TestToDict:
    """Tests for _to_dict field mapping."""

    def test_to_dict_maps_project_id_to_project(self, repository: WikiRepositoryImpl) -> None:
        """Test that entity 'project_id' field is mapped to 'project'."""
        entity = WikiPage(id=1, slug="home", project_id=5, version=1)
        data = repository._to_dict(entity)
        assert "project" in data
        assert data["project"] == 5
        assert "project_id" not in data

    def test_to_dict_maps_owner_id_to_owner(self, repository: WikiRepositoryImpl) -> None:
        """Test that entity 'owner_id' field is mapped to 'owner'."""
        entity = WikiPage(id=1, slug="home", project_id=5, owner_id=3, version=1)
        data = repository._to_dict(entity)
        assert "owner" in data
        assert data["owner"] == 3
        assert "owner_id" not in data


class TestGetBySlug:
    """Tests for get_by_slug method."""

    @pytest.mark.asyncio
    async def test_get_by_slug_returns_wiki_page_when_found(
        self,
        repository: WikiRepositoryImpl,
        mock_client: MagicMock,
        sample_wiki_page_data: dict,
    ) -> None:
        """Test that get_by_slug returns a wiki page when found."""
        mock_client.get.return_value = sample_wiki_page_data

        page = await repository.get_by_slug(project_id=5, slug="home")

        assert page is not None
        assert page.id == 1
        assert page.slug == "home"
        mock_client.get.assert_called_once_with(
            "wiki/by_slug", params={"project": 5, "slug": "home"}
        )

    @pytest.mark.asyncio
    async def test_get_by_slug_returns_none_when_not_found(
        self, repository: WikiRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_by_slug returns None when not found."""
        mock_client.get.side_effect = Exception("Not found")

        page = await repository.get_by_slug(project_id=5, slug="nonexistent")

        assert page is None

    @pytest.mark.asyncio
    async def test_get_by_slug_returns_none_for_empty_response(
        self, repository: WikiRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_by_slug returns None for empty response."""
        mock_client.get.return_value = None

        page = await repository.get_by_slug(project_id=5, slug="home")

        assert page is None


class TestListByProject:
    """Tests for list_by_project method."""

    @pytest.mark.asyncio
    async def test_list_by_project_returns_wiki_pages(
        self,
        repository: WikiRepositoryImpl,
        mock_client: MagicMock,
        sample_wiki_page_data: dict,
    ) -> None:
        """Test that list_by_project returns wiki pages for project."""
        mock_client.get.return_value = [sample_wiki_page_data]

        pages = await repository.list_by_project(project_id=5)

        assert len(pages) == 1
        mock_client.get.assert_called_once_with("wiki", params={"project": 5})


class TestListActive:
    """Tests for list_active method."""

    @pytest.mark.asyncio
    async def test_list_active_returns_only_active_pages(
        self,
        repository: WikiRepositoryImpl,
        mock_client: MagicMock,
        sample_wiki_page_data: dict,
    ) -> None:
        """Test that list_active returns only non-deleted pages."""
        deleted_page = dict(sample_wiki_page_data)
        deleted_page["id"] = 2
        deleted_page["slug"] = "deleted-page"
        deleted_page["is_deleted"] = True
        mock_client.get.return_value = [sample_wiki_page_data, deleted_page]

        pages = await repository.list_active(project_id=5)

        assert len(pages) == 1
        assert pages[0].is_deleted is False

    @pytest.mark.asyncio
    async def test_list_active_returns_empty_when_all_deleted(
        self,
        repository: WikiRepositoryImpl,
        mock_client: MagicMock,
        sample_wiki_page_data: dict,
    ) -> None:
        """Test that list_active returns empty list when all pages deleted."""
        sample_wiki_page_data["is_deleted"] = True
        mock_client.get.return_value = [sample_wiki_page_data]

        pages = await repository.list_active(project_id=5)

        assert pages == []


class TestListDeleted:
    """Tests for list_deleted method."""

    @pytest.mark.asyncio
    async def test_list_deleted_returns_only_deleted_pages(
        self,
        repository: WikiRepositoryImpl,
        mock_client: MagicMock,
        sample_wiki_page_data: dict,
    ) -> None:
        """Test that list_deleted returns only deleted pages."""
        deleted_page = dict(sample_wiki_page_data)
        deleted_page["id"] = 2
        deleted_page["slug"] = "deleted-page"
        deleted_page["is_deleted"] = True
        mock_client.get.return_value = [sample_wiki_page_data, deleted_page]

        pages = await repository.list_deleted(project_id=5)

        assert len(pages) == 1
        assert pages[0].is_deleted is True
        assert pages[0].slug == "deleted-page"

    @pytest.mark.asyncio
    async def test_list_deleted_returns_empty_when_no_deleted(
        self,
        repository: WikiRepositoryImpl,
        mock_client: MagicMock,
        sample_wiki_page_data: dict,
    ) -> None:
        """Test that list_deleted returns empty list when no deleted pages."""
        mock_client.get.return_value = [sample_wiki_page_data]

        pages = await repository.list_deleted(project_id=5)

        assert pages == []
