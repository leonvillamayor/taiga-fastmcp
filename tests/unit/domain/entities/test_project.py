"""Tests for Project entity."""

import pytest
from pydantic import ValidationError

from src.domain.entities.project import Project
from src.domain.value_objects.project_slug import ProjectSlug


def test_project_creation() -> None:
    """Test creating a project."""
    project = Project(name="My Project")
    assert project.name == "My Project"
    assert project.description == ""
    assert project.is_private is True


def test_project_with_slug() -> None:
    """Test project with slug."""
    slug = ProjectSlug(value="my-project")
    project = Project(name="My Project", slug=slug)
    assert project.slug == slug


def test_project_name_validation_empty() -> None:
    """Test that empty name raises error."""
    with pytest.raises(ValidationError) as exc_info:
        Project(name="")
    assert "El nombre del proyecto no puede estar vacío" in str(exc_info.value)


def test_project_name_validation_whitespace() -> None:
    """Test that whitespace-only name raises error."""
    with pytest.raises(ValidationError) as exc_info:
        Project(name="   ")
    assert "El nombre del proyecto no puede estar vacío" in str(exc_info.value)


def test_project_name_stripped() -> None:
    """Test that name whitespace is stripped."""
    project = Project(name="  My Project  ")
    assert project.name == "My Project"


def test_project_tags_normalized() -> None:
    """Test that tags are normalized."""
    project = Project(name="Project", tags=["Tag1", "TAG2", "  tag3  ", "TAG1"])
    assert "tag1" in project.tags
    assert "tag2" in project.tags
    assert "tag3" in project.tags
    assert len(project.tags) == 3  # Duplicates removed


def test_project_activate_module() -> None:
    """Test activating a module."""
    project = Project(name="Project", is_wiki_activated=False)
    project.activate_module("wiki")
    assert project.is_wiki_activated is True


def test_project_deactivate_module() -> None:
    """Test deactivating a module."""
    project = Project(name="Project", is_wiki_activated=True)
    project.deactivate_module("wiki")
    assert project.is_wiki_activated is False


def test_project_activate_unknown_module() -> None:
    """Test activating unknown module raises error."""
    project = Project(name="Project")
    with pytest.raises(ValueError) as exc_info:
        project.activate_module("unknown")
    assert "Módulo desconocido" in str(exc_info.value)


def test_project_deactivate_unknown_module() -> None:
    """Test deactivating unknown module raises error."""
    project = Project(name="Project")
    with pytest.raises(ValueError) as exc_info:
        project.deactivate_module("unknown")
    assert "Módulo desconocido" in str(exc_info.value)


def test_project_all_modules() -> None:
    """Test all module operations."""
    project = Project(name="Project")

    # Test backlog
    project.deactivate_module("backlog")
    assert project.is_backlog_activated is False
    project.activate_module("backlog")
    assert project.is_backlog_activated is True

    # Test kanban
    project.deactivate_module("kanban")
    assert project.is_kanban_activated is False
    project.activate_module("kanban")
    assert project.is_kanban_activated is True

    # Test issues
    project.deactivate_module("issues")
    assert project.is_issues_activated is False
    project.activate_module("issues")
    assert project.is_issues_activated is True


def test_project_story_points_non_negative() -> None:
    """Test that story points must be non-negative."""
    with pytest.raises(ValidationError):
        Project(name="Project", total_story_points=-1.0)


def test_project_milestones_non_negative() -> None:
    """Test that total milestones must be non-negative."""
    with pytest.raises(ValidationError):
        Project(name="Project", total_milestones=-1)


def test_project_with_metadata() -> None:
    """Test project with metadata."""
    project = Project(name="Project", owner_id=1, total_story_points=100.5, total_milestones=5)
    assert project.owner_id == 1
    assert project.total_story_points == 100.5
    assert project.total_milestones == 5


def test_project_slug_string_conversion() -> None:
    """Test that slug string is automatically converted to ProjectSlug."""
    project = Project(name="Project", slug="my-project-slug")
    assert isinstance(project.slug, ProjectSlug)
    assert project.slug.value == "my-project-slug"


def test_project_slug_none() -> None:
    """Test that slug can be None."""
    project = Project(name="Project", slug=None)
    assert project.slug is None


def test_project_equality_by_id() -> None:
    """Test that two projects with same ID are equal."""
    project1 = Project(name="Project A", id=1)
    project2 = Project(name="Project B", id=1)
    assert project1 == project2


def test_project_inequality_different_id() -> None:
    """Test that two projects with different IDs are not equal."""
    project1 = Project(name="Project A", id=1)
    project2 = Project(name="Project A", id=2)
    assert project1 != project2


def test_project_to_dict() -> None:
    """Test project serialization to dict."""
    project = Project(name="Project", is_private=False, tags=["tag1", "tag2"])
    data = project.to_dict()
    assert data["name"] == "Project"
    assert data["is_private"] is False
    assert "tag1" in data["tags"]


def test_project_from_dict() -> None:
    """Test project creation from dict."""
    data = {"name": "From Dict", "is_private": True, "owner_id": 42}
    project = Project.from_dict(data)
    assert project.name == "From Dict"
    assert project.is_private is True
    assert project.owner_id == 42


def test_project_empty_tags_filtered() -> None:
    """Test that empty tags are filtered out."""
    project = Project(name="Project", tags=["tag1", "", "  ", "tag2"])
    assert "" not in project.tags
    assert len(project.tags) == 2


def test_project_hash_by_id() -> None:
    """Test that hash is based on ID."""
    project1 = Project(name="Project A", id=1)
    project2 = Project(name="Project B", id=1)
    assert hash(project1) == hash(project2)


def test_project_name_too_long() -> None:
    """Test that name exceeding max length raises error."""
    with pytest.raises(ValidationError):
        Project(name="x" * 256)


def test_project_slug_unknown_type_returns_none() -> None:
    """Test that slug with unknown type returns None."""
    # Pass an integer which is not a recognized slug type
    project = Project(name="Project", slug=123)  # type: ignore[arg-type]
    assert project.slug is None


def test_project_update_from_dict() -> None:
    """Test updating project from dict."""
    project = Project(name="Original", is_private=True)
    project.update_from_dict({"name": "Updated", "is_private": False})
    assert project.name == "Updated"
    assert project.is_private is False


def test_project_update_from_dict_ignores_unknown_keys() -> None:
    """Test that update_from_dict ignores unknown keys."""
    project = Project(name="Original")
    project.update_from_dict({"name": "Updated", "unknown_field": "value"})
    assert project.name == "Updated"
    assert not hasattr(project, "unknown_field")
