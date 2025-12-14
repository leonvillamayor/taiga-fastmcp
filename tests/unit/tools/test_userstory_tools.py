"""
Tests unitarios para las herramientas de user stories del servidor MCP.
Verifica las herramientas de user stories según RF-012, RF-016, RF-030.
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.application.tools.userstory_tools import UserStoryTools


class TestListUserStoriesTool:
    """Tests para la herramienta list_userstories - RF-012, RF-016."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_tool_is_registered(self) -> None:
        """
        RF-012: Las herramientas DEBEN cubrir user stories de Taiga.
        RF-016: El servidor DEBE soportar operaciones CRUD en user stories.
        Verifica que la herramienta list_userstories está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)

        # Act
        userstory_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_list_userstories" in tool_names

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_by_project(self, mock_taiga_api) -> None:
        """
        Verifica que list_userstories retorna historias de un proyecto.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        # Mock de respuesta exitosa
        mock_taiga_api.get(
            "https://api.taiga.io/api/v1/userstories?project=123&page=1&page_size=100"
        ).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "ref": 1,
                        "subject": "As a user I want to login",
                        "description": "Login functionality",
                        "project": 123,
                        "status": {"id": 1, "name": "New", "color": "#999999"},
                        "points": {"1": 3, "2": 5, "3": 8},
                        "total_points": 5.33,
                        "is_closed": False,
                        "tags": ["auth", "critical"],
                    },
                    {
                        "id": 2,
                        "ref": 2,
                        "subject": "As a user I want to reset password",
                        "description": "Password reset flow",
                        "project": 123,
                        "status": {"id": 2, "name": "In Progress", "color": "#ff9900"},
                        "points": {"1": 2, "2": 3, "3": 5},
                        "total_points": 3.33,
                        "is_closed": False,
                        "tags": ["auth"],
                    },
                ],
            )
        )

        # Act
        result = await userstory_tools.list_userstories(auth_token="valid_token", project_id=123)

        # Assert
        assert len(result) == 2
        assert result[0]["subject"] == "As a user I want to login"
        assert result[1]["subject"] == "As a user I want to reset password"
        assert result[0]["total_points"] == 5.33

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_with_filters(self, mock_taiga_api) -> None:
        """
        RF-032: El servidor DEBE soportar filtrado y búsqueda de elementos.
        Verifica que list_userstories puede filtrar historias.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        # Mock con filtros
        mock_taiga_api.get(
            "https://api.taiga.io/api/v1/userstories?project=123&status=1&tags=auth&page=1&page_size=100"
        ).mock(
            return_value=httpx.Response(
                200, json=[{"id": 1, "subject": "Login story", "status": {"id": 1}}]
            )
        )

        # Act
        result = await userstory_tools.list_userstories(
            auth_token="valid_token", project_id=123, status=1, tags=["auth"]
        )

        # Assert
        assert len(result) == 1
        assert result[0]["subject"] == "Login story"

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_by_milestone(self, mock_taiga_api) -> None:
        """
        RF-020: El servidor DEBE soportar operaciones CRUD en sprints/milestones.
        Verifica que puede listar historias de un sprint.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        mock_taiga_api.get(
            "https://api.taiga.io/api/v1/userstories?milestone=10&page=1&page_size=100"
        ).mock(
            return_value=httpx.Response(
                200, json=[{"id": 3, "subject": "Sprint story", "milestone": 10}]
            )
        )

        # Act
        result = await userstory_tools.list_userstories(auth_token="valid_token", milestone_id=10)

        # Assert
        assert len(result) == 1
        assert result[0]["milestone"] == 10


class TestCreateUserStoryTool:
    """Tests para la herramienta create_userstory - RF-012, RF-016."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_create_userstory_tool_is_registered(self) -> None:
        """
        RF-016: El servidor DEBE soportar operaciones CRUD en user stories.
        Verifica que la herramienta create_userstory está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)

        # Act
        userstory_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_create_userstory" in tool_names

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_create_userstory_minimal(self, mock_taiga_api) -> None:
        """
        Verifica creación de user story con datos mínimos.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/userstories").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": 100,
                    "ref": 25,
                    "project": 123,
                    "subject": "New user story",
                    "description": "Story description",
                    "status": {"id": 1, "name": "New"},
                    "is_closed": False,
                },
            )
        )

        # Act
        result = await userstory_tools.create_userstory(
            auth_token="valid_token",
            project_id=123,
            subject="New user story",
            description="Story description",
        )

        # Assert
        assert result["id"] == 100
        assert result["ref"] == 25
        assert result["subject"] == "New user story"

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_create_userstory_with_points(self, mock_taiga_api) -> None:
        """
        RF-028: El servidor DEBE soportar estimación de puntos en user stories.
        Verifica creación con puntos de historia.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/userstories").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": 101,
                    "subject": "Story with points",
                    "points": {"1": 5, "2": 8, "3": 13},
                    "total_points": 8.67,
                },
            )
        )

        # Act
        result = await userstory_tools.create_userstory(
            auth_token="valid_token",
            project_id=123,
            subject="Story with points",
            points={"1": 5, "2": 8, "3": 13},
        )

        # Assert
        assert result["points"]["1"] == 5
        assert result["points"]["2"] == 8
        assert result["points"]["3"] == 13
        assert result["total_points"] == 8.67

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_create_userstory_with_attachments(self, mock_taiga_api) -> None:
        """
        RF-022: El servidor DEBE soportar adjuntar archivos a elementos.
        Verifica creación con attachments.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/userstories").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": 102,
                    "subject": "Story with attachments",
                    "attachments": [{"id": 1, "name": "mockup.png", "size": 102400}],
                },
            )
        )

        # Act
        result = await userstory_tools.create_userstory(
            auth_token="valid_token",
            project_id=123,
            subject="Story with attachments",
            attachments=[{"file": "mockup.png", "description": "UI mockup"}],
        )

        # Assert
        assert len(result["attachments"]) == 1
        assert result["attachments"][0]["name"] == "mockup.png"


class TestGetUserStoryTool:
    """Tests para la herramienta get_userstory - RF-012, RF-016."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_by_id(self, mock_taiga_api) -> None:
        """
        Verifica obtener user story por ID.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/userstories/100").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 100,
                    "ref": 25,
                    "subject": "Complete user story",
                    "description": "Full details",
                    "status": {"id": 2, "name": "In Progress"},
                    "assigned_to": {"id": 5, "username": "developer"},
                    "watchers": [5, 6, 7],
                    "total_watchers": 3,
                    "is_blocked": False,
                    "blocked_note": "",
                    "client_requirement": True,
                    "team_requirement": False,
                },
            )
        )

        # Act
        result = await userstory_tools.get_userstory(auth_token="valid_token", userstory_id=100)

        # Assert
        assert result["id"] == 100
        assert result["assigned_to"]["username"] == "developer"
        assert result["total_watchers"] == 3
        assert result["client_requirement"] is True

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_by_ref(self, mock_taiga_api) -> None:
        """
        Verifica obtener user story por referencia.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        mock_taiga_api.get(
            "https://api.taiga.io/api/v1/userstories/by_ref?ref=25&project=123"
        ).mock(
            return_value=httpx.Response(200, json={"id": 100, "ref": 25, "subject": "Story by ref"})
        )

        # Act
        result = await userstory_tools.get_userstory(
            auth_token="valid_token", project_id=123, ref=25
        )

        # Assert
        assert result["ref"] == 25
        assert result["subject"] == "Story by ref"


class TestUpdateUserStoryTool:
    """Tests para la herramienta update_userstory - RF-012, RF-016."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_status(self, mock_taiga_api) -> None:
        """
        RF-029: El servidor DEBE soportar cambio de estado en elementos.
        Verifica actualización de estado.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        mock_taiga_api.patch("https://api.taiga.io/api/v1/userstories/100").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 100,
                    "status": {"id": 3, "name": "Done"},
                    "is_closed": True,
                    "version": 2,
                },
            )
        )

        # Act
        result = await userstory_tools.update_userstory(
            auth_token="valid_token", userstory_id=100, status=3, is_closed=True, version=1
        )

        # Assert
        assert result["status"]["name"] == "Done"
        assert result["is_closed"] is True
        assert result["version"] == 2

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_assignment(self, mock_taiga_api) -> None:
        """
        Verifica actualización de asignación.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        mock_taiga_api.patch("https://api.taiga.io/api/v1/userstories/100").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 100,
                    "assigned_to": {"id": 10, "username": "newdev"},
                    "assigned_users": [10],
                },
            )
        )

        # Act
        result = await userstory_tools.update_userstory(
            auth_token="valid_token", userstory_id=100, assigned_to=10
        )

        # Assert
        assert result["assigned_to"]["username"] == "newdev"

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_blocked_status(self, mock_taiga_api) -> None:
        """
        Verifica actualización de bloqueo.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        mock_taiga_api.patch("https://api.taiga.io/api/v1/userstories/100").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 100,
                    "is_blocked": True,
                    "blocked_note": "Waiting for API documentation",
                },
            )
        )

        # Act
        result = await userstory_tools.update_userstory(
            auth_token="valid_token",
            userstory_id=100,
            is_blocked=True,
            blocked_note="Waiting for API documentation",
        )

        # Assert
        assert result["is_blocked"] is True
        assert result["blocked_note"] == "Waiting for API documentation"


class TestDeleteUserStoryTool:
    """Tests para la herramienta delete_userstory - RF-012, RF-016."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_delete_userstory_success(self, mock_taiga_api) -> None:
        """
        Verifica eliminación exitosa de user story.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        mock_taiga_api.delete("https://api.taiga.io/api/v1/userstories/100").mock(
            return_value=httpx.Response(204)
        )

        # Act
        result = await userstory_tools.delete_userstory(auth_token="valid_token", userstory_id=100)

        # Assert
        assert result is True

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_delete_userstory_not_found(self, mock_taiga_api) -> None:
        """
        Verifica manejo de user story no encontrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        mock_taiga_api.delete("https://api.taiga.io/api/v1/userstories/999").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Not found"):
            await userstory_tools.delete_userstory(auth_token="valid_token", userstory_id=999)


class TestBulkUserStoryOperations:
    """Tests para operaciones bulk en user stories - RF-027."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_create_userstories(self, mock_taiga_api) -> None:
        """
        RF-027: El servidor DEBE soportar operaciones bulk en elementos.
        Verifica creación masiva de user stories.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/userstories/bulk_create").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"id": 201, "subject": "Bulk story 1"},
                    {"id": 202, "subject": "Bulk story 2"},
                    {"id": 203, "subject": "Bulk story 3"},
                ],
            )
        )

        # Act
        result = await userstory_tools.bulk_create_userstories(
            auth_token="valid_token",
            project_id=123,
            bulk_stories="Bulk story 1\nBulk story 2\nBulk story 3",
        )

        # Assert
        assert len(result) == 3
        assert result[0]["subject"] == "Bulk story 1"
        assert result[2]["id"] == 203

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_update_userstories(self, mock_taiga_api) -> None:
        """
        RF-027: Operaciones bulk en elementos.
        Verifica actualización masiva.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/userstories/bulk_update").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"id": 201, "status": {"id": 3, "name": "Done"}},
                    {"id": 202, "status": {"id": 3, "name": "Done"}},
                ],
            )
        )

        # Act
        result = await userstory_tools.bulk_update_userstories(
            auth_token="valid_token", story_ids=[201, 202], status=3
        )

        # Assert
        assert len(result) == 2
        assert all(s["status"]["name"] == "Done" for s in result)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_bulk_delete_userstories(self, mock_taiga_api) -> None:
        """
        RF-027: Operaciones bulk en elementos.
        Verifica eliminación masiva.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/userstories/bulk_delete").mock(
            return_value=httpx.Response(204)
        )

        # Act
        result = await userstory_tools.bulk_delete_userstories(
            auth_token="valid_token", story_ids=[201, 202, 203]
        )

        # Assert
        assert result is True


class TestUserStoryRelatedOperations:
    """Tests para operaciones relacionadas con user stories."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_move_userstory_to_milestone(self, mock_taiga_api) -> None:
        """
        RF-020: Operaciones CRUD en sprints/milestones.
        Verifica mover story a otro sprint.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        mock_taiga_api.patch("https://api.taiga.io/api/v1/userstories/100").mock(
            return_value=httpx.Response(
                200, json={"id": 100, "milestone": 20, "milestone_name": "Sprint 2"}
            )
        )

        # Act
        result = await userstory_tools.move_to_milestone(
            auth_token="valid_token", userstory_id=100, milestone_id=20
        )

        # Assert
        assert result["milestone"] == 20
        assert result["milestone_name"] == "Sprint 2"

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_history(self, mock_taiga_api) -> None:
        """
        RF-021: El servidor DEBE soportar historial de cambios.
        Verifica obtener historial de cambios.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/history/userstory/100").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "user": {"username": "user1"},
                        "created_at": "2024-01-01T10:00:00Z",
                        "type": 1,
                        "diff": {"status": ["New", "In Progress"]},
                    },
                    {
                        "id": 2,
                        "user": {"username": "user2"},
                        "created_at": "2024-01-02T15:00:00Z",
                        "type": 1,
                        "diff": {"assigned_to": [None, "developer"]},
                    },
                ],
            )
        )

        # Act
        result = await userstory_tools.get_userstory_history(
            auth_token="valid_token", userstory_id=100
        )

        # Assert
        assert len(result) == 2
        assert result[0]["diff"]["status"][1] == "In Progress"
        assert result[1]["diff"]["assigned_to"][1] == "developer"

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_watch_unwatch_userstory(self, mock_taiga_api) -> None:
        """
        RF-024: El servidor DEBE soportar notificaciones y watchers.
        Verifica watch/unwatch de user story.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        # Watch
        mock_taiga_api.post("https://api.taiga.io/api/v1/userstories/100/watch").mock(
            return_value=httpx.Response(200, json={"is_watcher": True, "total_watchers": 5})
        )

        result_watch = await userstory_tools.watch_userstory(
            auth_token="valid_token", userstory_id=100
        )

        assert result_watch["is_watcher"] is True

        # Unwatch
        mock_taiga_api.post("https://api.taiga.io/api/v1/userstories/100/unwatch").mock(
            return_value=httpx.Response(200, json={"is_watcher": False, "total_watchers": 4})
        )

        result_unwatch = await userstory_tools.unwatch_userstory(
            auth_token="valid_token", userstory_id=100
        )

        assert result_unwatch["is_watcher"] is False


class TestUserStoryToolsBestPractices:
    """Tests para verificar buenas prácticas en herramientas de user stories."""

    @pytest.mark.unit
    @pytest.mark.userstories
    def test_userstory_tools_are_async(self) -> None:
        """
        RNF-001: Usar async/await para operaciones I/O.
        Verifica que todas las herramientas son asíncronas.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        # Act
        import inspect

        # Assert
        assert inspect.iscoroutinefunction(userstory_tools.list_userstories)
        assert inspect.iscoroutinefunction(userstory_tools.create_userstory)
        assert inspect.iscoroutinefunction(userstory_tools.get_userstory)
        assert inspect.iscoroutinefunction(userstory_tools.update_userstory)
        assert inspect.iscoroutinefunction(userstory_tools.delete_userstory)
        assert inspect.iscoroutinefunction(userstory_tools.bulk_create_userstories)

    @pytest.mark.unit
    @pytest.mark.userstories
    def test_all_userstory_tools_registered(self) -> None:
        """
        RF-030: TODAS las funcionalidades de Taiga DEBEN estar expuestas.
        Verifica que todas las herramientas están registradas.
        """
        # Arrange
        import asyncio

        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)

        # Act
        userstory_tools.register_tools()
        tools = asyncio.run(mcp.get_tools())
        tool_names = list(tools.keys())

        # Assert - Todas las herramientas esperadas
        expected_tools = [
            "taiga_list_userstories",
            "taiga_create_userstory",
            "taiga_get_userstory",
            "taiga_update_userstory",
            "taiga_delete_userstory",
            "taiga_bulk_create_userstories",
            "taiga_bulk_update_userstories",
            "taiga_bulk_delete_userstories",
            "taiga_move_to_milestone",
            "taiga_get_userstory_history",
            "taiga_watch_userstory",
            "taiga_unwatch_userstory",
            "taiga_upvote_userstory",
            "taiga_downvote_userstory",
            "taiga_get_userstory_voters",
        ]

        for tool in expected_tools:
            assert tool in tool_names, f"Tool {tool} not registered"

        # Verificar que hay al menos 14 herramientas de user stories
        assert len([t for t in tool_names if "userstor" in t.lower()]) >= 14


class TestUserStoryToolsExceptionHandling:
    """Tests para manejo de excepciones en UserStoryTools."""

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_authentication_error(self) -> None:
        """
        Verifica que se maneja correctamente AuthenticationError.
        Cubre líneas 94-95 de userstory_tools.py.
        """
        from src.domain.exceptions import AuthenticationError

        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        # Mock TaigaAPIClient para lanzar AuthenticationError
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.side_effect = AuthenticationError("Invalid token")

            # Act & Assert
            with pytest.raises(ToolError, match="Authentication failed"):
                await userstory_tools.list_userstories(auth_token="invalid_token")

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_taiga_api_error(self) -> None:
        """
        Verifica que se maneja correctamente TaigaAPIError.
        Cubre líneas 96-97 de userstory_tools.py.
        """
        from src.domain.exceptions import TaigaAPIError

        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        # Mock TaigaAPIClient para lanzar TaigaAPIError
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.side_effect = TaigaAPIError("API rate limit exceeded")

            # Act & Assert
            with pytest.raises(ToolError, match="API error: API rate limit exceeded"):
                await userstory_tools.list_userstories(auth_token="valid_token")

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_list_userstories_unexpected_error(self) -> None:
        """
        Verifica que se manejan correctamente errores inesperados.
        Cubre líneas 98-99 de userstory_tools.py.
        """
        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        # Mock TaigaAPIClient para lanzar excepción genérica
        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.side_effect = RuntimeError("Network connection lost")

            # Act & Assert
            with pytest.raises(ToolError, match="Unexpected error: Network connection lost"):
                await userstory_tools.list_userstories(auth_token="valid_token")

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_create_userstory_authentication_error(self) -> None:
        """
        Verifica manejo de AuthenticationError en create_userstory.
        Cubre más líneas de manejo de excepciones.
        """
        from src.domain.exceptions import AuthenticationError

        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.side_effect = AuthenticationError("Token expired")

            # Act & Assert
            with pytest.raises(ToolError, match="Authentication failed"):
                await userstory_tools.create_userstory(
                    auth_token="expired_token", project_id=1, subject="Test story"
                )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_update_userstory_api_error(self) -> None:
        """
        Verifica manejo de TaigaAPIError en update_userstory.
        Cubre más líneas de manejo de excepciones.
        """
        from src.domain.exceptions import TaigaAPIError

        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.patch.side_effect = TaigaAPIError("Story not found")

            # Act & Assert
            with pytest.raises(ToolError, match="Failed to update user story: Story not found"):
                await userstory_tools.update_userstory(
                    auth_token="valid_token", userstory_id=999, subject="Updated"
                )

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_delete_userstory_permission_error(self) -> None:
        """
        Verifica manejo de PermissionDeniedError en delete_userstory.
        Cubre más casos de excepción.
        """
        from src.domain.exceptions import PermissionDeniedError

        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.delete.side_effect = PermissionDeniedError("No permission to delete")

            # Act & Assert
            with pytest.raises(ToolError, match="No permission to delete user story"):
                await userstory_tools.delete_userstory(auth_token="valid_token", userstory_id=100)

    @pytest.mark.unit
    @pytest.mark.userstories
    @pytest.mark.asyncio
    async def test_get_userstory_not_found_error(self) -> None:
        """
        Verifica manejo de ResourceNotFoundError en get_userstory.
        Cubre más casos de excepción.
        """
        from src.domain.exceptions import ResourceNotFoundError

        # Arrange
        mcp = FastMCP("Test")
        userstory_tools = UserStoryTools(mcp)
        userstory_tools.register_tools()

        with patch("src.application.tools.userstory_tools.TaigaAPIClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.side_effect = ResourceNotFoundError("User story not found")

            # Act & Assert
            with pytest.raises(ToolError, match="User story not found"):
                await userstory_tools.get_userstory(auth_token="valid_token", userstory_id=999)
