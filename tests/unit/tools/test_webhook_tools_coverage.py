"""
Tests adicionales para webhook_tools.py para alcanzar >= 90% de cobertura.

Cubre:
- Método set_client
- Todos los exception handlers (AuthenticationError, TaigaAPIError,
  ResourceNotFoundError, PermissionDeniedError, ValidationError)
- Ramas opcionales (auto_paginate=False, no update data, etc.)
- Ramas específicas de test_webhook (timeout, connection, 404)
- Método legacy _register_tools
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.application.tools.webhook_tools import WebhookTools
from src.domain.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    ResourceNotFoundError,
    TaigaAPIError,
    ValidationError,
)


@pytest.fixture
def webhook_tools_instance():
    """Fixture que crea una instancia de WebhookTools con mock del cliente."""
    mcp = FastMCP("Test")
    with patch("src.application.tools.webhook_tools.TaigaAPIClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        tools = WebhookTools(mcp)
        tools.register_tools()
        tools._mock_client = mock_client
        tools._mock_client_cls = mock_client_cls

        yield tools


class TestSetClient:
    """Tests para el método set_client."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    def test_set_client_stores_client(self):
        """Verifica que set_client almacena el cliente correctamente."""
        mcp = FastMCP("Test")
        tools = WebhookTools(mcp)

        mock_client = MagicMock()
        tools.set_client(mock_client)

        assert tools.client is mock_client


class TestListWebhooksExceptionHandlers:
    """Tests para los exception handlers de list_webhooks."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_list_webhooks_authentication_error(self, webhook_tools_instance):
        """Verifica manejo de AuthenticationError en list_webhooks."""
        paginator_mock = MagicMock()
        paginator_mock.paginate = AsyncMock(side_effect=AuthenticationError("Token expired"))

        with patch(
            "src.application.tools.webhook_tools.AutoPaginator", return_value=paginator_mock
        ), pytest.raises(ToolError, match="Authentication failed"):
            await webhook_tools_instance.list_webhooks(
                auth_token="invalid_token", project_id=123
            )

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_list_webhooks_taiga_api_error(self, webhook_tools_instance):
        """Verifica manejo de TaigaAPIError en list_webhooks."""
        paginator_mock = MagicMock()
        paginator_mock.paginate = AsyncMock(side_effect=TaigaAPIError("Server error"))

        with patch(
            "src.application.tools.webhook_tools.AutoPaginator", return_value=paginator_mock
        ), pytest.raises(ToolError, match="Failed to list webhooks"):
            await webhook_tools_instance.list_webhooks(auth_token="token", project_id=123)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_list_webhooks_unexpected_exception(self, webhook_tools_instance):
        """Verifica manejo de Exception genérica en list_webhooks."""
        paginator_mock = MagicMock()
        paginator_mock.paginate = AsyncMock(side_effect=RuntimeError("Unexpected"))

        with patch(
            "src.application.tools.webhook_tools.AutoPaginator", return_value=paginator_mock
        ), pytest.raises(ToolError, match="Unexpected error"):
            await webhook_tools_instance.list_webhooks(auth_token="token", project_id=123)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_list_webhooks_auto_paginate_false(self, webhook_tools_instance):
        """Verifica que auto_paginate=False usa paginate_first_page."""
        paginator_mock = MagicMock()
        paginator_mock.paginate_first_page = AsyncMock(
            return_value=[{"id": 1, "name": "Test Webhook", "project": 123}]
        )

        with patch(
            "src.application.tools.webhook_tools.AutoPaginator", return_value=paginator_mock
        ):
            result = await webhook_tools_instance.list_webhooks(
                auth_token="token", project_id=123, auto_paginate=False
            )

            paginator_mock.paginate_first_page.assert_called_once()
            assert len(result) == 1

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_list_webhooks_returns_empty_when_not_list(self, webhook_tools_instance):
        """Verifica que retorna lista vacía cuando el resultado no es una lista."""
        paginator_mock = MagicMock()
        paginator_mock.paginate = AsyncMock(return_value=None)

        with patch(
            "src.application.tools.webhook_tools.AutoPaginator", return_value=paginator_mock
        ):
            result = await webhook_tools_instance.list_webhooks(auth_token="token", project_id=123)

            assert result == []

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_list_webhooks_returns_empty_when_dict(self, webhook_tools_instance):
        """Verifica que retorna lista vacía cuando el resultado es un dict."""
        paginator_mock = MagicMock()
        paginator_mock.paginate = AsyncMock(return_value={"error": "not a list"})

        with patch(
            "src.application.tools.webhook_tools.AutoPaginator", return_value=paginator_mock
        ):
            result = await webhook_tools_instance.list_webhooks(auth_token="token", project_id=123)

            assert result == []


class TestCreateWebhookExceptionHandlers:
    """Tests para los exception handlers de create_webhook."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_create_webhook_validation_error(self, webhook_tools_instance):
        """Verifica manejo de ValidationError en create_webhook."""
        with patch(
            "src.application.tools.webhook_tools.validate_input",
            side_effect=ValidationError("Invalid webhook data"),
        ), pytest.raises(ToolError, match="Invalid webhook data"):
            await webhook_tools_instance.create_webhook(
                auth_token="token",
                project_id=123,
                name="Test",
                url="https://example.com/webhook",
                key="secret",
            )

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_create_webhook_permission_denied_error(self, webhook_tools_instance):
        """Verifica manejo de PermissionDeniedError en create_webhook."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        with pytest.raises(ToolError, match="No permission to create webhooks"):
            await webhook_tools_instance.create_webhook(
                auth_token="token",
                project_id=123,
                name="Test",
                url="https://example.com/webhook",
                key="secret",
            )

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_create_webhook_authentication_error(self, webhook_tools_instance):
        """Verifica manejo de AuthenticationError en create_webhook."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Token expired")
        )

        with pytest.raises(ToolError, match="Authentication failed"):
            await webhook_tools_instance.create_webhook(
                auth_token="invalid",
                project_id=123,
                name="Test",
                url="https://example.com/webhook",
                key="secret",
            )

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_create_webhook_duplicate_error(self, webhook_tools_instance):
        """Verifica manejo de error de webhook duplicado."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("Webhook already exists")
        )

        with pytest.raises(ToolError, match="already exists"):
            await webhook_tools_instance.create_webhook(
                auth_token="token",
                project_id=123,
                name="Test",
                url="https://example.com/webhook",
                key="secret",
            )

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_create_webhook_duplicate_error_alternate(self, webhook_tools_instance):
        """Verifica manejo de error con mensaje 'duplicate'."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("Duplicate entry found")
        )

        with pytest.raises(ToolError, match="already exists"):
            await webhook_tools_instance.create_webhook(
                auth_token="token",
                project_id=123,
                name="Test",
                url="https://example.com/webhook",
                key="secret",
            )

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_create_webhook_taiga_api_error(self, webhook_tools_instance):
        """Verifica manejo de TaigaAPIError genérico en create_webhook."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("Server error")
        )

        with pytest.raises(ToolError, match="Failed to create webhook"):
            await webhook_tools_instance.create_webhook(
                auth_token="token",
                project_id=123,
                name="Test",
                url="https://example.com/webhook",
                key="secret",
            )

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_create_webhook_unexpected_exception(self, webhook_tools_instance):
        """Verifica manejo de Exception genérica en create_webhook."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            side_effect=RuntimeError("Unexpected error")
        )

        with pytest.raises(ToolError, match="Unexpected error"):
            await webhook_tools_instance.create_webhook(
                auth_token="token",
                project_id=123,
                name="Test",
                url="https://example.com/webhook",
                key="secret",
            )


class TestGetWebhookExceptionHandlers:
    """Tests para los exception handlers de get_webhook."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_get_webhook_success(self, webhook_tools_instance):
        """Verifica get_webhook exitoso."""
        webhook_tools_instance._mock_client.get = AsyncMock(
            return_value={
                "id": 1,
                "project": 123,
                "name": "Test Webhook",
                "url": "https://example.com/webhook",
                "key": "secret",
                "enabled": True,
                "created_date": "2024-01-01",
                "modified_date": "2024-01-02",
                "logs_counter": 5,
                "logs": [{"status": 200}],
            }
        )

        result = await webhook_tools_instance.get_webhook(auth_token="token", webhook_id=1)

        assert result["id"] == 1
        assert result["name"] == "Test Webhook"
        assert result["logs_counter"] == 5

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_get_webhook_not_found_error(self, webhook_tools_instance):
        """Verifica manejo de ResourceNotFoundError en get_webhook."""
        webhook_tools_instance._mock_client.get = AsyncMock(
            side_effect=ResourceNotFoundError("Webhook not found")
        )

        with pytest.raises(ToolError, match="Webhook not found"):
            await webhook_tools_instance.get_webhook(auth_token="token", webhook_id=999)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_get_webhook_authentication_error(self, webhook_tools_instance):
        """Verifica manejo de AuthenticationError en get_webhook."""
        webhook_tools_instance._mock_client.get = AsyncMock(
            side_effect=AuthenticationError("Token expired")
        )

        with pytest.raises(ToolError, match="Authentication failed"):
            await webhook_tools_instance.get_webhook(auth_token="invalid", webhook_id=1)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_get_webhook_taiga_api_error(self, webhook_tools_instance):
        """Verifica manejo de TaigaAPIError en get_webhook."""
        webhook_tools_instance._mock_client.get = AsyncMock(
            side_effect=TaigaAPIError("Server error")
        )

        with pytest.raises(ToolError, match="Failed to get webhook"):
            await webhook_tools_instance.get_webhook(auth_token="token", webhook_id=1)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_get_webhook_unexpected_exception(self, webhook_tools_instance):
        """Verifica manejo de Exception genérica en get_webhook."""
        webhook_tools_instance._mock_client.get = AsyncMock(
            side_effect=RuntimeError("Unexpected")
        )

        with pytest.raises(ToolError, match="Unexpected error"):
            await webhook_tools_instance.get_webhook(auth_token="token", webhook_id=1)


class TestUpdateWebhookExceptionHandlers:
    """Tests para los exception handlers de update_webhook."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_update_webhook_success(self, webhook_tools_instance):
        """Verifica update_webhook exitoso."""
        webhook_tools_instance._mock_client.patch = AsyncMock(
            return_value={
                "id": 1,
                "project": 123,
                "name": "Updated Webhook",
                "url": "https://example.com/updated",
                "key": "new_secret",
                "enabled": False,
                "modified_date": "2024-01-02",
            }
        )

        result = await webhook_tools_instance.update_webhook(
            auth_token="token", webhook_id=1, name="Updated Webhook"
        )

        assert result["name"] == "Updated Webhook"
        assert "updated successfully" in result["message"]

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_update_webhook_no_data_provided(self, webhook_tools_instance):
        """Verifica error cuando no se proporciona ningún dato para actualizar."""
        with pytest.raises(ToolError, match="No update data provided"):
            await webhook_tools_instance.update_webhook(auth_token="token", webhook_id=1)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_update_webhook_validation_error(self, webhook_tools_instance):
        """Verifica manejo de ValidationError en update_webhook."""
        with patch(
            "src.application.tools.webhook_tools.validate_input",
            side_effect=ValidationError("Invalid URL format"),
        ), pytest.raises(ToolError, match="Invalid URL format"):
            await webhook_tools_instance.update_webhook(
                auth_token="token", webhook_id=1, url="not-valid"
            )

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_update_webhook_not_found_error(self, webhook_tools_instance):
        """Verifica manejo de ResourceNotFoundError en update_webhook."""
        webhook_tools_instance._mock_client.patch = AsyncMock(
            side_effect=ResourceNotFoundError("Webhook not found")
        )

        with pytest.raises(ToolError, match="Webhook not found"):
            await webhook_tools_instance.update_webhook(
                auth_token="token", webhook_id=999, name="Updated"
            )

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_update_webhook_permission_denied_error(self, webhook_tools_instance):
        """Verifica manejo de PermissionDeniedError en update_webhook."""
        webhook_tools_instance._mock_client.patch = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        with pytest.raises(ToolError, match="No permission to update"):
            await webhook_tools_instance.update_webhook(
                auth_token="token", webhook_id=1, name="Updated"
            )

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_update_webhook_authentication_error(self, webhook_tools_instance):
        """Verifica manejo de AuthenticationError en update_webhook."""
        webhook_tools_instance._mock_client.patch = AsyncMock(
            side_effect=AuthenticationError("Token expired")
        )

        with pytest.raises(ToolError, match="Authentication failed"):
            await webhook_tools_instance.update_webhook(
                auth_token="invalid", webhook_id=1, name="Updated"
            )

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_update_webhook_taiga_api_error(self, webhook_tools_instance):
        """Verifica manejo de TaigaAPIError en update_webhook."""
        webhook_tools_instance._mock_client.patch = AsyncMock(
            side_effect=TaigaAPIError("Server error")
        )

        with pytest.raises(ToolError, match="Failed to update webhook"):
            await webhook_tools_instance.update_webhook(
                auth_token="token", webhook_id=1, name="Updated"
            )

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_update_webhook_unexpected_exception(self, webhook_tools_instance):
        """Verifica manejo de Exception genérica en update_webhook."""
        webhook_tools_instance._mock_client.patch = AsyncMock(
            side_effect=RuntimeError("Unexpected")
        )

        with pytest.raises(ToolError, match="Unexpected error"):
            await webhook_tools_instance.update_webhook(
                auth_token="token", webhook_id=1, name="Updated"
            )

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_update_webhook_with_all_optional_fields(self, webhook_tools_instance):
        """Verifica update_webhook con todos los campos opcionales."""
        webhook_tools_instance._mock_client.patch = AsyncMock(
            return_value={
                "id": 1,
                "project": 123,
                "name": "Updated Name",
                "url": "https://new.example.com",
                "key": "new_key",
                "enabled": True,
                "modified_date": "2024-01-02",
            }
        )

        result = await webhook_tools_instance.update_webhook(
            auth_token="token",
            webhook_id=1,
            name="Updated Name",
            url="https://new.example.com",
            key="new_key",
            enabled=True,
        )

        assert result["name"] == "Updated Name"
        assert result["url"] == "https://new.example.com"
        assert result["key"] == "new_key"
        assert result["enabled"] is True


class TestDeleteWebhookExceptionHandlers:
    """Tests para los exception handlers de delete_webhook."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_delete_webhook_success(self, webhook_tools_instance):
        """Verifica delete_webhook exitoso."""
        webhook_tools_instance._mock_client.delete = AsyncMock(return_value=True)

        result = await webhook_tools_instance.delete_webhook(auth_token="token", webhook_id=1)

        assert result is True

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_delete_webhook_not_found_error(self, webhook_tools_instance):
        """Verifica manejo de ResourceNotFoundError en delete_webhook."""
        webhook_tools_instance._mock_client.delete = AsyncMock(
            side_effect=ResourceNotFoundError("Webhook not found")
        )

        with pytest.raises(ToolError, match="Webhook not found"):
            await webhook_tools_instance.delete_webhook(auth_token="token", webhook_id=999)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_delete_webhook_permission_denied_error(self, webhook_tools_instance):
        """Verifica manejo de PermissionDeniedError en delete_webhook."""
        webhook_tools_instance._mock_client.delete = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        with pytest.raises(ToolError, match="No permission to delete"):
            await webhook_tools_instance.delete_webhook(auth_token="token", webhook_id=1)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_delete_webhook_authentication_error(self, webhook_tools_instance):
        """Verifica manejo de AuthenticationError en delete_webhook."""
        webhook_tools_instance._mock_client.delete = AsyncMock(
            side_effect=AuthenticationError("Token expired")
        )

        with pytest.raises(ToolError, match="Authentication failed"):
            await webhook_tools_instance.delete_webhook(auth_token="invalid", webhook_id=1)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_delete_webhook_taiga_api_error(self, webhook_tools_instance):
        """Verifica manejo de TaigaAPIError en delete_webhook."""
        webhook_tools_instance._mock_client.delete = AsyncMock(
            side_effect=TaigaAPIError("Server error")
        )

        with pytest.raises(ToolError, match="Failed to delete webhook"):
            await webhook_tools_instance.delete_webhook(auth_token="token", webhook_id=1)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_delete_webhook_unexpected_exception(self, webhook_tools_instance):
        """Verifica manejo de Exception genérica en delete_webhook."""
        webhook_tools_instance._mock_client.delete = AsyncMock(
            side_effect=RuntimeError("Unexpected")
        )

        with pytest.raises(ToolError, match="Unexpected error"):
            await webhook_tools_instance.delete_webhook(auth_token="token", webhook_id=1)


class TestTestWebhookExceptionHandlers:
    """Tests para los exception handlers de test_webhook."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_test_webhook_success(self, webhook_tools_instance):
        """Verifica test_webhook exitoso."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            return_value={
                "status": 200,
                "response_data": {"ok": True},
                "headers": {"Content-Type": "application/json"},
                "duration": 150,
                "message": "Test successful",
            }
        )

        result = await webhook_tools_instance.test_webhook(auth_token="token", webhook_id=1)

        assert result["success"] is True
        assert result["status"] == 200
        assert result["duration"] == 150

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_test_webhook_not_found_error(self, webhook_tools_instance):
        """Verifica manejo de ResourceNotFoundError en test_webhook."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            side_effect=ResourceNotFoundError("Webhook not found")
        )

        with pytest.raises(ToolError, match="Webhook not found"):
            await webhook_tools_instance.test_webhook(auth_token="token", webhook_id=999)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_test_webhook_permission_denied_error(self, webhook_tools_instance):
        """Verifica manejo de PermissionDeniedError en test_webhook."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            side_effect=PermissionDeniedError("No permission")
        )

        with pytest.raises(ToolError, match="No permission to test"):
            await webhook_tools_instance.test_webhook(auth_token="token", webhook_id=1)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_test_webhook_authentication_error(self, webhook_tools_instance):
        """Verifica manejo de AuthenticationError en test_webhook."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            side_effect=AuthenticationError("Token expired")
        )

        with pytest.raises(ToolError, match="Authentication failed"):
            await webhook_tools_instance.test_webhook(auth_token="invalid", webhook_id=1)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_test_webhook_timeout_error(self, webhook_tools_instance):
        """Verifica manejo de timeout en test_webhook."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("Connection timeout occurred")
        )

        with pytest.raises(ToolError, match="Connection timeout"):
            await webhook_tools_instance.test_webhook(auth_token="token", webhook_id=1)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_test_webhook_connection_refused_error(self, webhook_tools_instance):
        """Verifica manejo de connection refused en test_webhook."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("Connection refused by server")
        )

        with pytest.raises(ToolError, match="Connection refused"):
            await webhook_tools_instance.test_webhook(auth_token="token", webhook_id=1)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_test_webhook_connection_error_alternate(self, webhook_tools_instance):
        """Verifica manejo de error de conexión sin 'refused'."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("Connection error to host")
        )

        with pytest.raises(ToolError, match="Connection refused"):
            await webhook_tools_instance.test_webhook(auth_token="token", webhook_id=1)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_test_webhook_endpoint_not_found_404(self, webhook_tools_instance):
        """Verifica manejo de 404 en test_webhook."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("404 - Endpoint not reachable")
        )

        with pytest.raises(ToolError, match="Endpoint not found"):
            await webhook_tools_instance.test_webhook(auth_token="token", webhook_id=1)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_test_webhook_endpoint_not_found_text(self, webhook_tools_instance):
        """Verifica manejo de 'not found' en mensaje de error."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("Remote endpoint not found")
        )

        with pytest.raises(ToolError, match="Endpoint not found"):
            await webhook_tools_instance.test_webhook(auth_token="token", webhook_id=1)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_test_webhook_taiga_api_error_generic(self, webhook_tools_instance):
        """Verifica manejo de TaigaAPIError genérico en test_webhook."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            side_effect=TaigaAPIError("Unknown server error")
        )

        with pytest.raises(ToolError, match="Webhook test failed"):
            await webhook_tools_instance.test_webhook(auth_token="token", webhook_id=1)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_test_webhook_unexpected_exception(self, webhook_tools_instance):
        """Verifica manejo de Exception genérica en test_webhook."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            side_effect=RuntimeError("Unexpected")
        )

        with pytest.raises(ToolError, match="Unexpected error"):
            await webhook_tools_instance.test_webhook(auth_token="token", webhook_id=1)

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_test_webhook_with_empty_response(self, webhook_tools_instance):
        """Verifica test_webhook con respuesta vacía (usa defaults)."""
        webhook_tools_instance._mock_client.post = AsyncMock(return_value={})

        result = await webhook_tools_instance.test_webhook(auth_token="token", webhook_id=1)

        assert result["success"] is True
        assert result["status"] == 200
        assert result["response_data"] == {}
        assert result["headers"] == {}
        assert result["duration"] == 0
        assert result["message"] == "Test webhook sent successfully"


class TestLegacyMethods:
    """Tests para métodos legacy de WebhookTools."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    def test_legacy_register_tools_method(self):
        """Verifica que _register_tools llama a register_tools."""
        mcp = FastMCP("Test")
        tools = WebhookTools(mcp)

        # Usa _register_tools (método legacy)
        tools._register_tools()

        # Verifica que las herramientas fueron registradas
        import asyncio

        registered_tools = asyncio.run(mcp.get_tools())
        assert "taiga_list_webhooks" in registered_tools


class TestWebhookToolsInitialization:
    """Tests para la inicialización de WebhookTools."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    def test_init_creates_config_and_logger(self):
        """Verifica que __init__ crea config y logger correctamente."""
        mcp = FastMCP("Test")
        tools = WebhookTools(mcp)

        assert tools.mcp is mcp
        assert tools.config is not None
        assert tools.client is None
        assert tools._logger is not None

    @pytest.mark.unit
    @pytest.mark.webhooks
    def test_tools_have_fn_attribute_for_direct_access(self):
        """Verifica que las herramientas tienen referencia directa."""
        mcp = FastMCP("Test")
        tools = WebhookTools(mcp)
        tools.register_tools()

        # Verifica que se pueden acceder directamente
        assert hasattr(tools, "list_webhooks")
        assert hasattr(tools, "create_webhook")
        assert hasattr(tools, "get_webhook")
        assert hasattr(tools, "update_webhook")
        assert hasattr(tools, "delete_webhook")
        assert hasattr(tools, "test_webhook")


class TestCreateWebhookWithEnabledFalse:
    """Tests para create_webhook con enabled=False."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_create_webhook_with_enabled_false(self, webhook_tools_instance):
        """Verifica crear webhook con enabled=False."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            return_value={
                "id": 1,
                "project": 123,
                "name": "Disabled Webhook",
                "url": "https://example.com/webhook",
                "key": "secret",
                "enabled": False,
                "created_date": "2024-01-01",
            }
        )

        result = await webhook_tools_instance.create_webhook(
            auth_token="token",
            project_id=123,
            name="Disabled Webhook",
            url="https://example.com/webhook",
            key="secret",
            enabled=False,
        )

        assert result["enabled"] is False


class TestListWebhooksWithPagination:
    """Tests para list_webhooks con diferentes opciones de paginación."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_list_webhooks_formats_response_correctly(self, webhook_tools_instance):
        """Verifica que list_webhooks formatea la respuesta correctamente."""
        paginator_mock = MagicMock()
        paginator_mock.paginate = AsyncMock(
            return_value=[
                {
                    "id": 1,
                    "project": 123,
                    "name": "Test Webhook",
                    "url": "https://example.com/webhook",
                    "key": "secret",
                    "enabled": True,
                    "created_date": "2024-01-01",
                    "modified_date": "2024-01-02",
                    "extra_field": "should_be_ignored",
                }
            ]
        )

        with patch(
            "src.application.tools.webhook_tools.AutoPaginator", return_value=paginator_mock
        ):
            result = await webhook_tools_instance.list_webhooks(auth_token="token", project_id=123)

            assert len(result) == 1
            assert result[0]["id"] == 1
            assert result[0]["name"] == "Test Webhook"
            assert "extra_field" not in result[0]

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_list_webhooks_handles_missing_enabled_field(self, webhook_tools_instance):
        """Verifica que maneja webhooks sin campo enabled (default True)."""
        paginator_mock = MagicMock()
        paginator_mock.paginate = AsyncMock(
            return_value=[
                {
                    "id": 1,
                    "project": 123,
                    "name": "Test",
                    "url": "https://example.com",
                    "key": "secret",
                    # Sin campo "enabled"
                }
            ]
        )

        with patch(
            "src.application.tools.webhook_tools.AutoPaginator", return_value=paginator_mock
        ):
            result = await webhook_tools_instance.list_webhooks(auth_token="token", project_id=123)

            assert result[0]["enabled"] is True  # Default value


class TestGetWebhookResponseDefaults:
    """Tests para verificar valores por defecto en get_webhook."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_get_webhook_with_missing_optional_fields(self, webhook_tools_instance):
        """Verifica que get_webhook maneja campos opcionales ausentes."""
        webhook_tools_instance._mock_client.get = AsyncMock(
            return_value={
                "id": 1,
                "project": 123,
                "name": "Test Webhook",
                "url": "https://example.com/webhook",
                "key": "secret",
                # Sin enabled, logs_counter, logs
            }
        )

        result = await webhook_tools_instance.get_webhook(auth_token="token", webhook_id=1)

        assert result["enabled"] is True  # Default
        assert result["logs_counter"] == 0  # Default
        assert result["logs"] == []  # Default


class TestCreateWebhookResponseDefaults:
    """Tests para verificar valores por defecto en create_webhook."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_create_webhook_with_missing_enabled_in_response(self, webhook_tools_instance):
        """Verifica que create_webhook maneja enabled ausente en respuesta."""
        webhook_tools_instance._mock_client.post = AsyncMock(
            return_value={
                "id": 1,
                "project": 123,
                "name": "Test",
                "url": "https://example.com",
                "key": "secret",
                # Sin enabled
            }
        )

        result = await webhook_tools_instance.create_webhook(
            auth_token="token",
            project_id=123,
            name="Test",
            url="https://example.com",
            key="secret",
        )

        assert result["enabled"] is True  # Default


class TestUpdateWebhookResponseDefaults:
    """Tests para verificar valores por defecto en update_webhook."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_update_webhook_with_missing_enabled_in_response(self, webhook_tools_instance):
        """Verifica que update_webhook maneja enabled ausente en respuesta."""
        webhook_tools_instance._mock_client.patch = AsyncMock(
            return_value={
                "id": 1,
                "project": 123,
                "name": "Updated",
                "url": "https://example.com",
                "key": "secret",
                # Sin enabled
            }
        )

        result = await webhook_tools_instance.update_webhook(
            auth_token="token", webhook_id=1, name="Updated"
        )

        assert result["enabled"] is True  # Default
