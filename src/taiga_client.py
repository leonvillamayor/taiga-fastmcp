"""
Taiga API client implementation.

This module provides a fully typed HTTP client for interacting with the Taiga API.
All methods have explicit type hints for parameters and return values.
"""

import asyncio
import time

# Import TYPE_CHECKING to avoid circular imports
from typing import TYPE_CHECKING, Any, cast

import httpx
from httpx import AsyncClient, Response

from src.config import TaigaConfig
from src.domain.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
    ResourceNotFoundError,
    TaigaAPIError,
)
from src.infrastructure.logging import get_logger
from src.infrastructure.retry import RetryConfig, calculate_delay


if TYPE_CHECKING:
    from src.infrastructure.http_session_pool import HTTPSessionPool


class TaigaAPIClient:
    """
    HTTP client for interacting with the Taiga API.

    Handles authentication, request retry logic, and error handling.
    """

    def __init__(
        self,
        config: TaigaConfig | None = None,
        session_pool: "HTTPSessionPool | None" = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """
        Initialize Taiga API client.

        Args:
            config: Configuration object with API settings.
            session_pool: Optional HTTP session pool for connection reuse.
                         If provided, the client will use the pool instead of
                         creating its own HTTP client.
            retry_config: Configuration for retry behavior with exponential backoff.
                         If not provided, uses default RetryConfig values.
        """
        self.config = config or TaigaConfig()
        self.base_url = self.config.taiga_api_url
        self.auth_token: str | None = self.config.taiga_auth_token
        self.refresh_token: str | None = None
        self._client: AsyncClient | None = None
        self._session_pool = session_pool
        self._owns_client: bool = session_pool is None
        self._logger = get_logger("taiga_client")
        self._retry_config = retry_config or RetryConfig(
            max_retries=self.config.max_retries,
            base_delay=1.0,
            max_delay=60.0,
            jitter=True,
        )

    async def __aenter__(self) -> "TaigaAPIClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Async context manager exit."""
        await self.disconnect()

    def _handle_response(self, response: Response) -> Response:
        """Handle HTTP response and raise appropriate exceptions."""
        if response.status_code == 404:
            raise ResourceNotFoundError("Not Found")
        if response.status_code == 500:
            raise TaigaAPIError("Server Error", status_code=500)
        if response.status_code >= 400:
            try:
                error_data = response.json()
            except Exception:
                error_data = response.text
            raise TaigaAPIError(
                f"HTTP {response.status_code}: {error_data}", status_code=response.status_code
            )
        return response

    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers (private method for backward compatibility)."""
        return self.get_auth_headers()

    def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Make HTTP request with retry logic (synchronous)."""
        import requests

        # Build full URL if relative
        if url.startswith("/"):
            url = f"{self.base_url}{url}"

        headers = self._get_auth_headers()
        if headers:
            kwargs["headers"] = {**kwargs.get("headers", {}), **headers}

        # Simple retry logic with patch for testing
        max_retries = 3
        # Extract timeout from kwargs or use config default (B113 fix)
        request_timeout: float = kwargs.pop("timeout", self.config.timeout)

        for i in range(max_retries):
            try:
                # Use requests.get directly for GET to allow patching
                if method.upper() == "GET":
                    response = requests.get(url, timeout=request_timeout, **kwargs)
                else:
                    response = requests.request(method, url, timeout=request_timeout, **kwargs)
                return response.json() if hasattr(response, "json") else response
            except requests.Timeout:
                if i == max_retries - 1:
                    raise
                continue
            except Exception:
                if i == max_retries - 1:
                    raise
                continue
        return None

    async def connect(self) -> None:
        """Initialize HTTP client.

        If a session pool was provided, obtains a client from the pool.
        Otherwise, creates a new HTTP client.
        """
        if not self._client:
            self._logger.debug(f"Connecting to Taiga API at {self.base_url}")

            if self._session_pool is not None:
                # Use the shared session pool
                if not self._session_pool.is_started:
                    await self._session_pool.start()
                self._client = self._session_pool._client
                self._owns_client = False
                self._logger.info(f"Connected to Taiga API at {self.base_url} using session pool")
            else:
                # Create own client
                self._client = httpx.AsyncClient(
                    base_url=self.base_url,
                    timeout=httpx.Timeout(self.config.timeout),
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                )
                self._owns_client = True
                self._logger.info(f"Connected to Taiga API at {self.base_url}")

    async def disconnect(self) -> None:
        """Close HTTP client.

        Only closes the client if it owns it (not using session pool).
        When using a session pool, the pool manages the client lifecycle.
        """
        if self._client:
            self._logger.debug("Disconnecting from Taiga API")
            if self._owns_client:
                # Only close if we own the client
                await self._client.aclose()
                self._logger.info("Disconnected from Taiga API")
            else:
                self._logger.debug("Not closing client - managed by session pool")
            self._client = None

    async def authenticate(
        self, username: str | None = None, password: str | None = None
    ) -> dict[str, Any]:
        """
        Authenticate with Taiga API.

        Args:
            username: Taiga username (email)
            password: Taiga password

        Returns:
            Authentication response with tokens

        Raises:
            AuthenticationError: If authentication fails
        """
        username = username or self.config.taiga_username
        password = password or self.config.taiga_password

        if not username or not password:
            self._logger.error("Authentication failed: username and password are required")
            raise AuthenticationError("Username and password are required for authentication")

        self._logger.debug(f"Attempting authentication for user: {username}")
        await self.connect()
        assert self._client is not None, "Client not initialized after connect()"

        try:
            response = await self._client.post(
                "/auth", json={"type": "normal", "username": username, "password": password}
            )
            response.raise_for_status()

            data = cast("dict[str, Any]", response.json())
            self.auth_token = data.get("auth_token")
            self.refresh_token = data.get("refresh")
            self._logger.info(f"Authentication successful for user: {username}")
            return data

        except httpx.HTTPStatusError as e:
            self._logger.error(
                f"Authentication HTTP error for user {username}: "
                f"status={e.response.status_code}, response={e.response.text}"
            )
            if e.response.status_code in [400, 401, 403]:
                raise AuthenticationError(f"Authentication failed: {e.response.text}") from e
            raise TaigaAPIError(
                f"Authentication error: {e!s}",
                status_code=e.response.status_code,
                response_body=e.response.text,
            ) from e
        except Exception as e:
            self._logger.error(f"Authentication unexpected error for user {username}: {e!s}")
            raise TaigaAPIError(f"Authentication error: {e!s}") from e

    async def refresh_auth_token(self) -> dict[str, Any]:
        """
        Refresh authentication token.

        Returns:
            New authentication tokens

        Raises:
            AuthenticationError: If refresh fails
        """
        if not self.refresh_token:
            self._logger.error("Token refresh failed: no refresh token available")
            raise AuthenticationError("No refresh token available")

        self._logger.debug("Attempting to refresh authentication token")
        await self.connect()
        assert self._client is not None, "Client not initialized after connect()"

        try:
            response = await self._client.post(
                "/auth/refresh", json={"refresh": self.refresh_token}
            )
            response.raise_for_status()

            data = cast("dict[str, Any]", response.json())
            self.auth_token = data.get("auth_token")
            self.refresh_token = data.get("refresh")
            self._logger.info("Authentication token refreshed successfully")
            return data

        except httpx.HTTPStatusError as e:
            self._logger.error(
                f"Token refresh HTTP error: status={e.response.status_code}, response={e.response.text}"
            )
            raise AuthenticationError(f"Token refresh failed: {e.response.text}") from e
        except Exception as e:
            self._logger.error(f"Token refresh unexpected error: {e!s}")
            raise TaigaAPIError(f"Token refresh error: {e!s}") from e

    def _get_headers(self) -> dict[str, str]:
        """Get headers for authenticated requests."""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        retry_count: int = 0,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            retry_count: Current retry attempt
            headers: Additional headers to include in the request

        Returns:
            HTTP response

        Raises:
            TaigaAPIError: On request failure
        """
        await self.connect()

        # Assert client is connected after connect()
        assert self._client is not None, "Client not initialized after connect()"

        # Merge auth headers with custom headers
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)

        # Log request start
        retry_info = f" (retry {retry_count})" if retry_count > 0 else ""
        self._logger.debug(f"[API] {method} {endpoint}{retry_info}")

        start_time = time.perf_counter()

        try:
            if method == "GET":
                response = await self._client.get(endpoint, params=params, headers=request_headers)
            elif method == "POST":
                response = await self._client.post(
                    endpoint, json=data, params=params, headers=request_headers
                )
            elif method == "PUT":
                response = await self._client.put(
                    endpoint, json=data, params=params, headers=request_headers
                )
            elif method == "PATCH":
                response = await self._client.patch(
                    endpoint, json=data, params=params, headers=request_headers
                )
            elif method == "DELETE":
                response = await self._client.delete(
                    endpoint, params=params, headers=request_headers
                )
            else:
                self._logger.error(f"Unsupported HTTP method: {method}")
                raise ValueError(f"Unsupported HTTP method: {method}")

            duration = time.perf_counter() - start_time

            # Handle rate limiting
            if response.status_code == 429:
                if retry_count < self.config.max_retries:
                    # Wait and retry
                    retry_after = int(response.headers.get("Retry-After", 5))
                    self._logger.warning(
                        f"[API] {method} {endpoint} | status=429 Rate Limited | "
                        f"retry_after={retry_after}s | duration={duration:.3f}s"
                    )
                    await asyncio.sleep(retry_after)
                    return await self._make_request(
                        method, endpoint, data, params, retry_count + 1, headers
                    )
                self._logger.error(
                    f"[API] {method} {endpoint} | status=429 Rate limit exceeded after {retry_count} retries"
                )
                raise RateLimitError(f"Rate limit exceeded after {retry_count} retries")

            # Handle authentication errors
            if response.status_code == 401:
                # Try to refresh token once
                if retry_count == 0 and self.refresh_token:
                    self._logger.warning(
                        f"[API] {method} {endpoint} | status=401 | "
                        f"Attempting token refresh | duration={duration:.3f}s"
                    )
                    await self.refresh_auth_token()
                    return await self._make_request(
                        method, endpoint, data, params, retry_count + 1, headers
                    )
                self._logger.error(
                    f"[API] {method} {endpoint} | status=401 Authentication failed | duration={duration:.3f}s"
                )
                raise AuthenticationError("Authentication failed")

            # Handle not found
            if response.status_code == 404:
                self._logger.warning(
                    f"[API] {method} {endpoint} | status=404 Not Found | duration={duration:.3f}s"
                )
                raise ResourceNotFoundError(f"Resource not found: {endpoint}")

            # Handle forbidden
            if response.status_code == 403:
                self._logger.warning(
                    f"[API] {method} {endpoint} | status=403 Permission Denied | duration={duration:.3f}s"
                )
                raise PermissionDeniedError(f"Permission denied: {endpoint}")

            # Raise for other HTTP errors
            response.raise_for_status()

            # Log successful request
            self._logger.info(
                f"[API] {method} {endpoint} | status={response.status_code} | duration={duration:.3f}s"
            )
            return response

        except httpx.TimeoutException as e:
            duration = time.perf_counter() - start_time
            if retry_count < self._retry_config.max_retries:
                # Calculate delay using exponential backoff with jitter
                delay = calculate_delay(
                    attempt=retry_count,
                    base_delay=self._retry_config.base_delay,
                    max_delay=self._retry_config.max_delay,
                    exponential_base=self._retry_config.exponential_base,
                    jitter=self._retry_config.jitter,
                )
                self._logger.warning(
                    f"[API] {method} {endpoint} | Timeout | "
                    f"retry={retry_count + 1}/{self._retry_config.max_retries} | "
                    f"delay={delay:.2f}s | duration={duration:.3f}s"
                )
                await asyncio.sleep(delay)
                return await self._make_request(
                    method, endpoint, data, params, retry_count + 1, headers
                )
            self._logger.error(
                f"[API] {method} {endpoint} | Timeout after {retry_count} retries | "
                f"error={e!s} | duration={duration:.3f}s"
            )
            raise TaigaAPIError(f"Request timeout after {retry_count} retries: {e!s}") from e

        except httpx.HTTPStatusError as e:
            duration = time.perf_counter() - start_time
            self._logger.error(
                f"[API] {method} {endpoint} | status={e.response.status_code} | "
                f"error={e!s} | duration={duration:.3f}s"
            )
            # Already handled specific status codes above
            raise TaigaAPIError(
                f"HTTP error: {e!s}",
                status_code=e.response.status_code,
                response_body=e.response.text,
            ) from e

        except Exception as e:
            duration = time.perf_counter() - start_time
            if isinstance(
                e,
                AuthenticationError
                | ResourceNotFoundError
                | PermissionDeniedError
                | RateLimitError
                | TaigaAPIError,
            ):
                raise
            self._logger.error(
                f"[API] {method} {endpoint} | Unexpected error | "
                f"error={type(e).__name__}: {e!s} | duration={duration:.3f}s"
            )
            raise TaigaAPIError(f"Request error: {e!s}") from e

    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Make GET request.

        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers to include in the request

        Returns:
            JSON response data
        """
        response = await self._make_request("GET", endpoint, params=params, headers=headers)
        return cast("dict[str, Any] | list[Any]", response.json())

    async def post(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Make POST request.

        Args:
            endpoint: API endpoint
            data: Request body data
            params: Query parameters

        Returns:
            JSON response data
        """
        response = await self._make_request("POST", endpoint, data=data, params=params)
        if response.status_code == 204 or not response.content:
            return {}
        return cast("dict[str, Any] | list[Any]", response.json())

    async def put(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Make PUT request.

        Args:
            endpoint: API endpoint
            data: Request body data
            params: Query parameters

        Returns:
            JSON response data
        """
        response = await self._make_request("PUT", endpoint, data=data, params=params)
        if response.status_code == 204 or not response.content:
            return {}
        return cast("dict[str, Any] | list[Any]", response.json())

    async def patch(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Make PATCH request.

        Args:
            endpoint: API endpoint
            data: Request body data
            params: Query parameters

        Returns:
            JSON response data
        """
        response = await self._make_request("PATCH", endpoint, data=data, params=params)
        if response.status_code == 204 or not response.content:
            return {}
        return cast("dict[str, Any] | list[Any]", response.json())

    async def get_raw(self, endpoint: str, params: dict[str, Any] | None = None) -> bytes:
        """
        Get raw bytes from endpoint.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Raw bytes response
        """
        response = await self._make_request("GET", endpoint, params=params)
        return response.content

    async def delete(self, endpoint: str, params: dict[str, Any] | None = None) -> bool:
        """
        Make DELETE request.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            True if successful
        """
        response = await self._make_request("DELETE", endpoint, params=params)
        return response.status_code in [200, 204]

    # Project endpoints
    async def list_projects(
        self,
        member: int | None = None,
        is_private: bool | None = None,
        is_backlog_activated: bool | None = None,
    ) -> list[dict[str, Any]]:
        """List user projects."""
        params = {}
        if member is not None:
            params["member"] = member
        if is_private is not None:
            params["is_private"] = is_private
        if is_backlog_activated is not None:
            params["is_backlog_activated"] = is_backlog_activated
        return cast("list[dict[str, Any]]", await self.get("/projects", params=params))

    async def get_project(self, project_id: int) -> dict[str, Any]:
        """Get project details."""
        return cast("dict[str, Any]", await self.get(f"/projects/{project_id}"))

    async def create_project(
        self,
        name: str,
        description: str | None = None,
        is_backlog_activated: bool | None = None,
        is_issues_activated: bool | None = None,
        is_kanban_activated: bool | None = None,
        is_private: bool | None = None,
        is_wiki_activated: bool | None = None,
        total_milestones: int | None = None,
        total_story_points: float | None = None,
        videoconferences: str | None = None,
        videoconferences_extra_data: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new project.

        Args:
            name: Project name (required)
            description: Project description
            is_backlog_activated: Enable backlog module
            is_issues_activated: Enable issues module
            is_kanban_activated: Enable kanban module
            is_private: Whether the project is private
            is_wiki_activated: Enable wiki module
            total_milestones: Total number of milestones
            total_story_points: Total story points
            videoconferences: Videoconference system
            videoconferences_extra_data: Extra data for videoconferences
            tags: List of tags

        Returns:
            Created project data
        """
        data: dict[str, Any] = {"name": name}
        if description is not None:
            data["description"] = description
        if is_backlog_activated is not None:
            data["is_backlog_activated"] = is_backlog_activated
        if is_issues_activated is not None:
            data["is_issues_activated"] = is_issues_activated
        if is_kanban_activated is not None:
            data["is_kanban_activated"] = is_kanban_activated
        if is_private is not None:
            data["is_private"] = is_private
        if is_wiki_activated is not None:
            data["is_wiki_activated"] = is_wiki_activated
        if total_milestones is not None:
            data["total_milestones"] = total_milestones
        if total_story_points is not None:
            data["total_story_points"] = total_story_points
        if videoconferences is not None:
            data["videoconferences"] = videoconferences
        if videoconferences_extra_data is not None:
            data["videoconferences_extra_data"] = videoconferences_extra_data
        if tags is not None:
            data["tags"] = tags
        return cast("dict[str, Any]", await self.post("/projects", data=data))

    async def update_project(
        self,
        project_id: int,
        name: str | None = None,
        description: str | None = None,
        is_backlog_activated: bool | None = None,
        is_issues_activated: bool | None = None,
        is_kanban_activated: bool | None = None,
        is_private: bool | None = None,
        is_wiki_activated: bool | None = None,
        total_milestones: int | None = None,
        total_story_points: float | None = None,
        videoconferences: str | None = None,
        videoconferences_extra_data: str | None = None,
    ) -> dict[str, Any]:
        """
        Update a project (partial update).

        Args:
            project_id: Project ID
            name: New project name
            description: New project description
            is_backlog_activated: Enable/disable backlog module
            is_issues_activated: Enable/disable issues module
            is_kanban_activated: Enable/disable kanban module
            is_private: Change privacy setting
            is_wiki_activated: Enable/disable wiki module
            total_milestones: Update total milestones
            total_story_points: Update total story points
            videoconferences: Update videoconference system
            videoconferences_extra_data: Update videoconference extra data

        Returns:
            Updated project data
        """
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if is_backlog_activated is not None:
            data["is_backlog_activated"] = is_backlog_activated
        if is_issues_activated is not None:
            data["is_issues_activated"] = is_issues_activated
        if is_kanban_activated is not None:
            data["is_kanban_activated"] = is_kanban_activated
        if is_private is not None:
            data["is_private"] = is_private
        if is_wiki_activated is not None:
            data["is_wiki_activated"] = is_wiki_activated
        if total_milestones is not None:
            data["total_milestones"] = total_milestones
        if total_story_points is not None:
            data["total_story_points"] = total_story_points
        if videoconferences is not None:
            data["videoconferences"] = videoconferences
        if videoconferences_extra_data is not None:
            data["videoconferences_extra_data"] = videoconferences_extra_data
        return cast("dict[str, Any]", await self.patch(f"/projects/{project_id}", data=data))

    async def delete_project(self, project_id: int) -> bool:
        """Delete project."""
        return await self.delete(f"/projects/{project_id}")

    # User Story endpoints
    async def list_userstories(
        self,
        project: int | None = None,
        milestone: int | None = None,
        status: int | None = None,
        tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """List user stories."""
        params: dict[str, Any] = {}
        if project is not None:
            params["project"] = project
        if milestone is not None:
            params["milestone"] = milestone
        if status is not None:
            params["status"] = status
        if tags:
            params["tags"] = ",".join(tags)
        return cast("list[dict[str, Any]]", await self.get("/userstories", params=params))

    async def get_userstory(self, userstory_id: int) -> dict[str, Any]:
        """Get user story details."""
        return cast("dict[str, Any]", await self.get(f"/userstories/{userstory_id}"))

    async def create_userstory(
        self,
        project: int,
        subject: str,
        description: str | None = None,
        assigned_to: int | None = None,
        status: int | None = None,
        milestone: int | None = None,
        points: dict[str, int] | None = None,
        tags: list[str] | None = None,
        is_blocked: bool | None = None,
        blocked_note: str | None = None,
        client_requirement: bool | None = None,
        team_requirement: bool | None = None,
        watchers: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new user story.

        Args:
            project: Project ID (required)
            subject: User story subject/title (required)
            description: User story description
            assigned_to: User ID to assign the story to
            status: Status ID
            milestone: Milestone/Sprint ID
            points: Points per role (e.g., {"role_id": points})
            tags: List of tags
            is_blocked: Whether the story is blocked
            blocked_note: Reason for blocking
            client_requirement: Is a client requirement
            team_requirement: Is a team requirement
            watchers: List of user IDs to watch the story

        Returns:
            Created user story data
        """
        data: dict[str, Any] = {"project": project, "subject": subject}
        if description is not None:
            data["description"] = description
        if assigned_to is not None:
            data["assigned_to"] = assigned_to
        if status is not None:
            data["status"] = status
        if milestone is not None:
            data["milestone"] = milestone
        if points is not None:
            data["points"] = points
        if tags is not None:
            data["tags"] = tags
        if is_blocked is not None:
            data["is_blocked"] = is_blocked
        if blocked_note is not None:
            data["blocked_note"] = blocked_note
        if client_requirement is not None:
            data["client_requirement"] = client_requirement
        if team_requirement is not None:
            data["team_requirement"] = team_requirement
        if watchers is not None:
            data["watchers"] = watchers
        return cast("dict[str, Any]", await self.post("/userstories", data=data))

    async def update_userstory(
        self,
        userstory_id: int,
        subject: str | None = None,
        description: str | None = None,
        assigned_to: int | None = None,
        status: int | None = None,
        milestone: int | None = None,
        points: dict[str, int] | None = None,
        tags: list[str] | None = None,
        is_blocked: bool | None = None,
        blocked_note: str | None = None,
        client_requirement: bool | None = None,
        team_requirement: bool | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        """
        Update a user story (partial update).

        Args:
            userstory_id: User story ID
            subject: New subject/title
            description: New description
            assigned_to: New assignee user ID
            status: New status ID
            milestone: New milestone/Sprint ID
            points: New points per role
            tags: New list of tags
            is_blocked: Whether blocked
            blocked_note: Blocking reason
            client_requirement: Is client requirement
            team_requirement: Is team requirement
            version: Version for optimistic locking

        Returns:
            Updated user story data
        """
        data: dict[str, Any] = {}
        if subject is not None:
            data["subject"] = subject
        if description is not None:
            data["description"] = description
        if assigned_to is not None:
            data["assigned_to"] = assigned_to
        if status is not None:
            data["status"] = status
        if milestone is not None:
            data["milestone"] = milestone
        if points is not None:
            data["points"] = points
        if tags is not None:
            data["tags"] = tags
        if is_blocked is not None:
            data["is_blocked"] = is_blocked
        if blocked_note is not None:
            data["blocked_note"] = blocked_note
        if client_requirement is not None:
            data["client_requirement"] = client_requirement
        if team_requirement is not None:
            data["team_requirement"] = team_requirement
        if version is not None:
            data["version"] = version
        return cast("dict[str, Any]", await self.patch(f"/userstories/{userstory_id}", data=data))

    async def delete_userstory(self, userstory_id: int) -> bool:
        """Delete user story."""
        return await self.delete(f"/userstories/{userstory_id}")

    async def get_userstory_filters(self, project: int) -> dict[str, Any]:
        """Get available filters for user stories in a project.

        Args:
            project: Project ID

        Returns:
            Dict with available filters including statuses, tags,
            assigned_to, owners, milestones, and epics.
        """
        return cast(
            "dict[str, Any]",
            await self.get("/userstories/filters_data", params={"project": project}),
        )

    async def list_userstory_custom_attributes(self, project: int) -> list[dict[str, Any]]:
        """List custom attributes defined for user stories in a project.

        Args:
            project: ID of the project

        Returns:
            List of custom attribute definitions
        """
        return cast(
            "list[dict[str, Any]]",
            await self.get(f"/userstory-custom-attributes?project={project}"),
        )

    # Milestone endpoints
    async def list_milestones(
        self, project: int | None = None, closed: bool | None = None
    ) -> list[dict[str, Any]]:
        """List milestones."""
        params: dict[str, Any] = {}
        if project is not None:
            params["project"] = project
        if closed is not None:
            params["closed"] = closed
        return cast("list[dict[str, Any]]", await self.get("/milestones", params=params))

    async def get_milestone(self, milestone_id: int) -> dict[str, Any]:
        """Get milestone details."""
        return cast("dict[str, Any]", await self.get(f"/milestones/{milestone_id}"))

    async def create_milestone(
        self,
        project: int,
        name: str,
        estimated_start: str,
        estimated_finish: str,
        disponibility: float | None = None,
        slug: str | None = None,
        order: int | None = None,
        watchers: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new milestone/sprint.

        Args:
            project: Project ID (required)
            name: Milestone name (required)
            estimated_start: Start date in YYYY-MM-DD format (required)
            estimated_finish: End date in YYYY-MM-DD format (required)
            disponibility: Team disponibility percentage
            slug: URL-friendly name
            order: Display order
            watchers: List of user IDs to watch the milestone

        Returns:
            Created milestone data
        """
        data: dict[str, Any] = {
            "project": project,
            "name": name,
            "estimated_start": estimated_start,
            "estimated_finish": estimated_finish,
        }
        if disponibility is not None:
            data["disponibility"] = disponibility
        if slug is not None:
            data["slug"] = slug
        if order is not None:
            data["order"] = order
        if watchers is not None:
            data["watchers"] = watchers
        return cast("dict[str, Any]", await self.post("/milestones", data=data))

    async def update_milestone(
        self,
        milestone_id: int,
        name: str | None = None,
        estimated_start: str | None = None,
        estimated_finish: str | None = None,
        disponibility: float | None = None,
        slug: str | None = None,
        order: int | None = None,
        closed: bool | None = None,
    ) -> dict[str, Any]:
        """
        Update a milestone/sprint (partial update).

        Args:
            milestone_id: Milestone ID
            name: New milestone name
            estimated_start: New start date in YYYY-MM-DD format
            estimated_finish: New end date in YYYY-MM-DD format
            disponibility: New team disponibility percentage
            slug: New URL-friendly name
            order: New display order
            closed: Whether the milestone is closed

        Returns:
            Updated milestone data
        """
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if estimated_start is not None:
            data["estimated_start"] = estimated_start
        if estimated_finish is not None:
            data["estimated_finish"] = estimated_finish
        if disponibility is not None:
            data["disponibility"] = disponibility
        if slug is not None:
            data["slug"] = slug
        if order is not None:
            data["order"] = order
        if closed is not None:
            data["closed"] = closed
        return cast("dict[str, Any]", await self.patch(f"/milestones/{milestone_id}", data=data))

    async def delete_milestone(self, milestone_id: int) -> bool:
        """Delete milestone."""
        return await self.delete(f"/milestones/{milestone_id}")

    async def get_milestone_stats(self, milestone_id: int) -> dict[str, Any]:
        """Get milestone statistics."""
        return cast("dict[str, Any]", await self.get(f"/milestones/{milestone_id}/stats"))

    async def watch_milestone(self, milestone_id: int) -> dict[str, Any]:
        """Start watching a milestone for updates.

        Args:
            milestone_id: ID of the milestone to watch

        Returns:
            Dict with milestone info including updated watchers list
        """
        result = await self.post(f"/milestones/{milestone_id}/watch")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": milestone_id, "watching": True}
        return cast("dict[str, Any]", result)

    async def unwatch_milestone(self, milestone_id: int) -> dict[str, Any]:
        """Stop watching a milestone.

        Args:
            milestone_id: ID of the milestone to unwatch

        Returns:
            Dict with milestone info including updated watchers list
        """
        result = await self.post(f"/milestones/{milestone_id}/unwatch")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": milestone_id, "watching": False}
        return cast("dict[str, Any]", result)

    async def get_milestone_watchers(self, milestone_id: int) -> list[dict[str, Any]]:
        """Get list of users watching a milestone.

        Args:
            milestone_id: ID of the milestone

        Returns:
            List of dicts with watcher user information
        """
        result = await self.get(f"/milestones/{milestone_id}/watchers")
        return cast("list[dict[str, Any]]", result if result else [])

    # Issue endpoints
    async def list_issues(
        self,
        project: int | None = None,
        milestone: int | None = None,
        status: int | None = None,
        severity: int | None = None,
        priority: int | None = None,
        type: int | None = None,
        assigned_to: int | None = None,
        owner: int | None = None,
        tags: list[str] | None = None,
        is_closed: bool | None = None,
        exclude_project: int | None = None,
        exclude_status: int | None = None,
        exclude_severity: int | None = None,
        exclude_priority: int | None = None,
    ) -> list[dict[str, Any]]:
        """List issues."""
        params: dict[str, Any] = {}
        if project is not None:
            params["project"] = project
        if milestone is not None:
            params["milestone"] = milestone
        if status is not None:
            params["status"] = status
        if severity is not None:
            params["severity"] = severity
        if priority is not None:
            params["priority"] = priority
        if type is not None:
            params["type"] = type
        if assigned_to is not None:
            params["assigned_to"] = assigned_to
        if owner is not None:
            params["owner"] = owner
        if tags:
            params["tags"] = ",".join(tags)
        if is_closed is not None:
            params["is_closed"] = is_closed
        if exclude_project is not None:
            params["exclude_project"] = exclude_project
        if exclude_status is not None:
            params["exclude_status"] = exclude_status
        if exclude_severity is not None:
            params["exclude_severity"] = exclude_severity
        if exclude_priority is not None:
            params["exclude_priority"] = exclude_priority
        return cast("list[dict[str, Any]]", await self.get("/issues", params=params))

    async def get_issue(self, issue_id: int) -> dict[str, Any]:
        """Get issue details."""
        return cast("dict[str, Any]", await self.get(f"/issues/{issue_id}"))

    async def get_issue_by_ref(self, ref: int, project: int) -> dict[str, Any]:
        """Get issue by reference."""
        return cast("dict[str, Any]", await self.get(f"/issues/by_ref?ref={ref}&project={project}"))

    async def create_issue(
        self,
        project: int,
        subject: str,
        description: str | None = None,
        assigned_to: int | None = None,
        status: int | None = None,
        severity: int | None = None,
        priority: int | None = None,
        issue_type: int | None = None,
        milestone: int | None = None,
        tags: list[str] | None = None,
        is_blocked: bool | None = None,
        blocked_note: str | None = None,
        is_closed: bool | None = None,
        watchers: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new issue.

        Args:
            project: Project ID (required)
            subject: Issue subject/title (required)
            description: Issue description
            assigned_to: User ID to assign the issue to
            status: Status ID
            severity: Severity ID (defaults to 1 if not provided)
            priority: Priority ID
            issue_type: Type ID
            milestone: Milestone/Sprint ID
            tags: List of tags
            is_blocked: Whether the issue is blocked
            blocked_note: Reason for blocking
            is_closed: Whether the issue is closed
            watchers: List of user IDs to watch the issue

        Returns:
            Created issue data
        """
        data: dict[str, Any] = {"project": project, "subject": subject}
        if description is not None:
            data["description"] = description
        if assigned_to is not None:
            data["assigned_to"] = assigned_to
        if status is not None:
            data["status"] = status
        # Ensure severity is included (default to 1)
        data["severity"] = severity if severity is not None else 1
        if priority is not None:
            data["priority"] = priority
        if issue_type is not None:
            data["type"] = issue_type
        if milestone is not None:
            data["milestone"] = milestone
        if tags is not None:
            data["tags"] = tags
        if is_blocked is not None:
            data["is_blocked"] = is_blocked
        if blocked_note is not None:
            data["blocked_note"] = blocked_note
        if is_closed is not None:
            data["is_closed"] = is_closed
        if watchers is not None:
            data["watchers"] = watchers
        return cast("dict[str, Any]", await self.post("/issues", data=data))

    async def update_issue(
        self,
        issue_id: int,
        subject: str | None = None,
        description: str | None = None,
        assigned_to: int | None = None,
        status: int | None = None,
        severity: int | None = None,
        priority: int | None = None,
        issue_type: int | None = None,
        milestone: int | None = None,
        tags: list[str] | None = None,
        is_blocked: bool | None = None,
        blocked_note: str | None = None,
        is_closed: bool | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        """
        Update an issue (partial update).

        Args:
            issue_id: Issue ID
            subject: New subject/title
            description: New description
            assigned_to: New assignee user ID
            status: New status ID
            severity: New severity ID
            priority: New priority ID
            issue_type: New type ID
            milestone: New milestone/Sprint ID
            tags: New list of tags
            is_blocked: Whether blocked
            blocked_note: Blocking reason
            is_closed: Whether closed
            version: Version for optimistic locking

        Returns:
            Updated issue data
        """
        data: dict[str, Any] = {}
        if subject is not None:
            data["subject"] = subject
        if description is not None:
            data["description"] = description
        if assigned_to is not None:
            data["assigned_to"] = assigned_to
        if status is not None:
            data["status"] = status
        if severity is not None:
            data["severity"] = severity
        if priority is not None:
            data["priority"] = priority
        if issue_type is not None:
            data["type"] = issue_type
        if milestone is not None:
            data["milestone"] = milestone
        if tags is not None:
            data["tags"] = tags
        if is_blocked is not None:
            data["is_blocked"] = is_blocked
        if blocked_note is not None:
            data["blocked_note"] = blocked_note
        if is_closed is not None:
            data["is_closed"] = is_closed
        if version is not None:
            data["version"] = version
        result = cast("dict[str, Any]", await self.patch(f"/issues/{issue_id}", data=data))
        # Ensure severity field is present in the response
        if "severity" not in result and severity is not None:
            result["severity"] = severity
        return result

    async def update_issue_full(
        self,
        issue_id: int,
        project: int,
        subject: str,
        description: str | None = None,
        assigned_to: int | None = None,
        status: int | None = None,
        severity: int | None = None,
        priority: int | None = None,
        issue_type: int | None = None,
        milestone: int | None = None,
        tags: list[str] | None = None,
        is_blocked: bool | None = None,
        blocked_note: str | None = None,
        is_closed: bool | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        """
        Update an issue (full update - PUT).

        Args:
            issue_id: Issue ID
            project: Project ID (required for full update)
            subject: Issue subject (required for full update)
            description: Issue description
            assigned_to: Assignee user ID
            status: Status ID
            severity: Severity ID
            priority: Priority ID
            issue_type: Type ID
            milestone: Milestone/Sprint ID
            tags: List of tags
            is_blocked: Whether blocked
            blocked_note: Blocking reason
            is_closed: Whether closed
            version: Version for optimistic locking

        Returns:
            Updated issue data
        """
        data: dict[str, Any] = {"project": project, "subject": subject}
        if description is not None:
            data["description"] = description
        if assigned_to is not None:
            data["assigned_to"] = assigned_to
        if status is not None:
            data["status"] = status
        if severity is not None:
            data["severity"] = severity
        if priority is not None:
            data["priority"] = priority
        if issue_type is not None:
            data["type"] = issue_type
        if milestone is not None:
            data["milestone"] = milestone
        if tags is not None:
            data["tags"] = tags
        if is_blocked is not None:
            data["is_blocked"] = is_blocked
        if blocked_note is not None:
            data["blocked_note"] = blocked_note
        if is_closed is not None:
            data["is_closed"] = is_closed
        if version is not None:
            data["version"] = version
        return cast("dict[str, Any]", await self.put(f"/issues/{issue_id}", data=data))

    async def delete_issue(self, issue_id: int) -> bool:
        """Delete issue."""
        return await self.delete(f"/issues/{issue_id}")

    async def bulk_create_issues(
        self, project_id: int, bulk_issues: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Bulk create issues."""
        data = {"project_id": project_id, "bulk_issues": bulk_issues}
        return cast("list[dict[str, Any]]", await self.post("/issues/bulk_create", data=data))

    async def get_issue_filters_data(self) -> dict[str, Any]:
        """Get issue filters data."""
        return cast("dict[str, Any]", await self.get("/issues/filters_data"))

    async def get_issue_filters(self, project: int) -> dict[str, Any]:
        """Get available filters for issues in a project.

        Args:
            project: Project ID

        Returns:
            Dict with available filters including statuses, types,
            priorities, severities, assigned_to, owners, and tags.
        """
        return cast(
            "dict[str, Any]", await self.get("/issues/filters_data", params={"project": project})
        )

    async def upvote_issue(self, issue_id: int) -> dict[str, Any]:
        """Upvote issue."""
        result = await self.post(f"/issues/{issue_id}/upvote")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": issue_id, "voted": True}
        return cast("dict[str, Any]", result)

    async def downvote_issue(self, issue_id: int) -> dict[str, Any]:
        """Downvote issue."""
        result = await self.post(f"/issues/{issue_id}/downvote")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": issue_id, "voted": False}
        return cast("dict[str, Any]", result)

    async def get_issue_voters(self, issue_id: int) -> list[dict[str, Any]]:
        """Get issue voters."""
        return cast("list[dict[str, Any]]", await self.get(f"/issues/{issue_id}/voters"))

    async def watch_issue(self, issue_id: int) -> dict[str, Any]:
        """Watch issue."""
        result = await self.post(f"/issues/{issue_id}/watch")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": issue_id, "watching": True}
        return cast("dict[str, Any]", result)

    async def unwatch_issue(self, issue_id: int) -> dict[str, Any]:
        """Unwatch issue."""
        result = await self.post(f"/issues/{issue_id}/unwatch")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": issue_id, "watching": False}
        return cast("dict[str, Any]", result)

    async def get_issue_watchers(self, issue_id: int) -> list[dict[str, Any]]:
        """Get issue watchers."""
        return cast("list[dict[str, Any]]", await self.get(f"/issues/{issue_id}/watchers"))

    async def list_issue_attachments(self, issue_id: int) -> list[dict[str, Any]]:
        """List issue attachments."""
        return cast(
            "list[dict[str, Any]]", await self.get(f"/issues/attachments?object_id={issue_id}")
        )

    async def get_issue_attachments(self, issue_id: int) -> list[dict[str, Any]]:
        """Get issue attachments (alias for list_issue_attachments)."""
        return await self.list_issue_attachments(issue_id)

    async def create_issue_attachment(
        self,
        object_id: int,
        project: int,
        attached_file: str,
        description: str | None = None,
        is_deprecated: bool | None = None,
    ) -> dict[str, Any]:
        """
        Create an issue attachment.

        Args:
            object_id: Issue ID to attach the file to
            project: Project ID
            attached_file: File path or content
            description: Attachment description
            is_deprecated: Whether the attachment is deprecated

        Returns:
            Created attachment data
        """
        data: dict[str, Any] = {
            "object_id": object_id,
            "project": project,
            "attached_file": attached_file,
        }
        if description is not None:
            data["description"] = description
        if is_deprecated is not None:
            data["is_deprecated"] = is_deprecated
        return cast("dict[str, Any]", await self.post("/issues/attachments", data=data))

    async def get_issue_attachment(self, attachment_id: int) -> dict[str, Any]:
        """Get issue attachment."""
        return cast("dict[str, Any]", await self.get(f"/issues/attachments/{attachment_id}"))

    async def update_issue_attachment(
        self,
        attachment_id: int,
        description: str | None = None,
        is_deprecated: bool | None = None,
    ) -> dict[str, Any]:
        """
        Update an issue attachment.

        Args:
            attachment_id: Attachment ID
            description: New description
            is_deprecated: Whether deprecated

        Returns:
            Updated attachment data
        """
        data: dict[str, Any] = {}
        if description is not None:
            data["description"] = description
        if is_deprecated is not None:
            data["is_deprecated"] = is_deprecated
        return cast(
            "dict[str, Any]", await self.patch(f"/issues/attachments/{attachment_id}", data=data)
        )

    async def delete_issue_attachment(self, attachment_id: int) -> bool:
        """Delete issue attachment."""
        return await self.delete(f"/issues/attachments/{attachment_id}")

    async def get_issue_history(self, issue_id: int) -> list[dict[str, Any]]:
        """Get issue history."""
        return cast("list[dict[str, Any]]", await self.get(f"/history/issue/{issue_id}"))

    async def create_issue_comment(
        self, issue_id: int, comment: str, version: int
    ) -> dict[str, Any]:
        """Create issue comment."""
        data = {"comment": comment, "version": version}
        return cast("dict[str, Any]", await self.post(f"/issues/{issue_id}/comments", data=data))

    async def list_issue_custom_attributes(self, project: int) -> list[dict[str, Any]]:
        """List custom attributes defined for issues in a project.

        Args:
            project: ID of the project

        Returns:
            List of custom attribute definitions
        """
        return cast(
            "list[dict[str, Any]]",
            await self.get(f"/issue-custom-attributes?project={project}"),
        )

    async def get_issue_custom_attributes(self, issue_id: int) -> dict[str, Any]:
        """Get issue custom attributes."""
        return cast("dict[str, Any]", await self.get(f"/issues/custom-attributes/{issue_id}"))

    async def get_issue_custom_attribute_values(self, issue_id: int) -> dict[str, Any]:
        """Get issue custom attribute values."""
        return cast(
            "dict[str, Any]", await self.get(f"/issues/custom-attributes-values/{issue_id}")
        )

    async def update_issue_custom_attribute_values(
        self, issue_id: int, attributes: dict[str, Any], version: int
    ) -> dict[str, Any]:
        """Update issue custom attribute values."""
        data = {"attributes": attributes, "version": version}
        return cast(
            "dict[str, Any]",
            await self.patch(f"/issues/custom-attributes-values/{issue_id}", data=data),
        )

    # Task endpoints
    async def list_tasks(
        self,
        project: int | None = None,
        milestone: int | None = None,
        user_story: int | None = None,
        status: int | None = None,
        assigned_to: int | None = None,
        owner: int | None = None,
        tags: list[str] | None = None,
        is_closed: bool | None = None,
        exclude_project: int | None = None,
        exclude_status: int | None = None,
    ) -> list[dict[str, Any]]:
        """List tasks."""
        params: dict[str, Any] = {}
        if project is not None:
            params["project"] = project
        if milestone is not None:
            params["milestone"] = milestone
        if user_story is not None:
            params["user_story"] = user_story
        if status is not None:
            params["status"] = status
        if assigned_to is not None:
            params["assigned_to"] = assigned_to
        if owner is not None:
            params["owner"] = owner
        if tags:
            params["tags"] = ",".join(tags)
        if is_closed is not None:
            params["is_closed"] = is_closed
        if exclude_project is not None:
            params["exclude_project"] = exclude_project
        if exclude_status is not None:
            params["exclude_status"] = exclude_status
        return cast("list[dict[str, Any]]", await self.get("/tasks", params=params))

    async def get_task(self, task_id: int) -> dict[str, Any]:
        """Get task details."""
        return cast("dict[str, Any]", await self.get(f"/tasks/{task_id}"))

    async def get_task_by_ref(self, ref: int, project: int) -> dict[str, Any]:
        """Get task by reference."""
        return cast("dict[str, Any]", await self.get(f"/tasks/by_ref?ref={ref}&project={project}"))

    async def create_task(
        self,
        project: int,
        subject: str,
        description: str | None = None,
        assigned_to: int | None = None,
        status: int | None = None,
        milestone: int | None = None,
        user_story: int | None = None,
        tags: list[str] | None = None,
        is_blocked: bool | None = None,
        blocked_note: str | None = None,
        is_closed: bool | None = None,
        watchers: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new task.

        Args:
            project: Project ID (required)
            subject: Task subject/title (required)
            description: Task description
            assigned_to: User ID to assign the task to
            status: Status ID
            milestone: Milestone/Sprint ID
            user_story: User story ID this task belongs to
            tags: List of tags
            is_blocked: Whether the task is blocked
            blocked_note: Reason for blocking
            is_closed: Whether the task is closed
            watchers: List of user IDs to watch the task

        Returns:
            Created task data
        """
        data: dict[str, Any] = {"project": project, "subject": subject}
        if description is not None:
            data["description"] = description
        if assigned_to is not None:
            data["assigned_to"] = assigned_to
        if status is not None:
            data["status"] = status
        if milestone is not None:
            data["milestone"] = milestone
        if user_story is not None:
            data["user_story"] = user_story
        if tags is not None:
            data["tags"] = tags
        if is_blocked is not None:
            data["is_blocked"] = is_blocked
        if blocked_note is not None:
            data["blocked_note"] = blocked_note
        if is_closed is not None:
            data["is_closed"] = is_closed
        if watchers is not None:
            data["watchers"] = watchers
        return cast("dict[str, Any]", await self.post("/tasks", data=data))

    async def update_task(
        self,
        task_id: int,
        subject: str | None = None,
        description: str | None = None,
        assigned_to: int | None = None,
        status: int | None = None,
        milestone: int | None = None,
        user_story: int | None = None,
        tags: list[str] | None = None,
        is_blocked: bool | None = None,
        blocked_note: str | None = None,
        is_closed: bool | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        """
        Update a task (partial update).

        Args:
            task_id: Task ID
            subject: New subject/title
            description: New description
            assigned_to: New assignee user ID
            status: New status ID
            milestone: New milestone/Sprint ID
            user_story: New user story ID
            tags: New list of tags
            is_blocked: Whether blocked
            blocked_note: Blocking reason
            is_closed: Whether closed
            version: Version for optimistic locking

        Returns:
            Updated task data
        """
        data: dict[str, Any] = {}
        if subject is not None:
            data["subject"] = subject
        if description is not None:
            data["description"] = description
        if assigned_to is not None:
            data["assigned_to"] = assigned_to
        if status is not None:
            data["status"] = status
        if milestone is not None:
            data["milestone"] = milestone
        if user_story is not None:
            data["user_story"] = user_story
        if tags is not None:
            data["tags"] = tags
        if is_blocked is not None:
            data["is_blocked"] = is_blocked
        if blocked_note is not None:
            data["blocked_note"] = blocked_note
        if is_closed is not None:
            data["is_closed"] = is_closed
        if version is not None:
            data["version"] = version
        return cast("dict[str, Any]", await self.patch(f"/tasks/{task_id}", data=data))

    async def delete_task(self, task_id: int) -> bool:
        """Delete task."""
        return await self.delete(f"/tasks/{task_id}")

    async def bulk_create_tasks(self, project_id: int, bulk_tasks: str) -> list[dict[str, Any]]:
        """Bulk create tasks from a text block.

        Args:
            project_id: ID of the project where tasks will be created
            bulk_tasks: Text block with one task subject per line, separated by newlines

        Returns:
            List of created tasks

        Example:
            >>> await client.bulk_create_tasks(123, "Task 1\\nTask 2\\nTask 3")
        """
        data = {"project_id": project_id, "bulk_tasks": bulk_tasks}
        return cast("list[dict[str, Any]]", await self.post("/tasks/bulk_create", data=data))

    async def get_task_filters(self, project: int) -> dict[str, Any]:
        """Get available filters for tasks in a project.

        Args:
            project: Project ID

        Returns:
            Dict with available filters including statuses, assigned_to,
            owners, and tags.
        """
        return cast(
            "dict[str, Any]", await self.get("/tasks/filters_data", params={"project": project})
        )

    async def upvote_task(self, task_id: int) -> dict[str, Any]:
        """Upvote task."""
        result = await self.post(f"/tasks/{task_id}/upvote")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": task_id, "voted": True}
        return cast("dict[str, Any]", result)

    async def downvote_task(self, task_id: int) -> dict[str, Any]:
        """Downvote task."""
        result = await self.post(f"/tasks/{task_id}/downvote")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": task_id, "voted": False}
        return cast("dict[str, Any]", result)

    async def get_task_voters(self, task_id: int) -> list[dict[str, Any]]:
        """Get task voters."""
        return cast("list[dict[str, Any]]", await self.get(f"/tasks/{task_id}/voters"))

    async def watch_task(self, task_id: int) -> dict[str, Any]:
        """Watch task."""
        result = await self.post(f"/tasks/{task_id}/watch")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": task_id, "watching": True}
        return cast("dict[str, Any]", result)

    async def unwatch_task(self, task_id: int) -> dict[str, Any]:
        """Unwatch task."""
        result = await self.post(f"/tasks/{task_id}/unwatch")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": task_id, "watching": False}
        return cast("dict[str, Any]", result)

    async def get_task_watchers(self, task_id: int) -> list[dict[str, Any]]:
        """Get task watchers."""
        return cast("list[dict[str, Any]]", await self.get(f"/tasks/{task_id}/watchers"))

    async def list_task_attachments(
        self, task_id: int | None = None, project: int | None = None, object_id: int | None = None
    ) -> list[dict[str, Any]]:
        """List task attachments.

        Args:
            task_id: ID of the task (alias for object_id)
            project: ID of the project to filter attachments
            object_id: ID of the task (alternative to task_id)

        Returns:
            List of task attachments
        """
        # Support task_id as alias for object_id
        effective_object_id = object_id or task_id
        params = []
        if effective_object_id:
            params.append(f"object_id={effective_object_id}")
        if project:
            params.append(f"project={project}")
        query_string = "&".join(params) if params else ""
        url = f"/tasks/attachments?{query_string}" if query_string else "/tasks/attachments"
        return cast("list[dict[str, Any]]", await self.get(url))

    async def create_task_attachment(
        self, task_id: int, attached_file: bytes, name: str = "attachment.txt"
    ) -> dict[str, Any]:
        """Create task attachment."""
        data = {"object_id": task_id, "attached_file": attached_file, "name": name}
        return cast("dict[str, Any]", await self.post("/tasks/attachments", data=data))

    async def get_task_attachment(self, attachment_id: int) -> dict[str, Any]:
        """Get task attachment."""
        return cast("dict[str, Any]", await self.get(f"/tasks/attachments/{attachment_id}"))

    async def update_task_attachment(
        self,
        attachment_id: int,
        description: str | None = None,
        is_deprecated: bool | None = None,
    ) -> dict[str, Any]:
        """
        Update a task attachment.

        Args:
            attachment_id: Attachment ID
            description: New description
            is_deprecated: Whether deprecated

        Returns:
            Updated attachment data
        """
        data: dict[str, Any] = {}
        if description is not None:
            data["description"] = description
        if is_deprecated is not None:
            data["is_deprecated"] = is_deprecated
        return cast(
            "dict[str, Any]", await self.patch(f"/tasks/attachments/{attachment_id}", data=data)
        )

    async def delete_task_attachment(self, attachment_id: int) -> bool:
        """Delete task attachment."""
        return await self.delete(f"/tasks/attachments/{attachment_id}")

    async def get_task_history(self, task_id: int) -> list[dict[str, Any]]:
        """Get task history."""
        return cast("list[dict[str, Any]]", await self.get(f"/history/task/{task_id}"))

    async def create_task_comment(self, task_id: int, comment: str, version: int) -> dict[str, Any]:
        """Create task comment."""
        data = {"comment": comment, "version": version}
        return cast("dict[str, Any]", await self.post(f"/tasks/{task_id}/comments", data=data))

    async def list_task_custom_attributes(self, project: int) -> list[dict[str, Any]]:
        """List custom attributes defined for tasks in a project.

        Args:
            project: ID of the project

        Returns:
            List of custom attribute definitions
        """
        return cast(
            "list[dict[str, Any]]",
            await self.get(f"/task-custom-attributes?project={project}"),
        )

    async def get_task_custom_attributes(self, task_id: int) -> dict[str, Any]:
        """Get task custom attributes."""
        return cast("dict[str, Any]", await self.get(f"/tasks/custom-attributes/{task_id}"))

    async def get_task_custom_attribute_values(self, task_id: int) -> dict[str, Any]:
        """Get task custom attribute values."""
        return cast("dict[str, Any]", await self.get(f"/tasks/custom-attributes-values/{task_id}"))

    async def update_task_custom_attribute_values(
        self, task_id: int, attributes: dict[str, Any], version: int
    ) -> dict[str, Any]:
        """Update task custom attribute values."""
        data = {"attributes": attributes, "version": version}
        return cast(
            "dict[str, Any]",
            await self.patch(f"/tasks/custom-attributes-values/{task_id}", data=data),
        )

    # Membership endpoints
    async def list_memberships(self, project: int | None = None) -> list[dict[str, Any]]:
        """List memberships."""
        params = {}
        if project is not None:
            params["project"] = project
        return cast("list[dict[str, Any]]", await self.get("/memberships", params=params))

    async def get_membership(self, membership_id: int) -> dict[str, Any]:
        """Get membership details."""
        return cast("dict[str, Any]", await self.get(f"/memberships/{membership_id}"))

    async def create_membership(
        self,
        project: int,
        role: int,
        username: str | None = None,
        email: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new membership (invite user to project).

        Args:
            project: Project ID (required)
            role: Role ID to assign (required)
            username: Username of existing Taiga user
            email: Email of user to invite (if not existing user)

        Returns:
            Created membership data

        Note:
            Either username or email must be provided.
        """
        data: dict[str, Any] = {"project": project, "role": role}
        if username is not None:
            data["username"] = username
        if email is not None:
            data["email"] = email
        return cast("dict[str, Any]", await self.post("/memberships", data=data))

    async def update_membership(
        self,
        membership_id: int,
        role: int | None = None,
        is_admin: bool | None = None,
    ) -> dict[str, Any]:
        """
        Update a membership.

        Args:
            membership_id: Membership ID
            role: New role ID
            is_admin: Whether the member is a project admin

        Returns:
            Updated membership data
        """
        data: dict[str, Any] = {}
        if role is not None:
            data["role"] = role
        if is_admin is not None:
            data["is_admin"] = is_admin
        return cast("dict[str, Any]", await self.patch(f"/memberships/{membership_id}", data=data))

    async def delete_membership(self, membership_id: int) -> bool:
        """Delete membership."""
        return await self.delete(f"/memberships/{membership_id}")

    async def bulk_create_memberships(
        self, project_id: int, memberships: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Bulk create memberships."""
        data = {"project": project_id, "bulk_memberships": memberships}
        return cast("list[dict[str, Any]]", await self.post("/memberships/bulk_create", data=data))

    # Webhook endpoints
    async def list_webhooks(self, project: int | None = None) -> list[dict[str, Any]]:
        """List webhooks."""
        params = {}
        if project is not None:
            params["project"] = project
        return cast("list[dict[str, Any]]", await self.get("/webhooks", params=params))

    async def get_webhook(self, webhook_id: int) -> dict[str, Any]:
        """Get webhook details."""
        return cast("dict[str, Any]", await self.get(f"/webhooks/{webhook_id}"))

    async def create_webhook(
        self,
        project: int,
        name: str,
        url: str,
        key: str,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """
        Create a new webhook.

        Args:
            project: Project ID (required)
            name: Webhook name (required)
            url: Webhook URL to call (required)
            key: Secret key for signing webhook payloads (required)
            enabled: Whether the webhook is enabled (default: True)

        Returns:
            Created webhook data
        """
        data: dict[str, Any] = {
            "project": project,
            "name": name,
            "url": url,
            "key": key,
            "enabled": enabled,
        }
        return cast("dict[str, Any]", await self.post("/webhooks", data=data))

    async def update_webhook(
        self,
        webhook_id: int,
        name: str | None = None,
        url: str | None = None,
        key: str | None = None,
        enabled: bool | None = None,
    ) -> dict[str, Any]:
        """
        Update a webhook.

        Args:
            webhook_id: Webhook ID
            name: New webhook name
            url: New webhook URL
            key: New secret key
            enabled: Enable or disable the webhook

        Returns:
            Updated webhook data
        """
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if url is not None:
            data["url"] = url
        if key is not None:
            data["key"] = key
        if enabled is not None:
            data["enabled"] = enabled
        return cast("dict[str, Any]", await self.patch(f"/webhooks/{webhook_id}", data=data))

    async def delete_webhook(self, webhook_id: int) -> bool:
        """Delete webhook."""
        return await self.delete(f"/webhooks/{webhook_id}")

    async def test_webhook(self, webhook_id: int) -> dict[str, Any]:
        """Test webhook."""
        return cast("dict[str, Any]", await self.post(f"/webhooks/{webhook_id}/test"))

    async def get_webhook_logs(self, webhook_id: int) -> list[dict[str, Any]]:
        """Get webhook logs."""
        return cast("list[dict[str, Any]]", await self.get(f"/webhooks/{webhook_id}/logs"))

    # Wiki endpoints
    async def list_wiki_pages(self, project: int) -> list[dict[str, Any]]:
        """List wiki pages."""
        return cast("list[dict[str, Any]]", await self.get(f"/wiki?project={project}"))

    async def get_wiki_page(self, page_id: int) -> dict[str, Any]:
        """Get wiki page details."""
        return cast("dict[str, Any]", await self.get(f"/wiki/{page_id}"))

    async def get_wiki_page_by_slug(self, project: int, slug: str) -> dict[str, Any]:
        """Get wiki page by slug."""
        return cast(
            "dict[str, Any]", await self.get(f"/wiki/by_slug?project={project}&slug={slug}")
        )

    async def create_wiki_page(
        self,
        project: int,
        slug: str,
        content: str,
        watchers: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new wiki page.

        Args:
            project: Project ID (required)
            slug: URL-friendly page identifier (required)
            content: Page content in markdown format (required)
            watchers: List of user IDs to watch the page

        Returns:
            Created wiki page data
        """
        data: dict[str, Any] = {"project": project, "slug": slug, "content": content}
        if watchers is not None:
            data["watchers"] = watchers
        return cast("dict[str, Any]", await self.post("/wiki", data=data))

    async def update_wiki_page(
        self,
        page_id: int,
        slug: str | None = None,
        content: str | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        """
        Update a wiki page.

        Args:
            page_id: Wiki page ID
            slug: New URL-friendly identifier
            content: New page content
            version: Version for optimistic locking

        Returns:
            Updated wiki page data
        """
        data: dict[str, Any] = {}
        if slug is not None:
            data["slug"] = slug
        if content is not None:
            data["content"] = content
        if version is not None:
            data["version"] = version
        return cast("dict[str, Any]", await self.patch(f"/wiki/{page_id}", data=data))

    async def delete_wiki_page(self, page_id: int) -> bool:
        """Delete wiki page."""
        return await self.delete(f"/wiki/{page_id}")

    async def restore_wiki_page(self, page_id: int) -> dict[str, Any]:
        """Restore deleted wiki page."""
        result = await self.post(f"/wiki/{page_id}/restore")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": page_id, "restored": True}
        return cast("dict[str, Any]", result)

    async def watch_wiki_page(self, page_id: int) -> dict[str, Any]:
        """Watch wiki page."""
        result = await self.post(f"/wiki/{page_id}/watch")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": page_id, "watching": True}
        return cast("dict[str, Any]", result)

    async def unwatch_wiki_page(self, page_id: int) -> dict[str, Any]:
        """Unwatch wiki page."""
        result = await self.post(f"/wiki/{page_id}/unwatch")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": page_id, "watching": False}
        return cast("dict[str, Any]", result)

    async def get_wiki_page_watchers(self, page_id: int) -> list[dict[str, Any]]:
        """Get wiki page watchers."""
        return cast("list[dict[str, Any]]", await self.get(f"/wiki/{page_id}/watchers"))

    async def list_wiki_attachments(self, page_id: int) -> list[dict[str, Any]]:
        """List wiki attachments."""
        return cast(
            "list[dict[str, Any]]", await self.get(f"/wiki/attachments?object_id={page_id}")
        )

    async def create_wiki_attachment(
        self, page_id: int, attached_file: bytes, name: str = "attachment.txt"
    ) -> dict[str, Any]:
        """Create wiki attachment."""
        data = {"object_id": page_id, "attached_file": attached_file, "name": name}
        return cast("dict[str, Any]", await self.post("/wiki/attachments", data=data))

    async def get_wiki_attachment(self, attachment_id: int) -> dict[str, Any]:
        """Get wiki attachment."""
        return cast("dict[str, Any]", await self.get(f"/wiki/attachments/{attachment_id}"))

    async def update_wiki_attachment(
        self,
        attachment_id: int,
        description: str | None = None,
        is_deprecated: bool | None = None,
    ) -> dict[str, Any]:
        """
        Update a wiki attachment.

        Args:
            attachment_id: Attachment ID
            description: New description
            is_deprecated: Whether deprecated

        Returns:
            Updated attachment data
        """
        data: dict[str, Any] = {}
        if description is not None:
            data["description"] = description
        if is_deprecated is not None:
            data["is_deprecated"] = is_deprecated
        return cast(
            "dict[str, Any]", await self.patch(f"/wiki/attachments/{attachment_id}", data=data)
        )

    async def delete_wiki_attachment(self, attachment_id: int) -> bool:
        """Delete wiki attachment."""
        return await self.delete(f"/wiki/attachments/{attachment_id}")

    async def get_wiki_page_history(self, page_id: int) -> list[dict[str, Any]]:
        """Get wiki page history."""
        return cast("list[dict[str, Any]]", await self.get(f"/history/wiki/{page_id}"))

    # Epic endpoints
    async def list_epics(
        self, project: int | None = None, status: int | None = None, assigned_to: int | None = None
    ) -> list[dict[str, Any]]:
        """List epics."""
        params = {}
        if project is not None:
            params["project"] = project
        if status is not None:
            params["status"] = status
        if assigned_to is not None:
            params["assigned_to"] = assigned_to
        return cast("list[dict[str, Any]]", await self.get("/epics", params=params))

    async def get_epic(self, epic_id: int) -> dict[str, Any]:
        """Get epic details."""
        return cast("dict[str, Any]", await self.get(f"/epics/{epic_id}"))

    async def create_epic(
        self,
        project: int,
        subject: str,
        description: str | None = None,
        assigned_to: int | None = None,
        status: int | None = None,
        color: str | None = None,
        tags: list[str] | None = None,
        watchers: list[int] | None = None,
        client_requirement: bool | None = None,
        team_requirement: bool | None = None,
    ) -> dict[str, Any]:
        """
        Create a new epic.

        Args:
            project: Project ID (required)
            subject: Epic subject/title (required)
            description: Epic description
            assigned_to: User ID to assign the epic to
            status: Status ID
            color: Hex color code for the epic (e.g., "#FF0000")
            tags: List of tags
            watchers: List of user IDs to watch the epic
            client_requirement: Is a client requirement
            team_requirement: Is a team requirement

        Returns:
            Created epic data
        """
        data: dict[str, Any] = {"project": project, "subject": subject}
        if description is not None:
            data["description"] = description
        if assigned_to is not None:
            data["assigned_to"] = assigned_to
        if status is not None:
            data["status"] = status
        if color is not None:
            data["color"] = color
        if tags is not None:
            data["tags"] = tags
        if watchers is not None:
            data["watchers"] = watchers
        if client_requirement is not None:
            data["client_requirement"] = client_requirement
        if team_requirement is not None:
            data["team_requirement"] = team_requirement
        return cast("dict[str, Any]", await self.post("/epics", data=data))

    async def update_epic(
        self,
        epic_id: int,
        subject: str | None = None,
        description: str | None = None,
        assigned_to: int | None = None,
        status: int | None = None,
        color: str | None = None,
        tags: list[str] | None = None,
        client_requirement: bool | None = None,
        team_requirement: bool | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        """
        Update an epic (partial update).

        Args:
            epic_id: Epic ID
            subject: New subject/title
            description: New description
            assigned_to: New assignee user ID
            status: New status ID
            color: New hex color code
            tags: New list of tags
            client_requirement: Is client requirement
            team_requirement: Is team requirement
            version: Version for optimistic locking

        Returns:
            Updated epic data
        """
        data: dict[str, Any] = {}
        if subject is not None:
            data["subject"] = subject
        if description is not None:
            data["description"] = description
        if assigned_to is not None:
            data["assigned_to"] = assigned_to
        if status is not None:
            data["status"] = status
        if color is not None:
            data["color"] = color
        if tags is not None:
            data["tags"] = tags
        if client_requirement is not None:
            data["client_requirement"] = client_requirement
        if team_requirement is not None:
            data["team_requirement"] = team_requirement
        if version is not None:
            data["version"] = version
        return cast("dict[str, Any]", await self.patch(f"/epics/{epic_id}", data=data))

    async def update_epic_full(
        self,
        epic_id: int,
        project: int,
        subject: str,
        description: str | None = None,
        assigned_to: int | None = None,
        status: int | None = None,
        color: str | None = None,
        tags: list[str] | None = None,
        client_requirement: bool | None = None,
        team_requirement: bool | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        """
        Update an epic (full update - PUT).

        Args:
            epic_id: Epic ID
            project: Project ID (required for full update)
            subject: Epic subject (required for full update)
            description: Epic description
            assigned_to: Assignee user ID
            status: Status ID
            color: Hex color code
            tags: List of tags
            client_requirement: Is client requirement
            team_requirement: Is team requirement
            version: Version for optimistic locking

        Returns:
            Updated epic data
        """
        data: dict[str, Any] = {"project": project, "subject": subject}
        if description is not None:
            data["description"] = description
        if assigned_to is not None:
            data["assigned_to"] = assigned_to
        if status is not None:
            data["status"] = status
        if color is not None:
            data["color"] = color
        if tags is not None:
            data["tags"] = tags
        if client_requirement is not None:
            data["client_requirement"] = client_requirement
        if team_requirement is not None:
            data["team_requirement"] = team_requirement
        if version is not None:
            data["version"] = version
        return cast("dict[str, Any]", await self.put(f"/epics/{epic_id}", data=data))

    async def delete_epic(self, epic_id: int) -> bool:
        """Delete epic."""
        return await self.delete(f"/epics/{epic_id}")

    async def bulk_create_epics(
        self,
        project_id: int,
        bulk_epics: str,
        status_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Create multiple epics at once.

        Args:
            project_id: Project ID to create epics in
            bulk_epics: Newline-separated list of epic subjects
            status_id: Optional status ID for all created epics

        Returns:
            List of created epic data
        """
        data: dict[str, Any] = {
            "project_id": project_id,
            "bulk_epics": bulk_epics,
        }
        if status_id is not None:
            data["status_id"] = status_id
        return cast("list[dict[str, Any]]", await self.post("/epics/bulk_create", data=data))

    async def get_epic_by_ref(self, project_id: int, ref: int) -> dict[str, Any]:
        """Get epic by reference number."""
        params = {"project": project_id, "ref": ref}
        return cast("dict[str, Any]", await self.get("/epics/by_ref", params=params))

    # Epic Related User Stories methods
    async def list_epic_related_userstories(self, epic_id: int) -> list[dict[str, Any]]:
        """List user stories related to an epic."""
        return cast("list[dict[str, Any]]", await self.get(f"/epics/{epic_id}/related_userstories"))

    async def create_epic_related_userstory(
        self,
        epic_id: int,
        user_story: int,
        order: int | None = None,
    ) -> dict[str, Any]:
        """
        Create a relationship between an epic and an existing user story.

        Args:
            epic_id: ID of the epic
            user_story: ID of the existing user story to link
            order: Optional order position in the epic

        Returns:
            Dict with the created relationship
        """
        data: dict[str, Any] = {"epic": epic_id, "user_story": user_story}
        if order is not None:
            data["order"] = order
        return cast(
            "dict[str, Any]", await self.post(f"/epics/{epic_id}/related_userstories", data=data)
        )

    async def get_epic_related_userstory(self, epic_id: int, userstory_id: int) -> dict[str, Any]:
        """Get a specific user story relationship with an epic."""
        return cast(
            "dict[str, Any]", await self.get(f"/epics/{epic_id}/related_userstories/{userstory_id}")
        )

    async def update_epic_related_userstory(
        self,
        epic_id: int,
        userstory_id: int,
        order: int | None = None,
    ) -> dict[str, Any]:
        """
        Update a relationship between an epic and a user story.

        Args:
            epic_id: Epic ID
            userstory_id: User story ID
            order: New order position

        Returns:
            Updated relationship data
        """
        data: dict[str, Any] = {}
        if order is not None:
            data["order"] = order
        return cast(
            "dict[str, Any]",
            await self.patch(f"/epics/{epic_id}/related_userstories/{userstory_id}", data=data),
        )

    async def delete_epic_related_userstory(self, epic_id: int, userstory_id: int) -> bool:
        """Delete a relationship between an epic and a user story."""
        return await self.delete(f"/epics/{epic_id}/related_userstories/{userstory_id}")

    async def bulk_create_epic_related_userstories(
        self,
        epic_id: int,
        userstories_data: list[dict[str, Any]] | None = None,
        bulk_userstories: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Bulk create relationships between an epic and multiple user stories.

        Args:
            epic_id: ID of the epic
            userstories_data: List of dicts with user_story IDs and optionally order
            bulk_userstories: Alternative parameter name for compatibility

        Returns:
            List of created relationships
        """
        data_list = userstories_data or bulk_userstories or []
        return cast(
            "list[dict[str, Any]]",
            await self.post(
                f"/epics/{epic_id}/related_userstories/bulk_create",
                data={"bulk_userstories": data_list},
            ),
        )

    # Epic voting methods
    async def upvote_epic(self, epic_id: int) -> dict[str, Any]:
        """Add a positive vote to an epic.

        Args:
            epic_id: ID of the epic to upvote

        Returns:
            Updated epic data or empty dict on success
        """
        result = await self.post(f"/epics/{epic_id}/upvote")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": epic_id, "voted": True}
        return cast("dict[str, Any]", result)

    async def downvote_epic(self, epic_id: int) -> dict[str, Any]:
        """Remove vote from an epic.

        Args:
            epic_id: ID of the epic to downvote

        Returns:
            Updated epic data or empty dict on success
        """
        result = await self.post(f"/epics/{epic_id}/downvote")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": epic_id, "voted": False}
        return cast("dict[str, Any]", result)

    async def get_epic_voters(self, epic_id: int) -> list[dict[str, Any]]:
        """Get list of users who voted for an epic.

        Args:
            epic_id: ID of the epic

        Returns:
            List of voter information
        """
        return cast("list[dict[str, Any]]", await self.get(f"/epics/{epic_id}/voters"))

    # Epic watching methods
    async def watch_epic(self, epic_id: int) -> dict[str, Any]:
        """Start watching an epic for updates.

        Args:
            epic_id: ID of the epic to watch

        Returns:
            Confirmation of watching status
        """
        result = await self.post(f"/epics/{epic_id}/watch")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": epic_id, "watching": True}
        return cast("dict[str, Any]", result)

    async def unwatch_epic(self, epic_id: int) -> dict[str, Any]:
        """Stop watching an epic.

        Args:
            epic_id: ID of the epic to unwatch

        Returns:
            Confirmation of unwatching status
        """
        result = await self.post(f"/epics/{epic_id}/unwatch")
        # HTTP 204 returns empty dict, provide default response
        if not result:
            return {"id": epic_id, "watching": False}
        return cast("dict[str, Any]", result)

    async def get_epic_watchers(self, epic_id: int) -> list[dict[str, Any]]:
        """Get list of users watching an epic.

        Args:
            epic_id: ID of the epic

        Returns:
            List of watcher information
        """
        return cast("list[dict[str, Any]]", await self.get(f"/epics/{epic_id}/watchers"))

    # Epic attachments
    async def list_epic_attachments(
        self,
        epic_id: int | None = None,
        project_id: int | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """List attachments for epics.

        Args:
            epic_id: Filter by epic ID (object_id in API)
            project_id: Filter by project ID
            **kwargs: Additional filter parameters

        Returns:
            List of attachment data
        """
        params: dict[str, Any] = {}
        if epic_id is not None:
            params["object_id"] = epic_id
        if project_id is not None:
            params["project"] = project_id
        params.update(kwargs)
        return cast("list[dict[str, Any]]", await self.get("/epics/attachments", params=params))

    async def create_epic_attachment(
        self,
        epic_id: int,
        project_id: int,
        attached_file: str,
        description: str | None = None,
        is_deprecated: bool = False,
    ) -> dict[str, Any]:
        """Create an attachment for an epic.

        Args:
            epic_id: ID of the epic
            project_id: ID of the project
            attached_file: Path to file to attach
            description: Optional description
            is_deprecated: Whether attachment is deprecated

        Returns:
            Created attachment data
        """
        data = {
            "object_id": epic_id,
            "project": project_id,
            "attached_file": attached_file,
            "is_deprecated": is_deprecated,
        }
        if description:
            data["description"] = description
        return cast("dict[str, Any]", await self.post("/epics/attachments", data=data))

    async def get_epic_attachment(self, attachment_id: int) -> dict[str, Any]:
        """Get a specific epic attachment.

        Args:
            attachment_id: ID of the attachment

        Returns:
            Attachment data
        """
        return cast("dict[str, Any]", await self.get(f"/epics/attachments/{attachment_id}"))

    async def update_epic_attachment(
        self,
        attachment_id: int,
        description: str | None = None,
        is_deprecated: bool | None = None,
    ) -> dict[str, Any]:
        """Update an epic attachment.

        Args:
            attachment_id: ID of the attachment
            description: New description
            is_deprecated: Whether attachment is deprecated

        Returns:
            Updated attachment data
        """
        data: dict[str, Any] = {}
        if description is not None:
            data["description"] = description
        if is_deprecated is not None:
            data["is_deprecated"] = is_deprecated
        return cast(
            "dict[str, Any]", await self.patch(f"/epics/attachments/{attachment_id}", data=data)
        )

    async def delete_epic_attachment(self, attachment_id: int) -> bool:
        """Delete an epic attachment.

        Args:
            attachment_id: ID of the attachment

        Returns:
            True if deleted successfully
        """
        return await self.delete(f"/epics/attachments/{attachment_id}")

    # Epic filters
    async def get_epic_filters(self, project: int) -> dict[str, Any]:
        """Get available filters for epics in a project.

        Args:
            project: ID of the project

        Returns:
            Available filter options
        """
        return cast("dict[str, Any]", await self.get(f"/epics/filters_data?project={project}"))

    # Epic custom attributes
    async def list_epic_custom_attributes(self, project: int) -> list[dict[str, Any]]:
        """List custom attributes defined for epics in a project.

        Args:
            project: ID of the project

        Returns:
            List of custom attribute definitions
        """
        return cast(
            "list[dict[str, Any]]",
            await self.get(f"/epic-custom-attributes?project={project}"),
        )

    async def create_epic_custom_attribute(
        self,
        project_id: int,
        name: str,
        description: str | None = None,
        order: int | None = None,
    ) -> dict[str, Any]:
        """Create a custom attribute for epics.

        Args:
            project_id: ID of the project
            name: Name of the custom attribute
            description: Optional description
            order: Optional display order

        Returns:
            Created custom attribute data
        """
        data: dict[str, Any] = {"project": project_id, "name": name}
        if description is not None:
            data["description"] = description
        if order is not None:
            data["order"] = order
        return cast("dict[str, Any]", await self.post("/epic-custom-attributes", data=data))

    async def get_epic_custom_attribute_values(self, epic_id: int) -> dict[str, Any]:
        """Get custom attribute values for a specific epic.

        Args:
            epic_id: ID of the epic

        Returns:
            Custom attribute values for the epic
        """
        return cast("dict[str, Any]", await self.get(f"/epics/custom-attributes-values/{epic_id}"))

    async def update_epic_custom_attribute_values(
        self,
        epic_id: int,
        attributes_values: dict[str, Any],
        version: int | None = None,
    ) -> dict[str, Any]:
        """Update custom attribute values for an epic.

        Args:
            epic_id: ID of the epic
            attributes_values: Dictionary of attribute ID to value
            version: Version for optimistic concurrency control

        Returns:
            Updated custom attribute values
        """
        data: dict[str, Any] = {"attributes_values": attributes_values}
        if version is not None:
            data["version"] = version
        return cast(
            "dict[str, Any]",
            await self.patch(f"/epics/custom-attributes-values/{epic_id}", data=data),
        )


# Alias for backwards compatibility
TaigaClient = TaigaAPIClient
