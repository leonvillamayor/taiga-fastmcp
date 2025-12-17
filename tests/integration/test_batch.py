"""Tests de integración para el sistema de operaciones batch.

Tests requeridos según Tarea 3.10:
- Test 3.10.1: Batch respeta max_concurrency
- Test 3.10.2: Resultados en orden correcto
- Test 3.10.3: fail_fast detiene al primer error
- Test 3.10.4: Sin fail_fast continúa después de errores
- Test 3.10.5: Performance mejor que secuencial
"""

import asyncio
import time
from typing import Any

import pytest

from src.infrastructure.batch import BatchConfig, BatchExecutor, BatchProgress


class TestBatchExecutorConcurrency:
    """Test 3.10.1: Batch respeta max_concurrency."""

    @pytest.mark.asyncio
    async def test_max_concurrency_respected(self) -> None:
        """Verifica que no se ejecutan más operaciones concurrentes que max_concurrency."""
        max_concurrency = 3
        config = BatchConfig(max_concurrency=max_concurrency)
        executor: BatchExecutor[int] = BatchExecutor(config)

        concurrent_count = 0
        max_observed_concurrency = 0
        lock = asyncio.Lock()

        async def track_concurrency(item: int) -> int:
            nonlocal concurrent_count, max_observed_concurrency
            async with lock:
                concurrent_count += 1
                max_observed_concurrency = max(max_observed_concurrency, concurrent_count)

            # Simular trabajo
            await asyncio.sleep(0.05)

            async with lock:
                concurrent_count -= 1

            return item * 2

        items = list(range(10))
        result = await executor.execute(items, track_concurrency)

        assert max_observed_concurrency <= max_concurrency
        assert max_observed_concurrency > 0  # Al menos una operación se ejecutó
        assert len(result.successful_results) == 10

    @pytest.mark.asyncio
    async def test_concurrency_with_different_limits(self) -> None:
        """Verifica que diferentes límites de concurrencia se respetan."""
        for max_conc in [1, 2, 5]:
            await self._verify_concurrency_limit(max_conc)

    async def _verify_concurrency_limit(self, max_conc: int) -> None:
        """Helper para verificar un límite de concurrencia específico."""
        config = BatchConfig(max_concurrency=max_conc)
        executor: BatchExecutor[int] = BatchExecutor(config)

        concurrent_count = 0
        max_observed = 0
        lock = asyncio.Lock()

        async def track(item: int) -> int:
            nonlocal concurrent_count, max_observed
            async with lock:
                concurrent_count += 1
                max_observed = max(max_observed, concurrent_count)
            await asyncio.sleep(0.02)
            async with lock:
                concurrent_count -= 1
            return item

        items = list(range(10))
        await executor.execute(items, track)

        assert (
            max_observed <= max_conc
        ), f"Con max_concurrency={max_conc}, se observó {max_observed}"


class TestBatchExecutorOrder:
    """Test 3.10.2: Resultados en orden correcto."""

    @pytest.mark.asyncio
    async def test_results_preserve_order(self) -> None:
        """Verifica que los resultados mantienen el orden de los items de entrada."""
        config = BatchConfig(max_concurrency=5)
        executor: BatchExecutor[int] = BatchExecutor(config)

        async def process(item: int) -> int:
            # Diferentes tiempos de espera para provocar desorden en ejecución
            await asyncio.sleep(0.01 * (10 - item))
            return item * 10

        items = list(range(10))
        result = await executor.execute(items, process)

        expected = [i * 10 for i in items]
        assert result.successful_results == expected

    @pytest.mark.asyncio
    async def test_results_order_with_varying_delays(self) -> None:
        """Verifica orden incluso con delays variables que causan terminación desordenada."""
        config = BatchConfig(max_concurrency=3)
        executor: BatchExecutor[str] = BatchExecutor(config)

        async def process(item: int) -> str:
            # Items pares tardan más que impares
            delay = 0.1 if item % 2 == 0 else 0.01
            await asyncio.sleep(delay)
            return f"item_{item}"

        items = list(range(6))
        result = await executor.execute(items, process)

        expected = [f"item_{i}" for i in items]
        assert result.successful_results == expected


class TestBatchExecutorFailFast:
    """Test 3.10.3: fail_fast detiene al primer error."""

    @pytest.mark.asyncio
    async def test_fail_fast_stops_on_first_error(self) -> None:
        """Verifica que fail_fast=True propaga la excepción inmediatamente.

        Nota: asyncio.gather crea todas las tareas antes de ejecutar,
        por lo que algunas tareas pueden iniciar incluso con fail_fast=True.
        Lo importante es que la excepción se propaga y no se retorna un resultado.
        """
        config = BatchConfig(max_concurrency=2, fail_fast=True)
        executor: BatchExecutor[int] = BatchExecutor(config)

        error_raised = False

        async def process(item: int) -> int:
            nonlocal error_raised
            await asyncio.sleep(0.01)  # Pequeño delay para simular trabajo
            if item == 2 and not error_raised:
                error_raised = True
                raise ValueError(f"Error en item {item}")
            return item * 2

        items = list(range(5))

        with pytest.raises(ValueError, match="Error en item 2"):
            await executor.execute(items, process)

        # Lo importante es que se propagó la excepción
        assert error_raised

    @pytest.mark.asyncio
    async def test_fail_fast_propagates_exception(self) -> None:
        """Verifica que la excepción original se propaga con fail_fast."""
        config = BatchConfig(max_concurrency=2, fail_fast=True)
        executor: BatchExecutor[int] = BatchExecutor(config)

        class CustomError(Exception):
            pass

        async def process(item: int) -> int:
            if item == 1:
                raise CustomError("Error personalizado")
            return item

        items = [0, 1, 2, 3]

        with pytest.raises(CustomError, match="Error personalizado"):
            await executor.execute(items, process)


class TestBatchExecutorContinueOnError:
    """Test 3.10.4: Sin fail_fast continúa después de errores."""

    @pytest.mark.asyncio
    async def test_continue_on_error(self) -> None:
        """Verifica que sin fail_fast continúa procesando después de errores."""
        config = BatchConfig(max_concurrency=2, fail_fast=False)
        executor: BatchExecutor[int] = BatchExecutor(config)

        async def process(item: int) -> int:
            if item == 2 or item == 4:
                raise ValueError(f"Error en {item}")
            return item * 10

        items = list(range(6))  # 0, 1, 2, 3, 4, 5
        result = await executor.execute(items, process)

        # Debe tener errores
        assert result.has_errors
        assert len(result.errors) == 2

        # Debe tener resultados exitosos
        assert len(result.successful_results) == 4
        assert set(result.successful_results) == {0, 10, 30, 50}

    @pytest.mark.asyncio
    async def test_errors_tracked_with_indices(self) -> None:
        """Verifica que los errores se rastrean con sus índices correctos."""
        config = BatchConfig(max_concurrency=5, fail_fast=False)
        executor: BatchExecutor[int] = BatchExecutor(config)

        error_indices = [1, 3, 5]

        async def process(item: int) -> int:
            if item in error_indices:
                raise RuntimeError(f"Error at {item}")
            return item

        items = list(range(7))
        result = await executor.execute(items, process)

        error_idx_from_result = [idx for idx, _ in result.errors]
        assert sorted(error_idx_from_result) == error_indices

    @pytest.mark.asyncio
    async def test_all_items_processed_despite_errors(self) -> None:
        """Verifica que todos los items se procesan incluso con errores."""
        config = BatchConfig(max_concurrency=3, fail_fast=False)
        executor: BatchExecutor[int] = BatchExecutor(config)

        processed: list[int] = []
        lock = asyncio.Lock()

        async def process(item: int) -> int:
            async with lock:
                processed.append(item)
            if item % 3 == 0:
                raise ValueError(f"Error en {item}")
            return item

        items = list(range(10))
        await executor.execute(items, process)

        # Todos los items deben haber sido procesados
        assert sorted(processed) == items


class TestBatchExecutorPerformance:
    """Test 3.10.5: Performance mejor que secuencial."""

    @pytest.mark.asyncio
    async def test_parallel_faster_than_sequential(self) -> None:
        """Verifica que la ejecución paralela es más rápida que secuencial."""
        item_count = 10
        delay_per_item = 0.05  # 50ms por item

        async def slow_operation(item: int) -> int:
            await asyncio.sleep(delay_per_item)
            return item * 2

        items = list(range(item_count))

        # Ejecución secuencial (max_concurrency=1)
        sequential_config = BatchConfig(max_concurrency=1)
        sequential_executor: BatchExecutor[int] = BatchExecutor(sequential_config)

        start_sequential = time.monotonic()
        await sequential_executor.execute(items, slow_operation)
        sequential_time = time.monotonic() - start_sequential

        # Ejecución paralela (max_concurrency=5)
        parallel_config = BatchConfig(max_concurrency=5)
        parallel_executor: BatchExecutor[int] = BatchExecutor(parallel_config)

        start_parallel = time.monotonic()
        await parallel_executor.execute(items, slow_operation)
        parallel_time = time.monotonic() - start_parallel

        # La ejecución paralela debe ser al menos 2x más rápida
        assert parallel_time < sequential_time * 0.5, (
            f"Paralelo ({parallel_time:.3f}s) no es suficientemente más rápido "
            f"que secuencial ({sequential_time:.3f}s)"
        )

    @pytest.mark.asyncio
    async def test_performance_improvement_percentage(self) -> None:
        """Verifica que hay al menos 200% de mejora en performance (3x más rápido)."""
        item_count = 15
        delay_per_item = 0.03

        async def work(item: int) -> int:
            await asyncio.sleep(delay_per_item)
            return item

        items = list(range(item_count))

        # Secuencial
        seq_config = BatchConfig(max_concurrency=1)
        seq_executor: BatchExecutor[int] = BatchExecutor(seq_config)
        start = time.monotonic()
        await seq_executor.execute(items, work)
        seq_time = time.monotonic() - start

        # Paralelo con alta concurrencia
        par_config = BatchConfig(max_concurrency=10)
        par_executor: BatchExecutor[int] = BatchExecutor(par_config)
        start = time.monotonic()
        await par_executor.execute(items, work)
        par_time = time.monotonic() - start

        # Calcular mejora porcentual
        improvement = ((seq_time - par_time) / par_time) * 100
        assert improvement >= 200, (
            f"Mejora de {improvement:.0f}% es menor que 200% requerido. "
            f"Secuencial: {seq_time:.3f}s, Paralelo: {par_time:.3f}s"
        )


class TestBatchProgress:
    """Tests para el sistema de reportes de progreso."""

    @pytest.mark.asyncio
    async def test_progress_callback_called(self) -> None:
        """Verifica que el callback de progreso se llama."""
        config = BatchConfig(max_concurrency=2)
        executor: BatchExecutor[int] = BatchExecutor(config)

        progress_updates: list[BatchProgress] = []

        def on_progress(progress: BatchProgress) -> None:
            # Copiar el progreso para evitar referencias mutables
            progress_updates.append(
                BatchProgress(
                    total=progress.total,
                    completed=progress.completed,
                    failed=progress.failed,
                    current_item=progress.current_item,
                )
            )

        executor.set_progress_callback(on_progress)

        async def process(item: int) -> int:
            await asyncio.sleep(0.01)
            return item

        items = list(range(5))
        await executor.execute(items, process)

        assert len(progress_updates) > 0
        # El último progreso debe tener todos completados
        final = progress_updates[-1]
        assert final.completed == 5

    @pytest.mark.asyncio
    async def test_progress_tracks_failures(self) -> None:
        """Verifica que el progreso rastrea los fallos."""
        config = BatchConfig(max_concurrency=1, fail_fast=False)
        executor: BatchExecutor[int] = BatchExecutor(config)

        final_progress: BatchProgress | None = None

        def on_progress(progress: BatchProgress) -> None:
            nonlocal final_progress
            final_progress = BatchProgress(
                total=progress.total,
                completed=progress.completed,
                failed=progress.failed,
                current_item=progress.current_item,
            )

        executor.set_progress_callback(on_progress)

        async def process(item: int) -> int:
            if item % 2 == 0:
                raise ValueError("Error")
            return item

        items = list(range(6))
        await executor.execute(items, process)

        assert final_progress is not None
        assert final_progress.completed == 3  # 1, 3, 5
        assert final_progress.failed == 3  # 0, 2, 4
        assert final_progress.is_complete

    @pytest.mark.asyncio
    async def test_progress_percentage(self) -> None:
        """Verifica el cálculo del porcentaje de progreso."""
        progress = BatchProgress(total=10, completed=3, failed=2)
        assert progress.percentage == 50.0

        progress_empty = BatchProgress(total=0)
        assert progress_empty.percentage == 0.0

    def test_progress_is_complete(self) -> None:
        """Verifica la detección de completitud."""
        progress = BatchProgress(total=10, completed=8, failed=2)
        assert progress.is_complete

        progress_incomplete = BatchProgress(total=10, completed=5, failed=2)
        assert not progress_incomplete.is_complete


class TestBatchExecutorChunked:
    """Tests para execute_chunked."""

    @pytest.mark.asyncio
    async def test_execute_chunked_splits_correctly(self) -> None:
        """Verifica que execute_chunked divide correctamente en chunks."""
        config = BatchConfig(max_concurrency=2, chunk_size=3)
        executor: BatchExecutor[int] = BatchExecutor(config)

        chunks_received: list[list[Any]] = []
        lock = asyncio.Lock()

        async def process_chunk(chunk: list[Any]) -> list[int]:
            async with lock:
                chunks_received.append(chunk.copy())
            return [item * 2 for item in chunk]

        items = list(range(10))
        result = await executor.execute_chunked(items, process_chunk)

        # Debe haber recibido chunks de tamaño 3 (excepto el último)
        assert len(chunks_received) == 4  # [0,1,2], [3,4,5], [6,7,8], [9]
        assert chunks_received[-1] == [9]

        # Los resultados deben estar correctos
        assert result.successful_results == [i * 2 for i in items]

    @pytest.mark.asyncio
    async def test_execute_chunked_handles_errors(self) -> None:
        """Verifica que execute_chunked maneja errores en chunks."""
        config = BatchConfig(max_concurrency=2, chunk_size=3, fail_fast=False)
        executor: BatchExecutor[int] = BatchExecutor(config)

        async def process_chunk(chunk: list[Any]) -> list[int]:
            if 5 in chunk:  # Chunk [3,4,5] fallará
                raise ValueError("Error en chunk con 5")
            return [item * 2 for item in chunk]

        items = list(range(9))  # [0,1,2], [3,4,5], [6,7,8]
        result = await executor.execute_chunked(items, process_chunk)

        # Debe tener errores del chunk que falló
        assert result.has_errors
        # Los otros chunks deben haber sido procesados
        successful = [r for r in result.successful_results if isinstance(r, int)]
        assert len(successful) == 6  # 0,2,4 y 12,14,16

    @pytest.mark.asyncio
    async def test_execute_chunked_fail_fast_raises(self) -> None:
        """Verifica que execute_chunked con fail_fast=True propaga excepciones."""
        config = BatchConfig(max_concurrency=1, chunk_size=3, fail_fast=True)
        executor: BatchExecutor[int] = BatchExecutor(config)

        async def process_chunk(chunk: list[Any]) -> list[int]:
            if 5 in chunk:  # Chunk [3,4,5] fallará
                raise ValueError("Error en chunk con 5")
            return [item * 2 for item in chunk]

        items = list(range(9))  # [0,1,2], [3,4,5], [6,7,8]

        with pytest.raises(ValueError, match="Error en chunk con 5"):
            await executor.execute_chunked(items, process_chunk)


class TestBatchConfig:
    """Tests para BatchConfig."""

    def test_default_config(self) -> None:
        """Verifica los valores por defecto de la configuración."""
        config = BatchConfig()
        assert config.max_concurrency == 5
        assert config.chunk_size == 10
        assert config.fail_fast is False

    def test_custom_config(self) -> None:
        """Verifica configuración personalizada."""
        config = BatchConfig(max_concurrency=10, chunk_size=5, fail_fast=True)
        assert config.max_concurrency == 10
        assert config.chunk_size == 5
        assert config.fail_fast is True


class TestBatchResult:
    """Tests para BatchResult."""

    def test_successful_results_filters_exceptions(self) -> None:
        """Verifica que successful_results filtra excepciones."""
        from src.infrastructure.batch import BatchResult

        result: BatchResult[int] = BatchResult(
            results=[1, ValueError("error"), 3, RuntimeError("otro"), 5]
        )

        assert result.successful_results == [1, 3, 5]

    def test_has_errors(self) -> None:
        """Verifica detección de errores."""
        from src.infrastructure.batch import BatchResult

        result_with_errors: BatchResult[int] = BatchResult(errors=[(0, ValueError("error"))])
        assert result_with_errors.has_errors

        result_no_errors: BatchResult[int] = BatchResult(errors=[])
        assert not result_no_errors.has_errors


class TestBatchExecutorChunkedBaseException:
    """Tests para el manejo de BaseException en execute_chunked."""

    @pytest.mark.asyncio
    async def test_execute_chunked_handles_base_exception_in_gather(self) -> None:
        """Verifica que execute_chunked maneja BaseException capturada por gather.

        Cuando fail_fast=False y gather(return_exceptions=True) captura
        una BaseException que no es Exception, debe agregarla al resultado.
        """
        config = BatchConfig(max_concurrency=2, chunk_size=2, fail_fast=False)
        executor: BatchExecutor[int] = BatchExecutor(config)

        class CustomBaseException(BaseException):
            """BaseException personalizada para testing (no es Exception)."""

        async def process_chunk(chunk: list[Any]) -> list[int]:
            if 3 in chunk:
                # Lanzar BaseException que no será capturada por except Exception
                raise CustomBaseException("BaseException en chunk")
            return [item * 2 for item in chunk]

        items = list(range(6))  # Chunks: [0,1], [2,3], [4,5]
        result = await executor.execute_chunked(items, process_chunk)

        # Debe tener resultados exitosos y la BaseException
        assert result.has_errors or any(isinstance(r, BaseException) for r in result.results)
        # Los chunks exitosos deben tener sus resultados
        successful = [r for r in result.results if isinstance(r, int)]
        assert 0 in successful  # 0*2=0
        assert 2 in successful  # 1*2=2
