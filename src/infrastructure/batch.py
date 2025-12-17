"""Sistema de operaciones batch optimizadas con concurrencia controlada."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar, cast


T = TypeVar("T")


@dataclass
class BatchConfig:
    """Configuración para operaciones batch.

    Attributes:
        max_concurrency: Número máximo de operaciones concurrentes.
        chunk_size: Tamaño de cada chunk para procesamiento por lotes.
        fail_fast: Si True, detiene ejecución al primer error.
            Si False, continúa y retorna excepciones en resultados.
    """

    max_concurrency: int = 5
    chunk_size: int = 10
    fail_fast: bool = False


@dataclass
class BatchProgress:
    """Estado de progreso de una operación batch.

    Attributes:
        total: Número total de items a procesar.
        completed: Número de items completados.
        failed: Número de items que fallaron.
        current_item: Índice del item actual siendo procesado.
    """

    total: int = 0
    completed: int = 0
    failed: int = 0
    current_item: int = 0

    @property
    def percentage(self) -> float:
        """Retorna el porcentaje de progreso."""
        if self.total == 0:
            return 0.0
        return (self.completed + self.failed) / self.total * 100.0

    @property
    def is_complete(self) -> bool:
        """Indica si el batch ha completado."""
        return (self.completed + self.failed) >= self.total


# Tipo para callback de progreso
ProgressCallback = Callable[[BatchProgress], None]


@dataclass
class BatchResult(Generic[T]):
    """Resultado de una operación batch.

    Attributes:
        results: Lista de resultados exitosos o excepciones.
        progress: Estado final del progreso.
        errors: Lista de errores encontrados (índice, excepción).
    """

    results: list[T | BaseException] = field(default_factory=list)
    progress: BatchProgress = field(default_factory=BatchProgress)
    errors: list[tuple[int, BaseException]] = field(default_factory=list)

    @property
    def successful_results(self) -> list[T]:
        """Retorna solo los resultados exitosos."""
        return [r for r in self.results if not isinstance(r, BaseException)]

    @property
    def has_errors(self) -> bool:
        """Indica si hubo errores durante la ejecución."""
        return len(self.errors) > 0


class BatchExecutor(Generic[T]):
    """Ejecutor de operaciones batch con concurrencia controlada.

    Permite ejecutar múltiples operaciones asíncronas de forma paralela
    con control de concurrencia mediante semáforos.

    Example:
        >>> config = BatchConfig(max_concurrency=3, fail_fast=False)
        >>> executor = BatchExecutor(config)
        >>> async def fetch_item(item_id: int) -> dict:
        ...     return await api.get(item_id)
        >>> result = await executor.execute([1, 2, 3, 4, 5], fetch_item)
        >>> print(result.successful_results)
    """

    def __init__(self, config: BatchConfig | None = None) -> None:
        """Inicializa el ejecutor con la configuración dada.

        Args:
            config: Configuración del batch. Si es None, usa valores por defecto.
        """
        self.config = config or BatchConfig()
        self._progress_callback: ProgressCallback | None = None

    def set_progress_callback(self, callback: ProgressCallback) -> None:
        """Establece el callback para reportes de progreso.

        Args:
            callback: Función a llamar con cada actualización de progreso.
        """
        self._progress_callback = callback

    async def execute(
        self,
        items: list[Any],
        operation: Callable[[Any], Awaitable[T]],
    ) -> BatchResult[T]:
        """Ejecuta operación para cada item con concurrencia controlada.

        Args:
            items: Lista de items a procesar.
            operation: Función asíncrona a ejecutar para cada item.

        Returns:
            BatchResult con los resultados y estado de progreso.

        Raises:
            Exception: Si fail_fast=True y ocurre un error.
        """
        semaphore = asyncio.Semaphore(self.config.max_concurrency)
        progress = BatchProgress(total=len(items))
        errors: list[tuple[int, BaseException]] = []
        lock = asyncio.Lock()

        async def bounded_operation(index: int, item: Any) -> T | BaseException:
            async with semaphore:
                async with lock:
                    progress.current_item = index
                    self._notify_progress(progress)

                try:
                    result = await operation(item)
                    async with lock:
                        progress.completed += 1
                        self._notify_progress(progress)
                    return result
                except Exception as e:
                    async with lock:
                        progress.failed += 1
                        errors.append((index, e))
                        self._notify_progress(progress)

                    if self.config.fail_fast:
                        raise
                    return e

        tasks = [bounded_operation(i, item) for i, item in enumerate(items)]

        if self.config.fail_fast:
            results = list(await asyncio.gather(*tasks))
        else:
            results = list(await asyncio.gather(*tasks, return_exceptions=True))

        return BatchResult(
            results=results,
            progress=progress,
            errors=errors,
        )

    async def execute_chunked(
        self,
        items: list[Any],
        operation: Callable[[list[Any]], Awaitable[list[T]]],
    ) -> BatchResult[T]:
        """Ejecuta operación por chunks con concurrencia controlada.

        Útil para APIs que soportan operaciones bulk nativas.

        Args:
            items: Lista de items a procesar.
            operation: Función asíncrona que procesa un chunk de items.

        Returns:
            BatchResult con los resultados combinados.
        """
        chunks = self._split_into_chunks(items)
        progress = BatchProgress(total=len(chunks))
        all_results: list[T | BaseException] = []
        errors: list[tuple[int, BaseException]] = []
        semaphore = asyncio.Semaphore(self.config.max_concurrency)
        lock = asyncio.Lock()

        async def process_chunk(chunk_index: int, chunk: list[Any]) -> list[T | BaseException]:
            async with semaphore:
                async with lock:
                    progress.current_item = chunk_index
                    self._notify_progress(progress)

                try:
                    result = await operation(chunk)
                    async with lock:
                        progress.completed += 1
                        self._notify_progress(progress)
                    return cast("list[T | BaseException]", result)
                except Exception as e:
                    async with lock:
                        progress.failed += 1
                        errors.append((chunk_index, e))
                        self._notify_progress(progress)

                    if self.config.fail_fast:
                        raise
                    # Retornar la excepción para cada item del chunk
                    return [e] * len(chunk)

        tasks = [process_chunk(i, chunk) for i, chunk in enumerate(chunks)]

        if self.config.fail_fast:
            chunk_results: list[list[T | BaseException]] = list(await asyncio.gather(*tasks))
        else:
            # Con return_exceptions=True, gather puede retornar BaseException directamente
            raw_results = await asyncio.gather(*tasks, return_exceptions=True)
            chunk_results = []
            for raw in raw_results:
                if isinstance(raw, BaseException):
                    # Si gather captura una excepción, la agregamos como item único
                    chunk_results.append([raw])
                else:
                    chunk_results.append(raw)

        # Aplanar resultados
        for chunk_result in chunk_results:
            all_results.extend(chunk_result)

        return BatchResult(
            results=all_results,
            progress=progress,
            errors=errors,
        )

    def _split_into_chunks(self, items: list[Any]) -> list[list[Any]]:
        """Divide la lista en chunks del tamaño configurado.

        Args:
            items: Lista a dividir.

        Returns:
            Lista de chunks.
        """
        chunk_size = self.config.chunk_size
        return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]

    def _notify_progress(self, progress: BatchProgress) -> None:
        """Notifica el progreso al callback si está configurado.

        Args:
            progress: Estado actual del progreso.
        """
        if self._progress_callback is not None:
            self._progress_callback(progress)
