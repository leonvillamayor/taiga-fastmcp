"""
Tests for Issue management tools.
ISSUE-001 to ISSUE-030: Complete Issue functionality testing.
"""

import pytest


class TestIssueCRUD:
    """Tests for Issue CRUD operations (ISSUE-001 to ISSUE-007)."""

    @pytest.mark.asyncio
    async def test_list_issues_tool_is_registered(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-001: Test that list_issues tool is registered in MCP server."""
        # Verificar que la herramienta está registrada
        assert hasattr(mcp_server.issue_tools, "list_issues")

    @pytest.mark.asyncio
    async def test_list_issues_with_valid_token(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-001: Test listing issues with valid auth token."""
        # Configurar mock
        taiga_client_mock.list_issues.return_value = [
            {
                "id": 789012,
                "ref": 10,
                "subject": "Error en login",
                "type": 1,
                "severity": 2,
                "priority": 3,
                "status": 1,
                "project": 309804,
            },
            {
                "id": 789013,
                "ref": 11,
                "subject": "Bug en formulario",
                "type": 1,
                "severity": 1,
                "priority": 2,
                "status": 2,
                "project": 309804,
            },
        ]

        # Ejecutar herramienta
        result = await mcp_server.issue_tools.list_issues(auth_token="valid_token", project=309804)

        # Verificar
        assert len(result) == 2
        assert result[0]["subject"] == "Error en login"
        assert result[0]["type"] == 1
        taiga_client_mock.list_issues.assert_called_once_with(project=309804)

    @pytest.mark.asyncio
    async def test_list_issues_with_filters(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-001: Test listing issues with various filters."""
        # Configurar mock
        taiga_client_mock.list_issues.return_value = []

        # Test con múltiples filtros
        await mcp_server.issue_tools.list_issues(
            auth_token="valid_token",
            project=309804,
            status=1,
            severity=2,
            priority=3,
            type=1,
            assigned_to=888691,
            tags=["bug", "critical"],
            is_closed=False,
        )

        # Verificar que se pasaron todos los filtros
        taiga_client_mock.list_issues.assert_called_once_with(
            project=309804,
            status=1,
            severity=2,
            priority=3,
            type=1,
            assigned_to=888691,
            tags=["bug", "critical"],
            is_closed=False,
        )

    @pytest.mark.asyncio
    async def test_create_issue_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-002: Test that create_issue tool is registered."""
        assert hasattr(mcp_server.issue_tools, "create_issue")

    @pytest.mark.asyncio
    async def test_create_issue_with_valid_data(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-002: Test creating an issue with valid data."""
        # Configurar mock
        taiga_client_mock.create_issue.return_value = {
            "id": 789014,
            "ref": 12,
            "subject": "Nuevo bug encontrado",
            "description": "Descripción detallada del bug",
            "type": 1,
            "status": 1,
            "priority": 3,
            "severity": 2,
            "project": 309804,
            "assigned_to": 888691,
            "tags": ["bug", "frontend"],
        }

        # Ejecutar
        result = await mcp_server.issue_tools.create_issue(
            auth_token="valid_token",
            project=309804,
            subject="Nuevo bug encontrado",
            description="Descripción detallada del bug",
            type=1,
            status=1,
            priority=3,
            severity=2,
            assigned_to=888691,
            tags=["bug", "frontend"],
        )

        # Verificar
        assert result["id"] == 789014
        assert result["subject"] == "Nuevo bug encontrado"
        taiga_client_mock.create_issue.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_issue_without_required_fields(self, mcp_server) -> None:
        """ISSUE-002: Test creating an issue without required fields fails."""
        with pytest.raises(ValueError, match="project and subject are required"):
            await mcp_server.issue_tools.create_issue(auth_token="valid_token")

    @pytest.mark.asyncio
    async def test_get_issue_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-003: Test that get_issue tool is registered."""
        assert hasattr(mcp_server.issue_tools, "get_issue")

    @pytest.mark.asyncio
    async def test_get_issue_by_id(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-003: Test getting an issue by ID."""
        # Configurar mock
        taiga_client_mock.get_issue.return_value = {
            "id": 789012,
            "ref": 10,
            "subject": "Error en login",
            "description": "Descripción del error",
            "status": 1,
            "type": 1,
            "severity": 2,
            "priority": 3,
            "project": 309804,
        }

        # Ejecutar
        result = await mcp_server.issue_tools.get_issue(auth_token="valid_token", issue_id=789012)

        # Verificar
        assert result["id"] == 789012
        assert result["subject"] == "Error en login"
        taiga_client_mock.get_issue.assert_called_once_with(issue_id=789012)

    @pytest.mark.asyncio
    async def test_get_issue_by_ref_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-004: Test that get_issue_by_ref tool is registered."""
        assert hasattr(mcp_server.issue_tools, "get_issue_by_ref")

    @pytest.mark.asyncio
    async def test_get_issue_by_ref(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-004: Test getting an issue by reference."""
        # Configurar mock
        taiga_client_mock.get_issue_by_ref.return_value = {
            "id": 789012,
            "ref": 10,
            "subject": "Error en login",
            "project": 309804,
        }

        # Ejecutar
        result = await mcp_server.issue_tools.get_issue_by_ref(
            auth_token="valid_token", ref=10, project=309804
        )

        # Verificar
        assert result["ref"] == 10
        assert result["project"] == 309804
        taiga_client_mock.get_issue_by_ref.assert_called_once_with(ref=10, project=309804)

    @pytest.mark.asyncio
    async def test_update_issue_full_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-005: Test that update_issue_full tool is registered."""
        assert hasattr(mcp_server.issue_tools, "update_issue_full")

    @pytest.mark.asyncio
    async def test_update_issue_full(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-005: Test full update (PUT) of an issue."""
        # Configurar mock
        updated_issue = {
            "id": 789012,
            "ref": 10,
            "version": 3,
            "subject": "Error crítico en login",
            "description": "Descripción actualizada completa",
            "status": 3,
            "type": 1,
            "severity": 3,
            "priority": 4,
        }
        taiga_client_mock.update_issue_full.return_value = updated_issue

        # Ejecutar
        result = await mcp_server.issue_tools.update_issue_full(
            auth_token="valid_token",
            issue_id=789012,
            version=2,
            subject="Error crítico en login",
            description="Descripción actualizada completa",
            status=3,
            type=1,
            severity=3,
            priority=4,
        )

        # Verificar
        assert result["subject"] == "Error crítico en login"
        assert result["severity"] == 3
        taiga_client_mock.update_issue_full.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_issue_partial_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-006: Test that update_issue tool (PATCH) is registered."""
        assert hasattr(mcp_server.issue_tools, "update_issue")

    @pytest.mark.asyncio
    async def test_update_issue_partial(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-006: Test partial update (PATCH) of an issue."""
        # Configurar mock
        taiga_client_mock.update_issue.return_value = {
            "id": 789012,
            "ref": 10,
            "version": 3,
            "status": 2,
            "assigned_to": 999999,
        }

        # Ejecutar
        result = await mcp_server.issue_tools.update_issue(
            auth_token="valid_token", issue_id=789012, version=2, status=2, assigned_to=999999
        )

        # Verificar
        assert result["status"] == 2
        assert result["assigned_to"] == 999999
        taiga_client_mock.update_issue.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_issue_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-007: Test that delete_issue tool is registered."""
        assert hasattr(mcp_server.issue_tools, "delete_issue")

    @pytest.mark.asyncio
    async def test_delete_issue(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-007: Test deleting an issue."""
        # Configurar mock
        taiga_client_mock.delete_issue.return_value = {"success": True}

        # Ejecutar
        result = await mcp_server.issue_tools.delete_issue(
            auth_token="valid_token", issue_id=789012
        )

        # Verificar
        assert result["success"] is True
        taiga_client_mock.delete_issue.assert_called_once_with(issue_id=789012)


class TestIssueBulkOperations:
    """Tests for Issue bulk operations (ISSUE-008)."""

    @pytest.mark.asyncio
    async def test_bulk_create_issues_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-008: Test that bulk_create_issues tool is registered."""
        assert hasattr(mcp_server.issue_tools, "bulk_create_issues")

    @pytest.mark.asyncio
    async def test_bulk_create_issues(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-008: Test creating multiple issues in bulk."""
        # Configurar mock
        taiga_client_mock.bulk_create_issues.return_value = [
            {"id": 789015, "ref": 13, "subject": "Bug 1"},
            {"id": 789016, "ref": 14, "subject": "Bug 2"},
            {"id": 789017, "ref": 15, "subject": "Bug 3"},
        ]

        # Ejecutar
        result = await mcp_server.issue_tools.bulk_create_issues(
            auth_token="valid_token",
            project_id=309804,
            bulk_issues=[
                {"subject": "Bug 1", "type": 1, "severity": 2},
                {"subject": "Bug 2", "type": 1, "severity": 1},
                {"subject": "Bug 3", "type": 2, "severity": 3},
            ],
        )

        # Verificar
        assert len(result) == 3
        assert result[0]["subject"] == "Bug 1"
        taiga_client_mock.bulk_create_issues.assert_called_once()


class TestIssueFilters:
    """Tests for Issue filters (ISSUE-009)."""

    @pytest.mark.asyncio
    async def test_get_issue_filters_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-009: Test that get_issue_filters tool is registered."""
        assert hasattr(mcp_server.issue_tools, "get_issue_filters")

    @pytest.mark.asyncio
    async def test_get_issue_filters(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-009: Test getting available issue filters."""
        # Configurar mock
        taiga_client_mock.get_issue_filters.return_value = {
            "statuses": [
                {"id": 1, "name": "New"},
                {"id": 2, "name": "In Progress"},
                {"id": 3, "name": "Ready for test"},
                {"id": 4, "name": "Closed"},
            ],
            "types": [
                {"id": 1, "name": "Bug"},
                {"id": 2, "name": "Question"},
                {"id": 3, "name": "Enhancement"},
            ],
            "severities": [
                {"id": 1, "name": "Wishlist"},
                {"id": 2, "name": "Minor"},
                {"id": 3, "name": "Normal"},
                {"id": 4, "name": "Important"},
                {"id": 5, "name": "Critical"},
            ],
            "priorities": [
                {"id": 1, "name": "Low"},
                {"id": 2, "name": "Normal"},
                {"id": 3, "name": "High"},
            ],
            "assigned_users": [
                {"id": 888691, "username": "usuario1"},
                {"id": 999999, "username": "usuario2"},
            ],
            "tags": ["bug", "critical", "frontend", "backend"],
        }

        # Ejecutar
        result = await mcp_server.issue_tools.get_issue_filters(
            auth_token="valid_token", project=309804
        )

        # Verificar
        assert "statuses" in result
        assert len(result["statuses"]) == 4
        assert "types" in result
        assert "severities" in result
        assert "priorities" in result
        taiga_client_mock.get_issue_filters.assert_called_once_with(project=309804)


class TestIssueVoting:
    """Tests for Issue voting functionality (ISSUE-010 to ISSUE-012)."""

    @pytest.mark.asyncio
    async def test_upvote_issue_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-010: Test that upvote_issue tool is registered."""
        assert hasattr(mcp_server.issue_tools, "upvote_issue")

    @pytest.mark.asyncio
    async def test_upvote_issue(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-010: Test upvoting an issue."""
        # Configurar mock
        taiga_client_mock.upvote_issue.return_value = {"id": 789012, "total_voters": 5}

        # Ejecutar
        result = await mcp_server.issue_tools.upvote_issue(
            auth_token="valid_token", issue_id=789012
        )

        # Verificar
        assert result["total_voters"] == 5
        taiga_client_mock.upvote_issue.assert_called_once_with(issue_id=789012)

    @pytest.mark.asyncio
    async def test_downvote_issue_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-011: Test that downvote_issue tool is registered."""
        assert hasattr(mcp_server.issue_tools, "downvote_issue")

    @pytest.mark.asyncio
    async def test_downvote_issue(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-011: Test downvoting an issue."""
        # Configurar mock
        taiga_client_mock.downvote_issue.return_value = {"id": 789012, "total_voters": 3}

        # Ejecutar
        result = await mcp_server.issue_tools.downvote_issue(
            auth_token="valid_token", issue_id=789012
        )

        # Verificar
        assert result["total_voters"] == 3
        taiga_client_mock.downvote_issue.assert_called_once_with(issue_id=789012)

    @pytest.mark.asyncio
    async def test_get_issue_voters_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-012: Test that get_issue_voters tool is registered."""
        assert hasattr(mcp_server.issue_tools, "get_issue_voters")

    @pytest.mark.asyncio
    async def test_get_issue_voters(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-012: Test getting voters of an issue."""
        # Configurar mock
        taiga_client_mock.get_issue_voters.return_value = [
            {"id": 888691, "username": "usuario1", "full_name": "Usuario Uno"},
            {"id": 999999, "username": "usuario2", "full_name": "Usuario Dos"},
        ]

        # Ejecutar
        result = await mcp_server.issue_tools.get_issue_voters(
            auth_token="valid_token", issue_id=789012
        )

        # Verificar
        assert len(result) == 2
        assert result[0]["username"] == "usuario1"
        taiga_client_mock.get_issue_voters.assert_called_once_with(issue_id=789012)


class TestIssueWatchers:
    """Tests for Issue watchers functionality (ISSUE-013 to ISSUE-015)."""

    @pytest.mark.asyncio
    async def test_watch_issue_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-013: Test that watch_issue tool is registered."""
        assert hasattr(mcp_server.issue_tools, "watch_issue")

    @pytest.mark.asyncio
    async def test_watch_issue(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-013: Test watching an issue."""
        # Configurar mock
        taiga_client_mock.watch_issue.return_value = {
            "id": 789012,
            "watchers": [888691, 999999],
            "total_watchers": 2,
        }

        # Ejecutar
        result = await mcp_server.issue_tools.watch_issue(auth_token="valid_token", issue_id=789012)

        # Verificar
        assert result["total_watchers"] == 2
        taiga_client_mock.watch_issue.assert_called_once_with(issue_id=789012)

    @pytest.mark.asyncio
    async def test_unwatch_issue_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-014: Test that unwatch_issue tool is registered."""
        assert hasattr(mcp_server.issue_tools, "unwatch_issue")

    @pytest.mark.asyncio
    async def test_unwatch_issue(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-014: Test unwatching an issue."""
        # Configurar mock
        taiga_client_mock.unwatch_issue.return_value = {
            "id": 789012,
            "watchers": [888691],
            "total_watchers": 1,
        }

        # Ejecutar
        result = await mcp_server.issue_tools.unwatch_issue(
            auth_token="valid_token", issue_id=789012
        )

        # Verificar
        assert result["total_watchers"] == 1
        taiga_client_mock.unwatch_issue.assert_called_once_with(issue_id=789012)

    @pytest.mark.asyncio
    async def test_get_issue_watchers_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-015: Test that get_issue_watchers tool is registered."""
        assert hasattr(mcp_server.issue_tools, "get_issue_watchers")

    @pytest.mark.asyncio
    async def test_get_issue_watchers(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-015: Test getting watchers of an issue."""
        # Configurar mock
        taiga_client_mock.get_issue_watchers.return_value = [
            {"id": 888691, "username": "usuario1", "full_name": "Usuario Uno"},
            {"id": 999999, "username": "usuario2", "full_name": "Usuario Dos"},
        ]

        # Ejecutar
        result = await mcp_server.issue_tools.get_issue_watchers(
            auth_token="valid_token", issue_id=789012
        )

        # Verificar
        assert len(result) == 2
        assert result[0]["username"] == "usuario1"
        taiga_client_mock.get_issue_watchers.assert_called_once_with(issue_id=789012)


class TestIssueAttachments:
    """Tests for Issue attachments functionality (ISSUE-016 to ISSUE-020)."""

    @pytest.mark.asyncio
    async def test_list_issue_attachments_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-016: Test that list_issue_attachments tool is registered."""
        assert hasattr(mcp_server.issue_tools, "list_issue_attachments")

    @pytest.mark.asyncio
    async def test_list_issue_attachments(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-016: Test listing issue attachments."""
        # Configurar mock
        taiga_client_mock.list_issue_attachments.return_value = [
            {
                "id": 1001,
                "name": "screenshot.png",
                "size": 102400,
                "url": "https://example.com/files/screenshot.png",
                "description": "Screenshot del error",
                "object_id": 789012,
            }
        ]

        # Ejecutar
        result = await mcp_server.issue_tools.list_issue_attachments(
            auth_token="valid_token", issue_id=789012
        )

        # Verificar
        assert len(result) == 1
        assert result[0]["name"] == "screenshot.png"
        taiga_client_mock.list_issue_attachments.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_issue_attachment_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-017: Test that create_issue_attachment tool is registered."""
        assert hasattr(mcp_server.issue_tools, "create_issue_attachment")

    @pytest.mark.asyncio
    async def test_create_issue_attachment(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-017: Test creating an issue attachment."""
        # Configurar mock
        taiga_client_mock.create_issue_attachment.return_value = {
            "id": 1002,
            "name": "error_log.txt",
            "size": 5000,
            "url": "https://example.com/files/error_log.txt",
            "description": "Log del error",
            "object_id": 789012,
            "project": 309804,
        }

        # Ejecutar
        result = await mcp_server.issue_tools.create_issue_attachment(
            auth_token="valid_token",
            project_id=309804,
            object_id=789012,
            attached_file="@/path/to/error_log.txt",
            description="Log del error",
        )

        # Verificar
        assert result["id"] == 1002
        assert result["name"] == "error_log.txt"
        taiga_client_mock.create_issue_attachment.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_issue_attachment_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-018: Test that get_issue_attachment tool is registered."""
        assert hasattr(mcp_server.issue_tools, "get_issue_attachment")

    @pytest.mark.asyncio
    async def test_get_issue_attachment(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-018: Test getting a specific issue attachment."""
        # Configurar mock
        taiga_client_mock.get_issue_attachment.return_value = {
            "id": 1001,
            "name": "screenshot.png",
            "size": 102400,
            "url": "https://example.com/files/screenshot.png",
            "description": "Screenshot del error",
        }

        # Ejecutar
        result = await mcp_server.issue_tools.get_issue_attachment(
            auth_token="valid_token", attachment_id=1001
        )

        # Verificar
        assert result["id"] == 1001
        assert result["name"] == "screenshot.png"
        taiga_client_mock.get_issue_attachment.assert_called_once_with(attachment_id=1001)

    @pytest.mark.asyncio
    async def test_update_issue_attachment_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-019: Test that update_issue_attachment tool is registered."""
        assert hasattr(mcp_server.issue_tools, "update_issue_attachment")

    @pytest.mark.asyncio
    async def test_update_issue_attachment(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-019: Test updating an issue attachment."""
        # Configurar mock
        taiga_client_mock.update_issue_attachment.return_value = {
            "id": 1001,
            "description": "Screenshot actualizado del error",
        }

        # Ejecutar
        result = await mcp_server.issue_tools.update_issue_attachment(
            auth_token="valid_token",
            attachment_id=1001,
            description="Screenshot actualizado del error",
        )

        # Verificar
        assert result["description"] == "Screenshot actualizado del error"
        taiga_client_mock.update_issue_attachment.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_issue_attachment_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-020: Test that delete_issue_attachment tool is registered."""
        assert hasattr(mcp_server.issue_tools, "delete_issue_attachment")

    @pytest.mark.asyncio
    async def test_delete_issue_attachment(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-020: Test deleting an issue attachment."""
        # Configurar mock
        taiga_client_mock.delete_issue_attachment.return_value = {"success": True}

        # Ejecutar
        result = await mcp_server.issue_tools.delete_issue_attachment(
            auth_token="valid_token", attachment_id=1001
        )

        # Verificar
        assert result["success"] is True
        taiga_client_mock.delete_issue_attachment.assert_called_once_with(attachment_id=1001)


class TestIssueHistory:
    """Tests for Issue history functionality (ISSUE-021 to ISSUE-025)."""

    @pytest.mark.asyncio
    async def test_get_issue_history_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-021: Test that get_issue_history tool is registered."""
        assert hasattr(mcp_server.issue_tools, "get_issue_history")

    @pytest.mark.asyncio
    async def test_get_issue_history(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-021: Test getting issue history."""
        # Configurar mock
        taiga_client_mock.get_issue_history.return_value = [
            {
                "id": "hist123",
                "user": {"username": "usuario", "full_name": "Usuario Completo"},
                "created_at": "2025-01-20T14:30:00Z",
                "type": 1,
                "diff": {"status": ["1", "2"]},
                "comment": "Cambiado a In Progress",
            }
        ]

        # Ejecutar
        result = await mcp_server.issue_tools.get_issue_history(
            auth_token="valid_token", issue_id=789012
        )

        # Verificar
        assert len(result) == 1
        assert result[0]["comment"] == "Cambiado a In Progress"
        taiga_client_mock.get_issue_history.assert_called_once_with(issue_id=789012)

    @pytest.mark.asyncio
    async def test_get_issue_comment_versions_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-022: Test that get_issue_comment_versions tool is registered."""
        assert hasattr(mcp_server.issue_tools, "get_issue_comment_versions")

    @pytest.mark.asyncio
    async def test_get_issue_comment_versions(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-022: Test getting comment versions for an issue."""
        # Configurar mock
        taiga_client_mock.get_issue_comment_versions.return_value = [
            {
                "id": 1,
                "comment": "Versión original del comentario",
                "created_at": "2025-01-20T14:00:00Z",
            },
            {
                "id": 2,
                "comment": "Versión editada del comentario",
                "created_at": "2025-01-20T14:30:00Z",
            },
        ]

        # Ejecutar
        result = await mcp_server.issue_tools.get_issue_comment_versions(
            auth_token="valid_token", issue_id=789012, comment_id="hist123"
        )

        # Verificar
        assert len(result) == 2
        assert result[1]["comment"] == "Versión editada del comentario"
        taiga_client_mock.get_issue_comment_versions.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_issue_comment_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-023: Test that edit_issue_comment tool is registered."""
        assert hasattr(mcp_server.issue_tools, "edit_issue_comment")

    @pytest.mark.asyncio
    async def test_edit_issue_comment(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-023: Test editing an issue comment."""
        # Configurar mock
        taiga_client_mock.edit_issue_comment.return_value = {
            "id": "hist123",
            "comment": "Comentario editado",
            "comment_html": "<p>Comentario editado</p>",
        }

        # Ejecutar
        result = await mcp_server.issue_tools.edit_issue_comment(
            auth_token="valid_token",
            issue_id=789012,
            comment_id="hist123",
            comment="Comentario editado",
        )

        # Verificar
        assert result["comment"] == "Comentario editado"
        taiga_client_mock.edit_issue_comment.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_issue_comment_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-024: Test that delete_issue_comment tool is registered."""
        assert hasattr(mcp_server.issue_tools, "delete_issue_comment")

    @pytest.mark.asyncio
    async def test_delete_issue_comment(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-024: Test deleting an issue comment."""
        # Configurar mock
        taiga_client_mock.delete_issue_comment.return_value = {"success": True}

        # Ejecutar
        result = await mcp_server.issue_tools.delete_issue_comment(
            auth_token="valid_token", issue_id=789012, comment_id="hist123"
        )

        # Verificar
        assert result["success"] is True
        taiga_client_mock.delete_issue_comment.assert_called_once()

    @pytest.mark.asyncio
    async def test_undelete_issue_comment_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-025: Test that undelete_issue_comment tool is registered."""
        assert hasattr(mcp_server.issue_tools, "undelete_issue_comment")

    @pytest.mark.asyncio
    async def test_undelete_issue_comment(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-025: Test restoring a deleted issue comment."""
        # Configurar mock
        taiga_client_mock.undelete_issue_comment.return_value = {
            "id": "hist123",
            "comment": "Comentario restaurado",
            "delete_comment_date": None,
        }

        # Ejecutar
        result = await mcp_server.issue_tools.undelete_issue_comment(
            auth_token="valid_token", issue_id=789012, comment_id="hist123"
        )

        # Verificar
        assert result["comment"] == "Comentario restaurado"
        assert result["delete_comment_date"] is None
        taiga_client_mock.undelete_issue_comment.assert_called_once()


class TestIssueCustomAttributes:
    """Tests for Issue custom attributes functionality (ISSUE-026 to ISSUE-030)."""

    @pytest.mark.asyncio
    async def test_list_issue_custom_attributes_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-026: Test that list_issue_custom_attributes tool is registered."""
        assert hasattr(mcp_server.issue_tools, "list_issue_custom_attributes")

    @pytest.mark.asyncio
    async def test_list_issue_custom_attributes(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-026: Test listing issue custom attributes."""
        # Configurar mock
        taiga_client_mock.list_issue_custom_attributes.return_value = [
            {
                "id": 1,
                "name": "Browser",
                "description": "Browser donde ocurre el issue",
                "type": "text",
                "order": 1,
                "project": 309804,
            }
        ]

        # Ejecutar
        result = await mcp_server.issue_tools.list_issue_custom_attributes(
            auth_token="valid_token", project=309804
        )

        # Verificar
        assert len(result) == 1
        assert result[0]["name"] == "Browser"
        taiga_client_mock.list_issue_custom_attributes.assert_called_once_with(project=309804)

    @pytest.mark.asyncio
    async def test_create_issue_custom_attribute_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-027: Test that create_issue_custom_attribute tool is registered."""
        assert hasattr(mcp_server.issue_tools, "create_issue_custom_attribute")

    @pytest.mark.asyncio
    async def test_create_issue_custom_attribute(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-027: Test creating an issue custom attribute."""
        # Configurar mock
        taiga_client_mock.create_issue_custom_attribute.return_value = {
            "id": 2,
            "name": "Environment",
            "description": "Environment donde se detectó",
            "type": "dropdown",
            "order": 2,
            "project": 309804,
        }

        # Ejecutar
        result = await mcp_server.issue_tools.create_issue_custom_attribute(
            auth_token="valid_token",
            project_id=309804,
            name="Environment",
            description="Environment donde se detectó",
            type="dropdown",
            order=2,
        )

        # Verificar
        assert result["id"] == 2
        assert result["name"] == "Environment"
        taiga_client_mock.create_issue_custom_attribute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_issue_custom_attribute_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-028: Test that get_issue_custom_attribute tool is registered."""
        assert hasattr(mcp_server.issue_tools, "get_issue_custom_attribute")

    @pytest.mark.asyncio
    async def test_update_issue_custom_attribute_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-029: Test that update_issue_custom_attribute tool is registered."""
        assert hasattr(mcp_server.issue_tools, "update_issue_custom_attribute")

    @pytest.mark.asyncio
    async def test_delete_issue_custom_attribute_tool_is_registered(self, mcp_server) -> None:
        """ISSUE-030: Test that delete_issue_custom_attribute tool is registered."""
        assert hasattr(mcp_server.issue_tools, "delete_issue_custom_attribute")

    @pytest.mark.asyncio
    async def test_delete_issue_custom_attribute(self, mcp_server, taiga_client_mock) -> None:
        """ISSUE-030: Test deleting an issue custom attribute."""
        # Configurar mock
        taiga_client_mock.delete_issue_custom_attribute.return_value = {"success": True}

        # Ejecutar
        result = await mcp_server.issue_tools.delete_issue_custom_attribute(
            auth_token="valid_token", attribute_id=1
        )

        # Verificar
        assert result["success"] is True
        taiga_client_mock.delete_issue_custom_attribute.assert_called_once_with(attribute_id=1)
