"""Tests para el sistema de métricas.

Este módulo contiene tests unitarios para el sistema de métricas
del servidor, verificando registro de métricas, snapshots,
thread-safety y cálculo de tasas de caché.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pytest

from src.infrastructure.metrics import (
    MetricsCollector,
    MetricsSnapshot,
    RequestRecord,
    get_metrics_collector,
    reset_metrics_collector,
)


class TestMetricsSnapshot:
    """Tests para MetricsSnapshot."""

    def test_create_snapshot(self) -> None:
        """Test 3.9.2: Snapshot se crea con todos los campos."""
        snapshot = MetricsSnapshot(
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            avg_response_time_ms=150.5,
            cache_hit_rate=0.75,
            requests_by_endpoint={"projects": 50, "epics": 50},
            errors_by_type={"Timeout": 3, "ValidationError": 2},
            timestamp=datetime.now(),
        )

        assert snapshot.total_requests == 100
        assert snapshot.successful_requests == 95
        assert snapshot.failed_requests == 5
        assert snapshot.avg_response_time_ms == 150.5
        assert snapshot.cache_hit_rate == 0.75
        assert snapshot.requests_by_endpoint == {"projects": 50, "epics": 50}
        assert snapshot.errors_by_type == {"Timeout": 3, "ValidationError": 2}
        assert isinstance(snapshot.timestamp, datetime)

    def test_snapshot_is_frozen(self) -> None:
        """Test que snapshot es inmutable (frozen)."""
        snapshot = MetricsSnapshot(
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            avg_response_time_ms=150.5,
            cache_hit_rate=0.75,
            requests_by_endpoint={},
            errors_by_type={},
            timestamp=datetime.now(),
        )

        with pytest.raises(AttributeError):
            snapshot.total_requests = 200  # type: ignore[misc]

    def test_snapshot_hash(self) -> None:
        """Test que snapshot es hashable."""
        snapshot = MetricsSnapshot(
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            avg_response_time_ms=150.5,
            cache_hit_rate=0.75,
            requests_by_endpoint={},
            errors_by_type={},
            timestamp=datetime.now(),
        )

        # Debe poder usarse como clave en dict o en set
        assert isinstance(hash(snapshot), int)
        snapshot_set = {snapshot}
        assert snapshot in snapshot_set


class TestRequestRecord:
    """Tests para RequestRecord."""

    def test_create_request_record(self) -> None:
        """Test creación de registro de request."""
        record = RequestRecord(
            endpoint="projects",
            method="GET",
            duration_ms=150.0,
            success=True,
        )

        assert record.endpoint == "projects"
        assert record.method == "GET"
        assert record.duration_ms == 150.0
        assert record.success is True
        assert isinstance(record.timestamp, datetime)

    def test_request_record_with_custom_timestamp(self) -> None:
        """Test registro con timestamp personalizado."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        record = RequestRecord(
            endpoint="epics",
            method="POST",
            duration_ms=200.0,
            success=False,
            timestamp=custom_time,
        )

        assert record.timestamp == custom_time


class TestMetricsCollector:
    """Tests para MetricsCollector."""

    @pytest.fixture
    def collector(self) -> MetricsCollector:
        """Fixture que crea un collector limpio."""
        return MetricsCollector()

    def test_initial_state(self, collector: MetricsCollector) -> None:
        """Test estado inicial del collector."""
        snapshot = collector.get_snapshot()

        assert snapshot.total_requests == 0
        assert snapshot.successful_requests == 0
        assert snapshot.failed_requests == 0
        assert snapshot.avg_response_time_ms == 0.0
        assert snapshot.cache_hit_rate == 0.0
        assert snapshot.requests_by_endpoint == {}
        assert snapshot.errors_by_type == {}

    def test_record_request_success(self, collector: MetricsCollector) -> None:
        """Test 3.9.1: Registrar request exitoso."""
        collector.record_request("projects", "GET", 150.0, True)

        snapshot = collector.get_snapshot()
        assert snapshot.total_requests == 1
        assert snapshot.successful_requests == 1
        assert snapshot.failed_requests == 0
        assert snapshot.avg_response_time_ms == 150.0
        assert snapshot.requests_by_endpoint == {"projects": 1}

    def test_record_request_failure(self, collector: MetricsCollector) -> None:
        """Test 3.9.1: Registrar request fallido."""
        collector.record_request("epics", "POST", 200.0, False)

        snapshot = collector.get_snapshot()
        assert snapshot.total_requests == 1
        assert snapshot.successful_requests == 0
        assert snapshot.failed_requests == 1

    def test_record_multiple_requests(self, collector: MetricsCollector) -> None:
        """Test 3.9.1: Registrar múltiples requests."""
        collector.record_request("projects", "GET", 100.0, True)
        collector.record_request("projects", "GET", 200.0, True)
        collector.record_request("epics", "POST", 300.0, False)

        snapshot = collector.get_snapshot()
        assert snapshot.total_requests == 3
        assert snapshot.successful_requests == 2
        assert snapshot.failed_requests == 1
        assert snapshot.avg_response_time_ms == 200.0  # (100 + 200 + 300) / 3
        assert snapshot.requests_by_endpoint == {"projects": 2, "epics": 1}

    def test_record_error(self, collector: MetricsCollector) -> None:
        """Test 3.9.1: Registrar errores por tipo."""
        collector.record_error("Timeout")
        collector.record_error("Timeout")
        collector.record_error("ValidationError")

        snapshot = collector.get_snapshot()
        assert snapshot.errors_by_type == {"Timeout": 2, "ValidationError": 1}

    def test_record_cache_hit(self, collector: MetricsCollector) -> None:
        """Test 3.9.4: Registrar aciertos de caché."""
        collector.record_cache_hit()
        collector.record_cache_hit()
        collector.record_cache_hit()

        hits, misses, rate = collector.get_cache_stats()
        assert hits == 3
        assert misses == 0
        assert rate == 1.0

    def test_record_cache_miss(self, collector: MetricsCollector) -> None:
        """Test 3.9.4: Registrar fallos de caché."""
        collector.record_cache_miss()
        collector.record_cache_miss()

        hits, misses, rate = collector.get_cache_stats()
        assert hits == 0
        assert misses == 2
        assert rate == 0.0

    def test_cache_hit_rate_calculation(self, collector: MetricsCollector) -> None:
        """Test 3.9.4: Cálculo correcto de cache hit rate."""
        # 3 hits, 1 miss = 75% hit rate
        collector.record_cache_hit()
        collector.record_cache_hit()
        collector.record_cache_hit()
        collector.record_cache_miss()

        snapshot = collector.get_snapshot()
        assert snapshot.cache_hit_rate == 0.75

        hits, misses, rate = collector.get_cache_stats()
        assert hits == 3
        assert misses == 1
        assert rate == 0.75

    def test_cache_hit_rate_empty(self, collector: MetricsCollector) -> None:
        """Test 3.9.4: Hit rate con sin operaciones de caché."""
        snapshot = collector.get_snapshot()
        assert snapshot.cache_hit_rate == 0.0

    def test_snapshot_reflects_current_state(self, collector: MetricsCollector) -> None:
        """Test 3.9.2: Snapshot refleja estado actual correctamente."""
        # Estado inicial
        snapshot1 = collector.get_snapshot()
        assert snapshot1.total_requests == 0

        # Agregar datos
        collector.record_request("projects", "GET", 100.0, True)
        collector.record_cache_hit()
        collector.record_error("Timeout")

        # Nuevo snapshot debe reflejar cambios
        snapshot2 = collector.get_snapshot()
        assert snapshot2.total_requests == 1
        assert snapshot2.successful_requests == 1
        assert snapshot2.errors_by_type == {"Timeout": 1}

        # Timestamps diferentes
        assert snapshot1.timestamp != snapshot2.timestamp

    def test_reset(self, collector: MetricsCollector) -> None:
        """Test que reset limpia todas las métricas."""
        collector.record_request("projects", "GET", 100.0, True)
        collector.record_cache_hit()
        collector.record_error("Timeout")

        collector.reset()

        snapshot = collector.get_snapshot()
        assert snapshot.total_requests == 0
        assert snapshot.cache_hit_rate == 0.0
        assert snapshot.errors_by_type == {}

    def test_get_request_count(self, collector: MetricsCollector) -> None:
        """Test obtener conteo de requests."""
        assert collector.get_request_count() == 0

        collector.record_request("projects", "GET", 100.0, True)
        assert collector.get_request_count() == 1

        collector.record_request("epics", "POST", 200.0, False)
        assert collector.get_request_count() == 2

    def test_get_error_count_by_type(self, collector: MetricsCollector) -> None:
        """Test obtener conteo de errores por tipo."""
        collector.record_error("Timeout")
        collector.record_error("Timeout")
        collector.record_error("ValidationError")

        assert collector.get_error_count("Timeout") == 2
        assert collector.get_error_count("ValidationError") == 1
        assert collector.get_error_count("NotFound") == 0

    def test_get_error_count_total(self, collector: MetricsCollector) -> None:
        """Test obtener conteo total de errores."""
        collector.record_error("Timeout")
        collector.record_error("Timeout")
        collector.record_error("ValidationError")

        assert collector.get_error_count() == 3


class TestMetricsCollectorThreadSafety:
    """Tests de thread-safety para MetricsCollector."""

    def test_concurrent_record_requests(self) -> None:
        """Test 3.9.3: Thread-safe bajo concurrencia - requests."""
        collector = MetricsCollector()
        num_threads = 10
        requests_per_thread = 100

        def record_requests(thread_id: int) -> None:
            for i in range(requests_per_thread):
                collector.record_request(
                    endpoint=f"endpoint_{thread_id}",
                    method="GET",
                    duration_ms=float(i),
                    success=True,
                )

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(record_requests, i) for i in range(num_threads)]
            for future in futures:
                future.result()

        snapshot = collector.get_snapshot()
        expected_total = num_threads * requests_per_thread
        assert snapshot.total_requests == expected_total

    def test_concurrent_record_errors(self) -> None:
        """Test 3.9.3: Thread-safe bajo concurrencia - errores."""
        collector = MetricsCollector()
        num_threads = 10
        errors_per_thread = 100

        def record_errors(thread_id: int) -> None:
            for _ in range(errors_per_thread):
                collector.record_error(f"Error_{thread_id}")

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(record_errors, i) for i in range(num_threads)]
            for future in futures:
                future.result()

        total_errors = collector.get_error_count()
        expected_total = num_threads * errors_per_thread
        assert total_errors == expected_total

    def test_concurrent_cache_operations(self) -> None:
        """Test 3.9.3: Thread-safe bajo concurrencia - cache."""
        collector = MetricsCollector()
        num_threads = 10
        operations_per_thread = 100

        def record_cache_ops(thread_id: int) -> None:
            for i in range(operations_per_thread):
                if i % 2 == 0:
                    collector.record_cache_hit()
                else:
                    collector.record_cache_miss()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(record_cache_ops, i) for i in range(num_threads)]
            for future in futures:
                future.result()

        hits, misses, rate = collector.get_cache_stats()
        expected_per_type = (num_threads * operations_per_thread) // 2
        assert hits == expected_per_type
        assert misses == expected_per_type
        assert rate == 0.5

    def test_concurrent_mixed_operations(self) -> None:
        """Test 3.9.3: Thread-safety con operaciones mixtas."""
        collector = MetricsCollector()
        num_threads = 5
        operations_per_thread = 50

        def mixed_operations(thread_id: int) -> None:
            for _i in range(operations_per_thread):
                collector.record_request(
                    endpoint=f"endpoint_{thread_id}",
                    method="GET",
                    duration_ms=100.0,
                    success=True,
                )
                collector.record_error("Error")
                collector.record_cache_hit()
                collector.record_cache_miss()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(mixed_operations, i) for i in range(num_threads)]
            for future in futures:
                future.result()

        snapshot = collector.get_snapshot()
        expected_requests = num_threads * operations_per_thread
        expected_errors = num_threads * operations_per_thread

        assert snapshot.total_requests == expected_requests
        assert snapshot.errors_by_type == {"Error": expected_errors}
        assert snapshot.cache_hit_rate == 0.5

    def test_concurrent_snapshot_reads(self) -> None:
        """Test 3.9.3: Thread-safety al leer snapshots concurrentemente."""
        collector = MetricsCollector()

        # Pre-cargar algunos datos
        for _i in range(100):
            collector.record_request("test", "GET", 100.0, True)
            collector.record_cache_hit()

        snapshots: list[MetricsSnapshot] = []
        lock = threading.Lock()

        def read_snapshot() -> None:
            snapshot = collector.get_snapshot()
            with lock:
                snapshots.append(snapshot)

        threads = [threading.Thread(target=read_snapshot) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Todas las lecturas deben ser consistentes
        for snapshot in snapshots:
            assert snapshot.total_requests == 100
            assert snapshot.cache_hit_rate == 1.0


class TestMetricsCollectorSingleton:
    """Tests para el patrón singleton del MetricsCollector."""

    def test_get_metrics_collector_singleton(self) -> None:
        """Test que get_metrics_collector retorna siempre la misma instancia."""
        reset_metrics_collector()

        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        assert collector1 is collector2

    def test_reset_metrics_collector(self) -> None:
        """Test que reset_metrics_collector crea nueva instancia."""
        reset_metrics_collector()

        collector1 = get_metrics_collector()
        collector1.record_request("test", "GET", 100.0, True)

        reset_metrics_collector()
        collector2 = get_metrics_collector()

        # Nueva instancia debe estar limpia
        assert collector2.get_request_count() == 0

    def test_singleton_thread_safe(self) -> None:
        """Test que el singleton es thread-safe."""
        reset_metrics_collector()
        collectors: list[MetricsCollector] = []
        lock = threading.Lock()

        def get_collector() -> None:
            collector = get_metrics_collector()
            with lock:
                collectors.append(collector)

        threads = [threading.Thread(target=get_collector) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Todas las referencias deben ser al mismo objeto
        first = collectors[0]
        for c in collectors[1:]:
            assert c is first


class TestMetricsIntegration:
    """Tests de integración para el sistema de métricas."""

    def test_full_workflow(self) -> None:
        """Test flujo completo de uso de métricas."""
        collector = MetricsCollector()

        # Simular actividad típica
        endpoints = ["projects", "epics", "user_stories", "tasks"]
        for i, endpoint in enumerate(endpoints):
            # Requests
            collector.record_request(endpoint, "GET", 100.0 + i * 10, True)
            collector.record_request(endpoint, "POST", 200.0 + i * 10, True)
            if i % 2 == 0:
                collector.record_request(endpoint, "DELETE", 50.0, False)
                collector.record_error("PermissionDenied")

            # Cache
            collector.record_cache_hit()
            if i % 3 == 0:
                collector.record_cache_miss()

        snapshot = collector.get_snapshot()

        # Verificar totales
        assert snapshot.total_requests == 10  # 4*2 + 2 failed
        assert snapshot.successful_requests == 8
        assert snapshot.failed_requests == 2
        assert snapshot.errors_by_type == {"PermissionDenied": 2}

        # Verificar distribución por endpoint
        assert "projects" in snapshot.requests_by_endpoint
        assert "epics" in snapshot.requests_by_endpoint

        # Verificar cache (4 hits, 2 misses para i=0,3)
        assert 0.0 < snapshot.cache_hit_rate < 1.0

    def test_time_series_tracking(self) -> None:
        """Test que timestamps se registran correctamente."""
        collector = MetricsCollector()

        snapshot1 = collector.get_snapshot()
        time.sleep(0.01)  # Pequeña pausa
        snapshot2 = collector.get_snapshot()

        assert snapshot2.timestamp > snapshot1.timestamp
