# Guía de Tests del Proyecto Taiga MCP

## Estructura de Tests

```
tests/
├── conftest.py                         # Fixtures globales y configuración pytest ✅
├── unit/                               # Tests unitarios (aislados, rápidos)
│   ├── test_server.py                  # Core del servidor MCP ✅
│   ├── test_configuration.py           # Carga de configuración y .env ✅
│   └── tools/                          # Tests de herramientas
│       ├── test_auth_tools.py          # Herramientas de autenticación ✅
│       ├── test_project_tools.py       # Gestión de proyectos (22 funcionalidades) ✅
│       ├── test_userstory_tools.py     # Historias de usuario (completo) ✅
│       ├── test_issue_tools.py         # Gestión de issues ✅
│       ├── test_task_tools.py          # Gestión de tareas ✅
│       ├── test_milestone_tools.py     # Gestión de sprints ✅
│       ├── test_epic_tools.py          # Gestión de épicas ✅
│       ├── test_wiki_tools.py          # Gestión de wiki (10 funcionalidades) ✅
│       ├── test_user_tools.py          # Estadísticas de usuarios ✅
│       ├── test_membership_tools.py    # Gestión de membresías (5 funcionalidades) ✅
│       └── test_webhook_tools.py       # Gestión de webhooks (6 funcionalidades) ✅
├── integration/                        # Tests de integración (con Taiga real)
│   ├── test_auth_integration.py        # Autenticación real con Taiga ✅
│   ├── test_projects_integration.py    # Proyectos con API real ✅
│   ├── test_userstories_integration.py # User stories integración ✅
│   ├── test_issues_integration.py      # Issues integración ✅
│   ├── test_tasks_integration.py       # Tareas integración ✅
│   ├── test_milestones_integration.py  # Sprints integración ✅
│   ├── test_epics_integration.py       # Épicas integración ✅
│   ├── test_wiki_integration.py        # Wiki integración ✅
│   ├── test_users_integration.py       # Usuarios integración ✅
│   ├── test_memberships_integration.py # Membresías integración ✅
│   └── test_webhooks_integration.py    # Webhooks integración ✅
└── functional/                         # Tests End-to-End (pendientes)
```

**Archivos totales**: 25
**Tests totales**: 585+
**Estado**: TODOS EN ROJO ✅ (ModuleNotFoundError - esperado en TDD)

## Ejecutar Tests

### Todos los tests
```bash
uv run pytest
```

### Con output detallado
```bash
uv run pytest -v
```

### Solo tests unitarios
```bash
uv run pytest tests/unit -m unit
```

### Solo tests de integración
```bash
uv run pytest tests/integration -m integration
```

### Solo tests funcionales
```bash
uv run pytest tests/functional -m functional
```

### Tests de un módulo específico
```bash
# Solo tests de proyectos
uv run pytest tests/unit/tools/test_project_tools.py

# Solo tests de autenticación
uv run pytest tests/unit/test_authentication.py
```

### Tests con marcadores específicos
```bash
# Solo tests relacionados con Taiga
uv run pytest -m taiga

# Solo tests de transporte
uv run pytest -m transport

# Solo tests de autenticación
uv run pytest -m auth

# Excluir tests lentos
uv run pytest -m "not slow"
```

### Con cobertura de código
```bash
# Generar reporte de cobertura
uv run pytest --cov=src --cov-report=html

# Ver cobertura en terminal
uv run pytest --cov=src --cov-report=term-missing

# Con umbral mínimo (falla si cobertura < 80%)
uv run pytest --cov=src --cov-fail-under=80
```

### Tests en paralelo (requiere pytest-xdist)
```bash
# Instalar plugin
uv add --dev pytest-xdist

# Ejecutar con 4 procesos
uv run pytest -n 4
```

## Escribir Nuevos Tests

### Estructura básica de un test

```python
import pytest
from unittest.mock import MagicMock, AsyncMock

class TestFeature:
    """Descripción de la feature testeada."""

    @pytest.mark.unit  # Marcador de tipo
    def test_comportamiento_especifico(self):
        """
        RF-XXX: Descripción del requerimiento.

        Explicación detallada de qué se está testeando y por qué.
        """
        # Arrange - Preparar datos y contexto
        dato_entrada = "valor"
        esperado = "resultado"

        # Act - Ejecutar la acción
        resultado = funcion_a_testear(dato_entrada)

        # Assert - Verificar resultado
        assert resultado == esperado
```

### Test asíncrono

```python
@pytest.mark.asyncio
async def test_operacion_asincrona(self):
    """Test de operación asíncrona."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get.return_value = {"data": "value"}

    # Act
    resultado = await operacion_async(mock_client)

    # Assert
    assert resultado["data"] == "value"
    mock_client.get.assert_called_once()
```

### Test con fixtures

```python
def test_con_fixture(self, mcp_server):
    """Test usando fixture del servidor MCP."""
    # La fixture mcp_server viene de conftest.py
    assert mcp_server.name == "TestTaigaServer"
```

### Test parametrizado

```python
@pytest.mark.parametrize("input,expected", [
    ("input1", "output1"),
    ("input2", "output2"),
    ("input3", "output3"),
])
def test_multiples_casos(self, input, expected):
    """Test con múltiples casos de entrada."""
    resultado = funcion(input)
    assert resultado == expected
```

## Fixtures Disponibles

### Globales (en conftest.py)

| Fixture | Scope | Descripción |
|---------|-------|-------------|
| `test_env` | session | Variables de entorno (.env) |
| `mcp_server` | function | Instancia de FastMCP |
| `mock_taiga_auth_response` | function | Respuesta de auth mockeada |
| `mock_project_response` | function | Proyecto mockeado |
| `mock_userstory_response` | function | User story mockeada |
| `mock_issue_response` | function | Issue mockeado |
| `mock_epic_response` | function | Épica mockeada |
| `mock_task_response` | function | Tarea mockeada |
| `mock_milestone_response` | function | Sprint mockeado |
| `real_auth_token` | function | Token real de Taiga (async) |
| `test_data_tracker` | function | Tracking para cleanup |

### Uso de fixtures

```python
def test_ejemplo(self, mcp_server, mock_project_response):
    """Ejemplo usando múltiples fixtures."""
    # mcp_server está configurado
    assert mcp_server is not None

    # mock_project_response tiene datos de prueba
    assert mock_project_response["id"] == 1
    assert mock_project_response["name"] == "Test Project"
```

## Marcadores (Markers)

### Marcadores de tipo
- `@pytest.mark.unit` - Tests unitarios
- `@pytest.mark.integration` - Tests de integración
- `@pytest.mark.functional` - Tests funcionales/E2E

### Marcadores de módulo
- `@pytest.mark.taiga` - Tests relacionados con Taiga
- `@pytest.mark.mcp` - Tests del protocolo MCP
- `@pytest.mark.transport` - Tests de transporte
- `@pytest.mark.auth` - Tests de autenticación
- `@pytest.mark.projects` - Tests de proyectos
- `@pytest.mark.userstories` - Tests de historias de usuario
- `@pytest.mark.issues` - Tests de issues
- `@pytest.mark.tasks` - Tests de tareas
- `@pytest.mark.milestones` - Tests de sprints
- `@pytest.mark.epics` - Tests de épicas
- `@pytest.mark.wiki` - Tests de wiki
- `@pytest.mark.users` - Tests de usuarios
- `@pytest.mark.memberships` - Tests de membresías
- `@pytest.mark.webhooks` - Tests de webhooks

### Marcadores especiales
- `@pytest.mark.slow` - Tests que tardan > 1s
- `@pytest.mark.asyncio` - Tests asíncronos
- `@pytest.mark.e2e` - Tests End-to-End

### Uso de marcadores

```python
@pytest.mark.unit
@pytest.mark.taiga
@pytest.mark.asyncio
async def test_taiga_operation(self):
    """Test marcado como unit, taiga y asyncio."""
    pass
```

## Mocking y Stubs

### Mock de cliente HTTP

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_http_call(self):
    """Test con mock de httpx."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"key": "value"}
    mock_client.get.return_value = mock_response

    with patch('httpx.AsyncClient', return_value=mock_client):
        result = await function_that_uses_http()

    assert result["key"] == "value"
    mock_client.get.assert_called_once()
```

### Mock con respx

```python
import respx

@respx.mock
@pytest.mark.asyncio
async def test_with_respx(self):
    """Test usando respx para mockear HTTP."""
    route = respx.get("https://api.taiga.io/api/v1/projects").mock(
        return_value=httpx.Response(200, json=[{"id": 1}])
    )

    result = await get_projects()

    assert len(result) == 1
    assert route.called
```

## Patrones de Test

### 1. AAA (Arrange, Act, Assert)
```python
def test_aaa_pattern(self):
    """Ejemplo del patrón AAA."""
    # Arrange - Preparar
    usuario = Usuario(nombre="Juan")

    # Act - Actuar
    resultado = usuario.cambiar_nombre("Pedro")

    # Assert - Verificar
    assert usuario.nombre == "Pedro"
    assert resultado is True
```

### 2. Given-When-Then (BDD)
```python
def test_bdd_pattern(self):
    """Ejemplo del patrón BDD."""
    # Given - Dado un usuario existente
    usuario = Usuario(nombre="Juan")

    # When - Cuando cambia su nombre
    usuario.cambiar_nombre("Pedro")

    # Then - Entonces el nombre debe actualizarse
    assert usuario.nombre == "Pedro"
```

### 3. Test con cleanup
```python
@pytest.mark.asyncio
async def test_with_cleanup(self):
    """Test con limpieza garantizada."""
    recurso = None
    try:
        # Arrange & Act
        recurso = await crear_recurso()
        resultado = await usar_recurso(recurso)

        # Assert
        assert resultado is not None
    finally:
        # Cleanup
        if recurso:
            await eliminar_recurso(recurso)
```

## Mejores Prácticas

### 1. Nombres descriptivos
```python
# ✅ BUENO
def test_crear_proyecto_con_nombre_vacio_debe_lanzar_excepcion(self):
    pass

# ❌ MALO
def test_project_1(self):
    pass
```

### 2. Un assert por concepto
```python
# ✅ BUENO
def test_usuario_creado_correctamente(self):
    usuario = crear_usuario("Juan", "juan@example.com")
    assert usuario.nombre == "Juan"

def test_usuario_tiene_email_correcto(self):
    usuario = crear_usuario("Juan", "juan@example.com")
    assert usuario.email == "juan@example.com"

# ❌ MALO
def test_usuario(self):
    usuario = crear_usuario("Juan", "juan@example.com")
    assert usuario.nombre == "Juan"
    assert usuario.email == "juan@example.com"
    assert usuario.activo is True
    assert usuario.id is not None
```

### 3. Tests independientes
```python
# ✅ BUENO - Cada test crea sus propios datos
def test_actualizar_proyecto(self):
    proyecto = crear_proyecto("Test")
    proyecto.actualizar(nombre="Nuevo")
    assert proyecto.nombre == "Nuevo"

# ❌ MALO - Depende de estado compartido
def test_actualizar_proyecto(self):
    # Asume que self.proyecto existe de otro test
    self.proyecto.actualizar(nombre="Nuevo")
    assert self.proyecto.nombre == "Nuevo"
```

### 4. Uso de fixtures para DRY
```python
# ✅ BUENO
@pytest.fixture
def proyecto_con_tareas(self):
    proyecto = Proyecto("Test")
    proyecto.agregar_tarea("Tarea 1")
    proyecto.agregar_tarea("Tarea 2")
    return proyecto

def test_contar_tareas(self, proyecto_con_tareas):
    assert proyecto_con_tareas.contar_tareas() == 2
```

## Debugging de Tests

### Ver output completo
```bash
uv run pytest -v -s
```

### Ver solo tests que fallan
```bash
uv run pytest --lf  # last failed
uv run pytest --ff  # failed first
```

### Debugger interactivo
```bash
uv run pytest --pdb  # Abre pdb cuando falla un test
```

### Ver warnings
```bash
uv run pytest -W error  # Convierte warnings en errores
```

## Reporte de Cobertura

### Generar reporte HTML
```bash
uv run pytest --cov=src --cov-report=html
# Abrir htmlcov/index.html en el navegador
```

### Ver líneas no cubiertas
```bash
uv run pytest --cov=src --cov-report=term-missing
```

### Excluir archivos de cobertura
En `pyproject.toml`:
```toml
[tool.coverage.run]
omit = [
    "tests/*",
    "**/__init__.py",
    "**/migrations/*"
]
```

## Requerimientos Cubiertos por Tests

Ver [verificacion_cobertura_tdd.md](verificacion_cobertura_tdd.md) para la matriz completa de requerimientos vs tests.

Resumen:
- ✅ 100% de funcionalidades de Taiga API cubiertas (170/170)
- ✅ 100% de requerimientos funcionales cubiertos
- ✅ 100% de requerimientos no funcionales cubiertos
- ✅ 585+ tests totales
- ✅ Todos los tests en ROJO (esperando implementación)

## Troubleshooting

### Tests no se ejecutan
```bash
# Verificar que pytest está instalado
uv pip list | grep pytest

# Reinstalar dependencias
uv sync
```

### ImportError en tests
- Los tests están en ROJO porque los módulos no existen aún
- Esto es normal en TDD
- El Experto DDD implementará los módulos

### Tests lentos
```bash
# Identificar tests lentos
uv run pytest --durations=10

# Marcar tests lentos
@pytest.mark.slow
def test_operacion_lenta():
    pass

# Excluir tests lentos
uv run pytest -m "not slow"
```

---

**Fecha de creación**: 2025-12-01
**Versión**: 1.0
**Estado**: Tests en ROJO - Listos para implementación
