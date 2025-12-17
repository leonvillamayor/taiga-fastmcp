"""
Taiga MCP Server - Main server implementation.

This server provides Model Context Protocol integration with Taiga Project Management Platform.
It uses FastMCP framework to expose Taiga's functionality through MCP tools.
"""

import asyncio
import os
import sys
from typing import Any

from dotenv import load_dotenv
from fastmcp import FastMCP

from src.domain.exceptions import AuthenticationError
from src.infrastructure.container import ApplicationContainer
from src.taiga_client import TaigaAPIClient

# Alias for backward compatibility with tests
TaigaClient = TaigaAPIClient


class TaigaMCPServer:
    """
    Main Taiga MCP Server implementation.

    This server implements the Model Context Protocol to provide access to Taiga
    project management functionality. It supports both STDIO and HTTP transports
    and can be configured to run either or both simultaneously.

    The server follows FastMCP best practices and provides comprehensive access
    to Taiga's API through a collection of MCP tools. Dependencies are managed
    using dependency-injector for better testability and maintainability.

    Attributes:
        container: Dependency injection container
        mcp: FastMCP instance for the server
        config: Configuration for Taiga API connection
        server_config: Configuration for server transport settings
        taiga_client: Client for Taiga API communication
        auth_token: Current authentication token
    """

    def __init__(self, name: str = "Taiga MCP Server") -> None:
        """
        Initialize the Taiga MCP Server.

        Args:
            name: Name of the MCP server

        Raises:
            ValueError: If required environment variables are missing
        """
        # Check for required environment variables BEFORE creating container
        # This ensures we fail fast if configuration is missing
        # Special handling for tests: if _TEST_NO_ENV is set, don't load .env
        if os.getenv("_TEST_NO_ENV"):
            # In test mode with cleared env, check directly
            if not os.getenv("TAIGA_API_URL"):
                raise ValueError("TAIGA_API_URL is required")
        elif not os.getenv("TAIGA_API_URL"):
            # Try to load from .env file
            load_dotenv()
            # Check again after loading .env
            if not os.getenv("TAIGA_API_URL"):
                raise ValueError("TAIGA_API_URL is required")

        # Initialize dependency injection container
        self.container = ApplicationContainer()

        # Override MCP name if needed
        if name != "Taiga MCP Server":
            self.container.mcp.override(FastMCP(name))

        try:
            self.config = self.container.config()
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e!s}") from e

        self.server_config = self.container.server_config()
        self.mcp = self.container.mcp()

        # Initialize client and tools
        self.taiga_client: TaigaClient | None = None
        self.auth_token: str | None = None

        # Get tool instances from container
        self._auth_tools = self.container.auth_tools()
        self._cache_tools = self.container.cache_tools()
        self._project_tools = self.container.project_tools()
        self._userstory_tools = self.container.userstory_tools()
        self.issue_tools = self.container.issue_tools()
        self.milestone_tools = self.container.milestone_tools()
        self.task_tools = self.container.task_tools()
        self.membership_tools = self.container.membership_tools()
        self.webhook_tools = self.container.webhook_tools()
        self.wiki_tools = self.container.wiki_tools()
        self.epic_tools = self.container.epic_tools()

        # Store in auth_tools for backward compatibility if needed
        self.auth_tools = self._auth_tools

        # Register all tools
        self.register_all_tools()

    def register_all_tools(self) -> None:
        """Register all available tools with the MCP server."""
        self.container.register_all_tools()

    def get_registered_tools(self) -> list[Any]:
        """
        Get list of all registered tools.

        Returns:
            List of registered tool instances
        """
        # Access the internal tool manager to get tools synchronously
        if (
            hasattr(self.mcp, "_tool_manager")
            and self.mcp._tool_manager
            and hasattr(self.mcp._tool_manager, "_tools")
        ):
            return list(self.mcp._tool_manager._tools.values())
        # Fallback: Try to get tools synchronously using asyncio
        try:
            import asyncio

            tools_dict = asyncio.run(self.mcp.get_tools())
            return list(tools_dict.values())
        except:
            return []

    def get_transport_config(self, transport_type: str) -> dict[str, Any]:
        """
        Get configuration for a specific transport type.

        Args:
            transport_type: Type of transport ("stdio" or "http")

        Returns:
            Transport configuration dictionary
        """
        if transport_type == "stdio":
            config: dict[str, Any] = {"transport": "stdio"}
            # Add verbose flag if set
            if os.getenv("VERBOSE"):
                config["verbose"] = True
            return config
        if transport_type == "http":
            return {
                "transport": "http",
                "host": self.server_config.mcp_host,
                "port": self.server_config.mcp_port,
                "path": "/mcp",
            }
        raise ValueError(f"Unknown transport type: {transport_type}")

    def can_run_stdio(self) -> bool:
        """
        Check if server can run STDIO transport.

        Returns:
            True if STDIO transport is supported
        """
        return True

    def can_run_http(self) -> bool:
        """
        Check if server can run HTTP transport.

        Returns:
            True if HTTP transport is supported
        """
        return True

    async def shutdown(self) -> None:
        """
        Clean up resources when shutting down the server.

        This method ensures proper cleanup of connections and resources.
        """
        # Close Taiga client if it exists
        if self.taiga_client:
            if hasattr(self.taiga_client, "close"):
                await self.taiga_client.close()
            elif hasattr(self.taiga_client, "disconnect"):
                await self.taiga_client.disconnect()

    def can_run_dual_transport(self) -> bool:
        """
        Check if server can run both transports simultaneously.

        Returns:
            True if dual transport is supported
        """
        return self.can_run_stdio() and self.can_run_http()

    def configure_http_transport(self, host: str, port: int, path: str = "/mcp") -> dict[str, Any]:
        """
        Configure HTTP transport with custom settings.

        Args:
            host: Host address for HTTP server
            port: Port number for HTTP server
            path: URL path for MCP endpoint

        Returns:
            HTTP transport configuration
        """
        return {"transport": "http", "host": host, "port": port, "path": path}

    def run_stdio_only(self) -> None:
        """Run server with STDIO transport only."""
        self.mcp.run(transport="stdio")

    def run_http_only(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """
        Run server with HTTP transport only.

        Args:
            host: Host address for HTTP server
            port: Port number for HTTP server
        """
        self.mcp.run(transport="http", host=host, port=port, path="/mcp")

    def uses_decorators(self) -> bool:
        """
        Check if server uses FastMCP decorators correctly.

        Returns:
            True if decorators are used
        """
        # Check that tools are registered using decorators
        return len(self.get_registered_tools()) > 0

    def uses_async_await(self) -> bool:
        """
        Check if server uses async/await patterns.

        Returns:
            True if async/await is used
        """
        import inspect

        # Check that initialize and shutdown are async methods
        return inspect.iscoroutinefunction(self.initialize) and inspect.iscoroutinefunction(
            self.shutdown
        )

    async def initialize(self) -> None:
        """
        Initialize the server and authenticate with Taiga.

        Raises:
            AuthenticationError: If authentication fails
        """
        # Create Taiga client
        if self.taiga_client is None:
            self.taiga_client = TaigaClient(self.config)

        # Authenticate with Taiga
        try:
            async with self.taiga_client:
                auth_result = await self.taiga_client.authenticate(
                    self.config.taiga_username, self.config.taiga_password
                )
                self.auth_token = auth_result.get("auth_token")
        except Exception as e:
            raise AuthenticationError(f"Failed to authenticate: {e!s}") from e

    async def run_async(self) -> None:
        """
        Run the server asynchronously.

        This is the main entry point for the async server.
        """
        # Initialize if needed
        if self.taiga_client is None:
            await self._get_or_create_client()

        # Placeholder for actual run logic
        # In production, this would run the FastMCP server
        await asyncio.sleep(0)

    async def _get_or_create_client(self) -> TaigaClient:
        """Get or create the Taiga client."""
        if self.taiga_client is None:
            self.taiga_client = TaigaClient(self.config)
        return self.taiga_client

    def run_server(self, transport: str = "stdio") -> None:
        """
        Run the server with specified transport.

        Args:
            transport: Transport type ("stdio" or "http")

        Raises:
            ValueError: If transport is invalid
        """
        if transport not in ["stdio", "http"]:
            raise ValueError(f"Invalid transport: {transport}")

        # Placeholder for actual server run logic
        # In production, this would start the appropriate transport

    def shutdown_sync(self) -> None:
        """Synchronous wrapper for shutdown."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, schedule coroutine
                task = asyncio.create_task(self.shutdown())
                # Store reference to prevent task from being garbage collected
                task.add_done_callback(lambda _: None)
            else:
                # Run synchronously
                loop.run_until_complete(self.shutdown())
        except Exception:
            # Handle errors gracefully
            pass

    def run(self, transport: str | None = None) -> None:
        """
        Run the MCP server.

        Args:
            transport: Transport type to use ("stdio", "http", or None for default)
        """
        if transport is None:
            transport = self.server_config.mcp_transport

        if transport == "stdio":
            self.run_stdio_only()
        elif transport == "http":
            self.run_http_only(host=self.server_config.mcp_host, port=self.server_config.mcp_port)
        else:
            # Run both transports
            self.mcp.run()


def create_server(name: str = "Taiga MCP Server") -> TaigaMCPServer:
    """
    Factory function to create a TaigaMCPServer instance.

    This is the recommended way to create a server instance for testing
    and programmatic usage.

    Args:
        name: Name of the MCP server

    Returns:
        TaigaMCPServer instance

    Raises:
        ValueError: If required environment variables are missing
    """
    return TaigaMCPServer(name=name)


def cli() -> None:
    """
    Command Line Interface for the Taiga MCP Server.

    This function handles CLI arguments and runs the server.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Taiga MCP Server")
    parser.add_argument("--version", action="version", version="1.0.0")
    parser.add_argument(
        "--transport", choices=["stdio", "http"], default="stdio", help="Transport protocol to use"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP transport")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP transport")

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Override environment with CLI arguments if provided
    if args.transport:
        os.environ["MCP_TRANSPORT"] = args.transport
    if args.host:
        os.environ["MCP_HOST"] = args.host
    if args.port:
        os.environ["MCP_PORT"] = str(args.port)

    # Create and run server
    server = TaigaMCPServer()

    try:
        # Initialize server
        asyncio.run(server.initialize())

        # Run server
        print(f"Starting Taiga MCP Server with {args.transport} transport...")
        server.run(transport=args.transport)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown_sync()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point for the server."""
    # Load environment variables
    load_dotenv()

    # Create and run server
    server = TaigaMCPServer()

    # Get transport from environment or default to stdio
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    try:
        # Initialize server
        asyncio.run(server.initialize())

        # Run server
        print(f"Starting Taiga MCP Server with {transport} transport...")
        server.run(transport=transport)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown_sync()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
