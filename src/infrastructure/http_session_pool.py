"""Pool de sesiones HTTP reutilizables.

Este módulo implementa un pool de conexiones HTTP usando httpx.AsyncClient
con soporte para keep-alive y límites configurables de conexiones.
"""

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx

from src.infrastructure.logging.performance import (PerformanceLogger,
                                                    get_performance_logger)


class HTTPSessionPool:
    """Pool de sesiones HTTP con keep-alive y límites configurables.

    Esta clase gestiona un pool de conexiones HTTP reutilizables para
    mejorar el rendimiento evitando la creación/destrucción de conexiones
    en cada request.

    Attributes:
        base_url: URL base para todas las peticiones.
        timeout: Timeout en segundos para las peticiones.
        max_connections: Número máximo de conexiones en el pool.
        max_keepalive: Número máximo de conexiones keep-alive.

    Example:
        >>> pool = HTTPSessionPool(
        ...     base_url="https://api.taiga.io/api/v1",
        ...     timeout=30.0,
        ...     max_connections=100,
        ...     max_keepalive=20
        ... )
        >>> await pool.start()
        >>> async with pool.session() as client:
        ...     response = await client.get("/projects")
        >>> await pool.stop()
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_connections: int = 100,
        max_keepalive: int = 20,
        perf_logger: PerformanceLogger | None = None,
    ) -> None:
        """Inicializa el pool de sesiones HTTP.

        Args:
            base_url: URL base para todas las peticiones HTTP.
            timeout: Timeout en segundos para las peticiones (default: 30.0).
            max_connections: Número máximo de conexiones permitidas (default: 100).
            max_keepalive: Número máximo de conexiones keep-alive (default: 20).
            perf_logger: Logger de performance. Si es None, usa el global.
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_connections = max_connections
        self.max_keepalive = max_keepalive
        self._client: httpx.AsyncClient | None = None
        self._logger = logging.getLogger(__name__)
        self._perf_logger = perf_logger or get_performance_logger()

    @property
    def is_started(self) -> bool:
        """Indica si el pool está iniciado.

        Returns:
            True si el pool tiene un cliente activo, False en caso contrario.
        """
        return self._client is not None

    async def start(self) -> None:
        """Inicializa el pool de conexiones.

        Crea un httpx.AsyncClient configurado con los límites de conexión
        y timeout especificados. Si el pool ya está iniciado, no hace nada.

        Example:
            >>> pool = HTTPSessionPool("https://api.example.com")
            >>> await pool.start()
            >>> assert pool.is_started
        """
        if self._client is None:
            self._logger.debug(
                "Starting HTTP session pool for %s with max_connections=%d, max_keepalive=%d",
                self.base_url,
                self.max_connections,
                self.max_keepalive,
            )
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(
                    max_connections=self.max_connections,
                    max_keepalive_connections=self.max_keepalive,
                ),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip, deflate",
                },
            )
            self._logger.info("HTTP session pool started successfully")

    async def stop(self) -> None:
        """Cierra todas las conexiones del pool.

        Libera todos los recursos asociados al cliente HTTP.
        Si el pool no está iniciado, no hace nada.

        Example:
            >>> pool = HTTPSessionPool("https://api.example.com")
            >>> await pool.start()
            >>> await pool.stop()
            >>> assert not pool.is_started
        """
        if self._client is not None:
            self._logger.debug("Stopping HTTP session pool")
            await self._client.aclose()
            self._client = None
            self._logger.info("HTTP session pool stopped")

    @asynccontextmanager
    async def session(self) -> AsyncIterator[httpx.AsyncClient]:
        """Obtiene una sesión del pool.

        Context manager que proporciona acceso al cliente HTTP del pool.
        Si el pool no está iniciado, lo inicia automáticamente.

        Yields:
            httpx.AsyncClient: Cliente HTTP configurado del pool.

        Raises:
            RuntimeError: Si el cliente no puede ser inicializado.

        Example:
            >>> pool = HTTPSessionPool("https://api.example.com")
            >>> async with pool.session() as client:
            ...     response = await client.get("/endpoint")
        """
        if self._client is None:
            await self.start()

        if self._client is None:
            raise RuntimeError("Failed to initialize HTTP client")

        yield self._client

    async def __aenter__(self) -> "HTTPSessionPool":
        """Permite usar el pool como async context manager.

        Returns:
            HTTPSessionPool: La instancia del pool iniciada.

        Example:
            >>> async with HTTPSessionPool("https://api.example.com") as pool:
            ...     async with pool.session() as client:
            ...         response = await client.get("/endpoint")
        """
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Cierra el pool al salir del context manager.

        Args:
            exc_type: Tipo de excepción si ocurrió una.
            exc_val: Valor de la excepción si ocurrió una.
            exc_tb: Traceback de la excepción si ocurrió una.
        """
        await self.stop()

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
        content: bytes | None = None,
    ) -> httpx.Response:
        """Realiza una petición HTTP con logging de performance.

        Este método envuelve la petición HTTP con métricas de tiempo
        y las registra usando el PerformanceLogger.

        Args:
            method: Método HTTP (GET, POST, PUT, DELETE, etc.).
            endpoint: Path del endpoint (se concatena con base_url).
            headers: Headers adicionales para la petición.
            json: Datos JSON a enviar en el body.
            params: Parámetros de query string.
            content: Contenido raw del body.

        Returns:
            httpx.Response: Respuesta HTTP del servidor.

        Raises:
            RuntimeError: Si el pool no está iniciado.
            httpx.HTTPError: Si ocurre un error HTTP.

        Example:
            >>> async with pool.session() as client:
            ...     response = await pool.request("GET", "/projects")
        """
        if self._client is None:
            await self.start()

        if self._client is None:
            raise RuntimeError("HTTP client not initialized")

        start_time = time.perf_counter()
        status_code = 0
        error_msg: str | None = None
        request_size: int | None = None
        response_size: int | None = None

        try:
            # Calcular tamaño del request si hay body
            if json is not None:
                import json as json_module

                request_size = len(json_module.dumps(json).encode())
            elif content is not None:
                request_size = len(content)

            response = await self._client.request(
                method=method,
                url=endpoint,
                headers=headers,
                json=json,
                params=params,
                content=content,
            )
            status_code = response.status_code
            response_size = len(response.content)
            return response

        except httpx.HTTPError as e:
            status_code = getattr(e, "status_code", 0) or 500
            error_msg = str(e)
            raise

        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._perf_logger.log_api_call(
                method=method,
                endpoint=endpoint,
                duration_ms=duration_ms,
                status_code=status_code,
                request_size=request_size,
                response_size=response_size,
                error=error_msg,
            )

    async def get(
        self,
        endpoint: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Realiza una petición GET con logging de performance.

        Args:
            endpoint: Path del endpoint.
            headers: Headers adicionales.
            params: Parámetros de query string.

        Returns:
            httpx.Response: Respuesta HTTP.
        """
        return await self.request("GET", endpoint, headers=headers, params=params)

    async def post(
        self,
        endpoint: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Realiza una petición POST con logging de performance.

        Args:
            endpoint: Path del endpoint.
            headers: Headers adicionales.
            json: Datos JSON a enviar.
            params: Parámetros de query string.

        Returns:
            httpx.Response: Respuesta HTTP.
        """
        return await self.request("POST", endpoint, headers=headers, json=json, params=params)

    async def put(
        self,
        endpoint: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Realiza una petición PUT con logging de performance.

        Args:
            endpoint: Path del endpoint.
            headers: Headers adicionales.
            json: Datos JSON a enviar.
            params: Parámetros de query string.

        Returns:
            httpx.Response: Respuesta HTTP.
        """
        return await self.request("PUT", endpoint, headers=headers, json=json, params=params)

    async def patch(
        self,
        endpoint: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Realiza una petición PATCH con logging de performance.

        Args:
            endpoint: Path del endpoint.
            headers: Headers adicionales.
            json: Datos JSON a enviar.
            params: Parámetros de query string.

        Returns:
            httpx.Response: Respuesta HTTP.
        """
        return await self.request("PATCH", endpoint, headers=headers, json=json, params=params)

    async def delete(
        self,
        endpoint: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Realiza una petición DELETE con logging de performance.

        Args:
            endpoint: Path del endpoint.
            headers: Headers adicionales.
            params: Parámetros de query string.

        Returns:
            httpx.Response: Respuesta HTTP.
        """
        return await self.request("DELETE", endpoint, headers=headers, params=params)

    def get_metrics(self) -> dict[str, dict[str, Any]]:
        """Obtiene las métricas de performance del pool.

        Returns:
            Dict con métricas agregadas por endpoint.
        """
        return self._perf_logger.get_metrics_summary()
