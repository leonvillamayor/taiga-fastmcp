"""
Tests unitarios para las herramientas de Webhooks del servidor MCP.
Cubre las funcionalidades WEBH-001 según Documentacion/taiga.md.
"""

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.application.tools.webhook_tools import WebhookTools


class TestListWebhooksTool:
    """Tests para la herramienta list_webhooks."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_list_webhooks_tool_is_registered(self) -> None:
        """
        WEBH-001: Gestión de webhooks.
        Verifica que la herramienta list_webhooks está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)

        # Act
        webhook_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_list_webhooks" in tool_names

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_list_webhooks_by_project(self, mock_taiga_api) -> None:
        """
        Verifica que lista webhooks por proyecto correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)
        webhook_tools.register_tools()

        mock_taiga_api.get(
            "https://api.taiga.io/api/v1/webhooks?project=123&page=1&page_size=100"
        ).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "project": 123,
                        "name": "Slack Integration",
                        "url": "https://hooks.slack.com/services/T00000000/B00000000/XXXX",
                        "key": "webhook_secret_key",
                        "enabled": True,
                        "created_date": "2025-01-01T10:00:00Z",
                        "modified_date": "2025-01-15T14:00:00Z",
                    },
                    {
                        "id": 2,
                        "project": 123,
                        "name": "Jenkins CI",
                        "url": "https://jenkins.example.com/webhook",
                        "key": "jenkins_secret",
                        "enabled": False,
                        "created_date": "2025-01-05T10:00:00Z",
                        "modified_date": "2025-01-10T14:00:00Z",
                    },
                ],
            )
        )

        # Act
        result = await webhook_tools.list_webhooks(auth_token="valid_token", project_id=123)

        # Assert
        assert len(result) == 2
        assert result[0]["name"] == "Slack Integration"
        assert result[0]["enabled"] is True
        assert result[1]["name"] == "Jenkins CI"
        assert result[1]["enabled"] is False


class TestCreateWebhookTool:
    """Tests para la herramienta create_webhook."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_create_webhook_tool_is_registered(self) -> None:
        """
        WEBH-001: Crear webhook.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)

        # Act
        webhook_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_create_webhook" in tool_names

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_create_webhook_success(self, mock_taiga_api) -> None:
        """
        Verifica que crea webhook correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)
        webhook_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/webhooks").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": 10,
                    "project": 123,
                    "name": "GitHub Actions",
                    "url": "https://github.com/webhook",
                    "key": "github_secret_key",
                    "enabled": True,
                    "created_date": "2025-01-20T10:00:00Z",
                },
            )
        )

        # Act
        result = await webhook_tools.create_webhook(
            auth_token="valid_token",
            project_id=123,
            name="GitHub Actions",
            url="https://github.com/webhook",
            key="github_secret_key",
        )

        # Assert
        assert result["id"] == 10
        assert result["name"] == "GitHub Actions"
        assert result["url"] == "https://github.com/webhook"
        assert result["enabled"] is True

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_create_webhook_invalid_url(self, mock_taiga_api) -> None:
        """
        Verifica manejo de URL inválida al crear webhook.

        La validación temprana de parámetros captura URLs inválidas
        antes de llamar a la API.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)
        webhook_tools.register_tools()

        # No se necesita mock porque la validación temprana captura el error
        # antes de llamar a la API

        # Act & Assert - Early validation catches invalid URL
        with pytest.raises(ToolError, match=r"url:.*debe comenzar con http"):
            await webhook_tools.create_webhook(
                auth_token="valid_token",
                project_id=123,
                name="Invalid Webhook",
                url="not-a-valid-url",
                key="secret",
            )


class TestGetWebhookTool:
    """Tests para la herramienta get_webhook."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_get_webhook_tool_is_registered(self) -> None:
        """
        WEBH-001: Obtener webhook.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)

        # Act
        webhook_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_get_webhook" in tool_names

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_get_webhook_by_id(self, mock_taiga_api) -> None:
        """
        Verifica que obtiene webhook por ID correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)
        webhook_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/webhooks/10").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 10,
                    "project": {"id": 123, "name": "My Project", "slug": "my-project"},
                    "name": "Slack Integration",
                    "url": "https://hooks.slack.com/services/XXX",
                    "key": "slack_secret",
                    "enabled": True,
                    "logs": [
                        {
                            "id": 100,
                            "status": 200,
                            "request_data": {"event": "issue.created"},
                            "response_data": {"ok": True},
                            "created": "2025-01-20T15:00:00Z",
                        }
                    ],
                },
            )
        )

        # Act
        result = await webhook_tools.get_webhook(auth_token="valid_token", webhook_id=10)

        # Assert
        assert result["id"] == 10
        assert result["name"] == "Slack Integration"
        assert result["project"]["id"] == 123
        assert len(result["logs"]) == 1


class TestUpdateWebhookTool:
    """Tests para la herramienta update_webhook."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_update_webhook_tool_is_registered(self) -> None:
        """
        WEBH-001: Actualizar webhook.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)

        # Act
        webhook_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_update_webhook" in tool_names

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_update_webhook_url_and_status(self, mock_taiga_api) -> None:
        """
        Verifica que actualiza URL y estado del webhook.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)
        webhook_tools.register_tools()

        mock_taiga_api.patch("https://api.taiga.io/api/v1/webhooks/10").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 10,
                    "name": "Slack Integration",
                    "url": "https://hooks.slack.com/services/NEW",
                    "key": "new_secret",
                    "enabled": False,
                },
            )
        )

        # Act
        result = await webhook_tools.update_webhook(
            auth_token="valid_token",
            webhook_id=10,
            url="https://hooks.slack.com/services/NEW",
            key="new_secret",
            enabled=False,
        )

        # Assert
        assert result["url"] == "https://hooks.slack.com/services/NEW"
        assert result["key"] == "new_secret"
        assert result["enabled"] is False


class TestDeleteWebhookTool:
    """Tests para la herramienta delete_webhook."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_delete_webhook_tool_is_registered(self) -> None:
        """
        WEBH-001: Eliminar webhook.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)

        # Act
        webhook_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_delete_webhook" in tool_names

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_delete_webhook_success(self, mock_taiga_api) -> None:
        """
        Verifica que elimina webhook correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)
        webhook_tools.register_tools()

        mock_taiga_api.delete("https://api.taiga.io/api/v1/webhooks/10").mock(
            return_value=httpx.Response(204)
        )

        # Act
        result = await webhook_tools.delete_webhook(auth_token="valid_token", webhook_id=10)

        # Assert
        assert result is True

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_delete_webhook_not_found(self, mock_taiga_api) -> None:
        """
        Verifica manejo de webhook no encontrado al eliminar.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)
        webhook_tools.register_tools()

        mock_taiga_api.delete("https://api.taiga.io/api/v1/webhooks/999").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Webhook not found"):
            await webhook_tools.delete_webhook(auth_token="valid_token", webhook_id=999)


class TestTestWebhookTool:
    """Tests para la herramienta test_webhook."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_test_webhook_tool_is_registered(self) -> None:
        """
        WEBH-001: Probar webhook.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)

        # Act
        webhook_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_test_webhook" in tool_names

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_test_webhook_success(self, mock_taiga_api) -> None:
        """
        Verifica que prueba webhook correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)
        webhook_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/webhooks/10/test").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": 200,
                    "response_data": {"success": True},
                    "headers": {"Content-Type": "application/json"},
                    "duration": 0.5,
                },
            )
        )

        # Act
        result = await webhook_tools.test_webhook(auth_token="valid_token", webhook_id=10)

        # Assert
        assert result["status"] == 200
        assert result["response_data"]["success"] is True
        assert result["duration"] == 0.5

    @pytest.mark.unit
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_test_webhook_failure(self, mock_taiga_api) -> None:
        """
        Verifica manejo de fallo en prueba de webhook.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)
        webhook_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/webhooks/10/test").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": 500,
                    "response_data": {"error": "Internal server error"},
                    "duration": 1.2,
                },
            )
        )

        # Act
        result = await webhook_tools.test_webhook(auth_token="valid_token", webhook_id=10)

        # Assert
        assert result["status"] == 500
        assert "error" in result["response_data"]


class TestWebhookToolsBestPractices:
    """Tests para verificar buenas prácticas en herramientas de Webhooks."""

    @pytest.mark.unit
    @pytest.mark.webhooks
    def test_webhook_tools_use_async_await(self) -> None:
        """
        RNF-001: Usar async/await para operaciones I/O.
        Verifica que las herramientas de webhooks son asíncronas.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)
        webhook_tools.register_tools()

        # Act
        import inspect

        # Assert
        assert inspect.iscoroutinefunction(webhook_tools.list_webhooks)
        assert inspect.iscoroutinefunction(webhook_tools.create_webhook)
        assert inspect.iscoroutinefunction(webhook_tools.get_webhook)
        assert inspect.iscoroutinefunction(webhook_tools.update_webhook)
        assert inspect.iscoroutinefunction(webhook_tools.delete_webhook)
        assert inspect.iscoroutinefunction(webhook_tools.test_webhook)

    @pytest.mark.unit
    @pytest.mark.webhooks
    def test_webhook_tools_have_docstrings(self) -> None:
        """
        RNF-006: El código DEBE tener docstrings descriptivos.
        Verifica que las herramientas tienen documentación.
        """
        # Arrange
        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)
        webhook_tools.register_tools()

        # Act & Assert
        assert webhook_tools.list_webhooks.__doc__ is not None
        assert "webhook" in webhook_tools.list_webhooks.__doc__.lower()

        assert webhook_tools.create_webhook.__doc__ is not None
        assert "create" in webhook_tools.create_webhook.__doc__.lower()

        assert webhook_tools.get_webhook.__doc__ is not None
        assert webhook_tools.update_webhook.__doc__ is not None
        assert webhook_tools.delete_webhook.__doc__ is not None
        assert webhook_tools.test_webhook.__doc__ is not None

    @pytest.mark.unit
    @pytest.mark.webhooks
    def test_all_webhook_tools_are_registered(self) -> None:
        """
        RF-030: TODAS las funcionalidades de Taiga DEBEN estar expuestas.
        Verifica que todas las herramientas de webhooks están registradas.
        """
        # Arrange
        import asyncio

        mcp = FastMCP("Test")
        webhook_tools = WebhookTools(mcp)

        # Act
        webhook_tools.register_tools()
        tools = asyncio.run(mcp.get_tools())
        tool_names = list(tools.keys())

        # Assert - Todas las herramientas de webhooks necesarias
        expected_tools = [
            "taiga_list_webhooks",  # Listar webhooks
            "taiga_create_webhook",  # Crear webhook
            "taiga_get_webhook",  # Obtener webhook
            "taiga_update_webhook",  # Actualizar webhook
            "taiga_delete_webhook",  # Eliminar webhook
            "taiga_test_webhook",  # Probar webhook
        ]

        for tool in expected_tools:
            assert tool in tool_names, f"Tool {tool} not registered"
