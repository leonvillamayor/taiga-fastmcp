"""Tests unitarios para la entidad Issue."""

import pytest
from pydantic import ValidationError

from src.domain.entities.issue import Issue


class TestIssueEntity:
    """Tests para la entidad Issue."""

    def test_create_issue_minimal(self) -> None:
        """Test creating issue with minimal data."""
        issue = Issue(subject="Bug en login", project_id=1)
        assert issue.subject == "Bug en login"
        assert issue.project_id == 1
        assert issue.description == ""
        assert issue.is_closed is False
        assert issue.is_blocked is False
        assert issue.tags == []

    def test_create_issue_full_data(self) -> None:
        """Test creating issue with full data."""
        issue = Issue(
            subject="Critical bug",
            project_id=1,
            description="Detailed description",
            type=1,
            status=2,
            priority=3,
            severity=4,
            milestone_id=5,
            assigned_to_id=6,
            ref=7,
            is_closed=False,
            is_blocked=True,
            blocked_note="Waiting for API",
            tags=["bug", "critical"],
        )
        assert issue.subject == "Critical bug"
        assert issue.description == "Detailed description"
        assert issue.type == 1
        assert issue.status == 2
        assert issue.priority == 3
        assert issue.severity == 4
        assert issue.milestone_id == 5
        assert issue.assigned_to_id == 6
        assert issue.ref == 7
        assert issue.is_blocked is True
        assert issue.blocked_note == "Waiting for API"
        assert set(issue.tags) == {"bug", "critical"}

    def test_issue_subject_validation_empty(self) -> None:
        """Test that empty subject raises error."""
        with pytest.raises(ValidationError):
            Issue(subject="", project_id=1)

    def test_issue_subject_validation_whitespace(self) -> None:
        """Test that whitespace-only subject raises error."""
        with pytest.raises(ValidationError):
            Issue(subject="   ", project_id=1)

    def test_issue_subject_stripped(self) -> None:
        """Test that subject whitespace is stripped."""
        issue = Issue(subject="  Bug fix  ", project_id=1)
        assert issue.subject == "Bug fix"

    def test_issue_tags_normalized(self) -> None:
        """Test that tags are normalized to lowercase."""
        issue = Issue(subject="Test", project_id=1, tags=["BUG", "Critical", "  security  ", "BUG"])
        assert "bug" in issue.tags
        assert "critical" in issue.tags
        assert "security" in issue.tags
        assert len(issue.tags) == 3  # Duplicates removed

    def test_issue_block(self) -> None:
        """Test blocking an issue."""
        issue = Issue(subject="Test", project_id=1)
        assert issue.is_blocked is False

        issue.block("Waiting for dependency")
        assert issue.is_blocked is True
        assert issue.blocked_note == "Waiting for dependency"

    def test_issue_unblock(self) -> None:
        """Test unblocking an issue."""
        issue = Issue(subject="Test", project_id=1, is_blocked=True, blocked_note="Test note")
        issue.unblock()
        assert issue.is_blocked is False
        assert issue.blocked_note == ""

    def test_issue_close(self) -> None:
        """Test closing an issue."""
        issue = Issue(subject="Test", project_id=1)
        assert issue.is_closed is False

        issue.close()
        assert issue.is_closed is True

    def test_issue_reopen(self) -> None:
        """Test reopening a closed issue."""
        issue = Issue(subject="Test", project_id=1, is_closed=True)
        issue.reopen()
        assert issue.is_closed is False

    def test_issue_equality_with_id(self) -> None:
        """Test issue equality based on ID."""
        issue1 = Issue(subject="Test 1", project_id=1)
        issue1.id = 100

        issue2 = Issue(subject="Test 2", project_id=1)
        issue2.id = 100

        issue3 = Issue(subject="Test 3", project_id=1)
        issue3.id = 200

        assert issue1 == issue2  # Same ID
        assert issue1 != issue3  # Different ID

    def test_issue_equality_without_id(self) -> None:
        """Test that issues without ID are not equal."""
        issue1 = Issue(subject="Test 1", project_id=1)
        issue2 = Issue(subject="Test 1", project_id=1)
        assert issue1 != issue2

    def test_issue_hash_with_id(self) -> None:
        """Test issue hash with ID."""
        issue = Issue(subject="Test", project_id=1)
        issue.id = 100
        assert hash(issue) == hash(100)

    def test_issue_hash_without_id(self) -> None:
        """Test issue hash without ID uses object id."""
        issue = Issue(subject="Test", project_id=1)
        # Should not raise error
        hash_value = hash(issue)
        assert isinstance(hash_value, int)

    def test_issue_in_set(self) -> None:
        """Test issues can be added to sets."""
        issue1 = Issue(subject="Test 1", project_id=1)
        issue1.id = 100

        issue2 = Issue(subject="Test 2", project_id=1)
        issue2.id = 200

        issue_set = {issue1, issue2}
        assert len(issue_set) == 2
        assert issue1 in issue_set
        assert issue2 in issue_set

    def test_issue_to_dict(self) -> None:
        """Test converting issue to dictionary."""
        issue = Issue(subject="Test", project_id=1, description="Desc", tags=["bug"])
        issue.id = 100
        issue.ref = 5

        issue_dict = issue.to_dict()
        assert isinstance(issue_dict, dict)
        assert issue_dict["id"] == 100
        assert issue_dict["ref"] == 5
        assert issue_dict["subject"] == "Test"
        assert issue_dict["project_id"] == 1
        assert issue_dict["description"] == "Desc"
        assert "bug" in issue_dict["tags"]

    def test_issue_from_dict(self) -> None:
        """Test creating issue from dictionary."""
        data = {
            "id": 100,
            "ref": 5,
            "version": 1,
            "subject": "Test Issue",
            "project_id": 1,
            "description": "Test description",
            "tags": ["bug", "critical"],
            "is_closed": False,
            "is_blocked": False,
            "blocked_note": "",
        }
        issue = Issue.from_dict(data)
        assert issue.id == 100
        assert issue.ref == 5
        assert issue.version == 1
        assert issue.subject == "Test Issue"
        assert issue.project_id == 1
        assert set(issue.tags) == {"bug", "critical"}

    def test_issue_update_from_dict(self) -> None:
        """Test updating issue from dictionary."""
        issue = Issue(subject="Original", project_id=1)

        update_data = {"subject": "Updated", "description": "New description", "is_closed": True}
        issue.update_from_dict(update_data)

        assert issue.subject == "Updated"
        assert issue.description == "New description"
        assert issue.is_closed is True
        assert issue.project_id == 1  # Should not change
