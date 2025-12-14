"""
Tests de integración para las herramientas de Webhooks del servidor MCP.
Prueba la integración completa de las funcionalidades de Webhooks.
"""

import httpx
import pytest
from fastmcp import FastMCP

from src.application.tools.webhook_tools import WebhookTools


class TestWebhooksIntegration:
    """Tests de integración para Webhooks."""

    @pytest.mark.integration
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_complete_webhook_lifecycle(self, mock_taiga_api, auth_token) -> None:
        """
        Test completo del ciclo de vida de un webhook:
        1. Crear webhook
        2. Listar webhooks
        3. Obtener webhook
        4. Probar webhook
        5. Actualizar webhook
        6. Eliminar webhook
        """
        # Arrange
        mcp = FastMCP("Test Webhooks Integration")
        webhook_tools = WebhookTools(mcp)
        webhook_tools.register_tools()
        project_id = 123

        # 1. Crear webhook
        mock_taiga_api.post("https://api.taiga.io/api/v1/webhooks").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": 10,
                    "project": project_id,
                    "name": "Slack Notifications",
                    "url": "https://hooks.slack.com/services/T00/B00/XXX",
                    "key": "slack_secret_key",
                    "enabled": True,
                    "created_date": "2025-01-20T10:00:00Z",
                },
            )
        )

        create_result = await webhook_tools.create_webhook(
            auth_token=auth_token,
            project_id=project_id,
            name="Slack Notifications",
            url="https://hooks.slack.com/services/T00/B00/XXX",
            key="slack_secret_key",
        )

        assert create_result["id"] == 10
        assert create_result["name"] == "Slack Notifications"
        assert create_result["enabled"] is True

        # 2. Listar webhooks (includes pagination params from AutoPaginator)
        mock_taiga_api.get(
            f"https://api.taiga.io/api/v1/webhooks?project={project_id}&page=1&page_size=100"
        ).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": 10,
                        "project": project_id,
                        "name": "Slack Notifications",
                        "url": "https://hooks.slack.com/services/T00/B00/XXX",
                        "enabled": True,
                    }
                ],
            )
        )

        list_result = await webhook_tools.list_webhooks(
            auth_token=auth_token, project_id=project_id
        )

        assert len(list_result) == 1
        assert list_result[0]["id"] == 10

        # 3. Obtener webhook específico
        mock_taiga_api.get("https://api.taiga.io/api/v1/webhooks/10").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 10,
                    "project": {"id": project_id, "name": "Test Project", "slug": "test-project"},
                    "name": "Slack Notifications",
                    "url": "https://hooks.slack.com/services/T00/B00/XXX",
                    "key": "slack_secret_key",
                    "enabled": True,
                    "logs": [
                        {
                            "id": 100,
                            "status": 200,
                            "request_data": {"event": "issue.created", "issue_id": 123},
                            "response_data": {"ok": True},
                            "created": "2025-01-20T15:00:00Z",
                        }
                    ],
                },
            )
        )

        get_result = await webhook_tools.get_webhook(auth_token=auth_token, webhook_id=10)

        assert get_result["id"] == 10
        assert get_result["project"]["id"] == project_id
        assert len(get_result["logs"]) == 1

        # 4. Probar webhook
        mock_taiga_api.post("https://api.taiga.io/api/v1/webhooks/10/test").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": 200,
                    "response_data": {"success": True, "message": "Test received"},
                    "headers": {"Content-Type": "application/json"},
                    "duration": 0.3,
                },
            )
        )

        test_result = await webhook_tools.test_webhook(auth_token=auth_token, webhook_id=10)

        assert test_result["status"] == 200
        assert test_result["response_data"]["success"] is True
        assert test_result["duration"] == 0.3

        # 5. Actualizar webhook
        mock_taiga_api.patch("https://api.taiga.io/api/v1/webhooks/10").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 10,
                    "name": "Slack Notifications Updated",
                    "url": "https://hooks.slack.com/services/T00/B00/YYY",
                    "key": "new_slack_secret",
                    "enabled": False,
                },
            )
        )

        update_result = await webhook_tools.update_webhook(
            auth_token=auth_token,
            webhook_id=10,
            name="Slack Notifications Updated",
            url="https://hooks.slack.com/services/T00/B00/YYY",
            key="new_slack_secret",
            enabled=False,
        )

        assert update_result["name"] == "Slack Notifications Updated"
        assert update_result["url"] == "https://hooks.slack.com/services/T00/B00/YYY"
        assert update_result["enabled"] is False

        # 6. Eliminar webhook
        mock_taiga_api.delete("https://api.taiga.io/api/v1/webhooks/10").mock(
            return_value=httpx.Response(204)
        )

        delete_result = await webhook_tools.delete_webhook(auth_token=auth_token, webhook_id=10)

        assert delete_result is True

    @pytest.mark.integration
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_multiple_webhooks_per_project(self, mock_taiga_api, auth_token) -> None:
        """
        Test de múltiples webhooks en un proyecto.
        """
        # Arrange
        mcp = FastMCP("Test Webhooks Integration")
        webhook_tools = WebhookTools(mcp)
        webhook_tools.register_tools()
        project_id = 123

        # Crear múltiples webhooks
        webhooks = [
            {"name": "Slack", "url": "https://hooks.slack.com/services/XXX", "key": "slack_key"},
            {"name": "Jenkins", "url": "https://jenkins.example.com/webhook", "key": "jenkins_key"},
            {"name": "GitHub Actions", "url": "https://github.com/webhook", "key": "github_key"},
        ]

        created_webhooks = []
        for i, webhook in enumerate(webhooks, start=1):
            mock_taiga_api.post("https://api.taiga.io/api/v1/webhooks").mock(
                return_value=httpx.Response(
                    201,
                    json={
                        "id": 10 + i,
                        "project": project_id,
                        "name": webhook["name"],
                        "url": webhook["url"],
                        "key": webhook["key"],
                        "enabled": True,
                    },
                )
            )

            result = await webhook_tools.create_webhook(
                auth_token=auth_token, project_id=project_id, **webhook
            )

            created_webhooks.append(result)
            assert result["name"] == webhook["name"]

        # Listar todos los webhooks (includes pagination params from AutoPaginator)
        mock_taiga_api.get(
            f"https://api.taiga.io/api/v1/webhooks?project={project_id}&page=1&page_size=100"
        ).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": 11,
                        "name": "Slack",
                        "url": "https://hooks.slack.com/services/XXX",
                        "enabled": True,
                    },
                    {
                        "id": 12,
                        "name": "Jenkins",
                        "url": "https://jenkins.example.com/webhook",
                        "enabled": True,
                    },
                    {
                        "id": 13,
                        "name": "GitHub Actions",
                        "url": "https://github.com/webhook",
                        "enabled": True,
                    },
                ],
            )
        )

        list_result = await webhook_tools.list_webhooks(
            auth_token=auth_token, project_id=project_id
        )

        assert len(list_result) == 3
        assert {w["name"] for w in list_result} == {"Slack", "Jenkins", "GitHub Actions"}

    @pytest.mark.integration
    @pytest.mark.webhooks
    @pytest.mark.asyncio
    async def test_webhook_test_with_failures(self, mock_taiga_api, auth_token) -> None:
        """
        Test de webhook con fallos en la prueba.
        """
        # Arrange
        mcp = FastMCP("Test Webhooks Integration")
        webhook_tools = WebhookTools(mcp)
        webhook_tools.register_tools()

        # Webhook que falla al probar
        mock_taiga_api.post("https://api.taiga.io/api/v1/webhooks/20/test").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": 500,
                    "response_data": {"error": "Internal server error"},
                    "headers": {"Content-Type": "text/html"},
                    "duration": 5.0,
                },
            )
        )

        # Act
        result = await webhook_tools.test_webhook(auth_token=auth_token, webhook_id=20)

        # Assert - El test devuelve el resultado aunque sea un error
        assert result["status"] == 500
        assert "error" in result["response_data"]
        assert result["duration"] == 5.0

        # Webhook con timeout
        mock_taiga_api.post("https://api.taiga.io/api/v1/webhooks/21/test").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": 0,
                    "response_data": {"error": "Connection timeout"},
                    "duration": 30.0,
                },
            )
        )

        timeout_result = await webhook_tools.test_webhook(auth_token=auth_token, webhook_id=21)

        assert timeout_result["status"] == 0
        assert "timeout" in timeout_result["response_data"]["error"].lower()
        assert timeout_result["duration"] == 30.0
