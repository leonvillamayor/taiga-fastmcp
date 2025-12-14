"""Sistema de métricas del servidor.

Este módulo implementa un sistema de recolección de métricas thread-safe
para monitoreo de rendimiento, tasas de error y uso de caché.

Métricas disponibles:
    - total_requests: Número total de requests procesados
    - successful_requests: Requests exitosos
    - failed_requests: Requests fallidos
    - avg_response_time_ms: Tiempo promedio de respuesta en milisegundos
    - cache_hit_rate: Tasa de aciertos de caché (0.0 a 1.0)
    - requests_by_endpoint: Contador de requests por endpoint
    - errors_by_type: Contador de errores por tipo
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock


@dataclass(frozen=True)
class MetricsSnapshot:
    """Snapshot inmutable del estado de métricas.

    Representa el estado de todas las métricas en un momento dado.
    Es inmutable (frozen=True) para garantizar thread-safety al pasar
    entre hilos.

    Attributes:
        total_requests: Número total de requests procesados.
        successful_requests: Número de requests exitosos.
        failed_requests: Número de requests fallidos.
        avg_response_time_ms: Tiempo promedio de respuesta en milisegundos.
        cache_hit_rate: Tasa de aciertos de caché (0.0 a 1.0).
        requests_by_endpoint: Diccionario con conteo de requests por endpoint.
        errors_by_type: Diccionario con conteo de errores por tipo.
        timestamp: Momento en que se generó el snapshot.
    """

    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    cache_hit_rate: float
    requests_by_endpoint: dict[str, int]
    errors_by_type: dict[str, int]
    timestamp: datetime

    def __hash__(self) -> int:
        """Calcula hash basado en timestamp para permitir uso en sets/dicts."""
        return hash(self.timestamp)


@dataclass
class RequestRecord:
    """Registro individual de un request.

    Attributes:
        endpoint: Nombre del endpoint invocado.
        method: Método HTTP o tipo de operación.
        duration_ms: Duración del request en milisegundos.
        success: Si el request fue exitoso.
        timestamp: Momento del request.
    """

    endpoint: str
    method: str
    duration_ms: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)


class MetricsCollector:
    """Recolector de métricas thread-safe.

    Recolecta métricas de uso, rendimiento y errores de forma
    thread-safe usando un Lock. Permite registrar requests,
    aciertos/fallos de caché y errores, así como obtener snapshots
    del estado actual.

    Example:
        >>> collector = MetricsCollector()
        >>> collector.record_request("projects", "GET", 150.5, True)
        >>> collector.record_cache_hit()
        >>> snapshot = collector.get_snapshot()
        >>> print(f"Total requests: {snapshot.total_requests}")
        Total requests: 1

    Attributes:
        _lock: Lock para garantizar thread-safety.
        _requests: Lista de registros de requests.
        _errors: Contador de errores por tipo.
        _cache_hits: Contador de aciertos de caché.
        _cache_misses: Contador de fallos de caché.
    """

    def __init__(self) -> None:
        """Inicializa el recolector de métricas."""
        self._lock = Lock()
        self._requests: list[RequestRecord] = []
        self._errors: dict[str, int] = defaultdict(int)
        self._cache_hits: int = 0
        self._cache_misses: int = 0

    def record_request(
        self,
        endpoint: str,
        method: str,
        duration_ms: float,
        success: bool,
    ) -> None:
        """Registra un request procesado.

        Args:
            endpoint: Nombre del endpoint invocado (ej: "projects", "epics").
            method: Método HTTP o tipo de operación (ej: "GET", "POST").
            duration_ms: Duración del request en milisegundos.
            success: True si el request fue exitoso, False si falló.

        Example:
            >>> collector.record_request("projects", "GET", 150.5, True)
            >>> collector.record_request("epics", "POST", 200.0, False)
        """
        with self._lock:
            self._requests.append(
                RequestRecord(
                    endpoint=endpoint,
                    method=method,
                    duration_ms=duration_ms,
                    success=success,
                    timestamp=datetime.now(),
                )
            )

    def record_error(self, error_type: str) -> None:
        """Registra un error por su tipo.

        Args:
            error_type: Tipo o clase del error (ej: "ValidationError", "Timeout").

        Example:
            >>> collector.record_error("ValidationError")
            >>> collector.record_error("Timeout")
        """
        with self._lock:
            self._errors[error_type] += 1

    def record_cache_hit(self) -> None:
        """Registra un acierto de caché.

        Se llama cuando una operación encuentra el dato en caché
        y no necesita ir al backend.

        Example:
            >>> collector.record_cache_hit()
        """
        with self._lock:
            self._cache_hits += 1

    def record_cache_miss(self) -> None:
        """Registra un fallo de caché.

        Se llama cuando una operación no encuentra el dato en caché
        y debe ir al backend.

        Example:
            >>> collector.record_cache_miss()
        """
        with self._lock:
            self._cache_misses += 1

    def get_snapshot(self) -> MetricsSnapshot:
        """Obtiene un snapshot inmutable del estado actual de métricas.

        Calcula todas las métricas agregadas basándose en los datos
        recolectados hasta el momento.

        Returns:
            MetricsSnapshot con el estado actual de todas las métricas.

        Example:
            >>> snapshot = collector.get_snapshot()
            >>> print(f"Hit rate: {snapshot.cache_hit_rate:.2%}")
            Hit rate: 75.00%
        """
        with self._lock:
            total_requests = len(self._requests)
            successful_requests = sum(1 for r in self._requests if r.success)
            failed_requests = total_requests - successful_requests

            # Calcular tiempo promedio de respuesta
            if total_requests > 0:
                total_duration = sum(r.duration_ms for r in self._requests)
                avg_response_time_ms = total_duration / total_requests
            else:
                avg_response_time_ms = 0.0

            # Calcular tasa de aciertos de caché
            total_cache_ops = self._cache_hits + self._cache_misses
            cache_hit_rate = self._cache_hits / total_cache_ops if total_cache_ops > 0 else 0.0

            # Contar requests por endpoint
            requests_by_endpoint: dict[str, int] = defaultdict(int)
            for request in self._requests:
                requests_by_endpoint[request.endpoint] += 1

            # Copiar errores por tipo
            errors_by_type = dict(self._errors)

            return MetricsSnapshot(
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                avg_response_time_ms=avg_response_time_ms,
                cache_hit_rate=cache_hit_rate,
                requests_by_endpoint=dict(requests_by_endpoint),
                errors_by_type=errors_by_type,
                timestamp=datetime.now(),
            )

    def reset(self) -> None:
        """Resetea todas las métricas a sus valores iniciales.

        Útil para testing o para reiniciar el conteo de métricas
        periódicamente.

        Example:
            >>> collector.record_request("test", "GET", 100.0, True)
            >>> collector.reset()
            >>> snapshot = collector.get_snapshot()
            >>> print(snapshot.total_requests)
            0
        """
        with self._lock:
            self._requests.clear()
            self._errors.clear()
            self._cache_hits = 0
            self._cache_misses = 0

    def get_request_count(self) -> int:
        """Obtiene el número total de requests registrados.

        Returns:
            Número total de requests.

        Example:
            >>> collector.record_request("test", "GET", 100.0, True)
            >>> print(collector.get_request_count())
            1
        """
        with self._lock:
            return len(self._requests)

    def get_error_count(self, error_type: str | None = None) -> int:
        """Obtiene el conteo de errores.

        Args:
            error_type: Si se especifica, retorna solo los errores de ese tipo.
                       Si es None, retorna el total de todos los errores.

        Returns:
            Número de errores (del tipo especificado o total).

        Example:
            >>> collector.record_error("Timeout")
            >>> collector.record_error("Timeout")
            >>> collector.record_error("ValidationError")
            >>> print(collector.get_error_count("Timeout"))
            2
            >>> print(collector.get_error_count())
            3
        """
        with self._lock:
            if error_type is not None:
                return self._errors.get(error_type, 0)
            return sum(self._errors.values())

    def get_cache_stats(self) -> tuple[int, int, float]:
        """Obtiene estadísticas de caché.

        Returns:
            Tupla con (hits, misses, hit_rate).

        Example:
            >>> collector.record_cache_hit()
            >>> collector.record_cache_hit()
            >>> collector.record_cache_miss()
            >>> hits, misses, rate = collector.get_cache_stats()
            >>> print(f"Hits: {hits}, Misses: {misses}, Rate: {rate:.2%}")
            Hits: 2, Misses: 1, Rate: 66.67%
        """
        with self._lock:
            total = self._cache_hits + self._cache_misses
            hit_rate = self._cache_hits / total if total > 0 else 0.0
            return self._cache_hits, self._cache_misses, hit_rate


# Singleton global para uso en toda la aplicación
_metrics_collector: MetricsCollector | None = None
_metrics_lock = Lock()


def get_metrics_collector() -> MetricsCollector:
    """Obtiene la instancia singleton del recolector de métricas.

    Esta función garantiza que solo existe una instancia del
    MetricsCollector en toda la aplicación, usando un patrón
    singleton thread-safe.

    Returns:
        La instancia singleton de MetricsCollector.

    Example:
        >>> collector1 = get_metrics_collector()
        >>> collector2 = get_metrics_collector()
        >>> assert collector1 is collector2
    """
    global _metrics_collector
    if _metrics_collector is None:
        with _metrics_lock:
            if _metrics_collector is None:
                _metrics_collector = MetricsCollector()
    return _metrics_collector


def reset_metrics_collector() -> None:
    """Resetea el singleton del recolector de métricas.

    Útil para testing para asegurar un estado limpio entre tests.

    Example:
        >>> reset_metrics_collector()
        >>> collector = get_metrics_collector()
        >>> print(collector.get_request_count())
        0
    """
    global _metrics_collector
    with _metrics_lock:
        _metrics_collector = None
