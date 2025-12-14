"""Tests unitarios para la entidad Task."""

import pytest
from pydantic import ValidationError

from src.domain.entities.task import Task


class TestTaskEntity:
    """Tests para la entidad Task."""

    def test_create_task_minimal(self) -> None:
        """Test creating task with minimal data."""
        task = Task(subject="Implement login", project_id=1)
        assert task.subject == "Implement login"
        assert task.project_id == 1
        assert task.description == ""
        assert task.is_closed is False
        assert task.is_blocked is False
        assert task.is_iocaine is False
        assert task.tags == []

    def test_create_task_full_data(self) -> None:
        """Test creating task with full data."""
        task = Task(
            subject="Implement feature",
            project_id=1,
            description="Detailed description",
            user_story_id=10,
            status=2,
            milestone_id=3,
            assigned_to_id=4,
            ref=5,
            is_closed=False,
            is_blocked=True,
            blocked_note="Waiting for API",
            is_iocaine=True,
            tags=["backend", "api"],
        )
        assert task.subject == "Implement feature"
        assert task.description == "Detailed description"
        assert task.user_story_id == 10
        assert task.status == 2
        assert task.milestone_id == 3
        assert task.assigned_to_id == 4
        assert task.ref == 5
        assert task.is_blocked is True
        assert task.blocked_note == "Waiting for API"
        assert task.is_iocaine is True
        assert set(task.tags) == {"backend", "api"}

    def test_task_subject_validation_empty(self) -> None:
        """Test that empty subject raises error."""
        with pytest.raises(ValidationError):
            Task(subject="", project_id=1)

    def test_task_subject_validation_whitespace(self) -> None:
        """Test that whitespace-only subject raises error."""
        with pytest.raises(ValidationError):
            Task(subject="   ", project_id=1)

    def test_task_subject_stripped(self) -> None:
        """Test that subject whitespace is stripped."""
        task = Task(subject="  Task name  ", project_id=1)
        assert task.subject == "Task name"

    def test_task_tags_normalized(self) -> None:
        """Test that tags are normalized to lowercase."""
        task = Task(
            subject="Test", project_id=1, tags=["BACKEND", "API", "  frontend  ", "BACKEND"]
        )
        assert "backend" in task.tags
        assert "api" in task.tags
        assert "frontend" in task.tags
        assert len(task.tags) == 3  # Duplicates removed

    def test_task_block(self) -> None:
        """Test blocking a task."""
        task = Task(subject="Test", project_id=1)
        assert task.is_blocked is False

        task.block("Waiting for dependencies")
        assert task.is_blocked is True
        assert task.blocked_note == "Waiting for dependencies"

    def test_task_unblock(self) -> None:
        """Test unblocking a task."""
        task = Task(subject="Test", project_id=1, is_blocked=True, blocked_note="Test note")
        task.unblock()
        assert task.is_blocked is False
        assert task.blocked_note == ""

    def test_task_mark_as_iocaine(self) -> None:
        """Test marking task as difficult/risky."""
        task = Task(subject="Test", project_id=1)
        assert task.is_iocaine is False

        task.mark_as_iocaine()
        assert task.is_iocaine is True

    def test_task_unmark_as_iocaine(self) -> None:
        """Test unmarking task as difficult/risky."""
        task = Task(subject="Test", project_id=1, is_iocaine=True)
        task.unmark_as_iocaine()
        assert task.is_iocaine is False

    def test_task_finish(self) -> None:
        """Test finishing a task."""
        task = Task(subject="Test", project_id=1)
        assert task.is_closed is False
        assert task.finished_date is None

        task.finish()
        assert task.is_closed is True
        assert task.finished_date is not None

    def test_task_reopen(self) -> None:
        """Test reopening a finished task."""
        task = Task(subject="Test", project_id=1)
        task.finish()
        assert task.is_closed is True

        task.reopen()
        assert task.is_closed is False
        assert task.finished_date is None

    def test_task_equality_with_id(self) -> None:
        """Test task equality based on ID."""
        task1 = Task(subject="Task 1", project_id=1)
        task1.id = 100

        task2 = Task(subject="Task 2", project_id=1)
        task2.id = 100

        task3 = Task(subject="Task 3", project_id=1)
        task3.id = 200

        assert task1 == task2  # Same ID
        assert task1 != task3  # Different ID

    def test_task_equality_without_id(self) -> None:
        """Test that tasks without ID are not equal."""
        task1 = Task(subject="Task 1", project_id=1)
        task2 = Task(subject="Task 1", project_id=1)
        assert task1 != task2

    def test_task_hash_with_id(self) -> None:
        """Test task hash with ID."""
        task = Task(subject="Test", project_id=1)
        task.id = 100
        assert hash(task) == hash(100)

    def test_task_hash_without_id(self) -> None:
        """Test task hash without ID uses object id."""
        task = Task(subject="Test", project_id=1)
        hash_value = hash(task)
        assert isinstance(hash_value, int)

    def test_task_in_set(self) -> None:
        """Test tasks can be added to sets."""
        task1 = Task(subject="Task 1", project_id=1)
        task1.id = 100

        task2 = Task(subject="Task 2", project_id=1)
        task2.id = 200

        task_set = {task1, task2}
        assert len(task_set) == 2
        assert task1 in task_set
        assert task2 in task_set

    def test_task_to_dict(self) -> None:
        """Test converting task to dictionary."""
        task = Task(subject="Test", project_id=1, description="Desc", tags=["backend"])
        task.id = 100
        task.ref = 5

        task_dict = task.to_dict()
        assert isinstance(task_dict, dict)
        assert task_dict["id"] == 100
        assert task_dict["ref"] == 5
        assert task_dict["subject"] == "Test"
        assert task_dict["project_id"] == 1
        assert "backend" in task_dict["tags"]

    def test_task_from_dict(self) -> None:
        """Test creating task from dictionary."""
        data = {
            "id": 100,
            "version": 1,
            "subject": "Test Task",
            "project_id": 1,
            "description": "Description",
            "tags": ["backend", "api"],
            "is_closed": False,
            "is_blocked": False,
            "is_iocaine": True,
        }
        task = Task.from_dict(data)
        assert task.id == 100
        assert task.subject == "Test Task"
        assert task.project_id == 1
        assert task.is_iocaine is True
        assert set(task.tags) == {"backend", "api"}

    def test_task_update_from_dict(self) -> None:
        """Test updating task from dictionary."""
        task = Task(subject="Original", project_id=1)

        update_data = {"subject": "Updated", "description": "New description", "is_closed": True}
        task.update_from_dict(update_data)

        assert task.subject == "Updated"
        assert task.description == "New description"
        assert task.is_closed is True
        assert task.project_id == 1  # Should not change
