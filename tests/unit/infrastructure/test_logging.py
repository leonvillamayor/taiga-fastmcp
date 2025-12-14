"""
Tests para el sistema de logging de performance.

Este módulo verifica:
- Test 3.8.1: Log de operación incluye duración
- Test 3.8.2: Log de API incluye método, endpoint, status
- Test 3.8.3: Formato JSON correcto
- Test 3.8.4: No impacta performance significativamente
"""

import json
import logging
import time

import pytest

from src.infrastructure.logging.config import LoggingConfig, LogLevel
from src.infrastructure.logging.correlation import CorrelationIdManager
from src.infrastructure.logging.logger import (
    TaigaLogFormatter,
    get_logger,
    reset_logging,
    setup_logging,
)
from src.infrastructure.logging.performance import (
    APIMetrics,
    EndpointMetricsStore,
    PerformanceLogger,
    get_performance_logger,
    reset_performance_logger,
)


class TestAPIMetrics:
    """Tests para la clase APIMetrics."""

    def test_initial_values(self) -> None:
        """Test valores iniciales de APIMetrics."""
        metrics = APIMetrics()
        assert metrics.total_calls == 0
        assert metrics.total_duration_ms == 0.0
        assert metrics.min_duration_ms == float("inf")
        assert metrics.max_duration_ms == 0.0
        assert metrics.success_count == 0
        assert metrics.error_count == 0

    def test_avg_duration_zero_calls(self) -> None:
        """Test duración promedio con cero llamadas."""
        metrics = APIMetrics()
        assert metrics.avg_duration_ms == 0.0

    def test_avg_duration_with_calls(self) -> None:
        """Test duración promedio con llamadas."""
        metrics = APIMetrics(total_calls=10, total_duration_ms=1000.0)
        assert metrics.avg_duration_ms == 100.0

    def test_success_rate_zero_calls(self) -> None:
        """Test tasa de éxito con cero llamadas."""
        metrics = APIMetrics()
        assert metrics.success_rate == 0.0

    def test_success_rate_with_calls(self) -> None:
        """Test tasa de éxito con llamadas."""
        metrics = APIMetrics(total_calls=10, success_count=8)
        assert metrics.success_rate == 0.8

    def test_to_dict(self) -> None:
        """Test conversión a diccionario."""
        metrics = APIMetrics(
            total_calls=5,
            total_duration_ms=500.0,
            min_duration_ms=50.0,
            max_duration_ms=150.0,
            success_count=4,
            error_count=1,
        )
        result = metrics.to_dict()
        assert result["total_calls"] == 5
        assert result["total_duration_ms"] == 500.0
        assert result["avg_duration_ms"] == 100.0
        assert result["min_duration_ms"] == 50.0
        assert result["max_duration_ms"] == 150.0
        assert result["success_count"] == 4
        assert result["error_count"] == 1
        assert result["success_rate"] == 0.8

    def test_to_dict_handles_infinity(self) -> None:
        """Test que to_dict maneja infinito en min_duration_ms."""
        metrics = APIMetrics()
        result = metrics.to_dict()
        assert result["min_duration_ms"] == 0.0


class TestEndpointMetricsStore:
    """Tests para EndpointMetricsStore."""

    def test_record_success(self) -> None:
        """Test registro de operación exitosa."""
        store = EndpointMetricsStore()
        store.record("/api/test", 100.0, success=True)

        metrics = store.get_metrics("/api/test")
        assert metrics.total_calls == 1
        assert metrics.success_count == 1
        assert metrics.error_count == 0
        assert metrics.min_duration_ms == 100.0
        assert metrics.max_duration_ms == 100.0

    def test_record_failure(self) -> None:
        """Test registro de operación fallida."""
        store = EndpointMetricsStore()
        store.record("/api/test", 200.0, success=False)

        metrics = store.get_metrics("/api/test")
        assert metrics.total_calls == 1
        assert metrics.success_count == 0
        assert metrics.error_count == 1

    def test_record_multiple(self) -> None:
        """Test múltiples registros actualizan correctamente las métricas."""
        store = EndpointMetricsStore()
        store.record("/api/test", 50.0, success=True)
        store.record("/api/test", 150.0, success=True)
        store.record("/api/test", 100.0, success=False)

        metrics = store.get_metrics("/api/test")
        assert metrics.total_calls == 3
        assert metrics.success_count == 2
        assert metrics.error_count == 1
        assert metrics.min_duration_ms == 50.0
        assert metrics.max_duration_ms == 150.0
        assert metrics.total_duration_ms == 300.0

    def test_get_all_metrics(self) -> None:
        """Test obtener todas las métricas."""
        store = EndpointMetricsStore()
        store.record("/api/a", 100.0, success=True)
        store.record("/api/b", 200.0, success=True)

        all_metrics = store.get_all_metrics()
        assert "/api/a" in all_metrics
        assert "/api/b" in all_metrics
        assert all_metrics["/api/a"]["total_calls"] == 1
        assert all_metrics["/api/b"]["total_calls"] == 1

    def test_reset(self) -> None:
        """Test reset de métricas."""
        store = EndpointMetricsStore()
        store.record("/api/test", 100.0, success=True)
        store.reset()

        all_metrics = store.get_all_metrics()
        assert len(all_metrics) == 0


class TestPerformanceLogger:
    """Tests para PerformanceLogger."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Setup para cada test."""
        reset_performance_logger()
        reset_logging()
        CorrelationIdManager.reset()

    @pytest.fixture
    def propagating_logger(self) -> logging.Logger:
        """Crea un logger que propaga logs (para caplog)."""
        logger = logging.getLogger("test_perf_logger")
        logger.setLevel(logging.DEBUG)
        logger.propagate = True
        return logger

    def test_measure_logs_duration(
        self, caplog: pytest.LogCaptureFixture, propagating_logger: logging.Logger
    ) -> None:
        """Test 3.8.1: Log de operación incluye duración."""
        perf_logger = PerformanceLogger(logger=propagating_logger)

        with caplog.at_level(logging.INFO), perf_logger.measure("test_operation"):
            time.sleep(0.01)  # 10ms mínimo

        # Verificar que hay un log con la duración
        assert len(caplog.records) >= 1
        log_record = caplog.records[-1]
        assert "test_operation" in log_record.message
        assert "ms" in log_record.message
        assert "[PERF]" in log_record.message

    def test_measure_includes_context(
        self, caplog: pytest.LogCaptureFixture, propagating_logger: logging.Logger
    ) -> None:
        """Test que measure incluye contexto adicional."""
        perf_logger = PerformanceLogger(logger=propagating_logger)

        with (
            caplog.at_level(logging.INFO),
            perf_logger.measure("query", table="users", project_id=123),
        ):
            pass

        assert len(caplog.records) >= 1
        # El contexto se incluye en extra_data del log
        log_record = caplog.records[-1]
        assert "query" in log_record.message

    def test_measure_on_exception(
        self, caplog: pytest.LogCaptureFixture, propagating_logger: logging.Logger
    ) -> None:
        """Test que measure registra errores correctamente."""
        perf_logger = PerformanceLogger(logger=propagating_logger)

        with (
            caplog.at_level(logging.WARNING),
            pytest.raises(ValueError),
            perf_logger.measure("failing_operation"),
        ):
            raise ValueError("Test error")

        # Debe haber un log de warning con el error
        assert len(caplog.records) >= 1
        log_record = caplog.records[-1]
        assert "failing_operation" in log_record.message
        assert "failed" in log_record.message.lower()

    def test_log_api_call_includes_method_endpoint_status(
        self, caplog: pytest.LogCaptureFixture, propagating_logger: logging.Logger
    ) -> None:
        """Test 3.8.2: Log de API incluye método, endpoint, status."""
        perf_logger = PerformanceLogger(logger=propagating_logger)

        with caplog.at_level(logging.INFO):
            perf_logger.log_api_call(
                method="GET",
                endpoint="/api/v1/projects",
                duration_ms=150.5,
                status_code=200,
            )

        assert len(caplog.records) >= 1
        log_record = caplog.records[-1]
        assert "GET" in log_record.message
        assert "/api/v1/projects" in log_record.message
        assert "200" in log_record.message
        assert "150.50ms" in log_record.message

    def test_log_api_call_with_error(
        self, caplog: pytest.LogCaptureFixture, propagating_logger: logging.Logger
    ) -> None:
        """Test log de API con error."""
        perf_logger = PerformanceLogger(logger=propagating_logger)

        with caplog.at_level(logging.WARNING):
            perf_logger.log_api_call(
                method="POST",
                endpoint="/api/v1/projects",
                duration_ms=50.0,
                status_code=500,
                error="Internal Server Error",
            )

        assert len(caplog.records) >= 1
        log_record = caplog.records[-1]
        assert log_record.levelno == logging.WARNING
        assert "500" in log_record.message

    def test_log_api_call_with_sizes(
        self, caplog: pytest.LogCaptureFixture, propagating_logger: logging.Logger
    ) -> None:
        """Test log de API con tamaños de request/response."""
        perf_logger = PerformanceLogger(logger=propagating_logger)

        with caplog.at_level(logging.INFO):
            perf_logger.log_api_call(
                method="POST",
                endpoint="/api/v1/tasks",
                duration_ms=100.0,
                status_code=201,
                request_size=256,
                response_size=1024,
            )

        assert len(caplog.records) >= 1
        # Los tamaños se incluyen en extra_data

    def test_metrics_aggregation(self) -> None:
        """Test agregación de métricas."""
        perf_logger = PerformanceLogger()

        perf_logger.log_api_call("GET", "/api/test", 100.0, 200)
        perf_logger.log_api_call("GET", "/api/test", 200.0, 200)
        perf_logger.log_api_call("GET", "/api/test", 150.0, 500)

        metrics = perf_logger.get_metrics_summary()
        endpoint_key = "GET /api/test"
        assert endpoint_key in metrics
        assert metrics[endpoint_key]["total_calls"] == 3
        assert metrics[endpoint_key]["success_count"] == 2
        assert metrics[endpoint_key]["error_count"] == 1

    def test_reset_metrics(self) -> None:
        """Test reset de métricas."""
        perf_logger = PerformanceLogger()

        perf_logger.log_api_call("GET", "/api/test", 100.0, 200)
        perf_logger.reset_metrics()

        metrics = perf_logger.get_metrics_summary()
        assert len(metrics) == 0


class TestTaigaLogFormatterJSON:
    """Tests para el formato JSON del logger."""

    def test_json_format_correct(self) -> None:
        """Test 3.8.3: Formato JSON correcto."""
        formatter = TaigaLogFormatter(json_format=True)

        # Crear un log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        # Verificar que es JSON válido
        parsed = json.loads(result)
        assert "timestamp" in parsed
        assert "level" in parsed
        assert parsed["level"] == "INFO"
        assert "message" in parsed
        assert parsed["message"] == "Test message"
        assert "logger" in parsed
        assert "module" in parsed
        assert "function" in parsed
        assert "line" in parsed

    def test_json_format_masks_sensitive_data(self) -> None:
        """Test que el formato JSON enmascara datos sensibles."""
        formatter = TaigaLogFormatter(json_format=True)

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Auth attempt",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"username": "john", "password": "secret123"}

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "extra" in parsed
        assert parsed["extra"]["username"] == "john"
        assert parsed["extra"]["password"] == "***MASKED***"

    def test_json_format_includes_correlation_id(self) -> None:
        """Test que el formato JSON incluye correlation_id."""
        formatter = TaigaLogFormatter(json_format=True)

        # Establecer correlation ID
        with CorrelationIdManager.context("test-correlation-123"):
            record = logging.LogRecord(
                name="test_logger",
                level=logging.INFO,
                pathname="test.py",
                lineno=42,
                msg="Test with correlation",
                args=(),
                exc_info=None,
            )

            result = formatter.format(record)
            parsed = json.loads(result)

            assert "correlation_id" in parsed
            assert parsed["correlation_id"] == "test-correlation-123"


class TestPerformanceOverhead:
    """Tests de overhead de performance."""

    def test_logging_overhead_minimal(self) -> None:
        """Test 3.8.4: No impacta performance significativamente (< 1ms)."""
        perf_logger = PerformanceLogger()

        # Medir tiempo de log_api_call
        iterations = 1000
        start = time.perf_counter()

        for i in range(iterations):
            perf_logger.log_api_call(
                method="GET",
                endpoint=f"/api/test/{i}",
                duration_ms=100.0,
                status_code=200,
            )

        total_time_ms = (time.perf_counter() - start) * 1000
        avg_overhead_ms = total_time_ms / iterations

        # El overhead promedio debe ser < 1ms por request
        assert avg_overhead_ms < 1.0, f"Overhead promedio: {avg_overhead_ms:.3f}ms (debe ser < 1ms)"

    def test_measure_context_manager_overhead(self) -> None:
        """Test overhead del context manager measure."""
        perf_logger = PerformanceLogger()

        # Medir overhead del context manager vacío
        iterations = 1000
        start = time.perf_counter()

        for _ in range(iterations):
            with perf_logger.measure("test_op"):
                pass  # Operación vacía

        total_time_ms = (time.perf_counter() - start) * 1000
        avg_overhead_ms = total_time_ms / iterations

        # El overhead del context manager debe ser < 1ms
        assert avg_overhead_ms < 1.0, f"Overhead promedio: {avg_overhead_ms:.3f}ms (debe ser < 1ms)"


class TestGlobalPerformanceLogger:
    """Tests para el singleton global."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Reset del logger global antes de cada test."""
        reset_performance_logger()

    def test_get_performance_logger_singleton(self) -> None:
        """Test que get_performance_logger retorna singleton."""
        logger1 = get_performance_logger()
        logger2 = get_performance_logger()
        assert logger1 is logger2

    def test_reset_performance_logger(self) -> None:
        """Test que reset_performance_logger limpia el singleton."""
        logger1 = get_performance_logger()
        logger1.log_api_call("GET", "/test", 100.0, 200)

        reset_performance_logger()

        logger2 = get_performance_logger()
        assert logger1 is not logger2
        assert len(logger2.get_metrics_summary()) == 0


class TestCorrelationIdManager:
    """Tests para CorrelationIdManager."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Reset correlation ID antes de cada test."""
        CorrelationIdManager.reset()

    def test_generate_unique_ids(self) -> None:
        """Test que generate produce IDs únicos."""
        ids = {CorrelationIdManager.generate() for _ in range(100)}
        assert len(ids) == 100  # Todos deben ser únicos

    def test_context_manager_sets_and_resets(self) -> None:
        """Test que el context manager establece y restaura el ID."""
        assert CorrelationIdManager.get() == ""

        with CorrelationIdManager.context("test-id-123"):
            assert CorrelationIdManager.get() == "test-id-123"

        assert CorrelationIdManager.get() == ""

    def test_ensure_correlation_id_creates_if_missing(self) -> None:
        """Test que ensure_correlation_id crea un ID si no existe."""
        assert CorrelationIdManager.get() == ""

        cid = CorrelationIdManager.ensure_correlation_id()
        assert cid != ""
        assert CorrelationIdManager.get() == cid

    def test_ensure_correlation_id_returns_existing(self) -> None:
        """Test que ensure_correlation_id retorna el ID existente."""
        CorrelationIdManager.set("existing-id")

        cid = CorrelationIdManager.ensure_correlation_id()
        assert cid == "existing-id"


class TestLoggingConfig:
    """Tests para LoggingConfig."""

    def test_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test valores por defecto de LoggingConfig."""
        # Limpiar variables de entorno que podrían afectar la configuración
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        config = LoggingConfig()
        assert config.log_level == LogLevel.INFO
        assert config.log_json is False
        assert config.log_file is None

    def test_get_log_level_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test conversión de nivel de log."""
        # Limpiar variables de entorno que podrían sobrescribir el constructor
        monkeypatch.delenv("LOG_LEVEL", raising=False)

        config = LoggingConfig(log_level=LogLevel.DEBUG)
        assert config.get_log_level_value() == logging.DEBUG

        config = LoggingConfig(log_level=LogLevel.ERROR)
        assert config.get_log_level_value() == logging.ERROR

    def test_sensitive_fields_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test campos sensibles por defecto."""
        monkeypatch.delenv("LOG_SENSITIVE_FIELDS", raising=False)
        config = LoggingConfig()
        assert "password" in config.log_sensitive_fields
        assert "auth_token" in config.log_sensitive_fields
        assert "secret" in config.log_sensitive_fields


class TestSetupLogging:
    """Tests para setup_logging."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Reset logging antes de cada test."""
        reset_logging()

    def test_setup_logging_configures_root_logger(self) -> None:
        """Test que setup_logging configura el logger raíz."""
        config = LoggingConfig(log_level=LogLevel.DEBUG)
        setup_logging(config)

        logger = get_logger("test_module")
        assert logger.name.startswith("taiga_mcp")

    def test_setup_logging_idempotent(self) -> None:
        """Test que setup_logging es idempotente."""
        config = LoggingConfig()
        setup_logging(config)
        setup_logging(config)  # No debe fallar

        # Obtener logger y verificar que funciona
        logger = get_logger("test")
        logger.info("Test message")
