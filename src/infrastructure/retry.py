"""Sistema de reintentos con backoff exponencial.

Este módulo implementa un decorador para reintentos automáticos con backoff
exponencial y jitter, útil para manejar errores transitorios en operaciones
de red como timeouts y errores de conexión.

Example:
    >>> from src.infrastructure.retry import with_retry, RetryConfig
    >>> import httpx
    >>>
    >>> config = RetryConfig(
    ...     max_retries=3,
    ...     base_delay=1.0,
    ...     retryable_exceptions={httpx.TimeoutException, httpx.ConnectError}
    ... )
    >>>
    >>> @with_retry(config)
    ... async def fetch_data() -> dict:
    ...     async with httpx.AsyncClient() as client:
    ...         response = await client.get("https://api.example.com/data")
    ...         return response.json()
"""

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import ParamSpec, TypeVar

import httpx


# Type variables para preservar tipos de funciones decoradas
P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuración para el sistema de reintentos.

    Attributes:
        max_retries: Número máximo de reintentos (default: 3).
        base_delay: Delay base en segundos entre reintentos (default: 1.0).
        max_delay: Delay máximo en segundos (default: 60.0).
        exponential_base: Base para el cálculo exponencial (default: 2.0).
        jitter: Si añadir variabilidad aleatoria al delay (default: True).
        retryable_exceptions: Set de excepciones que triggean reintentos.

    Example:
        >>> config = RetryConfig(
        ...     max_retries=5,
        ...     base_delay=0.5,
        ...     max_delay=30.0,
        ...     jitter=True
        ... )
        >>> config.max_retries
        5
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: set[type[Exception]] = field(
        default_factory=lambda: {
            TimeoutError,
            ConnectionError,
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.NetworkError,
        }
    )

    def __post_init__(self) -> None:
        """Valida la configuración después de inicialización."""
        if self.max_retries < 0:
            raise ValueError("max_retries debe ser >= 0")
        if self.base_delay < 0:
            raise ValueError("base_delay debe ser >= 0")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay debe ser >= base_delay")
        if self.exponential_base < 1:
            raise ValueError("exponential_base debe ser >= 1")


def calculate_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    exponential_base: float,
    jitter: bool,
) -> float:
    """Calcula el delay para un intento específico.

    Implementa backoff exponencial con jitter opcional.

    Args:
        attempt: Número de intento actual (0-indexed).
        base_delay: Delay base en segundos.
        max_delay: Delay máximo en segundos.
        exponential_base: Base para el cálculo exponencial.
        jitter: Si añadir variabilidad aleatoria.

    Returns:
        Delay calculado en segundos.

    Example:
        >>> delay = calculate_delay(
        ...     attempt=2,
        ...     base_delay=1.0,
        ...     max_delay=60.0,
        ...     exponential_base=2.0,
        ...     jitter=False
        ... )
        >>> delay  # 1.0 * (2.0 ** 2) = 4.0
        4.0
    """
    delay = min(
        base_delay * (exponential_base**attempt),
        max_delay,
    )

    if jitter:
        # Añade variabilidad entre 50% y 150% del delay calculado
        delay *= 0.5 + random.random()

    return delay


def with_retry(
    config: RetryConfig | None = None,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Decorador para reintentos con backoff exponencial.

    Envuelve funciones async para reintentar automáticamente en caso de
    excepciones transitorias configuradas.

    Args:
        config: Configuración de reintentos. Si es None, usa valores por defecto.

    Returns:
        Decorador que envuelve la función con lógica de reintentos.

    Raises:
        Exception: Re-lanza la última excepción después de agotar reintentos.

    Example:
        >>> @with_retry(RetryConfig(max_retries=3))
        ... async def unstable_operation() -> str:
        ...     # Operación que puede fallar transitoriamente
        ...     return "success"
    """
    effective_config = config if config is not None else RetryConfig()
    logger = logging.getLogger(__name__)

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Exception | None = None

            for attempt in range(effective_config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except tuple(effective_config.retryable_exceptions) as e:
                    last_exception = e
                    remaining_retries = effective_config.max_retries - attempt

                    if attempt < effective_config.max_retries:
                        delay = calculate_delay(
                            attempt=attempt,
                            base_delay=effective_config.base_delay,
                            max_delay=effective_config.max_delay,
                            exponential_base=effective_config.exponential_base,
                            jitter=effective_config.jitter,
                        )

                        logger.warning(
                            "Intento %d/%d fallido para %s: %s. "
                            "Reintentando en %.2f segundos. Reintentos restantes: %d",
                            attempt + 1,
                            effective_config.max_retries + 1,
                            func.__name__,
                            str(e),
                            delay,
                            remaining_retries,
                        )

                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            "Todos los reintentos agotados para %s después de %d intentos. "
                            "Último error: %s",
                            func.__name__,
                            effective_config.max_retries + 1,
                            str(e),
                        )

            # Si llegamos aquí, agotamos todos los reintentos
            if last_exception is not None:
                raise last_exception

            # Esto no debería ocurrir, pero mypy necesita esta línea
            raise RuntimeError("Estado inesperado en retry wrapper")

        return wrapper

    return decorator


class RetryableHTTPClient:
    """Cliente HTTP con reintentos automáticos integrados.

    Wrapper alrededor de operaciones HTTP que aplica automáticamente
    la lógica de reintentos con backoff exponencial.

    Attributes:
        config: Configuración de reintentos a aplicar.
        logger: Logger para mensajes de reintento.

    Example:
        >>> client = RetryableHTTPClient(RetryConfig(max_retries=3))
        >>> # El cliente puede ser usado para wrappear llamadas HTTP
    """

    def __init__(self, config: RetryConfig | None = None) -> None:
        """Inicializa el cliente con configuración de reintentos.

        Args:
            config: Configuración de reintentos. Si es None, usa valores por defecto.
        """
        self.config = config if config is not None else RetryConfig()
        self.logger = logging.getLogger(__name__)

    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        operation_name: str = "HTTP operation",
    ) -> T:
        """Ejecuta una operación con reintentos automáticos.

        Args:
            operation: Función async sin argumentos que ejecuta la operación.
            operation_name: Nombre descriptivo para logging.

        Returns:
            Resultado de la operación exitosa.

        Raises:
            Exception: Re-lanza la última excepción después de agotar reintentos.

        Example:
            >>> async def fetch():
            ...     return await some_http_call()
            >>> result = await client.execute_with_retry(fetch, "fetch data")
        """
        last_exception: Exception | None = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return await operation()
            except tuple(self.config.retryable_exceptions) as e:
                last_exception = e
                remaining_retries = self.config.max_retries - attempt

                if attempt < self.config.max_retries:
                    delay = calculate_delay(
                        attempt=attempt,
                        base_delay=self.config.base_delay,
                        max_delay=self.config.max_delay,
                        exponential_base=self.config.exponential_base,
                        jitter=self.config.jitter,
                    )

                    self.logger.warning(
                        "Intento %d/%d fallido para '%s': %s. "
                        "Reintentando en %.2f segundos. Reintentos restantes: %d",
                        attempt + 1,
                        self.config.max_retries + 1,
                        operation_name,
                        str(e),
                        delay,
                        remaining_retries,
                    )

                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        "Todos los reintentos agotados para '%s' después de %d intentos. "
                        "Último error: %s",
                        operation_name,
                        self.config.max_retries + 1,
                        str(e),
                    )

        if last_exception is not None:
            raise last_exception

        raise RuntimeError("Estado inesperado en retry execution")
