# Análisis TDD del Caso de Negocio - Herramientas MCP para Épicas en Taiga

## Resumen Ejecutivo

Este documento presenta el análisis exhaustivo y minucioso del caso de negocio para implementar las herramientas MCP de gestión de épicas en Taiga. Se han identificado **26 requerimientos funcionales** y **10 requerimientos no funcionales**, todos los cuales requieren cobertura completa de tests siguiendo metodología TDD.

## 1. Requerimientos Funcionales Identificados

### 1.1 Gestión Básica de Épicas (RF-001 a RF-007)

#### RF-001: Listar Épicas
- **Descripción**: Obtener lista de épicas con filtros opcionales
- **Endpoint**: `GET /api/v1/epics`
- **Criterios de aceptación**:
  - Listar todas las épicas sin filtros
  - Filtrar por project, assigned_to, status, tags
  - Manejo de errores 401, 403
- **Tests necesarios**:
  - `test_list_epics_without_filters`
  - `test_list_epics_with_project_filter`
  - `test_list_epics_with_multiple_filters`
  - `test_list_epics_unauthorized`
  - `test_list_epics_forbidden`

#### RF-002: Crear Épica
- **Descripción**: Crear nueva épica en proyecto
- **Endpoint**: `POST /api/v1/epics`
- **Criterios de aceptación**:
  - Crear con campos obligatorios (project, subject)
  - Crear con campos opcionales (description, color, tags, etc.)
  - Validar proyecto existe
  - Errores de validación y permisos
- **Tests necesarios**:
  - `test_create_epic_minimal`
  - `test_create_epic_full_data`
  - `test_create_epic_invalid_project`
  - `test_create_epic_invalid_color`
  - `test_create_epic_without_permission`

#### RF-003: Obtener Épica por ID
- **Descripción**: Obtener detalles de épica específica
- **Endpoint**: `GET /api/v1/epics/{epicId}`
- **Criterios de aceptación**:
  - Retornar épica existente
  - Error 404 si no existe
  - Error 403 sin permisos
- **Tests necesarios**:
  - `test_get_epic_by_id_success`
  - `test_get_epic_by_id_not_found`
  - `test_get_epic_by_id_forbidden`

#### RF-004: Obtener Épica por Referencia
- **Descripción**: Obtener épica por ref y project
- **Endpoint**: `GET /api/v1/epics/by_ref`
- **Criterios de aceptación**:
  - Retornar épica correcta por ref
  - Error 404 si no existe
- **Tests necesarios**:
  - `test_get_epic_by_ref_success`
  - `test_get_epic_by_ref_not_found`
  - `test_get_epic_by_ref_invalid_project`

#### RF-005: Actualizar Épica (Completo)
- **Descripción**: Actualización PUT completa
- **Endpoint**: `PUT /api/v1/epics/{epicId}`
- **Criterios de aceptación**:
  - Actualizar todos los campos
  - Validar version (control concurrencia)
  - Error 409 si version no coincide
- **Tests necesarios**:
  - `test_update_epic_put_success`
  - `test_update_epic_put_version_conflict`
  - `test_update_epic_put_validation_error`

#### RF-006: Actualizar Épica (Parcial)
- **Descripción**: Actualización PATCH parcial
- **Endpoint**: `PATCH /api/v1/epics/{epicId}`
- **Criterios de aceptación**:
  - Actualizar solo campos proporcionados
  - Mantener valores previos no especificados
  - Validar version
- **Tests necesarios**:
  - `test_update_epic_patch_single_field`
  - `test_update_epic_patch_multiple_fields`
  - `test_update_epic_patch_version_conflict`

#### RF-007: Eliminar Épica
- **Descripción**: Eliminar épica existente
- **Endpoint**: `DELETE /api/v1/epics/{epicId}`
- **Criterios de aceptación**:
  - Eliminar si existe
  - 404 si no existe
  - 403 sin permisos
  - NO eliminar user stories relacionadas
- **Tests necesarios**:
  - `test_delete_epic_success`
  - `test_delete_epic_not_found`
  - `test_delete_epic_forbidden`
  - `test_delete_epic_preserves_userstories`

### 1.2 Operaciones Masivas (RF-008, RF-014)

#### RF-008: Crear Múltiples Épicas (Bulk)
- **Descripción**: Crear varias épicas en un request
- **Endpoint**: `POST /api/v1/epics/bulk_create`
- **Criterios de aceptación**:
  - Crear todas las épicas
  - Transacción atómica (todo o nada)
  - Errores de validación específicos
- **Tests necesarios**:
  - `test_bulk_create_epics_success`
  - `test_bulk_create_epics_partial_failure`
  - `test_bulk_create_epics_rollback_on_error`

#### RF-014: Relacionar Múltiples User Stories (Bulk)
- **Descripción**: Relacionar múltiples US con épica
- **Endpoint**: `POST /api/v1/epics/{epicId}/related_userstories/bulk_create`
- **Criterios de aceptación**:
  - Crear todas las relaciones
  - Validar todas existen y mismo proyecto
  - Evitar duplicados
  - Transacción atómica
- **Tests necesarios**:
  - `test_bulk_relate_userstories_success`
  - `test_bulk_relate_userstories_duplicates`
  - `test_bulk_relate_userstories_different_projects`

### 1.3 Gestión de Relaciones Epic-UserStory (RF-009 a RF-013)

#### RF-009: Listar User Stories Relacionadas
- **Descripción**: Obtener US de una épica
- **Endpoint**: `GET /api/v1/epics/{epicId}/related_userstories`
- **Criterios de aceptación**:
  - Devolver todas las US relacionadas
  - Respetar orden
  - Lista vacía si no hay relaciones
- **Tests necesarios**:
  - `test_list_related_userstories_with_data`
  - `test_list_related_userstories_empty`
  - `test_list_related_userstories_ordered`

#### RF-010: Relacionar User Story con Épica
- **Descripción**: Crear relación epic-US
- **Endpoint**: `POST /api/v1/epics/{epicId}/related_userstories`
- **Criterios de aceptación**:
  - Crear relación
  - Validar mismo proyecto
  - Evitar duplicados
- **Tests necesarios**:
  - `test_relate_userstory_success`
  - `test_relate_userstory_duplicate`
  - `test_relate_userstory_different_project`

#### RF-011: Obtener Relación Epic-UserStory
- **Descripción**: Obtener información de relación
- **Endpoint**: `GET /api/v1/epics/{epicId}/related_userstories/{usId}`
- **Criterios de aceptación**:
  - Devolver relación si existe
  - 404 si no existe
- **Tests necesarios**:
  - `test_get_related_userstory_success`
  - `test_get_related_userstory_not_found`

#### RF-012: Actualizar Relación Epic-UserStory
- **Descripción**: Actualizar relación (orden)
- **Endpoint**: `PATCH /api/v1/epics/{epicId}/related_userstories/{usId}`
- **Criterios de aceptación**:
  - Actualizar campo order
  - Validar relación existe
- **Tests necesarios**:
  - `test_update_related_userstory_order`
  - `test_update_related_userstory_not_found`

#### RF-013: Eliminar Relación Epic-UserStory
- **Descripción**: Desvincular US de épica
- **Endpoint**: `DELETE /api/v1/epics/{epicId}/related_userstories/{usId}`
- **Criterios de aceptación**:
  - Eliminar relación sin afectar entidades
  - 404 si no existe
- **Tests necesarios**:
  - `test_delete_related_userstory_success`
  - `test_delete_related_userstory_not_found`
  - `test_delete_related_preserves_entities`

### 1.4 Filtros y Metadatos (RF-015)

#### RF-015: Obtener Filtros Disponibles
- **Descripción**: Datos para filtrar épicas
- **Endpoint**: `GET /api/v1/epics/filters_data`
- **Criterios de aceptación**:
  - Devolver statuses disponibles
  - Devolver usuarios asignables
  - Devolver tags usados
- **Tests necesarios**:
  - `test_get_filters_data_complete`
  - `test_get_filters_data_empty_project`

### 1.5 Sistema de Votación (RF-016 a RF-018)

#### RF-016: Votar Épica (Upvote)
- **Descripción**: Dar voto positivo
- **Endpoint**: `POST /api/v1/epics/{epicId}/upvote`
- **Criterios de aceptación**:
  - Agregar voto del usuario
  - Evitar duplicados
  - Incrementar contador
- **Tests necesarios**:
  - `test_upvote_epic_success`
  - `test_upvote_epic_duplicate`
  - `test_upvote_epic_counter_increment`

#### RF-017: Quitar Voto (Downvote)
- **Descripción**: Quitar voto
- **Endpoint**: `POST /api/v1/epics/{epicId}/downvote`
- **Criterios de aceptación**:
  - Quitar voto del usuario
  - Error si no había votado
  - Decrementar contador
- **Tests necesarios**:
  - `test_downvote_epic_success`
  - `test_downvote_epic_not_voted`
  - `test_downvote_epic_counter_decrement`

#### RF-018: Obtener Votantes
- **Descripción**: Listar votantes
- **Endpoint**: `GET /api/v1/epics/{epicId}/voters`
- **Criterios de aceptación**:
  - Lista completa de votantes
  - Información básica de usuarios
  - Lista vacía si no hay votos
- **Tests necesarios**:
  - `test_get_voters_with_data`
  - `test_get_voters_empty`

### 1.6 Sistema de Observadores (RF-019 a RF-021)

#### RF-019: Observar Épica (Watch)
- **Descripción**: Agregar como observador
- **Endpoint**: `POST /api/v1/epics/{epicId}/watch`
- **Criterios de aceptación**:
  - Agregar a watchers
  - Evitar duplicados
  - Usuario recibe notificaciones
- **Tests necesarios**:
  - `test_watch_epic_success`
  - `test_watch_epic_duplicate`

#### RF-020: Dejar de Observar (Unwatch)
- **Descripción**: Quitar de observadores
- **Endpoint**: `POST /api/v1/epics/{epicId}/unwatch`
- **Criterios de aceptación**:
  - Quitar de watchers
  - Error si no observaba
- **Tests necesarios**:
  - `test_unwatch_epic_success`
  - `test_unwatch_epic_not_watching`

#### RF-021: Obtener Observadores
- **Descripción**: Listar observadores
- **Endpoint**: `GET /api/v1/epics/{epicId}/watchers`
- **Criterios de aceptación**:
  - Lista completa de watchers
  - Información básica usuarios
- **Tests necesarios**:
  - `test_get_watchers_with_data`
  - `test_get_watchers_empty`

### 1.7 Gestión de Adjuntos (RF-022 a RF-026)

#### RF-022: Listar Adjuntos
- **Descripción**: Obtener adjuntos de épica
- **Endpoint**: `GET /api/v1/epics/attachments`
- **Criterios de aceptación**:
  - Filtrar por epic_id o project
  - Incluir metadata completa
- **Tests necesarios**:
  - `test_list_attachments_by_epic`
  - `test_list_attachments_by_project`
  - `test_list_attachments_empty`

#### RF-023: Crear Adjunto
- **Descripción**: Subir archivo
- **Endpoint**: `POST /api/v1/epics/attachments`
- **Criterios de aceptación**:
  - Subir archivo (multipart)
  - Validar tamaño y tipo
  - Generar URL
- **Tests necesarios**:
  - `test_create_attachment_success`
  - `test_create_attachment_size_exceeded`
  - `test_create_attachment_invalid_type`

#### RF-024: Obtener Adjunto
- **Descripción**: Obtener información adjunto
- **Endpoint**: `GET /api/v1/epics/attachments/{id}`
- **Criterios de aceptación**:
  - Información completa
  - 404 si no existe
- **Tests necesarios**:
  - `test_get_attachment_success`
  - `test_get_attachment_not_found`

#### RF-025: Actualizar Adjunto
- **Descripción**: Actualizar metadata
- **Endpoint**: `PATCH /api/v1/epics/attachments/{id}`
- **Criterios de aceptación**:
  - Actualizar descripción/deprecado
  - No cambiar archivo
- **Tests necesarios**:
  - `test_update_attachment_metadata`
  - `test_update_attachment_forbidden`

#### RF-026: Eliminar Adjunto
- **Descripción**: Eliminar archivo
- **Endpoint**: `DELETE /api/v1/epics/attachments/{id}`
- **Criterios de aceptación**:
  - Eliminar archivo y registro
  - 404 si no existe
- **Tests necesarios**:
  - `test_delete_attachment_success`
  - `test_delete_attachment_not_found`

## 2. Requerimientos No Funcionales Identificados

### RNF-001: Arquitectura DDD
- **Criterio**: Separación clara de capas Domain/Application/Infrastructure
- **Tests necesarios**:
  - Tests unitarios para entidades Epic, RelatedUserStory, Attachment
  - Tests de repositorios (interfaces)
  - Tests de casos de uso
  - Tests de implementaciones de infraestructura

### RNF-002: Consistencia con Patrón Existente
- **Criterio**: Seguir patrones de herramientas existentes
- **Tests necesarios**:
  - Verificar estructura de herramientas MCP
  - Verificar manejo de errores consistente
  - Verificar documentación

### RNF-003: Gestión de Errores
- **Criterio**: Manejo robusto de todos los tipos de error
- **Tests necesarios**:
  - Test error 400 (validación)
  - Test error 401 (autenticación)
  - Test error 403 (permisos)
  - Test error 404 (no encontrado)
  - Test error 409 (conflicto de versión)
  - Test error 500 (servidor)
  - Test timeouts y errores de red

### RNF-004: Validación de Datos
- **Criterio**: Validación exhaustiva de inputs
- **Tests necesarios**:
  - Test validación de tipos
  - Test validación de formatos (color hex, fechas)
  - Test validación de rangos
  - Test validación de relaciones

### RNF-005: Testabilidad
- **Criterio**: Cobertura >= 80%
- **Tests necesarios**:
  - Tests unitarios completos
  - Tests de integración completos
  - Tests funcionales end-to-end
  - Mocks para API externa

### RNF-006: Documentación de Código
- **Criterio**: Código autodocumentado
- **Tests necesarios**:
  - Verificar docstrings
  - Verificar type hints
  - Verificar ejemplos en herramientas

### RNF-007: Performance
- **Criterio**: Operaciones eficientes
- **Tests necesarios**:
  - Test operaciones bulk son atómicas
  - Test timeouts configurados
  - Test sin llamadas redundantes

### RNF-008: Compatibilidad MCP
- **Criterio**: Compatible con estándar MCP
- **Tests necesarios**:
  - Test decoradores @server.call_tool
  - Test schemas Pydantic
  - Test formato de salida

### RNF-009: Seguridad
- **Criterio**: Manejo seguro de credenciales
- **Tests necesarios**:
  - Test tokens no en logs
  - Test validación permisos
  - Test headers autenticación

### RNF-010: Mantenibilidad
- **Criterio**: Código mantenible y extensible
- **Tests necesarios**:
  - Test principio SRP
  - Test no duplicación
  - Test modularidad

## 3. Matriz de Trazabilidad

| Requerimiento | Tests Unitarios | Tests Integración | Tests Funcionales | Cobertura |
|--------------|-----------------|-------------------|-------------------|-----------|
| RF-001: Listar Épicas | test_epic_entity_creation | test_list_epics_use_case | test_list_epics_tool | ✅ |
| RF-002: Crear Épica | test_epic_validation | test_create_epic_use_case | test_create_epic_tool | ✅ |
| RF-003: Obtener por ID | test_epic_id_property | test_get_epic_use_case | test_get_epic_tool | ✅ |
| RF-004: Obtener por Ref | test_epic_ref_property | test_get_by_ref_use_case | test_get_epic_by_ref_tool | ✅ |
| RF-005: Actualizar PUT | test_epic_update_version | test_update_epic_put_use_case | test_update_epic_put_tool | ✅ |
| RF-006: Actualizar PATCH | test_epic_partial_update | test_update_epic_patch_use_case | test_update_epic_patch_tool | ✅ |
| RF-007: Eliminar | test_epic_deletion | test_delete_epic_use_case | test_delete_epic_tool | ✅ |
| RF-008: Bulk Create | test_epic_bulk_validation | test_bulk_create_use_case | test_bulk_create_tool | ✅ |
| RF-009: Listar Relaciones | test_related_userstory_entity | test_list_relations_use_case | test_list_relations_tool | ✅ |
| RF-010: Crear Relación | test_relation_validation | test_create_relation_use_case | test_create_relation_tool | ✅ |
| RF-011: Obtener Relación | test_relation_id | test_get_relation_use_case | test_get_relation_tool | ✅ |
| RF-012: Actualizar Relación | test_relation_order | test_update_relation_use_case | test_update_relation_tool | ✅ |
| RF-013: Eliminar Relación | test_relation_deletion | test_delete_relation_use_case | test_delete_relation_tool | ✅ |
| RF-014: Bulk Relate | test_bulk_relations | test_bulk_relate_use_case | test_bulk_relate_tool | ✅ |
| RF-015: Filtros | test_filters_entity | test_get_filters_use_case | test_get_filters_tool | ✅ |
| RF-016: Upvote | test_epic_voters | test_upvote_use_case | test_upvote_tool | ✅ |
| RF-017: Downvote | test_epic_remove_voter | test_downvote_use_case | test_downvote_tool | ✅ |
| RF-018: Listar Votantes | test_epic_voters_list | test_get_voters_use_case | test_get_voters_tool | ✅ |
| RF-019: Watch | test_epic_watchers | test_watch_use_case | test_watch_tool | ✅ |
| RF-020: Unwatch | test_epic_remove_watcher | test_unwatch_use_case | test_unwatch_tool | ✅ |
| RF-021: Listar Watchers | test_epic_watchers_list | test_get_watchers_use_case | test_get_watchers_tool | ✅ |
| RF-022: Listar Adjuntos | test_attachment_entity | test_list_attachments_use_case | test_list_attachments_tool | ✅ |
| RF-023: Crear Adjunto | test_attachment_validation | test_create_attachment_use_case | test_create_attachment_tool | ✅ |
| RF-024: Obtener Adjunto | test_attachment_id | test_get_attachment_use_case | test_get_attachment_tool | ✅ |
| RF-025: Actualizar Adjunto | test_attachment_metadata | test_update_attachment_use_case | test_update_attachment_tool | ✅ |
| RF-026: Eliminar Adjunto | test_attachment_deletion | test_delete_attachment_use_case | test_delete_attachment_tool | ✅ |
| RNF-001: DDD | test_domain_isolation | test_use_cases_orchestration | - | ✅ |
| RNF-002: Consistencia | - | - | test_tool_patterns | ✅ |
| RNF-003: Errores | test_exceptions | test_error_handling | test_error_responses | ✅ |
| RNF-004: Validación | test_entity_validation | test_input_validation | test_tool_validation | ✅ |
| RNF-005: Testabilidad | Todos los tests | Todos los tests | Todos los tests | ✅ |
| RNF-006: Documentación | test_docstrings | - | test_tool_descriptions | ✅ |
| RNF-007: Performance | - | test_bulk_atomicity | test_timeout_handling | ✅ |
| RNF-008: MCP | - | - | test_mcp_compatibility | ✅ |
| RNF-009: Seguridad | test_no_token_exposure | test_permission_checks | test_auth_headers | ✅ |
| RNF-010: Mantenibilidad | test_single_responsibility | test_no_duplication | test_modularity | ✅ |

## 4. Convergencias y Dependencias Detectadas

### 4.1 Convergencia de Operaciones CRUD
Los requerimientos RF-001 a RF-007 siguen el patrón CRUD estándar que converge con las implementaciones existentes de UserStories, Issues y Tasks.

### 4.2 Convergencia de Relaciones
RF-009 a RF-014 convergen en el manejo de relaciones Many-to-Many entre épicas y user stories, similar a las relaciones existentes en el proyecto.

### 4.3 Convergencia de Features Sociales
RF-016 a RF-021 (votación y observadores) convergen con features similares en otras entidades del sistema.

### 4.4 Convergencia de Adjuntos
RF-022 a RF-026 convergen con el sistema de adjuntos existente, requiriendo manejo especial de multipart/form-data.

### 4.5 Dependencias Críticas

1. **Dependencia de Autenticación**: Todos los endpoints requieren auth_token
2. **Dependencia de Proyecto**: Las épicas dependen de la existencia del proyecto
3. **Dependencia de Versión**: RF-005 y RF-006 dependen del control de concurrencia
4. **Dependencia de Relaciones**: Las user stories relacionadas deben pertenecer al mismo proyecto
5. **Dependencia de Transacciones**: RF-008 y RF-014 requieren transacciones atómicas

## 5. Arquitectura de Tests

### 5.1 Estructura de Directorios

```
tests/
├── conftest.py                      # Fixtures globales
├── unit/                           # Tests unitarios
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── test_epic.py       # Tests entidad Epic
│   │   │   ├── test_related_userstory.py  # Tests RelatedUserStory
│   │   │   └── test_attachment.py # Tests Attachment
│   │   ├── value_objects/
│   │   │   ├── test_color.py      # Tests value object Color
│   │   │   └── test_epic_ref.py   # Tests value object EpicRef
│   │   └── repositories/
│   │       └── test_epic_repository_interface.py
│   └── application/
│       ├── use_cases/
│       │   ├── test_epic_use_cases.py
│       │   ├── test_related_userstory_use_cases.py
│       │   └── test_attachment_use_cases.py
│       └── validators/
│           └── test_epic_validators.py
├── integration/                    # Tests de integración
│   ├── test_epic_repository_impl.py
│   ├── test_epic_use_cases_integration.py
│   ├── test_related_userstory_integration.py
│   └── test_attachment_integration.py
├── functional/                     # Tests funcionales
│   ├── test_epic_tools.py        # Tests herramientas MCP
│   ├── test_epic_crud_flow.py    # Flujo completo CRUD
│   ├── test_epic_relations_flow.py # Flujo relaciones
│   └── test_epic_social_flow.py  # Flujo votación/observadores
└── fixtures/                      # Datos de prueba
    ├── epic_data.py              # Fixtures de épicas
    ├── userstory_data.py         # Fixtures de user stories
    └── api_responses.py          # Respuestas mockeadas de API
```

### 5.2 Estrategia de Testing

#### Tests Unitarios (Capa Domain)
- Validación de entidades y value objects
- Lógica de negocio pura sin dependencias
- Validaciones de formato y reglas de negocio
- Coverage objetivo: 100%

#### Tests de Integración (Capa Application)
- Casos de uso con mocks de repositorios
- Orquestación de operaciones
- Manejo de errores y excepciones
- Coverage objetivo: 90%

#### Tests Funcionales (Capa Infrastructure)
- Herramientas MCP completas
- Flujos end-to-end
- Integración con API mockeada
- Coverage objetivo: 85%

### 5.3 Fixtures y Helpers Necesarios

```python
# fixtures/epic_data.py
@pytest.fixture
def valid_epic_data():
    """Datos válidos para crear una épica."""
    return {
        "project": 309804,
        "subject": "Test Epic",
        "description": "Test Description",
        "color": "#A5694F",
        "tags": ["test", "tdd"]
    }

@pytest.fixture
def mock_epic_response():
    """Respuesta mockeada de la API."""
    return {
        "id": 456789,
        "ref": 5,
        "version": 1,
        "subject": "Test Epic",
        # ... más campos
    }

@pytest.fixture
def mock_taiga_client(mocker):
    """Cliente Taiga mockeado."""
    return mocker.MagicMock(spec=TaigaAPIClient)
```

## 6. Librerías a Investigar con context7

Antes de implementar los tests, se deben investigar las siguientes librerías:

### 6.1 Testing Framework
- **pytest**: Framework principal de testing
  - Fixtures y parametrización
  - Markers para categorizar tests
  - Plugins y extensiones

### 6.2 Coverage y Mocking
- **pytest-cov**: Medición de cobertura
- **pytest-mock**: Simplificación de mocks
- **responses**: Mocking de requests HTTP
- **pytest-httpx**: Mocking específico para httpx

### 6.3 Async Testing
- **pytest-asyncio**: Testing de código asíncrono
- **aioresponses**: Mocking de aiohttp

### 6.4 Validación y Serialización
- **pydantic**: Validación de modelos y schemas
- **marshmallow**: Serialización alternativa

### 6.5 Framework MCP
- **fastmcp**: Framework para Model Context Protocol
- **mcp**: Protocolo base

### 6.6 Cliente HTTP
- **httpx**: Cliente HTTP moderno
- **requests**: Cliente HTTP tradicional

## 7. Plan de Ejecución de Tests

### Fase 1: Setup y Configuración
1. Configurar pytest y plugins
2. Crear estructura de directorios
3. Configurar fixtures globales
4. Establecer configuración de cobertura

### Fase 2: Tests Unitarios (Domain)
1. Tests de entidades (Epic, RelatedUserStory, Attachment)
2. Tests de value objects (Color, EpicRef)
3. Tests de interfaces de repositorio
4. Tests de excepciones de dominio

### Fase 3: Tests de Integración (Application)
1. Tests de casos de uso de épicas
2. Tests de casos de uso de relaciones
3. Tests de casos de uso de adjuntos
4. Tests de validadores y orquestación

### Fase 4: Tests Funcionales (Infrastructure)
1. Tests de herramientas MCP individuales
2. Tests de flujos completos CRUD
3. Tests de flujos de relaciones
4. Tests de flujos sociales

### Fase 5: Verificación y Documentación
1. Ejecutar suite completa
2. Verificar cobertura >= 80%
3. Documentar resultados
4. Generar reporte de cobertura

## 8. Criterios de Aceptación Globales

Para considerar la implementación TDD completa:

1. ✅ Todos los tests están en ROJO (fallan porque no hay implementación)
2. ✅ 100% de requerimientos tienen al menos un test
3. ✅ Estructura de tests sigue arquitectura DDD
4. ✅ Fixtures y helpers reutilizables creados
5. ✅ Configuración de pytest y cobertura completa
6. ✅ Documentación de tests generada
7. ✅ Tests son independientes y reproducibles
8. ✅ Tests siguen patrón AAA (Arrange, Act, Assert)
9. ✅ Nombres de tests son descriptivos y claros
10. ✅ Mocks apropiados para dependencias externas

## 9. Riesgos y Mitigaciones

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|--------------|------------|
| Cambios en API de Taiga | Alto | Baja | Mocks completos, tests de contrato |
| Complejidad de relaciones | Medio | Media | Tests exhaustivos de casos edge |
| Performance en bulk operations | Medio | Media | Tests de carga, timeouts apropiados |
| Concurrencia de versiones | Alto | Media | Tests específicos de conflictos |
| Manejo de archivos grandes | Medio | Baja | Tests con límites, validación de tamaño |

## 10. Conclusión

Este análisis exhaustivo ha identificado:
- **26 requerimientos funcionales** que requieren **78+ tests funcionales**
- **10 requerimientos no funcionales** que requieren **30+ tests de calidad**
- **Total estimado**: 200+ tests entre unitarios, integración y funcionales

La implementación seguirá estrictamente TDD, con todos los tests en ROJO antes de cualquier implementación, garantizando así que el comportamiento esperado está completamente especificado antes del desarrollo.
