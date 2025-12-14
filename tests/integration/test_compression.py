"""Tests de integración para compresión HTTP.

Este módulo verifica que las peticiones HTTP incluyen los headers de
compresión correctos y que las respuestas comprimidas se descomprimen
automáticamente.

Tests:
    - Test 3.7.1: Requests envían Accept-Encoding
    - Test 3.7.2: Responses comprimidas se descomprimen
    - Test 3.7.3: Bodies grandes se comprimen correctamente
"""

import gzip
from unittest.mock import patch

import httpx
import pytest

from src.infrastructure.http_session_pool import HTTPSessionPool


class TestAcceptEncodingHeader:
    """Test 3.7.1: Requests envían Accept-Encoding."""

    @pytest.mark.asyncio
    async def test_pool_includes_accept_encoding_header(self) -> None:
        """Verifica que HTTPSessionPool configura Accept-Encoding."""
        pool = HTTPSessionPool(
            base_url="https://api.example.com",
            timeout=30.0,
        )

        await pool.start()

        try:
            assert pool._client is not None
            # Verificar que el header está configurado
            headers = pool._client.headers
            assert "accept-encoding" in headers
            assert "gzip" in headers["accept-encoding"].lower()
            assert "deflate" in headers["accept-encoding"].lower()
        finally:
            await pool.stop()

    @pytest.mark.asyncio
    async def test_pool_context_manager_includes_accept_encoding(self) -> None:
        """Verifica Accept-Encoding usando context manager."""
        async with (
            HTTPSessionPool(
                base_url="https://api.example.com",
                timeout=30.0,
            ) as pool,
            pool.session() as client,
        ):
            headers = client.headers
            assert "accept-encoding" in headers
            accept_encoding = headers["accept-encoding"].lower()
            assert "gzip" in accept_encoding
            assert "deflate" in accept_encoding

    @pytest.mark.asyncio
    async def test_accept_encoding_not_overwritten(self) -> None:
        """Verifica que Accept-Encoding no se sobrescribe al usar session()."""
        pool = HTTPSessionPool(
            base_url="https://api.example.com",
            timeout=30.0,
        )

        async with pool.session() as client:
            # Primera llamada a session()
            first_headers = dict(client.headers)

        async with pool.session() as client:
            # Segunda llamada a session()
            second_headers = dict(client.headers)

        assert first_headers.get("accept-encoding") == second_headers.get("accept-encoding")

        await pool.stop()


class TestGzipDecompression:
    """Test 3.7.2: Responses comprimidas se descomprimen."""

    @pytest.mark.asyncio
    async def test_gzip_response_decompressed_automatically(self) -> None:
        """Verifica que httpx descomprime automáticamente gzip."""
        original_data = b'{"key": "value", "items": [1, 2, 3]}'
        compressed_data = gzip.compress(original_data)

        # Mock de respuesta HTTP con contenido comprimido
        # httpx descomprime automáticamente cuando recibe content-encoding: gzip
        mock_response = httpx.Response(
            status_code=200,
            content=compressed_data,  # Datos comprimidos
            headers={"content-encoding": "gzip"},
        )

        with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
            pool = HTTPSessionPool(
                base_url="https://api.example.com",
                timeout=30.0,
            )

            async with pool.session() as client:
                response = await client.get("/test")
                # httpx descomprime automáticamente
                assert response.content == original_data

            await pool.stop()

    @pytest.mark.asyncio
    async def test_deflate_response_decompressed_automatically(self) -> None:
        """Verifica que httpx descomprime automáticamente deflate."""
        import zlib

        original_data = b'{"status": "ok", "data": "test content"}'
        # deflate usa raw deflate (wbits=-15) para compatibilidad HTTP
        compress_obj = zlib.compressobj(level=9, wbits=-15)
        compressed_data = compress_obj.compress(original_data) + compress_obj.flush()

        mock_response = httpx.Response(
            status_code=200,
            content=compressed_data,  # Datos comprimidos
            headers={"content-encoding": "deflate"},
        )

        with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
            pool = HTTPSessionPool(
                base_url="https://api.example.com",
                timeout=30.0,
            )

            async with pool.session() as client:
                response = await client.get("/test")
                assert response.content == original_data

            await pool.stop()

    @pytest.mark.asyncio
    async def test_uncompressed_response_works(self) -> None:
        """Verifica que respuestas sin compresión funcionan correctamente."""
        original_data = b'{"simple": "response"}'

        mock_response = httpx.Response(
            status_code=200,
            content=original_data,
        )

        with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
            pool = HTTPSessionPool(
                base_url="https://api.example.com",
                timeout=30.0,
            )

            async with pool.session() as client:
                response = await client.get("/test")
                assert response.content == original_data

            await pool.stop()


class TestLargeBodyCompression:
    """Test 3.7.3: Bodies grandes se comprimen correctamente."""

    @pytest.mark.asyncio
    async def test_large_gzip_response_decompressed(self) -> None:
        """Verifica descompresión de respuestas grandes gzip."""
        import json

        # Crear un body grande (simula respuesta de listado)
        large_items = [{"id": i, "name": f"Item {i}" * 100} for i in range(1000)]

        original_data = json.dumps(large_items).encode("utf-8")

        # Verificar que los datos son suficientemente grandes
        assert len(original_data) > 10000, "Test data should be large"

        # Comprimir los datos
        compressed_data = gzip.compress(original_data)

        # Verificar que la compresión es efectiva
        compression_ratio = len(compressed_data) / len(original_data)
        assert compression_ratio < 0.5, "Compression should reduce size significantly"

        mock_response = httpx.Response(
            status_code=200,
            content=compressed_data,  # Datos comprimidos
            headers={"content-encoding": "gzip"},
        )

        with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
            pool = HTTPSessionPool(
                base_url="https://api.example.com",
                timeout=30.0,
            )

            async with pool.session() as client:
                response = await client.get("/large-list")
                assert response.content == original_data
                # Verificar que se puede parsear como JSON
                parsed = json.loads(response.content)
                assert len(parsed) == 1000

            await pool.stop()

    @pytest.mark.asyncio
    async def test_compression_ratio_is_significant(self) -> None:
        """Verifica que gzip reduce significativamente el tamaño."""
        import json

        # Crear datos repetitivos (comprimen muy bien)
        repetitive_data = {"items": ["repetitive content"] * 10000}
        original_bytes = json.dumps(repetitive_data).encode("utf-8")
        compressed_bytes = gzip.compress(original_bytes)

        original_size = len(original_bytes)
        compressed_size = len(compressed_bytes)
        ratio = compressed_size / original_size

        # Datos repetitivos deberían comprimir a menos del 10%
        assert ratio < 0.1, f"Expected ratio < 0.1, got {ratio:.4f}"
        assert original_size > 100000, "Original should be large"

    @pytest.mark.asyncio
    async def test_deflate_large_response(self) -> None:
        """Verifica descompresión deflate de respuestas grandes."""
        import json
        import zlib

        large_data = {"records": [{"field": f"value_{i}"} for i in range(500)]}
        original_data = json.dumps(large_data).encode("utf-8")
        # deflate usa raw deflate (wbits=-15) para compatibilidad HTTP
        compress_obj = zlib.compressobj(level=9, wbits=-15)
        compressed_data = compress_obj.compress(original_data) + compress_obj.flush()

        mock_response = httpx.Response(
            status_code=200,
            content=compressed_data,  # Datos comprimidos
            headers={"content-encoding": "deflate"},
        )

        with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
            pool = HTTPSessionPool(
                base_url="https://api.example.com",
                timeout=30.0,
            )

            async with pool.session() as client:
                response = await client.get("/large-data")
                parsed = json.loads(response.content)
                assert len(parsed["records"]) == 500

            await pool.stop()


class TestHTTPPoolConfiguration:
    """Tests adicionales de configuración del pool HTTP."""

    @pytest.mark.asyncio
    async def test_pool_default_headers(self) -> None:
        """Verifica todos los headers por defecto del pool."""
        pool = HTTPSessionPool(
            base_url="https://api.example.com",
            timeout=30.0,
        )

        await pool.start()

        try:
            assert pool._client is not None
            headers = pool._client.headers

            # Verificar Content-Type
            assert "content-type" in headers
            assert headers["content-type"] == "application/json"

            # Verificar Accept
            assert "accept" in headers
            assert headers["accept"] == "application/json"

            # Verificar Accept-Encoding
            assert "accept-encoding" in headers
            assert "gzip" in headers["accept-encoding"]
            assert "deflate" in headers["accept-encoding"]
        finally:
            await pool.stop()

    @pytest.mark.asyncio
    async def test_pool_not_started_raises_on_invalid_state(self) -> None:
        """Verifica que session() maneja correctamente el estado."""
        pool = HTTPSessionPool(
            base_url="https://api.example.com",
            timeout=30.0,
        )

        # session() debe iniciar el pool automáticamente
        async with pool.session() as client:
            assert pool.is_started
            assert client is not None

        await pool.stop()
        assert not pool.is_started

    @pytest.mark.asyncio
    async def test_pool_limits_configuration(self) -> None:
        """Verifica configuración de límites de conexión."""
        pool = HTTPSessionPool(
            base_url="https://api.example.com",
            timeout=30.0,
            max_connections=50,
            max_keepalive=10,
        )

        # Verificar que los límites se almacenan correctamente en el pool
        assert pool.max_connections == 50
        assert pool.max_keepalive == 10

        await pool.start()

        try:
            assert pool._client is not None
            # El cliente httpx debe existir y estar configurado
            # Verificamos indirectamente que el pool se configuró
            assert pool.is_started
        finally:
            await pool.stop()
