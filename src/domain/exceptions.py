"""
Domain exceptions for Taiga MCP Server.
"""


class DomainException(Exception):
    """Base exception for domain layer errors."""


class ConfigurationError(DomainException):
    """Error en la configuración del servidor."""


class AuthenticationError(DomainException):
    """Error de autenticación con Taiga."""


class TaigaAPIError(DomainException):
    """Error al comunicarse con la API de Taiga."""

    def __init__(
        self, message: str, status_code: int | None = None, response_body: str | None = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class ValidationError(DomainException):
    """Error de validación de datos."""


class ResourceNotFoundError(DomainException):
    """Recurso no encontrado en Taiga."""


class PermissionDeniedError(DomainException):
    """Sin permisos para realizar la operación."""


class RateLimitError(DomainException):
    """Rate limit exceeded en la API de Taiga."""


class ConcurrencyError(DomainException):
    """Error de concurrencia en actualizaciones (version conflict)."""


class TaigaException(DomainException):
    """Base exception for Taiga-specific errors."""


# Alias for compatibility
TaigaError = TaigaException


class NotFoundError(TaigaException):
    """Se lanzará cuando un recurso no sea encontrado."""
