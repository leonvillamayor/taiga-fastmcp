"""
Tests adicionales para cobertura de task_tools.py.
Cubre herramientas registradas, ValidationError handlers, exception paths y branches.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.application.tools.task_tools import TaskTools
from src.domain.exceptions import ValidationError


@pytest.fixture
def task_tools_instance():
    """Fixture que crea una instancia de TaskTools con mocks."""
    mcp = FastMCP("Test")
    with patch("src.application.tools.task_tools.TaigaAPIClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client
        tools = TaskTools(mcp)
        tools._mock_client = mock_client
        tools._mock_client_cls = mock_client_cls
        yield tools


class TestListTasksRegisteredTool:
    """Tests para la herramienta registrada list_tasks."""

    @pytest.mark.asyncio
    async def test_list_tasks_registered_tool_success(self, task_tools_instance):
        """Verifica list_tasks registrada con éxito."""
        paginator_mock = MagicMock()
        paginator_mock.paginate = AsyncMock(return_value=[{"id": 1}, {"id": 2}])

        with patch(
            "src.application.tools.task_tools.AutoPaginator",
            return_value=paginator_mock,
        ):
            tools = await task_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_tasks"]

            result = await tool.fn(auth_token="token", project_id=123)

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_tasks_auto_paginate_false(self, task_tools_instance):
        """Verifica list_tasks con auto_paginate=False."""
        paginator_mock = MagicMock()
        paginator_mock.paginate_first_page = AsyncMock(return_value=[{"id": 1}])

        with patch(
            "src.application.tools.task_tools.AutoPaginator",
            return_value=paginator_mock,
        ):
            tools = await task_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_tasks"]

            result = await tool.fn(
                auth_token="token",
                project_id=123,
                auto_paginate=False,
            )

            assert len(result) == 1
            paginator_mock.paginate_first_page.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tasks_with_all_filters(self, task_tools_instance):
        """Verifica list_tasks con todos los filtros."""
        paginator_mock = MagicMock()
        paginator_mock.paginate = AsyncMock(return_value=[])

        with patch(
            "src.application.tools.task_tools.AutoPaginator",
            return_value=paginator_mock,
        ):
            tools = await task_tools_instance.mcp.get_tools()
            tool = tools["taiga_list_tasks"]

            result = await tool.fn(
                auth_token="token",
                project_id=123,
                user_story_id=456,
                milestone_id=789,
                status=1,
                assigned_to=42,
                tags=["backend"],
                is_closed=False,
                exclude_status=2,
                exclude_assigned_to=99,
                exclude_tags=["deprecated"],
            )

            assert result == []


class TestCreateTaskRegisteredTool:
    """Tests para la herramienta registrada create_task."""

    @pytest.mark.asyncio
    async def test_create_task_registered_success(self, task_tools_instance):
        """Verifica create_task registrada con éxito."""
        task_tools_instance._mock_client.create_task = AsyncMock(
            return_value={"id": 1, "subject": "Test Task"}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_task"]

        result = await tool.fn(
            auth_token="token",
            project_id=123,
            subject="Test Task",
        )

        assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_create_task_with_all_fields(self, task_tools_instance):
        """Verifica create_task con todos los campos opcionales."""
        task_tools_instance._mock_client.create_task = AsyncMock(
            return_value={"id": 1, "subject": "Test Task", "is_blocked": True}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_task"]

        result = await tool.fn(
            auth_token="token",
            project_id=123,
            subject="Test Task",
            description="Description",
            user_story_id=456,
            milestone_id=789,
            status=1,
            assigned_to=42,
            tags=["urgent"],
            is_blocked=True,
            blocked_note="Waiting for dependency",
        )

        assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_create_task_validation_error(self, task_tools_instance):
        """Verifica manejo de ValidationError en create_task."""
        with patch(
            "src.application.tools.task_tools.validate_input",
            side_effect=ValidationError("Invalid data"),
        ):
            tools = await task_tools_instance.mcp.get_tools()
            tool = tools["taiga_create_task"]

            with pytest.raises(ToolError, match="Invalid data"):
                await tool.fn(
                    auth_token="token",
                    project_id=123,
                    subject="Test",
                )


class TestGetTaskRegisteredTool:
    """Tests para la herramienta registrada get_task."""

    @pytest.mark.asyncio
    async def test_get_task_registered_success(self, task_tools_instance):
        """Verifica get_task registrada con éxito."""
        task_tools_instance._mock_client.get_task = AsyncMock(
            return_value={"id": 1, "subject": "Test Task"}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_task"]

        result = await tool.fn(auth_token="token", task_id=1)

        assert result["id"] == 1


class TestGetTaskByRefRegisteredTool:
    """Tests para la herramienta registrada get_task_by_ref."""

    @pytest.mark.asyncio
    async def test_get_task_by_ref_registered_success(self, task_tools_instance):
        """Verifica get_task_by_ref registrada con éxito."""
        task_tools_instance._mock_client.get_task_by_ref = AsyncMock(
            return_value={"id": 1, "ref": 10, "project": 123}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_task_by_ref"]

        result = await tool.fn(auth_token="token", project_id=123, ref=10)

        assert result["ref"] == 10


class TestUpdateTaskFullRegisteredTool:
    """Tests para la herramienta registrada update_task_full."""

    @pytest.mark.asyncio
    async def test_update_task_full_registered_success(self, task_tools_instance):
        """Verifica update_task_full registrada con éxito."""
        task_tools_instance._mock_client.update_task_full = AsyncMock(
            return_value={"id": 1, "subject": "Updated Task"}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_task_full"]

        result = await tool.fn(
            auth_token="token",
            task_id=1,
            subject="Updated Task",
            project_id=123,
        )

        assert result["subject"] == "Updated Task"

    @pytest.mark.asyncio
    async def test_update_task_full_with_all_fields(self, task_tools_instance):
        """Verifica update_task_full con todos los campos."""
        task_tools_instance._mock_client.update_task_full = AsyncMock(
            return_value={"id": 1, "subject": "Updated"}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_task_full"]

        result = await tool.fn(
            auth_token="token",
            task_id=1,
            subject="Updated",
            project_id=123,
            description="New description",
            user_story_id=456,
            milestone_id=789,
            status=2,
            assigned_to=42,
            tags=["done"],
            is_blocked=False,
            blocked_note=None,
        )

        assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_update_task_full_validation_error(self, task_tools_instance):
        """Verifica manejo de ValidationError en update_task_full."""
        with patch(
            "src.application.tools.task_tools.validate_input",
            side_effect=ValidationError("Invalid update"),
        ):
            tools = await task_tools_instance.mcp.get_tools()
            tool = tools["taiga_update_task_full"]

            with pytest.raises(ToolError, match="Invalid update"):
                await tool.fn(
                    auth_token="token",
                    task_id=1,
                    subject="Test",
                    project_id=123,
                )


class TestUpdateTaskPartialRegisteredTool:
    """Tests para la herramienta registrada update_task."""

    @pytest.mark.asyncio
    async def test_update_task_partial_registered_success(self, task_tools_instance):
        """Verifica update_task registrada con éxito."""
        task_tools_instance._mock_client.update_task = AsyncMock(
            return_value={"id": 1, "status": 2}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_task"]

        result = await tool.fn(
            auth_token="token",
            task_id=1,
            status=2,
        )

        assert result["status"] == 2

    @pytest.mark.asyncio
    async def test_update_task_partial_validation_error(self, task_tools_instance):
        """Verifica manejo de ValidationError en update_task."""
        with patch(
            "src.application.tools.task_tools.validate_input",
            side_effect=ValidationError("Invalid patch"),
        ):
            tools = await task_tools_instance.mcp.get_tools()
            tool = tools["taiga_update_task"]

            with pytest.raises(ToolError, match="Invalid patch"):
                await tool.fn(auth_token="token", task_id=1)


class TestDeleteTaskRegisteredTool:
    """Tests para la herramienta registrada delete_task."""

    @pytest.mark.asyncio
    async def test_delete_task_registered_success(self, task_tools_instance):
        """Verifica delete_task registrada con éxito."""
        task_tools_instance._mock_client.delete_task = AsyncMock(
            return_value={"success": True}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_task"]

        result = await tool.fn(auth_token="token", task_id=1)

        assert result["success"] is True


class TestBulkCreateTasksRegisteredTool:
    """Tests para la herramienta registrada bulk_create_tasks."""

    @pytest.mark.asyncio
    async def test_bulk_create_tasks_registered_success(self, task_tools_instance):
        """Verifica bulk_create_tasks registrada con éxito."""
        task_tools_instance._mock_client.bulk_create_tasks = AsyncMock(
            return_value=[{"id": 1}, {"id": 2}, {"id": 3}]
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_create_tasks"]

        result = await tool.fn(
            auth_token="token",
            project_id=123,
            bulk_tasks="Task 1\nTask 2\nTask 3",
        )

        assert len(result) == 3


class TestGetTaskFiltersRegisteredTool:
    """Tests para la herramienta registrada get_task_filters."""

    @pytest.mark.asyncio
    async def test_get_task_filters_registered_success(self, task_tools_instance):
        """Verifica get_task_filters registrada con éxito."""
        task_tools_instance._mock_client.get_task_filters = AsyncMock(
            return_value={"statuses": [{"id": 1}], "tags": ["urgent"]}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_task_filters"]

        result = await tool.fn(auth_token="token", project_id=123)

        assert "statuses" in result


class TestTaskVotingRegisteredTools:
    """Tests para herramientas de votación registradas."""

    @pytest.mark.asyncio
    async def test_upvote_task_registered(self, task_tools_instance):
        """Verifica upvote_task registrada."""
        task_tools_instance._mock_client.upvote_task = AsyncMock(
            return_value={"id": 1, "total_voters": 5}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_upvote_task"]

        result = await tool.fn(auth_token="token", task_id=1)

        assert result["total_voters"] == 5

    @pytest.mark.asyncio
    async def test_downvote_task_registered(self, task_tools_instance):
        """Verifica downvote_task registrada."""
        task_tools_instance._mock_client.downvote_task = AsyncMock(
            return_value={"id": 1, "total_voters": 4}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_downvote_task"]

        result = await tool.fn(auth_token="token", task_id=1)

        assert result["total_voters"] == 4

    @pytest.mark.asyncio
    async def test_get_task_voters_registered(self, task_tools_instance):
        """Verifica get_task_voters registrada."""
        task_tools_instance._mock_client.get_task_voters = AsyncMock(
            return_value=[{"id": 1, "username": "voter1"}]
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_task_voters"]

        result = await tool.fn(auth_token="token", task_id=1)

        assert len(result) == 1


class TestTaskWatchersRegisteredTools:
    """Tests para herramientas de watchers registradas."""

    @pytest.mark.asyncio
    async def test_watch_task_registered(self, task_tools_instance):
        """Verifica watch_task registrada."""
        task_tools_instance._mock_client.watch_task = AsyncMock(
            return_value={"id": 1, "total_watchers": 3}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_watch_task"]

        result = await tool.fn(auth_token="token", task_id=1)

        assert result["total_watchers"] == 3

    @pytest.mark.asyncio
    async def test_unwatch_task_registered(self, task_tools_instance):
        """Verifica unwatch_task registrada."""
        task_tools_instance._mock_client.unwatch_task = AsyncMock(
            return_value={"id": 1, "total_watchers": 2}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_unwatch_task"]

        result = await tool.fn(auth_token="token", task_id=1)

        assert result["total_watchers"] == 2

    @pytest.mark.asyncio
    async def test_get_task_watchers_registered(self, task_tools_instance):
        """Verifica get_task_watchers registrada."""
        task_tools_instance._mock_client.get_task_watchers = AsyncMock(
            return_value=[{"id": 1, "username": "watcher1"}]
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_task_watchers"]

        result = await tool.fn(auth_token="token", task_id=1)

        assert len(result) == 1


class TestTaskAttachmentsRegisteredTools:
    """Tests para herramientas de attachments registradas."""

    @pytest.mark.asyncio
    async def test_list_task_attachments_registered(self, task_tools_instance):
        """Verifica list_task_attachments registrada."""
        task_tools_instance._mock_client.list_task_attachments = AsyncMock(
            return_value=[{"id": 1, "name": "file.pdf"}]
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_list_task_attachments"]

        result = await tool.fn(auth_token="token", project_id=123, task_id=1)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_task_attachment_registered(self, task_tools_instance):
        """Verifica create_task_attachment registrada."""
        task_tools_instance._mock_client.create_task_attachment = AsyncMock(
            return_value={"id": 1, "name": "new_file.pdf"}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_task_attachment"]

        result = await tool.fn(
            auth_token="token",
            project_id=123,
            task_id=1,
            attached_file="/path/to/file.pdf",
            description="Test file",
            is_deprecated=False,
        )

        assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_get_task_attachment_registered(self, task_tools_instance):
        """Verifica get_task_attachment registrada."""
        task_tools_instance._mock_client.get_task_attachment = AsyncMock(
            return_value={"id": 1, "name": "file.pdf", "size": 1024}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_task_attachment"]

        result = await tool.fn(auth_token="token", attachment_id=1)

        assert result["name"] == "file.pdf"

    @pytest.mark.asyncio
    async def test_update_task_attachment_registered(self, task_tools_instance):
        """Verifica update_task_attachment registrada."""
        task_tools_instance._mock_client.update_task_attachment = AsyncMock(
            return_value={"id": 1, "description": "Updated"}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_task_attachment"]

        result = await tool.fn(
            auth_token="token",
            attachment_id=1,
            description="Updated",
            is_deprecated=True,
        )

        assert result["description"] == "Updated"

    @pytest.mark.asyncio
    async def test_delete_task_attachment_registered(self, task_tools_instance):
        """Verifica delete_task_attachment registrada."""
        task_tools_instance._mock_client.delete_task_attachment = AsyncMock(
            return_value=None
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_task_attachment"]

        result = await tool.fn(auth_token="token", attachment_id=1)

        assert result["status"] == "deleted"


class TestTaskHistoryRegisteredTools:
    """Tests para herramientas de historial registradas."""

    @pytest.mark.asyncio
    async def test_get_task_history_registered(self, task_tools_instance):
        """Verifica get_task_history registrada."""
        task_tools_instance._mock_client.get_task_history = AsyncMock(
            return_value=[{"id": "h1", "type": 1, "comment": "Changed status"}]
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_task_history"]

        result = await tool.fn(auth_token="token", task_id=1)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_task_comment_versions_registered(self, task_tools_instance):
        """Verifica get_task_comment_versions registrada."""
        task_tools_instance._mock_client.get_task_comment_versions = AsyncMock(
            return_value=[{"id": "v1", "comment": "Version 1"}]
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_task_comment_versions"]

        result = await tool.fn(auth_token="token", task_id=1, comment_id="c1")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_edit_task_comment_registered(self, task_tools_instance):
        """Verifica edit_task_comment registrada."""
        task_tools_instance._mock_client.edit_task_comment = AsyncMock(
            return_value={"id": "c1", "comment": "Edited comment"}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_edit_task_comment"]

        result = await tool.fn(
            auth_token="token",
            task_id=1,
            comment_id="c1",
            comment="Edited comment",
        )

        assert result["comment"] == "Edited comment"

    @pytest.mark.asyncio
    async def test_delete_task_comment_registered(self, task_tools_instance):
        """Verifica delete_task_comment registrada."""
        task_tools_instance._mock_client.delete_task_comment = AsyncMock(
            return_value=None
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_task_comment"]

        result = await tool.fn(auth_token="token", task_id=1, comment_id="c1")

        assert result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_undelete_task_comment_registered(self, task_tools_instance):
        """Verifica undelete_task_comment registrada."""
        task_tools_instance._mock_client.undelete_task_comment = AsyncMock(
            return_value={"id": "c1", "comment": "Restored comment"}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_undelete_task_comment"]

        result = await tool.fn(auth_token="token", task_id=1, comment_id="c1")

        assert result["comment"] == "Restored comment"


class TestTaskCustomAttributesRegisteredTools:
    """Tests para herramientas de atributos personalizados registradas."""

    @pytest.mark.asyncio
    async def test_list_task_custom_attributes_registered(self, task_tools_instance):
        """Verifica list_task_custom_attributes registrada."""
        task_tools_instance._mock_client.list_task_custom_attributes = AsyncMock(
            return_value=[{"id": 1, "name": "Estimated Hours"}]
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_list_task_custom_attributes"]

        result = await tool.fn(auth_token="token", project_id=123)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_task_custom_attribute_registered(self, task_tools_instance):
        """Verifica create_task_custom_attribute registrada."""
        task_tools_instance._mock_client.create_task_custom_attribute = AsyncMock(
            return_value={"id": 1, "name": "Priority Level", "type": "text"}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_task_custom_attribute"]

        result = await tool.fn(
            auth_token="token",
            project_id=123,
            name="Priority Level",
            description="Priority for tasks",
            field_type="text",
        )

        assert result["name"] == "Priority Level"

    @pytest.mark.asyncio
    async def test_update_task_custom_attribute_registered(self, task_tools_instance):
        """Verifica update_task_custom_attribute registrada."""
        task_tools_instance._mock_client.update_task_custom_attribute = AsyncMock(
            return_value={"id": 1, "name": "Updated Name"}
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_task_custom_attribute"]

        result = await tool.fn(
            auth_token="token",
            attribute_id=1,
            name="Updated Name",
            description="Updated description",
        )

        assert result["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_task_custom_attribute_registered(self, task_tools_instance):
        """Verifica delete_task_custom_attribute registrada."""
        task_tools_instance._mock_client.delete_task_custom_attribute = AsyncMock(
            return_value=None
        )

        tools = await task_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_task_custom_attribute"]

        result = await tool.fn(auth_token="token", attribute_id=1)

        assert result["status"] == "deleted"


class TestDirectMethodsExceptionHandlers:
    """Tests para manejadores de excepciones en métodos directos."""

    @pytest.mark.asyncio
    async def test_list_tasks_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en list_tasks."""
        with patch(
            "src.application.tools.task_tools.AutoPaginator"
        ) as paginator_mock:
            paginator_mock.return_value.paginate = AsyncMock(
                side_effect=Exception("API Error")
            )

            with pytest.raises(Exception, match="API Error"):
                await task_tools_instance.list_tasks(auth_token="token", project=123)

    @pytest.mark.asyncio
    async def test_create_task_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en create_task."""
        task_tools_instance._mock_client.create_task = AsyncMock(
            side_effect=Exception("Create failed")
        )

        with pytest.raises(Exception, match="Create failed"):
            await task_tools_instance.create_task(
                auth_token="token",
                project=123,
                user_story=456,
                subject="Test",
            )

    @pytest.mark.asyncio
    async def test_get_task_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en get_task."""
        task_tools_instance._mock_client.get_task = AsyncMock(
            side_effect=Exception("Not found")
        )

        with pytest.raises(Exception, match="Not found"):
            await task_tools_instance.get_task(auth_token="token", task_id=1)

    @pytest.mark.asyncio
    async def test_get_task_by_ref_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en get_task_by_ref."""
        task_tools_instance._mock_client.get_task_by_ref = AsyncMock(
            side_effect=Exception("Ref not found")
        )

        with pytest.raises(Exception, match="Ref not found"):
            await task_tools_instance.get_task_by_ref(
                auth_token="token", project=123, ref=10
            )

    @pytest.mark.asyncio
    async def test_update_task_full_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en update_task_full."""
        task_tools_instance._mock_client.update_task_full = AsyncMock(
            side_effect=Exception("Update failed")
        )

        with pytest.raises(Exception, match="Update failed"):
            await task_tools_instance.update_task_full(
                auth_token="token",
                task_id=1,
                subject="Test",
            )

    @pytest.mark.asyncio
    async def test_update_task_partial_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en update_task_partial."""
        task_tools_instance._mock_client.update_task = AsyncMock(
            side_effect=Exception("Patch failed")
        )

        with pytest.raises(Exception, match="Patch failed"):
            await task_tools_instance.update_task_partial(
                auth_token="token",
                task_id=1,
                status=2,
            )

    @pytest.mark.asyncio
    async def test_delete_task_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en delete_task."""
        task_tools_instance._mock_client.delete_task = AsyncMock(
            side_effect=Exception("Delete failed")
        )

        with pytest.raises(Exception, match="Delete failed"):
            await task_tools_instance.delete_task(auth_token="token", task_id=1)

    @pytest.mark.asyncio
    async def test_delete_task_returns_non_dict(self, task_tools_instance):
        """Verifica delete_task cuando no retorna dict."""
        task_tools_instance._mock_client.delete_task = AsyncMock(return_value=None)

        result = await task_tools_instance.delete_task(auth_token="token", task_id=1)

        assert "success" in result

    @pytest.mark.asyncio
    async def test_bulk_create_tasks_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en bulk_create_tasks."""
        task_tools_instance._mock_client.bulk_create_tasks = AsyncMock(
            side_effect=Exception("Bulk create failed")
        )

        with pytest.raises(Exception, match="Bulk create failed"):
            await task_tools_instance.bulk_create_tasks(
                auth_token="token",
                project_id=123,
                bulk_tasks="Task1\nTask2",
            )

    @pytest.mark.asyncio
    async def test_get_task_filters_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en get_task_filters."""
        task_tools_instance._mock_client.get_task_filters = AsyncMock(
            side_effect=Exception("Filters failed")
        )

        with pytest.raises(Exception, match="Filters failed"):
            await task_tools_instance.get_task_filters(auth_token="token", project=123)

    @pytest.mark.asyncio
    async def test_upvote_task_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en upvote_task."""
        task_tools_instance._mock_client.upvote_task = AsyncMock(
            side_effect=Exception("Upvote failed")
        )

        with pytest.raises(Exception, match="Upvote failed"):
            await task_tools_instance.upvote_task(auth_token="token", task_id=1)

    @pytest.mark.asyncio
    async def test_downvote_task_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en downvote_task."""
        task_tools_instance._mock_client.downvote_task = AsyncMock(
            side_effect=Exception("Downvote failed")
        )

        with pytest.raises(Exception, match="Downvote failed"):
            await task_tools_instance.downvote_task(auth_token="token", task_id=1)

    @pytest.mark.asyncio
    async def test_get_task_voters_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en get_task_voters."""
        task_tools_instance._mock_client.get_task_voters = AsyncMock(
            side_effect=Exception("Voters failed")
        )

        with pytest.raises(Exception, match="Voters failed"):
            await task_tools_instance.get_task_voters(auth_token="token", task_id=1)

    @pytest.mark.asyncio
    async def test_watch_task_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en watch_task."""
        task_tools_instance._mock_client.watch_task = AsyncMock(
            side_effect=Exception("Watch failed")
        )

        with pytest.raises(Exception, match="Watch failed"):
            await task_tools_instance.watch_task(auth_token="token", task_id=1)

    @pytest.mark.asyncio
    async def test_unwatch_task_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en unwatch_task."""
        task_tools_instance._mock_client.unwatch_task = AsyncMock(
            side_effect=Exception("Unwatch failed")
        )

        with pytest.raises(Exception, match="Unwatch failed"):
            await task_tools_instance.unwatch_task(auth_token="token", task_id=1)

    @pytest.mark.asyncio
    async def test_get_task_watchers_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en get_task_watchers."""
        task_tools_instance._mock_client.get_task_watchers = AsyncMock(
            side_effect=Exception("Watchers failed")
        )

        with pytest.raises(Exception, match="Watchers failed"):
            await task_tools_instance.get_task_watchers(auth_token="token", task_id=1)


class TestAttachmentMethodsExceptionHandlers:
    """Tests para manejadores de excepciones en métodos de attachments."""

    @pytest.mark.asyncio
    async def test_list_task_attachments_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en list_task_attachments."""
        task_tools_instance._mock_client.list_task_attachments = AsyncMock(
            side_effect=Exception("List attachments failed")
        )

        with pytest.raises(Exception, match="List attachments failed"):
            await task_tools_instance.list_task_attachments(
                auth_token="token", task_id=1
            )

    @pytest.mark.asyncio
    async def test_create_task_attachment_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en create_task_attachment."""
        task_tools_instance._mock_client.create_task_attachment = AsyncMock(
            side_effect=Exception("Create attachment failed")
        )

        with pytest.raises(Exception, match="Create attachment failed"):
            await task_tools_instance.create_task_attachment(
                auth_token="token",
                task_id=1,
                attached_file="/path/to/file",
            )

    @pytest.mark.asyncio
    async def test_get_task_attachment_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en get_task_attachment."""
        task_tools_instance._mock_client.get_task_attachment = AsyncMock(
            side_effect=Exception("Get attachment failed")
        )

        with pytest.raises(Exception, match="Get attachment failed"):
            await task_tools_instance.get_task_attachment(
                auth_token="token", attachment_id=1
            )

    @pytest.mark.asyncio
    async def test_update_task_attachment_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en update_task_attachment."""
        task_tools_instance._mock_client.update_task_attachment = AsyncMock(
            side_effect=Exception("Update attachment failed")
        )

        with pytest.raises(Exception, match="Update attachment failed"):
            await task_tools_instance.update_task_attachment(
                auth_token="token",
                attachment_id=1,
                description="New description",
            )

    @pytest.mark.asyncio
    async def test_delete_task_attachment_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en delete_task_attachment."""
        task_tools_instance._mock_client.delete_task_attachment = AsyncMock(
            side_effect=Exception("Delete attachment failed")
        )

        with pytest.raises(Exception, match="Delete attachment failed"):
            await task_tools_instance.delete_task_attachment(
                auth_token="token", attachment_id=1
            )


class TestHistoryMethodsExceptionHandlers:
    """Tests para manejadores de excepciones en métodos de historial."""

    @pytest.mark.asyncio
    async def test_get_task_history_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en get_task_history."""
        task_tools_instance._mock_client.get_task_history = AsyncMock(
            side_effect=Exception("History failed")
        )

        with pytest.raises(Exception, match="History failed"):
            await task_tools_instance.get_task_history(auth_token="token", task_id=1)

    @pytest.mark.asyncio
    async def test_get_task_comment_versions_direct_exception(
        self, task_tools_instance
    ):
        """Verifica manejo de excepciones en get_task_comment_versions."""
        task_tools_instance._mock_client.get_task_comment_versions = AsyncMock(
            side_effect=Exception("Versions failed")
        )

        with pytest.raises(Exception, match="Versions failed"):
            await task_tools_instance.get_task_comment_versions(
                auth_token="token", task_id=1, comment_id="c1"
            )

    @pytest.mark.asyncio
    async def test_edit_task_comment_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en edit_task_comment."""
        task_tools_instance._mock_client.edit_task_comment = AsyncMock(
            side_effect=Exception("Edit comment failed")
        )

        with pytest.raises(Exception, match="Edit comment failed"):
            await task_tools_instance.edit_task_comment(
                auth_token="token",
                task_id=1,
                comment_id="c1",
                comment="New text",
            )

    @pytest.mark.asyncio
    async def test_delete_task_comment_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en delete_task_comment."""
        task_tools_instance._mock_client.delete_task_comment = AsyncMock(
            side_effect=Exception("Delete comment failed")
        )

        with pytest.raises(Exception, match="Delete comment failed"):
            await task_tools_instance.delete_task_comment(
                auth_token="token", task_id=1, comment_id="c1"
            )

    @pytest.mark.asyncio
    async def test_undelete_task_comment_direct_exception(self, task_tools_instance):
        """Verifica manejo de excepciones en undelete_task_comment."""
        task_tools_instance._mock_client.undelete_task_comment = AsyncMock(
            side_effect=Exception("Undelete comment failed")
        )

        with pytest.raises(Exception, match="Undelete comment failed"):
            await task_tools_instance.undelete_task_comment(
                auth_token="token", task_id=1, comment_id="c1"
            )


class TestCustomAttributesMethodsExceptionHandlers:
    """Tests para manejadores de excepciones en métodos de atributos personalizados."""

    @pytest.mark.asyncio
    async def test_list_task_custom_attributes_direct_exception(
        self, task_tools_instance
    ):
        """Verifica manejo de excepciones en list_task_custom_attributes."""
        task_tools_instance._mock_client.list_task_custom_attributes = AsyncMock(
            side_effect=Exception("List attrs failed")
        )

        with pytest.raises(Exception, match="List attrs failed"):
            await task_tools_instance.list_task_custom_attributes(
                auth_token="token", project=123
            )

    @pytest.mark.asyncio
    async def test_create_task_custom_attribute_direct_exception(
        self, task_tools_instance
    ):
        """Verifica manejo de excepciones en create_task_custom_attribute."""
        task_tools_instance._mock_client.create_task_custom_attribute = AsyncMock(
            side_effect=Exception("Create attr failed")
        )

        with pytest.raises(Exception, match="Create attr failed"):
            await task_tools_instance.create_task_custom_attribute(
                auth_token="token",
                project=123,
                name="Test Attr",
            )

    @pytest.mark.asyncio
    async def test_update_task_custom_attribute_direct_exception(
        self, task_tools_instance
    ):
        """Verifica manejo de excepciones en update_task_custom_attribute."""
        task_tools_instance._mock_client.update_task_custom_attribute = AsyncMock(
            side_effect=Exception("Update attr failed")
        )

        with pytest.raises(Exception, match="Update attr failed"):
            await task_tools_instance.update_task_custom_attribute(
                auth_token="token",
                attribute_id=1,
                name="Updated",
            )

    @pytest.mark.asyncio
    async def test_delete_task_custom_attribute_direct_exception(
        self, task_tools_instance
    ):
        """Verifica manejo de excepciones en delete_task_custom_attribute."""
        task_tools_instance._mock_client.delete_task_custom_attribute = AsyncMock(
            side_effect=Exception("Delete attr failed")
        )

        with pytest.raises(Exception, match="Delete attr failed"):
            await task_tools_instance.delete_task_custom_attribute(
                auth_token="token", attribute_id=1
            )
