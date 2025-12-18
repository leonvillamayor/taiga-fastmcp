"""
Tests para los decoradores de logging.

Este módulo verifica:
- _mask_sensitive_args: Enmascaramiento de argumentos sensibles
- log_operation: Decorador para operaciones generales (async y sync)
- log_api_call: Decorador para llamadas API (async y sync)
- LogContext: Context manager para logs con contexto
"""

import logging

import pytest

from src.infrastructure.logging.config import LoggingConfig, LogLevel
from src.infrastructure.logging.correlation import CorrelationIdManager
from src.infrastructure.logging.decorators import (
    LogContext,
    _mask_sensitive_args,
    log_api_call,
    log_operation,
)
from src.infrastructure.logging.logger import reset_logging, setup_logging


@pytest.fixture(autouse=True)
def setup_logging_for_tests() -> None:
    """Setup logging para capturar logs en tests."""
    reset_logging()
    CorrelationIdManager.reset()
    # Configurar logging con nivel DEBUG y propagación
    config = LoggingConfig(log_level=LogLevel.DEBUG)
    setup_logging(config)
    # Habilitar propagación para caplog
    taiga_logger = logging.getLogger("taiga_mcp")
    taiga_logger.propagate = True
    api_logger = logging.getLogger("api")
    api_logger.propagate = True


class TestMaskSensitiveArgs:
    """Tests para _mask_sensitive_args."""

    def test_mask_password_in_kwargs(self) -> None:
        """Test que password se enmascara."""
        args = ()
        kwargs = {"username": "john", "password": "secret123"}
        sensitive_keys = ["password"]

        _masked_args, masked_kwargs = _mask_sensitive_args(args, kwargs, sensitive_keys)

        assert masked_kwargs["username"] == "john"
        assert masked_kwargs["password"] == "***MASKED***"

    def test_mask_multiple_sensitive_keys(self) -> None:
        """Test que múltiples claves sensibles se enmascaran."""
        args = ()
        kwargs = {"username": "john", "password": "secret", "auth_token": "abc123"}
        sensitive_keys = ["password", "auth_token"]

        _, masked_kwargs = _mask_sensitive_args(args, kwargs, sensitive_keys)

        assert masked_kwargs["username"] == "john"
        assert masked_kwargs["password"] == "***MASKED***"
        assert masked_kwargs["auth_token"] == "***MASKED***"

    def test_case_insensitive_masking(self) -> None:
        """Test que el enmascaramiento es case-insensitive."""
        args = ()
        kwargs = {"PASSWORD": "secret", "Auth_Token": "abc"}
        sensitive_keys = ["password", "auth_token"]

        _, masked_kwargs = _mask_sensitive_args(args, kwargs, sensitive_keys)

        assert masked_kwargs["PASSWORD"] == "***MASKED***"
        assert masked_kwargs["Auth_Token"] == "***MASKED***"

    def test_empty_kwargs(self) -> None:
        """Test con kwargs vacíos."""
        args = (1, 2, 3)
        kwargs: dict = {}
        sensitive_keys = ["password"]

        masked_args, masked_kwargs = _mask_sensitive_args(args, kwargs, sensitive_keys)

        assert masked_args == (1, 2, 3)
        assert masked_kwargs == {}

    def test_no_sensitive_keys(self) -> None:
        """Test sin claves sensibles."""
        args = ()
        kwargs = {"name": "test", "value": 123}
        sensitive_keys: list[str] = []

        _, masked_kwargs = _mask_sensitive_args(args, kwargs, sensitive_keys)

        assert masked_kwargs == kwargs

    def test_args_unchanged(self) -> None:
        """Test que args no se modifican."""
        args = ("arg1", "arg2", 123)
        kwargs = {"password": "secret"}
        sensitive_keys = ["password"]

        masked_args, _ = _mask_sensitive_args(args, kwargs, sensitive_keys)

        assert masked_args == args


class TestLogOperationAsync:
    """Tests para log_operation con funciones async."""

    @pytest.mark.asyncio
    async def test_logs_operation_start_and_end(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que se loguea inicio y fin de operación."""

        @log_operation(operation_name="test_op")
        async def test_func(x: int) -> int:
            return x * 2

        with caplog.at_level(logging.DEBUG, logger="taiga_mcp"):
            result = await test_func(5)

        assert result == 10
        messages = [r.message for r in caplog.records]
        assert any("test_op" in m and "Starting" in m for m in messages)
        assert any("test_op" in m and "Completed" in m for m in messages)

    @pytest.mark.asyncio
    async def test_logs_execution_time(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que se loguea tiempo de ejecución."""

        @log_operation(log_execution_time=True)
        async def slow_func() -> str:
            import asyncio

            await asyncio.sleep(0.01)
            return "done"

        with caplog.at_level(logging.DEBUG, logger="taiga_mcp"):
            await slow_func()

        messages = [r.message for r in caplog.records]
        assert any("duration=" in m for m in messages)

    @pytest.mark.asyncio
    async def test_masks_sensitive_args(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que se enmascaran argumentos sensibles."""

        @log_operation(log_args=True, sensitive_args=["password"])
        async def login(username: str, password: str) -> bool:
            return True

        with caplog.at_level(logging.DEBUG, logger="taiga_mcp"):
            await login(username="john", password="secret123")

        # El password no debe aparecer en los logs
        for record in caplog.records:
            assert "secret123" not in record.message

    @pytest.mark.asyncio
    async def test_logs_result_when_enabled(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que se loguea el resultado cuando está habilitado."""

        @log_operation(log_result=True)
        async def get_data() -> dict:
            return {"status": "ok"}

        with caplog.at_level(logging.DEBUG, logger="taiga_mcp"):
            await get_data()

        messages = [r.message for r in caplog.records]
        assert any("result=" in m for m in messages)

    @pytest.mark.asyncio
    async def test_truncates_large_results(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que resultados grandes se truncan."""

        @log_operation(log_result=True)
        async def get_large_data() -> str:
            return "x" * 500

        with caplog.at_level(logging.DEBUG, logger="taiga_mcp"):
            await get_large_data()

        messages = [r.message for r in caplog.records]
        # El resultado truncado debe tener "..."
        assert any("..." in m for m in messages if "result=" in m)

    @pytest.mark.asyncio
    async def test_logs_error_on_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que se loguean errores."""

        @log_operation()
        async def failing_func() -> None:
            raise ValueError("Test error")

        with caplog.at_level(logging.DEBUG, logger="taiga_mcp"), pytest.raises(ValueError):
            await failing_func()

        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) >= 1
        assert "ValueError" in error_records[0].message
        assert "Test error" in error_records[0].message

    @pytest.mark.asyncio
    async def test_uses_function_name_if_no_operation_name(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test que usa el nombre de la función si no se proporciona operation_name."""

        @log_operation()
        async def my_custom_function() -> int:
            return 42

        with caplog.at_level(logging.DEBUG, logger="taiga_mcp"):
            await my_custom_function()

        messages = [r.message for r in caplog.records]
        assert any("my_custom_function" in m for m in messages)

    @pytest.mark.asyncio
    async def test_ensures_correlation_id(self) -> None:
        """Test que se asegura un correlation ID."""
        CorrelationIdManager.reset()

        @log_operation()
        async def func_with_correlation() -> str:
            return CorrelationIdManager.get()

        cid = await func_with_correlation()
        assert cid != ""


class TestLogOperationSync:
    """Tests para log_operation con funciones síncronas."""

    def test_sync_logs_operation(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que funciones síncronas se loguean correctamente."""

        @log_operation(operation_name="sync_test")
        def sync_func(x: int) -> int:
            return x + 1

        with caplog.at_level(logging.DEBUG, logger="taiga_mcp"):
            result = sync_func(10)

        assert result == 11
        messages = [r.message for r in caplog.records]
        assert any("sync_test" in m and "Starting" in m for m in messages)
        assert any("sync_test" in m and "Completed" in m for m in messages)

    def test_sync_logs_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que errores síncronos se loguean."""

        @log_operation()
        def sync_failing() -> None:
            raise RuntimeError("Sync error")

        with caplog.at_level(logging.DEBUG, logger="taiga_mcp"), pytest.raises(RuntimeError):
            sync_failing()

        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) >= 1
        assert "RuntimeError" in error_records[0].message

    def test_sync_masks_sensitive(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que sync también enmascara datos sensibles."""

        @log_operation(log_args=True)
        def sync_with_token(data: str, auth_token: str) -> str:
            return data

        with caplog.at_level(logging.DEBUG, logger="taiga_mcp"):
            sync_with_token(data="test", auth_token="my-secret-token")

        for record in caplog.records:
            assert "my-secret-token" not in record.message

    def test_sync_logs_result(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que sync loguea resultado cuando está habilitado."""

        @log_operation(log_result=True)
        def sync_with_result() -> dict:
            return {"key": "value"}

        with caplog.at_level(logging.DEBUG, logger="taiga_mcp"):
            sync_with_result()

        messages = [r.message for r in caplog.records]
        assert any("result=" in m for m in messages)

    def test_sync_truncates_large_results(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que resultados grandes se truncan en sync."""

        @log_operation(log_result=True)
        def sync_large_result() -> str:
            return "y" * 500

        with caplog.at_level(logging.DEBUG, logger="taiga_mcp"):
            sync_large_result()

        messages = [r.message for r in caplog.records]
        assert any("..." in m for m in messages if "result=" in m)


class TestLogApiCallAsync:
    """Tests para log_api_call con funciones async."""

    @pytest.mark.asyncio
    async def test_logs_api_method_and_endpoint(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que se loguea método y endpoint."""

        @log_api_call(method="GET", endpoint="/api/projects")
        async def get_projects() -> list:
            return [{"id": 1}, {"id": 2}]

        with caplog.at_level(logging.DEBUG, logger="api"):
            await get_projects()

        messages = [r.message for r in caplog.records]
        assert any("GET" in m and "/api/projects" in m for m in messages)

    @pytest.mark.asyncio
    async def test_extracts_method_from_function_name(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test que extrae método del nombre de función."""

        @log_api_call(endpoint="/api/tasks")
        async def post_task() -> dict:
            return {"id": 1}

        with caplog.at_level(logging.DEBUG, logger="api"):
            await post_task()

        messages = [r.message for r in caplog.records]
        assert any("POST" in m for m in messages)

    @pytest.mark.asyncio
    async def test_extracts_endpoint_from_kwargs(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que extrae endpoint de kwargs."""

        @log_api_call(method="GET")
        async def api_call(endpoint: str) -> dict:
            return {}

        with caplog.at_level(logging.DEBUG, logger="api"):
            await api_call(endpoint="/api/users")

        messages = [r.message for r in caplog.records]
        assert any("/api/users" in m for m in messages)

    @pytest.mark.asyncio
    async def test_extracts_endpoint_from_args(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que extrae endpoint de args posicionales."""

        @log_api_call(method="GET")
        async def api_call(path: str) -> dict:
            return {}

        with caplog.at_level(logging.DEBUG, logger="api"):
            await api_call("/api/items")

        messages = [r.message for r in caplog.records]
        assert any("/api/items" in m for m in messages)

    @pytest.mark.asyncio
    async def test_logs_response_size_for_list(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que loguea cantidad de items para listas."""

        @log_api_call(method="GET", endpoint="/api/items")
        async def get_items() -> list:
            return [1, 2, 3, 4, 5]

        with caplog.at_level(logging.DEBUG, logger="api"):
            await get_items()

        messages = [r.message for r in caplog.records]
        assert any("5 items" in m for m in messages)

    @pytest.mark.asyncio
    async def test_logs_response_when_enabled(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que loguea respuesta cuando está habilitado."""

        @log_api_call(method="GET", endpoint="/api/test", log_response=True)
        async def get_data() -> dict:
            return {"status": "success"}

        with caplog.at_level(logging.DEBUG, logger="api"):
            await get_data()

        messages = [r.message for r in caplog.records]
        assert any("Response:" in m for m in messages)

    @pytest.mark.asyncio
    async def test_logs_request_body_when_enabled(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que loguea body del request cuando está habilitado."""

        @log_api_call(method="POST", endpoint="/api/test", log_request_body=True)
        async def post_data(json: dict) -> dict:
            return {"id": 1}

        with caplog.at_level(logging.DEBUG, logger="api"):
            await post_data(json={"name": "test"})

        messages = [r.message for r in caplog.records]
        assert any("body=" in m for m in messages)

    @pytest.mark.asyncio
    async def test_masks_sensitive_in_body(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que enmascara datos sensibles en el body."""

        @log_api_call(method="POST", endpoint="/auth", log_request_body=True)
        async def authenticate(json: dict) -> dict:
            return {"token": "abc"}

        with caplog.at_level(logging.DEBUG, logger="api"):
            await authenticate(json={"username": "john", "password": "secret123"})

        for record in caplog.records:
            assert "secret123" not in record.message

    @pytest.mark.asyncio
    async def test_logs_error_with_status_code(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que loguea errores con código de status."""

        class APIError(Exception):
            status_code = 404

        @log_api_call(method="GET", endpoint="/api/missing")
        async def get_missing() -> dict:
            raise APIError("Not found")

        with caplog.at_level(logging.DEBUG, logger="api"), pytest.raises(APIError):
            await get_missing()

        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) >= 1
        assert "404" in error_records[0].message

    @pytest.mark.asyncio
    async def test_truncates_large_response(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que trunca respuestas grandes."""

        @log_api_call(method="GET", endpoint="/api/large", log_response=True)
        async def get_large() -> str:
            return "z" * 1000

        with caplog.at_level(logging.DEBUG, logger="api"):
            await get_large()

        messages = [r.message for r in caplog.records]
        assert any("..." in m for m in messages if "Response:" in m)


class TestLogApiCallSync:
    """Tests para log_api_call con funciones síncronas."""

    def test_sync_logs_api_call(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que funciones síncronas de API se loguean."""

        @log_api_call(method="GET", endpoint="/sync/api")
        def sync_get() -> dict:
            return {"data": "test"}

        with caplog.at_level(logging.DEBUG, logger="api"):
            result = sync_get()

        assert result == {"data": "test"}
        messages = [r.message for r in caplog.records]
        assert any("GET" in m and "/sync/api" in m for m in messages)
        assert any("200 OK" in m for m in messages)

    def test_sync_logs_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que errores síncronos se loguean."""

        class SyncAPIError(Exception):
            code = 500

        @log_api_call(method="POST", endpoint="/sync/error")
        def sync_error() -> dict:
            raise SyncAPIError("Server error")

        with caplog.at_level(logging.DEBUG, logger="api"), pytest.raises(SyncAPIError):
            sync_error()

        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) >= 1
        assert "500" in error_records[0].message

    def test_sync_extracts_endpoint_from_kwargs(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que extrae endpoint de kwargs en sync."""

        @log_api_call(method="DELETE")
        def sync_delete(path: str) -> bool:
            return True

        with caplog.at_level(logging.DEBUG, logger="api"):
            sync_delete(path="/api/item/1")

        messages = [r.message for r in caplog.records]
        assert any("/api/item/1" in m for m in messages)


class TestLogContext:
    """Tests para LogContext context manager."""

    def test_context_returns_self(self) -> None:
        """Test que __enter__ retorna self."""
        ctx = LogContext(key="value")
        with ctx as returned:
            assert returned is ctx

    def test_context_stores_values(self) -> None:
        """Test que el contexto almacena valores."""
        ctx = LogContext(user_id=123, project_id=456)
        assert ctx.context == {"user_id": 123, "project_id": 456}

    def test_context_restores_factory(self) -> None:
        """Test que LogContext restaura la factory original."""
        import logging

        original_factory = logging.getLogRecordFactory()

        with LogContext(key="value"):
            # Factory cambia dentro del contexto
            current_factory = logging.getLogRecordFactory()
            assert current_factory != original_factory

        # Factory restaurada después del contexto
        restored_factory = logging.getLogRecordFactory()
        assert restored_factory == original_factory

    def test_context_factory_adds_extra_data(self) -> None:
        """Test que la factory añade extra_data a los records."""
        import logging

        with LogContext(user_id=123, project_id=456):
            # Crear un log record usando la factory (no directamente)
            factory = logging.getLogRecordFactory()
            record = factory(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test",
                args=(),
                exc_info=None,
            )
            # El record debería tener extra_data
            assert hasattr(record, "extra_data")
            assert record.extra_data == {"user_id": 123, "project_id": 456}

    def test_context_with_empty_kwargs(self) -> None:
        """Test contexto con kwargs vacíos."""
        import logging

        with LogContext():
            # Crear un log record usando la factory (no directamente)
            factory = logging.getLogRecordFactory()
            record = factory(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Empty context",
                args=(),
                exc_info=None,
            )
            assert hasattr(record, "extra_data")
            assert record.extra_data == {}


class TestDecoratorIntegration:
    """Tests de integración entre decoradores."""

    @pytest.mark.asyncio
    async def test_log_operation_preserves_function_metadata(self) -> None:
        """Test que el decorador preserva metadatos de la función."""

        @log_operation()
        async def documented_func() -> int:
            """Esta es la documentación."""
            return 42

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "Esta es la documentación."

    @pytest.mark.asyncio
    async def test_log_api_call_preserves_function_metadata(self) -> None:
        """Test que log_api_call preserva metadatos."""

        @log_api_call(method="GET", endpoint="/test")
        async def api_func() -> dict:
            """API documentation."""
            return {}

        assert api_func.__name__ == "api_func"
        assert api_func.__doc__ == "API documentation."

    @pytest.mark.asyncio
    async def test_stacked_decorators(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que decoradores apilados funcionan."""

        @log_operation(operation_name="outer_op")
        @log_api_call(method="GET", endpoint="/inner")
        async def stacked_func() -> dict:
            return {"stacked": True}

        # Habilitar propagación para ambos loggers
        logging.getLogger("taiga_mcp").propagate = True
        logging.getLogger("api").propagate = True

        with caplog.at_level(logging.DEBUG):
            result = await stacked_func()

        assert result == {"stacked": True}
        messages = [r.message for r in caplog.records]
        # Debe haber logs de ambos decoradores
        assert any("outer_op" in m for m in messages)
        assert any("GET" in m and "/inner" in m for m in messages)


class TestEdgeCases:
    """Tests para casos límite."""

    @pytest.mark.asyncio
    async def test_log_operation_with_none_result(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test log_operation con resultado None."""

        @log_operation(log_result=True)
        async def return_none() -> None:
            return None

        with caplog.at_level(logging.DEBUG, logger="taiga_mcp"):
            result = await return_none()

        assert result is None
        # No debe loguear resultado si es None
        messages = [r.message for r in caplog.records]
        assert not any("result=None" in m for m in messages)

    @pytest.mark.asyncio
    async def test_log_operation_without_logging_args(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test log_operation sin loguear args."""

        @log_operation(log_args=False)
        async def no_args_logged(x: int, y: int) -> int:
            return x + y

        with caplog.at_level(logging.DEBUG, logger="taiga_mcp"):
            result = await no_args_logged(5, 10)

        assert result == 15
        # No debe loguear params
        messages = [r.message for r in caplog.records]
        start_messages = [m for m in messages if "Starting" in m]
        assert all("params=" not in m for m in start_messages)

    def test_log_operation_sync_with_default_sensitive_keys(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test que los sensitive keys por defecto funcionan."""

        @log_operation(log_args=True)
        def func_with_secrets(username: str, password: str, token: str, secret: str) -> bool:
            return True

        with caplog.at_level(logging.DEBUG, logger="taiga_mcp"):
            func_with_secrets(
                username="john",
                password="pass123",
                token="tok456",
                secret="sec789",
            )

        for record in caplog.records:
            assert "pass123" not in record.message
            assert "tok456" not in record.message
            assert "sec789" not in record.message
