# Estructura del Proyecto - Taiga MCP Server

## Vision General

Este documento explica la organizacion del codigo del proyecto Taiga MCP Server, describiendo el proposito y responsabilidad de cada componente, siguiendo los principios de **Domain-Driven Design (DDD)**.

## Arbol de Directorios

```
taiga_mcp_claude_code/
├── src/                          # Codigo fuente principal
│   ├── domain/                   # Capa de Dominio (logica de negocio pura)
│   │   ├── __init__.py
│   │   └── exceptions.py         # Excepciones del dominio
│   ├── application/              # Capa de Aplicacion (casos de uso)
│   │   ├── __init__.py
│   │   └── tools/                # Herramientas MCP (Application Services)
│   │       ├── __init__.py
│   │       ├── auth_tools.py     # Herramientas de autenticacion
│   │       ├── project_tools.py  # Herramientas de proyectos
│   │       └── userstory_tools.py # Herramientas de user stories
│   ├── infrastructure/           # Capa de Infraestructura (detalles tecnicos)
│   │   ├── __init__.py
│   │   └── config.py             # Configuracion con Pydantic Settings
│   ├── tools/                    # Herramientas legacy (migrando a application/)
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── projects.py
│   │   └── userstories.py
│   ├── __init__.py
│   ├── server.py                 # Servidor MCP principal
│   ├── config.py                 # Configuracion central
│   └── taiga_client.py           # Cliente HTTP para Taiga API
│
├── tests/                        # Suite completa de tests
│   ├── conftest.py               # Fixtures globales de pytest
│   ├── unit/                     # Tests unitarios (rapidos, sin I/O)
│   │   ├── infrastructure/
│   │   │   └── test_config.py    # Tests de configuracion
│   │   ├── tools/
│   │   │   ├── test_auth.py
│   │   │   ├── test_auth_tools.py
│   │   │   ├── test_projects.py
│   │   │   ├── test_project_tools.py
│   │   │   ├── test_userstories.py
│   │   │   └── test_userstory_tools.py
│   │   ├── test_server.py        # Tests del servidor MCP
│   │   ├── test_config_coverage.py
│   │   └── test_configuration.py
│   └── integration/              # Tests de integracion (con API real)
│       ├── test_auth_integration.py
│       └── test_projects_integration.py
│
├── Documentacion/                # Documentacion del proyecto
│   ├── analisis_tdd.md           # Analisis TDD exhaustivo
│   ├── caso_negocio.txt          # Requerimientos originales
│   ├── fastmcp.md                # Documentacion de FastMCP
│   ├── taiga.md                  # Documentacion de Taiga API
│   ├── estructura_proyecto.md    # Este archivo
│   └── [otros documentos]
│
├── .env.example                  # Plantilla de configuracion
├── .env                          # Configuracion real (no versionado)
├── .gitignore                    # Archivos ignorados por git
├── pyproject.toml                # Configuracion del proyecto (uv/pytest/ruff)
├── uv.lock                       # Lock file de dependencias
├── README.md                     # Documentacion principal
└── guia_uso.md                   # Guia de uso detallada
```

## Directorios Principales

### `/src` - Codigo Fuente

Contiene todo el codigo fuente del proyecto, organizado en capas DDD.

#### `/src/domain` - Capa de Dominio

**Proposito**: Contiene la logica de negocio pura, sin dependencias de frameworks o infraestructura.

**Componentes**:

- **`exceptions.py`**: Define las excepciones del dominio
  - `TaigaAPIError`: Error base para problemas de API
  - `AuthenticationError`: Error de autenticacion
  - `ResourceNotFoundError`: Recurso no encontrado (404)
  - `PermissionDeniedError`: Sin permisos (403)
  - `RateLimitError`: Rate limiting excedido (429)
  - `ConfigurationError`: Error de configuracion

**Principios**:
- No depende de ninguna otra capa
- No tiene conocimiento de HTTP, bases de datos, etc.
- Define conceptos del dominio del negocio
- Inmutable y sin estado

**Ejemplo**:
```python
# src/domain/exceptions.py
class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass
```

#### `/src/application` - Capa de Aplicacion

**Proposito**: Orquesta la logica de negocio mediante casos de uso. Coordina entidades y servicios del dominio.

**Componentes**:

- **`tools/`**: Herramientas MCP que exponen funcionalidad a clientes
  - `auth_tools.py`: Herramientas de autenticacion (login, logout, refresh)
  - `project_tools.py`: Herramientas de gestion de proyectos (CRUD)
  - `userstory_tools.py`: Herramientas de user stories (CRUD, bulk ops)

**Principios**:
- Depende solo de la capa de dominio
- Coordina llamadas a servicios externos (TaigaAPIClient)
- No contiene logica de negocio (eso va en domain)
- Define casos de uso como herramientas MCP

**Ejemplo**:
```python
# src/application/tools/auth_tools.py
class AuthTools:
    """Application service for authentication."""

    def __init__(self, mcp: FastMCP):
        self.mcp = mcp

    def register_tools(self):
        @self.mcp.tool(name="authenticate")
        async def authenticate(username: str, password: str):
            # Orquesta la autenticacion usando TaigaAPIClient
            async with TaigaAPIClient(config) as client:
                return await client.authenticate(username, password)
```

#### `/src/infrastructure` - Capa de Infraestructura

**Proposito**: Implementa detalles tecnicos y conexiones externas.

**Componentes**:

- **`config.py`**: Configuracion usando Pydantic Settings
  - `TaigaConfig`: Configuracion de Taiga API
  - `ServerConfig`: Configuracion del servidor MCP
  - `MCPConfig`: Configuracion de transporte MCP
  - Validadores de campos (URL, email, password, etc.)

**Principios**:
- Implementa interfaces definidas en domain
- Conoce detalles de frameworks (FastMCP, Pydantic)
- Maneja I/O (archivos .env, variables de entorno)
- Depende de domain y application

**Ejemplo**:
```python
# src/infrastructure/config.py
from pydantic_settings import BaseSettings

class TaigaConfig(BaseSettings):
    """Configuration loaded from .env file."""
    taiga_api_url: str
    taiga_username: str
    taiga_password: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
```

#### `/src/server.py` - Servidor MCP Principal

**Proposito**: Punto de entrada del servidor MCP. Inicializa FastMCP y registra todas las herramientas.

**Responsabilidades**:
- Crear instancia de FastMCP
- Cargar configuracion
- Crear TaigaAPIClient
- Registrar herramientas (AuthTools, ProjectTools, UserStoryTools)
- Manejar ciclo de vida del servidor (initialize, shutdown)
- Soportar STDIO y HTTP transport

**Ejemplo de uso**:
```python
from src.server import TaigaMCPServer

server = TaigaMCPServer()
await server.initialize()  # Autentica con Taiga
server.run()  # Inicia servidor (STDIO o HTTP segun config)
```

#### `/src/config.py` - Configuracion Central

**Proposito**: Centralizacion de configuracion del sistema (duplica/migra de infrastructure/config.py)

**Contenido**: Mismo que `infrastructure/config.py` (actualmente hay duplicacion por migracion en progreso)

#### `/src/taiga_client.py` - Cliente HTTP para Taiga

**Proposito**: Cliente HTTP que abstrae todas las llamadas a Taiga API REST.

**Responsabilidades**:
- Gestionar sesion HTTP con httpx
- Autenticacion y refresh de tokens
- Retry logic con exponential backoff
- Manejo de rate limiting (429)
- Traducir errores HTTP a excepciones de dominio
- Proporcionar metodos de alto nivel (list_projects, create_userstory, etc.)

**Principios**:
- Async/await nativo
- Context manager para manejo de recursos
- Timeouts configurables
- Type hints completos

**Ejemplo**:
```python
async with TaigaAPIClient(config) as client:
    # Autenticar
    await client.authenticate(username, password)

    # Usar API
    projects = await client.list_projects()
    story = await client.create_userstory(data)
```

### `/tests` - Tests

**Proposito**: Suite completa de tests que garantiza calidad y cobertura.

#### Estructura de Tests

**`/tests/unit`** - Tests Unitarios
- **Rapidos**: No hacen I/O real (mocks)
- **Aislados**: Cada test verifica un componente especifico
- **Deterministas**: Siempre dan el mismo resultado
- **Cobertura**: 277 tests unitarios

**`/tests/integration`** - Tests de Integracion
- **Reales**: Conectan con Taiga API real
- **Completos**: Verifican flujos end-to-end
- **Requieren credenciales**: .env con credenciales validas
- **Idempotentes**: No dejan basura en Taiga
- **Cobertura**: 17 tests de integracion

#### Fixtures Globales (`conftest.py`)

Proporciona fixtures reutilizables:
- `mock_taiga_config`: Configuracion mockeada
- `mock_httpx_client`: Cliente HTTP mockeado
- `taiga_client`: TaigaAPIClient real
- `auth_token`: Token de autenticacion real
- `test_project_id`: ID de proyecto de prueba

**Ejemplo**:
```python
# tests/conftest.py
@pytest.fixture
def mock_taiga_config():
    return TaigaConfig(
        taiga_api_url="https://api.taiga.io/api/v1",
        taiga_username="test@example.com",
        taiga_password="testpass123"
    )
```

### `/Documentacion` - Documentacion

**Proposito**: Toda la documentacion tecnica y de negocio del proyecto.

**Archivos clave**:

- **`caso_negocio.txt`**: Requerimientos funcionales y no funcionales originales
- **`analisis_tdd.md`**: Analisis exhaustivo del caso de negocio con matriz de trazabilidad
- **`fastmcp.md`**: Documentacion de referencia de FastMCP framework
- **`taiga.md`**: Documentacion de Taiga API REST
- **`estructura_proyecto.md`**: Este archivo

## Flujo de Datos

### Arquitectura de Capas

```
┌─────────────────────────────────────────────┐
│           Cliente MCP (Claude)              │
└──────────────────┬──────────────────────────┘
                   │ MCP Protocol
                   ▼
┌─────────────────────────────────────────────┐
│     Infrastructure: FastMCP Server          │
│          (STDIO/HTTP Transport)             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│    Application: AuthTools, ProjectTools     │
│         (Orquesta casos de uso)             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Infrastructure: TaigaAPIClient             │
│        (Cliente HTTP con httpx)             │
└──────────────────┬──────────────────────────┘
                   │ HTTPS
                   ▼
┌─────────────────────────────────────────────┐
│         Taiga API REST (Externa)            │
└─────────────────────────────────────────────┘
```

### Flujo de una Peticion

**Ejemplo: Crear User Story**

1. **Cliente MCP** invoca herramienta `create_userstory`:
   ```json
   {
     "name": "create_userstory",
     "arguments": {
       "auth_token": "...",
       "project_id": 309804,
       "subject": "Nueva historia"
     }
   }
   ```

2. **FastMCP Server** recibe peticion via STDIO/HTTP y rutea a `UserStoryTools`

3. **UserStoryTools** (Application):
   - Valida parametros
   - Construye payload para Taiga
   - Invoca `TaigaAPIClient.create_userstory()`

4. **TaigaAPIClient** (Infrastructure):
   - Serializa datos a JSON
   - Añade headers de autenticacion
   - Hace POST a `/api/v1/userstories`
   - Maneja errores HTTP
   - Deserializa respuesta

5. **Taiga API** procesa peticion y retorna JSON

6. **TaigaAPIClient** retorna respuesta a UserStoryTools

7. **UserStoryTools** formatea respuesta y retorna a FastMCP

8. **FastMCP Server** envia respuesta al cliente MCP

9. **Cliente MCP** recibe y procesa respuesta

## Dependencias entre Capas

```
Infrastructure ──────> Application ──────> Domain
       │                                      ▲
       └──────────────────────────────────────┘
```

**Regla de Dependencia**: Las flechas muestran dependencias permitidas.

- **Domain** NO depende de nadie (pura logica de negocio)
- **Application** depende solo de Domain
- **Infrastructure** depende de Domain y Application
- Nunca al reves (no ciclos)

**Violaciones Comunes a Evitar**:
- ❌ Domain importando de Application
- ❌ Domain importando de Infrastructure
- ❌ Application importando de Infrastructure (debil: solo para dependency injection)

**Ejemplo Correcto**:
```python
# ✅ Infrastructure puede importar de Application y Domain
from src.domain.exceptions import AuthenticationError
from src.application.tools.auth_tools import AuthTools

# ✅ Application puede importar de Domain
from src.domain.exceptions import TaigaAPIError

# ❌ Domain NO debe importar de Application
# from src.application.tools.auth_tools import AuthTools  # PROHIBIDO
```

## Nomenclatura y Convenciones

### Archivos y Directorios

- **Directorios**: `snake_case` (minusculas con guion bajo)
  - Ejemplos: `src/`, `domain/`, `application/tools/`

- **Archivos Python**: `snake_case.py`
  - Ejemplos: `taiga_client.py`, `auth_tools.py`, `exceptions.py`

- **Tests**: `test_*.py` o `*_test.py`
  - Ejemplos: `test_server.py`, `test_auth_tools.py`

### Clases

- **Entidades**: `PascalCase`, sustantivos
  - Ejemplos: `Usuario`, `Proyecto` (actualmente no tenemos entidades, usamos dicts)

- **Value Objects**: `PascalCase`, sustantivos
  - Ejemplos: `Email`, `AuthToken` (futuro)

- **Services**: `PascalCase` terminado en `Tools` o `Service`
  - Ejemplos: `AuthTools`, `ProjectTools`, `TaigaAPIClient`

- **Exceptions**: `PascalCase` terminado en `Error`
  - Ejemplos: `AuthenticationError`, `ConfigurationError`

- **Configuracion**: `PascalCase` terminado en `Config`
  - Ejemplos: `TaigaConfig`, `ServerConfig`

### Funciones y Metodos

- **Acciones**: `snake_case`, verbos en infinitivo
  - Ejemplos: `authenticate()`, `list_projects()`, `create_userstory()`

- **Predicados (booleanos)**: `is_*`, `has_*`, `can_*`
  - Ejemplos: `is_authenticated()`, `has_credentials()`, `can_run_stdio()`

- **Getters**: `get_*`
  - Ejemplos: `get_auth_token()`, `get_registered_tools()`

### Variables

- **Locales**: `snake_case`
  - Ejemplos: `auth_token`, `project_id`, `user_data`

- **Constantes**: `UPPER_CASE`
  - Ejemplos: `DEFAULT_TIMEOUT`, `MAX_RETRIES`

- **Privadas**: Prefijo `_`
  - Ejemplos: `_auth_token`, `_make_request()`

## Configuracion del Proyecto

### `pyproject.toml`

Configuracion centralizada del proyecto:

**[project]**: Metadatos del proyecto
- Nombre: `taiga-mcp-server`
- Version: `0.1.0`
- Python: `>=3.11`
- Dependencias principales

**[tool.pytest.ini_options]**: Configuracion de pytest
- Test paths: `tests/`
- Markers: `unit`, `integration`, `functional`, etc.
- Coverage minima: `80%`
- Modo async: `auto`

**[tool.ruff]**: Configuracion de linter
- Line length: `100`
- Target: `py311`
- Rules: `E`, `W`, `F`, `I`, `N`, `UP`, `B`

**[tool.mypy]**: Configuracion de type checker
- Python version: `3.11`
- Strict mode: `true`
- Disallow untyped defs: `true`

### `.env` y `.env.example`

**`.env.example`**: Plantilla de configuracion (versionada en git)
```bash
TAIGA_API_URL=
TAIGA_USERNAME=
TAIGA_PASSWORD=
```

**`.env`**: Configuracion real (NO versionada, en `.gitignore`)
```bash
TAIGA_API_URL=https://api.taiga.io/api/v1
TAIGA_USERNAME=real@email.com
TAIGA_PASSWORD=real_password
```

## Patrones de Diseño Aplicados

### 1. Repository Pattern (Simplificado)

**Donde**: `TaigaAPIClient` actua como repositorio para entidades de Taiga

**Por que**: Abstrae el acceso a datos (en este caso, API REST)

**Ejemplo**:
```python
# TaigaAPIClient es un pseudo-repositorio
async def get_project(self, project_id: int) -> Dict[str, Any]:
    return await self.get(f"/projects/{project_id}")
```

### 2. Factory Pattern

**Donde**: Creacion de configuraciones y clientes

**Por que**: Centraliza la creacion de objetos complejos

**Ejemplo**:
```python
def load_config() -> tuple[TaigaConfig, ServerConfig]:
    """Factory for configuration objects."""
    return TaigaConfig(), ServerConfig()
```

### 3. Strategy Pattern

**Donde**: Soporte de multiples transportes (STDIO vs HTTP)

**Por que**: Permite cambiar estrategia de transporte sin modificar codigo

**Ejemplo**:
```python
if transport == "stdio":
    self.run_stdio_only()
elif transport == "http":
    self.run_http_only()
```

### 4. Dependency Injection

**Donde**: Inyeccion de configuracion y clientes

**Por que**: Facilita testing y desacoplamiento

**Ejemplo**:
```python
class AuthTools:
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp  # Inyeccion de dependencia
        self.config = TaigaConfig()
```

### 5. Context Manager

**Donde**: `TaigaAPIClient` con `async with`

**Por que**: Garantiza cierre de recursos (conexiones HTTP)

**Ejemplo**:
```python
async with TaigaAPIClient(config) as client:
    # Conexiones se cierran automaticamente al salir
    await client.authenticate()
```

## Migraciones en Progreso

### Duplicacion de Codigo

Actualmente hay duplicacion entre:
- `src/config.py` y `src/infrastructure/config.py`
- `src/tools/` y `src/application/tools/`

**Razon**: Migracion gradual a arquitectura DDD completa

**Estado**:
- ✅ `src/infrastructure/config.py` creado
- ✅ `src/application/tools/` creado
- 🚧 Tests usando ambas versiones
- ❌ Limpieza pendiente

**Plan**:
1. Migrar todos los tests a usar `src/application/tools/`
2. Deprecar `src/tools/`
3. Eliminar `src/config.py` (usar solo `infrastructure/config.py`)

## Mantenimiento y Evolucion

### Como Agregar una Nueva Funcionalidad

**Ejemplo: Soporte para Issues**

1. **Domain**: Definir excepciones si es necesario
   ```python
   # src/domain/exceptions.py
   class IssueNotFoundError(ResourceNotFoundError):
       pass
   ```

2. **Infrastructure**: Agregar metodos a TaigaAPIClient
   ```python
   # src/taiga_client.py
   async def list_issues(self, project: int) -> List[Dict]:
       return await self.get("/issues", params={"project": project})
   ```

3. **Application**: Crear IssueTools
   ```python
   # src/application/tools/issue_tools.py
   class IssueTools:
       def register_tools(self):
           @self.mcp.tool(name="list_issues")
           async def list_issues(auth_token: str, project_id: int):
               # Implementacion
               pass
   ```

4. **Server**: Registrar herramientas
   ```python
   # src/server.py
   self._issue_tools = IssueTools(self.mcp)
   self._issue_tools.register_tools()
   ```

5. **Tests**: Crear tests unitarios e integracion
   ```python
   # tests/unit/tools/test_issue_tools.py
   # tests/integration/test_issues_integration.py
   ```

### Como Extender Configuracion

1. Agregar campo a `TaigaConfig` en `infrastructure/config.py`
2. Agregar validador con `@field_validator`
3. Actualizar `.env.example`
4. Documentar en README.md
5. Crear tests para validacion

---

**Ultima actualizacion**: 2025-12-04
**Mantenedor**: Equipo de Desarrollo
**Version del documento**: 1.0
