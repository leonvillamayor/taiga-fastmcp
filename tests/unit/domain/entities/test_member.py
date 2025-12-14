"""Tests unitarios para la entidad Member."""

import pytest
from pydantic import ValidationError

from src.domain.entities.member import Member
from src.domain.value_objects.email import Email


class TestMemberEntity:
    """Tests para la entidad Member."""

    def test_create_member_minimal(self) -> None:
        """Test creating member with minimal data."""
        member = Member(project_id=1, user_id=100, username="jdoe")
        assert member.project_id == 1
        assert member.user_id == 100
        assert member.username == "jdoe"
        assert member.full_name == ""
        assert member.is_admin is False
        assert member.role_id is None

    def test_create_member_full_data(self) -> None:
        """Test creating member with full data."""
        email = Email(value="john@example.com")
        member = Member(
            project_id=1,
            user_id=100,
            username="jdoe",
            full_name="John Doe",
            email=email,
            role_id=5,
            is_admin=True,
        )
        assert member.project_id == 1
        assert member.user_id == 100
        assert member.username == "jdoe"
        assert member.full_name == "John Doe"
        assert member.email == email
        assert member.role_id == 5
        assert member.is_admin is True

    def test_member_username_validation_empty(self) -> None:
        """Test that empty username raises error."""
        with pytest.raises(ValidationError):
            Member(project_id=1, user_id=100, username="")

    def test_member_username_validation_whitespace(self) -> None:
        """Test that whitespace-only username raises error."""
        with pytest.raises(ValidationError):
            Member(project_id=1, user_id=100, username="   ")

    def test_member_username_stripped(self) -> None:
        """Test that username whitespace is stripped."""
        member = Member(project_id=1, user_id=100, username="  jdoe  ")
        assert member.username == "jdoe"

    def test_member_make_admin(self) -> None:
        """Test promoting member to admin."""
        member = Member(project_id=1, user_id=100, username="jdoe")
        assert member.is_admin is False

        member.make_admin()
        assert member.is_admin is True

    def test_member_remove_admin(self) -> None:
        """Test removing admin privileges."""
        member = Member(project_id=1, user_id=100, username="jdoe", is_admin=True)
        member.remove_admin()
        assert member.is_admin is False

    def test_member_change_role(self) -> None:
        """Test changing member role."""
        member = Member(project_id=1, user_id=100, username="jdoe")
        member.change_role(10)
        assert member.role_id == 10

    def test_member_change_role_invalid(self) -> None:
        """Test that invalid role ID raises error."""
        member = Member(project_id=1, user_id=100, username="jdoe")
        with pytest.raises(ValueError, match="ID de rol inválido"):
            member.change_role(0)

        with pytest.raises(ValueError, match="ID de rol inválido"):
            member.change_role(-1)

    def test_member_equality_with_id(self) -> None:
        """Test member equality based on ID."""
        member1 = Member(project_id=1, user_id=100, username="user1")
        member1.id = 1000

        member2 = Member(project_id=1, user_id=200, username="user2")
        member2.id = 1000

        member3 = Member(project_id=1, user_id=300, username="user3")
        member3.id = 2000

        assert member1 == member2  # Same ID
        assert member1 != member3  # Different ID

    def test_member_equality_without_id(self) -> None:
        """Test that members without ID are not equal."""
        member1 = Member(project_id=1, user_id=100, username="jdoe")
        member2 = Member(project_id=1, user_id=100, username="jdoe")
        assert member1 != member2

    def test_member_hash_with_id(self) -> None:
        """Test member hash with ID."""
        member = Member(project_id=1, user_id=100, username="jdoe")
        member.id = 1000
        assert hash(member) == hash(1000)

    def test_member_hash_without_id(self) -> None:
        """Test member hash without ID uses object id."""
        member = Member(project_id=1, user_id=100, username="jdoe")
        hash_value = hash(member)
        assert isinstance(hash_value, int)

    def test_member_in_set(self) -> None:
        """Test members can be added to sets."""
        member1 = Member(project_id=1, user_id=100, username="user1")
        member1.id = 1000

        member2 = Member(project_id=1, user_id=200, username="user2")
        member2.id = 2000

        member_set = {member1, member2}
        assert len(member_set) == 2
        assert member1 in member_set
        assert member2 in member_set

    def test_member_to_dict(self) -> None:
        """Test converting member to dictionary."""
        email = Email(value="john@example.com")
        member = Member(
            project_id=1,
            user_id=100,
            username="jdoe",
            full_name="John Doe",
            email=email,
            is_admin=True,
        )
        member.id = 1000

        member_dict = member.to_dict()
        assert isinstance(member_dict, dict)
        assert member_dict["id"] == 1000
        assert member_dict["project_id"] == 1
        assert member_dict["user_id"] == 100
        assert member_dict["username"] == "jdoe"
        assert member_dict["full_name"] == "John Doe"
        assert member_dict["is_admin"] is True

    def test_member_from_dict(self) -> None:
        """Test creating member from dictionary."""
        data = {
            "id": 1000,
            "version": 1,
            "project_id": 1,
            "user_id": 100,
            "username": "jdoe",
            "full_name": "John Doe",
            "email": {"value": "john@example.com"},
            "role_id": 5,
            "is_admin": True,
        }
        member = Member.from_dict(data)
        assert member.id == 1000
        assert member.version == 1
        assert member.project_id == 1
        assert member.user_id == 100
        assert member.username == "jdoe"
        assert member.full_name == "John Doe"
        assert member.role_id == 5
        assert member.is_admin is True

    def test_member_update_from_dict(self) -> None:
        """Test updating member from dictionary."""
        member = Member(project_id=1, user_id=100, username="jdoe")

        update_data = {"full_name": "John Doe Updated", "role_id": 10, "is_admin": True}
        member.update_from_dict(update_data)

        assert member.full_name == "John Doe Updated"
        assert member.role_id == 10
        assert member.is_admin is True
        assert member.project_id == 1  # Should not change
        assert member.username == "jdoe"  # Should not change

    def test_member_email_none_conversion(self) -> None:
        """Test that None email is handled correctly (covers convert_email line 54)."""
        member = Member(project_id=1, user_id=100, username="jdoe", email=None)
        assert member.email is None

    def test_member_email_string_conversion(self) -> None:
        """Test that string email is converted to Email object (covers convert_email line 58)."""
        member = Member(project_id=1, user_id=100, username="jdoe", email="test@example.com")
        assert isinstance(member.email, Email)
        assert member.email.value == "test@example.com"

    def test_member_email_unknown_type_returns_none(self) -> None:
        """Test that unknown email type returns None (covers convert_email line 59)."""
        # Pass an integer which should return None
        member = Member(project_id=1, user_id=100, username="jdoe", email=123)  # type: ignore[arg-type]
        assert member.email is None

    def test_member_equality_not_member(self) -> None:
        """Test equality with non-Member object returns NotImplemented."""
        member = Member(project_id=1, user_id=100, username="jdoe")
        assert member != "not a member"
        assert member != 123
        assert member != None  # noqa: E711
