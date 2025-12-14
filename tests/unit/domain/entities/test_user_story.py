"""Tests unitarios para la entidad UserStory."""

import pytest
from pydantic import ValidationError

from src.domain.entities.user_story import UserStory


class TestUserStoryEntity:
    """Tests para la entidad UserStory."""

    def test_create_userstory_minimal(self) -> None:
        """Test creating user story with minimal data."""
        story = UserStory(subject="As a user, I want to login", project_id=1)
        assert story.subject == "As a user, I want to login"
        assert story.project_id == 1
        assert story.description == ""
        assert story.is_closed is False
        assert story.is_blocked is False
        assert story.client_requirement is False
        assert story.team_requirement is False
        assert story.tags == []
        assert story.points == {}

    def test_create_userstory_full_data(self) -> None:
        """Test creating user story with full data."""
        story = UserStory(
            subject="User authentication",
            project_id=1,
            description="Detailed description",
            status=2,
            milestone_id=3,
            assigned_to_id=4,
            ref=5,
            is_closed=False,
            is_blocked=True,
            blocked_note="Waiting for design",
            client_requirement=True,
            team_requirement=False,
            tags=["auth", "security"],
            points={"dev": 5.0, "qa": 2.0},
        )
        assert story.subject == "User authentication"
        assert story.description == "Detailed description"
        assert story.status == 2
        assert story.milestone_id == 3
        assert story.assigned_to_id == 4
        assert story.ref == 5
        assert story.is_blocked is True
        assert story.blocked_note == "Waiting for design"
        assert story.client_requirement is True
        assert story.team_requirement is False
        assert set(story.tags) == {"auth", "security"}
        assert story.points == {"dev": 5.0, "qa": 2.0}

    def test_userstory_subject_validation_empty(self) -> None:
        """Test that empty subject raises error."""
        with pytest.raises(ValidationError):
            UserStory(subject="", project_id=1)

    def test_userstory_subject_validation_whitespace(self) -> None:
        """Test that whitespace-only subject raises error."""
        with pytest.raises(ValidationError):
            UserStory(subject="   ", project_id=1)

    def test_userstory_subject_stripped(self) -> None:
        """Test that subject whitespace is stripped."""
        story = UserStory(subject="  User story  ", project_id=1)
        assert story.subject == "User story"

    def test_userstory_tags_normalized(self) -> None:
        """Test that tags are normalized to lowercase."""
        story = UserStory(
            subject="Test", project_id=1, tags=["AUTH", "Security", "  frontend  ", "AUTH"]
        )
        assert "auth" in story.tags
        assert "security" in story.tags
        assert "frontend" in story.tags
        assert len(story.tags) == 3  # Duplicates removed

    def test_userstory_block(self) -> None:
        """Test blocking a user story."""
        story = UserStory(subject="Test", project_id=1)
        assert story.is_blocked is False

        story.block("Waiting for API")
        assert story.is_blocked is True
        assert story.blocked_note == "Waiting for API"

    def test_userstory_unblock(self) -> None:
        """Test unblocking a user story."""
        story = UserStory(subject="Test", project_id=1, is_blocked=True, blocked_note="Test note")
        story.unblock()
        assert story.is_blocked is False
        assert story.blocked_note == ""

    def test_userstory_assign_to_valid(self) -> None:
        """Test assigning user story to valid user."""
        story = UserStory(subject="Test", project_id=1)
        story.assign_to(100)
        assert story.assigned_to_id == 100

    def test_userstory_assign_to_invalid(self) -> None:
        """Test that invalid user ID raises error."""
        story = UserStory(subject="Test", project_id=1)

        with pytest.raises(ValueError, match="ID de usuario inválido"):
            story.assign_to(0)

        with pytest.raises(ValueError, match="ID de usuario inválido"):
            story.assign_to(-1)

    def test_userstory_unassign(self) -> None:
        """Test unassigning user story."""
        story = UserStory(subject="Test", project_id=1, assigned_to_id=100)
        story.unassign()
        assert story.assigned_to_id is None

    def test_userstory_equality_with_id(self) -> None:
        """Test user story equality based on ID."""
        story1 = UserStory(subject="Story 1", project_id=1)
        story1.id = 100

        story2 = UserStory(subject="Story 2", project_id=1)
        story2.id = 100

        story3 = UserStory(subject="Story 3", project_id=1)
        story3.id = 200

        assert story1 == story2  # Same ID
        assert story1 != story3  # Different ID

    def test_userstory_equality_without_id(self) -> None:
        """Test that user stories without ID are not equal."""
        story1 = UserStory(subject="Story 1", project_id=1)
        story2 = UserStory(subject="Story 1", project_id=1)
        assert story1 != story2

    def test_userstory_hash_with_id(self) -> None:
        """Test user story hash with ID."""
        story = UserStory(subject="Test", project_id=1)
        story.id = 100
        assert hash(story) == hash(100)

    def test_userstory_hash_without_id(self) -> None:
        """Test user story hash without ID uses object id."""
        story = UserStory(subject="Test", project_id=1)
        hash_value = hash(story)
        assert isinstance(hash_value, int)

    def test_userstory_in_set(self) -> None:
        """Test user stories can be added to sets."""
        story1 = UserStory(subject="Story 1", project_id=1)
        story1.id = 100

        story2 = UserStory(subject="Story 2", project_id=1)
        story2.id = 200

        story_set = {story1, story2}
        assert len(story_set) == 2
        assert story1 in story_set
        assert story2 in story_set

    def test_userstory_to_dict(self) -> None:
        """Test converting user story to dictionary."""
        story = UserStory(
            subject="Test", project_id=1, description="Desc", tags=["auth"], points={"dev": 5.0}
        )
        story.id = 100
        story.ref = 5

        story_dict = story.to_dict()
        assert isinstance(story_dict, dict)
        assert story_dict["id"] == 100
        assert story_dict["ref"] == 5
        assert story_dict["subject"] == "Test"
        assert story_dict["project_id"] == 1
        assert "auth" in story_dict["tags"]
        assert story_dict["points"] == {"dev": 5.0}

    def test_userstory_from_dict(self) -> None:
        """Test creating user story from dictionary."""
        data = {
            "id": 100,
            "version": 1,
            "subject": "Test Story",
            "project_id": 1,
            "description": "Description",
            "tags": ["auth", "security"],
            "is_closed": False,
            "is_blocked": False,
            "client_requirement": True,
            "points": {"dev": 5.0, "qa": 2.0},
        }
        story = UserStory.from_dict(data)
        assert story.id == 100
        assert story.subject == "Test Story"
        assert story.project_id == 1
        assert story.client_requirement is True
        assert set(story.tags) == {"auth", "security"}
        assert story.points == {"dev": 5.0, "qa": 2.0}

    def test_userstory_update_from_dict(self) -> None:
        """Test updating user story from dictionary."""
        story = UserStory(subject="Original", project_id=1)

        update_data = {
            "subject": "Updated",
            "description": "New description",
            "is_closed": True,
            "client_requirement": True,
        }
        story.update_from_dict(update_data)

        assert story.subject == "Updated"
        assert story.description == "New description"
        assert story.is_closed is True
        assert story.client_requirement is True
        assert story.project_id == 1  # Should not change
