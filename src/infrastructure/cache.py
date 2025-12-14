"""Sistema de caché en memoria con TTL.

Este módulo implementa un sistema de caché en memoria con TTL configurable
para reducir llamadas redundantes a endpoints de metadatos de Taiga.

Features:
- TTL configurable por entrada
- Límite máximo de entradas
- Invalidación por patrón
- Métricas de hit/miss
- Thread-safe con asyncio.Lock
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class CacheEntry:
    """Entrada individual del caché con valor y tiempo de expiración.

    Attributes:
        value: Valor almacenado en la entrada del caché.
        expires_at: Momento en que la entrada expira.
    """

    value: Any
    expires_at: datetime

    def is_expired(self) -> bool:
        """Verifica si la entrada ha expirado.

        Returns:
            True si la entrada ha expirado, False en caso contrario.
        """
        return datetime.now() > self.expires_at


@dataclass
class CacheMetrics:
    """Métricas de rendimiento del caché.

    Attributes:
        hits: Número de aciertos en el caché.
        misses: Número de fallos en el caché.
        evictions: Número de entradas eliminadas por expiración o límite.
        invalidations: Número de invalidaciones manuales.
    """

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    invalidations: int = 0

    @property
    def total_requests(self) -> int:
        """Número total de solicitudes al caché."""
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        """Tasa de aciertos del caché (0.0 a 1.0)."""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    @property
    def miss_rate(self) -> float:
        """Tasa de fallos del caché (0.0 a 1.0)."""
        if self.total_requests == 0:
            return 0.0
        return self.misses / self.total_requests

    def reset(self) -> None:
        """Reinicia todas las métricas a cero."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.invalidations = 0


@dataclass
class MemoryCache:
    """Caché en memoria con TTL y limpieza automática.

    Implementa un caché thread-safe con soporte para TTL configurable,
    límite de tamaño y métricas de rendimiento.

    Attributes:
        default_ttl: TTL por defecto en segundos para nuevas entradas.
        max_size: Número máximo de entradas permitidas en el caché.
    """

    default_ttl: int = 3600
    max_size: int = 1000
    _cache: dict[str, CacheEntry] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _metrics: CacheMetrics = field(default_factory=CacheMetrics)

    async def get(self, key: str) -> Any | None:
        """Obtiene valor del caché si existe y no expiró.

        Args:
            key: Clave de la entrada a obtener.

        Returns:
            El valor almacenado si existe y no ha expirado, None en caso contrario.
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is not None:
                if not entry.is_expired():
                    self._metrics.hits += 1
                    return entry.value
                # Entrada expirada, eliminar
                del self._cache[key]
                self._metrics.evictions += 1
            self._metrics.misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Guarda valor en caché con TTL.

        Si el caché está lleno, primero elimina las entradas expiradas.
        Si aún está lleno después de la limpieza, elimina la entrada más antigua.

        Args:
            key: Clave bajo la cual almacenar el valor.
            value: Valor a almacenar.
            ttl: TTL en segundos. Si es None, usa el default_ttl.
        """
        async with self._lock:
            # Si estamos en el límite, limpiar expiradas primero
            if len(self._cache) >= self.max_size and key not in self._cache:
                await self._evict_expired_unlocked()

            # Si aún estamos en el límite, eliminar la más antigua
            if len(self._cache) >= self.max_size and key not in self._cache:
                await self._evict_oldest_unlocked()

            expires_at = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> bool:
        """Elimina una entrada específica del caché.

        Args:
            key: Clave de la entrada a eliminar.

        Returns:
            True si la entrada existía y fue eliminada, False si no existía.
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._metrics.invalidations += 1
                return True
            return False

    async def invalidate(self, pattern: str) -> int:
        """Invalida entradas que coincidan con el patrón.

        Args:
            pattern: Patrón a buscar en las claves (búsqueda por substring).

        Returns:
            Número de entradas invalidadas.
        """
        async with self._lock:
            keys_to_delete = [k for k in self._cache if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
            self._metrics.invalidations += len(keys_to_delete)
            return len(keys_to_delete)

    async def clear(self) -> int:
        """Limpia todo el caché.

        Returns:
            Número de entradas eliminadas.
        """
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._metrics.invalidations += count
            return count

    async def _evict_expired_unlocked(self) -> int:
        """Elimina todas las entradas expiradas (sin lock).

        Este método debe ser llamado solo cuando ya se tiene el lock.

        Returns:
            Número de entradas eliminadas.
        """
        now = datetime.now()
        keys_to_delete = [k for k, entry in self._cache.items() if entry.expires_at <= now]
        for key in keys_to_delete:
            del self._cache[key]
        self._metrics.evictions += len(keys_to_delete)
        return len(keys_to_delete)

    async def _evict_oldest_unlocked(self) -> bool:
        """Elimina la entrada más antigua (sin lock).

        Este método debe ser llamado solo cuando ya se tiene el lock.

        Returns:
            True si se eliminó una entrada, False si el caché estaba vacío.
        """
        if not self._cache:
            return False

        # Encontrar la entrada que expira primero
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].expires_at)
        del self._cache[oldest_key]
        self._metrics.evictions += 1
        return True

    async def evict_expired(self) -> int:
        """Elimina todas las entradas expiradas.

        Returns:
            Número de entradas eliminadas.
        """
        async with self._lock:
            return await self._evict_expired_unlocked()

    def get_metrics(self) -> CacheMetrics:
        """Obtiene las métricas actuales del caché.

        Returns:
            Objeto CacheMetrics con las métricas actuales.
        """
        return self._metrics

    def reset_metrics(self) -> None:
        """Reinicia las métricas del caché a cero."""
        self._metrics.reset()

    async def size(self) -> int:
        """Obtiene el número actual de entradas en el caché.

        Returns:
            Número de entradas en el caché.
        """
        async with self._lock:
            return len(self._cache)

    async def contains(self, key: str) -> bool:
        """Verifica si una clave existe en el caché (sin actualizar métricas).

        Args:
            key: Clave a verificar.

        Returns:
            True si la clave existe y no ha expirado, False en caso contrario.
        """
        async with self._lock:
            entry = self._cache.get(key)
            return bool(entry is not None and not entry.is_expired())

    async def get_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas completas del caché.

        Returns:
            Diccionario con estadísticas del caché incluyendo:
            - size: Número de entradas
            - max_size: Tamaño máximo
            - default_ttl: TTL por defecto
            - metrics: Métricas de hit/miss
        """
        async with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "default_ttl": self.default_ttl,
                "metrics": {
                    "hits": self._metrics.hits,
                    "misses": self._metrics.misses,
                    "evictions": self._metrics.evictions,
                    "invalidations": self._metrics.invalidations,
                    "total_requests": self._metrics.total_requests,
                    "hit_rate": self._metrics.hit_rate,
                    "miss_rate": self._metrics.miss_rate,
                },
            }
