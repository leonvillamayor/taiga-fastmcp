# Decisiones de Diseño DDD - Taiga MCP Server

## Fecha: 2025-11-30

## Estado Actual del Proyecto

### Tests Pasando
- **Value Objects (Domain Layer)**: 14/14 VERDE ✅
- **Total**: 14/96 tests pasando (14.6%)
- **Cobertura**: Aún no alcanzada (objetivo: >=80%)

### Estructura Implementada

```
src/taiga_mcp_server/
├── domain/
│   ├── value_objects/
│   │   ├── project_id.py ✅
│   │   ├── email.py ✅
│   │   ├── project_slug.py ✅
│   │   └── userstory_ref.py ✅
│   ├── entities/
│   │   ├── project.py (pendiente)
│   │   └── userstory.py (pendiente)
│   └── exceptions/ (pendiente)
├── application/
│   └── use_cases/
│       └── create_project_use_case.py (pendiente)
└── infrastructure/
    ├── config/
    │   └── settings.py (pendiente)
    ├── taiga_client/
    │   ├── client.py (pendiente)
    │   └── exceptions.py (pendiente)
    └── mcp_server/
        └── server.py (pendiente)
```

## Decisiones de Arquitectura DDD

### 1. Domain Layer (Capa de Dominio)

#### Value Objects Implementados

**ProjectId**
- Inmutable (frozen=True)
- Validación: Solo enteros positivos
- Comparación por valor
- Decisión: Usar dataclass en lugar de Pydantic para mantener el dominio libre de dependencias externas

**Email**
- Inmutable
- Validación: Regex para formato de email estándar
- Pattern: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- Decisión: Validación en `__post_init__` para garantizar que nunca exista un Email inválido

**ProjectSlug**
- Inmutable
- Generación desde nombre con método de clase `from_name()`
- Normalización:
  - Minúsculas
  - Espacios → guiones
  - Solo alfanuméricos y guiones
  - Sin caracteres especiales
- Decisión: Factory method pattern para crear slugs desde nombres de proyectos

**UserStoryRef**
- Inmutable
- Identifica únicamente una User Story con ref + project_id
- Decisión: Composite value object que encapsula la identidad compuesta

### 2. Principios DDD Aplicados

#### Inmutabilidad
- Todos los Value Objects usan `@dataclass(frozen=True)`
- Imposible modificar valores después de la creación
- Garantiza thread-safety y previene efectos secundarios

#### Encapsulación de Validaciones
- Validaciones en `__post_init__()`
- ValueError con mensajes descriptivos
- Regla: "Si el objeto existe, es válido"

#### Comparación por Valor
- Dataclasses implementan `__eq__` automáticamente
- Dos Value Objects con mismos valores son iguales
- No hay identidad, solo valor

#### Separación de Responsabilidades
- Domain: Lógica de negocio pura, sin dependencias externas
- Application: Casos de uso y orquestación
- Infrastructure: Detalles técnicos (HTTP, DB, MCP)

### 3. Configuración de Tests

#### Problema de Imports Resuelto
- **Problema**: Tests usaban `from src.taiga_mcp_server...` pero el paquete se instalaba como `taiga_mcp_server`
- **Solución**: Agregado `pythonpath = ["."]` a `[tool.pytest.ini_options]` en pyproject.toml
- **Resultado**: Pytest ahora encuentra correctamente el módulo `src`

#### Estructura de Tests
- Seguimiento estricto de AAA (Arrange, Act, Assert)
- Tests descriptivos siguiendo convención: `test_<accion>_<condicion>_should_<resultado>`
- Cobertura objetivo: >=80%

### 4. Librerías Investigadas

#### FastMCP (>=2.0.0)
- Framework para crear servidores MCP
- Decoradores: `@mcp.tool`, `@mcp.resource`, `@mcp.prompt`
- Soporte stdio y HTTP transport
- Context para logging y progreso

#### Pydantic (>=2.0)
- Validación de datos en Infrastructure Layer
- Settings management con pydantic-settings
- No usado en Domain Layer (mantener pureza)

#### HTTPX (>=0.27.0)
- Cliente HTTP asíncrono para Taiga API
- Soporte async/await
- Mejores features que requests

#### Python-dotenv (>=1.0.0)
- Carga de variables de entorno desde .env
- Usado con pydantic-settings

### 5. Próximos Pasos (Orden de Implementación)

#### Fase 1: Completar Domain Layer
1. **Domain Exceptions** (src/domain/exceptions.py)
   - DomainException (base)
   - InvalidProjectDataException
   - InvalidUserStoryDataException

2. **Project Entity** (src/domain/entities/project.py)
   - Atributos: id, name, slug, description, tags, is_private
   - Métodos: update_name(), add_tag(), remove_tag()
   - Tests: 10 tests en test_project_entity.py

3. **UserStory Entity** (src/domain/entities/userstory.py)
   - Atributos: id, ref, subject, description, project_id, points
   - Métodos: update_subject(), calculate_total_points()
   - Tests: 10+ tests en test_userstory_entity.py

#### Fase 2: Infrastructure Layer
1. **TaigaConfig** (src/infrastructure/config/settings.py)
   - Usar pydantic-settings BaseSettings
   - Cargar desde .env
   - Validar URLs, puertos, etc.
   - Tests: 10 tests en test_env_config.py

2. **TaigaClient** (src/infrastructure/taiga_client/client.py)
   - Autenticación con Taiga API
   - Operaciones CRUD para proyectos, user stories, etc.
   - Manejo de errores HTTP
   - Tests: 20+ tests en test_taiga_client.py

3. **Excepciones de Infrastructure** (src/infrastructure/taiga_client/exceptions.py)
   - AuthenticationError
   - TaigaAPIError
   - NotFoundError

4. **FastMCP Server** (src/infrastructure/mcp_server/server.py)
   - Configuración del servidor FastMCP
   - Implementación de las 84 herramientas MCP
   - Soporte stdio y HTTP
   - Tests: 15+ tests en test_fastmcp_server.py

#### Fase 3: Application Layer
1. **Use Cases** (src/application/use_cases/)
   - CreateProjectUseCase
   - GetProjectUseCase
   - CreateUserStoryUseCase
   - etc.
   - Tests: 5+ tests por use case

#### Fase 4: Integration Tests
- Tests de integración con API real de Taiga
- Tests funcionales E2E (stdio y HTTP)

## Decisiones Técnicas Clave

### 1. Domain libre de Dependencias
**Decisión**: El Domain Layer NO usa Pydantic ni ninguna librería externa
**Razón**: Mantener el dominio puro y enfocado en lógica de negocio
**Implementación**: Usar dataclasses estándar de Python

### 2. Inmutabilidad en Value Objects
**Decisión**: Todos los Value Objects son frozen
**Razón**: Prevenir mutación accidental y efectos secundarios
**Implementación**: `@dataclass(frozen=True)`

### 3. Validación Temprana
**Decisión**: Validar en `__post_init__` y lanzar ValueError
**Razón**: "Make illegal states unrepresentable" - si el objeto existe, es válido
**Implementación**: Validaciones explícitas con mensajes claros

### 4. Factory Methods para Value Objects
**Decisión**: Usar métodos de clase como `ProjectSlug.from_name()`
**Razón**: Encapsular lógica de creación compleja
**Patrón**: Factory Method pattern

### 5. Async/Await en Infrastructure
**Decisión**: Usar async/await para todas las operaciones de I/O
**Razón**: Mejor rendimiento y escalabilidad
**Implementación**: httpx.AsyncClient, async def en cliente Taiga

### 6. Separación de Excepciones por Capa
**Decisión**: Excepciones de dominio separadas de infrastructure
**Razón**: No mezclar errores de negocio con errores técnicos
**Implementación**:
- Domain: DomainException
- Infrastructure: TaigaAPIError, AuthenticationError

## Problemas Encontrados y Soluciones

### Problema 1: Import de módulo `src`
**Error**: `ModuleNotFoundError: No module named 'src'`
**Causa**: Tests importaban `from src.taiga_mcp_server...` pero Python no encontraba src
**Solución**: Agregar `pythonpath = ["."]` a pytest.ini_options
**Resultado**: ✅ Resuelto

### Problema 2: Instalación del paquete
**Error**: Módulo no encontrado incluso con editable install
**Causa**: pyproject.toml tenía `packages = ["src/taiga_mcp_server"]` pero tests usaban src
**Solución**: Crear src/__init__.py y configurar pythonpath
**Resultado**: ✅ Resuelto

## Métricas Actuales

- **Tests totales**: 96
- **Tests pasando**: 14 (14.6%)
- **Tests fallando**: 82 (85.4%)
- **Cobertura de código**: 0% → objetivo 80%
- **Value Objects implementados**: 4/4 ✅
- **Entities implementadas**: 0/2
- **Infrastructure implementada**: 0/3
- **Use Cases implementados**: 0/1+
- **Herramientas MCP implementadas**: 0/84

## Plan de Continuación

1. ✅ Value Objects (completado)
2. 🔄 Domain Entities (siguiente)
3. ⏳ Infrastructure Config
4. ⏳ Infrastructure TaigaClient
5. ⏳ Infrastructure FastMCP Server
6. ⏳ Application Use Cases
7. ⏳ Integration Tests
8. ⏳ Functional Tests

## Referencias

- Documentación FastMCP: Documentacion/fastmcp.md
- Documentación Taiga API: Documentacion/taiga.md
- Análisis TDD: Documentacion/analisis_tdd.md
- Caso de Negocio: Documentacion/caso_negocio.txt
