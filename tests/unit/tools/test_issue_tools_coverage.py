"""
Tests adicionales para issue_tools.py para alcanzar >= 90% de cobertura.

Cubre:
- Herramientas registradas vía @self.mcp.tool() en register_tools()
- ValidationError handlers
- Ramas de auto_paginate
- Exception handlers en métodos directos
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.application.tools.issue_tools import IssueTools
from src.domain.exceptions import ValidationError


@pytest.fixture
def issue_tools_instance():
    """Fixture que crea una instancia de IssueTools con mock del cliente."""
    mcp = FastMCP("Test")
    with patch("src.application.tools.issue_tools.TaigaAPIClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        tools = IssueTools(mcp)
        tools.register_tools()
        tools._mock_client = mock_client
        tools._mock_client_cls = mock_client_cls

        yield tools


class TestListIssuesRegisteredTool:
    """Tests para la herramienta list_issues registrada."""

    @pytest.mark.asyncio
    async def test_list_issues_registered_tool_success(self, issue_tools_instance):
        """Verifica list_issues registrada con auto_paginate=True."""
        paginator_mock = MagicMock()
        paginator_mock.paginate = AsyncMock(
            return_value=[
                {"id": 1, "ref": 1, "subject": "Test Issue"},
                {"id": 2, "ref": 2, "subject": "Another Issue"},
            ]
        )

        with patch(
            "src.application.tools.issue_tools.AutoPaginator", return_value=paginator_mock
        ):
            # Acceder a la herramienta registrada
            tools = await issue_tools_instance.mcp.get_tools()
            list_issues_tool = tools["taiga_list_issues"]

            result = await list_issues_tool.fn(auth_token="token", project_id=123)

            assert len(result) == 2
            paginator_mock.paginate.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_issues_registered_auto_paginate_false(self, issue_tools_instance):
        """Verifica list_issues con auto_paginate=False."""
        paginator_mock = MagicMock()
        paginator_mock.paginate_first_page = AsyncMock(
            return_value=[{"id": 1, "ref": 1, "subject": "Test Issue"}]
        )

        with patch(
            "src.application.tools.issue_tools.AutoPaginator", return_value=paginator_mock
        ):
            tools = await issue_tools_instance.mcp.get_tools()
            list_issues_tool = tools["taiga_list_issues"]

            result = await list_issues_tool.fn(
                auth_token="token", project_id=123, auto_paginate=False
            )

            assert len(result) == 1
            paginator_mock.paginate_first_page.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_issues_with_all_filters(self, issue_tools_instance):
        """Verifica list_issues con todos los filtros posibles."""
        paginator_mock = MagicMock()
        paginator_mock.paginate = AsyncMock(return_value=[])

        with patch(
            "src.application.tools.issue_tools.AutoPaginator", return_value=paginator_mock
        ):
            tools = await issue_tools_instance.mcp.get_tools()
            list_issues_tool = tools["taiga_list_issues"]

            await list_issues_tool.fn(
                auth_token="token",
                project_id=123,
                status=1,
                severity=2,
                priority=3,
                type=1,
                assigned_to=10,
                tags=["bug"],
                is_closed=False,
                exclude_status=4,
                exclude_severity=5,
                exclude_priority=1,
                exclude_type=2,
                exclude_assigned_to=20,
                exclude_tags=["wontfix"],
            )

            paginator_mock.paginate.assert_called_once()


class TestCreateIssueRegisteredTool:
    """Tests para la herramienta create_issue registrada."""

    @pytest.mark.asyncio
    async def test_create_issue_registered_tool_success(self, issue_tools_instance):
        """Verifica create_issue registrada con éxito."""
        issue_tools_instance._mock_client.create_issue = AsyncMock(
            return_value={
                "id": 1,
                "ref": 10,
                "subject": "Test Issue",
                "project": 123,
                "type": 1,
                "priority": 2,
                "severity": 3,
            }
        )

        tools = await issue_tools_instance.mcp.get_tools()
        create_issue_tool = tools["taiga_create_issue"]

        result = await create_issue_tool.fn(
            auth_token="token",
            project_id=123,
            subject="Test Issue",
            type=1,
            priority=2,
            severity=3,
        )

        assert result["id"] == 1
        assert result["subject"] == "Test Issue"

    @pytest.mark.asyncio
    async def test_create_issue_with_all_optional_fields(self, issue_tools_instance):
        """Verifica create_issue con todos los campos opcionales."""
        issue_tools_instance._mock_client.create_issue = AsyncMock(
            return_value={"id": 1, "ref": 10, "subject": "Full Issue"}
        )

        tools = await issue_tools_instance.mcp.get_tools()
        create_issue_tool = tools["taiga_create_issue"]

        await create_issue_tool.fn(
            auth_token="token",
            project_id=123,
            subject="Full Issue",
            type=1,
            priority=2,
            severity=3,
            description="A detailed description",
            status=1,
            assigned_to=10,
            milestone_id=5,
            tags=["bug", "critical"],
            watchers=[1, 2],
            attachments=[],
            blocked_note="Blocked by X",
            is_blocked=True,
            due_date="2024-12-31",
            due_date_reason="End of year deadline",
        )

        issue_tools_instance._mock_client.create_issue.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_issue_validation_error(self, issue_tools_instance):
        """Verifica que ValidationError se convierte en ToolError."""
        with patch(
            "src.application.tools.issue_tools.validate_input",
            side_effect=ValidationError("Invalid issue data"),
        ):
            tools = await issue_tools_instance.mcp.get_tools()
            create_issue_tool = tools["taiga_create_issue"]

            with pytest.raises(ToolError, match="Invalid issue data"):
                await create_issue_tool.fn(
                    auth_token="token",
                    project_id=123,
                    subject="Test",
                    type=1,
                    priority=2,
                    severity=3,
                )


class TestGetIssueRegisteredTool:
    """Tests para la herramienta get_issue registrada."""

    @pytest.mark.asyncio
    async def test_get_issue_registered_tool_success(self, issue_tools_instance):
        """Verifica get_issue registrada con éxito."""
        issue_tools_instance._mock_client.get_issue = AsyncMock(
            return_value={"id": 456, "ref": 10, "subject": "Test Issue"}
        )

        tools = await issue_tools_instance.mcp.get_tools()
        get_issue_tool = tools["taiga_get_issue"]

        result = await get_issue_tool.fn(auth_token="token", issue_id=456)

        assert result["id"] == 456


class TestGetIssueByRefRegisteredTool:
    """Tests para la herramienta get_issue_by_ref registrada."""

    @pytest.mark.asyncio
    async def test_get_issue_by_ref_registered_success(self, issue_tools_instance):
        """Verifica get_issue_by_ref registrada con éxito."""
        issue_tools_instance._mock_client.get_issue_by_ref = AsyncMock(
            return_value={"id": 456, "ref": 10, "project": 123}
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_issue_by_ref"]

        result = await tool.fn(auth_token="token", project_id=123, ref=10)

        assert result["ref"] == 10


class TestUpdateIssueRegisteredTool:
    """Tests para la herramienta update_issue registrada."""

    @pytest.mark.asyncio
    async def test_update_issue_registered_success(self, issue_tools_instance):
        """Verifica update_issue registrada con éxito."""
        issue_tools_instance._mock_client.update_issue = AsyncMock(
            return_value={"id": 456, "subject": "Updated Issue"}
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_issue"]

        result = await tool.fn(auth_token="token", issue_id=456, subject="Updated Issue")

        assert result["subject"] == "Updated Issue"

    @pytest.mark.asyncio
    async def test_update_issue_with_all_fields(self, issue_tools_instance):
        """Verifica update_issue con todos los campos opcionales."""
        issue_tools_instance._mock_client.update_issue = AsyncMock(return_value={"id": 456})

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_issue"]

        await tool.fn(
            auth_token="token",
            issue_id=456,
            subject="Updated",
            description="New description",
            type=2,
            priority=3,
            severity=4,
            status=2,
            assigned_to=15,
            milestone_id=10,
            tags=["updated"],
            blocked_note="New block",
            is_blocked=True,
            due_date="2025-01-15",
            due_date_reason="New deadline",
            version=2,
        )

        issue_tools_instance._mock_client.update_issue.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_issue_validation_error(self, issue_tools_instance):
        """Verifica que ValidationError se convierte en ToolError."""
        with patch(
            "src.application.tools.issue_tools.validate_input",
            side_effect=ValidationError("Invalid update data"),
        ):
            tools = await issue_tools_instance.mcp.get_tools()
            tool = tools["taiga_update_issue"]

            with pytest.raises(ToolError, match="Invalid update data"):
                await tool.fn(auth_token="token", issue_id=456, subject="Test")


class TestDeleteIssueRegisteredTool:
    """Tests para la herramienta delete_issue registrada."""

    @pytest.mark.asyncio
    async def test_delete_issue_registered_success(self, issue_tools_instance):
        """Verifica delete_issue registrada con éxito."""
        issue_tools_instance._mock_client.delete_issue = AsyncMock(return_value=True)

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_issue"]

        result = await tool.fn(auth_token="token", issue_id=456)

        assert result is True


class TestBulkCreateIssuesRegisteredTool:
    """Tests para la herramienta bulk_create_issues registrada."""

    @pytest.mark.asyncio
    async def test_bulk_create_issues_registered_success(self, issue_tools_instance):
        """Verifica bulk_create_issues registrada con éxito."""
        issue_tools_instance._mock_client.bulk_create_issues = AsyncMock(
            return_value=[{"id": 1}, {"id": 2}]
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_create_issues"]

        issues = [
            {"subject": "Issue 1", "type": 1, "priority": 2, "severity": 3},
            {"subject": "Issue 2", "type": 1, "priority": 2, "severity": 3},
        ]

        result = await tool.fn(auth_token="token", project_id=123, issues=issues)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_bulk_create_issues_invalid_project_id(self, issue_tools_instance):
        """Verifica error cuando project_id es inválido."""
        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_create_issues"]

        issues = [{"subject": "Issue 1", "type": 1, "priority": 2, "severity": 3}]

        with pytest.raises(ToolError, match="project_id"):
            await tool.fn(auth_token="token", project_id=0, issues=issues)

    @pytest.mark.asyncio
    async def test_bulk_create_issues_validation_error_in_item(self, issue_tools_instance):
        """Verifica error cuando un issue tiene datos inválidos."""
        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_bulk_create_issues"]

        # Issue sin subject
        issues = [{"type": 1, "priority": 2, "severity": 3}]

        with pytest.raises(ToolError):
            await tool.fn(auth_token="token", project_id=123, issues=issues)


class TestGetIssueFiltersRegisteredTool:
    """Tests para la herramienta get_issue_filters registrada."""

    @pytest.mark.asyncio
    async def test_get_issue_filters_registered_success(self, issue_tools_instance):
        """Verifica get_issue_filters registrada con éxito."""
        issue_tools_instance._mock_client.get_issue_filters = AsyncMock(
            return_value={"statuses": [], "priorities": [], "severities": []}
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_issue_filters"]

        result = await tool.fn(auth_token="token", project_id=123)

        assert "statuses" in result


class TestIssueVotingRegisteredTools:
    """Tests para las herramientas de votación registradas."""

    @pytest.mark.asyncio
    async def test_upvote_issue_registered(self, issue_tools_instance):
        """Verifica upvote_issue registrada."""
        issue_tools_instance._mock_client.upvote_issue = AsyncMock(
            return_value={"id": 456, "total_voters": 5}
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_upvote_issue"]

        result = await tool.fn(auth_token="token", issue_id=456)

        assert result["total_voters"] == 5

    @pytest.mark.asyncio
    async def test_downvote_issue_registered(self, issue_tools_instance):
        """Verifica downvote_issue registrada."""
        issue_tools_instance._mock_client.downvote_issue = AsyncMock(
            return_value={"id": 456, "total_voters": 4}
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_downvote_issue"]

        result = await tool.fn(auth_token="token", issue_id=456)

        assert result["total_voters"] == 4

    @pytest.mark.asyncio
    async def test_get_issue_voters_registered(self, issue_tools_instance):
        """Verifica get_issue_voters registrada."""
        issue_tools_instance._mock_client.get_issue_voters = AsyncMock(
            return_value=[{"id": 1, "username": "user1"}]
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_issue_voters"]

        result = await tool.fn(auth_token="token", issue_id=456)

        assert len(result) == 1


class TestIssueWatchersRegisteredTools:
    """Tests para las herramientas de watchers registradas."""

    @pytest.mark.asyncio
    async def test_watch_issue_registered(self, issue_tools_instance):
        """Verifica watch_issue registrada."""
        issue_tools_instance._mock_client.watch_issue = AsyncMock(
            return_value={"id": 456, "total_watchers": 3}
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_watch_issue"]

        result = await tool.fn(auth_token="token", issue_id=456)

        assert result["total_watchers"] == 3

    @pytest.mark.asyncio
    async def test_unwatch_issue_registered(self, issue_tools_instance):
        """Verifica unwatch_issue registrada."""
        issue_tools_instance._mock_client.unwatch_issue = AsyncMock(
            return_value={"id": 456, "total_watchers": 2}
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_unwatch_issue"]

        result = await tool.fn(auth_token="token", issue_id=456)

        assert result["total_watchers"] == 2

    @pytest.mark.asyncio
    async def test_get_issue_watchers_registered(self, issue_tools_instance):
        """Verifica get_issue_watchers registrada."""
        issue_tools_instance._mock_client.get_issue_watchers = AsyncMock(
            return_value=[{"id": 1, "username": "watcher1"}]
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_issue_watchers"]

        result = await tool.fn(auth_token="token", issue_id=456)

        assert len(result) == 1


class TestIssueAttachmentsRegisteredTools:
    """Tests para las herramientas de attachments registradas."""

    @pytest.mark.asyncio
    async def test_get_issue_attachments_registered(self, issue_tools_instance):
        """Verifica get_issue_attachments registrada."""
        issue_tools_instance._mock_client.get_issue_attachments = AsyncMock(
            return_value=[{"id": 1, "name": "file.pdf"}]
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_issue_attachments"]

        result = await tool.fn(auth_token="token", issue_id=456)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_issue_attachment_registered(self, issue_tools_instance):
        """Verifica create_issue_attachment registrada."""
        issue_tools_instance._mock_client.create_issue_attachment = AsyncMock(
            return_value={"id": 1, "name": "file.pdf", "size": 1024}
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_issue_attachment"]

        result = await tool.fn(
            auth_token="token",
            issue_id=456,
            file=b"content",
            filename="file.pdf",
            description="Test file",
        )

        assert result["name"] == "file.pdf"

    @pytest.mark.asyncio
    async def test_get_issue_attachment_registered(self, issue_tools_instance):
        """Verifica get_issue_attachment registrada."""
        issue_tools_instance._mock_client.get_issue_attachment = AsyncMock(
            return_value={"id": 789, "name": "file.pdf"}
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_issue_attachment"]

        result = await tool.fn(auth_token="token", attachment_id=789)

        assert result["id"] == 789

    @pytest.mark.asyncio
    async def test_update_issue_attachment_registered(self, issue_tools_instance):
        """Verifica update_issue_attachment registrada."""
        issue_tools_instance._mock_client.update_issue_attachment = AsyncMock(
            return_value={"id": 789, "description": "Updated"}
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_issue_attachment"]

        result = await tool.fn(
            auth_token="token",
            attachment_id=789,
            description="Updated",
            is_deprecated=False,
            order=1,
        )

        assert result["description"] == "Updated"

    @pytest.mark.asyncio
    async def test_delete_issue_attachment_registered(self, issue_tools_instance):
        """Verifica delete_issue_attachment registrada."""
        issue_tools_instance._mock_client.delete_issue_attachment = AsyncMock(return_value=True)

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_issue_attachment"]

        result = await tool.fn(auth_token="token", attachment_id=789)

        assert result is True


class TestIssueHistoryRegisteredTools:
    """Tests para las herramientas de historial registradas."""

    @pytest.mark.asyncio
    async def test_get_issue_history_registered(self, issue_tools_instance):
        """Verifica get_issue_history registrada."""
        issue_tools_instance._mock_client.get_issue_history = AsyncMock(
            return_value=[{"id": "abc", "comment": "Test"}]
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_issue_history"]

        result = await tool.fn(auth_token="token", issue_id=456)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_issue_comment_versions_registered(self, issue_tools_instance):
        """Verifica get_issue_comment_versions registrada."""
        issue_tools_instance._mock_client.get_issue_comment_versions = AsyncMock(
            return_value=[{"comment": "v1"}, {"comment": "v2"}]
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_issue_comment_versions"]

        result = await tool.fn(auth_token="token", issue_id=456, comment_id="abc-123")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_edit_issue_comment_registered(self, issue_tools_instance):
        """Verifica edit_issue_comment registrada."""
        issue_tools_instance._mock_client.edit_issue_comment = AsyncMock(
            return_value={"id": "abc", "comment": "Edited"}
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_edit_issue_comment"]

        result = await tool.fn(
            auth_token="token", issue_id=456, comment_id="abc-123", comment="Edited"
        )

        assert result["comment"] == "Edited"

    @pytest.mark.asyncio
    async def test_delete_issue_comment_registered(self, issue_tools_instance):
        """Verifica delete_issue_comment registrada."""
        issue_tools_instance._mock_client.delete_issue_comment = AsyncMock(return_value=True)

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_issue_comment"]

        result = await tool.fn(auth_token="token", issue_id=456, comment_id="abc-123")

        assert result is True

    @pytest.mark.asyncio
    async def test_undelete_issue_comment_registered(self, issue_tools_instance):
        """Verifica undelete_issue_comment registrada."""
        issue_tools_instance._mock_client.undelete_issue_comment = AsyncMock(
            return_value={"id": "abc", "comment": "Restored"}
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_undelete_issue_comment"]

        result = await tool.fn(auth_token="token", issue_id=456, comment_id="abc-123")

        assert result["comment"] == "Restored"


class TestIssueCustomAttributesRegisteredTools:
    """Tests para las herramientas de atributos personalizados registradas."""

    @pytest.mark.asyncio
    async def test_get_issue_custom_attributes_registered(self, issue_tools_instance):
        """Verifica get_issue_custom_attributes registrada."""
        issue_tools_instance._mock_client.get_issue_custom_attributes = AsyncMock(
            return_value=[{"id": 1, "name": "Custom Field"}]
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_get_issue_custom_attributes"]

        result = await tool.fn(auth_token="token", project_id=123)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_issue_custom_attribute_registered(self, issue_tools_instance):
        """Verifica create_issue_custom_attribute registrada."""
        issue_tools_instance._mock_client.create_issue_custom_attribute = AsyncMock(
            return_value={"id": 1, "name": "New Attr", "type": "text"}
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_create_issue_custom_attribute"]

        result = await tool.fn(
            auth_token="token",
            project_id=123,
            name="New Attr",
            description="Description",
            order=1,
            type="text",
        )

        assert result["name"] == "New Attr"

    @pytest.mark.asyncio
    async def test_update_issue_custom_attribute_registered(self, issue_tools_instance):
        """Verifica update_issue_custom_attribute registrada."""
        issue_tools_instance._mock_client.update_issue_custom_attribute = AsyncMock(
            return_value={"id": 789, "name": "Updated Attr"}
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_update_issue_custom_attribute"]

        result = await tool.fn(
            auth_token="token", attribute_id=789, name="Updated Attr", description="New desc"
        )

        assert result["name"] == "Updated Attr"

    @pytest.mark.asyncio
    async def test_delete_issue_custom_attribute_registered(self, issue_tools_instance):
        """Verifica delete_issue_custom_attribute registrada."""
        issue_tools_instance._mock_client.delete_issue_custom_attribute = AsyncMock(
            return_value=True
        )

        tools = await issue_tools_instance.mcp.get_tools()
        tool = tools["taiga_delete_issue_custom_attribute"]

        result = await tool.fn(auth_token="token", attribute_id=789)

        assert result is True


class TestDirectMethodsExceptionHandlers:
    """Tests para exception handlers de métodos directos."""

    @pytest.mark.asyncio
    async def test_list_issues_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en list_issues directo."""
        issue_tools_instance._mock_client.list_issues = AsyncMock(
            side_effect=RuntimeError("API Error")
        )

        with pytest.raises(RuntimeError, match="API Error"):
            await issue_tools_instance.list_issues(auth_token="token", project=123)

    @pytest.mark.asyncio
    async def test_create_issue_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en create_issue directo."""
        issue_tools_instance._mock_client.create_issue = AsyncMock(
            side_effect=RuntimeError("Create failed")
        )

        with pytest.raises(RuntimeError, match="Create failed"):
            await issue_tools_instance.create_issue(
                auth_token="token", project=123, subject="Test"
            )

    @pytest.mark.asyncio
    async def test_get_issue_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en get_issue directo."""
        issue_tools_instance._mock_client.get_issue = AsyncMock(
            side_effect=RuntimeError("Not found")
        )

        with pytest.raises(RuntimeError, match="Not found"):
            await issue_tools_instance.get_issue(auth_token="token", issue_id=999)

    @pytest.mark.asyncio
    async def test_update_issue_direct_validation_error(self, issue_tools_instance):
        """Verifica ValidationError en update_issue directo."""
        with patch(
            "src.application.tools.issue_tools.validate_input",
            side_effect=ValidationError("Validation failed"),
        ), pytest.raises(ValidationError, match="Validation failed"):
            await issue_tools_instance.update_issue(issue_id=456, subject="")

    @pytest.mark.asyncio
    async def test_update_issue_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción genérica en update_issue directo."""
        issue_tools_instance._mock_client.update_issue = AsyncMock(
            side_effect=RuntimeError("Update failed")
        )

        with pytest.raises(RuntimeError, match="Update failed"):
            await issue_tools_instance.update_issue(
                auth_token="token", issue_id=456, subject="Test"
            )

    @pytest.mark.asyncio
    async def test_update_issue_full_direct_validation_error(self, issue_tools_instance):
        """Verifica ValidationError en update_issue_full directo."""
        with patch(
            "src.application.tools.issue_tools.validate_input",
            side_effect=ValidationError("Full validation failed"),
        ), pytest.raises(ValidationError, match="Full validation failed"):
            await issue_tools_instance.update_issue_full(issue_id=456, subject="")

    @pytest.mark.asyncio
    async def test_update_issue_full_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción genérica en update_issue_full directo."""
        issue_tools_instance._mock_client.update_issue_full = AsyncMock(
            side_effect=RuntimeError("Full update failed")
        )

        with pytest.raises(RuntimeError, match="Full update failed"):
            await issue_tools_instance.update_issue_full(
                auth_token="token", issue_id=456, subject="Test"
            )

    @pytest.mark.asyncio
    async def test_delete_issue_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en delete_issue directo."""
        issue_tools_instance._mock_client.delete_issue = AsyncMock(
            side_effect=RuntimeError("Delete failed")
        )

        with pytest.raises(RuntimeError, match="Delete failed"):
            await issue_tools_instance.delete_issue(auth_token="token", issue_id=456)

    @pytest.mark.asyncio
    async def test_bulk_create_issues_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en bulk_create_issues directo."""
        issue_tools_instance._mock_client.bulk_create_issues = AsyncMock(
            side_effect=RuntimeError("Bulk create failed")
        )

        with pytest.raises(RuntimeError, match="Bulk create failed"):
            await issue_tools_instance.bulk_create_issues(
                auth_token="token", project_id=123, issues=[]
            )

    @pytest.mark.asyncio
    async def test_get_issue_filters_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en get_issue_filters directo."""
        issue_tools_instance._mock_client.get_issue_filters = AsyncMock(
            side_effect=RuntimeError("Filters failed")
        )

        with pytest.raises(RuntimeError, match="Filters failed"):
            await issue_tools_instance.get_issue_filters(auth_token="token", project=123)

    @pytest.mark.asyncio
    async def test_upvote_issue_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en upvote_issue directo."""
        issue_tools_instance._mock_client.upvote_issue = AsyncMock(
            side_effect=RuntimeError("Upvote failed")
        )

        with pytest.raises(RuntimeError, match="Upvote failed"):
            await issue_tools_instance.upvote_issue(auth_token="token", issue_id=456)

    @pytest.mark.asyncio
    async def test_downvote_issue_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en downvote_issue directo."""
        issue_tools_instance._mock_client.downvote_issue = AsyncMock(
            side_effect=RuntimeError("Downvote failed")
        )

        with pytest.raises(RuntimeError, match="Downvote failed"):
            await issue_tools_instance.downvote_issue(auth_token="token", issue_id=456)

    @pytest.mark.asyncio
    async def test_get_issue_voters_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en get_issue_voters directo."""
        issue_tools_instance._mock_client.get_issue_voters = AsyncMock(
            side_effect=RuntimeError("Voters failed")
        )

        with pytest.raises(RuntimeError, match="Voters failed"):
            await issue_tools_instance.get_issue_voters(auth_token="token", issue_id=456)

    @pytest.mark.asyncio
    async def test_watch_issue_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en watch_issue directo."""
        issue_tools_instance._mock_client.watch_issue = AsyncMock(
            side_effect=RuntimeError("Watch failed")
        )

        with pytest.raises(RuntimeError, match="Watch failed"):
            await issue_tools_instance.watch_issue(auth_token="token", issue_id=456)

    @pytest.mark.asyncio
    async def test_unwatch_issue_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en unwatch_issue directo."""
        issue_tools_instance._mock_client.unwatch_issue = AsyncMock(
            side_effect=RuntimeError("Unwatch failed")
        )

        with pytest.raises(RuntimeError, match="Unwatch failed"):
            await issue_tools_instance.unwatch_issue(auth_token="token", issue_id=456)

    @pytest.mark.asyncio
    async def test_get_issue_watchers_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en get_issue_watchers directo."""
        issue_tools_instance._mock_client.get_issue_watchers = AsyncMock(
            side_effect=RuntimeError("Watchers failed")
        )

        with pytest.raises(RuntimeError, match="Watchers failed"):
            await issue_tools_instance.get_issue_watchers(auth_token="token", issue_id=456)


class TestAttachmentMethodsExceptionHandlers:
    """Tests para exception handlers de métodos de attachments."""

    @pytest.mark.asyncio
    async def test_get_issue_attachments_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en get_issue_attachments directo."""
        issue_tools_instance._mock_client.get_issue_attachments = AsyncMock(
            side_effect=RuntimeError("Attachments failed")
        )

        with pytest.raises(RuntimeError, match="Attachments failed"):
            await issue_tools_instance.get_issue_attachments(auth_token="token", issue_id=456)

    @pytest.mark.asyncio
    async def test_list_issue_attachments_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en list_issue_attachments directo."""
        # El método usa list_issue_attachments si existe, sino get_issue_attachments
        issue_tools_instance._mock_client.list_issue_attachments = AsyncMock(
            side_effect=RuntimeError("List attachments failed")
        )

        with pytest.raises(RuntimeError, match="List attachments failed"):
            await issue_tools_instance.list_issue_attachments(auth_token="token", issue_id=456)

    @pytest.mark.asyncio
    async def test_list_issue_attachments_fallback(self, issue_tools_instance):
        """Verifica que list_issue_attachments usa fallback correctamente."""
        # Eliminar el método list_issue_attachments para forzar el fallback
        del issue_tools_instance._mock_client.list_issue_attachments
        issue_tools_instance._mock_client.get_issue_attachments = AsyncMock(
            return_value=[{"id": 1, "name": "file.pdf"}]
        )

        result = await issue_tools_instance.list_issue_attachments(
            auth_token="token", issue_id=456
        )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_issue_attachment_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en create_issue_attachment directo."""
        issue_tools_instance._mock_client.create_issue_attachment = AsyncMock(
            side_effect=RuntimeError("Create attachment failed")
        )

        with pytest.raises(RuntimeError, match="Create attachment failed"):
            await issue_tools_instance.create_issue_attachment(
                auth_token="token", issue_id=456, file=b"content", filename="test.txt"
            )

    @pytest.mark.asyncio
    async def test_get_issue_attachment_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en get_issue_attachment directo."""
        issue_tools_instance._mock_client.get_issue_attachment = AsyncMock(
            side_effect=RuntimeError("Get attachment failed")
        )

        with pytest.raises(RuntimeError, match="Get attachment failed"):
            await issue_tools_instance.get_issue_attachment(auth_token="token", attachment_id=789)

    @pytest.mark.asyncio
    async def test_update_issue_attachment_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en update_issue_attachment directo."""
        issue_tools_instance._mock_client.update_issue_attachment = AsyncMock(
            side_effect=RuntimeError("Update attachment failed")
        )

        with pytest.raises(RuntimeError, match="Update attachment failed"):
            await issue_tools_instance.update_issue_attachment(
                auth_token="token", attachment_id=789, description="New"
            )

    @pytest.mark.asyncio
    async def test_delete_issue_attachment_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en delete_issue_attachment directo."""
        issue_tools_instance._mock_client.delete_issue_attachment = AsyncMock(
            side_effect=RuntimeError("Delete attachment failed")
        )

        with pytest.raises(RuntimeError, match="Delete attachment failed"):
            await issue_tools_instance.delete_issue_attachment(
                auth_token="token", attachment_id=789
            )


class TestHistoryMethodsExceptionHandlers:
    """Tests para exception handlers de métodos de historial."""

    @pytest.mark.asyncio
    async def test_get_issue_history_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en get_issue_history directo."""
        issue_tools_instance._mock_client.get_issue_history = AsyncMock(
            side_effect=RuntimeError("History failed")
        )

        with pytest.raises(RuntimeError, match="History failed"):
            await issue_tools_instance.get_issue_history(auth_token="token", issue_id=456)

    @pytest.mark.asyncio
    async def test_get_issue_comment_versions_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en get_issue_comment_versions directo."""
        issue_tools_instance._mock_client.get_issue_comment_versions = AsyncMock(
            side_effect=RuntimeError("Comment versions failed")
        )

        with pytest.raises(RuntimeError, match="Comment versions failed"):
            await issue_tools_instance.get_issue_comment_versions(
                auth_token="token", issue_id=456, comment_id="abc"
            )

    @pytest.mark.asyncio
    async def test_edit_issue_comment_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en edit_issue_comment directo."""
        issue_tools_instance._mock_client.edit_issue_comment = AsyncMock(
            side_effect=RuntimeError("Edit comment failed")
        )

        with pytest.raises(RuntimeError, match="Edit comment failed"):
            await issue_tools_instance.edit_issue_comment(
                auth_token="token", issue_id=456, comment_id="abc", comment="New"
            )

    @pytest.mark.asyncio
    async def test_delete_issue_comment_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en delete_issue_comment directo."""
        issue_tools_instance._mock_client.delete_issue_comment = AsyncMock(
            side_effect=RuntimeError("Delete comment failed")
        )

        with pytest.raises(RuntimeError, match="Delete comment failed"):
            await issue_tools_instance.delete_issue_comment(
                auth_token="token", issue_id=456, comment_id="abc"
            )

    @pytest.mark.asyncio
    async def test_undelete_issue_comment_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en undelete_issue_comment directo."""
        issue_tools_instance._mock_client.undelete_issue_comment = AsyncMock(
            side_effect=RuntimeError("Undelete comment failed")
        )

        with pytest.raises(RuntimeError, match="Undelete comment failed"):
            await issue_tools_instance.undelete_issue_comment(
                auth_token="token", issue_id=456, comment_id="abc"
            )


class TestCustomAttributesMethodsExceptionHandlers:
    """Tests para exception handlers de métodos de atributos personalizados."""

    @pytest.mark.asyncio
    async def test_get_issue_custom_attributes_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en get_issue_custom_attributes directo."""
        issue_tools_instance._mock_client.get_issue_custom_attributes = AsyncMock(
            side_effect=RuntimeError("Custom attrs failed")
        )

        with pytest.raises(RuntimeError, match="Custom attrs failed"):
            await issue_tools_instance.get_issue_custom_attributes(auth_token="token", project=123)

    @pytest.mark.asyncio
    async def test_create_issue_custom_attribute_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en create_issue_custom_attribute directo."""
        issue_tools_instance._mock_client.create_issue_custom_attribute = AsyncMock(
            side_effect=RuntimeError("Create custom attr failed")
        )

        with pytest.raises(RuntimeError, match="Create custom attr failed"):
            await issue_tools_instance.create_issue_custom_attribute(
                auth_token="token", project_id=123, name="New Attr"
            )

    @pytest.mark.asyncio
    async def test_update_issue_custom_attribute_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en update_issue_custom_attribute directo."""
        issue_tools_instance._mock_client.update_issue_custom_attribute = AsyncMock(
            side_effect=RuntimeError("Update custom attr failed")
        )

        with pytest.raises(RuntimeError, match="Update custom attr failed"):
            await issue_tools_instance.update_issue_custom_attribute(
                auth_token="token", attribute_id=789, name="Updated"
            )

    @pytest.mark.asyncio
    async def test_list_issue_custom_attributes_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en list_issue_custom_attributes directo."""
        issue_tools_instance._mock_client.list_issue_custom_attributes = AsyncMock(
            side_effect=RuntimeError("List custom attrs failed")
        )

        with pytest.raises(RuntimeError, match="List custom attrs failed"):
            await issue_tools_instance.list_issue_custom_attributes(
                auth_token="token", project=123
            )

    @pytest.mark.asyncio
    async def test_list_issue_custom_attributes_fallback(self, issue_tools_instance):
        """Verifica que list_issue_custom_attributes usa fallback."""
        del issue_tools_instance._mock_client.list_issue_custom_attributes
        issue_tools_instance._mock_client.get_issue_custom_attributes = AsyncMock(
            return_value=[{"id": 1, "name": "Attr"}]
        )

        result = await issue_tools_instance.list_issue_custom_attributes(
            auth_token="token", project=123
        )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_issue_custom_attribute_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en get_issue_custom_attribute directo."""
        issue_tools_instance._mock_client.get_issue_custom_attribute = AsyncMock(
            side_effect=RuntimeError("Get custom attr failed")
        )

        with pytest.raises(RuntimeError, match="Get custom attr failed"):
            await issue_tools_instance.get_issue_custom_attribute(
                auth_token="token", attribute_id=789
            )

    @pytest.mark.asyncio
    async def test_delete_issue_custom_attribute_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en delete_issue_custom_attribute directo."""
        issue_tools_instance._mock_client.delete_issue_custom_attribute = AsyncMock(
            side_effect=RuntimeError("Delete custom attr failed")
        )

        with pytest.raises(RuntimeError, match="Delete custom attr failed"):
            await issue_tools_instance.delete_issue_custom_attribute(
                auth_token="token", attribute_id=789
            )


class TestGetIssueByRefDirectMethod:
    """Tests para el método get_issue_by_ref directo."""

    @pytest.mark.asyncio
    async def test_get_issue_by_ref_direct_success(self, issue_tools_instance):
        """Verifica get_issue_by_ref directo con éxito."""
        issue_tools_instance._mock_client.get_issue_by_ref = AsyncMock(
            return_value={"id": 456, "ref": 10, "project": 123}
        )

        result = await issue_tools_instance.get_issue_by_ref(
            auth_token="token", project=123, ref=10
        )

        assert result["ref"] == 10

    @pytest.mark.asyncio
    async def test_get_issue_by_ref_direct_exception(self, issue_tools_instance):
        """Verifica manejo de excepción en get_issue_by_ref directo."""
        issue_tools_instance._mock_client.get_issue_by_ref = AsyncMock(
            side_effect=RuntimeError("Issue by ref failed")
        )

        with pytest.raises(RuntimeError, match="Issue by ref failed"):
            await issue_tools_instance.get_issue_by_ref(auth_token="token", project=123, ref=10)
