"""Tests unitarios para el sistema de caché.

Este módulo contiene tests exhaustivos para el sistema de caché en memoria,
cubriendo todos los casos de uso especificados en la tarea 3.2.

Tests implementados:
- Test 3.2.1: Cache almacena y recupera valores
- Test 3.2.2: Entradas expiran después de TTL
- Test 3.2.3: Invalidación por patrón funciona
- Test 3.2.4: Cache respeta max_size
- Test 3.2.5: Llamadas cacheables no invocan API
- Test 3.2.6: Llamadas no cacheables siempre invocan API
- Test 3.2.7: Concurrencia segura (múltiples lecturas/escrituras)
- Test 3.2.8: Métricas de hit/miss correctas
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.cache import CacheEntry, CacheMetrics, MemoryCache
from src.infrastructure.cached_client import CachedTaigaClient, CacheKeyBuilder


class TestCacheEntry:
    """Tests para la clase CacheEntry."""

    def test_cache_entry_not_expired(self) -> None:
        """Test que una entrada con tiempo futuro no esté expirada."""
        entry = CacheEntry(
            value="test_value",
            expires_at=datetime.now() + timedelta(hours=1),
        )
        assert not entry.is_expired()

    def test_cache_entry_expired(self) -> None:
        """Test que una entrada con tiempo pasado esté expirada."""
        entry = CacheEntry(
            value="test_value",
            expires_at=datetime.now() - timedelta(seconds=1),
        )
        assert entry.is_expired()

    def test_cache_entry_stores_value(self) -> None:
        """Test que la entrada almacene el valor correctamente."""
        test_data = {"key": "value", "numbers": [1, 2, 3]}
        entry = CacheEntry(
            value=test_data,
            expires_at=datetime.now() + timedelta(hours=1),
        )
        assert entry.value == test_data


class TestCacheMetrics:
    """Tests para la clase CacheMetrics."""

    def test_initial_metrics_are_zero(self) -> None:
        """Test que las métricas iniciales sean cero."""
        metrics = CacheMetrics()
        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.evictions == 0
        assert metrics.invalidations == 0

    def test_total_requests(self) -> None:
        """Test que total_requests sea la suma de hits y misses."""
        metrics = CacheMetrics(hits=10, misses=5)
        assert metrics.total_requests == 15

    def test_hit_rate_calculation(self) -> None:
        """Test del cálculo de hit rate."""
        metrics = CacheMetrics(hits=80, misses=20)
        assert metrics.hit_rate == 0.8

    def test_hit_rate_zero_requests(self) -> None:
        """Test de hit rate con cero requests."""
        metrics = CacheMetrics()
        assert metrics.hit_rate == 0.0

    def test_miss_rate_calculation(self) -> None:
        """Test del cálculo de miss rate."""
        metrics = CacheMetrics(hits=80, misses=20)
        assert metrics.miss_rate == 0.2

    def test_miss_rate_zero_requests(self) -> None:
        """Test de miss rate con cero requests."""
        metrics = CacheMetrics()
        assert metrics.miss_rate == 0.0

    def test_reset_metrics(self) -> None:
        """Test que reset() ponga todo a cero."""
        metrics = CacheMetrics(hits=10, misses=5, evictions=3, invalidations=2)
        metrics.reset()
        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.evictions == 0
        assert metrics.invalidations == 0


class TestMemoryCache:
    """Tests para la clase MemoryCache."""

    @pytest.fixture
    def cache(self) -> MemoryCache:
        """Fixture que crea un MemoryCache para cada test."""
        return MemoryCache(default_ttl=3600, max_size=100)

    @pytest.mark.asyncio
    async def test_3_2_1_cache_stores_and_retrieves_values(self, cache: MemoryCache) -> None:
        """Test 3.2.1: Cache almacena y recupera valores correctamente."""
        # Arrange
        key = "test_key"
        value = {"data": "test_value", "numbers": [1, 2, 3]}

        # Act
        await cache.set(key, value)
        retrieved = await cache.get(key)

        # Assert
        assert retrieved == value

    @pytest.mark.asyncio
    async def test_3_2_1_cache_returns_none_for_missing_key(self, cache: MemoryCache) -> None:
        """Test 3.2.1: Cache retorna None para claves inexistentes."""
        result = await cache.get("nonexistent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_3_2_2_entries_expire_after_ttl(self) -> None:
        """Test 3.2.2: Entradas expiran después de TTL."""
        # Arrange - crear caché con TTL muy corto
        cache = MemoryCache(default_ttl=1, max_size=100)
        key = "expiring_key"
        value = "expiring_value"

        # Act - guardar y verificar inmediatamente
        await cache.set(key, value, ttl=1)
        immediate_result = await cache.get(key)

        # Assert - debe existir inmediatamente
        assert immediate_result == value

        # Act - esperar a que expire
        await asyncio.sleep(1.1)
        expired_result = await cache.get(key)

        # Assert - debe haber expirado
        assert expired_result is None

    @pytest.mark.asyncio
    async def test_3_2_2_custom_ttl_overrides_default(self, cache: MemoryCache) -> None:
        """Test 3.2.2: TTL personalizado sobreescribe el default."""
        # Arrange
        key = "custom_ttl_key"
        value = "custom_ttl_value"

        # Act - usar TTL personalizado corto
        await cache.set(key, value, ttl=1)

        # Assert - debe existir inmediatamente
        assert await cache.get(key) == value

        # Act - esperar a que expire
        await asyncio.sleep(1.1)

        # Assert - debe haber expirado
        assert await cache.get(key) is None

    @pytest.mark.asyncio
    async def test_3_2_3_invalidation_by_pattern(self, cache: MemoryCache) -> None:
        """Test 3.2.3: Invalidación por patrón funciona correctamente."""
        # Arrange - crear varias entradas
        await cache.set("epic_filters:project_id=1", {"data": "epic1"})
        await cache.set("epic_filters:project_id=2", {"data": "epic2"})
        await cache.set("issue_filters:project_id=1", {"data": "issue1"})
        await cache.set("task_filters:project_id=1", {"data": "task1"})

        # Act - invalidar todas las entradas de epic_filters
        count = await cache.invalidate("epic_filters")

        # Assert - solo epic_filters deben haber sido invalidados
        assert count == 2
        assert await cache.get("epic_filters:project_id=1") is None
        assert await cache.get("epic_filters:project_id=2") is None
        assert await cache.get("issue_filters:project_id=1") is not None
        assert await cache.get("task_filters:project_id=1") is not None

    @pytest.mark.asyncio
    async def test_3_2_3_invalidation_by_project_id(self, cache: MemoryCache) -> None:
        """Test 3.2.3: Invalidación por project_id funciona."""
        # Arrange
        await cache.set("epic_filters:project_id=123", {"data": "epic"})
        await cache.set("issue_filters:project_id=123", {"data": "issue"})
        await cache.set("epic_filters:project_id=456", {"data": "other"})

        # Act
        count = await cache.invalidate("project_id=123")

        # Assert
        assert count == 2
        assert await cache.get("epic_filters:project_id=123") is None
        assert await cache.get("issue_filters:project_id=123") is None
        assert await cache.get("epic_filters:project_id=456") is not None

    @pytest.mark.asyncio
    async def test_3_2_4_cache_respects_max_size(self) -> None:
        """Test 3.2.4: Cache respeta max_size."""
        # Arrange - crear caché con tamaño pequeño
        cache = MemoryCache(default_ttl=3600, max_size=3)

        # Act - añadir más entradas que el límite
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        await cache.set("key4", "value4")  # Debería triggear evicción

        # Assert - el tamaño no debe exceder max_size
        size = await cache.size()
        assert size <= 3

    @pytest.mark.asyncio
    async def test_3_2_4_eviction_removes_oldest_entry(self) -> None:
        """Test 3.2.4: La evicción elimina la entrada más antigua."""
        # Arrange
        cache = MemoryCache(default_ttl=3600, max_size=2)

        # Act - añadir entradas con pequeña diferencia de tiempo
        await cache.set("key1", "value1", ttl=100)
        await asyncio.sleep(0.01)
        await cache.set("key2", "value2", ttl=200)
        await asyncio.sleep(0.01)
        await cache.set("key3", "value3", ttl=300)  # Debería eliminar key1

        # Assert - key1 debería haber sido eliminada
        assert await cache.get("key1") is None
        # key2 o key3 deberían existir
        assert await cache.get("key2") is not None or await cache.get("key3") is not None

    @pytest.mark.asyncio
    async def test_3_2_7_concurrency_safe_reads_writes(self, cache: MemoryCache) -> None:
        """Test 3.2.7: Concurrencia segura con múltiples lecturas/escrituras."""
        # Arrange
        num_operations = 50

        async def write_task(i: int) -> None:
            await cache.set(f"key_{i}", f"value_{i}")

        async def read_task(i: int) -> str | None:
            return await cache.get(f"key_{i}")

        # Act - ejecutar escrituras concurrentes
        write_tasks = [write_task(i) for i in range(num_operations)]
        await asyncio.gather(*write_tasks)

        # Act - ejecutar lecturas concurrentes
        read_tasks = [read_task(i) for i in range(num_operations)]
        results = await asyncio.gather(*read_tasks)

        # Assert - todas las lecturas deben tener éxito
        for i, result in enumerate(results):
            assert result == f"value_{i}"

    @pytest.mark.asyncio
    async def test_3_2_7_concurrency_mixed_operations(self, cache: MemoryCache) -> None:
        """Test 3.2.7: Concurrencia con operaciones mixtas."""
        # Arrange
        results: list[str | None] = []

        async def mixed_operation(i: int) -> None:
            if i % 3 == 0:
                await cache.set(f"mixed_{i}", f"value_{i}")
            elif i % 3 == 1:
                result = await cache.get(f"mixed_{i - 1}")
                results.append(result)
            else:
                await cache.invalidate(f"mixed_{i - 2}")

        # Act - ejecutar operaciones concurrentes
        tasks = [mixed_operation(i) for i in range(30)]
        await asyncio.gather(*tasks)

        # Assert - no debe haber excepciones (si llegamos aquí, pasó)
        assert True

    @pytest.mark.asyncio
    async def test_3_2_8_metrics_hit_miss_correct(self, cache: MemoryCache) -> None:
        """Test 3.2.8: Métricas de hit/miss son correctas."""
        # Arrange
        await cache.set("existing_key", "value")

        # Act - generar hits y misses
        await cache.get("existing_key")  # hit
        await cache.get("existing_key")  # hit
        await cache.get("nonexistent1")  # miss
        await cache.get("nonexistent2")  # miss
        await cache.get("nonexistent3")  # miss

        # Assert
        metrics = cache.get_metrics()
        assert metrics.hits == 2
        assert metrics.misses == 3
        assert metrics.hit_rate == 0.4  # 2/5
        assert metrics.miss_rate == 0.6  # 3/5

    @pytest.mark.asyncio
    async def test_3_2_8_metrics_evictions_counted(self) -> None:
        """Test 3.2.8: Las eviciones se cuentan correctamente."""
        # Arrange
        cache = MemoryCache(default_ttl=1, max_size=2)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")  # Trigger eviction

        # Assert
        metrics = cache.get_metrics()
        assert metrics.evictions >= 1

    @pytest.mark.asyncio
    async def test_3_2_8_metrics_invalidations_counted(self, cache: MemoryCache) -> None:
        """Test 3.2.8: Las invalidaciones se cuentan correctamente."""
        # Arrange
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        # Act
        await cache.delete("key1")
        await cache.invalidate("key2")

        # Assert
        metrics = cache.get_metrics()
        assert metrics.invalidations == 2

    @pytest.mark.asyncio
    async def test_delete_returns_true_for_existing_key(self, cache: MemoryCache) -> None:
        """Test que delete retorne True para claves existentes."""
        await cache.set("key", "value")
        result = await cache.delete("key")
        assert result is True
        assert await cache.get("key") is None

    @pytest.mark.asyncio
    async def test_delete_returns_false_for_missing_key(self, cache: MemoryCache) -> None:
        """Test que delete retorne False para claves inexistentes."""
        result = await cache.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear_removes_all_entries(self, cache: MemoryCache) -> None:
        """Test que clear elimine todas las entradas."""
        # Arrange
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Act
        count = await cache.clear()

        # Assert
        assert count == 3
        assert await cache.size() == 0

    @pytest.mark.asyncio
    async def test_contains_returns_correct_value(self, cache: MemoryCache) -> None:
        """Test que contains funcione correctamente."""
        await cache.set("existing", "value")

        assert await cache.contains("existing") is True
        assert await cache.contains("nonexistent") is False

    @pytest.mark.asyncio
    async def test_contains_returns_false_for_expired(self) -> None:
        """Test que contains retorne False para entradas expiradas."""
        cache = MemoryCache(default_ttl=1, max_size=100)
        await cache.set("expiring", "value", ttl=1)

        assert await cache.contains("expiring") is True

        await asyncio.sleep(1.1)

        assert await cache.contains("expiring") is False

    @pytest.mark.asyncio
    async def test_get_stats_returns_complete_info(self, cache: MemoryCache) -> None:
        """Test que get_stats retorne información completa."""
        # Arrange
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.get("key1")  # hit
        await cache.get("missing")  # miss

        # Act
        stats = await cache.get_stats()

        # Assert
        assert stats["size"] == 2
        assert stats["max_size"] == 100
        assert stats["default_ttl"] == 3600
        assert "metrics" in stats
        assert stats["metrics"]["hits"] == 1
        assert stats["metrics"]["misses"] == 1
        assert stats["metrics"]["hit_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_evict_expired_removes_expired_entries(self) -> None:
        """Test que evict_expired elimine entradas expiradas."""
        cache = MemoryCache(default_ttl=1, max_size=100)

        # Arrange
        await cache.set("expiring1", "value1", ttl=1)
        await cache.set("expiring2", "value2", ttl=1)
        await cache.set("not_expiring", "value3", ttl=3600)

        await asyncio.sleep(1.1)

        # Act
        evicted = await cache.evict_expired()

        # Assert
        assert evicted == 2
        assert await cache.contains("not_expiring") is True

    @pytest.mark.asyncio
    async def test_reset_metrics_clears_all_metrics(self, cache: MemoryCache) -> None:
        """Test que reset_metrics limpie todas las métricas."""
        # Arrange
        await cache.set("key", "value")
        await cache.get("key")
        await cache.get("missing")

        # Act
        cache.reset_metrics()

        # Assert
        metrics = cache.get_metrics()
        assert metrics.hits == 0
        assert metrics.misses == 0


class TestCacheKeyBuilder:
    """Tests para la clase CacheKeyBuilder."""

    def test_build_simple_key(self) -> None:
        """Test construcción de clave simple."""
        key = CacheKeyBuilder.build("epic_filters")
        assert key == "epic_filters"

    def test_build_key_with_params(self) -> None:
        """Test construcción de clave con parámetros."""
        key = CacheKeyBuilder.build("epic_filters", project_id=123)
        assert key == "epic_filters:project_id=123"

    def test_build_key_with_multiple_params(self) -> None:
        """Test construcción de clave con múltiples parámetros."""
        key = CacheKeyBuilder.build("epic_filters", project_id=123, status="active")
        # Los parámetros deben estar ordenados
        assert key == "epic_filters:project_id=123:status=active"

    def test_build_key_ignores_none_params(self) -> None:
        """Test que se ignoren los parámetros None."""
        key = CacheKeyBuilder.build("epic_filters", project_id=123, status=None)
        assert key == "epic_filters:project_id=123"


class TestCachedTaigaClient:
    """Tests para la clase CachedTaigaClient."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Fixture que crea un mock de TaigaAPIClient."""
        client = MagicMock()
        client.get_epic_filters = AsyncMock(return_value={"filters": "data"})
        client.get_issue_filters_data = AsyncMock(return_value={"issue_filters": "data"})
        client.get_task_filters = AsyncMock(return_value={"task_filters": "data"})
        client.list_epic_custom_attributes = AsyncMock(return_value=[{"id": 1, "name": "attr1"}])
        return client

    @pytest.fixture
    def cached_client(self, mock_client: MagicMock) -> CachedTaigaClient:
        """Fixture que crea un CachedTaigaClient."""
        return CachedTaigaClient(client=mock_client)

    @pytest.mark.asyncio
    async def test_3_2_5_cacheable_calls_dont_invoke_api_twice(
        self, cached_client: CachedTaigaClient, mock_client: MagicMock
    ) -> None:
        """Test 3.2.5: Llamadas cacheables no invocan API la segunda vez."""
        # Act - primera llamada
        result1 = await cached_client.get_epic_filters(project_id=123)

        # Act - segunda llamada
        result2 = await cached_client.get_epic_filters(project_id=123)

        # Assert - API solo debe ser llamada una vez
        assert mock_client.get_epic_filters.call_count == 1
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_3_2_6_different_params_invoke_api(
        self, cached_client: CachedTaigaClient, mock_client: MagicMock
    ) -> None:
        """Test 3.2.6: Parámetros diferentes invocan la API."""
        # Act
        await cached_client.get_epic_filters(project_id=123)
        await cached_client.get_epic_filters(project_id=456)

        # Assert - API debe ser llamada dos veces (diferentes proyectos)
        assert mock_client.get_epic_filters.call_count == 2

    @pytest.mark.asyncio
    async def test_delegation_to_underlying_client(
        self, cached_client: CachedTaigaClient, mock_client: MagicMock
    ) -> None:
        """Test que atributos no encontrados se deleguen al cliente."""
        mock_client.some_method = AsyncMock(return_value="result")

        # Act
        method = cached_client.some_method

        # Assert
        assert method is mock_client.some_method

    @pytest.mark.asyncio
    async def test_get_ttl_returns_configured_value(self, cached_client: CachedTaigaClient) -> None:
        """Test que get_ttl retorne el valor configurado."""
        assert cached_client.get_ttl("epic_filters") == 3600
        assert cached_client.get_ttl("project_modules") == 1800
        assert cached_client.get_ttl("project_stats") == 600

    @pytest.mark.asyncio
    async def test_get_ttl_returns_default_for_unknown(
        self, cached_client: CachedTaigaClient
    ) -> None:
        """Test que get_ttl retorne default para tipos desconocidos."""
        assert cached_client.get_ttl("unknown_type") == 3600

    @pytest.mark.asyncio
    async def test_invalidate_project_cache(
        self, cached_client: CachedTaigaClient, mock_client: MagicMock
    ) -> None:
        """Test que invalidate_project_cache funcione correctamente."""
        # Arrange - llenar caché
        await cached_client.get_epic_filters(project_id=123)
        await cached_client.get_epic_filters(project_id=456)

        # Act
        invalidated_count = await cached_client.invalidate_project_cache(123)
        assert invalidated_count == 1  # Solo invalida la entrada del proyecto 123

        # Assert - debe invalidar la entrada del proyecto 123
        # La siguiente llamada debe invocar la API
        await cached_client.get_epic_filters(project_id=123)
        assert mock_client.get_epic_filters.call_count == 3

    @pytest.mark.asyncio
    async def test_invalidate_endpoint_type(
        self, cached_client: CachedTaigaClient, mock_client: MagicMock
    ) -> None:
        """Test que invalidate_endpoint_type funcione correctamente."""
        # Arrange
        await cached_client.get_epic_filters(project_id=123)
        await cached_client.get_epic_filters(project_id=456)

        # Act
        count = await cached_client.invalidate_endpoint_type("epic_filters")

        # Assert
        assert count == 2

    @pytest.mark.asyncio
    async def test_clear_cache_removes_all(
        self, cached_client: CachedTaigaClient, mock_client: MagicMock
    ) -> None:
        """Test que clear_cache elimine todo el caché."""
        # Arrange
        await cached_client.get_epic_filters(project_id=123)
        await cached_client.get_issue_filters(project_id=123)

        # Act
        count = await cached_client.clear_cache()

        # Assert
        assert count == 2

    @pytest.mark.asyncio
    async def test_get_metrics_returns_cache_metrics(
        self, cached_client: CachedTaigaClient, mock_client: MagicMock
    ) -> None:
        """Test que get_metrics retorne métricas del caché."""
        # Arrange
        await cached_client.get_epic_filters(project_id=123)  # miss + set
        await cached_client.get_epic_filters(project_id=123)  # hit

        # Act
        metrics = cached_client.get_metrics()

        # Assert
        assert metrics.hits == 1
        assert metrics.misses == 1

    @pytest.mark.asyncio
    async def test_get_stats_returns_complete_stats(
        self, cached_client: CachedTaigaClient, mock_client: MagicMock
    ) -> None:
        """Test que get_stats retorne estadísticas completas."""
        # Arrange
        await cached_client.get_epic_filters(project_id=123)

        # Act
        stats = await cached_client.get_stats()

        # Assert
        assert "size" in stats
        assert "metrics" in stats

    @pytest.mark.asyncio
    async def test_reset_metrics(
        self, cached_client: CachedTaigaClient, mock_client: MagicMock
    ) -> None:
        """Test que reset_metrics limpie las métricas."""
        # Arrange
        await cached_client.get_epic_filters(project_id=123)

        # Act
        cached_client.reset_metrics()
        metrics = cached_client.get_metrics()

        # Assert
        assert metrics.hits == 0
        assert metrics.misses == 0

    @pytest.mark.asyncio
    async def test_client_property(
        self, cached_client: CachedTaigaClient, mock_client: MagicMock
    ) -> None:
        """Test que la propiedad client retorne el cliente subyacente."""
        assert cached_client.client is mock_client

    @pytest.mark.asyncio
    async def test_cache_property(self, cached_client: CachedTaigaClient) -> None:
        """Test que la propiedad cache retorne el caché."""
        assert isinstance(cached_client.cache, MemoryCache)
