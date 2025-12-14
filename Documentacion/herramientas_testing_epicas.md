# Herramientas de Testing Investigadas para Épicas

## 1. pytest - Framework Principal de Testing

### Instalación y Configuración
```bash
uv add --dev pytest
```

### Características Principales
- **Fixtures**: Sistema poderoso para setup/teardown de tests
- **Parametrización**: Ejecutar el mismo test con diferentes datos
- **Markers**: Categorización y filtrado de tests
- **Plugins**: Extensibilidad mediante plugins

### Fixtures Relevantes para Épicas
```python
import pytest

@pytest.fixture
def epic_data():
    """Fixture que provee datos de épica válidos."""
    return {
        "project": 309804,
        "subject": "Test Epic",
        "description": "Test Description",
        "color": "#A5694F"
    }

@pytest.fixture
def mock_api_client(mocker):
    """Fixture que mockea el cliente de API."""
    from src.taiga_client import TaigaAPIClient
    return mocker.MagicMock(spec=TaigaAPIClient)
```

### Parametrización para Tests de Épicas
```python
@pytest.mark.parametrize("status,expected", [
    (1, "New"),
    (2, "Ready"),
    (3, "In Progress"),
    (4, "Ready for Test"),
    (5, "Done")
])
def test_epic_status_mapping(status, expected):
    """Test que verifica el mapeo de estados."""
    pass
```

### Markers Útiles
```python
@pytest.mark.unit          # Tests unitarios
@pytest.mark.integration   # Tests de integración
@pytest.mark.functional    # Tests funcionales
@pytest.mark.slow         # Tests que toman tiempo
@pytest.mark.epic         # Tests específicos de épicas
```

## 2. pytest-cov - Cobertura de Código

### Instalación
```bash
uv add --dev pytest-cov
```

### Configuración en pyproject.toml
```toml
[tool.pytest.ini_options]
addopts = [
    "--cov=src",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=80"
]

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "**/__init__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:"
]
```

### Comandos Útiles
```bash
# Ejecutar tests con cobertura
uv run pytest --cov=src

# Generar reporte HTML
uv run pytest --cov=src --cov-report=html

# Ver líneas no cubiertas
uv run pytest --cov=src --cov-report=term-missing
```

## 3. pytest-mock - Simplificación de Mocks

### Instalación
```bash
uv add --dev pytest-mock
```

### Fixture mocker
```python
def test_create_epic_with_mock(mocker):
    """Test creación de épica con mock."""
    # Mock del cliente HTTP
    mock_post = mocker.patch('httpx.post')
    mock_post.return_value.json.return_value = {
        "id": 456789,
        "subject": "Test Epic"
    }

    # Mock del repositorio
    mock_repo = mocker.MagicMock()
    mock_repo.create.return_value = Epic(id=456789)
```

### Spy para Verificación
```python
def test_epic_notification_sent(mocker):
    """Verificar que se envía notificación."""
    spy = mocker.spy(NotificationService, 'send')

    # Ejecutar operación
    create_epic(data)

    # Verificar que se llamó
    spy.assert_called_once()
```

## 4. httpx - Cliente HTTP Moderno

### Instalación
```bash
uv add httpx
```

### Cliente para API de Taiga
```python
import httpx
from typing import Dict, Any

class TaigaEpicsClient:
    """Cliente HTTP para épicas de Taiga."""

    def __init__(self, base_url: str, auth_token: str):
        self.client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

    async def create_epic(self, data: Dict[str, Any]) -> Dict:
        """Crear una nueva épica."""
        response = self.client.post("/api/v1/epics", json=data)
        response.raise_for_status()
        return response.json()
```

### Testing con httpx
```python
import pytest
from httpx import Response

@pytest.fixture
def mock_httpx_client(mocker):
    """Mock del cliente httpx."""
    mock_client = mocker.MagicMock()
    mock_response = Response(
        200,
        json={"id": 456789, "subject": "Test"}
    )
    mock_client.post.return_value = mock_response
    return mock_client
```

## 5. pytest-httpx - Mocking Específico para httpx

### Instalación
```bash
uv add --dev pytest-httpx
```

### Uso con Épicas
```python
import pytest
from pytest_httpx import HTTPXMock

def test_list_epics(httpx_mock: HTTPXMock):
    """Test listar épicas con mock de httpx."""
    # Configurar mock
    httpx_mock.add_response(
        url="https://api.taiga.io/api/v1/epics",
        json=[
            {"id": 1, "subject": "Epic 1"},
            {"id": 2, "subject": "Epic 2"}
        ]
    )

    # Ejecutar código que usa httpx
    epics = list_epics(project=309804)

    # Verificar
    assert len(epics) == 2
```

## 6. pydantic - Validación de Datos

### Instalación
```bash
uv add pydantic
```

### Modelos para Épicas
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class EpicModel(BaseModel):
    """Modelo Pydantic para épicas."""

    id: Optional[int] = None
    ref: Optional[int] = None
    version: int = 1
    subject: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    color: str = Field(default="#A5694F", regex="^#[0-9A-Fa-f]{6}$")
    project: int = Field(..., gt=0)
    assigned_to: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    client_requirement: bool = False
    team_requirement: bool = False
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None

    @validator('color')
    def validate_color(cls, v):
        """Validar formato de color hexadecimal."""
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Color must be in hex format #RRGGBB')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### Schemas para Herramientas MCP
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class CreateEpicSchema(BaseModel):
    """Schema para crear épica."""
    auth_token: str = Field(..., description="Token de autenticación")
    project: int = Field(..., description="ID del proyecto")
    subject: str = Field(..., description="Título de la épica")
    description: Optional[str] = Field(None, description="Descripción")
    color: Optional[str] = Field("#A5694F", description="Color en hex")
    assigned_to: Optional[int] = Field(None, description="ID usuario asignado")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags")

class ListEpicsSchema(BaseModel):
    """Schema para listar épicas."""
    auth_token: str = Field(..., description="Token de autenticación")
    project: Optional[int] = Field(None, description="Filtrar por proyecto")
    status: Optional[int] = Field(None, description="Filtrar por estado")
    assigned_to: Optional[int] = Field(None, description="Filtrar por asignado")
    tags: Optional[List[str]] = Field(None, description="Filtrar por tags")
```

## 7. fastmcp - Framework MCP

### Instalación
```bash
uv add fastmcp
```

### Definición de Herramientas para Épicas
```python
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

mcp = FastMCP()

@mcp.tool()
async def create_epic(
    auth_token: str = Field(..., description="Token de autenticación"),
    project: int = Field(..., description="ID del proyecto"),
    subject: str = Field(..., description="Título de la épica"),
    description: Optional[str] = Field(None, description="Descripción"),
    color: Optional[str] = Field("#A5694F", description="Color hex"),
    tags: Optional[List[str]] = Field(None, description="Lista de tags")
) -> Dict[str, Any]:
    """
    Crear una nueva épica en Taiga.

    Args:
        auth_token: Token de autenticación de Taiga
        project: ID del proyecto donde crear la épica
        subject: Título de la épica
        description: Descripción detallada (opcional)
        color: Color en formato hexadecimal (opcional)
        tags: Lista de tags (opcional)

    Returns:
        Diccionario con la épica creada

    Example:
        >>> epic = await create_epic(
        ...     auth_token="Bearer abc123",
        ...     project=309804,
        ...     subject="Nueva Épica",
        ...     description="Descripción de la épica",
        ...     tags=["feature", "v2"]
        ... )
    """
    # Implementación aquí
    pass
```

### Testing de Herramientas MCP
```python
import pytest
from fastmcp import FastMCP

@pytest.fixture
def mcp_server():
    """Fixture para servidor MCP."""
    return FastMCP()

@pytest.fixture
def epic_tools(mcp_server):
    """Fixture para herramientas de épicas."""
    from src.application.tools.epic_tools import EpicTools
    return EpicTools(mcp_server)

async def test_create_epic_tool(epic_tools, mocker):
    """Test de herramienta create_epic."""
    mock_client = mocker.MagicMock()
    epic_tools.set_client(mock_client)

    result = await epic_tools.create_epic(
        auth_token="token",
        project=309804,
        subject="Test Epic"
    )

    mock_client.create_epic.assert_called_once()
```

## 8. pytest-asyncio - Testing Asíncrono

### Instalación
```bash
uv add --dev pytest-asyncio
```

### Configuración
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### Tests Asíncronos para Épicas
```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_create_epic():
    """Test asíncrono de creación de épica."""
    epic = await create_epic_async(data)
    assert epic.id is not None

@pytest.mark.asyncio
async def test_bulk_create_epics():
    """Test creación masiva asíncrona."""
    tasks = [
        create_epic_async({"subject": f"Epic {i}"})
        for i in range(10)
    ]
    epics = await asyncio.gather(*tasks)
    assert len(epics) == 10
```

## 9. responses - Mock de Requests HTTP

### Instalación
```bash
uv add --dev responses
```

### Mocking de API de Taiga
```python
import responses
import requests

@responses.activate
def test_epic_api_call():
    """Test con mock de responses."""
    responses.add(
        responses.POST,
        'https://api.taiga.io/api/v1/epics',
        json={'id': 456789, 'subject': 'New Epic'},
        status=201
    )

    response = requests.post(
        'https://api.taiga.io/api/v1/epics',
        json={'subject': 'New Epic'}
    )

    assert response.status_code == 201
    assert response.json()['id'] == 456789
```

## 10. factory-boy - Generación de Datos de Prueba

### Instalación
```bash
uv add --dev factory-boy
```

### Factories para Épicas
```python
import factory
from factory import Factory, Faker, SubFactory
from datetime import datetime

class EpicFactory(Factory):
    """Factory para generar épicas de prueba."""

    class Meta:
        model = dict

    id = factory.Sequence(lambda n: n + 1)
    ref = factory.Sequence(lambda n: n + 1)
    version = 1
    subject = Faker('sentence', nb_words=4)
    description = Faker('text')
    color = factory.LazyFunction(lambda: f"#{Faker('hex_color')[1:]}")
    project = 309804
    assigned_to = Faker('random_int', min=1, max=1000)
    tags = factory.List([Faker('word') for _ in range(3)])
    client_requirement = Faker('boolean')
    team_requirement = Faker('boolean')
    created_date = factory.LazyFunction(datetime.now)
    modified_date = factory.LazyFunction(datetime.now)

class RelatedUserStoryFactory(Factory):
    """Factory para relaciones epic-userstory."""

    class Meta:
        model = dict

    id = factory.Sequence(lambda n: n + 1)
    epic = 456789
    user_story = factory.Sequence(lambda n: n + 10000)
    order = factory.Sequence(lambda n: n)
```

## 11. faker - Datos Realistas de Prueba

### Instalación
```bash
uv add --dev faker
```

### Generación de Datos para Épicas
```python
from faker import Faker

fake = Faker('es_ES')  # Español para datos localizados

def generate_epic_data():
    """Generar datos de épica realistas."""
    return {
        'subject': fake.catch_phrase(),
        'description': fake.paragraph(nb_sentences=5),
        'color': fake.hex_color(),
        'tags': [fake.word() for _ in range(3)],
        'client_requirement': fake.boolean(chance_of_getting_true=30),
        'team_requirement': fake.boolean(chance_of_getting_true=70)
    }

# Datos específicos del dominio
epic_subjects = [
    "Módulo de Autenticación",
    "Sistema de Notificaciones",
    "Dashboard Analytics",
    "API REST v2",
    "Migración a Cloud"
]

epic_colors = [
    "#A5694F",  # Brown
    "#B83A3A",  # Red
    "#3AB83A",  # Green
    "#3A3AB8",  # Blue
    "#B83AB8"   # Purple
]
```

## Resumen de Herramientas Seleccionadas

| Librería | Propósito | Versión Recomendada |
|----------|-----------|-------------------|
| pytest | Framework principal | >= 7.4.0 |
| pytest-cov | Cobertura de código | >= 4.1.0 |
| pytest-mock | Simplificación mocks | >= 3.11.0 |
| pytest-httpx | Mock de httpx | >= 0.21.0 |
| pytest-asyncio | Tests asíncronos | >= 0.21.0 |
| httpx | Cliente HTTP | >= 0.25.0 |
| pydantic | Validación datos | >= 2.4.0 |
| fastmcp | Framework MCP | >= 0.1.0 |
| factory-boy | Factories de test | >= 3.3.0 |
| faker | Datos de prueba | >= 19.0.0 |

## Configuración Completa para el Proyecto

```toml
# pyproject.toml
[project]
name = "taiga-mcp-epics"
version = "0.1.0"
dependencies = [
    "httpx>=0.25.0",
    "pydantic>=2.4.0",
    "fastmcp>=0.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
    "pytest-httpx>=0.21.0",
    "pytest-asyncio>=0.21.0",
    "factory-boy>=3.3.0",
    "faker>=19.0.0",
]

[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
addopts = [
    "-v",
    "--strict-markers",
    "--cov=src",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=80"
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "functional: Functional tests",
    "epic: Epic-specific tests",
    "slow: Tests that take significant time"
]
```

Esta investigación proporciona toda la información necesaria para implementar los tests de épicas siguiendo las mejores prácticas y aprovechando las capacidades de cada librería.
