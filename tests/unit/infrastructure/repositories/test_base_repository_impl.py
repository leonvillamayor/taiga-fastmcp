"""Unit tests for BaseRepositoryImpl."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.base import BaseEntity
from src.domain.exceptions import ConcurrencyError, ResourceNotFoundError
from src.infrastructure.repositories.base_repository_impl import BaseRepositoryImpl
from src.taiga_client import TaigaAPIClient


class SampleEntity(BaseEntity):
    """Sample entity for repository tests."""

    name: str = ""
    description: str | None = None


class ConcreteBaseRepositoryImpl(BaseRepositoryImpl[SampleEntity]):
    """Concrete implementation of BaseRepositoryImpl for testing."""

    def __init__(self, client: TaigaAPIClient) -> None:
        """Initialize test repository."""
        super().__init__(client=client, entity_class=SampleEntity, endpoint="test_entities")


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
def repository(mock_client: MagicMock) -> ConcreteBaseRepositoryImpl:
    """Create a test repository instance."""
    return ConcreteBaseRepositoryImpl(client=mock_client)


class TestToEntity:
    """Tests for _to_entity method."""

    def test_to_entity_converts_dict_to_entity(
        self, repository: ConcreteBaseRepositoryImpl
    ) -> None:
        """Test that _to_entity correctly converts a dictionary to an entity."""
        data = {"id": 1, "name": "Test", "description": "A test entity", "version": 1}
        entity = repository._to_entity(data)

        assert isinstance(entity, SampleEntity)
        assert entity.id == 1
        assert entity.name == "Test"
        assert entity.description == "A test entity"
        assert entity.version == 1

    def test_to_entity_handles_minimal_data(self, repository: ConcreteBaseRepositoryImpl) -> None:
        """Test that _to_entity handles minimal required data."""
        data: dict[str, Any] = {"id": None, "version": 1}
        entity = repository._to_entity(data)

        assert entity.id is None
        assert entity.name == ""
        assert entity.description is None


class TestToDict:
    """Tests for _to_dict method."""

    def test_to_dict_converts_entity_to_dict(self, repository: ConcreteBaseRepositoryImpl) -> None:
        """Test that _to_dict correctly converts an entity to a dictionary."""
        entity = SampleEntity(id=1, name="Test", description="A test", version=2)
        data = repository._to_dict(entity)

        assert data["id"] == 1
        assert data["name"] == "Test"
        assert data["description"] == "A test"
        assert data["version"] == 2

    def test_to_dict_excludes_none_by_default(self, repository: ConcreteBaseRepositoryImpl) -> None:
        """Test that _to_dict excludes None values by default."""
        entity = SampleEntity(id=1, name="Test", description=None, version=1)
        data = repository._to_dict(entity)

        assert "description" not in data

    def test_to_dict_includes_none_when_specified(
        self, repository: ConcreteBaseRepositoryImpl
    ) -> None:
        """Test that _to_dict includes None values when exclude_none is False."""
        entity = SampleEntity(id=1, name="Test", description=None, version=1)
        data = repository._to_dict(entity, exclude_none=False)

        assert "description" in data
        assert data["description"] is None


class TestGetById:
    """Tests for get_by_id method."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_entity_when_found(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_by_id returns an entity when found."""
        mock_client.get.return_value = {
            "id": 1,
            "name": "Test",
            "description": "Found entity",
            "version": 1,
        }

        entity = await repository.get_by_id(1)

        assert entity is not None
        assert entity.id == 1
        assert entity.name == "Test"
        mock_client.get.assert_called_once_with("test_entities/1")

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_by_id returns None when entity is not found."""
        mock_client.get.side_effect = Exception("Not found")

        entity = await repository.get_by_id(999)

        assert entity is None

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_empty_response(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_by_id returns None for empty response."""
        mock_client.get.return_value = None

        entity = await repository.get_by_id(1)

        assert entity is None

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_list_response(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_by_id returns None when response is a list (not dict)."""
        mock_client.get.return_value = [{"id": 1, "name": "Test"}]

        entity = await repository.get_by_id(1)

        assert entity is None


class TestList:
    """Tests for list method."""

    @pytest.mark.asyncio
    async def test_list_returns_entities(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that list returns a list of entities."""
        mock_client.get.return_value = [
            {"id": 1, "name": "Entity 1", "version": 1},
            {"id": 2, "name": "Entity 2", "version": 1},
        ]

        entities = await repository.list()

        assert len(entities) == 2
        assert entities[0].name == "Entity 1"
        assert entities[1].name == "Entity 2"
        mock_client.get.assert_called_once_with("test_entities", params=None)

    @pytest.mark.asyncio
    async def test_list_with_filters(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that list applies filters correctly."""
        mock_client.get.return_value = [{"id": 1, "name": "Filtered", "version": 1}]

        entities = await repository.list(filters={"status": "active"})

        assert len(entities) == 1
        mock_client.get.assert_called_once_with("test_entities", params={"status": "active"})

    @pytest.mark.asyncio
    async def test_list_with_pagination(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that list applies pagination correctly."""
        mock_client.get.return_value = [{"id": 3, "name": "Page 2", "version": 1}]

        entities = await repository.list(limit=10, offset=10)

        assert len(entities) == 1
        mock_client.get.assert_called_once_with("test_entities", params={"limit": 10, "offset": 10})

    @pytest.mark.asyncio
    async def test_list_returns_empty_on_error(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that list returns an empty list on error."""
        mock_client.get.side_effect = Exception("API error")

        entities = await repository.list()

        assert entities == []

    @pytest.mark.asyncio
    async def test_list_returns_empty_for_non_list_response(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that list returns empty for non-list response."""
        mock_client.get.return_value = {"error": "unexpected"}

        entities = await repository.list()

        assert entities == []


class TestCreate:
    """Tests for create method."""

    @pytest.mark.asyncio
    async def test_create_returns_created_entity(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that create returns the created entity with assigned ID."""
        new_entity = SampleEntity(name="New Entity", description="New description")
        mock_client.post.return_value = {
            "id": 42,
            "name": "New Entity",
            "description": "New description",
            "version": 1,
        }

        created = await repository.create(new_entity)

        assert created.id == 42
        assert created.name == "New Entity"
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_removes_id_and_version_from_request(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that create removes id and version from request data."""
        new_entity = SampleEntity(id=100, name="Test", version=5)
        mock_client.post.return_value = {"id": 1, "name": "Test", "version": 1}

        await repository.create(new_entity)

        call_args = mock_client.post.call_args
        data = call_args.kwargs["data"]
        assert "id" not in data
        assert "version" not in data


class TestUpdate:
    """Tests for update method."""

    @pytest.mark.asyncio
    async def test_update_returns_updated_entity(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that update returns the updated entity."""
        entity = SampleEntity(id=1, name="Updated Name", version=2)
        mock_client.patch.return_value = {
            "id": 1,
            "name": "Updated Name",
            "version": 3,
        }

        updated = await repository.update(entity)

        assert updated.id == 1
        assert updated.name == "Updated Name"
        assert updated.version == 3
        mock_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_raises_error_without_id(
        self, repository: ConcreteBaseRepositoryImpl
    ) -> None:
        """Test that update raises ValueError when entity has no ID."""
        entity = SampleEntity(name="No ID", version=1)

        with pytest.raises(ValueError, match="Entity must have an ID"):
            await repository.update(entity)

    @pytest.mark.asyncio
    async def test_update_raises_not_found_error(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that update raises ResourceNotFoundError for 404."""
        entity = SampleEntity(id=999, name="Missing", version=1)
        mock_client.patch.side_effect = Exception("404 Not Found")

        with pytest.raises(ResourceNotFoundError):
            await repository.update(entity)

    @pytest.mark.asyncio
    async def test_update_raises_concurrency_error(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that update raises ConcurrencyError for version conflict."""
        entity = SampleEntity(id=1, name="Conflict", version=1)
        mock_client.patch.side_effect = Exception("409 Conflict")

        with pytest.raises(ConcurrencyError):
            await repository.update(entity)


class TestDelete:
    """Tests for delete method."""

    @pytest.mark.asyncio
    async def test_delete_returns_true_on_success(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that delete returns True on successful deletion."""
        mock_client.delete.return_value = None

        result = await repository.delete(1)

        assert result is True
        mock_client.delete.assert_called_once_with("test_entities/1")

    @pytest.mark.asyncio
    async def test_delete_returns_false_on_error(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that delete returns False on error."""
        mock_client.delete.side_effect = Exception("Delete failed")

        result = await repository.delete(999)

        assert result is False


class TestExists:
    """Tests for exists method."""

    @pytest.mark.asyncio
    async def test_exists_returns_true_when_found(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that exists returns True when entity is found."""
        mock_client.get.return_value = {"id": 1, "name": "Exists", "version": 1}

        result = await repository.exists(1)

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_when_not_found(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that exists returns False when entity is not found."""
        mock_client.get.side_effect = Exception("Not found")

        result = await repository.exists(999)

        assert result is False


class TestCount:
    """Tests for count method."""

    @pytest.mark.asyncio
    async def test_count_returns_number_of_entities(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that count returns the number of matching entities."""
        mock_client.get.return_value = [
            {"id": 1, "name": "E1", "version": 1},
            {"id": 2, "name": "E2", "version": 1},
            {"id": 3, "name": "E3", "version": 1},
        ]

        count = await repository.count()

        assert count == 3

    @pytest.mark.asyncio
    async def test_count_with_filters(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that count applies filters correctly."""
        mock_client.get.return_value = [{"id": 1, "name": "Filtered", "version": 1}]

        count = await repository.count(filters={"status": "active"})

        assert count == 1


class TestGetOrCreate:
    """Tests for get_or_create method."""

    @pytest.mark.asyncio
    async def test_get_or_create_returns_existing_by_id(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_or_create returns existing entity when found by ID."""
        entity = SampleEntity(id=1, name="Existing", version=1)
        mock_client.get.return_value = {
            "id": 1,
            "name": "Existing",
            "version": 1,
        }

        result, created = await repository.get_or_create(entity)

        assert result.id == 1
        assert created is False

    @pytest.mark.asyncio
    async def test_get_or_create_creates_new_entity(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_or_create creates new entity when not found."""
        entity = SampleEntity(name="New Entity", version=1)
        mock_client.get.return_value = []  # List endpoint returns empty
        mock_client.post.return_value = {
            "id": 42,
            "name": "New Entity",
            "version": 1,
        }

        result, created = await repository.get_or_create(entity)

        assert result.id == 42
        assert created is True

    @pytest.mark.asyncio
    async def test_get_or_create_uses_lookup_fields(
        self, repository: ConcreteBaseRepositoryImpl, mock_client: MagicMock
    ) -> None:
        """Test that get_or_create uses lookup_fields for filtering."""
        entity = SampleEntity(name="Lookup Test", version=1)
        mock_client.get.return_value = [{"id": 5, "name": "Lookup Test", "version": 1}]

        result, created = await repository.get_or_create(entity, lookup_fields=["name"])

        assert result.id == 5
        assert created is False
        mock_client.get.assert_called_with("test_entities", params={"name": "Lookup Test"})
