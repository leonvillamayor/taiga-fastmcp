"""
Tests funcionales para herramientas MCP de épicas.
Implementa tests end-to-end para todas las herramientas (RF-001 a RF-026).
"""

import pytest


@pytest.mark.functional
@pytest.mark.asyncio
class TestEpicToolsMCP:
    """Tests funcionales para herramientas MCP de épicas"""

    @pytest.fixture
    def epic_tools(self, mock_mcp_server, mock_taiga_client, monkeypatch) -> None:
        """Fixture para EpicTools con mocks configurados."""
        from unittest.mock import AsyncMock, MagicMock

        from fastmcp import FastMCP

        from src.application.tools.epic_tools import EpicTools

        # Ensure mock_taiga_client.get is AsyncMock for AutoPaginator
        if not isinstance(mock_taiga_client.get, AsyncMock):
            mock_taiga_client.get = AsyncMock(return_value=[])

        # Patch TaigaAPIClient to use the mock
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_taiga_client)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        monkeypatch.setattr(
            "src.application.tools.epic_tools.TaigaAPIClient",
            lambda config: mock_client_instance,
        )

        mcp = FastMCP("Test")
        tools = EpicTools(mcp)
        tools.register_tools()
        return tools

    # ==================== CRUD BÁSICO ====================

    async def test_list_epics_tool(self, epic_tools, mock_taiga_client, epic_response_data) -> None:
        """
        RF-001: Herramienta MCP para listar épicas.

        Verifica la herramienta list_epics con todos los filtros.
        """
        from unittest.mock import AsyncMock

        # Arrange - AutoPaginator calls client.get() not list_epics
        mock_taiga_client.get = AsyncMock(return_value=[epic_response_data])

        # Act - Usamos nombres de parámetros del API interno (project, no project_id)
        result = await epic_tools.list_epics(
            auth_token="Bearer token",
            project=309804,
            assigned_to=888691,
            status=1,
            tags=["auth", "security"],
        )

        # Assert
        # El método devuelve la lista directamente, no un string JSON
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == 456789
        # AutoPaginator calls client.get("/epics", params={...})
        mock_taiga_client.get.assert_called()
        call_args = mock_taiga_client.get.call_args
        assert call_args[0][0] == "/epics"
        params = call_args[1].get("params", call_args[0][1] if len(call_args[0]) > 1 else {})
        assert params.get("project") == 309804

    async def test_create_epic_tool(
        self, epic_tools, mock_taiga_client, valid_epic_data, epic_response_data
    ):
        """
        RF-002: Herramienta MCP para crear épica.

        Verifica la herramienta create_epic con todos los campos.
        """
        # Arrange
        mock_taiga_client.create_epic.return_value = epic_response_data

        # Act
        result = await epic_tools.create_epic(auth_token="Bearer token", **valid_epic_data)

        # Assert
        assert isinstance(result, dict)
        assert result["id"] == 456789
        assert result["subject"] == valid_epic_data["subject"]
        mock_taiga_client.create_epic.assert_called_once()

    async def test_create_epic_validation_error(self, epic_tools, invalid_epic_colors) -> None:
        """
        RNF-004: Validación de datos en herramienta create_epic.

        Verifica validación de color inválido.
        """
        # Arrange
        # Act & Assert
        for invalid_color in invalid_epic_colors:
            with pytest.raises(
                ValueError, match=r"Invalid color format|project and subject are required"
            ):
                await epic_tools.create_epic(
                    auth_token="Bearer token",
                    project_id=309804,
                    subject="Test Epic",
                    color=invalid_color,
                )

    async def test_get_epic_tool(self, epic_tools, mock_taiga_client, epic_response_data) -> None:
        """
        RF-003: Herramienta MCP para obtener épica por ID.

        Verifica la herramienta get_epic.
        """
        # Arrange
        mock_taiga_client.get_epic.return_value = epic_response_data

        # Act
        result = await epic_tools.get_epic(auth_token="Bearer token", epic_id=456789)

        # Assert - El método devuelve un dict, no un string JSON
        assert isinstance(result, dict)
        assert result["id"] == 456789
        mock_taiga_client.get_epic.assert_called_once_with(456789)

    async def test_get_epic_by_ref_tool(
        self, epic_tools, mock_taiga_client, epic_response_data
    ) -> None:
        """
        RF-004: Herramienta MCP para obtener épica por referencia.

        Verifica la herramienta get_epic_by_ref.
        """
        # Arrange
        mock_taiga_client.get_epic_by_ref.return_value = epic_response_data

        # Act - El método interno espera project_id y lo traduce internamente
        result = await epic_tools.get_epic_by_ref(
            auth_token="Bearer token", ref=5, project_id=309804
        )

        # Assert - El método devuelve un dict, no un string JSON
        assert isinstance(result, dict)
        assert result["ref"] == 5
        assert result["project"] == 309804
        mock_taiga_client.get_epic_by_ref.assert_called_once_with(ref=5, project_id=309804)

    async def test_update_epic_tool(
        self, epic_tools, mock_taiga_client, epic_response_data
    ) -> None:
        """
        RF-005: Herramienta MCP para actualización completa.

        Verifica la herramienta update_epic (PUT).
        """
        # Arrange
        updated_epic = dict(epic_response_data)
        updated_epic["version"] = 2
        updated_epic["subject"] = "Updated Epic"
        mock_taiga_client.update_epic_full.return_value = updated_epic

        # Act - Usamos project, no project_id
        result = await epic_tools.update_epic(
            auth_token="Bearer token",
            epic_id=456789,
            version=1,
            subject="Updated Epic",
            project=309804,
        )

        # Assert - El método devuelve un dict, no un string JSON
        assert isinstance(result, dict)
        assert result["version"] == 2
        assert result["subject"] == "Updated Epic"
        mock_taiga_client.update_epic_full.assert_called_once()

    async def test_patch_epic_tool(self, epic_tools, mock_taiga_client, epic_response_data) -> None:
        """
        RF-006: Herramienta MCP para actualización parcial.

        Verifica la herramienta patch_epic (PATCH).
        """
        # Arrange
        updated_epic = dict(epic_response_data)
        updated_epic["status"] = 2
        mock_taiga_client.update_epic.return_value = updated_epic

        # Act
        result = await epic_tools.patch_epic(
            auth_token="Bearer token", epic_id=456789, version=1, status=2
        )

        # Assert - El método devuelve un dict, no un string JSON
        assert isinstance(result, dict)
        assert result["status"] == 2
        mock_taiga_client.update_epic.assert_called_once()

    async def test_delete_epic_tool(self, epic_tools, mock_taiga_client) -> None:
        """
        RF-007: Herramienta MCP para eliminar épica.

        Verifica la herramienta delete_epic.
        """
        # Arrange
        mock_taiga_client.delete_epic.return_value = None

        # Act
        result = await epic_tools.delete_epic(auth_token="Bearer token", epic_id=456789)

        # Assert - El método devuelve un dict con success y message (SuccessResponse)
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "deleted" in result["message"]
        mock_taiga_client.delete_epic.assert_called_once_with(456789)

    async def test_bulk_create_epics_tool(
        self, epic_tools, mock_taiga_client, multiple_epics_data
    ) -> None:
        """
        RF-008: Herramienta MCP para crear múltiples épicas.

        Verifica la herramienta bulk_create_epics.
        """
        # Arrange
        created_epics = [{"id": 456789 + i, **epic} for i, epic in enumerate(multiple_epics_data)]
        mock_taiga_client.bulk_create_epics.return_value = created_epics

        # Act - El método interno espera project_id
        result = await epic_tools.bulk_create_epics(
            auth_token="Bearer token", project_id=309804, bulk_epics=multiple_epics_data
        )

        # Assert - El método devuelve una lista, no un string JSON
        assert isinstance(result, list)
        assert len(result) == 3
        mock_taiga_client.bulk_create_epics.assert_called_once()

    # ==================== RELACIONES EPIC-USERSTORY ====================

    async def test_list_related_userstories_tool(
        self, epic_tools, mock_taiga_client, related_userstory_data
    ):
        """
        RF-009: Herramienta MCP para listar user stories relacionadas.

        Verifica la herramienta list_related_userstories.
        """
        # Arrange
        mock_taiga_client.list_epic_related_userstories.return_value = [related_userstory_data]

        # Act
        result = await epic_tools.list_related_userstories(
            auth_token="Bearer token", epic_id=456789
        )

        # Assert - El método devuelve una lista, no un string JSON
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == 123
        assert result[0]["epic"] == 456789
        mock_taiga_client.list_epic_related_userstories.assert_called_once_with(456789)

    async def test_create_related_userstory_tool(
        self, epic_tools, mock_taiga_client, related_userstory_data
    ):
        """
        RF-010: Herramienta MCP para relacionar user story con épica.

        Verifica la herramienta create_related_userstory.
        """
        # Arrange
        mock_taiga_client.create_epic_related_userstory.return_value = related_userstory_data

        # Act - Usamos user_story, no user_story_id (parámetro interno)
        result = await epic_tools.create_related_userstory(
            auth_token="Bearer token", epic_id=456789, user_story=123456, order=1
        )

        # Assert - El método devuelve un dict, no un string JSON
        assert isinstance(result, dict)
        assert result["epic"] == 456789
        assert result["user_story"]["id"] == 123456
        mock_taiga_client.create_epic_related_userstory.assert_called_once()

    async def test_bulk_create_related_userstories_tool(
        self, epic_tools, mock_taiga_client, bulk_userstories_ids
    ):
        """
        RF-014: Herramienta MCP para relacionar múltiples user stories.

        Verifica la herramienta bulk_create_related_userstories.
        """
        # Arrange
        created_relations = [
            {"id": i, "epic": 456789, "user_story": us_id, "order": i}
            for i, us_id in enumerate(bulk_userstories_ids, 1)
        ]
        # El código usa bulk_create_related_userstories (sin "epic") como primera opción
        mock_taiga_client.bulk_create_related_userstories.return_value = created_relations

        # Act
        result = await epic_tools.bulk_create_related_userstories(
            auth_token="Bearer token", epic_id=456789, bulk_userstories=bulk_userstories_ids
        )

        # Assert - El método devuelve una lista, no un string JSON
        assert isinstance(result, list)
        assert len(result) == 4
        mock_taiga_client.bulk_create_related_userstories.assert_called_once()

    # ==================== VOTACIÓN ====================

    async def test_upvote_epic_tool(
        self, epic_tools, mock_taiga_client, epic_response_data
    ) -> None:
        """
        RF-016: Herramienta MCP para votar épica.

        Verifica la herramienta upvote_epic.
        """
        # Arrange
        updated_epic = dict(epic_response_data)
        updated_epic["total_voters"] = 1
        mock_taiga_client.upvote_epic.return_value = updated_epic

        # Act
        result = await epic_tools.upvote_epic(auth_token="Bearer token", epic_id=456789)

        # Assert - El método devuelve un dict con success y message (SuccessResponse)
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "upvoted" in result["message"]
        mock_taiga_client.upvote_epic.assert_called_once_with(456789)

    async def test_downvote_epic_tool(
        self, epic_tools, mock_taiga_client, epic_response_data
    ) -> None:
        """
        RF-017: Herramienta MCP para quitar voto.

        Verifica la herramienta downvote_epic.
        """
        # Arrange
        updated_epic = dict(epic_response_data)
        updated_epic["total_voters"] = 0
        mock_taiga_client.downvote_epic.return_value = updated_epic

        # Act
        result = await epic_tools.downvote_epic(auth_token="Bearer token", epic_id=456789)

        # Assert - El método devuelve un dict con success y message (SuccessResponse)
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "downvoted" in result["message"]
        mock_taiga_client.downvote_epic.assert_called_once_with(456789)

    async def test_get_epic_voters_tool(
        self, epic_tools, mock_taiga_client, epic_voters_data
    ) -> None:
        """
        RF-018: Herramienta MCP para obtener votantes.

        Verifica la herramienta get_epic_voters.
        """
        # Arrange
        mock_taiga_client.get_epic_voters.return_value = epic_voters_data

        # Act
        result = await epic_tools.get_epic_voters(auth_token="Bearer token", epic_id=456789)

        # Assert - El método devuelve una lista, no un string JSON
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["username"] == "john.doe"
        mock_taiga_client.get_epic_voters.assert_called_once_with(456789)

    # ==================== OBSERVADORES ====================

    async def test_watch_epic_tool(self, epic_tools, mock_taiga_client, epic_response_data) -> None:
        """
        RF-019: Herramienta MCP para observar épica.

        Verifica la herramienta watch_epic.
        """
        # Arrange
        updated_epic = dict(epic_response_data)
        updated_epic["watchers"] = [888691, 888692]
        mock_taiga_client.watch_epic.return_value = updated_epic

        # Act
        result = await epic_tools.watch_epic(auth_token="Bearer token", epic_id=456789)

        # Assert - El método devuelve un dict con success y message (SuccessResponse)
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "watching" in result["message"]
        mock_taiga_client.watch_epic.assert_called_once_with(456789)

    async def test_unwatch_epic_tool(
        self, epic_tools, mock_taiga_client, epic_response_data
    ) -> None:
        """
        RF-020: Herramienta MCP para dejar de observar.

        Verifica la herramienta unwatch_epic.
        """
        # Arrange
        updated_epic = dict(epic_response_data)
        updated_epic["watchers"] = []
        mock_taiga_client.unwatch_epic.return_value = updated_epic

        # Act
        result = await epic_tools.unwatch_epic(auth_token="Bearer token", epic_id=456789)

        # Assert - El método devuelve un dict con success y message (SuccessResponse)
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "watching" in result["message"]
        mock_taiga_client.unwatch_epic.assert_called_once_with(456789)

    async def test_get_epic_watchers_tool(
        self, epic_tools, mock_taiga_client, epic_watchers_data
    ) -> None:
        """
        RF-021: Herramienta MCP para obtener observadores.

        Verifica la herramienta get_epic_watchers.
        """
        # Arrange
        mock_taiga_client.get_epic_watchers.return_value = epic_watchers_data

        # Act
        result = await epic_tools.get_epic_watchers(auth_token="Bearer token", epic_id=456789)

        # Assert - El método devuelve una lista, no un string JSON
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["username"] == "john.doe"
        mock_taiga_client.get_epic_watchers.assert_called_once_with(456789)

    # ==================== ADJUNTOS ====================

    async def test_list_epic_attachments_tool(
        self, epic_tools, mock_taiga_client, epic_attachment_data
    ):
        """
        RF-022: Herramienta MCP para listar adjuntos.

        Verifica la herramienta list_epic_attachments.
        """
        # Arrange
        mock_taiga_client.list_epic_attachments.return_value = [epic_attachment_data]

        # Act - Usamos project, no project_id (parámetro interno)
        result = await epic_tools.list_epic_attachments(
            auth_token="Bearer token", epic_id=456789, project=309804
        )

        # Assert - El método devuelve una lista, no un string JSON
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "requirements.pdf"
        mock_taiga_client.list_epic_attachments.assert_called_once()

    async def test_create_epic_attachment_tool(
        self, epic_tools, mock_taiga_client, epic_attachment_data
    ):
        """
        RF-023: Herramienta MCP para crear adjunto.

        Verifica la herramienta create_epic_attachment.
        """
        # Arrange
        mock_taiga_client.create_epic_attachment.return_value = epic_attachment_data

        # Act - Usamos project, no project_id (parámetro interno)
        result = await epic_tools.create_epic_attachment(
            auth_token="Bearer token",
            project=309804,
            object_id=456789,
            attached_file="path/to/file.pdf",
            description="Test attachment",
        )

        # Assert - El método devuelve un dict, no un string JSON
        assert isinstance(result, dict)
        assert result["id"] == 789012
        assert result["name"] == "requirements.pdf"
        mock_taiga_client.create_epic_attachment.assert_called_once()

    # ==================== FILTROS ====================

    async def test_get_epic_filters_tool(
        self, epic_tools, mock_taiga_client, epic_filters_data
    ) -> None:
        """
        RF-015: Herramienta MCP para obtener filtros.

        Verifica la herramienta get_epic_filters.
        """
        # Arrange
        mock_taiga_client.get_epic_filters.return_value = epic_filters_data

        # Act - El método interno espera project_id y lo traduce internamente
        result = await epic_tools.get_epic_filters(auth_token="Bearer token", project_id=309804)

        # Assert - El método devuelve un dict, no un string JSON
        assert isinstance(result, dict)
        assert "statuses" in result
        assert "assigned_to" in result
        assert "tags" in result
        assert len(result["statuses"]) == 5
        mock_taiga_client.get_epic_filters.assert_called_once_with(project=309804)

    # ==================== MANEJO DE ERRORES ====================

    async def test_authentication_error_handling(self, epic_tools, mock_taiga_client) -> None:
        """
        RNF-003: Manejo de errores de autenticación (401).

        Verifica manejo correcto de error 401.
        """
        from unittest.mock import AsyncMock

        # Arrange
        from fastmcp.exceptions import ToolError

        from src.domain.exceptions import AuthenticationError

        # AutoPaginator calls client.get(), not list_epics
        mock_taiga_client.get = AsyncMock(side_effect=AuthenticationError("Invalid token"))

        # Act & Assert
        with pytest.raises(ToolError, match="Authentication failed"):
            await epic_tools.list_epics(auth_token="invalid_token")

    async def test_permission_error_handling(self, epic_tools, mock_taiga_client) -> None:
        """
        RNF-003: Manejo de errores de permisos (403).

        Verifica manejo correcto de error 403.
        """
        # Arrange
        from fastmcp.exceptions import ToolError

        from src.domain.exceptions import PermissionDeniedError

        mock_taiga_client.delete_epic.side_effect = PermissionDeniedError("No permission")

        # Act & Assert
        with pytest.raises(ToolError, match="Permission denied"):
            await epic_tools.delete_epic(auth_token="Bearer token", epic_id=456789)

    async def test_not_found_error_handling(self, epic_tools, mock_taiga_client) -> None:
        """
        RNF-003: Manejo de errores 404.

        Verifica manejo correcto de recurso no encontrado.
        """
        # Arrange
        from fastmcp.exceptions import ToolError

        from src.domain.exceptions import ResourceNotFoundError

        mock_taiga_client.get_epic.side_effect = ResourceNotFoundError("Epic not found")

        # Act & Assert
        with pytest.raises(ToolError, match="Epic not found"):
            await epic_tools.get_epic(auth_token="Bearer token", epic_id=999999)

    async def test_version_conflict_error_handling(self, epic_tools, mock_taiga_client) -> None:
        """
        RNF-003: Manejo de errores de concurrencia (409).

        Verifica manejo correcto de conflicto de versión.
        """
        # Arrange
        from fastmcp.exceptions import ToolError

        from src.domain.exceptions import ConcurrencyError

        mock_taiga_client.update_epic_full.side_effect = ConcurrencyError("Version conflict")

        # Act & Assert - Usamos project, no project_id (parámetro interno)
        with pytest.raises(ToolError, match="Version conflict"):
            await epic_tools.update_epic(
                auth_token="Bearer token",
                epic_id=456789,
                version=0,
                subject="Updated",
                project=309804,
            )

    # ==================== COMPATIBILIDAD MCP ====================

    async def test_mcp_tool_registration(self, mock_mcp_server) -> None:
        """
        RNF-008: Herramientas registradas correctamente en MCP.

        Verifica que todas las herramientas estén registradas.
        """
        # Arrange
        from fastmcp import FastMCP

        from src.application.tools.epic_tools import EpicTools

        mcp = FastMCP("Test")
        tools = EpicTools(mcp)

        # Act
        tools.register_tools()

        # Assert
        registered_tools = await mcp.get_tools()
        registered_tool_names = list(registered_tools.keys())
        expected_tools = [
            "taiga_list_epics",
            "taiga_create_epic",
            "taiga_get_epic",
            "taiga_get_epic_by_ref",
            "taiga_update_epic_full",
            "taiga_update_epic_partial",
            "taiga_delete_epic",
            "taiga_bulk_create_epics",
            "taiga_list_epic_related_userstories",
            "taiga_create_epic_related_userstory",
            "taiga_update_epic_related_userstory",
            "taiga_delete_epic_related_userstory",
            "taiga_get_epic_filters",
            "taiga_upvote_epic",
            "taiga_downvote_epic",
            "taiga_get_epic_voters",
            "taiga_watch_epic",
            "taiga_unwatch_epic",
            "taiga_get_epic_watchers",
            "taiga_list_epic_attachments",
            "taiga_create_epic_attachment",
            "taiga_get_epic_attachment",
            "taiga_update_epic_attachment",
            "taiga_delete_epic_attachment",
        ]

        for tool_name in expected_tools:
            assert tool_name in registered_tool_names, f"Tool {tool_name} not registered"

    async def test_mcp_tool_schemas(self, mock_mcp_server) -> None:
        """
        RNF-008: Schemas de herramientas validados con Pydantic.

        Verifica que las herramientas tengan schemas correctos.
        """
        # Arrange
        from fastmcp import FastMCP

        from src.application.tools.epic_tools import EpicTools

        mcp = FastMCP("Test")
        tools = EpicTools(mcp)
        tools.register_tools()

        # Act & Assert
        for tool_name in ["taiga_create_epic", "taiga_update_epic_full", "taiga_list_epics"]:
            tool = await mcp.get_tool(tool_name)
            assert tool is not None, f"Tool {tool_name} not found"
            assert hasattr(tool, "name"), f"Tool {tool_name} doesn't have name"
            assert tool.name == tool_name, "Tool name mismatch"

            # Verificar que la herramienta tiene un schema de entrada
            assert hasattr(tool, "input_schema") or hasattr(
                tool, "fn"
            ), f"Tool {tool_name} doesn't have input_schema or fn"
