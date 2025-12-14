"""
Tests unitarios para las herramientas de Wiki del servidor MCP.
Cubre las funcionalidades WIKI-001 a WIKI-010 según Documentacion/taiga.md.
"""

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.application.tools.wiki_tools import WikiTools


class TestListWikiPagesTool:
    """Tests para la herramienta list_wiki_pages - WIKI-001."""

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_list_wiki_pages_tool_is_registered(self) -> None:
        """
        WIKI-001: Listar páginas wiki del proyecto.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)

        # Act
        wiki_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_list_wiki_pages" in tool_names

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_list_wiki_pages_success(self, mock_taiga_api) -> None:
        """
        Verifica que list_wiki_pages retorna páginas correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.get(
            "https://api.taiga.io/api/v1/wiki?project=123&page=1&page_size=100"
        ).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "slug": "home",
                        "content": "# Home Page\nWelcome to the wiki",
                        "version": 1,
                        "created_date": "2025-01-01T10:00:00Z",
                        "modified_date": "2025-01-15T14:00:00Z",
                        "owner": {"id": 1, "username": "user1"},
                    },
                    {
                        "id": 2,
                        "slug": "documentation",
                        "content": "# Documentation\nAPI docs",
                        "version": 2,
                        "created_date": "2025-01-02T10:00:00Z",
                        "modified_date": "2025-01-16T14:00:00Z",
                        "owner": {"id": 1, "username": "user1"},
                    },
                ],
            )
        )

        # Act
        result = await wiki_tools.list_wiki_pages(auth_token="valid_token", project_id=123)

        # Assert
        assert len(result) == 2
        assert result[0]["slug"] == "home"
        assert result[1]["slug"] == "documentation"
        assert "# Home Page" in result[0]["content"]

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_list_wiki_pages_empty_project(self, mock_taiga_api) -> None:
        """
        Verifica manejo de proyecto sin páginas wiki.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.get(
            "https://api.taiga.io/api/v1/wiki?project=456&page=1&page_size=100"
        ).mock(return_value=httpx.Response(200, json=[]))

        # Act
        result = await wiki_tools.list_wiki_pages(auth_token="valid_token", project_id=456)

        # Assert
        assert result == []


class TestCreateWikiPageTool:
    """Tests para la herramienta create_wiki_page - WIKI-002."""

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_create_wiki_page_tool_is_registered(self) -> None:
        """
        WIKI-002: Crear página wiki.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)

        # Act
        wiki_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_create_wiki_page" in tool_names

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_create_wiki_page_success(self, mock_taiga_api) -> None:
        """
        Verifica que create_wiki_page crea página correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/wiki").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": 10,
                    "project": 123,
                    "slug": "new-page",
                    "content": "# New Page\nContent here",
                    "version": 1,
                    "created_date": "2025-01-20T10:00:00Z",
                    "owner": {"id": 1, "username": "user1"},
                },
            )
        )

        # Act
        result = await wiki_tools.create_wiki_page(
            auth_token="valid_token",
            project_id=123,
            slug="new-page",
            content="# New Page\nContent here",
        )

        # Assert
        assert result["id"] == 10
        assert result["slug"] == "new-page"
        assert result["content"] == "# New Page\nContent here"
        assert result["version"] == 1

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_create_wiki_page_duplicate_slug(self, mock_taiga_api) -> None:
        """
        Verifica manejo de slug duplicado al crear página.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/wiki").mock(
            return_value=httpx.Response(
                400, json={"slug": ["A wiki page with this slug already exists"]}
            )
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Failed to create wiki page"):
            await wiki_tools.create_wiki_page(
                auth_token="valid_token", project_id=123, slug="existing-page", content="Content"
            )


class TestGetWikiPageTool:
    """Tests para la herramienta get_wiki_page - WIKI-003."""

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_get_wiki_page_tool_is_registered(self) -> None:
        """
        WIKI-003: Obtener página wiki por ID.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)

        # Act
        wiki_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_get_wiki_page" in tool_names

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_get_wiki_page_by_id(self, mock_taiga_api) -> None:
        """
        Verifica que obtiene página wiki por ID correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/wiki/10").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 10,
                    "project": 123,
                    "slug": "architecture",
                    "content": "# Architecture\nSystem design docs",
                    "version": 3,
                    "html": "<h1>Architecture</h1><p>System design docs</p>",
                    "editions": 5,
                    "last_modifier": {"id": 2, "username": "user2"},
                    "created_date": "2025-01-01T10:00:00Z",
                    "modified_date": "2025-01-20T16:00:00Z",
                },
            )
        )

        # Act
        result = await wiki_tools.get_wiki_page(auth_token="valid_token", wiki_id=10)

        # Assert
        assert result["id"] == 10
        assert result["slug"] == "architecture"
        assert "# Architecture" in result["content"]
        assert result["version"] == 3
        assert result["editions"] == 5

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_get_wiki_page_not_found(self, mock_taiga_api) -> None:
        """
        Verifica manejo de página no encontrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/wiki/999").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Wiki page not found"):
            await wiki_tools.get_wiki_page(auth_token="valid_token", wiki_id=999)


class TestGetWikiPageBySlugTool:
    """Tests para la herramienta get_wiki_page_by_slug - WIKI-004."""

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_get_wiki_page_by_slug_tool_is_registered(self) -> None:
        """
        WIKI-004: Obtener página wiki por slug.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)

        # Act
        wiki_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_get_wiki_page_by_slug" in tool_names

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_get_wiki_page_by_slug_success(self, mock_taiga_api) -> None:
        """
        Verifica que obtiene página wiki por slug correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/wiki/by_slug?slug=home&project=123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 1,
                    "project": 123,
                    "slug": "home",
                    "content": "# Home\nMain page",
                    "version": 1,
                },
            )
        )

        # Act
        result = await wiki_tools.get_wiki_page_by_slug(
            auth_token="valid_token", slug="home", project_id=123
        )

        # Assert
        assert result["id"] == 1
        assert result["slug"] == "home"
        assert result["content"] == "# Home\nMain page"


class TestUpdateWikiPageTool:
    """Tests para la herramienta update_wiki_page - WIKI-005."""

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_update_wiki_page_tool_is_registered(self) -> None:
        """
        WIKI-005: Actualizar página wiki.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)

        # Act
        wiki_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_update_wiki_page" in tool_names

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_update_wiki_page_content(self, mock_taiga_api) -> None:
        """
        Verifica que actualiza contenido de página wiki.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.patch("https://api.taiga.io/api/v1/wiki/10").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 10,
                    "slug": "architecture",
                    "content": "# Architecture Updated\nNew content",
                    "version": 4,
                },
            )
        )

        # Act
        result = await wiki_tools.update_wiki_page(
            auth_token="valid_token",
            wiki_id=10,
            content="# Architecture Updated\nNew content",
            version=3,
        )

        # Assert
        assert result["content"] == "# Architecture Updated\nNew content"
        assert result["version"] == 4

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_update_wiki_page_version_conflict(self, mock_taiga_api) -> None:
        """
        Verifica manejo de conflicto de versiones.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.patch("https://api.taiga.io/api/v1/wiki/10").mock(
            return_value=httpx.Response(400, json={"version": ["Version conflict"]})
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Failed to update wiki page"):
            await wiki_tools.update_wiki_page(
                auth_token="valid_token", wiki_id=10, content="Updated content", version=1
            )


class TestDeleteWikiPageTool:
    """Tests para la herramienta delete_wiki_page - WIKI-006."""

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_delete_wiki_page_tool_is_registered(self) -> None:
        """
        WIKI-006: Eliminar página wiki.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)

        # Act
        wiki_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_delete_wiki_page" in tool_names

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_delete_wiki_page_success(self, mock_taiga_api) -> None:
        """
        Verifica que elimina página wiki correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.delete("https://api.taiga.io/api/v1/wiki/10").mock(
            return_value=httpx.Response(204)
        )

        # Act
        result = await wiki_tools.delete_wiki_page(auth_token="valid_token", wiki_id=10)

        # Assert
        assert result is True

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_delete_wiki_page_not_found(self, mock_taiga_api) -> None:
        """
        Verifica manejo de página no encontrada al eliminar.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.delete("https://api.taiga.io/api/v1/wiki/999").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )

        # Act & Assert
        with pytest.raises(ToolError, match="Wiki page not found"):
            await wiki_tools.delete_wiki_page(auth_token="valid_token", wiki_id=999)


class TestRestoreWikiPageTool:
    """Tests para la herramienta restore_wiki_page - WIKI-007."""

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_restore_wiki_page_tool_is_registered(self) -> None:
        """
        WIKI-007: Restaurar página wiki eliminada.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)

        # Act
        wiki_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_restore_wiki_page" in tool_names

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_restore_wiki_page_success(self, mock_taiga_api) -> None:
        """
        Verifica que restaura página wiki eliminada.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/wiki/10/restore").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 10,
                    "slug": "restored-page",
                    "content": "# Restored Page",
                    "version": 5,
                },
            )
        )

        # Act
        result = await wiki_tools.restore_wiki_page(auth_token="valid_token", wiki_id=10)

        # Assert
        assert result["id"] == 10
        assert result["slug"] == "restored-page"


class TestWikiAttachmentTools:
    """Tests para herramientas de adjuntos wiki - WIKI-008 a WIKI-010."""

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_list_wiki_attachments_tool_is_registered(self) -> None:
        """
        WIKI-008: Ver adjuntos de wiki.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)

        # Act
        wiki_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_list_wiki_attachments" in tool_names

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_list_wiki_attachments(self, mock_taiga_api) -> None:
        """
        Verifica que lista adjuntos de página wiki.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.get(
            "https://api.taiga.io/api/v1/wiki/attachments?object_id=10&project=123&page=1&page_size=100"
        ).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": 100,
                        "name": "diagram.png",
                        "size": 50000,
                        "url": "https://media.taiga.io/attachments/diagram.png",
                        "description": "Architecture diagram",
                        "created_date": "2025-01-15T10:00:00Z",
                        "object_id": 10,
                        "project": 123,
                        "owner": {"id": 1, "username": "user1"},
                    },
                    {
                        "id": 101,
                        "name": "spec.pdf",
                        "size": 150000,
                        "url": "https://media.taiga.io/attachments/spec.pdf",
                        "description": "Technical specification",
                        "created_date": "2025-01-16T10:00:00Z",
                        "object_id": 10,
                        "project": 123,
                        "owner": {"id": 2, "username": "user2"},
                    },
                ],
            )
        )

        # Act
        result = await wiki_tools.list_wiki_attachments(
            auth_token="valid_token", wiki_page_id=10, project_id=123
        )

        # Assert
        assert len(result) == 2
        assert result[0]["name"] == "diagram.png"
        assert result[1]["name"] == "spec.pdf"

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_create_wiki_attachment_tool_is_registered(self) -> None:
        """
        WIKI-009: Crear adjunto de wiki.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)

        # Act
        wiki_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_create_wiki_attachment" in tool_names

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_create_wiki_attachment(self, mock_taiga_api) -> None:
        """
        Verifica que crea adjunto de wiki correctamente.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.post("https://api.taiga.io/api/v1/wiki/attachments").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": 102,
                    "name": "new-file.txt",
                    "size": 1000,
                    "url": "https://media.taiga.io/attachments/new-file.txt",
                    "description": "New attachment",
                    "object_id": 10,
                    "project": 123,
                },
            )
        )

        # Act
        result = await wiki_tools.create_wiki_attachment(
            auth_token="valid_token",
            wiki_page_id=10,
            project_id=123,
            attached_file="path/to/file.txt",
            description="New attachment",
        )

        # Assert
        assert result["id"] == 102
        assert result["name"] == "new-file.txt"
        assert result["description"] == "New attachment"

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_update_wiki_attachment_tool_is_registered(self) -> None:
        """
        WIKI-010: Modificar adjunto de wiki.
        Verifica que la herramienta está registrada.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)

        # Act
        wiki_tools.register_tools()
        tools = await mcp.get_tools()

        # Assert
        tool_names = list(tools.keys())
        assert "taiga_update_wiki_attachment" in tool_names

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_update_wiki_attachment(self, mock_taiga_api) -> None:
        """
        Verifica que actualiza adjunto de wiki.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.patch("https://api.taiga.io/api/v1/wiki/attachments/100").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 100,
                    "name": "diagram.png",
                    "description": "Updated description",
                    "object_id": 10,
                },
            )
        )

        # Act
        result = await wiki_tools.update_wiki_attachment(
            auth_token="valid_token", attachment_id=100, description="Updated description"
        )

        # Assert
        assert result["description"] == "Updated description"

    @pytest.mark.unit
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_delete_wiki_attachment(self, mock_taiga_api) -> None:
        """
        Verifica que elimina adjunto de wiki.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.delete("https://api.taiga.io/api/v1/wiki/attachments/100").mock(
            return_value=httpx.Response(204)
        )

        # Act
        result = await wiki_tools.delete_wiki_attachment(
            auth_token="valid_token", attachment_id=100
        )

        # Assert
        assert result is True


class TestWikiToolsBestPractices:
    """Tests para verificar buenas prácticas en herramientas de Wiki."""

    @pytest.mark.unit
    @pytest.mark.wiki
    def test_wiki_tools_use_async_await(self) -> None:
        """
        RNF-001: Usar async/await para operaciones I/O.
        Verifica que las herramientas de wiki son asíncronas.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        # Act
        import inspect

        # Assert
        assert inspect.iscoroutinefunction(wiki_tools.list_wiki_pages)
        assert inspect.iscoroutinefunction(wiki_tools.create_wiki_page)
        assert inspect.iscoroutinefunction(wiki_tools.get_wiki_page)
        assert inspect.iscoroutinefunction(wiki_tools.update_wiki_page)
        assert inspect.iscoroutinefunction(wiki_tools.delete_wiki_page)

    @pytest.mark.unit
    @pytest.mark.wiki
    def test_wiki_tools_have_docstrings(self) -> None:
        """
        RNF-006: El código DEBE tener docstrings descriptivos.
        Verifica que las herramientas tienen documentación.
        """
        # Arrange
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        # Act & Assert
        assert wiki_tools.list_wiki_pages.__doc__ is not None
        assert "wiki" in wiki_tools.list_wiki_pages.__doc__.lower()

        assert wiki_tools.create_wiki_page.__doc__ is not None
        assert "create" in wiki_tools.create_wiki_page.__doc__.lower()

        assert wiki_tools.get_wiki_page.__doc__ is not None
        assert wiki_tools.update_wiki_page.__doc__ is not None
        assert wiki_tools.delete_wiki_page.__doc__ is not None

    @pytest.mark.unit
    @pytest.mark.wiki
    def test_all_wiki_tools_are_registered(self) -> None:
        """
        RF-030: TODAS las funcionalidades de Taiga DEBEN estar expuestas.
        Verifica que todas las herramientas de wiki están registradas.
        """
        # Arrange
        import asyncio

        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)

        # Act
        wiki_tools.register_tools()
        tools = asyncio.run(mcp.get_tools())
        tool_names = list(tools.keys())

        # Assert - Todas las herramientas de wiki necesarias
        expected_tools = [
            "taiga_list_wiki_pages",  # WIKI-001
            "taiga_create_wiki_page",  # WIKI-002
            "taiga_get_wiki_page",  # WIKI-003
            "taiga_get_wiki_page_by_slug",  # WIKI-004
            "taiga_update_wiki_page",  # WIKI-005
            "taiga_delete_wiki_page",  # WIKI-006
            "taiga_restore_wiki_page",  # WIKI-007
            "taiga_list_wiki_attachments",  # WIKI-008
            "taiga_create_wiki_attachment",  # WIKI-009
            "taiga_update_wiki_attachment",  # WIKI-010
            "taiga_delete_wiki_attachment",
        ]

        for tool in expected_tools:
            assert tool in tool_names, f"Tool {tool} not registered"
