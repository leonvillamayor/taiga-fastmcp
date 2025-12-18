# Plan Detallado Release 0.3.0 - taiga-fastmcp

## Resumen Ejecutivo

Este documento describe el plan de trabajo para llevar el proyecto taiga-fastmcp a la release 0.3.0 con:
- Cobertura de tests superior al 90%
- Cobertura completa de la API de Taiga
- Mejoras en el uso de FastMCP
- Sistema de cache optimizado para autenticacion
- Configuracion Docker/Docker Compose

---

## Estado Actual del Proyecto

### Metricas Actuales

| Metrica | Valor Actual | Objetivo |
|---------|--------------|----------|
| Cobertura de tests | 88.37% | >90% |
| Herramientas MCP | 224 | Completo |
| Resources MCP | 6 | Mantener |
| Prompts MCP | 7 | Mantener |
| Tests fallando | 6 | 0 |

### Archivos con Menor Cobertura

| Archivo | Cobertura | Prioridad |
|---------|-----------|-----------|
| `src/infrastructure/logging/decorators.py` | 7.18% | ALTA |
| `src/infrastructure/http_session_pool.py` | 56.67% | ALTA |
| `src/infrastructure/repositories/epic_repository_impl.py` | 66.67% | MEDIA |
| `src/infrastructure/repositories/user_story_repository_impl.py` | 74.44% | MEDIA |
| `src/server.py` | 77.21% | MEDIA |
| `src/infrastructure/cached_client.py` | 82.05% | BAJA |
| `src/infrastructure/repositories/task_repository_impl.py` | 84.04% | BAJA |

### Tests Fallando Actualmente (6)

1. `tests/integration/test_projects_integration.py::test_project_with_all_modules_activated`
2. `tests/integration/test_projects_integration.py::test_project_members_management`
3. `tests/integration/test_projects_integration.py::test_project_stats_retrieval`
4. `tests/integration/test_projects_integration.py::test_project_duplicate_name_handling`
5. `tests/integration/test_projects_integration.py::test_project_search_and_filter`
6. `tests/integration/tools/test_epic_tools_integration.py::test_call_delete_epic`

---

## Fase 1: Correccion de Tests Fallidos

**Duracion estimada**: 1-2 dias
**Responsable**: Desarrollador
**Prioridad**: CRITICA

### Tareas

#### 1.1 Analizar y corregir tests de proyectos
- **Archivo**: `tests/integration/test_projects_integration.py`
- **Accion**: Revisar por que fallan los 5 tests relacionados con proyectos
- **Posibles causas**: Mocks desactualizados, cambios en la API, fixtures incorrectas

#### 1.2 Corregir test de epic tools
- **Archivo**: `tests/integration/tools/test_epic_tools_integration.py`
- **Accion**: Revisar el test `test_call_delete_epic`
- **Posible causa**: Problema con el mock del cliente o respuesta esperada

### Verificacion
```bash
uv run pytest tests/integration/test_projects_integration.py -v
uv run pytest tests/integration/tools/test_epic_tools_integration.py::test_call_delete_epic -v
```

---

## Fase 2: Mejora de Cobertura de Tests (>90%)

**Duracion estimada**: 3-4 dias
**Prioridad**: ALTA

### 2.1 Tests para logging/decorators.py (Cobertura: 7.18% -> 80%+)

**Archivo destino**: `tests/unit/infrastructure/test_logging_decorators.py`

**Tests a crear**:
1. `test_log_operation_decorator_sync_function`
2. `test_log_operation_decorator_async_function`
3. `test_log_operation_with_exception`
4. `test_log_api_call_decorator_success`
5. `test_log_api_call_decorator_failure`
6. `test_log_api_call_with_retry`
7. `test_log_context_manager_entry_exit`
8. `test_sensitive_argument_masking`
9. `test_correlation_id_propagation`
10. `test_timing_measurement`
11. `test_nested_decorators`
12. `test_decorator_with_custom_logger`
13. `test_log_level_configuration`
14. `test_async_context_preservation`
15. `test_exception_logging_format`

**Estimacion**: 15-20 tests nuevos

### 2.2 Tests para http_session_pool.py (Cobertura: 56.67% -> 85%+)

**Archivo destino**: `tests/unit/infrastructure/test_http_session_pool_extended.py`

**Tests a crear**:
1. `test_pool_shutdown_cleanup`
2. `test_pool_connection_timeout_handling`
3. `test_pool_max_connections_exceeded`
4. `test_pool_connection_reuse_after_error`
5. `test_pool_concurrent_connection_limits`
6. `test_pool_idle_connection_cleanup`
7. `test_pool_health_check_mechanism`
8. `test_pool_graceful_shutdown`
9. `test_pool_force_shutdown`
10. `test_pool_statistics_tracking`

**Estimacion**: 10-15 tests nuevos

### 2.3 Tests para container.py

**Archivo destino**: `tests/unit/infrastructure/test_container.py`

**Tests a crear**:
1. `test_container_initialization`
2. `test_container_config_provider`
3. `test_container_mcp_provider`
4. `test_container_repository_providers`
5. `test_container_use_case_providers`
6. `test_container_tool_providers`
7. `test_container_client_factory_integration`
8. `test_container_singleton_behavior`
9. `test_container_override_providers`
10. `test_container_reset`

**Estimacion**: 10-15 tests nuevos

### 2.4 Tests para repository implementations

**Archivos destino**:
- `tests/unit/infrastructure/repositories/test_epic_repository_impl_extended.py`
- `tests/unit/infrastructure/repositories/test_user_story_repository_impl_extended.py`
- `tests/unit/infrastructure/repositories/test_task_repository_impl_extended.py`

**Tests por archivo**:
1. `test_empty_result_handling`
2. `test_pagination_edge_cases`
3. `test_filter_combinations`
4. `test_error_response_handling`
5. `test_timeout_handling`

**Estimacion**: 15 tests nuevos (5 por repositorio)

### 2.5 Tests para server.py

**Archivo destino**: `tests/unit/test_server_extended.py`

**Tests a crear**:
1. `test_server_startup_error_handling`
2. `test_server_tool_registration_failure`
3. `test_server_shutdown_cleanup`
4. `test_server_http_transport_config`
5. `test_server_stdio_transport_config`
6. `test_server_missing_env_vars`
7. `test_server_invalid_config`
8. `test_server_reconnection_logic`

**Estimacion**: 8-10 tests nuevos

### Resumen Fase 2

| Modulo | Tests Actuales | Tests Nuevos | Cobertura Estimada |
|--------|---------------|--------------|-------------------|
| logging/decorators.py | 0 | 15-20 | 80%+ |
| http_session_pool.py | ~10 | 10-15 | 85%+ |
| container.py | 0 | 10-15 | 90%+ |
| Repository impls | Varios | 15 | 85%+ |
| server.py | ~10 | 8-10 | 85%+ |
| **TOTAL** | - | **58-75** | **>90%** |

---

## Fase 3: Mejoras en FastMCP

**Duracion estimada**: 2-3 dias
**Prioridad**: MEDIA

### 3.1 Implementar Middleware Stack

**Archivo**: `src/server.py`

**Middleware a agregar**:

```python
from fastmcp.server.middleware.errors import ErrorHandlingMiddleware
from fastmcp.server.middleware.ratelimit import RateLimitingMiddleware
from fastmcp.server.middleware.logging import StructuredLoggingMiddleware
from fastmcp.server.middleware.timing import DetailedTimingMiddleware

# En __init__ de TaigaMCPServer:
self.mcp.add_middleware(ErrorHandlingMiddleware(max_retries=3))
self.mcp.add_middleware(RateLimitingMiddleware(
    max_requests_per_second=50,
    algorithm="token_bucket"
))
self.mcp.add_middleware(DetailedTimingMiddleware())
self.mcp.add_middleware(StructuredLoggingMiddleware())
```

### 3.2 Agregar Anotaciones a Tools

**Archivos**: Todos en `src/application/tools/`

**Anotaciones a agregar**:
- `readOnlyHint: True` para tools de lectura (list, get)
- `destructiveHint: True` para tools de eliminacion (delete)
- `idempotentHint: True` para operaciones idempotentes

**Ejemplo**:
```python
@self.mcp.tool(
    name="taiga_list_projects",
    description="List all projects",
    annotations={
        "readOnlyHint": True,
        "openWorldHint": False
    }
)
async def list_projects(...):
    ...
```

### 3.3 Mejorar Manejo de Errores

**Archivos**: Todos los tools

**Cambio**:
```python
# Antes
except Exception as e:
    return {"error": str(e)}

# Despues
from fastmcp.exceptions import ToolError

except TaigaAPIError as e:
    raise ToolError(f"API error: {e}")
except ValidationError as e:
    raise ToolError(f"Validation error: {e}")
```

### 3.4 Configuracion de Produccion

**Archivo**: `src/server.py`

```python
mcp = FastMCP(
    name="Taiga MCP Server",
    mask_error_details=True,  # Produccion: ocultar stack traces
    strict_input_validation=True,
    on_duplicate_tools="error"
)
```

---

## Fase 4: Optimizacion de Cache para Autenticacion

**Duracion estimada**: 2 dias
**Prioridad**: ALTA

### 4.1 Cache de Token de Autenticacion

**Archivo nuevo**: `src/infrastructure/auth_cache.py`

**Funcionalidad**:
```python
class AuthTokenCache:
    """Cache especifico para tokens de autenticacion.

    Features:
    - TTL basado en expiracion del token
    - Refresh automatico antes de expiracion
    - Singleton por instancia de servidor
    """

    def __init__(self, refresh_threshold_seconds: int = 300):
        self._token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: datetime | None = None
        self._refresh_threshold = timedelta(seconds=refresh_threshold_seconds)
        self._lock = asyncio.Lock()

    async def get_valid_token(self, refresh_func) -> str:
        """Obtiene token valido, refrescando si es necesario."""
        async with self._lock:
            if self._needs_refresh():
                await self._refresh(refresh_func)
            return self._token

    def _needs_refresh(self) -> bool:
        if not self._token or not self._expires_at:
            return True
        return datetime.now() + self._refresh_threshold > self._expires_at
```

### 4.2 Integracion con CachedTaigaClient

**Archivo**: `src/infrastructure/cached_client.py`

**Cambios**:
- Agregar AuthTokenCache como dependencia
- Usar token cacheado en todas las llamadas
- Invalidar cache de auth en logout

### 4.3 Cache de Middleware FastMCP (Opcional)

Si se requiere cache a nivel de responses MCP:

```python
from fastmcp.server.middleware.caching import ResponseCachingMiddleware
from key_value.aio.stores.disk import DiskStore

mcp.add_middleware(ResponseCachingMiddleware(
    cache_storage=DiskStore(directory=".cache/mcp"),
    ttl=300  # 5 minutos para responses
))
```

---

## Fase 5: Verificacion de Cobertura API Taiga

**Duracion estimada**: 1 dia
**Prioridad**: MEDIA

### 5.1 Herramientas Ya Implementadas (224 tools)

| Categoria | Implementadas | API Taiga | Estado |
|-----------|---------------|-----------|--------|
| Auth | 5 | 2 | COMPLETO |
| Projects | 22 | ~15 | COMPLETO |
| User Stories | 20+ | ~28 | COMPLETO |
| Issues | 28 | ~24 | COMPLETO |
| Epics | 29 | ~24 | COMPLETO |
| Tasks | 29 | ~24 | COMPLETO |
| Milestones | 10 | ~9 | COMPLETO |
| Wiki | 14 | ~10 | COMPLETO |
| Memberships | 5 | 5 | COMPLETO |
| Webhooks | 6 | ~5 | COMPLETO |
| Users | 3 | ~3 | COMPLETO |
| Settings | 46 | ~40 | COMPLETO |
| Search | 3 | 1 | COMPLETO |
| Cache | 4 | N/A | EXTRA |

### 5.2 Funcionalidades Verificadas como Completas

Todas las funcionalidades principales de la API de Taiga estan cubiertas:
- CRUD completo para todas las entidades
- Operaciones bulk
- Votacion y watchers
- Attachments
- Historia y comentarios
- Custom attributes
- Filtros

**Conclusion**: No se requieren herramientas adicionales.

---

## Fase 6: Docker y Docker Compose

**Duracion estimada**: 1-2 dias
**Prioridad**: MEDIA

### 6.1 Dockerfile

**Archivo**: `Dockerfile`

```dockerfile
# Build stage
FROM python:3.13-slim AS builder

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Runtime stage
FROM python:3.13-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code
COPY src/ ./src/

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# Expose port for HTTP transport
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Default command (STDIO transport)
CMD ["python", "-m", "src.server"]
```

### 6.2 Docker Compose

**Archivo**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  taiga-mcp:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: taiga-mcp-server
    environment:
      - TAIGA_API_URL=${TAIGA_API_URL}
      - TAIGA_USERNAME=${TAIGA_USERNAME}
      - TAIGA_PASSWORD=${TAIGA_PASSWORD}
      - MCP_TRANSPORT=http
      - MCP_HOST=0.0.0.0
      - MCP_PORT=8000
      - LOG_LEVEL=INFO
    ports:
      - "8000:8000"
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
      - ./.cache:/app/.cache
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  # Opcional: Redis para cache distribuido
  redis:
    image: redis:7-alpine
    container_name: taiga-mcp-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped

volumes:
  redis-data:
```

### 6.3 Archivo .env.example

**Archivo**: `.env.example`

```bash
# Taiga API Configuration
TAIGA_API_URL=https://api.taiga.io/api/v1
TAIGA_USERNAME=your_username
TAIGA_PASSWORD=your_password

# MCP Server Configuration
MCP_TRANSPORT=stdio  # stdio | http
MCP_HOST=0.0.0.0
MCP_PORT=8000

# Logging
LOG_LEVEL=INFO

# Cache (opcional)
CACHE_TTL=3600
CACHE_MAX_SIZE=1000

# Redis (opcional, para cache distribuido)
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## Fase 7: Release y GitHub

**Duracion estimada**: 1 dia
**Prioridad**: ALTA

### 7.1 Actualizacion de Version

**Archivo**: `pyproject.toml`

```toml
[project]
name = "taiga-fastmcp"
version = "0.3.0"  # Cambiar de 0.2.0 a 0.3.0
```

### 7.2 Actualizacion CHANGELOG

**Archivo**: `CHANGELOG.md`

```markdown
## [0.3.0] - 2024-XX-XX

### Added
- Middleware stack de FastMCP (ErrorHandling, RateLimiting, Logging, Timing)
- Cache optimizado para tokens de autenticacion
- Anotaciones en tools (readOnlyHint, destructiveHint)
- Configuracion Docker y Docker Compose
- Tests adicionales para cobertura >90%

### Changed
- Mejorado manejo de errores con ToolError de FastMCP
- Optimizado sistema de cache en memoria

### Fixed
- Corregidos 6 tests de integracion fallidos
- Mejorada cobertura de logging/decorators.py
- Mejorada cobertura de http_session_pool.py

### Technical
- Cobertura de tests: 88.37% -> 90%+
- 58-75 tests nuevos agregados
```

### 7.3 Comandos para Release

```bash
# 1. Asegurar que todos los tests pasan
uv run pytest --cov=src --cov-fail-under=90

# 2. Verificar linting
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# 3. Crear commit de release
git add .
git commit -m "release: version 0.3.0 - improved coverage, FastMCP middleware, Docker support"

# 4. Crear tag
git tag -a v0.3.0 -m "Release 0.3.0"

# 5. Push branch y tag
git push origin release/0.3.0
git push origin v0.3.0

# 6. Crear PR a main
gh pr create --title "Release 0.3.0" --body "..."

# 7. Merge y crear GitHub Release
gh release create v0.3.0 --title "v0.3.0" --notes-file CHANGELOG.md
```

---

## Cronograma Resumido

| Fase | Descripcion | Duracion | Prioridad |
|------|-------------|----------|-----------|
| 1 | Correccion tests fallidos | 1-2 dias | CRITICA |
| 2 | Mejora cobertura >90% | 3-4 dias | ALTA |
| 3 | Mejoras FastMCP | 2-3 dias | MEDIA |
| 4 | Optimizacion cache auth | 2 dias | ALTA |
| 5 | Verificacion API Taiga | 1 dia | MEDIA |
| 6 | Docker/Docker Compose | 1-2 dias | MEDIA |
| 7 | Release GitHub | 1 dia | ALTA |
| **TOTAL** | | **11-15 dias** | |

---

## Archivos Implicados por Fase

### Fase 1
- `tests/integration/test_projects_integration.py`
- `tests/integration/tools/test_epic_tools_integration.py`

### Fase 2
- `tests/unit/infrastructure/test_logging_decorators.py` (NUEVO)
- `tests/unit/infrastructure/test_http_session_pool_extended.py` (NUEVO)
- `tests/unit/infrastructure/test_container.py` (NUEVO)
- `tests/unit/infrastructure/repositories/test_*_extended.py` (NUEVOS)
- `tests/unit/test_server_extended.py` (NUEVO)

### Fase 3
- `src/server.py`
- `src/application/tools/*.py` (todos)

### Fase 4
- `src/infrastructure/auth_cache.py` (NUEVO)
- `src/infrastructure/cached_client.py`
- `src/infrastructure/client_factory.py`

### Fase 5
- Solo documentacion

### Fase 6
- `Dockerfile` (NUEVO)
- `docker-compose.yml` (NUEVO)
- `.env.example` (NUEVO)
- `.dockerignore` (NUEVO)

### Fase 7
- `pyproject.toml`
- `CHANGELOG.md`
- `README.md`

---

## Verificacion Final

Antes de la release, ejecutar:

```bash
# Tests completos con cobertura
uv run pytest --cov=src --cov-report=html --cov-fail-under=90

# Linting
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# Type checking
uv run mypy src/

# Security
uv run bandit -r src/

# Build Docker
docker build -t taiga-mcp:0.3.0 .
docker-compose up -d
docker-compose logs -f

# Health check
curl http://localhost:8000/health
```

---

**Documento generado**: 2024
**Version del plan**: 1.0
**Proyecto**: taiga-fastmcp
**Release objetivo**: 0.3.0
