"""
Tests adicionales para mejorar la cobertura de epic_tools.py.
Enfocados en: manejo de errores, edge cases, y rutas de código no cubiertas.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.application.tools.epic_tools import EpicTools
from src.domain.exceptions import (
    AuthenticationError,
    ConcurrencyError,
    PermissionDeniedError,
    ResourceNotFoundError,
    ValidationError,
)


@pytest.fixture
def epic_tools_instance():
    """Crea una instancia de EpicTools con mocks."""
    mcp = FastMCP("Test")

    with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        tools = EpicTools(mcp)
        tools._mock_client = mock_client
        tools._mock_client_cls = mock_client_cls

        yield tools


class TestListEpicsErrorHandling:
    """Tests para manejo de errores en list_epics."""

    @pytest.mark.asyncio
    async def test_list_epics_authentication_error(self, epic_tools_instance):
        """Test que list_epics maneja AuthenticationError correctamente."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            # Simular error de paginación
            from src.infrastructure.pagination import AutoPaginator

            with patch.object(
                AutoPaginator, "paginate", side_effect=AuthenticationError("Invalid token")
            ):
                with pytest.raises(ToolError) as exc_info:
                    await epic_tools_instance.list_epics(auth_token="invalid", project=123)
                assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_epics_permission_denied_error(self, epic_tools_instance):
        """Test que list_epics maneja PermissionDeniedError correctamente."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            from src.infrastructure.pagination import AutoPaginator

            with patch.object(
                AutoPaginator, "paginate", side_effect=PermissionDeniedError("No access")
            ):
                with pytest.raises(ToolError) as exc_info:
                    await epic_tools_instance.list_epics(auth_token="token", project=123)
                assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_epics_resource_not_found_error(self, epic_tools_instance):
        """Test que list_epics maneja ResourceNotFoundError correctamente."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            from src.infrastructure.pagination import AutoPaginator

            with patch.object(
                AutoPaginator, "paginate", side_effect=ResourceNotFoundError("Not found")
            ):
                with pytest.raises(ToolError) as exc_info:
                    await epic_tools_instance.list_epics(auth_token="token", project=999)
                assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_list_epics_generic_error(self, epic_tools_instance):
        """Test que list_epics maneja excepciones genéricas."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            from src.infrastructure.pagination import AutoPaginator

            with patch.object(AutoPaginator, "paginate", side_effect=Exception("Network error")):
                with pytest.raises(ToolError) as exc_info:
                    await epic_tools_instance.list_epics(auth_token="token", project=123)
                assert "Error listing epics" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_epics_without_auto_paginate(self, epic_tools_instance):
        """Test list_epics con auto_paginate=False."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            from src.infrastructure.pagination import AutoPaginator

            with patch.object(
                AutoPaginator,
                "paginate_first_page",
                return_value=[{"id": 1, "ref": 1, "subject": "Epic 1", "project": 123}],
            ) as mock_paginate:
                result = await epic_tools_instance.list_epics(
                    auth_token="token", project=123, auto_paginate=False
                )
                mock_paginate.assert_called_once()
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_epics_with_all_filters(self, epic_tools_instance):
        """Test list_epics con todos los filtros activos."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            from src.infrastructure.pagination import AutoPaginator

            with patch.object(
                AutoPaginator,
                "paginate",
                return_value=[
                    {
                        "id": 1,
                        "ref": 1,
                        "subject": "Epic 1",
                        "project": 123,
                        "status": 2,
                        "assigned_to": 456,
                    }
                ],
            ) as mock_paginate:
                await epic_tools_instance.list_epics(
                    auth_token="token", project=123, status=2, assigned_to=456
                )
                # Verificar que se pasaron los parámetros correctos
                call_args = mock_paginate.call_args
                assert call_args[1]["params"]["project"] == 123
                assert call_args[1]["params"]["status"] == 2
                assert call_args[1]["params"]["assigned_to"] == 456


class TestCreateEpicErrorHandling:
    """Tests para manejo de errores en create_epic."""

    @pytest.mark.asyncio
    async def test_create_epic_missing_project(self, epic_tools_instance):
        """Test que create_epic falla sin project."""
        with pytest.raises(ValueError) as exc_info:
            await epic_tools_instance.create_epic(auth_token="token", subject="Test Epic")
        assert "project and subject are required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_epic_missing_subject(self, epic_tools_instance):
        """Test que create_epic falla sin subject."""
        with pytest.raises(ValueError) as exc_info:
            await epic_tools_instance.create_epic(auth_token="token", project=123)
        assert "project and subject are required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_epic_validation_error(self, epic_tools_instance):
        """Test que create_epic maneja ValidationError de validate_input (propagado directamente)."""
        with patch("src.application.tools.epic_tools.validate_input") as mock_validate:
            mock_validate.side_effect = ValidationError("Invalid color format")
            # ValidationError desde validate_input se propaga directamente (no está en try block)
            with pytest.raises(ValidationError) as exc_info:
                await epic_tools_instance.create_epic(
                    auth_token="token", project=123, subject="Test", color="invalid"
                )
            assert "Invalid color format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_epic_with_all_parameters(self, epic_tools_instance):
        """Test create_epic con todos los parámetros opcionales."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic = AsyncMock(
                return_value={
                    "id": 1,
                    "ref": 1,
                    "subject": "Full Epic",
                    "description": "Description",
                    "color": "#FF0000",
                    "project": 123,
                    "assigned_to": 456,
                    "status": 2,
                    "tags": ["tag1", "tag2"],
                    "watchers": [789],
                    "client_requirement": True,
                    "team_requirement": False,
                }
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.create_epic(
                auth_token="token",
                project=123,
                subject="Full Epic",
                description="Description",
                color="#FF0000",
                assigned_to=456,
                status=2,
                tags=["tag1", "tag2"],
                watchers=[789],
                client_requirement=True,
                team_requirement=False,
            )

            assert result["subject"] == "Full Epic"
            mock_client.create_epic.assert_called_once()


class TestGetEpicErrorHandling:
    """Tests para manejo de errores en get_epic."""

    @pytest.mark.asyncio
    async def test_get_epic_authentication_error(self, epic_tools_instance):
        """Test que get_epic maneja AuthenticationError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic = AsyncMock(side_effect=AuthenticationError("Invalid"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic(auth_token="bad", epic_id=1)
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_epic_permission_denied(self, epic_tools_instance):
        """Test que get_epic maneja PermissionDeniedError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic = AsyncMock(side_effect=PermissionDeniedError("No access"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic(auth_token="token", epic_id=1)
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_epic_not_found(self, epic_tools_instance):
        """Test que get_epic maneja ResourceNotFoundError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic(auth_token="token", epic_id=999)
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_epic_concurrency_error(self, epic_tools_instance):
        """Test que get_epic maneja ConcurrencyError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic = AsyncMock(side_effect=ConcurrencyError("Version conflict"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic(auth_token="token", epic_id=1)
            assert "Version conflict" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_epic_generic_error(self, epic_tools_instance):
        """Test que get_epic maneja excepciones genéricas."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic = AsyncMock(side_effect=Exception("Unknown error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic(auth_token="token", epic_id=1)
            assert "Error getting epic" in str(exc_info.value)


class TestGetEpicByRefErrorHandling:
    """Tests para manejo de errores en get_epic_by_ref."""

    @pytest.mark.asyncio
    async def test_get_epic_by_ref_authentication_error(self, epic_tools_instance):
        """Test que get_epic_by_ref maneja AuthenticationError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_by_ref = AsyncMock(side_effect=AuthenticationError("Invalid"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic_by_ref(auth_token="bad", project_id=123, ref=1)
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_epic_by_ref_permission_denied(self, epic_tools_instance):
        """Test que get_epic_by_ref maneja PermissionDeniedError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_by_ref = AsyncMock(side_effect=PermissionDeniedError("No access"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic_by_ref(auth_token="token", project_id=123, ref=1)
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_epic_by_ref_not_found(self, epic_tools_instance):
        """Test que get_epic_by_ref maneja ResourceNotFoundError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_by_ref = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic_by_ref(
                    auth_token="token", project_id=123, ref=999
                )
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_epic_by_ref_generic_error(self, epic_tools_instance):
        """Test que get_epic_by_ref maneja excepciones genéricas."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_by_ref = AsyncMock(side_effect=Exception("Error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic_by_ref(auth_token="token", project_id=123, ref=1)
            assert "Error getting epic by ref" in str(exc_info.value)


class TestUpdateEpicFullErrorHandling:
    """Tests para manejo de errores en update_epic_full."""

    @pytest.mark.asyncio
    async def test_update_epic_full_missing_subject(self, epic_tools_instance):
        """Test que update_epic_full falla sin subject."""
        with pytest.raises(ValueError) as exc_info:
            await epic_tools_instance.update_epic_full(auth_token="token", epic_id=1, project=123)
        assert "subject is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_epic_full_missing_project(self, epic_tools_instance):
        """Test que update_epic_full falla sin project."""
        with pytest.raises(ValueError) as exc_info:
            await epic_tools_instance.update_epic_full(
                auth_token="token", epic_id=1, subject="Test"
            )
        assert "project is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_epic_full_concurrency_error(self, epic_tools_instance):
        """Test que update_epic_full maneja ConcurrencyError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic_full = AsyncMock(side_effect=ConcurrencyError("Conflict"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.update_epic_full(
                    auth_token="token", epic_id=1, project=123, subject="Test"
                )
            assert "Version conflict" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_epic_full_authentication_error(self, epic_tools_instance):
        """Test que update_epic_full maneja AuthenticationError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic_full = AsyncMock(side_effect=AuthenticationError("Invalid"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.update_epic_full(
                    auth_token="bad", epic_id=1, project=123, subject="Test"
                )
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_epic_full_permission_denied(self, epic_tools_instance):
        """Test que update_epic_full maneja PermissionDeniedError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic_full = AsyncMock(side_effect=PermissionDeniedError("No access"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.update_epic_full(
                    auth_token="token", epic_id=1, project=123, subject="Test"
                )
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_epic_full_not_found(self, epic_tools_instance):
        """Test que update_epic_full maneja ResourceNotFoundError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic_full = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.update_epic_full(
                    auth_token="token", epic_id=999, project=123, subject="Test"
                )
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_epic_full_validation_error(self, epic_tools_instance):
        """Test que update_epic_full maneja ValidationError."""
        with patch("src.application.tools.epic_tools.validate_input") as mock_validate:
            mock_validate.side_effect = ValidationError("Invalid data")
            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.update_epic_full(
                    auth_token="token", epic_id=1, project=123, subject="Test", color="invalid"
                )
            assert "Invalid data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_epic_full_generic_error(self, epic_tools_instance):
        """Test que update_epic_full maneja excepciones genéricas."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic_full = AsyncMock(side_effect=Exception("Error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.update_epic_full(
                    auth_token="token", epic_id=1, project=123, subject="Test"
                )
            assert "Error updating epic" in str(exc_info.value)


class TestUpdateEpicErrorHandling:
    """Tests para manejo de errores en update_epic (decides between full/partial)."""

    @pytest.mark.asyncio
    async def test_update_epic_partial_mode(self, epic_tools_instance):
        """Test que update_epic usa modo parcial sin subject/project/version."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic = AsyncMock(
                return_value={
                    "id": 1,
                    "ref": 1,
                    "subject": "Original",
                    "status": 2,
                    "project": 123,
                }
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.update_epic(
                auth_token="token",
                epic_id=1,
                status=2,  # Solo cambiar status
            )

            mock_client.update_epic.assert_called_once()
            assert result["status"] == 2

    @pytest.mark.asyncio
    async def test_update_epic_full_mode(self, epic_tools_instance):
        """Test que update_epic usa modo full con subject/project/version."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic_full = AsyncMock(
                return_value={
                    "id": 1,
                    "ref": 1,
                    "subject": "Updated",
                    "project": 123,
                    "version": 3,
                }
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.update_epic(
                auth_token="token", epic_id=1, subject="Updated", project=123, version=2
            )

            mock_client.update_epic_full.assert_called_once()
            assert result["subject"] == "Updated"

    @pytest.mark.asyncio
    async def test_update_epic_concurrency_error(self, epic_tools_instance):
        """Test que update_epic maneja ConcurrencyError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic = AsyncMock(side_effect=ConcurrencyError("Conflict"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.update_epic(auth_token="token", epic_id=1, status=2)
            assert "Version conflict" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_epic_authentication_error(self, epic_tools_instance):
        """Test que update_epic maneja AuthenticationError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic = AsyncMock(side_effect=AuthenticationError("Invalid"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.update_epic(auth_token="bad", epic_id=1, status=2)
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_epic_permission_denied(self, epic_tools_instance):
        """Test que update_epic maneja PermissionDeniedError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic = AsyncMock(side_effect=PermissionDeniedError("No access"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.update_epic(auth_token="token", epic_id=1, status=2)
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_epic_not_found(self, epic_tools_instance):
        """Test que update_epic maneja ResourceNotFoundError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.update_epic(auth_token="token", epic_id=999, status=2)
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_epic_validation_error(self, epic_tools_instance):
        """Test que update_epic maneja ValidationError."""
        with patch("src.application.tools.epic_tools.validate_input") as mock_validate:
            mock_validate.side_effect = ValidationError("Invalid")
            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.update_epic(
                    auth_token="token", epic_id=1, color="invalid"
                )
            assert "Invalid" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_epic_generic_error(self, epic_tools_instance):
        """Test que update_epic maneja excepciones genéricas."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic = AsyncMock(side_effect=Exception("Error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.update_epic(auth_token="token", epic_id=1, status=2)
            assert "Error updating epic" in str(exc_info.value)


class TestUpdateEpicPartialAndPatchEpic:
    """Tests para update_epic_partial y patch_epic (aliases)."""

    @pytest.mark.asyncio
    async def test_update_epic_partial_delegates_to_update_epic(self, epic_tools_instance):
        """Test que update_epic_partial delega a update_epic."""
        with patch.object(
            epic_tools_instance, "update_epic", return_value={"id": 1, "status": 2}
        ) as mock:
            result = await epic_tools_instance.update_epic_partial(
                auth_token="token", epic_id=1, status=2
            )
            mock.assert_called_once()
            assert result["status"] == 2

    @pytest.mark.asyncio
    async def test_patch_epic_delegates_to_update_epic(self, epic_tools_instance):
        """Test que patch_epic delega a update_epic."""
        with patch.object(
            epic_tools_instance, "update_epic", return_value={"id": 1, "color": "#FF0000"}
        ) as mock:
            result = await epic_tools_instance.patch_epic(
                auth_token="token", epic_id=1, color="#FF0000"
            )
            mock.assert_called_once()
            assert result["color"] == "#FF0000"


class TestDeleteEpicErrorHandling:
    """Tests para manejo de errores en delete_epic."""

    @pytest.mark.asyncio
    async def test_delete_epic_authentication_error(self, epic_tools_instance):
        """Test que delete_epic maneja AuthenticationError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete_epic = AsyncMock(side_effect=AuthenticationError("Invalid"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.delete_epic(auth_token="bad", epic_id=1)
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_epic_permission_denied(self, epic_tools_instance):
        """Test que delete_epic maneja PermissionDeniedError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete_epic = AsyncMock(side_effect=PermissionDeniedError("No access"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.delete_epic(auth_token="token", epic_id=1)
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_epic_not_found(self, epic_tools_instance):
        """Test que delete_epic maneja ResourceNotFoundError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete_epic = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.delete_epic(auth_token="token", epic_id=999)
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_epic_generic_error(self, epic_tools_instance):
        """Test que delete_epic maneja excepciones genéricas."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete_epic = AsyncMock(side_effect=Exception("Error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.delete_epic(auth_token="token", epic_id=1)
            assert "Error deleting epic" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_epic_success(self, epic_tools_instance):
        """Test delete_epic exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete_epic = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.delete_epic(auth_token="token", epic_id=1)

            assert result["success"] is True
            assert "deleted successfully" in result["message"]


# ============================================================================
# Related User Stories Tests
# ============================================================================


class TestListRelatedUserstories:
    """Tests para list_related_userstories (alias)."""

    @pytest.mark.asyncio
    async def test_list_related_userstories_success(self, epic_tools_instance):
        """Test list_related_userstories exitoso."""
        with patch.object(epic_tools_instance, "list_epic_related_userstories") as mock:
            mock.return_value = [{"id": 1, "subject": "Story 1"}]

            result = await epic_tools_instance.list_related_userstories(
                auth_token="token", epic_id=1
            )

            assert len(result) == 1
            mock.assert_called_once_with(auth_token="token", epic_id=1)

    @pytest.mark.asyncio
    async def test_list_related_userstories_auth_error(self, epic_tools_instance):
        """Test list_related_userstories con AuthenticationError."""
        with patch.object(epic_tools_instance, "list_epic_related_userstories") as mock:
            mock.side_effect = AuthenticationError("Invalid")

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.list_related_userstories(auth_token="bad", epic_id=1)
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_related_userstories_permission_error(self, epic_tools_instance):
        """Test list_related_userstories con PermissionDeniedError."""
        with patch.object(epic_tools_instance, "list_epic_related_userstories") as mock:
            mock.side_effect = PermissionDeniedError("No access")

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.list_related_userstories(auth_token="token", epic_id=1)
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_related_userstories_not_found(self, epic_tools_instance):
        """Test list_related_userstories con ResourceNotFoundError."""
        with patch.object(epic_tools_instance, "list_epic_related_userstories") as mock:
            mock.side_effect = ResourceNotFoundError("Not found")

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.list_related_userstories(auth_token="token", epic_id=999)
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_list_related_userstories_generic_error(self, epic_tools_instance):
        """Test list_related_userstories con error genérico."""
        with patch.object(epic_tools_instance, "list_epic_related_userstories") as mock:
            mock.side_effect = Exception("Error")

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.list_related_userstories(auth_token="token", epic_id=1)
            assert "Error listing related user stories" in str(exc_info.value)


class TestCreateEpicRelatedUserstory:
    """Tests para create_epic_related_userstory."""

    @pytest.mark.asyncio
    async def test_create_epic_related_userstory_success(self, epic_tools_instance):
        """Test create_epic_related_userstory exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic_related_userstory = AsyncMock(
                return_value={"epic": 1, "user_story": 100, "order": 1}
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.create_epic_related_userstory(
                auth_token="token", epic_id=1, user_story=100, order=1
            )

            assert result["epic"] == 1
            assert result["user_story"] == 100


class TestCreateRelatedUserstory:
    """Tests para create_related_userstory (alias)."""

    @pytest.mark.asyncio
    async def test_create_related_userstory_success(self, epic_tools_instance):
        """Test create_related_userstory exitoso."""
        with patch.object(epic_tools_instance, "create_epic_related_userstory") as mock:
            mock.return_value = {"epic": 1, "user_story": 100}

            result = await epic_tools_instance.create_related_userstory(
                auth_token="token", epic_id=1, user_story=100, order=1
            )

            assert result["epic"] == 1
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_related_userstory_auth_error(self, epic_tools_instance):
        """Test create_related_userstory con AuthenticationError."""
        with patch.object(epic_tools_instance, "create_epic_related_userstory") as mock:
            mock.side_effect = AuthenticationError("Invalid")

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.create_related_userstory(
                    auth_token="bad", epic_id=1, user_story=100
                )
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_related_userstory_permission_error(self, epic_tools_instance):
        """Test create_related_userstory con PermissionDeniedError."""
        with patch.object(epic_tools_instance, "create_epic_related_userstory") as mock:
            mock.side_effect = PermissionDeniedError("No access")

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.create_related_userstory(
                    auth_token="token", epic_id=1, user_story=100
                )
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_related_userstory_not_found(self, epic_tools_instance):
        """Test create_related_userstory con ResourceNotFoundError."""
        with patch.object(epic_tools_instance, "create_epic_related_userstory") as mock:
            mock.side_effect = ResourceNotFoundError("Not found")

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.create_related_userstory(
                    auth_token="token", epic_id=999, user_story=100
                )
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_related_userstory_generic_error(self, epic_tools_instance):
        """Test create_related_userstory con error genérico."""
        with patch.object(epic_tools_instance, "create_epic_related_userstory") as mock:
            mock.side_effect = Exception("Error")

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.create_related_userstory(
                    auth_token="token", epic_id=1, user_story=100
                )
            assert "Error creating related user story" in str(exc_info.value)


class TestGetEpicRelatedUserstory:
    """Tests para get_epic_related_userstory."""

    @pytest.mark.asyncio
    async def test_get_epic_related_userstory_success(self, epic_tools_instance):
        """Test get_epic_related_userstory exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_related_userstory = AsyncMock(
                return_value={"epic": 1, "user_story": 100, "order": 1}
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.get_epic_related_userstory(
                auth_token="token", epic_id=1, userstory_id=100
            )

            assert result["epic"] == 1
            assert result["user_story"] == 100


class TestUpdateEpicRelatedUserstory:
    """Tests para update_epic_related_userstory."""

    @pytest.mark.asyncio
    async def test_update_epic_related_userstory_success(self, epic_tools_instance):
        """Test update_epic_related_userstory exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic_related_userstory = AsyncMock(
                return_value={"epic": 1, "user_story": 100, "order": 5}
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.update_epic_related_userstory(
                auth_token="token", epic_id=1, userstory_id=100, order=5
            )

            assert result["order"] == 5


class TestDeleteEpicRelatedUserstory:
    """Tests para delete_epic_related_userstory."""

    @pytest.mark.asyncio
    async def test_delete_epic_related_userstory_success(self, epic_tools_instance):
        """Test delete_epic_related_userstory exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete_epic_related_userstory = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.delete_epic_related_userstory(
                auth_token="token", epic_id=1, userstory_id=100
            )

            assert "removed" in result["message"]


# ============================================================================
# Bulk Operations Tests
# ============================================================================


class TestBulkCreateEpics:
    """Tests para bulk_create_epics."""

    @pytest.mark.asyncio
    async def test_bulk_create_epics_with_bulk_epics_success(self, epic_tools_instance):
        """Test bulk_create_epics con bulk_epics string exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.bulk_create_epics = AsyncMock(
                return_value=[
                    {"id": 1, "ref": 1, "subject": "Epic 1", "project": 123},
                    {"id": 2, "ref": 2, "subject": "Epic 2", "project": 123},
                ]
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.bulk_create_epics(
                auth_token="token", project_id=123, bulk_epics="Epic 1\nEpic 2"
            )

            assert len(result) == 2
            mock_client.bulk_create_epics.assert_called_once_with(
                project_id=123, bulk_epics="Epic 1\nEpic 2"
            )

    @pytest.mark.asyncio
    async def test_bulk_create_epics_with_epics_data_success(self, epic_tools_instance):
        """Test bulk_create_epics con epics_data list exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.bulk_create_epics = AsyncMock(
                return_value=[{"id": 1, "ref": 1, "subject": "Epic 1", "project": 123}]
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.bulk_create_epics(
                auth_token="token", project_id=123, epics_data=[{"subject": "Epic 1"}]
            )

            assert len(result) == 1
            mock_client.bulk_create_epics.assert_called_once_with(
                project_id=123, epics_data=[{"subject": "Epic 1"}]
            )

    @pytest.mark.asyncio
    async def test_bulk_create_epics_auth_error(self, epic_tools_instance):
        """Test bulk_create_epics con AuthenticationError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.bulk_create_epics = AsyncMock(side_effect=AuthenticationError("Invalid"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.bulk_create_epics(
                    auth_token="bad", project_id=123, bulk_epics="Epic"
                )
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_bulk_create_epics_permission_error(self, epic_tools_instance):
        """Test bulk_create_epics con PermissionDeniedError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.bulk_create_epics = AsyncMock(
                side_effect=PermissionDeniedError("No access")
            )
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.bulk_create_epics(
                    auth_token="token", project_id=123, bulk_epics="Epic"
                )
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_bulk_create_epics_generic_error(self, epic_tools_instance):
        """Test bulk_create_epics con error genérico."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.bulk_create_epics = AsyncMock(side_effect=Exception("Error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.bulk_create_epics(
                    auth_token="token", project_id=123, bulk_epics="Epic"
                )
            assert "Error bulk creating epics" in str(exc_info.value)


class TestBulkCreateRelatedUserstories:
    """Tests para bulk_create_related_userstories."""

    @pytest.mark.asyncio
    async def test_bulk_create_related_userstories_with_bulk_userstories(self, epic_tools_instance):
        """Test bulk_create_related_userstories con bulk_userstories."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            # Simula que el cliente tiene el método bulk_create_related_userstories
            mock_client.bulk_create_related_userstories = AsyncMock(
                return_value=[{"epic": 1, "user_story": 100, "order": 1}]
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.bulk_create_related_userstories(
                auth_token="token", epic_id=1, bulk_userstories=[{"user_story": 100, "order": 1}]
            )

            assert len(result) == 1
            mock_client.bulk_create_related_userstories.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_create_related_userstories_with_userstories_data(self, epic_tools_instance):
        """Test bulk_create_related_userstories con userstories_data."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.bulk_create_related_userstories = AsyncMock(
                return_value=[{"epic": 1, "user_story": 100, "order": 1}]
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.bulk_create_related_userstories(
                auth_token="token", epic_id=1, userstories_data=[{"user_story": 100}]
            )

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_bulk_create_related_userstories_fallback(self, epic_tools_instance):
        """Test bulk_create_related_userstories con fallback a bulk_create_epic_related_userstories."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            # Eliminar el atributo para que hasattr retorne False
            del mock_client.bulk_create_related_userstories
            mock_client.bulk_create_epic_related_userstories = AsyncMock(
                return_value=[{"epic": 1, "user_story": 100, "order": 1}]
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.bulk_create_related_userstories(
                auth_token="token", epic_id=1, bulk_userstories=[{"user_story": 100}]
            )

            assert len(result) == 1
            mock_client.bulk_create_epic_related_userstories.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_create_related_userstories_fallback_userstories_data(
        self, epic_tools_instance
    ):
        """Test bulk_create_related_userstories fallback con userstories_data."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            # Eliminar el atributo para que hasattr retorne False
            del mock_client.bulk_create_related_userstories
            mock_client.bulk_create_epic_related_userstories = AsyncMock(
                return_value=[{"epic": 1, "user_story": 100}]
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.bulk_create_related_userstories(
                auth_token="token", epic_id=1, userstories_data=[{"user_story": 100}]
            )

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_bulk_create_related_userstories_auth_error(self, epic_tools_instance):
        """Test bulk_create_related_userstories con AuthenticationError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.bulk_create_related_userstories = AsyncMock(
                side_effect=AuthenticationError("Invalid")
            )
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.bulk_create_related_userstories(
                    auth_token="bad", epic_id=1, bulk_userstories=[{"user_story": 100}]
                )
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_bulk_create_related_userstories_permission_error(self, epic_tools_instance):
        """Test bulk_create_related_userstories con PermissionDeniedError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.bulk_create_related_userstories = AsyncMock(
                side_effect=PermissionDeniedError("No access")
            )
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.bulk_create_related_userstories(
                    auth_token="token", epic_id=1, bulk_userstories=[{"user_story": 100}]
                )
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_bulk_create_related_userstories_not_found(self, epic_tools_instance):
        """Test bulk_create_related_userstories con ResourceNotFoundError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.bulk_create_related_userstories = AsyncMock(
                side_effect=ResourceNotFoundError("Not found")
            )
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.bulk_create_related_userstories(
                    auth_token="token", epic_id=999, bulk_userstories=[{"user_story": 100}]
                )
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_bulk_create_related_userstories_generic_error(self, epic_tools_instance):
        """Test bulk_create_related_userstories con error genérico."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.bulk_create_related_userstories = AsyncMock(side_effect=Exception("Error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.bulk_create_related_userstories(
                    auth_token="token", epic_id=1, bulk_userstories=[{"user_story": 100}]
                )
            assert "Error bulk creating related user stories" in str(exc_info.value)


class TestBulkCreateEpicRelatedUserstories:
    """Tests para bulk_create_epic_related_userstories (alias)."""

    @pytest.mark.asyncio
    async def test_bulk_create_epic_related_userstories_delegates(self, epic_tools_instance):
        """Test que bulk_create_epic_related_userstories delega a bulk_create_related_userstories."""
        with patch.object(epic_tools_instance, "bulk_create_related_userstories") as mock:
            mock.return_value = [{"epic": 1, "user_story": 100}]

            result = await epic_tools_instance.bulk_create_epic_related_userstories(
                auth_token="token", epic_id=1, userstories_data=[{"user_story": 100}]
            )

            assert len(result) == 1
            mock.assert_called_once_with("token", 1, [{"user_story": 100}])


# ============================================================================
# Epic Filters Tests
# ============================================================================


class TestGetEpicFilters:
    """Tests para get_epic_filters."""

    @pytest.mark.asyncio
    async def test_get_epic_filters_success(self, epic_tools_instance):
        """Test get_epic_filters exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_filters = AsyncMock(
                return_value={
                    "statuses": [{"id": 1, "name": "New"}],
                    "assigned_to": [{"id": 1, "full_name": "User"}],
                }
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.get_epic_filters(auth_token="token", project_id=123)

            assert "statuses" in result
            mock_client.get_epic_filters.assert_called_once_with(project=123)

    @pytest.mark.asyncio
    async def test_get_epic_filters_auth_error(self, epic_tools_instance):
        """Test get_epic_filters con AuthenticationError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_filters = AsyncMock(side_effect=AuthenticationError("Invalid"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic_filters(auth_token="bad", project_id=123)
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_epic_filters_permission_error(self, epic_tools_instance):
        """Test get_epic_filters con PermissionDeniedError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_filters = AsyncMock(side_effect=PermissionDeniedError("No access"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic_filters(auth_token="token", project_id=123)
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_epic_filters_not_found(self, epic_tools_instance):
        """Test get_epic_filters con ResourceNotFoundError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_filters = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic_filters(auth_token="token", project_id=999)
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_epic_filters_generic_error(self, epic_tools_instance):
        """Test get_epic_filters con error genérico."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_filters = AsyncMock(side_effect=Exception("Error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic_filters(auth_token="token", project_id=123)
            assert "Error getting epic filters" in str(exc_info.value)


# ============================================================================
# Voting Tests
# ============================================================================


class TestUpvoteEpic:
    """Tests para upvote_epic."""

    @pytest.mark.asyncio
    async def test_upvote_epic_success(self, epic_tools_instance):
        """Test upvote_epic exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.upvote_epic = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.upvote_epic(auth_token="token", epic_id=1)

            assert "upvoted successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_upvote_epic_auth_error(self, epic_tools_instance):
        """Test upvote_epic con AuthenticationError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.upvote_epic = AsyncMock(side_effect=AuthenticationError("Invalid"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.upvote_epic(auth_token="bad", epic_id=1)
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upvote_epic_permission_error(self, epic_tools_instance):
        """Test upvote_epic con PermissionDeniedError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.upvote_epic = AsyncMock(side_effect=PermissionDeniedError("No access"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.upvote_epic(auth_token="token", epic_id=1)
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upvote_epic_not_found(self, epic_tools_instance):
        """Test upvote_epic con ResourceNotFoundError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.upvote_epic = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.upvote_epic(auth_token="token", epic_id=999)
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_upvote_epic_generic_error(self, epic_tools_instance):
        """Test upvote_epic con error genérico."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.upvote_epic = AsyncMock(side_effect=Exception("Error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.upvote_epic(auth_token="token", epic_id=1)
            assert "Error upvoting epic" in str(exc_info.value)


class TestDownvoteEpic:
    """Tests para downvote_epic."""

    @pytest.mark.asyncio
    async def test_downvote_epic_success(self, epic_tools_instance):
        """Test downvote_epic exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.downvote_epic = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.downvote_epic(auth_token="token", epic_id=1)

            assert "downvoted successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_downvote_epic_auth_error(self, epic_tools_instance):
        """Test downvote_epic con AuthenticationError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.downvote_epic = AsyncMock(side_effect=AuthenticationError("Invalid"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.downvote_epic(auth_token="bad", epic_id=1)
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_downvote_epic_permission_error(self, epic_tools_instance):
        """Test downvote_epic con PermissionDeniedError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.downvote_epic = AsyncMock(side_effect=PermissionDeniedError("No access"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.downvote_epic(auth_token="token", epic_id=1)
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_downvote_epic_not_found(self, epic_tools_instance):
        """Test downvote_epic con ResourceNotFoundError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.downvote_epic = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.downvote_epic(auth_token="token", epic_id=999)
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_downvote_epic_generic_error(self, epic_tools_instance):
        """Test downvote_epic con error genérico."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.downvote_epic = AsyncMock(side_effect=Exception("Error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.downvote_epic(auth_token="token", epic_id=1)
            assert "Error downvoting epic" in str(exc_info.value)


class TestGetEpicVoters:
    """Tests para get_epic_voters."""

    @pytest.mark.asyncio
    async def test_get_epic_voters_success(self, epic_tools_instance):
        """Test get_epic_voters exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_voters = AsyncMock(
                return_value=[{"id": 1, "full_name": "User 1"}, {"id": 2, "full_name": "User 2"}]
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.get_epic_voters(auth_token="token", epic_id=1)

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_epic_voters_auth_error(self, epic_tools_instance):
        """Test get_epic_voters con AuthenticationError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_voters = AsyncMock(side_effect=AuthenticationError("Invalid"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic_voters(auth_token="bad", epic_id=1)
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_epic_voters_permission_error(self, epic_tools_instance):
        """Test get_epic_voters con PermissionDeniedError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_voters = AsyncMock(side_effect=PermissionDeniedError("No access"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic_voters(auth_token="token", epic_id=1)
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_epic_voters_not_found(self, epic_tools_instance):
        """Test get_epic_voters con ResourceNotFoundError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_voters = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic_voters(auth_token="token", epic_id=999)
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_epic_voters_generic_error(self, epic_tools_instance):
        """Test get_epic_voters con error genérico."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_voters = AsyncMock(side_effect=Exception("Error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic_voters(auth_token="token", epic_id=1)
            assert "Error getting epic voters" in str(exc_info.value)


# ============================================================================
# Watching Tests
# ============================================================================


class TestWatchEpic:
    """Tests para watch_epic."""

    @pytest.mark.asyncio
    async def test_watch_epic_success(self, epic_tools_instance):
        """Test watch_epic exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.watch_epic = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.watch_epic(auth_token="token", epic_id=1)

            assert "watching epic" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_watch_epic_auth_error(self, epic_tools_instance):
        """Test watch_epic con AuthenticationError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.watch_epic = AsyncMock(side_effect=AuthenticationError("Invalid"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.watch_epic(auth_token="bad", epic_id=1)
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_watch_epic_permission_error(self, epic_tools_instance):
        """Test watch_epic con PermissionDeniedError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.watch_epic = AsyncMock(side_effect=PermissionDeniedError("No access"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.watch_epic(auth_token="token", epic_id=1)
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_watch_epic_not_found(self, epic_tools_instance):
        """Test watch_epic con ResourceNotFoundError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.watch_epic = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.watch_epic(auth_token="token", epic_id=999)
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_watch_epic_generic_error(self, epic_tools_instance):
        """Test watch_epic con error genérico."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.watch_epic = AsyncMock(side_effect=Exception("Error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.watch_epic(auth_token="token", epic_id=1)
            assert "Error watching epic" in str(exc_info.value)


class TestUnwatchEpic:
    """Tests para unwatch_epic."""

    @pytest.mark.asyncio
    async def test_unwatch_epic_success(self, epic_tools_instance):
        """Test unwatch_epic exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.unwatch_epic = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.unwatch_epic(auth_token="token", epic_id=1)

            assert "stopped watching" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_unwatch_epic_auth_error(self, epic_tools_instance):
        """Test unwatch_epic con AuthenticationError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.unwatch_epic = AsyncMock(side_effect=AuthenticationError("Invalid"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.unwatch_epic(auth_token="bad", epic_id=1)
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unwatch_epic_permission_error(self, epic_tools_instance):
        """Test unwatch_epic con PermissionDeniedError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.unwatch_epic = AsyncMock(side_effect=PermissionDeniedError("No access"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.unwatch_epic(auth_token="token", epic_id=1)
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unwatch_epic_not_found(self, epic_tools_instance):
        """Test unwatch_epic con ResourceNotFoundError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.unwatch_epic = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.unwatch_epic(auth_token="token", epic_id=999)
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_unwatch_epic_generic_error(self, epic_tools_instance):
        """Test unwatch_epic con error genérico."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.unwatch_epic = AsyncMock(side_effect=Exception("Error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.unwatch_epic(auth_token="token", epic_id=1)
            assert "Error unwatching epic" in str(exc_info.value)


class TestGetEpicWatchers:
    """Tests para get_epic_watchers."""

    @pytest.mark.asyncio
    async def test_get_epic_watchers_success(self, epic_tools_instance):
        """Test get_epic_watchers exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_watchers = AsyncMock(
                return_value=[{"id": 1, "full_name": "User 1"}, {"id": 2, "full_name": "User 2"}]
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.get_epic_watchers(auth_token="token", epic_id=1)

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_epic_watchers_auth_error(self, epic_tools_instance):
        """Test get_epic_watchers con AuthenticationError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_watchers = AsyncMock(side_effect=AuthenticationError("Invalid"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic_watchers(auth_token="bad", epic_id=1)
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_epic_watchers_permission_error(self, epic_tools_instance):
        """Test get_epic_watchers con PermissionDeniedError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_watchers = AsyncMock(
                side_effect=PermissionDeniedError("No access")
            )
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic_watchers(auth_token="token", epic_id=1)
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_epic_watchers_not_found(self, epic_tools_instance):
        """Test get_epic_watchers con ResourceNotFoundError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_watchers = AsyncMock(
                side_effect=ResourceNotFoundError("Not found")
            )
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic_watchers(auth_token="token", epic_id=999)
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_epic_watchers_generic_error(self, epic_tools_instance):
        """Test get_epic_watchers con error genérico."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_watchers = AsyncMock(side_effect=Exception("Error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.get_epic_watchers(auth_token="token", epic_id=1)
            assert "Error getting epic watchers" in str(exc_info.value)


# =============================================================================
# Tests para Attachments (EPIC-021 a EPIC-025)
# =============================================================================


class TestListEpicAttachments:
    """Tests para list_epic_attachments."""

    @pytest.mark.asyncio
    async def test_list_epic_attachments_success(self, epic_tools_instance):
        """Test list_epic_attachments exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.list_epic_attachments = AsyncMock(
                return_value=[
                    {"id": 1, "attached_file": "file1.pdf", "name": "Doc 1"},
                    {"id": 2, "attached_file": "file2.pdf", "name": "Doc 2"},
                ]
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.list_epic_attachments(auth_token="token", epic_id=1)

            assert len(result) == 2
            assert result[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_list_epic_attachments_auth_error(self, epic_tools_instance):
        """Test list_epic_attachments con AuthenticationError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.list_epic_attachments = AsyncMock(
                side_effect=AuthenticationError("Invalid")
            )
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.list_epic_attachments(auth_token="bad", epic_id=1)
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_epic_attachments_permission_error(self, epic_tools_instance):
        """Test list_epic_attachments con PermissionDeniedError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.list_epic_attachments = AsyncMock(
                side_effect=PermissionDeniedError("No access")
            )
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.list_epic_attachments(auth_token="token", epic_id=1)
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_epic_attachments_not_found(self, epic_tools_instance):
        """Test list_epic_attachments con ResourceNotFoundError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.list_epic_attachments = AsyncMock(
                side_effect=ResourceNotFoundError("Not found")
            )
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.list_epic_attachments(auth_token="token", epic_id=999)
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_list_epic_attachments_generic_error(self, epic_tools_instance):
        """Test list_epic_attachments con error genérico."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.list_epic_attachments = AsyncMock(side_effect=Exception("Error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.list_epic_attachments(auth_token="token", epic_id=1)
            assert "Error listing epic attachments" in str(exc_info.value)


class TestCreateEpicAttachment:
    """Tests para create_epic_attachment."""

    @pytest.mark.asyncio
    async def test_create_epic_attachment_success(self, epic_tools_instance):
        """Test create_epic_attachment exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic_attachment = AsyncMock(
                return_value={"id": 1, "attached_file": "newfile.pdf", "name": "New Doc"}
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.create_epic_attachment(
                auth_token="token", epic_id=1, attached_file="/path/to/file.pdf"
            )

            assert result["id"] == 1
            mock_client.create_epic_attachment.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_epic_attachment_with_object_id(self, epic_tools_instance):
        """Test create_epic_attachment usando object_id en lugar de epic_id."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic_attachment = AsyncMock(
                return_value={"id": 2, "attached_file": "doc.pdf", "name": "Doc"}
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.create_epic_attachment(
                auth_token="token", object_id=5, attached_file="/path/to/file.pdf"
            )

            assert result["id"] == 2

    @pytest.mark.asyncio
    async def test_create_epic_attachment_auth_error(self, epic_tools_instance):
        """Test create_epic_attachment con AuthenticationError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic_attachment = AsyncMock(
                side_effect=AuthenticationError("Invalid")
            )
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.create_epic_attachment(
                    auth_token="bad", epic_id=1, attached_file="file.pdf"
                )
            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_epic_attachment_permission_error(self, epic_tools_instance):
        """Test create_epic_attachment con PermissionDeniedError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic_attachment = AsyncMock(
                side_effect=PermissionDeniedError("No access")
            )
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.create_epic_attachment(
                    auth_token="token", epic_id=1, attached_file="file.pdf"
                )
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_epic_attachment_not_found(self, epic_tools_instance):
        """Test create_epic_attachment con ResourceNotFoundError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic_attachment = AsyncMock(
                side_effect=ResourceNotFoundError("Not found")
            )
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.create_epic_attachment(
                    auth_token="token", epic_id=999, attached_file="file.pdf"
                )
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_epic_attachment_generic_error(self, epic_tools_instance):
        """Test create_epic_attachment con error genérico."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic_attachment = AsyncMock(side_effect=Exception("Error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.create_epic_attachment(
                    auth_token="token", epic_id=1, attached_file="file.pdf"
                )
            assert "Error creating epic attachment" in str(exc_info.value)


class TestGetEpicAttachment:
    """Tests para get_epic_attachment."""

    @pytest.mark.asyncio
    async def test_get_epic_attachment_success(self, epic_tools_instance):
        """Test get_epic_attachment exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_attachment = AsyncMock(
                return_value={"id": 1, "attached_file": "file.pdf", "name": "Document"}
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.get_epic_attachment(
                auth_token="token", attachment_id=1
            )

            assert result["id"] == 1
            assert result["name"] == "Document"


class TestUpdateEpicAttachment:
    """Tests para update_epic_attachment."""

    @pytest.mark.asyncio
    async def test_update_epic_attachment_success(self, epic_tools_instance):
        """Test update_epic_attachment exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic_attachment = AsyncMock(
                return_value={
                    "id": 1,
                    "attached_file": "file.pdf",
                    "name": "Updated Document",
                    "description": "New description",
                }
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.update_epic_attachment(
                auth_token="token", attachment_id=1, description="New description"
            )

            assert result["id"] == 1
            assert result["description"] == "New description"


class TestDeleteEpicAttachment:
    """Tests para delete_epic_attachment."""

    @pytest.mark.asyncio
    async def test_delete_epic_attachment_success(self, epic_tools_instance):
        """Test delete_epic_attachment exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete_epic_attachment = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.delete_epic_attachment(
                auth_token="token", attachment_id=1
            )

            assert "deleted successfully" in result["message"]
            mock_client.delete_epic_attachment.assert_called_once_with(attachment_id=1)


# =============================================================================
# Tests para Custom Attributes (EPIC-026 a EPIC-028)
# =============================================================================


class TestListEpicCustomAttributes:
    """Tests para list_epic_custom_attributes."""

    @pytest.mark.asyncio
    async def test_list_epic_custom_attributes_success(self, epic_tools_instance):
        """Test list_epic_custom_attributes exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.list_epic_custom_attributes = AsyncMock(
                return_value=[
                    {"id": 1, "name": "Priority", "type": "text"},
                    {"id": 2, "name": "Category", "type": "dropdown"},
                ]
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.list_epic_custom_attributes(
                auth_token="token", project_id=1
            )

            assert len(result) == 2
            assert result[0]["name"] == "Priority"


class TestCreateEpicCustomAttribute:
    """Tests para create_epic_custom_attribute."""

    @pytest.mark.asyncio
    async def test_create_epic_custom_attribute_success(self, epic_tools_instance):
        """Test create_epic_custom_attribute exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic_custom_attribute = AsyncMock(
                return_value={"id": 3, "name": "New Attribute", "type": "text"}
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.create_epic_custom_attribute(
                auth_token="token", project_id=1, name="New Attribute"
            )

            assert result["id"] == 3
            assert result["name"] == "New Attribute"


class TestGetEpicCustomAttributeValues:
    """Tests para get_epic_custom_attribute_values."""

    @pytest.mark.asyncio
    async def test_get_epic_custom_attribute_values_success(self, epic_tools_instance):
        """Test get_epic_custom_attribute_values exitoso."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_custom_attribute_values = AsyncMock(
                return_value={
                    "epic": 1,
                    "attributes_values": {"1": "High", "2": "Feature"},
                    "version": 1,
                }
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.get_epic_custom_attribute_values(
                auth_token="token", epic_id=1
            )

            assert result["epic"] == 1
            assert "attributes_values" in result


# =============================================================================
# Tests para MCP Tool Functions con parámetros opcionales
# =============================================================================


class TestMCPToolFunctionsWithOptionalParams:
    """Tests para las funciones MCP tool con parámetros opcionales."""

    @pytest.mark.asyncio
    async def test_list_epics_tool_with_optional_params(self):
        """Test taiga_list_epics con parámetros opcionales."""
        mcp = FastMCP("Test")

        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            EpicTools(mcp)

            # Mock pagination
            from src.infrastructure.pagination import AutoPaginator

            with patch.object(AutoPaginator, "paginate", new_callable=AsyncMock) as mock_paginate:
                mock_paginate.return_value = [{"id": 1, "subject": "Epic", "ref": 1}]

                # Acceder al tool registrado
                tool_func = None
                for tool in mcp._tool_manager._tools.values():
                    if tool.name == "taiga_list_epics":
                        tool_func = tool.fn
                        break

                if tool_func:
                    result = await tool_func(
                        auth_token="token",
                        project_id=123,
                        status=1,
                        assigned_to=5,
                        auto_paginate=True,
                    )
                    assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_create_epic_tool_with_all_optional_params(self):
        """Test taiga_create_epic con todos los parámetros opcionales."""
        mcp = FastMCP("Test")

        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic = AsyncMock(
                return_value={"id": 1, "subject": "Test Epic", "project": 123, "ref": 1}
            )
            mock_cls.return_value = mock_client

            EpicTools(mcp)

            # Acceder al tool registrado
            tool_func = None
            for tool in mcp._tool_manager._tools.values():
                if tool.name == "taiga_create_epic":
                    tool_func = tool.fn
                    break

            if tool_func:
                result = await tool_func(
                    auth_token="token",
                    project_id=123,
                    subject="Test Epic",
                    description="A description",
                    color="#FF0000",
                    assigned_to=5,
                    status=1,
                    tags=["tag1", "tag2"],
                )
                assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_update_epic_full_tool_with_all_optional_params(self):
        """Test taiga_update_epic con todos los parámetros opcionales."""
        mcp = FastMCP("Test")

        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic = AsyncMock(
                return_value={
                    "id": 1,
                    "subject": "Updated Epic",
                    "project": 123,
                    "version": 2,
                    "ref": 1,
                }
            )
            mock_cls.return_value = mock_client

            EpicTools(mcp)

            # Acceder al tool registrado
            tool_func = None
            for tool in mcp._tool_manager._tools.values():
                if tool.name == "taiga_update_epic":
                    tool_func = tool.fn
                    break

            if tool_func:
                result = await tool_func(
                    auth_token="token",
                    epic_id=1,
                    subject="Updated Epic",
                    description="Updated description",
                    color="#00FF00",
                    assigned_to=10,
                    status=2,
                    tags=["updated"],
                )
                assert result["version"] == 2

    @pytest.mark.asyncio
    async def test_update_epic_partial_tool_with_all_optional_params(self):
        """Test taiga_update_epic_partial con todos los parámetros opcionales."""
        mcp = FastMCP("Test")

        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic = AsyncMock(
                return_value={
                    "id": 1,
                    "subject": "Partial Updated",
                    "project": 123,
                    "version": 3,
                    "ref": 1,
                }
            )
            mock_cls.return_value = mock_client

            EpicTools(mcp)

            # Acceder al tool registrado
            tool_func = None
            for tool in mcp._tool_manager._tools.values():
                if tool.name == "taiga_update_epic_partial":
                    tool_func = tool.fn
                    break

            if tool_func:
                result = await tool_func(
                    auth_token="token",
                    epic_id=1,
                    subject="Partial Updated",
                    description="Partial desc",
                    color="#0000FF",
                    assigned_to=15,
                    status=3,
                    tags=["partial"],
                )
                assert result["version"] == 3


# =============================================================================
# Tests adicionales para paths de éxito
# =============================================================================


class TestSuccessPaths:
    """Tests para paths de éxito de métodos internos."""

    @pytest.mark.asyncio
    async def test_get_epic_success_path(self, epic_tools_instance):
        """Test get_epic path de éxito completo."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic = AsyncMock(
                return_value={"id": 1, "ref": 10, "subject": "Test Epic", "project": 123}
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.get_epic(auth_token="token", epic_id=1)

            assert result["id"] == 1
            assert result["ref"] == 10

    @pytest.mark.asyncio
    async def test_get_epic_by_ref_success_path(self, epic_tools_instance):
        """Test get_epic_by_ref path de éxito completo."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_by_ref = AsyncMock(
                return_value={"id": 5, "ref": 25, "subject": "Epic by Ref", "project": 123}
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.get_epic_by_ref(
                auth_token="token", project_id=123, ref=25
            )

            assert result["id"] == 5
            assert result["ref"] == 25

    @pytest.mark.asyncio
    async def test_list_epic_related_userstories_success(self, epic_tools_instance):
        """Test list_epic_related_userstories path de éxito."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.list_epic_related_userstories = AsyncMock(
                return_value=[
                    {"id": 1, "epic": 1, "user_story": 10, "order": 1},
                    {"id": 2, "epic": 1, "user_story": 20, "order": 2},
                ]
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.list_epic_related_userstories(
                auth_token="token", epic_id=1
            )

            assert len(result) == 2
            assert result[0]["user_story"] == 10

    @pytest.mark.asyncio
    async def test_create_epic_success_path(self, epic_tools_instance):
        """Test create_epic path de éxito completo."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic = AsyncMock(
                return_value={"id": 100, "ref": 50, "subject": "New Epic", "project": 123}
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.create_epic(
                auth_token="token", project=123, subject="New Epic"
            )

            assert result["id"] == 100
            assert result["ref"] == 50

    @pytest.mark.asyncio
    async def test_create_epic_generic_exception(self, epic_tools_instance):
        """Test create_epic con excepción genérica."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic = AsyncMock(side_effect=Exception("Network error"))
            mock_cls.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                await epic_tools_instance.create_epic(
                    auth_token="token", project=123, subject="New Epic"
                )
            assert "Network error" in str(exc_info.value)


class TestListRelatedUserstoriesSuccessPaths:
    """Tests adicionales para list_related_userstories."""

    @pytest.mark.asyncio
    async def test_list_related_userstories_success(self, epic_tools_instance):
        """Test list_related_userstories path de éxito."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.list_epic_related_userstories = AsyncMock(
                return_value=[{"id": 1, "epic": 1, "user_story": 10, "order": 1}]
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.list_related_userstories(
                auth_token="token", epic_id=1
            )

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_related_userstories_not_found(self, epic_tools_instance):
        """Test list_related_userstories con ResourceNotFoundError."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.list_epic_related_userstories = AsyncMock(
                side_effect=ResourceNotFoundError("Not found")
            )
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError) as exc_info:
                await epic_tools_instance.list_related_userstories(auth_token="token", epic_id=999)
            assert "not found" in str(exc_info.value).lower()


class TestMoreSuccessPaths:
    """Tests adicionales para mejorar cobertura."""

    @pytest.mark.asyncio
    async def test_update_epic_full_success(self, epic_tools_instance):
        """Test update_epic_full path de éxito."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic_full = AsyncMock(
                return_value={
                    "id": 1,
                    "ref": 10,
                    "subject": "Updated Epic",
                    "project": 123,
                    "version": 2,
                }
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.update_epic_full(
                auth_token="token",
                epic_id=1,
                subject="Updated Epic",
                project=123,  # Required parameter
            )

            assert result["version"] == 2

    @pytest.mark.asyncio
    async def test_update_epic_partial_success(self, epic_tools_instance):
        """Test update_epic_partial path de éxito."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic = AsyncMock(
                return_value={
                    "id": 1,
                    "ref": 10,
                    "subject": "Patched Epic",
                    "project": 123,
                    "version": 3,
                }
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.update_epic_partial(
                auth_token="token", epic_id=1, subject="Patched Epic"
            )

            assert result["version"] == 3

    @pytest.mark.asyncio
    async def test_delete_epic_success(self, epic_tools_instance):
        """Test delete_epic path de éxito."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete_epic = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.delete_epic(auth_token="token", epic_id=1)

            assert "deleted" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_create_related_userstory_success(self, epic_tools_instance):
        """Test create_related_userstory path de éxito."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic_related_userstory = AsyncMock(
                return_value={"id": 1, "epic": 1, "user_story": 10, "order": 1}
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.create_related_userstory(
                auth_token="token", epic_id=1, user_story=10
            )

            assert result["user_story"] == 10

    @pytest.mark.asyncio
    async def test_bulk_create_epics_success(self, epic_tools_instance):
        """Test bulk_create_epics path de éxito."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.bulk_create_epics = AsyncMock(
                return_value=[
                    {"id": 1, "ref": 1, "subject": "Epic 1"},
                    {"id": 2, "ref": 2, "subject": "Epic 2"},
                ]
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.bulk_create_epics(
                auth_token="token", project_id=123, bulk_epics="Epic 1\nEpic 2"
            )

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_epic_filters_success(self, epic_tools_instance):
        """Test get_epic_filters path de éxito."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_filters = AsyncMock(
                return_value={
                    "statuses": [{"id": 1, "name": "New"}],
                    "assigned_to": [{"id": 1, "name": "User 1"}],
                }
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.get_epic_filters(auth_token="token", project_id=123)

            assert "statuses" in result

    @pytest.mark.asyncio
    async def test_upvote_epic_success(self, epic_tools_instance):
        """Test upvote_epic path de éxito."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.upvote_epic = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.upvote_epic(auth_token="token", epic_id=1)

            assert "voted" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_downvote_epic_success(self, epic_tools_instance):
        """Test downvote_epic path de éxito."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.downvote_epic = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.downvote_epic(auth_token="token", epic_id=1)

            assert "downvoted" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_get_epic_voters_success(self, epic_tools_instance):
        """Test get_epic_voters path de éxito."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_voters = AsyncMock(return_value=[{"id": 1, "full_name": "User 1"}])
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.get_epic_voters(auth_token="token", epic_id=1)

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_watch_epic_success(self, epic_tools_instance):
        """Test watch_epic path de éxito."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.watch_epic = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.watch_epic(auth_token="token", epic_id=1)

            assert "watching" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_unwatch_epic_success(self, epic_tools_instance):
        """Test unwatch_epic path de éxito."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.unwatch_epic = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.unwatch_epic(auth_token="token", epic_id=1)

            assert "stopped" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_get_epic_watchers_success(self, epic_tools_instance):
        """Test get_epic_watchers path de éxito."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_watchers = AsyncMock(
                return_value=[{"id": 1, "full_name": "Watcher 1"}]
            )
            mock_cls.return_value = mock_client

            result = await epic_tools_instance.get_epic_watchers(auth_token="token", epic_id=1)

            assert len(result) == 1


class TestMCPToolWrappersWithOptionalParams:
    """Tests para las funciones MCP tool wrapper con parámetros opcionales."""

    @pytest.mark.asyncio
    async def test_update_epic_full_tool_with_all_optional_params(self, epic_tools_instance):
        """Test update_epic_full_tool con todos los parámetros opcionales.

        Este test cubre las líneas 358-369 (kwargs building en el wrapper).
        Mockeamos el método de implementación para evitar la validación de project.
        """
        # Mock the implementation method directly on the instance
        epic_tools_instance.update_epic_full = AsyncMock(
            return_value={
                "id": 1,
                "ref": 10,
                "subject": "Updated",
                "project": 123,
                "version": 2,
                "description": "New desc",
                "color": "#FF0000",
                "assigned_to": 5,
                "status": 2,
                "tags": ["tag1"],
            }
        )

        # Get the tool from MCP
        tool = await epic_tools_instance.mcp.get_tool("taiga_update_epic_full")
        result = await tool.fn(
            auth_token="token",
            epic_id=1,
            project_id=123,
            subject="Updated",
            description="New desc",
            color="#FF0000",
            assigned_to=5,
            status=2,
            tags=["tag1"],
        )

        assert result["version"] == 2
        # Verify the implementation method was called with kwargs
        epic_tools_instance.update_epic_full.assert_called_once()
        call_kwargs = epic_tools_instance.update_epic_full.call_args.kwargs
        assert call_kwargs["description"] == "New desc"
        assert call_kwargs["color"] == "#FF0000"
        assert call_kwargs["assigned_to"] == 5

    @pytest.mark.asyncio
    async def test_create_epic_related_userstory_tool_with_order(self, epic_tools_instance):
        """Test create_epic_related_userstory_tool con parámetro order."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic_related_userstory = AsyncMock(
                return_value={"id": 1, "epic": 1, "user_story": 10, "order": 5}
            )
            mock_cls.return_value = mock_client

            # Get the tool from MCP
            tool = await epic_tools_instance.mcp.get_tool("taiga_create_epic_related_userstory")
            result = await tool.fn(auth_token="token", epic_id=1, user_story_id=10, order=5)

            assert result["order"] == 5

    @pytest.mark.asyncio
    async def test_update_epic_related_userstory_tool_with_all_params(self, epic_tools_instance):
        """Test update_epic_related_userstory_tool con todos los parámetros.

        Este test cubre las líneas 684-693 (kwargs building en el wrapper).
        Mockeamos el método de implementación directamente.
        """
        # Mock the implementation method directly on the instance
        epic_tools_instance.update_epic_related_userstory = AsyncMock(
            return_value={
                "id": 1,
                "epic": 1,
                "user_story": 10,
                "subject": "Updated Story",
                "description": "New desc",
                "status": 2,
                "assigned_to": 5,
            }
        )

        tool = await epic_tools_instance.mcp.get_tool("taiga_update_epic_related_userstory")
        result = await tool.fn(
            auth_token="token",
            epic_id=1,
            userstory_id=10,
            subject="Updated Story",
            description="New desc",
            status=2,
            assigned_to=5,
        )

        assert result["subject"] == "Updated Story"
        # Verify kwargs were built and passed
        epic_tools_instance.update_epic_related_userstory.assert_called_once()
        call_kwargs = epic_tools_instance.update_epic_related_userstory.call_args.kwargs
        assert call_kwargs["subject"] == "Updated Story"
        assert call_kwargs["description"] == "New desc"

    @pytest.mark.asyncio
    async def test_create_epic_attachment_tool_with_description(self, epic_tools_instance):
        """Test create_epic_attachment_tool con parámetro description."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic_attachment = AsyncMock(
                return_value={
                    "id": 1,
                    "name": "file.pdf",
                    "size": 1024,
                    "description": "Important doc",
                    "object_id": 10,
                }
            )
            mock_cls.return_value = mock_client

            tool = await epic_tools_instance.mcp.get_tool("taiga_create_epic_attachment")
            result = await tool.fn(
                auth_token="token", epic_id=10, file="base64_content", description="Important doc"
            )

            assert result["description"] == "Important doc"

    @pytest.mark.asyncio
    async def test_update_epic_attachment_tool_with_description(self, epic_tools_instance):
        """Test update_epic_attachment_tool con parámetro description."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.update_epic_attachment = AsyncMock(
                return_value={"id": 1, "name": "file.pdf", "description": "Updated desc"}
            )
            mock_cls.return_value = mock_client

            tool = await epic_tools_instance.mcp.get_tool("taiga_update_epic_attachment")
            result = await tool.fn(auth_token="token", attachment_id=1, description="Updated desc")

            assert result["description"] == "Updated desc"

    @pytest.mark.asyncio
    async def test_create_epic_custom_attribute_tool_with_all_params(self, epic_tools_instance):
        """Test create_epic_custom_attribute_tool con todos los parámetros."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic_custom_attribute = AsyncMock(
                return_value={
                    "id": 1,
                    "name": "Priority",
                    "description": "Priority level",
                    "order": 5,
                    "project": 123,
                }
            )
            mock_cls.return_value = mock_client

            tool = await epic_tools_instance.mcp.get_tool("taiga_create_epic_custom_attribute")
            result = await tool.fn(
                auth_token="token",
                project_id=123,
                name="Priority",
                description="Priority level",
                order=5,
            )

            assert result["name"] == "Priority"
            assert result["order"] == 5

    @pytest.mark.asyncio
    async def test_get_epic_tool_wrapper(self, epic_tools_instance):
        """Test get_epic_tool wrapper (line 245)."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic = AsyncMock(
                return_value={"id": 1, "ref": 10, "subject": "Epic", "project": 123}
            )
            mock_cls.return_value = mock_client

            tool = await epic_tools_instance.mcp.get_tool("taiga_get_epic")
            result = await tool.fn(auth_token="token", epic_id=1)

            assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_get_epic_by_ref_tool_wrapper(self, epic_tools_instance):
        """Test get_epic_by_ref_tool wrapper (line 295)."""
        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_epic_by_ref = AsyncMock(
                return_value={"id": 1, "ref": 10, "subject": "Epic", "project": 123}
            )
            mock_cls.return_value = mock_client

            tool = await epic_tools_instance.mcp.get_tool("taiga_get_epic_by_ref")
            result = await tool.fn(auth_token="token", project_id=123, ref=10)

            assert result["ref"] == 10


class TestValidationErrorHandling:
    """Tests para ValidationError handling."""

    @pytest.mark.asyncio
    async def test_create_epic_domain_validation_error(self, epic_tools_instance):
        """Test create_epic con ValidationError from domain (lines 1566-1568).

        La ValidationError del dominio se lanza cuando hay errores de validación
        personalizados. El código la captura y la convierte en ToolError.
        """
        from src.domain.exceptions import ValidationError as DomainValidationError

        with patch("src.application.tools.epic_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_epic = AsyncMock(
                return_value={"id": 1, "ref": 10, "subject": "Epic", "project": 123}
            )
            mock_cls.return_value = mock_client

            # Mock EpicResponse.model_validate to raise domain ValidationError
            with patch(
                "src.application.tools.epic_tools.EpicResponse.model_validate"
            ) as mock_validate:
                mock_validate.side_effect = DomainValidationError("Invalid epic data")

                with pytest.raises(ToolError) as exc_info:
                    await epic_tools_instance.create_epic(
                        auth_token="token", project=123, subject="New Epic"
                    )
                # ValidationError is caught and converted to ToolError
                assert "Invalid epic data" in str(exc_info.value)
