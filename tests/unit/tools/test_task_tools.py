"""
Tests for Task management tools.
TASK-001 to TASK-026: Complete Task functionality testing.
"""

import pytest


class TestTaskCRUD:
    """Tests for Task CRUD operations (TASK-001 to TASK-007)."""

    @pytest.mark.asyncio
    async def test_list_tasks_tool_is_registered(self, mcp_server, taiga_client_mock) -> None:
        """TASK-001: Test that list_tasks tool is registered in MCP server."""
        assert hasattr(mcp_server.task_tools, "list_tasks")

    @pytest.mark.asyncio
    async def test_list_tasks_with_valid_token(self, mcp_server, taiga_client_mock) -> None:
        """TASK-001: Test listing tasks with valid auth token."""
        # Configurar mock - AutoPaginator calls client.get("/tasks", ...)
        tasks_data = [
            {
                "id": 345678,
                "ref": 20,
                "subject": "Implementar validación de email",
                "description": "Agregar validación de formato de email",
                "status": 2,
                "project": 309804,
                "user_story": 123456,
                "milestone": 5678,
                "assigned_to": 888691,
            },
            {
                "id": 345679,
                "ref": 21,
                "subject": "Crear tests unitarios",
                "status": 1,
                "project": 309804,
                "user_story": 123456,
            },
        ]
        taiga_client_mock.get.return_value = tasks_data

        # Ejecutar herramienta
        result = await mcp_server.task_tools.list_tasks(auth_token="valid_token", project=309804)

        # Verificar
        assert len(result) == 2
        assert result[0]["subject"] == "Implementar validación de email"
        assert result[0]["user_story"] == 123456
        # AutoPaginator calls client.get with endpoint and params
        taiga_client_mock.get.assert_called()

    @pytest.mark.asyncio
    async def test_list_tasks_with_filters(self, mcp_server, taiga_client_mock) -> None:
        """TASK-001: Test listing tasks with various filters."""
        # Configurar mock - AutoPaginator calls client.get("/tasks", ...)
        taiga_client_mock.get.return_value = []

        # Test con múltiples filtros
        result = await mcp_server.task_tools.list_tasks(
            auth_token="valid_token",
            project=309804,
            user_story=123456,
            milestone=5678,
            status=2,
            assigned_to=888691,
            tags=["backend", "validation"],
            is_closed=False,
        )

        # Verificar que se llamó a get con los filtros
        taiga_client_mock.get.assert_called()
        assert result == []

    @pytest.mark.asyncio
    async def test_create_task_tool_is_registered(self, mcp_server) -> None:
        """TASK-002: Test that create_task tool is registered."""
        assert hasattr(mcp_server.task_tools, "create_task")

    @pytest.mark.asyncio
    async def test_create_task_with_valid_data(self, mcp_server, taiga_client_mock) -> None:
        """TASK-002: Test creating a task with valid data."""
        # Configurar mock
        taiga_client_mock.create_task.return_value = {
            "id": 345680,
            "ref": 22,
            "subject": "Nueva tarea de desarrollo",
            "description": "Descripción de la tarea",
            "status": 1,
            "project": 309804,
            "user_story": 123456,
            "assigned_to": 888691,
            "tags": ["backend"],
        }

        # Ejecutar
        result = await mcp_server.task_tools.create_task(
            auth_token="valid_token",
            project=309804,
            user_story=123456,
            subject="Nueva tarea de desarrollo",
            description="Descripción de la tarea",
            status=1,
            assigned_to=888691,
            tags=["backend"],
        )

        # Verificar
        assert result["id"] == 345680
        assert result["subject"] == "Nueva tarea de desarrollo"
        assert result["user_story"] == 123456
        taiga_client_mock.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_task_without_required_fields(self, mcp_server) -> None:
        """TASK-002: Test creating a task without required fields fails."""
        with pytest.raises(ValueError, match="project, user_story and subject are required"):
            await mcp_server.task_tools.create_task(
                auth_token="valid_token",
                project=309804,  # Missing user_story and subject
            )

    @pytest.mark.asyncio
    async def test_get_task_tool_is_registered(self, mcp_server) -> None:
        """TASK-003: Test that get_task tool is registered."""
        assert hasattr(mcp_server.task_tools, "get_task")

    @pytest.mark.asyncio
    async def test_get_task_by_id(self, mcp_server, taiga_client_mock) -> None:
        """TASK-003: Test getting a task by ID."""
        # Configurar mock
        taiga_client_mock.get_task.return_value = {
            "id": 345678,
            "ref": 20,
            "subject": "Implementar validación de email",
            "description": "Agregar validación de formato de email",
            "status": 2,
            "project": 309804,
            "user_story": 123456,
            "milestone": 5678,
        }

        # Ejecutar
        result = await mcp_server.task_tools.get_task(auth_token="valid_token", task_id=345678)

        # Verificar
        assert result["id"] == 345678
        assert result["subject"] == "Implementar validación de email"
        taiga_client_mock.get_task.assert_called_once_with(task_id=345678)

    @pytest.mark.asyncio
    async def test_get_task_by_ref_tool_is_registered(self, mcp_server) -> None:
        """TASK-004: Test that get_task_by_ref tool is registered."""
        assert hasattr(mcp_server.task_tools, "get_task_by_ref")

    @pytest.mark.asyncio
    async def test_get_task_by_ref(self, mcp_server, taiga_client_mock) -> None:
        """TASK-004: Test getting a task by reference."""
        # Configurar mock
        taiga_client_mock.get_task_by_ref.return_value = {
            "id": 345678,
            "ref": 20,
            "subject": "Implementar validación de email",
            "project": 309804,
        }

        # Ejecutar
        result = await mcp_server.task_tools.get_task_by_ref(
            auth_token="valid_token", ref=20, project=309804
        )

        # Verificar
        assert result["ref"] == 20
        assert result["project"] == 309804
        taiga_client_mock.get_task_by_ref.assert_called_once_with(ref=20, project=309804)

    @pytest.mark.asyncio
    async def test_update_task_full_tool_is_registered(self, mcp_server) -> None:
        """TASK-005: Test that update_task_full tool is registered."""
        assert hasattr(mcp_server.task_tools, "update_task_full")

    @pytest.mark.asyncio
    async def test_update_task_full(self, mcp_server, taiga_client_mock) -> None:
        """TASK-005: Test full update (PUT) of a task."""
        # Configurar mock - update_task_full es el método que se llama
        updated_task = {
            "id": 345678,
            "ref": 20,
            "version": 3,
            "subject": "Validación completa de email",
            "description": "Descripción actualizada completa",
            "status": 3,
            "assigned_to": 999999,
        }
        taiga_client_mock.update_task_full.return_value = updated_task

        # Ejecutar
        result = await mcp_server.task_tools.update_task_full(
            auth_token="valid_token",
            task_id=345678,
            version=2,
            subject="Validación completa de email",
            description="Descripción actualizada completa",
            status=3,
            assigned_to=999999,
        )

        # Verificar
        assert result["subject"] == "Validación completa de email"
        assert result["status"] == 3
        taiga_client_mock.update_task_full.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_partial_tool_is_registered(self, mcp_server) -> None:
        """TASK-006: Test that update_task tool (PATCH) is registered."""
        assert hasattr(mcp_server.task_tools, "update_task")

    @pytest.mark.asyncio
    async def test_update_task_partial(self, mcp_server, taiga_client_mock) -> None:
        """TASK-006: Test partial update (PATCH) of a task."""
        # Configurar mock
        taiga_client_mock.update_task.return_value = {
            "id": 345678,
            "ref": 20,
            "version": 3,
            "status": 3,
            "is_closed": True,
        }

        # Ejecutar
        result = await mcp_server.task_tools.update_task(
            auth_token="valid_token", task_id=345678, version=2, status=3, is_closed=True
        )

        # Verificar
        assert result["status"] == 3
        assert result["is_closed"] is True
        taiga_client_mock.update_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_task_tool_is_registered(self, mcp_server) -> None:
        """TASK-007: Test that delete_task tool is registered."""
        assert hasattr(mcp_server.task_tools, "delete_task")

    @pytest.mark.asyncio
    async def test_delete_task(self, mcp_server, taiga_client_mock) -> None:
        """TASK-007: Test deleting a task."""
        # Configurar mock
        taiga_client_mock.delete_task.return_value = {"success": True}

        # Ejecutar
        result = await mcp_server.task_tools.delete_task(auth_token="valid_token", task_id=345678)

        # Verificar
        assert result["success"] is True
        taiga_client_mock.delete_task.assert_called_once_with(task_id=345678)


class TestTaskBulkOperations:
    """Tests for Task bulk operations (TASK-008)."""

    @pytest.mark.asyncio
    async def test_bulk_create_tasks_tool_is_registered(self, mcp_server) -> None:
        """TASK-008: Test that bulk_create_tasks tool is registered."""
        assert hasattr(mcp_server.task_tools, "bulk_create_tasks")

    @pytest.mark.asyncio
    async def test_bulk_create_tasks(self, mcp_server, taiga_client_mock) -> None:
        """TASK-008: Test creating multiple tasks in bulk."""
        # Configurar mock
        taiga_client_mock.bulk_create_tasks.return_value = [
            {"id": 345681, "ref": 23, "subject": "Tarea 1"},
            {"id": 345682, "ref": 24, "subject": "Tarea 2"},
            {"id": 345683, "ref": 25, "subject": "Tarea 3"},
        ]

        # Ejecutar
        result = await mcp_server.task_tools.bulk_create_tasks(
            auth_token="valid_token",
            project_id=309804,
            user_story=123456,
            bulk_tasks=[{"subject": "Tarea 1"}, {"subject": "Tarea 2"}, {"subject": "Tarea 3"}],
        )

        # Verificar
        assert len(result) == 3
        assert result[0]["subject"] == "Tarea 1"
        taiga_client_mock.bulk_create_tasks.assert_called_once()


class TestTaskFilters:
    """Tests for Task filters (TASK-009)."""

    @pytest.mark.asyncio
    async def test_get_task_filters_tool_is_registered(self, mcp_server) -> None:
        """TASK-009: Test that get_task_filters tool is registered."""
        assert hasattr(mcp_server.task_tools, "get_task_filters")

    @pytest.mark.asyncio
    async def test_get_task_filters(self, mcp_server, taiga_client_mock) -> None:
        """TASK-009: Test getting available task filters."""
        # Configurar mock
        taiga_client_mock.get_task_filters.return_value = {
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
            "tags": ["backend", "frontend", "testing"],
            "user_stories": [
                {"id": 123456, "ref": 1, "subject": "Login de usuarios"},
                {"id": 123457, "ref": 2, "subject": "Registro de usuarios"},
            ],
        }

        # Ejecutar
        result = await mcp_server.task_tools.get_task_filters(
            auth_token="valid_token", project=309804
        )

        # Verificar
        assert "statuses" in result
        assert len(result["statuses"]) == 4
        assert "user_stories" in result
        assert "tags" in result
        taiga_client_mock.get_task_filters.assert_called_once_with(project=309804)


class TestTaskVoting:
    """Tests for Task voting functionality (TASK-010 to TASK-012)."""

    @pytest.mark.asyncio
    async def test_upvote_task_tool_is_registered(self, mcp_server) -> None:
        """TASK-010: Test that upvote_task tool is registered."""
        assert hasattr(mcp_server.task_tools, "upvote_task")

    @pytest.mark.asyncio
    async def test_upvote_task(self, mcp_server, taiga_client_mock) -> None:
        """TASK-010: Test upvoting a task."""
        # Configurar mock
        taiga_client_mock.upvote_task.return_value = {"id": 345678, "total_voters": 3}

        # Ejecutar
        result = await mcp_server.task_tools.upvote_task(auth_token="valid_token", task_id=345678)

        # Verificar
        assert result["total_voters"] == 3
        taiga_client_mock.upvote_task.assert_called_once_with(task_id=345678)

    @pytest.mark.asyncio
    async def test_downvote_task_tool_is_registered(self, mcp_server) -> None:
        """TASK-011: Test that downvote_task tool is registered."""
        assert hasattr(mcp_server.task_tools, "downvote_task")

    @pytest.mark.asyncio
    async def test_downvote_task(self, mcp_server, taiga_client_mock) -> None:
        """TASK-011: Test downvoting a task."""
        # Configurar mock
        taiga_client_mock.downvote_task.return_value = {"id": 345678, "total_voters": 1}

        # Ejecutar
        result = await mcp_server.task_tools.downvote_task(auth_token="valid_token", task_id=345678)

        # Verificar
        assert result["total_voters"] == 1
        taiga_client_mock.downvote_task.assert_called_once_with(task_id=345678)

    @pytest.mark.asyncio
    async def test_get_task_voters_tool_is_registered(self, mcp_server) -> None:
        """TASK-012: Test that get_task_voters tool is registered."""
        assert hasattr(mcp_server.task_tools, "get_task_voters")

    @pytest.mark.asyncio
    async def test_get_task_voters(self, mcp_server, taiga_client_mock) -> None:
        """TASK-012: Test getting voters of a task."""
        # Configurar mock
        taiga_client_mock.get_task_voters.return_value = [
            {"id": 888691, "username": "usuario1", "full_name": "Usuario Uno"},
            {"id": 999999, "username": "usuario2", "full_name": "Usuario Dos"},
        ]

        # Ejecutar
        result = await mcp_server.task_tools.get_task_voters(
            auth_token="valid_token", task_id=345678
        )

        # Verificar
        assert len(result) == 2
        assert result[0]["username"] == "usuario1"
        taiga_client_mock.get_task_voters.assert_called_once_with(task_id=345678)


class TestTaskWatchers:
    """Tests for Task watchers functionality (TASK-013 to TASK-015)."""

    @pytest.mark.asyncio
    async def test_watch_task_tool_is_registered(self, mcp_server) -> None:
        """TASK-013: Test that watch_task tool is registered."""
        assert hasattr(mcp_server.task_tools, "watch_task")

    @pytest.mark.asyncio
    async def test_watch_task(self, mcp_server, taiga_client_mock) -> None:
        """TASK-013: Test watching a task."""
        # Configurar mock
        taiga_client_mock.watch_task.return_value = {
            "id": 345678,
            "watchers": [888691, 999999],
            "total_watchers": 2,
        }

        # Ejecutar
        result = await mcp_server.task_tools.watch_task(auth_token="valid_token", task_id=345678)

        # Verificar
        assert result["total_watchers"] == 2
        taiga_client_mock.watch_task.assert_called_once_with(task_id=345678)

    @pytest.mark.asyncio
    async def test_unwatch_task_tool_is_registered(self, mcp_server) -> None:
        """TASK-014: Test that unwatch_task tool is registered."""
        assert hasattr(mcp_server.task_tools, "unwatch_task")

    @pytest.mark.asyncio
    async def test_unwatch_task(self, mcp_server, taiga_client_mock) -> None:
        """TASK-014: Test unwatching a task."""
        # Configurar mock
        taiga_client_mock.unwatch_task.return_value = {
            "id": 345678,
            "watchers": [888691],
            "total_watchers": 1,
        }

        # Ejecutar
        result = await mcp_server.task_tools.unwatch_task(auth_token="valid_token", task_id=345678)

        # Verificar
        assert result["total_watchers"] == 1
        taiga_client_mock.unwatch_task.assert_called_once_with(task_id=345678)

    @pytest.mark.asyncio
    async def test_get_task_watchers_tool_is_registered(self, mcp_server) -> None:
        """TASK-015: Test that get_task_watchers tool is registered."""
        assert hasattr(mcp_server.task_tools, "get_task_watchers")

    @pytest.mark.asyncio
    async def test_get_task_watchers(self, mcp_server, taiga_client_mock) -> None:
        """TASK-015: Test getting watchers of a task."""
        # Configurar mock
        taiga_client_mock.get_task_watchers.return_value = [
            {"id": 888691, "username": "usuario1", "full_name": "Usuario Uno"}
        ]

        # Ejecutar
        result = await mcp_server.task_tools.get_task_watchers(
            auth_token="valid_token", task_id=345678
        )

        # Verificar
        assert len(result) == 1
        assert result[0]["username"] == "usuario1"
        taiga_client_mock.get_task_watchers.assert_called_once_with(task_id=345678)


class TestTaskAttachments:
    """Tests for Task attachments functionality (TASK-016 to TASK-020)."""

    @pytest.mark.asyncio
    async def test_list_task_attachments_tool_is_registered(self, mcp_server) -> None:
        """TASK-016: Test that list_task_attachments tool is registered."""
        assert hasattr(mcp_server.task_tools, "list_task_attachments")

    @pytest.mark.asyncio
    async def test_list_task_attachments(self, mcp_server, taiga_client_mock) -> None:
        """TASK-016: Test listing task attachments."""
        # Configurar mock
        taiga_client_mock.list_task_attachments.return_value = [
            {
                "id": 2001,
                "name": "design.pdf",
                "size": 204800,
                "url": "https://example.com/files/design.pdf",
                "description": "Design document",
                "object_id": 345678,
            }
        ]

        # Ejecutar
        result = await mcp_server.task_tools.list_task_attachments(
            auth_token="valid_token", task_id=345678
        )

        # Verificar
        assert len(result) == 1
        assert result[0]["name"] == "design.pdf"
        taiga_client_mock.list_task_attachments.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_task_attachment_tool_is_registered(self, mcp_server) -> None:
        """TASK-017: Test that create_task_attachment tool is registered."""
        assert hasattr(mcp_server.task_tools, "create_task_attachment")

    @pytest.mark.asyncio
    async def test_create_task_attachment(self, mcp_server, taiga_client_mock) -> None:
        """TASK-017: Test creating a task attachment."""
        # Configurar mock
        taiga_client_mock.create_task_attachment.return_value = {
            "id": 2002,
            "name": "implementation.py",
            "size": 1024,
            "url": "https://example.com/files/implementation.py",
            "description": "Implementation code",
            "object_id": 345678,
            "project": 309804,
        }

        # Ejecutar
        result = await mcp_server.task_tools.create_task_attachment(
            auth_token="valid_token",
            project=309804,
            task_id=345678,
            attached_file="@/path/to/implementation.py",
            description="Implementation code",
        )

        # Verificar
        assert result["id"] == 2002
        assert result["name"] == "implementation.py"
        taiga_client_mock.create_task_attachment.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_task_attachment_tool_is_registered(self, mcp_server) -> None:
        """TASK-018: Test that get_task_attachment tool is registered."""
        assert hasattr(mcp_server.task_tools, "get_task_attachment")

    @pytest.mark.asyncio
    async def test_update_task_attachment_tool_is_registered(self, mcp_server) -> None:
        """TASK-019: Test that update_task_attachment tool is registered."""
        assert hasattr(mcp_server.task_tools, "update_task_attachment")

    @pytest.mark.asyncio
    async def test_delete_task_attachment_tool_is_registered(self, mcp_server) -> None:
        """TASK-020: Test that delete_task_attachment tool is registered."""
        assert hasattr(mcp_server.task_tools, "delete_task_attachment")


class TestTaskHistory:
    """Tests for Task history functionality (TASK-021 to TASK-025)."""

    @pytest.mark.asyncio
    async def test_get_task_history_tool_is_registered(self, mcp_server) -> None:
        """TASK-021: Test that get_task_history tool is registered."""
        assert hasattr(mcp_server.task_tools, "get_task_history")

    @pytest.mark.asyncio
    async def test_get_task_history(self, mcp_server, taiga_client_mock) -> None:
        """TASK-021: Test getting task history."""
        # Configurar mock
        taiga_client_mock.get_task_history.return_value = [
            {
                "id": "hist456",
                "user": {"username": "developer", "full_name": "Developer Name"},
                "created_at": "2025-01-21T10:30:00Z",
                "type": 1,
                "diff": {"status": ["1", "2"]},
                "comment": "Started working on task",
            }
        ]

        # Ejecutar
        result = await mcp_server.task_tools.get_task_history(
            auth_token="valid_token", task_id=345678
        )

        # Verificar
        assert len(result) == 1
        assert result[0]["comment"] == "Started working on task"
        taiga_client_mock.get_task_history.assert_called_once_with(task_id=345678)

    @pytest.mark.asyncio
    async def test_get_task_comment_versions_tool_is_registered(self, mcp_server) -> None:
        """TASK-022: Test that get_task_comment_versions tool is registered."""
        assert hasattr(mcp_server.task_tools, "get_task_comment_versions")

    @pytest.mark.asyncio
    async def test_edit_task_comment_tool_is_registered(self, mcp_server) -> None:
        """TASK-023: Test that edit_task_comment tool is registered."""
        assert hasattr(mcp_server.task_tools, "edit_task_comment")

    @pytest.mark.asyncio
    async def test_delete_task_comment_tool_is_registered(self, mcp_server) -> None:
        """TASK-024: Test that delete_task_comment tool is registered."""
        assert hasattr(mcp_server.task_tools, "delete_task_comment")

    @pytest.mark.asyncio
    async def test_undelete_task_comment_tool_is_registered(self, mcp_server) -> None:
        """TASK-025: Test that undelete_task_comment tool is registered."""
        assert hasattr(mcp_server.task_tools, "undelete_task_comment")


class TestTaskCustomAttributes:
    """Tests for Task custom attributes functionality (TASK-026)."""

    @pytest.mark.asyncio
    async def test_list_task_custom_attributes_tool_is_registered(self, mcp_server) -> None:
        """TASK-026: Test that list_task_custom_attributes tool is registered."""
        assert hasattr(mcp_server.task_tools, "list_task_custom_attributes")

    @pytest.mark.asyncio
    async def test_list_task_custom_attributes(self, mcp_server, taiga_client_mock) -> None:
        """TASK-026: Test listing task custom attributes."""
        # Configurar mock
        taiga_client_mock.list_task_custom_attributes.return_value = [
            {
                "id": 1,
                "name": "Estimated Hours",
                "description": "Estimated hours for task completion",
                "type": "number",
                "order": 1,
                "project": 309804,
            }
        ]

        # Ejecutar
        result = await mcp_server.task_tools.list_task_custom_attributes(
            auth_token="valid_token", project=309804
        )

        # Verificar
        assert len(result) == 1
        assert result[0]["name"] == "Estimated Hours"
        taiga_client_mock.list_task_custom_attributes.assert_called_once_with(project=309804)

    @pytest.mark.asyncio
    async def test_create_task_custom_attribute_tool_is_registered(self, mcp_server) -> None:
        """TASK-026: Test that create_task_custom_attribute tool is registered."""
        assert hasattr(mcp_server.task_tools, "create_task_custom_attribute")

    @pytest.mark.asyncio
    async def test_update_task_custom_attribute_tool_is_registered(self, mcp_server) -> None:
        """TASK-026: Test that update_task_custom_attribute tool is registered."""
        assert hasattr(mcp_server.task_tools, "update_task_custom_attribute")

    @pytest.mark.asyncio
    async def test_delete_task_custom_attribute_tool_is_registered(self, mcp_server) -> None:
        """TASK-026: Test that delete_task_custom_attribute tool is registered."""
        assert hasattr(mcp_server.task_tools, "delete_task_custom_attribute")
