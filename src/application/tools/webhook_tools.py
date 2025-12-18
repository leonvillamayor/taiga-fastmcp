"""
Webhook management tools for Taiga MCP Server - Application layer.
"""

from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError as MCPError

from src.config import TaigaConfig
from src.domain.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    ResourceNotFoundError,
    TaigaAPIError,
    ValidationError,
)
from src.domain.validators import WebhookCreateValidator, WebhookUpdateValidator, validate_input
from src.infrastructure.logging import get_logger
from src.infrastructure.pagination import AutoPaginator, PaginationConfig
from src.taiga_client import TaigaAPIClient


class WebhookTools:
    """
    Webhook management tools for Taiga MCP Server.

    Provides MCP tools for managing webhooks in Taiga projects.
    """

    def __init__(self, mcp: FastMCP) -> None:
        """
        Initialize webhook tools.

        Args:
            mcp: FastMCP server instance
        """
        self.mcp = mcp
        self.config = TaigaConfig()
        self.client = None  # For backward compatibility
        self._logger = get_logger("webhook_tools")

    def set_client(self, client: Any) -> None:
        """Inject Taiga client for backward compatibility."""
        self.client = client

    def register_tools(self) -> None:
        """Register webhook tools with the MCP server."""

        # List webhooks
        @self.mcp.tool(name="taiga_list_webhooks", description="List project webhooks")
        async def list_webhooks(
            auth_token: str,
            project_id: int,
            auto_paginate: bool = True,
        ) -> list[dict[str, Any]]:
            """
            List webhooks for a project.

            Esta herramienta lista todos los webhooks configurados para un proyecto
            en Taiga, incluyendo su URL, estado y configuración.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto del que se quieren listar los webhooks
                auto_paginate: Si es True, obtiene automáticamente todas las páginas.
                    Si es False, retorna solo la primera página. Default: True.

            Returns:
                Lista de diccionarios con información de webhooks, cada uno conteniendo:
                - id: ID del webhook
                - project: ID del proyecto
                - name: Nombre del webhook
                - url: URL de destino del webhook
                - key: Clave secreta del webhook
                - enabled: Si el webhook está habilitado
                - created_date: Fecha de creación
                - modified_date: Fecha de última modificación

            Raises:
                MCPError: Si la autenticación falla o hay error en la API

            Example:
                >>> webhooks = await taiga_list_webhooks(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print(webhooks)
                [
                    {
                        "id": 1,
                        "project": 123,
                        "name": "Slack Integration",
                        "url": "https://hooks.slack.com/services/...",
                        "key": "secret123",
                        "enabled": True,
                        "created_date": "2024-01-15T10:30:00Z",
                        "modified_date": "2024-01-20T15:45:00Z"
                    }
                ]
            """
            self._logger.debug(f"[list_webhooks] Starting | project_id={project_id}")
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    paginator = AutoPaginator(client, PaginationConfig())
                    params = {"project": project_id}

                    if auto_paginate:
                        webhooks = await paginator.paginate("/webhooks", params=params)
                    else:
                        webhooks = await paginator.paginate_first_page("/webhooks", params=params)

                    if isinstance(webhooks, list):
                        result = [
                            {
                                "id": w.get("id"),
                                "project": w.get("project"),
                                "name": w.get("name"),
                                "url": w.get("url"),
                                "key": w.get("key"),
                                "enabled": w.get("enabled", True),
                                "created_date": w.get("created_date"),
                                "modified_date": w.get("modified_date"),
                            }
                            for w in webhooks
                        ]
                        self._logger.info(
                            f"[list_webhooks] Success | project_id={project_id}, count={len(result)}"
                        )
                        return result
                    self._logger.info(f"[list_webhooks] Success | project_id={project_id}, count=0")
                    return []

            except AuthenticationError:
                self._logger.error(
                    f"[list_webhooks] Authentication failed | project_id={project_id}"
                )
                raise MCPError("Authentication failed. Please authenticate first") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[list_webhooks] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Failed to list webhooks: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[list_webhooks] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.list_webhooks = list_webhooks.fn if hasattr(list_webhooks, "fn") else list_webhooks

        # Create webhook
        @self.mcp.tool(
            name="taiga_create_webhook", description="Create a new webhook for a project"
        )
        async def create_webhook(
            auth_token: str, project_id: int, name: str, url: str, key: str, enabled: bool = True
        ) -> dict[str, Any]:
            """
            Create a new webhook.

            Esta herramienta crea un nuevo webhook para un proyecto en Taiga.
            Los webhooks permiten recibir notificaciones HTTP cuando ocurren
            eventos en el proyecto.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde crear el webhook
                name: Nombre descriptivo del webhook
                url: URL de destino que recibirá las notificaciones
                key: Clave secreta para verificar autenticidad de las peticiones
                enabled: Si el webhook estará habilitado (por defecto: True)

            Returns:
                Dict con los siguientes campos:
                - id: ID del webhook creado
                - project: ID del proyecto
                - name: Nombre del webhook
                - url: URL de destino
                - key: Clave secreta
                - enabled: Estado de habilitación
                - created_date: Fecha de creación
                - message: Mensaje de confirmación

            Raises:
                MCPError: Si no hay permisos, ya existe, o falla la API

            Example:
                >>> webhook = await taiga_create_webhook(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     name="Slack Notifications",
                ...     url="https://hooks.slack.com/services/xxx",
                ...     key="my_secret_key",
                ...     enabled=True
                ... )
                >>> print(webhook)
                {
                    "id": 456,
                    "project": 123,
                    "name": "Slack Notifications",
                    "url": "https://hooks.slack.com/services/xxx",
                    "key": "my_secret_key",
                    "enabled": True,
                    "created_date": "2024-01-15T10:30:00Z",
                    "message": "Webhook 'Slack Notifications' created successfully"
                }
            """
            self._logger.debug(f"[create_webhook] Starting | project_id={project_id}, name={name}")
            try:
                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {
                    "project_id": project_id,
                    "name": name,
                    "url": url,
                    "key": key,
                    "enabled": enabled,
                }
                validate_input(WebhookCreateValidator, validation_data)

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token

                    webhook_data: dict[str, Any] = {
                        "project": project_id,  # API expects 'project'
                        "name": name,
                        "url": url,
                        "key": key,
                        "enabled": enabled,
                    }

                    webhook = await client.post("/webhooks", data=webhook_data)

                    result = {
                        "id": webhook.get("id"),
                        "project": webhook.get("project"),
                        "name": webhook.get("name"),
                        "url": webhook.get("url"),
                        "key": webhook.get("key"),
                        "enabled": webhook.get("enabled", True),
                        "created_date": webhook.get("created_date"),
                        "message": f"Webhook '{name}' created successfully",
                    }
                    self._logger.info(
                        f"[create_webhook] Success | webhook_id={result.get('id')}, name={name}"
                    )
                    return result

            except ValidationError as e:
                self._logger.warning(
                    f"[create_webhook] Validation error | project_id={project_id}, name={name}, error={e!s}"
                )
                raise MCPError(str(e)) from e
            except PermissionDeniedError:
                self._logger.error(f"[create_webhook] Permission denied | project_id={project_id}")
                raise MCPError("No permission to create webhooks in this project") from None
            except AuthenticationError:
                self._logger.error(
                    f"[create_webhook] Authentication failed | project_id={project_id}"
                )
                raise MCPError("Authentication failed. Please authenticate first") from None
            except TaigaAPIError as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    self._logger.error(
                        f"[create_webhook] Duplicate | project_id={project_id}, name={name}"
                    )
                    raise MCPError("A webhook with this name already exists") from e
                self._logger.error(
                    f"[create_webhook] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Failed to create webhook: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[create_webhook] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.create_webhook = create_webhook.fn if hasattr(create_webhook, "fn") else create_webhook

        # Get webhook
        @self.mcp.tool(name="taiga_get_webhook", description="Get webhook details")
        async def get_webhook(auth_token: str, webhook_id: int) -> dict[str, Any]:
            """
            Get webhook details.

            Esta herramienta obtiene los detalles de un webhook específico,
            incluyendo su configuración y logs de ejecución.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                webhook_id: ID del webhook a consultar

            Returns:
                Dict con los siguientes campos:
                - id: ID del webhook
                - project: ID del proyecto
                - name: Nombre del webhook
                - url: URL de destino
                - key: Clave secreta
                - enabled: Estado de habilitación
                - created_date: Fecha de creación
                - modified_date: Fecha de última modificación
                - logs_counter: Número de logs de ejecución
                - logs: Lista de logs recientes

            Raises:
                MCPError: Si el webhook no existe o falla la API

            Example:
                >>> webhook = await taiga_get_webhook(
                ...     auth_token="eyJ0eXAiOi...",
                ...     webhook_id=456
                ... )
                >>> print(webhook)
                {
                    "id": 456,
                    "project": 123,
                    "name": "Slack Notifications",
                    "url": "https://hooks.slack.com/services/xxx",
                    "key": "my_secret_key",
                    "enabled": True,
                    "created_date": "2024-01-15T10:30:00Z",
                    "modified_date": "2024-01-20T15:45:00Z",
                    "logs_counter": 25,
                    "logs": [{"status": 200, "created": "2024-01-20T15:45:00Z"}]
                }
            """
            self._logger.debug(f"[get_webhook] Starting | webhook_id={webhook_id}")
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    webhook = await client.get(f"/webhooks/{webhook_id}")

                    result = {
                        "id": webhook.get("id"),
                        "project": webhook.get("project"),
                        "name": webhook.get("name"),
                        "url": webhook.get("url"),
                        "key": webhook.get("key"),
                        "enabled": webhook.get("enabled", True),
                        "created_date": webhook.get("created_date"),
                        "modified_date": webhook.get("modified_date"),
                        "logs_counter": webhook.get("logs_counter", 0),
                        "logs": webhook.get("logs", []),
                    }
                    self._logger.info(f"[get_webhook] Success | webhook_id={webhook_id}")
                    return result

            except ResourceNotFoundError:
                self._logger.error(f"[get_webhook] Not found | webhook_id={webhook_id}")
                raise MCPError("Webhook not found") from None
            except AuthenticationError:
                self._logger.error(f"[get_webhook] Authentication failed | webhook_id={webhook_id}")
                raise MCPError("Authentication failed. Please authenticate first") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[get_webhook] API error | webhook_id={webhook_id}, error={e!s}"
                )
                raise MCPError(f"Failed to get webhook: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[get_webhook] Unexpected error | webhook_id={webhook_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.get_webhook = get_webhook.fn if hasattr(get_webhook, "fn") else get_webhook

        # Update webhook
        @self.mcp.tool(name="taiga_update_webhook", description="Update webhook configuration")
        async def update_webhook(
            auth_token: str,
            webhook_id: int,
            name: str | None = None,
            url: str | None = None,
            key: str | None = None,
            enabled: bool | None = None,
        ) -> dict[str, Any]:
            """
            Update webhook configuration.

            Esta herramienta permite actualizar la configuración de un webhook
            existente, modificando su nombre, URL, clave o estado.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                webhook_id: ID del webhook a actualizar
                name: Nuevo nombre del webhook (opcional)
                url: Nueva URL de destino (opcional)
                key: Nueva clave secreta (opcional)
                enabled: Nuevo estado de habilitación (opcional)

            Returns:
                Dict con los siguientes campos:
                - id: ID del webhook
                - project: ID del proyecto
                - name: Nombre actualizado
                - url: URL actualizada
                - key: Clave actualizada
                - enabled: Estado de habilitación
                - modified_date: Fecha de modificación
                - message: Mensaje de confirmación

            Raises:
                MCPError: Si no hay permisos, no existe, o falla la API

            Example:
                >>> webhook = await taiga_update_webhook(
                ...     auth_token="eyJ0eXAiOi...",
                ...     webhook_id=456,
                ...     name="Updated Webhook Name",
                ...     enabled=False
                ... )
                >>> print(webhook)
                {
                    "id": 456,
                    "project": 123,
                    "name": "Updated Webhook Name",
                    "url": "https://hooks.slack.com/services/xxx",
                    "key": "my_secret_key",
                    "enabled": False,
                    "modified_date": "2024-01-25T12:00:00Z",
                    "message": "Webhook 456 updated successfully"
                }
            """
            self._logger.debug(f"[update_webhook] Starting | webhook_id={webhook_id}")
            try:
                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {
                    "webhook_id": webhook_id,
                    "name": name,
                    "url": url,
                    "key": key,
                    "enabled": enabled,
                }
                validate_input(WebhookUpdateValidator, validation_data)

                update_data = {}
                if name is not None:
                    update_data["name"] = name
                if url is not None:
                    update_data["url"] = url
                if key is not None:
                    update_data["key"] = key
                if enabled is not None:
                    update_data["enabled"] = enabled

                if not update_data:
                    self._logger.error(
                        f"[update_webhook] No data provided | webhook_id={webhook_id}"
                    )
                    raise MCPError("No update data provided")

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    webhook = await client.patch(f"/webhooks/{webhook_id}", data=update_data)

                    result = {
                        "id": webhook.get("id"),
                        "project": webhook.get("project"),
                        "name": webhook.get("name"),
                        "url": webhook.get("url"),
                        "key": webhook.get("key"),
                        "enabled": webhook.get("enabled", True),
                        "modified_date": webhook.get("modified_date"),
                        "message": f"Webhook {webhook_id} updated successfully",
                    }
                    self._logger.info(f"[update_webhook] Success | webhook_id={webhook_id}")
                    return result

            except ValidationError as e:
                self._logger.warning(
                    f"[update_webhook] Validation error | webhook_id={webhook_id}, error={e!s}"
                )
                raise MCPError(str(e)) from e
            except ResourceNotFoundError:
                self._logger.error(f"[update_webhook] Not found | webhook_id={webhook_id}")
                raise MCPError("Webhook not found") from None
            except PermissionDeniedError:
                self._logger.error(f"[update_webhook] Permission denied | webhook_id={webhook_id}")
                raise MCPError("No permission to update this webhook") from None
            except AuthenticationError:
                self._logger.error(
                    f"[update_webhook] Authentication failed | webhook_id={webhook_id}"
                )
                raise MCPError("Authentication failed. Please authenticate first") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[update_webhook] API error | webhook_id={webhook_id}, error={e!s}"
                )
                raise MCPError(f"Failed to update webhook: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[update_webhook] Unexpected error | webhook_id={webhook_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.update_webhook = update_webhook.fn if hasattr(update_webhook, "fn") else update_webhook

        # Delete webhook
        @self.mcp.tool(name="taiga_delete_webhook", description="Delete a webhook")
        async def delete_webhook(auth_token: str, webhook_id: int) -> bool:
            """
            Delete a webhook.

            Esta herramienta elimina un webhook de un proyecto en Taiga.
            Una vez eliminado, el webhook dejará de enviar notificaciones.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                webhook_id: ID del webhook a eliminar

            Returns:
                True si la eliminación fue exitosa

            Raises:
                MCPError: Si no hay permisos, no existe, o falla la API

            Example:
                >>> result = await taiga_delete_webhook(
                ...     auth_token="eyJ0eXAiOi...",
                ...     webhook_id=456
                ... )
                >>> print(result)
                True
            """
            self._logger.debug(f"[delete_webhook] Starting | webhook_id={webhook_id}")
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    result = await client.delete(f"/webhooks/{webhook_id}")
                    self._logger.info(f"[delete_webhook] Success | webhook_id={webhook_id}")
                    return result

            except ResourceNotFoundError:
                self._logger.error(f"[delete_webhook] Not found | webhook_id={webhook_id}")
                raise MCPError("Webhook not found") from None
            except PermissionDeniedError:
                self._logger.error(f"[delete_webhook] Permission denied | webhook_id={webhook_id}")
                raise MCPError("No permission to delete this webhook") from None
            except AuthenticationError:
                self._logger.error(
                    f"[delete_webhook] Authentication failed | webhook_id={webhook_id}"
                )
                raise MCPError("Authentication failed. Please authenticate first") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[delete_webhook] API error | webhook_id={webhook_id}, error={e!s}"
                )
                raise MCPError(f"Failed to delete webhook: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[delete_webhook] Unexpected error | webhook_id={webhook_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.delete_webhook = delete_webhook.fn if hasattr(delete_webhook, "fn") else delete_webhook

        # Test webhook
        @self.mcp.tool(
            name="taiga_test_webhook", description="Test a webhook by sending a test payload"
        )
        async def test_webhook(auth_token: str, webhook_id: int) -> dict[str, Any]:
            """
            Test a webhook by sending a test payload.

            Esta herramienta envía una petición de prueba al webhook para verificar
            que está configurado correctamente y puede recibir notificaciones.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                webhook_id: ID del webhook a probar

            Returns:
                Dict con los siguientes campos:
                - success: True si la prueba fue exitosa
                - status: Código de estado HTTP de la respuesta
                - response_data: Datos de la respuesta
                - headers: Headers de la respuesta
                - duration: Duración de la petición en milisegundos
                - message: Mensaje descriptivo del resultado

            Raises:
                MCPError: Si no hay permisos, no existe, timeout, o falla la conexión

            Example:
                >>> result = await taiga_test_webhook(
                ...     auth_token="eyJ0eXAiOi...",
                ...     webhook_id=456
                ... )
                >>> print(result)
                {
                    "success": True,
                    "status": 200,
                    "response_data": {"ok": True},
                    "headers": {"content-type": "application/json"},
                    "duration": 150,
                    "message": "Test webhook sent successfully"
                }
            """
            self._logger.debug(f"[test_webhook] Starting | webhook_id={webhook_id}")
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    result = await client.post(f"/webhooks/{webhook_id}/test", data={})

                    response = {
                        "success": result.get("status", 200) == 200,
                        "status": result.get("status", 200),
                        "response_data": result.get("response_data", {}),
                        "headers": result.get("headers", {}),
                        "duration": result.get("duration", 0),
                        "message": result.get("message", "Test webhook sent successfully"),
                    }
                    self._logger.info(
                        f"[test_webhook] Success | webhook_id={webhook_id}, status={response.get('status')}"
                    )
                    return response

            except ResourceNotFoundError:
                self._logger.error(f"[test_webhook] Not found | webhook_id={webhook_id}")
                raise MCPError("Webhook not found") from None
            except PermissionDeniedError:
                self._logger.error(f"[test_webhook] Permission denied | webhook_id={webhook_id}")
                raise MCPError("No permission to test this webhook") from None
            except AuthenticationError:
                self._logger.error(
                    f"[test_webhook] Authentication failed | webhook_id={webhook_id}"
                )
                raise MCPError("Authentication failed. Please authenticate first") from None
            except TaigaAPIError as e:
                # Check for specific webhook test failures
                error_msg = str(e).lower()
                if "timeout" in error_msg:
                    self._logger.error(f"[test_webhook] Timeout | webhook_id={webhook_id}")
                    raise MCPError("Webhook test failed: Connection timeout") from e
                if "connection" in error_msg or "refused" in error_msg:
                    self._logger.error(
                        f"[test_webhook] Connection refused | webhook_id={webhook_id}"
                    )
                    raise MCPError("Webhook test failed: Connection refused") from e
                if "404" in error_msg or "not found" in error_msg:
                    self._logger.error(
                        f"[test_webhook] Endpoint not found | webhook_id={webhook_id}"
                    )
                    raise MCPError("Webhook test failed: Endpoint not found") from e
                self._logger.error(
                    f"[test_webhook] API error | webhook_id={webhook_id}, error={e!s}"
                )
                raise MCPError(f"Webhook test failed: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[test_webhook] Unexpected error | webhook_id={webhook_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.test_webhook = test_webhook.fn if hasattr(test_webhook, "fn") else test_webhook

    # Legacy methods for backward compatibility
    def _register_tools(self) -> None:
        """Legacy registration method."""
        self.register_tools()
