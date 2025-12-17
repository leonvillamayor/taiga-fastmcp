"""Cliente Taiga con cacheo inteligente.

Este módulo implementa un wrapper sobre TaigaAPIClient que cachea
automáticamente las llamadas a endpoints de metadatos para reducir
la carga en la API.

Features:
- Cacheo automático de endpoints estáticos
- TTL configurable por tipo de endpoint
- Métricas de hit/miss disponibles
- Invalidación manual de caché
"""

from typing import TYPE_CHECKING, Any, ClassVar, cast

from src.infrastructure.cache import CacheMetrics, MemoryCache

if TYPE_CHECKING:
    from src.taiga_client import TaigaAPIClient


class CacheKeyBuilder:
    """Constructor de claves para el caché.

    Genera claves únicas basadas en el tipo de endpoint y sus parámetros.
    """

    @staticmethod
    def build(endpoint_type: str, **params: Any) -> str:
        """Construye una clave de caché única.

        Args:
            endpoint_type: Tipo de endpoint (e.g., 'epic_filters').
            **params: Parámetros adicionales para distinguir la clave.

        Returns:
            Clave única para el caché.
        """
        param_str = ":".join(f"{k}={v}" for k, v in sorted(params.items()) if v is not None)
        if param_str:
            return f"{endpoint_type}:{param_str}"
        return endpoint_type


class CachedTaigaClient:
    """Cliente Taiga con cacheo inteligente.

    Envuelve un TaigaAPIClient y cachea automáticamente las llamadas
    a endpoints de metadatos (filtros, atributos personalizados, módulos).

    Attributes:
        CACHEABLE_ENDPOINTS: Diccionario de endpoints cacheables con sus TTLs.
    """

    # Endpoints cacheables con TTL en segundos
    CACHEABLE_ENDPOINTS: ClassVar[dict[str, int]] = {
        "epic_filters": 3600,  # 1 hora
        "issue_filters": 3600,
        "task_filters": 3600,
        "userstory_filters": 3600,
        "project_modules": 1800,  # 30 minutos
        "epic_custom_attributes": 3600,
        "issue_custom_attributes": 3600,
        "task_custom_attributes": 3600,
        "userstory_custom_attributes": 3600,
        "project_stats": 600,  # 10 minutos (cambian más frecuentemente)
        "milestone_stats": 600,
    }

    def __init__(
        self,
        client: "TaigaAPIClient",
        cache: MemoryCache | None = None,
    ) -> None:
        """Inicializa el cliente cacheado.

        Args:
            client: Instancia de TaigaAPIClient a envolver.
            cache: Instancia de MemoryCache. Si es None, crea una nueva.
        """
        self._client = client
        self._cache = cache or MemoryCache()

    @property
    def client(self) -> "TaigaAPIClient":
        """Obtiene el cliente subyacente."""
        return self._client

    @property
    def cache(self) -> MemoryCache:
        """Obtiene la instancia del caché."""
        return self._cache

    def get_ttl(self, endpoint_type: str) -> int:
        """Obtiene el TTL para un tipo de endpoint.

        Args:
            endpoint_type: Tipo de endpoint.

        Returns:
            TTL en segundos, o el default_ttl si no está definido.
        """
        return self.CACHEABLE_ENDPOINTS.get(endpoint_type, self._cache.default_ttl)

    async def get_cached_or_fetch(
        self,
        endpoint_type: str,
        fetch_func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Obtiene datos del caché o los recupera de la API.

        Esta es la función principal para obtener datos cacheables.
        Primero intenta obtener del caché, si no existe llama a la función
        de fetch y guarda el resultado.

        Args:
            endpoint_type: Tipo de endpoint para determinar TTL.
            fetch_func: Función async que recupera los datos de la API.
            *args: Argumentos posicionales para fetch_func.
            **kwargs: Argumentos keyword para fetch_func y para la clave del caché.

        Returns:
            Los datos del caché o de la API.
        """
        # Construir clave de caché
        cache_key = CacheKeyBuilder.build(endpoint_type, **kwargs)

        # Intentar obtener del caché
        cached_value = await self._cache.get(cache_key)
        if cached_value is not None:
            return cached_value

        # Llamar a la función de fetch
        result = await fetch_func(*args, **kwargs)

        # Guardar en caché con TTL apropiado
        ttl = self.get_ttl(endpoint_type)
        await self._cache.set(cache_key, result, ttl)

        return result

    # === Métodos de filtros cacheados ===

    async def get_epic_filters(self, project_id: int) -> dict[str, Any]:
        """Obtiene filtros de epics (cacheado).

        Args:
            project_id: ID del proyecto.

        Returns:
            Filtros disponibles para epics.
        """
        # Usamos project_id para consistencia en claves de caché e invalidación
        # Luego pasamos como 'project' al método del cliente
        cache_key = CacheKeyBuilder.build("epic_filters", project_id=project_id)
        cached_value = await self._cache.get(cache_key)
        if cached_value is not None:
            return cast("dict[str, Any]", cached_value)

        result = await self._client.get_epic_filters(project=project_id)
        ttl = self.get_ttl("epic_filters")
        await self._cache.set(cache_key, result, ttl)
        return result

    async def get_issue_filters(self, project_id: int) -> dict[str, Any]:
        """Obtiene filtros de issues (cacheado).

        Args:
            project_id: ID del proyecto.

        Returns:
            Filtros disponibles para issues.
        """
        result = await self.get_cached_or_fetch(
            "issue_filters",
            self._client.get_issue_filters_data,
            project_id=project_id,
        )
        return cast("dict[str, Any]", result)

    async def get_task_filters(self, project_id: int) -> dict[str, Any]:
        """Obtiene filtros de tareas (cacheado).

        Args:
            project_id: ID del proyecto.

        Returns:
            Filtros disponibles para tareas.
        """
        result = await self.get_cached_or_fetch(
            "task_filters",
            self._client.get_task_filters,
            project_id=project_id,
        )
        return cast("dict[str, Any]", result)

    # === Métodos de atributos personalizados cacheados ===

    async def list_epic_custom_attributes(self, project_id: int) -> list[dict[str, Any]]:
        """Lista atributos personalizados de epics (cacheado).

        Args:
            project_id: ID del proyecto.

        Returns:
            Lista de atributos personalizados.
        """
        # Usamos project_id para consistencia en claves de caché e invalidación
        cache_key = CacheKeyBuilder.build("epic_custom_attributes", project_id=project_id)
        cached_value = await self._cache.get(cache_key)
        if cached_value is not None:
            return cast("list[dict[str, Any]]", cached_value)

        result = await self._client.list_epic_custom_attributes(project=project_id)
        ttl = self.get_ttl("epic_custom_attributes")
        await self._cache.set(cache_key, result, ttl)
        return result

    # === Métodos de invalidación ===

    async def invalidate_project_cache(self, project_id: int) -> int:
        """Invalida todo el caché relacionado con un proyecto.

        Args:
            project_id: ID del proyecto.

        Returns:
            Número de entradas invalidadas.
        """
        pattern = f"project_id={project_id}"
        return await self._cache.invalidate(pattern)

    async def invalidate_endpoint_type(self, endpoint_type: str) -> int:
        """Invalida todo el caché de un tipo de endpoint.

        Args:
            endpoint_type: Tipo de endpoint (e.g., 'epic_filters').

        Returns:
            Número de entradas invalidadas.
        """
        return await self._cache.invalidate(endpoint_type)

    async def clear_cache(self) -> int:
        """Limpia todo el caché.

        Returns:
            Número de entradas eliminadas.
        """
        return await self._cache.clear()

    # === Métodos de métricas ===

    def get_metrics(self) -> CacheMetrics:
        """Obtiene las métricas del caché.

        Returns:
            Objeto CacheMetrics con las métricas actuales.
        """
        return self._cache.get_metrics()

    def reset_metrics(self) -> None:
        """Reinicia las métricas del caché."""
        self._cache.reset_metrics()

    async def get_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas completas del caché.

        Returns:
            Diccionario con estadísticas del caché.
        """
        return await self._cache.get_stats()

    # === Delegación al cliente subyacente ===

    def __getattr__(self, name: str) -> Any:
        """Delega atributos no encontrados al cliente subyacente.

        Esto permite usar el CachedTaigaClient como si fuera el
        TaigaAPIClient original para métodos no cacheados.

        Args:
            name: Nombre del atributo.

        Returns:
            El atributo del cliente subyacente.
        """
        return getattr(self._client, name)
