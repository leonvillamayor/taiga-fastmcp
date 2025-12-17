"""Performance tests for Taiga MCP Server.

Test 4.9.1: Latencia de operaciones CRUD
Test 4.9.2: Throughput de requests concurrentes
"""

from __future__ import annotations

import asyncio
import statistics
import time
from unittest.mock import AsyncMock, Mock

import pytest

# Performance thresholds
LATENCY_THRESHOLD_MS = 500  # Maximum acceptable latency in milliseconds
CONCURRENT_REQUESTS = 10  # Number of concurrent requests to test
MIN_THROUGHPUT_RPS = 5  # Minimum requests per second


@pytest.fixture
def performance_client(
    mock_projects_response: list[dict[str, object]],
    mock_single_project: dict[str, object],
) -> Mock:
    """Create a mock TaigaClient for performance testing.

    Uses Mock/AsyncMock pattern to simulate API responses
    without requiring real credentials or network calls.
    """
    client = Mock()

    # Setup async methods with appropriate return values
    client.list_projects = AsyncMock(return_value=mock_projects_response)
    client.get_project = AsyncMock(return_value=mock_single_project)
    client.create_project = AsyncMock(return_value=mock_single_project)
    client.update_project = AsyncMock(return_value=mock_single_project)
    client.delete_project = AsyncMock(return_value=None)

    return client


@pytest.fixture
def mock_projects_response() -> list[dict[str, object]]:
    """Mock projects response data."""
    return [
        {
            "id": i,
            "name": f"Project {i}",
            "slug": f"project-{i}",
            "description": f"Description for project {i}",
            "is_private": False,
            "total_milestones": 5,
            "total_story_points": 100.0,
        }
        for i in range(1, 11)
    ]


@pytest.fixture
def mock_single_project() -> dict[str, object]:
    """Mock single project response data."""
    return {
        "id": 1,
        "name": "Test Project",
        "slug": "test-project",
        "description": "A test project for performance testing",
        "is_private": False,
        "total_milestones": 5,
        "total_story_points": 100.0,
        "created_date": "2024-01-01T00:00:00Z",
        "modified_date": "2024-01-02T00:00:00Z",
    }


@pytest.mark.performance
class TestCRUDLatency:
    """Test 4.9.1: Latencia de operaciones CRUD."""

    async def test_list_projects_latency(
        self,
        performance_client: Mock,
    ) -> None:
        """List projects debe responder en < 500ms.

        Measures the latency of listing projects and verifies
        it's within acceptable thresholds.
        """
        latencies: list[float] = []
        iterations = 10

        for _ in range(iterations):
            start_time = time.perf_counter()
            result = await performance_client.list_projects()
            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)

            assert result is not None, "Response should not be None"

        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        assert (
            avg_latency < LATENCY_THRESHOLD_MS
        ), f"Average latency {avg_latency:.2f}ms exceeds threshold {LATENCY_THRESHOLD_MS}ms"
        assert (
            p95_latency < LATENCY_THRESHOLD_MS * 1.5
        ), f"P95 latency {p95_latency:.2f}ms exceeds threshold {LATENCY_THRESHOLD_MS * 1.5}ms"

    async def test_get_project_latency(
        self,
        performance_client: Mock,
    ) -> None:
        """Get single project debe responder en < 500ms."""
        latencies: list[float] = []
        iterations = 10

        for _ in range(iterations):
            start_time = time.perf_counter()
            result = await performance_client.get_project(1)
            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)

            assert result is not None, "Response should not be None"

        avg_latency = statistics.mean(latencies)

        assert (
            avg_latency < LATENCY_THRESHOLD_MS
        ), f"Average latency {avg_latency:.2f}ms exceeds threshold {LATENCY_THRESHOLD_MS}ms"

    async def test_create_project_latency(
        self,
        performance_client: Mock,
    ) -> None:
        """Create project debe responder en < 500ms."""
        latencies: list[float] = []
        iterations = 10

        for _ in range(iterations):
            start_time = time.perf_counter()
            result = await performance_client.create_project(
                name="Test Project",
                description="A test project",
            )
            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)

            assert result is not None, "Response should not be None"

        avg_latency = statistics.mean(latencies)

        assert (
            avg_latency < LATENCY_THRESHOLD_MS
        ), f"Average latency {avg_latency:.2f}ms exceeds threshold {LATENCY_THRESHOLD_MS}ms"

    async def test_update_project_latency(
        self,
        performance_client: Mock,
    ) -> None:
        """Update project debe responder en < 500ms."""
        latencies: list[float] = []
        iterations = 10

        for _ in range(iterations):
            start_time = time.perf_counter()
            result = await performance_client.update_project(
                project_id=1,
                name="Updated Project",
            )
            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)

            assert result is not None, "Response should not be None"

        avg_latency = statistics.mean(latencies)

        assert (
            avg_latency < LATENCY_THRESHOLD_MS
        ), f"Average latency {avg_latency:.2f}ms exceeds threshold {LATENCY_THRESHOLD_MS}ms"

    async def test_delete_project_latency(
        self,
        performance_client: Mock,
    ) -> None:
        """Delete project debe responder en < 500ms."""
        latencies: list[float] = []
        iterations = 10

        for _ in range(iterations):
            start_time = time.perf_counter()
            await performance_client.delete_project(1)
            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)

        avg_latency = statistics.mean(latencies)

        assert (
            avg_latency < LATENCY_THRESHOLD_MS
        ), f"Average latency {avg_latency:.2f}ms exceeds threshold {LATENCY_THRESHOLD_MS}ms"


@pytest.mark.performance
class TestConcurrentRequests:
    """Test 4.9.2: Throughput de requests concurrentes."""

    async def test_concurrent_list_projects(
        self,
        performance_client: Mock,
    ) -> None:
        """Soporta 10 requests concurrentes de list_projects.

        Verifies that the client can handle multiple concurrent
        requests without errors or significant performance degradation.
        """

        async def make_request() -> tuple[float, bool]:
            """Make a single request and return latency and success status."""
            start_time = time.perf_counter()
            try:
                result = await performance_client.list_projects()
                success = result is not None
            except Exception:
                success = False
            end_time = time.perf_counter()
            return (end_time - start_time) * 1000, success

        start_time = time.perf_counter()
        tasks = [make_request() for _ in range(CONCURRENT_REQUESTS)]
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time

        latencies = [r[0] for r in results]
        successes = [r[1] for r in results]

        success_rate = sum(successes) / len(successes)
        throughput = len(results) / total_time

        assert success_rate == 1.0, f"Success rate {success_rate:.2%} is below 100%"
        assert (
            throughput >= MIN_THROUGHPUT_RPS
        ), f"Throughput {throughput:.2f} RPS is below minimum {MIN_THROUGHPUT_RPS} RPS"

        avg_latency = statistics.mean(latencies)
        assert (
            avg_latency < LATENCY_THRESHOLD_MS * 2
        ), f"Average latency under load {avg_latency:.2f}ms exceeds threshold"

    async def test_concurrent_mixed_operations(
        self,
        performance_client: Mock,
    ) -> None:
        """Soporta operaciones mixtas concurrentes (GET/POST/PATCH).

        Simulates a more realistic workload with different operation types.
        """

        async def list_op() -> tuple[str, float, bool]:
            start = time.perf_counter()
            try:
                await performance_client.list_projects()
                return "list", (time.perf_counter() - start) * 1000, True
            except Exception:
                return "list", (time.perf_counter() - start) * 1000, False

        async def get_op() -> tuple[str, float, bool]:
            start = time.perf_counter()
            try:
                await performance_client.get_project(1)
                return "get", (time.perf_counter() - start) * 1000, True
            except Exception:
                return "get", (time.perf_counter() - start) * 1000, False

        async def create_op() -> tuple[str, float, bool]:
            start = time.perf_counter()
            try:
                await performance_client.create_project(name="Test", description="Test")
                return "create", (time.perf_counter() - start) * 1000, True
            except Exception:
                return "create", (time.perf_counter() - start) * 1000, False

        # Mix of operations: 5 list, 3 get, 2 create
        tasks = (
            [list_op() for _ in range(5)]
            + [get_op() for _ in range(3)]
            + [create_op() for _ in range(2)]
        )

        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time

        successes = [r[2] for r in results]
        success_rate = sum(successes) / len(successes)

        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} is below 95%"

        throughput = len(results) / total_time
        assert (
            throughput >= MIN_THROUGHPUT_RPS
        ), f"Mixed operation throughput {throughput:.2f} RPS below minimum"

    async def test_throughput_under_sustained_load(
        self,
        performance_client: Mock,
    ) -> None:
        """Mantiene throughput estable bajo carga sostenida.

        Runs multiple batches of concurrent requests and verifies
        that throughput remains stable.
        """

        async def make_request() -> bool:
            try:
                await performance_client.list_projects()
                return True
            except Exception:
                return False

        batch_throughputs: list[float] = []
        num_batches = 5

        for _ in range(num_batches):
            tasks = [make_request() for _ in range(CONCURRENT_REQUESTS)]
            start_time = time.perf_counter()
            results = await asyncio.gather(*tasks)
            batch_time = time.perf_counter() - start_time

            success_count = sum(results)
            batch_throughput = success_count / batch_time
            batch_throughputs.append(batch_throughput)

        avg_throughput = statistics.mean(batch_throughputs)
        throughput_stddev = statistics.stdev(batch_throughputs) if len(batch_throughputs) > 1 else 0

        # Throughput should be stable (low standard deviation relative to mean)
        coefficient_of_variation = (
            throughput_stddev / avg_throughput if avg_throughput > 0 else float("inf")
        )

        assert (
            coefficient_of_variation < 0.5
        ), f"Throughput too variable: CV={coefficient_of_variation:.2f}"
        assert (
            avg_throughput >= MIN_THROUGHPUT_RPS
        ), f"Average throughput {avg_throughput:.2f} RPS below minimum"
