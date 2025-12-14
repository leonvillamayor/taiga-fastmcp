"""Tests unitarios para la entidad WikiPage."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.domain.entities.wiki_page import WikiPage


class TestWikiPageEntity:
    """Tests para la entidad WikiPage."""

    def test_create_wikipage_minimal(self) -> None:
        """Test creating wiki page with minimal data."""
        page = WikiPage(slug="home", project_id=1)
        assert page.slug == "home"
        assert page.project_id == 1
        assert page.content == ""
        assert page.owner_id is None
        assert page.is_deleted is False
        assert page.created_date is None
        assert page.modified_date is None

    def test_create_wikipage_full_data(self) -> None:
        """Test creating wiki page with full data."""
        now = datetime.now()
        page = WikiPage(
            slug="getting-started",
            content="# Getting Started\n\nWelcome to the project!",
            project_id=1,
            owner_id=5,
            is_deleted=False,
            created_date=now,
            modified_date=now,
        )
        assert page.slug == "getting-started"
        assert page.content == "# Getting Started\n\nWelcome to the project!"
        assert page.project_id == 1
        assert page.owner_id == 5
        assert page.is_deleted is False
        assert page.created_date == now
        assert page.modified_date == now

    def test_wikipage_slug_validation_empty(self) -> None:
        """Test that empty slug raises error."""
        with pytest.raises(ValidationError):
            WikiPage(slug="", project_id=1)

    def test_wikipage_slug_validation_whitespace(self) -> None:
        """Test that whitespace-only slug raises error."""
        with pytest.raises(ValidationError):
            WikiPage(slug="   ", project_id=1)

    def test_wikipage_slug_stripped_and_lowercased(self) -> None:
        """Test that slug whitespace is stripped and converted to lowercase."""
        page = WikiPage(slug="  My-Page  ", project_id=1)
        assert page.slug == "my-page"

    def test_wikipage_slug_lowercase_conversion(self) -> None:
        """Test that slug is converted to lowercase."""
        page = WikiPage(slug="MyWikiPage", project_id=1)
        assert page.slug == "mywikipage"

    def test_wikipage_slug_max_length(self) -> None:
        """Test slug max length validation."""
        valid_slug = "a" * 255
        page = WikiPage(slug=valid_slug, project_id=1)
        assert len(page.slug) == 255

        # Test exceeding max length
        invalid_slug = "a" * 256
        with pytest.raises(ValidationError):
            WikiPage(slug=invalid_slug, project_id=1)

    def test_wikipage_project_id_validation(self) -> None:
        """Test that project_id must be positive."""
        with pytest.raises(ValidationError):
            WikiPage(slug="test", project_id=0)

        with pytest.raises(ValidationError):
            WikiPage(slug="test", project_id=-1)

    def test_wikipage_update_content(self) -> None:
        """Test updating wiki page content."""
        page = WikiPage(slug="test", project_id=1, content="Original content")

        # Modified date is None initially
        assert page.modified_date is None

        # Update content
        new_content = "# Updated Content\n\nThis is new."
        page.update_content(new_content)

        assert page.content == new_content
        assert page.modified_date is not None
        assert isinstance(page.modified_date, datetime)

    def test_wikipage_update_content_multiple_times(self) -> None:
        """Test that each update changes modified_date."""
        page = WikiPage(slug="test", project_id=1)

        page.update_content("First update")
        first_modified = page.modified_date

        # Small delay to ensure different timestamp
        import time

        time.sleep(0.01)

        page.update_content("Second update")
        second_modified = page.modified_date

        assert page.content == "Second update"
        assert second_modified > first_modified

    def test_wikipage_delete(self) -> None:
        """Test deleting a wiki page (soft delete)."""
        page = WikiPage(slug="test", project_id=1)
        assert page.is_deleted is False

        page.delete()
        assert page.is_deleted is True

    def test_wikipage_restore(self) -> None:
        """Test restoring a deleted wiki page."""
        page = WikiPage(slug="test", project_id=1, is_deleted=True)
        assert page.is_deleted is True

        page.restore()
        assert page.is_deleted is False

    def test_wikipage_delete_and_restore_cycle(self) -> None:
        """Test multiple delete/restore cycles."""
        page = WikiPage(slug="test", project_id=1)

        # Initial state
        assert page.is_deleted is False

        # Delete
        page.delete()
        assert page.is_deleted is True

        # Restore
        page.restore()
        assert page.is_deleted is False

        # Delete again
        page.delete()
        assert page.is_deleted is True

    def test_wikipage_equality_with_id(self) -> None:
        """Test wiki page equality based on ID."""
        page1 = WikiPage(slug="home", project_id=1)
        page1.id = 100

        page2 = WikiPage(slug="about", project_id=1)
        page2.id = 100

        page3 = WikiPage(slug="contact", project_id=1)
        page3.id = 200

        assert page1 == page2  # Same ID
        assert page1 != page3  # Different ID

    def test_wikipage_equality_without_id(self) -> None:
        """Test that wiki pages without ID are not equal."""
        page1 = WikiPage(slug="home", project_id=1)
        page2 = WikiPage(slug="home", project_id=1)
        assert page1 != page2

    def test_wikipage_hash_with_id(self) -> None:
        """Test wiki page hash with ID."""
        page = WikiPage(slug="test", project_id=1)
        page.id = 100
        assert hash(page) == hash(100)

    def test_wikipage_hash_without_id(self) -> None:
        """Test wiki page hash without ID uses object id."""
        page = WikiPage(slug="test", project_id=1)
        hash_value = hash(page)
        assert isinstance(hash_value, int)

    def test_wikipage_in_set(self) -> None:
        """Test wiki pages can be added to sets."""
        page1 = WikiPage(slug="home", project_id=1)
        page1.id = 100

        page2 = WikiPage(slug="about", project_id=1)
        page2.id = 200

        page_set = {page1, page2}
        assert len(page_set) == 2
        assert page1 in page_set
        assert page2 in page_set

    def test_wikipage_to_dict(self) -> None:
        """Test converting wiki page to dictionary."""
        page = WikiPage(slug="test", project_id=1, content="# Test\n\nContent here", owner_id=5)
        page.id = 100

        page_dict = page.to_dict()
        assert isinstance(page_dict, dict)
        assert page_dict["id"] == 100
        assert page_dict["slug"] == "test"
        assert page_dict["project_id"] == 1
        assert page_dict["content"] == "# Test\n\nContent here"
        assert page_dict["owner_id"] == 5
        assert page_dict["is_deleted"] is False

    def test_wikipage_from_dict(self) -> None:
        """Test creating wiki page from dictionary."""
        data = {
            "id": 100,
            "version": 1,
            "slug": "documentation",
            "content": "# Documentation\n\nProject docs",
            "project_id": 1,
            "owner_id": 5,
            "is_deleted": False,
        }
        page = WikiPage.from_dict(data)
        assert page.id == 100
        assert page.version == 1
        assert page.slug == "documentation"
        assert page.content == "# Documentation\n\nProject docs"
        assert page.project_id == 1
        assert page.owner_id == 5
        assert page.is_deleted is False

    def test_wikipage_update_from_dict(self) -> None:
        """Test updating wiki page from dictionary."""
        page = WikiPage(slug="original", project_id=1, content="Original content")

        update_data = {
            "content": "Updated content",
            "owner_id": 10,
            "is_deleted": True,
        }
        page.update_from_dict(update_data)

        assert page.content == "Updated content"
        assert page.owner_id == 10
        assert page.is_deleted is True
        assert page.slug == "original"  # Should not change
        assert page.project_id == 1  # Should not change

    def test_wikipage_markdown_content_multiline(self) -> None:
        """Test that wiki page supports multiline markdown content."""
        content = """# Main Title

## Section 1

This is paragraph 1.

## Section 2

- Item 1
- Item 2
- Item 3

```python
def hello() -> None:
    print("Hello, World!")
```"""
        page = WikiPage(slug="guide", project_id=1, content=content)
        assert page.content == content
        assert "# Main Title" in page.content
        assert "```python" in page.content

    def test_wikipage_slug_validator_non_string_passthrough(self) -> None:
        """Test that slug validator passes through non-string values."""
        # The validator in mode="before" should pass through non-strings
        # so Pydantic can handle type coercion/validation
        result = WikiPage.validate_slug(123)  # type: ignore[arg-type]
        assert result == 123  # Should return as-is for non-string input
