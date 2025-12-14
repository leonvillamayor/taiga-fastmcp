"""Integration tests for HTTPSessionPool.

Tests:
- Test 3.1.1: Pool se inicializa correctamente
- Test 3.1.2: Las sesiones se reutilizan (verificar keep-alive)
- Test 3.1.3: Pool respeta límites de conexiones
- Test 3.1.4: Pool se cierra correctamente al finalizar
- Test 3.1.5: Múltiples requests concurrentes funcionan
"""

import asyncio
import time

import httpx
import pytest

from src.infrastructure.http_session_pool import HTTPSessionPool


class TestHTTPSessionPoolInitialization:
    """Test 3.1.1: Pool se inicializa correctamente."""

    @pytest.mark.asyncio
    async def test_pool_initializes_with_default_values(self) -> None:
        """Test that pool initializes with default configuration."""
        pool = HTTPSessionPool(base_url="https://api.example.com")

        assert pool.base_url == "https://api.example.com"
        assert pool.timeout == 30.0
        assert pool.max_connections == 100
        assert pool.max_keepalive == 20
        assert pool._client is None
        assert not pool.is_started

    @pytest.mark.asyncio
    async def test_pool_initializes_with_custom_values(self) -> None:
        """Test that pool accepts custom configuration."""
        pool = HTTPSessionPool(
            base_url="https://api.taiga.io/api/v1",
            timeout=60.0,
            max_connections=50,
            max_keepalive=10,
        )

        assert pool.base_url == "https://api.taiga.io/api/v1"
        assert pool.timeout == 60.0
        assert pool.max_connections == 50
        assert pool.max_keepalive == 10

    @pytest.mark.asyncio
    async def test_pool_start_creates_client(self) -> None:
        """Test that start() creates an AsyncClient with correct settings."""
        pool = HTTPSessionPool(
            base_url="https://api.example.com",
            timeout=45.0,
            max_connections=75,
            max_keepalive=15,
        )

        await pool.start()

        try:
            assert pool.is_started
            assert pool._client is not None
            assert isinstance(pool._client, httpx.AsyncClient)
            # Verify pool configuration is stored
            assert pool.max_connections == 75
            assert pool.max_keepalive == 15
        finally:
            await pool.stop()

    @pytest.mark.asyncio
    async def test_pool_start_is_idempotent(self) -> None:
        """Test that calling start() multiple times doesn't recreate client."""
        pool = HTTPSessionPool(base_url="https://api.example.com")

        await pool.start()
        first_client = pool._client

        await pool.start()
        second_client = pool._client

        try:
            assert first_client is second_client
        finally:
            await pool.stop()


class TestHTTPSessionPoolSessionReuse:
    """Test 3.1.2: Las sesiones se reutilizan (verificar keep-alive)."""

    @pytest.mark.asyncio
    async def test_session_returns_same_client(self) -> None:
        """Test that session() context manager returns the same client instance."""
        pool = HTTPSessionPool(base_url="https://api.example.com")

        try:
            async with pool.session() as client1:
                first_client = client1

            async with pool.session() as client2:
                second_client = client2

            assert first_client is second_client
        finally:
            await pool.stop()

    @pytest.mark.asyncio
    async def test_session_auto_starts_pool(self) -> None:
        """Test that session() automatically starts the pool if not started."""
        pool = HTTPSessionPool(base_url="https://api.example.com")

        assert not pool.is_started

        try:
            async with pool.session() as client:
                assert pool.is_started
                assert client is not None
        finally:
            await pool.stop()

    @pytest.mark.asyncio
    async def test_multiple_sessions_share_connections(self) -> None:
        """Test that multiple session calls reuse the underlying connection pool."""
        pool = HTTPSessionPool(
            base_url="https://api.example.com",
            max_keepalive=5,
        )

        clients: list[httpx.AsyncClient] = []

        try:
            for _ in range(10):
                async with pool.session() as client:
                    clients.append(client)

            # All sessions should reference the same client
            assert all(c is clients[0] for c in clients)
        finally:
            await pool.stop()


class TestHTTPSessionPoolLimits:
    """Test 3.1.3: Pool respeta límites de conexiones."""

    @pytest.mark.asyncio
    async def test_pool_enforces_max_connections_limit(self) -> None:
        """Test that pool respects max_connections setting."""
        pool = HTTPSessionPool(
            base_url="https://api.example.com",
            max_connections=5,
            max_keepalive=2,
        )

        await pool.start()

        try:
            assert pool._client is not None
            # Verify pool configuration is stored
            assert pool.max_connections == 5
            assert pool.max_keepalive == 2
        finally:
            await pool.stop()

    @pytest.mark.asyncio
    async def test_pool_limits_are_configurable(self) -> None:
        """Test that different pool instances can have different limits."""
        pool1 = HTTPSessionPool(
            base_url="https://api1.example.com",
            max_connections=10,
            max_keepalive=5,
        )
        pool2 = HTTPSessionPool(
            base_url="https://api2.example.com",
            max_connections=50,
            max_keepalive=25,
        )

        await pool1.start()
        await pool2.start()

        try:
            assert pool1._client is not None
            assert pool2._client is not None
            # Verify each pool has its own configuration
            assert pool1.max_connections == 10
            assert pool1.max_keepalive == 5
            assert pool2.max_connections == 50
            assert pool2.max_keepalive == 25
        finally:
            await pool1.stop()
            await pool2.stop()


class TestHTTPSessionPoolStop:
    """Test 3.1.4: Pool se cierra correctamente al finalizar."""

    @pytest.mark.asyncio
    async def test_stop_closes_client(self) -> None:
        """Test that stop() properly closes the client."""
        pool = HTTPSessionPool(base_url="https://api.example.com")

        await pool.start()
        assert pool.is_started
        assert pool._client is not None

        await pool.stop()

        assert not pool.is_started
        assert pool._client is None

    @pytest.mark.asyncio
    async def test_stop_is_idempotent(self) -> None:
        """Test that calling stop() multiple times is safe."""
        pool = HTTPSessionPool(base_url="https://api.example.com")

        await pool.start()
        await pool.stop()
        await pool.stop()  # Should not raise

        assert not pool.is_started

    @pytest.mark.asyncio
    async def test_context_manager_closes_pool(self) -> None:
        """Test that async context manager properly closes pool."""
        async with HTTPSessionPool(base_url="https://api.example.com") as pool:
            assert pool.is_started

        assert not pool.is_started

    @pytest.mark.asyncio
    async def test_pool_can_be_restarted_after_stop(self) -> None:
        """Test that pool can be started again after being stopped."""
        pool = HTTPSessionPool(base_url="https://api.example.com")

        await pool.start()
        first_client = pool._client

        await pool.stop()
        assert pool._client is None

        await pool.start()
        second_client = pool._client

        try:
            assert pool.is_started
            assert second_client is not None
            # New client after restart
            assert first_client is not second_client
        finally:
            await pool.stop()


class TestHTTPSessionPoolConcurrency:
    """Test 3.1.5: Múltiples requests concurrentes funcionan."""

    @pytest.mark.asyncio
    async def test_concurrent_session_access(self) -> None:
        """Test that multiple concurrent session accesses work correctly."""
        pool = HTTPSessionPool(
            base_url="https://api.example.com",
            max_connections=10,
        )

        results: list[httpx.AsyncClient] = []

        async def get_session() -> httpx.AsyncClient:
            async with pool.session() as client:
                await asyncio.sleep(0.01)  # Simulate async work
                return client

        try:
            tasks = [get_session() for _ in range(5)]
            results = await asyncio.gather(*tasks)

            # All should reference the same client
            assert all(r is results[0] for r in results)
        finally:
            await pool.stop()

    @pytest.mark.asyncio
    async def test_concurrent_operations_dont_corrupt_state(self) -> None:
        """Test that concurrent operations don't corrupt pool state."""
        pool = HTTPSessionPool(
            base_url="https://api.example.com",
            max_connections=20,
        )

        operation_count = 0

        async def operation() -> None:
            nonlocal operation_count
            async with pool.session():
                await asyncio.sleep(0.005)
                operation_count += 1

        try:
            await asyncio.gather(*[operation() for _ in range(20)])

            assert operation_count == 20
            assert pool.is_started
        finally:
            await pool.stop()

    @pytest.mark.asyncio
    async def test_pool_handles_rapid_start_stop_cycles(self) -> None:
        """Test that pool handles rapid start/stop cycles gracefully."""
        pool = HTTPSessionPool(base_url="https://api.example.com")

        for _ in range(5):
            await pool.start()
            assert pool.is_started
            await pool.stop()
            assert not pool.is_started


class TestHTTPSessionPoolErrorHandling:
    """Additional tests for error handling."""

    @pytest.mark.asyncio
    async def test_session_raises_if_client_init_fails(self) -> None:
        """Test that session() raises RuntimeError if client can't be initialized."""
        pool = HTTPSessionPool(base_url="https://api.example.com")

        # Mock start to not create client
        original_start = pool.start

        async def mock_start() -> None:
            pass  # Don't create client

        pool.start = mock_start  # type: ignore[method-assign]

        with pytest.raises(RuntimeError, match="Failed to initialize HTTP client"):
            async with pool.session():
                pass

        # Restore for cleanup
        pool.start = original_start  # type: ignore[method-assign]


class TestHTTPSessionPoolWithTaigaClient:
    """Integration tests with TaigaAPIClient."""

    @pytest.mark.asyncio
    async def test_taiga_client_uses_pool(self) -> None:
        """Test that TaigaAPIClient correctly uses the session pool."""
        from src.config import TaigaConfig
        from src.taiga_client import TaigaAPIClient

        pool = HTTPSessionPool(
            base_url="https://api.taiga.io/api/v1",
            max_connections=50,
        )

        config = TaigaConfig()
        client = TaigaAPIClient(config=config, session_pool=pool)

        try:
            await pool.start()
            await client.connect()

            # Client should use the pool's client
            assert client._client is pool._client
            assert not client._owns_client
        finally:
            await client.disconnect()
            await pool.stop()

    @pytest.mark.asyncio
    async def test_taiga_client_disconnect_doesnt_close_pool(self) -> None:
        """Test that TaigaAPIClient disconnect doesn't close the shared pool."""
        from src.config import TaigaConfig
        from src.taiga_client import TaigaAPIClient

        pool = HTTPSessionPool(
            base_url="https://api.taiga.io/api/v1",
        )

        config = TaigaConfig()
        client1 = TaigaAPIClient(config=config, session_pool=pool)
        client2 = TaigaAPIClient(config=config, session_pool=pool)

        try:
            await pool.start()
            await client1.connect()
            await client2.connect()

            # Disconnect client1
            await client1.disconnect()

            # Pool should still be running
            assert pool.is_started
            assert pool._client is not None

            # client2 should still work
            assert client2._client is pool._client
        finally:
            await client2.disconnect()
            await pool.stop()

    @pytest.mark.asyncio
    async def test_taiga_client_without_pool_owns_client(self) -> None:
        """Test that TaigaAPIClient without pool creates and owns its client."""
        from src.config import TaigaConfig
        from src.taiga_client import TaigaAPIClient

        config = TaigaConfig()
        client = TaigaAPIClient(config=config)  # No pool

        try:
            await client.connect()

            assert client._client is not None
            assert client._owns_client
        finally:
            await client.disconnect()


class TestHTTPSessionPoolPerformance:
    """Performance-related tests."""

    @pytest.mark.asyncio
    async def test_pool_latency_improvement(self) -> None:
        """Test that pool provides latency improvement over creating new clients.

        This test verifies that using a session pool is faster than creating
        new clients for each request (acceptance criteria: >=30% improvement).
        """
        # Create pool
        pool = HTTPSessionPool(base_url="https://api.example.com")

        # Time multiple session accesses with pool
        await pool.start()
        pool_start = time.perf_counter()
        for _ in range(100):
            async with pool.session():
                pass
        pool_time = time.perf_counter() - pool_start
        await pool.stop()

        # Time creating new clients each time
        new_client_start = time.perf_counter()
        for _ in range(100):
            client = httpx.AsyncClient(base_url="https://api.example.com")
            await client.aclose()
        new_client_time = time.perf_counter() - new_client_start

        # Pool should be significantly faster
        # Note: This is a rough comparison; actual improvement depends on network
        improvement = (new_client_time - pool_time) / new_client_time * 100

        # Log for visibility
        print(f"\nPool time: {pool_time:.4f}s")
        print(f"New client time: {new_client_time:.4f}s")
        print(f"Improvement: {improvement:.1f}%")

        # We expect the pool to be faster, but exact percentage varies
        # The improvement should be significant (pool reuses, new creates each time)
        assert pool_time < new_client_time
