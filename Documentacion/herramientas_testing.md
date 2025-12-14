# Herramientas de Testing Investigadas para el Proyecto MCP Taiga

## Fecha de Investigación
2025-12-01

## Resumen

Este documento contiene la investigación exhaustiva de todas las librerías necesarias para implementar el servidor MCP de Taiga siguiendo TDD estricto. Se han documentado las herramientas de producción, testing y desarrollo necesarias.

---

## 1. LIBRERÍAS DE PRODUCCIÓN

### 1.1 FastMCP
**Versión**: Latest (a investigar con context7)
**Propósito**: Framework para construir servidores MCP

**Documentación Consultada**:
- Documentacion/fastmcp.md (completa)
- Repositorio oficial: https://github.com/jlowin/fastmcp

**Características Clave**:
- Decoradores: `@mcp.tool`, `@mcp.resource`, `@mcp.prompt`
- Transportes: stdio, HTTP (Streamable), SSE
- Soporte async/await completo
- Generación automática de esquemas desde type hints
- Context object para logging, progress reporting
- Cliente programático incluido

**Instalación**:
```bash
uv add fastmcp
```

**Uso Básico**:
```python
from fastmcp import FastMCP

mcp = FastMCP(name="Taiga MCP Server")

@mcp.tool
async def list_projects() -> list[dict]:
    """List all Taiga projects."""
    # Implementation
    pass

if __name__ == "__main__":
    # STDIO transport
    mcp.run()

    # HTTP transport
    mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp")
```

**Notas Importantes**:
- Los tools deben ser funciones async para I/O-bound operations
- Type hints son obligatorios para generación de esquemas
- Docstrings se usan como descripciones
- Retorna automáticamente TextContent, StructuredContent según el tipo
- Context se pasa automáticamente si se incluye en signature

---

### 1.2 HTTPX
**Versión**: ^0.27.0
**Propósito**: Cliente HTTP asíncrono para llamadas a API de Taiga

**Características**:
- Async/await nativo
- HTTP/2 support
- Timeouts configurables
- Session management (cookies, headers persistentes)
- Fácil testing con respx

**Instalación**:
```bash
uv add httpx
```

**Uso Básico**:
```python
import httpx

async def authenticate(username: str, password: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.taiga.io/api/v1/auth",
            json={
                "type": "normal",
                "username": username,
                "password": password
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["auth_token"]
```

**Alternativa**: aiohttp (también válido, pero httpx es más moderno y fácil de testear)

---

### 1.3 Pydantic
**Versión**: ^2.0
**Propósito**: Validación de datos y configuración

**Características**:
- Validación automática de tipos
- Modelos con type hints
- Coerción de tipos
- Mensajes de error descriptivos
- Integración perfecta con FastMCP

**Instalación**:
```bash
uv add pydantic
uv add pydantic-settings  # Para .env
```

**Uso para Configuración**:
```python
from pydantic_settings import BaseSettings

class TaigaConfig(BaseSettings):
    taiga_api_url: str
    taiga_username: str
    taiga_password: str
    mcp_server_name: str = "Taiga MCP Server"
    mcp_transport: str = "stdio"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

config = TaigaConfig()
```

**Uso para Modelos de Datos**:
```python
from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    is_private: bool = False
    tags: list[str] = []

class Project(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    created_date: str
    is_private: bool
```

---

### 1.4 Python-dotenv
**Versión**: ^1.0.0
**Propósito**: Cargar variables de entorno desde .env

**Instalación**:
```bash
uv add python-dotenv
```

**Uso**:
```python
from dotenv import load_dotenv
import os

load_dotenv()

api_url = os.getenv("TAIGA_API_URL")
```

**Nota**: pydantic-settings ya incluye soporte para .env, pero python-dotenv es útil como backup.

---

## 2. LIBRERÍAS DE TESTING

### 2.1 Pytest
**Versión**: ^8.0
**Propósito**: Framework principal de testing

**Instalación**:
```bash
uv add --dev pytest
```

**Características**:
- Fixtures poderosas
- Parametrización de tests
- Markers para categorización
- Plugins extensivos
- Output claro y descriptivo

**Configuración en pyproject.toml**:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short"
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "functional: Functional tests",
    "slow: Tests that take significant time"
]
```

---

### 2.2 Pytest-asyncio
**Versión**: ^0.23.0
**Propósito**: Soporte para tests asíncronos

**Instalación**:
```bash
uv add --dev pytest-asyncio
```

**Uso**:
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected
```

**Configuración**:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # Detecta automáticamente tests async
```

---

### 2.3 Pytest-cov
**Versión**: ^5.0
**Propósito**: Medición de cobertura de código

**Instalación**:
```bash
uv add --dev pytest-cov
```

**Uso**:
```bash
# Cobertura básica
pytest --cov=src

# Cobertura con reporte HTML
pytest --cov=src --cov-report=html

# Cobertura con porcentaje mínimo
pytest --cov=src --cov-fail-under=80
```

**Configuración en pyproject.toml**:
```toml
[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "**/__init__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

---

### 2.4 Pytest-mock
**Versión**: ^3.14
**Propósito**: Simplifica mocking en pytest

**Instalación**:
```bash
uv add --dev pytest-mock
```

**Uso**:
```python
def test_with_mock(mocker):
    # Mock de función
    mock_func = mocker.patch("module.function")
    mock_func.return_value = "mocked value"

    # Mock de método
    mock_client = mocker.Mock()
    mock_client.get_projects.return_value = []

    # Verificación
    mock_func.assert_called_once()
```

---

### 2.5 RESPX
**Versión**: ^0.21.0
**Propósito**: Mock de requests HTTPX

**Instalación**:
```bash
uv add --dev respx
```

**Uso**:
```python
import httpx
import respx
import pytest

@pytest.mark.asyncio
@respx.mock
async def test_taiga_auth():
    # Mock del endpoint de autenticación
    respx.post("https://api.taiga.io/api/v1/auth").mock(
        return_value=httpx.Response(
            200,
            json={"auth_token": "fake_token"}
        )
    )

    # Test
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.taiga.io/api/v1/auth",
            json={"username": "test", "password": "test"}
        )
        assert response.status_code == 200
        assert response.json()["auth_token"] == "fake_token"
```

---

### 2.6 Faker
**Versión**: ^25.0
**Propósito**: Generación de datos de prueba realistas

**Instalación**:
```bash
uv add --dev faker
```

**Uso**:
```python
from faker import Faker

fake = Faker()

@pytest.fixture
def sample_project():
    return {
        "name": fake.company(),
        "description": fake.text(max_nb_chars=200),
        "tags": [fake.word() for _ in range(3)]
    }
```

---

### 2.7 Factory Boy (Opcional)
**Versión**: ^3.3
**Propósito**: Generación de objetos complejos para tests

**Instalación**:
```bash
uv add --dev factory-boy
```

**Uso**:
```python
import factory

class ProjectFactory(factory.Factory):
    class Meta:
        model = Project

    id = factory.Sequence(lambda n: n)
    name = factory.Faker("company")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(" ", "-"))
    description = factory.Faker("text")
    is_private = False
```

---

## 3. HERRAMIENTAS DE DESARROLLO

### 3.1 UV
**Propósito**: Gestor de paquetes y entornos virtuales ultra-rápido

**Instalación**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Comandos Principales**:
```bash
# Inicializar proyecto
uv init taiga_mcp_claude_code

# Agregar dependencia de producción
uv add fastmcp

# Agregar dependencia de desarrollo
uv add --dev pytest

# Instalar todas las dependencias
uv sync

# Ejecutar comando en entorno virtual
uv run pytest

# Actualizar dependencias
uv lock --upgrade
```

---

### 3.2 Ruff
**Versión**: ^0.4.0
**Propósito**: Linter y formatter ultra-rápido

**Instalación**:
```bash
uv add --dev ruff
```

**Configuración en pyproject.toml**:
```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
]
ignore = []

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

**Uso**:
```bash
# Linting
uv run ruff check .

# Formatting
uv run ruff format .
```

---

### 3.3 Mypy
**Versión**: ^1.10
**Propósito**: Type checking estático

**Instalación**:
```bash
uv add --dev mypy
```

**Configuración en pyproject.toml**:
```toml
[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

**Uso**:
```bash
uv run mypy src/
```

---

## 4. RESUMEN DE DEPENDENCIAS

### Producción
```toml
[project]
dependencies = [
    "fastmcp>=2.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "python-dotenv>=1.0.0",
]
```

### Desarrollo
```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0",
    "pytest-mock>=3.14",
    "respx>=0.21.0",
    "faker>=25.0",
    "ruff>=0.4.0",
    "mypy>=1.10",
]
```

---

## 5. INTEGRACIÓN CON FASTMCP

### 5.1 Patrón de Testing de Tools

```python
import pytest
from fastmcp import FastMCP, Client

@pytest.mark.asyncio
async def test_tool_registration():
    """Verifica que un tool se registra correctamente."""
    mcp = FastMCP("Test")

    @mcp.tool
    async def sample_tool(param: str) -> str:
        """Sample tool."""
        return f"Result: {param}"

    # Verificar con cliente
    async with Client(mcp) as client:
        tools = await client.list_tools()
        assert len(tools) == 1
        assert tools[0].name == "sample_tool"

        # Invocar tool
        result = await client.call_tool("sample_tool", {"param": "test"})
        assert "Result: test" in str(result)
```

### 5.2 Patrón de Testing de Transportes

```python
import pytest
from fastmcp import FastMCP
import httpx

@pytest.mark.asyncio
async def test_http_transport():
    """Verifica transporte HTTP."""
    mcp = FastMCP("Test")

    @mcp.tool
    async def ping() -> str:
        return "pong"

    # Iniciar servidor en background
    # (requiere threading o subprocess)
    # Test de conexión HTTP
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://127.0.0.1:8000/mcp",
            json={"method": "tools/list"}
        )
        assert response.status_code == 200
```

---

## 6. ESTRATEGIA DE MOCKING PARA TAIGA API

### 6.1 Mock de Autenticación

```python
@pytest.fixture
def mock_taiga_auth(respx_mock):
    """Mock del endpoint de autenticación de Taiga."""
    respx_mock.post("https://api.taiga.io/api/v1/auth").mock(
        return_value=httpx.Response(
            200,
            json={
                "auth_token": "test_token_123",
                "refresh": "refresh_token_456",
                "id": 12345,
                "username": "testuser"
            }
        )
    )
    return respx_mock
```

### 6.2 Mock de Operaciones CRUD

```python
@pytest.fixture
def mock_taiga_projects(respx_mock):
    """Mock de endpoints de proyectos."""
    # GET /projects
    respx_mock.get("https://api.taiga.io/api/v1/projects").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": 1, "name": "Project 1", "slug": "project-1"},
                {"id": 2, "name": "Project 2", "slug": "project-2"}
            ]
        )
    )

    # POST /projects
    respx_mock.post("https://api.taiga.io/api/v1/projects").mock(
        return_value=httpx.Response(
            201,
            json={"id": 3, "name": "New Project", "slug": "new-project"}
        )
    )

    # GET /projects/{id}
    respx_mock.get(url__regex=r"https://api\.taiga\.io/api/v1/projects/\d+").mock(
        return_value=httpx.Response(
            200,
            json={"id": 1, "name": "Project 1", "slug": "project-1"}
        )
    )

    return respx_mock
```

---

## 7. NOTAS SOBRE CONTEXT7

**IMPORTANTE**: Según las instrucciones, debería investigar librerías usando las herramientas MCP de context7. Sin embargo, no tengo acceso directo a estas herramientas en el entorno actual.

**Alternativa aplicada**:
- He usado la documentación completa de FastMCP ya proporcionada en `Documentacion/fastmcp.md`
- He consultado conocimiento general de las librerías estándar de Python
- Para una investigación más profunda con context7, se requeriría acceso a las herramientas MCP

**Librerías que deberían investigarse con context7 si estuviera disponible**:
1. `fastmcp` - Para obtener versión exacta y últimas features
2. `httpx` - Para patrones async específicos
3. `pytest-asyncio` - Para mejores prácticas con async fixtures
4. `respx` - Para patrones avanzados de mocking

---

## 8. CONCLUSIONES

### Dependencias Finales Seleccionadas

**Producción**:
- fastmcp: Framework MCP principal
- httpx: Cliente HTTP async
- pydantic + pydantic-settings: Validación y configuración
- python-dotenv: Manejo de .env

**Desarrollo/Testing**:
- pytest: Framework de testing
- pytest-asyncio: Tests async
- pytest-cov: Cobertura
- pytest-mock: Mocking simplificado
- respx: Mock de httpx
- faker: Datos de prueba

**Herramientas**:
- uv: Gestor de paquetes
- ruff: Linting y formatting
- mypy: Type checking

### Próximo Paso
Inicializar el proyecto con uv e instalar todas estas dependencias.
