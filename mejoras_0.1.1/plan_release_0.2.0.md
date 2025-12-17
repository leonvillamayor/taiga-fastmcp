# Plan Detallado - Release 0.2.0

**Fecha:** 2025-12-17
**Objetivo:** Completar cobertura de API Taiga + Optimizar uso de FastMCP

---

## 1. ANÁLISIS DE COBERTURA ACTUAL

### 1.1 Herramientas Implementadas (171 tools)

| Módulo | Herramientas | Estado |
|--------|--------------|--------|
| Auth | 5 | ✅ Completo |
| Cache | 4 | ✅ Completo |
| Projects | 26 | ✅ Completo |
| User Stories | 16 | ⚠️ Faltan bulk order |
| Epics | 28 | ✅ Completo |
| Issues | 30 | ✅ Completo |
| Tasks | 25 | ✅ Completo |
| Milestones | 10 | ✅ Completo |
| Wiki | 14 | ✅ Completo |
| Webhooks | 6 | ✅ Completo |
| Memberships | 5 | ✅ Completo |
| Users | 3 | ✅ Completo |

### 1.2 Funcionalidades Taiga API FALTANTES

#### PRIORIDAD ALTA (Core del producto)

1. **Configuración de Proyecto (Project Settings)**
   - Puntos (Points) - Para estimación de historias
   - Estados (Statuses) - Issue, Task, US, Epic statuses
   - Prioridades (Priorities) - Para issues
   - Severidades (Severities) - Para issues
   - Tipos de Issue (Issue Types)
   - Roles del proyecto

2. **Ordenación en Lote (Bulk Order)**
   - `bulk_update_backlog_order` - Ordenar historias en backlog
   - `bulk_update_kanban_order` - Ordenar en tablero kanban
   - `bulk_update_sprint_order` - Ordenar dentro de sprint

#### PRIORIDAD MEDIA (Útil pero no crítico)

3. **Búsqueda Global**
   - `/api/v1/search` - Búsqueda en todo el proyecto

4. **Timeline/Actividad**
   - `/api/v1/timeline/user/{userId}` - Timeline de usuario
   - `/api/v1/timeline/project/{projectId}` - Timeline de proyecto

5. **Importación de Proyectos**
   - Import desde JSON/CSV (export ya existe)

#### PRIORIDAD BAJA (Nice to have)

6. **Notificaciones**
   - Listar notificaciones del usuario
   - Marcar como leídas

7. **Application Tokens**
   - Gestión de tokens de aplicación

8. **Contact Project Admins**
   - Contactar administradores del proyecto

---

## 2. ANÁLISIS DE USO DE FASTMCP

### 2.1 Uso Actual

| Componente FastMCP | Estado | Notas |
|-------------------|--------|-------|
| `@mcp.tool()` | ✅ Usado | 171 herramientas registradas |
| `@mcp.resource()` | ❌ No usado | Oportunidad de mejora |
| `@mcp.prompt()` | ❌ No usado | Oportunidad de mejora |
| Context | ⚠️ Parcial | Solo para logging básico |
| Middleware | ❌ No usado | Usa infraestructura propia |
| Server Composition | ❌ No usado | Oportunidad modularización |
| Authentication | ⚠️ Custom | Usa autenticación propia vs FastMCP auth |

### 2.2 Mejoras Identificadas en FastMCP

#### A. Implementar Resources (MCP Resources)

Los Resources exponen datos de solo lectura. Casos de uso:

```python
# Configuración del proyecto como recurso
@mcp.resource("taiga://projects/{project_id}/config")
async def get_project_config(project_id: int) -> dict:
    """Configuración actual del proyecto."""
    return await taiga_client.get_project_modules(project_id)

# Estadísticas como recurso
@mcp.resource("taiga://projects/{project_id}/stats")
async def get_project_stats(project_id: int) -> dict:
    """Estadísticas del proyecto."""
    return await taiga_client.get_project_stats(project_id)

# Usuario actual como recurso
@mcp.resource("taiga://users/me")
async def get_current_user() -> dict:
    """Usuario autenticado actual."""
    return await taiga_client.get_current_user()
```

**Beneficio:** Los clientes MCP pueden "suscribirse" a recursos para obtener datos actualizados.

#### B. Implementar Prompts (MCP Prompts)

Los Prompts son plantillas reutilizables:

```python
@mcp.prompt(
    name="create_sprint_planning",
    description="Genera un prompt para planificación de sprint"
)
def sprint_planning_prompt(
    project_name: str,
    sprint_name: str,
    capacity_points: int
) -> str:
    return f"""
    Ayúdame a planificar el sprint "{sprint_name}" para el proyecto "{project_name}".

    Capacidad disponible: {capacity_points} puntos de historia.

    Por favor:
    1. Revisa las historias de usuario del backlog
    2. Sugiere qué historias incluir basándote en prioridad y puntos
    3. Identifica dependencias entre historias
    4. Propón una distribución de trabajo
    """

@mcp.prompt(
    name="analyze_project_health",
    description="Analiza la salud del proyecto"
)
def project_health_prompt(project_id: int) -> str:
    return f"""
    Analiza la salud del proyecto {project_id}:

    1. Revisa las estadísticas del proyecto
    2. Identifica issues críticos sin resolver
    3. Analiza la velocidad del equipo
    4. Sugiere mejoras basadas en los datos
    """
```

#### C. Usar Context para Logging Mejorado

```python
from fastmcp import Context

@mcp.tool(name="taiga_create_project")
async def create_project(name: str, ctx: Context) -> dict:
    await ctx.info(f"Creando proyecto: {name}")
    await ctx.report_progress(progress=0, total=100)

    # Crear proyecto
    result = await taiga_client.create_project(name)

    await ctx.report_progress(progress=100, total=100)
    await ctx.info(f"Proyecto creado con ID: {result['id']}")

    return result
```

#### D. Implementar Middleware FastMCP

```python
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.middleware.timing import TimingMiddleware
from fastmcp.server.middleware.logging import LoggingMiddleware

# Middleware de métricas
class MetricsMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        tool_name = context.message.params.get("name")
        start_time = time.time()

        try:
            result = await call_next(context)
            self.metrics.record_success(tool_name, time.time() - start_time)
            return result
        except Exception as e:
            self.metrics.record_error(tool_name, str(e))
            raise

# Aplicar middlewares
mcp.add_middleware(TimingMiddleware())
mcp.add_middleware(LoggingMiddleware(include_payloads=True))
mcp.add_middleware(MetricsMiddleware())
```

#### E. Server Composition para Modularización

```python
# Crear sub-servidores por dominio
auth_server = FastMCP(name="TaigaAuth")
projects_server = FastMCP(name="TaigaProjects")
agile_server = FastMCP(name="TaigaAgile")  # US, Epics, Tasks

# Servidor principal compuesto
main_mcp = FastMCP(name="TaigaMCP")
main_mcp.mount(auth_server, prefix="auth")
main_mcp.mount(projects_server, prefix="projects")
main_mcp.mount(agile_server, prefix="agile")
```

---

## 3. PLAN DE IMPLEMENTACIÓN

### Fase 1: Consolidación de Tests (1-2 días)

**Objetivo:** Eliminar duplicación de tests

```bash
# 1. Ejecutar cobertura actual
uv run pytest --cov=src --cov-report=html

# 2. Eliminar archivos *_coverage.py
rm tests/unit/tools/test_*_coverage.py

# 3. Verificar cobertura >= 80%
uv run pytest --cov=src --cov-fail-under=80
```

**Entregables:**
- [ ] Eliminar 7 archivos `*_coverage.py`
- [ ] Verificar cobertura se mantiene
- [ ] Documentar cambios

---

### Fase 2: Herramientas de Configuración de Proyecto (3-4 días)

**Objetivo:** Implementar gestión de configuración del proyecto

#### 2.1 Points (Story Points)

```python
# Endpoints Taiga:
# GET    /api/v1/points?project={projectId}
# POST   /api/v1/points
# GET    /api/v1/points/{pointId}
# PUT    /api/v1/points/{pointId}
# PATCH  /api/v1/points/{pointId}
# DELETE /api/v1/points/{pointId}
# POST   /api/v1/points/bulk_update_order

# Herramientas a implementar:
taiga_list_points(project_id: int) -> list[dict]
taiga_create_point(project_id: int, name: str, value: float) -> dict
taiga_get_point(point_id: int) -> dict
taiga_update_point(point_id: int, ...) -> dict
taiga_delete_point(point_id: int) -> dict
taiga_bulk_update_points_order(project_id: int, points: list) -> list
```

#### 2.2 Statuses (Estados)

```python
# Endpoints para cada tipo de status:
# /api/v1/userstory-statuses
# /api/v1/task-statuses
# /api/v1/issue-statuses
# /api/v1/epic-statuses

# Herramientas a implementar (por tipo):
taiga_list_userstory_statuses(project_id: int) -> list[dict]
taiga_create_userstory_status(project_id: int, name: str, ...) -> dict
taiga_update_userstory_status(status_id: int, ...) -> dict
taiga_delete_userstory_status(status_id: int) -> dict
# ... similar para task, issue, epic
```

#### 2.3 Priorities, Severities, Types

```python
# Endpoints:
# /api/v1/priorities
# /api/v1/severities
# /api/v1/issue-types

# Herramientas:
taiga_list_priorities(project_id: int) -> list[dict]
taiga_create_priority(project_id: int, name: str, ...) -> dict
# ... CRUD completo

taiga_list_severities(project_id: int) -> list[dict]
# ... CRUD completo

taiga_list_issue_types(project_id: int) -> list[dict]
# ... CRUD completo
```

#### 2.4 Roles

```python
# Endpoints:
# /api/v1/roles?project={projectId}
# /api/v1/roles

taiga_list_roles(project_id: int) -> list[dict]
taiga_create_role(project_id: int, name: str, permissions: list) -> dict
taiga_update_role(role_id: int, ...) -> dict
taiga_delete_role(role_id: int) -> dict
```

**Archivo:** `src/application/tools/settings_tools.py`

**Tests:** `tests/unit/tools/test_settings_tools.py`

**Entregables:**
- [ ] 30-40 nuevas herramientas de configuración
- [ ] Tests unitarios (cobertura >= 80%)
- [ ] Documentación de herramientas

---

### Fase 3: Bulk Order Operations (1-2 días)

**Objetivo:** Completar operaciones de ordenación en lote

```python
# Endpoints:
# POST /api/v1/userstories/bulk_update_backlog_order
# POST /api/v1/userstories/bulk_update_kanban_order
# POST /api/v1/userstories/bulk_update_sprint_order

# Herramientas:
taiga_bulk_update_backlog_order(
    project_id: int,
    bulk_stories: list[tuple[int, int]]  # [(us_id, order), ...]
) -> list[dict]

taiga_bulk_update_kanban_order(
    project_id: int,
    status_id: int,
    bulk_stories: list[tuple[int, int]]
) -> list[dict]

taiga_bulk_update_sprint_order(
    project_id: int,
    milestone_id: int,
    bulk_stories: list[tuple[int, int]]
) -> list[dict]
```

**Entregables:**
- [ ] 3 nuevas herramientas de ordenación
- [ ] Tests unitarios
- [ ] Documentación

---

### Fase 4: Búsqueda y Timeline (2 días)

**Objetivo:** Implementar búsqueda global y timeline

#### 4.1 Búsqueda Global

```python
# Endpoint:
# GET /api/v1/search?project={projectId}&text={searchText}

taiga_search(
    project_id: int,
    text: str,
    count: int = 20
) -> dict[str, list]
# Retorna: {"userstories": [...], "issues": [...], "tasks": [...], ...}
```

#### 4.2 Timeline

```python
# Endpoints:
# GET /api/v1/timeline/user/{userId}
# GET /api/v1/timeline/project/{projectId}

taiga_get_user_timeline(
    user_id: int,
    page: int = 1
) -> list[dict]

taiga_get_project_timeline(
    project_id: int,
    page: int = 1
) -> list[dict]
```

**Entregables:**
- [ ] 3 nuevas herramientas
- [ ] Tests unitarios
- [ ] Documentación

---

### Fase 5: Mejoras FastMCP (2-3 días)

**Objetivo:** Optimizar uso de FastMCP

#### 5.1 Implementar Resources

```python
# src/application/resources/project_resources.py

from fastmcp import FastMCP

class ProjectResources:
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp

    def register_resources(self):
        @self.mcp.resource("taiga://projects/{project_id}/stats")
        async def project_stats(project_id: int) -> dict:
            """Estadísticas del proyecto en tiempo real."""
            return await self.taiga_client.get_project_stats(project_id)

        @self.mcp.resource("taiga://users/me")
        async def current_user() -> dict:
            """Usuario autenticado actual."""
            return await self.taiga_client.get_current_user()
```

#### 5.2 Implementar Prompts

```python
# src/application/prompts/planning_prompts.py

class PlanningPrompts:
    def register_prompts(self):
        @self.mcp.prompt(name="sprint_planning")
        def sprint_planning(project_id: int, sprint_name: str) -> str:
            return f"Planifica el sprint {sprint_name}..."
```

#### 5.3 Implementar Middleware

```python
# src/infrastructure/middleware.py

from fastmcp.server.middleware import Middleware

class TaigaMetricsMiddleware(Middleware):
    async def on_call_tool(self, context, call_next):
        # Métricas y logging
        pass
```

**Entregables:**
- [ ] 5-10 Resources implementados
- [ ] 3-5 Prompts implementados
- [ ] Middleware de métricas
- [ ] Tests y documentación

---

### Fase 6: Docker y Docker Compose (1 día)

**Objetivo:** Actualizar configuración Docker para release 0.2.0

```yaml
# docker-compose.yml actualizado
version: '3.8'

services:
  taiga-mcp:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - TAIGA_API_URL=${TAIGA_API_URL}
      - TAIGA_USERNAME=${TAIGA_USERNAME}
      - TAIGA_PASSWORD=${TAIGA_PASSWORD}
      - MCP_TRANSPORT=http
      - MCP_HOST=0.0.0.0
      - MCP_PORT=8000
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
```

```dockerfile
# Dockerfile actualizado
FROM python:3.11-slim

WORKDIR /app

# Instalar uv
RUN pip install uv

# Copiar proyecto
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Instalar dependencias
RUN uv sync --frozen

# Ejecutar servidor
CMD ["uv", "run", "python", "-m", "src.server"]
```

**Entregables:**
- [ ] Dockerfile actualizado
- [ ] docker-compose.yml actualizado
- [ ] Documentación de despliegue
- [ ] Health check endpoint

---

### Fase 7: Documentación y Release (1 día)

**Objetivo:** Preparar release 0.2.0

**Entregables:**
- [ ] README.md actualizado
- [ ] CHANGELOG.md con cambios
- [ ] Documentación de nuevas herramientas
- [ ] Guía de migración 0.1.1 → 0.2.0
- [ ] Tag de release v0.2.0

---

## 4. RESUMEN DE NUEVAS HERRAMIENTAS

### Herramientas de Configuración (~35 nuevas)

| Categoría | Cantidad | Herramientas |
|-----------|----------|--------------|
| Points | 6 | list, create, get, update, delete, bulk_order |
| US Statuses | 5 | list, create, get, update, delete |
| Task Statuses | 5 | list, create, get, update, delete |
| Issue Statuses | 5 | list, create, get, update, delete |
| Epic Statuses | 5 | list, create, get, update, delete |
| Priorities | 5 | list, create, get, update, delete |
| Severities | 5 | list, create, get, update, delete |
| Issue Types | 5 | list, create, get, update, delete |
| Roles | 4 | list, create, update, delete |

### Herramientas de Ordenación (3 nuevas)

- `taiga_bulk_update_backlog_order`
- `taiga_bulk_update_kanban_order`
- `taiga_bulk_update_sprint_order`

### Herramientas de Búsqueda/Timeline (3 nuevas)

- `taiga_search`
- `taiga_get_user_timeline`
- `taiga_get_project_timeline`

### Resources FastMCP (~10 nuevos)

- `taiga://projects/{id}/stats`
- `taiga://projects/{id}/config`
- `taiga://users/me`
- `taiga://projects/{id}/timeline`
- etc.

### Prompts FastMCP (~5 nuevos)

- `sprint_planning`
- `analyze_project_health`
- `triage_issues`
- `retrospective_summary`
- `daily_standup`

---

## 5. CRONOGRAMA ESTIMADO

| Fase | Duración | Inicio | Fin |
|------|----------|--------|-----|
| 1. Consolidación Tests | 2 días | Día 1 | Día 2 |
| 2. Config Tools | 4 días | Día 3 | Día 6 |
| 3. Bulk Order | 2 días | Día 7 | Día 8 |
| 4. Search/Timeline | 2 días | Día 9 | Día 10 |
| 5. Mejoras FastMCP | 3 días | Día 11 | Día 13 |
| 6. Docker | 1 día | Día 14 | Día 14 |
| 7. Release | 1 día | Día 15 | Día 15 |

**Total estimado:** ~15 días de desarrollo

---

## 6. CRITERIOS DE ACEPTACIÓN RELEASE 0.2.0

- [ ] 200+ herramientas MCP implementadas
- [ ] Cobertura de tests >= 80%
- [ ] Todos los tests pasan
- [ ] Docker funcionando
- [ ] Documentación completa
- [ ] Sin duplicación de tests significativa
- [ ] Resources y Prompts implementados
- [ ] Middleware de métricas funcionando

---

## 7. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| API Taiga cambia | Baja | Alto | Versionado de API, tests de integración |
| Cobertura baja al eliminar tests | Media | Medio | Verificar antes de eliminar |
| Complejidad de FastMCP | Media | Medio | Implementar incrementalmente |
| Tiempo insuficiente | Media | Alto | Priorizar fases 1-4, diferir 5-7 |

---

**Documento preparado por:** Claude Code Analysis
**Fecha:** 2025-12-17
