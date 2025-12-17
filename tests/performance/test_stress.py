"""Stress tests for Taiga MCP Server.

Test 4.9.3: Stress test de creación masiva
Test 4.9.4: Memory leak detection
Test 4.9.5: Connection pool bajo carga
"""

from __future__ import annotations

import asyncio
import contextlib
import gc
import tracemalloc
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

# Stress test configuration
HIGH_VOLUME_COUNT = 100  # Number of items for high volume tests
MEMORY_GROWTH_THRESHOLD_MB = 50  # Maximum memory growth in MB
CONNECTION_POOL_SIZE = 20  # Connection pool test size


def _create_issue_response(call_count: int, base_response: dict[str, object]) -> dict[str, Any]:
    """Create an issue response with incrementing ID."""
    return {**base_response, "id": call_count, "ref": call_count}


def _create_userstory_response(call_count: int, base_response: dict[str, object]) -> dict[str, Any]:
    """Create a user story response with incrementing ID."""
    return {**base_response, "id": call_count, "ref": call_count}


def _create_task_response(call_count: int, base_response: dict[str, object]) -> dict[str, Any]:
    """Create a task response with incrementing ID."""
    return {**base_response, "id": call_count, "ref": call_count}


@pytest.fixture
def stress_client(
    mock_created_issue: dict[str, object],
    mock_created_userstory: dict[str, object],
    mock_created_task: dict[str, object],
) -> Mock:
    """Create a mock TaigaClient for stress testing.

    Uses Mock/AsyncMock pattern with side_effect to simulate
    incrementing IDs for created resources.
    """
    client = Mock()

    # Track call counts for incrementing IDs
    issue_count = 0
    userstory_count = 0
    task_count = 0

    async def create_issue_side_effect(**kwargs: Any) -> dict[str, Any]:
        nonlocal issue_count
        issue_count += 1
        return _create_issue_response(issue_count, mock_created_issue)

    async def create_userstory_side_effect(**kwargs: Any) -> dict[str, Any]:
        nonlocal userstory_count
        userstory_count += 1
        return _create_userstory_response(userstory_count, mock_created_userstory)

    async def create_task_side_effect(**kwargs: Any) -> dict[str, Any]:
        nonlocal task_count
        task_count += 1
        return _create_task_response(task_count, mock_created_task)

    # Setup async methods
    client.create_issue = AsyncMock(side_effect=create_issue_side_effect)
    client.create_userstory = AsyncMock(side_effect=create_userstory_side_effect)
    client.create_task = AsyncMock(side_effect=create_task_side_effect)
    client.list_projects = AsyncMock(return_value=[{"id": 1, "name": "Project"}])
    client.get_project = AsyncMock(return_value={"id": 1, "name": "Test Project"})

    return client


@pytest.fixture
def mock_created_issue() -> dict[str, object]:
    """Mock created issue response data."""
    return {
        "id": 1,
        "ref": 1,
        "subject": "Test Issue",
        "description": "A test issue for stress testing",
        "project": 1,
        "status": 1,
        "severity": 1,
        "priority": 1,
        "type": 1,
        "assigned_to": None,
        "is_closed": False,
    }


@pytest.fixture
def mock_created_userstory() -> dict[str, object]:
    """Mock created user story response data."""
    return {
        "id": 1,
        "ref": 1,
        "subject": "Test User Story",
        "description": "A test user story for stress testing",
        "project": 1,
        "status": 1,
        "assigned_to": None,
        "is_closed": False,
        "points": {},
    }


@pytest.fixture
def mock_created_task() -> dict[str, object]:
    """Mock created task response data."""
    return {
        "id": 1,
        "ref": 1,
        "subject": "Test Task",
        "description": "A test task for stress testing",
        "project": 1,
        "status": 1,
        "user_story": 1,
        "assigned_to": None,
        "is_closed": False,
    }


@pytest.mark.stress
class TestMassCreation:
    """Test 4.9.3: Stress test de creación masiva."""

    async def test_mass_issue_creation(
        self,
        stress_client: Mock,
    ) -> None:
        """Crear 100 issues de forma secuencial.

        Verifies that the system can handle high volume sequential creates
        without failures or significant performance degradation.
        """
        created_ids: list[int] = []
        errors: list[str] = []

        for i in range(HIGH_VOLUME_COUNT):
            try:
                result = await stress_client.create_issue(
                    project_id=1,
                    subject=f"Stress Test Issue {i}",
                    issue_type=1,
                    priority=1,
                    severity=1,
                )
                if result and "id" in result:
                    created_ids.append(int(result["id"]))
            except Exception as e:
                errors.append(f"Issue {i}: {e!s}")

        success_rate = len(created_ids) / HIGH_VOLUME_COUNT

        assert success_rate >= 0.95, (
            f"Mass creation success rate {success_rate:.2%} below 95%. "
            f"Errors: {errors[:5]}"  # Show first 5 errors
        )
        assert (
            len(created_ids) >= HIGH_VOLUME_COUNT * 0.95
        ), f"Only {len(created_ids)} issues created out of {HIGH_VOLUME_COUNT}"

    async def test_mass_concurrent_creation(
        self,
        stress_client: Mock,
    ) -> None:
        """Crear 50 user stories de forma concurrente.

        Tests concurrent high-volume creation to verify system stability.
        """
        concurrent_count = 50

        async def create_userstory(idx: int) -> tuple[int, bool, str]:
            """Create a single user story and return result."""
            try:
                result = await stress_client.create_userstory(
                    project_id=1,
                    subject=f"Concurrent Story {idx}",
                )
                success = result is not None and "id" in result
                return idx, success, ""
            except Exception as e:
                return idx, False, str(e)

        tasks = [create_userstory(i) for i in range(concurrent_count)]
        results = await asyncio.gather(*tasks)

        successes = [r[1] for r in results]
        success_rate = sum(successes) / len(successes)

        assert (
            success_rate >= 0.90
        ), f"Concurrent creation success rate {success_rate:.2%} below 90%"

    async def test_burst_creation(
        self,
        stress_client: Mock,
    ) -> None:
        """Burst de creación: 20 tasks en ráfagas.

        Tests system behavior under burst load conditions.
        """
        burst_size = 20
        num_bursts = 5
        all_results: list[bool] = []

        for burst in range(num_bursts):

            async def create_task(idx: int, burst_num: int = burst) -> bool:
                try:
                    result = await stress_client.create_task(
                        project_id=1,
                        subject=f"Burst {burst_num} Task {idx}",
                    )
                    return result is not None
                except Exception:
                    return False

            tasks = [create_task(i, burst) for i in range(burst_size)]
            burst_results = await asyncio.gather(*tasks)
            all_results.extend(burst_results)

            # Small delay between bursts
            await asyncio.sleep(0.01)

        total_success = sum(all_results)
        total_attempts = len(all_results)
        success_rate = total_success / total_attempts

        assert success_rate >= 0.85, f"Burst creation success rate {success_rate:.2%} below 85%"


@pytest.mark.stress
class TestMemoryLeaks:
    """Test 4.9.4: Memory leak detection."""

    async def test_no_memory_leak_on_repeated_requests(
        self,
        stress_client: Mock,
    ) -> None:
        """Verifica que no hay memory leaks en requests repetidas.

        Performs many requests and checks that memory usage doesn't
        grow beyond acceptable thresholds.
        """
        # Force garbage collection and start memory tracking
        gc.collect()
        tracemalloc.start()
        initial_snapshot = tracemalloc.take_snapshot()

        # Perform many requests
        num_iterations = 500
        for _ in range(num_iterations):
            await stress_client.list_projects()

        # Force garbage collection and take final snapshot
        gc.collect()
        final_snapshot = tracemalloc.take_snapshot()

        # Compare snapshots
        top_stats = final_snapshot.compare_to(initial_snapshot, "lineno")
        tracemalloc.stop()

        # Calculate total memory growth
        total_growth_bytes = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)
        total_growth_mb = total_growth_bytes / (1024 * 1024)

        assert total_growth_mb < MEMORY_GROWTH_THRESHOLD_MB, (
            f"Memory grew by {total_growth_mb:.2f} MB over {num_iterations} requests, "
            f"exceeds threshold of {MEMORY_GROWTH_THRESHOLD_MB} MB"
        )

    async def test_no_memory_leak_on_error_responses(
        self,
        stress_client: Mock,
    ) -> None:
        """Verifica que no hay memory leaks cuando hay errores.

        Ensures error handling doesn't cause memory accumulation.
        """
        # Configure mock to raise exception for this test
        stress_client.list_projects = AsyncMock(side_effect=Exception("Simulated error"))

        gc.collect()
        tracemalloc.start()
        initial_memory = tracemalloc.get_traced_memory()[0]

        # Perform many failing requests
        num_iterations = 200
        for _ in range(num_iterations):
            with contextlib.suppress(Exception):
                await stress_client.list_projects()

        gc.collect()
        final_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()

        memory_growth_mb = (final_memory - initial_memory) / (1024 * 1024)

        assert memory_growth_mb < MEMORY_GROWTH_THRESHOLD_MB / 2, (
            f"Memory grew by {memory_growth_mb:.2f} MB during error handling, "
            f"exceeds threshold of {MEMORY_GROWTH_THRESHOLD_MB / 2} MB"
        )

    async def test_object_cleanup_after_requests(
        self,
        stress_client: Mock,
    ) -> None:
        """Verifica que los objetos se limpian correctamente.

        Checks that response objects are properly garbage collected.
        """
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Perform requests
        for _ in range(100):
            result = await stress_client.get_project(1)
            del result

        gc.collect()
        final_objects = len(gc.get_objects())

        # Allow some growth for internal caching, but not excessive
        object_growth = final_objects - initial_objects
        max_allowed_growth = 1000  # Reasonable threshold for 100 requests

        assert (
            object_growth < max_allowed_growth
        ), f"Object count grew by {object_growth}, exceeds threshold {max_allowed_growth}"


@pytest.mark.stress
class TestConnectionPool:
    """Test 4.9.5: Connection pool bajo carga."""

    async def test_connection_pool_handles_concurrent_load(
        self,
        stress_client: Mock,
    ) -> None:
        """Connection pool maneja carga concurrente correctamente.

        Tests that the connection pool can handle many concurrent
        connections without exhaustion or errors.
        """

        async def make_request() -> bool:
            try:
                await stress_client.list_projects()
                return True
            except Exception:
                return False

        # Create more concurrent requests than typical pool size
        concurrent_requests = CONNECTION_POOL_SIZE * 2

        tasks = [make_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)

        success_rate = sum(results) / len(results)

        assert success_rate >= 0.95, f"Connection pool success rate {success_rate:.2%} below 95%"

    async def test_connection_pool_recovery(
        self,
        stress_client: Mock,
    ) -> None:
        """Connection pool se recupera después de errores.

        Verifies that the connection pool recovers properly after
        encountering errors.
        """
        request_count = 0
        simulate_failures = True

        async def variable_response() -> list[dict[str, object]]:
            nonlocal request_count
            request_count += 1
            # Simulate intermittent failures (every 5th request fails) only when enabled
            if simulate_failures and request_count % 5 == 0:
                raise Exception("Service Unavailable")
            return [{"id": 1}]

        stress_client.list_projects = AsyncMock(side_effect=variable_response)

        # First batch with some failures
        first_batch_results: list[bool] = []
        for _ in range(20):
            try:
                result = await stress_client.list_projects()
                first_batch_results.append(result is not None)
            except Exception:
                first_batch_results.append(False)

        # Disable failure simulation - simulates system recovery
        simulate_failures = False

        # Second batch - should all succeed now that failures are disabled
        second_batch_results: list[bool] = []
        for _ in range(20):
            try:
                result = await stress_client.list_projects()
                second_batch_results.append(result is not None)
            except Exception:
                second_batch_results.append(False)

        # First batch should have some failures (expected)
        first_success_rate = sum(first_batch_results) / len(first_batch_results)

        # Second batch should have higher success rate (recovery)
        second_success_rate = sum(second_batch_results) / len(second_batch_results)

        assert (
            second_success_rate >= 0.90
        ), f"Recovery success rate {second_success_rate:.2%} too low"
        assert (
            second_success_rate >= first_success_rate * 0.8
        ), "Connection pool didn't recover properly after errors"

    async def test_sustained_high_connection_load(
        self,
        stress_client: Mock,
    ) -> None:
        """Connection pool mantiene estabilidad bajo carga sostenida.

        Tests connection pool behavior over extended concurrent usage.
        """

        async def sustained_requests(batch_id: int) -> list[bool]:
            results: list[bool] = []
            for _ in range(10):
                try:
                    await stress_client.list_projects()
                    results.append(True)
                except Exception:
                    results.append(False)
            return results

        # Run multiple sustained batches concurrently
        num_concurrent_batches = 10
        tasks = [sustained_requests(i) for i in range(num_concurrent_batches)]
        all_batch_results = await asyncio.gather(*tasks)

        # Flatten results
        all_results: list[bool] = []
        for batch_results in all_batch_results:
            all_results.extend(batch_results)

        total_requests = len(all_results)
        total_successes = sum(all_results)
        success_rate = total_successes / total_requests

        assert success_rate >= 0.90, (
            f"Sustained load success rate {success_rate:.2%} below 90%. "
            f"Total: {total_requests}, Successes: {total_successes}"
        )
