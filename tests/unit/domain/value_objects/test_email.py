"""Tests for Email value object."""

import pytest
from pydantic import ValidationError

from src.domain.value_objects.email import Email


def test_email_valid() -> None:
    """Test creating valid email."""
    email = Email(value="user@example.com")
    assert email.value == "user@example.com"


def test_email_lowercase() -> None:
    """Test email is converted to lowercase."""
    email = Email(value="USER@EXAMPLE.COM")
    assert email.value == "user@example.com"


def test_email_with_subdomain() -> None:
    """Test email with subdomain."""
    email = Email(value="user@mail.example.com")
    assert email.value == "user@mail.example.com"


def test_email_with_plus() -> None:
    """Test email with plus sign."""
    email = Email(value="user+tag@example.com")
    assert email.value == "user+tag@example.com"


def test_email_invalid_format() -> None:
    """Test invalid email format."""
    with pytest.raises(ValidationError) as exc_info:
        Email(value="invalid-email")
    assert "inválido" in str(exc_info.value)


def test_email_missing_at() -> None:
    """Test email without @ symbol."""
    with pytest.raises(ValidationError):
        Email(value="userexample.com")


def test_email_missing_domain() -> None:
    """Test email without domain."""
    with pytest.raises(ValidationError):
        Email(value="user@")


def test_email_too_short() -> None:
    """Test email too short."""
    with pytest.raises(ValidationError):
        Email(value="a@")


def test_email_immutable() -> None:
    """Test that email is immutable."""
    email = Email(value="user@example.com")
    with pytest.raises(ValidationError):
        email.value = "other@example.com"


def test_email_str() -> None:
    """Test string representation."""
    email = Email(value="user@example.com")
    assert str(email) == "user@example.com"


def test_email_repr() -> None:
    """Test repr representation."""
    email = Email(value="user@example.com")
    assert repr(email) == "Email('user@example.com')"


def test_email_domain_property() -> None:
    """Test domain property."""
    email = Email(value="user@example.com")
    assert email.domain == "example.com"


def test_email_local_part_property() -> None:
    """Test local_part property."""
    email = Email(value="user@example.com")
    assert email.local_part == "user"


def test_email_equality() -> None:
    """Test equality."""
    email1 = Email(value="user@example.com")
    email2 = Email(value="user@example.com")
    assert email1 == email2


def test_email_whitespace_stripping() -> None:
    """Test whitespace is stripped."""
    email = Email(value="  user@example.com  ")
    assert email.value == "user@example.com"
