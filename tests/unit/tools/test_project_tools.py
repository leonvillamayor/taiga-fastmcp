"""
Tests unitarios para las herramientas de proyectos del servidor MCP.
Verifica las herramientas de proyectos según RF-011 y RF-030.
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.application.tools.project_tools import ProjectTools


class TestListProjectsTool:
    """Tests para la herramienta list_projects - RF-011, RF-030."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_list_projects_tool_is_registered(self) -> None:
        """
        RF-011: Las herramientas DEBEN cubrir gestión de proyectos de Taiga.
        RF-030: TODAS las funcionalidades de Taiga DEBEN estar expuestas.
        Verifica que la herramienta list_projects está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)

        # Act
        project_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_list_projects" in tool_names

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_list_projects_returns_all_projects(self, mock_taiga_api) -> None:
        """
        Verifica que list_projects retorna todos los proyectos del usuario.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        # Mock de respuesta exitosa (con parámetros de paginación)
        mock_taiga_api.get("https://api.taiga.io/api/v1/projects?page=1&page_size=100").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "name": "Project Alpha",
                        "slug": "project-alpha",
                        "description": "First project",
                        "is_private": False,
                        "owner": {"id": 12345, "username": "testuser"},
                    },
                    {
                        "id": 2,
                        "name": "Project Beta",
                        "slug": "project-beta",
                        "description": "Second project",
                        "is_private": True,
                        "owner": {"id": 12345, "username": "testuser"},
                    },
                ],
            )
        )

        # Act
        result = await project_tools.list_projects(auth_token="valid_token")

        # Assert
        assert result is not None
        assert len(result) == 2
        assert result[0]["name"] == "Project Alpha"
        assert result[1]["name"] == "Project Beta"
        assert result[0]["is_private"] is False
        assert result[1]["is_private"] is True

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_list_projects_with_filters(self, mock_taiga_api) -> None:
        """
        Verifica que list_projects puede filtrar proyectos.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        # Mock de respuesta con filtros (con parámetros de paginación)
        mock_taiga_api.get(
            "https://api.taiga.io/api/v1/projects?member=12345&is_backlog_activated=true&page=1&page_size=100"
        ).mock(
            return_value=httpx.Response(
                200, json=[{"id": 3, "name": "Filtered Project", "slug": "filtered"}]
            )
        )

        # Act
        result = await project_tools.list_projects(
            auth_token="valid_token", member_id=12345, is_backlog_activated=True
        )

        # Assert
        assert len(result) == 1
        assert result[0]["name"] == "Filtered Project"

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_list_projects_handles_empty_results(self, mock_taiga_api) -> None:
        """
        Verifica que list_projects maneja lista vacía correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/projects?page=1&page_size=100").mock(
            return_value=httpx.Response(200, json=[])
        )

        # Act
        result = await project_tools.list_projects(auth_token="valid_token")

        # Assert
        assert result == []


class TestCreateProjectTool:
    """Tests para la herramienta create_project - RF-011."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_tool_is_registered(self) -> None:
        """
        RF-011: Las herramientas DEBEN cubrir gestión de proyectos.
        Verifica que la herramienta create_project está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)

        # Act
        project_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_create_project" in tool_names

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_with_minimal_data(self, mock_taiga_api) -> None:
        """
        Verifica que create_project funciona con datos mínimos.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        # Mock de respuesta exitosa
        mock_taiga_api.post("https://api.taiga.io/api/v1/projects").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": 100,
                    "name": "New Project",
                    "slug": "new-project",
                    "description": "Project description",
                    "is_private": False,
                    "is_backlog_activated": True,
                    "is_kanban_activated": True,
                    "is_wiki_activated": True,
                    "is_issues_activated": True,
                },
            )
        )

        # Act
        result = await project_tools.create_project(
            auth_token="valid_token", name="New Project", description="Project description"
        )

        # Assert
        assert result is not None
        assert result["id"] == 100
        assert result["name"] == "New Project"
        assert result["slug"] == "new-project"

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_with_all_options(self, mock_taiga_api) -> None:
        """
        Verifica que create_project funciona con todas las opciones.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/projects").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": 101,
                    "name": "Full Project",
                    "slug": "full-project",
                    "description": "Complete project",
                    "is_private": True,
                    "is_backlog_activated": False,
                    "is_kanban_activated": True,
                    "is_wiki_activated": False,
                    "is_issues_activated": True,
                    "videoconferences": "jitsi",
                    "total_story_points": 100,
                    "tags": ["important", "phase1"],
                },
            )
        )

        # Act
        result = await project_tools.create_project(
            auth_token="valid_token",
            name="Full Project",
            description="Complete project",
            is_private=True,
            is_backlog_activated=False,
            is_kanban_activated=True,
            is_wiki_activated=False,
            is_issues_activated=True,
            videoconferences="jitsi",
            tags=["important", "phase1"],
        )

        # Assert
        assert result["is_private"] is True
        assert result["is_backlog_activated"] is False
        assert result["videoconferences"] == "jitsi"
        assert "important" in result["tags"]

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_handles_duplicate_name(self, mock_taiga_api) -> None:
        """
        RF-041: El servidor DEBE manejar errores de autenticación.
        Verifica manejo de nombres duplicados.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/projects").mock(
            return_value=httpx.Response(
                400, json={"name": ["A project with this name already exists"]}
            )
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Failed to create project"):
            await project_tools.create_project(
                auth_token="valid_token", name="Existing Project", description="Duplicate"
            )


class TestGetProjectTool:
    """Tests para la herramienta get_project - RF-011."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_by_id(self, mock_taiga_api) -> None:
        """
        Verifica que get_project obtiene proyecto por ID.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/projects/123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 123,
                    "name": "Test Project",
                    "slug": "test-project",
                    "description": "A test project",
                    "members": [
                        {"id": 1, "username": "user1", "role": "Product Owner"},
                        {"id": 2, "username": "user2", "role": "Developer"},
                    ],
                    "milestones": [{"id": 10, "name": "Sprint 1"}, {"id": 11, "name": "Sprint 2"}],
                },
            )
        )

        # Act
        result = await project_tools.get_project(auth_token="valid_token", project_id=123)

        # Assert
        assert result["id"] == 123
        assert result["name"] == "Test Project"
        assert len(result["members"]) == 2
        assert len(result["milestones"]) == 2

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_by_slug(self, mock_taiga_api) -> None:
        """
        Verifica que get_project obtiene proyecto por slug.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/projects/by_slug?slug=test-slug").mock(
            return_value=httpx.Response(
                200, json={"id": 456, "name": "Project by Slug", "slug": "test-slug"}
            )
        )

        # Act
        result = await project_tools.get_project(auth_token="valid_token", slug="test-slug")

        # Assert
        assert result["id"] == 456
        assert result["slug"] == "test-slug"

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_not_found(self, mock_taiga_api) -> None:
        """
        Verifica manejo de proyecto no encontrado.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/projects/999").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Project not found"):
            await project_tools.get_project(auth_token="valid_token", project_id=999)


class TestUpdateProjectTool:
    """Tests para la herramienta update_project - RF-011."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_update_project_tool_is_registered(self) -> None:
        """
        Verifica que la herramienta update_project está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)

        # Act
        project_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_update_project" in tool_names

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_update_project_name_and_description(self, mock_taiga_api) -> None:
        """
        Verifica que update_project actualiza nombre y descripción.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.patch("https://api.taiga.io/api/v1/projects/123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 123,
                    "name": "Updated Name",
                    "description": "Updated description",
                    "version": 2,
                },
            )
        )

        # Act
        result = await project_tools.update_project(
            auth_token="valid_token",
            project_id=123,
            name="Updated Name",
            description="Updated description",
        )

        # Assert
        assert result["name"] == "Updated Name"
        assert result["description"] == "Updated description"
        assert result["version"] == 2

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_update_project_settings(self, mock_taiga_api) -> None:
        """
        Verifica que update_project actualiza configuraciones del proyecto.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.patch("https://api.taiga.io/api/v1/projects/123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 123,
                    "is_private": True,
                    "is_kanban_activated": False,
                    "is_issues_activated": True,
                },
            )
        )

        # Act
        result = await project_tools.update_project(
            auth_token="valid_token",
            project_id=123,
            is_private=True,
            is_kanban_activated=False,
            is_issues_activated=True,
        )

        # Assert
        assert result["is_private"] is True
        assert result["is_kanban_activated"] is False
        assert result["is_issues_activated"] is True

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_update_project_handles_version_conflict(self, mock_taiga_api) -> None:
        """
        RF-034: El servidor DEBE manejar rate limiting de Taiga.
        Verifica manejo de conflictos de versión (optimistic locking).
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.patch("https://api.taiga.io/api/v1/projects/123").mock(
            return_value=httpx.Response(400, json={"version": ["Version conflict"]})
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Failed to update project"):
            await project_tools.update_project(
                auth_token="valid_token", project_id=123, name="Updated", version=1
            )


class TestDeleteProjectTool:
    """Tests para la herramienta delete_project - RF-011."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_delete_project_success(self, mock_taiga_api) -> None:
        """
        Verifica que delete_project elimina un proyecto correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.delete("https://api.taiga.io/api/v1/projects/123").mock(
            return_value=httpx.Response(204)
        )

        # Act
        result = await project_tools.delete_project(auth_token="valid_token", project_id=123)

        # Assert
        assert result is True

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, mock_taiga_api) -> None:
        """
        Verifica manejo de proyecto no encontrado al eliminar.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.delete("https://api.taiga.io/api/v1/projects/999").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Project 999 not found"):
            await project_tools.delete_project(auth_token="valid_token", project_id=999)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_delete_project_permission_denied(self, mock_taiga_api) -> None:
        """
        Verifica manejo de permisos insuficientes.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.delete("https://api.taiga.io/api/v1/projects/123").mock(
            return_value=httpx.Response(
                403, json={"detail": "You do not have permission to delete this project"}
            )
        )

        # Act & Assert
        with pytest.raises(ToolError, match="permission"):
            await project_tools.delete_project(auth_token="valid_token", project_id=123)


class TestProjectStatsTool:
    """Tests para la herramienta get_project_stats - RF-011."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_stats(self, mock_taiga_api) -> None:
        """
        Verifica que get_project_stats retorna estadísticas del proyecto.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/projects/123/stats").mock(
            return_value=httpx.Response(
                200,
                json={
                    "total_milestones": 5,
                    "total_points": 150,
                    "closed_points": 75,
                    "defined_points": 100,
                    "assigned_points": 120,
                    "total_userstories": 25,
                    "total_issues": 45,
                    "total_tasks": 120,
                    "speed": 15.5,
                    "closed_issues": 30,
                    "closed_tasks": 80,
                },
            )
        )

        # Act
        result = await project_tools.get_project_stats(auth_token="valid_token", project_id=123)

        # Assert
        assert result["total_milestones"] == 5
        assert result["total_points"] == 150
        assert result["closed_points"] == 75
        assert result["speed"] == 15.5


class TestDuplicateProjectTool:
    """Tests para la herramienta duplicate_project - RF-011, RF-030."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_duplicate_project_tool_is_registered(self) -> None:
        """
        RF-030: TODAS las funcionalidades de Taiga DEBEN estar expuestas.
        Verifica que duplicate_project está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)

        # Act
        project_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_duplicate_project" in tool_names

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_duplicate_project_success(self, mock_taiga_api) -> None:
        """
        Verifica que duplicate_project duplica un proyecto correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/projects/123/duplicate").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": 456,
                    "name": "Copy of Original Project",
                    "slug": "copy-of-original-project",
                    "description": "Duplicated project",
                    "is_private": False,
                },
            )
        )

        # Act
        result = await project_tools.duplicate_project(
            auth_token="valid_token",
            project_id=123,
            name="Copy of Original Project",
            description="Duplicated project",
            users=["user1@example.com", "user2@example.com"],
        )

        # Assert
        assert result["id"] == 456
        assert result["name"] == "Copy of Original Project"
        assert result["id"] != 123  # Es un proyecto nuevo


class TestProjectLikeWatchTools:
    """Tests para las herramientas like/unlike y watch/unwatch - RF-011."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_like_project(self, mock_taiga_api) -> None:
        """
        Verifica que like_project marca proyecto como favorito.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/projects/123/like").mock(
            return_value=httpx.Response(200, json={"is_fan": True, "total_fans": 10})
        )

        # Act
        result = await project_tools.like_project(auth_token="valid_token", project_id=123)

        # Assert
        assert result["is_fan"] is True
        assert result["total_fans"] == 10

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_unlike_project(self, mock_taiga_api) -> None:
        """
        Verifica que unlike_project remueve proyecto de favoritos.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/projects/123/unlike").mock(
            return_value=httpx.Response(200, json={"is_fan": False, "total_fans": 9})
        )

        # Act
        result = await project_tools.unlike_project(auth_token="valid_token", project_id=123)

        # Assert
        assert result["is_fan"] is False
        assert result["total_fans"] == 9

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_watch_project(self, mock_taiga_api) -> None:
        """
        Verifica que watch_project activa notificaciones del proyecto.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/projects/123/watch").mock(
            return_value=httpx.Response(200, json={"is_watcher": True, "total_watchers": 15})
        )

        # Act
        result = await project_tools.watch_project(auth_token="valid_token", project_id=123)

        # Assert
        assert result["is_watcher"] is True
        assert result["total_watchers"] == 15

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_unwatch_project(self, mock_taiga_api) -> None:
        """
        Verifica que unwatch_project desactiva notificaciones.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/projects/123/unwatch").mock(
            return_value=httpx.Response(200, json={"is_watcher": False, "total_watchers": 14})
        )

        # Act
        result = await project_tools.unwatch_project(auth_token="valid_token", project_id=123)

        # Assert
        assert result["is_watcher"] is False
        assert result["total_watchers"] == 14


class TestProjectToolsBestPractices:
    """Tests para verificar buenas prácticas en herramientas de proyectos."""

    @pytest.mark.unit
    @pytest.mark.projects
    def test_project_tools_use_async_await(self) -> None:
        """
        RF-007, RNF-001: Usar async/await para operaciones I/O.
        Verifica que las herramientas de proyectos son asíncronas.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        # Act
        import inspect

        # Assert
        assert inspect.iscoroutinefunction(project_tools.list_projects)
        assert inspect.iscoroutinefunction(project_tools.create_project)
        assert inspect.iscoroutinefunction(project_tools.get_project)
        assert inspect.iscoroutinefunction(project_tools.update_project)
        assert inspect.iscoroutinefunction(project_tools.delete_project)

    @pytest.mark.unit
    @pytest.mark.projects
    def test_project_tools_have_docstrings(self) -> None:
        """
        RNF-006: El código DEBE tener docstrings descriptivos.
        Verifica que las herramientas tienen documentación.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        # Act & Assert
        assert project_tools.list_projects.__doc__ is not None
        assert "list" in project_tools.list_projects.__doc__.lower()

        assert project_tools.create_project.__doc__ is not None
        assert "create" in project_tools.create_project.__doc__.lower()

        assert project_tools.get_project.__doc__ is not None
        assert project_tools.update_project.__doc__ is not None
        assert project_tools.delete_project.__doc__ is not None

    @pytest.mark.unit
    @pytest.mark.projects
    def test_project_tools_use_type_hints(self) -> None:
        """
        RNF-005: El código DEBE usar type hints completos.
        Verifica que las herramientas tienen type hints.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()  # Need to register tools first

        # Act
        import inspect

        # Assert - list_projects
        sig = inspect.signature(project_tools.list_projects)
        assert sig.return_annotation != inspect.Signature.empty

        # Assert - create_project
        sig = inspect.signature(project_tools.create_project)
        assert sig.parameters["name"].annotation is str
        assert sig.parameters["description"].annotation == str | None
        assert sig.return_annotation != inspect.Signature.empty

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_project_tools_handle_errors_properly(self) -> None:
        """
        RF-026: El servidor DEBE implementar manejo de errores con ToolError.
        Verifica que las herramientas manejan errores correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        # Test varios tipos de errores
        test_cases = [
            (httpx.NetworkError("Network error"), "Network error"),
            (httpx.TimeoutException("Timeout"), "Timeout"),
            (ValueError("Invalid data"), "Invalid data"),
            (Exception("Unknown error"), "Unknown error"),
        ]

        for error, expected_message in test_cases:
            with patch("httpx.AsyncClient.get") as mock_get:
                mock_get.side_effect = error

                # Act & Assert
                with pytest.raises(ToolError) as exc_info:
                    await project_tools.list_projects("token")

                assert expected_message in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.projects
    def test_all_project_tools_are_registered(self) -> None:
        """
        RF-030: TODAS las funcionalidades de Taiga DEBEN estar expuestas.
        Verifica que todas las herramientas de proyecto están registradas.
        """
        # Arrange
        import asyncio

        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)

        # Act
        project_tools.register_tools()
        tools = asyncio.run(mcp.get_tools())
        tool_names = list(tools.keys())

        # Assert - Todas las herramientas necesarias (con prefijo taiga_)
        expected_tools = [
            "taiga_list_projects",
            "taiga_create_project",
            "taiga_get_project",
            "taiga_update_project",
            "taiga_delete_project",
            "taiga_get_project_stats",
            "taiga_duplicate_project",
            "taiga_like_project",
            "taiga_unlike_project",
            "taiga_watch_project",
            "taiga_unwatch_project",
            "taiga_get_project_modules",
            "taiga_update_project_modules",
        ]

        for tool in expected_tools:
            assert tool in tool_names, f"Tool {tool} not registered"

        # Verificar que hay al menos 12 herramientas de proyectos
        assert len([t for t in tool_names if "project" in t]) >= 12


class TestProjectToolsExceptionHandling:
    """Tests para manejo de excepciones en ProjectTools."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_list_projects_authentication_error(self) -> None:
        """
        Verifica que se maneja correctamente AuthenticationError.
        Cubre líneas 91-92 de project_tools.py.
        """
        from src.domain.exceptions import AuthenticationError

        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        # Mock TaigaAPIClient para lanzar AuthenticationError
        with patch("src.application.tools.project_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.side_effect = AuthenticationError("Invalid token")

            # Act & Assert
            with pytest.raises(ToolError, match="Authentication failed"):
                await project_tools.list_projects(auth_token="invalid_token")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_list_projects_taiga_api_error(self) -> None:
        """
        Verifica que se maneja correctamente TaigaAPIError.
        Cubre líneas 93-94 de project_tools.py.
        """
        from src.domain.exceptions import TaigaAPIError

        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        # Mock TaigaAPIClient para lanzar TaigaAPIError
        with patch("src.application.tools.project_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.side_effect = TaigaAPIError("API rate limit exceeded")

            # Act & Assert
            with pytest.raises(ToolError, match="API error: API rate limit exceeded"):
                await project_tools.list_projects(auth_token="valid_token")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_list_projects_unexpected_error(self) -> None:
        """
        Verifica que se manejan correctamente errores inesperados.
        Cubre líneas 95-96 de project_tools.py.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        # Mock TaigaAPIClient para lanzar excepción genérica
        with patch("src.application.tools.project_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.side_effect = RuntimeError("Network connection lost")

            # Act & Assert
            with pytest.raises(ToolError, match="Unexpected error: Network connection lost"):
                await project_tools.list_projects(auth_token="valid_token")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_authentication_error(self) -> None:
        """
        Verifica manejo de AuthenticationError en create_project.
        """
        from src.domain.exceptions import AuthenticationError

        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        with patch("src.application.tools.project_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.side_effect = AuthenticationError("Token expired")

            # Act & Assert
            with pytest.raises(ToolError, match="Authentication failed"):
                await project_tools.create_project(auth_token="expired_token", name="Test Project")

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_update_project_permission_error(self) -> None:
        """
        Verifica manejo de PermissionDeniedError en update_project.
        """
        from src.domain.exceptions import PermissionDeniedError

        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        with patch("src.application.tools.project_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.patch.side_effect = PermissionDeniedError("No permission to update")

            # Act & Assert
            with pytest.raises(ToolError, match="No permission"):
                await project_tools.update_project(
                    auth_token="valid_token", project_id=123, name="Updated"
                )

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_delete_project_not_found_error(self) -> None:
        """
        Verifica manejo de ResourceNotFoundError en delete_project.
        """
        from src.domain.exceptions import ResourceNotFoundError

        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        with patch("src.application.tools.project_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.delete.side_effect = ResourceNotFoundError("Project not found")

            # Act & Assert
            with pytest.raises(ToolError, match="not found"):
                await project_tools.delete_project(auth_token="valid_token", project_id=999)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_taiga_error(self) -> None:
        """
        Verifica manejo de TaigaAPIError en get_project.
        """
        from src.domain.exceptions import TaigaAPIError

        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        with patch("src.application.tools.project_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.side_effect = TaigaAPIError("Server error")

            # Act & Assert
            with pytest.raises(ToolError, match="API error: Server error"):
                await project_tools.get_project(auth_token="valid_token", project_id=123)

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_duplicate_project_permissions_error(self) -> None:
        """
        Verifica manejo de PermissionDeniedError en duplicate_project.
        """
        from src.domain.exceptions import PermissionDeniedError

        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        with patch("src.application.tools.project_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.side_effect = PermissionDeniedError("Cannot duplicate project")

            # Act & Assert
            with pytest.raises(ToolError, match="Unexpected error: Cannot duplicate"):
                await project_tools.duplicate_project(
                    auth_token="valid_token", project_id=123, name="Duplicate"
                )


class TestGetProjectBySlugTool:
    """Tests para obtener proyecto por slug - PROJ-014."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_by_slug_tool_is_registered(self) -> None:
        """
        PROJ-014: Obtener proyecto por slug.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)

        # Act
        project_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_get_project_by_slug" in tool_names

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_by_slug_success(self, mock_taiga_api) -> None:
        """
        Verifica que get_project_by_slug obtiene proyecto correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/projects/by_slug?slug=my-project").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 123,
                    "name": "My Project",
                    "slug": "my-project",
                    "description": "A test project",
                },
            )
        )

        # Act
        result = await project_tools.get_project_by_slug(
            auth_token="valid_token", slug="my-project"
        )

        # Assert
        assert result["id"] == 123
        assert result["slug"] == "my-project"


class TestProjectIssuesStatsTool:
    """Tests para estadísticas de issues del proyecto - PROJ-015."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_issues_stats_tool_is_registered(self) -> None:
        """
        PROJ-015: Estadísticas de issues del proyecto.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)

        # Act
        project_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_get_project_issues_stats" in tool_names

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_issues_stats(self, mock_taiga_api) -> None:
        """
        Verifica que obtiene estadísticas de issues correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/projects/123/issues_stats").mock(
            return_value=httpx.Response(
                200,
                json={
                    "total_issues": 45,
                    "opened_issues": 20,
                    "closed_issues": 25,
                    "issues_per_type": {"Bug": 15, "Enhancement": 10, "Task": 20},
                    "issues_per_status": {"New": 5, "In Progress": 15, "Closed": 25},
                },
            )
        )

        # Act
        result = await project_tools.get_project_issues_stats(
            auth_token="valid_token", project_id=123
        )

        # Assert
        assert result["total_issues"] == 45
        assert result["opened_issues"] == 20
        assert result["closed_issues"] == 25


class TestProjectTagsTools:
    """Tests para gestión de tags del proyecto - PROJ-016 a PROJ-020."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_tags_tool_is_registered(self) -> None:
        """
        PROJ-016: Obtener tags del proyecto.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)

        # Act
        project_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_get_project_tags" in tool_names

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_get_project_tags(self, mock_taiga_api) -> None:
        """
        Verifica que obtiene tags del proyecto correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/projects/123/tags").mock(
            return_value=httpx.Response(
                200, json=[["backend", "#FF0000"], ["frontend", "#00FF00"], ["bug", "#0000FF"]]
            )
        )

        # Act
        result = await project_tools.get_project_tags(auth_token="valid_token", project_id=123)

        # Assert
        assert len(result) == 3
        assert result[0][0] == "backend"
        assert result[0][1] == "#FF0000"

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_tag_tool_is_registered(self) -> None:
        """
        PROJ-017: Crear tag en proyecto.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)

        # Act
        project_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_create_project_tag" in tool_names

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_create_project_tag(self, mock_taiga_api) -> None:
        """
        Verifica que crea tag correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/projects/123/create_tag").mock(
            return_value=httpx.Response(200, json=["new-tag", "#FF00FF"])
        )

        # Act
        result = await project_tools.create_project_tag(
            auth_token="valid_token", project_id=123, tag="new-tag", color="#FF00FF"
        )

        # Assert
        assert result[0] == "new-tag"
        assert result[1] == "#FF00FF"

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_edit_project_tag_tool_is_registered(self) -> None:
        """
        PROJ-018: Editar tag del proyecto.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)

        # Act
        project_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_edit_project_tag" in tool_names

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_edit_project_tag(self, mock_taiga_api) -> None:
        """
        Verifica que edita tag correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/projects/123/edit_tag").mock(
            return_value=httpx.Response(200, json=["edited-tag", "#FFFF00"])
        )

        # Act
        result = await project_tools.edit_project_tag(
            auth_token="valid_token",
            project_id=123,
            from_tag="old-tag",
            to_tag="edited-tag",
            color="#FFFF00",
        )

        # Assert
        assert result[0] == "edited-tag"
        assert result[1] == "#FFFF00"

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_delete_project_tag_tool_is_registered(self) -> None:
        """
        PROJ-019: Eliminar tag del proyecto.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)

        # Act
        project_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_delete_project_tag" in tool_names

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_delete_project_tag(self, mock_taiga_api) -> None:
        """
        Verifica que elimina tag correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/projects/123/delete_tag").mock(
            return_value=httpx.Response(204)
        )

        # Act
        result = await project_tools.delete_project_tag(
            auth_token="valid_token", project_id=123, tag="obsolete-tag"
        )

        # Assert
        assert result is True

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_mix_project_tags_tool_is_registered(self) -> None:
        """
        PROJ-020: Mezclar tags del proyecto.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)

        # Act
        project_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_mix_project_tags" in tool_names

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_mix_project_tags(self, mock_taiga_api) -> None:
        """
        Verifica que mezcla tags correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/projects/123/mix_tags").mock(
            return_value=httpx.Response(200, json=["merged-tag", "#AABBCC"])
        )

        # Act
        result = await project_tools.mix_project_tags(
            auth_token="valid_token",
            project_id=123,
            from_tags=["tag1", "tag2"],
            to_tag="merged-tag",
        )

        # Assert
        assert result[0] == "merged-tag"
        assert result[1] == "#AABBCC"


class TestProjectExportTool:
    """Tests para exportar proyecto - PROJ-021."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_export_project_tool_is_registered(self) -> None:
        """
        PROJ-021: Exportar proyecto.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)

        # Act
        project_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_export_project" in tool_names

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_export_project(self, mock_taiga_api) -> None:
        """
        Verifica que exporta proyecto correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/exporter/123").mock(
            return_value=httpx.Response(200, content=b'{"project": "data", "version": "1.0"}')
        )

        # Act
        result = await project_tools.export_project(auth_token="valid_token", project_id=123)

        # Assert
        assert result == b'{"project": "data", "version": "1.0"}'


class TestProjectBulkUpdateOrderTool:
    """Tests para reordenar proyectos en lote - PROJ-022."""

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_bulk_update_projects_order_tool_is_registered(self) -> None:
        """
        PROJ-022: Reordenar proyectos en lote.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)

        # Act
        project_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_bulk_update_projects_order" in tool_names

    @pytest.mark.unit
    @pytest.mark.projects
    @pytest.mark.asyncio
    async def test_bulk_update_projects_order(self, mock_taiga_api) -> None:
        """
        Verifica que reordena proyectos en lote correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        project_tools = ProjectTools(mcp)
        project_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/projects/bulk_update_order").mock(
            return_value=httpx.Response(
                200, json=[{"id": 1, "order": 0}, {"id": 2, "order": 1}, {"id": 3, "order": 2}]
            )
        )

        # Act
        result = await project_tools.bulk_update_projects_order(
            auth_token="valid_token", projects_order=[[1, 0], [2, 1], [3, 2]]
        )

        # Assert
        assert len(result) == 3
        assert result[0]["order"] == 0
        assert result[1]["order"] == 1
        assert result[2]["order"] == 2
