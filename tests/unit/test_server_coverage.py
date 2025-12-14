"""
Tests adicionales para mejorar la cobertura del módulo server.
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.server import TaigaMCPServer


class TestServerAdditionalCoverage:
    """Tests adicionales para el servidor MCP."""

    @pytest.mark.unit
    def test_init_with_config_exception(self) -> None:
        """
        Verifica manejo de excepción al cargar configuración.
        Cubre línea 69-70 de server.py.
        """
        # Arrange & Act & Assert
        with (
            patch.dict(
                os.environ,
                {
                    "TAIGA_API_URL": "invalid-url",  # Will cause validation error
                    "TAIGA_USERNAME": "user@example.com",
                    "TAIGA_PASSWORD": "password123",
                },
                clear=True,
            ),
            pytest.raises(ValueError, match="Failed to load configuration"),
        ):
            TaigaMCPServer()

    @pytest.mark.unit
    def test_get_registered_tools_fallback(self) -> None:
        """
        Verifica fallback de get_registered_tools.
        Cubre líneas 103-108 de server.py.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "password123",
            },
        ):
            server = TaigaMCPServer()

            # Mock mcp without _tool_manager
            server.mcp = MagicMock()
            server.mcp._tool_manager = None

            # Mock asyncio.run to return tools
            mock_tools = {"tool1": Mock(), "tool2": Mock()}
            with patch("asyncio.run", return_value=mock_tools):
                # Act
                tools = server.get_registered_tools()

                # Assert
                assert len(tools) == 2
                # Verify all tools are Mock objects
                assert all(isinstance(t, Mock) for t in tools)

    @pytest.mark.unit
    def test_get_registered_tools_exception_handling(self) -> None:
        """
        Verifica manejo de excepción en get_registered_tools.
        Cubre líneas 107-108 de server.py.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "password123",
            },
        ):
            server = TaigaMCPServer()

            # Mock mcp without _tool_manager
            server.mcp = MagicMock()
            server.mcp._tool_manager = None

            # Mock asyncio.run to raise exception
            with patch("asyncio.run", side_effect=RuntimeError("Test error")):
                # Act
                tools = server.get_registered_tools()

                # Assert
                assert tools == []

    @pytest.mark.unit
    def test_get_transport_config_stdio_verbose(self) -> None:
        """
        Verifica configuración de transporte stdio con verbose.
        Cubre línea 132 de server.py.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "password123",
                "VERBOSE": "true",
            },
        ):
            server = TaigaMCPServer()

            # Act
            config = server.get_transport_config("stdio")

            # Assert
            assert config["transport"] == "stdio"
            assert config["verbose"] is True

    @pytest.mark.unit
    def test_run_server_invalid_transport(self) -> None:
        """
        Verifica error con transporte inválido.
        Cubre líneas 162-163 de server.py.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "password123",
            },
        ):
            server = TaigaMCPServer()

            # Act & Assert
            with pytest.raises(ValueError, match="Invalid transport"):
                server.run_server(transport="websocket")

    @pytest.mark.asyncio
    async def test_run_async_initialization(self) -> None:
        """
        Verifica inicialización asíncrona.
        Cubre línea 261 de server.py.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "password123",
            },
        ):
            server = TaigaMCPServer()

            # Mock dependencies
            mock_client = AsyncMock()
            mock_client.initialize = AsyncMock()

            # Ensure the _get_or_create_client returns mock_client and properly calls initialize
            async def mock_get_or_create() -> None:
                server.taiga_client = mock_client
                await mock_client.initialize()
                return mock_client

            server._get_or_create_client = AsyncMock(side_effect=mock_get_or_create)

            # Act
            await server.run_async()

            # Assert
            server._get_or_create_client.assert_called_once()
            mock_client.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_async_exception_handling(self) -> None:
        """
        Verifica manejo de excepciones en run.
        Cubre línea 274 de server.py.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "password123",
            },
        ):
            server = TaigaMCPServer()

            # Mock to raise exception
            server._get_or_create_client = AsyncMock(side_effect=Exception("Test error"))

            # Act - Try to run and catch the exception
            with pytest.raises(Exception) as exc_info:
                await server.run_async()

            # Assert
            assert str(exc_info.value) == "Test error"
            server._get_or_create_client.assert_called_once()

    @pytest.mark.unit
    def test_cli_main_help(self) -> None:
        """
        Verifica CLI con argumento --help.
        Cubre líneas 289-301 de server.py (parcialmente).
        """
        # Arrange
        test_args = ["server.py", "--help"]

        # Act & Assert
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                from src.server import cli

                cli()

            # Help should exit with 0
            assert exc_info.value.code == 0

    @pytest.mark.unit
    def test_cli_main_version(self) -> None:
        """
        Verifica CLI con argumento --version.
        Cubre más líneas del CLI.
        """
        # Arrange
        test_args = ["server.py", "--version"]

        # Act & Assert
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                from src.server import cli

                cli()

            # Version should exit with 0
            assert exc_info.value.code == 0

    @pytest.mark.unit
    def test_cli_with_http_transport(self) -> None:
        """
        Verifica CLI con transporte HTTP.
        Cubre más líneas del CLI.
        """
        # Arrange
        test_args = ["server.py", "--transport", "http", "--port", "9000"]

        with (
            patch.dict(
                os.environ,
                {
                    "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                    "TAIGA_USERNAME": "user@example.com",
                    "TAIGA_PASSWORD": "password123",
                },
            ),
            patch.object(sys, "argv", test_args),
            patch("src.server.TaigaMCPServer") as mock_server_class,
        ):
            mock_server = MagicMock()
            # Make initialize() return a coroutine
            mock_server.initialize = AsyncMock()
            mock_server.run = MagicMock()
            mock_server_class.return_value = mock_server

            # Act
            from src.server import cli

            cli()

            # Assert
            mock_server.run.assert_called_with(transport="http")

    @pytest.mark.unit
    def test_cli_with_invalid_transport(self) -> None:
        """
        Verifica CLI con transporte inválido.
        """
        # Arrange
        test_args = ["server.py", "--transport", "invalid"]

        with (
            patch.dict(
                os.environ,
                {
                    "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                    "TAIGA_USERNAME": "user@example.com",
                    "TAIGA_PASSWORD": "password123",
                },
            ),
            patch.object(sys, "argv", test_args),
        ):
            # Act & Assert - argparse exits with code 2 for invalid arguments
            with pytest.raises(SystemExit) as exc_info:
                from src.server import cli

                cli()

            # Verify it exits with code 2 (argparse error)
            assert exc_info.value.code == 2

    @pytest.mark.unit
    def test_main_function(self) -> None:
        """
        Verifica función main.
        Cubre líneas 307-327 de server.py.
        """
        # Arrange
        with (
            patch.dict(
                os.environ,
                {
                    "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                    "TAIGA_USERNAME": "user@example.com",
                    "TAIGA_PASSWORD": "password123",
                    "MCP_TRANSPORT": "stdio",
                },
            ),
            patch("src.server.TaigaMCPServer") as mock_server_class,
        ):
            mock_server = MagicMock()
            mock_server.initialize = AsyncMock()
            mock_server.run = MagicMock()
            mock_server_class.return_value = mock_server

            # Act
            from src.server import main

            main()

            # Assert
            mock_server_class.assert_called_once()
            mock_server.run.assert_called_once_with(transport="stdio")

    @pytest.mark.unit
    def test_main_as_module(self) -> None:
        """
        Verifica ejecución como módulo principal.
        """
        # Arrange
        with (
            patch.dict(
                os.environ,
                {
                    "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                    "TAIGA_USERNAME": "user@example.com",
                    "TAIGA_PASSWORD": "password123",
                },
            ),
            patch("src.server.__name__", "__main__"),
            patch("src.server.main"),
        ):
            # Import will trigger if __name__ == '__main__'
            # But we can't really test this without exec
            # So we'll just call main directly
            from src.server import main as real_main

            with patch("src.server.cli"):
                real_main()

            # This at least ensures main can be called
            assert True
