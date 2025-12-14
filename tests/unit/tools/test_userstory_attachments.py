"""
Tests for User Story attachments functionality.
US-020 to US-024: Complete User Story attachments testing.
"""

import pytest


class TestUserStoryAttachments:
    """Tests for User Story attachments functionality (US-020 to US-024)."""

    @pytest.mark.asyncio
    async def test_list_userstory_attachments_tool_is_registered(self, mcp_server) -> None:
        """US-020: Test that list_userstory_attachments tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "list_userstory_attachments")

    @pytest.mark.asyncio
    async def test_list_userstory_attachments(self, mcp_server, taiga_client_mock) -> None:
        """US-020: Test listing user story attachments."""
        # Configurar mock
        taiga_client_mock.list_userstory_attachments.return_value = [
            {
                "id": 4001,
                "name": "requirements.pdf",
                "size": 1024000,
                "url": "https://example.com/files/requirements.pdf",
                "description": "Detailed requirements document",
                "object_id": 123456,
                "created_date": "2025-01-20T10:00:00Z",
                "modified_date": "2025-01-20T10:00:00Z",
                "owner": 888691,
            },
            {
                "id": 4002,
                "name": "mockup.png",
                "size": 204800,
                "url": "https://example.com/files/mockup.png",
                "description": "UI mockup",
                "object_id": 123456,
            },
        ]

        # Ejecutar
        result = await mcp_server.userstory_tools.list_userstory_attachments(
            auth_token="valid_token", userstory_id=123456
        )

        # Verificar
        assert len(result) == 2
        assert result[0]["name"] == "requirements.pdf"
        assert result[1]["name"] == "mockup.png"
        taiga_client_mock.list_userstory_attachments.assert_called_once_with(userstory_id=123456)

    @pytest.mark.asyncio
    async def test_create_userstory_attachment_tool_is_registered(self, mcp_server) -> None:
        """US-021: Test that create_userstory_attachment tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "create_userstory_attachment")

    @pytest.mark.asyncio
    async def test_create_userstory_attachment(self, mcp_server, taiga_client_mock) -> None:
        """US-021: Test creating a user story attachment."""
        # Configurar mock
        taiga_client_mock.create_userstory_attachment.return_value = {
            "id": 4003,
            "name": "specification.docx",
            "size": 512000,
            "url": "https://example.com/files/specification.docx",
            "description": "Technical specification",
            "object_id": 123456,
            "project": 309804,
            "created_date": "2025-01-25T14:00:00Z",
        }

        # Ejecutar
        result = await mcp_server.userstory_tools.create_userstory_attachment(
            auth_token="valid_token",
            project=309804,
            object_id=123456,
            attached_file="@/path/to/specification.docx",
            description="Technical specification",
        )

        # Verificar
        assert result["id"] == 4003
        assert result["name"] == "specification.docx"
        assert result["description"] == "Technical specification"
        taiga_client_mock.create_userstory_attachment.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_userstory_attachment_tool_is_registered(self, mcp_server) -> None:
        """US-022: Test that get_userstory_attachment tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "get_userstory_attachment")

    @pytest.mark.asyncio
    async def test_get_userstory_attachment(self, mcp_server, taiga_client_mock) -> None:
        """US-022: Test getting a specific user story attachment."""
        # Configurar mock
        taiga_client_mock.get_userstory_attachment.return_value = {
            "id": 4001,
            "name": "requirements.pdf",
            "size": 1024000,
            "url": "https://example.com/files/requirements.pdf",
            "description": "Detailed requirements document",
            "object_id": 123456,
            "is_deprecated": False,
        }

        # Ejecutar
        result = await mcp_server.userstory_tools.get_userstory_attachment(
            auth_token="valid_token", attachment_id=4001
        )

        # Verificar
        assert result["id"] == 4001
        assert result["name"] == "requirements.pdf"
        assert result["is_deprecated"] is False
        taiga_client_mock.get_userstory_attachment.assert_called_once_with(attachment_id=4001)

    @pytest.mark.asyncio
    async def test_update_userstory_attachment_tool_is_registered(self, mcp_server) -> None:
        """US-023: Test that update_userstory_attachment tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "update_userstory_attachment")

    @pytest.mark.asyncio
    async def test_update_userstory_attachment(self, mcp_server, taiga_client_mock) -> None:
        """US-023: Test updating a user story attachment."""
        # Configurar mock
        taiga_client_mock.update_userstory_attachment.return_value = {
            "id": 4001,
            "description": "Updated requirements document v2",
            "is_deprecated": True,
        }

        # Ejecutar
        result = await mcp_server.userstory_tools.update_userstory_attachment(
            auth_token="valid_token",
            attachment_id=4001,
            description="Updated requirements document v2",
            is_deprecated=True,
        )

        # Verificar
        assert result["description"] == "Updated requirements document v2"
        assert result["is_deprecated"] is True
        taiga_client_mock.update_userstory_attachment.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_userstory_attachment_tool_is_registered(self, mcp_server) -> None:
        """US-024: Test that delete_userstory_attachment tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "delete_userstory_attachment")

    @pytest.mark.asyncio
    async def test_delete_userstory_attachment(self, mcp_server, taiga_client_mock) -> None:
        """US-024: Test deleting a user story attachment."""
        # Configurar mock
        taiga_client_mock.delete_userstory_attachment.return_value = {"success": True}

        # Ejecutar
        result = await mcp_server.userstory_tools.delete_userstory_attachment(
            auth_token="valid_token", attachment_id=4001
        )

        # Verificar
        assert result["success"] is True
        taiga_client_mock.delete_userstory_attachment.assert_called_once_with(attachment_id=4001)

    @pytest.mark.asyncio
    async def test_bulk_create_attachments(self, mcp_server, taiga_client_mock) -> None:
        """Test creating multiple attachments for a user story."""
        # Configurar mock
        taiga_client_mock.create_userstory_attachment.side_effect = [
            {"id": 4004, "name": "file1.pdf"},
            {"id": 4005, "name": "file2.png"},
            {"id": 4006, "name": "file3.docx"},
        ]

        # Simular creación múltiple
        files = [
            ("@/path/to/file1.pdf", "First document"),
            ("@/path/to/file2.png", "Image mockup"),
            ("@/path/to/file3.docx", "Word document"),
        ]

        results = []
        for file_path, description in files:
            result = await mcp_server.userstory_tools.create_userstory_attachment(
                auth_token="valid_token",
                project=309804,
                object_id=123456,
                attached_file=file_path,
                description=description,
            )
            results.append(result)

        # Verificar
        assert len(results) == 3
        assert results[0]["name"] == "file1.pdf"
        assert results[1]["name"] == "file2.png"
        assert results[2]["name"] == "file3.docx"
        assert taiga_client_mock.create_userstory_attachment.call_count == 3
