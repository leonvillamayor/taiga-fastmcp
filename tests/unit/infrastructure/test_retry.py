"""Tests unitarios para el sistema de reintentos con backoff exponencial.

Este módulo contiene los tests para verificar el correcto funcionamiento
del decorador de reintentos y la clase RetryableHTTPClient.

Tests incluidos:
- Test 3.6.1: Reintenta en error transitorio
- Test 3.6.2: No reintenta en error definitivo
- Test 3.6.3: Respeta max_retries
- Test 3.6.4: Backoff exponencial correcto
- Test 3.6.5: Jitter añade variabilidad
- Test 3.6.6: Éxito en segundo intento
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.infrastructure.retry import (
    RetryableHTTPClient,
    RetryConfig,
    calculate_delay,
    with_retry,
)


class TestRetryConfig:
    """Tests para la configuración de reintentos."""

    def test_default_config(self) -> None:
        """Test que la configuración por defecto es correcta."""
        config = RetryConfig()

        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert TimeoutError in config.retryable_exceptions
        assert ConnectionError in config.retryable_exceptions
        assert httpx.TimeoutException in config.retryable_exceptions
        assert httpx.ConnectError in config.retryable_exceptions

    def test_custom_config(self) -> None:
        """Test que se pueden especificar valores personalizados."""
        config = RetryConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=30.0,
            exponential_base=3.0,
            jitter=False,
            retryable_exceptions={ValueError},
        )

        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 3.0
        assert config.jitter is False
        assert config.retryable_exceptions == {ValueError}

    def test_invalid_max_retries_raises_error(self) -> None:
        """Test que max_retries negativo lanza ValueError."""
        with pytest.raises(ValueError, match="max_retries debe ser >= 0"):
            RetryConfig(max_retries=-1)

    def test_invalid_base_delay_raises_error(self) -> None:
        """Test que base_delay negativo lanza ValueError."""
        with pytest.raises(ValueError, match="base_delay debe ser >= 0"):
            RetryConfig(base_delay=-1.0)

    def test_invalid_max_delay_raises_error(self) -> None:
        """Test que max_delay < base_delay lanza ValueError."""
        with pytest.raises(ValueError, match="max_delay debe ser >= base_delay"):
            RetryConfig(base_delay=10.0, max_delay=5.0)

    def test_invalid_exponential_base_raises_error(self) -> None:
        """Test que exponential_base < 1 lanza ValueError."""
        with pytest.raises(ValueError, match="exponential_base debe ser >= 1"):
            RetryConfig(exponential_base=0.5)


class TestCalculateDelay:
    """Tests para la función calculate_delay."""

    def test_backoff_exponencial_sin_jitter(self) -> None:
        """Test 3.6.4: Backoff exponencial correcto sin jitter."""
        # Intento 0: 1.0 * (2.0 ** 0) = 1.0
        delay_0 = calculate_delay(
            attempt=0,
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
            jitter=False,
        )
        assert delay_0 == 1.0

        # Intento 1: 1.0 * (2.0 ** 1) = 2.0
        delay_1 = calculate_delay(
            attempt=1,
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
            jitter=False,
        )
        assert delay_1 == 2.0

        # Intento 2: 1.0 * (2.0 ** 2) = 4.0
        delay_2 = calculate_delay(
            attempt=2,
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
            jitter=False,
        )
        assert delay_2 == 4.0

        # Intento 3: 1.0 * (2.0 ** 3) = 8.0
        delay_3 = calculate_delay(
            attempt=3,
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
            jitter=False,
        )
        assert delay_3 == 8.0

    def test_respeta_max_delay(self) -> None:
        """Test que el delay no excede max_delay."""
        # Intento 10: 1.0 * (2.0 ** 10) = 1024.0, pero max_delay=60.0
        delay = calculate_delay(
            attempt=10,
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
            jitter=False,
        )
        assert delay == 60.0

    def test_jitter_añade_variabilidad(self) -> None:
        """Test 3.6.5: Jitter añade variabilidad al delay."""
        delays: list[float] = []

        # Generamos múltiples delays con el mismo intento
        for _ in range(100):
            delay = calculate_delay(
                attempt=2,
                base_delay=1.0,
                max_delay=60.0,
                exponential_base=2.0,
                jitter=True,
            )
            delays.append(delay)

        # El delay base sería 4.0, con jitter debería variar entre 2.0 y 6.0
        # (50% a 150% de 4.0)
        assert min(delays) >= 2.0  # 4.0 * 0.5
        assert max(delays) <= 6.0  # 4.0 * 1.5

        # Verificar que hay variabilidad (no todos los valores son iguales)
        unique_delays = {round(d, 6) for d in delays}
        assert len(unique_delays) > 1


class TestWithRetryDecorator:
    """Tests para el decorador with_retry."""

    @pytest.mark.asyncio
    async def test_exito_sin_reintentos(self) -> None:
        """Test que funciones exitosas no reintentan."""
        call_count = 0

        @with_retry(RetryConfig(max_retries=3))
        async def successful_operation() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_operation()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_reintenta_en_error_transitorio(self) -> None:
        """Test 3.6.1: Reintenta en error transitorio."""
        call_count = 0

        @with_retry(RetryConfig(max_retries=3, base_delay=0.01, jitter=False))
        async def flaky_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("Connection timed out")
            return "success"

        result = await flaky_operation()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_no_reintenta_en_error_definitivo(self) -> None:
        """Test 3.6.2: No reintenta en error definitivo."""
        call_count = 0
        config = RetryConfig(
            max_retries=3,
            retryable_exceptions={TimeoutError},  # ValueError no está incluido
        )

        @with_retry(config)
        async def operation_with_definitive_error() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid argument")

        with pytest.raises(ValueError, match="Invalid argument"):
            await operation_with_definitive_error()

        assert call_count == 1  # Solo un intento, sin reintentos

    @pytest.mark.asyncio
    async def test_respeta_max_retries(self) -> None:
        """Test 3.6.3: Respeta max_retries."""
        call_count = 0
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)

        @with_retry(config)
        async def always_fails() -> str:
            nonlocal call_count
            call_count += 1
            raise TimeoutError("Always times out")

        with pytest.raises(TimeoutError):
            await always_fails()

        # max_retries=2 significa 1 intento inicial + 2 reintentos = 3 llamadas
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_exito_en_segundo_intento(self) -> None:
        """Test 3.6.6: Éxito en segundo intento."""
        call_count = 0

        @with_retry(RetryConfig(max_retries=3, base_delay=0.01, jitter=False))
        async def succeeds_on_second_attempt() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Connection refused")
            return "success"

        result = await succeeds_on_second_attempt()

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_usa_config_por_defecto_si_none(self) -> None:
        """Test que usa RetryConfig por defecto si config es None."""
        call_count = 0

        @with_retry(None)  # type: ignore[arg-type]
        async def operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError()
            return "ok"

        # Patcheamos sleep para que sea rápido
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await operation()

        assert result == "ok"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_decorador_sin_argumentos(self) -> None:
        """Test que el decorador funciona sin pasar config."""
        call_count = 0

        @with_retry()
        async def operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError()
            return "ok"

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await operation()

        assert result == "ok"

    @pytest.mark.asyncio
    async def test_preserva_nombre_funcion(self) -> None:
        """Test que el decorador preserva el nombre de la función."""

        @with_retry()
        async def my_custom_function() -> str:
            return "test"

        assert my_custom_function.__name__ == "my_custom_function"

    @pytest.mark.asyncio
    async def test_logging_en_reintento(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test que se logea correctamente en cada reintento."""
        call_count = 0

        @with_retry(RetryConfig(max_retries=2, base_delay=0.01, jitter=False))
        async def flaky() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("Timeout")
            return "ok"

        with caplog.at_level("WARNING"):
            result = await flaky()

        assert result == "ok"
        # Debe haber loggeado warnings para los reintentos
        warning_logs = [r for r in caplog.records if r.levelname == "WARNING"]
        assert len(warning_logs) >= 1
        assert "Intento" in warning_logs[0].message
        assert "Reintentando" in warning_logs[0].message

    @pytest.mark.asyncio
    async def test_logging_error_cuando_agota_reintentos(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test que se logea error cuando se agotan los reintentos."""

        @with_retry(RetryConfig(max_retries=1, base_delay=0.01, jitter=False))
        async def always_fails() -> str:
            raise TimeoutError("Always fails")

        with caplog.at_level("ERROR"), pytest.raises(TimeoutError):
            await always_fails()

        # Debe haber loggeado el error final
        error_logs = [r for r in caplog.records if r.levelname == "ERROR"]
        assert len(error_logs) >= 1
        assert "reintentos agotados" in error_logs[0].message


class TestRetryableHTTPClient:
    """Tests para la clase RetryableHTTPClient."""

    def test_inicializacion_con_config(self) -> None:
        """Test que se inicializa correctamente con config."""
        config = RetryConfig(max_retries=5)
        client = RetryableHTTPClient(config)

        assert client.config.max_retries == 5

    def test_inicializacion_sin_config(self) -> None:
        """Test que usa config por defecto si no se proporciona."""
        client = RetryableHTTPClient()

        assert client.config.max_retries == 3  # Valor por defecto

    @pytest.mark.asyncio
    async def test_execute_with_retry_exitoso(self) -> None:
        """Test que execute_with_retry funciona correctamente."""
        client = RetryableHTTPClient(RetryConfig(max_retries=3))

        async def successful_op() -> str:
            return "success"

        result = await client.execute_with_retry(successful_op, "test op")
        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_with_retry_reintenta(self) -> None:
        """Test que execute_with_retry reintenta en errores transitorios."""
        client = RetryableHTTPClient(RetryConfig(max_retries=3, base_delay=0.01, jitter=False))
        call_count = 0

        async def flaky_op() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError()
            return "success"

        result = await client.execute_with_retry(flaky_op, "flaky operation")

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_agota_reintentos(self) -> None:
        """Test que execute_with_retry lanza excepción al agotar reintentos."""
        client = RetryableHTTPClient(RetryConfig(max_retries=2, base_delay=0.01, jitter=False))

        async def always_fails() -> str:
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError, match="Always fails"):
            await client.execute_with_retry(always_fails, "failing op")


class TestHTTPXExceptions:
    """Tests para excepciones específicas de httpx."""

    @pytest.mark.asyncio
    async def test_reintenta_en_httpx_timeout(self) -> None:
        """Test que reintenta en httpx.TimeoutException."""
        call_count = 0
        config = RetryConfig(max_retries=3, base_delay=0.01, jitter=False)

        @with_retry(config)
        async def httpx_timeout_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.TimeoutException("Request timed out")
            return "success"

        result = await httpx_timeout_operation()

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_reintenta_en_httpx_connect_error(self) -> None:
        """Test que reintenta en httpx.ConnectError."""
        call_count = 0
        config = RetryConfig(max_retries=3, base_delay=0.01, jitter=False)

        @with_retry(config)
        async def httpx_connect_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.ConnectError("Connection failed")
            return "success"

        result = await httpx_connect_operation()

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_reintenta_en_httpx_network_error(self) -> None:
        """Test que reintenta en httpx.NetworkError."""
        call_count = 0
        config = RetryConfig(max_retries=3, base_delay=0.01, jitter=False)

        @with_retry(config)
        async def httpx_network_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.NetworkError("Network error")
            return "success"

        result = await httpx_network_operation()

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_no_reintenta_en_httpx_http_status_error(self) -> None:
        """Test que NO reintenta en errores HTTP 4xx/5xx por defecto."""
        call_count = 0
        config = RetryConfig(max_retries=3)

        @with_retry(config)
        async def httpx_status_error() -> str:
            nonlocal call_count
            call_count += 1
            request = httpx.Request("GET", "https://example.com")
            response = httpx.Response(404, request=request)
            raise httpx.HTTPStatusError("Not found", request=request, response=response)

        with pytest.raises(httpx.HTTPStatusError):
            await httpx_status_error()

        # Solo un intento porque HTTPStatusError no está en retryable_exceptions
        assert call_count == 1


class TestEdgeCases:
    """Tests para casos límite."""

    @pytest.mark.asyncio
    async def test_zero_retries(self) -> None:
        """Test con max_retries=0 (sin reintentos)."""
        call_count = 0
        config = RetryConfig(max_retries=0)

        @with_retry(config)
        async def operation() -> str:
            nonlocal call_count
            call_count += 1
            raise TimeoutError()

        with pytest.raises(TimeoutError):
            await operation()

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_zero_base_delay(self) -> None:
        """Test con base_delay=0."""
        call_count = 0
        config = RetryConfig(max_retries=2, base_delay=0.0, jitter=False)

        @with_retry(config)
        async def operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError()
            return "ok"

        result = await operation()

        assert result == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_custom_exception_set(self) -> None:
        """Test con set personalizado de excepciones retriables."""
        call_count = 0
        config = RetryConfig(
            max_retries=2,
            base_delay=0.01,
            jitter=False,
            retryable_exceptions={KeyError},  # Solo KeyError es retriable
        )

        @with_retry(config)
        async def operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise KeyError("missing key")
            return "ok"

        result = await operation()

        assert result == "ok"
        assert call_count == 2
