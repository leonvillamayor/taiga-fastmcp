"""Mock server for Taiga API using respx to mock httpx requests.

This module provides a TaigaMockServer class that sets up mock responses
for Taiga API endpoints, enabling offline integration testing of the
TaigaAPIClient without requiring a real Taiga server.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import httpx
import respx


@dataclass
class MockAuthTokens:
    """Stores authentication tokens for mock responses."""

    auth_token: str = "mock-auth-token-12345"
    refresh_token: str = "mock-refresh-token-67890"
    new_auth_token: str = "mock-refreshed-token-99999"


@dataclass
class MockResponseConfig:
    """Configuration for mock response behavior."""

    # Authentication
    auth_success: bool = True
    auth_tokens: MockAuthTokens = field(default_factory=MockAuthTokens)

    # Error simulation
    simulate_401: bool = False
    simulate_403: bool = False
    simulate_404: bool = False
    simulate_429: bool = False
    rate_limit_retry_after: int = 1

    # Token refresh
    allow_token_refresh: bool = True
    refresh_count: int = 0

    # Rate limiting tracking
    rate_limit_request_count: int = 0
    rate_limit_after_requests: int = 0  # 0 = always rate limit when simulate_429=True

    # Pagination
    total_items: int = 25
    page_size: int = 10

    # Timeout simulation
    simulate_timeout: bool = False
    timeout_request_count: int = 0
    timeout_after_requests: int = 0  # Timeout for first N requests


class TaigaMockServer:
    """Mock server for Taiga API endpoints using respx.

    This class provides a context manager that sets up respx routes
    to mock Taiga API responses for integration testing.

    Usage:
        async with TaigaMockServer() as mock_server:
            client = TaigaAPIClient(base_url="https://api.taiga.io")
            await client.authenticate("user", "pass")

        # Or with custom configuration:
        config = MockResponseConfig(simulate_404=True)
        async with TaigaMockServer(config=config) as mock_server:
            # Test 404 handling
            ...
    """

    BASE_URL = "https://api.taiga.io"

    def __init__(self, config: MockResponseConfig | None = None) -> None:
        """Initialize the mock server with optional configuration.

        Args:
            config: Configuration for mock response behavior.
        """
        self.config = config or MockResponseConfig()
        self._mock: respx.MockRouter | None = None
        self._request_count: int = 0

    async def __aenter__(self) -> TaigaMockServer:
        """Enter the async context and start mocking."""
        self._mock = respx.mock(assert_all_called=False)
        self._mock.start()
        self._setup_routes()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the async context and stop mocking."""
        if self._mock:
            self._mock.stop()

    def _setup_routes(self) -> None:
        """Set up all mock routes for Taiga API endpoints."""
        if not self._mock:
            return

        # Authentication endpoint
        self._mock.post(f"{self.BASE_URL}/api/v1/auth").mock(side_effect=self._handle_auth)

        # Token refresh endpoint
        self._mock.post(f"{self.BASE_URL}/api/v1/auth/refresh").mock(
            side_effect=self._handle_refresh
        )

        # Projects endpoint (with pagination)
        self._mock.get(f"{self.BASE_URL}/api/v1/projects").mock(side_effect=self._handle_projects)

        # Single project endpoint
        self._mock.get(re.compile(rf"{re.escape(self.BASE_URL)}/api/v1/projects/\d+")).mock(
            side_effect=self._handle_single_project
        )

        # User stories endpoint (for pagination testing)
        self._mock.get(re.compile(rf"{re.escape(self.BASE_URL)}/api/v1/userstories")).mock(
            side_effect=self._handle_userstories
        )

        # Generic endpoint for 404 testing
        self._mock.get(re.compile(rf"{re.escape(self.BASE_URL)}/api/v1/nonexistent.*")).mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )

        # Generic endpoint for other resources
        self._mock.route(method="GET").mock(side_effect=self._handle_generic_get)
        self._mock.route(method="POST").mock(side_effect=self._handle_generic_post)
        self._mock.route(method="PATCH").mock(side_effect=self._handle_generic_patch)
        self._mock.route(method="PUT").mock(side_effect=self._handle_generic_put)
        self._mock.route(method="DELETE").mock(side_effect=self._handle_generic_delete)

    def _handle_auth(self, request: httpx.Request) -> httpx.Response:
        """Handle authentication requests."""
        self._request_count += 1

        if self.config.simulate_timeout:
            self.config.timeout_request_count += 1
            if self.config.timeout_request_count <= self.config.timeout_after_requests:
                raise httpx.TimeoutException("Connection timeout", request=request)

        if not self.config.auth_success:
            return httpx.Response(
                401,
                json={"_error_message": "Invalid username or password"},
            )

        return httpx.Response(
            200,
            json={
                "auth_token": self.config.auth_tokens.auth_token,
                "refresh": self.config.auth_tokens.refresh_token,
                "id": 1,
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User",
            },
        )

    def _handle_refresh(self, request: httpx.Request) -> httpx.Response:
        """Handle token refresh requests."""
        self._request_count += 1
        self.config.refresh_count += 1

        if not self.config.allow_token_refresh:
            return httpx.Response(
                401,
                json={"_error_message": "Invalid refresh token"},
            )

        return httpx.Response(
            200,
            json={
                "auth_token": self.config.auth_tokens.new_auth_token,
                "refresh": self.config.auth_tokens.refresh_token,
            },
        )

    def _handle_projects(self, request: httpx.Request) -> httpx.Response:
        """Handle projects list requests with pagination."""
        self._request_count += 1

        # Check for error simulations first
        error_response = self._check_error_simulation(request)
        if error_response:
            return error_response

        # Parse pagination parameters
        params = dict(request.url.params)
        page = int(params.get("page", 1))
        page_size = int(params.get("page_size", self.config.page_size))

        # Calculate pagination
        total_items = self.config.total_items
        total_pages = (total_items + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_items)

        # Generate mock projects
        projects = [
            {
                "id": i + 1,
                "name": f"Project {i + 1}",
                "slug": f"project-{i + 1}",
                "description": f"Description for project {i + 1}",
                "is_private": False,
            }
            for i in range(start_idx, end_idx)
        ]

        # Build response headers for pagination
        headers = {
            "x-pagination-count": str(total_items),
            "x-paginated": "true",
            "x-paginated-by": str(page_size),
            "x-pagination-current": str(page),
        }

        if page < total_pages:
            headers["x-pagination-next"] = "true"

        return httpx.Response(200, json=projects, headers=headers)

    def _handle_single_project(self, request: httpx.Request) -> httpx.Response:
        """Handle single project retrieval."""
        self._request_count += 1

        error_response = self._check_error_simulation(request)
        if error_response:
            return error_response

        # Extract project ID from URL
        match = re.search(r"/projects/(\d+)", str(request.url))
        project_id = int(match.group(1)) if match else 1

        if self.config.simulate_404:
            return httpx.Response(
                404,
                json={"detail": f"Project {project_id} not found"},
            )

        return httpx.Response(
            200,
            json={
                "id": project_id,
                "name": f"Project {project_id}",
                "slug": f"project-{project_id}",
                "description": f"Description for project {project_id}",
                "is_private": False,
            },
        )

    def _handle_userstories(self, request: httpx.Request) -> httpx.Response:
        """Handle user stories list with pagination."""
        self._request_count += 1

        error_response = self._check_error_simulation(request)
        if error_response:
            return error_response

        # Parse pagination parameters
        params = dict(request.url.params)
        page = int(params.get("page", 1))
        page_size = int(params.get("page_size", self.config.page_size))

        # Calculate pagination
        total_items = self.config.total_items
        total_pages = (total_items + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_items)

        # Generate mock user stories
        stories = [
            {
                "id": i + 1,
                "ref": i + 1,
                "subject": f"User Story {i + 1}",
                "description": f"Description for story {i + 1}",
                "status": 1,
                "project": 1,
            }
            for i in range(start_idx, end_idx)
        ]

        headers = {
            "x-pagination-count": str(total_items),
            "x-paginated": "true",
            "x-paginated-by": str(page_size),
            "x-pagination-current": str(page),
        }

        if page < total_pages:
            headers["x-pagination-next"] = "true"

        return httpx.Response(200, json=stories, headers=headers)

    def _check_error_simulation(self, request: httpx.Request) -> httpx.Response | None:
        """Check if an error should be simulated for this request.

        Returns:
            An error response if simulation is active, None otherwise.
        """
        # Timeout simulation
        if self.config.simulate_timeout:
            self.config.timeout_request_count += 1
            if self.config.timeout_request_count <= self.config.timeout_after_requests:
                raise httpx.TimeoutException("Connection timeout", request=request)

        # Rate limiting (429)
        if self.config.simulate_429:
            self.config.rate_limit_request_count += 1
            # If rate_limit_after_requests > 0, only rate limit after that many requests
            if (
                self.config.rate_limit_after_requests == 0
                or self.config.rate_limit_request_count <= self.config.rate_limit_after_requests
            ):
                return httpx.Response(
                    429,
                    json={"_error_message": "Too many requests"},
                    headers={"Retry-After": str(self.config.rate_limit_retry_after)},
                )
            # After N rate-limited requests, succeed
            self.config.simulate_429 = False

        # Unauthorized (401)
        if self.config.simulate_401:
            return httpx.Response(
                401,
                json={"_error_message": "Unauthorized"},
            )

        # Forbidden (403)
        if self.config.simulate_403:
            return httpx.Response(
                403,
                json={"_error_message": "Permission denied"},
            )

        # Not Found (404)
        if self.config.simulate_404:
            return httpx.Response(
                404,
                json={"detail": "Not found"},
            )

        return None

    def _handle_generic_get(self, request: httpx.Request) -> httpx.Response:
        """Handle generic GET requests."""
        self._request_count += 1
        error_response = self._check_error_simulation(request)
        if error_response:
            return error_response
        return httpx.Response(200, json={"message": "OK"})

    def _handle_generic_post(self, request: httpx.Request) -> httpx.Response:
        """Handle generic POST requests."""
        self._request_count += 1
        error_response = self._check_error_simulation(request)
        if error_response:
            return error_response
        return httpx.Response(201, json={"id": 1, "message": "Created"})

    def _handle_generic_patch(self, request: httpx.Request) -> httpx.Response:
        """Handle generic PATCH requests."""
        self._request_count += 1
        error_response = self._check_error_simulation(request)
        if error_response:
            return error_response
        return httpx.Response(200, json={"message": "Updated"})

    def _handle_generic_put(self, request: httpx.Request) -> httpx.Response:
        """Handle generic PUT requests."""
        self._request_count += 1
        error_response = self._check_error_simulation(request)
        if error_response:
            return error_response
        return httpx.Response(200, json={"message": "Replaced"})

    def _handle_generic_delete(self, request: httpx.Request) -> httpx.Response:
        """Handle generic DELETE requests."""
        self._request_count += 1
        error_response = self._check_error_simulation(request)
        if error_response:
            return error_response
        return httpx.Response(204)

    @property
    def request_count(self) -> int:
        """Get the total number of requests handled."""
        return self._request_count

    def reset_counters(self) -> None:
        """Reset all request counters."""
        self._request_count = 0
        self.config.refresh_count = 0
        self.config.rate_limit_request_count = 0
        self.config.timeout_request_count = 0
