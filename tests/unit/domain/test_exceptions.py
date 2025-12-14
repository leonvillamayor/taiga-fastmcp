"""Tests for domain exceptions."""

import pytest

from src.domain.exceptions import (
    AuthenticationError,
    ConcurrencyError,
    ConfigurationError,
    DomainException,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ResourceNotFoundError,
    TaigaAPIError,
    TaigaException,
    ValidationError,
)


def test_domain_exception() -> None:
    """Test base DomainException."""
    exc = DomainException("Error message")
    assert str(exc) == "Error message"
    assert isinstance(exc, Exception)


def test_configuration_error() -> None:
    """Test ConfigurationError."""
    exc = ConfigurationError("Config invalid")
    assert str(exc) == "Config invalid"
    assert isinstance(exc, DomainException)


def test_authentication_error() -> None:
    """Test AuthenticationError."""
    exc = AuthenticationError("Invalid credentials")
    assert str(exc) == "Invalid credentials"
    assert isinstance(exc, DomainException)


def test_taiga_api_error() -> None:
    """Test TaigaAPIError without status code and response body."""
    exc = TaigaAPIError("API error")
    assert str(exc) == "API error"
    assert exc.status_code is None
    assert exc.response_body is None
    assert isinstance(exc, DomainException)


def test_taiga_api_error_with_status_code() -> None:
    """Test TaigaAPIError with status code."""
    exc = TaigaAPIError("Not found", status_code=404)
    assert str(exc) == "Not found"
    assert exc.status_code == 404
    assert exc.response_body is None


def test_taiga_api_error_with_response_body() -> None:
    """Test TaigaAPIError with response body."""
    exc = TaigaAPIError("Server error", status_code=500, response_body='{"error": "Internal"}')
    assert str(exc) == "Server error"
    assert exc.status_code == 500
    assert exc.response_body == '{"error": "Internal"}'


def test_validation_error() -> None:
    """Test ValidationError."""
    exc = ValidationError("Invalid data")
    assert str(exc) == "Invalid data"
    assert isinstance(exc, DomainException)


def test_resource_not_found_error() -> None:
    """Test ResourceNotFoundError."""
    exc = ResourceNotFoundError("Resource not found")
    assert str(exc) == "Resource not found"
    assert isinstance(exc, DomainException)


def test_permission_denied_error() -> None:
    """Test PermissionDeniedError."""
    exc = PermissionDeniedError("No permission")
    assert str(exc) == "No permission"
    assert isinstance(exc, DomainException)


def test_rate_limit_error() -> None:
    """Test RateLimitError."""
    exc = RateLimitError("Rate limit exceeded")
    assert str(exc) == "Rate limit exceeded"
    assert isinstance(exc, DomainException)


def test_concurrency_error() -> None:
    """Test ConcurrencyError."""
    exc = ConcurrencyError("Version conflict")
    assert str(exc) == "Version conflict"
    assert isinstance(exc, DomainException)


def test_taiga_exception() -> None:
    """Test base TaigaException."""
    exc = TaigaException("Taiga error")
    assert str(exc) == "Taiga error"
    assert isinstance(exc, DomainException)


def test_not_found_error() -> None:
    """Test NotFoundError."""
    exc = NotFoundError("Not found")
    assert str(exc) == "Not found"
    assert isinstance(exc, TaigaException)
    assert isinstance(exc, DomainException)


def test_exceptions_can_be_raised_and_caught() -> None:
    """Test exceptions can be raised and caught."""
    with pytest.raises(ConfigurationError) as exc_info:
        raise ConfigurationError("Test error")
    assert "Test error" in str(exc_info.value)

    with pytest.raises(DomainException):
        raise AuthenticationError("Auth failed")


def test_exceptions_inheritance_chain() -> None:
    """Test exception inheritance chain."""
    # DomainException is base for all
    assert issubclass(ConfigurationError, DomainException)
    assert issubclass(AuthenticationError, DomainException)
    assert issubclass(TaigaAPIError, DomainException)
    assert issubclass(ValidationError, DomainException)

    # TaigaException extends DomainException
    assert issubclass(TaigaException, DomainException)

    # NotFoundError extends TaigaException
    assert issubclass(NotFoundError, TaigaException)
    assert issubclass(NotFoundError, DomainException)
