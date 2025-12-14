"""Tests for BaseEntity."""

from src.domain.entities.base import BaseEntity


class ConcreteEntity(BaseEntity):
    """Concrete implementation of BaseEntity for testing."""

    name: str


def test_base_entity_creation() -> None:
    """Test creating a base entity."""
    entity = ConcreteEntity(name="Test")
    assert entity.name == "Test"
    assert entity.id is None
    assert entity.version is None


def test_base_entity_with_id() -> None:
    """Test creating entity with ID."""
    entity = ConcreteEntity(id=1, name="Test")
    assert entity.id == 1
    assert entity.name == "Test"


def test_base_entity_with_version() -> None:
    """Test creating entity with version."""
    entity = ConcreteEntity(id=1, version=2, name="Test")
    assert entity.version == 2


def test_base_entity_equality_with_same_id() -> None:
    """Test that entities with same ID are equal."""
    entity1 = ConcreteEntity(id=1, name="Test1")
    entity2 = ConcreteEntity(id=1, name="Test2")
    assert entity1 == entity2


def test_base_entity_equality_with_different_id() -> None:
    """Test that entities with different IDs are not equal."""
    entity1 = ConcreteEntity(id=1, name="Test")
    entity2 = ConcreteEntity(id=2, name="Test")
    assert entity1 != entity2


def test_base_entity_equality_with_none_id() -> None:
    """Test that entities without ID are not equal."""
    entity1 = ConcreteEntity(name="Test")
    entity2 = ConcreteEntity(name="Test")
    assert entity1 != entity2


def test_base_entity_equality_with_different_type() -> None:
    """Test that entity is not equal to different type."""
    entity = ConcreteEntity(id=1, name="Test")
    assert entity != "not an entity"
    assert entity != 1
    assert entity != None  # noqa: E711


def test_base_entity_hash_with_id() -> None:
    """Test hash for entity with ID."""
    entity1 = ConcreteEntity(id=1, name="Test1")
    entity2 = ConcreteEntity(id=1, name="Test2")
    assert hash(entity1) == hash(entity2)


def test_base_entity_hash_without_id() -> None:
    """Test hash for entity without ID."""
    entity = ConcreteEntity(name="Test")
    # Entity without ID uses default object hash
    assert isinstance(hash(entity), int)


def test_base_entity_in_set() -> None:
    """Test that entities can be used in sets."""
    entity1 = ConcreteEntity(id=1, name="Test1")
    entity2 = ConcreteEntity(id=1, name="Test2")  # Same ID
    entity3 = ConcreteEntity(id=2, name="Test3")  # Different ID

    entities = {entity1, entity2, entity3}
    assert len(entities) == 2  # entity1 and entity2 are considered equal


def test_base_entity_in_dict() -> None:
    """Test that entities can be used as dict keys."""
    entity1 = ConcreteEntity(id=1, name="Test")
    entity2 = ConcreteEntity(id=2, name="Test")

    mapping = {entity1: "value1", entity2: "value2"}
    assert mapping[entity1] == "value1"
    assert mapping[entity2] == "value2"


def test_base_entity_mutability() -> None:
    """Test that entities are mutable."""
    entity = ConcreteEntity(id=1, name="Test")
    entity.name = "Updated"
    assert entity.name == "Updated"


def test_base_entity_validation_on_assignment() -> None:
    """Test that validation occurs on assignment."""
    entity = ConcreteEntity(name="Test")
    # Should validate that name is still a string
    entity.name = "New Name"
    assert entity.name == "New Name"


def test_base_entity_whitespace_stripping() -> None:
    """Test that whitespace is stripped from string fields."""
    entity = ConcreteEntity(name="  Test  ")
    assert entity.name == "Test"
