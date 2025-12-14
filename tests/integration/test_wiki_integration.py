"""
Tests de integración para las herramientas de Wiki del servidor MCP.
Prueba la integración completa de las funcionalidades de Wiki.
"""

import httpx
import pytest
from fastmcp import FastMCP

from src.application.tools.wiki_tools import WikiTools


class TestWikiIntegration:
    """Tests de integración para Wiki."""

    @pytest.mark.integration
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_complete_wiki_page_lifecycle(self, mock_taiga_api, auth_token) -> None:
        """
        Test completo del ciclo de vida de una página wiki:
        1. Crear página
        2. Listar páginas
        3. Obtener página
        4. Actualizar página
        5. Eliminar página
        """
        # Arrange
        mcp = FastMCP("Test Wiki Integration")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()
        project_id = 123
        page_slug = "test-page"

        # 1. Crear página wiki
        mock_taiga_api.post("https://api.taiga.io/api/v1/wiki").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": 1000,
                    "project": project_id,
                    "slug": page_slug,
                    "content": "# Test Page\nInitial content",
                    "version": 1,
                },
            )
        )

        result_create = await wiki_tools.create_wiki_page(
            auth_token=auth_token,
            project_id=project_id,
            slug=page_slug,
            content="# Test Page\nInitial content",
        )

        assert result_create["id"] == 1000
        assert result_create["slug"] == page_slug

        # 2. Listar páginas wiki (includes pagination params from AutoPaginator)
        mock_taiga_api.get(
            f"https://api.taiga.io/api/v1/wiki?project={project_id}&page=1&page_size=100"
        ).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": 1000,
                        "slug": page_slug,
                        "content": "# Test Page\nInitial content",
                        "version": 1,
                    }
                ],
            )
        )

        result_list = await wiki_tools.list_wiki_pages(auth_token=auth_token, project_id=project_id)

        assert len(result_list) == 1
        assert result_list[0]["id"] == 1000

        # 3. Obtener página por ID
        mock_taiga_api.get("https://api.taiga.io/api/v1/wiki/1000").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 1000,
                    "slug": page_slug,
                    "content": "# Test Page\nInitial content",
                    "version": 1,
                    "html": "<h1>Test Page</h1><p>Initial content</p>",
                },
            )
        )

        result_get = await wiki_tools.get_wiki_page(auth_token=auth_token, wiki_id=1000)

        assert result_get["id"] == 1000
        assert "html" in result_get

        # 4. Actualizar página
        mock_taiga_api.patch("https://api.taiga.io/api/v1/wiki/1000").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 1000,
                    "slug": page_slug,
                    "content": "# Test Page\nUpdated content",
                    "version": 2,
                },
            )
        )

        result_update = await wiki_tools.update_wiki_page(
            auth_token=auth_token, wiki_id=1000, content="# Test Page\nUpdated content", version=1
        )

        assert result_update["version"] == 2
        assert "Updated content" in result_update["content"]

        # 5. Eliminar página
        mock_taiga_api.delete("https://api.taiga.io/api/v1/wiki/1000").mock(
            return_value=httpx.Response(204)
        )

        result_delete = await wiki_tools.delete_wiki_page(auth_token=auth_token, wiki_id=1000)

        assert result_delete is True

    @pytest.mark.integration
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_wiki_attachments_workflow(self, mock_taiga_api, auth_token) -> None:
        """
        Test de flujo completo de adjuntos en wiki:
        1. Crear adjunto
        2. Listar adjuntos
        3. Actualizar adjunto
        4. Eliminar adjunto
        """
        # Arrange
        mcp = FastMCP("Test Wiki Integration")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()
        wiki_id = 1000
        project_id = 123

        # 1. Crear adjunto
        mock_taiga_api.post("https://api.taiga.io/api/v1/wiki/attachments").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": 500,
                    "name": "diagram.png",
                    "size": 50000,
                    "url": "https://media.taiga.io/attachments/diagram.png",
                    "description": "Architecture diagram",
                    "object_id": wiki_id,
                    "project": project_id,
                },
            )
        )

        result_create = await wiki_tools.create_wiki_attachment(
            auth_token=auth_token,
            wiki_page_id=wiki_id,
            project_id=project_id,
            attached_file="path/to/diagram.png",
            description="Architecture diagram",
        )

        assert result_create["id"] == 500
        assert result_create["name"] == "diagram.png"

        # 2. Listar adjuntos (includes pagination params from AutoPaginator)
        mock_taiga_api.get(
            f"https://api.taiga.io/api/v1/wiki/attachments?object_id={wiki_id}&project={project_id}&page=1&page_size=100"
        ).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": 500,
                        "name": "diagram.png",
                        "description": "Architecture diagram",
                        "object_id": wiki_id,
                    }
                ],
            )
        )

        result_list = await wiki_tools.list_wiki_attachments(
            auth_token=auth_token, wiki_page_id=wiki_id, project_id=project_id
        )

        assert len(result_list) == 1
        assert result_list[0]["id"] == 500

        # 3. Actualizar adjunto
        mock_taiga_api.patch("https://api.taiga.io/api/v1/wiki/attachments/500").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 500,
                    "name": "diagram.png",
                    "description": "Updated architecture diagram",
                },
            )
        )

        result_update = await wiki_tools.update_wiki_attachment(
            auth_token=auth_token, attachment_id=500, description="Updated architecture diagram"
        )

        assert result_update["description"] == "Updated architecture diagram"

        # 4. Eliminar adjunto
        mock_taiga_api.delete("https://api.taiga.io/api/v1/wiki/attachments/500").mock(
            return_value=httpx.Response(204)
        )

        result_delete = await wiki_tools.delete_wiki_attachment(
            auth_token=auth_token, attachment_id=500
        )

        assert result_delete is True

    @pytest.mark.integration
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_wiki_restore_deleted_page(self, mock_taiga_api, auth_token) -> None:
        """
        Test de restauración de página wiki eliminada.
        """
        # Arrange
        mcp = FastMCP("Test Wiki Integration")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        # Simular restauración
        mock_taiga_api.post("https://api.taiga.io/api/v1/wiki/1000/restore").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 1000,
                    "slug": "restored-page",
                    "content": "# Restored Page",
                    "version": 3,
                },
            )
        )

        # Act
        result = await wiki_tools.restore_wiki_page(auth_token=auth_token, wiki_id=1000)

        # Assert
        assert result["id"] == 1000
        assert result["slug"] == "restored-page"
        assert result["version"] == 3

    @pytest.mark.integration
    @pytest.mark.wiki
    @pytest.mark.asyncio
    async def test_wiki_get_page_by_slug(self, mock_taiga_api, auth_token) -> None:
        """
        Test de obtención de página wiki por slug.
        """
        # Arrange
        mcp = FastMCP("Test Wiki Integration")
        wiki_tools = WikiTools(mcp)
        wiki_tools.register_tools()

        mock_taiga_api.get("https://api.taiga.io/api/v1/wiki/by_slug?slug=home&project=123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 1,
                    "project": 123,
                    "slug": "home",
                    "content": "# Home\nWelcome page",
                    "version": 1,
                },
            )
        )

        # Act
        result = await wiki_tools.get_wiki_page_by_slug(
            auth_token=auth_token, slug="home", project_id=123
        )

        # Assert
        assert result["id"] == 1
        assert result["slug"] == "home"
        assert "Welcome page" in result["content"]
