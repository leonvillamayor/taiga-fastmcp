"""
Tests unitarios para las herramientas de Membresías del servidor MCP.
Cubre las funcionalidades MEMB-001 a MEMB-005 según Documentacion/taiga.md.
"""

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.application.tools.membership_tools import MembershipTools


class TestListMembershipsTool:
    """Tests para la herramienta list_memberships - MEMB-001."""

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_list_memberships_tool_is_registered(self) -> None:
        """
        MEMB-001: Listar membresías del proyecto.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)

        # Act
        membership_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_list_memberships" in tool_names

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_list_memberships_by_project(self, mock_taiga_api) -> None:
        """
        Verifica que lista membresías por proyecto correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()

        mock_taiga_api.get(
            "https://api.taiga.io/api/v1/memberships?project=123&page=1&page_size=100"
        ).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "user": {
                            "id": 100,
                            "username": "john_doe",
                            "full_name": "John Doe",
                            "email": "john@example.com",
                        },
                        "role": {
                            "id": 10,
                            "name": "Product Owner",
                            "slug": "product-owner",
                            "permissions": ["view_project", "edit_project", "delete_project"],
                        },
                        "project": 123,
                        "created_at": "2025-01-01T10:00:00Z",
                        "is_admin": True,
                    },
                    {
                        "id": 2,
                        "user": {
                            "id": 101,
                            "username": "jane_smith",
                            "full_name": "Jane Smith",
                            "email": "jane@example.com",
                        },
                        "role": {
                            "id": 11,
                            "name": "Developer",
                            "slug": "developer",
                            "permissions": ["view_project", "edit_tasks"],
                        },
                        "project": 123,
                        "created_at": "2025-01-02T10:00:00Z",
                        "is_admin": False,
                    },
                ],
            )
        )

        # Act
        result = await membership_tools.list_memberships(auth_token="valid_token", project_id=123)

        # Assert
        assert len(result) == 2
        assert result[0]["user"]["username"] == "john_doe"
        assert result[0]["role"]["name"] == "Product Owner"
        assert result[0]["is_admin"] is True
        assert result[1]["user"]["username"] == "jane_smith"
        assert result[1]["role"]["name"] == "Developer"
        assert result[1]["is_admin"] is False

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_list_memberships_empty_project(self, mock_taiga_api) -> None:
        """
        Verifica manejo de proyecto sin membresías.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()

        mock_taiga_api.get(
            "https://api.taiga.io/api/v1/memberships?project=456&page=1&page_size=100"
        ).mock(return_value=httpx.Response(200, json=[]))

        # Act
        result = await membership_tools.list_memberships(auth_token="valid_token", project_id=456)

        # Assert
        assert result == []


class TestCreateMembershipTool:
    """Tests para la herramienta create_membership - MEMB-002."""

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_create_membership_tool_is_registered(self) -> None:
        """
        MEMB-002: Crear membresía.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)

        # Act
        membership_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_create_membership" in tool_names

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_create_membership_with_email(self, mock_taiga_api) -> None:
        """
        Verifica que crea membresía con email correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/memberships").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": 10,
                    "user": {
                        "id": 200,
                        "username": "new_user",
                        "full_name": "New User",
                        "email": "newuser@example.com",
                    },
                    "role": {"id": 11, "name": "Developer", "slug": "developer"},
                    "project": 123,
                    "created_at": "2025-01-20T10:00:00Z",
                    "is_admin": False,
                },
            )
        )

        # Act
        result = await membership_tools.create_membership(
            auth_token="valid_token", project_id=123, role=11, email="newuser@example.com"
        )

        # Assert
        assert result["id"] == 10
        assert result["user"]["email"] == "newuser@example.com"
        assert result["role"]["name"] == "Developer"
        assert result["is_admin"] is False

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_create_membership_with_username(self, mock_taiga_api) -> None:
        """
        Verifica que crea membresía con username correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/memberships").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": 11,
                    "user": {"id": 201, "username": "existing_user", "full_name": "Existing User"},
                    "role": {"id": 10, "name": "Product Owner"},
                    "project": 123,
                    "is_admin": True,
                },
            )
        )

        # Act
        result = await membership_tools.create_membership(
            auth_token="valid_token", project_id=123, role=10, username="existing_user"
        )

        # Assert
        assert result["user"]["username"] == "existing_user"
        assert result["role"]["name"] == "Product Owner"
        assert result["is_admin"] is True

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_create_membership_duplicate_user(self, mock_taiga_api) -> None:
        """
        Verifica manejo de usuario duplicado en proyecto.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/memberships").mock(
            return_value=httpx.Response(
                400, json={"non_field_errors": ["User is already a member of this project"]}
            )
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Failed to create membership"):
            await membership_tools.create_membership(
                auth_token="valid_token", project_id=123, role=11, email="existing@example.com"
            )


class TestGetMembershipTool:
    """Tests para la herramienta get_membership - MEMB-003."""

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_get_membership_tool_is_registered(self) -> None:
        """
        MEMB-003: Obtener membresía.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)

        # Act
        membership_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_get_membership" in tool_names

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_get_membership_by_id(self, mock_taiga_api) -> None:
        """
        Verifica que obtiene membresía por ID correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/memberships/10").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 10,
                    "user": {
                        "id": 100,
                        "username": "john_doe",
                        "full_name": "John Doe",
                        "email": "john@example.com",
                        "photo": "https://example.com/photo.jpg",
                    },
                    "role": {
                        "id": 10,
                        "name": "Product Owner",
                        "slug": "product-owner",
                        "permissions": ["all"],
                    },
                    "project": {"id": 123, "name": "My Project", "slug": "my-project"},
                    "created_at": "2025-01-01T10:00:00Z",
                    "is_admin": True,
                    "is_owner": False,
                },
            )
        )

        # Act
        result = await membership_tools.get_membership(auth_token="valid_token", membership_id=10)

        # Assert
        assert result["id"] == 10
        assert result["user"]["username"] == "john_doe"
        assert result["role"]["name"] == "Product Owner"
        assert result["project"]["id"] == 123
        assert result["is_admin"] is True

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_get_membership_not_found(self, mock_taiga_api) -> None:
        """
        Verifica manejo de membresía no encontrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/memberships/999").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Membership not found"):
            await membership_tools.get_membership(auth_token="valid_token", membership_id=999)


class TestUpdateMembershipTool:
    """Tests para la herramienta update_membership - MEMB-004."""

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_update_membership_tool_is_registered(self) -> None:
        """
        MEMB-004: Actualizar rol de membresía.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)

        # Act
        membership_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_update_membership" in tool_names

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_update_membership_role(self, mock_taiga_api) -> None:
        """
        Verifica que actualiza rol de membresía correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()

        mock_taiga_api.patch("https://api.taiga.io/api/v1/memberships/10").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 10,
                    "user": {"id": 100, "username": "john_doe"},
                    "role": {"id": 12, "name": "Scrum Master", "slug": "scrum-master"},
                    "project": 123,
                    "is_admin": True,
                },
            )
        )

        # Act
        result = await membership_tools.update_membership(
            auth_token="valid_token", membership_id=10, role=12
        )

        # Assert
        assert result["role"]["id"] == 12
        assert result["role"]["name"] == "Scrum Master"

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_update_membership_admin_status(self, mock_taiga_api) -> None:
        """
        Verifica que actualiza estado de admin correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()

        mock_taiga_api.patch("https://api.taiga.io/api/v1/memberships/10").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 10,
                    "user": {"id": 100, "username": "john_doe"},
                    "role": {"id": 11, "name": "Developer"},
                    "is_admin": False,
                },
            )
        )

        # Act
        result = await membership_tools.update_membership(
            auth_token="valid_token", membership_id=10, is_admin=False
        )

        # Assert
        assert result["is_admin"] is False

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_update_membership_permission_denied(self, mock_taiga_api) -> None:
        """
        Verifica manejo de permisos insuficientes.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()

        mock_taiga_api.patch("https://api.taiga.io/api/v1/memberships/10").mock(
            return_value=httpx.Response(
                403, json={"detail": "You do not have permission to update memberships"}
            )
        )

        # Act & Assert
        with pytest.raises(ToolError, match="permission"):
            await membership_tools.update_membership(
                auth_token="valid_token", membership_id=10, role=12
            )


class TestDeleteMembershipTool:
    """Tests para la herramienta delete_membership - MEMB-005."""

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_delete_membership_tool_is_registered(self) -> None:
        """
        MEMB-005: Eliminar membresía.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)

        # Act
        membership_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_delete_membership" in tool_names

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_delete_membership_success(self, mock_taiga_api) -> None:
        """
        Verifica que elimina membresía correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()

        mock_taiga_api.delete("https://api.taiga.io/api/v1/memberships/10").mock(
            return_value=httpx.Response(204)
        )

        # Act
        result = await membership_tools.delete_membership(
            auth_token="valid_token", membership_id=10
        )

        # Assert
        assert result is True

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_delete_membership_not_found(self, mock_taiga_api) -> None:
        """
        Verifica manejo de membresía no encontrada al eliminar.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()

        mock_taiga_api.delete("https://api.taiga.io/api/v1/memberships/999").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Membership not found"):
            await membership_tools.delete_membership(auth_token="valid_token", membership_id=999)

    @pytest.mark.unit
    @pytest.mark.memberships
    @pytest.mark.asyncio
    async def test_delete_membership_owner_error(self, mock_taiga_api) -> None:
        """
        Verifica manejo de intento de eliminar al owner del proyecto.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()

        mock_taiga_api.delete("https://api.taiga.io/api/v1/memberships/1").mock(
            return_value=httpx.Response(400, json={"error": "Cannot remove project owner"})
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Cannot remove"):
            await membership_tools.delete_membership(auth_token="valid_token", membership_id=1)


class TestMembershipToolsBestPractices:
    """Tests para verificar buenas prácticas en herramientas de Membresías."""

    @pytest.mark.unit
    @pytest.mark.memberships
    def test_membership_tools_use_async_await(self) -> None:
        """
        RNF-001: Usar async/await para operaciones I/O.
        Verifica que las herramientas de membresías son asíncronas.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()

        # Act
        import inspect

        # Assert
        assert inspect.iscoroutinefunction(membership_tools.list_memberships)
        assert inspect.iscoroutinefunction(membership_tools.create_membership)
        assert inspect.iscoroutinefunction(membership_tools.get_membership)
        assert inspect.iscoroutinefunction(membership_tools.update_membership)
        assert inspect.iscoroutinefunction(membership_tools.delete_membership)

    @pytest.mark.unit
    @pytest.mark.memberships
    def test_membership_tools_have_docstrings(self) -> None:
        """
        RNF-006: El código DEBE tener docstrings descriptivos.
        Verifica que las herramientas tienen documentación.
        """
        # Arrange
        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)
        membership_tools.register_tools()

        # Act & Assert
        assert membership_tools.list_memberships.__doc__ is not None
        assert "membership" in membership_tools.list_memberships.__doc__.lower()

        assert membership_tools.create_membership.__doc__ is not None
        assert "create" in membership_tools.create_membership.__doc__.lower()

        assert membership_tools.get_membership.__doc__ is not None
        assert membership_tools.update_membership.__doc__ is not None
        assert membership_tools.delete_membership.__doc__ is not None

    @pytest.mark.unit
    @pytest.mark.memberships
    def test_all_membership_tools_are_registered(self) -> None:
        """
        RF-030: TODAS las funcionalidades de Taiga DEBEN estar expuestas.
        Verifica que todas las herramientas de membresías están registradas.
        """
        # Arrange
        import asyncio

        mcp = FastMCP("Test")
        membership_tools = MembershipTools(mcp)

        # Act
        membership_tools.register_tools()
        tools = asyncio.run(mcp.get_tools())
        tool_names = list(tools.keys())

        # Assert - Todas las herramientas de membresías necesarias
        expected_tools = [
            "taiga_list_memberships",  # MEMB-001
            "taiga_create_membership",  # MEMB-002
            "taiga_get_membership",  # MEMB-003
            "taiga_update_membership",  # MEMB-004
            "taiga_delete_membership",  # MEMB-005
        ]

        for tool in expected_tools:
            assert tool in tool_names, f"Tool {tool} not registered"
