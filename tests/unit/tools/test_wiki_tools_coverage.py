"""
Tests adicionales para cobertura de wiki_tools.py.
Objetivo: alcanzar 90% de cobertura.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.application.tools.wiki_tools import WikiTools
from src.domain.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    ResourceNotFoundError,
    TaigaAPIError,
    ValidationError,
)


@pytest.fixture
def wiki_tools_instance():
    """Crea una instancia de WikiTools con mocks."""
    mcp = FastMCP("Test")
    with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client
        tools = WikiTools(mcp)
        tools.register_tools()
        tools._mock_client = mock_client
        tools._mock_client_cls = mock_client_cls
        yield tools


class TestSetClient:
    """Tests para set_client method (line 54)."""

    def test_set_client(self):
        """Test set_client inyecta el cliente correctamente."""
        mcp = FastMCP("Test")
        wiki_tools = WikiTools(mcp)
        mock_client = MagicMock()

        wiki_tools.set_client(mock_client)

        assert wiki_tools.client == mock_client


class TestListWikiPagesExceptionHandlers:
    """Tests para exception handlers de list_wiki_pages."""

    @pytest.mark.asyncio
    async def test_list_wiki_pages_auto_paginate_false(self, wiki_tools_instance):
        """Test list_wiki_pages con auto_paginate=False (line 112)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            with patch("src.application.tools.wiki_tools.AutoPaginator") as mock_paginator_cls:
                mock_paginator = MagicMock()
                mock_paginator.paginate_first_page = AsyncMock(return_value=[
                    {"id": 1, "slug": "home", "project": 123, "content": "Content"}
                ])
                mock_paginator_cls.return_value = mock_paginator

                result = await wiki_tools_instance.list_wiki_pages(
                    auth_token="token", project_id=123, auto_paginate=False
                )

                assert len(result) == 1
                mock_paginator.paginate_first_page.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_wiki_pages_authentication_error(self, wiki_tools_instance):
        """Test list_wiki_pages con AuthenticationError (lines 138-142)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            with patch("src.application.tools.wiki_tools.AutoPaginator") as mock_paginator_cls:
                mock_paginator = MagicMock()
                mock_paginator.paginate = AsyncMock(side_effect=AuthenticationError("Auth failed"))
                mock_paginator_cls.return_value = mock_paginator

                with pytest.raises(ToolError, match="Authentication failed"):
                    await wiki_tools_instance.list_wiki_pages(auth_token="token", project_id=123)

    @pytest.mark.asyncio
    async def test_list_wiki_pages_taiga_api_error(self, wiki_tools_instance):
        """Test list_wiki_pages con TaigaAPIError (lines 143-147)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            with patch("src.application.tools.wiki_tools.AutoPaginator") as mock_paginator_cls:
                mock_paginator = MagicMock()
                mock_paginator.paginate = AsyncMock(side_effect=TaigaAPIError("API error"))
                mock_paginator_cls.return_value = mock_paginator

                with pytest.raises(ToolError, match="API error"):
                    await wiki_tools_instance.list_wiki_pages(auth_token="token", project_id=123)

    @pytest.mark.asyncio
    async def test_list_wiki_pages_unexpected_error(self, wiki_tools_instance):
        """Test list_wiki_pages con Exception genérica (lines 148-152)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            with patch("src.application.tools.wiki_tools.AutoPaginator") as mock_paginator_cls:
                mock_paginator = MagicMock()
                mock_paginator.paginate = AsyncMock(side_effect=RuntimeError("Unexpected"))
                mock_paginator_cls.return_value = mock_paginator

                with pytest.raises(ToolError, match="Unexpected error"):
                    await wiki_tools_instance.list_wiki_pages(auth_token="token", project_id=123)


class TestCreateWikiPageExceptionHandlers:
    """Tests para exception handlers de create_wiki_page."""

    @pytest.mark.asyncio
    async def test_create_wiki_page_with_watchers(self, wiki_tools_instance):
        """Test create_wiki_page con watchers (line 224)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value={
                "id": 1, "slug": "test", "project": 123, "content": "Content", "version": 1
            })
            mock_cls.return_value = mock_client

            result = await wiki_tools_instance.create_wiki_page(
                auth_token="token",
                project_id=123,
                slug="test",
                content="Content",
                watchers=[1, 2, 3]
            )

            assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_create_wiki_page_validation_error(self, wiki_tools_instance):
        """Test create_wiki_page con ValidationError (lines 244-248)."""
        with patch("src.application.tools.wiki_tools.validate_input") as mock_validate:
            mock_validate.side_effect = ValidationError("Invalid data")

            with pytest.raises(ToolError, match="Invalid data"):
                await wiki_tools_instance.create_wiki_page(
                    auth_token="token", project_id=123, slug="test", content="Content"
                )

    @pytest.mark.asyncio
    async def test_create_wiki_page_authentication_error(self, wiki_tools_instance):
        """Test create_wiki_page con AuthenticationError (lines 249-253)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=AuthenticationError("Auth failed"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Authentication failed"):
                await wiki_tools_instance.create_wiki_page(
                    auth_token="token", project_id=123, slug="test", content="Content"
                )

    @pytest.mark.asyncio
    async def test_create_wiki_page_slug_already_exists(self, wiki_tools_instance):
        """Test create_wiki_page con slug duplicado (lines 254-259)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=TaigaAPIError("Slug already exists"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="already exists"):
                await wiki_tools_instance.create_wiki_page(
                    auth_token="token", project_id=123, slug="test", content="Content"
                )

    @pytest.mark.asyncio
    async def test_create_wiki_page_taiga_api_error(self, wiki_tools_instance):
        """Test create_wiki_page con TaigaAPIError genérico (lines 260-263)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=TaigaAPIError("Server error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Failed to create wiki page"):
                await wiki_tools_instance.create_wiki_page(
                    auth_token="token", project_id=123, slug="test", content="Content"
                )

    @pytest.mark.asyncio
    async def test_create_wiki_page_unexpected_error(self, wiki_tools_instance):
        """Test create_wiki_page con Exception genérica (lines 264-268)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=RuntimeError("Unexpected"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Unexpected error"):
                await wiki_tools_instance.create_wiki_page(
                    auth_token="token", project_id=123, slug="test", content="Content"
                )


class TestGetWikiPageExceptionHandlers:
    """Tests para exception handlers de get_wiki_page."""

    @pytest.mark.asyncio
    async def test_get_wiki_page_authentication_error(self, wiki_tools_instance):
        """Test get_wiki_page con AuthenticationError (lines 351-353)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=AuthenticationError("Auth failed"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Authentication failed"):
                await wiki_tools_instance.get_wiki_page(auth_token="token", wiki_id=1)

    @pytest.mark.asyncio
    async def test_get_wiki_page_taiga_api_error(self, wiki_tools_instance):
        """Test get_wiki_page con TaigaAPIError (lines 354-356)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=TaigaAPIError("API error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="API error"):
                await wiki_tools_instance.get_wiki_page(auth_token="token", wiki_id=1)

    @pytest.mark.asyncio
    async def test_get_wiki_page_unexpected_error(self, wiki_tools_instance):
        """Test get_wiki_page con Exception genérica (lines 357-361)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=RuntimeError("Unexpected"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Unexpected error"):
                await wiki_tools_instance.get_wiki_page(auth_token="token", wiki_id=1)


class TestGetWikiPageBySlugExceptionHandlers:
    """Tests para exception handlers de get_wiki_page_by_slug."""

    @pytest.mark.asyncio
    async def test_get_wiki_page_by_slug_not_found(self, wiki_tools_instance):
        """Test get_wiki_page_by_slug con ResourceNotFoundError (lines 439-443)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="not found"):
                await wiki_tools_instance.get_wiki_page_by_slug(
                    auth_token="token", slug="missing", project_id=123
                )

    @pytest.mark.asyncio
    async def test_get_wiki_page_by_slug_authentication_error(self, wiki_tools_instance):
        """Test get_wiki_page_by_slug con AuthenticationError (lines 444-448)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=AuthenticationError("Auth failed"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Authentication failed"):
                await wiki_tools_instance.get_wiki_page_by_slug(
                    auth_token="token", slug="test", project_id=123
                )

    @pytest.mark.asyncio
    async def test_get_wiki_page_by_slug_taiga_api_error(self, wiki_tools_instance):
        """Test get_wiki_page_by_slug con TaigaAPIError (lines 449-453)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=TaigaAPIError("API error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="API error"):
                await wiki_tools_instance.get_wiki_page_by_slug(
                    auth_token="token", slug="test", project_id=123
                )

    @pytest.mark.asyncio
    async def test_get_wiki_page_by_slug_unexpected_error(self, wiki_tools_instance):
        """Test get_wiki_page_by_slug con Exception genérica (lines 454-458)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=RuntimeError("Unexpected"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Unexpected error"):
                await wiki_tools_instance.get_wiki_page_by_slug(
                    auth_token="token", slug="test", project_id=123
                )


class TestUpdateWikiPageBranches:
    """Tests para branches y exception handlers de update_wiki_page."""

    @pytest.mark.asyncio
    async def test_update_wiki_page_with_slug(self, wiki_tools_instance):
        """Test update_wiki_page con solo slug (line 526)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(return_value={
                "id": 1, "slug": "new-slug", "project": 123, "version": 2
            })
            mock_cls.return_value = mock_client

            result = await wiki_tools_instance.update_wiki_page(
                auth_token="token", wiki_id=1, slug="new-slug"
            )

            assert result["slug"] == "new-slug"

    @pytest.mark.asyncio
    async def test_update_wiki_page_validation_error(self, wiki_tools_instance):
        """Test update_wiki_page con ValidationError (lines 550-554)."""
        with patch("src.application.tools.wiki_tools.validate_input") as mock_validate:
            mock_validate.side_effect = ValidationError("Invalid data")

            with pytest.raises(ToolError, match="Invalid data"):
                await wiki_tools_instance.update_wiki_page(
                    auth_token="token", wiki_id=1, content="New content"
                )

    @pytest.mark.asyncio
    async def test_update_wiki_page_not_found(self, wiki_tools_instance):
        """Test update_wiki_page con ResourceNotFoundError (lines 555-557)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="not found"):
                await wiki_tools_instance.update_wiki_page(
                    auth_token="token", wiki_id=999, content="Content"
                )

    @pytest.mark.asyncio
    async def test_update_wiki_page_permission_denied(self, wiki_tools_instance):
        """Test update_wiki_page con PermissionDeniedError (lines 558-560)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(side_effect=PermissionDeniedError("Forbidden"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="No permission"):
                await wiki_tools_instance.update_wiki_page(
                    auth_token="token", wiki_id=1, content="Content"
                )

    @pytest.mark.asyncio
    async def test_update_wiki_page_authentication_error(self, wiki_tools_instance):
        """Test update_wiki_page con AuthenticationError (lines 561-563)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(side_effect=AuthenticationError("Auth failed"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Authentication failed"):
                await wiki_tools_instance.update_wiki_page(
                    auth_token="token", wiki_id=1, content="Content"
                )

    @pytest.mark.asyncio
    async def test_update_wiki_page_version_conflict(self, wiki_tools_instance):
        """Test update_wiki_page con version conflict (lines 565-567)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(side_effect=TaigaAPIError("Version conflict detected"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Version conflict"):
                await wiki_tools_instance.update_wiki_page(
                    auth_token="token", wiki_id=1, content="Content"
                )

    @pytest.mark.asyncio
    async def test_update_wiki_page_taiga_api_error(self, wiki_tools_instance):
        """Test update_wiki_page con TaigaAPIError genérico (lines 568-569)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(side_effect=TaigaAPIError("Server error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Failed to update wiki page"):
                await wiki_tools_instance.update_wiki_page(
                    auth_token="token", wiki_id=1, content="Content"
                )

    @pytest.mark.asyncio
    async def test_update_wiki_page_unexpected_error(self, wiki_tools_instance):
        """Test update_wiki_page con Exception genérica (lines 570-574)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(side_effect=RuntimeError("Unexpected"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Unexpected error"):
                await wiki_tools_instance.update_wiki_page(
                    auth_token="token", wiki_id=1, content="Content"
                )


class TestDeleteWikiPageExceptionHandlers:
    """Tests para exception handlers de delete_wiki_page."""

    @pytest.mark.asyncio
    async def test_delete_wiki_page_permission_denied(self, wiki_tools_instance):
        """Test delete_wiki_page con PermissionDeniedError (lines 620-622)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete = AsyncMock(side_effect=PermissionDeniedError("Forbidden"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="No permission"):
                await wiki_tools_instance.delete_wiki_page(auth_token="token", wiki_id=1)

    @pytest.mark.asyncio
    async def test_delete_wiki_page_authentication_error(self, wiki_tools_instance):
        """Test delete_wiki_page con AuthenticationError (lines 623-625)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete = AsyncMock(side_effect=AuthenticationError("Auth failed"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Authentication failed"):
                await wiki_tools_instance.delete_wiki_page(auth_token="token", wiki_id=1)

    @pytest.mark.asyncio
    async def test_delete_wiki_page_taiga_api_error(self, wiki_tools_instance):
        """Test delete_wiki_page con TaigaAPIError (lines 626-628)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete = AsyncMock(side_effect=TaigaAPIError("API error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Failed to delete wiki page"):
                await wiki_tools_instance.delete_wiki_page(auth_token="token", wiki_id=1)

    @pytest.mark.asyncio
    async def test_delete_wiki_page_unexpected_error(self, wiki_tools_instance):
        """Test delete_wiki_page con Exception genérica (lines 629-633)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete = AsyncMock(side_effect=RuntimeError("Unexpected"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Unexpected error"):
                await wiki_tools_instance.delete_wiki_page(auth_token="token", wiki_id=1)


class TestRestoreWikiPageExceptionHandlers:
    """Tests para exception handlers de restore_wiki_page."""

    @pytest.mark.asyncio
    async def test_restore_wiki_page_not_found(self, wiki_tools_instance):
        """Test restore_wiki_page con ResourceNotFoundError (lines 702-704)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="not found"):
                await wiki_tools_instance.restore_wiki_page(auth_token="token", wiki_id=999)

    @pytest.mark.asyncio
    async def test_restore_wiki_page_permission_denied(self, wiki_tools_instance):
        """Test restore_wiki_page con PermissionDeniedError (lines 705-707)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=PermissionDeniedError("Forbidden"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="No permission"):
                await wiki_tools_instance.restore_wiki_page(auth_token="token", wiki_id=1)

    @pytest.mark.asyncio
    async def test_restore_wiki_page_authentication_error(self, wiki_tools_instance):
        """Test restore_wiki_page con AuthenticationError (lines 708-710)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=AuthenticationError("Auth failed"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Authentication failed"):
                await wiki_tools_instance.restore_wiki_page(auth_token="token", wiki_id=1)

    @pytest.mark.asyncio
    async def test_restore_wiki_page_taiga_api_error(self, wiki_tools_instance):
        """Test restore_wiki_page con TaigaAPIError (lines 711-715)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=TaigaAPIError("API error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Failed to restore wiki page"):
                await wiki_tools_instance.restore_wiki_page(auth_token="token", wiki_id=1)

    @pytest.mark.asyncio
    async def test_restore_wiki_page_unexpected_error(self, wiki_tools_instance):
        """Test restore_wiki_page con Exception genérica (lines 716-720)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=RuntimeError("Unexpected"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Unexpected error"):
                await wiki_tools_instance.restore_wiki_page(auth_token="token", wiki_id=1)


class TestListWikiAttachmentsExceptionHandlers:
    """Tests para branches y exception handlers de list_wiki_attachments."""

    @pytest.mark.asyncio
    async def test_list_wiki_attachments_auto_paginate_false(self, wiki_tools_instance):
        """Test list_wiki_attachments con auto_paginate=False (line 788)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            with patch("src.application.tools.wiki_tools.AutoPaginator") as mock_paginator_cls:
                mock_paginator = MagicMock()
                mock_paginator.paginate_first_page = AsyncMock(return_value=[
                    {"id": 1, "name": "file.txt", "size": 100}
                ])
                mock_paginator_cls.return_value = mock_paginator

                result = await wiki_tools_instance.list_wiki_attachments(
                    auth_token="token", wiki_page_id=1, project_id=123, auto_paginate=False
                )

                assert len(result) == 1
                mock_paginator.paginate_first_page.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_wiki_attachments_not_found(self, wiki_tools_instance):
        """Test list_wiki_attachments con ResourceNotFoundError (lines 814-818)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            with patch("src.application.tools.wiki_tools.AutoPaginator") as mock_paginator_cls:
                mock_paginator = MagicMock()
                mock_paginator.paginate = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
                mock_paginator_cls.return_value = mock_paginator

                with pytest.raises(ToolError, match="not found"):
                    await wiki_tools_instance.list_wiki_attachments(
                        auth_token="token", wiki_page_id=999, project_id=123
                    )

    @pytest.mark.asyncio
    async def test_list_wiki_attachments_authentication_error(self, wiki_tools_instance):
        """Test list_wiki_attachments con AuthenticationError (lines 819-823)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            with patch("src.application.tools.wiki_tools.AutoPaginator") as mock_paginator_cls:
                mock_paginator = MagicMock()
                mock_paginator.paginate = AsyncMock(side_effect=AuthenticationError("Auth failed"))
                mock_paginator_cls.return_value = mock_paginator

                with pytest.raises(ToolError, match="Authentication failed"):
                    await wiki_tools_instance.list_wiki_attachments(
                        auth_token="token", wiki_page_id=1, project_id=123
                    )

    @pytest.mark.asyncio
    async def test_list_wiki_attachments_taiga_api_error(self, wiki_tools_instance):
        """Test list_wiki_attachments con TaigaAPIError (lines 824-828)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            with patch("src.application.tools.wiki_tools.AutoPaginator") as mock_paginator_cls:
                mock_paginator = MagicMock()
                mock_paginator.paginate = AsyncMock(side_effect=TaigaAPIError("API error"))
                mock_paginator_cls.return_value = mock_paginator

                with pytest.raises(ToolError, match="API error"):
                    await wiki_tools_instance.list_wiki_attachments(
                        auth_token="token", wiki_page_id=1, project_id=123
                    )

    @pytest.mark.asyncio
    async def test_list_wiki_attachments_unexpected_error(self, wiki_tools_instance):
        """Test list_wiki_attachments con Exception genérica (lines 829-833)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            with patch("src.application.tools.wiki_tools.AutoPaginator") as mock_paginator_cls:
                mock_paginator = MagicMock()
                mock_paginator.paginate = AsyncMock(side_effect=RuntimeError("Unexpected"))
                mock_paginator_cls.return_value = mock_paginator

                with pytest.raises(ToolError, match="Unexpected error"):
                    await wiki_tools_instance.list_wiki_attachments(
                        auth_token="token", wiki_page_id=1, project_id=123
                    )


class TestWatchWikiPageTools:
    """Tests para watch_wiki_page y unwatch_wiki_page."""

    @pytest.mark.asyncio
    async def test_watch_wiki_page_success(self, wiki_tools_instance):
        """Test watch_wiki_page exitoso."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value={"is_watcher": True, "total_watchers": 5})
            mock_cls.return_value = mock_client

            result = await wiki_tools_instance.watch_wiki_page(auth_token="token", page_id=1)

            assert result["is_watcher"] is True
            assert "watching" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_watch_wiki_page_not_found(self, wiki_tools_instance):
        """Test watch_wiki_page con ResourceNotFoundError (lines 887-889)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="not found"):
                await wiki_tools_instance.watch_wiki_page(auth_token="token", page_id=999)

    @pytest.mark.asyncio
    async def test_watch_wiki_page_authentication_error(self, wiki_tools_instance):
        """Test watch_wiki_page con AuthenticationError (lines 890-892)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=AuthenticationError("Auth failed"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Authentication failed"):
                await wiki_tools_instance.watch_wiki_page(auth_token="token", page_id=1)

    @pytest.mark.asyncio
    async def test_watch_wiki_page_taiga_api_error(self, wiki_tools_instance):
        """Test watch_wiki_page con TaigaAPIError (lines 893-895)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=TaigaAPIError("API error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Failed to watch wiki page"):
                await wiki_tools_instance.watch_wiki_page(auth_token="token", page_id=1)

    @pytest.mark.asyncio
    async def test_watch_wiki_page_unexpected_error(self, wiki_tools_instance):
        """Test watch_wiki_page con Exception genérica (lines 896-900)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=RuntimeError("Unexpected"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Unexpected error"):
                await wiki_tools_instance.watch_wiki_page(auth_token="token", page_id=1)

    @pytest.mark.asyncio
    async def test_unwatch_wiki_page_success(self, wiki_tools_instance):
        """Test unwatch_wiki_page exitoso."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value={"is_watcher": False, "total_watchers": 4})
            mock_cls.return_value = mock_client

            result = await wiki_tools_instance.unwatch_wiki_page(auth_token="token", page_id=1)

            assert result["is_watcher"] is False
            assert "stopped" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_unwatch_wiki_page_not_found(self, wiki_tools_instance):
        """Test unwatch_wiki_page con ResourceNotFoundError (lines 950-952)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="not found"):
                await wiki_tools_instance.unwatch_wiki_page(auth_token="token", page_id=999)

    @pytest.mark.asyncio
    async def test_unwatch_wiki_page_authentication_error(self, wiki_tools_instance):
        """Test unwatch_wiki_page con AuthenticationError (lines 953-955)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=AuthenticationError("Auth failed"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Authentication failed"):
                await wiki_tools_instance.unwatch_wiki_page(auth_token="token", page_id=1)

    @pytest.mark.asyncio
    async def test_unwatch_wiki_page_taiga_api_error(self, wiki_tools_instance):
        """Test unwatch_wiki_page con TaigaAPIError (lines 956-960)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=TaigaAPIError("API error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Failed to unwatch wiki page"):
                await wiki_tools_instance.unwatch_wiki_page(auth_token="token", page_id=1)

    @pytest.mark.asyncio
    async def test_unwatch_wiki_page_unexpected_error(self, wiki_tools_instance):
        """Test unwatch_wiki_page con Exception genérica (lines 961-965)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=RuntimeError("Unexpected"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Unexpected error"):
                await wiki_tools_instance.unwatch_wiki_page(auth_token="token", page_id=1)


class TestCreateWikiLinkTool:
    """Tests para create_wiki_link."""

    @pytest.mark.asyncio
    async def test_create_wiki_link_success(self, wiki_tools_instance):
        """Test create_wiki_link exitoso."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value={
                "id": 1, "project": 123, "title": "Home", "href": "home", "order": 1
            })
            mock_cls.return_value = mock_client

            result = await wiki_tools_instance.create_wiki_link(
                auth_token="token", project_id=123, title="Home", href="home"
            )

            assert result["id"] == 1
            assert result["title"] == "Home"

    @pytest.mark.asyncio
    async def test_create_wiki_link_authentication_error(self, wiki_tools_instance):
        """Test create_wiki_link con AuthenticationError (lines 1034-1038)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=AuthenticationError("Auth failed"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Authentication failed"):
                await wiki_tools_instance.create_wiki_link(
                    auth_token="token", project_id=123, title="Home", href="home"
                )

    @pytest.mark.asyncio
    async def test_create_wiki_link_taiga_api_error(self, wiki_tools_instance):
        """Test create_wiki_link con TaigaAPIError (lines 1039-1043)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=TaigaAPIError("API error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Failed to create wiki link"):
                await wiki_tools_instance.create_wiki_link(
                    auth_token="token", project_id=123, title="Home", href="home"
                )

    @pytest.mark.asyncio
    async def test_create_wiki_link_unexpected_error(self, wiki_tools_instance):
        """Test create_wiki_link con Exception genérica (lines 1044-1048)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=RuntimeError("Unexpected"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Unexpected error"):
                await wiki_tools_instance.create_wiki_link(
                    auth_token="token", project_id=123, title="Home", href="home"
                )


class TestCreateWikiAttachmentExceptionHandlers:
    """Tests para exception handlers de create_wiki_attachment."""

    @pytest.mark.asyncio
    async def test_create_wiki_attachment_not_found(self, wiki_tools_instance):
        """Test create_wiki_attachment con ResourceNotFoundError (lines 1136-1140)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="not found"):
                await wiki_tools_instance.create_wiki_attachment(
                    auth_token="token", wiki_page_id=999, project_id=123, attached_file="file.txt"
                )

    @pytest.mark.asyncio
    async def test_create_wiki_attachment_authentication_error(self, wiki_tools_instance):
        """Test create_wiki_attachment con AuthenticationError (lines 1141-1145)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=AuthenticationError("Auth failed"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Authentication failed"):
                await wiki_tools_instance.create_wiki_attachment(
                    auth_token="token", wiki_page_id=1, project_id=123, attached_file="file.txt"
                )

    @pytest.mark.asyncio
    async def test_create_wiki_attachment_taiga_api_error(self, wiki_tools_instance):
        """Test create_wiki_attachment con TaigaAPIError (lines 1146-1150)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=TaigaAPIError("API error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Failed to create attachment"):
                await wiki_tools_instance.create_wiki_attachment(
                    auth_token="token", wiki_page_id=1, project_id=123, attached_file="file.txt"
                )

    @pytest.mark.asyncio
    async def test_create_wiki_attachment_unexpected_error(self, wiki_tools_instance):
        """Test create_wiki_attachment con Exception genérica (lines 1151-1155)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=RuntimeError("Unexpected"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Unexpected error"):
                await wiki_tools_instance.create_wiki_attachment(
                    auth_token="token", wiki_page_id=1, project_id=123, attached_file="file.txt"
                )


class TestUpdateWikiAttachmentBranches:
    """Tests para branches y exception handlers de update_wiki_attachment."""

    @pytest.mark.asyncio
    async def test_update_wiki_attachment_with_is_deprecated(self, wiki_tools_instance):
        """Test update_wiki_attachment con is_deprecated (line 1216)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(return_value={
                "id": 1, "name": "file.txt", "is_deprecated": True
            })
            mock_cls.return_value = mock_client

            result = await wiki_tools_instance.update_wiki_attachment(
                auth_token="token", attachment_id=1, is_deprecated=True
            )

            assert result["is_deprecated"] is True

    @pytest.mark.asyncio
    async def test_update_wiki_attachment_not_found(self, wiki_tools_instance):
        """Test update_wiki_attachment con ResourceNotFoundError (lines 1239-1243)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="not found"):
                await wiki_tools_instance.update_wiki_attachment(
                    auth_token="token", attachment_id=999, description="New"
                )

    @pytest.mark.asyncio
    async def test_update_wiki_attachment_permission_denied(self, wiki_tools_instance):
        """Test update_wiki_attachment con PermissionDeniedError (lines 1244-1248)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(side_effect=PermissionDeniedError("Forbidden"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="No permission"):
                await wiki_tools_instance.update_wiki_attachment(
                    auth_token="token", attachment_id=1, description="New"
                )

    @pytest.mark.asyncio
    async def test_update_wiki_attachment_authentication_error(self, wiki_tools_instance):
        """Test update_wiki_attachment con AuthenticationError (lines 1249-1253)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(side_effect=AuthenticationError("Auth failed"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Authentication failed"):
                await wiki_tools_instance.update_wiki_attachment(
                    auth_token="token", attachment_id=1, description="New"
                )

    @pytest.mark.asyncio
    async def test_update_wiki_attachment_taiga_api_error(self, wiki_tools_instance):
        """Test update_wiki_attachment con TaigaAPIError (lines 1254-1258)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(side_effect=TaigaAPIError("API error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Failed to update attachment"):
                await wiki_tools_instance.update_wiki_attachment(
                    auth_token="token", attachment_id=1, description="New"
                )

    @pytest.mark.asyncio
    async def test_update_wiki_attachment_unexpected_error(self, wiki_tools_instance):
        """Test update_wiki_attachment con Exception genérica (lines 1259-1263)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.patch = AsyncMock(side_effect=RuntimeError("Unexpected"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Unexpected error"):
                await wiki_tools_instance.update_wiki_attachment(
                    auth_token="token", attachment_id=1, description="New"
                )


class TestDeleteWikiAttachmentExceptionHandlers:
    """Tests para exception handlers de delete_wiki_attachment."""

    @pytest.mark.asyncio
    async def test_delete_wiki_attachment_not_found(self, wiki_tools_instance):
        """Test delete_wiki_attachment con ResourceNotFoundError (lines 1312-1316)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="not found"):
                await wiki_tools_instance.delete_wiki_attachment(auth_token="token", attachment_id=999)

    @pytest.mark.asyncio
    async def test_delete_wiki_attachment_permission_denied(self, wiki_tools_instance):
        """Test delete_wiki_attachment con PermissionDeniedError (lines 1317-1321)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete = AsyncMock(side_effect=PermissionDeniedError("Forbidden"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="No permission"):
                await wiki_tools_instance.delete_wiki_attachment(auth_token="token", attachment_id=1)

    @pytest.mark.asyncio
    async def test_delete_wiki_attachment_authentication_error(self, wiki_tools_instance):
        """Test delete_wiki_attachment con AuthenticationError (lines 1322-1326)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete = AsyncMock(side_effect=AuthenticationError("Auth failed"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Authentication failed"):
                await wiki_tools_instance.delete_wiki_attachment(auth_token="token", attachment_id=1)

    @pytest.mark.asyncio
    async def test_delete_wiki_attachment_taiga_api_error(self, wiki_tools_instance):
        """Test delete_wiki_attachment con TaigaAPIError (lines 1327-1331)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete = AsyncMock(side_effect=TaigaAPIError("API error"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Failed to delete attachment"):
                await wiki_tools_instance.delete_wiki_attachment(auth_token="token", attachment_id=1)

    @pytest.mark.asyncio
    async def test_delete_wiki_attachment_unexpected_error(self, wiki_tools_instance):
        """Test delete_wiki_attachment con Exception genérica (lines 1332-1336)."""
        with patch("src.application.tools.wiki_tools.TaigaAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete = AsyncMock(side_effect=RuntimeError("Unexpected"))
            mock_cls.return_value = mock_client

            with pytest.raises(ToolError, match="Unexpected error"):
                await wiki_tools_instance.delete_wiki_attachment(auth_token="token", attachment_id=1)
