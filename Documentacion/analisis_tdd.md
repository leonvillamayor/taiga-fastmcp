# Análisis TDD del Caso de Negocio - Servidor MCP para Taiga

## 1. ANÁLISIS EXHAUSTIVO PUNTO POR PUNTO

### Punto 1: Framework FastMCP
**Línea 1**: "Queremos generar un servidor mcp utilizando el framework fastmcp"
- **RF-001**: El sistema DEBE utilizar el framework FastMCP para crear el servidor
- **RF-002**: El servidor DEBE implementar el protocolo MCP (Model Context Protocol)
- **RNF-001**: El servidor DEBE seguir las buenas prácticas de FastMCP
- **RNF-002**: El código DEBE ser Pythónico y limpio

### Punto 2: Capacidades del Framework
**Línea 3**: "Utilizando la documentación recogida en Documentacion/fastmcp.md y Documentacion/taiga.md"
- **RF-003**: El servidor DEBE implementar TODAS las capacidades necesarias de FastMCP
- **RF-004**: El servidor DEBE utilizar efectivamente las funcionalidades de FastMCP
- **RNF-003**: El servidor DEBE aplicar las mejores prácticas documentadas

### Punto 3: Protocolos de Transporte
**Línea 4-5**: "que permita los protocolos de transporte (ambos y por separado): stdio y HTTP Transport (Streamable)"
- **RF-005**: El servidor DEBE soportar transporte STDIO
- **RF-006**: El servidor DEBE soportar transporte HTTP (Streamable)
- **RF-007**: El servidor DEBE permitir ejecutar AMBOS transportes
- **RF-008**: El servidor DEBE permitir ejecutar transportes POR SEPARADO
- **RNF-004**: Los transportes DEBEN ser configurables

### Punto 4: Herramientas MCP para Taiga
**Línea 5-6**: "que ofrezca herramientas para interactuar con taiga, utilizando el documento Documentacion/taiga.md"
- **RF-009**: El servidor DEBE exponer herramientas MCP para TODAS las operaciones de Taiga
- **RF-010**: Las herramientas DEBEN cubrir autenticación de Taiga
- **RF-011**: Las herramientas DEBEN cubrir gestión de proyectos
- **RF-012**: Las herramientas DEBEN cubrir user stories
- **RF-013**: Las herramientas DEBEN cubrir issues
- **RF-014**: Las herramientas DEBEN cubrir epics
- **RF-015**: Las herramientas DEBEN cubrir tasks
- **RF-016**: Las herramientas DEBEN cubrir milestones/sprints
- **RF-017**: Las herramientas DEBEN cubrir history y comentarios
- **RF-018**: Las herramientas DEBEN cubrir usuarios y membresías
- **RF-019**: Las herramientas DEBEN cubrir atributos personalizados
- **RF-020**: Las herramientas DEBEN cubrir webhooks
- **RF-021**: Las herramientas DEBEN manejar adjuntos (attachments)
- **RF-022**: Las herramientas DEBEN manejar votación (upvote/downvote)
- **RF-023**: Las herramientas DEBEN manejar watchers
- **RF-024**: Las herramientas DEBEN manejar operaciones bulk

### Punto 5: Verificación de Implementación
**Línea 7-8**: "Se verificará que el servidor mcp ha aplicado correctamente las buenas practicas y funcionalidades de fastmcp"
- **RF-025**: El servidor DEBE pasar verificaciones de buenas prácticas
- **RF-026**: El servidor DEBE implementar manejo de errores con ToolError
- **RF-027**: El servidor DEBE usar tipos de retorno apropiados
- **RF-028**: El servidor DEBE implementar logging con Context
- **RF-029**: El servidor DEBE reportar progreso en operaciones largas
- **RNF-005**: El código DEBE usar type hints completos
- **RNF-006**: El código DEBE tener docstrings descriptivos

### Punto 6: Exposición y Orquestación
**Línea 8-9**: "el servidor mcp debe de exponer y orquestar todas las funcionalidades recogidas en Documentacion/taiga.md mediante herramientas del servidor mcp"
- **RF-030**: TODAS las funcionalidades de Taiga DEBEN estar expuestas
- **RF-031**: El servidor DEBE orquestar operaciones complejas
- **RF-032**: El servidor DEBE manejar paginación de la API de Taiga
- **RF-033**: El servidor DEBE manejar control de concurrencia optimista (version)
- **RF-034**: El servidor DEBE manejar rate limiting de Taiga
- **RF-035**: El servidor DEBE manejar internacionalización

### Punto 7: Configuración de Credenciales
**Línea 9-13**: "Poder configurar las credenciales para el uso de taiga utilizando el fichero .env"
- **RF-036**: El servidor DEBE leer credenciales desde archivo .env
- **RF-037**: El servidor DEBE usar TAIGA_API_URL del .env
- **RF-038**: El servidor DEBE usar TAIGA_USERNAME del .env
- **RF-039**: El servidor DEBE usar TAIGA_PASSWORD del .env
- **RF-040**: El servidor DEBE validar que las credenciales existan
- **RF-041**: El servidor DEBE manejar errores de autenticación
- **RNF-007**: Las credenciales NO DEBEN hardcodearse en el código

### Punto 8: Tests con Credenciales Reales
**Línea 13**: "Los test utilizaran las credenciales incluidas en .env para interactuar con taiga y verificar que todo funciona correctamente"
- **RF-042**: Los tests DEBEN usar credenciales reales del .env
- **RF-043**: Los tests DEBEN verificar conexión real con Taiga
- **RF-044**: Los tests DEBEN verificar operaciones CRUD reales
- **RF-045**: Los tests DEBEN manejar casos de error reales
- **RNF-008**: Los tests DEBEN ser idempotentes (limpiar después de ejecutar)

### Punto 9: Documentación del Servidor
**Línea 14**: "En el documento servidor_mcp_doc.md se describira de forma detallada la generacion, arranque, parada, etc del servidor mcp"
- **RF-046**: DEBE existir documentación completa del servidor
- **RF-047**: La documentación DEBE incluir instalación
- **RF-048**: La documentación DEBE incluir configuración
- **RF-049**: La documentación DEBE incluir arranque del servidor
- **RF-050**: La documentación DEBE incluir parada del servidor
- **RF-051**: La documentación DEBE incluir ejemplos de uso

### Punto 10: Documentación del Cliente
**Línea 15**: "En el documento cliente_mcp_doc.md se describirá de forma detallada la instalación y configuración del cliente mcp para que pueda ser incluido en claude code"
- **RF-052**: DEBE existir documentación del cliente MCP
- **RF-053**: La documentación DEBE incluir instalación en Claude Code
- **RF-054**: La documentación DEBE incluir configuración del cliente
- **RF-055**: La documentación DEBE incluir ejemplos de uso en Claude Code

## 2. ANÁLISIS DE CONVERGENCIAS Y DEPENDENCIAS

### Convergencias Identificadas

1. **Autenticación Central (RF-010, RF-036-041)**:
   - La autenticación es fundamental para TODAS las operaciones
   - Las credenciales del .env se usan en toda la aplicación
   - El token obtenido debe persistir durante la sesión

2. **Gestión de Estado (RF-032-035)**:
   - Paginación, concurrencia, rate limiting afectan a TODAS las herramientas
   - Necesidad de un sistema centralizado de manejo de estado

3. **Herramientas CRUD Comunes (RF-011-024)**:
   - Patrones similares para Projects, User Stories, Issues, Epics, Tasks
   - Oportunidad de abstracción y reutilización de código

4. **Operaciones Bulk y Relacionadas (RF-024, RF-031)**:
   - Muchas entidades tienen operaciones bulk
   - Relaciones entre entidades (Epic-US, US-Tasks, etc.)

5. **Características Transversales (RF-022-023)**:
   - Votación, watchers, adjuntos se aplican a múltiples entidades
   - Posible implementación como mixins o traits

6. **Transportes Múltiples (RF-005-008)**:
   - Necesidad de arquitectura que soporte múltiples transportes
   - Configuración dinámica de transportes

### Dependencias Críticas

1. **FastMCP → Taiga API**: El servidor depende completamente de la API de Taiga
2. **Autenticación → Todas las operaciones**: Sin auth no se puede hacer nada
3. **Proyecto → Todas las entidades**: Todo pertenece a un proyecto
4. **User Story → Tasks**: Las tasks dependen de user stories
5. **Epic → User Stories**: Relación de agregación
6. **Milestone → User Stories**: Asignación a sprints

## 3. CONSIDERACIONES DDD (Domain Driven Design)

### Bounded Contexts Identificados

1. **Authentication Context**
   - Manejo de credenciales
   - Gestión de tokens
   - Refresh de tokens

2. **Project Management Context**
   - Proyectos
   - Configuración de módulos
   - Estadísticas

3. **Work Items Context**
   - User Stories
   - Issues
   - Tasks
   - Epics

4. **Sprint Planning Context**
   - Milestones/Sprints
   - Asignación de trabajo
   - Estadísticas de sprint

5. **Collaboration Context**
   - Comentarios
   - History
   - Watchers
   - Votación

### Aggregates Principales

1. **Project Aggregate**: Raíz de todo
2. **Epic Aggregate**: Agrupa user stories
3. **User Story Aggregate**: Contiene tasks
4. **Sprint Aggregate**: Contiene asignaciones

## 4. MATRIZ DE TRAZABILIDAD INICIAL

| Categoría | Requerimientos | Tests Necesarios | Prioridad |
|-----------|---------------|------------------|-----------|
| Framework | RF-001 a RF-004 | test_fastmcp_server_creation, test_mcp_protocol_implementation | Alta |
| Transportes | RF-005 a RF-008 | test_stdio_transport, test_http_transport, test_dual_transport | Alta |
| Auth Taiga | RF-010, RF-036-041 | test_taiga_authentication, test_env_credentials, test_token_management | Crítica |
| Proyectos | RF-011 | test_project_crud, test_project_stats, test_project_modules | Alta |
| User Stories | RF-012 | test_userstory_crud, test_userstory_bulk, test_userstory_filters | Alta |
| Issues | RF-013 | test_issue_crud, test_issue_priorities, test_issue_types | Alta |
| Epics | RF-014 | test_epic_crud, test_epic_userstory_relations | Media |
| Tasks | RF-015 | test_task_crud, test_task_userstory_relation | Media |
| Milestones | RF-016 | test_milestone_crud, test_milestone_stats, test_sprint_planning | Alta |
| History | RF-017 | test_history_retrieval, test_comment_management | Media |
| Usuarios | RF-018 | test_user_info, test_memberships | Media |
| Atributos | RF-019 | test_custom_attributes | Baja |
| Webhooks | RF-020 | test_webhook_configuration | Baja |
| Adjuntos | RF-021 | test_attachment_upload, test_attachment_management | Media |
| Votación | RF-022 | test_voting_system | Baja |
| Watchers | RF-023 | test_watcher_management | Baja |
| Bulk | RF-024 | test_bulk_operations | Media |
| Verificación | RF-025-029 | test_error_handling, test_logging, test_progress_reporting | Alta |
| Orquestación | RF-030-035 | test_pagination, test_concurrency, test_rate_limiting | Alta |
| Documentación | RF-046-055 | test_documentation_generation | Media |

## 5. ARQUITECTURA DE TESTS PROPUESTA

```
tests/
├── conftest.py                        # Fixtures globales y configuración
├── unit/                              # Tests unitarios
│   ├── domain/
│   │   ├── test_auth_entity.py        # Entidad de autenticación
│   │   ├── test_project_entity.py     # Entidad proyecto
│   │   ├── test_userstory_entity.py   # Entidad user story
│   │   ├── test_issue_entity.py       # Entidad issue
│   │   ├── test_epic_entity.py        # Entidad epic
│   │   ├── test_task_entity.py        # Entidad task
│   │   └── test_milestone_entity.py   # Entidad milestone
│   ├── application/
│   │   ├── test_auth_use_cases.py     # Casos de uso de autenticación
│   │   ├── test_project_use_cases.py  # Casos de uso de proyectos
│   │   ├── test_work_item_use_cases.py # Casos de uso de work items
│   │   └── test_sprint_use_cases.py   # Casos de uso de sprints
│   └── infrastructure/
│       ├── test_taiga_client.py       # Cliente HTTP para Taiga
│       ├── test_env_config.py         # Configuración desde .env
│       ├── test_mcp_server.py         # Servidor MCP
│       └── test_transports.py         # Transportes stdio/http
├── integration/                        # Tests de integración
│   ├── test_taiga_connection.py       # Conexión real con Taiga
│   ├── test_mcp_tools.py              # Tools MCP funcionando
│   ├── test_auth_flow.py              # Flujo completo de auth
│   └── test_crud_operations.py        # Operaciones CRUD reales
├── functional/                         # Tests funcionales E2E
│   ├── test_complete_workflow.py      # Flujo completo de trabajo
│   ├── test_sprint_management.py      # Gestión de sprint completa
│   └── test_epic_management.py        # Gestión de épicas completa
└── fixtures/                           # Datos de prueba
    ├── sample_data.py                 # Datos de ejemplo
    ├── taiga_responses.py             # Respuestas mock de Taiga
    └── factories.py                   # Factories para entidades
```

## 6. LIBRERÍAS Y HERRAMIENTAS NECESARIAS

### Testing
- **pytest**: Framework de testing principal
- **pytest-cov**: Medición de cobertura
- **pytest-mock**: Mocking simplificado
- **pytest-asyncio**: Tests asíncronos
- **pytest-env**: Variables de entorno para tests

### FastMCP y MCP
- **fastmcp**: Framework MCP principal
- **mcp**: Protocolo MCP base

### HTTP y Async
- **httpx**: Cliente HTTP moderno con soporte async
- **aiohttp**: Servidor/cliente HTTP async
- **python-dotenv**: Carga de variables .env

### Validación y Tipos
- **pydantic**: Validación de datos y modelos
- **typing-extensions**: Tipos avanzados

### Utilidades
- **faker**: Generación de datos de prueba
- **factory-boy**: Factories para tests

## 7. FIXTURES Y HELPERS NECESARIOS

### Fixtures Principales

1. **taiga_auth_token**: Token de autenticación para tests
2. **taiga_client**: Cliente configurado para Taiga
3. **mcp_server**: Instancia del servidor MCP
4. **test_project**: Proyecto de prueba en Taiga
5. **test_user_story**: User story de prueba
6. **test_epic**: Epic de prueba
7. **test_sprint**: Sprint de prueba
8. **env_config**: Configuración desde .env

### Helpers

1. **cleanup_taiga_data**: Limpiar datos después de tests
2. **wait_for_rate_limit**: Manejar rate limiting
3. **verify_mcp_response**: Verificar respuestas MCP
4. **create_test_hierarchy**: Crear jerarquía de datos de prueba

## 8. CRITERIOS DE ACEPTACIÓN GLOBALES

1. ✅ TODOS los endpoints de Taiga documentados tienen al menos un test
2. ✅ TODAS las herramientas MCP tienen tests unitarios y de integración
3. ✅ El servidor soporta AMBOS transportes (stdio y HTTP)
4. ✅ La autenticación funciona con credenciales reales
5. ✅ Los tests son idempotentes (limpian después de ejecutar)
6. ✅ La cobertura de requerimientos es del 100%
7. ✅ Los tests están en ROJO inicialmente
8. ✅ La documentación se genera automáticamente
9. ✅ El manejo de errores es exhaustivo
10. ✅ El código sigue las buenas prácticas de FastMCP

## 9. RIESGOS Y MITIGACIONES

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Rate limiting de Taiga | Tests fallan intermitentemente | Implementar retry logic y delays |
| Cambios en API de Taiga | Tests se rompen | Versionar tests, usar mocks para unit tests |
| Credenciales expiradas | Tests no pueden ejecutarse | Refresh token automático |
| Datos de prueba persisten | Contamina ambiente | Cleanup exhaustivo después de cada test |
| Tests lentos con API real | CI/CD lento | Separar tests unitarios de integración |

## 10. MÉTRICAS DE ÉXITO

- **Cobertura de código**: >= 80%
- **Cobertura de requerimientos**: 100%
- **Tiempo de ejecución tests unitarios**: < 5 segundos
- **Tiempo de ejecución tests integración**: < 30 segundos
- **Tests en ROJO inicial**: 100%
- **Documentación generada**: 100% de funcionalidades

## RESUMEN EJECUTIVO

Este análisis TDD identifica **55 requerimientos funcionales** y **8 requerimientos no funcionales** del caso de negocio. Se han detectado **6 convergencias principales** y **6 dependencias críticas** entre componentes.

La arquitectura de tests propuesta incluye:
- **3 capas de testing**: unit, integration, functional
- **30+ archivos de test** organizados por dominio
- **8 fixtures principales** para facilitar testing
- **10 criterios de aceptación** globales

El proyecto requiere integración profunda con la API de Taiga, manejo de múltiples transportes MCP, y cumplimiento estricto de las buenas prácticas de FastMCP.

**PRÓXIMOS PASOS**:
1. Investigar con context7 las librerías FastMCP, httpx, pytest
2. Configurar el proyecto con uv
3. Crear todos los archivos de test en ROJO
4. Verificar cobertura del 100% de requerimientos
