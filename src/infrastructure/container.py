"""Container de inyección de dependencias.

Este módulo implementa el container de inyección de dependencias usando
dependency-injector para gestionar todas las dependencias de la aplicación.
"""

from typing import Any

from dependency_injector import containers, providers
from fastmcp import FastMCP

from src.application.prompts.taiga_prompts import TaigaPrompts
from src.application.resources.taiga_resources import TaigaResources
from src.application.tools.auth_tools import AuthTools
from src.application.tools.cache_tools import CacheTools
from src.application.tools.epic_tools import EpicTools
from src.application.tools.issue_tools import IssueTools
from src.application.tools.membership_tools import MembershipTools
from src.application.tools.milestone_tools import MilestoneTools
from src.application.tools.project_tools import ProjectTools
from src.application.tools.search_tools import SearchTools
from src.application.tools.settings_tools import SettingsTools
from src.application.tools.task_tools import TaskTools
from src.application.tools.userstory_tools import UserStoryTools
from src.application.tools.webhook_tools import WebhookTools
from src.application.tools.wiki_tools import WikiTools
from src.application.use_cases import (
    EpicUseCases,
    IssueUseCases,
    MemberUseCases,
    MilestoneUseCases,
    ProjectUseCases,
    TaskUseCases,
    UserStoryUseCases,
    WikiUseCases,
)
from src.config import ServerConfig, TaigaConfig
from src.infrastructure.cache import MemoryCache
from src.infrastructure.cached_client import CachedTaigaClient
from src.infrastructure.http_session_pool import HTTPSessionPool
from src.infrastructure.logging import LoggingConfig, setup_logging
from src.infrastructure.metrics import MetricsCollector
from src.infrastructure.repositories.epic_repository_impl import EpicRepositoryImpl
from src.infrastructure.repositories.issue_repository_impl import IssueRepositoryImpl
from src.infrastructure.repositories.member_repository_impl import MemberRepositoryImpl
from src.infrastructure.repositories.milestone_repository_impl import (
    MilestoneRepositoryImpl,
)
from src.infrastructure.repositories.project_repository_impl import (
    ProjectRepositoryImpl,
)
from src.infrastructure.repositories.task_repository_impl import TaskRepositoryImpl
from src.infrastructure.repositories.user_story_repository_impl import (
    UserStoryRepositoryImpl,
)
from src.infrastructure.repositories.wiki_repository_impl import WikiRepositoryImpl
from src.taiga_client import TaigaAPIClient


class _Container(containers.DeclarativeContainer):
    """Container interno de dependency injector.

    Este es el container de dependency-injector puro que define
    todos los providers.
    """

    # Configuración (Singleton porque es inmutable)
    config = providers.Singleton(TaigaConfig)

    server_config = providers.Singleton(ServerConfig)

    # Logging configuration (Singleton)
    logging_config = providers.Singleton(LoggingConfig)

    # FastMCP instance (Singleton)
    mcp = providers.Singleton(FastMCP, name="taiga-mcp-server")

    # HTTP Session Pool (Singleton - reutiliza conexiones HTTP)
    http_session_pool = providers.Singleton(
        HTTPSessionPool,
        base_url=config.provided.api_url,
        timeout=config.provided.timeout,
        max_connections=100,
        max_keepalive=20,
    )

    # Cliente Taiga (Factory porque cada request puede necesitar su instancia)
    taiga_client = providers.Factory(
        TaigaAPIClient,
        config=config,
        session_pool=http_session_pool,
    )

    # Memory Cache (Singleton - una sola instancia compartida)
    memory_cache = providers.Singleton(
        MemoryCache,
        default_ttl=3600,  # 1 hora por defecto
        max_size=1000,
    )

    # Metrics Collector (Singleton - recolector de métricas thread-safe)
    metrics_collector = providers.Singleton(MetricsCollector)

    # Cached Taiga Client (Singleton - wrapper con caché)
    cached_taiga_client = providers.Singleton(
        CachedTaigaClient,
        client=taiga_client,
        cache=memory_cache,
    )

    # Repositorios (Singleton - usan el mismo taiga_client factory)
    epic_repository = providers.Singleton(EpicRepositoryImpl, client=taiga_client)
    project_repository = providers.Singleton(ProjectRepositoryImpl, client=taiga_client)
    user_story_repository = providers.Singleton(UserStoryRepositoryImpl, client=taiga_client)
    task_repository = providers.Singleton(TaskRepositoryImpl, client=taiga_client)
    issue_repository = providers.Singleton(IssueRepositoryImpl, client=taiga_client)
    milestone_repository = providers.Singleton(MilestoneRepositoryImpl, client=taiga_client)
    member_repository = providers.Singleton(MemberRepositoryImpl, client=taiga_client)
    wiki_repository = providers.Singleton(WikiRepositoryImpl, client=taiga_client)

    # Use Cases (Singleton - inyectan repositorios)
    epic_use_cases = providers.Singleton(EpicUseCases, repository=epic_repository)
    project_use_cases = providers.Singleton(ProjectUseCases, repository=project_repository)
    user_story_use_cases = providers.Singleton(UserStoryUseCases, repository=user_story_repository)
    task_use_cases = providers.Singleton(TaskUseCases, repository=task_repository)
    issue_use_cases = providers.Singleton(IssueUseCases, repository=issue_repository)
    milestone_use_cases = providers.Singleton(MilestoneUseCases, repository=milestone_repository)
    member_use_cases = providers.Singleton(MemberUseCases, repository=member_repository)
    wiki_use_cases = providers.Singleton(WikiUseCases, repository=wiki_repository)

    # Tools (Singleton)
    auth_tools = providers.Singleton(AuthTools, mcp=mcp)

    cache_tools = providers.Singleton(CacheTools, mcp=mcp)

    epic_tools = providers.Singleton(EpicTools, mcp=mcp)

    project_tools = providers.Singleton(ProjectTools, mcp=mcp)

    userstory_tools = providers.Singleton(UserStoryTools, mcp=mcp)

    issue_tools = providers.Singleton(IssueTools, mcp=mcp)

    milestone_tools = providers.Singleton(MilestoneTools, mcp=mcp)

    task_tools = providers.Singleton(TaskTools, mcp=mcp)

    membership_tools = providers.Singleton(MembershipTools, mcp=mcp)

    webhook_tools = providers.Singleton(WebhookTools, mcp=mcp)

    wiki_tools = providers.Singleton(WikiTools, mcp=mcp)

    settings_tools = providers.Singleton(SettingsTools, mcp=mcp)

    search_tools = providers.Singleton(SearchTools, mcp=mcp)

    # MCP Resources (Singleton)
    taiga_resources = providers.Singleton(TaigaResources, mcp=mcp)

    # MCP Prompts (Singleton)
    taiga_prompts = providers.Singleton(TaigaPrompts, mcp=mcp)


class ApplicationContainer:
    """Container principal de la aplicación.

    Este container gestiona todas las dependencias de la aplicación usando
    dependency-injector, facilitando la inyección de dependencias y testing.

    Attributes:
        config: Configuración de Taiga API
        server_config: Configuración del servidor MCP
        mcp: Instancia de FastMCP
        http_session_pool: Pool de sesiones HTTP reutilizables
        memory_cache: Caché en memoria con TTL
        metrics_collector: Recolector de métricas thread-safe
        taiga_client: Cliente de la API de Taiga
        cached_taiga_client: Cliente de Taiga con caché
        epic_repository: Repositorio de Epics
        project_repository: Repositorio de Proyectos
        user_story_repository: Repositorio de User Stories
        task_repository: Repositorio de Tasks
        issue_repository: Repositorio de Issues
        milestone_repository: Repositorio de Milestones
        member_repository: Repositorio de Members
        wiki_repository: Repositorio de Wiki Pages
        epic_use_cases: Casos de uso de Epics
        project_use_cases: Casos de uso de Proyectos
        user_story_use_cases: Casos de uso de User Stories
        task_use_cases: Casos de uso de Tasks
        issue_use_cases: Casos de uso de Issues
        milestone_use_cases: Casos de uso de Milestones
        member_use_cases: Casos de uso de Members
        wiki_use_cases: Casos de uso de Wiki Pages
        auth_tools: Herramientas de autenticación
        epic_tools: Herramientas de Epics
        project_tools: Herramientas de proyectos
        userstory_tools: Herramientas de user stories
        issue_tools: Herramientas de issues
        milestone_tools: Herramientas de milestones
        task_tools: Herramientas de tareas
        membership_tools: Herramientas de membresías
        webhook_tools: Herramientas de webhooks
        wiki_tools: Herramientas de wiki
    """

    def __init__(self) -> None:
        """Inicializa el container de aplicación."""
        self._container = _Container()
        # Setup logging on container initialization
        logging_config = self._container.logging_config()
        setup_logging(logging_config)

    def __getattr__(self, name: str) -> Any:
        """Delega los atributos al container interno."""
        return getattr(self._container, name)

    def register_all_tools(self) -> None:
        """Registra todas las herramientas, recursos y prompts en el servidor MCP."""
        # Register tools
        self._container.auth_tools().register_tools()
        self._container.cache_tools().register_tools()
        self._container.epic_tools().register_tools()
        self._container.project_tools().register_tools()
        self._container.userstory_tools().register_tools()
        self._container.issue_tools().register_tools()
        # milestone_tools y task_tools usan _register_tools() automático en __init__
        self._container.milestone_tools()  # Solo instanciar
        self._container.task_tools()  # Solo instanciar
        self._container.membership_tools().register_tools()
        self._container.webhook_tools().register_tools()
        self._container.wiki_tools().register_tools()
        self._container.settings_tools().register_tools()
        self._container.search_tools().register_tools()

        # Register MCP resources
        self._container.taiga_resources().register_resources()

        # Register MCP prompts
        self._container.taiga_prompts().register_prompts()

    async def start_session_pool(self) -> None:
        """Inicia el pool de sesiones HTTP.

        Debe llamarse antes de realizar peticiones a la API de Taiga.
        """
        pool: HTTPSessionPool = self._container.http_session_pool()
        await pool.start()

    async def stop_session_pool(self) -> None:
        """Detiene el pool de sesiones HTTP.

        Debe llamarse al finalizar la aplicación para liberar recursos.
        """
        pool: HTTPSessionPool = self._container.http_session_pool()
        await pool.stop()

    def get_session_pool(self) -> HTTPSessionPool:
        """Obtiene la instancia del pool de sesiones HTTP.

        Returns:
            HTTPSessionPool: El pool de sesiones HTTP singleton.
        """
        return self._container.http_session_pool()

    def get_memory_cache(self) -> MemoryCache:
        """Obtiene la instancia del caché en memoria.

        Returns:
            MemoryCache: El caché en memoria singleton.
        """
        return self._container.memory_cache()

    def get_cached_client(self) -> CachedTaigaClient:
        """Obtiene la instancia del cliente Taiga cacheado.

        Returns:
            CachedTaigaClient: El cliente cacheado singleton.
        """
        return self._container.cached_taiga_client()

    def get_metrics_collector(self) -> MetricsCollector:
        """Obtiene la instancia del recolector de métricas.

        Returns:
            MetricsCollector: El recolector de métricas singleton.
        """
        return self._container.metrics_collector()

    async def clear_cache(self) -> int:
        """Limpia todo el caché de metadatos.

        Returns:
            int: Número de entradas eliminadas.
        """
        cached_client: CachedTaigaClient = self._container.cached_taiga_client()
        return await cached_client.clear_cache()

    async def get_cache_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas del caché.

        Returns:
            dict: Estadísticas del caché incluyendo métricas de hit/miss.
        """
        cached_client: CachedTaigaClient = self._container.cached_taiga_client()
        return await cached_client.get_stats()
