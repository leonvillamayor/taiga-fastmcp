"""
Tests de integración para las herramientas de Membresías del servidor MCP.
Prueba la integración completa de las funcionalidades de Membresías.
"""

import httpx
import pytest
from fastmcp import FastMCP

from src.application.tools.membership_tools import MembershipTools
from src.application.tools.project_tools import ProjectTools


class TestMembershipsIntegration:
    """Tests de integración para Membresías."""

    @pytest.mark.integration
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_complete_membership_lifecycle(self, mock_taiga_api, auth_token) -> None:
        """
        Test completo del ciclo de vida de una membresía:
        1. Crear proyecto
        2. Crear membresía
        3. Listar membresías
        4. Obtener membresía
        5. Actualizar membresía
        6. Eliminar membresía
        """
        # Arrange
        mcp = FastMCP("Test Memberships Integration")
        membership_tools = MembershipTools(mcp)
        project_tools = ProjectTools(mcp)
        membership_tools.register_tools()
        project_tools.register_tools()

        project_id = 123

        # 1. Crear proyecto (simulación)
        mock_taiga_api.post("https://api.taiga.io/api/v1/projects").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": project_id,
                    "name": "Test Project",
                    "slug": "test-project",
                    "owner": {"id": 1, "username": "owner"},
                },
            )
        )

        project_result = await project_tools.create_project(
            auth_token=auth_token, name="Test Project", description="Project for membership tests"
        )

        assert project_result["id"] == project_id

        # 2. Crear membresía
        mock_taiga_api.post("https://api.taiga.io/api/v1/memberships").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": 100,
                    "user": {
                        "id": 200,
                        "username": "newmember",
                        "full_name": "New Member",
                        "email": "newmember@example.com",
                    },
                    "role": {"id": 11, "name": "Developer", "slug": "developer"},
                    "project": project_id,
                    "is_admin": False,
                },
            )
        )

        membership_result = await membership_tools.create_membership(
            auth_token=auth_token, project_id=project_id, role=11, email="newmember@example.com"
        )

        assert membership_result["id"] == 100
        assert membership_result["user"]["email"] == "newmember@example.com"

        # 3. Listar membresías (includes pagination params from AutoPaginator)
        mock_taiga_api.get(
            f"https://api.taiga.io/api/v1/memberships?project={project_id}&page=1&page_size=100"
        ).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "user": {"id": 1, "username": "owner"},
                        "role": {"id": 10, "name": "Product Owner"},
                        "is_admin": True,
                    },
                    {
                        "id": 100,
                        "user": {"id": 200, "username": "newmember"},
                        "role": {"id": 11, "name": "Developer"},
                        "is_admin": False,
                    },
                ],
            )
        )

        list_result = await membership_tools.list_memberships(
            auth_token=auth_token, project_id=project_id
        )

        assert len(list_result) == 2
        assert list_result[1]["id"] == 100

        # 4. Obtener membresía específica
        mock_taiga_api.get("https://api.taiga.io/api/v1/memberships/100").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 100,
                    "user": {
                        "id": 200,
                        "username": "newmember",
                        "full_name": "New Member",
                        "email": "newmember@example.com",
                    },
                    "role": {
                        "id": 11,
                        "name": "Developer",
                        "permissions": ["view_project", "edit_tasks"],
                    },
                    "project": {"id": project_id, "name": "Test Project"},
                    "is_admin": False,
                },
            )
        )

        get_result = await membership_tools.get_membership(auth_token=auth_token, membership_id=100)

        assert get_result["id"] == 100
        assert get_result["user"]["username"] == "newmember"

        # 5. Actualizar membresía (cambiar rol)
        mock_taiga_api.patch("https://api.taiga.io/api/v1/memberships/100").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 100,
                    "user": {"id": 200, "username": "newmember"},
                    "role": {"id": 12, "name": "Scrum Master", "slug": "scrum-master"},
                    "is_admin": True,
                },
            )
        )

        update_result = await membership_tools.update_membership(
            auth_token=auth_token, membership_id=100, role=12, is_admin=True
        )

        assert update_result["role"]["name"] == "Scrum Master"
        assert update_result["is_admin"] is True

        # 6. Eliminar membresía
        mock_taiga_api.delete("https://api.taiga.io/api/v1/memberships/100").mock(
            return_value=httpx.Response(204)
        )

        delete_result = await membership_tools.delete_membership(
            auth_token=auth_token, membership_id=100
        )

        assert delete_result is True

    @pytest.mark.integration
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_membership_bulk_operations(self, mock_taiga_api, auth_token) -> None:
        """
        Test de operaciones en lote con membresías.
        """
        # Arrange
        mcp = FastMCP("Test Memberships Integration")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()
        project_id = 123

        # Crear múltiples membresías
        emails = ["user1@example.com", "user2@example.com", "user3@example.com"]

        for i, email in enumerate(emails, start=1):
            mock_taiga_api.post("https://api.taiga.io/api/v1/memberships").mock(
                return_value=httpx.Response(
                    201,
                    json={
                        "id": 100 + i,
                        "user": {"id": 200 + i, "username": f"user{i}", "email": email},
                        "role": {"id": 11, "name": "Developer"},
                        "project": project_id,
                        "is_admin": False,
                    },
                )
            )

            result = await membership_tools.create_membership(
                auth_token=auth_token, project_id=project_id, role=11, email=email
            )

            assert result["user"]["email"] == email

        # Listar todas las membresías (includes pagination params from AutoPaginator)
        mock_taiga_api.get(
            f"https://api.taiga.io/api/v1/memberships?project={project_id}&page=1&page_size=100"
        ).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": 101,
                        "user": {"id": 201, "username": "user1", "email": "user1@example.com"},
                        "role": {"id": 11, "name": "Developer"},
                    },
                    {
                        "id": 102,
                        "user": {"id": 202, "username": "user2", "email": "user2@example.com"},
                        "role": {"id": 11, "name": "Developer"},
                    },
                    {
                        "id": 103,
                        "user": {"id": 203, "username": "user3", "email": "user3@example.com"},
                        "role": {"id": 11, "name": "Developer"},
                    },
                ],
            )
        )

        list_result = await membership_tools.list_memberships(
            auth_token=auth_token, project_id=project_id
        )

        assert len(list_result) == 3
        assert all(m["role"]["name"] == "Developer" for m in list_result)

    @pytest.mark.integration
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_membership_with_username(self, mock_taiga_api, auth_token) -> None:
        """
        Test de creación de membresía usando username en lugar de email.
        """
        # Arrange
        mcp = FastMCP("Test Memberships Integration")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()

        # Crear membresía con username
        mock_taiga_api.post("https://api.taiga.io/api/v1/memberships").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": 150,
                    "user": {"id": 250, "username": "existinguser", "full_name": "Existing User"},
                    "role": {"id": 10, "name": "Product Owner"},
                    "project": 123,
                    "is_admin": True,
                },
            )
        )

        # Act
        result = await membership_tools.create_membership(
            auth_token=auth_token, project_id=123, role=10, username="existinguser"
        )

        # Assert
        assert result["id"] == 150
        assert result["user"]["username"] == "existinguser"
        assert result["role"]["name"] == "Product Owner"
        assert result["is_admin"] is True
