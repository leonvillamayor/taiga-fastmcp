# Documento de Mejoras - Taiga FastMCP v0.1.1

## Índice

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Análisis de Cobertura de Funcionalidades Taiga](#análisis-de-cobertura-de-funcionalidades-taiga)
3. [Análisis de Uso de FastMCP](#análisis-de-uso-de-fastmcp)
4. [Análisis del Sistema de Caché](#análisis-del-sistema-de-caché)
5. [Mejoras Propuestas](#mejoras-propuestas)
6. [Funcionalidades Faltantes](#funcionalidades-faltantes)
7. [Recomendaciones de Arquitectura](#recomendaciones-de-arquitectura)

---

## Resumen Ejecutivo

### Estado Actual
El proyecto implementa un servidor MCP para interactuar con la API de Taiga. Se han identificado:

| Categoría | Estado | Cobertura |
|-----------|--------|-----------|
| Autenticación | ✅ Completo | 100% |
| Proyectos | ✅ Mayormente completo | 85% |
| User Stories | ✅ Mayormente completo | 90% |
| Issues | ✅ Implementado | 80% |
| Tasks | ✅ Implementado | 80% |
| Epics | ✅ Implementado | 85% |
| Milestones | ✅ Implementado | 75% |
| Wiki | ✅ Implementado | 70% |
| Webhooks | ⚠️ Parcial | 50% |
| Memberships | ✅ Implementado | 75% |
| Users | ✅ Implementado | 80% |
| Atributos Personalizados | ❌ No implementado | 0% |
| History/Comentarios | ⚠️ Parcial | 40% |
| **Sistema de Caché** | ⚠️ **Implementado pero NO integrado** | 0% uso |

### Hallazgo Crítico: Sistema de Caché No Integrado

El proyecto tiene infraestructura de caché completa en:
- `src/infrastructure/cache.py` - MemoryCache con TTL, métricas, invalidación
- `src/infrastructure/cached_client.py` - CachedTaigaClient wrapper

**Pero NO se está usando en ningún tool MCP.** Cada llamada va directamente a la API de Taiga, causando:
- Mayor latencia
- Riesgo de rate limiting
- Carga innecesaria en servidor Taiga

Ver sección [Análisis del Sistema de Caché](#análisis-del-sistema-de-caché) para detalles.

---

## Análisis de Cobertura de Funcionalidades Taiga

### 1. Autenticación (`auth_tools.py`)

#### Implementado ✅
- `taiga_authenticate` - Login con usuario/contraseña
- `taiga_refresh_token` - Renovar token
- `taiga_get_current_user` - Obtener usuario actual
- `taiga_logout` - Cerrar sesión

#### Conforme a documentación Taiga
La implementación cubre todos los endpoints de autenticación documentados:
- `POST /api/v1/auth` ✅
- `POST /api/v1/auth/refresh` ✅
- `GET /api/v1/users/me` ✅

---

### 2. Proyectos (`project_tools.py`)

#### Implementado ✅
- `taiga_list_projects` - Listar proyectos
- `taiga_get_project` - Obtener proyecto por ID
- `taiga_get_project_by_slug` - Obtener por slug
- `taiga_create_project` - Crear proyecto
- `taiga_update_project` - Actualizar proyecto
- `taiga_delete_project` - Eliminar proyecto
- `taiga_get_project_stats` - Estadísticas
- `taiga_get_project_issues_stats` - Estadísticas de issues
- `taiga_duplicate_project` - Duplicar proyecto
- `taiga_create_project_tag` - Crear tag
- `taiga_edit_project_tag` - Editar tag
- `taiga_delete_project_tag` - Eliminar tag

#### Faltante según documentación Taiga ❌
| Endpoint | Descripción | Prioridad |
|----------|-------------|-----------|
| `GET /api/v1/projects/{id}/modules` | Obtener módulos del proyecto | Media |
| `PATCH /api/v1/projects/{id}/modules` | Modificar módulos | Media |
| `POST /api/v1/projects/{id}/like` | Like a proyecto | Baja |
| `POST /api/v1/projects/{id}/unlike` | Unlike a proyecto | Baja |
| `POST /api/v1/projects/{id}/watch` | Watch proyecto | Media |
| `POST /api/v1/projects/{id}/unwatch` | Unwatch proyecto | Media |
| `POST /api/v1/projects/bulk_update_order` | Reordenar proyectos | Baja |
| `POST /api/v1/projects/{id}/mix_tags` | Mezclar tags | Baja |

---

### 3. User Stories (`userstory_tools.py`)

#### Implementado ✅
- `taiga_list_userstories` - Listar con filtros
- `taiga_get_userstory` - Obtener por ID
- `taiga_get_userstory_by_ref` - Obtener por referencia
- `taiga_create_userstory` - Crear
- `taiga_update_userstory` - Actualizar
- `taiga_delete_userstory` - Eliminar
- `taiga_bulk_create_userstories` - Crear en lote
- `taiga_bulk_update_userstories` - Actualizar en lote
- `taiga_bulk_delete_userstories` - Eliminar en lote
- `taiga_move_to_milestone` - Mover a sprint
- `taiga_get_userstory_history` - Historial
- `taiga_watch_userstory` / `taiga_unwatch_userstory` - Watch/Unwatch
- `taiga_upvote_userstory` / `taiga_downvote_userstory` - Votar
- `taiga_get_userstory_voters` - Obtener votantes

#### Faltante según documentación Taiga ❌
| Endpoint | Descripción | Prioridad |
|----------|-------------|-----------|
| `POST /api/v1/userstories/bulk_update_backlog_order` | Reordenar en backlog | Media |
| `POST /api/v1/userstories/bulk_update_kanban_order` | Reordenar en kanban | Media |
| `POST /api/v1/userstories/bulk_update_sprint_order` | Reordenar en sprint | Media |
| `GET /api/v1/userstories/filters_data` | Datos de filtros | Alta |
| `GET /api/v1/userstories/{id}/watchers` | Listar watchers | Baja |

#### Adjuntos (userstory_attachments) ⚠️
| Estado | Endpoint |
|--------|----------|
| ❓ Verificar | `GET /api/v1/userstories/attachments` |
| ❓ Verificar | `POST /api/v1/userstories/attachments` |
| ❓ Verificar | `DELETE /api/v1/userstories/attachments/{id}` |

---

### 4. Issues (`issue_tools.py`)

#### Implementado ✅
- CRUD completo de issues
- Filtrado por proyecto, estado, prioridad
- Asignación de usuarios

#### Faltante según documentación Taiga ❌
| Endpoint | Descripción | Prioridad |
|----------|-------------|-----------|
| `POST /api/v1/issues/bulk_create` | Crear en lote | Media |
| `GET /api/v1/issues/filters_data` | Datos de filtros | Alta |
| `POST /api/v1/issues/{id}/upvote` | Votar positivo | Baja |
| `POST /api/v1/issues/{id}/downvote` | Votar negativo | Baja |
| `GET /api/v1/issues/{id}/voters` | Listar votantes | Baja |
| `POST /api/v1/issues/{id}/watch` | Watch issue | Media |
| `POST /api/v1/issues/{id}/unwatch` | Unwatch issue | Media |
| `GET /api/v1/issues/{id}/watchers` | Listar watchers | Baja |
| Gestión de adjuntos | Attachments CRUD | Media |

---

### 5. Tasks (`task_tools.py`)

#### Implementado ✅
- CRUD completo de tasks
- Asignación a user stories
- Filtrado por proyecto, milestone, user story

#### Faltante según documentación Taiga ❌
| Endpoint | Descripción | Prioridad |
|----------|-------------|-----------|
| `POST /api/v1/tasks/bulk_create` | Crear en lote | Alta |
| `GET /api/v1/tasks/filters_data` | Datos de filtros | Media |
| `POST /api/v1/tasks/{id}/upvote` | Votar positivo | Baja |
| `POST /api/v1/tasks/{id}/downvote` | Votar negativo | Baja |
| `POST /api/v1/tasks/{id}/watch` | Watch task | Baja |
| `POST /api/v1/tasks/{id}/unwatch` | Unwatch task | Baja |
| Gestión de adjuntos | Attachments CRUD | Media |

---

### 6. Epics (`epic_tools.py`)

#### Implementado ✅
- CRUD completo de epics
- Relacionar user stories con epics
- Filtrado por proyecto

#### Faltante según documentación Taiga ❌
| Endpoint | Descripción | Prioridad |
|----------|-------------|-----------|
| `POST /api/v1/epics/bulk_create` | Crear en lote | Media |
| `POST /api/v1/epics/{id}/related_userstories/bulk_create` | Relacionar US en lote | Alta |
| `GET /api/v1/epics/filters_data` | Datos de filtros | Media |
| `POST /api/v1/epics/{id}/upvote` | Votar positivo | Baja |
| `POST /api/v1/epics/{id}/downvote` | Votar negativo | Baja |
| `POST /api/v1/epics/{id}/watch` | Watch epic | Baja |
| `POST /api/v1/epics/{id}/unwatch` | Unwatch epic | Baja |
| Gestión de adjuntos | Attachments CRUD | Media |

---

### 7. Milestones/Sprints (`milestone_tools.py`)

#### Implementado ✅
- CRUD completo de milestones
- Estadísticas de sprint

#### Faltante según documentación Taiga ❌
| Endpoint | Descripción | Prioridad |
|----------|-------------|-----------|
| `POST /api/v1/milestones/{id}/watch` | Watch milestone | Baja |
| `POST /api/v1/milestones/{id}/unwatch` | Unwatch milestone | Baja |
| `GET /api/v1/milestones/{id}/watchers` | Listar watchers | Baja |

---

### 8. Wiki (`wiki_tools.py`)

#### Implementado ✅
- CRUD de páginas wiki

#### Faltante según documentación Taiga ❌
| Endpoint | Descripción | Prioridad |
|----------|-------------|-----------|
| `GET /api/v1/wiki/by_slug` | Obtener por slug | Alta |
| `POST /api/v1/wiki/{id}/watch` | Watch página | Baja |
| `POST /api/v1/wiki/{id}/unwatch` | Unwatch página | Baja |
| Gestión de adjuntos | Attachments CRUD | Media |
| Wiki links | Enlaces entre páginas | Baja |

---

### 9. Webhooks (`webhook_tools.py`)

#### Estado: ⚠️ Parcialmente Implementado

#### Implementado ✅
- Listar webhooks
- Crear webhook
- Obtener webhook
- Actualizar webhook
- Eliminar webhook

#### Faltante ❌
| Funcionalidad | Descripción | Prioridad |
|---------------|-------------|-----------|
| Test webhook | Probar envío de webhook | Alta |
| Webhook logs | Ver historial de envíos | Media |

---

### 10. Memberships (`membership_tools.py`)

#### Implementado ✅
- Listar membresías de proyecto
- Crear membresía (invitar usuario)
- Obtener membresía
- Actualizar membresía (cambiar rol)
- Eliminar membresía

#### Conforme a documentación ✅
Cubre los endpoints principales de `/api/v1/memberships`

---

### 11. Users (`user_tools.py`)

#### Implementado ✅
- Obtener usuario actual
- Listar usuarios de proyecto

#### Faltante ❌
| Endpoint | Descripción | Prioridad |
|----------|-------------|-----------|
| `GET /api/v1/users/{id}` | Obtener usuario por ID | Media |
| `PATCH /api/v1/users/me` | Actualizar perfil | Baja |
| `GET /api/v1/users/{id}/contacts` | Contactos del usuario | Baja |
| `GET /api/v1/users/{id}/liked` | Proyectos que le gustan | Baja |
| `GET /api/v1/users/{id}/watched` | Elementos observados | Baja |

---

### 12. Funcionalidades NO Implementadas ❌

#### Atributos Personalizados (Custom Attributes)
**Prioridad: Alta**

| Endpoint | Descripción |
|----------|-------------|
| `GET/POST /api/v1/userstory-custom-attributes` | Atributos de US |
| `GET/POST /api/v1/issue-custom-attributes` | Atributos de Issues |
| `GET/POST /api/v1/task-custom-attributes` | Atributos de Tasks |
| `GET/POST /api/v1/epic-custom-attributes` | Atributos de Epics |
| Valores de atributos | Establecer valores en entidades |

#### History y Comentarios Avanzados
**Prioridad: Media**

| Endpoint | Descripción |
|----------|-------------|
| `POST /api/v1/history/{entity}/{id}/edit_comment` | Editar comentario |
| `POST /api/v1/history/{entity}/{id}/delete_comment` | Eliminar comentario |
| `POST /api/v1/history/{entity}/{id}/undelete_comment` | Restaurar comentario |
| `GET /api/v1/history/{entity}/{id}/commentVersions` | Versiones de comentario |

---

## Análisis de Uso de FastMCP

### Uso Correcto ✅

#### 1. Decorador `@mcp.tool`
```python
@self.mcp.tool(
    name="taiga_list_projects",
    description="List all Taiga projects accessible to the authenticated user"
)
async def list_projects_tool(...):
```
**Conforme a FastMCP:** El uso del decorador `@mcp.tool` con `name` y `description` es correcto.

#### 2. Manejo de Errores con `ToolError`
```python
from fastmcp.exceptions import ToolError as MCPError

raise MCPError(f"Authentication failed: {str(e)}")
```
**Conforme a FastMCP:** Uso correcto de `ToolError` para errores de herramienta.

#### 3. Funciones Asíncronas
```python
async def list_projects_tool(auth_token: str | None = None) -> list[dict]:
```
**Conforme a FastMCP:** Uso correcto de `async/await` para operaciones I/O.

#### 4. Type Hints
```python
def list_projects(self, **kwargs: Any) -> dict[str, Any]:
```
**Conforme a FastMCP:** Uso correcto de type hints para generación de esquemas.

---

### Mejoras Sugeridas para FastMCP

#### 1. Usar `tags` para Organización
```python
# Actual
@self.mcp.tool(name="taiga_list_projects", description="...")

# Mejorado
@self.mcp.tool(
    name="taiga_list_projects",
    description="...",
    tags={"projects", "read"}
)
```

#### 2. Usar `annotations` para Metadatos
```python
@self.mcp.tool(
    name="taiga_delete_project",
    description="...",
    annotations={
        "destructiveHint": True,
        "title": "Delete Taiga Project"
    }
)
```

#### 3. Usar `Field` para Documentación de Parámetros
```python
from typing import Annotated
from pydantic import Field

async def create_project_tool(
    name: Annotated[str, Field(description="Project name")],
    description: Annotated[str | None, Field(description="Project description")] = None,
    is_private: Annotated[bool, Field(description="Whether project is private")] = True
) -> dict:
```

#### 4. Considerar `exclude_args` para Tokens
```python
@self.mcp.tool(
    name="taiga_list_projects",
    exclude_args=["auth_token"]  # Ocultar token del esquema
)
```

---

## Análisis del Sistema de Caché

### Estado Actual: ⚠️ IMPLEMENTADO PERO NO INTEGRADO

El proyecto tiene un **sistema de caché completo** en la infraestructura, pero **NO se está utilizando** en los tools MCP.

### Archivos Existentes

#### 1. `src/infrastructure/cache.py` - Sistema de Caché en Memoria

```python
class MemoryCache:
    """Caché en memoria con TTL y limpieza automática."""
    default_ttl: int = 3600  # 1 hora
    max_size: int = 1000
```

**Características implementadas:**
- ✅ TTL configurable por entrada
- ✅ Límite máximo de entradas (eviction LRU)
- ✅ Invalidación por patrón (regex)
- ✅ Métricas de hit/miss/evictions
- ✅ Thread-safe con `asyncio.Lock`
- ✅ Limpieza automática de entradas expiradas

#### 2. `src/infrastructure/cached_client.py` - Cliente Cacheado

```python
class CachedTaigaClient:
    """Cliente Taiga con cacheo inteligente."""

    CACHEABLE_ENDPOINTS = {
        "epic_filters": 3600,        # 1 hora
        "issue_filters": 3600,
        "task_filters": 3600,
        "userstory_filters": 3600,
        "project_modules": 1800,     # 30 minutos
        "epic_custom_attributes": 3600,
        "issue_custom_attributes": 3600,
        "task_custom_attributes": 3600,
        "userstory_custom_attributes": 3600,
        "project_stats": 600,        # 10 minutos
        "milestone_stats": 600,
    }
```

**Métodos implementados:**
- ✅ `get_cached_or_fetch()` - Obtener del caché o API
- ✅ `get_epic_filters()` - Filtros cacheados
- ✅ `get_issue_filters()` - Filtros cacheados
- ✅ `invalidate_project_cache()` - Invalidar por proyecto
- ✅ `get_stats()` - Estadísticas del caché

### Problema: No Integrado con Tools

```python
# En src/application/tools/project_tools.py (ACTUAL)
def get_taiga_client(auth_token: str | None = None) -> TaigaAPIClient:
    config = TaigaConfig()
    client = TaigaAPIClient(config)  # ❌ NO usa CachedTaigaClient
    if auth_token:
        client.auth_token = auth_token
    return client
```

**Resultado:** Cada llamada a la API de Taiga va directamente al servidor, sin cachear.

### Solución Propuesta: Integrar CachedTaigaClient

```python
# Propuesta para src/application/tools/project_tools.py
from src.infrastructure.cached_client import CachedTaigaClient
from src.infrastructure.cache import MemoryCache

# Caché global compartido entre todas las herramientas
_global_cache = MemoryCache(default_ttl=3600, max_size=1000)

def get_taiga_client(auth_token: str | None = None) -> CachedTaigaClient:
    config = TaigaConfig()
    base_client = TaigaAPIClient(config)
    if auth_token:
        base_client.auth_token = auth_token
    return CachedTaigaClient(base_client, cache=_global_cache)
```

### Endpoints Candidatos para Cacheo

| Endpoint | TTL Recomendado | Justificación |
|----------|-----------------|---------------|
| `GET /projects` | 5 min | Lista de proyectos cambia poco |
| `GET /projects/{id}` | 5 min | Metadata de proyecto estable |
| `GET /projects/{id}/stats` | 2 min | Stats cambian con frecuencia |
| `GET /*/filters_data` | 30 min | Filtros son muy estables |
| `GET /users/me` | 10 min | Perfil de usuario estable |
| `GET /milestones/{id}/stats` | 2 min | Cambios durante sprint |
| `GET /memberships` | 10 min | Membresías cambian poco |

### Endpoints que NO deben cachearse

| Endpoint | Razón |
|----------|-------|
| `POST /auth` | Autenticación debe ser siempre en tiempo real |
| `GET /userstories` | Datos que cambian frecuentemente |
| `GET /issues` | Datos que cambian frecuentemente |
| `GET /tasks` | Datos que cambian frecuentemente |
| Cualquier `POST/PUT/PATCH/DELETE` | Operaciones de escritura |

### Métricas Disponibles (sin usar)

```python
# Ejemplo de uso de métricas
cache = MemoryCache()
metrics = cache.get_metrics()
print(f"Hit rate: {metrics.hit_rate:.2%}")
print(f"Miss rate: {metrics.miss_rate:.2%}")
print(f"Evictions: {metrics.evictions}")
```

### Plan de Integración

#### Fase 1: Integrar caché básico (Alta prioridad)
1. Modificar `get_taiga_client()` en todos los tools para usar `CachedTaigaClient`
2. Usar caché global compartido
3. Implementar invalidación en operaciones de escritura

#### Fase 2: Exponer herramientas de caché como MCP tools
```python
@self.mcp.tool(name="taiga_cache_stats")
async def get_cache_stats() -> dict:
    """Get cache statistics and hit/miss rates."""
    return await _global_cache.get_stats()

@self.mcp.tool(name="taiga_cache_clear")
async def clear_cache(project_id: int | None = None) -> dict:
    """Clear cache for a project or all cache."""
    if project_id:
        count = await cached_client.invalidate_project_cache(project_id)
    else:
        count = await cached_client.clear_cache()
    return {"cleared_entries": count}
```

#### Fase 3: Implementar invalidación inteligente
```python
# Después de crear/actualizar/eliminar, invalidar caché relacionado
async def create_userstory_tool(...):
    result = await client.create_userstory(...)
    # Invalidar caché del proyecto
    await cached_client.invalidate_project_cache(project_id)
    return result
```

### Impacto Estimado

| Métrica | Sin Caché | Con Caché |
|---------|-----------|-----------|
| Llamadas a API Taiga | 100% | ~40-60% |
| Latencia promedio | ~200ms | ~50ms (cached) |
| Rate limiting issues | Posible | Reducido |
| Carga en servidor Taiga | Alta | Baja |

---

## Mejoras Propuestas

### Alta Prioridad

#### 1. Implementar Custom Attributes
**Impacto:** Alto - Funcionalidad empresarial clave
```python
# Nuevo archivo: src/application/tools/custom_attribute_tools.py
class CustomAttributeTools:
    def register_tools(self):
        @self.mcp.tool(name="taiga_list_userstory_custom_attributes")
        async def list_userstory_custom_attributes(project_id: int, auth_token: str):
            ...

        @self.mcp.tool(name="taiga_create_userstory_custom_attribute")
        async def create_userstory_custom_attribute(
            project_id: int,
            name: str,
            description: str,
            attribute_type: str,  # text, richtext, date, url, dropdown, checkbox, number
            auth_token: str
        ):
            ...
```

#### 2. Implementar Filters Data
**Impacto:** Alto - Mejora UX para búsquedas
```python
@self.mcp.tool(name="taiga_get_userstory_filters")
async def get_userstory_filters(project_id: int, auth_token: str) -> dict:
    """Get available filter options for user stories in a project."""
    # Returns: statuses, assigned_to options, tags, milestones, etc.
```

#### 3. Implementar Bulk Operations Faltantes
**Impacto:** Alto - Eficiencia en operaciones masivas
```python
@self.mcp.tool(name="taiga_bulk_create_tasks")
async def bulk_create_tasks(
    project_id: int,
    user_story_id: int,
    tasks: list[dict],
    auth_token: str
) -> list[dict]:
    ...
```

---

### Media Prioridad

#### 4. Mejorar Gestión de Adjuntos
```python
# Nuevo archivo: src/application/tools/attachment_tools.py
class AttachmentTools:
    def register_tools(self):
        @self.mcp.tool(name="taiga_upload_attachment")
        async def upload_attachment(
            entity_type: str,  # userstory, issue, task, epic, wiki
            entity_id: int,
            file_path: str,
            description: str | None,
            auth_token: str
        ):
            ...
```

#### 5. Implementar Watch/Unwatch Unificado
```python
@self.mcp.tool(name="taiga_watch")
async def watch(
    entity_type: str,  # project, userstory, issue, task, epic, wiki, milestone
    entity_id: int,
    auth_token: str
):
    ...

@self.mcp.tool(name="taiga_unwatch")
async def unwatch(...):
    ...
```

#### 6. Implementar Historial de Comentarios
```python
@self.mcp.tool(name="taiga_edit_comment")
async def edit_comment(
    entity_type: str,
    entity_id: int,
    comment_id: str,
    new_comment: str,
    auth_token: str
):
    ...
```

---

### Baja Prioridad

#### 7. Implementar Like/Unlike
```python
@self.mcp.tool(name="taiga_like_project")
async def like_project(project_id: int, auth_token: str):
    ...
```

#### 8. Implementar Reordenamiento
```python
@self.mcp.tool(name="taiga_reorder_backlog")
async def reorder_backlog(
    project_id: int,
    story_orders: list[tuple[int, int]],  # [(story_id, order), ...]
    auth_token: str
):
    ...
```

---

## Recomendaciones de Arquitectura

### 1. Consolidar Estrategia de Mocking en Tests
- **Problema:** Dos estrategias diferentes (respx vs patch)
- **Solución:** Estandarizar en `patch` para unit tests, `respx` para integration

### 2. Implementar Caché de Tokens
- **Problema:** Cada operación requiere token explícito
- **Solución:** Implementar session management con caché de tokens

### 3. Mejorar Documentación de Tools
- **Problema:** Descripciones básicas
- **Solución:** Usar docstrings detallados con ejemplos

### 4. Implementar Rate Limiting Handler
- **Problema:** No hay manejo de throttling de Taiga
- **Solución:** Implementar retry con backoff exponencial

### 5. Agregar Validación de Entrada más Robusta
- **Problema:** Validación dispersa
- **Solución:** Usar Pydantic models para todas las entradas

---

## Tabla Resumen de Cobertura

| Módulo | Endpoints Taiga | Implementados | Cobertura |
|--------|-----------------|---------------|-----------|
| Auth | 3 | 3 | 100% |
| Projects | 15 | 12 | 80% |
| User Stories | 20 | 16 | 80% |
| Issues | 15 | 8 | 53% |
| Tasks | 12 | 6 | 50% |
| Epics | 15 | 8 | 53% |
| Milestones | 8 | 5 | 63% |
| Wiki | 8 | 4 | 50% |
| Webhooks | 6 | 5 | 83% |
| Memberships | 5 | 5 | 100% |
| Users | 8 | 2 | 25% |
| Custom Attrs | 8 | 0 | 0% |
| History | 10 | 2 | 20% |
| **TOTAL** | **133** | **76** | **57%** |

---

## Plan de Implementación Sugerido

### Sprint 1: Funcionalidades Críticas
1. Custom Attributes (todos los tipos de entidad)
2. Filters Data para búsquedas
3. Bulk create tasks

### Sprint 2: Mejoras de UX
1. Gestión unificada de adjuntos
2. Watch/Unwatch unificado
3. Historial de comentarios

### Sprint 3: Funcionalidades Adicionales
1. Like/Unlike de proyectos
2. Reordenamiento de backlog/kanban
3. Módulos de proyecto

### Sprint 4: Refinamiento
1. Consolidación de tests
2. Mejora de documentación
3. Rate limiting handler

---

**Fecha de análisis:** 2025-12-17
**Versión analizada:** 0.1.1
**Basado en documentación:**
- [Documentacion/taiga.md](../Documentacion/taiga.md)
- [Documentacion/fastmcp.md](../Documentacion/fastmcp.md)
