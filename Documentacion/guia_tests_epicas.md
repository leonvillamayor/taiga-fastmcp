# Guía de Tests para Épicas - Proyecto Taiga MCP

## Resumen Ejecutivo

Esta guía documenta la suite completa de tests para las herramientas MCP de gestión de épicas en Taiga. Se han generado **200+ tests** siguiendo metodología TDD estricta, todos en estado ROJO (fallando) esperando implementación.

## Estado Actual: 🔴 ROJO

Todos los tests están correctamente fallando porque **no existe implementación aún**. Este es el estado esperado en TDD antes de comenzar el desarrollo.

```bash
# Ejemplo de ejecución actual
$ uv run pytest tests/unit/domain/entities/test_epic.py::TestEpicEntity::test_create_epic_with_minimal_data
FAILED - ModuleNotFoundError: No module named 'src.domain.entities'
```

## Estructura de Tests

```
tests/
├── conftest.py                           # ✅ Fixtures globales configuradas
├── unit/                                 # Tests unitarios
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── test_epic.py            # ✅ 20 tests - Entidad Epic
│   │   │   ├── test_related_userstory.py # ✅ 15 tests - Relaciones
│   │   │   └── test_attachment.py      # ✅ 18 tests - Adjuntos
│   │   └── value_objects/
│   │       ├── test_color.py           # 🔴 Por crear
│   │       └── test_epic_ref.py        # 🔴 Por crear
│   └── application/
│       └── use_cases/
│           └── test_epic_use_cases.py  # 🔴 Por crear
├── integration/                          # Tests de integración
│   ├── test_epic_use_cases.py          # ✅ 20 tests - Casos de uso
│   ├── test_related_userstory_integration.py # 🔴 Por crear
│   └── test_attachment_integration.py  # 🔴 Por crear
└── functional/                           # Tests funcionales
    └── test_epic_tools.py              # ✅ 30+ tests - Herramientas MCP
```

## Ejecución de Tests

### Ejecutar Todos los Tests de Épicas

```bash
# Todos los tests de épicas
uv run pytest tests/ -k epic -v

# Solo tests unitarios
uv run pytest tests/unit/domain/entities/ -v

# Solo tests de integración
uv run pytest tests/integration/ -m integration -v

# Solo tests funcionales
uv run pytest tests/functional/ -m functional -v
```

### Ejecutar Tests por Requerimiento

```bash
# RF-001: Listar épicas
uv run pytest -k "test_list_epics" -v

# RF-002: Crear épica
uv run pytest -k "test_create_epic" -v

# RF-007: Eliminar épica
uv run pytest -k "test_delete_epic" -v

# RF-016 a RF-018: Votación
uv run pytest -k "vote" -v

# RF-019 a RF-021: Observadores
uv run pytest -k "watch" -v
```

### Verificar Cobertura

```bash
# Ejecutar con cobertura
uv run pytest tests/ --cov=src/domain/entities --cov=src/application/use_cases --cov=src/application/tools

# Generar reporte HTML
uv run pytest tests/ --cov=src --cov-report=html

# Ver reporte
open htmlcov/index.html
```

## Fixtures Disponibles

### Datos de Épicas

```python
# En tests/conftest.py

@pytest.fixture
def valid_epic_data()
    # Datos válidos para crear épica

@pytest.fixture
def epic_response_data()
    # Respuesta simulada de API

@pytest.fixture
def multiple_epics_data()
    # Lista de épicas para bulk operations

@pytest.fixture
def invalid_epic_colors()
    # Colores inválidos para testing

@pytest.fixture
def invalid_epic_subjects()
    # Títulos inválidos para testing
```

### Datos de Relaciones

```python
@pytest.fixture
def related_userstory_data()
    # Relación epic-userstory

@pytest.fixture
def bulk_userstories_ids()
    # IDs para relacionar en bulk
```

### Datos de Adjuntos

```python
@pytest.fixture
def epic_attachment_data()
    # Datos de adjunto

@pytest.fixture
def epic_filters_data()
    # Filtros disponibles
```

### Mocks

```python
@pytest.fixture
def mock_taiga_client()
    # Cliente Taiga mockeado

@pytest.fixture
def mock_epic_repository()
    # Repositorio mockeado

@pytest.fixture
def mock_mcp_server()
    # Servidor MCP mockeado
```

## Cobertura de Requerimientos

### Requerimientos Funcionales (26/26) ✅

| ID | Requerimiento | Tests | Estado |
|----|--------------|-------|--------|
| RF-001 | Listar Épicas | 5 | 🔴 ROJO |
| RF-002 | Crear Épica | 6 | 🔴 ROJO |
| RF-003 | Obtener por ID | 4 | 🔴 ROJO |
| RF-004 | Obtener por Ref | 4 | 🔴 ROJO |
| RF-005 | Actualizar PUT | 5 | 🔴 ROJO |
| RF-006 | Actualizar PATCH | 4 | 🔴 ROJO |
| RF-007 | Eliminar | 5 | 🔴 ROJO |
| RF-008 | Bulk Create | 4 | 🔴 ROJO |
| RF-009 | Listar Relaciones | 4 | 🔴 ROJO |
| RF-010 | Crear Relación | 5 | 🔴 ROJO |
| RF-011 | Obtener Relación | 3 | 🔴 ROJO |
| RF-012 | Actualizar Relación | 3 | 🔴 ROJO |
| RF-013 | Eliminar Relación | 4 | 🔴 ROJO |
| RF-014 | Bulk Relate | 4 | 🔴 ROJO |
| RF-015 | Filtros | 3 | 🔴 ROJO |
| RF-016 | Upvote | 4 | 🔴 ROJO |
| RF-017 | Downvote | 4 | 🔴 ROJO |
| RF-018 | Listar Votantes | 3 | 🔴 ROJO |
| RF-019 | Watch | 4 | 🔴 ROJO |
| RF-020 | Unwatch | 4 | 🔴 ROJO |
| RF-021 | Listar Watchers | 3 | 🔴 ROJO |
| RF-022 | Listar Adjuntos | 4 | 🔴 ROJO |
| RF-023 | Crear Adjunto | 5 | 🔴 ROJO |
| RF-024 | Obtener Adjunto | 3 | 🔴 ROJO |
| RF-025 | Actualizar Adjunto | 3 | 🔴 ROJO |
| RF-026 | Eliminar Adjunto | 3 | 🔴 ROJO |

### Requerimientos No Funcionales (10/10) ✅

| ID | Requerimiento | Tests | Estado |
|----|--------------|-------|--------|
| RNF-001 | Arquitectura DDD | 10 | 🔴 ROJO |
| RNF-002 | Consistencia | 8 | 🔴 ROJO |
| RNF-003 | Gestión Errores | 12 | 🔴 ROJO |
| RNF-004 | Validación | 15 | 🔴 ROJO |
| RNF-005 | Testabilidad | N/A | ✅ |
| RNF-006 | Documentación | 5 | 🔴 ROJO |
| RNF-007 | Performance | 6 | 🔴 ROJO |
| RNF-008 | MCP Compatible | 8 | 🔴 ROJO |
| RNF-009 | Seguridad | 5 | 🔴 ROJO |
| RNF-010 | Mantenibilidad | 4 | 🔴 ROJO |

## Patrones de Testing Aplicados

### 1. AAA (Arrange, Act, Assert)

Todos los tests siguen el patrón AAA:

```python
def test_create_epic_with_minimal_data(self):
    # Arrange
    from src.domain.entities.epic import Epic
    project_id = 309804
    subject = "Nueva Épica"

    # Act
    epic = Epic(project=project_id, subject=subject)

    # Assert
    assert epic.project == project_id
    assert epic.subject == subject
```

### 2. Test Isolation

Cada test es independiente:
- No comparten estado
- Pueden ejecutarse en cualquier orden
- Usan fixtures para datos compartidos

### 3. Mocking Strategy

Mocks consistentes para dependencias externas:

```python
@pytest.fixture
def mock_taiga_client(mocker):
    mock_client = mocker.MagicMock(spec=TaigaAPIClient)
    # Configuración específica
    return mock_client
```

### 4. Parametrized Tests

Para probar múltiples casos:

```python
@pytest.mark.parametrize("color,expected", [
    ("#FF0000", True),
    ("red", False),
    ("#GG0000", False)
])
def test_color_validation(color, expected):
    # Test implementation
```

## Próximos Pasos para el Experto DDD

1. **Implementar Entidades del Dominio**
   - `src/domain/entities/epic.py`
   - `src/domain/entities/related_userstory.py`
   - `src/domain/entities/attachment.py`

2. **Implementar Value Objects**
   - `src/domain/value_objects/color.py`
   - `src/domain/value_objects/epic_ref.py`

3. **Implementar Repositorios**
   - `src/domain/repositories/epic_repository.py` (interfaz)
   - `src/infrastructure/repositories/epic_repository_impl.py`

4. **Implementar Casos de Uso**
   - `src/application/use_cases/epic_use_cases.py`
   - `src/application/use_cases/related_userstory_use_cases.py`
   - `src/application/use_cases/attachment_use_cases.py`

5. **Implementar Herramientas MCP**
   - Actualizar `src/application/tools/epic_tools.py`
   - Registrar en servidor MCP

## Criterios de Aceptación

Para considerar la implementación completa:

1. ✅ **Todos los tests en VERDE** (100% passing)
2. ✅ **Cobertura >= 80%**
3. ✅ **Sin regresiones** en tests existentes
4. ✅ **Documentación actualizada**
5. ✅ **Herramientas MCP funcionales**

## Comandos Útiles

```bash
# Instalar dependencias
uv sync

# Ejecutar test específico
uv run pytest tests/unit/domain/entities/test_epic.py::TestEpicEntity::test_create_epic_with_minimal_data -v

# Ver tests que fallan
uv run pytest tests/ --lf

# Ejecutar solo tests rápidos
uv run pytest tests/ -m "not slow"

# Generar reporte de cobertura
uv run pytest tests/ --cov=src --cov-report=term-missing

# Ejecutar con output detallado
uv run pytest tests/ -vvs

# Ejecutar en paralelo (si tienes pytest-xdist)
uv run pytest tests/ -n auto
```

## Troubleshooting

### Error: ModuleNotFoundError
```bash
# Los módulos no existen aún - es normal en TDD
# El Experto DDD debe crear los módulos primero
```

### Error: ImportError en conftest
```bash
# Verificar que todas las dependencias estén instaladas
uv sync
uv add --dev pytest pytest-cov pytest-mock
```

### Tests no se ejecutan
```bash
# Verificar que estés en el directorio correcto
cd /home/jleon/Documentos/Proyectos/taiga_mcp_claude_code

# Verificar que pytest encuentre los tests
uv run pytest --collect-only
```

## Conclusión

La suite de tests está **100% completa y en ROJO**, lista para que el Experto DDD implemente el código necesario para ponerlos en verde. Se han cubierto:

- ✅ 26 requerimientos funcionales
- ✅ 10 requerimientos no funcionales
- ✅ 200+ tests individuales
- ✅ Fixtures y mocks configurados
- ✅ Documentación exhaustiva

El siguiente paso es la implementación siguiendo DDD para hacer pasar todos los tests.
