# Parameter Naming Standardization - Tarea 2.4

## Objetivo

Estandarizar la nomenclatura de parámetros en todas las herramientas MCP del servidor Taiga, eliminando aliases y adoptando un estándar consistente de nomenclatura para IDs.

## Estándar Adoptado

### Regla Principal: Sufijo `_id` para Todos los IDs

**Antes (inconsistente):**
- `epic` (ID del epic)
- `project` (ID del proyecto)
- `milestone` (ID del milestone)
- `epic_id` (ID del epic en algunos métodos)
- `project_id` (ID del proyecto en algunos métodos)

**Después (consistente):**
- `epic_id` - Siempre con sufijo `_id`
- `project_id` - Siempre con sufijo `_id`
- `milestone_id` - Siempre con sufijo `_id`
- `user_story_id` - Siempre con sufijo `_id`
- `task_id` - Siempre con sufijo `_id`
- `issue_id` - Siempre con sufijo `_id`
- `wiki_id` - Siempre con sufijo `_id`
- `attachment_id` - Siempre con sufijo `_id`
- `membership_id` - Siempre con sufijo `_id`
- `webhook_id` - Siempre con sufijo `_id`

### Arquitectura de Dos Capas

El proyecto mantiene una arquitectura de dos capas para el manejo de parámetros:

#### Capa 1: API Pública MCP (Tools)
- **Ubicación**: `src/application/tools/*_tools.py`
- **Convención**: Todos los IDs usan sufijo `_id`
- **Ejemplo**: `@mcp.tool()` decorators exponen `epic_id`, `project_id`, etc.
- **Propósito**: Proporcionar una API consistente y predecible para los clientes MCP

#### Capa 2: Cliente Taiga API Interno
- **Ubicación**: `src/taiga_client.py`
- **Convención**: Usa nombres según la API de Taiga (sin sufijo `_id` en algunos casos)
- **Ejemplo**: Métodos internos pueden usar `project` o `epic` al llamar a la API de Taiga
- **Propósito**: Mantener compatibilidad con la API REST de Taiga

#### Traducción de Parámetros

Los métodos tool traducen entre ambas capas:

```python
@mcp.tool(name="taiga_get_epic_by_ref")
async def get_epic_by_ref(
    auth_token: str,
    project_id: int,  # <-- API pública MCP usa _id
    ref: int
) -> dict[str, Any]:
    # Internamente traduce a lo que espera la API de Taiga
    client = TaigaAPIClient()
    return await client.get_epic_by_ref(
        project=project_id,  # <-- API interna puede usar nombre corto
        ref=ref
    )
```

## Cambios Realizados

### 1. Epic Tools ([src/application/tools/epic_tools.py](../src/application/tools/epic_tools.py))

#### Métodos Actualizados

| Método Tool (MCP) | Parámetro Antes | Parámetro Después |
|-------------------|-----------------|-------------------|
| `taiga_list_epics` | `project` | `project_id` |
| `taiga_create_epic` | `project` | `project_id` |
| `taiga_get_epic` | `epic` | `epic_id` |
| `taiga_get_epic_by_ref` | `project`, `epic` | `project_id`, `ref` |
| `taiga_update_epic_full` | `epic` | `epic_id` |
| `taiga_update_epic_partial` | `epic` | `epic_id` |
| `taiga_delete_epic` | `epic` | `epic_id` |
| `taiga_list_epic_related_userstories` | `epic` | `epic_id` |
| `taiga_create_epic_related_userstory` | `epic`, `user_story` | `epic_id`, `user_story_id` |
| `taiga_bulk_create_epics` | `project` | `project_id` |
| `taiga_get_epic_filters` | `project` | `project_id` |
| `taiga_upvote_epic` | `epic` | `epic_id` |
| `taiga_downvote_epic` | `epic` | `epic_id` |
| `taiga_get_epic_voters` | `epic` | `epic_id` |
| `taiga_watch_epic` | `epic` | `epic_id` |
| `taiga_unwatch_epic` | `epic` | `epic_id` |
| `taiga_get_epic_watchers` | `epic` | `epic_id` |
| `taiga_list_epic_attachments` | `epic` | `epic_id` |
| `taiga_create_epic_attachment` | `epic` | `epic_id` |
| `taiga_get_epic_attachment` | `attachment` | `attachment_id` |
| `taiga_update_epic_attachment` | `attachment` | `attachment_id` |
| `taiga_delete_epic_attachment` | `attachment` | `attachment_id` |
| `taiga_get_epic_custom_attributes` | `project` | `project_id` |
| `taiga_create_epic_custom_attribute` | `project` | `project_id` |
| `taiga_get_epic_custom_attribute_values` | `epic` | `epic_id` |

### 2. Milestone Tools ([src/application/tools/milestone_tools.py](../src/application/tools/milestone_tools.py))

| Método Tool (MCP) | Parámetro Antes | Parámetro Después |
|-------------------|-----------------|-------------------|
| `taiga_list_milestones` | `project` | `project_id` |
| `taiga_create_milestone` | `project` | `project_id` |
| `taiga_get_milestone` | `milestone` | `milestone_id` |
| `taiga_update_milestone_full` | `milestone`, `project` | `milestone_id`, `project_id` |
| `taiga_update_milestone` | `milestone` | `milestone_id` |
| `taiga_delete_milestone` | `milestone` | `milestone_id` |
| `taiga_get_milestone_stats` | `milestone` | `milestone_id` |
| `taiga_watch_milestone` | `milestone` | `milestone_id` |
| `taiga_unwatch_milestone` | `milestone` | `milestone_id` |
| `taiga_get_milestone_watchers` | `milestone` | `milestone_id` |

### 3. Task Tools ([src/application/tools/task_tools.py](../src/application/tools/task_tools.py))

| Método Tool (MCP) | Parámetro Antes | Parámetro Después |
|-------------------|-----------------|-------------------|
| `taiga_list_tasks` | `project`, `milestone`, `user_story` | `project_id`, `milestone_id`, `user_story_id` |
| `taiga_create_task` | `project`, `milestone`, `user_story` | `project_id`, `milestone_id`, `user_story_id` |
| `taiga_get_task` | `task` | `task_id` |
| `taiga_get_task_by_ref` | `project` | `project_id` |
| `taiga_update_task_full` | `task`, `project`, `milestone`, `user_story` | `task_id`, `project_id`, `milestone_id`, `user_story_id` |
| `taiga_update_task` | `task`, `milestone`, `user_story` | `task_id`, `milestone_id`, `user_story_id` |
| `taiga_delete_task` | `task` | `task_id` |
| `taiga_bulk_create_tasks` | `project` | `project_id` |
| `taiga_get_task_filters` | `project` | `project_id` |
| Todos los métodos de attachments, voting, watching | Similar pattern | Similar pattern con `_id` |

### 4. Issue Tools ([src/application/tools/issue_tools.py](../src/application/tools/issue_tools.py))

| Método Tool (MCP) | Parámetro Antes | Parámetro Después |
|-------------------|-----------------|-------------------|
| `taiga_list_issues` | `project`, `milestone` | `project_id`, `milestone_id` |
| `taiga_create_issue` | `project`, `milestone` | `project_id`, `milestone_id` |
| `taiga_get_issue` | `issue` | `issue_id` |
| `taiga_get_issue_by_ref` | `project` | `project_id` |
| `taiga_update_issue` | `issue`, `milestone` | `issue_id`, `milestone_id` |
| `taiga_delete_issue` | `issue` | `issue_id` |
| `taiga_bulk_create_issues` | `project` | `project_id` |
| `taiga_get_issue_filters` | `project` | `project_id` |
| Todos los métodos de attachments, comments, attributes | Similar pattern | Similar pattern con `_id` |

### 5. User Story Tools ([src/application/tools/userstory_tools.py](../src/application/tools/userstory_tools.py))

| Método Tool (MCP) | Parámetro Antes | Parámetro Después |
|-------------------|-----------------|-------------------|
| `taiga_list_userstories` | `project`, `milestone` | `project_id`, `milestone_id` |
| `taiga_create_userstory` | `project`, `milestone` | `project_id`, `milestone_id` |
| `taiga_get_userstory` | `userstory`, `project` | `userstory_id`, `project_id` |
| `taiga_update_userstory` | `userstory`, `milestone` | `userstory_id`, `milestone_id` |
| `taiga_delete_userstory` | `userstory` | `userstory_id` |
| `taiga_bulk_create_userstories` | `project`, `milestone` | `project_id`, `milestone_id` |
| `taiga_move_to_milestone` | `userstory`, `milestone` | `userstory_id`, `milestone_id` |
| Todos los métodos adicionales | Similar pattern | Similar pattern con `_id` |

### 6. Project Tools ([src/application/tools/project_tools.py](../src/application/tools/project_tools.py))

| Método Tool (MCP) | Parámetro Antes | Parámetro Después |
|-------------------|-----------------|-------------------|
| `taiga_get_project` | `project` | `project_id` |
| `taiga_update_project` | `project` | `project_id` |
| `taiga_delete_project` | `project` | `project_id` |
| `taiga_get_project_stats` | `project` | `project_id` |
| `taiga_duplicate_project` | `project` | `project_id` |
| `taiga_like_project` | `project` | `project_id` |
| `taiga_unlike_project` | `project` | `project_id` |
| `taiga_watch_project` | `project` | `project_id` |
| `taiga_unwatch_project` | `project` | `project_id` |
| `taiga_get_project_modules` | `project` | `project_id` |
| `taiga_update_project_modules` | `project` | `project_id` |
| `taiga_get_project_issues_stats` | `project` | `project_id` |
| `taiga_get_project_tags` | `project` | `project_id` |
| `taiga_create_project_tag` | `project` | `project_id` |
| `taiga_edit_project_tag` | `project` | `project_id` |
| `taiga_delete_project_tag` | `project` | `project_id` |
| `taiga_mix_project_tags` | `project` | `project_id` |
| `taiga_export_project` | `project` | `project_id` |

### 7. Wiki Tools ([src/application/tools/wiki_tools.py](../src/application/tools/wiki_tools.py))

| Método Tool (MCP) | Parámetro Antes | Parámetro Después |
|-------------------|-----------------|-------------------|
| `taiga_list_wiki_pages` | `project` | `project_id` |
| `taiga_create_wiki_page` | `project` | `project_id` |
| `taiga_get_wiki_page` | `wiki` | `wiki_id` |
| `taiga_get_wiki_page_by_slug` | `project` | `project_id` |
| `taiga_update_wiki_page` | `wiki` | `wiki_id` |
| `taiga_delete_wiki_page` | `wiki` | `wiki_id` |
| `taiga_restore_wiki_page` | `wiki` | `wiki_id` |
| `taiga_list_wiki_attachments` | `project` | `project_id` |
| `taiga_watch_wiki_page` | `page` | `page_id` |
| `taiga_unwatch_wiki_page` | `page` | `page_id` |
| `taiga_create_wiki_link` | `project` | `project_id` |
| Métodos de attachments | Similar pattern | Similar pattern con `_id` |

### 8. Membership Tools ([src/application/tools/membership_tools.py](../src/application/tools/membership_tools.py))

| Método Tool (MCP) | Parámetro Antes | Parámetro Después |
|-------------------|-----------------|-------------------|
| `taiga_list_memberships` | `project` | `project_id` |
| `taiga_create_membership` | `project` | `project_id` |
| `taiga_get_membership` | `membership` | `membership_id` |
| `taiga_update_membership` | `membership` | `membership_id` |
| `taiga_delete_membership` | `membership` | `membership_id` |

### 9. Webhook Tools ([src/application/tools/webhook_tools.py](../src/application/tools/webhook_tools.py))

| Método Tool (MCP) | Parámetro Antes | Parámetro Después |
|-------------------|-----------------|-------------------|
| `taiga_list_webhooks` | `project` | `project_id` |
| `taiga_create_webhook` | `project` | `project_id` |
| `taiga_get_webhook` | `webhook` | `webhook_id` |
| `taiga_update_webhook` | `webhook` | `webhook_id` |
| `taiga_delete_webhook` | `webhook` | `webhook_id` |
| `taiga_test_webhook` | `webhook` | `webhook_id` |

## Actualización de Tests

Todos los tests fueron actualizados para usar la nueva nomenclatura:

### Tests Unitarios
- **Ubicación**: [tests/unit/tools/](../tests/unit/tools/)
- **Cambios**: Todos los mocks y llamadas usan parámetros con sufijo `_id`

### Tests de Integración
- **Ubicación**: [tests/integration/](../tests/integration/)
- **Cambios**: Todas las llamadas reales a herramientas usan parámetros con sufijo `_id`

### Tests Funcionales
- **Ubicación**: [tests/functional/](../tests/functional/)
- **Cambios**: Tests de métodos internos ajustados según expectativas de cada capa

## Guía de Migración para Usuarios

### Para Clientes MCP

Si tu código llamaba a las herramientas MCP, debes actualizar los nombres de parámetros:

**Antes:**
```python
# Llamada antigua (NO funciona más)
result = await taiga_get_epic(
    auth_token="Bearer xxx",
    epic=123456
)

result = await taiga_list_epics(
    auth_token="Bearer xxx",
    project=309804
)
```

**Después:**
```python
# Llamada nueva (estándar actual)
result = await taiga_get_epic(
    auth_token="Bearer xxx",
    epic_id=123456  # <-- Ahora con _id
)

result = await taiga_list_epics(
    auth_token="Bearer xxx",
    project_id=309804  # <-- Ahora con _id
)
```

### Tabla de Conversión Rápida

| Parámetro Antiguo | Parámetro Nuevo |
|-------------------|-----------------|
| `epic=X` | `epic_id=X` |
| `project=X` | `project_id=X` |
| `milestone=X` | `milestone_id=X` |
| `task=X` | `task_id=X` |
| `issue=X` | `issue_id=X` |
| `userstory=X` | `userstory_id=X` |
| `user_story=X` | `user_story_id=X` |
| `wiki=X` | `wiki_id=X` |
| `page=X` | `page_id=X` |
| `attachment=X` | `attachment_id=X` |
| `membership=X` | `membership_id=X` |
| `webhook=X` | `webhook_id=X` |

### Compatibilidad

**IMPORTANTE**: Esta es una **breaking change**. Los clientes que usen nombres antiguos recibirán errores de tipo:

```
TypeError: taiga_get_epic() got an unexpected keyword argument 'epic'
```

**Solución**: Actualizar todos los nombres de parámetros según la tabla de conversión.

## Verificación de Calidad

Tras completar los cambios, se ejecutaron las siguientes verificaciones:

### Tests
```bash
uv run pytest tests/ -v
# Resultado: 1313 tests passed ✅
```

### Type Checking (mypy)
```bash
uv run mypy src/
# Resultado: Success: no issues found in 68 source files ✅
```

### Linting (ruff)
```bash
uv run ruff check src/ tests/
# Resultado: All checks passed! ✅
```

### Formateo (black)
```bash
uv run black src/ tests/ --line-length 100
# Resultado: 16 files reformatted ✅
```

### Imports (isort)
```bash
uv run isort src/ tests/ --profile black
# Resultado: Multiple files fixed ✅
```

## Beneficios de la Estandarización

### 1. Consistencia
- **Antes**: Los usuarios debían recordar qué métodos usaban `epic` vs `epic_id`
- **Después**: Todos los IDs siempre usan el sufijo `_id`

### 2. Predictibilidad
- La API es más intuitiva
- Menos errores de programación
- Mejor experiencia de desarrollo

### 3. Mantenibilidad
- Código más limpio y uniforme
- Más fácil de entender para nuevos desarrolladores
- Menos confusión al leer el código

### 4. Type Safety
- Los IDEs pueden proporcionar mejor autocompletado
- mypy puede detectar errores más fácilmente
- Menos bugs en producción

## Archivos Modificados

### Archivos de Código Fuente (src/)
- [src/application/tools/epic_tools.py](../src/application/tools/epic_tools.py)
- [src/application/tools/milestone_tools.py](../src/application/tools/milestone_tools.py)
- [src/application/tools/task_tools.py](../src/application/tools/task_tools.py)
- [src/application/tools/issue_tools.py](../src/application/tools/issue_tools.py)
- [src/application/tools/userstory_tools.py](../src/application/tools/userstory_tools.py)
- [src/application/tools/project_tools.py](../src/application/tools/project_tools.py)
- [src/application/tools/wiki_tools.py](../src/application/tools/wiki_tools.py)
- [src/application/tools/membership_tools.py](../src/application/tools/membership_tools.py)
- [src/application/tools/webhook_tools.py](../src/application/tools/webhook_tools.py)

### Archivos de Tests (tests/)
- [tests/unit/tools/test_epic_tools.py](../tests/unit/tools/test_epic_tools.py)
- [tests/unit/tools/test_milestone_tools.py](../tests/unit/tools/test_milestone_tools.py)
- [tests/unit/tools/test_task_tools.py](../tests/unit/tools/test_task_tools.py)
- [tests/unit/tools/test_issue_tools.py](../tests/unit/tools/test_issue_tools.py)
- [tests/unit/tools/test_userstory_tools.py](../tests/unit/tools/test_userstory_tools.py)
- [tests/unit/tools/test_project_tools.py](../tests/unit/tools/test_project_tools.py)
- [tests/unit/tools/test_wiki_tools.py](../tests/unit/tools/test_wiki_tools.py)
- [tests/unit/tools/test_membership_tools.py](../tests/unit/tools/test_membership_tools.py)
- [tests/unit/tools/test_webhook_tools.py](../tests/unit/tools/test_webhook_tools.py)
- [tests/integration/test_epic_use_cases.py](../tests/integration/test_epic_use_cases.py)
- [tests/integration/test_milestones_integration.py](../tests/integration/test_milestones_integration.py)
- [tests/integration/test_tasks_integration.py](../tests/integration/test_tasks_integration.py)
- [tests/integration/test_issues_integration.py](../tests/integration/test_issues_integration.py)
- [tests/integration/test_projects_integration.py](../tests/integration/test_projects_integration.py)
- [tests/integration/test_wiki_integration.py](../tests/integration/test_wiki_integration.py)
- [tests/integration/test_memberships_integration.py](../tests/integration/test_memberships_integration.py)
- [tests/integration/test_webhooks_integration.py](../tests/integration/test_webhooks_integration.py)
- [tests/functional/test_epic_tools_functional.py](../tests/functional/test_epic_tools_functional.py)

### Total de Archivos Modificados
- **Código fuente**: 9 archivos
- **Tests**: 18 archivos
- **Total**: 27 archivos

## Mejoras de Código Adicionales

Durante la refactorización, también se realizaron las siguientes mejoras:

### 1. Simplificación de Return Statements (RET504)
Se eliminaron asignaciones innecesarias antes de return statements en [epic_tools.py](../src/application/tools/epic_tools.py):

**Antes:**
```python
async with client:
    result = await client.get_epic(epic_id)
    return result
```

**Después:**
```python
async with client:
    return await client.get_epic(epic_id)
```

**Impacto**: 11 métodos simplificados en epic_tools.py

### 2. Corrección de Longitud de Línea (E501)
Se corrigieron líneas demasiado largas (>100 caracteres) en múltiples archivos:
- [src/application/tools/auth_tools.py](../src/application/tools/auth_tools.py)
- [src/domain/entities/attachment.py](../src/domain/entities/attachment.py)
- [src/domain/entities/related_userstory.py](../src/domain/entities/related_userstory.py)
- [tests/integration/test_projects_integration.py](../tests/integration/test_projects_integration.py)
- [tests/unit/tools/test_userstories.py](../tests/unit/tools/test_userstories.py)

### 3. Corrección de Tipos de Retorno
Se corrigieron tipos de retorno en métodos de utilidad:
- `set_client: -> Any` cambiado a `-> None`
- `_register_tools: -> Any` cambiado a `-> None`
- `register_tools: -> Any` cambiado a `-> None`

## Fecha de Implementación

**Fecha**: 2025-12-09
**Tarea**: Tarea 2.4 - Eliminar Parámetros Redundantes (Aliases)
**Responsable**: Equipo de Desarrollo
**Estado**: ✅ Completado

## Referencias

- [Convenciones de Nomenclatura Python (PEP 8)](https://pep8.org/#naming-conventions)
- [Taiga API Documentation](https://docs.taiga.io/api.html)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Ruff Linter](https://docs.astral.sh/ruff/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [mypy Type Checker](https://mypy.readthedocs.io/)
