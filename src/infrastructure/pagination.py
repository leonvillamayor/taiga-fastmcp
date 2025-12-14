"""Sistema de paginación automática para la API de Taiga.

Este módulo proporciona clases y funciones para manejar la paginación
de forma automática y transparente en los endpoints de lista de Taiga.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from src.taiga_client import TaigaAPIClient


@dataclass(frozen=True)
class PaginationConfig:
    """Configuración para la paginación automática.

    Attributes:
        page_size: Número de items por página. Default: 100.
        max_pages: Límite máximo de páginas a obtener (seguridad). Default: 50.
        max_total_items: Límite máximo de items totales a obtener. Default: 5000.
    """

    page_size: int = 100
    max_pages: int = 50
    max_total_items: int = 5000

    def __post_init__(self) -> None:
        """Valida la configuración después de la inicialización."""
        if self.page_size < 1:
            raise ValueError("page_size debe ser mayor a 0")
        if self.max_pages < 1:
            raise ValueError("max_pages debe ser mayor a 0")
        if self.max_total_items < 1:
            raise ValueError("max_total_items debe ser mayor a 0")


@dataclass
class PaginationResult:
    """Resultado de una operación de paginación.

    Attributes:
        items: Lista de items obtenidos.
        total_pages: Número total de páginas procesadas.
        total_items: Número total de items obtenidos.
        has_more: Indica si hay más páginas disponibles.
        was_truncated: Indica si se truncó por límites de seguridad.
    """

    items: list[dict[str, Any]] = field(default_factory=list)
    total_pages: int = 0
    total_items: int = 0
    has_more: bool = False
    was_truncated: bool = False


class AutoPaginator:
    """Paginador automático para endpoints de lista de Taiga.

    Proporciona paginación automática transparente que retorna todos
    los resultados disponibles respetando límites de seguridad.
    """

    def __init__(
        self,
        client: TaigaAPIClient,
        config: PaginationConfig | None = None,
    ) -> None:
        """Inicializa el paginador automático.

        Args:
            client: Cliente de API de Taiga.
            config: Configuración de paginación. Si es None, usa valores por defecto.
        """
        self.client = client
        self.config = config or PaginationConfig()

    async def paginate(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Obtiene todos los items paginando automáticamente.

        Itera sobre todas las páginas disponibles hasta obtener todos
        los items o alcanzar los límites de seguridad configurados.

        Args:
            endpoint: Endpoint de la API (ej: "/projects", "/userstories").
            params: Parámetros adicionales para la petición.

        Returns:
            Lista de todos los items obtenidos de todas las páginas.
        """
        result = await self.paginate_with_info(endpoint, params)
        return result.items

    async def paginate_with_info(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> PaginationResult:
        """Obtiene todos los items con información de paginación.

        Similar a paginate() pero retorna información adicional sobre
        el proceso de paginación.

        Args:
            endpoint: Endpoint de la API.
            params: Parámetros adicionales para la petición.

        Returns:
            PaginationResult con items y metadatos de paginación.
        """
        all_items: list[dict[str, Any]] = []
        page = 1
        request_params = dict(params) if params else {}
        was_truncated = False
        has_more = False

        while page <= self.config.max_pages:
            request_params["page"] = page
            request_params["page_size"] = self.config.page_size

            response = await self.client.get(endpoint, params=request_params)

            # Manejar diferentes formatos de respuesta
            items = self._extract_items(response)

            if not items:
                break

            all_items.extend(items)

            # Verificar límite de items totales
            if len(all_items) >= self.config.max_total_items:
                was_truncated = True
                all_items = all_items[: self.config.max_total_items]
                has_more = True
                break

            # Verificar si hay más páginas
            if not self._has_next_page(response, items):
                break

            page += 1

            # Si alcanzamos max_pages pero hay más datos
            if page > self.config.max_pages:
                was_truncated = True
                has_more = True

        return PaginationResult(
            items=all_items,
            total_pages=page,
            total_items=len(all_items),
            has_more=has_more,
            was_truncated=was_truncated,
        )

    async def paginate_lazy(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Itera sobre items paginando bajo demanda (lazy).

        Esta implementación es más eficiente en memoria para grandes
        datasets ya que no almacena todos los items en memoria.

        Args:
            endpoint: Endpoint de la API.
            params: Parámetros adicionales para la petición.

        Yields:
            Items individuales de cada página.
        """
        page = 1
        total_items = 0
        request_params = dict(params) if params else {}

        while page <= self.config.max_pages:
            request_params["page"] = page
            request_params["page_size"] = self.config.page_size

            response = await self.client.get(endpoint, params=request_params)
            items = self._extract_items(response)

            if not items:
                break

            for item in items:
                if total_items >= self.config.max_total_items:
                    return
                yield item
                total_items += 1

            if not self._has_next_page(response, items):
                break

            page += 1

    async def paginate_first_page(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Obtiene solo la primera página de resultados.

        Útil cuando auto_paginate=False o se necesita solo una página.

        Args:
            endpoint: Endpoint de la API.
            params: Parámetros adicionales para la petición.

        Returns:
            Lista de items de la primera página.
        """
        request_params = dict(params) if params else {}
        request_params["page"] = 1
        request_params["page_size"] = self.config.page_size

        response = await self.client.get(endpoint, params=request_params)
        return self._extract_items(response)

    def _extract_items(self, response: Any) -> list[dict[str, Any]]:
        """Extrae items de la respuesta de la API.

        Maneja diferentes formatos de respuesta de Taiga:
        - Respuesta con 'results' (paginación estándar)
        - Lista directa de items
        - Respuesta vacía

        Args:
            response: Respuesta de la API.

        Returns:
            Lista de items extraídos.
        """
        if response is None:
            return []

        # Formato paginado estándar: {"results": [...], "next": ..., "count": ...}
        if isinstance(response, dict):
            if "results" in response:
                results = response.get("results", [])
                return results if isinstance(results, list) else []
            # Respuesta dict única (no es una lista)
            return []

        # Respuesta es directamente una lista
        if isinstance(response, list):
            return response

        return []

    def _has_next_page(
        self,
        response: Any,
        current_items: list[dict[str, Any]],
    ) -> bool:
        """Determina si hay una página siguiente disponible.

        Args:
            response: Respuesta de la API.
            current_items: Items de la página actual.

        Returns:
            True si hay más páginas disponibles.
        """
        if not current_items:
            return False

        # Si la respuesta tiene indicador 'next'
        if isinstance(response, dict):
            # Formato con 'next' URL
            if response.get("next") is not None:
                return True
            # Formato con total count
            if "count" in response:
                # Si hay más items que los obtenidos
                count = response.get("count", 0)
                return int(count) > len(current_items) if count is not None else False

        # Asumimos que hay más páginas si obtuvimos page_size completo
        return len(current_items) >= self.config.page_size


# Instancia por defecto con configuración estándar
DEFAULT_PAGINATION_CONFIG = PaginationConfig()
