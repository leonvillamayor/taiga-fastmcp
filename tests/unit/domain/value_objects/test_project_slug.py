"""Tests for ProjectSlug value object."""

import pytest
from pydantic import ValidationError

from src.domain.value_objects.project_slug import ProjectSlug


def test_project_slug_valid() -> None:
    """Test creating a valid project slug."""
    slug = ProjectSlug(value="mi-proyecto")
    assert slug.value == "mi-proyecto"


def test_project_slug_with_numbers() -> None:
    """Test slug with numbers."""
    slug = ProjectSlug(value="proyecto-2024")
    assert slug.value == "proyecto-2024"


def test_project_slug_only_lowercase() -> None:
    """Test slug with only lowercase letters."""
    slug = ProjectSlug(value="proyecto")
    assert slug.value == "proyecto"


def test_project_slug_only_numbers() -> None:
    """Test slug with only numbers."""
    slug = ProjectSlug(value="12345")
    assert slug.value == "12345"


def test_project_slug_multiple_hyphens() -> None:
    """Test slug with multiple hyphens."""
    slug = ProjectSlug(value="mi-super-proyecto-2024")
    assert slug.value == "mi-super-proyecto-2024"


def test_project_slug_min_length() -> None:
    """Test minimum slug length (3 characters)."""
    slug = ProjectSlug(value="abc")
    assert slug.value == "abc"


def test_project_slug_max_length() -> None:
    """Test maximum slug length (50 characters)."""
    long_slug = "a" * 50
    slug = ProjectSlug(value=long_slug)
    assert slug.value == long_slug


def test_project_slug_too_short() -> None:
    """Test that slug too short raises error."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectSlug(value="ab")
    assert "at least 3 characters" in str(exc_info.value)


def test_project_slug_too_long() -> None:
    """Test that slug too long raises error."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectSlug(value="a" * 51)
    assert "at most 50 characters" in str(exc_info.value)


def test_project_slug_with_uppercase() -> None:
    """Test that uppercase letters are not allowed."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectSlug(value="Mi-Proyecto")
    assert "minúsculas, números y guiones" in str(exc_info.value)


def test_project_slug_with_spaces() -> None:
    """Test that spaces are not allowed."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectSlug(value="mi proyecto")
    assert "minúsculas, números y guiones" in str(exc_info.value)


def test_project_slug_starts_with_hyphen() -> None:
    """Test that starting with hyphen is not allowed."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectSlug(value="-proyecto")
    assert "no al inicio/fin" in str(exc_info.value)


def test_project_slug_ends_with_hyphen() -> None:
    """Test that ending with hyphen is not allowed."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectSlug(value="proyecto-")
    assert "no al inicio/fin" in str(exc_info.value)


def test_project_slug_double_hyphen() -> None:
    """Test that double hyphens are not allowed."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectSlug(value="mi--proyecto")
    assert "minúsculas, números y guiones" in str(exc_info.value)


def test_project_slug_with_special_characters() -> None:
    """Test that special characters are not allowed."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectSlug(value="mi_proyecto")
    assert "minúsculas, números y guiones" in str(exc_info.value)


def test_project_slug_immutability() -> None:
    """Test that ProjectSlug is immutable."""
    slug = ProjectSlug(value="mi-proyecto")
    with pytest.raises(ValidationError):
        slug.value = "otro-proyecto"


def test_project_slug_str() -> None:
    """Test string representation."""
    slug = ProjectSlug(value="mi-proyecto")
    assert str(slug) == "mi-proyecto"


def test_project_slug_repr() -> None:
    """Test repr representation."""
    slug = ProjectSlug(value="mi-proyecto")
    assert repr(slug) == "ProjectSlug('mi-proyecto')"


def test_project_slug_equality() -> None:
    """Test equality between slugs."""
    slug1 = ProjectSlug(value="mi-proyecto")
    slug2 = ProjectSlug(value="mi-proyecto")
    assert slug1 == slug2


def test_project_slug_inequality() -> None:
    """Test inequality between different slugs."""
    slug1 = ProjectSlug(value="proyecto-a")
    slug2 = ProjectSlug(value="proyecto-b")
    assert slug1 != slug2


def test_project_slug_hash() -> None:
    """Test that slugs can be hashed."""
    slug1 = ProjectSlug(value="mi-proyecto")
    slug2 = ProjectSlug(value="mi-proyecto")
    assert hash(slug1) == hash(slug2)


def test_project_slug_in_set() -> None:
    """Test that slugs can be used in sets."""
    slug1 = ProjectSlug(value="proyecto-a")
    slug2 = ProjectSlug(value="proyecto-b")
    slug3 = ProjectSlug(value="proyecto-a")  # Duplicate

    slugs = {slug1, slug2, slug3}
    assert len(slugs) == 2


def test_project_slug_whitespace_stripping() -> None:
    """Test that whitespace is stripped."""
    slug = ProjectSlug(value="  mi-proyecto  ")
    assert slug.value == "mi-proyecto"
