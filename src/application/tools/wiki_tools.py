"""
Wiki management tools for Taiga MCP Server - Application layer.
"""

from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError as MCPError

from src.config import TaigaConfig
from src.domain.exceptions import (AuthenticationError, PermissionDeniedError,
                                   ResourceNotFoundError, TaigaAPIError,
                                   ValidationError)
from src.domain.validators import (WikiPageCreateValidator,
                                   WikiPageUpdateValidator, validate_input)
from src.infrastructure.logging import get_logger
from src.infrastructure.pagination import AutoPaginator, PaginationConfig
from src.taiga_client import TaigaAPIClient


class WikiTools:
    """
    Wiki management tools for Taiga MCP Server.

    Provides MCP tools for managing wiki pages in Taiga projects.
    """

    def __init__(self, mcp: FastMCP) -> None:
        """
        Initialize wiki tools.

        Args:
            mcp: FastMCP server instance
        """
        self.mcp = mcp
        self.config = TaigaConfig()
        self.client = None  # Se inyecta después
        self._logger = get_logger("wiki_tools")

    def set_client(self, client: Any) -> None:
        """
        Inyecta el cliente de Taiga (Dependency Injection).

        Args:
            client: Cliente de Taiga para realizar operaciones
        """
        self.client = client

    def register_tools(self) -> None:
        """Register wiki tools with the MCP server."""

        # List wiki pages
        @self.mcp.tool(name="taiga_list_wiki_pages", description="List all wiki pages in a project")
        async def list_wiki_pages(
            auth_token: str,
            project_id: int,
            auto_paginate: bool = True,
        ) -> list[dict[str, Any]]:
            """
            List wiki pages in a project.

            Esta herramienta obtiene todas las páginas wiki de un proyecto en Taiga.
            Las páginas wiki permiten documentar el proyecto con contenido en Markdown.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto del que listar las páginas wiki
                auto_paginate: Si es True, obtiene automáticamente todas las páginas.
                    Si es False, retorna solo la primera página. Default: True.

            Returns:
                Lista de diccionarios con páginas wiki, cada una conteniendo:
                - id: ID de la página wiki
                - slug: Identificador URL-friendly de la página
                - project: ID del proyecto
                - content: Contenido en Markdown de la página
                - created_date: Fecha de creación
                - modified_date: Fecha de última modificación
                - version: Versión actual de la página
                - watchers: Lista de IDs de usuarios observando
                - last_modifier: ID del último usuario que modificó

            Raises:
                ToolError: Si el proyecto no existe, no hay permisos de
                    lectura, o la autenticación falla

            Example:
                >>> pages = await taiga_list_wiki_pages(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> for page in pages:
                ...     print(f"{page['slug']}: {len(page['content'])} chars")
            """
            self._logger.debug(f"[list_wiki_pages] Starting | project_id={project_id}")
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    paginator = AutoPaginator(client, PaginationConfig())
                    params = {"project": project_id}

                    if auto_paginate:
                        pages = await paginator.paginate("/wiki", params=params)
                    else:
                        pages = await paginator.paginate_first_page("/wiki", params=params)

                    if isinstance(pages, list):
                        result = [
                            {
                                "id": page.get("id"),
                                "slug": page.get("slug"),
                                "project": page.get("project"),
                                "content": page.get("content"),
                                "created_date": page.get("created_date"),
                                "modified_date": page.get("modified_date"),
                                "version": page.get("version"),
                                "watchers": page.get("watchers", []),
                                "last_modifier": page.get("last_modifier"),
                            }
                            for page in pages
                        ]
                        self._logger.info(
                            f"[list_wiki_pages] Success | project_id={project_id}, count={len(result)}"
                        )
                        return result
                    self._logger.info(
                        f"[list_wiki_pages] Success | project_id={project_id}, count=0"
                    )
                    return []

            except AuthenticationError:
                self._logger.error(
                    f"[list_wiki_pages] Authentication failed | project_id={project_id}"
                )
                raise MCPError("Authentication failed. Please authenticate first") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[list_wiki_pages] API error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[list_wiki_pages] Unexpected error | project_id={project_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.list_wiki_pages = (
            list_wiki_pages.fn if hasattr(list_wiki_pages, "fn") else list_wiki_pages
        )

        # Create wiki page
        @self.mcp.tool(name="taiga_create_wiki_page", description="Create a new wiki page")
        async def create_wiki_page(
            auth_token: str,
            project_id: int,
            slug: str,
            content: str,
            watchers: list[int] | None = None,
        ) -> dict[str, Any]:
            """
            Create a new wiki page.

            Esta herramienta crea una nueva página wiki en un proyecto de Taiga.
            El contenido puede escribirse en Markdown y se renderizará automáticamente.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde crear la página wiki
                slug: Identificador URL-friendly para la página (ej: "getting-started")
                content: Contenido de la página en formato Markdown
                watchers: Lista de IDs de usuarios a añadir como observadores (opcional)

            Returns:
                Dict con la página wiki creada conteniendo:
                - id: ID de la nueva página wiki
                - slug: Slug asignado
                - project: ID del proyecto
                - content: Contenido guardado
                - version: Versión inicial (1)
                - created_date: Fecha de creación
                - message: Mensaje de confirmación

            Raises:
                ToolError: Si el proyecto no existe, el slug ya está en uso,
                    no hay permisos, o la autenticación falla

            Example:
                >>> page = await taiga_create_wiki_page(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     slug="getting-started",
                ...     content="# Getting Started\\n\\nWelcome to our project!"
                ... )
                >>> print(f"Created page '{page['slug']}' with ID {page['id']}")
            """
            self._logger.debug(
                f"[create_wiki_page] Starting | project_id={project_id}, slug={slug}"
            )
            try:
                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {
                    "project_id": project_id,
                    "slug": slug,
                    "content": content,
                    "watchers": watchers,
                }
                validate_input(WikiPageCreateValidator, validation_data)

                page_data: dict[str, Any] = {
                    "project": project_id,
                    "slug": slug,
                    "content": content,
                }  # API expects 'project'

                if watchers:
                    page_data["watchers"] = watchers

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    page = await client.post("/wiki", data=page_data)

                    result = {
                        "id": page.get("id"),
                        "slug": page.get("slug"),
                        "project": page.get("project"),
                        "content": page.get("content"),
                        "version": page.get("version"),
                        "created_date": page.get("created_date"),
                        "message": f"Successfully created wiki page '{slug}'",
                    }
                    self._logger.info(
                        f"[create_wiki_page] Success | page_id={result.get('id')}, slug={slug}"
                    )
                    return result

            except ValidationError as e:
                self._logger.warning(
                    f"[create_wiki_page] Validation error | project_id={project_id}, slug={slug}, error={e!s}"
                )
                raise MCPError(str(e)) from e
            except AuthenticationError:
                self._logger.error(
                    f"[create_wiki_page] Authentication failed | project_id={project_id}, slug={slug}"
                )
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                if "already exists" in str(e).lower():
                    self._logger.error(
                        f"[create_wiki_page] Slug already exists | project_id={project_id}, slug={slug}"
                    )
                    raise MCPError(f"Wiki page with slug '{slug}' already exists") from e
                self._logger.error(
                    f"[create_wiki_page] API error | project_id={project_id}, slug={slug}, error={e!s}"
                )
                raise MCPError(f"Failed to create wiki page: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[create_wiki_page] Unexpected error | project_id={project_id}, slug={slug}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.create_wiki_page = (
            create_wiki_page.fn if hasattr(create_wiki_page, "fn") else create_wiki_page
        )

        # Get wiki page
        @self.mcp.tool(
            name="taiga_get_wiki_page", description="Get details of a specific wiki page"
        )
        async def get_wiki_page(auth_token: str, wiki_id: int) -> dict[str, Any]:
            """
            Get wiki page details.

            Esta herramienta obtiene los detalles completos de una página wiki
            específica incluyendo el contenido renderizado en HTML.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                wiki_id: ID de la página wiki a obtener

            Returns:
                Dict con los detalles de la página wiki conteniendo:
                - id: ID de la página
                - slug: Identificador URL-friendly
                - project: ID del proyecto
                - content: Contenido en Markdown
                - html: Contenido renderizado en HTML
                - created_date: Fecha de creación
                - modified_date: Fecha de última modificación
                - version: Versión actual
                - editions: Número de ediciones
                - watchers: Lista de IDs de observadores
                - total_watchers: Número total de observadores
                - is_watcher: Si el usuario actual está observando
                - last_modifier: ID del último editor
                - owner: ID del creador
                - attachments: Lista de archivos adjuntos

            Raises:
                ToolError: Si la página no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> page = await taiga_get_wiki_page(
                ...     auth_token="eyJ0eXAiOi...",
                ...     wiki_id=456
                ... )
                >>> print(f"Page: {page['slug']}")
                >>> print(f"Content: {page['content'][:100]}...")
            """
            self._logger.debug(f"[get_wiki_page] Starting | wiki_id={wiki_id}")
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    page = await client.get(f"/wiki/{wiki_id}")

                    result = {
                        "id": page.get("id"),
                        "slug": page.get("slug"),
                        "project": page.get("project"),
                        "content": page.get("content"),
                        "html": page.get("html"),  # Rendered HTML content
                        "created_date": page.get("created_date"),
                        "modified_date": page.get("modified_date"),
                        "version": page.get("version"),
                        "editions": page.get("editions"),
                        "watchers": page.get("watchers", []),
                        "total_watchers": page.get("total_watchers", 0),
                        "is_watcher": page.get("is_watcher", False),
                        "last_modifier": page.get("last_modifier"),
                        "owner": page.get("owner"),
                        "attachments": page.get("attachments", []),
                    }
                    self._logger.info(
                        f"[get_wiki_page] Success | wiki_id={wiki_id}, slug={result.get('slug')}"
                    )
                    return result

            except ResourceNotFoundError:
                self._logger.error(f"[get_wiki_page] Not found | wiki_id={wiki_id}")
                raise MCPError("Wiki page not found") from None
            except AuthenticationError:
                self._logger.error(f"[get_wiki_page] Authentication failed | wiki_id={wiki_id}")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(f"[get_wiki_page] API error | wiki_id={wiki_id}, error={e!s}")
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[get_wiki_page] Unexpected error | wiki_id={wiki_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.get_wiki_page = get_wiki_page.fn if hasattr(get_wiki_page, "fn") else get_wiki_page

        # Get wiki page by slug
        @self.mcp.tool(
            name="taiga_get_wiki_page_by_slug", description="Get wiki page by project and slug"
        )
        async def get_wiki_page_by_slug(
            auth_token: str, slug: str, project_id: int
        ) -> dict[str, Any]:
            """
            Get wiki page by slug.

            Esta herramienta obtiene una página wiki usando su slug URL-friendly
            en lugar de su ID numérico. Útil para acceder a páginas por nombre.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                slug: Identificador URL-friendly de la página (ej: "getting-started")
                project_id: ID del proyecto que contiene la página

            Returns:
                Dict con los detalles de la página wiki conteniendo:
                - id: ID de la página
                - slug: Identificador URL-friendly
                - project: ID del proyecto
                - content: Contenido en Markdown
                - created_date: Fecha de creación
                - modified_date: Fecha de última modificación
                - version: Versión actual
                - watchers: Lista de IDs de observadores
                - total_watchers: Número total de observadores
                - is_watcher: Si el usuario actual está observando
                - attachments: Lista de archivos adjuntos

            Raises:
                ToolError: Si la página no existe con ese slug, no hay permisos,
                    o la autenticación falla

            Example:
                >>> page = await taiga_get_wiki_page_by_slug(
                ...     auth_token="eyJ0eXAiOi...",
                ...     slug="getting-started",
                ...     project_id=123
                ... )
                >>> print(f"Found page ID {page['id']}: {page['slug']}")
            """
            self._logger.debug(
                f"[get_wiki_page_by_slug] Starting | project_id={project_id}, slug={slug}"
            )
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    page = await client.get(
                        "/wiki/by_slug",
                        params={"project": project_id, "slug": slug},  # API expects 'project'
                    )

                    result = {
                        "id": page.get("id"),
                        "slug": page.get("slug"),
                        "project": page.get("project"),
                        "content": page.get("content"),
                        "created_date": page.get("created_date"),
                        "modified_date": page.get("modified_date"),
                        "version": page.get("version"),
                        "watchers": page.get("watchers", []),
                        "total_watchers": page.get("total_watchers", 0),
                        "is_watcher": page.get("is_watcher", False),
                        "attachments": page.get("attachments", []),
                    }
                    self._logger.info(
                        f"[get_wiki_page_by_slug] Success | project_id={project_id}, slug={slug}, page_id={result.get('id')}"
                    )
                    return result

            except ResourceNotFoundError:
                self._logger.error(
                    f"[get_wiki_page_by_slug] Not found | project_id={project_id}, slug={slug}"
                )
                raise MCPError(f"Wiki page with slug '{slug}' not found") from None
            except AuthenticationError:
                self._logger.error(
                    f"[get_wiki_page_by_slug] Authentication failed | project_id={project_id}, slug={slug}"
                )
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[get_wiki_page_by_slug] API error | project_id={project_id}, slug={slug}, error={e!s}"
                )
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[get_wiki_page_by_slug] Unexpected error | project_id={project_id}, slug={slug}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.get_wiki_page_by_slug = (
            get_wiki_page_by_slug.fn
            if hasattr(get_wiki_page_by_slug, "fn")
            else get_wiki_page_by_slug
        )

        # Update wiki page
        @self.mcp.tool(name="taiga_update_wiki_page", description="Update an existing wiki page")
        async def update_wiki_page(
            auth_token: str,
            wiki_id: int,
            slug: str | None = None,
            content: str | None = None,
            version: int | None = None,
        ) -> dict[str, Any]:
            """
            Update wiki page.

            Esta herramienta actualiza una página wiki existente. Soporta control
            de versiones para evitar conflictos de edición concurrente.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                wiki_id: ID de la página wiki a actualizar
                slug: Nuevo slug URL-friendly (opcional, para renombrar)
                content: Nuevo contenido en Markdown (opcional)
                version: Versión esperada para control de concurrencia (opcional).
                    Si se proporciona y no coincide, la actualización fallará.

            Returns:
                Dict con la página actualizada conteniendo:
                - id: ID de la página
                - slug: Slug actual (posiblemente nuevo)
                - project: ID del proyecto
                - content: Contenido actualizado
                - version: Nueva versión
                - modified_date: Fecha de modificación
                - message: Mensaje de confirmación

            Raises:
                ToolError: Si la página no existe, hay conflicto de versiones,
                    no hay permisos de edición, o la autenticación falla

            Example:
                >>> updated = await taiga_update_wiki_page(
                ...     auth_token="eyJ0eXAiOi...",
                ...     wiki_id=456,
                ...     content="# Updated Content\\n\\nNew information here.",
                ...     version=1
                ... )
                >>> print(f"Page updated to version {updated['version']}")
            """
            self._logger.debug(f"[update_wiki_page] Starting | wiki_id={wiki_id}")
            try:
                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {
                    "wiki_id": wiki_id,
                    "slug": slug,
                    "content": content,
                    "version": version,
                }
                validate_input(WikiPageUpdateValidator, validation_data)

                update_data = {}
                if slug is not None:
                    update_data["slug"] = slug
                if content is not None:
                    update_data["content"] = content
                if version is not None:
                    update_data["version"] = version

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    page = await client.patch(f"/wiki/{wiki_id}", data=update_data)

                    result = {
                        "id": page.get("id"),
                        "slug": page.get("slug"),
                        "project": page.get("project"),
                        "content": page.get("content"),
                        "version": page.get("version"),
                        "modified_date": page.get("modified_date"),
                        "message": f"Successfully updated wiki page {wiki_id}",
                    }
                    self._logger.info(
                        f"[update_wiki_page] Success | wiki_id={wiki_id}, version={result.get('version')}"
                    )
                    return result

            except ValidationError as e:
                self._logger.warning(
                    f"[update_wiki_page] Validation error | wiki_id={wiki_id}, error={e!s}"
                )
                raise MCPError(str(e)) from e
            except ResourceNotFoundError:
                self._logger.error(f"[update_wiki_page] Not found | wiki_id={wiki_id}")
                raise MCPError(f"Wiki page {wiki_id} not found") from None
            except PermissionDeniedError:
                self._logger.error(f"[update_wiki_page] Permission denied | wiki_id={wiki_id}")
                raise MCPError(f"No permission to update wiki page {wiki_id}") from None
            except AuthenticationError:
                self._logger.error(f"[update_wiki_page] Authentication failed | wiki_id={wiki_id}")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                if "version" in str(e).lower() and "conflict" in str(e).lower():
                    self._logger.error(f"[update_wiki_page] Version conflict | wiki_id={wiki_id}")
                    raise MCPError("Version conflict - page was modified by another user") from e
                self._logger.error(f"[update_wiki_page] API error | wiki_id={wiki_id}, error={e!s}")
                raise MCPError(f"Failed to update wiki page: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[update_wiki_page] Unexpected error | wiki_id={wiki_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.update_wiki_page = (
            update_wiki_page.fn if hasattr(update_wiki_page, "fn") else update_wiki_page
        )

        # Delete wiki page
        @self.mcp.tool(name="taiga_delete_wiki_page", description="Delete a wiki page")
        async def delete_wiki_page(auth_token: str, wiki_id: int) -> bool:
            """
            Delete wiki page.

            Esta herramienta elimina una página wiki. Las páginas eliminadas
            pueden ser restauradas posteriormente usando taiga_restore_wiki_page.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                wiki_id: ID de la página wiki a eliminar

            Returns:
                True si la página fue eliminada exitosamente

            Raises:
                ToolError: Si la página no existe, no hay permisos de
                    eliminación, o la autenticación falla

            Example:
                >>> result = await taiga_delete_wiki_page(
                ...     auth_token="eyJ0eXAiOi...",
                ...     wiki_id=456
                ... )
                >>> if result:
                ...     print("Wiki page deleted (can be restored)")
            """
            self._logger.debug(f"[delete_wiki_page] Starting | wiki_id={wiki_id}")
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    result = await client.delete(f"/wiki/{wiki_id}")
                    self._logger.info(f"[delete_wiki_page] Success | wiki_id={wiki_id}")
                    return result

            except ResourceNotFoundError:
                self._logger.error(f"[delete_wiki_page] Not found | wiki_id={wiki_id}")
                raise MCPError("Wiki page not found") from None
            except PermissionDeniedError:
                self._logger.error(f"[delete_wiki_page] Permission denied | wiki_id={wiki_id}")
                raise MCPError(f"No permission to delete wiki page {wiki_id}") from None
            except AuthenticationError:
                self._logger.error(f"[delete_wiki_page] Authentication failed | wiki_id={wiki_id}")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(f"[delete_wiki_page] API error | wiki_id={wiki_id}, error={e!s}")
                raise MCPError(f"Failed to delete wiki page: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[delete_wiki_page] Unexpected error | wiki_id={wiki_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.delete_wiki_page = (
            delete_wiki_page.fn if hasattr(delete_wiki_page, "fn") else delete_wiki_page
        )

        # Restore wiki page
        @self.mcp.tool(name="taiga_restore_wiki_page", description="Restore a deleted wiki page")
        async def restore_wiki_page(auth_token: str, wiki_id: int) -> dict[str, Any]:
            """
            Restore deleted wiki page.

            Esta herramienta restaura una página wiki que fue previamente
            eliminada, recuperando todo su contenido y metadatos.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                wiki_id: ID de la página wiki eliminada a restaurar

            Returns:
                Dict con la página restaurada conteniendo:
                - id: ID de la página
                - slug: Slug de la página
                - project: ID del proyecto
                - content: Contenido recuperado
                - html: Contenido renderizado en HTML
                - version: Versión actual
                - created_date: Fecha de creación original
                - modified_date: Fecha de restauración
                - watchers: Lista de observadores
                - total_watchers: Número de observadores
                - message: Mensaje de confirmación

            Raises:
                ToolError: Si la página no existe, no está eliminada,
                    no hay permisos, o la autenticación falla

            Example:
                >>> restored = await taiga_restore_wiki_page(
                ...     auth_token="eyJ0eXAiOi...",
                ...     wiki_id=456
                ... )
                >>> print(f"Restored: {restored['slug']}")
            """
            self._logger.debug(f"[restore_wiki_page] Starting | wiki_id={wiki_id}")
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    page = await client.post(f"/wiki/{wiki_id}/restore")

                    result = {
                        "id": page.get("id"),
                        "slug": page.get("slug"),
                        "project": page.get("project"),
                        "content": page.get("content"),
                        "html": page.get("html"),
                        "version": page.get("version"),
                        "created_date": page.get("created_date"),
                        "modified_date": page.get("modified_date"),
                        "watchers": page.get("watchers", []),
                        "total_watchers": page.get("total_watchers", 0),
                        "message": f"Successfully restored wiki page {wiki_id}",
                    }
                    self._logger.info(
                        f"[restore_wiki_page] Success | wiki_id={wiki_id}, slug={result.get('slug')}"
                    )
                    return result

            except ResourceNotFoundError:
                self._logger.error(f"[restore_wiki_page] Not found | wiki_id={wiki_id}")
                raise MCPError(f"Wiki page {wiki_id} not found") from None
            except PermissionDeniedError:
                self._logger.error(f"[restore_wiki_page] Permission denied | wiki_id={wiki_id}")
                raise MCPError(f"No permission to restore wiki page {wiki_id}") from None
            except AuthenticationError:
                self._logger.error(f"[restore_wiki_page] Authentication failed | wiki_id={wiki_id}")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[restore_wiki_page] API error | wiki_id={wiki_id}, error={e!s}"
                )
                raise MCPError(f"Failed to restore wiki page: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[restore_wiki_page] Unexpected error | wiki_id={wiki_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.restore_wiki_page = (
            restore_wiki_page.fn if hasattr(restore_wiki_page, "fn") else restore_wiki_page
        )

        # List wiki attachments
        @self.mcp.tool(
            name="taiga_list_wiki_attachments", description="List attachments on a wiki page"
        )
        async def list_wiki_attachments(
            auth_token: str,
            wiki_page_id: int,
            project_id: int,
            auto_paginate: bool = True,
        ) -> list[dict[str, Any]]:
            """
            List wiki page attachments.

            Esta herramienta obtiene todos los archivos adjuntos de una página wiki.
            Los adjuntos pueden ser imágenes, documentos u otros archivos.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                wiki_page_id: ID de la página wiki
                project_id: ID del proyecto que contiene la página
                auto_paginate: Si es True, obtiene automáticamente todas las páginas.
                    Si es False, retorna solo la primera página. Default: True.

            Returns:
                Lista de diccionarios con adjuntos, cada uno conteniendo:
                - id: ID del adjunto
                - name: Nombre del archivo
                - size: Tamaño en bytes
                - url: URL para descargar el archivo
                - created_date: Fecha de subida
                - owner: ID del usuario que subió el archivo
                - is_deprecated: Si está marcado como obsoleto

            Raises:
                ToolError: Si la página no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> attachments = await taiga_list_wiki_attachments(
                ...     auth_token="eyJ0eXAiOi...",
                ...     wiki_page_id=456,
                ...     project_id=123
                ... )
                >>> for att in attachments:
                ...     print(f"{att['name']}: {att['size']} bytes")
            """
            self._logger.debug(
                f"[list_wiki_attachments] Starting | wiki_page_id={wiki_page_id}, project_id={project_id}"
            )
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    paginator = AutoPaginator(client, PaginationConfig())
                    params = {
                        "object_id": wiki_page_id,
                        "project": project_id,
                    }

                    if auto_paginate:
                        attachments = await paginator.paginate("/wiki/attachments", params=params)
                    else:
                        attachments = await paginator.paginate_first_page(
                            "/wiki/attachments", params=params
                        )

                    if isinstance(attachments, list):
                        result = [
                            {
                                "id": att.get("id"),
                                "name": att.get("name"),
                                "size": att.get("size"),
                                "url": att.get("url"),
                                "created_date": att.get("created_date"),
                                "owner": att.get("owner"),
                                "is_deprecated": att.get("is_deprecated", False),
                            }
                            for att in attachments
                        ]
                        self._logger.info(
                            f"[list_wiki_attachments] Success | wiki_page_id={wiki_page_id}, count={len(result)}"
                        )
                        return result
                    self._logger.info(
                        f"[list_wiki_attachments] Success | wiki_page_id={wiki_page_id}, count=0"
                    )
                    return []

            except ResourceNotFoundError:
                self._logger.error(
                    f"[list_wiki_attachments] Not found | wiki_page_id={wiki_page_id}"
                )
                raise MCPError(f"Wiki page {wiki_page_id} not found") from None
            except AuthenticationError:
                self._logger.error(
                    f"[list_wiki_attachments] Authentication failed | wiki_page_id={wiki_page_id}"
                )
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[list_wiki_attachments] API error | wiki_page_id={wiki_page_id}, error={e!s}"
                )
                raise MCPError(f"API error: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[list_wiki_attachments] Unexpected error | wiki_page_id={wiki_page_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.list_wiki_attachments = (
            list_wiki_attachments.fn
            if hasattr(list_wiki_attachments, "fn")
            else list_wiki_attachments
        )

        # Watch wiki page
        @self.mcp.tool(
            name="taiga_watch_wiki_page", description="Watch a wiki page for notifications"
        )
        async def watch_wiki_page(auth_token: str, page_id: int) -> dict[str, Any]:
            """
            Watch wiki page.

            Esta herramienta suscribe al usuario actual para recibir notificaciones
            cuando la página wiki sea modificada.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                page_id: ID de la página wiki a observar

            Returns:
                Dict con el estado de observación conteniendo:
                - is_watcher: True indicando que ahora está observando
                - total_watchers: Número total de observadores de la página
                - message: Mensaje de confirmación

            Raises:
                ToolError: Si la página no existe, o la autenticación falla

            Example:
                >>> result = await taiga_watch_wiki_page(
                ...     auth_token="eyJ0eXAiOi...",
                ...     page_id=456
                ... )
                >>> print(f"Watching: {result['is_watcher']}")
            """
            self._logger.debug(f"[watch_wiki_page] Starting | page_id={page_id}")
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    api_result = await client.post(f"/wiki/{page_id}/watch")

                    result = {
                        "is_watcher": api_result.get("is_watcher", True),
                        "total_watchers": api_result.get("total_watchers", 0),
                        "message": f"Now watching wiki page {page_id}",
                    }
                    self._logger.info(f"[watch_wiki_page] Success | page_id={page_id}")
                    return result

            except ResourceNotFoundError:
                self._logger.error(f"[watch_wiki_page] Not found | page_id={page_id}")
                raise MCPError(f"Wiki page {page_id} not found") from None
            except AuthenticationError:
                self._logger.error(f"[watch_wiki_page] Authentication failed | page_id={page_id}")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(f"[watch_wiki_page] API error | page_id={page_id}, error={e!s}")
                raise MCPError(f"Failed to watch wiki page: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[watch_wiki_page] Unexpected error | page_id={page_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.watch_wiki_page = (
            watch_wiki_page.fn if hasattr(watch_wiki_page, "fn") else watch_wiki_page
        )

        # Unwatch wiki page
        @self.mcp.tool(name="taiga_unwatch_wiki_page", description="Stop watching a wiki page")
        async def unwatch_wiki_page(auth_token: str, page_id: int) -> dict[str, Any]:
            """
            Unwatch wiki page.

            Esta herramienta cancela la suscripción del usuario actual a las
            notificaciones de cambios en la página wiki.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                page_id: ID de la página wiki a dejar de observar

            Returns:
                Dict con el estado de observación conteniendo:
                - is_watcher: False indicando que ya no está observando
                - total_watchers: Número total de observadores restantes
                - message: Mensaje de confirmación

            Raises:
                ToolError: Si la página no existe, o la autenticación falla

            Example:
                >>> result = await taiga_unwatch_wiki_page(
                ...     auth_token="eyJ0eXAiOi...",
                ...     page_id=456
                ... )
                >>> print(f"Still watching: {result['is_watcher']}")
            """
            self._logger.debug(f"[unwatch_wiki_page] Starting | page_id={page_id}")
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    api_result = await client.post(f"/wiki/{page_id}/unwatch")

                    result = {
                        "is_watcher": api_result.get("is_watcher", False),
                        "total_watchers": api_result.get("total_watchers", 0),
                        "message": f"Stopped watching wiki page {page_id}",
                    }
                    self._logger.info(f"[unwatch_wiki_page] Success | page_id={page_id}")
                    return result

            except ResourceNotFoundError:
                self._logger.error(f"[unwatch_wiki_page] Not found | page_id={page_id}")
                raise MCPError(f"Wiki page {page_id} not found") from None
            except AuthenticationError:
                self._logger.error(f"[unwatch_wiki_page] Authentication failed | page_id={page_id}")
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[unwatch_wiki_page] API error | page_id={page_id}, error={e!s}"
                )
                raise MCPError(f"Failed to unwatch wiki page: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[unwatch_wiki_page] Unexpected error | page_id={page_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.unwatch_wiki_page = (
            unwatch_wiki_page.fn if hasattr(unwatch_wiki_page, "fn") else unwatch_wiki_page
        )

        # Create wiki link
        @self.mcp.tool(name="taiga_create_wiki_link", description="Create a wiki link in a project")
        async def create_wiki_link(
            auth_token: str, project_id: int, title: str, href: str
        ) -> dict[str, Any]:
            """
            Create wiki link.

            Esta herramienta crea un enlace en la navegación del wiki del proyecto.
            Los enlaces aparecen en la barra lateral de la wiki para navegación rápida.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde crear el enlace
                title: Título visible del enlace en la navegación
                href: Destino del enlace (puede ser un slug de wiki o URL externa)

            Returns:
                Dict con el enlace creado conteniendo:
                - id: ID del enlace
                - project: ID del proyecto
                - title: Título del enlace
                - href: Destino del enlace
                - order: Posición en la navegación
                - message: Mensaje de confirmación

            Raises:
                ToolError: Si el proyecto no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> link = await taiga_create_wiki_link(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     title="Getting Started",
                ...     href="getting-started"
                ... )
                >>> print(f"Created link '{link['title']}' -> {link['href']}")
            """
            self._logger.debug(
                f"[create_wiki_link] Starting | project_id={project_id}, title={title}"
            )
            try:
                link_data = {"project": project_id, "title": title, "href": href}

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    link = await client.post("/wiki-links", data=link_data)

                    result = {
                        "id": link.get("id"),
                        "project": link.get("project"),
                        "title": link.get("title"),
                        "href": link.get("href"),
                        "order": link.get("order"),
                        "message": f"Successfully created wiki link '{title}'",
                    }
                    self._logger.info(
                        f"[create_wiki_link] Success | project_id={project_id}, link_id={result.get('id')}, title={title}"
                    )
                    return result

            except AuthenticationError:
                self._logger.error(
                    f"[create_wiki_link] Authentication failed | project_id={project_id}, title={title}"
                )
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[create_wiki_link] API error | project_id={project_id}, title={title}, error={e!s}"
                )
                raise MCPError(f"Failed to create wiki link: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[create_wiki_link] Unexpected error | project_id={project_id}, title={title}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.create_wiki_link = (
            create_wiki_link.fn if hasattr(create_wiki_link, "fn") else create_wiki_link
        )

        # Create wiki attachment
        @self.mcp.tool(
            name="taiga_create_wiki_attachment", description="Create an attachment on a wiki page"
        )
        async def create_wiki_attachment(
            auth_token: str,
            wiki_page_id: int,
            project_id: int,
            attached_file: str,
            description: str | None = None,
        ) -> dict[str, Any]:
            """
            Create wiki attachment.

            Esta herramienta sube un archivo adjunto a una página wiki.
            Los adjuntos pueden referenciarse desde el contenido Markdown.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                wiki_page_id: ID de la página wiki donde adjuntar el archivo
                project_id: ID del proyecto que contiene la página
                attached_file: Ruta o contenido del archivo a adjuntar
                description: Descripción opcional del archivo adjunto

            Returns:
                Dict con el adjunto creado conteniendo:
                - id: ID del adjunto
                - name: Nombre del archivo
                - size: Tamaño en bytes
                - url: URL para descargar
                - attached_file: Ruta del archivo en el servidor
                - created_date: Fecha de subida
                - description: Descripción del archivo
                - message: Mensaje de confirmación

            Raises:
                ToolError: Si la página no existe, el archivo es inválido,
                    no hay permisos, o la autenticación falla

            Example:
                >>> attachment = await taiga_create_wiki_attachment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     wiki_page_id=456,
                ...     project_id=123,
                ...     attached_file="/path/to/diagram.png",
                ...     description="Architecture diagram"
                ... )
                >>> print(f"Uploaded: {attachment['name']} ({attachment['url']})")
            """
            self._logger.debug(
                f"[create_wiki_attachment] Starting | wiki_page_id={wiki_page_id}, project_id={project_id}"
            )
            try:
                attachment_data: dict[str, Any] = {
                    "object_id": wiki_page_id,  # API expects object_id
                    "project": project_id,  # API expects 'project'
                    "attached_file": attached_file,
                }

                if description:
                    attachment_data["description"] = description

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    attachment = await client.post("/wiki/attachments", data=attachment_data)

                    result = {
                        "id": attachment.get("id"),
                        "name": attachment.get("name"),
                        "size": attachment.get("size"),
                        "url": attachment.get("url"),
                        "attached_file": attachment.get("attached_file"),
                        "created_date": attachment.get("created_date"),
                        "description": attachment.get("description"),
                        "message": f"Successfully created attachment on wiki page {wiki_page_id}",
                    }
                    self._logger.info(
                        f"[create_wiki_attachment] Success | wiki_page_id={wiki_page_id}, attachment_id={result.get('id')}"
                    )
                    return result

            except ResourceNotFoundError:
                self._logger.error(
                    f"[create_wiki_attachment] Not found | wiki_page_id={wiki_page_id}"
                )
                raise MCPError(f"Wiki page {wiki_page_id} not found") from None
            except AuthenticationError:
                self._logger.error(
                    f"[create_wiki_attachment] Authentication failed | wiki_page_id={wiki_page_id}"
                )
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[create_wiki_attachment] API error | wiki_page_id={wiki_page_id}, error={e!s}"
                )
                raise MCPError(f"Failed to create attachment: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[create_wiki_attachment] Unexpected error | wiki_page_id={wiki_page_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.create_wiki_attachment = (
            create_wiki_attachment.fn
            if hasattr(create_wiki_attachment, "fn")
            else create_wiki_attachment
        )

        # Update wiki attachment
        @self.mcp.tool(
            name="taiga_update_wiki_attachment", description="Update an attachment on a wiki page"
        )
        async def update_wiki_attachment(
            auth_token: str,
            attachment_id: int,
            description: str | None = None,
            is_deprecated: bool | None = None,
        ) -> dict[str, Any]:
            """
            Update wiki attachment.

            Esta herramienta actualiza los metadatos de un archivo adjunto
            en una página wiki. No permite cambiar el archivo en sí.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                attachment_id: ID del adjunto a actualizar
                description: Nueva descripción del archivo (opcional)
                is_deprecated: Marcar como obsoleto sin eliminar (opcional)

            Returns:
                Dict con el adjunto actualizado conteniendo:
                - id: ID del adjunto
                - name: Nombre del archivo
                - size: Tamaño en bytes
                - url: URL de descarga
                - description: Descripción actualizada
                - is_deprecated: Estado de obsolescencia
                - modified_date: Fecha de modificación
                - message: Mensaje de confirmación

            Raises:
                ToolError: Si el adjunto no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> updated = await taiga_update_wiki_attachment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     attachment_id=789,
                ...     description="Updated architecture diagram v2",
                ...     is_deprecated=False
                ... )
                >>> print(f"Updated: {updated['description']}")
            """
            self._logger.debug(f"[update_wiki_attachment] Starting | attachment_id={attachment_id}")
            try:
                update_data = {}
                if description is not None:
                    update_data["description"] = description
                if is_deprecated is not None:
                    update_data["is_deprecated"] = is_deprecated

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    attachment = await client.patch(
                        f"/wiki/attachments/{attachment_id}", data=update_data
                    )

                    result = {
                        "id": attachment.get("id"),
                        "name": attachment.get("name"),
                        "size": attachment.get("size"),
                        "url": attachment.get("url"),
                        "description": attachment.get("description"),
                        "is_deprecated": attachment.get("is_deprecated", False),
                        "modified_date": attachment.get("modified_date"),
                        "message": f"Successfully updated attachment {attachment_id}",
                    }
                    self._logger.info(
                        f"[update_wiki_attachment] Success | attachment_id={attachment_id}"
                    )
                    return result

            except ResourceNotFoundError:
                self._logger.error(
                    f"[update_wiki_attachment] Not found | attachment_id={attachment_id}"
                )
                raise MCPError("Attachment or wiki page not found") from None
            except PermissionDeniedError:
                self._logger.error(
                    f"[update_wiki_attachment] Permission denied | attachment_id={attachment_id}"
                )
                raise MCPError("No permission to update attachment") from None
            except AuthenticationError:
                self._logger.error(
                    f"[update_wiki_attachment] Authentication failed | attachment_id={attachment_id}"
                )
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[update_wiki_attachment] API error | attachment_id={attachment_id}, error={e!s}"
                )
                raise MCPError(f"Failed to update attachment: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[update_wiki_attachment] Unexpected error | attachment_id={attachment_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.update_wiki_attachment = (
            update_wiki_attachment.fn
            if hasattr(update_wiki_attachment, "fn")
            else update_wiki_attachment
        )

        # Delete wiki attachment
        @self.mcp.tool(
            name="taiga_delete_wiki_attachment", description="Delete an attachment from a wiki page"
        )
        async def delete_wiki_attachment(auth_token: str, attachment_id: int) -> bool:
            """
            Delete wiki attachment.

            Esta herramienta elimina permanentemente un archivo adjunto de una
            página wiki. Esta acción no se puede deshacer.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                attachment_id: ID del adjunto a eliminar

            Returns:
                True si el adjunto fue eliminado exitosamente

            Raises:
                ToolError: Si el adjunto no existe, no hay permisos de
                    eliminación, o la autenticación falla

            Example:
                >>> result = await taiga_delete_wiki_attachment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     attachment_id=789
                ... )
                >>> if result:
                ...     print("Attachment permanently deleted")
            """
            self._logger.debug(f"[delete_wiki_attachment] Starting | attachment_id={attachment_id}")
            try:
                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    result = await client.delete(f"/wiki/attachments/{attachment_id}")
                    self._logger.info(
                        f"[delete_wiki_attachment] Success | attachment_id={attachment_id}"
                    )
                    return result

            except ResourceNotFoundError:
                self._logger.error(
                    f"[delete_wiki_attachment] Not found | attachment_id={attachment_id}"
                )
                raise MCPError("Attachment or wiki page not found") from None
            except PermissionDeniedError:
                self._logger.error(
                    f"[delete_wiki_attachment] Permission denied | attachment_id={attachment_id}"
                )
                raise MCPError("No permission to delete attachment") from None
            except AuthenticationError:
                self._logger.error(
                    f"[delete_wiki_attachment] Authentication failed | attachment_id={attachment_id}"
                )
                raise MCPError("Authentication failed") from None
            except TaigaAPIError as e:
                self._logger.error(
                    f"[delete_wiki_attachment] API error | attachment_id={attachment_id}, error={e!s}"
                )
                raise MCPError(f"Failed to delete attachment: {e!s}") from e
            except Exception as e:
                self._logger.error(
                    f"[delete_wiki_attachment] Unexpected error | attachment_id={attachment_id}, error={e!s}"
                )
                raise MCPError(f"Unexpected error: {e!s}") from e

        # Store reference for direct test access
        self.delete_wiki_attachment = (
            delete_wiki_attachment.fn
            if hasattr(delete_wiki_attachment, "fn")
            else delete_wiki_attachment
        )
