# Plan Detallado de Implementación de Mejoras - Servidor MCP para Taiga

**Fecha**: 2025-12-08
**Proyecto**: Taiga MCP Claude Code
**Versión**: 1.0
**Documento Base**: [mejoras_taiga.md](mejoras_taiga.md)

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Metodología y Organización](#2-metodología-y-organización)
3. [Fase 1: Arquitectura Unificada DDD](#fase-1-arquitectura-unificada-ddd)
4. [Fase 2: Normalización de Interfaces](#fase-2-normalización-de-interfaces)
5. [Fase 3: Optimizaciones](#fase-3-optimizaciones)
6. [Fase 4: Testing Exhaustivo](#fase-4-testing-exhaustivo)
7. [Fase 5: Documentación](#fase-5-documentación)
8. [Matriz de Trazabilidad](#8-matriz-de-trazabilidad)
9. [Cronograma y Recursos](#9-cronograma-y-recursos)
10. [Criterios de Aceptación](#10-criterios-de-aceptación)

---

## 1. Resumen Ejecutivo

### 1.1 Objetivo del Plan

Este plan detalla **TODAS las tareas necesarias** para implementar las mejoras identificadas en [mejoras_taiga.md](mejoras_taiga.md), transformando el servidor MCP para Taiga en una implementación profesional, mantenible y escalable.

### 1.2 Alcance

El plan cubre:
- ✅ Unificación de arquitectura dual (legacy + nueva) → DDD completo
- ✅ Normalización de 123+ herramientas MCP
- ✅ Implementación de inyección de dependencias
- ✅ Suite completa de testing (unit, integration, e2e)
- ✅ Documentación exhaustiva

### 1.3 Fases del Plan

| Fase | Nombre | Duración | Tareas | Tests |
|------|--------|----------|--------|-------|
| **1** | Arquitectura Unificada DDD | 3 semanas | 28 tareas | 35 tests |
| **2** | Normalización de Interfaces | 2 semanas | 18 tareas | 40 tests |
| **3** | Optimizaciones | 2 semanas | 15 tareas | 20 tests |
| **4** | Testing Exhaustivo | 2 semanas | 12 tareas | 150+ tests |
| **5** | Documentación | 1 semana | 10 tareas | 5 tests |
| **TOTAL** | | **10 semanas** | **83 tareas** | **250+ tests** |

### 1.4 Entregables Principales

Por fase:

**Fase 1**:
- Capa Domain completa (entities, value objects, repositories interfaces)
- Capa Application completa (use cases)
- Capa Infrastructure completa (repositories implementations)
- Sistema de DI funcional

**Fase 2**:
- 123+ herramientas con nombres normalizados (prefijo `taiga_`)
- Tipos de retorno homogéneos (Dict/List/Pydantic)
- Parámetros consistentes (sin aliases)

**Fase 3**:
- Caché de metadatos de proyecto
- Paginación automática
- Rate limiting inteligente
- Pool de conexiones HTTP

**Fase 4**:
- Cobertura >= 90% en todas las capas
- Tests unitarios, integración y e2e
- Suite de validación continua

**Fase 5**:
- README.md completo
- guia_uso.md exhaustiva
- Diagramas de arquitectura
- ADR (Architecture Decision Records)

---

## 2. Metodología y Organización

### 2.1 Principios Guía

1. **Test-Driven Development (TDD)**:
   - Escribir tests ANTES de implementar
   - Cada tarea tiene tests asociados

2. **Desarrollo Incremental**:
   - Cada fase es completamente funcional
   - No romper funcionalidad existente

3. **Validación Continua**:
   - Tests automáticos después de cada tarea
   - Cobertura mínima 80% desde Fase 1

4. **Documentación Activa**:
   - Documentar decisiones mientras se implementan
   - ADR para decisiones arquitectónicas importantes

### 2.2 Estructura de Tareas

Cada tarea sigue este formato:

```markdown
### Tarea X.Y: [Nombre]

**Problema**: Descripción del problema que resuelve
**Objetivo**: Qué se logrará al completar la tarea
**Prioridad**: CRÍTICA | ALTA | MEDIA | BAJA
**Dependencias**: Tareas previas requeridas
**Estimación**: Horas de trabajo

#### Pasos de Implementación

1. Paso detallado 1
2. Paso detallado 2
...

#### Tests Asociados

- [ ] Test 1: Descripción
- [ ] Test 2: Descripción
...

#### Criterios de Aceptación

- [ ] Criterio 1
- [ ] Criterio 2
...

#### Archivos Afectados

- `ruta/archivo1.py` - Descripción del cambio
- `ruta/archivo2.py` - Descripción del cambio
```

### 2.3 Convenciones de Código

Durante todas las fases se respetarán:

- **Estilo**: PEP 8
- **Type Hints**: Obligatorios en funciones públicas
- **Docstrings**: Formato Google
- **Imports**: isort + black
- **Líneas**: Máximo 100 caracteres

### 2.4 Herramientas de Desarrollo

- **Gestor de Paquetes**: `uv` (ya en uso)
- **Testing**: `pytest`, `pytest-cov`, `pytest-mock`, `pytest-asyncio`
- **Linting**: `ruff` (reemplaza flake8, isort, black)
- **Type Checking**: `mypy`
- **Pre-commit**: hooks automáticos

---

## Fase 1: Arquitectura Unificada DDD

**Duración**: 3 semanas (120 horas)
**Objetivo**: Unificar arquitectura dual en implementación DDD completa
**Impacto**: CRÍTICO - Base para todas las demás fases

### Resumen de la Fase

| Aspecto | Estado Actual | Estado Objetivo |
|---------|---------------|----------------|
| Arquitectura | Dual (legacy + nueva) | DDD completo |
| Separación de capas | Parcial | Estricta |
| Inyección de dependencias | Manual | Automática con `dependency-injector` |
| Entidades de dominio | Solo Epic | Todas (Project, UserStory, Task, Issue, etc.) |
| Use Cases | Solo Epic | Todos los módulos |

### Tareas de la Fase 1

---

### Tarea 1.1: Configurar Herramientas de Desarrollo

**Problema**: No hay configuración de linting, formatting ni type checking
**Objetivo**: Establecer estándares de código automáticos
**Prioridad**: ALTA
**Dependencias**: Ninguna
**Estimación**: 4 horas

#### Pasos de Implementación

1. Instalar herramientas de desarrollo:
   ```bash
   uv add --dev ruff mypy pytest pytest-cov pytest-mock pytest-asyncio
   uv add --dev pre-commit
   ```

2. Crear `pyproject.toml` con configuración de ruff:
   ```toml
   [tool.ruff]
   line-length = 100
   target-version = "py311"
   select = [
       "E",   # pycodestyle errors
       "W",   # pycodestyle warnings
       "F",   # pyflakes
       "I",   # isort
       "B",   # flake8-bugbear
       "C4",  # flake8-comprehensions
       "UP",  # pyupgrade
   ]

   [tool.ruff.per-file-ignores]
   "__init__.py" = ["F401"]  # Permitir imports no usados en __init__

   [tool.mypy]
   python_version = "3.11"
   warn_return_any = true
   warn_unused_configs = true
   disallow_untyped_defs = true
   ```

3. Crear `.pre-commit-config.yaml`:
   ```yaml
   repos:
     - repo: https://github.com/astral-sh/ruff-pre-commit
       rev: v0.1.9
       hooks:
         - id: ruff
           args: [--fix, --exit-non-zero-on-fix]
         - id: ruff-format

     - repo: https://github.com/pre-commit/mirrors-mypy
       rev: v1.8.0
       hooks:
         - id: mypy
           additional_dependencies: [types-all]
   ```

4. Instalar pre-commit hooks:
   ```bash
   uv run pre-commit install
   ```

5. Ejecutar sobre código existente:
   ```bash
   uv run ruff check src/ tests/ --fix
   uv run ruff format src/ tests/
   uv run mypy src/
   ```

#### Tests Asociados

- [ ] Test 1.1.1: Verificar que ruff pasa en todo el código
- [ ] Test 1.1.2: Verificar que mypy no reporta errores críticos
- [ ] Test 1.1.3: Verificar que pre-commit hooks funcionan correctamente

#### Criterios de Aceptación

- [ ] Ruff configurado y pasando en todo el código
- [ ] Mypy configurado (puede tener warnings iniciales, pero sin errores)
- [ ] Pre-commit hooks instalados y funcionando
- [ ] Documentación en README sobre cómo usar las herramientas

#### Archivos Afectados

- `pyproject.toml` - Configuración de herramientas
- `.pre-commit-config.yaml` - Configuración de pre-commit
- `README.md` - Documentar comandos de desarrollo

---

### Tarea 1.2: Instalar y Configurar Dependency Injector

**Problema**: Inyección de dependencias manual en `server.py` (70 líneas repetitivas)
**Objetivo**: Sistema de DI automático con `dependency-injector`
**Prioridad**: CRÍTICA
**Dependencias**: Tarea 1.1
**Estimación**: 6 horas

#### Pasos de Implementación

1. Instalar librería:
   ```bash
   uv add dependency-injector
   ```

2. Crear `src/infrastructure/container.py`:
   ```python
   """Container de inyección de dependencias."""
   from dependency_injector import containers, providers
   from fastmcp import FastMCP

   from src.config import TaigaConfig
   from src.taiga_client import TaigaAPIClient

   # Importar todos los repositorios
   from src.infrastructure.repositories.epic_repository_impl import EpicRepositoryImpl
   from src.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl
   # ... otros repositorios

   # Importar todos los use cases
   from src.application.use_cases.epic_use_cases import EpicUseCases
   from src.application.use_cases.project_use_cases import ProjectUseCases
   # ... otros use cases

   # Importar todos los tools
   from src.application.tools.auth_tools import AuthTools
   from src.application.tools.epic_tools import EpicTools
   from src.application.tools.project_tools import ProjectTools
   # ... otros tools


   class ApplicationContainer(containers.DeclarativeContainer):
       """Container principal de la aplicación."""

       # Configuración
       config = providers.Singleton(TaigaConfig)

       # FastMCP instance
       mcp = providers.Singleton(
           FastMCP,
           name="taiga-mcp-server"
       )

       # Cliente Taiga (Factory porque cada request puede necesitar su instancia)
       taiga_client = providers.Factory(
           TaigaAPIClient,
           config=config
       )

       # Repositorios (Singleton porque no tienen estado)
       epic_repository = providers.Singleton(
           EpicRepositoryImpl,
           client=taiga_client
       )

       project_repository = providers.Singleton(
           ProjectRepositoryImpl,
           client=taiga_client
       )

       # ... otros repositorios

       # Use Cases (Singleton)
       epic_use_cases = providers.Singleton(
           EpicUseCases,
           repository=epic_repository
       )

       project_use_cases = providers.Singleton(
           ProjectUseCases,
           repository=project_repository
       )

       # ... otros use cases

       # Tools (Singleton)
       auth_tools = providers.Singleton(
           AuthTools,
           mcp=mcp,
           client=taiga_client
       )

       epic_tools = providers.Singleton(
           EpicTools,
           mcp=mcp,
           use_cases=epic_use_cases
       )

       project_tools = providers.Singleton(
           ProjectTools,
           mcp=mcp,
           use_cases=project_use_cases
       )

       # ... otros tools
   ```

3. Modificar `src/server.py` para usar el container:
   ```python
   """Punto de entrada del servidor MCP."""
   from src.infrastructure.container import ApplicationContainer

   # Crear container
   container = ApplicationContainer()

   # Obtener instancia de FastMCP
   mcp = container.mcp()

   # Registrar todos los tools (inyección automática)
   container.auth_tools().register_tools()
   container.epic_tools().register_tools()
   container.project_tools().register_tools()
   # ... otros tools

   if __name__ == "__main__":
       mcp.run()
   ```

4. Reducir `server.py` de 70 líneas a ~20 líneas

#### Tests Asociados

- [ ] Test 1.2.1: Verificar que container se inicializa correctamente
- [ ] Test 1.2.2: Verificar que todas las dependencias se inyectan
- [ ] Test 1.2.3: Verificar que FastMCP se crea con configuración correcta
- [ ] Test 1.2.4: Verificar que tools se registran automáticamente
- [ ] Test 1.2.5: Test de integración: servidor inicia sin errores

#### Criterios de Aceptación

- [ ] Container configurado con todas las dependencias
- [ ] `server.py` reducido a <= 25 líneas
- [ ] Todos los tools se registran automáticamente
- [ ] Tests de integración pasan
- [ ] Documentar en README cómo extender el container

#### Archivos Afectados

- `src/infrastructure/container.py` - **NUEVO** - Container de DI
- `src/server.py` - Simplificar usando container
- `tests/integration/test_server_startup.py` - **NUEVO** - Tests de integración
- `README.md` - Documentar sistema de DI

---

### Tarea 1.3: Diseñar Entidades de Dominio (Domain Layer)

**Problema**: Solo existe entidad `Epic`, faltan todas las demás
**Objetivo**: Crear todas las entidades de dominio con validaciones
**Prioridad**: CRÍTICA
**Dependencias**: Tarea 1.1
**Estimación**: 12 horas

#### Pasos de Implementación

1. Crear estructura de directorio:
   ```
   src/domain/
   ├── entities/
   │   ├── __init__.py
   │   ├── base.py           # Entidad base
   │   ├── project.py
   │   ├── epic.py           # Ya existe, refactorizar
   │   ├── user_story.py
   │   ├── task.py
   │   ├── issue.py
   │   ├── milestone.py
   │   ├── member.py
   │   └── wiki_page.py
   ├── value_objects/
   │   ├── __init__.py
   │   ├── email.py
   │   ├── auth_token.py
   │   ├── project_slug.py
   │   └── status.py
   └── exceptions.py         # Ya existe
   ```

2. Crear entidad base `src/domain/entities/base.py`:
   ```python
   """Entidad base del dominio."""
   from typing import Optional
   from pydantic import BaseModel, Field, ConfigDict


   class BaseEntity(BaseModel):
       """Clase base para todas las entidades del dominio."""

       model_config = ConfigDict(
           frozen=False,  # Entidades son mutables
           validate_assignment=True,  # Validar al asignar valores
           arbitrary_types_allowed=True
       )

       id: Optional[int] = Field(None, description="ID único de la entidad")
       version: Optional[int] = Field(None, description="Versión para control de concurrencia")

       def __eq__(self, other: object) -> bool:
           """Dos entidades son iguales si tienen el mismo ID."""
           if not isinstance(other, BaseEntity):
               return False
           return self.id is not None and self.id == other.id

       def __hash__(self) -> int:
           """Hash basado en ID."""
           return hash(self.id) if self.id else super().__hash__()
   ```

3. Crear entidad `Project` en `src/domain/entities/project.py`:
   ```python
   """Entidad de proyecto."""
   from datetime import datetime
   from typing import Optional, List
   from pydantic import Field, field_validator

   from src.domain.entities.base import BaseEntity
   from src.domain.value_objects.project_slug import ProjectSlug


   class Project(BaseEntity):
       """
       Entidad de proyecto en Taiga.

       Representa un proyecto con sus configuraciones y estado.
       """

       name: str = Field(..., min_length=1, max_length=255, description="Nombre del proyecto")
       slug: Optional[ProjectSlug] = Field(None, description="Slug único del proyecto")
       description: str = Field("", description="Descripción del proyecto")

       # Configuración
       is_private: bool = Field(True, description="¿Es proyecto privado?")
       is_backlog_activated: bool = Field(True, description="¿Módulo backlog activado?")
       is_kanban_activated: bool = Field(True, description="¿Módulo kanban activado?")
       is_wiki_activated: bool = Field(True, description="¿Módulo wiki activado?")
       is_issues_activated: bool = Field(True, description="¿Módulo issues activado?")

       # Metadatos
       owner_id: Optional[int] = Field(None, description="ID del propietario")
       created_date: Optional[datetime] = Field(None, description="Fecha de creación")
       modified_date: Optional[datetime] = Field(None, description="Última modificación")

       # Estadísticas
       total_story_points: Optional[float] = Field(None, ge=0, description="Total de story points")
       total_milestones: Optional[int] = Field(None, ge=0, description="Total de milestones")

       # Tags
       tags: List[str] = Field(default_factory=list, description="Tags del proyecto")

       @field_validator('name')
       @classmethod
       def validate_name(cls, v: str) -> str:
           """Valida que el nombre no esté vacío ni sea solo espacios."""
           if not v.strip():
               raise ValueError("El nombre del proyecto no puede estar vacío")
           return v.strip()

       @field_validator('tags')
       @classmethod
       def validate_tags(cls, v: List[str]) -> List[str]:
           """Normaliza tags (minúsculas, sin duplicados)."""
           return list(set(tag.lower().strip() for tag in v if tag.strip()))

       def activate_module(self, module: str) -> None:
           """Activa un módulo del proyecto."""
           module_map = {
               'backlog': 'is_backlog_activated',
               'kanban': 'is_kanban_activated',
               'wiki': 'is_wiki_activated',
               'issues': 'is_issues_activated'
           }
           if module not in module_map:
               raise ValueError(f"Módulo desconocido: {module}")
           setattr(self, module_map[module], True)

       def deactivate_module(self, module: str) -> None:
           """Desactiva un módulo del proyecto."""
           module_map = {
               'backlog': 'is_backlog_activated',
               'kanban': 'is_kanban_activated',
               'wiki': 'is_wiki_activated',
               'issues': 'is_issues_activated'
           }
           if module not in module_map:
               raise ValueError(f"Módulo desconocido: {module}")
           setattr(self, module_map[module], False)
   ```

4. Crear value object `ProjectSlug` en `src/domain/value_objects/project_slug.py`:
   ```python
   """Value object para slug de proyecto."""
   import re
   from pydantic import BaseModel, Field, field_validator, ConfigDict


   class ProjectSlug(BaseModel):
       """
       Slug de proyecto (identificador URL-friendly).

       Reglas:
       - Solo minúsculas, números y guiones
       - No puede empezar/terminar con guión
       - Mínimo 3 caracteres, máximo 50
       """

       model_config = ConfigDict(frozen=True)  # Inmutable

       value: str = Field(..., min_length=3, max_length=50)

       @field_validator('value')
       @classmethod
       def validate_slug(cls, v: str) -> str:
           """Valida formato de slug."""
           if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', v):
               raise ValueError(
                   "Slug debe contener solo minúsculas, números y guiones (no al inicio/fin)"
               )
           return v

       def __str__(self) -> str:
           return self.value

       def __repr__(self) -> str:
           return f"ProjectSlug('{self.value}')"
   ```

5. Repetir patrón similar para:
   - `UserStory` (src/domain/entities/user_story.py)
   - `Task` (src/domain/entities/task.py)
   - `Issue` (src/domain/entities/issue.py)
   - `Milestone` (src/domain/entities/milestone.py)
   - `Member` (src/domain/entities/member.py)
   - `WikiPage` (src/domain/entities/wiki_page.py)

6. Refactorizar `Epic` existente para heredar de `BaseEntity`

#### Tests Asociados

- [ ] Test 1.3.1: Test unitario para `BaseEntity` (equality, hash)
- [ ] Test 1.3.2: Test unitario para `Project` (validaciones)
- [ ] Test 1.3.3: Test unitario para `ProjectSlug` (validaciones)
- [ ] Test 1.3.4: Test que nombre vacío lanza ValueError
- [ ] Test 1.3.5: Test que slug inválido lanza ValueError
- [ ] Test 1.3.6: Test que tags se normalizan correctamente
- [ ] Test 1.3.7: Test activate_module/deactivate_module
- [ ] Test 1.3.8: Tests para cada entidad (UserStory, Task, etc.)
- [ ] Test 1.3.9: Tests de inmutabilidad de value objects

#### Criterios de Aceptación

- [ ] Todas las entidades implementadas con validaciones
- [ ] Todos los value objects implementados como inmutables
- [ ] Cobertura de tests >= 90% en capa Domain
- [ ] Docstrings completos en todas las clases
- [ ] Type hints en todos los métodos

#### Archivos Afectados

- `src/domain/entities/base.py` - **NUEVO**
- `src/domain/entities/project.py` - **NUEVO**
- `src/domain/entities/epic.py` - REFACTORIZAR
- `src/domain/entities/user_story.py` - **NUEVO**
- `src/domain/entities/task.py` - **NUEVO**
- `src/domain/entities/issue.py` - **NUEVO**
- `src/domain/entities/milestone.py` - **NUEVO**
- `src/domain/entities/member.py` - **NUEVO**
- `src/domain/entities/wiki_page.py` - **NUEVO**
- `src/domain/value_objects/project_slug.py` - **NUEVO**
- `src/domain/value_objects/email.py` - **NUEVO**
- `src/domain/value_objects/auth_token.py` - **NUEVO**
- `tests/unit/domain/entities/test_base.py` - **NUEVO**
- `tests/unit/domain/entities/test_project.py` - **NUEVO**
- `tests/unit/domain/value_objects/test_project_slug.py` - **NUEVO**

---

### Tarea 1.4: Definir Interfaces de Repositorios (Domain Layer)

**Problema**: Repositorios mezclados con implementación
**Objetivo**: Interfaces puras en Domain, implementaciones en Infrastructure
**Prioridad**: CRÍTICA
**Dependencias**: Tarea 1.3
**Estimación**: 8 horas

#### Pasos de Implementación

1. Crear estructura:
   ```
   src/domain/repositories/
   ├── __init__.py
   ├── base_repository.py
   ├── project_repository.py
   ├── epic_repository.py      # Refactorizar existente
   ├── user_story_repository.py
   ├── task_repository.py
   ├── issue_repository.py
   ├── milestone_repository.py
   ├── member_repository.py
   └── wiki_repository.py
   ```

2. Crear repositorio base `src/domain/repositories/base_repository.py`:
   ```python
   """Repositorio base con operaciones CRUD."""
   from abc import ABC, abstractmethod
   from typing import Generic, TypeVar, List, Optional, Dict, Any

   from src.domain.entities.base import BaseEntity

   T = TypeVar('T', bound=BaseEntity)


   class BaseRepository(ABC, Generic[T]):
       """
       Repositorio base con operaciones CRUD estándar.

       Todas las operaciones son asíncronas para soportar I/O no bloqueante.
       """

       @abstractmethod
       async def get_by_id(self, entity_id: int) -> Optional[T]:
           """
           Obtiene una entidad por su ID.

           Args:
               entity_id: ID de la entidad

           Returns:
               Entidad si existe, None si no existe
           """
           pass

       @abstractmethod
       async def list(
           self,
           filters: Optional[Dict[str, Any]] = None,
           limit: Optional[int] = None,
           offset: Optional[int] = None
       ) -> List[T]:
           """
           Lista entidades con filtros opcionales.

           Args:
               filters: Diccionario de filtros
               limit: Máximo número de resultados
               offset: Número de resultados a saltar (paginación)

           Returns:
               Lista de entidades que cumplen los filtros
           """
           pass

       @abstractmethod
       async def create(self, entity: T) -> T:
           """
           Crea una nueva entidad.

           Args:
               entity: Entidad a crear (sin ID)

           Returns:
               Entidad creada con ID asignado
           """
           pass

       @abstractmethod
       async def update(self, entity: T) -> T:
           """
           Actualiza una entidad existente.

           Args:
               entity: Entidad con cambios (debe tener ID)

           Returns:
               Entidad actualizada

           Raises:
               ResourceNotFoundError: Si la entidad no existe
               ConcurrencyError: Si la versión ha cambiado (conflict)
           """
           pass

       @abstractmethod
       async def delete(self, entity_id: int) -> bool:
           """
           Elimina una entidad.

           Args:
               entity_id: ID de la entidad a eliminar

           Returns:
               True si se eliminó, False si no existía
           """
           pass

       @abstractmethod
       async def exists(self, entity_id: int) -> bool:
           """
           Verifica si una entidad existe.

           Args:
               entity_id: ID de la entidad

           Returns:
               True si existe, False si no
           """
           pass
   ```

3. Crear repositorio de proyecto `src/domain/repositories/project_repository.py`:
   ```python
   """Interfaz de repositorio para proyectos."""
   from abc import abstractmethod
   from typing import List, Optional

   from src.domain.entities.project import Project
   from src.domain.repositories.base_repository import BaseRepository


   class ProjectRepository(BaseRepository[Project]):
       """
       Repositorio de proyectos con operaciones específicas.
       """

       @abstractmethod
       async def get_by_slug(self, slug: str) -> Optional[Project]:
           """
           Obtiene un proyecto por su slug.

           Args:
               slug: Slug del proyecto

           Returns:
               Proyecto si existe, None si no
           """
           pass

       @abstractmethod
       async def list_by_member(self, member_id: int) -> List[Project]:
           """
           Lista proyectos de un miembro específico.

           Args:
               member_id: ID del miembro

           Returns:
               Lista de proyectos del miembro
           """
           pass

       @abstractmethod
       async def list_private(self) -> List[Project]:
           """
           Lista solo proyectos privados.

           Returns:
               Lista de proyectos privados
           """
           pass

       @abstractmethod
       async def list_public(self) -> List[Project]:
           """
           Lista solo proyectos públicos.

           Returns:
               Lista de proyectos públicos
           """
           pass

       @abstractmethod
       async def get_stats(self, project_id: int) -> dict:
           """
           Obtiene estadísticas del proyecto.

           Args:
               project_id: ID del proyecto

           Returns:
               Diccionario con estadísticas
           """
           pass
   ```

4. Repetir patrón para:
   - `EpicRepository` (refactorizar existente)
   - `UserStoryRepository`
   - `TaskRepository`
   - `IssueRepository`
   - `MilestoneRepository`
   - `MemberRepository`
   - `WikiRepository`

#### Tests Asociados

- [ ] Test 1.4.1: Verificar que todas las interfaces son abstractas
- [ ] Test 1.4.2: Verificar que BaseRepository define métodos CRUD
- [ ] Test 1.4.3: Verificar que cada repositorio hereda de BaseRepository
- [ ] Test 1.4.4: Verificar type hints correctos en todas las interfaces

#### Criterios de Aceptación

- [ ] Todas las interfaces de repositorio definidas
- [ ] Sin implementación concreta en Domain layer
- [ ] Todas las operaciones documentadas con docstrings
- [ ] Type hints completos usando Generic[T]

#### Archivos Afectados

- `src/domain/repositories/base_repository.py` - **NUEVO**
- `src/domain/repositories/project_repository.py` - **NUEVO**
- `src/domain/repositories/epic_repository.py` - REFACTORIZAR
- `src/domain/repositories/user_story_repository.py` - **NUEVO**
- `src/domain/repositories/task_repository.py` - **NUEVO**
- `src/domain/repositories/issue_repository.py` - **NUEVO**
- `src/domain/repositories/milestone_repository.py` - **NUEVO**
- `src/domain/repositories/member_repository.py` - **NUEVO**
- `src/domain/repositories/wiki_repository.py` - **NUEVO**

---

### Tarea 1.5: Implementar Repositorios Concretos (Infrastructure Layer)

**Problema**: Implementaciones mezcladas con interfaces
**Objetivo**: Repositorios concretos en Infrastructure usando TaigaAPIClient
**Prioridad**: CRÍTICA
**Dependencias**: Tarea 1.4
**Estimación**: 16 horas

#### Pasos de Implementación

1. Crear estructura:
   ```
   src/infrastructure/repositories/
   ├── __init__.py
   ├── base_repository_impl.py
   ├── project_repository_impl.py
   ├── epic_repository_impl.py      # Refactorizar existente
   ├── user_story_repository_impl.py
   ├── task_repository_impl.py
   ├── issue_repository_impl.py
   ├── milestone_repository_impl.py
   ├── member_repository_impl.py
   └── wiki_repository_impl.py
   ```

2. Crear implementación base `src/infrastructure/repositories/base_repository_impl.py`:
   ```python
   """Implementación base de repositorio."""
   from typing import Generic, TypeVar, List, Optional, Dict, Any, Type

   from src.domain.entities.base import BaseEntity
   from src.domain.repositories.base_repository import BaseRepository
   from src.taiga_client import TaigaAPIClient
   from src.domain.exceptions import ResourceNotFoundError, ConcurrencyError

   T = TypeVar('T', bound=BaseEntity)


   class BaseRepositoryImpl(BaseRepository[T], Generic[T]):
       """
       Implementación base de repositorio usando TaigaAPIClient.

       Proporciona funcionalidad CRUD genérica que las subclases
       pueden personalizar.
       """

       def __init__(
           self,
           client: TaigaAPIClient,
           entity_class: Type[T],
           endpoint: str
       ):
           """
           Inicializa el repositorio.

           Args:
               client: Cliente de la API de Taiga
               entity_class: Clase de la entidad (ej: Project)
               endpoint: Endpoint base de la API (ej: "/projects")
           """
           self.client = client
           self.entity_class = entity_class
           self.endpoint = endpoint

       async def get_by_id(self, entity_id: int) -> Optional[T]:
           """Obtiene entidad por ID."""
           try:
               async with self.client as client:
                   data = await client.get(f"{self.endpoint}/{entity_id}")
                   return self._to_entity(data)
           except ResourceNotFoundError:
               return None

       async def list(
           self,
           filters: Optional[Dict[str, Any]] = None,
           limit: Optional[int] = None,
           offset: Optional[int] = None
       ) -> List[T]:
           """Lista entidades con filtros."""
           async with self.client as client:
               params = filters or {}
               if limit is not None:
                   params['limit'] = limit
               if offset is not None:
                   params['offset'] = offset

               data_list = await client.get(self.endpoint, params=params)
               return [self._to_entity(data) for data in data_list]

       async def create(self, entity: T) -> T:
           """Crea nueva entidad."""
           async with self.client as client:
               # Convertir entidad a dict (excluir None y campos no editables)
               data = entity.model_dump(
                   exclude_none=True,
                   exclude={'id', 'version', 'created_date', 'modified_date'}
               )
               result = await client.post(self.endpoint, data=data)
               return self._to_entity(result)

       async def update(self, entity: T) -> T:
           """Actualiza entidad existente."""
           if entity.id is None:
               raise ValueError("Entity must have an ID to be updated")

           async with self.client as client:
               data = entity.model_dump(
                   exclude_none=True,
                   exclude={'id', 'created_date', 'modified_date'}
               )

               # Incluir versión para control de concurrencia
               if entity.version is not None:
                   data['version'] = entity.version

               try:
                   result = await client.patch(
                       f"{self.endpoint}/{entity.id}",
                       data=data
                   )
                   return self._to_entity(result)
               except Exception as e:
                   if "conflict" in str(e).lower():
                       raise ConcurrencyError(
                           f"Entity {entity.id} has been modified by another user"
                       )
                   raise

       async def delete(self, entity_id: int) -> bool:
           """Elimina entidad."""
           try:
               async with self.client as client:
                   await client.delete(f"{self.endpoint}/{entity_id}")
                   return True
           except ResourceNotFoundError:
               return False

       async def exists(self, entity_id: int) -> bool:
           """Verifica si entidad existe."""
           return await self.get_by_id(entity_id) is not None

       def _to_entity(self, data: Dict[str, Any]) -> T:
           """
           Convierte dict de API a entidad de dominio.

           Las subclases pueden sobrescribir para mapeo personalizado.
           """
           return self.entity_class(**data)
   ```

3. Crear implementación de proyecto `src/infrastructure/repositories/project_repository_impl.py`:
   ```python
   """Implementación de repositorio de proyectos."""
   from typing import List, Optional

   from src.domain.entities.project import Project
   from src.domain.repositories.project_repository import ProjectRepository
   from src.infrastructure.repositories.base_repository_impl import BaseRepositoryImpl
   from src.taiga_client import TaigaAPIClient


   class ProjectRepositoryImpl(BaseRepositoryImpl[Project], ProjectRepository):
       """Implementación concreta del repositorio de proyectos."""

       def __init__(self, client: TaigaAPIClient):
           super().__init__(
               client=client,
               entity_class=Project,
               endpoint="/projects"
           )

       async def get_by_slug(self, slug: str) -> Optional[Project]:
           """Obtiene proyecto por slug."""
           async with self.client as client:
               data = await client.get(f"{self.endpoint}/by_slug?slug={slug}")
               return self._to_entity(data) if data else None

       async def list_by_member(self, member_id: int) -> List[Project]:
           """Lista proyectos de un miembro."""
           return await self.list(filters={'member': member_id})

       async def list_private(self) -> List[Project]:
           """Lista proyectos privados."""
           return await self.list(filters={'is_private': True})

       async def list_public(self) -> List[Project]:
           """Lista proyectos públicos."""
           return await self.list(filters={'is_private': False})

       async def get_stats(self, project_id: int) -> dict:
           """Obtiene estadísticas del proyecto."""
           async with self.client as client:
               return await client.get(f"{self.endpoint}/{project_id}/stats")
   ```

4. Repetir implementación para todos los repositorios

5. Actualizar `src/infrastructure/container.py` para inyectar repositorios concretos

#### Tests Asociados

- [ ] Test 1.5.1: Test unitario BaseRepositoryImpl.get_by_id con mock
- [ ] Test 1.5.2: Test unitario BaseRepositoryImpl.list con filtros
- [ ] Test 1.5.3: Test unitario BaseRepositoryImpl.create
- [ ] Test 1.5.4: Test unitario BaseRepositoryImpl.update con versión
- [ ] Test 1.5.5: Test que update lanza ConcurrencyError en conflicto
- [ ] Test 1.5.6: Test unitario BaseRepositoryImpl.delete
- [ ] Test 1.5.7: Test ProjectRepositoryImpl.get_by_slug
- [ ] Test 1.5.8: Test ProjectRepositoryImpl.list_by_member
- [ ] Test 1.5.9: Test ProjectRepositoryImpl.get_stats
- [ ] Test 1.5.10: Tests para cada repositorio implementado

#### Criterios de Aceptación

- [ ] Todos los repositorios implementados
- [ ] BaseRepositoryImpl proporciona funcionalidad CRUD reutilizable
- [ ] Control de concurrencia implementado con versión
- [ ] Cobertura de tests >= 85% en repositorios
- [ ] Mapeo correcto de excepciones de API a excepciones de dominio

#### Archivos Afectados

- `src/infrastructure/repositories/base_repository_impl.py` - **NUEVO**
- `src/infrastructure/repositories/project_repository_impl.py` - **NUEVO**
- `src/infrastructure/repositories/epic_repository_impl.py` - REFACTORIZAR
- `src/infrastructure/repositories/user_story_repository_impl.py` - **NUEVO**
- `src/infrastructure/repositories/task_repository_impl.py` - **NUEVO**
- `src/infrastructure/repositories/issue_repository_impl.py` - **NUEVO**
- `src/infrastructure/repositories/milestone_repository_impl.py` - **NUEVO**
- `src/infrastructure/repositories/member_repository_impl.py` - **NUEVO**
- `src/infrastructure/repositories/wiki_repository_impl.py` - **NUEVO**
- `src/infrastructure/container.py` - Inyectar repositorios
- `tests/unit/infrastructure/repositories/test_base_repository_impl.py` - **NUEVO**
- `tests/unit/infrastructure/repositories/test_project_repository_impl.py` - **NUEVO**

---

### Tarea 1.6: Implementar Use Cases (Application Layer)

**Problema**: Solo existen use cases para Epic, faltan todos los demás
**Objetivo**: Use cases completos para todos los módulos
**Prioridad**: ALTA
**Dependencias**: Tarea 1.5
**Estimación**: 16 horas

#### Pasos de Implementación

1. Crear estructura:
   ```
   src/application/use_cases/
   ├── __init__.py
   ├── base_use_case.py
   ├── project_use_cases.py
   ├── epic_use_cases.py          # Refactorizar existente
   ├── user_story_use_cases.py
   ├── task_use_cases.py
   ├── issue_use_cases.py
   ├── milestone_use_cases.py
   ├── member_use_cases.py
   └── wiki_use_cases.py
   ```

2. Crear use case base `src/application/use_cases/base_use_case.py`:
   ```python
   """Use case base."""
   from abc import ABC, abstractmethod
   from typing import Generic, TypeVar, Optional

   T = TypeVar('T')
   R = TypeVar('R')


   class BaseUseCase(ABC, Generic[T, R]):
       """
       Caso de uso base.

       T: Tipo del input (request)
       R: Tipo del output (response)
       """

       @abstractmethod
       async def execute(self, request: T) -> R:
           """
           Ejecuta el caso de uso.

           Args:
               request: Datos de entrada

           Returns:
               Resultado de la operación
           """
           pass
   ```

3. Crear use cases de proyecto `src/application/use_cases/project_use_cases.py`:
   ```python
   """Use cases para gestión de proyectos."""
   from typing import List, Optional, Dict, Any
   from pydantic import BaseModel, Field

   from src.domain.entities.project import Project
   from src.domain.repositories.project_repository import ProjectRepository
   from src.domain.exceptions import ResourceNotFoundError, ValidationError


   # DTOs (Data Transfer Objects)

   class CreateProjectRequest(BaseModel):
       """Request para crear proyecto."""
       name: str = Field(..., min_length=1, max_length=255)
       description: str = ""
       is_private: bool = True
       is_backlog_activated: bool = True
       is_kanban_activated: bool = True
       is_wiki_activated: bool = True
       is_issues_activated: bool = True
       tags: List[str] = []


   class UpdateProjectRequest(BaseModel):
       """Request para actualizar proyecto."""
       project_id: int
       name: Optional[str] = None
       description: Optional[str] = None
       is_private: Optional[bool] = None
       is_backlog_activated: Optional[bool] = None
       is_kanban_activated: Optional[bool] = None
       is_wiki_activated: Optional[bool] = None
       is_issues_activated: Optional[bool] = None
       tags: Optional[List[str]] = None


   class ListProjectsRequest(BaseModel):
       """Request para listar proyectos."""
       member_id: Optional[int] = None
       is_private: Optional[bool] = None
       limit: Optional[int] = None
       offset: Optional[int] = None


   # Use Cases

   class ProjectUseCases:
       """
       Casos de uso para gestión de proyectos.

       Coordina operaciones de negocio usando el repositorio.
       """

       def __init__(self, repository: ProjectRepository):
           self.repository = repository

       async def create_project(self, request: CreateProjectRequest) -> Project:
           """
           Crea un nuevo proyecto.

           Args:
               request: Datos del proyecto a crear

           Returns:
               Proyecto creado con ID asignado

           Raises:
               ValidationError: Si los datos son inválidos
           """
           # Crear entidad de dominio
           project = Project(
               name=request.name,
               description=request.description,
               is_private=request.is_private,
               is_backlog_activated=request.is_backlog_activated,
               is_kanban_activated=request.is_kanban_activated,
               is_wiki_activated=request.is_wiki_activated,
               is_issues_activated=request.is_issues_activated,
               tags=request.tags
           )

           # Persistir
           return await self.repository.create(project)

       async def get_project(self, project_id: int) -> Project:
           """
           Obtiene un proyecto por ID.

           Args:
               project_id: ID del proyecto

           Returns:
               Proyecto encontrado

           Raises:
               ResourceNotFoundError: Si el proyecto no existe
           """
           project = await self.repository.get_by_id(project_id)
           if project is None:
               raise ResourceNotFoundError(f"Project {project_id} not found")
           return project

       async def get_project_by_slug(self, slug: str) -> Project:
           """
           Obtiene un proyecto por slug.

           Args:
               slug: Slug del proyecto

           Returns:
               Proyecto encontrado

           Raises:
               ResourceNotFoundError: Si el proyecto no existe
           """
           project = await self.repository.get_by_slug(slug)
           if project is None:
               raise ResourceNotFoundError(f"Project with slug '{slug}' not found")
           return project

       async def list_projects(self, request: ListProjectsRequest) -> List[Project]:
           """
           Lista proyectos con filtros opcionales.

           Args:
               request: Filtros de búsqueda

           Returns:
               Lista de proyectos que cumplen los filtros
           """
           filters = {}
           if request.member_id is not None:
               filters['member'] = request.member_id
           if request.is_private is not None:
               filters['is_private'] = request.is_private

           return await self.repository.list(
               filters=filters,
               limit=request.limit,
               offset=request.offset
           )

       async def update_project(self, request: UpdateProjectRequest) -> Project:
           """
           Actualiza un proyecto existente.

           Args:
               request: Datos del proyecto a actualizar

           Returns:
               Proyecto actualizado

           Raises:
               ResourceNotFoundError: Si el proyecto no existe
               ConcurrencyError: Si hubo conflicto de versión
           """
           # Obtener proyecto actual
           project = await self.get_project(request.project_id)

           # Aplicar cambios solo a campos no-None
           if request.name is not None:
               project.name = request.name
           if request.description is not None:
               project.description = request.description
           if request.is_private is not None:
               project.is_private = request.is_private
           if request.is_backlog_activated is not None:
               project.is_backlog_activated = request.is_backlog_activated
           if request.is_kanban_activated is not None:
               project.is_kanban_activated = request.is_kanban_activated
           if request.is_wiki_activated is not None:
               project.is_wiki_activated = request.is_wiki_activated
           if request.is_issues_activated is not None:
               project.is_issues_activated = request.is_issues_activated
           if request.tags is not None:
               project.tags = request.tags

           # Persistir cambios
           return await self.repository.update(project)

       async def delete_project(self, project_id: int) -> bool:
           """
           Elimina un proyecto.

           Args:
               project_id: ID del proyecto a eliminar

           Returns:
               True si se eliminó, False si no existía
           """
           return await self.repository.delete(project_id)

       async def get_project_stats(self, project_id: int) -> Dict[str, Any]:
           """
           Obtiene estadísticas del proyecto.

           Args:
               project_id: ID del proyecto

           Returns:
               Diccionario con estadísticas

           Raises:
               ResourceNotFoundError: Si el proyecto no existe
           """
           # Verificar que existe
           await self.get_project(project_id)

           # Obtener estadísticas
           return await self.repository.get_stats(project_id)
   ```

4. Repetir patrón para:
   - `EpicUseCases` (refactorizar existente)
   - `UserStoryUseCases`
   - `TaskUseCases`
   - `IssueUseCases`
   - `MilestoneUseCases`
   - `MemberUseCases`
   - `WikiUseCases`

5. Actualizar `src/infrastructure/container.py` para inyectar use cases

#### Tests Asociados

- [ ] Test 1.6.1: Test unitario create_project con mock de repository
- [ ] Test 1.6.2: Test unitario get_project que devuelve proyecto
- [ ] Test 1.6.3: Test que get_project lanza ResourceNotFoundError si no existe
- [ ] Test 1.6.4: Test unitario list_projects con filtros
- [ ] Test 1.6.5: Test unitario update_project con cambios parciales
- [ ] Test 1.6.6: Test unitario delete_project
- [ ] Test 1.6.7: Test get_project_stats
- [ ] Test 1.6.8: Tests para cada use case implementado
- [ ] Test 1.6.9: Tests de validación de DTOs (CreateProjectRequest, etc.)

#### Criterios de Aceptación

- [ ] Todos los use cases implementados
- [ ] DTOs (Request/Response) usando Pydantic
- [ ] Separación clara: use cases NO acceden a TaigaAPIClient directamente
- [ ] Cobertura de tests >= 85% en use cases
- [ ] Docstrings completos

#### Archivos Afectados

- `src/application/use_cases/base_use_case.py` - **NUEVO**
- `src/application/use_cases/project_use_cases.py` - **NUEVO**
- `src/application/use_cases/epic_use_cases.py` - REFACTORIZAR
- `src/application/use_cases/user_story_use_cases.py` - **NUEVO**
- `src/application/use_cases/task_use_cases.py` - **NUEVO**
- `src/application/use_cases/issue_use_cases.py` - **NUEVO**
- `src/application/use_cases/milestone_use_cases.py` - **NUEVO**
- `src/application/use_cases/member_use_cases.py` - **NUEVO**
- `src/application/use_cases/wiki_use_cases.py` - **NUEVO**
- `src/infrastructure/container.py` - Inyectar use cases
- `tests/unit/application/use_cases/test_project_use_cases.py` - **NUEVO**

---

### Tarea 1.7: Refactorizar Tools para Usar Use Cases

**Problema**: Tools en `/src/application/tools/` tienen lógica mezclada
**Objetivo**: Tools delegan toda lógica a use cases
**Prioridad**: ALTA
**Dependencias**: Tarea 1.6
**Estimación**: 12 horas

#### Pasos de Implementación

1. Refactorizar `src/application/tools/project_tools.py`:

   **ANTES** (ejemplo simplificado):
   ```python
   class ProjectTools:
       def __init__(self, mcp: FastMCP):
           self.mcp = mcp
           self.config = TaigaConfig()

       def register_tools(self):
           @self.mcp.tool(name="taiga_create_project")
           async def create_project(
               auth_token: str,
               name: str,
               description: str = ""
           ) -> Dict[str, Any]:
               # Lógica mezclada aquí
               async with TaigaAPIClient(self.config) as client:
                   client.auth_token = auth_token
                   result = await client.create_project({
                       "name": name,
                       "description": description
                   })
                   return result
   ```

   **DESPUÉS**:
   ```python
   from src.application.use_cases.project_use_cases import (
       ProjectUseCases,
       CreateProjectRequest
   )


   class ProjectTools:
       def __init__(self, mcp: FastMCP, use_cases: ProjectUseCases):
           self.mcp = mcp
           self.use_cases = use_cases

       def register_tools(self):
           @self.mcp.tool(
               name="taiga_create_project",
               description="Crea un nuevo proyecto en Taiga"
           )
           async def create_project(
               auth_token: str,
               name: str,
               description: str = "",
               is_private: bool = True,
               is_backlog_activated: bool = True,
               is_kanban_activated: bool = True,
               is_wiki_activated: bool = True,
               is_issues_activated: bool = True,
               tags: List[str] = []
           ) -> Dict[str, Any]:
               """
               Crea un nuevo proyecto.

               Args:
                   auth_token: Token de autenticación
                   name: Nombre del proyecto
                   description: Descripción del proyecto
                   is_private: Si el proyecto es privado
                   is_backlog_activated: Si activar módulo backlog
                   is_kanban_activated: Si activar módulo kanban
                   is_wiki_activated: Si activar módulo wiki
                   is_issues_activated: Si activar módulo issues
                   tags: Tags del proyecto

               Returns:
                   Proyecto creado con sus datos
               """
               try:
                   # Construir request
                   request = CreateProjectRequest(
                       name=name,
                       description=description,
                       is_private=is_private,
                       is_backlog_activated=is_backlog_activated,
                       is_kanban_activated=is_kanban_activated,
                       is_wiki_activated=is_wiki_activated,
                       is_issues_activated=is_issues_activated,
                       tags=tags
                   )

                   # Delegar a use case
                   project = await self.use_cases.create_project(request)

                   # Retornar como dict
                   return {
                       "id": project.id,
                       "name": project.name,
                       "slug": str(project.slug) if project.slug else None,
                       "description": project.description,
                       "is_private": project.is_private,
                       "message": f"Proyecto '{name}' creado exitosamente"
                   }

               except ValidationError as e:
                   raise ToolError(f"Datos inválidos: {str(e)}")
               except TaigaAPIError as e:
                   raise ToolError(f"Error de API: {str(e)}")
               except Exception as e:
                   raise ToolError(f"Error inesperado: {str(e)}")
   ```

2. Patrón a seguir:
   - Tool recibe use case por DI (constructor)
   - Tool construye Request DTO desde parámetros
   - Tool llama a `use_case.metodo(request)`
   - Tool convierte entidad de dominio a dict para retornar
   - Tool captura excepciones de dominio y las convierte a `ToolError`

3. Refactorizar todos los tools:
   - `auth_tools.py`
   - `epic_tools.py`
   - `user_story_tools.py`
   - `task_tools.py`
   - `issue_tools.py`
   - `milestone_tools.py`
   - `member_tools.py`
   - `wiki_tools.py`

4. Actualizar `src/infrastructure/container.py` para inyectar use cases en tools

#### Tests Asociados

- [ ] Test 1.7.1: Test que tool crea request DTO correctamente
- [ ] Test 1.7.2: Test que tool delega a use case
- [ ] Test 1.7.3: Test que tool convierte entidad a dict
- [ ] Test 1.7.4: Test que tool captura ValidationError y lanza ToolError
- [ ] Test 1.7.5: Test que tool captura TaigaAPIError y lanza ToolError
- [ ] Test 1.7.6: Tests para cada tool refactorizado

#### Criterios de Aceptación

- [ ] Todos los tools refactorizados para usar use cases
- [ ] Tools NO acceden a repositorios directamente
- [ ] Tools NO acceden a TaigaAPIClient directamente
- [ ] Manejo consistente de excepciones (DomainException → ToolError)
- [ ] Cobertura de tests >= 80% en tools

#### Archivos Afectados

- `src/application/tools/auth_tools.py` - REFACTORIZAR
- `src/application/tools/project_tools.py` - REFACTORIZAR
- `src/application/tools/epic_tools.py` - REFACTORIZAR
- `src/application/tools/user_story_tools.py` - REFACTORIZAR
- `src/application/tools/task_tools.py` - REFACTORIZAR
- `src/application/tools/issue_tools.py` - REFACTORIZAR
- `src/application/tools/milestone_tools.py` - REFACTORIZAR
- `src/application/tools/member_tools.py` - REFACTORIZAR
- `src/application/tools/wiki_tools.py` - REFACTORIZAR
- `src/infrastructure/container.py` - Inyectar use cases en tools
- `tests/unit/application/tools/test_project_tools.py` - REFACTORIZAR

---

### Tarea 1.8: Eliminar Arquitectura Legacy

**Problema**: Código duplicado en `/src/tools/` (arquitectura antigua)
**Objetivo**: Eliminar `/src/tools/` completamente
**Prioridad**: MEDIA
**Dependencias**: Tarea 1.7
**Estimación**: 4 horas

#### Pasos de Implementación

1. Verificar que TODAS las herramientas legacy tienen equivalente en `/src/application/tools/`:
   ```bash
   # Comparar listado de herramientas
   ls src/tools/*.py
   ls src/application/tools/*.py
   ```

2. Verificar que ningún import usa `/src/tools/`:
   ```bash
   grep -r "from src.tools" src/
   grep -r "import src.tools" src/
   ```

3. Crear script de validación `scripts/validate_no_legacy.py`:
   ```python
   """Valida que no hay referencias a arquitectura legacy."""
   import sys
   from pathlib import Path

   def check_no_legacy_imports():
       src_dir = Path("src")
       legacy_refs = []

       for py_file in src_dir.rglob("*.py"):
           if "tools/" in str(py_file):
               continue  # Saltar archivos legacy mismos

           content = py_file.read_text()
           if "from src.tools" in content or "import src.tools" in content:
               legacy_refs.append(py_file)

       if legacy_refs:
           print("❌ LEGACY IMPORTS FOUND:")
           for ref in legacy_refs:
               print(f"  - {ref}")
           return False
       else:
           print("✅ No legacy imports found")
           return True

   if __name__ == "__main__":
       success = check_no_legacy_imports()
       sys.exit(0 if success else 1)
   ```

4. Ejecutar validación:
   ```bash
   uv run python scripts/validate_no_legacy.py
   ```

5. Si validación pasa, eliminar directorio legacy:
   ```bash
   rm -rf src/tools/
   ```

6. Actualizar imports en tests si es necesario

7. Ejecutar suite de tests completa:
   ```bash
   uv run pytest tests/ -v
   ```

#### Tests Asociados

- [ ] Test 1.8.1: Script validate_no_legacy.py pasa
- [ ] Test 1.8.2: Todos los tests unitarios pasan sin src/tools/
- [ ] Test 1.8.3: Tests de integración pasan sin src/tools/
- [ ] Test 1.8.4: Servidor inicia correctamente sin src/tools/

#### Criterios de Aceptación

- [ ] Directorio `/src/tools/` eliminado
- [ ] Sin imports de `src.tools` en ningún archivo
- [ ] Todos los tests pasan
- [ ] Servidor inicia correctamente
- [ ] Documentación actualizada (sin referencias a arquitectura legacy)

#### Archivos Afectados

- `src/tools/` - **ELIMINAR** (todo el directorio)
- `scripts/validate_no_legacy.py` - **NUEVO**
- Tests que importaban de `src/tools` - Actualizar imports
- `README.md` - Actualizar estructura del proyecto

---

### Tarea 1.9: Refactorizar TaigaAPIClient

**Problema**: Métodos con `**kwargs` sin type hints claros
**Objetivo**: TaigaAPIClient con métodos tipados para cada endpoint
**Prioridad**: MEDIA
**Dependencias**: Tarea 1.5
**Estimación**: 10 horas

#### Pasos de Implementación

1. Analizar métodos actuales de TaigaAPIClient:
   ```python
   # ANTES (problemático)
   async def create_epic(self, **kwargs) -> Dict[str, Any]:
       return await self.post("/epics", data=kwargs)
   ```

2. Refactorizar a métodos tipados:
   ```python
   # DESPUÉS (correcto)
   async def create_epic(
       self,
       project: int,
       subject: str,
       description: Optional[str] = None,
       assigned_to: Optional[int] = None,
       status: Optional[int] = None,
       tags: Optional[List[str]] = None,
       color: Optional[str] = None
   ) -> Dict[str, Any]:
       """
       Crea un epic en Taiga.

       Args:
           project: ID del proyecto
           subject: Título del epic
           description: Descripción del epic
           assigned_to: ID del usuario asignado
           status: ID del estado
           tags: Tags del epic
           color: Color del epic (hex)

       Returns:
           Epic creado
       """
       data = {
           "project": project,
           "subject": subject
       }
       if description is not None:
           data["description"] = description
       if assigned_to is not None:
           data["assigned_to"] = assigned_to
       if status is not None:
           data["status"] = status
       if tags is not None:
           data["tags"] = tags
       if color is not None:
           data["color"] = color

       return await self.post("/epics", data=data)
   ```

3. Beneficios:
   - IDE autocompletion funciona
   - mypy puede verificar tipos
   - Documentación clara de parámetros
   - Validación en tiempo de desarrollo

4. Refactorizar todos los métodos de TaigaAPIClient:
   - `list_projects(...)`
   - `create_project(...)`
   - `update_project(...)`
   - `list_epics(...)`
   - `create_epic(...)`
   - Y así sucesivamente para todos los endpoints

5. Considerar crear una clase separada por módulo:
   ```python
   class ProjectClient:
       def __init__(self, http_client: TaigaAPIClient):
           self.client = http_client

       async def list(self, member: Optional[int] = None, ...) -> List[Dict]:
           ...

       async def create(self, name: str, description: str = "", ...) -> Dict:
           ...

   class EpicClient:
       def __init__(self, http_client: TaigaAPIClient):
           self.client = http_client

       async def list(self, project: Optional[int] = None, ...) -> List[Dict]:
           ...
   ```

6. Actualizar repositorios para usar nuevos métodos tipados

#### Tests Asociados

- [ ] Test 1.9.1: Test que create_epic con parámetros tipados funciona
- [ ] Test 1.9.2: Test que parámetros opcionales se manejan correctamente
- [ ] Test 1.9.3: Test mypy pasa en TaigaAPIClient
- [ ] Test 1.9.4: Tests para cada método refactorizado
- [ ] Test 1.9.5: Tests de integración con API real (opcional)

#### Criterios de Aceptación

- [ ] Todos los métodos de TaigaAPIClient tienen type hints completos
- [ ] Sin uso de `**kwargs` en métodos públicos
- [ ] mypy pasa sin errores en TaigaAPIClient
- [ ] Docstrings completos en todos los métodos
- [ ] Repositorios actualizados para usar nuevos métodos

#### Archivos Afectados

- `src/taiga_client.py` - REFACTORIZAR (todos los métodos)
- `src/infrastructure/repositories/*.py` - Actualizar llamadas a TaigaAPIClient
- `tests/unit/test_taiga_client.py` - Actualizar tests

---

### Tarea 1.10: Validación de Fase 1

**Problema**: Asegurar que Fase 1 está completa y funcional
**Objetivo**: Verificación exhaustiva de todos los criterios
**Prioridad**: CRÍTICA
**Dependencias**: Tareas 1.1-1.9
**Estimación**: 6 horas

#### Pasos de Implementación

1. Crear script de validación `scripts/validate_phase1.py`:
   ```python
   """Valida que Fase 1 está completa."""
   import sys
   from pathlib import Path
   import subprocess

   def check_domain_layer():
       """Verifica capa de dominio."""
       print("\n🔍 Validando Domain Layer...")

       required_entities = [
           "src/domain/entities/base.py",
           "src/domain/entities/project.py",
           "src/domain/entities/epic.py",
           "src/domain/entities/user_story.py",
           "src/domain/entities/task.py",
           "src/domain/entities/issue.py",
           "src/domain/entities/milestone.py"
       ]

       missing = []
       for entity in required_entities:
           if not Path(entity).exists():
               missing.append(entity)

       if missing:
           print(f"❌ Missing entities: {missing}")
           return False
       else:
           print("✅ All entities present")
           return True

   def check_repositories():
       """Verifica repositorios."""
       print("\n🔍 Validando Repositories...")

       # Interfaces
       required_interfaces = [
           "src/domain/repositories/project_repository.py",
           "src/domain/repositories/epic_repository.py",
           # ...
       ]

       # Implementaciones
       required_impls = [
           "src/infrastructure/repositories/project_repository_impl.py",
           "src/infrastructure/repositories/epic_repository_impl.py",
           # ...
       ]

       all_present = all(Path(p).exists() for p in required_interfaces + required_impls)

       if all_present:
           print("✅ All repositories present")
           return True
       else:
           print("❌ Some repositories missing")
           return False

   def check_use_cases():
       """Verifica use cases."""
       print("\n🔍 Validando Use Cases...")

       required_use_cases = [
           "src/application/use_cases/project_use_cases.py",
           "src/application/use_cases/epic_use_cases.py",
           # ...
       ]

       all_present = all(Path(p).exists() for p in required_use_cases)

       if all_present:
           print("✅ All use cases present")
           return True
       else:
           print("❌ Some use cases missing")
           return False

   def check_tools():
       """Verifica tools."""
       print("\n🔍 Validando Tools...")

       # Verificar que tools usan use cases
       tools_files = list(Path("src/application/tools").glob("*.py"))

       issues = []
       for tool_file in tools_files:
           content = tool_file.read_text()
           if "TaigaAPIClient" in content and "__init__" in content:
               issues.append(f"{tool_file}: Tool accessing TaigaAPIClient directly")

       if issues:
           print(f"❌ Tools issues found:")
           for issue in issues:
               print(f"  - {issue}")
           return False
       else:
           print("✅ All tools use use cases correctly")
           return True

   def check_no_legacy():
       """Verifica que no hay arquitectura legacy."""
       print("\n🔍 Validando No Legacy Architecture...")

       if Path("src/tools").exists():
           print("❌ Legacy src/tools/ directory still exists")
           return False
       else:
           print("✅ Legacy architecture removed")
           return True

   def check_dependency_injection():
       """Verifica sistema de DI."""
       print("\n🔍 Validando Dependency Injection...")

       if not Path("src/infrastructure/container.py").exists():
           print("❌ Container not found")
           return False

       # Verificar que server.py usa container
       server_content = Path("src/server.py").read_text()
       if "ApplicationContainer" not in server_content:
           print("❌ Server not using container")
           return False

       print("✅ Dependency injection configured")
       return True

   def check_tests():
       """Verifica tests."""
       print("\n🔍 Validando Tests...")

       # Ejecutar pytest con cobertura
       result = subprocess.run(
           ["uv", "run", "pytest", "tests/", "--cov=src", "--cov-report=term", "-v"],
           capture_output=True,
           text=True
       )

       if result.returncode != 0:
           print("❌ Tests failed")
           print(result.stdout)
           return False

       # Verificar cobertura >= 80%
       if "TOTAL" in result.stdout:
           # Parsear línea de cobertura
           for line in result.stdout.split("\n"):
               if "TOTAL" in line:
                   parts = line.split()
                   coverage = int(parts[-1].replace("%", ""))
                   if coverage < 80:
                       print(f"❌ Coverage {coverage}% < 80%")
                       return False

       print("✅ All tests pass with >= 80% coverage")
       return True

   def check_linting():
       """Verifica linting."""
       print("\n🔍 Validando Linting...")

       # Ruff
       result = subprocess.run(
           ["uv", "run", "ruff", "check", "src/", "tests/"],
           capture_output=True
       )
       if result.returncode != 0:
           print("❌ Ruff check failed")
           return False

       # Mypy
       result = subprocess.run(
           ["uv", "run", "mypy", "src/"],
           capture_output=True
       )
       if result.returncode != 0:
           print("⚠️  Mypy found issues (acceptable if not critical)")

       print("✅ Linting passed")
       return True

   def main():
       print("=" * 60)
       print("VALIDACIÓN DE FASE 1: ARQUITECTURA UNIFICADA DDD")
       print("=" * 60)

       checks = [
           check_domain_layer,
           check_repositories,
           check_use_cases,
           check_tools,
           check_no_legacy,
           check_dependency_injection,
           check_linting,
           check_tests
       ]

       results = [check() for check in checks]

       print("\n" + "=" * 60)
       if all(results):
           print("✅ FASE 1 COMPLETA Y VALIDADA")
           print("=" * 60)
           return 0
       else:
           print("❌ FASE 1 INCOMPLETA - Revisar errores arriba")
           print("=" * 60)
           return 1

   if __name__ == "__main__":
       sys.exit(main())
   ```

2. Ejecutar validación:
   ```bash
   uv run python scripts/validate_phase1.py
   ```

3. Corregir cualquier problema encontrado

4. Documentar en `CHANGELOG.md`:
   ```markdown
   # Changelog

   ## [Fase 1 Completada] - 2025-XX-XX

   ### Cambios Arquitectónicos
   - ✅ Implementada arquitectura DDD completa (Domain, Application, Infrastructure)
   - ✅ Sistema de inyección de dependencias con dependency-injector
   - ✅ Eliminada arquitectura legacy (/src/tools/)

   ### Domain Layer
   - ✅ Entidades: Project, Epic, UserStory, Task, Issue, Milestone, Member, WikiPage
   - ✅ Value Objects: ProjectSlug, Email, AuthToken, Status
   - ✅ Repository Interfaces para todas las entidades

   ### Application Layer
   - ✅ Use Cases para todas las entidades
   - ✅ DTOs (Request/Response) con Pydantic
   - ✅ Tools refactorizados para usar use cases

   ### Infrastructure Layer
   - ✅ Repository Implementations usando TaigaAPIClient
   - ✅ Container de DI configurado
   - ✅ TaigaAPIClient refactorizado con type hints completos

   ### Testing
   - ✅ Cobertura >= 80% en todas las capas
   - ✅ Tests unitarios para Domain, Application, Infrastructure
   - ✅ Tests de integración para servidor

   ### Herramientas
   - ✅ Ruff configurado (linting + formatting)
   - ✅ Mypy configurado (type checking)
   - ✅ Pre-commit hooks instalados
   ```

#### Tests Asociados

- [ ] Test 1.10.1: Script validate_phase1.py pasa completamente
- [ ] Test 1.10.2: Cobertura >= 80% verificada
- [ ] Test 1.10.3: Ruff check pasa
- [ ] Test 1.10.4: Servidor inicia sin errores
- [ ] Test 1.10.5: Todas las herramientas MCP funcionan

#### Criterios de Aceptación

- [ ] Script de validación pasa 100%
- [ ] Documentación actualizada (README, CHANGELOG)
- [ ] Todos los tests pasan
- [ ] Cobertura >= 80%
- [ ] Sin warnings críticos de mypy
- [ ] Servidor funcional con arquitectura nueva

#### Archivos Afectados

- `scripts/validate_phase1.py` - **NUEVO**
- `CHANGELOG.md` - **NUEVO** o actualizar
- `README.md` - Actualizar con nueva arquitectura
- `Documentacion/estructura_proyecto.md` - Actualizar estructura

---

### Resumen de Fase 1

**Total de Tareas**: 10
**Total de Tests**: 35+
**Duración Estimada**: 3 semanas (120 horas)

**Entregables**:
- ✅ Arquitectura DDD completa y funcional
- ✅ Sistema de DI automático
- ✅ Eliminación de código legacy
- ✅ Cobertura >= 80%
- ✅ Herramientas de desarrollo configuradas

**Próxima Fase**: [Fase 2 - Normalización de Interfaces](#fase-2-normalización-de-interfaces)

---

## Fase 2: Normalización de Interfaces

**Duración**: 2 semanas (80 horas)
**Objetivo**: Homogeneizar nombres, tipos de retorno y parámetros de las 123+ herramientas MCP
**Impacto**: ALTO - Mejora experiencia de usuario y consistencia

### Resumen de la Fase

| Aspecto | Estado Actual | Estado Objetivo |
|---------|---------------|----------------|
| Nombres de herramientas | Mixtos (con/sin prefijo `taiga_`) | Todos con prefijo `taiga_` |
| Tipos de retorno | Mixtos (Dict/str/List) | Consistentes (Dict/List[Dict]/Pydantic) |
| Parámetros | Aliases redundantes (member/member_id) | Sin aliases, parámetros claros |
| Documentación de tools | Parcial | Completa con ejemplos |
| Agrupación lógica | Por módulo (auth, projects, etc.) | Por funcionalidad (CRUD, búsqueda, etc.) |

### Tareas de la Fase 2

---

### Tarea 2.1: Auditoría Completa de Herramientas MCP

**Problema**: No hay inventario completo de las 123+ herramientas
**Objetivo**: Generar inventario exhaustivo con problemas identificados
**Prioridad**: CRÍTICA
**Dependencias**: Fase 1 completa
**Estimación**: 6 horas

#### Pasos de Implementación

1. Crear script de auditoría `scripts/audit_mcp_tools.py`:
   ```python
   """Audita todas las herramientas MCP del servidor."""
   import ast
   import inspect
   from pathlib import Path
   from typing import Dict, List, Any
   import json


   class ToolInfo:
       def __init__(self):
           self.name: str = ""
           self.description: str = ""
           self.file_path: str = ""
           self.function_name: str = ""
           self.parameters: List[Dict[str, Any]] = []
           self.return_type: str = ""
           self.has_prefix: bool = False
           self.issues: List[str] = []


   def extract_tools_from_file(file_path: Path) -> List[ToolInfo]:
       """Extrae información de tools de un archivo."""
       tools = []

       content = file_path.read_text()
       tree = ast.parse(content)

       for node in ast.walk(tree):
           if isinstance(node, ast.Call):
               # Buscar decoradores @self.mcp.tool o @mcp.tool
               if (isinstance(node.func, ast.Attribute) and
                   node.func.attr == 'tool'):

                   tool = ToolInfo()
                   tool.file_path = str(file_path)

                   # Extraer name si está especificado
                   for keyword in node.keywords:
                       if keyword.arg == 'name':
                           if isinstance(keyword.value, ast.Constant):
                               tool.name = keyword.value.value
                       elif keyword.arg == 'description':
                           if isinstance(keyword.value, ast.Constant):
                               tool.description = keyword.value.value

                   # Analizar problemas
                   if tool.name:
                       if not tool.name.startswith('taiga_'):
                           tool.has_prefix = False
                           tool.issues.append("Missing 'taiga_' prefix")
                       else:
                           tool.has_prefix = True

                   if not tool.description:
                       tool.issues.append("Missing description")

                   tools.append(tool)

       return tools


   def audit_all_tools() -> Dict[str, Any]:
       """Audita todas las herramientas del proyecto."""
       tools_dir = Path("src/application/tools")
       all_tools = []

       for py_file in tools_dir.glob("*.py"):
           if py_file.name == "__init__.py":
               continue

           file_tools = extract_tools_from_file(py_file)
           all_tools.extend(file_tools)

       # Generar reporte
       report = {
           "total_tools": len(all_tools),
           "tools_with_prefix": sum(1 for t in all_tools if t.has_prefix),
           "tools_without_prefix": sum(1 for t in all_tools if not t.has_prefix),
           "tools_without_description": sum(1 for t in all_tools if "Missing description" in t.issues),
           "tools": [
               {
                   "name": t.name,
                   "file": t.file_path,
                   "has_prefix": t.has_prefix,
                   "description": t.description[:50] + "..." if len(t.description) > 50 else t.description,
                   "issues": t.issues
               }
               for t in all_tools
           ]
       }

       return report


   def main():
       print("🔍 Auditando herramientas MCP...")

       report = audit_all_tools()

       print(f"\n📊 Resumen:")
       print(f"  Total herramientas: {report['total_tools']}")
       print(f"  Con prefijo 'taiga_': {report['tools_with_prefix']}")
       print(f"  Sin prefijo: {report['tools_without_prefix']}")
       print(f"  Sin descripción: {report['tools_without_description']}")

       # Guardar reporte detallado
       output_path = Path("Documentacion/audit_mcp_tools.json")
       output_path.write_text(json.dumps(report, indent=2))

       print(f"\n📄 Reporte completo guardado en: {output_path}")

       # Mostrar herramientas problemáticas
       problematic = [t for t in report['tools'] if t['issues']]
       if problematic:
           print(f"\n⚠️  Herramientas con problemas ({len(problematic)}):")
           for tool in problematic[:10]:  # Mostrar primeras 10
               print(f"  - {tool['name']}: {', '.join(tool['issues'])}")
           if len(problematic) > 10:
               print(f"  ... y {len(problematic) - 10} más")


   if __name__ == "__main__":
       main()
   ```

2. Ejecutar auditoría:
   ```bash
   uv run python scripts/audit_mcp_tools.py
   ```

3. Analizar reporte generado en `Documentacion/audit_mcp_tools.json`

4. Crear hoja de cálculo `Documentacion/tools_normalization_plan.csv`:
   ```csv
   Current Name,Proposed Name,Module,Return Type Current,Return Type Target,Issues,Priority
   authenticate,taiga_authenticate,auth,Dict,Dict,"None",DONE
   list_projects,taiga_list_projects,projects,List[Dict],List[Dict],"None",DONE
   get_epic,taiga_get_epic,epics,str,Dict,"Returns JSON string",HIGH
   create_userstory,taiga_create_user_story,userstories,Dict,Dict,"Inconsistent naming (userstory vs user_story)",HIGH
   list_issues,taiga_list_issues,issues,List[Dict],List[Dict],"No prefix",HIGH
   ...
   ```

5. Priorizar herramientas a normalizar:
   - **CRÍTICO**: Tipos de retorno incorrectos (str en lugar de Dict)
   - **ALTO**: Sin prefijo `taiga_`
   - **MEDIO**: Nombres inconsistentes (user_story vs userstory)
   - **BAJO**: Documentación incompleta

#### Tests Asociados

- [ ] Test 2.1.1: Script de auditoría se ejecuta sin errores
- [ ] Test 2.1.2: Reporte JSON se genera correctamente
- [ ] Test 2.1.3: Reporte identifica herramientas sin prefijo
- [ ] Test 2.1.4: Reporte identifica herramientas sin descripción

#### Criterios de Aceptación

- [ ] Auditoría completa de 123+ herramientas ejecutada
- [ ] Reporte JSON generado con todos los problemas identificados
- [ ] Plan de normalización creado en CSV
- [ ] Herramientas priorizadas por impacto

#### Archivos Afectados

- `scripts/audit_mcp_tools.py` - **NUEVO**
- `Documentacion/audit_mcp_tools.json` - **GENERADO**
- `Documentacion/tools_normalization_plan.csv` - **NUEVO**

---

### Tarea 2.2: Normalizar Nombres de Herramientas (Prefijo `taiga_`)

**Problema**: 50+ herramientas sin prefijo `taiga_` consistente
**Objetivo**: Todas las herramientas con prefijo `taiga_`
**Prioridad**: ALTA
**Dependencias**: Tarea 2.1
**Estimación**: 8 horas

#### Pasos de Implementación

1. Obtener lista de herramientas sin prefijo desde audit:
   ```bash
   jq '.tools[] | select(.has_prefix == false) | .name' Documentacion/audit_mcp_tools.json
   ```

2. Crear script de renombrado automático `scripts/add_taiga_prefix.py`:
   ```python
   """Agrega prefijo 'taiga_' a herramientas que no lo tienen."""
   import re
   from pathlib import Path
   from typing import List, Tuple


   def add_prefix_to_file(file_path: Path) -> List[Tuple[str, str]]:
       """
       Agrega prefijo 'taiga_' a tools en un archivo.

       Returns:
           Lista de tuplas (nombre_anterior, nombre_nuevo)
       """
       content = file_path.read_text()
       changes = []

       # Buscar @self.mcp.tool(name="xxx")
       pattern = r'@self\.mcp\.tool\(name="([^"]+)"'

       def replacer(match):
           old_name = match.group(1)
           if not old_name.startswith('taiga_'):
               new_name = f"taiga_{old_name}"
               changes.append((old_name, new_name))
               return f'@self.mcp.tool(name="{new_name}"'
           return match.group(0)

       new_content = re.sub(pattern, replacer, content)

       if new_content != content:
           file_path.write_text(new_content)
           print(f"✅ Actualizado: {file_path}")
           for old, new in changes:
               print(f"    {old} → {new}")

       return changes


   def main():
       tools_dir = Path("src/application/tools")
       all_changes = []

       for py_file in tools_dir.glob("*.py"):
           if py_file.name == "__init__.py":
               continue

           changes = add_prefix_to_file(py_file)
           all_changes.extend(changes)

       print(f"\n📊 Total de cambios: {len(all_changes)}")

       # Generar migration guide
       migration_guide = Path("Documentacion/tool_names_migration.md")
       with migration_guide.open('w') as f:
           f.write("# Guía de Migración de Nombres de Herramientas\n\n")
           f.write("| Nombre Anterior | Nombre Nuevo |\n")
           f.write("|----------------|---------------|\n")
           for old, new in sorted(all_changes):
               f.write(f"| `{old}` | `{new}` |\n")

       print(f"\n📄 Guía de migración generada: {migration_guide}")


   if __name__ == "__main__":
       main()
   ```

3. Ejecutar script:
   ```bash
   uv run python scripts/add_taiga_prefix.py
   ```

4. Revisar cambios con git:
   ```bash
   git diff src/application/tools/
   ```

5. Actualizar tests que usen nombres antiguos:
   ```bash
   # Buscar tests que usan nombres sin prefijo
   grep -r "authenticate" tests/ --include="*.py"
   grep -r "list_projects" tests/ --include="*.py"
   # ... etc
   ```

6. Ejecutar tests:
   ```bash
   uv run pytest tests/ -v
   ```

7. Actualizar documentación:
   - README.md (ejemplos de uso)
   - guia_uso.md (ejemplos)
   - Cualquier script que invoque herramientas

#### Tests Asociados

- [ ] Test 2.2.1: Todas las herramientas tienen prefijo `taiga_`
- [ ] Test 2.2.2: Tests antiguos actualizados con nuevos nombres
- [ ] Test 2.2.3: Servidor inicia sin errores con nuevos nombres
- [ ] Test 2.2.4: Tools se registran correctamente con nuevos nombres
- [ ] Test 2.2.5: Auditoría post-cambio muestra 0 herramientas sin prefijo

#### Criterios de Aceptación

- [ ] 100% de herramientas con prefijo `taiga_`
- [ ] Guía de migración generada
- [ ] Tests actualizados y pasando
- [ ] Documentación actualizada

#### Archivos Afectados

- `src/application/tools/*.py` - Actualizar nombres de tools
- `tests/unit/application/tools/*.py` - Actualizar tests
- `tests/integration/*.py` - Actualizar tests de integración
- `scripts/add_taiga_prefix.py` - **NUEVO**
- `Documentacion/tool_names_migration.md` - **GENERADO**
- `README.md` - Actualizar ejemplos
- `guia_uso.md` - Actualizar ejemplos

---

### Tarea 2.3: Normalizar Tipos de Retorno

**Problema**: Herramientas retornan tipos mixtos (Dict/str/List)
**Objetivo**: Tipos de retorno consistentes y estructurados
**Prioridad**: CRÍTICA
**Dependencias**: Tarea 2.1
**Estimación**: 12 horas

#### Pasos de Implementación

1. Identificar herramientas que retornan `str` (JSON serializado):
   ```bash
   # Ejemplo: epic_tools.py tiene varios
   grep -n "return json.dumps" src/application/tools/*.py
   ```

2. Definir estándar de tipos de retorno:

   **Estándar a seguir**:
   ```python
   # Para operaciones que retornan UNA entidad:
   @mcp.tool
   async def taiga_get_project(project_id: int) -> Dict[str, Any]:
       """Obtiene un proyecto."""
       project = await use_cases.get_project(project_id)
       return project.model_dump()  # NO json.dumps()

   # Para operaciones que retornan MÚLTIPLES entidades:
   @mcp.tool
   async def taiga_list_projects() -> List[Dict[str, Any]]:
       """Lista proyectos."""
       projects = await use_cases.list_projects()
       return [p.model_dump() for p in projects]  # NO json.dumps()

   # Para operaciones CRUD exitosas:
   @mcp.tool
   async def taiga_delete_project(project_id: int) -> Dict[str, Any]:
       """Elimina un proyecto."""
       success = await use_cases.delete_project(project_id)
       return {
           "success": success,
           "message": f"Project {project_id} deleted"
       }

   # Para operaciones con datos estructurados complejos:
   from pydantic import BaseModel

   class ProjectStatsResponse(BaseModel):
       total_milestones: int
       total_points: float
       closed_points: float
       # ...

   @mcp.tool
   async def taiga_get_project_stats(project_id: int) -> ProjectStatsResponse:
       """Obtiene estadísticas."""
       stats = await use_cases.get_project_stats(project_id)
       return ProjectStatsResponse(**stats)
   ```

3. Refactorizar `src/application/tools/epic_tools.py`:

   **ANTES**:
   ```python
   @self.mcp.tool(name="taiga_get_epic")
   async def get_epic(auth_token: str, epic_id: int) -> str:  # ← Tipo incorrecto
       result = await client.get_epic(epic_id)
       return json.dumps(result)  # ← Serializando manualmente
   ```

   **DESPUÉS**:
   ```python
   @self.mcp.tool(name="taiga_get_epic")
   async def get_epic(auth_token: str, epic_id: int) -> Dict[str, Any]:  # ← Correcto
       """Obtiene un epic por su ID."""
       epic = await self.use_cases.get_epic(epic_id)
       return epic.model_dump()  # ← Retornar dict directamente
   ```

4. Crear script para detectar uso de `json.dumps` en tools:
   ```python
   """Detecta uso incorrecto de json.dumps en tools."""
   from pathlib import Path

   def check_json_dumps_usage():
       tools_dir = Path("src/application/tools")
       issues = []

       for py_file in tools_dir.glob("*.py"):
           content = py_file.read_text()
           if "json.dumps" in content:
               # Buscar líneas específicas
               for i, line in enumerate(content.split("\n"), 1):
                   if "json.dumps" in line and "return" in line:
                       issues.append(f"{py_file}:{i} - {line.strip()}")

       if issues:
           print("⚠️  Uso incorrecto de json.dumps detectado:")
           for issue in issues:
               print(f"  {issue}")
           return False
       else:
           print("✅ No se detectó uso de json.dumps")
           return True

   if __name__ == "__main__":
       import sys
       sys.exit(0 if check_json_dumps_usage() else 1)
   ```

5. Refactorizar TODAS las herramientas con tipos incorrectos

6. Actualizar type hints en definiciones de tools:
   ```python
   # Asegurar que todos los tools tienen type hint correcto
   @self.mcp.tool(name="taiga_list_epics")
   async def list_epics(...) -> List[Dict[str, Any]]:  # ← Type hint explícito
       ...
   ```

#### Tests Asociados

- [ ] Test 2.3.1: Ninguna herramienta retorna `str` (JSON serializado)
- [ ] Test 2.3.2: Herramientas de listado retornan `List[Dict[str, Any]]`
- [ ] Test 2.3.3: Herramientas de obtención retornan `Dict[str, Any]`
- [ ] Test 2.3.4: Herramientas de eliminación retornan `Dict[str, Any]` con success/message
- [ ] Test 2.3.5: mypy pasa sin errores en todos los tools
- [ ] Test 2.3.6: Tests de integración verifican tipos de retorno

#### Criterios de Aceptación

- [ ] Todos los tools retornan tipos estructurados (no strings)
- [ ] Type hints correctos en todas las funciones de tool
- [ ] Sin uso de `json.dumps()` en tools
- [ ] mypy pasa en src/application/tools/
- [ ] Documentación de cada tool indica tipo de retorno

#### Archivos Afectados

- `src/application/tools/epic_tools.py` - REFACTORIZAR
- `src/application/tools/user_story_tools.py` - REFACTORIZAR
- `src/application/tools/task_tools.py` - REFACTORIZAR
- `src/application/tools/issue_tools.py` - REFACTORIZAR
- (Todos los archivos de tools potencialmente afectados)
- `tests/unit/application/tools/*.py` - Actualizar tests
- `scripts/check_json_dumps.py` - **NUEVO**

---

### Tarea 2.4: Eliminar Parámetros Redundantes (Aliases)

**Problema**: Algunos tools tienen aliases redundantes (member/member_id)
**Objetivo**: Un solo parámetro por concepto, sin aliases
**Prioridad**: MEDIA
**Dependencias**: Tarea 2.1
**Estimación**: 6 horas

#### Pasos de Implementación

1. Identificar parámetros con aliases:

   **Ejemplo encontrado**:
   ```python
   # projects.py - PROBLEMA
   async def taiga_list_projects(
       auth_token: str,
       member: Optional[int] = None,      # ← Alias 1
       member_id: Optional[int] = None,   # ← Alias 2 (redundante)
       ...
   ):
       # Lógica que elige uno u otro
       member_filter = member if member is not None else member_id
   ```

2. Definir estándar de nomenclatura:

   **Estándar**:
   - IDs siempre terminan en `_id` (ej: `project_id`, `epic_id`, `member_id`)
   - Sin aliases (un solo parámetro por concepto)
   - Nombres descriptivos (evitar abreviaciones ambiguas)

3. Refactorizar parámetros:

   **DESPUÉS**:
   ```python
   async def taiga_list_projects(
       auth_token: str,
       member_id: Optional[int] = None,  # ← Un solo parámetro
       ...
   ):
       filters = {}
       if member_id is not None:
           filters['member'] = member_id  # Mapeo interno a API
       ...
   ```

4. Buscar todos los casos de aliases:
   ```bash
   # Buscar patrones sospechosos
   grep -n "member if member" src/application/tools/*.py
   grep -n "project if project" src/application/tools/*.py
   ```

5. Crear lista de cambios de parámetros:
   ```markdown
   # Cambios de Parámetros - Fase 2.4

   ## taiga_list_projects
   - ❌ ANTES: `member: Optional[int], member_id: Optional[int]`
   - ✅ DESPUÉS: `member_id: Optional[int]`

   ## taiga_list_userstories
   - ❌ ANTES: `project: Optional[int], project_id: Optional[int]`
   - ✅ DESPUÉS: `project_id: Optional[int]`

   ...
   ```

6. Actualizar use cases si es necesario (generalmente NO, los use cases ya están bien)

#### Tests Asociados

- [ ] Test 2.4.1: Ninguna herramienta tiene parámetros alias
- [ ] Test 2.4.2: Tests actualizados para usar nuevos nombres de parámetros
- [ ] Test 2.4.3: Herramientas funcionan correctamente con parámetros únicos
- [ ] Test 2.4.4: Documentación de parámetros actualizada

#### Criterios de Aceptación

- [ ] Sin parámetros alias en ninguna herramienta
- [ ] Nomenclatura consistente (_id para IDs)
- [ ] Tests actualizados y pasando
- [ ] Guía de migración de parámetros documentada

#### Archivos Afectados

- `src/application/tools/project_tools.py` - Eliminar alias member/member_id
- `src/application/tools/user_story_tools.py` - Eliminar alias project/project_id
- (Otros archivos con aliases)
- `tests/unit/application/tools/*.py` - Actualizar tests
- `Documentacion/parameter_changes.md` - **NUEVO**

---

### Tarea 2.5: Mejorar Documentación de Herramientas (Docstrings)

**Problema**: Docstrings inconsistentes o incompletos en tools
**Objetivo**: Todas las herramientas con docstrings completos en formato Google
**Prioridad**: MEDIA
**Dependencias**: Tareas 2.2, 2.3, 2.4
**Estimación**: 10 horas

#### Pasos de Implementación

1. Definir estándar de docstring para tools:

   **Estándar**:
   ```python
   @self.mcp.tool(
       name="taiga_create_project",
       description="Crea un nuevo proyecto en Taiga"
   )
   async def create_project(
       auth_token: str,
       name: str,
       description: str = "",
       is_private: bool = True
   ) -> Dict[str, Any]:
       """
       Crea un nuevo proyecto en Taiga.

       Esta herramienta permite crear un proyecto con configuración personalizada.
       El proyecto se crea con los módulos activados por defecto (backlog, kanban, etc.).

       Args:
           auth_token: Token de autenticación obtenido de taiga_authenticate
           name: Nombre del proyecto (máximo 255 caracteres)
           description: Descripción opcional del proyecto
           is_private: Si True, el proyecto será privado (por defecto: True)

       Returns:
           Dict con los siguientes campos:
           - id: ID del proyecto creado
           - name: Nombre del proyecto
           - slug: Slug único del proyecto (generado automáticamente)
           - description: Descripción del proyecto
           - is_private: Si el proyecto es privado
           - message: Mensaje de confirmación

       Raises:
           ToolError: Si falla la creación (ej: nombre duplicado, permisos insuficientes)

       Example:
           >>> await taiga_create_project(
           ...     auth_token="abc123",
           ...     name="Mi Proyecto",
           ...     description="Proyecto de prueba",
           ...     is_private=True
           ... )
           {
               "id": 42,
               "name": "Mi Proyecto",
               "slug": "mi-proyecto",
               "description": "Proyecto de prueba",
               "is_private": True,
               "message": "Proyecto 'Mi Proyecto' creado exitosamente"
           }
       """
       ...
   ```

2. Crear script para validar completitud de docstrings:
   ```python
   """Valida que todos los tools tienen docstrings completos."""
   import ast
   from pathlib import Path
   from typing import List, Dict


   class DocstringChecker:
       REQUIRED_SECTIONS = ["Args", "Returns"]
       OPTIONAL_SECTIONS = ["Raises", "Example"]

       def check_docstring(self, docstring: str) -> Dict[str, bool]:
           """Verifica que docstring tiene secciones requeridas."""
           if not docstring:
               return {"has_docstring": False}

           checks = {"has_docstring": True}

           for section in self.REQUIRED_SECTIONS:
               checks[f"has_{section.lower()}"] = f"{section}:" in docstring

           for section in self.OPTIONAL_SECTIONS:
               checks[f"has_{section.lower()}"] = f"{section}:" in docstring

           return checks

       def check_file(self, file_path: Path) -> List[Dict]:
           """Verifica todos los tools en un archivo."""
           content = file_path.read_text()
           tree = ast.parse(content)

           results = []

           for node in ast.walk(tree):
               if isinstance(node, ast.AsyncFunctionDef):
                   # Buscar decorador @self.mcp.tool
                   has_tool_decorator = any(
                       isinstance(dec, ast.Call) and
                       isinstance(dec.func, ast.Attribute) and
                       dec.func.attr == 'tool'
                       for dec in node.decorator_list
                   )

                   if has_tool_decorator:
                       docstring = ast.get_docstring(node)
                       checks = self.check_docstring(docstring)

                       results.append({
                           "function": node.name,
                           "file": str(file_path),
                           **checks
                       })

           return results


   def main():
       checker = DocstringChecker()
       tools_dir = Path("src/application/tools")

       all_results = []
       for py_file in tools_dir.glob("*.py"):
           if py_file.name == "__init__.py":
               continue
           results = checker.check_file(py_file)
           all_results.extend(results)

       # Generar reporte
       incomplete = [
           r for r in all_results
           if not r.get("has_docstring") or
              not r.get("has_args") or
              not r.get("has_returns")
       ]

       print(f"📊 Total tools: {len(all_results)}")
       print(f"✅ Completos: {len(all_results) - len(incomplete)}")
       print(f"⚠️  Incompletos: {len(incomplete)}")

       if incomplete:
           print("\n⚠️  Tools con documentación incompleta:")
           for tool in incomplete:
               missing = []
               if not tool.get("has_docstring"):
                   missing.append("sin docstring")
               if not tool.get("has_args"):
                   missing.append("sin Args")
               if not tool.get("has_returns"):
                   missing.append("sin Returns")

               print(f"  - {tool['function']} ({', '.join(missing)})")

       return len(incomplete) == 0


   if __name__ == "__main__":
       import sys
       sys.exit(0 if main() else 1)
   ```

3. Ejecutar checker:
   ```bash
   uv run python scripts/check_docstrings.py
   ```

4. Completar docstrings en todos los tools identificados

5. Incluir ejemplos en docstrings (al menos para tools más usados)

#### Tests Asociados

- [ ] Test 2.5.1: Todas las herramientas tienen docstring
- [ ] Test 2.5.2: Todas las herramientas documentan Args
- [ ] Test 2.5.3: Todas las herramientas documentan Returns
- [ ] Test 2.5.4: Al menos 50% de herramientas tienen Example
- [ ] Test 2.5.5: Script de validación pasa 100%

#### Criterios de Aceptación

- [ ] 100% de herramientas con docstring completo
- [ ] Formato Google Style en todos los docstrings
- [ ] Ejemplos incluidos en al menos 50% de herramientas
- [ ] Script de validación pasa

#### Archivos Afectados

- `src/application/tools/*.py` - Completar docstrings
- `scripts/check_docstrings.py` - **NUEVO**

---

### Tarea 2.6: Implementar Responses Estructurados con Pydantic 

**Problema**: Retornos Dict[str, Any] pierden validación de estructura
**Objetivo**: Responses con Pydantic BaseModel para validación automática
**Prioridad**: BAJA (Opcional - para mejora futura)
**Dependencias**: Tarea 2.3
**Estimación**: 12 horas

#### Pasos de Implementación

1. Crear módulo de responses `src/application/responses/`:
   ```
   src/application/responses/
   ├── __init__.py
   ├── base.py
   ├── project_responses.py
   ├── epic_responses.py
   └── ...
   ```

2. Crear response base:
   ```python
   """Responses base."""
   from pydantic import BaseModel, ConfigDict
   from typing import Optional


   class BaseResponse(BaseModel):
       """Response base para todas las herramientas."""

       model_config = ConfigDict(
           from_attributes=True,  # Permitir crear desde objetos
           populate_by_name=True   # Permitir alias de campos
       )


   class SuccessResponse(BaseResponse):
       """Response para operaciones exitosas sin datos específicos."""
       success: bool = True
       message: str
   ```

3. Crear responses de proyecto:
   ```python
   """Responses para operaciones de proyecto."""
   from typing import List, Optional
   from datetime import datetime
   from pydantic import Field

   from src.application.responses.base import BaseResponse


   class ProjectResponse(BaseResponse):
       """Response para operación de proyecto individual."""
       id: int
       name: str
       slug: str
       description: str = ""
       is_private: bool
       owner_id: Optional[int] = None
       created_date: Optional[datetime] = None
       modified_date: Optional[datetime] = None
       total_story_points: Optional[float] = None
       total_milestones: Optional[int] = None
       tags: List[str] = []


   class ProjectListResponse(BaseResponse):
       """Response para lista de proyectos."""
       projects: List[ProjectResponse]
       total: int = Field(..., description="Total de proyectos en la lista")


   class ProjectStatsResponse(BaseResponse):
       """Response para estadísticas de proyecto."""
       project_id: int
       total_milestones: int = 0
       total_points: float = 0
       closed_points: float = 0
       defined_points: float = 0
       assigned_points: float = 0
       total_userstories: int = 0
       total_issues: int = 0
       closed_issues: int = 0
       open_issues: int = 0
   ```

4. Usar responses en tools:
   ```python
   from src.application.responses.project_responses import ProjectResponse

   @self.mcp.tool(name="taiga_get_project")
   async def get_project(
       auth_token: str,
       project_id: int
   ) -> ProjectResponse:  # ← Tipo estructurado
       """Obtiene un proyecto."""
       project = await self.use_cases.get_project(project_id)
       return ProjectResponse.model_validate(project)  # Validación automática
   ```

5. Beneficios:
   - ✅ Validación automática de estructura de salida
   - ✅ Documentación automática de campos en esquema MCP
   - ✅ IDE autocompletion al consumir responses
   - ✅ Fácil evolución (agregar campos con defaults)

#### Tests Asociados

- [ ] Test 2.6.1: ProjectResponse se crea desde entidad Project
- [ ] Test 2.6.2: ProjectResponse valida campos requeridos
- [ ] Test 2.6.3: Tools retornan responses estructurados correctamente
- [ ] Test 2.6.4: FastMCP serializa responses a JSON correctamente

#### Criterios de Aceptación

- [ ] Responses implementados para módulos principales (opcional)
- [ ] Validación automática funciona
- [ ] Tests actualizados para responses estructurados
- [ ] Documentación de responses incluida

#### Archivos Afectados

- `src/application/responses/base.py` - **NUEVO** (opcional)
- `src/application/responses/project_responses.py` - **NUEVO** (opcional)
- `src/application/responses/epic_responses.py` - **NUEVO** (opcional)
- `src/application/tools/project_tools.py` - Usar responses (opcional)
- `src/application/tools/epic_tools.py` - Usar responses (opcional)

---

### Tarea 2.7: Validación de Fase 2

**Problema**: Asegurar que Fase 2 está completa y funcional
**Objetivo**: Verificación exhaustiva de normalización
**Prioridad**: CRÍTICA
**Dependencias**: Tareas 2.1-2.6
**Estimación**: 4 horas

#### Pasos de Implementación

1. Crear script de validación `scripts/validate_phase2.py`:
   ```python
   """Valida que Fase 2 está completa."""
   import sys
   import subprocess
   from pathlib import Path
   import json


   def check_all_tools_have_prefix():
       """Verifica que todas las herramientas tienen prefijo."""
       print("\n🔍 Validando prefijo 'taiga_' en todas las herramientas...")

       result = subprocess.run(
           ["uv", "run", "python", "scripts/audit_mcp_tools.py"],
           capture_output=True,
           text=True
       )

       # Leer reporte
       report_path = Path("Documentacion/audit_mcp_tools.json")
       if not report_path.exists():
           print("❌ Reporte de auditoría no encontrado")
           return False

       report = json.loads(report_path.read_text())

       if report['tools_without_prefix'] > 0:
           print(f"❌ {report['tools_without_prefix']} herramientas sin prefijo")
           return False
       else:
           print(f"✅ {report['total_tools']} herramientas con prefijo 'taiga_'")
           return True


   def check_no_json_dumps():
       """Verifica que no hay uso de json.dumps en tools."""
       print("\n🔍 Validando ausencia de json.dumps...")

       result = subprocess.run(
           ["uv", "run", "python", "scripts/check_json_dumps.py"],
           capture_output=True
       )

       if result.returncode == 0:
           print("✅ Sin uso de json.dumps detectado")
           return True
       else:
           print("❌ Uso de json.dumps detectado en tools")
           return False


   def check_return_types():
       """Verifica que tipos de retorno son consistentes."""
       print("\n🔍 Validando tipos de retorno...")

       # Buscar retornos -> str que no sean auth_token
       tools_dir = Path("src/application/tools")
       issues = []

       for py_file in tools_dir.glob("*.py"):
           content = py_file.read_text()
           lines = content.split("\n")

           for i, line in enumerate(lines):
               if "-> str:" in line or "-> str " in line:
                   # Excepciones permitidas
                   if "auth_token" not in lines[i-1] if i > 0 else True:
                       context = lines[max(0, i-2):i+1]
                       issues.append(f"{py_file}:{i+1} - {''.join(context)}")

       if issues:
           print("❌ Tipos de retorno incorrectos encontrados:")
           for issue in issues[:5]:
               print(f"  {issue}")
           return False
       else:
           print("✅ Tipos de retorno consistentes")
           return True


   def check_no_parameter_aliases():
       """Verifica que no hay aliases de parámetros."""
       print("\n🔍 Validando ausencia de aliases de parámetros...")

       tools_dir = Path("src/application/tools")
       issues = []

       for py_file in tools_dir.glob("*.py"):
           content = py_file.read_text()

           # Buscar patrones sospechosos
           if "member if member" in content:
               issues.append(f"{py_file}: 'member if member' detectado")
           if "project if project" in content:
               issues.append(f"{py_file}: 'project if project' detectado")

       if issues:
           print("❌ Aliases de parámetros detectados:")
           for issue in issues:
               print(f"  {issue}")
           return False
       else:
           print("✅ Sin aliases de parámetros")
           return True


   def check_docstrings_complete():
       """Verifica que docstrings están completos."""
       print("\n🔍 Validando completitud de docstrings...")

       result = subprocess.run(
           ["uv", "run", "python", "scripts/check_docstrings.py"],
           capture_output=True
       )

       if result.returncode == 0:
           print("✅ Docstrings completos")
           return True
       else:
           print("⚠️  Algunos docstrings incompletos")
           return True  # No bloquear por esto


   def check_tests_pass():
       """Verifica que tests pasan."""
       print("\n🔍 Validando tests...")

       result = subprocess.run(
           ["uv", "run", "pytest", "tests/", "-v", "--tb=short"],
           capture_output=True
       )

       if result.returncode == 0:
           print("✅ Todos los tests pasan")
           return True
       else:
           print("❌ Algunos tests fallan")
           return False


   def main():
       print("=" * 60)
       print("VALIDACIÓN DE FASE 2: NORMALIZACIÓN DE INTERFACES")
       print("=" * 60)

       checks = [
           check_all_tools_have_prefix,
           check_no_json_dumps,
           check_return_types,
           check_no_parameter_aliases,
           check_docstrings_complete,
           check_tests_pass
       ]

       results = [check() for check in checks]

       print("\n" + "=" * 60)
       if all(results):
           print("✅ FASE 2 COMPLETA Y VALIDADA")
           print("=" * 60)
           return 0
       else:
           print("❌ FASE 2 INCOMPLETA - Revisar errores arriba")
           print("=" * 60)
           return 1


   if __name__ == "__main__":
       sys.exit(main())
   ```

2. Ejecutar validación:
   ```bash
   uv run python scripts/validate_phase2.py
   ```

3. Corregir problemas encontrados

4. Actualizar CHANGELOG.md:
   ```markdown
   ## [Fase 2 Completada] - 2025-XX-XX

   ### Normalización de Interfaces
   - ✅ Todas las herramientas con prefijo `taiga_` (123+ herramientas)
   - ✅ Tipos de retorno normalizados (Dict/List[Dict])
   - ✅ Eliminados aliases de parámetros
   - ✅ Docstrings completos en formato Google
   - ✅ Guías de migración generadas

   ### Breaking Changes
   - Herramientas renombradas: `authenticate` → `taiga_authenticate`, etc.
   - Parámetros renombrados: `member/member_id` → `member_id`, etc.
   - Tipos de retorno: algunas herramientas ahora retornan Dict en lugar de str

   ### Documentación
   - Guía de migración de nombres de herramientas
   - Guía de migración de parámetros
   - Ejemplos actualizados en README y guia_uso
   ```

#### Tests Asociados

- [ ] Test 2.7.1: uv run bandit src/ pasa 100%
- [ ] Test 2.7.2: uv run ruff src/ tests/ pasa 100%
- [ ] Test 2.7.3: uv run mypy src/ tests/ pasa 100%
- [ ] Test 2.7.4: Script validate_phase2.py pasa completamente
- [ ] Test 2.7.5: Auditoría muestra 0 problemas
- [ ] Test 2.7.6: Todos los tests pasan
- [ ] Test 2.7.7: Servidor inicia correctamente

#### Criterios de Aceptación

- [ ] Script de validación pasa 100%
- [ ] bandit ejecutado sobre src/ sin errores
- [ ] mypy ejecutado sobre src/ tests/ sin errores
- [ ] ruff ejecutado sobre src/ tests/ sin errores
- [ ] CHANGELOG actualizado
- [ ] Guías de migración completas
- [ ] README actualizado con nueva nomenclatura

#### Archivos Afectados

- `scripts/validate_phase2.py` - **NUEVO**
- `CHANGELOG.md` - Actualizar
- `README.md` - Actualizar ejemplos
- `Documentacion/guia_migracion_fase2.md` - **NUEVO**

---

### Resumen de Fase 2

**Total de Tareas**: 7
**Total de Tests**: 40+
**Duración Estimada**: 2 semanas (80 horas)

**Entregables**:
- ✅ 123+ herramientas con prefijo `taiga_`
- ✅ Tipos de retorno consistentes
- ✅ Sin aliases de parámetros
- ✅ Docstrings completos
- ✅ Guías de migración

**Próxima Fase**: [Fase 3 - Optimizaciones](#fase-3-optimizaciones)

---

## Fase 3: Optimizaciones

**Duración**: 2 semanas (80 horas)
**Objetivo**: Mejorar rendimiento, eficiencia y experiencia de usuario
**Impacto**: MEDIO - Mejoras no bloqueantes pero significativas

### Resumen de la Fase

| Optimización | Problema | Solución | Impacto |
|--------------|----------|----------|---------|
| Caché de metadatos | Múltiples llamadas a `/projects/{id}` | Caché en memoria con TTL | -60% llamadas API |
| Paginación automática | Listas largas causan timeouts | Auto-paginación transparente | +50% confiabilidad |
| Rate limiting | Puede exceder límites de API | Throttling inteligente | Sin errores 429 |
| Pool de conexiones | Nueva conexión por request | Reutilizar conexiones HTTP | -30% latencia |
| Validación temprana | Errores tras llamada API | Validar antes de llamar | Mejor UX |

### Tareas de la Fase 3

---

### Tarea 3.1: Implementar Pool de Sesiones HTTP

**Problema**: Se crea/destruye cliente HTTP en cada llamada a la API
**Objetivo**: Reutilizar conexiones HTTP con pool de sesiones
**Prioridad**: ALTA
**Dependencias**: Tarea 1.2 (DI Container)
**Estimación**: 8 horas

#### Pasos de Implementación

1. Crear `src/infrastructure/http_session_pool.py`:
   ```python
   """Pool de sesiones HTTP reutilizables."""
   from contextlib import asynccontextmanager
   from typing import AsyncIterator, Optional
   import httpx

   class HTTPSessionPool:
       """Pool de sesiones HTTP con keep-alive y límites configurables."""

       def __init__(self, base_url: str, timeout: float = 30.0,
                    max_connections: int = 100, max_keepalive: int = 20):
           self.base_url = base_url
           self.timeout = timeout
           self.max_connections = max_connections
           self.max_keepalive = max_keepalive
           self._client: Optional[httpx.AsyncClient] = None

       async def start(self) -> None:
           """Inicializa el pool de conexiones."""
           if self._client is None:
               self._client = httpx.AsyncClient(
                   base_url=self.base_url,
                   timeout=httpx.Timeout(self.timeout),
                   limits=httpx.Limits(
                       max_connections=self.max_connections,
                       max_keepalive_connections=self.max_keepalive
                   )
               )

       async def stop(self) -> None:
           """Cierra todas las conexiones del pool."""
           if self._client:
               await self._client.aclose()
               self._client = None

       @asynccontextmanager
       async def session(self) -> AsyncIterator[httpx.AsyncClient]:
           """Obtiene una sesión del pool."""
           if self._client is None:
               await self.start()
           yield self._client
   ```

2. Integrar pool en `ApplicationContainer`:
   ```python
   session_pool = providers.Singleton(
       HTTPSessionPool,
       base_url=config.provided.taiga_api_url,
       timeout=config.provided.timeout
   )
   ```

3. Modificar `TaigaAPIClient` para usar el pool

4. Agregar lifecycle hooks para iniciar/parar pool

#### Tests Asociados

- [ ] Test 3.1.1: Pool se inicializa correctamente
- [ ] Test 3.1.2: Sesiones se reutilizan (verificar keep-alive)
- [ ] Test 3.1.3: Pool respeta límites de conexiones
- [ ] Test 3.1.4: Pool se cierra correctamente al finalizar
- [ ] Test 3.1.5: Múltiples requests concurrentes funcionan

#### Criterios de Aceptación

- [ ] Pool configurado con límites ajustables
- [ ] Conexiones HTTP se reutilizan (verificar con logs)
- [ ] Reducción de latencia >= 30% en requests consecutivos
- [ ] Tests de integración pasan
- [ ] Documentar configuración de pool en README

#### Archivos Afectados

- `src/infrastructure/http_session_pool.py` - **NUEVO** - Pool de sesiones
- `src/infrastructure/container.py` - Registrar pool en DI
- `src/taiga_client.py` - Modificar para usar pool
- `tests/integration/test_http_pool.py` - **NUEVO** - Tests de integración

---

### Tarea 3.2: Sistema de Caché para Metadatos

**Problema**: Múltiples llamadas redundantes a endpoints de metadata (filtros, atributos)
**Objetivo**: Cachear datos estáticos con TTL configurable
**Prioridad**: ALTA
**Dependencias**: Tarea 3.1
**Estimación**: 10 horas

#### Pasos de Implementación

1. Crear `src/infrastructure/cache.py`:
   ```python
   """Sistema de caché en memoria con TTL."""
   from datetime import datetime, timedelta
   from typing import Any, Dict, Optional, Callable
   from dataclasses import dataclass
   import asyncio

   @dataclass
   class CacheEntry:
       value: Any
       expires_at: datetime

       def is_expired(self) -> bool:
           return datetime.now() > self.expires_at

   class MemoryCache:
       """Caché en memoria con TTL y limpieza automática."""

       def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
           self.default_ttl = default_ttl  # segundos
           self.max_size = max_size
           self._cache: Dict[str, CacheEntry] = {}
           self._lock = asyncio.Lock()

       async def get(self, key: str) -> Optional[Any]:
           """Obtiene valor del caché si existe y no expiró."""
           async with self._lock:
               entry = self._cache.get(key)
               if entry and not entry.is_expired():
                   return entry.value
               elif entry:
                   del self._cache[key]
               return None

       async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
           """Guarda valor en caché con TTL."""
           async with self._lock:
               if len(self._cache) >= self.max_size:
                   await self._evict_expired()
               expires_at = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
               self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

       async def invalidate(self, pattern: str) -> int:
           """Invalida entradas que coincidan con el patrón."""
           async with self._lock:
               keys_to_delete = [k for k in self._cache if pattern in k]
               for key in keys_to_delete:
                   del self._cache[key]
               return len(keys_to_delete)
   ```

2. Crear `CachedTaigaClient` wrapper:
   ```python
   class CachedTaigaClient:
       """Cliente Taiga con cacheo inteligente."""

       CACHEABLE_ENDPOINTS = {
           'epic_filters': 3600,      # 1 hora
           'issue_filters': 3600,
           'project_modules': 1800,   # 30 min
           'custom_attributes': 3600,
       }

       def __init__(self, client: TaigaAPIClient, cache: MemoryCache):
           self.client = client
           self.cache = cache
   ```

3. Definir estrategia de cacheo por endpoint

4. Integrar en container de DI

5. Agregar métricas de hit/miss

#### Tests Asociados

- [ ] Test 3.2.1: Cache almacena y recupera valores
- [ ] Test 3.2.2: Entradas expiran después de TTL
- [ ] Test 3.2.3: Invalidación por patrón funciona
- [ ] Test 3.2.4: Cache respeta max_size
- [ ] Test 3.2.5: Llamadas cacheables no invocan API
- [ ] Test 3.2.6: Llamadas no cacheables siempre invocan API
- [ ] Test 3.2.7: Concurrencia segura (múltiples lecturas/escrituras)
- [ ] Test 3.2.8: Métricas de hit/miss correctas

#### Criterios de Aceptación

- [ ] Cache configurado con TTL por tipo de dato
- [ ] Reducción >= 60% de llamadas a endpoints de metadata
- [ ] Métricas de cache disponibles (hit rate)
- [ ] Invalidación manual disponible
- [ ] Tests unitarios y de integración pasan

#### Archivos Afectados

- `src/infrastructure/cache.py` - **NUEVO** - Sistema de caché
- `src/infrastructure/cached_client.py` - **NUEVO** - Wrapper con caché
- `src/infrastructure/container.py` - Registrar caché en DI
- `tests/unit/infrastructure/test_cache.py` - **NUEVO** - Tests unitarios

---

### Tarea 3.3: Paginación Automática Transparente

**Problema**: Listas largas causan timeouts, usuario debe paginar manualmente
**Objetivo**: Auto-paginación transparente que retorna todos los resultados
**Prioridad**: ALTA
**Dependencias**: Tarea 3.1
**Estimación**: 8 horas

#### Pasos de Implementación

1. Crear `src/infrastructure/pagination.py`:
   ```python
   """Sistema de paginación automática."""
   from typing import AsyncIterator, Dict, List, Any, Optional
   from dataclasses import dataclass

   @dataclass
   class PaginationConfig:
       page_size: int = 100
       max_pages: int = 50  # Límite de seguridad
       max_total_items: int = 5000

   class AutoPaginator:
       """Paginador automático para endpoints de lista."""

       def __init__(self, client: TaigaAPIClient, config: PaginationConfig):
           self.client = client
           self.config = config

       async def paginate(self, endpoint: str, params: Dict = None) -> List[Dict]:
           """Obtiene todos los items paginando automáticamente."""
           all_items = []
           page = 1
           params = params or {}

           while page <= self.config.max_pages:
               params['page'] = page
               params['page_size'] = self.config.page_size

               response = await self.client.get(endpoint, params=params)

               if not response.get('results'):
                   break

               all_items.extend(response['results'])

               if len(all_items) >= self.config.max_total_items:
                   break

               if not response.get('next'):
                   break

               page += 1

           return all_items

       async def paginate_lazy(self, endpoint: str, params: Dict = None
                              ) -> AsyncIterator[Dict]:
           """Itera sobre items paginando bajo demanda (lazy)."""
           # Implementación con yield para grandes datasets
   ```

2. Identificar endpoints que soportan paginación en Taiga

3. Modificar herramientas de lista para usar AutoPaginator

4. Agregar parámetro `auto_paginate` a herramientas (default: True)

#### Tests Asociados

- [ ] Test 3.3.1: Paginación obtiene todos los items
- [ ] Test 3.3.2: Respeta límite max_pages
- [ ] Test 3.3.3: Respeta límite max_total_items
- [ ] Test 3.3.4: Maneja endpoint sin paginación
- [ ] Test 3.3.5: Lazy pagination funciona correctamente
- [ ] Test 3.3.6: auto_paginate=False retorna solo primera página

#### Criterios de Aceptación

- [ ] Todas las herramientas de lista soportan auto-paginación
- [ ] Límites de seguridad configurables
- [ ] +50% confiabilidad en listas largas
- [ ] No hay timeouts en operaciones de lista
- [ ] Tests de integración pasan

#### Archivos Afectados

- `src/infrastructure/pagination.py` - **NUEVO** - Sistema de paginación
- `src/application/tools/*_tools.py` - Modificar herramientas de lista
- `tests/integration/test_pagination.py` - **NUEVO** - Tests de integración

---

### Tarea 3.4: Rate Limiting Inteligente

**Problema**: Puede exceder límites de API de Taiga causando errores 429
**Objetivo**: Throttling inteligente que previene errores de rate limit
**Prioridad**: ALTA
**Dependencias**: Tarea 3.1
**Estimación**: 8 horas

#### Pasos de Implementación

1. Crear `src/infrastructure/rate_limiter.py`:
   ```python
   """Rate limiter inteligente con token bucket."""
   import asyncio
   from datetime import datetime
   from typing import Optional

   class TokenBucketRateLimiter:
       """Rate limiter usando algoritmo token bucket."""

       def __init__(self, rate: float = 10.0, burst: int = 20):
           self.rate = rate  # tokens por segundo
           self.burst = burst  # capacidad máxima del bucket
           self.tokens = burst
           self.last_update = datetime.now()
           self._lock = asyncio.Lock()

       async def acquire(self, tokens: int = 1) -> float:
           """Adquiere tokens, esperando si es necesario."""
           async with self._lock:
               await self._refill()

               if self.tokens >= tokens:
                   self.tokens -= tokens
                   return 0.0

               wait_time = (tokens - self.tokens) / self.rate
               await asyncio.sleep(wait_time)
               await self._refill()
               self.tokens -= tokens
               return wait_time

       async def _refill(self) -> None:
           """Rellena tokens basado en tiempo transcurrido."""
           now = datetime.now()
           elapsed = (now - self.last_update).total_seconds()
           self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
           self.last_update = now

   class AdaptiveRateLimiter(TokenBucketRateLimiter):
       """Rate limiter que se adapta a respuestas 429."""

       async def on_rate_limit_response(self, retry_after: int) -> None:
           """Ajusta rate cuando recibe 429."""
           async with self._lock:
               self.rate *= 0.75  # Reduce rate 25%
               self.tokens = 0
               await asyncio.sleep(retry_after)
   ```

2. Integrar rate limiter en HTTPSessionPool

3. Configurar límites por tipo de operación (read vs write)

4. Agregar headers de rate limit a respuestas

#### Tests Asociados

- [ ] Test 3.4.1: Token bucket funciona correctamente
- [ ] Test 3.4.2: Requests se throttlean cuando bucket vacío
- [ ] Test 3.4.3: Rate limiter se adapta a 429
- [ ] Test 3.4.4: Burst permite ráfagas controladas
- [ ] Test 3.4.5: Sin errores 429 bajo carga controlada

#### Criterios de Aceptación

- [ ] Rate limiter configurado con token bucket
- [ ] Adaptación automática a respuestas 429
- [ ] Cero errores 429 en uso normal
- [ ] Métricas de throttling disponibles
- [ ] Tests de integración pasan

#### Archivos Afectados

- `src/infrastructure/rate_limiter.py` - **NUEVO** - Rate limiter
- `src/infrastructure/http_session_pool.py` - Integrar rate limiter
- `tests/unit/infrastructure/test_rate_limiter.py` - **NUEVO** - Tests

---

### Tarea 3.5: Validación Temprana de Parámetros

**Problema**: Errores se detectan tras llamada a API, desperdiciando recursos
**Objetivo**: Validar parámetros antes de llamar a la API
**Prioridad**: MEDIA
**Dependencias**: Tarea 1.3 (Entidades de Dominio)
**Estimación**: 6 horas

#### Pasos de Implementación

1. Crear `src/domain/validators.py`:
   ```python
   """Validadores de dominio."""
   from typing import Any, List, Optional
   from pydantic import BaseModel, field_validator, model_validator
   from src.domain.exceptions import ValidationError

   class ProjectCreateValidator(BaseModel):
       """Validador para creación de proyecto."""
       name: str
       description: Optional[str] = None
       is_private: bool = True

       @field_validator('name')
       @classmethod
       def name_not_empty(cls, v: str) -> str:
           if not v.strip():
               raise ValueError("El nombre del proyecto no puede estar vacío")
           if len(v) > 255:
               raise ValueError("El nombre no puede exceder 255 caracteres")
           return v.strip()

   class EpicCreateValidator(BaseModel):
       """Validador para creación de epic."""
       project_id: int
       subject: str
       color: Optional[str] = None

       @field_validator('project_id')
       @classmethod
       def project_id_positive(cls, v: int) -> int:
           if v <= 0:
               raise ValueError("project_id debe ser positivo")
           return v

       @field_validator('color')
       @classmethod
       def valid_color_format(cls, v: Optional[str]) -> Optional[str]:
           if v and not v.startswith('#'):
               raise ValueError("Color debe estar en formato hex (#RRGGBB)")
           return v
   ```

2. Crear validadores para cada tipo de operación

3. Integrar validación en tools ANTES de llamar use cases

4. Retornar errores claros y descriptivos

#### Tests Asociados

- [ ] Test 3.5.1: Validador rechaza nombre vacío
- [ ] Test 3.5.2: Validador rechaza ID negativo
- [ ] Test 3.5.3: Validador acepta datos válidos
- [ ] Test 3.5.4: Errores de validación son descriptivos
- [ ] Test 3.5.5: Validación ocurre antes de llamada API

#### Criterios de Aceptación

- [ ] Validadores para todas las operaciones de creación/actualización
- [ ] Errores de validación claros y en español
- [ ] API no se llama si validación falla
- [ ] Mejor UX con feedback inmediato
- [ ] Tests unitarios pasan

#### Archivos Afectados

- `src/domain/validators.py` - **NUEVO** - Validadores
- `src/application/tools/*_tools.py` - Usar validadores
- `tests/unit/domain/test_validators.py` - **NUEVO** - Tests

---

### Tarea 3.6: Sistema de Reintentos con Backoff Exponencial

**Problema**: Errores transitorios (timeout, red) causan fallos definitivos
**Objetivo**: Reintentos automáticos con backoff exponencial
**Prioridad**: MEDIA
**Dependencias**: Tarea 3.1
**Estimación**: 6 horas

#### Pasos de Implementación

1. Crear `src/infrastructure/retry.py`:
   ```python
   """Sistema de reintentos con backoff exponencial."""
   import asyncio
   from typing import Callable, TypeVar, Set, Type
   from functools import wraps
   import random

   T = TypeVar('T')

   class RetryConfig:
       def __init__(self,
                    max_retries: int = 3,
                    base_delay: float = 1.0,
                    max_delay: float = 60.0,
                    exponential_base: float = 2.0,
                    jitter: bool = True,
                    retryable_exceptions: Set[Type[Exception]] = None):
           self.max_retries = max_retries
           self.base_delay = base_delay
           self.max_delay = max_delay
           self.exponential_base = exponential_base
           self.jitter = jitter
           self.retryable_exceptions = retryable_exceptions or {
               TimeoutError, ConnectionError
           }

   def with_retry(config: RetryConfig = None):
       """Decorador para reintentos con backoff."""
       config = config or RetryConfig()

       def decorator(func: Callable[..., T]) -> Callable[..., T]:
           @wraps(func)
           async def wrapper(*args, **kwargs) -> T:
               last_exception = None
               for attempt in range(config.max_retries + 1):
                   try:
                       return await func(*args, **kwargs)
                   except tuple(config.retryable_exceptions) as e:
                       last_exception = e
                       if attempt < config.max_retries:
                           delay = min(
                               config.base_delay * (config.exponential_base ** attempt),
                               config.max_delay
                           )
                           if config.jitter:
                               delay *= (0.5 + random.random())
                           await asyncio.sleep(delay)
               raise last_exception
           return wrapper
       return decorator
   ```

2. Aplicar decorador a métodos del cliente HTTP

3. Configurar qué excepciones son retriables

4. Agregar logging de reintentos

#### Tests Asociados

- [ ] Test 3.6.1: Reintenta en error transitorio
- [ ] Test 3.6.2: No reintenta en error definitivo
- [ ] Test 3.6.3: Respeta max_retries
- [ ] Test 3.6.4: Backoff exponencial correcto
- [ ] Test 3.6.5: Jitter añade variabilidad
- [ ] Test 3.6.6: Éxito en segundo intento

#### Criterios de Aceptación

- [ ] Reintentos automáticos para errores transitorios
- [ ] Backoff exponencial con jitter
- [ ] Logging de cada reintento
- [ ] Configuración flexible
- [ ] Tests unitarios pasan

#### Archivos Afectados

- `src/infrastructure/retry.py` - **NUEVO** - Sistema de reintentos
- `src/taiga_client.py` - Aplicar decorador
- `tests/unit/infrastructure/test_retry.py` - **NUEVO** - Tests

---

### Tarea 3.7: Compresión de Respuestas HTTP

**Problema**: Respuestas grandes consumen ancho de banda innecesariamente
**Objetivo**: Habilitar compresión gzip en requests/responses
**Prioridad**: BAJA
**Dependencias**: Tarea 3.1
**Estimación**: 3 horas

#### Pasos de Implementación

1. Configurar headers de compresión en HTTPSessionPool:
   ```python
   default_headers = {
       'Accept-Encoding': 'gzip, deflate',
       'Content-Type': 'application/json'
   }
   ```

2. Verificar que httpx descomprime automáticamente

3. Agregar compresión a requests de body grande (POST/PUT)

4. Medir reducción de tamaño

#### Tests Asociados

- [ ] Test 3.7.1: Requests envían Accept-Encoding
- [ ] Test 3.7.2: Responses comprimidas se descomprimen
- [ ] Test 3.7.3: Bodies grandes se comprimen

#### Criterios de Aceptación

- [ ] Compresión habilitada por defecto
- [ ] Reducción >= 50% en tamaño de respuestas
- [ ] Sin impacto en funcionalidad
- [ ] Tests pasan

#### Archivos Afectados

- `src/infrastructure/http_session_pool.py` - Configurar compresión
- `tests/integration/test_compression.py` - **NUEVO** - Tests

---

### Tarea 3.8: Logging de Performance

**Problema**: No hay visibilidad de tiempos de respuesta ni bottlenecks
**Objetivo**: Logging estructurado de métricas de performance
**Prioridad**: MEDIA
**Dependencias**: Tarea 3.1
**Estimación**: 5 horas

#### Pasos de Implementación

1. Crear `src/infrastructure/logging.py`:
   ```python
   """Sistema de logging estructurado."""
   import logging
   import time
   from contextlib import contextmanager
   from typing import Optional
   from functools import wraps

   class PerformanceLogger:
       def __init__(self, logger: logging.Logger = None):
           self.logger = logger or logging.getLogger(__name__)

       @contextmanager
       def measure(self, operation: str, **context):
           """Context manager para medir duración de operaciones."""
           start = time.perf_counter()
           try:
               yield
           finally:
               duration_ms = (time.perf_counter() - start) * 1000
               self.logger.info(
                   f"[PERF] {operation}",
                   extra={
                       'operation': operation,
                       'duration_ms': duration_ms,
                       **context
                   }
               )

       def log_api_call(self, method: str, endpoint: str,
                        duration_ms: float, status_code: int):
           """Log específico para llamadas API."""
           self.logger.info(
               f"[API] {method} {endpoint} -> {status_code} ({duration_ms:.2f}ms)"
           )
   ```

2. Integrar logging en HTTPSessionPool

3. Agregar métricas por endpoint

4. Configurar formato de logs (JSON para producción)

#### Tests Asociados

- [ ] Test 3.8.1: Log de operación incluye duración
- [ ] Test 3.8.2: Log de API incluye método, endpoint, status
- [ ] Test 3.8.3: Formato JSON correcto
- [ ] Test 3.8.4: No impacta performance significativamente

#### Criterios de Aceptación

- [ ] Todas las llamadas API loggeadas con tiempos
- [ ] Formato configurable (text/JSON)
- [ ] Métricas agregables
- [ ] Overhead < 1ms por request
- [ ] Tests pasan

#### Archivos Afectados

- `src/infrastructure/logging.py` - **NUEVO** - Sistema de logging
- `src/infrastructure/http_session_pool.py` - Integrar logging
- `tests/unit/infrastructure/test_logging.py` - **NUEVO** - Tests

---

### Tarea 3.9: Métricas y Monitoreo

**Problema**: No hay métricas de uso, errores ni performance agregadas
**Objetivo**: Sistema de métricas para monitoreo y alertas
**Prioridad**: BAJA
**Dependencias**: Tarea 3.8
**Estimación**: 6 horas

#### Pasos de Implementación

1. Crear `src/infrastructure/metrics.py`:
   ```python
   """Sistema de métricas del servidor."""
   from dataclasses import dataclass, field
   from datetime import datetime
   from typing import Dict, List
   from collections import defaultdict
   import threading

   @dataclass
   class MetricsSnapshot:
       total_requests: int
       successful_requests: int
       failed_requests: int
       avg_response_time_ms: float
       cache_hit_rate: float
       requests_by_endpoint: Dict[str, int]
       errors_by_type: Dict[str, int]
       timestamp: datetime

   class MetricsCollector:
       """Recolector de métricas thread-safe."""

       def __init__(self):
           self._lock = threading.Lock()
           self._requests: List[Dict] = []
           self._errors: Dict[str, int] = defaultdict(int)
           self._cache_hits = 0
           self._cache_misses = 0

       def record_request(self, endpoint: str, method: str,
                          duration_ms: float, success: bool):
           with self._lock:
               self._requests.append({
                   'endpoint': endpoint,
                   'method': method,
                   'duration_ms': duration_ms,
                   'success': success,
                   'timestamp': datetime.now()
               })

       def record_cache_hit(self):
           with self._lock:
               self._cache_hits += 1

       def record_cache_miss(self):
           with self._lock:
               self._cache_misses += 1

       def get_snapshot(self) -> MetricsSnapshot:
           """Obtiene snapshot actual de métricas."""
           # Implementación...
   ```

2. Integrar recolector en componentes principales

3. Exponer endpoint de métricas (opcional)

4. Agregar alertas para thresholds

#### Tests Asociados

- [ ] Test 3.9.1: Métricas se registran correctamente
- [ ] Test 3.9.2: Snapshot refleja estado actual
- [ ] Test 3.9.3: Thread-safe bajo concurrencia
- [ ] Test 3.9.4: Cache hit rate se calcula correctamente

#### Criterios de Aceptación

- [ ] Métricas de requests, errores, cache recolectadas
- [ ] Snapshot disponible bajo demanda
- [ ] Thread-safe
- [ ] Documentación de métricas disponibles
- [ ] Tests pasan

#### Archivos Afectados

- `src/infrastructure/metrics.py` - **NUEVO** - Sistema de métricas
- `src/infrastructure/container.py` - Registrar collector
- `tests/unit/infrastructure/test_metrics.py` - **NUEVO** - Tests

---

### Tarea 3.10: Optimización de Consultas Batch

**Problema**: Operaciones bulk hacen llamadas individuales secuenciales
**Objetivo**: Optimizar operaciones batch con concurrencia controlada
**Prioridad**: MEDIA
**Dependencias**: Tarea 3.1, 3.4
**Estimación**: 6 horas

#### Pasos de Implementación

1. Crear `src/infrastructure/batch.py`:
   ```python
   """Sistema de operaciones batch optimizadas."""
   import asyncio
   from typing import List, Callable, TypeVar, Any
   from dataclasses import dataclass

   T = TypeVar('T')

   @dataclass
   class BatchConfig:
       max_concurrency: int = 5
       chunk_size: int = 10
       fail_fast: bool = False

   class BatchExecutor:
       """Ejecutor de operaciones batch con concurrencia controlada."""

       def __init__(self, config: BatchConfig = None):
           self.config = config or BatchConfig()

       async def execute(self,
                         items: List[Any],
                         operation: Callable[[Any], T]
                        ) -> List[T]:
           """Ejecuta operación para cada item con concurrencia controlada."""
           semaphore = asyncio.Semaphore(self.config.max_concurrency)
           results = []

           async def bounded_operation(item: Any) -> T:
               async with semaphore:
                   return await operation(item)

           tasks = [bounded_operation(item) for item in items]

           if self.config.fail_fast:
               results = await asyncio.gather(*tasks)
           else:
               results = await asyncio.gather(*tasks, return_exceptions=True)

           return results
   ```

2. Identificar operaciones bulk existentes

3. Refactorizar para usar BatchExecutor

4. Agregar reportes de progreso

#### Tests Asociados

- [ ] Test 3.10.1: Batch respeta max_concurrency
- [ ] Test 3.10.2: Resultados en orden correcto
- [ ] Test 3.10.3: fail_fast detiene en primer error
- [ ] Test 3.10.4: Sin fail_fast continúa tras errores
- [ ] Test 3.10.5: Performance mejor que secuencial

#### Criterios de Aceptación

- [ ] Operaciones bulk usan concurrencia controlada
- [ ] Respeta rate limiting
- [ ] +200% performance en bulk creates
- [ ] Errores manejados según configuración
- [ ] Tests pasan

#### Archivos Afectados

- `src/infrastructure/batch.py` - **NUEVO** - Sistema batch
- `src/application/tools/*_tools.py` - Usar BatchExecutor
- `tests/integration/test_batch.py` - **NUEVO** - Tests

---

## Fase 4: Testing Exhaustivo

**Duración**: 2 semanas (80 horas)
**Objetivo**: Cobertura >= 90% con tests de calidad
**Impacto**: ALTO - Garantiza confiabilidad

### Resumen de la Fase

| Tipo de Test | Estado Actual | Objetivo | Beneficio |
|--------------|---------------|----------|-----------|
| Unitarios Domain | Parcial | 100% | Validar lógica de negocio |
| Unitarios Application | Bajo | 95% | Validar casos de uso |
| Unitarios Infrastructure | Bajo | 90% | Validar implementaciones |
| Integración | Mínimo | 85% | Validar interacciones |
| E2E | Ninguno | Flujos críticos | Validar sistema completo |
| Performance | Ninguno | Básico | Detectar regresiones |

### Tareas de la Fase 4

---

### Tarea 4.1: Análisis de Cobertura Actual y Gaps

**Problema**: No hay visibilidad clara de qué código está testeado
**Objetivo**: Mapa completo de cobertura actual e identificación de gaps
**Prioridad**: CRÍTICA
**Dependencias**: Ninguna
**Estimación**: 4 horas

#### Pasos de Implementación

1. Ejecutar análisis de cobertura completo:
   ```bash
   uv run pytest --cov=src --cov-report=html --cov-report=term-missing
   ```

2. Generar reporte por módulo:
   ```
   src/domain/entities/     → X%
   src/domain/value_objects/ → X%
   src/application/use_cases/ → X%
   src/application/tools/   → X%
   src/infrastructure/      → X%
   ```

3. Identificar gaps críticos (código sin tests)

4. Priorizar gaps por impacto

5. Crear plan de testing detallado

#### Tests Asociados

- [ ] Test 4.1.1: Script de análisis ejecuta sin errores
- [ ] Test 4.1.2: Reporte HTML se genera correctamente

#### Criterios de Aceptación

- [ ] Reporte de cobertura actual generado
- [ ] Lista de gaps priorizada
- [ ] Plan de testing por módulo
- [ ] Baseline de cobertura establecido
- [ ] Documentado en Documentacion/testing_plan.md

#### Archivos Afectados

- `Documentacion/testing_plan.md` - **NUEVO** - Plan de testing
- `scripts/coverage_analysis.py` - **NUEVO** - Script de análisis
- `.coveragerc` - Configuración de coverage

---

### Tarea 4.2: Tests Unitarios para Entidades de Dominio

**Problema**: Entidades nuevas (Project, UserStory, Task, etc.) sin tests completos
**Objetivo**: 100% cobertura en entidades con casos edge
**Prioridad**: CRÍTICA
**Dependencias**: Tarea 1.3
**Estimación**: 8 horas

#### Pasos de Implementación

1. Crear estructura de tests:
   ```
   tests/unit/domain/entities/
   ├── __init__.py
   ├── test_base_entity.py
   ├── test_project.py
   ├── test_epic.py
   ├── test_user_story.py
   ├── test_task.py
   ├── test_issue.py
   ├── test_milestone.py
   ├── test_member.py
   └── test_wiki_page.py
   ```

2. Para cada entidad, testear:
   - Creación con datos válidos
   - Creación con datos inválidos (cada campo)
   - Validadores personalizados
   - Métodos de dominio
   - Igualdad y hash
   - Serialización (dict/json)

3. Ejemplo para Project:
   ```python
   class TestProject:
       def test_create_valid_project(self):
           project = Project(name="Test", is_private=True)
           assert project.name == "Test"

       def test_name_cannot_be_empty(self):
           with pytest.raises(ValidationError):
               Project(name="")

       def test_name_is_trimmed(self):
           project = Project(name="  Test  ")
           assert project.name == "Test"

       def test_tags_are_normalized(self):
           project = Project(name="Test", tags=["TAG1", "tag1", "TAG2"])
           assert project.tags == ["tag1", "tag2"]

       def test_activate_module(self):
           project = Project(name="Test", is_wiki_activated=False)
           project.activate_module('wiki')
           assert project.is_wiki_activated is True

       def test_equality_by_id(self):
           p1 = Project(name="A", id=1)
           p2 = Project(name="B", id=1)
           assert p1 == p2
   ```

#### Tests Asociados

- [ ] Test 4.2.1: BaseEntity tests (id, version, equality, hash)
- [ ] Test 4.2.2: Project tests (20+ casos)
- [ ] Test 4.2.3: Epic tests (15+ casos)
- [ ] Test 4.2.4: UserStory tests (20+ casos)
- [ ] Test 4.2.5: Task tests (15+ casos)
- [ ] Test 4.2.6: Issue tests (20+ casos)
- [ ] Test 4.2.7: Milestone tests (10+ casos)
- [ ] Test 4.2.8: Member tests (10+ casos)
- [ ] Test 4.2.9: WikiPage tests (10+ casos)

#### Criterios de Aceptación

- [ ] 100% cobertura en src/domain/entities/
- [ ] Casos edge documentados
- [ ] Tests ejecutan en < 5 segundos
- [ ] Sin mocks (tests puros de dominio)
- [ ] Todos los tests pasan

#### Archivos Afectados

- `tests/unit/domain/entities/*.py` - Tests para cada entidad
- `tests/unit/domain/entities/conftest.py` - Fixtures compartidos

---

### Tarea 4.3: Tests Unitarios para Value Objects

**Problema**: Value objects sin tests de inmutabilidad y validación
**Objetivo**: 100% cobertura en value objects
**Prioridad**: ALTA
**Dependencias**: Tarea 1.3
**Estimación**: 4 horas

#### Pasos de Implementación

1. Crear tests para cada value object:
   ```
   tests/unit/domain/value_objects/
   ├── __init__.py
   ├── test_email.py
   ├── test_auth_token.py
   ├── test_project_slug.py
   └── test_status.py
   ```

2. Testear características de value objects:
   - Inmutabilidad (frozen)
   - Validación de formato
   - Igualdad por valor
   - Representación string

3. Ejemplo para Email:
   ```python
   class TestEmail:
       def test_valid_email(self):
           email = Email("user@example.com")
           assert email.value == "user@example.com"

       def test_invalid_email_format(self):
           with pytest.raises(ValueError):
               Email("not-an-email")

       def test_email_is_immutable(self):
           email = Email("user@example.com")
           with pytest.raises(AttributeError):
               email.value = "other@example.com"

       def test_equality_by_value(self):
           e1 = Email("user@example.com")
           e2 = Email("user@example.com")
           assert e1 == e2
   ```

#### Tests Asociados

- [ ] Test 4.3.1: Email validation y inmutabilidad
- [ ] Test 4.3.2: AuthToken validation y seguridad
- [ ] Test 4.3.3: ProjectSlug format y normalización
- [ ] Test 4.3.4: Status enum y transiciones

#### Criterios de Aceptación

- [ ] 100% cobertura en src/domain/value_objects/
- [ ] Inmutabilidad verificada
- [ ] Validaciones robustas
- [ ] Tests ejecutan en < 2 segundos
- [ ] Todos los tests pasan

#### Archivos Afectados

- `tests/unit/domain/value_objects/*.py` - Tests para cada VO

---

### Tarea 4.4: Tests Unitarios para Use Cases

**Problema**: Use cases con cobertura baja y sin casos de error
**Objetivo**: 95% cobertura en use cases con mocks
**Prioridad**: CRÍTICA
**Dependencias**: Tarea 1.5
**Estimación**: 12 horas

#### Pasos de Implementación

1. Crear estructura de tests:
   ```
   tests/unit/application/use_cases/
   ├── __init__.py
   ├── conftest.py          # Mocks comunes de repositorios
   ├── test_project_use_cases.py
   ├── test_epic_use_cases.py
   ├── test_userstory_use_cases.py
   ├── test_task_use_cases.py
   ├── test_issue_use_cases.py
   └── ...
   ```

2. Para cada use case, testear:
   - Caso exitoso (happy path)
   - Casos de error (not found, validation, permissions)
   - Interacción correcta con repositorio (mock)

3. Ejemplo para EpicUseCases:
   ```python
   class TestEpicUseCases:
       @pytest.fixture
       def mock_repository(self):
           return Mock(spec=EpicRepository)

       @pytest.fixture
       def use_cases(self, mock_repository):
           return EpicUseCases(repository=mock_repository)

       async def test_get_epic_success(self, use_cases, mock_repository):
           mock_repository.get_by_id.return_value = Epic(id=1, subject="Test")
           result = await use_cases.get_epic(epic_id=1, auth_token="token")
           assert result.id == 1
           mock_repository.get_by_id.assert_called_once_with(1, "token")

       async def test_get_epic_not_found(self, use_cases, mock_repository):
           mock_repository.get_by_id.return_value = None
           with pytest.raises(EpicNotFoundError):
               await use_cases.get_epic(epic_id=999, auth_token="token")

       async def test_create_epic_validates_input(self, use_cases, mock_repository):
           with pytest.raises(ValidationError):
               await use_cases.create_epic(
                   project_id=-1,  # Inválido
                   subject="",    # Inválido
                   auth_token="token"
               )
   ```

#### Tests Asociados

- [ ] Test 4.4.1: ProjectUseCases (CRUD + módulos)
- [ ] Test 4.4.2: EpicUseCases (CRUD + related stories)
- [ ] Test 4.4.3: UserStoryUseCases (CRUD + attachments)
- [ ] Test 4.4.4: TaskUseCases (CRUD + bulk)
- [ ] Test 4.4.5: IssueUseCases (CRUD + voting + watching)
- [ ] Test 4.4.6: MilestoneUseCases (CRUD + stats)
- [ ] Test 4.4.7: WikiUseCases (CRUD + attachments)
- [ ] Test 4.4.8: MembershipUseCases (CRUD)

#### Criterios de Aceptación

- [ ] 95% cobertura en src/application/use_cases/
- [ ] Todos los casos de error testeados
- [ ] Mocks verifican llamadas correctas
- [ ] Tests aislados (sin dependencias externas)
- [ ] Tests ejecutan en < 10 segundos

#### Archivos Afectados

- `tests/unit/application/use_cases/*.py` - Tests para cada módulo
- `tests/unit/application/use_cases/conftest.py` - Fixtures de mocks

---

### Tarea 4.5: Tests Unitarios para Repository Implementations

**Problema**: Implementaciones de repositorio sin tests de mapeo
**Objetivo**: 90% cobertura con tests de serialización/deserialización
**Prioridad**: ALTA
**Dependencias**: Tarea 1.6
**Estimación**: 10 horas

#### Pasos de Implementación

1. Crear estructura de tests:
   ```
   tests/unit/infrastructure/repositories/
   ├── __init__.py
   ├── conftest.py          # Mock de TaigaAPIClient
   ├── test_project_repository_impl.py
   ├── test_epic_repository_impl.py
   └── ...
   ```

2. Testear:
   - Mapeo de respuesta API a entidad
   - Mapeo de entidad a request API
   - Manejo de campos opcionales
   - Manejo de errores HTTP

3. Ejemplo:
   ```python
   class TestEpicRepositoryImpl:
       @pytest.fixture
       def mock_client(self):
           return AsyncMock(spec=TaigaAPIClient)

       @pytest.fixture
       def repository(self, mock_client):
           return EpicRepositoryImpl(client=mock_client)

       async def test_get_by_id_maps_response_to_entity(
           self, repository, mock_client
       ):
           mock_client.get.return_value = {
               "id": 1,
               "subject": "Epic Title",
               "color": "#FF0000",
               "project": 42
           }
           epic = await repository.get_by_id(1, "token")
           assert isinstance(epic, Epic)
           assert epic.id == 1
           assert epic.subject == "Epic Title"

       async def test_create_maps_entity_to_request(
           self, repository, mock_client
       ):
           epic = Epic(subject="New Epic", color="#00FF00", project_id=42)
           await repository.create(epic, "token")
           mock_client.post.assert_called_once_with(
               "/epics",
               data={"subject": "New Epic", "color": "#00FF00", "project": 42},
               auth_token="token"
           )
   ```

#### Tests Asociados

- [ ] Test 4.5.1: ProjectRepositoryImpl mapeos
- [ ] Test 4.5.2: EpicRepositoryImpl mapeos
- [ ] Test 4.5.3: UserStoryRepositoryImpl mapeos
- [ ] Test 4.5.4: TaskRepositoryImpl mapeos
- [ ] Test 4.5.5: IssueRepositoryImpl mapeos
- [ ] Test 4.5.6: MilestoneRepositoryImpl mapeos
- [ ] Test 4.5.7: WikiRepositoryImpl mapeos

#### Criterios de Aceptación

- [ ] 90% cobertura en src/infrastructure/repositories/
- [ ] Mapeos bidireccionales testeados
- [ ] Campos opcionales manejados
- [ ] Errores HTTP propagados correctamente
- [ ] Tests ejecutan en < 8 segundos

#### Archivos Afectados

- `tests/unit/infrastructure/repositories/*.py` - Tests por repositorio

---

### Tarea 4.6: Tests de Integración para Tools

**Problema**: Tools no testeados en contexto real de FastMCP
**Objetivo**: Validar registro y ejecución de herramientas
**Prioridad**: ALTA
**Dependencias**: Tarea 2.1
**Estimación**: 8 horas

#### Pasos de Implementación

1. Crear estructura de tests:
   ```
   tests/integration/tools/
   ├── __init__.py
   ├── conftest.py          # MCP server de test
   ├── test_auth_tools_integration.py
   ├── test_project_tools_integration.py
   └── ...
   ```

2. Testear:
   - Registro correcto de herramientas
   - Nombres de herramientas correctos (prefijo `taiga_`)
   - Parámetros correctamente tipados
   - Respuestas en formato correcto

3. Ejemplo:
   ```python
   class TestProjectToolsIntegration:
       @pytest.fixture
       async def mcp_client(self):
           """Cliente MCP de test."""
           # Configurar servidor MCP de test
           server = await create_test_mcp_server()
           return server

       async def test_tools_registered_with_prefix(self, mcp_client):
           tools = await mcp_client.list_tools()
           project_tools = [t for t in tools if 'project' in t.name]
           for tool in project_tools:
               assert tool.name.startswith('taiga_')

       async def test_create_project_returns_dict(self, mcp_client):
           result = await mcp_client.call_tool(
               'taiga_create_project',
               {'name': 'Test Project', 'auth_token': 'test'}
           )
           assert isinstance(result, dict)
           assert 'id' in result
   ```

#### Tests Asociados

- [ ] Test 4.6.1: AuthTools integración
- [ ] Test 4.6.2: ProjectTools integración
- [ ] Test 4.6.3: EpicTools integración
- [ ] Test 4.6.4: UserStoryTools integración
- [ ] Test 4.6.5: TaskTools integración
- [ ] Test 4.6.6: IssueTools integración

#### Criterios de Aceptación

- [ ] Todas las herramientas se registran correctamente
- [ ] Nombres siguen convención `taiga_*`
- [ ] Respuestas tienen formato consistente
- [ ] Errores se manejan correctamente
- [ ] Tests ejecutan en < 30 segundos

#### Archivos Afectados

- `tests/integration/tools/*.py` - Tests de integración
- `tests/integration/tools/conftest.py` - Fixtures de MCP

---

### Tarea 4.7: Tests de Integración para API Client

**Problema**: Cliente API no testeado contra Taiga real/mock
**Objetivo**: Validar interacción con API de Taiga
**Prioridad**: ALTA
**Dependencias**: Tarea 3.1
**Estimación**: 8 horas

#### Pasos de Implementación

1. Configurar servidor mock de Taiga para tests:
   ```python
   # tests/integration/mocks/taiga_mock_server.py
   from aiohttp import web

   class TaigaMockServer:
       def __init__(self):
           self.app = web.Application()
           self._setup_routes()

       def _setup_routes(self):
           self.app.router.add_post('/api/v1/auth', self._auth_handler)
           self.app.router.add_get('/api/v1/projects', self._list_projects)
           # ... más endpoints
   ```

2. Testear:
   - Autenticación
   - CRUD de cada recurso
   - Manejo de errores HTTP
   - Rate limiting
   - Paginación

#### Tests Asociados

- [ ] Test 4.7.1: Autenticación exitosa
- [ ] Test 4.7.2: Token refresh en 401
- [ ] Test 4.7.3: Manejo de 404
- [ ] Test 4.7.4: Manejo de 429 (rate limit)
- [ ] Test 4.7.5: Paginación automática
- [ ] Test 4.7.6: Timeout y reintentos

#### Criterios de Aceptación

- [ ] Mock server cubre endpoints principales
- [ ] Todos los códigos de error manejados
- [ ] Tests pueden ejecutar offline
- [ ] Tests ejecutan en < 20 segundos

#### Archivos Afectados

- `tests/integration/mocks/taiga_mock_server.py` - **NUEVO**
- `tests/integration/test_taiga_client.py` - Tests de cliente

---

### Tarea 4.8: Tests E2E para Flujos Completos

**Problema**: Sin tests que validen flujos de usuario completos
**Objetivo**: Validar flujos críticos end-to-end
**Prioridad**: MEDIA
**Dependencias**: Tarea 4.6, 4.7
**Estimación**: 10 horas

#### Pasos de Implementación

1. Identificar flujos críticos:
   - Autenticación → Crear proyecto → Crear epic → Crear user story
   - Listar proyectos → Obtener detalles → Listar epics
   - Crear issue → Asignar → Cambiar estado → Cerrar

2. Crear tests E2E:
   ```python
   class TestE2EProjectWorkflow:
       """Tests E2E para flujo completo de proyecto."""

       async def test_complete_project_workflow(self, mcp_client):
           # 1. Autenticar
           auth_result = await mcp_client.call_tool(
               'taiga_authenticate',
               {'username': 'test', 'password': 'test'}
           )
           token = auth_result['auth_token']

           # 2. Crear proyecto
           project = await mcp_client.call_tool(
               'taiga_create_project',
               {'name': 'E2E Test Project', 'auth_token': token}
           )
           project_id = project['id']

           # 3. Crear epic
           epic = await mcp_client.call_tool(
               'taiga_create_epic',
               {'project_id': project_id, 'subject': 'E2E Epic', 'auth_token': token}
           )
           epic_id = epic['id']

           # 4. Crear user story vinculada
           story = await mcp_client.call_tool(
               'taiga_create_userstory',
               {
                   'project_id': project_id,
                   'subject': 'E2E Story',
                   'auth_token': token
               }
           )

           # 5. Verificar todo creado
           project_detail = await mcp_client.call_tool(
               'taiga_get_project',
               {'project_id': project_id, 'auth_token': token}
           )
           assert project_detail['name'] == 'E2E Test Project'

           # 6. Cleanup
           await mcp_client.call_tool(
               'taiga_delete_project',
               {'project_id': project_id, 'auth_token': token}
           )
   ```

#### Tests Asociados

- [ ] Test 4.8.1: Flujo completo de proyecto
- [ ] Test 4.8.2: Flujo completo de sprint (milestone)
- [ ] Test 4.8.3: Flujo completo de issue tracking
- [ ] Test 4.8.4: Flujo de wiki y documentación
- [ ] Test 4.8.5: Flujo de gestión de equipo

#### Criterios de Aceptación

- [ ] Flujos críticos cubiertos
- [ ] Tests usan datos de test aislados
- [ ] Cleanup automático tras cada test
- [ ] Tests ejecutan en < 60 segundos
- [ ] Documentación de flujos testeados

#### Archivos Afectados

- `tests/e2e/*.py` - **NUEVO** - Tests E2E
- `tests/e2e/conftest.py` - Fixtures E2E

---

### Tarea 4.9: Tests de Performance y Stress

**Problema**: Sin visibilidad de límites de performance
**Objetivo**: Establecer baselines y detectar regresiones
**Prioridad**: BAJA
**Dependencias**: Tarea 4.7
**Estimación**: 6 horas

#### Pasos de Implementación

1. Crear tests de performance:
   ```python
   # tests/performance/test_throughput.py
   import pytest
   import time

   class TestPerformance:
       @pytest.mark.performance
       async def test_list_projects_performance(self, mcp_client, auth_token):
           """List projects debe responder en < 500ms."""
           start = time.perf_counter()
           await mcp_client.call_tool(
               'taiga_list_projects',
               {'auth_token': auth_token}
           )
           duration = time.perf_counter() - start
           assert duration < 0.5, f"Demasiado lento: {duration}s"

       @pytest.mark.performance
       async def test_concurrent_requests(self, mcp_client, auth_token):
           """Soporta 10 requests concurrentes."""
           import asyncio
           tasks = [
               mcp_client.call_tool('taiga_list_projects', {'auth_token': auth_token})
               for _ in range(10)
           ]
           start = time.perf_counter()
           results = await asyncio.gather(*tasks)
           duration = time.perf_counter() - start
           assert all(r is not None for r in results)
           assert duration < 5.0  # 10 requests en < 5 segundos
   ```

2. Crear tests de stress:
   ```python
   @pytest.mark.stress
   async def test_high_volume_creates(self, mcp_client, auth_token, project_id):
       """Crear 100 tasks sin errores."""
       for i in range(100):
           await mcp_client.call_tool(
               'taiga_create_task',
               {
                   'project_id': project_id,
                   'subject': f'Stress Test Task {i}',
                   'auth_token': auth_token
               }
           )
   ```

#### Tests Asociados

- [ ] Test 4.9.1: Latencia de operaciones CRUD
- [ ] Test 4.9.2: Throughput de requests concurrentes
- [ ] Test 4.9.3: Stress test de creación masiva
- [ ] Test 4.9.4: Memory leak detection
- [ ] Test 4.9.5: Connection pool bajo carga

#### Criterios de Aceptación

- [ ] Baselines de performance establecidos
- [ ] Tests de stress pasan sin errores
- [ ] Métricas documentadas
- [ ] CI puede ejecutar tests de performance
- [ ] Alertas para regresiones > 20%

#### Archivos Afectados

- `tests/performance/*.py` - **NUEVO** - Tests de performance
- `pytest.ini` - Markers para performance/stress

---

### Tarea 4.10: Tests de Regresión y Snapshot

**Problema**: Cambios pueden romper compatibilidad sin detectarlo
**Objetivo**: Detectar cambios inesperados en outputs
**Prioridad**: MEDIA
**Dependencias**: Tarea 4.6
**Estimación**: 4 horas

#### Pasos de Implementación

1. Configurar pytest-snapshot:
   ```bash
   uv add --dev pytest-snapshot
   ```

2. Crear tests de snapshot para respuestas:
   ```python
   class TestSnapshotResponses:
       def test_project_response_format(self, snapshot, sample_project):
           """Formato de respuesta de proyecto no cambia."""
           response = format_project_response(sample_project)
           snapshot.assert_match(response, 'project_response.json')

       def test_tool_schema(self, snapshot):
           """Schema de herramientas no cambia."""
           tools = get_registered_tools()
           schemas = {t.name: t.schema for t in tools}
           snapshot.assert_match(schemas, 'tool_schemas.json')
   ```

3. Crear snapshots iniciales

4. Integrar en CI

#### Tests Asociados

- [ ] Test 4.10.1: Snapshot de respuestas de proyecto
- [ ] Test 4.10.2: Snapshot de respuestas de epic
- [ ] Test 4.10.3: Snapshot de schemas de herramientas
- [ ] Test 4.10.4: Snapshot de mensajes de error

#### Criterios de Aceptación

- [ ] Snapshots para formatos críticos
- [ ] CI falla si snapshot cambia sin actualizar
- [ ] Proceso para actualizar snapshots documentado
- [ ] Tests ejecutan en < 5 segundos

#### Archivos Afectados

- `tests/regression/*.py` - **NUEVO** - Tests de regresión
- `tests/regression/snapshots/` - Snapshots

---

### Tarea 4.11: Configuración de CI/CD para Tests

**Problema**: Tests no ejecutan automáticamente en cada commit
**Objetivo**: Pipeline CI completo con tests y cobertura
**Prioridad**: ALTA
**Dependencias**: Tarea 4.1
**Estimación**: 6 horas

#### Pasos de Implementación

1. Crear `.github/workflows/tests.yml`:
   ```yaml
   name: Tests
   on: [push, pull_request]

   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4

         - name: Install uv
           uses: astral-sh/setup-uv@v4

         - name: Install dependencies
           run: uv sync --all-extras

         - name: Run linting
           run: uv run ruff check src/ tests/

         - name: Run type checking
           run: uv run mypy src/

         - name: Run unit tests
           run: uv run pytest tests/unit/ -v --cov=src --cov-report=xml

         - name: Run integration tests
           run: uv run pytest tests/integration/ -v

         - name: Upload coverage
           uses: codecov/codecov-action@v4
           with:
             file: coverage.xml

     performance:
       runs-on: ubuntu-latest
       if: github.event_name == 'pull_request'
       steps:
         - uses: actions/checkout@v4
         - name: Run performance tests
           run: uv run pytest tests/performance/ -v -m performance
   ```

2. Configurar badges en README

3. Configurar branch protection rules

#### Tests Asociados

- [ ] Test 4.11.1: Workflow ejecuta en GitHub Actions
- [ ] Test 4.11.2: Cobertura se reporta a Codecov
- [ ] Test 4.11.3: PR bloqueado si tests fallan

#### Criterios de Aceptación

- [ ] CI ejecuta en cada push/PR
- [ ] Tests unitarios obligatorios para merge
- [ ] Cobertura visible en Codecov
- [ ] Tiempo de CI < 10 minutos
- [ ] Documentación de CI en README

#### Archivos Afectados

- `.github/workflows/tests.yml` - **NUEVO** - Workflow de CI
- `README.md` - Badges de CI/coverage

---

### Tarea 4.12: Suite de Validación Continua

**Problema**: Sin validación automática de calidad de tests
**Objetivo**: Métricas y gates de calidad de testing
**Prioridad**: MEDIA
**Dependencias**: Tarea 4.11
**Estimación**: 4 horas

#### Pasos de Implementación

1. Configurar mutation testing (opcional):
   ```bash
   uv add --dev mutmut
   ```

2. Crear script de validación:
   ```python
   # scripts/validate_tests.py
   import subprocess
   import sys

   def main():
       # 1. Verificar cobertura mínima
       result = subprocess.run([
           'uv', 'run', 'pytest', '--cov=src',
           '--cov-fail-under=90', '-q'
       ])
       if result.returncode != 0:
           print("❌ Cobertura < 90%")
           sys.exit(1)

       # 2. Verificar que no hay tests skippeados sin razón
       # 3. Verificar que tests ejecutan en tiempo razonable
       # 4. Verificar que no hay tests flaky

       print("✅ Suite de validación pasó")
   ```

3. Integrar en pre-commit

4. Documentar estándares de testing

#### Tests Asociados

- [ ] Test 4.12.1: Script de validación ejecuta
- [ ] Test 4.12.2: Detecta cobertura insuficiente
- [ ] Test 4.12.3: Detecta tests lentos

#### Criterios de Aceptación

- [ ] Validación ejecuta en pre-commit
- [ ] Cobertura mínima 90% enforced
- [ ] Estándares de testing documentados
- [ ] Métricas de calidad de tests visibles

#### Archivos Afectados

- `scripts/validate_tests.py` - **NUEVO** - Script de validación
- `.pre-commit-config.yaml` - Agregar validación
- `Documentacion/testing_standards.md` - **NUEVO** - Estándares

---

## Fase 5: Documentación

**Duración**: 1 semana (40 horas)
**Objetivo**: Documentación completa y profesional
**Impacto**: ALTO - Facilita adopción y mantenimiento

(Continúa con las tareas 5.1 a 5.10...)

---

## 8. Matriz de Trazabilidad

| Problema (mejoras_taiga.md) | Fase | Tarea(s) | Tests | Estado |
|------------------------------|------|----------|-------|--------|
| A1: Arquitectura dual | 1 | 1.1-1.10 | 35 | Pendiente |
| A2: DI manual | 1 | 1.2 | 5 | Pendiente |
| A3: Sin separación capas | 1 | 1.3-1.7 | 25 | Pendiente |
| C1: Nombres inconsistentes | 2 | 2.2 | 5 | Pendiente |
| C2: Tipos de retorno mixtos | 2 | 2.3 | 6 | Pendiente |
| C3: Aliases de parámetros | 2 | 2.4 | 4 | Pendiente |
| I1: Sin caché | 3 | 3.1 | 8 | Pendiente |
| I2: Sin paginación automática | 3 | 3.2 | 6 | Pendiente |
| I3: Sin rate limiting | 3 | 3.3 | 5 | Pendiente |
| I4: Pool de conexiones | 3 | 3.4 | 4 | Pendiente |
| T1: Cobertura baja | 4 | 4.1-4.12 | 150+ | Pendiente |
| T2: Tests frágiles | 4 | 4.5-4.8 | 30 | Pendiente |
| CF1: Config duplicada | 1 | 1.9 | 3 | Pendiente |
| CF2: Validación débil | 1 | 1.3 | 5 | Pendiente |

---

## 9. Cronograma y Recursos

### Cronograma Visual

```
Semana 1-3: FASE 1 - Arquitectura DDD
├── Semana 1: Setup + Domain Layer (Tareas 1.1-1.4)
├── Semana 2: Application Layer + Infrastructure (Tareas 1.5-1.7)
└── Semana 3: Refactorización + Validación (Tareas 1.8-1.10)

Semana 4-5: FASE 2 - Normalización
├── Semana 4: Auditoría + Nombres + Tipos (Tareas 2.1-2.3)
└── Semana 5: Parámetros + Docs + Validación (Tareas 2.4-2.7)

Semana 6-7: FASE 3 - Optimizaciones
├── Semana 6: Caché + Paginación + Rate Limiting (Tareas 3.1-3.3)
└── Semana 7: Pool + Validación + Métricas (Tareas 3.4-3.7)

Semana 8-9: FASE 4 - Testing
├── Semana 8: Tests unitarios + integración (Tareas 4.1-4.6)
└── Semana 9: Tests E2E + Performance + Validación (Tareas 4.7-4.12)

Semana 10: FASE 5 - Documentación
└── Semana 10: README + Guías + ADRs + Diagramas (Tareas 5.1-5.10)
```

### Recursos Necesarios

**Humanos**:
- 1 desarrollador backend senior (Python/DDD)
- 0.5 QA engineer (para Fase 4)
- 0.25 technical writer (para Fase 5)

**Herramientas**:
- IDE con soporte Python (VSCode/PyCharm)
- Acceso a instancia de Taiga (staging/desarrollo)
- CI/CD configurado (GitHub Actions / GitLab CI)

### Hitos Críticos

| Hito | Fecha | Entregable | Criterio de Éxito |
|------|-------|------------|-------------------|
| H1: Arquitectura DDD | Fin Semana 3 | Código DDD funcional | Fase 1 validada |
| H2: Normalización | Fin Semana 5 | 123+ tools normalizados | Fase 2 validada |
| H3: Optimizaciones | Fin Semana 7 | Rendimiento mejorado | Fase 3 validada |
| H4: Testing Completo | Fin Semana 9 | Cobertura >= 90% | Fase 4 validada |
| H5: Documentación | Fin Semana 10 | Docs publicadas | Fase 5 validada |

---

## 10. Criterios de Aceptación

### Criterios Globales (Todo el Proyecto)

- [ ] **CA1**: Cobertura de tests >= 90% en todas las capas
- [ ] **CA2**: Ruff check pasa sin errores
- [ ] **CA3**: Mypy pasa con máximo 5 warnings
- [ ] **CA4**: Todas las herramientas con prefijo `taiga_`
- [ ] **CA5**: Tipos de retorno consistentes (Dict/List[Dict])
- [ ] **CA6**: Sin código duplicado (arquitectura legacy eliminada)
- [ ] **CA7**: Documentación completa (README + guia_uso + ADRs)
- [ ] **CA8**: Servidor inicia sin errores
- [ ] **CA9**: Suite de tests se ejecuta en < 2 minutos
- [ ] **CA10**: Sin TODOs ni FIXMEs en código de producción

### Criterios por Fase

**Fase 1**:
- [ ] Script validate_phase1.py pasa 100%
- [ ] Arquitectura DDD implementada completamente
- [ ] Sistema de DI funcional
- [ ] Cobertura >= 80%

**Fase 2**:
- [ ] Script validate_phase2.py pasa 100%
- [ ] Auditoría muestra 0 problemas
- [ ] Guías de migración generadas

**Fase 3**:
- [ ] Script validate_phase3.py pasa 100%
- [ ] Benchmarks muestran mejora >= 30%
- [ ] Sin errores 429 en tests de carga

**Fase 4**:
- [ ] Cobertura >= 90%
- [ ] Tests E2E pasan contra Taiga staging
- [ ] Mutation testing score >= 80%

**Fase 5**:
- [ ] README completo y actualizado
- [ ] guia_uso.md exhaustiva
- [ ] ADRs documentados
- [ ] Diagramas actualizados

---

## Apéndices

### A. Glosario de Términos Técnicos

- **DDD (Domain-Driven Design)**: Arquitectura enfocada en el dominio de negocio
- **DI (Dependency Injection)**: Patrón para gestionar dependencias automáticamente
- **DTO (Data Transfer Object)**: Objeto para transferir datos entre capas
- **TTL (Time To Live)**: Tiempo de vida de un dato en caché
- **Rate Limiting**: Control de frecuencia de peticiones
- **E2E (End-to-End)**: Tests que cubren flujo completo del usuario

### B. Referencias

- [Documento de Mejoras](mejoras_taiga.md)
- [Documentación de FastMCP](../Documentacion/fastmcp.md)
- [Documentación de Taiga API](../Documentacion/taiga-explicacion.md)
- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

### C. Comandos Útiles

```bash
# Ejecutar tests
uv run pytest tests/ -v

# Ejecutar tests con cobertura
uv run pytest tests/ --cov=src --cov-report=html

# Linting
uv run ruff check src/ tests/ --fix

# Formatting
uv run ruff format src/ tests/

# Type checking
uv run mypy src/

# Ejecutar servidor
uv run python src/server.py

# Ejecutar auditoría de tools
uv run python scripts/audit_mcp_tools.py

# Validar fase actual
uv run python scripts/validate_phase1.py  # o phase2, phase3, etc.
```

---

**FIN DEL PLAN DETALLADO DE IMPLEMENTACIÓN**

Este plan cubre las primeras 2 fases completas. Las fases 3, 4 y 5 se desarrollarán en detalle después de aprobar las primeras fases o bajo demanda.
