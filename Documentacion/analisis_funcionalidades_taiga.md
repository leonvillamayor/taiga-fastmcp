# Análisis Exhaustivo de Funcionalidades de Taiga API

## Metodología
Este documento extrae TODAS las funcionalidades de la API de Taiga documentadas en `Documentacion/taiga.md` (1791 líneas).

---

## 1. AUTENTICACIÓN (3 funcionalidades)

### 1.1 Autenticación Básica
- **AUTH-001**: `POST /api/v1/auth` - Obtener token con usuario/contraseña
  - Parámetros: type, username, password
  - Respuesta: auth_token, refresh token, datos de usuario

### 1.2 Refresh Token
- **AUTH-002**: `POST /api/v1/auth/refresh` - Renovar token expirado
  - Parámetros: refresh token
  - Respuesta: nuevo auth_token

### 1.3 Información Usuario Actual
- **AUTH-003**: `GET /api/v1/users/me` - Obtener datos del usuario autenticado
  - Respuesta: perfil completo, proyectos, roles

---

## 2. PROYECTOS (21 funcionalidades)

### 2.1 CRUD Básico (7)
- **PROJ-001**: `GET /api/v1/projects` - Listar proyectos
- **PROJ-002**: `POST /api/v1/projects` - Crear proyecto
- **PROJ-003**: `GET /api/v1/projects/{id}` - Obtener proyecto por ID
- **PROJ-004**: `GET /api/v1/projects/by_slug?slug={slug}` - Obtener por slug
- **PROJ-005**: `PUT /api/v1/projects/{id}` - Modificar proyecto completo
- **PROJ-006**: `PATCH /api/v1/projects/{id}` - Modificar proyecto parcial
- **PROJ-007**: `DELETE /api/v1/projects/{id}` - Eliminar proyecto

### 2.2 Estadísticas (2)
- **PROJ-008**: `GET /api/v1/projects/{id}/stats` - Estadísticas generales
- **PROJ-009**: `GET /api/v1/projects/{id}/issues_stats` - Estadísticas de issues

### 2.3 Módulos (2)
- **PROJ-010**: `GET /api/v1/projects/{id}/modules` - Obtener módulos activos
- **PROJ-011**: `PATCH /api/v1/projects/{id}/modules` - Activar/desactivar módulos

### 2.4 Etiquetas/Tags (4)
- **PROJ-012**: `POST /api/v1/projects/{id}/create_tag` - Crear tag
- **PROJ-013**: `POST /api/v1/projects/{id}/edit_tag` - Editar tag
- **PROJ-014**: `POST /api/v1/projects/{id}/delete_tag` - Eliminar tag
- **PROJ-015**: `POST /api/v1/projects/{id}/mix_tags` - Mezclar/fusionar tags

### 2.5 Interacciones (4)
- **PROJ-016**: `POST /api/v1/projects/{id}/like` - Me gusta al proyecto
- **PROJ-017**: `POST /api/v1/projects/{id}/unlike` - Quitar me gusta
- **PROJ-018**: `POST /api/v1/projects/{id}/watch` - Observar proyecto
- **PROJ-019**: `POST /api/v1/projects/{id}/unwatch` - Dejar de observar

### 2.6 Operaciones Avanzadas (2)
- **PROJ-020**: `POST /api/v1/projects/{id}/duplicate` - Duplicar proyecto
- **PROJ-021**: `POST /api/v1/projects/bulk_update_order` - Reordenar proyectos en lote

---

## 3. USER STORIES (35 funcionalidades)

### 3.1 CRUD Básico (7)
- **US-001**: `GET /api/v1/userstories` - Listar user stories
  - Filtros: project, milestone, status, assigned_to, tags, is_closed
- **US-002**: `POST /api/v1/userstories` - Crear user story
- **US-003**: `GET /api/v1/userstories/{id}` - Obtener user story por ID
- **US-004**: `GET /api/v1/userstories/by_ref?ref={ref}&project={projectId}` - Por referencia
- **US-005**: `PUT /api/v1/userstories/{id}` - Modificar completo
- **US-006**: `PATCH /api/v1/userstories/{id}` - Modificar parcial
- **US-007**: `DELETE /api/v1/userstories/{id}` - Eliminar

### 3.2 Operaciones en Lote (5)
- **US-008**: `POST /api/v1/userstories/bulk_create` - Crear múltiples
- **US-009**: `POST /api/v1/userstories/bulk_update_backlog_order` - Reordenar en backlog
- **US-010**: `POST /api/v1/userstories/bulk_update_kanban_order` - Reordenar en kanban
- **US-011**: `POST /api/v1/userstories/bulk_update_sprint_order` - Reordenar en sprint
- **US-012**: `POST /api/v1/userstories/bulk_update_milestone` - Cambiar milestone en lote

### 3.3 Filtros (1)
- **US-013**: `GET /api/v1/userstories/filters_data?project={id}` - Datos para filtrado

### 3.4 Votación (3)
- **US-014**: `POST /api/v1/userstories/{id}/upvote` - Votar positivo
- **US-015**: `POST /api/v1/userstories/{id}/downvote` - Votar negativo
- **US-016**: `GET /api/v1/userstories/{id}/voters` - Listar votantes

### 3.5 Watchers (3)
- **US-017**: `POST /api/v1/userstories/{id}/watch` - Observar
- **US-018**: `POST /api/v1/userstories/{id}/unwatch` - Dejar de observar
- **US-019**: `GET /api/v1/userstories/{id}/watchers` - Listar observadores

### 3.6 Adjuntos (5)
- **US-020**: `GET /api/v1/userstories/attachments` - Listar adjuntos
- **US-021**: `POST /api/v1/userstories/attachments` - Subir adjunto
- **US-022**: `GET /api/v1/userstories/attachments/{id}` - Obtener adjunto
- **US-023**: `PUT/PATCH /api/v1/userstories/attachments/{id}` - Modificar adjunto
- **US-024**: `DELETE /api/v1/userstories/attachments/{id}` - Eliminar adjunto

### 3.7 Historial (5)
- **US-025**: `GET /api/v1/history/userstory/{id}` - Obtener historial
- **US-026**: `GET /api/v1/history/userstory/{id}/commentVersions?id={commentId}` - Versiones de comentario
- **US-027**: `POST /api/v1/history/userstory/{id}/edit_comment?id={commentId}` - Editar comentario
- **US-028**: `POST /api/v1/history/userstory/{id}/delete_comment?id={commentId}` - Eliminar comentario
- **US-029**: `POST /api/v1/history/userstory/{id}/undelete_comment?id={commentId}` - Restaurar comentario

### 3.8 Atributos Personalizados (6)
- **US-030**: `GET /api/v1/userstory-custom-attributes?project={id}` - Listar atributos
- **US-031**: `POST /api/v1/userstory-custom-attributes` - Crear atributo
- **US-032**: `GET /api/v1/userstory-custom-attributes/{id}` - Obtener atributo
- **US-033**: `PUT /api/v1/userstory-custom-attributes/{id}` - Modificar atributo completo
- **US-034**: `PATCH /api/v1/userstory-custom-attributes/{id}` - Modificar atributo parcial
- **US-035**: `DELETE /api/v1/userstory-custom-attributes/{id}` - Eliminar atributo

---

## 4. ISSUES (30 funcionalidades)

### 4.1 CRUD Básico (7)
- **ISSUE-001**: `GET /api/v1/issues` - Listar issues
  - Filtros: project, status, severity, priority, type, assigned_to, tags, is_closed
- **ISSUE-002**: `POST /api/v1/issues` - Crear issue
- **ISSUE-003**: `GET /api/v1/issues/{id}` - Obtener issue por ID
- **ISSUE-004**: `GET /api/v1/issues/by_ref?ref={ref}&project={projectId}` - Por referencia
- **ISSUE-005**: `PUT /api/v1/issues/{id}` - Modificar completo
- **ISSUE-006**: `PATCH /api/v1/issues/{id}` - Modificar parcial
- **ISSUE-007**: `DELETE /api/v1/issues/{id}` - Eliminar

### 4.2 Operaciones en Lote (1)
- **ISSUE-008**: `POST /api/v1/issues/bulk_create` - Crear múltiples

### 4.3 Filtros (1)
- **ISSUE-009**: `GET /api/v1/issues/filters_data?project={id}` - Datos para filtrado

### 4.4 Votación (3)
- **ISSUE-010**: `POST /api/v1/issues/{id}/upvote` - Votar positivo
- **ISSUE-011**: `POST /api/v1/issues/{id}/downvote` - Votar negativo
- **ISSUE-012**: `GET /api/v1/issues/{id}/voters` - Listar votantes

### 4.5 Watchers (3)
- **ISSUE-013**: `POST /api/v1/issues/{id}/watch` - Observar
- **ISSUE-014**: `POST /api/v1/issues/{id}/unwatch` - Dejar de observar
- **ISSUE-015**: `GET /api/v1/issues/{id}/watchers` - Listar observadores

### 4.6 Adjuntos (5)
- **ISSUE-016**: `GET /api/v1/issues/attachments` - Listar adjuntos
- **ISSUE-017**: `POST /api/v1/issues/attachments` - Subir adjunto
- **ISSUE-018**: `GET /api/v1/issues/attachments/{id}` - Obtener adjunto
- **ISSUE-019**: `PUT/PATCH /api/v1/issues/attachments/{id}` - Modificar adjunto
- **ISSUE-020**: `DELETE /api/v1/issues/attachments/{id}` - Eliminar adjunto

### 4.7 Historial (5)
- **ISSUE-021**: `GET /api/v1/history/issue/{id}` - Obtener historial
- **ISSUE-022**: `POST /api/v1/history/issue/{id}/commentVersions?id={commentId}` - Versiones
- **ISSUE-023**: `POST /api/v1/history/issue/{id}/edit_comment?id={commentId}` - Editar comentario
- **ISSUE-024**: `POST /api/v1/history/issue/{id}/delete_comment?id={commentId}` - Eliminar comentario
- **ISSUE-025**: `POST /api/v1/history/issue/{id}/undelete_comment?id={commentId}` - Restaurar

### 4.8 Atributos Personalizados (5)
- **ISSUE-026**: `GET /api/v1/issue-custom-attributes?project={id}` - Listar
- **ISSUE-027**: `POST /api/v1/issue-custom-attributes` - Crear
- **ISSUE-028**: `GET /api/v1/issue-custom-attributes/{id}` - Obtener
- **ISSUE-029**: `PUT/PATCH /api/v1/issue-custom-attributes/{id}` - Modificar
- **ISSUE-030**: `DELETE /api/v1/issue-custom-attributes/{id}` - Eliminar

---

## 5. EPICS (28 funcionalidades)

### 5.1 CRUD Básico (7)
- **EPIC-001**: `GET /api/v1/epics` - Listar epics
- **EPIC-002**: `POST /api/v1/epics` - Crear epic
- **EPIC-003**: `GET /api/v1/epics/{id}` - Obtener epic por ID
- **EPIC-004**: `GET /api/v1/epics/by_ref?ref={ref}&project={projectId}` - Por referencia
- **EPIC-005**: `PUT /api/v1/epics/{id}` - Modificar completo
- **EPIC-006**: `PATCH /api/v1/epics/{id}` - Modificar parcial
- **EPIC-007**: `DELETE /api/v1/epics/{id}` - Eliminar

### 5.2 User Stories Relacionadas (5)
- **EPIC-008**: `GET /api/v1/epics/{id}/related_userstories` - Listar US relacionadas
- **EPIC-009**: `POST /api/v1/epics/{id}/related_userstories` - Relacionar US con epic
- **EPIC-010**: `GET /api/v1/epics/{epicId}/related_userstories/{usId}` - Obtener relación
- **EPIC-011**: `PUT/PATCH /api/v1/epics/{epicId}/related_userstories/{usId}` - Modificar relación
- **EPIC-012**: `DELETE /api/v1/epics/{epicId}/related_userstories/{usId}` - Eliminar relación

### 5.3 Operaciones en Lote (2)
- **EPIC-013**: `POST /api/v1/epics/bulk_create` - Crear múltiples epics
- **EPIC-014**: `POST /api/v1/epics/{id}/related_userstories/bulk_create` - Relacionar múltiples US

### 5.4 Filtros (1)
- **EPIC-015**: `GET /api/v1/epics/filters_data?project={id}` - Datos para filtrado

### 5.5 Votación (3)
- **EPIC-016**: `POST /api/v1/epics/{id}/upvote` - Votar positivo
- **EPIC-017**: `POST /api/v1/epics/{id}/downvote` - Votar negativo
- **EPIC-018**: `GET /api/v1/epics/{id}/voters` - Listar votantes

### 5.6 Watchers (3)
- **EPIC-019**: `POST /api/v1/epics/{id}/watch` - Observar
- **EPIC-020**: `POST /api/v1/epics/{id}/unwatch` - Dejar de observar
- **EPIC-021**: `GET /api/v1/epics/{id}/watchers` - Listar observadores

### 5.7 Adjuntos (5)
- **EPIC-022**: `GET /api/v1/epics/attachments` - Listar adjuntos
- **EPIC-023**: `POST /api/v1/epics/attachments` - Subir adjunto
- **EPIC-024**: `GET /api/v1/epics/attachments/{id}` - Obtener adjunto
- **EPIC-025**: `PUT/PATCH /api/v1/epics/attachments/{id}` - Modificar adjunto
- **EPIC-026**: `DELETE /api/v1/epics/attachments/{id}` - Eliminar adjunto

### 5.8 Atributos Personalizados (2)
- **EPIC-027**: `GET /api/v1/epic-custom-attributes?project={id}` - Listar
- **EPIC-028**: `POST /api/v1/epic-custom-attributes` - Crear

---

## 6. TASKS (26 funcionalidades)

### 6.1 CRUD Básico (7)
- **TASK-001**: `GET /api/v1/tasks` - Listar tasks
  - Filtros: project, user_story, milestone, status, assigned_to, tags, is_closed
- **TASK-002**: `POST /api/v1/tasks` - Crear task
- **TASK-003**: `GET /api/v1/tasks/{id}` - Obtener task por ID
- **TASK-004**: `GET /api/v1/tasks/by_ref?ref={ref}&project={projectId}` - Por referencia
- **TASK-005**: `PUT /api/v1/tasks/{id}` - Modificar completo
- **TASK-006**: `PATCH /api/v1/tasks/{id}` - Modificar parcial
- **TASK-007**: `DELETE /api/v1/tasks/{id}` - Eliminar

### 6.2 Operaciones en Lote (1)
- **TASK-008**: `POST /api/v1/tasks/bulk_create` - Crear múltiples

### 6.3 Filtros (1)
- **TASK-009**: `GET /api/v1/tasks/filters_data?project={id}` - Datos para filtrado

### 6.4 Votación (3)
- **TASK-010**: `POST /api/v1/tasks/{id}/upvote` - Votar positivo
- **TASK-011**: `POST /api/v1/tasks/{id}/downvote` - Votar negativo
- **TASK-012**: `GET /api/v1/tasks/{id}/voters` - Listar votantes

### 6.5 Watchers (3)
- **TASK-013**: `POST /api/v1/tasks/{id}/watch` - Observar
- **TASK-014**: `POST /api/v1/tasks/{id}/unwatch` - Dejar de observar
- **TASK-015**: `GET /api/v1/tasks/{id}/watchers` - Listar observadores

### 6.6 Adjuntos (5)
- **TASK-016**: `GET /api/v1/tasks/attachments` - Listar adjuntos
- **TASK-017**: `POST /api/v1/tasks/attachments` - Subir adjunto
- **TASK-018**: `GET /api/v1/tasks/attachments/{id}` - Obtener adjunto
- **TASK-019**: `PUT/PATCH /api/v1/tasks/attachments/{id}` - Modificar adjunto
- **TASK-020**: `DELETE /api/v1/tasks/attachments/{id}` - Eliminar adjunto

### 6.7 Historial (5)
- **TASK-021**: `GET /api/v1/history/task/{id}` - Obtener historial
- **TASK-022**: `POST /api/v1/history/task/{id}/commentVersions?id={commentId}` - Versiones
- **TASK-023**: `POST /api/v1/history/task/{id}/edit_comment?id={commentId}` - Editar comentario
- **TASK-024**: `POST /api/v1/history/task/{id}/delete_comment?id={commentId}` - Eliminar comentario
- **TASK-025**: `POST /api/v1/history/task/{id}/undelete_comment?id={commentId}` - Restaurar

### 6.8 Atributos Personalizados (1)
- **TASK-026**: `GET /api/v1/task-custom-attributes?project={id}` - Listar

---

## 7. MILESTONES/SPRINTS (8 funcionalidades)

### 7.1 CRUD Básico (6)
- **MILE-001**: `GET /api/v1/milestones` - Listar milestones
- **MILE-002**: `POST /api/v1/milestones` - Crear milestone
- **MILE-003**: `GET /api/v1/milestones/{id}` - Obtener milestone por ID
- **MILE-004**: `PUT /api/v1/milestones/{id}` - Modificar completo
- **MILE-005**: `PATCH /api/v1/milestones/{id}` - Modificar parcial
- **MILE-006**: `DELETE /api/v1/milestones/{id}` - Eliminar

### 7.2 Estadísticas (1)
- **MILE-007**: `GET /api/v1/milestones/{id}/stats` - Estadísticas del sprint

### 7.3 Watchers (1)
- **MILE-008**: `POST /api/v1/milestones/{id}/watch` - Observar
- **MILE-009**: `POST /api/v1/milestones/{id}/unwatch` - Dejar de observar
- **MILE-010**: `GET /api/v1/milestones/{id}/watchers` - Listar observadores

---

## 8. WIKI (10 funcionalidades estimadas)

### 8.1 Historial de Wiki (5)
- **WIKI-001**: `GET /api/v1/history/wiki/{id}` - Obtener historial
- **WIKI-002**: `POST /api/v1/history/wiki/{id}/commentVersions?id={commentId}` - Versiones
- **WIKI-003**: `POST /api/v1/history/wiki/{id}/edit_comment?id={commentId}` - Editar
- **WIKI-004**: `POST /api/v1/history/wiki/{id}/delete_comment?id={commentId}` - Eliminar
- **WIKI-005**: `POST /api/v1/history/wiki/{id}/undelete_comment?id={commentId}` - Restaurar

### 8.2 CRUD Wiki (estimado - no completamente documentado)
- **WIKI-006**: `GET /api/v1/wiki` - Listar páginas (estimado)
- **WIKI-007**: `POST /api/v1/wiki` - Crear página (estimado)
- **WIKI-008**: `GET /api/v1/wiki/{id}` - Obtener página (estimado)
- **WIKI-009**: `PUT/PATCH /api/v1/wiki/{id}` - Modificar (estimado)
- **WIKI-010**: `DELETE /api/v1/wiki/{id}` - Eliminar (estimado)

---

## 9. USUARIOS Y MEMBRESÍAS (6 funcionalidades)

### 9.1 Usuarios (2)
- **USER-001**: `GET /api/v1/users/me` - Usuario actual (ya contado en AUTH-003)
- **USER-002**: `GET /api/v1/users?project={id}` - Listar usuarios

### 9.2 Membresías (5)
- **MEMB-001**: `GET /api/v1/memberships?project={id}` - Listar membresías
- **MEMB-002**: `POST /api/v1/memberships` - Crear membresía (invitar usuario)
- **MEMB-003**: `GET /api/v1/memberships/{id}` - Obtener membresía
- **MEMB-004**: `PUT/PATCH /api/v1/memberships/{id}` - Modificar membresía/rol
- **MEMB-005**: `DELETE /api/v1/memberships/{id}` - Eliminar membresía

---

## 10. WEBHOOKS (1 funcionalidad)

- **WEBHOOK-001**: Configuración de webhooks para eventos
  - Eventos: milestones, user stories, tasks, issues, wiki pages
  - Configuración vía interfaz web/API (no completamente documentado)

---

## RESUMEN TOTAL DE FUNCIONALIDADES

| Categoría | Cantidad | Códigos |
|-----------|----------|---------|
| **Autenticación** | 3 | AUTH-001 a AUTH-003 |
| **Proyectos** | 21 | PROJ-001 a PROJ-021 |
| **User Stories** | 35 | US-001 a US-035 |
| **Issues** | 30 | ISSUE-001 a ISSUE-030 |
| **Epics** | 28 | EPIC-001 a EPIC-028 |
| **Tasks** | 26 | TASK-001 a TASK-026 |
| **Milestones/Sprints** | 10 | MILE-001 a MILE-010 |
| **Wiki** | 10 | WIKI-001 a WIKI-010 |
| **Usuarios** | 1 | USER-002 |
| **Membresías** | 5 | MEMB-001 a MEMB-005 |
| **Webhooks** | 1 | WEBHOOK-001 |
| **TOTAL** | **170** | |

---

## FUNCIONALIDADES COMUNES/TRANSVERSALES

Muchas entidades comparten patrones similares:

### Patrón CRUD Completo (7 operaciones)
- GET list
- POST create
- GET by ID
- GET by ref
- PUT update (completo)
- PATCH update (parcial)
- DELETE delete

### Patrón de Interacciones Sociales (6 operaciones)
- upvote
- downvote
- voters (get)
- watch
- unwatch
- watchers (get)

### Patrón de Adjuntos (5 operaciones)
- GET list attachments
- POST create attachment
- GET attachment by ID
- PUT/PATCH update attachment
- DELETE attachment

### Patrón de Historial (5 operaciones)
- GET history
- commentVersions
- edit_comment
- delete_comment
- undelete_comment

### Patrón de Atributos Personalizados (5 operaciones)
- GET list custom attributes
- POST create custom attribute
- GET custom attribute by ID
- PUT/PATCH update custom attribute
- DELETE custom attribute

### Patrón de Filtros (1 operación)
- GET filters_data

### Operaciones Bulk
- bulk_create
- bulk_update_*

---

## ANÁLISIS DE CARACTERÍSTICAS GENERALES DE LA API

### 1. Paginación
- Headers: X-Pagination-Count, X-Pagination-Current, X-Pagination-Next, X-Pagination-Prev
- Opción para deshabilitar: Header `x-disable-pagination: True`

### 2. Control de Concurrencia Optimista
- Campo `version` requerido en actualizaciones
- Error 409 (Conflict) si hay conflicto

### 3. Internacionalización
- Header `Accept-Language`
- Idiomas: en, es, fr, de, it, pt, ru, zh-Hans, etc.

### 4. Rate Limiting
- Error 429 Too Many Requests
- Headers: X-Throttle-Remaining, X-Throttle-Reset

### 5. Campos de Solo Lectura
- Campos terminados en `_extra_info`

---

## CONCLUSIÓN

La API de Taiga tiene **aproximadamente 170 funcionalidades distintas** documentadas, organizadas en 11 categorías principales. Muchas funcionalidades siguen patrones comunes (CRUD, social interactions, attachments, history), lo que facilita su implementación sistemática.
