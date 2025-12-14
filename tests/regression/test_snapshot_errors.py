"""
Tests de snapshot para mensajes de error.

Test 4.10.4: Snapshot de mensajes de error

Este test verifica que el formato de los mensajes de error no cambia
inesperadamente entre versiones, lo cual es crítico para que los
clientes puedan manejar errores de forma consistente.
"""

from typing import Any

from syrupy import SnapshotAssertion

from src.application.responses.base import ErrorResponse
from src.domain.exceptions import (
    AuthenticationError,
    NotFoundError,
    PermissionDeniedError,
    ResourceNotFoundError,
    TaigaAPIError,
    ValidationError,
)


class TestSnapshotErrors:
    """Test 4.10.4: Snapshot de mensajes de error."""

    def test_error_response_format(
        self,
        snapshot_json: SnapshotAssertion,
        sample_error_responses: dict[str, dict[str, Any]],
    ) -> None:
        """Formato de respuestas de error no cambia."""
        assert sample_error_responses == snapshot_json(name="error_responses")

    def test_not_found_error_format(
        self,
        snapshot_json: SnapshotAssertion,
    ) -> None:
        """Formato de error NOT_FOUND no cambia."""
        error = ResourceNotFoundError("Project with ID 999999 not found")
        error_dict = {
            "type": error.__class__.__name__,
            "message": str(error),
        }
        assert error_dict == snapshot_json(name="not_found_error")

    def test_not_found_error_alternative_format(
        self,
        snapshot_json: SnapshotAssertion,
    ) -> None:
        """Formato de error NotFoundError no cambia."""
        error = NotFoundError("Epic with ref #5 not found in project")
        error_dict = {
            "type": error.__class__.__name__,
            "message": str(error),
        }
        assert error_dict == snapshot_json(name="not_found_error_alt")

    def test_validation_error_format(
        self,
        snapshot_json: SnapshotAssertion,
    ) -> None:
        """Formato de error de validación no cambia."""
        error = ValidationError("El campo 'subject' es requerido")
        error_dict = {
            "type": error.__class__.__name__,
            "message": str(error),
        }
        assert error_dict == snapshot_json(name="validation_error")

    def test_permission_denied_error_format(
        self,
        snapshot_json: SnapshotAssertion,
    ) -> None:
        """Formato de error de permisos no cambia."""
        error = PermissionDeniedError("No tienes permisos para modificar este proyecto")
        error_dict = {
            "type": error.__class__.__name__,
            "message": str(error),
        }
        assert error_dict == snapshot_json(name="permission_denied_error")

    def test_authentication_error_format(
        self,
        snapshot_json: SnapshotAssertion,
    ) -> None:
        """Formato de error de autenticación no cambia."""
        error = AuthenticationError("Token inválido o expirado")
        error_dict = {
            "type": error.__class__.__name__,
            "message": str(error),
        }
        assert error_dict == snapshot_json(name="authentication_error")

    def test_api_error_format(
        self,
        snapshot_json: SnapshotAssertion,
    ) -> None:
        """Formato de error de API no cambia."""
        error = TaigaAPIError(
            message="Error de comunicación con Taiga API",
            status_code=503,
            response_body='{"detail": "Service Unavailable"}',
        )
        error_dict = {
            "type": error.__class__.__name__,
            "message": str(error),
            "status_code": error.status_code,
            "response_body": error.response_body,
        }
        assert error_dict == snapshot_json(name="api_error")

    def test_error_response_model(
        self,
        snapshot_json: SnapshotAssertion,
    ) -> None:
        """Formato del modelo ErrorResponse no cambia."""
        response = ErrorResponse(
            success=False,
            error="VALIDATION_ERROR",
            message="El campo 'name' es requerido",
            details={"field": "name", "constraint": "required"},
        )
        response_dict = response.model_dump(mode="json")
        assert response_dict == snapshot_json(name="error_response_model")

    def test_error_response_without_details(
        self,
        snapshot_json: SnapshotAssertion,
    ) -> None:
        """Formato del modelo ErrorResponse sin detalles no cambia."""
        response = ErrorResponse(
            success=False,
            error="INTERNAL_ERROR",
            message="Error interno del servidor",
        )
        response_dict = response.model_dump(mode="json")
        assert response_dict == snapshot_json(name="error_response_minimal")

    def test_all_error_codes_format(
        self,
        snapshot_json: SnapshotAssertion,
    ) -> None:
        """Formato de todos los códigos de error definidos."""
        error_codes = {
            "NOT_FOUND": {
                "code": "NOT_FOUND",
                "http_status": 404,
                "description": "El recurso solicitado no existe",
            },
            "VALIDATION_ERROR": {
                "code": "VALIDATION_ERROR",
                "http_status": 400,
                "description": "Los datos proporcionados no son válidos",
            },
            "PERMISSION_DENIED": {
                "code": "PERMISSION_DENIED",
                "http_status": 403,
                "description": "No tienes permisos para esta acción",
            },
            "AUTHENTICATION_ERROR": {
                "code": "AUTHENTICATION_ERROR",
                "http_status": 401,
                "description": "Autenticación requerida o inválida",
            },
            "CONFLICT": {
                "code": "CONFLICT",
                "http_status": 409,
                "description": "Conflicto con el estado actual del recurso",
            },
            "API_ERROR": {
                "code": "API_ERROR",
                "http_status": 502,
                "description": "Error de comunicación con la API de Taiga",
            },
            "INTERNAL_ERROR": {
                "code": "INTERNAL_ERROR",
                "http_status": 500,
                "description": "Error interno del servidor",
            },
        }
        assert error_codes == snapshot_json(name="all_error_codes")
