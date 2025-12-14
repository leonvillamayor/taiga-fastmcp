"""
Tests for Milestone/Sprint management tools.
MILE-001 to MILE-010: Complete Milestone functionality testing.
"""

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.application.tools.milestone_tools import MilestoneTools


class TestMilestoneCRUD:
    """Tests for Milestone CRUD operations (MILE-001 to MILE-006)."""

    @pytest.mark.asyncio
    async def test_list_milestones_tool_is_registered(self, mcp_server, taiga_client_mock) -> None:
        """MILE-001: Test that list_milestones tool is registered in MCP server."""
        assert hasattr(mcp_server.milestone_tools, "list_milestones")

    @pytest.mark.asyncio
    async def test_list_milestones_with_valid_token(self, mcp_server, taiga_client_mock) -> None:
        """MILE-001: Test listing milestones with valid auth token."""
        # Configurar mock - AutoPaginator usa client.get() con formato paginado
        taiga_client_mock.get.return_value = [
            {
                "id": 5678,
                "name": "Sprint 1",
                "slug": "sprint-1",
                "project": 309804,
                "estimated_start": "2025-01-15",
                "estimated_finish": "2025-01-29",
                "created_date": "2025-01-10T08:00:00Z",
                "modified_date": "2025-01-20T12:00:00Z",
                "closed": False,
                "disponibility": 0.0,
                "total_points": 45.0,
                "closed_points": 20.0,
                "watchers": [888691],
            },
            {
                "id": 5679,
                "name": "Sprint 2",
                "slug": "sprint-2",
                "project": 309804,
                "estimated_start": "2025-02-01",
                "estimated_finish": "2025-02-15",
                "closed": False,
                "total_points": 50.0,
                "closed_points": 0.0,
            },
        ]

        # Ejecutar herramienta
        result = await mcp_server.milestone_tools.list_milestones(
            auth_token="valid_token", project=309804
        )

        # Verificar
        assert len(result) == 2
        assert result[0]["name"] == "Sprint 1"
        assert result[0]["total_points"] == 45.0
        assert result[1]["name"] == "Sprint 2"
        # AutoPaginator calls client.get, not list_milestones
        taiga_client_mock.get.assert_called()

    @pytest.mark.asyncio
    async def test_list_milestones_with_closed_filter(self, mcp_server, taiga_client_mock) -> None:
        """MILE-001: Test listing milestones filtered by closed status."""
        # Configurar mock - AutoPaginator usa client.get()
        taiga_client_mock.get.return_value = []

        # Test filtrar solo milestones cerrados
        await mcp_server.milestone_tools.list_milestones(
            auth_token="valid_token", project=309804, closed=True
        )

        # AutoPaginator calls client.get with params
        taiga_client_mock.get.assert_called()

    @pytest.mark.asyncio
    async def test_create_milestone_tool_is_registered(self, mcp_server) -> None:
        """MILE-002: Test that create_milestone tool is registered."""
        assert hasattr(mcp_server.milestone_tools, "create_milestone")

    @pytest.mark.asyncio
    async def test_create_milestone_with_valid_data(self, mcp_server, taiga_client_mock) -> None:
        """MILE-002: Test creating a milestone with valid data."""
        # Configurar mock
        taiga_client_mock.create_milestone.return_value = {
            "id": 5680,
            "name": "Sprint 3",
            "slug": "sprint-3",
            "project": 309804,
            "estimated_start": "2025-02-16",
            "estimated_finish": "2025-03-01",
            "created_date": "2025-01-25T10:00:00Z",
            "closed": False,
            "disponibility": 0.0,
            "total_points": 0.0,
            "closed_points": 0.0,
        }

        # Ejecutar
        result = await mcp_server.milestone_tools.create_milestone(
            auth_token="valid_token",
            project=309804,
            name="Sprint 3",
            estimated_start="2025-02-16",
            estimated_finish="2025-03-01",
        )

        # Verificar
        assert result["id"] == 5680
        assert result["name"] == "Sprint 3"
        assert result["estimated_start"] == "2025-02-16"
        taiga_client_mock.create_milestone.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_milestone_without_required_fields(self, mcp_server) -> None:
        """MILE-002: Test creating a milestone without required fields fails."""
        with pytest.raises(ValueError, match="project and name are required"):
            await mcp_server.milestone_tools.create_milestone(
                auth_token="valid_token",
                project_id=309804,  # Missing name
            )

    @pytest.mark.asyncio
    async def test_get_milestone_tool_is_registered(self, mcp_server) -> None:
        """MILE-003: Test that get_milestone tool is registered."""
        assert hasattr(mcp_server.milestone_tools, "get_milestone")

    @pytest.mark.asyncio
    async def test_get_milestone_by_id(self, mcp_server, taiga_client_mock) -> None:
        """MILE-003: Test getting a milestone by ID."""
        # Configurar mock
        taiga_client_mock.get_milestone.return_value = {
            "id": 5678,
            "name": "Sprint 1",
            "slug": "sprint-1",
            "project": 309804,
            "estimated_start": "2025-01-15",
            "estimated_finish": "2025-01-29",
            "closed": False,
            "total_points": 45.0,
            "closed_points": 20.0,
            "user_stories": [{"id": 123456, "ref": 1, "subject": "Login de usuarios"}],
            "watchers": [888691],
        }

        # Ejecutar
        result = await mcp_server.milestone_tools.get_milestone(
            auth_token="valid_token", milestone_id=5678
        )

        # Verificar
        assert result["id"] == 5678
        assert result["name"] == "Sprint 1"
        assert len(result["user_stories"]) == 1
        taiga_client_mock.get_milestone.assert_called_once_with(milestone_id=5678)

    @pytest.mark.asyncio
    async def test_update_milestone_full_tool_is_registered(self, mcp_server) -> None:
        """MILE-004: Test that update_milestone_full tool is registered."""
        assert hasattr(mcp_server.milestone_tools, "update_milestone_full")

    @pytest.mark.asyncio
    async def test_update_milestone_full(self, mcp_server, taiga_client_mock) -> None:
        """MILE-004: Test full update (PUT) of a milestone."""
        # Configurar mock
        updated_milestone = {
            "id": 5678,
            "name": "Sprint 1 - Extended",
            "slug": "sprint-1-extended",
            "project": 309804,
            "estimated_start": "2025-01-15",
            "estimated_finish": "2025-02-05",
            "closed": False,
            "total_points": 60.0,
            "closed_points": 25.0,
        }
        taiga_client_mock.update_milestone_full.return_value = updated_milestone

        # Ejecutar
        result = await mcp_server.milestone_tools.update_milestone_full(
            auth_token="valid_token",
            milestone_id=5678,
            name="Sprint 1 - Extended",
            estimated_start="2025-01-15",
            estimated_finish="2025-02-05",
        )

        # Verificar
        assert result["name"] == "Sprint 1 - Extended"
        assert result["estimated_finish"] == "2025-02-05"
        taiga_client_mock.update_milestone_full.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_milestone_partial_tool_is_registered(self, mcp_server) -> None:
        """MILE-005: Test that update_milestone tool (PATCH) is registered."""
        assert hasattr(mcp_server.milestone_tools, "update_milestone")

    @pytest.mark.asyncio
    async def test_update_milestone_partial(self, mcp_server, taiga_client_mock) -> None:
        """MILE-005: Test partial update (PATCH) of a milestone."""
        # Configurar mock
        taiga_client_mock.update_milestone.return_value = {
            "id": 5678,
            "name": "Sprint 1 - Finalizado",
            "closed": True,
            "total_points": 45.0,
            "closed_points": 45.0,
        }

        # Ejecutar
        result = await mcp_server.milestone_tools.update_milestone(
            auth_token="valid_token", milestone_id=5678, name="Sprint 1 - Finalizado", closed=True
        )

        # Verificar
        assert result["name"] == "Sprint 1 - Finalizado"
        assert result["closed"] is True
        assert result["closed_points"] == 45.0
        taiga_client_mock.update_milestone.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_milestone_tool_is_registered(self, mcp_server) -> None:
        """MILE-006: Test that delete_milestone tool is registered."""
        assert hasattr(mcp_server.milestone_tools, "delete_milestone")

    @pytest.mark.asyncio
    async def test_delete_milestone(self, mcp_server, taiga_client_mock) -> None:
        """MILE-006: Test deleting a milestone."""
        # Configurar mock
        taiga_client_mock.delete_milestone.return_value = {"success": True}

        # Ejecutar
        result = await mcp_server.milestone_tools.delete_milestone(
            auth_token="valid_token", milestone_id=5678
        )

        # Verificar
        assert result["success"] is True
        taiga_client_mock.delete_milestone.assert_called_once_with(milestone_id=5678)


class TestMilestoneStatistics:
    """Tests for Milestone statistics (MILE-007)."""

    @pytest.mark.asyncio
    async def test_get_milestone_stats_tool_is_registered(self, mcp_server) -> None:
        """MILE-007: Test that get_milestone_stats tool is registered."""
        assert hasattr(mcp_server.milestone_tools, "get_milestone_stats")

    @pytest.mark.asyncio
    async def test_get_milestone_stats(self, mcp_server, taiga_client_mock) -> None:
        """MILE-007: Test getting milestone statistics."""
        # Configurar mock
        taiga_client_mock.get_milestone_stats.return_value = {
            "name": "Sprint 1",
            "estimated_start": "2025-01-15",
            "estimated_finish": "2025-01-29",
            "total_points": 45.0,
            "completed_points": 20.0,
            "total_userstories": 10,
            "completed_userstories": 4,
            "total_tasks": 30,
            "completed_tasks": 15,
            "iocaine_doses": 2,
            "days": [
                {"day": "2025-01-15", "open_points": 45.0, "completed_points": 0.0},
                {"day": "2025-01-16", "open_points": 40.0, "completed_points": 5.0},
                {"day": "2025-01-17", "open_points": 35.0, "completed_points": 10.0},
            ],
        }

        # Ejecutar
        result = await mcp_server.milestone_tools.get_milestone_stats(
            auth_token="valid_token", milestone_id=5678
        )

        # Verificar
        assert result["name"] == "Sprint 1"
        assert result["total_points"] == 45.0
        assert result["completed_points"] == 20.0
        assert result["total_userstories"] == 10
        assert result["completed_userstories"] == 4
        assert len(result["days"]) == 3
        assert result["days"][0]["day"] == "2025-01-15"
        taiga_client_mock.get_milestone_stats.assert_called_once_with(milestone_id=5678)

    @pytest.mark.asyncio
    async def test_get_milestone_burndown_chart_data(self, mcp_server, taiga_client_mock) -> None:
        """MILE-007: Test getting milestone burndown chart data."""
        # Configurar mock para obtener datos del burndown
        taiga_client_mock.get_milestone_stats.return_value = {
            "name": "Sprint 1",
            "total_points": 45.0,
            "days": [
                {"day": "2025-01-15", "open_points": 45.0, "completed_points": 0.0},
                {"day": "2025-01-16", "open_points": 40.0, "completed_points": 5.0},
                {"day": "2025-01-17", "open_points": 35.0, "completed_points": 10.0},
                {"day": "2025-01-18", "open_points": 30.0, "completed_points": 15.0},
                {"day": "2025-01-19", "open_points": 25.0, "completed_points": 20.0},
            ],
        }

        # Ejecutar
        result = await mcp_server.milestone_tools.get_milestone_stats(
            auth_token="valid_token", milestone_id=5678
        )

        # Verificar que tenemos datos para el burndown chart
        assert "days" in result
        assert len(result["days"]) == 5

        # Verificar progreso día a día
        for i, day_data in enumerate(result["days"]):
            assert "day" in day_data
            assert "open_points" in day_data
            assert "completed_points" in day_data
            # Los puntos completados deben ir aumentando
            if i > 0:
                assert day_data["completed_points"] >= result["days"][i - 1]["completed_points"]
            # Los puntos abiertos deben ir disminuyendo
            if i > 0:
                assert day_data["open_points"] <= result["days"][i - 1]["open_points"]


class TestMilestoneWatchers:
    """Tests for Milestone watchers functionality (MILE-008 to MILE-010)."""

    @pytest.mark.asyncio
    async def test_watch_milestone_tool_is_registered(self, mcp_server) -> None:
        """MILE-008: Test that watch_milestone tool is registered."""
        assert hasattr(mcp_server.milestone_tools, "watch_milestone")

    @pytest.mark.asyncio
    async def test_watch_milestone(self, mcp_server, taiga_client_mock) -> None:
        """MILE-008: Test watching a milestone."""
        # Configurar mock
        taiga_client_mock.watch_milestone.return_value = {
            "id": 5678,
            "watchers": [888691, 999999],
            "total_watchers": 2,
        }

        # Ejecutar
        result = await mcp_server.milestone_tools.watch_milestone(
            auth_token="valid_token", milestone_id=5678
        )

        # Verificar
        assert result["total_watchers"] == 2
        assert 888691 in result["watchers"]
        assert 999999 in result["watchers"]
        taiga_client_mock.watch_milestone.assert_called_once_with(milestone_id=5678)

    @pytest.mark.asyncio
    async def test_unwatch_milestone_tool_is_registered(self, mcp_server) -> None:
        """MILE-009: Test that unwatch_milestone tool is registered."""
        assert hasattr(mcp_server.milestone_tools, "unwatch_milestone")

    @pytest.mark.asyncio
    async def test_unwatch_milestone(self, mcp_server, taiga_client_mock) -> None:
        """MILE-009: Test unwatching a milestone."""
        # Configurar mock
        taiga_client_mock.unwatch_milestone.return_value = {
            "id": 5678,
            "watchers": [888691],
            "total_watchers": 1,
        }

        # Ejecutar
        result = await mcp_server.milestone_tools.unwatch_milestone(
            auth_token="valid_token", milestone_id=5678
        )

        # Verificar
        assert result["total_watchers"] == 1
        assert 888691 in result["watchers"]
        taiga_client_mock.unwatch_milestone.assert_called_once_with(milestone_id=5678)

    @pytest.mark.asyncio
    async def test_get_milestone_watchers_tool_is_registered(self, mcp_server) -> None:
        """MILE-010: Test that get_milestone_watchers tool is registered."""
        assert hasattr(mcp_server.milestone_tools, "get_milestone_watchers")

    @pytest.mark.asyncio
    async def test_get_milestone_watchers(self, mcp_server, taiga_client_mock) -> None:
        """MILE-010: Test getting watchers of a milestone."""
        # Configurar mock
        taiga_client_mock.get_milestone_watchers.return_value = [
            {"id": 888691, "username": "usuario1", "full_name": "Usuario Uno"},
            {"id": 999999, "username": "usuario2", "full_name": "Usuario Dos"},
            {"id": 777777, "username": "usuario3", "full_name": "Usuario Tres"},
        ]

        # Ejecutar
        result = await mcp_server.milestone_tools.get_milestone_watchers(
            auth_token="valid_token", milestone_id=5678
        )

        # Verificar
        assert len(result) == 3
        assert result[0]["username"] == "usuario1"
        assert result[1]["username"] == "usuario2"
        assert result[2]["username"] == "usuario3"
        taiga_client_mock.get_milestone_watchers.assert_called_once_with(milestone_id=5678)

    @pytest.mark.asyncio
    async def test_milestone_user_stories_management(self, mcp_server, taiga_client_mock) -> None:
        """Test managing user stories within a milestone."""
        # Configurar mock para obtener milestone con user stories
        taiga_client_mock.get_milestone.return_value = {
            "id": 5678,
            "name": "Sprint 1",
            "total_points": 45.0,
            "user_stories": [
                {"id": 123456, "ref": 1, "subject": "Login de usuarios", "total_points": 5.0},
                {"id": 123457, "ref": 2, "subject": "Registro de usuarios", "total_points": 8.0},
                {"id": 123458, "ref": 3, "subject": "Reset password", "total_points": 3.0},
            ],
        }

        # Ejecutar
        result = await mcp_server.milestone_tools.get_milestone(
            auth_token="valid_token", milestone_id=5678
        )

        # Verificar user stories en el milestone
        assert "user_stories" in result
        assert len(result["user_stories"]) == 3

        # Verificar que la suma de puntos de las user stories sea coherente
        total_story_points = sum(us.get("total_points", 0) for us in result["user_stories"])
        assert total_story_points == 16.0  # 5 + 8 + 3

    @pytest.mark.asyncio
    async def test_milestone_completion_tracking(self, mcp_server, taiga_client_mock) -> None:
        """Test tracking milestone completion progress."""
        # Configurar mock para milestone con progreso
        taiga_client_mock.get_milestone_stats.return_value = {
            "name": "Sprint 1",
            "total_points": 45.0,
            "completed_points": 30.0,
            "total_userstories": 10,
            "completed_userstories": 6,
            "total_tasks": 25,
            "completed_tasks": 20,
            "completion_percentage": 66.67,
            "days_remaining": 5,
            "estimated_finish": "2025-01-29",
        }

        # Ejecutar
        result = await mcp_server.milestone_tools.get_milestone_stats(
            auth_token="valid_token", milestone_id=5678
        )

        # Verificar métricas de completitud
        assert result["completed_points"] == 30.0
        assert result["total_points"] == 45.0

        # Calcular porcentaje de completitud
        completion_percentage = (result["completed_points"] / result["total_points"]) * 100
        assert completion_percentage == pytest.approx(66.67, rel=0.01)

        # Verificar progreso de user stories
        assert result["completed_userstories"] == 6
        assert result["total_userstories"] == 10

        # Verificar progreso de tareas
        assert result["completed_tasks"] == 20
        assert result["total_tasks"] == 25


class TestMilestoneToolsCoverage:
    """Tests for additional coverage of MilestoneTools."""

    @pytest.fixture
    def mock_taiga_api(self, respx_mock):
        """Fixture para mock de la API de Taiga."""
        # Auth
        respx_mock.post("https://api.taiga.io/api/v1/auth").mock(
            return_value=httpx.Response(
                200,
                json={
                    "auth_token": "test_token",
                    "id": 1,
                    "username": "testuser",
                },
            )
        )
        return respx_mock

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_milestones_auto_paginate_false(self, mock_taiga_api) -> None:
        """Test list_milestones con auto_paginate=False."""
        mcp = FastMCP("Test")
        milestone_tools = MilestoneTools(mcp)

        mock_taiga_api.get(
            "https://api.taiga.io/api/v1/milestones?project=123&page=1&page_size=100"
        ).mock(
            return_value=httpx.Response(
                200,
                json=[{"id": 1, "name": "Sprint 1", "project": 123}],
            )
        )

        result = await milestone_tools.list_milestones(
            auth_token="token", project=123, auto_paginate=False
        )
        assert len(result) == 1
        assert result[0]["name"] == "Sprint 1"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_milestone_missing_dates(self, mock_taiga_api) -> None:
        """Test create_milestone without estimated_start/estimated_finish."""
        mcp = FastMCP("Test")
        milestone_tools = MilestoneTools(mcp)

        with pytest.raises(ValueError, match="estimated_start and estimated_finish are required"):
            await milestone_tools.create_milestone(
                auth_token="token",
                project=123,
                name="Sprint 1",
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_milestone_full_missing_name(self, mock_taiga_api) -> None:
        """Test update_milestone_full without required name."""
        mcp = FastMCP("Test")
        milestone_tools = MilestoneTools(mcp)

        with pytest.raises(ValueError, match="name is required for full update"):
            await milestone_tools.update_milestone_full(
                auth_token="token",
                milestone_id=1,
                estimated_start="2025-01-01",
                estimated_finish="2025-01-15",
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_milestone_full_missing_dates(self, mock_taiga_api) -> None:
        """Test update_milestone_full without required dates."""
        mcp = FastMCP("Test")
        milestone_tools = MilestoneTools(mcp)

        with pytest.raises(
            ValueError, match="estimated_start and estimated_finish are required for full update"
        ):
            await milestone_tools.update_milestone_full(
                auth_token="token",
                milestone_id=1,
                name="Sprint 1",
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_milestone_non_dict_result(self, mock_taiga_api) -> None:
        """Test delete_milestone when client returns non-dict (e.g., None)."""
        from unittest.mock import AsyncMock, patch

        mcp = FastMCP("Test")
        milestone_tools = MilestoneTools(mcp)

        # Mock to return None (common for DELETE 204)
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.delete_milestone = AsyncMock(return_value=None)

        with patch(
            "src.application.tools.milestone_tools.TaigaAPIClient", return_value=mock_client
        ):
            result = await milestone_tools.delete_milestone(auth_token="token", milestone_id=123)

        assert "success" in result
        assert "message" in result
        assert "123" in result["message"]


class TestMilestoneToolsViaFastMCP:
    """Tests that exercise the MCP tool wrapper functions directly."""

    @pytest.fixture
    def mock_taiga_api(self, respx_mock):
        """Fixture para mock de la API de Taiga."""
        respx_mock.post("https://api.taiga.io/api/v1/auth").mock(
            return_value=httpx.Response(
                200, json={"auth_token": "test_token", "id": 1, "username": "testuser"}
            )
        )
        return respx_mock

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_milestone_tool_validation_error(self, mock_taiga_api) -> None:
        """Test create_milestone_tool ValidationError handler."""
        mcp = FastMCP("Test")
        MilestoneTools(mcp)

        # Get the registered tool
        tools = await mcp.get_tools()
        create_tool = tools.get("taiga_create_milestone")
        assert create_tool is not None

        # Call with invalid data - project_id=0 should fail validation
        with pytest.raises(ToolError):
            await create_tool.fn(
                auth_token="token",
                project_id=0,  # Invalid
                name="Sprint",
                estimated_start="2025-01-01",
                estimated_finish="2025-01-15",
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_milestone_full_tool_validation_error(self, mock_taiga_api) -> None:
        """Test update_milestone_full_tool ValidationError handler."""
        mcp = FastMCP("Test")
        MilestoneTools(mcp)

        tools = await mcp.get_tools()
        update_tool = tools.get("taiga_update_milestone_full")
        assert update_tool is not None

        # Call with invalid data - milestone_id=0 should fail validation
        with pytest.raises(ToolError):
            await update_tool.fn(
                auth_token="token",
                milestone_id=0,  # Invalid
                project_id=123,
                name="Sprint",
                estimated_start="2025-01-01",
                estimated_finish="2025-01-15",
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_milestone_partial_tool_validation_error(self, mock_taiga_api) -> None:
        """Test update_milestone_partial_tool ValidationError handler."""
        mcp = FastMCP("Test")
        MilestoneTools(mcp)

        tools = await mcp.get_tools()
        update_tool = tools.get("taiga_update_milestone")
        assert update_tool is not None

        # Call with invalid data - milestone_id=0 should fail validation
        with pytest.raises(ToolError):
            await update_tool.fn(
                auth_token="token",
                milestone_id=0,  # Invalid
                name="Sprint Updated",
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_milestones_tool_via_mcp(self, mock_taiga_api) -> None:
        """Test list_milestones through tool wrapper."""
        mcp = FastMCP("Test")
        MilestoneTools(mcp)

        mock_taiga_api.get(
            "https://api.taiga.io/api/v1/milestones?project=123&page=1&page_size=100"
        ).mock(
            return_value=httpx.Response(200, json=[{"id": 1, "name": "Sprint 1", "project": 123}])
        )

        tools = await mcp.get_tools()
        list_tool = tools.get("taiga_list_milestones")
        result = await list_tool.fn(auth_token="token", project_id=123, auto_paginate=False)

        assert len(result) == 1
        assert result[0]["name"] == "Sprint 1"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_milestone_tool_via_mcp(self, mock_taiga_api) -> None:
        """Test get_milestone through tool wrapper."""
        mcp = FastMCP("Test")
        MilestoneTools(mcp)

        mock_taiga_api.get("https://api.taiga.io/api/v1/milestones/45").mock(
            return_value=httpx.Response(
                200, json={"id": 45, "name": "Sprint 5", "project": 123, "closed": False}
            )
        )

        tools = await mcp.get_tools()
        get_tool = tools.get("taiga_get_milestone")
        result = await get_tool.fn(auth_token="token", milestone_id=45)

        assert result["id"] == 45
        assert result["name"] == "Sprint 5"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_milestone_tool_via_mcp(self, mock_taiga_api) -> None:
        """Test delete_milestone through tool wrapper."""
        mcp = FastMCP("Test")
        MilestoneTools(mcp)

        mock_taiga_api.delete("https://api.taiga.io/api/v1/milestones/45").mock(
            return_value=httpx.Response(204)
        )

        tools = await mcp.get_tools()
        delete_tool = tools.get("taiga_delete_milestone")
        result = await delete_tool.fn(auth_token="token", milestone_id=45)

        assert "success" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_milestone_stats_tool_via_mcp(self, mock_taiga_api) -> None:
        """Test get_milestone_stats through tool wrapper."""
        mcp = FastMCP("Test")
        MilestoneTools(mcp)

        mock_taiga_api.get("https://api.taiga.io/api/v1/milestones/45/stats").mock(
            return_value=httpx.Response(
                200,
                json={
                    "name": "Sprint 5",
                    "total_points": 50.0,
                    "completed_points": 25.0,
                    "days": [],
                },
            )
        )

        tools = await mcp.get_tools()
        stats_tool = tools.get("taiga_get_milestone_stats")
        result = await stats_tool.fn(auth_token="token", milestone_id=45)

        assert result["name"] == "Sprint 5"
        assert result["total_points"] == 50.0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_watch_milestone_tool_via_mcp(self, mock_taiga_api) -> None:
        """Test watch_milestone through tool wrapper."""
        mcp = FastMCP("Test")
        MilestoneTools(mcp)

        mock_taiga_api.post("https://api.taiga.io/api/v1/milestones/45/watch").mock(
            return_value=httpx.Response(200, json={"id": 45, "total_watchers": 3})
        )

        tools = await mcp.get_tools()
        watch_tool = tools.get("taiga_watch_milestone")
        result = await watch_tool.fn(auth_token="token", milestone_id=45)

        assert result["id"] == 45
        assert result["total_watchers"] == 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unwatch_milestone_tool_via_mcp(self, mock_taiga_api) -> None:
        """Test unwatch_milestone through tool wrapper."""
        mcp = FastMCP("Test")
        MilestoneTools(mcp)

        mock_taiga_api.post("https://api.taiga.io/api/v1/milestones/45/unwatch").mock(
            return_value=httpx.Response(200, json={"id": 45, "total_watchers": 2})
        )

        tools = await mcp.get_tools()
        unwatch_tool = tools.get("taiga_unwatch_milestone")
        result = await unwatch_tool.fn(auth_token="token", milestone_id=45)

        assert result["id"] == 45
        assert result["total_watchers"] == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_milestone_watchers_tool_via_mcp(self, mock_taiga_api) -> None:
        """Test get_milestone_watchers through tool wrapper."""
        mcp = FastMCP("Test")
        MilestoneTools(mcp)

        mock_taiga_api.get("https://api.taiga.io/api/v1/milestones/45/watchers").mock(
            return_value=httpx.Response(
                200,
                json=[{"id": 1, "username": "user1"}, {"id": 2, "username": "user2"}],
            )
        )

        tools = await mcp.get_tools()
        watchers_tool = tools.get("taiga_get_milestone_watchers")
        result = await watchers_tool.fn(auth_token="token", milestone_id=45)

        assert len(result) == 2
        assert result[0]["username"] == "user1"
