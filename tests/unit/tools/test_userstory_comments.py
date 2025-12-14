"""
Tests for User Story comments and history functionality.
US-025 to US-029: User Story history and comments testing.
US-004, US-005, US-009 to US-013, US-019: Additional missing functionality.
"""

import pytest


class TestUserStoryHistory:
    """Tests for User Story history functionality (US-025)."""

    @pytest.mark.asyncio
    async def test_get_userstory_history_tool_is_registered(self, mcp_server) -> None:
        """US-025: Test that get_userstory_history tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "get_userstory_history")

    @pytest.mark.asyncio
    async def test_get_userstory_history(self, mcp_server, taiga_client_mock) -> None:
        """US-025: Test getting user story history."""
        # Configure client.get to return history when called with history endpoint
        taiga_client_mock.get.return_value = [
            {
                "id": "hist789",
                "user": {"username": "developer", "full_name": "Developer Name"},
                "created_at": "2025-01-20T14:30:00Z",
                "type": 1,
                "is_snapshot": False,
                "diff": {"status": ["1", "2"], "assigned_to": ["888691", "999999"]},
                "values": {"status": 2, "assigned_to": 999999, "subject": "Login de usuarios"},
                "comment": "Cambiado a In Progress y reasignado",
                "comment_html": "<p>Cambiado a In Progress y reasignado</p>",
                "delete_comment_date": None,
                "delete_comment_user": None,
            },
            {
                "id": "hist790",
                "user": {"username": "tester", "full_name": "Tester Name"},
                "created_at": "2025-01-21T10:00:00Z",
                "type": 1,
                "diff": {"status": ["2", "3"]},
                "comment": "Movido a testing",
            },
        ]

        # Ejecutar
        result = await mcp_server.userstory_tools.get_userstory_history(
            auth_token="valid_token", userstory_id=123456
        )

        # Verificar
        assert len(result) == 2
        assert result[0]["comment"] == "Cambiado a In Progress y reasignado"
        assert result[1]["comment"] == "Movido a testing"
        # Verify client.get was called with correct endpoint
        taiga_client_mock.get.assert_called_once_with("/history/userstory/123456")


class TestUserStoryComments:
    """Tests for User Story comments functionality (US-026 to US-029)."""

    @pytest.mark.asyncio
    async def test_get_userstory_comment_versions_tool_is_registered(self, mcp_server) -> None:
        """US-026: Test that get_userstory_comment_versions tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "get_userstory_comment_versions")

    @pytest.mark.asyncio
    async def test_get_userstory_comment_versions(self, mcp_server, taiga_client_mock) -> None:
        """US-026: Test getting comment versions for a user story."""
        # Configurar mock
        taiga_client_mock.get_userstory_comment_versions.return_value = [
            {
                "id": 1,
                "comment": "Versión original del comentario",
                "created_at": "2025-01-20T14:00:00Z",
                "user": {"username": "usuario1"},
            },
            {
                "id": 2,
                "comment": "Versión editada del comentario",
                "created_at": "2025-01-20T14:30:00Z",
                "user": {"username": "usuario1"},
            },
        ]

        # Ejecutar
        result = await mcp_server.userstory_tools.get_userstory_comment_versions(
            auth_token="valid_token", userstory_id=123456, comment_id="hist789"
        )

        # Verificar
        assert len(result) == 2
        assert result[0]["comment"] == "Versión original del comentario"
        assert result[1]["comment"] == "Versión editada del comentario"
        taiga_client_mock.get_userstory_comment_versions.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_userstory_comment_tool_is_registered(self, mcp_server) -> None:
        """US-027: Test that edit_userstory_comment tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "edit_userstory_comment")

    @pytest.mark.asyncio
    async def test_edit_userstory_comment(self, mcp_server, taiga_client_mock) -> None:
        """US-027: Test editing a user story comment."""
        # Configurar mock
        taiga_client_mock.edit_userstory_comment.return_value = {
            "id": "hist789",
            "comment": "Comentario editado con correcciones",
            "comment_html": "<p>Comentario editado con correcciones</p>",
            "edit_comment_date": "2025-01-21T15:00:00Z",
        }

        # Ejecutar
        result = await mcp_server.userstory_tools.edit_userstory_comment(
            auth_token="valid_token",
            userstory_id=123456,
            comment_id="hist789",
            comment="Comentario editado con correcciones",
        )

        # Verificar
        assert result["comment"] == "Comentario editado con correcciones"
        assert result["edit_comment_date"] is not None
        taiga_client_mock.edit_userstory_comment.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_userstory_comment_tool_is_registered(self, mcp_server) -> None:
        """US-028: Test that delete_userstory_comment tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "delete_userstory_comment")

    @pytest.mark.asyncio
    async def test_delete_userstory_comment(self, mcp_server, taiga_client_mock) -> None:
        """US-028: Test deleting a user story comment."""
        # Configurar mock
        taiga_client_mock.delete_userstory_comment.return_value = {
            "id": "hist789",
            "delete_comment_date": "2025-01-21T16:00:00Z",
            "delete_comment_user": {"username": "admin"},
        }

        # Ejecutar
        result = await mcp_server.userstory_tools.delete_userstory_comment(
            auth_token="valid_token", userstory_id=123456, comment_id="hist789"
        )

        # Verificar
        assert result["delete_comment_date"] is not None
        assert result["delete_comment_user"]["username"] == "admin"
        taiga_client_mock.delete_userstory_comment.assert_called_once()

    @pytest.mark.asyncio
    async def test_undelete_userstory_comment_tool_is_registered(self, mcp_server) -> None:
        """US-029: Test that undelete_userstory_comment tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "undelete_userstory_comment")

    @pytest.mark.asyncio
    async def test_undelete_userstory_comment(self, mcp_server, taiga_client_mock) -> None:
        """US-029: Test restoring a deleted user story comment."""
        # Configurar mock
        taiga_client_mock.undelete_userstory_comment.return_value = {
            "id": "hist789",
            "comment": "Comentario restaurado",
            "delete_comment_date": None,
            "delete_comment_user": None,
        }

        # Ejecutar
        result = await mcp_server.userstory_tools.undelete_userstory_comment(
            auth_token="valid_token", userstory_id=123456, comment_id="hist789"
        )

        # Verificar
        assert result["comment"] == "Comentario restaurado"
        assert result["delete_comment_date"] is None
        assert result["delete_comment_user"] is None
        taiga_client_mock.undelete_userstory_comment.assert_called_once()


class TestUserStoryMissingFunctionality:
    """Tests for additional missing User Story functionality."""

    @pytest.mark.asyncio
    async def test_get_userstory_by_ref_tool_is_registered(self, mcp_server) -> None:
        """US-004: Test that get_userstory_by_ref tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "get_userstory_by_ref")

    @pytest.mark.asyncio
    async def test_get_userstory_by_ref(self, mcp_server, taiga_client_mock) -> None:
        """US-004: Test getting user story by reference."""
        # Configurar mock
        taiga_client_mock.get_userstory_by_ref.return_value = {
            "id": 123456,
            "ref": 1,
            "subject": "Login de usuarios",
            "project": 309804,
        }

        # Ejecutar
        result = await mcp_server.userstory_tools.get_userstory_by_ref(
            auth_token="valid_token", ref=1, project=309804
        )

        # Verificar
        assert result["ref"] == 1
        assert result["project"] == 309804
        taiga_client_mock.get_userstory_by_ref.assert_called_once_with(ref=1, project=309804)

    @pytest.mark.asyncio
    async def test_update_userstory_full_tool_is_registered(self, mcp_server) -> None:
        """US-005: Test that update_userstory_full tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "update_userstory_full")

    @pytest.mark.asyncio
    async def test_update_userstory_full(self, mcp_server, taiga_client_mock) -> None:
        """US-005: Test full update (PUT) of user story."""
        # Configurar mock
        taiga_client_mock.update_userstory_full.return_value = {
            "id": 123456,
            "ref": 1,
            "version": 5,
            "subject": "Login completo con OAuth",
            "description": "Descripción completamente actualizada",
            "status": 4,
            "points": {"1": 8, "2": 5, "3": 13},
        }

        # Ejecutar
        result = await mcp_server.userstory_tools.update_userstory_full(
            auth_token="valid_token",
            userstory_id=123456,
            version=4,
            subject="Login completo con OAuth",
            description="Descripción completamente actualizada",
            status=4,
            points={"1": 8, "2": 5, "3": 13},
        )

        # Verificar
        assert result["subject"] == "Login completo con OAuth"
        assert result["points"]["1"] == 8
        taiga_client_mock.update_userstory_full.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_update_backlog_order_tool_is_registered(self, mcp_server) -> None:
        """US-009: Test that bulk_update_backlog_order tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "bulk_update_backlog_order")

    @pytest.mark.asyncio
    async def test_bulk_update_backlog_order(self, mcp_server, taiga_client_mock) -> None:
        """US-009: Test reordering user stories in backlog."""
        # Configurar mock
        taiga_client_mock.bulk_update_backlog_order.return_value = {"success": True}

        # Ejecutar
        result = await mcp_server.userstory_tools.bulk_update_backlog_order(
            auth_token="valid_token",
            project_id=309804,
            bulk_stories=[[123456, 0], [123457, 1], [123458, 2]],
        )

        # Verificar
        assert result["success"] is True
        taiga_client_mock.bulk_update_backlog_order.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_update_kanban_order_tool_is_registered(self, mcp_server) -> None:
        """US-010: Test that bulk_update_kanban_order tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "bulk_update_kanban_order")

    @pytest.mark.asyncio
    async def test_bulk_update_kanban_order(self, mcp_server, taiga_client_mock) -> None:
        """US-010: Test reordering user stories in kanban."""
        # Configurar mock
        taiga_client_mock.bulk_update_kanban_order.return_value = {"success": True}

        # Ejecutar
        result = await mcp_server.userstory_tools.bulk_update_kanban_order(
            auth_token="valid_token",
            project_id=309804,
            bulk_stories=[[123456, 0], [123457, 1]],
            status=2,
        )

        # Verificar
        assert result["success"] is True
        taiga_client_mock.bulk_update_kanban_order.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_update_sprint_order_tool_is_registered(self, mcp_server) -> None:
        """US-011: Test that bulk_update_sprint_order tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "bulk_update_sprint_order")

    @pytest.mark.asyncio
    async def test_bulk_update_sprint_order(self, mcp_server, taiga_client_mock) -> None:
        """US-011: Test reordering user stories in sprint."""
        # Configurar mock
        taiga_client_mock.bulk_update_sprint_order.return_value = {"success": True}

        # Ejecutar
        result = await mcp_server.userstory_tools.bulk_update_sprint_order(
            auth_token="valid_token",
            project_id=309804,
            milestone_id=5678,
            bulk_stories=[[123456, 0], [123457, 1]],
        )

        # Verificar
        assert result["success"] is True
        taiga_client_mock.bulk_update_sprint_order.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_userstory_filters_tool_is_registered(self, mcp_server) -> None:
        """US-013: Test that get_userstory_filters tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "get_userstory_filters")

    @pytest.mark.asyncio
    async def test_get_userstory_filters(self, mcp_server, taiga_client_mock) -> None:
        """US-013: Test getting available user story filters."""
        # Configurar mock
        taiga_client_mock.get_userstory_filters.return_value = {
            "statuses": [
                {"id": 1, "name": "New"},
                {"id": 2, "name": "In Progress"},
                {"id": 3, "name": "Ready for test"},
                {"id": 4, "name": "Closed"},
            ],
            "assigned_users": [
                {"id": 888691, "username": "usuario1"},
                {"id": 999999, "username": "usuario2"},
            ],
            "tags": ["backend", "frontend", "bug", "feature"],
            "milestones": [{"id": 5678, "name": "Sprint 1"}, {"id": 5679, "name": "Sprint 2"}],
        }

        # Ejecutar
        result = await mcp_server.userstory_tools.get_userstory_filters(
            auth_token="valid_token", project=309804
        )

        # Verificar
        assert "statuses" in result
        assert "milestones" in result
        assert len(result["statuses"]) == 4
        assert len(result["milestones"]) == 2
        taiga_client_mock.get_userstory_filters.assert_called_once_with(project=309804)

    @pytest.mark.asyncio
    async def test_get_userstory_watchers_tool_is_registered(self, mcp_server) -> None:
        """US-019: Test that get_userstory_watchers tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "get_userstory_watchers")

    @pytest.mark.asyncio
    async def test_get_userstory_watchers(self, mcp_server, taiga_client_mock) -> None:
        """US-019: Test getting watchers of a user story."""
        # Configurar mock
        taiga_client_mock.get_userstory_watchers.return_value = [
            {"id": 888691, "username": "usuario1", "full_name": "Usuario Uno"},
            {"id": 999999, "username": "usuario2", "full_name": "Usuario Dos"},
            {"id": 777777, "username": "usuario3", "full_name": "Usuario Tres"},
        ]

        # Ejecutar
        result = await mcp_server.userstory_tools.get_userstory_watchers(
            auth_token="valid_token", userstory_id=123456
        )

        # Verificar
        assert len(result) == 3
        assert result[0]["username"] == "usuario1"
        assert result[2]["username"] == "usuario3"
        taiga_client_mock.get_userstory_watchers.assert_called_once_with(userstory_id=123456)
