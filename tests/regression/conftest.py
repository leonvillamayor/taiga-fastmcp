"""
Configuración y fixtures para tests de regresión y snapshot.

Este módulo proporciona fixtures específicas para snapshot testing
usando syrupy con extensión JSON.
"""

from typing import Any

import pytest
from syrupy import SnapshotAssertion
from syrupy.extensions.json import JSONSnapshotExtension


@pytest.fixture
def snapshot_json(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Fixture para snapshot testing con formato JSON."""
    return snapshot.use_extension(JSONSnapshotExtension)


@pytest.fixture
def sample_project() -> dict[str, Any]:
    """Proyecto de ejemplo para tests de snapshot."""
    return {
        "id": 123456,
        "name": "Test Project",
        "slug": "test-project",
        "description": "Proyecto de prueba para snapshot testing",
        "is_private": False,
        "is_backlog_activated": True,
        "is_kanban_activated": True,
        "is_wiki_activated": True,
        "is_issues_activated": True,
        "created_date": "2025-01-15T10:00:00Z",
        "modified_date": "2025-01-15T12:00:00Z",
        "owner": {
            "id": 888691,
            "username": "test_user",
            "full_name": "Test User",
        },
        "members": [888691, 888692],
        "tags": ["test", "snapshot"],
        "total_story_points": 100.0,
        "total_milestones": 3,
    }


@pytest.fixture
def sample_epic() -> dict[str, Any]:
    """Epic de ejemplo para tests de snapshot."""
    return {
        "id": 456789,
        "ref": 5,
        "version": 1,
        "subject": "Epic de Prueba",
        "description": "Descripción de la epic de prueba para snapshot testing",
        "status": 1,
        "status_extra_info": {
            "name": "New",
            "color": "#999999",
            "is_closed": False,
        },
        "color": "#A5694F",
        "project": 123456,
        "project_extra_info": {
            "id": 123456,
            "name": "Test Project",
            "slug": "test-project",
        },
        "assigned_to": 888691,
        "assigned_to_extra_info": {
            "id": 888691,
            "username": "test_user",
            "full_name": "Test User",
        },
        "owner": 888691,
        "tags": ["epic", "test"],
        "client_requirement": True,
        "team_requirement": False,
        "created_date": "2025-01-10T08:00:00Z",
        "modified_date": "2025-01-15T12:00:00Z",
        "user_stories_counts": {
            "total": 5,
            "progress": 60.0,
        },
    }


@pytest.fixture
def sample_error_responses() -> dict[str, dict[str, Any]]:
    """Respuestas de error de ejemplo para tests de snapshot."""
    return {
        "not_found": {
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "Recurso no encontrado",
                "details": {"resource_type": "project", "resource_id": 999999},
            },
        },
        "validation_error": {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Error de validación",
                "details": {
                    "field": "subject",
                    "error": "Este campo es requerido",
                },
            },
        },
        "permission_denied": {
            "success": False,
            "error": {
                "code": "PERMISSION_DENIED",
                "message": "No tienes permisos para realizar esta acción",
                "details": {"required_permission": "modify_project"},
            },
        },
        "conflict": {
            "success": False,
            "error": {
                "code": "CONFLICT",
                "message": "Conflicto de versión",
                "details": {
                    "current_version": 2,
                    "provided_version": 1,
                },
            },
        },
        "api_error": {
            "success": False,
            "error": {
                "code": "API_ERROR",
                "message": "Error de comunicación con la API de Taiga",
                "details": {"status_code": 503, "reason": "Service Unavailable"},
            },
        },
    }


@pytest.fixture
def normalize_timestamps() -> Any:
    """Helper para normalizar timestamps en respuestas antes de snapshot."""

    def _normalize(data: dict[str, Any]) -> dict[str, Any]:
        """Normaliza campos de fecha para comparación estable."""
        normalized = data.copy()
        timestamp_fields = [
            "created_date",
            "modified_date",
            "created_at",
            "updated_at",
            "timestamp",
        ]
        for field in timestamp_fields:
            if field in normalized:
                normalized[field] = "NORMALIZED_TIMESTAMP"
        return normalized

    return _normalize
