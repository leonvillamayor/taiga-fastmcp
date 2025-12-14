# Documentación Completa de FastMCP

## Índice

1. [Introducción](#introducción)
2. [Instalación y Requisitos](#instalación-y-requisitos)
3. [Conceptos Core](#conceptos-core)
4. [Tools (Herramientas)](#tools-herramientas)
5. [Resources (Recursos)](#resources-recursos)
6. [Prompts (Plantillas)](#prompts-plantillas)
7. [Context (Contexto)](#context-contexto)
8. [Client (Cliente)](#client-cliente)
9. [Authentication (Autenticación)](#authentication-autenticación)
10. [Transports (Transportes)](#transports-transportes)
11. [Middleware](#middleware)
12. [Server Composition (Composición de Servidores)](#server-composition-composición-de-servidores)
13. [Storage Backends](#storage-backends)
14. [Deployment (Despliegue)](#deployment-despliegue)
15. [Best Practices (Mejores Prácticas)](#best-practices-mejores-prácticas)

---

## Introducción

FastMCP es **"la forma rápida y Pythónica de construir servidores y clientes MCP"** (Model Context Protocol), creado por Prefect. Es un framework moderno que simplifica la construcción de servidores y clientes MCP con código mínimo.

### Características Principales

- **Simplicidad de Desarrollo**: Un simple decorador convierte funciones Python en capacidades MCP
- **Generación Automática de Esquemas**: A partir de anotaciones de tipo y docstrings
- **Múltiples Transportes**: stdio, HTTP (Streamable), SSE
- **Autenticación Empresarial**: OAuth integrado con 8+ proveedores
- **Composición de Servidores**: Arquitecturas modulares mediante `mount()` e `import_server()`
- **Soporte Async Completo**: Para operaciones I/O-bound eficientes
- **Cliente Programático**: Interacción programática con cualquier servidor MCP

---

## Instalación y Requisitos

### Requisitos

- **Python**: 3.10 o superior
- **Gestor de paquetes**: Se recomienda `uv`

### Instalación

```bash
# Con uv (recomendado)
uv pip install fastmcp

# Con pip estándar
pip install fastmcp
```

### Instalación para desarrollo

```bash
# Clonar repositorio
git clone https://github.com/jlowin/fastmcp.git
cd fastmcp

# Instalar dependencias de desarrollo
uv sync
```

---

## Conceptos Core

FastMCP expone tres primitivas principales del protocolo MCP:

1. **Tools**: Operaciones ejecutables (como funciones POST)
2. **Resources**: Acceso de solo lectura a datos (como endpoints GET)
3. **Prompts**: Plantillas reutilizables para interacciones LLM

### FastMCP Server Object

La instancia central que contiene todos los componentes:

```python
from fastmcp import FastMCP

mcp = FastMCP(name="MyAssistantServer")
```

**Parámetros del constructor FastMCP**:

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `name` | str | Nombre del servidor MCP |
| `auth` | Provider | Proveedor de autenticación |
| `strict_input_validation` | bool | Modo estricto de validación |
| `mask_error_details` | bool | Ocultar detalles de errores internos |
| `on_duplicate_tools` | str | Manejo de duplicados: "warn", "error", "replace", "ignore" |
| `on_duplicate_resources` | str | Manejo de duplicados en recursos |
| `on_duplicate_prompts` | str | Manejo de duplicados en prompts |
| `resource_prefix_format` | str | Formato de prefijo: "path" o "protocol" |
| `include_tags` | set[str] | Filtrar componentes por tags incluidos |
| `exclude_tags` | set[str] | Filtrar componentes por tags excluidos |

---

## Tools (Herramientas)

Los **Tools** son funciones Python expuestas como capacidades ejecutables para clientes MCP.

### Definición Básica

```python
from fastmcp import FastMCP

mcp = FastMCP(name="CalculatorServer")

@mcp.tool
def add(a: int, b: int) -> int:
    """Adds two integer numbers together."""
    return a + b
```

### Parámetros del Decorador @mcp.tool

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `name` | str | Nombre personalizado expuesto al cliente |
| `description` | str | Descripción alternativa al docstring |
| `tags` | set[str] | Categorías para organizar herramientas |
| `enabled` | bool | Activar/desactivar visibilidad (default: True) |
| `icons` | list[Icon] | Representaciones visuales (v2.14.0+) |
| `exclude_args` | list[str] | Argumentos ocultos al cliente |
| `annotations` | dict | Metadatos adicionales (readOnlyHint, destructiveHint) |
| `meta` | dict | Información personalizada para el cliente |

### Ejemplo Completo

```python
from typing import Annotated
from pydantic import Field

@mcp.tool(
    name="search_database",
    description="Search the database with filters",
    tags={"database", "search"},
    annotations={
        "title": "Database Search",
        "readOnlyHint": True,
        "openWorldHint": False
    }
)
def search_database(
    query: Annotated[str, Field(description="Término de búsqueda")],
    limit: Annotated[int, Field(description="Máximo de resultados", ge=1, le=100)] = 10,
    category: str | None = None
) -> list[dict]:
    """Search products in the database."""
    # Implementación
    return [{"id": 1, "name": "Product"}]
```

### Tipos de Retorno Soportados

FastMCP convierte automáticamente tipos Python a bloques de contenido MCP:

| Tipo Retorno | Conversión MCP |
|-------------|----------------|
| `str` | TextContent |
| `bytes` | BlobResourceContents (base64) |
| `Image` | ImageContent |
| `Audio` | AudioContent |
| `File` | EmbeddedResource |
| `dict`/Pydantic | Structured content (JSON) |
| `list` | Múltiples bloques de contenido |

### Salida Estructurada (v2.10.0+)

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int
    email: str

@mcp.tool
def get_user_profile(user_id: str) -> Person:
    """Get user profile with structured output."""
    return Person(name="Alice", age=30, email="alice@example.com")
```

### Control Total con ToolResult

```python
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

@mcp.tool
def advanced_tool() -> ToolResult:
    """Complete control over output."""
    return ToolResult(
        content=[TextContent(type="text", text="Summary")],
        structured_content={"data": "value", "count": 42},
        meta={"execution_time_ms": 145}
    )
```

### Soporte Asincrónico

```python
@mcp.tool
async def async_operation(data: str) -> str:
    """Async tools are preferred for I/O operations."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.example.com/{data}") as response:
            return await response.text()
```

### Manejo de Errores

```python
from fastmcp.exceptions import ToolError

@mcp.tool
def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ToolError("División por cero no permitida.")
    return a / b
```

### Acceso al Contexto

```python
from fastmcp import Context

@mcp.tool
async def process_data(data_uri: str, ctx: Context) -> dict:
    """Access MCP capabilities through context."""
    await ctx.info(f"Processing {data_uri}")
    await ctx.report_progress(progress=50, total=100)
    resource = await ctx.read_resource(data_uri)
    return {"length": len(resource[0].content if resource else "")}
```

### Gestión Dinámica

```python
# Deshabilitar herramienta
mcp.get_tool("calculate_sum").disable()

# Habilitar herramienta
mcp.get_tool("calculate_sum").enable()

# Remover herramienta
mcp.remove_tool("calculate_sum")
```

---

## Resources (Recursos)

Los **Resources** proporcionan acceso de solo lectura a fuentes de datos mediante URIs únicas.

### Definición Básica

```python
@mcp.resource("weather://current")
def get_weather() -> dict:
    """Get current weather data."""
    return {"temperature": 22, "condition": "Sunny"}
```

### Parámetros del Decorador @mcp.resource

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `uri` | str | Identificador único requerido |
| `name` | str | Nombre personalizado |
| `description` | str | Descripción personalizada |
| `mime_type` | str | Tipo MIME del contenido |
| `tags` | set[str] | Etiquetas para categorización |
| `enabled` | bool | Habilitar/deshabilitar recurso |
| `annotations` | dict | Metadatos adicionales |
| `meta` | dict | Información personalizada |

### Resource Templates (URIs Dinámicas)

Los templates permiten parámetros en la URI:

```python
@mcp.resource("weather://{city}/current")
def get_weather(city: str) -> dict:
    """Get weather for a specific city."""
    return {"city": city.capitalize(), "temperature": 22}

# Uso: weather://paris/current
```

#### Tipos de Parámetros

**Parámetros estándar** (`{param}`):
```python
@mcp.resource("users://{user_id}/profile")
def get_profile(user_id: int) -> dict:
    return {"id": user_id, "name": f"User {user_id}"}
```

**Parámetros wildcard** (`{param*}`):
```python
@mcp.resource("files://{path*}")
def read_file(path: str) -> str:
    """Captura múltiples segmentos incluyendo barras."""
    with open(f"/{path}") as f:
        return f.read()
```

**Query parameters** (`{?param1,param2}`):
```python
@mcp.resource("data://items{?filter,limit}")
def get_items(filter: str = None, limit: int = 10) -> list:
    """Query parameters opcionales."""
    return [{"id": i} for i in range(limit)]
```

### Valores Retornables

- **str**: Convertido a `TextResourceContents` (text/plain)
- **dict, list, pydantic.BaseModel**: Serializado a JSON automáticamente
- **bytes**: Codificado en base64 como `BlobResourceContents`
- **None**: Retorna lista vacía

### Clases de Recursos Directas

Para contenido estático:

```python
from fastmcp.resources import TextResource, FileResource, HttpResource, DirectoryResource

# Recurso de texto estático
mcp.add_resource(TextResource(
    uri="config://app",
    text="Configuration data",
    mime_type="text/plain"
))

# Recurso desde archivo
mcp.add_resource(FileResource(
    uri="file:///logs/app.log",
    path="/var/logs/app.log"
))

# Recurso HTTP
mcp.add_resource(HttpResource(
    uri="remote://api-data",
    url="https://api.example.com/data"
))

# Directorio (retorna JSON con lista de archivos)
mcp.add_resource(DirectoryResource(
    uri="dir:///workspace",
    path="/workspace"
))
```

### Recursos Asíncronos

```python
import aiofiles

@mcp.resource("file:///path/log.txt")
async def read_log() -> str:
    """Read file asynchronously."""
    async with aiofiles.open("/path/log.txt") as f:
        return await f.read()
```

### Anotaciones

```python
@mcp.resource(
    uri="data://readonly",
    annotations={
        "readOnlyHint": True,
        "idempotentHint": True
    }
)
def get_data():
    return {"data": "value"}
```

---

## Prompts (Plantillas)

Los **Prompts** son plantillas reutilizables de mensajes para guiar interacciones con LLMs.

### Definición Básica

```python
@mcp.prompt
def ask_about_topic(topic: str) -> str:
    """Generates a user message asking for an explanation."""
    return f"Can you please explain the concept of '{topic}'?"
```

### Parámetros del Decorador @mcp.prompt

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `name` | str | Identificador del prompt |
| `title` | str | Título legible por humanos |
| `description` | str | Descripción personalizada |
| `tags` | set[str] | Etiquetas de categorización |
| `enabled` | bool | Habilitar/deshabilitar (default: True) |
| `icons` | list[Icon] | Iconos visuales |
| `meta` | dict | Metadatos personalizados |

### Ejemplo Completo

```python
from pydantic import Field

@mcp.prompt(
    name="analyze_data_request",
    description="Creates a request to analyze data",
    tags={"analysis", "data"},
    meta={"version": "1.1", "author": "data-team"}
)
def data_analysis_prompt(
    data_uri: str = Field(description="URI del recurso con datos"),
    analysis_type: str = Field(default="summary", description="Tipo de análisis")
) -> str:
    return f"Please perform a '{analysis_type}' analysis on the data at {data_uri}."
```

### Tipos de Retorno

| Tipo Retorno | Comportamiento |
|-------------|----------------|
| `str` | Convertido a mensaje de usuario único |
| `PromptMessage` | Usado directamente |
| `list[PromptMessage \| str]` | Secuencia de conversación |
| Otros tipos | Convertidos a string, luego a mensaje |

### Multi-Mensaje

```python
from fastmcp.prompts.prompt import Message, PromptResult

@mcp.prompt
def roleplay_scenario(character: str, situation: str) -> PromptResult:
    """Sets up a roleplaying scenario."""
    return [
        Message(f"You are {character}. Situation: {situation}"),
        Message("Okay, I understand. What happens next?", role="assistant")
    ]
```

### Prompts Asíncronos

```python
@mcp.prompt
async def data_based_prompt(data_id: str) -> str:
    """Generates prompt based on fetched data."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.example.com/data/{data_id}") as response:
            data = await response.json()
            return f"Analyze this data: {data['content']}"
```

---

## Context (Contexto)

El objeto **Context** proporciona acceso a capacidades MCP dentro de las funciones.

### Acceso al Contexto

```python
from fastmcp import Context

@mcp.tool
async def process_file(file_uri: str, ctx: Context) -> str:
    """Access context through type hint."""
    await ctx.info(f"Processing {file_uri}")
    return "Processed"
```

### Métodos Disponibles

#### Logging

```python
await ctx.debug("Debug message")
await ctx.info("Info message")
await ctx.warning("Warning message")
await ctx.error("Error message")
```

#### Progress Reporting

```python
await ctx.report_progress(progress=50, total=100)
```

#### Resource Access

```python
# Listar recursos
resources = await ctx.list_resources()

# Leer recurso
content = await ctx.read_resource("file:///config/settings.json")
```

#### Prompt Access

```python
# Listar prompts
prompts = await ctx.list_prompts()

# Obtener prompt
result = await ctx.get_prompt("analyze_data", {"data": [1, 2, 3]})
```

#### LLM Sampling

```python
response = await ctx.sample("Analyze this data", temperature=0.7)
print(response.text)
```

#### User Elicitation

```python
name = await ctx.elicit("Enter your name:", response_type=str)
```

#### State Management

```python
# Guardar estado (solo durante la solicitud)
ctx.set_state("user_id", "123")

# Obtener estado
user_id = ctx.get_state("user_id")
```

### Información de la Solicitud

```python
# ID único de la solicitud
request_id = ctx.request_id

# ID del cliente
client_id = ctx.client_id

# ID de sesión (solo HTTP)
session_id = ctx.session_id

# Contexto MCP subyacente
request_context = ctx.request_context

# Instancia del servidor FastMCP
server = ctx.fastmcp
```

### Acceso HTTP

```python
from fastmcp.server.dependencies import get_http_request, get_http_headers

# En funciones decoradas
request = get_http_request()
headers = get_http_headers()
```

### Acceso a Token

```python
from fastmcp.server.dependencies import get_access_token

token = get_access_token()
if token:
    user_id = token.claims.get("sub")
    scopes = token.scopes
```

---

## Client (Cliente)

El **Client** de FastMCP permite interacción programática con servidores MCP.

### Creación de Cliente

```python
from fastmcp import Client, FastMCP

# Servidor en memoria (ideal para testing)
server = FastMCP("TestServer")
client = Client(server)

# Servidor HTTP
client = Client("https://example.com/mcp")

# Script Python local
client = Client("my_mcp_server.py")

# Script Node.js
client = Client("server.js")
```

### Ciclo de Vida de Conexión

```python
async with client:
    print(f"Connected: {client.is_connected()}")

    # Listar herramientas
    tools = await client.list_tools()

    # Llamar herramienta
    result = await client.call_tool("multiply", {"a": 5, "b": 3})

    # Listar recursos
    resources = await client.list_resources()

    # Leer recurso
    content = await client.read_resource("file:///config/settings.json")

    # Listar prompts
    prompts = await client.list_prompts()

    # Obtener prompt
    messages = await client.get_prompt("analyze_data", {"data": [1, 2, 3]})

    # Ping servidor
    await client.ping()
```

### Control de Inicialización

```python
client = Client("my_mcp_server.py", auto_initialize=False)

async with client:
    result = await client.initialize(timeout=10.0)
    print(f"Server: {result.serverInfo.name}")
```

### Cliente Multi-Servidor

```python
config = {
    "mcpServers": {
        "weather": {"url": "https://weather-api.example.com/mcp"},
        "assistant": {"command": "python", "args": ["./assistant_server.py"]}
    }
}

client = Client(config)

async with client:
    # Las herramientas tienen prefijo con el nombre del servidor
    weather_data = await client.call_tool("weather_get_forecast", {"city": "London"})
```

### Configuración del Cliente

```python
client = Client(
    "my_mcp_server.py",
    log_handler=custom_log_handler,
    progress_handler=progress_callback,
    sampling_handler=sampling_callback,
    timeout=30.0
)
```

---

## Authentication (Autenticación)

FastMCP proporciona autenticación empresarial integrada con múltiples proveedores OAuth.

### Proveedores Soportados

- **Google**
- **GitHub**
- **Microsoft Azure / Entra ID**
- **Auth0**
- **WorkOS / AuthKit**
- **Descope**
- **Scalekit**
- **AWS Cognito**
- **JWT**
- **API Keys**

### Configuración OAuth (Google)

```python
from fastmcp import FastMCP
from fastmcp.server.auth.providers.google import GoogleProvider

auth = GoogleProvider(
    client_id="your-client-id",
    client_secret="your-client-secret",
    base_url="https://myserver.com"
)

mcp = FastMCP("Protected Server", auth=auth)
```

### Configuración con GitHub

```python
from fastmcp.server.auth.providers.github import GitHubProvider

auth = GitHubProvider(
    client_id=os.environ["GITHUB_CLIENT_ID"],
    client_secret=os.environ["GITHUB_CLIENT_SECRET"],
    base_url="https://your-server.com"
)

mcp = FastMCP("GitHub Protected", auth=auth)
```

### Cliente con OAuth

```python
async with Client("https://protected-server.com/mcp", auth="oauth") as client:
    result = await client.call_tool("protected_tool")
```

### JWT y API Keys

```python
from fastmcp.server.auth.providers.jwt import JWTProvider
from fastmcp.server.auth.providers.apikey import APIKeyProvider

# JWT
jwt_auth = JWTProvider(
    jwt_signing_key=os.environ["JWT_SIGNING_KEY"]
)

# API Key
apikey_auth = APIKeyProvider(
    api_keys={"key1": {"user": "admin", "scopes": ["read", "write"]}}
)
```

---

## Transports (Transportes)

FastMCP soporta tres protocolos de transporte principales.

### STDIO (Default)

Ideal para herramientas CLI y aplicaciones de escritorio:

```python
mcp = FastMCP("MyServer")

if __name__ == "__main__":
    mcp.run()  # Usa STDIO por defecto
```

### HTTP (Streamable) - Recomendado para Producción

Para acceso en red y múltiples clientes simultáneos:

```python
mcp = FastMCP("MyServer")

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8000,
        path="/mcp"
    )
```

### SSE (Server-Sent Events) - Legacy

Para compatibilidad con clientes SSE existentes:

```python
mcp = FastMCP("MyServer")

if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host="127.0.0.1",
        port=8000
    )
```

### CLI de FastMCP

```bash
# Ejecutar servidor con STDIO
fastmcp run server.py

# Ejecutar con HTTP
fastmcp run server.py --transport http --port 8000
```

---

## Middleware

El middleware permite interceptar y modificar solicitudes/respuestas MCP.

### Implementación Básica

```python
from fastmcp.server.middleware import Middleware, MiddlewareContext

class CustomMiddleware(Middleware):
    async def on_message(self, context: MiddlewareContext, call_next):
        # Pre-procesamiento
        print(f"Request: {context.message}")

        # Ejecutar siguiente middleware
        result = await call_next(context)

        # Post-procesamiento
        print(f"Response: {result}")

        return result
```

### Hooks Disponibles

**Nivel de mensaje**:
- `on_message` - Todos los mensajes
- `on_request` - Solo solicitudes
- `on_notification` - Solo notificaciones

**Específicos de operación**:
- `on_call_tool`
- `on_read_resource`
- `on_get_prompt`
- `on_list_tools`
- `on_list_resources`
- `on_list_prompts`
- `on_list_resource_templates`
- `on_initialize` (v2.13.0+)

### Middleware Integrado

#### Timing

```python
from fastmcp.server.middleware.timing import TimingMiddleware, DetailedTimingMiddleware

mcp.add_middleware(TimingMiddleware())
mcp.add_middleware(DetailedTimingMiddleware())
```

#### Logging

```python
from fastmcp.server.middleware.logging import LoggingMiddleware, StructuredLoggingMiddleware

mcp.add_middleware(LoggingMiddleware(include_payloads=True))
mcp.add_middleware(StructuredLoggingMiddleware())
```

#### Rate Limiting

```python
from fastmcp.server.middleware.ratelimit import RateLimitingMiddleware

mcp.add_middleware(RateLimitingMiddleware(
    max_requests_per_second=50,
    algorithm="token_bucket"  # o "sliding_window"
))
```

#### Caching

```python
from fastmcp.server.middleware.caching import ResponseCachingMiddleware
from key_value.aio.stores.disk import DiskStore

mcp.add_middleware(ResponseCachingMiddleware(
    cache_storage=DiskStore(directory="cache"),
    ttl=3600  # 1 hora
))
```

#### Error Handling

```python
from fastmcp.server.middleware.errors import ErrorHandlingMiddleware

mcp.add_middleware(ErrorHandlingMiddleware(
    max_retries=3,
    backoff_factor=2.0
))
```

### Uso de Múltiples Middlewares

```python
# Se ejecutan en orden de registro
mcp.add_middleware(ErrorHandlingMiddleware())
mcp.add_middleware(RateLimitingMiddleware(max_requests_per_second=50))
mcp.add_middleware(ResponseCachingMiddleware())
mcp.add_middleware(LoggingMiddleware(include_payloads=True))
```

---

## Server Composition (Composición de Servidores)

FastMCP permite combinar múltiples servidores mediante dos métodos.

### Import Server (Composición Estática)

Copia componentes de un servidor a otro:

```python
from fastmcp import FastMCP

# Subservidor
weather_mcp = FastMCP(name="WeatherService")

@weather_mcp.tool
def get_forecast(city: str) -> dict:
    return {"city": city, "forecast": "Sunny"}

# Servidor principal
main_mcp = FastMCP(name="MainApp")

# Importar con prefijo
await main_mcp.import_server(weather_mcp, prefix="weather")

# Resultado: herramienta "weather_get_forecast"
```

**Características**:
- Copia estática (cambios posteriores NO se reflejan)
- Rápido (sin delegación en runtime)
- Ideal para bundling de componentes finalizados

### Mount (Composición Dinámica)

Establece enlace vivo con delegación en runtime:

```python
dynamic_mcp = FastMCP(name="DynamicService")

@dynamic_mcp.tool
def initial_tool():
    return "Initial Tool"

main_mcp = FastMCP(name="MainAppLive")
main_mcp.mount(dynamic_mcp, prefix="dynamic")

# Agregar herramienta DESPUÉS del mount
@dynamic_mcp.tool
def added_later():
    return "Added Dynamically!"

# La nueva herramienta está disponible inmediatamente
```

**Características**:
- Enlace vivo (cambios se reflejan inmediatamente)
- Más lento (delegación en runtime)
- Ideal para composición modular en runtime

### Comparación

| Característica | Import Server | Mount |
|----------------|---------------|-------|
| Actualizaciones | NO reflejadas | Reflejadas inmediatamente |
| Performance | Rápido | Más lento |
| Mejor para | Bundling estático | Composición dinámica |

### Prefijos

**Con prefijo**:
```python
await main_mcp.import_server(weather_mcp, prefix="weather")
# Tools: weather_get_forecast
# Resources: data://weather/info
```

**Sin prefijo**:
```python
await main_mcp.import_server(weather_mcp)
# Mantienen nombres originales
```

### Proxy Mounting

```python
# Mounting directo (default)
main_mcp.mount(api_server, prefix="api")

# Mounting como proxy (eventos de ciclo de vida completos)
main_mcp.mount(api_server, prefix="api", as_proxy=True)
```

### Tag Filtering en Composición

```python
api_server = FastMCP(name="APIServer")

@api_server.tool(tags={"production"})
def prod_endpoint() -> str:
    return "Production data"

@api_server.tool(tags={"development"})
def dev_endpoint() -> str:
    return "Debug data"

# Solo incluir tools de producción
prod_app = FastMCP(name="ProductionApp", include_tags={"production"})
prod_app.mount(api_server, prefix="api")

# Solo "api_prod_endpoint" es visible
```

---

## Storage Backends

FastMCP utiliza backends de almacenamiento enchufables para caché y estado OAuth.

### Backends Disponibles

- **In-Memory** (default para desarrollo)
- **DiskStore** (almacenamiento local)
- **RedisStore** (producción distribuida)
- **DynamoDBStore** (AWS)
- **MongoDBStore**
- **ElasticsearchStore**

### Encriptación Automática

Por defecto, el almacenamiento se encripta automáticamente con `FernetEncryptionWrapper`.

### Ejemplo con Redis y Encriptación

```python
import os
from fastmcp.server.auth.providers.github import GitHubProvider
from key_value.aio.stores.redis import RedisStore
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper
from cryptography.fernet import Fernet

auth = GitHubProvider(
    client_id=os.environ["GITHUB_CLIENT_ID"],
    client_secret=os.environ["GITHUB_CLIENT_SECRET"],
    base_url="https://your-server.com",
    jwt_signing_key=os.environ["JWT_SIGNING_KEY"],
    client_storage=FernetEncryptionWrapper(
        key_value=RedisStore(host="redis.example.com", port=6379),
        fernet=Fernet(os.environ["STORAGE_ENCRYPTION_KEY"])
    )
)

mcp = FastMCP("Server", auth=auth)
```

### Cache de Respuestas con DiskStore

```python
from fastmcp import FastMCP
from fastmcp.server.middleware.caching import ResponseCachingMiddleware
from key_value.aio.stores.disk import DiskStore

mcp = FastMCP("My Server")
mcp.add_middleware(ResponseCachingMiddleware(
    cache_storage=DiskStore(directory="cache"),
    ttl=3600  # TTL en segundos
))
```

### TTL (Time-to-Live)

Todos los backends soportan TTL con expiración automática:

```python
from key_value.aio.wrappers.ttl import TTLWrapper
from key_value.aio.stores.redis import RedisStore

storage = TTLWrapper(
    key_value=RedisStore(host="localhost", port=6379),
    default_ttl=3600  # 1 hora
)
```

---

## Deployment (Despliegue)

### Desarrollo Local

**Ejecución directa**:
```bash
python server.py
```

**Con FastMCP CLI**:
```bash
fastmcp run server.py
```

**Con parámetros**:
```bash
fastmcp run server.py --transport http --host 127.0.0.1 --port 8000
```

### Producción - HTTP Server

```python
from fastmcp import FastMCP

mcp = FastMCP("ProductionServer")

@mcp.tool
def process_data(data: str) -> str:
    return f"Processed: {data}"

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",  # Escuchar en todas las interfaces
        port=8000,
        path="/mcp"
    )
```

### Docker Deployment

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias
RUN pip install fastmcp

# Copiar servidor
COPY server.py .

# Exponer puerto
EXPOSE 8000

# Ejecutar servidor
CMD ["python", "server.py"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - TAIGA_API_URL=https://api.taiga.io/api/v1
      - TAIGA_USERNAME=${TAIGA_USERNAME}
      - TAIGA_PASSWORD=${TAIGA_PASSWORD}
    restart: unless-stopped
```

**Construcción y ejecución**:
```bash
docker-compose up -d
```

### FastMCP Cloud

FastMCP ofrece despliegue cloud con:
- HTTPS instantáneo
- Autenticación integrada
- Configuración cero

### Nginx Reverse Proxy

**nginx.conf**:
```nginx
server {
    listen 80;
    server_name mcp.example.com;

    location /mcp {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Systemd Service

**/etc/systemd/system/mcp-server.service**:
```ini
[Unit]
Description=FastMCP Server
After=network.target

[Service]
Type=simple
User=mcp-user
WorkingDirectory=/opt/mcp-server
ExecStart=/usr/bin/python3 /opt/mcp-server/server.py
Restart=always
Environment="TAIGA_API_URL=https://api.taiga.io/api/v1"
Environment="TAIGA_USERNAME=user@example.com"
Environment="TAIGA_PASSWORD=secretpass"

[Install]
WantedBy=multi-user.target
```

**Habilitar y ejecutar**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-server
sudo systemctl start mcp-server
sudo systemctl status mcp-server
```

---

## Best Practices (Mejores Prácticas)

### 1. Tools

- ✅ Usar anotaciones de tipo completas para generación automática de esquemas
- ✅ Escribir docstrings descriptivos
- ✅ Implementar `async def` para operaciones I/O-bound
- ✅ Usar `Context` para logging y progress reporting
- ✅ Manejar errores explícitamente con `ToolError`
- ✅ Retornar estructuras tipadas (dataclasses/Pydantic)
- ❌ Evitar operaciones bloqueantes síncronas para I/O

### 2. Resources

- ✅ Usar URIs significativas con esquemas consistentes (`data://`, `file://`)
- ✅ Implementar métodos asíncronos para I/O costoso
- ✅ Usar anotaciones claras (`readOnlyHint`, `idempotentHint`)
- ✅ Manejar errores con `ResourceError`
- ✅ Usar tags para categorización
- ❌ No exponer datos sensibles sin autenticación

### 3. Prompts

- ✅ Mantener tipos de parámetros simples
- ✅ Usar `Field` con descripciones claras
- ✅ Implementar async para llamadas a APIs externas
- ✅ Aprovechar auto-generación de esquemas JSON
- ❌ Evitar `*args` y `**kwargs` (no soportados)

### 4. Context

- ✅ Usar `ctx.info()` y `ctx.error()` para logging
- ✅ Reportar progreso en operaciones largas con `ctx.report_progress()`
- ✅ Usar `ctx.sample()` para interacciones LLM cuando sea apropiado
- ❌ No asumir que el estado persiste entre solicitudes

### 5. Authentication

- ✅ Siempre encriptar almacenamiento de tokens con `FernetEncryptionWrapper`
- ✅ Usar variables de entorno para credenciales
- ✅ Implementar HTTPS para producción
- ❌ Nunca hardcodear secrets en código

### 6. Middleware

- ✅ Ordenar middleware según importancia (auth primero, logging último)
- ✅ Usar middleware de caché para operaciones costosas
- ✅ Implementar rate limiting en producción
- ✅ Agregar error handling middleware

### 7. Deployment

- ✅ Usar HTTP transport para producción
- ✅ Configurar logging apropiado
- ✅ Implementar health checks
- ✅ Usar reverse proxy (nginx) para HTTPS
- ✅ Configurar systemd o supervisor para auto-restart
- ❌ No usar STDIO transport en producción remota

### 8. Testing

- ✅ Usar in-memory client para tests rápidos
- ✅ Implementar tests para cada tool, resource y prompt
- ✅ Testear manejo de errores
- ✅ Usar `pytest` y `pytest-asyncio`

```python
import pytest
from fastmcp import FastMCP, Client

@pytest.mark.asyncio
async def test_tool():
    mcp = FastMCP("TestServer")

    @mcp.tool
    def add(a: int, b: int) -> int:
        return a + b

    async with Client(mcp) as client:
        result = await client.call_tool("add", {"a": 5, "b": 3})
        assert result == 8
```

### 9. Performance

- ✅ Usar async/await para I/O
- ✅ Implementar caché para operaciones costosas
- ✅ Usar connection pooling para bases de datos
- ✅ Considerar `mount()` vs `import_server()` según necesidades
- ❌ Evitar operaciones bloqueantes en el event loop

### 10. Security

- ✅ Validar todas las entradas
- ✅ Usar autenticación para APIs públicas
- ✅ Implementar rate limiting
- ✅ Sanitizar URIs de recursos
- ✅ Usar `mask_error_details=True` en producción
- ❌ No exponer stack traces al cliente

---

## Resumen de Verificación

Esta documentación cubre todas las funcionalidades principales de FastMCP:

- ✅ **Instalación y requisitos**
- ✅ **FastMCP Server Object y configuración**
- ✅ **Tools** con decorador, parámetros, tipos de retorno, async, manejo de errores
- ✅ **Resources** con URIs dinámicas, templates, clases directas
- ✅ **Prompts** con parámetros, multi-mensaje, async
- ✅ **Context** con todos los métodos (logging, progress, resources, prompts, sampling, elicitation, state, HTTP, tokens)
- ✅ **Client** con creación, operaciones, multi-servidor, configuración
- ✅ **Authentication** con 8+ proveedores OAuth, JWT, API Keys
- ✅ **Transports** (STDIO, HTTP Streamable, SSE) con configuración y CLI
- ✅ **Middleware** con implementación, hooks, middleware integrado (timing, logging, rate limiting, caching, error handling)
- ✅ **Server Composition** con import_server, mount, proxy, tag filtering
- ✅ **Storage Backends** con encriptación, TTL, Redis, DynamoDB, Disk
- ✅ **Deployment** (local, HTTP, Docker, systemd, nginx)
- ✅ **Best Practices** completas para todos los componentes

Todas las funcionalidades de FastMCP están documentadas con ejemplos de uso completos.
