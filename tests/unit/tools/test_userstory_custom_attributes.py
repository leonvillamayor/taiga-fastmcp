"""
Tests for User Story custom attributes functionality.
US-030 to US-035: Complete User Story custom attributes testing.
"""

import pytest


class TestUserStoryCustomAttributes:
    """Tests for User Story custom attributes functionality (US-030 to US-035)."""

    @pytest.mark.asyncio
    async def test_list_userstory_custom_attributes_tool_is_registered(self, mcp_server) -> None:
        """US-030: Test that list_userstory_custom_attributes tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "list_userstory_custom_attributes")

    @pytest.mark.asyncio
    async def test_list_userstory_custom_attributes(self, mcp_server, taiga_client_mock) -> None:
        """US-030: Test listing user story custom attributes."""
        # Configurar mock
        taiga_client_mock.list_userstory_custom_attributes.return_value = [
            {
                "id": 1,
                "name": "Client Name",
                "description": "Name of the client who requested this feature",
                "type": "text",
                "order": 1,
                "project": 309804,
                "extra": None,
            },
            {
                "id": 2,
                "name": "Business Value",
                "description": "Business value score",
                "type": "number",
                "order": 2,
                "project": 309804,
                "extra": {"min": 1, "max": 10},
            },
            {
                "id": 3,
                "name": "Risk Level",
                "description": "Implementation risk level",
                "type": "dropdown",
                "order": 3,
                "project": 309804,
                "extra": {"options": ["Low", "Medium", "High", "Critical"]},
            },
        ]

        # Ejecutar
        result = await mcp_server.userstory_tools.list_userstory_custom_attributes(
            auth_token="valid_token", project=309804
        )

        # Verificar
        assert len(result) == 3
        assert result[0]["name"] == "Client Name"
        assert result[0]["type"] == "text"
        assert result[1]["name"] == "Business Value"
        assert result[1]["type"] == "number"
        assert result[2]["name"] == "Risk Level"
        assert result[2]["type"] == "dropdown"
        taiga_client_mock.list_userstory_custom_attributes.assert_called_once_with(project=309804)

    @pytest.mark.asyncio
    async def test_create_userstory_custom_attribute_tool_is_registered(self, mcp_server) -> None:
        """US-031: Test that create_userstory_custom_attribute tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "create_userstory_custom_attribute")

    @pytest.mark.asyncio
    async def test_create_userstory_custom_attribute(self, mcp_server, taiga_client_mock) -> None:
        """US-031: Test creating a user story custom attribute."""
        # Configurar mock
        taiga_client_mock.create_userstory_custom_attribute.return_value = {
            "id": 4,
            "name": "Sprint Goal",
            "description": "The sprint goal this US contributes to",
            "type": "text",
            "order": 4,
            "project": 309804,
            "created_date": "2025-01-25T10:00:00Z",
        }

        # Ejecutar
        result = await mcp_server.userstory_tools.create_userstory_custom_attribute(
            auth_token="valid_token",
            project=309804,
            name="Sprint Goal",
            description="The sprint goal this US contributes to",
            type="text",
            order=4,
        )

        # Verificar
        assert result["id"] == 4
        assert result["name"] == "Sprint Goal"
        assert result["type"] == "text"
        taiga_client_mock.create_userstory_custom_attribute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_custom_attribute_with_options(
        self, mcp_server, taiga_client_mock
    ) -> None:
        """US-031: Test creating a dropdown custom attribute with options."""
        # Configurar mock
        taiga_client_mock.create_userstory_custom_attribute.return_value = {
            "id": 5,
            "name": "Priority",
            "type": "dropdown",
            "extra": {"options": ["Low", "Normal", "High", "Urgent"]},
            "project": 309804,
        }

        # Ejecutar
        result = await mcp_server.userstory_tools.create_userstory_custom_attribute(
            auth_token="valid_token",
            project=309804,
            name="Priority",
            type="dropdown",
            extra={"options": ["Low", "Normal", "High", "Urgent"]},
        )

        # Verificar
        assert result["type"] == "dropdown"
        assert "options" in result["extra"]
        assert len(result["extra"]["options"]) == 4

    @pytest.mark.asyncio
    async def test_get_userstory_custom_attribute_tool_is_registered(self, mcp_server) -> None:
        """US-032: Test that get_userstory_custom_attribute tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "get_userstory_custom_attribute")

    @pytest.mark.asyncio
    async def test_get_userstory_custom_attribute(self, mcp_server, taiga_client_mock) -> None:
        """US-032: Test getting a specific user story custom attribute."""
        # Configurar mock
        taiga_client_mock.get_userstory_custom_attribute.return_value = {
            "id": 1,
            "name": "Client Name",
            "description": "Name of the client who requested this feature",
            "type": "text",
            "order": 1,
            "project": 309804,
            "created_date": "2025-01-01T10:00:00Z",
            "modified_date": "2025-01-15T12:00:00Z",
        }

        # Ejecutar
        result = await mcp_server.userstory_tools.get_userstory_custom_attribute(
            auth_token="valid_token", attribute_id=1
        )

        # Verificar
        assert result["id"] == 1
        assert result["name"] == "Client Name"
        assert result["type"] == "text"
        taiga_client_mock.get_userstory_custom_attribute.assert_called_once_with(attribute_id=1)

    @pytest.mark.asyncio
    async def test_update_userstory_custom_attribute_full_tool_is_registered(
        self, mcp_server
    ) -> None:
        """US-033: Test that update_userstory_custom_attribute_full tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "update_userstory_custom_attribute_full")

    @pytest.mark.asyncio
    async def test_update_userstory_custom_attribute_full(
        self, mcp_server, taiga_client_mock
    ) -> None:
        """US-033: Test full update (PUT) of a user story custom attribute."""
        # Configurar mock
        taiga_client_mock.update_userstory_custom_attribute_full.return_value = {
            "id": 1,
            "name": "Customer Company",
            "description": "Updated: Company name of the customer",
            "type": "text",
            "order": 1,
            "project": 309804,
        }

        # Ejecutar
        result = await mcp_server.userstory_tools.update_userstory_custom_attribute_full(
            auth_token="valid_token",
            attribute_id=1,
            name="Customer Company",
            description="Updated: Company name of the customer",
            type="text",
            order=1,
        )

        # Verificar
        assert result["name"] == "Customer Company"
        assert "Updated" in result["description"]
        taiga_client_mock.update_userstory_custom_attribute_full.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_userstory_custom_attribute_partial_tool_is_registered(
        self, mcp_server
    ) -> None:
        """US-034: Test that update_userstory_custom_attribute tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "update_userstory_custom_attribute")

    @pytest.mark.asyncio
    async def test_update_userstory_custom_attribute_partial(
        self, mcp_server, taiga_client_mock
    ) -> None:
        """US-034: Test partial update (PATCH) of a user story custom attribute."""
        # Configurar mock
        taiga_client_mock.update_userstory_custom_attribute.return_value = {
            "id": 2,
            "name": "Business Value Score",
            "description": "Business value score",
            "order": 5,
        }

        # Ejecutar
        result = await mcp_server.userstory_tools.update_userstory_custom_attribute(
            auth_token="valid_token", attribute_id=2, name="Business Value Score", order=5
        )

        # Verificar
        assert result["name"] == "Business Value Score"
        assert result["order"] == 5
        taiga_client_mock.update_userstory_custom_attribute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_userstory_custom_attribute_tool_is_registered(self, mcp_server) -> None:
        """US-035: Test that delete_userstory_custom_attribute tool is registered."""
        assert hasattr(mcp_server.userstory_tools, "delete_userstory_custom_attribute")

    @pytest.mark.asyncio
    async def test_delete_userstory_custom_attribute(self, mcp_server, taiga_client_mock) -> None:
        """US-035: Test deleting a user story custom attribute."""
        # Configurar mock
        taiga_client_mock.delete_userstory_custom_attribute.return_value = {"success": True}

        # Ejecutar
        result = await mcp_server.userstory_tools.delete_userstory_custom_attribute(
            auth_token="valid_token", attribute_id=1
        )

        # Verificar
        assert result["success"] is True
        taiga_client_mock.delete_userstory_custom_attribute.assert_called_once_with(attribute_id=1)

    @pytest.mark.asyncio
    async def test_set_custom_attribute_values_on_userstory(
        self, mcp_server, taiga_client_mock
    ) -> None:
        """Test setting custom attribute values on a user story."""
        # Configurar mock
        taiga_client_mock.update_userstory.return_value = {
            "id": 123456,
            "subject": "User story with custom attributes",
            "custom_attributes": {"1": "Acme Corp", "2": 8, "3": "High"},
        }

        # Ejecutar
        result = await mcp_server.userstory_tools.update_userstory(
            auth_token="valid_token",
            userstory_id=123456,
            version=1,
            custom_attributes={"1": "Acme Corp", "2": 8, "3": "High"},
        )

        # Verificar
        assert "custom_attributes" in result
        assert result["custom_attributes"]["1"] == "Acme Corp"
        assert result["custom_attributes"]["2"] == 8
        assert result["custom_attributes"]["3"] == "High"

    @pytest.mark.asyncio
    async def test_custom_attribute_validation(self, mcp_server, taiga_client_mock) -> None:
        """Test validation of custom attribute values."""
        from fastmcp.exceptions import ToolError as MCPError

        # Test con valor inválido para número
        with pytest.raises(MCPError, match="Value must be a number"):
            await mcp_server.userstory_tools.update_userstory(
                auth_token="valid_token",
                userstory_id=123456,
                version=1,
                custom_attributes={"2": "not-a-number"},  # Should be a number
            )

        # Test con opción inválida para dropdown
        with pytest.raises(MCPError, match="Invalid option"):
            await mcp_server.userstory_tools.update_userstory(
                auth_token="valid_token",
                userstory_id=123456,
                version=1,
                custom_attributes={"3": "InvalidOption"},  # Should be one of the defined options
            )
