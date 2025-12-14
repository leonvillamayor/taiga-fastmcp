"""
Fixture helper para configurar herramientas MCP con mocks.
"""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from fastmcp import FastMCP


@pytest.fixture
def mcp_server_real(taiga_client_mock, monkeypatch) -> None:
    """Mock del servidor MCP con todas las herramientas correctamente configuradas."""

    server = Mock()
    mcp = FastMCP("Test")

    # Patch global de TaigaAPIClient para herramientas que lo importan directamente
    mock_client_instance = MagicMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=taiga_client_mock)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)

    # Patchear TODOS los módulos que importan TaigaAPIClient
    # Todos los tools ahora usan TaigaAPIClient(self.config) localmente
    monkeypatch.setattr(
        "src.application.tools.wiki_tools.TaigaAPIClient", lambda config: mock_client_instance
    )
    monkeypatch.setattr(
        "src.application.tools.membership_tools.TaigaAPIClient",
        lambda config: mock_client_instance,
    )
    monkeypatch.setattr(
        "src.application.tools.webhook_tools.TaigaAPIClient", lambda config: mock_client_instance
    )
    monkeypatch.setattr(
        "src.application.tools.userstory_tools.TaigaAPIClient", lambda config: mock_client_instance
    )
    monkeypatch.setattr(
        "src.application.tools.auth_tools.TaigaAPIClient", lambda config: mock_client_instance
    )
    monkeypatch.setattr(
        "src.application.tools.project_tools.TaigaAPIClient", lambda config: mock_client_instance
    )
    # Tools migrados al patrón TaigaAPIClient local (ya no usan set_client)
    monkeypatch.setattr(
        "src.application.tools.issue_tools.TaigaAPIClient", lambda config: mock_client_instance
    )
    monkeypatch.setattr(
        "src.application.tools.task_tools.TaigaAPIClient", lambda config: mock_client_instance
    )
    monkeypatch.setattr(
        "src.application.tools.milestone_tools.TaigaAPIClient", lambda config: mock_client_instance
    )
    monkeypatch.setattr(
        "src.application.tools.epic_tools.TaigaAPIClient", lambda config: mock_client_instance
    )
    monkeypatch.setattr(
        "src.application.tools.user_tools.TaigaAPIClient", lambda config: mock_client_instance
    )

    # Importar herramientas desde application/tools
    from src.application.tools.auth_tools import AuthTools
    from src.application.tools.issue_tools import IssueTools
    from src.application.tools.membership_tools import MembershipTools
    from src.application.tools.milestone_tools import MilestoneTools
    from src.application.tools.project_tools import ProjectTools
    from src.application.tools.task_tools import TaskTools
    from src.application.tools.userstory_tools import UserStoryTools
    from src.application.tools.webhook_tools import WebhookTools
    from src.application.tools.wiki_tools import WikiTools

    # Herramientas migradas al patrón TaigaAPIClient local (patcheadas arriba)
    server.issue_tools = IssueTools(mcp)
    server.issue_tools.register_tools()

    # task_tools y milestone_tools usan _register_tools automático en __init__
    server.task_tools = TaskTools(mcp)

    server.milestone_tools = MilestoneTools(mcp)

    # Herramientas que importan TaigaAPIClient (patcheadas arriba)
    server.wiki_tools = WikiTools(mcp)
    server.wiki_tools.register_tools()

    server.membership_tools = MembershipTools(mcp)
    server.membership_tools.register_tools()

    server.webhook_tools = WebhookTools(mcp)
    server.webhook_tools.register_tools()

    server.userstory_tools = UserStoryTools(mcp)
    server.userstory_tools.register_tools()

    server.auth_tools = AuthTools(mcp)
    server.auth_tools.register_tools()

    server.project_tools = ProjectTools(mcp)
    server.project_tools.register_tools()

    # Epic tools (migrado al patrón TaigaAPIClient local)
    try:
        from src.application.tools.epic_tools import EpicTools

        epic_tools = EpicTools(mcp)
        epic_tools.register_tools()
        server.epic_tools = epic_tools
    except ImportError:
        pass

    # User tools (usa TaigaAPIClient local)
    try:
        from src.application.tools.user_tools import UserTools

        user_tools = UserTools(mcp)
        user_tools.register_tools()
        server.user_tools = user_tools
    except ImportError:
        pass

    return server
