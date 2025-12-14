"""
Sistema de logging estructurado para métricas de performance.

Este módulo proporciona herramientas para medir y registrar tiempos
de ejecución de operaciones y llamadas API, facilitando la identificación
de bottlenecks y el monitoreo de performance.
"""

import logging
import time
from collections import defaultdict
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from src.infrastructure.logging.correlation import CorrelationIdManager
from src.infrastructure.logging.logger import get_logger


@dataclass
class APIMetrics:
    """Métricas agregadas por endpoint.

    Attributes:
        total_calls: Número total de llamadas.
        total_duration_ms: Duración total acumulada en milisegundos.
        min_duration_ms: Duración mínima registrada.
        max_duration_ms: Duración máxima registrada.
        success_count: Número de llamadas exitosas.
        error_count: Número de llamadas con error.
    """

    total_calls: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0
    success_count: int = 0
    error_count: int = 0

    @property
    def avg_duration_ms(self) -> float:
        """Calcula la duración promedio en milisegundos."""
        if self.total_calls == 0:
            return 0.0
        return self.total_duration_ms / self.total_calls

    @property
    def success_rate(self) -> float:
        """Calcula la tasa de éxito (0.0 a 1.0)."""
        if self.total_calls == 0:
            return 0.0
        return self.success_count / self.total_calls

    def to_dict(self) -> dict[str, Any]:
        """Convierte las métricas a diccionario."""
        return {
            "total_calls": self.total_calls,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "min_duration_ms": round(self.min_duration_ms, 2)
            if self.min_duration_ms != float("inf")
            else 0.0,
            "max_duration_ms": round(self.max_duration_ms, 2),
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": round(self.success_rate, 4),
        }


@dataclass
class EndpointMetricsStore:
    """Almacén thread-safe de métricas por endpoint.

    Attributes:
        _metrics: Diccionario de métricas por endpoint.
    """

    _metrics: dict[str, APIMetrics] = field(default_factory=lambda: defaultdict(APIMetrics))

    def record(
        self,
        endpoint: str,
        duration_ms: float,
        success: bool,
    ) -> None:
        """Registra una métrica para un endpoint.

        Args:
            endpoint: Identificador del endpoint.
            duration_ms: Duración de la operación en milisegundos.
            success: Si la operación fue exitosa.
        """
        metrics = self._metrics[endpoint]
        metrics.total_calls += 1
        metrics.total_duration_ms += duration_ms
        metrics.min_duration_ms = min(metrics.min_duration_ms, duration_ms)
        metrics.max_duration_ms = max(metrics.max_duration_ms, duration_ms)
        if success:
            metrics.success_count += 1
        else:
            metrics.error_count += 1

    def get_metrics(self, endpoint: str) -> APIMetrics:
        """Obtiene métricas para un endpoint específico.

        Args:
            endpoint: Identificador del endpoint.

        Returns:
            APIMetrics para el endpoint.
        """
        return self._metrics[endpoint]

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """Obtiene todas las métricas en formato diccionario.

        Returns:
            Diccionario con métricas por endpoint.
        """
        return {endpoint: metrics.to_dict() for endpoint, metrics in self._metrics.items()}

    def reset(self) -> None:
        """Reinicia todas las métricas."""
        self._metrics.clear()


class PerformanceLogger:
    """Logger de performance con soporte para métricas estructuradas.

    Esta clase proporciona:
    - Context manager `measure()` para medir duración de operaciones
    - Método `log_api_call()` para registrar llamadas API
    - Almacenamiento y agregación de métricas por endpoint

    Example:
        >>> perf_logger = PerformanceLogger()
        >>> with perf_logger.measure("database_query", table="users"):
        ...     # Operación a medir
        ...     pass
        >>> perf_logger.log_api_call("GET", "/projects", 150.5, 200)
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Inicializa el PerformanceLogger.

        Args:
            logger: Logger a utilizar. Si es None, crea uno con get_logger.
        """
        self._logger = logger or get_logger("performance")
        self._metrics_store = EndpointMetricsStore()

    @property
    def metrics_store(self) -> EndpointMetricsStore:
        """Acceso al almacén de métricas."""
        return self._metrics_store

    @contextmanager
    def measure(
        self,
        operation: str,
        **context: Any,
    ) -> Generator[None, None, None]:
        """Context manager para medir duración de operaciones.

        Registra el tiempo de ejecución de un bloque de código y lo loggea
        con información de contexto adicional.

        Args:
            operation: Nombre de la operación a medir.
            **context: Datos adicionales de contexto para el log.

        Yields:
            None

        Example:
            >>> with perf_logger.measure("fetch_users", project_id=123):
            ...     users = await fetch_users_from_db()
        """
        correlation_id = CorrelationIdManager.ensure_correlation_id()
        start = time.perf_counter()
        success = True
        error_info: str | None = None

        try:
            yield
        except Exception as e:
            success = False
            error_info = f"{type(e).__name__}: {e}"
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000

            # Preparar datos del log
            log_data: dict[str, Any] = {
                "operation": operation,
                "duration_ms": round(duration_ms, 2),
                "correlation_id": correlation_id,
                "success": success,
            }
            log_data.update(context)

            if error_info:
                log_data["error"] = error_info

            # Log estructurado
            if success:
                self._logger.info(
                    "[PERF] %s completed in %.2fms",
                    operation,
                    duration_ms,
                    extra={"extra_data": log_data},
                )
            else:
                self._logger.warning(
                    "[PERF] %s failed after %.2fms: %s",
                    operation,
                    duration_ms,
                    error_info,
                    extra={"extra_data": log_data},
                )

            # Registrar métricas
            self._metrics_store.record(operation, duration_ms, success)

    def log_api_call(
        self,
        method: str,
        endpoint: str,
        duration_ms: float,
        status_code: int,
        *,
        request_size: int | None = None,
        response_size: int | None = None,
        error: str | None = None,
    ) -> None:
        """Log específico para llamadas API.

        Registra información detallada de una llamada HTTP incluyendo
        método, endpoint, tiempo de respuesta y código de estado.

        Args:
            method: Método HTTP (GET, POST, etc.).
            endpoint: URL o path del endpoint.
            duration_ms: Duración de la llamada en milisegundos.
            status_code: Código de estado HTTP de la respuesta.
            request_size: Tamaño del request en bytes (opcional).
            response_size: Tamaño de la respuesta en bytes (opcional).
            error: Mensaje de error si ocurrió uno (opcional).
        """
        correlation_id = CorrelationIdManager.get() or "-"
        success = 200 <= status_code < 400

        log_data: dict[str, Any] = {
            "method": method,
            "endpoint": endpoint,
            "duration_ms": round(duration_ms, 2),
            "status_code": status_code,
            "correlation_id": correlation_id,
            "success": success,
        }

        if request_size is not None:
            log_data["request_size_bytes"] = request_size
        if response_size is not None:
            log_data["response_size_bytes"] = response_size
        if error:
            log_data["error"] = error

        # Formatear mensaje legible
        msg = f"[API] {method} {endpoint} -> {status_code} ({duration_ms:.2f}ms)"

        if success:
            self._logger.info(msg, extra={"extra_data": log_data})
        else:
            self._logger.warning(msg, extra={"extra_data": log_data})

        # Registrar métricas por endpoint
        endpoint_key = f"{method} {endpoint}"
        self._metrics_store.record(endpoint_key, duration_ms, success)

    def get_metrics_summary(self) -> dict[str, dict[str, Any]]:
        """Obtiene resumen de todas las métricas registradas.

        Returns:
            Diccionario con métricas agregadas por operación/endpoint.
        """
        return self._metrics_store.get_all_metrics()

    def reset_metrics(self) -> None:
        """Reinicia todas las métricas almacenadas."""
        self._metrics_store.reset()


# Singleton global para uso compartido
_global_perf_logger: PerformanceLogger | None = None


def get_performance_logger() -> PerformanceLogger:
    """Obtiene la instancia global del PerformanceLogger.

    Returns:
        Instancia singleton de PerformanceLogger.
    """
    global _global_perf_logger
    if _global_perf_logger is None:
        _global_perf_logger = PerformanceLogger()
    return _global_perf_logger


def reset_performance_logger() -> None:
    """Reinicia el PerformanceLogger global (útil para testing)."""
    global _global_perf_logger
    if _global_perf_logger is not None:
        _global_perf_logger.reset_metrics()
    _global_perf_logger = None
