"""Tests de integración para el sistema de paginación automática.

Este módulo contiene tests de integración que verifican el correcto
funcionamiento del sistema de paginación automática con la API de Taiga.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.pagination import (
    AutoPaginator,
    PaginationConfig,
    PaginationResult,
)


class TestPaginationConfig:
    """Tests para la configuración de paginación."""

    def test_default_values(self) -> None:
        """Test 3.3.1a: Configuración por defecto tiene valores correctos."""
        config = PaginationConfig()
        assert config.page_size == 100
        assert config.max_pages == 50
        assert config.max_total_items == 5000

    def test_custom_values(self) -> None:
        """Test 3.3.1b: Configuración acepta valores personalizados."""
        config = PaginationConfig(page_size=50, max_pages=10, max_total_items=500)
        assert config.page_size == 50
        assert config.max_pages == 10
        assert config.max_total_items == 500

    def test_invalid_page_size_raises_error(self) -> None:
        """Test 3.3.1c: page_size inválido lanza error."""
        with pytest.raises(ValueError, match="page_size debe ser mayor a 0"):
            PaginationConfig(page_size=0)

    def test_invalid_max_pages_raises_error(self) -> None:
        """Test 3.3.1d: max_pages inválido lanza error."""
        with pytest.raises(ValueError, match="max_pages debe ser mayor a 0"):
            PaginationConfig(max_pages=0)

    def test_invalid_max_total_items_raises_error(self) -> None:
        """Test 3.3.1e: max_total_items inválido lanza error."""
        with pytest.raises(ValueError, match="max_total_items debe ser mayor a 0"):
            PaginationConfig(max_total_items=0)

    def test_config_is_immutable(self) -> None:
        """Test 3.3.1f: Configuración es inmutable (frozen)."""
        from dataclasses import FrozenInstanceError

        config = PaginationConfig()
        with pytest.raises(FrozenInstanceError):
            config.page_size = 50  # type: ignore[misc]


class TestAutoPaginator:
    """Tests para el paginador automático."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Crea un cliente mock para tests."""
        client = MagicMock()
        client.get = AsyncMock()
        return client

    @pytest.fixture
    def paginator(self, mock_client: MagicMock) -> AutoPaginator:
        """Crea un paginador con configuración de test."""
        config = PaginationConfig(page_size=10, max_pages=5, max_total_items=100)
        return AutoPaginator(mock_client, config)

    @pytest.mark.asyncio
    async def test_paginate_single_page(self, paginator: AutoPaginator) -> None:
        """Test 3.3.1: Paginación obtiene items de una sola página."""
        items = [{"id": i, "name": f"item_{i}"} for i in range(5)]
        paginator.client.get.return_value = {"results": items, "next": None}

        result = await paginator.paginate("/test")

        assert len(result) == 5
        assert result[0]["id"] == 0
        paginator.client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_paginate_multiple_pages(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Test 3.3.1: Paginación obtiene todos los items de múltiples páginas."""
        config = PaginationConfig(page_size=10, max_pages=5, max_total_items=100)
        paginator = AutoPaginator(mock_client, config)

        # Simular 3 páginas de resultados (última página tiene menos items que page_size)
        page1 = [{"id": i} for i in range(10)]
        page2 = [{"id": i} for i in range(10, 20)]
        page3 = [{"id": i} for i in range(20, 25)]  # Solo 5 items - indica fin

        mock_client.get.side_effect = [
            {"results": page1, "next": "/test?page=2"},
            {"results": page2, "next": "/test?page=3"},
            {"results": page3, "next": None},  # Sin next y menos items
        ]

        result = await paginator.paginate("/test")

        assert len(result) == 25
        assert mock_client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_respects_max_pages_limit(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Test 3.3.2: Respeta límite max_pages."""
        config = PaginationConfig(page_size=10, max_pages=2, max_total_items=1000)
        paginator = AutoPaginator(mock_client, config)

        # Simular muchas páginas disponibles
        page_data = {"results": [{"id": i} for i in range(10)], "next": "/test?page=2"}
        mock_client.get.return_value = page_data

        result = await paginator.paginate_with_info("/test")

        assert mock_client.get.call_count == 2
        assert result.was_truncated is True
        assert result.has_more is True

    @pytest.mark.asyncio
    async def test_respects_max_total_items_limit(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Test 3.3.3: Respeta límite max_total_items."""
        config = PaginationConfig(page_size=10, max_pages=100, max_total_items=15)
        paginator = AutoPaginator(mock_client, config)

        # Simular muchos items disponibles
        page1 = [{"id": i} for i in range(10)]
        page2 = [{"id": i} for i in range(10, 20)]

        mock_client.get.side_effect = [
            {"results": page1, "next": "/test?page=2"},
            {"results": page2, "next": "/test?page=3"},
        ]

        result = await paginator.paginate_with_info("/test")

        assert len(result.items) == 15
        assert result.was_truncated is True
        assert result.has_more is True

    @pytest.mark.asyncio
    async def test_handles_endpoint_without_pagination(
        self,
        paginator: AutoPaginator,
    ) -> None:
        """Test 3.3.4: Maneja endpoint sin paginación (lista directa)."""
        # Simular respuesta directa sin estructura de paginación
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        paginator.client.get.return_value = items

        result = await paginator.paginate("/test")

        assert len(result) == 3
        assert result[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_handles_empty_response(self, paginator: AutoPaginator) -> None:
        """Test 3.3.4b: Maneja respuesta vacía correctamente."""
        paginator.client.get.return_value = {"results": [], "next": None}

        result = await paginator.paginate("/test")

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_handles_none_response(self, paginator: AutoPaginator) -> None:
        """Test 3.3.4c: Maneja respuesta None correctamente."""
        paginator.client.get.return_value = None

        result = await paginator.paginate("/test")

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_lazy_pagination_yields_items(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Test 3.3.5: Lazy pagination funciona correctamente."""
        config = PaginationConfig(page_size=5, max_pages=3, max_total_items=100)
        paginator = AutoPaginator(mock_client, config)

        page1 = [{"id": i} for i in range(5)]
        page2 = [{"id": i} for i in range(5, 10)]
        page3 = [{"id": i} for i in range(10, 12)]

        mock_client.get.side_effect = [
            {"results": page1, "next": "/test?page=2"},
            {"results": page2, "next": "/test?page=3"},
            {"results": page3, "next": None},
        ]

        items: list[dict[str, Any]] = []
        async for item in paginator.paginate_lazy("/test"):
            items.append(item)

        assert len(items) == 12
        assert items[0]["id"] == 0
        assert items[-1]["id"] == 11

    @pytest.mark.asyncio
    async def test_lazy_pagination_respects_max_items(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Test 3.3.5b: Lazy pagination respeta max_total_items."""
        config = PaginationConfig(page_size=10, max_pages=100, max_total_items=5)
        paginator = AutoPaginator(mock_client, config)

        page_data = [{"id": i} for i in range(10)]
        mock_client.get.return_value = {"results": page_data, "next": "/test?page=2"}

        items: list[dict[str, Any]] = []
        async for item in paginator.paginate_lazy("/test"):
            items.append(item)

        assert len(items) == 5

    @pytest.mark.asyncio
    async def test_first_page_only(self, mock_client: MagicMock) -> None:
        """Test 3.3.6: auto_paginate=False retorna solo primera página."""
        config = PaginationConfig(page_size=10, max_pages=100, max_total_items=1000)
        paginator = AutoPaginator(mock_client, config)

        page1 = [{"id": i} for i in range(10)]
        mock_client.get.return_value = {"results": page1, "next": "/test?page=2"}

        result = await paginator.paginate_first_page("/test")

        assert len(result) == 10
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_paginate_with_params(self, paginator: AutoPaginator) -> None:
        """Test: Paginación pasa parámetros adicionales correctamente."""
        paginator.client.get.return_value = {"results": [{"id": 1}], "next": None}

        await paginator.paginate("/test", params={"project": 123, "status": "open"})

        call_args = paginator.client.get.call_args
        params = call_args.kwargs.get(
            "params", call_args.args[1] if len(call_args.args) > 1 else {}
        )
        assert params.get("project") == 123
        assert params.get("status") == "open"
        assert params.get("page") == 1
        assert params.get("page_size") == 10

    @pytest.mark.asyncio
    async def test_pagination_result_has_correct_metadata(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Test: PaginationResult contiene metadatos correctos."""
        config = PaginationConfig(page_size=10, max_pages=5, max_total_items=100)
        paginator = AutoPaginator(mock_client, config)

        page1 = [{"id": i} for i in range(10)]
        page2 = [{"id": i} for i in range(10, 15)]

        mock_client.get.side_effect = [
            {"results": page1, "next": "/test?page=2"},
            {"results": page2, "next": None},
        ]

        result = await paginator.paginate_with_info("/test")

        assert isinstance(result, PaginationResult)
        assert result.total_items == 15
        assert result.total_pages == 2
        assert result.has_more is False
        assert result.was_truncated is False

    @pytest.mark.asyncio
    async def test_handles_dict_response_without_results_key(
        self,
        paginator: AutoPaginator,
    ) -> None:
        """Test: Maneja respuesta dict sin clave 'results'."""
        # Una respuesta que es un dict pero no tiene 'results'
        paginator.client.get.return_value = {"error": "not found"}

        result = await paginator.paginate("/test")

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_stops_on_incomplete_page(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Test: Detiene paginación cuando página incompleta sin 'next'."""
        config = PaginationConfig(page_size=10, max_pages=5, max_total_items=100)
        paginator = AutoPaginator(mock_client, config)

        # Retorna menos items que page_size y sin 'next'
        page1 = [{"id": i} for i in range(7)]
        mock_client.get.return_value = {"results": page1}

        result = await paginator.paginate("/test")

        assert len(result) == 7
        mock_client.get.assert_called_once()


class TestAutoPaginatorWithListResponse:
    """Tests para paginador con respuestas de lista directa."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Crea un cliente mock."""
        client = MagicMock()
        client.get = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_handles_direct_list_response(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Test: Maneja respuesta que es directamente una lista."""
        config = PaginationConfig(page_size=10, max_pages=5, max_total_items=100)
        paginator = AutoPaginator(mock_client, config)

        # API retorna lista directamente (no objeto paginado)
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        mock_client.get.return_value = items

        result = await paginator.paginate("/test")

        assert len(result) == 3
        # Con lista directa, solo hace una llamada
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_response_full_page_continues(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Test: Lista de tamaño page_size intenta siguiente página."""
        config = PaginationConfig(page_size=3, max_pages=5, max_total_items=100)
        paginator = AutoPaginator(mock_client, config)

        # Primera llamada retorna lista completa
        page1 = [{"id": 1}, {"id": 2}, {"id": 3}]
        # Segunda llamada retorna lista vacía
        page2: list[dict[str, Any]] = []

        mock_client.get.side_effect = [page1, page2]

        result = await paginator.paginate("/test")

        assert len(result) == 3
        assert mock_client.get.call_count == 2


class TestPaginationResultDataclass:
    """Tests para el dataclass PaginationResult."""

    def test_default_values(self) -> None:
        """Test: Valores por defecto correctos."""
        result = PaginationResult()
        assert result.items == []
        assert result.total_pages == 0
        assert result.total_items == 0
        assert result.has_more is False
        assert result.was_truncated is False

    def test_custom_values(self) -> None:
        """Test: Acepta valores personalizados."""
        items = [{"id": 1}, {"id": 2}]
        result = PaginationResult(
            items=items,
            total_pages=3,
            total_items=2,
            has_more=True,
            was_truncated=True,
        )
        assert result.items == items
        assert result.total_pages == 3
        assert result.total_items == 2
        assert result.has_more is True
        assert result.was_truncated is True
