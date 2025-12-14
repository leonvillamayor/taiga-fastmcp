"""Tests for AuthToken value object."""

import pytest
from pydantic import ValidationError

from src.domain.value_objects.auth_token import AuthToken


def test_auth_token_valid() -> None:
    """Test creating valid auth token."""
    token = AuthToken(value="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
    assert token.value == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"


def test_auth_token_with_bearer() -> None:
    """Test token with Bearer prefix."""
    token = AuthToken(value="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
    assert token.value.startswith("Bearer ")


def test_auth_token_too_short() -> None:
    """Test token too short raises error."""
    with pytest.raises(ValidationError):
        AuthToken(value="short")


def test_auth_token_empty() -> None:
    """Test empty token raises error."""
    with pytest.raises(ValidationError) as exc_info:
        AuthToken(value="")
    assert "String should have at least 10 characters" in str(exc_info.value)


def test_auth_token_whitespace() -> None:
    """Test whitespace-only token raises error."""
    with pytest.raises(ValidationError) as exc_info:
        AuthToken(value="    ")
    assert "String should have at least 10 characters" in str(exc_info.value)


def test_auth_token_immutable() -> None:
    """Test that token is immutable."""
    token = AuthToken(value="validtoken123")
    with pytest.raises(ValidationError):
        token.value = "newtoken"


def test_auth_token_str() -> None:
    """Test string representation."""
    token = AuthToken(value="validtoken123")
    assert str(token) == "validtoken123"


def test_auth_token_repr() -> None:
    """Test repr hides token value."""
    token = AuthToken(value="validtoken123")
    assert "***" in repr(token)
    assert "validtoken123" not in repr(token) or "***ken123" in repr(token)


def test_auth_token_repr_short() -> None:
    """Test repr for short token."""
    token = AuthToken(value="shorttoken")
    assert "***" in repr(token)


def test_auth_token_is_bearer_format() -> None:
    """Test is_bearer_format method."""
    token_with_bearer = AuthToken(value="Bearer abc123def456")
    assert token_with_bearer.is_bearer_format() is True

    token_without_bearer = AuthToken(value="abc123def456")
    assert token_without_bearer.is_bearer_format() is False


def test_auth_token_get_bearer_token() -> None:
    """Test get_bearer_token method."""
    # Token without Bearer
    token = AuthToken(value="abc123def456")
    assert token.get_bearer_token() == "Bearer abc123def456"

    # Token with Bearer
    token_with_bearer = AuthToken(value="Bearer abc123def456")
    assert token_with_bearer.get_bearer_token() == "Bearer abc123def456"


def test_auth_token_get_raw_token() -> None:
    """Test get_raw_token method."""
    # Token without Bearer
    token = AuthToken(value="abc123def456")
    assert token.get_raw_token() == "abc123def456"

    # Token with Bearer
    token_with_bearer = AuthToken(value="Bearer abc123def456")
    assert token_with_bearer.get_raw_token() == "abc123def456"


def test_auth_token_equality() -> None:
    """Test equality."""
    token1 = AuthToken(value="sametoken123")
    token2 = AuthToken(value="sametoken123")
    assert token1 == token2


def test_auth_token_whitespace_stripping() -> None:
    """Test whitespace is stripped."""
    token = AuthToken(value="  validtoken123  ")
    assert token.value == "validtoken123"
