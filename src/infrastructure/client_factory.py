"""
Factory para crear clientes Taiga con cache compartido.

Este modulo proporciona funciones factory para obtener clientes Taiga
con cache integrado, asegurando que todos los tools compartan la misma
instancia de cache para maximizar los hits.

Features:
- Cache global singleton compartido entre todos los tools
- Factory function para obtener clientes cacheados
- Funciones de invalidacion para operaciones de escritura
"""

from src.config import TaigaConfig
from src.infrastructure.cache import MemoryCache
from src.infrastructure.cached_client import CachedTaigaClient
from src.taiga_client import TaigaAPIClient


# Cache global compartido - singleton
_global_cache: MemoryCache | None = None


def get_global_cache() -> MemoryCache:
    """
    Obtiene la instancia global del cache.

    La instancia se crea de forma lazy la primera vez que se llama.
    Todas las llamadas subsecuentes retornan la misma instancia.

    Returns:
        MemoryCache: Instancia singleton del cache.
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = MemoryCache(default_ttl=3600, max_size=1000)
    return _global_cache


def reset_global_cache() -> None:
    """
    Reinicia la instancia global del cache.

    Util principalmente para tests donde se necesita un cache limpio.
    """
    global _global_cache
    _global_cache = None


def get_taiga_client(auth_token: str | None = None) -> TaigaAPIClient:
    """
    Crea un cliente Taiga sin cache (para compatibilidad hacia atras).

    Args:
        auth_token: Token de autenticacion opcional.

    Returns:
        TaigaAPIClient: Cliente sin cache.
    """
    config = TaigaConfig()
    client = TaigaAPIClient(config)
    if auth_token:
        client.auth_token = auth_token
    return client


def get_cached_taiga_client(auth_token: str | None = None) -> CachedTaigaClient:
    """
    Crea un cliente Taiga con cache.

    El cache es compartido entre todas las instancias de clientes cacheados,
    lo que permite aprovechar los hits de cache entre diferentes tools.

    Args:
        auth_token: Token de autenticacion opcional.

    Returns:
        CachedTaigaClient: Cliente configurado con cache global.
    """
    config = TaigaConfig()
    base_client = TaigaAPIClient(config)
    if auth_token:
        base_client.auth_token = auth_token
    return CachedTaigaClient(base_client, cache=get_global_cache())


async def invalidate_project_cache(project_id: int) -> int:
    """
    Invalida cache relacionado con un proyecto.

    Debe llamarse despues de operaciones de escritura que afecten
    datos del proyecto (create, update, delete).

    Args:
        project_id: ID del proyecto a invalidar.

    Returns:
        int: Numero de entradas invalidadas.
    """
    cache = get_global_cache()
    return await cache.invalidate(f"project_id={project_id}")


async def invalidate_cache_by_pattern(pattern: str) -> int:
    """
    Invalida entradas de cache que coincidan con un patron.

    Args:
        pattern: Patron a buscar en las claves del cache.

    Returns:
        int: Numero de entradas invalidadas.
    """
    cache = get_global_cache()
    return await cache.invalidate(pattern)


async def clear_all_cache() -> int:
    """
    Limpia todo el cache.

    Returns:
        int: Numero de entradas eliminadas.
    """
    cache = get_global_cache()
    return await cache.clear()
