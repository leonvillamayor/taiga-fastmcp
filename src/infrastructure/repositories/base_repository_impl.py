"""
Base repository implementation for Taiga MCP Server.

Provides generic CRUD operations using TaigaAPIClient.
All concrete repositories should extend this base class.
"""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar, cast

from src.domain.entities.base import BaseEntity
from src.domain.exceptions import ConcurrencyError, ResourceNotFoundError
from src.domain.repositories.base_repository import BaseRepository
from src.taiga_client import TaigaAPIClient

T = TypeVar("T", bound=BaseEntity)


class BaseRepositoryImpl(BaseRepository[T], Generic[T]):
    """
    Base repository implementation using TaigaAPIClient.

    Provides generic CRUD operations that can be reused by all
    concrete repository implementations.

    Attributes:
        client: TaigaAPIClient instance for API communication
        entity_class: The entity class this repository manages
        endpoint: API endpoint for this entity type (e.g., "epics", "projects")
    """

    def __init__(
        self,
        client: TaigaAPIClient,
        entity_class: type[T],
        endpoint: str,
    ) -> None:
        """
        Initialize the base repository.

        Args:
            client: TaigaAPIClient instance for API communication
            entity_class: The entity class this repository manages
            endpoint: API endpoint for this entity type
        """
        self.client = client
        self.entity_class = entity_class
        self.endpoint = endpoint

    def _to_entity(self, data: dict[str, Any]) -> T:
        """
        Convert API response dictionary to entity.

        Args:
            data: Dictionary from API response

        Returns:
            Entity instance
        """
        return self.entity_class.model_validate(data)

    def _to_dict(self, entity: T, exclude_none: bool = True) -> dict[str, Any]:
        """
        Convert entity to dictionary for API request.

        Args:
            entity: Entity instance
            exclude_none: Whether to exclude None values

        Returns:
            Dictionary for API request
        """
        return entity.model_dump(exclude_none=exclude_none)

    async def get_by_id(self, entity_id: int) -> T | None:
        """
        Get an entity by its ID.

        Args:
            entity_id: Entity ID

        Returns:
            Entity if found, None otherwise
        """
        try:
            response = await self.client.get(f"{self.endpoint}/{entity_id}")
            if response and isinstance(response, dict):
                return self._to_entity(response)
            return None
        except Exception:
            return None

    async def list(
        self,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[T]:
        """
        List entities with optional filters and pagination.

        Args:
            filters: Optional dictionary of filters
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of entities
        """
        params: dict[str, Any] = {}
        if filters:
            params.update(filters)
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        try:
            response = await self.client.get(self.endpoint, params=params if params else None)
            if isinstance(response, list):
                return [self._to_entity(item) for item in response]
            return []
        except Exception:
            return []

    async def create(self, entity: T) -> T:
        """
        Create a new entity.

        Args:
            entity: Entity to create (without ID)

        Returns:
            Created entity with assigned ID

        Raises:
            Exception: If creation fails
        """
        data = self._to_dict(entity)
        # Remove id if None since it will be assigned by the server
        data.pop("id", None)
        data.pop("version", None)

        response = await self.client.post(self.endpoint, data=data)
        return self._to_entity(cast("dict[str, Any]", response))

    async def update(self, entity: T) -> T:
        """
        Update an existing entity (partial update using PATCH).

        Args:
            entity: Entity with updated values (must have ID and version)

        Returns:
            Updated entity

        Raises:
            ResourceNotFoundError: If entity doesn't exist
            ConcurrencyError: If version conflict occurs
        """
        if entity.id is None:
            raise ValueError("Entity must have an ID for update")

        data = self._to_dict(entity)
        entity_id = data.pop("id")

        try:
            response = await self.client.patch(f"{self.endpoint}/{entity_id}", data=data)
            return self._to_entity(cast("dict[str, Any]", response))
        except Exception as e:
            error_message = str(e).lower()
            if "404" in error_message or "not found" in error_message:
                raise ResourceNotFoundError(
                    f"{self.entity_class.__name__} with id {entity_id} not found"
                ) from e
            if "409" in error_message or "conflict" in error_message:
                raise ConcurrencyError(
                    f"Version conflict updating {self.entity_class.__name__} {entity_id}"
                ) from e
            raise

    async def delete(self, entity_id: int) -> bool:
        """
        Delete an entity by ID.

        Args:
            entity_id: ID of entity to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            await self.client.delete(f"{self.endpoint}/{entity_id}")
            return True
        except Exception:
            return False

    async def exists(self, entity_id: int) -> bool:
        """
        Check if an entity exists.

        Args:
            entity_id: Entity ID to check

        Returns:
            True if exists, False otherwise
        """
        entity = await self.get_by_id(entity_id)
        return entity is not None

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """
        Count entities matching the given filters.

        Note: This implementation fetches all entities and counts them.
        Override in specific repositories if the API supports a count endpoint.

        Args:
            filters: Optional dictionary of filters

        Returns:
            Count of matching entities
        """
        entities = await self.list(filters=filters)
        return len(entities)

    async def get_or_create(
        self,
        entity: T,
        lookup_fields: Sequence[str] | None = None,
    ) -> tuple[T, bool]:
        """
        Get an existing entity or create a new one.

        Args:
            entity: Entity to get or create
            lookup_fields: Fields to use for lookup (default: ["id"])

        Returns:
            Tuple of (entity, created) where created is True if new
        """
        # Use lookup_fields if provided to build filter criteria
        if lookup_fields:
            filters: dict[str, Any] = {}
            entity_dict = entity.model_dump()
            for field in lookup_fields:
                if field in entity_dict and entity_dict[field] is not None:
                    filters[field] = entity_dict[field]
            if filters:
                existing_list = await self.list(filters=filters)
                if existing_list:
                    return existing_list[0], False

        if entity.id is not None:
            existing = await self.get_by_id(entity.id)
            if existing:
                return existing, False

        # No existing entity found, create new one
        created = await self.create(entity)
        return created, True
