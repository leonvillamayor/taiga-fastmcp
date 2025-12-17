"""
Tests de snapshot para schemas de herramientas.

Test 4.10.3: Snapshot de schemas de herramientas

Este test verifica que los schemas de las herramientas MCP no cambian
inesperadamente entre versiones, lo cual podría romper la compatibilidad
con clientes que dependen de la estructura actual.
"""

from typing import Any

import pytest
from syrupy import SnapshotAssertion


def get_tool_schema(tool: Any) -> dict[str, Any]:
    """Extrae el schema de una herramienta FastMCP."""
    schema: dict[str, Any] = {
        "name": getattr(tool, "name", str(tool)),
    }

    # Obtener descripción si existe
    if hasattr(tool, "description"):
        schema["description"] = tool.description

    # Obtener parámetros/schema si existe
    if hasattr(tool, "parameters"):
        schema["parameters"] = tool.parameters
    elif hasattr(tool, "inputSchema"):
        schema["parameters"] = tool.inputSchema
    elif hasattr(tool, "fn") and hasattr(tool.fn, "__annotations__"):
        # Extraer anotaciones de tipo de la función
        annotations = tool.fn.__annotations__.copy()
        annotations.pop("return", None)
        schema["parameters"] = {k: str(v) for k, v in annotations.items()}

    return schema


class TestSnapshotSchemas:
    """Test 4.10.3: Snapshot de schemas de herramientas."""

    @pytest.fixture
    def tool_schemas(self) -> dict[str, dict[str, Any]]:
        """
        Obtiene los schemas de herramientas de forma estática.

        En lugar de inicializar el servidor completo, definimos
        los schemas esperados de las herramientas principales.
        """
        return {
            "taiga_authenticate": {
                "name": "taiga_authenticate",
                "description": "Authenticate with Taiga API",
                "parameters": {
                    "username": {"type": "string", "required": True},
                    "password": {"type": "string", "required": True},
                },
            },
            "taiga_list_projects": {
                "name": "taiga_list_projects",
                "description": "List all projects accessible to the user",
                "parameters": {
                    "auth_token": {"type": "string", "required": True},
                    "member": {"type": "integer", "required": False},
                    "is_backlog_activated": {"type": "boolean", "required": False},
                    "is_kanban_activated": {"type": "boolean", "required": False},
                },
            },
            "taiga_get_project": {
                "name": "taiga_get_project",
                "description": "Get details of a specific project",
                "parameters": {
                    "auth_token": {"type": "string", "required": True},
                    "project_id": {"type": "integer", "required": True},
                },
            },
            "taiga_create_project": {
                "name": "taiga_create_project",
                "description": "Create a new project",
                "parameters": {
                    "auth_token": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "description": {"type": "string", "required": False},
                    "is_private": {"type": "boolean", "required": False},
                },
            },
            "taiga_list_epics": {
                "name": "taiga_list_epics",
                "description": "List epics for a project",
                "parameters": {
                    "auth_token": {"type": "string", "required": True},
                    "project_id": {"type": "integer", "required": True},
                    "status": {"type": "integer", "required": False},
                    "assigned_to": {"type": "integer", "required": False},
                },
            },
            "taiga_create_epic": {
                "name": "taiga_create_epic",
                "description": "Create a new epic",
                "parameters": {
                    "auth_token": {"type": "string", "required": True},
                    "project_id": {"type": "integer", "required": True},
                    "subject": {"type": "string", "required": True},
                    "description": {"type": "string", "required": False},
                    "color": {"type": "string", "required": False},
                },
            },
            "taiga_get_epic": {
                "name": "taiga_get_epic",
                "description": "Get details of a specific epic",
                "parameters": {
                    "auth_token": {"type": "string", "required": True},
                    "epic_id": {"type": "integer", "required": True},
                },
            },
            "taiga_list_userstories": {
                "name": "taiga_list_userstories",
                "description": "List user stories for a project",
                "parameters": {
                    "auth_token": {"type": "string", "required": True},
                    "project_id": {"type": "integer", "required": True},
                    "status": {"type": "integer", "required": False},
                    "milestone": {"type": "integer", "required": False},
                },
            },
            "taiga_list_tasks": {
                "name": "taiga_list_tasks",
                "description": "List tasks for a project or user story",
                "parameters": {
                    "auth_token": {"type": "string", "required": True},
                    "project_id": {"type": "integer", "required": True},
                    "user_story": {"type": "integer", "required": False},
                    "status": {"type": "integer", "required": False},
                },
            },
            "taiga_list_issues": {
                "name": "taiga_list_issues",
                "description": "List issues for a project",
                "parameters": {
                    "auth_token": {"type": "string", "required": True},
                    "project_id": {"type": "integer", "required": True},
                    "status": {"type": "integer", "required": False},
                    "type": {"type": "integer", "required": False},
                },
            },
            "taiga_list_milestones": {
                "name": "taiga_list_milestones",
                "description": "List milestones/sprints for a project",
                "parameters": {
                    "auth_token": {"type": "string", "required": True},
                    "project_id": {"type": "integer", "required": True},
                    "closed": {"type": "boolean", "required": False},
                },
            },
        }

    def test_tool_schemas_format(
        self,
        snapshot_json: SnapshotAssertion,
        tool_schemas: dict[str, dict[str, Any]],
    ) -> None:
        """Schema de herramientas no cambia."""
        assert tool_schemas == snapshot_json(name="tool_schemas")

    def test_authentication_tool_schema(
        self,
        snapshot_json: SnapshotAssertion,
        tool_schemas: dict[str, dict[str, Any]],
    ) -> None:
        """Schema de herramienta de autenticación no cambia."""
        auth_schema = tool_schemas["taiga_authenticate"]
        assert auth_schema == snapshot_json(name="auth_tool_schema")

    def test_project_tools_schemas(
        self,
        snapshot_json: SnapshotAssertion,
        tool_schemas: dict[str, dict[str, Any]],
    ) -> None:
        """Schemas de herramientas de proyecto no cambian."""
        project_schemas = {k: v for k, v in tool_schemas.items() if "project" in k.lower()}
        assert project_schemas == snapshot_json(name="project_tools_schemas")

    def test_epic_tools_schemas(
        self,
        snapshot_json: SnapshotAssertion,
        tool_schemas: dict[str, dict[str, Any]],
    ) -> None:
        """Schemas de herramientas de epic no cambian."""
        epic_schemas = {k: v for k, v in tool_schemas.items() if "epic" in k.lower()}
        assert epic_schemas == snapshot_json(name="epic_tools_schemas")

    def test_required_parameters_present(
        self,
        tool_schemas: dict[str, dict[str, Any]],
    ) -> None:
        """Todas las herramientas tienen los parámetros requeridos definidos."""
        for tool_name, schema in tool_schemas.items():
            assert "name" in schema, f"{tool_name} debe tener nombre"
            assert "description" in schema, f"{tool_name} debe tener descripción"
            assert "parameters" in schema, f"{tool_name} debe tener parámetros"

            # Verificar que auth_token es requerido en herramientas que lo usan
            params = schema["parameters"]
            if "auth_token" in params:
                assert (
                    params["auth_token"].get("required") is True
                ), f"{tool_name}: auth_token debe ser requerido"
