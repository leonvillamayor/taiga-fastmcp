"""
Tests for Epic management tools.
EPIC-001 to EPIC-028: Complete Epic functionality testing.
"""

import pytest


class TestEpicCRUD:
    """Tests for Epic CRUD operations (EPIC-001 to EPIC-007)."""

    @pytest.mark.asyncio
    async def test_list_epics_tool_is_registered(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-001: Test that list_epics tool is registered in MCP server."""
        assert hasattr(mcp_server.epic_tools, "list_epics")

    @pytest.mark.asyncio
    async def test_list_epics_with_valid_token(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-001: Test listing epics with valid auth token."""
        # Configurar mock - AutoPaginator usa client.get() con formato paginado
        taiga_client_mock.get.return_value = [
            {
                "id": 456789,
                "ref": 5,
                "subject": "Autenticación de Usuarios",
                "description": "Epic para toda la funcionalidad de autenticación",
                "status": 1,
                "color": "#A5694F",
                "project": 309804,
                "assigned_to": 888691,
                "owner": 888691,
                "tags": ["auth", "security"],
                "client_requirement": True,
                "team_requirement": False,
                "watchers": [888691],
            },
            {
                "id": 456790,
                "ref": 6,
                "subject": "Panel de Administración",
                "color": "#B83A3A",
                "project": 309804,
            },
        ]

        # Ejecutar herramienta
        result = await mcp_server.epic_tools.list_epics(auth_token="valid_token", project=309804)

        # Verificar
        assert len(result) == 2
        assert result[0]["subject"] == "Autenticación de Usuarios"
        assert result[0]["color"] == "#A5694F"
        # Verify client.get was called (AutoPaginator calls get, not list_epics)
        taiga_client_mock.get.assert_called()

    @pytest.mark.asyncio
    async def test_create_epic_tool_is_registered(self, mcp_server) -> None:
        """EPIC-002: Test that create_epic tool is registered."""
        assert hasattr(mcp_server.epic_tools, "create_epic")

    @pytest.mark.asyncio
    async def test_create_epic_with_valid_data(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-002: Test creating an epic with valid data."""
        # Configurar mock
        taiga_client_mock.create_epic.return_value = {
            "id": 456791,
            "ref": 7,
            "subject": "Nueva Epic de Pagos",
            "description": "Epic para implementar sistema de pagos",
            "color": "#5C9210",
            "project": 309804,
            "assigned_to": 888691,
            "tags": ["payments", "feature"],
        }

        # Ejecutar
        result = await mcp_server.epic_tools.create_epic(
            auth_token="valid_token",
            project=309804,
            subject="Nueva Epic de Pagos",
            description="Epic para implementar sistema de pagos",
            color="#5C9210",
            assigned_to=888691,
            tags=["payments", "feature"],
        )

        # Verificar
        assert result["id"] == 456791
        assert result["subject"] == "Nueva Epic de Pagos"
        assert result["color"] == "#5C9210"
        taiga_client_mock.create_epic.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_epic_tool_is_registered(self, mcp_server) -> None:
        """EPIC-003: Test that get_epic tool is registered."""
        assert hasattr(mcp_server.epic_tools, "get_epic")

    @pytest.mark.asyncio
    async def test_get_epic_by_id(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-003: Test getting an epic by ID."""
        # Configurar mock
        taiga_client_mock.get_epic.return_value = {
            "id": 456789,
            "ref": 5,
            "subject": "Autenticación de Usuarios",
            "description": "Epic completa para autenticación",
            "status": 1,
            "color": "#A5694F",
            "project": 309804,
        }

        # Ejecutar (retorna dict directamente)
        result = await mcp_server.epic_tools.get_epic(auth_token="valid_token", epic_id=456789)

        # Verificar
        assert result["id"] == 456789
        assert result["subject"] == "Autenticación de Usuarios"
        taiga_client_mock.get_epic.assert_called_once_with(456789)

    @pytest.mark.asyncio
    async def test_get_epic_by_ref_tool_is_registered(self, mcp_server) -> None:
        """EPIC-004: Test that get_epic_by_ref tool is registered."""
        assert hasattr(mcp_server.epic_tools, "get_epic_by_ref")

    @pytest.mark.asyncio
    async def test_get_epic_by_ref(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-004: Test getting an epic by reference."""
        # Configurar mock
        taiga_client_mock.get_epic_by_ref.return_value = {
            "id": 456789,
            "ref": 5,
            "subject": "Autenticación de Usuarios",
            "project": 309804,
        }

        # Ejecutar (retorna dict directamente)
        result = await mcp_server.epic_tools.get_epic_by_ref(
            auth_token="valid_token", ref=5, project_id=309804
        )

        # Verificar
        assert result["ref"] == 5
        assert result["project"] == 309804
        taiga_client_mock.get_epic_by_ref.assert_called_once_with(ref=5, project_id=309804)

    @pytest.mark.asyncio
    async def test_update_epic_full_tool_is_registered(self, mcp_server) -> None:
        """EPIC-005: Test that update_epic_full tool is registered."""
        assert hasattr(mcp_server.epic_tools, "update_epic_full")

    @pytest.mark.asyncio
    async def test_update_epic_partial_tool_is_registered(self, mcp_server) -> None:
        """EPIC-006: Test that update_epic tool (PATCH) is registered."""
        assert hasattr(mcp_server.epic_tools, "update_epic")

    @pytest.mark.asyncio
    async def test_update_epic_partial(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-006: Test partial update (PATCH) of an epic."""
        # Configurar mock - update_epic_full se usa cuando hay subject + project + version
        taiga_client_mock.update_epic_full.return_value = {
            "id": 456789,
            "ref": 5,
            "version": 3,
            "subject": "Epic Actualizada",
            "status": 2,
        }

        # Ejecutar (retorna dict directamente) - requiere subject, project y version para PUT
        result = await mcp_server.epic_tools.update_epic(
            auth_token="valid_token",
            epic_id=456789,
            project=1,
            version=2,
            subject="Epic Actualizada",
            status=2,
        )

        # Verificar
        assert result["subject"] == "Epic Actualizada"
        assert result["status"] == 2
        taiga_client_mock.update_epic_full.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_epic_tool_is_registered(self, mcp_server) -> None:
        """EPIC-007: Test that delete_epic tool is registered."""
        assert hasattr(mcp_server.epic_tools, "delete_epic")

    @pytest.mark.asyncio
    async def test_delete_epic(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-007: Test deleting an epic."""
        # Configurar mock
        taiga_client_mock.delete_epic.return_value = {"success": True}

        # Ejecutar (retorna dict con success y message)
        result = await mcp_server.epic_tools.delete_epic(auth_token="valid_token", epic_id=456789)

        # Verificar - delete_epic retorna SuccessResponse con success bool
        assert result["success"] is True
        assert "deleted successfully" in result["message"]
        taiga_client_mock.delete_epic.assert_called_once_with(456789)


class TestEpicUserStories:
    """Tests for Epic-UserStory relationships (EPIC-008 to EPIC-012)."""

    @pytest.mark.asyncio
    async def test_list_epic_related_userstories_tool_is_registered(self, mcp_server) -> None:
        """EPIC-008: Test that list_epic_related_userstories tool is registered."""
        assert hasattr(mcp_server.epic_tools, "list_epic_related_userstories")

    @pytest.mark.asyncio
    async def test_list_epic_related_userstories(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-008: Test listing user stories related to an epic."""
        # Configurar mock
        taiga_client_mock.list_epic_related_userstories.return_value = [
            {
                "id": 123,
                "user_story": {"id": 123456, "ref": 1, "subject": "Login de usuarios", "status": 2},
                "epic": 456789,
                "order": 1,
            },
            {
                "id": 124,
                "user_story": {
                    "id": 123457,
                    "ref": 2,
                    "subject": "Registro de usuarios",
                    "status": 1,
                },
                "epic": 456789,
                "order": 2,
            },
        ]

        # Ejecutar (retorna lista directamente)
        result = await mcp_server.epic_tools.list_epic_related_userstories(
            auth_token="valid_token", epic_id=456789
        )

        # Verificar
        assert len(result) == 2
        assert result[0]["user_story"]["subject"] == "Login de usuarios"
        assert result[1]["user_story"]["subject"] == "Registro de usuarios"
        # La llamada usa epic_id posicionalmente
        taiga_client_mock.list_epic_related_userstories.assert_called_once_with(456789)

    @pytest.mark.asyncio
    async def test_create_epic_related_userstory_tool_is_registered(self, mcp_server) -> None:
        """EPIC-009: Test that create_epic_related_userstory tool is registered."""
        assert hasattr(mcp_server.epic_tools, "create_epic_related_userstory")

    @pytest.mark.asyncio
    async def test_create_epic_related_userstory(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-009: Test relating a user story to an epic."""
        # Configurar mock
        taiga_client_mock.create_epic_related_userstory.return_value = {
            "id": 125,
            "user_story": 123458,
            "epic": 456789,
            "order": 3,
        }

        # Ejecutar
        result = await mcp_server.epic_tools.create_epic_related_userstory(
            auth_token="valid_token", epic_id=456789, user_story=123458, order=3
        )

        # Verificar
        assert result["user_story"] == 123458
        assert result["epic"] == 456789
        taiga_client_mock.create_epic_related_userstory.assert_called_once_with(
            epic_id=456789, user_story=123458, order=3
        )

    @pytest.mark.asyncio
    async def test_get_epic_related_userstory_tool_is_registered(self, mcp_server) -> None:
        """EPIC-010: Test that get_epic_related_userstory tool is registered."""
        assert hasattr(mcp_server.epic_tools, "get_epic_related_userstory")

    @pytest.mark.asyncio
    async def test_update_epic_related_userstory_tool_is_registered(self, mcp_server) -> None:
        """EPIC-011: Test that update_epic_related_userstory tool is registered."""
        assert hasattr(mcp_server.epic_tools, "update_epic_related_userstory")

    @pytest.mark.asyncio
    async def test_delete_epic_related_userstory_tool_is_registered(self, mcp_server) -> None:
        """EPIC-012: Test that delete_epic_related_userstory tool is registered."""
        assert hasattr(mcp_server.epic_tools, "delete_epic_related_userstory")

    @pytest.mark.asyncio
    async def test_delete_epic_related_userstory(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-012: Test removing a user story from an epic."""
        # Configurar mock
        taiga_client_mock.delete_epic_related_userstory.return_value = {"success": True}

        # Ejecutar
        result = await mcp_server.epic_tools.delete_epic_related_userstory(
            auth_token="valid_token", epic_id=456789, userstory_id=123456
        )

        # Verificar
        assert result["success"] is True
        taiga_client_mock.delete_epic_related_userstory.assert_called_once()


class TestEpicBulkOperations:
    """Tests for Epic bulk operations (EPIC-013 to EPIC-014)."""

    @pytest.mark.asyncio
    async def test_bulk_create_epics_tool_is_registered(self, mcp_server) -> None:
        """EPIC-013: Test that bulk_create_epics tool is registered."""
        assert hasattr(mcp_server.epic_tools, "bulk_create_epics")

    @pytest.mark.asyncio
    async def test_bulk_create_epics(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-013: Test creating multiple epics in bulk."""
        # Configurar mock
        taiga_client_mock.bulk_create_epics.return_value = [
            {"id": 456792, "ref": 8, "subject": "Epic 1", "color": "#A5694F"},
            {"id": 456793, "ref": 9, "subject": "Epic 2", "color": "#B83A3A"},
            {"id": 456794, "ref": 10, "subject": "Epic 3", "color": "#5C9210"},
        ]

        # Ejecutar (retorna lista directamente)
        result = await mcp_server.epic_tools.bulk_create_epics(
            auth_token="valid_token",
            project_id=309804,
            bulk_epics=[
                {"subject": "Epic 1", "color": "#A5694F"},
                {"subject": "Epic 2", "color": "#B83A3A"},
                {"subject": "Epic 3", "color": "#5C9210"},
            ],
        )

        # Verificar
        assert len(result) == 3
        assert result[0]["subject"] == "Epic 1"
        assert result[1]["color"] == "#B83A3A"
        taiga_client_mock.bulk_create_epics.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_create_related_userstories_tool_is_registered(self, mcp_server) -> None:
        """EPIC-014: Test that bulk_create_related_userstories tool is registered."""
        assert hasattr(mcp_server.epic_tools, "bulk_create_related_userstories")

    @pytest.mark.asyncio
    async def test_bulk_create_related_userstories(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-014: Test relating multiple user stories to an epic in bulk."""
        # Configurar mock
        taiga_client_mock.bulk_create_related_userstories.return_value = [
            {"id": 126, "user_story": 123459, "epic": 456789},
            {"id": 127, "user_story": 123460, "epic": 456789},
            {"id": 128, "user_story": 123461, "epic": 456789},
        ]

        # Ejecutar (retorna lista directamente)
        result = await mcp_server.epic_tools.bulk_create_related_userstories(
            auth_token="valid_token", epic_id=456789, bulk_userstories=[123459, 123460, 123461]
        )

        # Verificar
        assert len(result) == 3
        assert all(rel["epic"] == 456789 for rel in result)
        taiga_client_mock.bulk_create_related_userstories.assert_called_once()


class TestEpicFilters:
    """Tests for Epic filters (EPIC-015)."""

    @pytest.mark.asyncio
    async def test_get_epic_filters_tool_is_registered(self, mcp_server) -> None:
        """EPIC-015: Test that get_epic_filters tool is registered."""
        assert hasattr(mcp_server.epic_tools, "get_epic_filters")

    @pytest.mark.asyncio
    async def test_get_epic_filters(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-015: Test getting available epic filters."""
        # Configurar mock
        taiga_client_mock.get_epic_filters.return_value = {
            "statuses": [
                {"id": 1, "name": "New"},
                {"id": 2, "name": "Ready"},
                {"id": 3, "name": "In Progress"},
                {"id": 4, "name": "Done"},
            ],
            "assigned_users": [
                {"id": 888691, "username": "usuario1"},
                {"id": 999999, "username": "usuario2"},
            ],
            "tags": ["auth", "payments", "frontend", "backend"],
        }

        # Ejecutar (retorna dict directamente)
        result = await mcp_server.epic_tools.get_epic_filters(
            auth_token="valid_token", project_id=309804
        )

        # Verificar - EpicFiltersResponse uses assigned_to not assigned_users
        assert "statuses" in result
        assert len(result["statuses"]) == 4
        # Note: EpicFiltersResponse has 'assigned_to' field, not 'assigned_users'
        assert "tags" in result
        taiga_client_mock.get_epic_filters.assert_called_once_with(project=309804)


class TestEpicVoting:
    """Tests for Epic voting functionality (EPIC-016 to EPIC-018)."""

    @pytest.mark.asyncio
    async def test_upvote_epic_tool_is_registered(self, mcp_server) -> None:
        """EPIC-016: Test that upvote_epic tool is registered."""
        assert hasattr(mcp_server.epic_tools, "upvote_epic")

    @pytest.mark.asyncio
    async def test_upvote_epic(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-016: Test upvoting an epic."""
        # Configurar mock
        taiga_client_mock.upvote_epic.return_value = {"id": 456789, "total_voters": 5}

        # Ejecutar (retorna SuccessResponse)
        result = await mcp_server.epic_tools.upvote_epic(auth_token="valid_token", epic_id=456789)

        # Verificar - upvote_epic now returns SuccessResponse
        assert result["success"] is True
        assert "upvoted" in result["message"]
        taiga_client_mock.upvote_epic.assert_called_once_with(456789)

    @pytest.mark.asyncio
    async def test_downvote_epic_tool_is_registered(self, mcp_server) -> None:
        """EPIC-017: Test that downvote_epic tool is registered."""
        assert hasattr(mcp_server.epic_tools, "downvote_epic")

    @pytest.mark.asyncio
    async def test_downvote_epic(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-017: Test downvoting an epic."""
        # Configurar mock
        taiga_client_mock.downvote_epic.return_value = {"id": 456789, "total_voters": 3}

        # Ejecutar (retorna SuccessResponse)
        result = await mcp_server.epic_tools.downvote_epic(auth_token="valid_token", epic_id=456789)

        # Verificar - downvote_epic now returns SuccessResponse
        assert result["success"] is True
        assert "downvoted" in result["message"]
        taiga_client_mock.downvote_epic.assert_called_once_with(456789)

    @pytest.mark.asyncio
    async def test_get_epic_voters_tool_is_registered(self, mcp_server) -> None:
        """EPIC-018: Test that get_epic_voters tool is registered."""
        assert hasattr(mcp_server.epic_tools, "get_epic_voters")

    @pytest.mark.asyncio
    async def test_get_epic_voters(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-018: Test getting voters of an epic."""
        # Configurar mock
        taiga_client_mock.get_epic_voters.return_value = [
            {"id": 888691, "username": "usuario1", "full_name": "Usuario Uno"},
            {"id": 999999, "username": "usuario2", "full_name": "Usuario Dos"},
        ]

        # Ejecutar (retorna lista directamente)
        result = await mcp_server.epic_tools.get_epic_voters(
            auth_token="valid_token", epic_id=456789
        )

        # Verificar
        assert len(result) == 2
        assert result[0]["username"] == "usuario1"
        taiga_client_mock.get_epic_voters.assert_called_once_with(456789)


class TestEpicWatchers:
    """Tests for Epic watchers functionality (EPIC-019 to EPIC-021)."""

    @pytest.mark.asyncio
    async def test_watch_epic_tool_is_registered(self, mcp_server) -> None:
        """EPIC-019: Test that watch_epic tool is registered."""
        assert hasattr(mcp_server.epic_tools, "watch_epic")

    @pytest.mark.asyncio
    async def test_watch_epic(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-019: Test watching an epic."""
        # Configurar mock
        taiga_client_mock.watch_epic.return_value = {
            "id": 456789,
            "watchers": [888691, 999999],
            "total_watchers": 2,
        }

        # Ejecutar (retorna SuccessResponse)
        result = await mcp_server.epic_tools.watch_epic(auth_token="valid_token", epic_id=456789)

        # Verificar - watch_epic now returns SuccessResponse
        assert result["success"] is True
        assert "watching" in result["message"]
        taiga_client_mock.watch_epic.assert_called_once_with(456789)

    @pytest.mark.asyncio
    async def test_unwatch_epic_tool_is_registered(self, mcp_server) -> None:
        """EPIC-020: Test that unwatch_epic tool is registered."""
        assert hasattr(mcp_server.epic_tools, "unwatch_epic")

    @pytest.mark.asyncio
    async def test_unwatch_epic(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-020: Test unwatching an epic."""
        # Configurar mock
        taiga_client_mock.unwatch_epic.return_value = {
            "id": 456789,
            "watchers": [888691],
            "total_watchers": 1,
        }

        # Ejecutar (retorna SuccessResponse)
        result = await mcp_server.epic_tools.unwatch_epic(auth_token="valid_token", epic_id=456789)

        # Verificar - unwatch_epic now returns SuccessResponse
        assert result["success"] is True
        assert "watching" in result["message"]
        taiga_client_mock.unwatch_epic.assert_called_once_with(456789)

    @pytest.mark.asyncio
    async def test_get_epic_watchers_tool_is_registered(self, mcp_server) -> None:
        """EPIC-021: Test that get_epic_watchers tool is registered."""
        assert hasattr(mcp_server.epic_tools, "get_epic_watchers")

    @pytest.mark.asyncio
    async def test_get_epic_watchers(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-021: Test getting watchers of an epic."""
        # Configurar mock
        taiga_client_mock.get_epic_watchers.return_value = [
            {"id": 888691, "username": "usuario1", "full_name": "Usuario Uno"}
        ]

        # Ejecutar (retorna lista directamente)
        result = await mcp_server.epic_tools.get_epic_watchers(
            auth_token="valid_token", epic_id=456789
        )

        # Verificar
        assert len(result) == 1
        assert result[0]["username"] == "usuario1"
        taiga_client_mock.get_epic_watchers.assert_called_once_with(456789)


class TestEpicAttachments:
    """Tests for Epic attachments functionality (EPIC-022 to EPIC-026)."""

    @pytest.mark.asyncio
    async def test_list_epic_attachments_tool_is_registered(self, mcp_server) -> None:
        """EPIC-022: Test that list_epic_attachments tool is registered."""
        assert hasattr(mcp_server.epic_tools, "list_epic_attachments")

    @pytest.mark.asyncio
    async def test_list_epic_attachments(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-022: Test listing epic attachments."""
        # Configurar mock
        taiga_client_mock.list_epic_attachments.return_value = [
            {
                "id": 3001,
                "name": "epic_diagram.png",
                "size": 512000,
                "url": "https://example.com/files/epic_diagram.png",
                "description": "Epic architecture diagram",
                "object_id": 456789,
            }
        ]

        # Ejecutar (retorna lista directamente)
        result = await mcp_server.epic_tools.list_epic_attachments(
            auth_token="valid_token", epic_id=456789
        )

        # Verificar
        assert len(result) == 1
        assert result[0]["name"] == "epic_diagram.png"
        taiga_client_mock.list_epic_attachments.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_epic_attachment_tool_is_registered(self, mcp_server) -> None:
        """EPIC-023: Test that create_epic_attachment tool is registered."""
        assert hasattr(mcp_server.epic_tools, "create_epic_attachment")

    @pytest.mark.asyncio
    async def test_get_epic_attachment_tool_is_registered(self, mcp_server) -> None:
        """EPIC-024: Test that get_epic_attachment tool is registered."""
        assert hasattr(mcp_server.epic_tools, "get_epic_attachment")

    @pytest.mark.asyncio
    async def test_update_epic_attachment_tool_is_registered(self, mcp_server) -> None:
        """EPIC-025: Test that update_epic_attachment tool is registered."""
        assert hasattr(mcp_server.epic_tools, "update_epic_attachment")

    @pytest.mark.asyncio
    async def test_delete_epic_attachment_tool_is_registered(self, mcp_server) -> None:
        """EPIC-026: Test that delete_epic_attachment tool is registered."""
        assert hasattr(mcp_server.epic_tools, "delete_epic_attachment")


class TestEpicCustomAttributes:
    """Tests for Epic custom attributes functionality (EPIC-027 to EPIC-028)."""

    @pytest.mark.asyncio
    async def test_list_epic_custom_attributes_tool_is_registered(self, mcp_server) -> None:
        """EPIC-027: Test that list_epic_custom_attributes tool is registered."""
        assert hasattr(mcp_server.epic_tools, "list_epic_custom_attributes")

    @pytest.mark.asyncio
    async def test_list_epic_custom_attributes(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-027: Test listing epic custom attributes."""
        # Configurar mock
        taiga_client_mock.list_epic_custom_attributes.return_value = [
            {
                "id": 1,
                "name": "Business Value",
                "description": "Business value score for the epic",
                "type": "number",
                "order": 1,
                "project": 309804,
            }
        ]

        # Ejecutar
        result = await mcp_server.epic_tools.list_epic_custom_attributes(
            auth_token="valid_token", project_id=309804
        )

        # Verificar
        assert len(result) == 1
        assert result[0]["name"] == "Business Value"
        taiga_client_mock.list_epic_custom_attributes.assert_called_once_with(project=309804)

    @pytest.mark.asyncio
    async def test_create_epic_custom_attribute_tool_is_registered(self, mcp_server) -> None:
        """EPIC-028: Test that create_epic_custom_attribute tool is registered."""
        assert hasattr(mcp_server.epic_tools, "create_epic_custom_attribute")

    @pytest.mark.asyncio
    async def test_create_epic_custom_attribute(self, mcp_server, taiga_client_mock) -> None:
        """EPIC-028: Test creating an epic custom attribute."""
        # Configurar mock
        taiga_client_mock.create_epic_custom_attribute.return_value = {
            "id": 2,
            "name": "ROI Expected",
            "description": "Expected return on investment",
            "type": "dropdown",
            "order": 2,
            "project": 309804,
        }

        # Ejecutar
        result = await mcp_server.epic_tools.create_epic_custom_attribute(
            auth_token="valid_token",
            project_id=309804,
            name="ROI Expected",
            description="Expected return on investment",
            type="dropdown",
            order=2,
        )

        # Verificar
        assert result["id"] == 2
        assert result["name"] == "ROI Expected"
        taiga_client_mock.create_epic_custom_attribute.assert_called_once()
