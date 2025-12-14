"""Tests unitarios para la entidad Milestone."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from src.domain.entities.milestone import Milestone


class TestMilestoneEntity:
    """Tests para la entidad Milestone."""

    def test_create_milestone_minimal(self) -> None:
        """Test creating milestone with minimal data."""
        milestone = Milestone(name="Sprint 1", project_id=1)
        assert milestone.name == "Sprint 1"
        assert milestone.project_id == 1
        assert milestone.is_closed is False
        assert milestone.disponibility == 1.0
        assert milestone.order == 1
        assert milestone.slug is None
        assert milestone.estimated_start is None
        assert milestone.estimated_finish is None

    def test_create_milestone_full_data(self) -> None:
        """Test creating milestone with full data."""
        start = date(2025, 1, 1)
        finish = date(2025, 1, 15)
        created = datetime(2025, 1, 1, 10, 0, 0)

        milestone = Milestone(
            name="Sprint 1",
            slug="sprint-1",
            project_id=1,
            estimated_start=start,
            estimated_finish=finish,
            is_closed=False,
            disponibility=0.8,
            order=2,
            created_date=created,
        )
        assert milestone.name == "Sprint 1"
        assert milestone.slug == "sprint-1"
        assert milestone.project_id == 1
        assert milestone.estimated_start == start
        assert milestone.estimated_finish == finish
        assert milestone.disponibility == 0.8
        assert milestone.order == 2
        assert milestone.created_date == created

    def test_milestone_name_validation_empty(self) -> None:
        """Test that empty name raises error."""
        with pytest.raises(ValidationError):
            Milestone(name="", project_id=1)

    def test_milestone_name_validation_whitespace(self) -> None:
        """Test that whitespace-only name raises error."""
        with pytest.raises(ValidationError):
            Milestone(name="   ", project_id=1)

    def test_milestone_name_stripped(self) -> None:
        """Test that name whitespace is stripped."""
        milestone = Milestone(name="  Sprint 1  ", project_id=1)
        assert milestone.name == "Sprint 1"

    def test_milestone_disponibility_validation(self) -> None:
        """Test that disponibility is between 0 and 1."""
        # Valid values
        milestone1 = Milestone(name="Sprint 1", project_id=1, disponibility=0.0)
        assert milestone1.disponibility == 0.0

        milestone2 = Milestone(name="Sprint 1", project_id=1, disponibility=1.0)
        assert milestone2.disponibility == 1.0

        milestone3 = Milestone(name="Sprint 1", project_id=1, disponibility=0.5)
        assert milestone3.disponibility == 0.5

        # Invalid values
        with pytest.raises(ValidationError):
            Milestone(name="Sprint 1", project_id=1, disponibility=-0.1)

        with pytest.raises(ValidationError):
            Milestone(name="Sprint 1", project_id=1, disponibility=1.1)

    def test_milestone_order_validation(self) -> None:
        """Test that order is at least 1."""
        milestone = Milestone(name="Sprint 1", project_id=1, order=5)
        assert milestone.order == 5

        with pytest.raises(ValidationError):
            Milestone(name="Sprint 1", project_id=1, order=0)

        with pytest.raises(ValidationError):
            Milestone(name="Sprint 1", project_id=1, order=-1)

    def test_milestone_close(self) -> None:
        """Test closing a milestone."""
        milestone = Milestone(name="Sprint 1", project_id=1)
        assert milestone.is_closed is False

        milestone.close()
        assert milestone.is_closed is True

    def test_milestone_reopen(self) -> None:
        """Test reopening a milestone."""
        milestone = Milestone(name="Sprint 1", project_id=1, is_closed=True)
        milestone.reopen()
        assert milestone.is_closed is False

    def test_milestone_set_dates_valid(self) -> None:
        """Test setting valid dates."""
        milestone = Milestone(name="Sprint 1", project_id=1)
        start = date(2025, 1, 1)
        finish = date(2025, 1, 15)

        milestone.set_dates(start, finish)
        assert milestone.estimated_start == start
        assert milestone.estimated_finish == finish

    def test_milestone_set_dates_same_day(self) -> None:
        """Test setting dates for same day (valid)."""
        milestone = Milestone(name="Sprint 1", project_id=1)
        same_date = date(2025, 1, 1)

        milestone.set_dates(same_date, same_date)
        assert milestone.estimated_start == same_date
        assert milestone.estimated_finish == same_date

    def test_milestone_set_dates_invalid_order(self) -> None:
        """Test that finish before start raises error."""
        milestone = Milestone(name="Sprint 1", project_id=1)
        start = date(2025, 1, 15)
        finish = date(2025, 1, 1)

        with pytest.raises(ValueError, match="posterior a la de inicio"):
            milestone.set_dates(start, finish)

    def test_milestone_equality_with_id(self) -> None:
        """Test milestone equality based on ID."""
        milestone1 = Milestone(name="Sprint 1", project_id=1)
        milestone1.id = 100

        milestone2 = Milestone(name="Sprint 2", project_id=1)
        milestone2.id = 100

        milestone3 = Milestone(name="Sprint 3", project_id=1)
        milestone3.id = 200

        assert milestone1 == milestone2  # Same ID
        assert milestone1 != milestone3  # Different ID

    def test_milestone_equality_without_id(self) -> None:
        """Test that milestones without ID are not equal."""
        milestone1 = Milestone(name="Sprint 1", project_id=1)
        milestone2 = Milestone(name="Sprint 1", project_id=1)
        assert milestone1 != milestone2

    def test_milestone_hash_with_id(self) -> None:
        """Test milestone hash with ID."""
        milestone = Milestone(name="Sprint 1", project_id=1)
        milestone.id = 100
        assert hash(milestone) == hash(100)

    def test_milestone_hash_without_id(self) -> None:
        """Test milestone hash without ID uses object id."""
        milestone = Milestone(name="Sprint 1", project_id=1)
        hash_value = hash(milestone)
        assert isinstance(hash_value, int)

    def test_milestone_in_set(self) -> None:
        """Test milestones can be added to sets."""
        milestone1 = Milestone(name="Sprint 1", project_id=1)
        milestone1.id = 100

        milestone2 = Milestone(name="Sprint 2", project_id=1)
        milestone2.id = 200

        milestone_set = {milestone1, milestone2}
        assert len(milestone_set) == 2
        assert milestone1 in milestone_set
        assert milestone2 in milestone_set

    def test_milestone_to_dict(self) -> None:
        """Test converting milestone to dictionary."""
        start = date(2025, 1, 1)
        finish = date(2025, 1, 15)
        milestone = Milestone(
            name="Sprint 1",
            slug="sprint-1",
            project_id=1,
            estimated_start=start,
            estimated_finish=finish,
            disponibility=0.8,
        )
        milestone.id = 100

        milestone_dict = milestone.to_dict()
        assert isinstance(milestone_dict, dict)
        assert milestone_dict["id"] == 100
        assert milestone_dict["name"] == "Sprint 1"
        assert milestone_dict["slug"] == "sprint-1"
        assert milestone_dict["project_id"] == 1
        assert milestone_dict["disponibility"] == 0.8

    def test_milestone_from_dict(self) -> None:
        """Test creating milestone from dictionary."""
        data = {
            "id": 100,
            "version": 1,
            "name": "Sprint 1",
            "slug": "sprint-1",
            "project_id": 1,
            "estimated_start": "2025-01-01",
            "estimated_finish": "2025-01-15",
            "is_closed": False,
            "disponibility": 0.8,
            "order": 2,
        }
        milestone = Milestone.from_dict(data)
        assert milestone.id == 100
        assert milestone.version == 1
        assert milestone.name == "Sprint 1"
        assert milestone.slug == "sprint-1"
        assert milestone.project_id == 1
        assert milestone.disponibility == 0.8
        assert milestone.order == 2

    def test_milestone_update_from_dict(self) -> None:
        """Test updating milestone from dictionary."""
        milestone = Milestone(name="Sprint 1", project_id=1)

        update_data = {"name": "Sprint 1 Updated", "disponibility": 0.6, "is_closed": True}
        milestone.update_from_dict(update_data)

        assert milestone.name == "Sprint 1 Updated"
        assert milestone.disponibility == 0.6
        assert milestone.is_closed is True
        assert milestone.project_id == 1  # Should not change
