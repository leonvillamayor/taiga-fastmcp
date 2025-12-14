# Documentación Completa de la API de Taiga

## Índice

1. [Introducción](#introducción)
2. [Autenticación](#autenticación)
3. [Características Generales de la API](#características-generales-de-la-api)
4. [Proyectos (Projects)](#proyectos-projects)
5. [User Stories (Historias de Usuario)](#user-stories-historias-de-usuario)
6. [Issues (Problemas/Incidencias)](#issues-problemasincidencias)
7. [Epics (Épicas)](#epics-épicas)
8. [Tasks (Tareas)](#tasks-tareas)
9. [Milestones/Sprints](#milestonessprints)
10. [History y Comentarios](#history-y-comentarios)
11. [Usuarios y Membresías](#usuarios-y-membresías)
12. [Atributos Personalizados](#atributos-personalizados)
13. [Webhooks](#webhooks)
14. [Ejemplos Completos](#ejemplos-completos)

---

## Introducción

**Taiga** es una plataforma de gestión de proyectos ágiles de código abierto. Su API REST permite interactuar programáticamente con todos los recursos de la plataforma.

### URL Base

- **Producción (Taiga Cloud)**: `https://api.taiga.io/api/v1`
- **Local/Self-hosted**: `http://localhost:8000/api/v1` (o tu dominio personalizado)

### Formato de Datos

- **Request**: JSON (`Content-Type: application/json`)
- **Response**: JSON
- **Encoding**: UTF-8

---

## Autenticación

Taiga soporta dos métodos principales de autenticación mediante tokens Bearer.

### 1. Token Estándar (Usuario/Contraseña)

#### Obtener Token

**Endpoint**: `POST /api/v1/auth`

**Request**:
```json
{
  "type": "normal",
  "username": "usuario@example.com",
  "password": "tu_contraseña"
}
```

**Response**:
```json
{
  "id": 888691,
  "username": "usuario",
  "full_name": "Usuario Completo",
  "full_name_display": "Usuario Completo",
  "color": "#121a86",
  "bio": "",
  "lang": "",
  "theme": "",
  "timezone": "",
  "is_active": true,
  "photo": null,
  "big_photo": null,
  "gravatar_id": "6d5851ce63b3246e331b5dddf2af9d33",
  "roles": ["Product Owner"],
  "total_private_projects": 1,
  "total_public_projects": 0,
  "email": "usuario@example.com",
  "uuid": "afe12dedb1514eb781b25ab5dedfa762",
  "date_joined": "2025-11-28T18:12:11.368Z",
  "read_new_terms": true,
  "accepted_terms": true,
  "auth_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Ejemplo de Autenticación

```bash
# Obtener token
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"type": "normal", "username": "user@example.com", "password": "pass"}' \
  https://api.taiga.io/api/v1/auth
```

```python
import requests

response = requests.post(
    "https://api.taiga.io/api/v1/auth",
    json={
        "type": "normal",
        "username": "user@example.com",
        "password": "password123"
    }
)
data = response.json()
auth_token = data["auth_token"]
```

#### Usar Token en Requests

**Header**: `Authorization: Bearer {AUTH_TOKEN}`

```bash
curl -X GET \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..." \
  https://api.taiga.io/api/v1/projects
```

```python
headers = {
    "Authorization": f"Bearer {auth_token}",
    "Content-Type": "application/json"
}
response = requests.get("https://api.taiga.io/api/v1/projects", headers=headers)
```

### 2. Token de Aplicación

Para aplicaciones externas que requieren permisos específicos.

**Formato**: `Authorization: Application {AUTH_TOKEN}`

**Proceso**:
1. Verificar token existente
2. Solicitar código de autorización
3. Validar código
4. Desencriptar token (usa JWE con algoritmo A128KW)

### 3. Refresh Token

Los tokens tienen expiración. Usar el `refresh` token para obtener uno nuevo:

**Endpoint**: `POST /api/v1/auth/refresh`

**Request**:
```json
{
  "refresh": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## Características Generales de la API

### Paginación

Por defecto, la API pagina las respuestas.

**Headers de respuesta**:
- `X-Pagination-Count`: Total de elementos
- `X-Pagination-Current`: Página actual
- `X-Pagination-Next`: URL de la siguiente página
- `X-Pagination-Prev`: URL de la página anterior

**Deshabilitar paginación**:
```bash
curl -H "x-disable-pagination: True" https://api.taiga.io/api/v1/projects
```

### Control de Concurrencia Optimista

Para evitar conflictos en actualizaciones concurrentes, se requiere el campo `version` en operaciones de modificación.

**Ejemplo**:
```json
{
  "version": 5,
  "subject": "Updated subject"
}
```

Si otro usuario modificó el recurso, recibirás un error 409 (Conflict).

### Internacionalización

Especificar idioma mediante header:

```bash
curl -H "Accept-Language: es" https://api.taiga.io/api/v1/projects
```

Idiomas disponibles: `en`, `es`, `fr`, `de`, `it`, `pt`, `ru`, `zh-Hans`, etc.

### Campos de Solo Lectura

Campos terminados en `_extra_info` son de solo lectura y se ignoran en requests de creación/actualización.

### Rate Limiting

La API implementa throttling. Si excedes el límite, recibirás:

**Response**: `429 Too Many Requests`

**Headers**:
- `X-Throttle-Remaining`: Solicitudes restantes
- `X-Throttle-Reset`: Timestamp de reset

---

## Proyectos (Projects)

Los proyectos son el contenedor principal para todos los recursos en Taiga.

### Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/projects` | Listar proyectos |
| POST | `/api/v1/projects` | Crear proyecto |
| GET | `/api/v1/projects/{projectId}` | Obtener proyecto por ID |
| GET | `/api/v1/projects/by_slug?slug={slug}` | Obtener proyecto por slug |
| PUT | `/api/v1/projects/{projectId}` | Modificar proyecto (completo) |
| PATCH | `/api/v1/projects/{projectId}` | Modificar proyecto (parcial) |
| DELETE | `/api/v1/projects/{projectId}` | Eliminar proyecto |

### Listar Proyectos

**Request**:
```bash
GET /api/v1/projects
```

**Response**:
```json
[
  {
    "id": 309804,
    "name": "Mi Proyecto",
    "slug": "mi-proyecto",
    "description": "Descripción del proyecto",
    "created_date": "2025-01-15T10:00:00Z",
    "modified_date": "2025-01-20T14:30:00Z",
    "owner": {
      "id": 888691,
      "username": "usuario",
      "full_name_display": "Usuario Completo"
    },
    "tags": ["backend", "api"],
    "is_private": false,
    "total_milestones": 3,
    "total_story_points": 45.0,
    "is_backlog_activated": true,
    "is_kanban_activated": true,
    "is_wiki_activated": true,
    "is_issues_activated": true,
    "members": [...]
  }
]
```

### Crear Proyecto

**Request**:
```json
POST /api/v1/projects
{
  "name": "Nuevo Proyecto",
  "description": "Descripción del nuevo proyecto",
  "is_private": true,
  "tags": ["desarrollo", "mvp"],
  "is_backlog_activated": true,
  "is_kanban_activated": true,
  "is_wiki_activated": true,
  "is_issues_activated": true
}
```

**Response**: Objeto del proyecto creado con ID asignado.

### Obtener Proyecto por ID

**Request**:
```bash
GET /api/v1/projects/309804
```

**Response**: Objeto completo del proyecto.

### Obtener Proyecto por Slug

**Request**:
```bash
GET /api/v1/projects/by_slug?slug=mi-proyecto
```

### Modificar Proyecto (Parcial)

**Request**:
```json
PATCH /api/v1/projects/309804
{
  "version": 2,
  "name": "Proyecto Renombrado",
  "description": "Nueva descripción"
}
```

### Eliminar Proyecto

**Request**:
```bash
DELETE /api/v1/projects/309804
```

**Response**: `204 No Content`

### Funcionalidades Adicionales de Proyectos

#### Estadísticas

```bash
GET /api/v1/projects/{projectId}/stats
GET /api/v1/projects/{projectId}/issues_stats
```

**Response Ejemplo**:
```json
{
  "total_points": 120.0,
  "closed_points": 80.0,
  "total_userstories": 24,
  "closed_userstories": 16,
  "total_issues": 15,
  "closed_issues": 10
}
```

#### Módulos del Proyecto

```bash
GET /api/v1/projects/{projectId}/modules
PATCH /api/v1/projects/{projectId}/modules
```

Habilitar/deshabilitar backlog, kanban, wiki, issues, epics.

#### Gestión de Etiquetas (Tags)

```bash
POST /api/v1/projects/{projectId}/create_tag
POST /api/v1/projects/{projectId}/edit_tag
POST /api/v1/projects/{projectId}/delete_tag
POST /api/v1/projects/{projectId}/mix_tags
```

#### Like/Unlike y Watch/Unwatch

```bash
POST /api/v1/projects/{projectId}/like
POST /api/v1/projects/{projectId}/unlike
POST /api/v1/projects/{projectId}/watch
POST /api/v1/projects/{projectId}/unwatch
```

#### Duplicar Proyecto

```bash
POST /api/v1/projects/{projectId}/duplicate
```

#### Reordenar Proyectos

```bash
POST /api/v1/projects/bulk_update_order
```

**Request**:
```json
{
  "bulk_projects": [[1, 0], [2, 1], [3, 2]]
}
```

---

## User Stories (Historias de Usuario)

Las User Stories representan funcionalidades desde la perspectiva del usuario.

### Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/userstories` | Listar user stories |
| POST | `/api/v1/userstories` | Crear user story |
| GET | `/api/v1/userstories/{usId}` | Obtener user story |
| GET | `/api/v1/userstories/by_ref?ref={ref}&project={projectId}` | Por referencia |
| PUT | `/api/v1/userstories/{usId}` | Modificar (completo) |
| PATCH | `/api/v1/userstories/{usId}` | Modificar (parcial) |
| DELETE | `/api/v1/userstories/{usId}` | Eliminar |

### Listar User Stories

**Request**:
```bash
GET /api/v1/userstories?project=309804
```

**Filtros disponibles**:
- `project`: ID del proyecto
- `milestone`: ID del sprint
- `status`: ID del estado
- `assigned_to`: ID del usuario asignado
- `tags`: Lista de tags
- `is_closed`: true/false

**Response**:
```json
[
  {
    "id": 123456,
    "ref": 1,
    "version": 3,
    "subject": "Como usuario quiero login",
    "description": "## Descripción\nImplementar login de usuarios",
    "status": 2,
    "status_extra_info": {
      "name": "In Progress",
      "color": "#ff9900"
    },
    "project": 309804,
    "milestone": 5678,
    "milestone_name": "Sprint 1",
    "assigned_to": 888691,
    "assigned_to_extra_info": {
      "username": "usuario",
      "full_name_display": "Usuario Completo"
    },
    "owner": 888691,
    "tags": ["backend", "auth"],
    "points": {
      "1": 5,
      "2": 3,
      "3": 8
    },
    "total_points": 5.0,
    "is_closed": false,
    "is_blocked": false,
    "blocked_note": "",
    "created_date": "2025-01-15T10:00:00Z",
    "modified_date": "2025-01-20T14:30:00Z",
    "finish_date": null,
    "watchers": [888691],
    "total_watchers": 1,
    "total_voters": 3
  }
]
```

### Crear User Story

**Request**:
```json
POST /api/v1/userstories
{
  "project": 309804,
  "subject": "Nueva historia de usuario",
  "description": "## Descripción\nImplementar funcionalidad X",
  "status": 1,
  "milestone": 5678,
  "assigned_to": 888691,
  "tags": ["feature", "backend"],
  "points": {
    "1": 3,
    "2": 2,
    "3": 5
  }
}
```

### Actualizar User Story

**Request**:
```json
PATCH /api/v1/userstories/123456
{
  "version": 3,
  "subject": "Título actualizado",
  "description": "Nueva descripción",
  "status": 3,
  "assigned_to": 999999
}
```

### Obtener por Referencia

**Request**:
```bash
GET /api/v1/userstories/by_ref?ref=1&project=309804
```

### Eliminar User Story

**Request**:
```bash
DELETE /api/v1/userstories/123456
```

### Operaciones en Lote (Bulk)

#### Crear Múltiples User Stories

**Request**:
```json
POST /api/v1/userstories/bulk_create
{
  "project_id": 309804,
  "bulk_stories": [
    {"subject": "Historia 1", "description": "Desc 1"},
    {"subject": "Historia 2", "description": "Desc 2"},
    {"subject": "Historia 3", "description": "Desc 3"}
  ]
}
```

#### Reordenar en Backlog

**Request**:
```json
POST /api/v1/userstories/bulk_update_backlog_order
{
  "project_id": 309804,
  "bulk_stories": [[123, 0], [124, 1], [125, 2]]
}
```

#### Reordenar en Kanban

**Request**:
```json
POST /api/v1/userstories/bulk_update_kanban_order
{
  "project_id": 309804,
  "bulk_stories": [[123, 0], [124, 1]],
  "status": 2
}
```

#### Reordenar en Sprint

**Request**:
```json
POST /api/v1/userstories/bulk_update_sprint_order
{
  "project_id": 309804,
  "milestone_id": 5678,
  "bulk_stories": [[123, 0], [124, 1]]
}
```

#### Actualizar Milestone en Lote

**Request**:
```json
POST /api/v1/userstories/bulk_update_milestone
{
  "project_id": 309804,
  "milestone_id": 5678,
  "bulk_stories": [123, 124, 125]
}
```

### Filtros

**Request**:
```bash
GET /api/v1/userstories/filters_data?project=309804
```

**Response**: Datos disponibles para filtrado (statuses, assigned users, tags, etc.)

### Votación

```bash
POST /api/v1/userstories/{usId}/upvote
POST /api/v1/userstories/{usId}/downvote
GET /api/v1/userstories/{usId}/voters
```

### Watchers (Observadores)

```bash
POST /api/v1/userstories/{usId}/watch
POST /api/v1/userstories/{usId}/unwatch
GET /api/v1/userstories/{usId}/watchers
```

### Adjuntos

| Método | Endpoint |
|--------|----------|
| GET | `/api/v1/userstories/attachments` |
| POST | `/api/v1/userstories/attachments` |
| GET | `/api/v1/userstories/attachments/{attachmentId}` |
| PUT/PATCH | `/api/v1/userstories/attachments/{attachmentId}` |
| DELETE | `/api/v1/userstories/attachments/{attachmentId}` |

**Crear Adjunto**:
```bash
POST /api/v1/userstories/attachments
Content-Type: multipart/form-data

project=309804
object_id=123456
attached_file=@/path/to/file.pdf
description=Documento de requisitos
```

---

## Issues (Problemas/Incidencias)

Los Issues representan bugs, problemas o incidencias en el proyecto.

### Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/issues` | Listar issues |
| POST | `/api/v1/issues` | Crear issue |
| GET | `/api/v1/issues/{issueId}` | Obtener issue |
| GET | `/api/v1/issues/by_ref?ref={ref}&project={projectId}` | Por referencia |
| PUT | `/api/v1/issues/{issueId}` | Modificar (completo) |
| PATCH | `/api/v1/issues/{issueId}` | Modificar (parcial) |
| DELETE | `/api/v1/issues/{issueId}` | Eliminar |

### Listar Issues

**Request**:
```bash
GET /api/v1/issues?project=309804&status=1
```

**Filtros**:
- `project`
- `status`
- `severity`
- `priority`
- `type`
- `assigned_to`
- `tags`
- `is_closed`

**Response**:
```json
[
  {
    "id": 789012,
    "ref": 10,
    "version": 2,
    "subject": "Error en login",
    "description": "Descripción del error",
    "status": 1,
    "status_extra_info": {
      "name": "New",
      "color": "#ff0000"
    },
    "type": 1,
    "type_extra_info": {
      "name": "Bug"
    },
    "severity": 2,
    "severity_extra_info": {
      "name": "Normal"
    },
    "priority": 3,
    "priority_extra_info": {
      "name": "High"
    },
    "project": 309804,
    "assigned_to": 888691,
    "owner": 888691,
    "tags": ["bug", "critical"],
    "is_closed": false,
    "is_blocked": false,
    "created_date": "2025-01-15T10:00:00Z",
    "modified_date": "2025-01-20T14:30:00Z",
    "watchers": [888691],
    "total_voters": 2
  }
]
```

### Crear Issue

**Request**:
```json
POST /api/v1/issues
{
  "project": 309804,
  "subject": "Nuevo bug encontrado",
  "description": "Descripción detallada del bug",
  "type": 1,
  "status": 1,
  "priority": 3,
  "severity": 2,
  "assigned_to": 888691,
  "tags": ["bug", "frontend"]
}
```

### Actualizar Issue

**Request**:
```json
PATCH /api/v1/issues/789012
{
  "version": 2,
  "status": 2,
  "assigned_to": 999999,
  "severity": 3
}
```

### Crear Múltiples Issues (Bulk)

**Request**:
```json
POST /api/v1/issues/bulk_create
{
  "project_id": 309804,
  "bulk_issues": [
    {"subject": "Bug 1", "type": 1, "severity": 2},
    {"subject": "Bug 2", "type": 1, "severity": 1}
  ]
}
```

### Filtros de Issues

```bash
GET /api/v1/issues/filters_data?project=309804
```

### Votación y Watchers

```bash
POST /api/v1/issues/{issueId}/upvote
POST /api/v1/issues/{issueId}/downvote
GET /api/v1/issues/{issueId}/voters

POST /api/v1/issues/{issueId}/watch
POST /api/v1/issues/{issueId}/unwatch
GET /api/v1/issues/{issueId}/watchers
```

### Adjuntos de Issues

Similar a user stories:

```bash
GET /api/v1/issues/attachments
POST /api/v1/issues/attachments
GET /api/v1/issues/attachments/{attachmentId}
PUT/PATCH /api/v1/issues/attachments/{attachmentId}
DELETE /api/v1/issues/attachments/{attachmentId}
```

---

## Epics (Épicas)

Las Epics agrupan múltiples user stories relacionadas.

### Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/epics` | Listar epics |
| POST | `/api/v1/epics` | Crear epic |
| GET | `/api/v1/epics/{epicId}` | Obtener epic |
| GET | `/api/v1/epics/by_ref?ref={ref}&project={projectId}` | Por referencia |
| PUT | `/api/v1/epics/{epicId}` | Modificar (completo) |
| PATCH | `/api/v1/epics/{epicId}` | Modificar (parcial) |
| DELETE | `/api/v1/epics/{epicId}` | Eliminar |

### Listar Epics

**Request**:
```bash
GET /api/v1/epics?project=309804
```

**Response**:
```json
[
  {
    "id": 456789,
    "ref": 5,
    "version": 1,
    "subject": "Autenticación de Usuarios",
    "description": "Epic para toda la funcionalidad de autenticación",
    "status": 1,
    "color": "#A5694F",
    "project": 309804,
    "assigned_to": 888691,
    "owner": 888691,
    "tags": ["auth", "security"],
    "client_requirement": true,
    "team_requirement": false,
    "created_date": "2025-01-10T08:00:00Z",
    "modified_date": "2025-01-15T12:00:00Z",
    "watchers": [888691]
  }
]
```

### Crear Epic

**Request**:
```json
POST /api/v1/epics
{
  "project": 309804,
  "subject": "Nueva Epic",
  "description": "Descripción de la epic",
  "color": "#A5694F",
  "assigned_to": 888691,
  "tags": ["feature"]
}
```

### Actualizar Epic

**Request**:
```json
PATCH /api/v1/epics/456789
{
  "version": 1,
  "subject": "Epic Actualizada",
  "status": 2
}
```

### User Stories Relacionadas

#### Listar User Stories de una Epic

**Request**:
```bash
GET /api/v1/epics/456789/related_userstories
```

**Response**:
```json
[
  {
    "id": 123,
    "user_story": {
      "id": 123456,
      "ref": 1,
      "subject": "Login de usuarios",
      "status": 2
    },
    "epic": 456789,
    "order": 1
  }
]
```

#### Relacionar User Story con Epic

**Request**:
```json
POST /api/v1/epics/456789/related_userstories
{
  "user_story": 123456,
  "epic": 456789
}
```

#### Obtener/Modificar/Eliminar Relación

```bash
GET /api/v1/epics/{epicId}/related_userstories/{usId}
PUT /api/v1/epics/{epicId}/related_userstories/{usId}
PATCH /api/v1/epics/{epicId}/related_userstories/{usId}
DELETE /api/v1/epics/{epicId}/related_userstories/{usId}
```

### Crear Múltiples Epics (Bulk)

**Request**:
```json
POST /api/v1/epics/bulk_create
{
  "project_id": 309804,
  "bulk_epics": [
    {"subject": "Epic 1", "color": "#A5694F"},
    {"subject": "Epic 2", "color": "#B83A3A"}
  ]
}
```

### Relacionar Múltiples User Stories (Bulk)

**Request**:
```json
POST /api/v1/epics/456789/related_userstories/bulk_create
{
  "bulk_userstories": [123456, 123457, 123458]
}
```

### Filtros, Votación y Watchers

```bash
GET /api/v1/epics/filters_data?project=309804

POST /api/v1/epics/{epicId}/upvote
POST /api/v1/epics/{epicId}/downvote
GET /api/v1/epics/{epicId}/voters

POST /api/v1/epics/{epicId}/watch
POST /api/v1/epics/{epicId}/unwatch
GET /api/v1/epics/{epicId}/watchers
```

### Adjuntos de Epics

```bash
GET /api/v1/epics/attachments
POST /api/v1/epics/attachments
GET /api/v1/epics/attachments/{attachmentId}
PUT/PATCH /api/v1/epics/attachments/{attachmentId}
DELETE /api/v1/epics/attachments/{attachmentId}
```

---

## Tasks (Tareas)

Las Tasks son unidades de trabajo dentro de user stories.

### Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/tasks` | Listar tasks |
| POST | `/api/v1/tasks` | Crear task |
| GET | `/api/v1/tasks/{taskId}` | Obtener task |
| GET | `/api/v1/tasks/by_ref?ref={ref}&project={projectId}` | Por referencia |
| PUT | `/api/v1/tasks/{taskId}` | Modificar (completo) |
| PATCH | `/api/v1/tasks/{taskId}` | Modificar (parcial) |
| DELETE | `/api/v1/tasks/{taskId}` | Eliminar |

### Listar Tasks

**Request**:
```bash
GET /api/v1/tasks?project=309804&user_story=123456
```

**Filtros**:
- `project`
- `user_story`
- `milestone`
- `status`
- `assigned_to`
- `tags`
- `is_closed`

**Response**:
```json
[
  {
    "id": 345678,
    "ref": 20,
    "version": 1,
    "subject": "Implementar validación de email",
    "description": "Agregar validación de formato de email",
    "status": 2,
    "status_extra_info": {
      "name": "In Progress",
      "color": "#ff9900"
    },
    "project": 309804,
    "user_story": 123456,
    "milestone": 5678,
    "assigned_to": 888691,
    "owner": 888691,
    "tags": ["validation", "backend"],
    "is_closed": false,
    "is_blocked": false,
    "created_date": "2025-01-16T09:00:00Z",
    "modified_date": "2025-01-18T11:00:00Z",
    "watchers": [888691]
  }
]
```

### Crear Task

**Request**:
```json
POST /api/v1/tasks
{
  "project": 309804,
  "user_story": 123456,
  "subject": "Nueva tarea",
  "description": "Descripción de la tarea",
  "status": 1,
  "assigned_to": 888691,
  "tags": ["backend"]
}
```

### Actualizar Task

**Request**:
```json
PATCH /api/v1/tasks/345678
{
  "version": 1,
  "status": 3,
  "assigned_to": 999999
}
```

### Crear Múltiples Tasks (Bulk)

**Request**:
```json
POST /api/v1/tasks/bulk_create
{
  "project_id": 309804,
  "user_story_id": 123456,
  "bulk_tasks": [
    {"subject": "Tarea 1"},
    {"subject": "Tarea 2"},
    {"subject": "Tarea 3"}
  ]
}
```

### Filtros

```bash
GET /api/v1/tasks/filters_data?project=309804
```

### Votación y Watchers

```bash
POST /api/v1/tasks/{taskId}/upvote
POST /api/v1/tasks/{taskId}/downvote
GET /api/v1/tasks/{taskId}/voters

POST /api/v1/tasks/{taskId}/watch
POST /api/v1/tasks/{taskId}/unwatch
GET /api/v1/tasks/{taskId}/watchers
```

### Adjuntos de Tasks

```bash
GET /api/v1/tasks/attachments
POST /api/v1/tasks/attachments
GET /api/v1/tasks/attachments/{attachmentId}
PUT/PATCH /api/v1/tasks/attachments/{attachmentId}
DELETE /api/v1/tasks/attachments/{attachmentId}
```

---

## Milestones/Sprints

Los Milestones (también llamados Sprints) son periodos de tiempo para planificar trabajo.

### Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/milestones` | Listar milestones |
| POST | `/api/v1/milestones` | Crear milestone |
| GET | `/api/v1/milestones/{milestoneId}` | Obtener milestone |
| PUT | `/api/v1/milestones/{milestoneId}` | Modificar (completo) |
| PATCH | `/api/v1/milestones/{milestoneId}` | Modificar (parcial) |
| DELETE | `/api/v1/milestones/{milestoneId}` | Eliminar |
| GET | `/api/v1/milestones/{milestoneId}/stats` | Estadísticas |

### Listar Milestones

**Request**:
```bash
GET /api/v1/milestones?project=309804
```

**Response**:
```json
[
  {
    "id": 5678,
    "name": "Sprint 1",
    "slug": "sprint-1",
    "project": 309804,
    "estimated_start": "2025-01-15",
    "estimated_finish": "2025-01-29",
    "created_date": "2025-01-10T08:00:00Z",
    "modified_date": "2025-01-20T12:00:00Z",
    "closed": false,
    "disponibility": 0.0,
    "total_points": 45.0,
    "closed_points": 20.0,
    "user_stories": [
      {
        "id": 123456,
        "ref": 1,
        "subject": "Login de usuarios"
      }
    ],
    "watchers": [888691]
  }
]
```

### Crear Milestone

**Request**:
```json
POST /api/v1/milestones
{
  "project": 309804,
  "name": "Sprint 2",
  "estimated_start": "2025-02-01",
  "estimated_finish": "2025-02-15"
}
```

### Actualizar Milestone

**Request**:
```json
PATCH /api/v1/milestones/5678
{
  "name": "Sprint 1 - Extendido",
  "estimated_finish": "2025-02-05",
  "closed": false
}
```

### Estadísticas del Milestone

**Request**:
```bash
GET /api/v1/milestones/5678/stats
```

**Response**:
```json
{
  "name": "Sprint 1",
  "estimated_start": "2025-01-15",
  "estimated_finish": "2025-01-29",
  "total_points": 45.0,
  "completed_points": 20.0,
  "total_userstories": 10,
  "completed_userstories": 4,
  "total_tasks": 30,
  "completed_tasks": 15,
  "iocaine_doses": 2,
  "days": [
    {
      "day": "2025-01-15",
      "open_points": 45.0,
      "completed_points": 0.0
    },
    {
      "day": "2025-01-16",
      "open_points": 40.0,
      "completed_points": 5.0
    }
  ]
}
```

### Watchers de Milestone

```bash
POST /api/v1/milestones/{milestoneId}/watch
POST /api/v1/milestones/{milestoneId}/unwatch
GET /api/v1/milestones/{milestoneId}/watchers
```

---

## History y Comentarios

Taiga mantiene un historial completo de cambios y comentarios para cada entidad.

### Endpoints de Historial

#### User Stories

```bash
GET /api/v1/history/userstory/{usId}
GET /api/v1/history/userstory/{usId}/commentVersions?id={commentId}
POST /api/v1/history/userstory/{usId}/edit_comment?id={commentId}
POST /api/v1/history/userstory/{usId}/delete_comment?id={commentId}
POST /api/v1/history/userstory/{usId}/undelete_comment?id={commentId}
```

#### Issues

```bash
GET /api/v1/history/issue/{issueId}
POST /api/v1/history/issue/{issueId}/commentVersions?id={commentId}
POST /api/v1/history/issue/{issueId}/edit_comment?id={commentId}
POST /api/v1/history/issue/{issueId}/delete_comment?id={commentId}
POST /api/v1/history/issue/{issueId}/undelete_comment?id={commentId}
```

#### Tasks

```bash
GET /api/v1/history/task/{taskId}
POST /api/v1/history/task/{taskId}/commentVersions?id={commentId}
POST /api/v1/history/task/{taskId}/edit_comment?id={commentId}
POST /api/v1/history/task/{taskId}/delete_comment?id={commentId}
POST /api/v1/history/task/{taskId}/undelete_comment?id={commentId}
```

#### Wiki

```bash
GET /api/v1/history/wiki/{wikiId}
POST /api/v1/history/wiki/{wikiId}/commentVersions?id={commentId}
POST /api/v1/history/wiki/{wikiId}/edit_comment?id={commentId}
POST /api/v1/history/wiki/{wikiId}/delete_comment?id={commentId}
POST /api/v1/history/wiki/{wikiId}/undelete_comment?id={commentId}
```

### Obtener Historial

**Request**:
```bash
GET /api/v1/history/userstory/123456
```

**Response**:
```json
[
  {
    "id": "abc123",
    "user": {
      "username": "usuario",
      "full_name_display": "Usuario Completo"
    },
    "created_at": "2025-01-20T14:30:00Z",
    "type": 1,
    "is_snapshot": false,
    "diff": {
      "status": ["1", "2"],
      "assigned_to": ["888691", "999999"]
    },
    "values": {
      "status": 2,
      "assigned_to": 999999,
      "subject": "Login de usuarios"
    },
    "comment": "Cambiado a In Progress y reasignado",
    "comment_html": "<p>Cambiado a In Progress y reasignado</p>",
    "delete_comment_date": null,
    "delete_comment_user": null
  }
]
```

### Agregar Comentario

Los comentarios se agregan al actualizar la entidad:

**Request**:
```json
PATCH /api/v1/userstories/123456
{
  "version": 3,
  "comment": "Este es un comentario sobre el cambio"
}
```

### Editar Comentario

**Request**:
```json
POST /api/v1/history/userstory/123456/edit_comment?id=abc123
{
  "comment": "Comentario editado"
}
```

### Eliminar Comentario

**Request**:
```bash
POST /api/v1/history/userstory/123456/delete_comment?id=abc123
```

### Restaurar Comentario

**Request**:
```bash
POST /api/v1/history/userstory/123456/undelete_comment?id=abc123
```

---

## Usuarios y Membresías

### Información del Usuario Actual

**Request**:
```bash
GET /api/v1/users/me
```

**Response**:
```json
{
  "id": 888691,
  "username": "usuario",
  "full_name": "Usuario Completo",
  "full_name_display": "Usuario Completo",
  "email": "usuario@example.com",
  "color": "#121a86",
  "bio": "Desarrollador Full Stack",
  "lang": "es",
  "theme": "taiga",
  "timezone": "America/Buenos_Aires",
  "is_active": true,
  "photo": "https://example.com/photo.jpg",
  "roles": ["Product Owner", "Developer"],
  "total_private_projects": 5,
  "total_public_projects": 2,
  "accepted_terms": true,
  "read_new_terms": true
}
```

### Listar Usuarios

**Request**:
```bash
GET /api/v1/users?project=309804
```

### Membresías de Proyecto

```bash
GET /api/v1/memberships?project=309804
POST /api/v1/memberships
GET /api/v1/memberships/{membershipId}
PUT/PATCH /api/v1/memberships/{membershipId}
DELETE /api/v1/memberships/{membershipId}
```

**Crear Membresía**:
```json
POST /api/v1/memberships
{
  "project": 309804,
  "role": 2,
  "email": "nuevo@example.com"
}
```

---

## Atributos Personalizados

Taiga permite definir atributos personalizados para proyectos, user stories, issues, tasks y epics.

### Endpoints

```bash
GET /api/v1/userstory-custom-attributes?project=309804
POST /api/v1/userstory-custom-attributes
GET /api/v1/userstory-custom-attributes/{attributeId}
PUT/PATCH /api/v1/userstory-custom-attributes/{attributeId}
DELETE /api/v1/userstory-custom-attributes/{attributeId}

GET /api/v1/issue-custom-attributes?project=309804
POST /api/v1/issue-custom-attributes

GET /api/v1/task-custom-attributes?project=309804
POST /api/v1/task-custom-attributes

GET /api/v1/epic-custom-attributes?project=309804
POST /api/v1/epic-custom-attributes
```

### Crear Atributo Personalizado

**Request**:
```json
POST /api/v1/userstory-custom-attributes
{
  "project": 309804,
  "name": "Cliente",
  "description": "Nombre del cliente que solicitó la feature",
  "type": "text",
  "order": 1
}
```

### Establecer Valores de Atributos

Los valores se establecen al crear/actualizar la entidad:

**Request**:
```json
PATCH /api/v1/userstories/123456
{
  "version": 3,
  "custom_attributes": {
    "1": "Empresa XYZ",
    "2": "Alta"
  }
}
```

---

## Webhooks

Taiga puede notificar cambios mediante webhooks.

### Eventos Soportados

- **Milestones**: cambios en sprints
- **User Stories**: creación, modificación, eliminación
- **Tasks**: cambios en tareas
- **Issues**: cambios en incidencias
- **Wiki Pages**: cambios en páginas wiki

### Configuración

Los webhooks se configuran a nivel de proyecto mediante la interfaz web o API.

### Payload de Webhook

**Ejemplo**:
```json
{
  "action": "change",
  "type": "userstory",
  "by": {
    "id": 888691,
    "username": "usuario",
    "full_name": "Usuario Completo"
  },
  "date": "2025-01-20T14:30:00Z",
  "data": {
    "id": 123456,
    "ref": 1,
    "subject": "Login de usuarios",
    "status": 2,
    "project": {
      "id": 309804,
      "name": "Mi Proyecto",
      "slug": "mi-proyecto"
    }
  },
  "change": {
    "diff": {
      "status": {
        "from": 1,
        "to": 2
      }
    },
    "comment": "Cambiado a In Progress"
  }
}
```

---

## Ejemplos Completos

### Ejemplo 1: Flujo Completo de Autenticación y Creación de Proyecto

```python
import requests

# 1. Autenticación
auth_response = requests.post(
    "https://api.taiga.io/api/v1/auth",
    json={
        "type": "normal",
        "username": "usuario@example.com",
        "password": "password123"
    }
)
auth_data = auth_response.json()
auth_token = auth_data["auth_token"]

headers = {
    "Authorization": f"Bearer {auth_token}",
    "Content-Type": "application/json"
}

# 2. Crear proyecto
project_response = requests.post(
    "https://api.taiga.io/api/v1/projects",
    headers=headers,
    json={
        "name": "Proyecto de Ejemplo",
        "description": "Proyecto creado mediante API",
        "is_private": True
    }
)
project = project_response.json()
project_id = project["id"]

print(f"Proyecto creado: {project['name']} (ID: {project_id})")
```

### Ejemplo 2: Crear User Story con Tasks

```python
# 1. Crear User Story
us_response = requests.post(
    "https://api.taiga.io/api/v1/userstories",
    headers=headers,
    json={
        "project": project_id,
        "subject": "Implementar autenticación",
        "description": "Sistema de login y registro",
        "tags": ["auth", "security"]
    }
)
user_story = us_response.json()
us_id = user_story["id"]

print(f"User Story creada: #{user_story['ref']} - {user_story['subject']}")

# 2. Crear Tasks para la User Story
tasks = [
    "Diseñar modelo de usuario",
    "Implementar endpoints de autenticación",
    "Crear formularios de login/registro",
    "Agregar tests unitarios"
]

for task_subject in tasks:
    task_response = requests.post(
        "https://api.taiga.io/api/v1/tasks",
        headers=headers,
        json={
            "project": project_id,
            "user_story": us_id,
            "subject": task_subject
        }
    )
    task = task_response.json()
    print(f"  Task creada: #{task['ref']} - {task['subject']}")
```

### Ejemplo 3: Crear Epic con User Stories Relacionadas

```python
# 1. Crear Epic
epic_response = requests.post(
    "https://api.taiga.io/api/v1/epics",
    headers=headers,
    json={
        "project": project_id,
        "subject": "Módulo de Autenticación Completo",
        "description": "Epic que agrupa toda la funcionalidad de auth",
        "color": "#A5694F"
    }
)
epic = epic_response.json()
epic_id = epic["id"]

print(f"Epic creada: #{epic['ref']} - {epic['subject']}")

# 2. Crear User Stories
user_stories_data = [
    {"subject": "Login de usuarios", "points": {"1": 5}},
    {"subject": "Registro de usuarios", "points": {"1": 3}},
    {"subject": "Recuperación de contraseña", "points": {"1": 3}},
    {"subject": "OAuth con Google", "points": {"1": 8}}
]

for us_data in user_stories_data:
    us_response = requests.post(
        "https://api.taiga.io/api/v1/userstories",
        headers=headers,
        json={
            "project": project_id,
            **us_data
        }
    )
    us = us_response.json()

    # 3. Relacionar con Epic
    rel_response = requests.post(
        f"https://api.taiga.io/api/v1/epics/{epic_id}/related_userstories",
        headers=headers,
        json={
            "user_story": us["id"],
            "epic": epic_id
        }
    )

    print(f"  US #{us['ref']} relacionada con Epic")
```

### Ejemplo 4: Crear Sprint y Asignar User Stories

```python
# 1. Crear Sprint (Milestone)
sprint_response = requests.post(
    "https://api.taiga.io/api/v1/milestones",
    headers=headers,
    json={
        "project": project_id,
        "name": "Sprint 1",
        "estimated_start": "2025-02-01",
        "estimated_finish": "2025-02-15"
    }
)
sprint = sprint_response.json()
sprint_id = sprint["id"]

print(f"Sprint creado: {sprint['name']}")

# 2. Obtener User Stories del proyecto
us_list_response = requests.get(
    f"https://api.taiga.io/api/v1/userstories?project={project_id}",
    headers=headers
)
user_stories = us_list_response.json()

# 3. Asignar primeras 3 User Stories al Sprint
us_ids = [us["id"] for us in user_stories[:3]]

bulk_response = requests.post(
    "https://api.taiga.io/api/v1/userstories/bulk_update_milestone",
    headers=headers,
    json={
        "project_id": project_id,
        "milestone_id": sprint_id,
        "bulk_stories": us_ids
    }
)

print(f"{len(us_ids)} User Stories asignadas al Sprint")

# 4. Obtener estadísticas del Sprint
stats_response = requests.get(
    f"https://api.taiga.io/api/v1/milestones/{sprint_id}/stats",
    headers=headers
)
stats = stats_response.json()

print(f"Total points: {stats['total_points']}")
print(f"Completed points: {stats['completed_points']}")
```

### Ejemplo 5: Gestionar Issues

```python
# 1. Crear Issue
issue_response = requests.post(
    "https://api.taiga.io/api/v1/issues",
    headers=headers,
    json={
        "project": project_id,
        "subject": "Error al hacer login con email especial",
        "description": "Los emails con caracteres especiales no funcionan",
        "type": 1,  # Bug
        "priority": 3,  # High
        "severity": 2,  # Normal
        "tags": ["bug", "auth"]
    }
)
issue = issue_response.json()
issue_id = issue["id"]

print(f"Issue creado: #{issue['ref']} - {issue['subject']}")

# 2. Asignar Issue
issue_update = requests.patch(
    f"https://api.taiga.io/api/v1/issues/{issue_id}",
    headers=headers,
    json={
        "version": issue["version"],
        "assigned_to": auth_data["id"]  # Asignar al usuario actual
    }
)

print(f"Issue asignado a {auth_data['username']}")

# 3. Agregar comentario
comment_update = requests.patch(
    f"https://api.taiga.io/api/v1/issues/{issue_id}",
    headers=headers,
    json={
        "version": issue_update.json()["version"],
        "comment": "Investigando el problema. Parece relacionado con la validación de email."
    }
)

print("Comentario agregado al issue")

# 4. Cambiar estado y cerrar
final_update = requests.patch(
    f"https://api.taiga.io/api/v1/issues/{issue_id}",
    headers=headers,
    json={
        "version": comment_update.json()["version"],
        "status": 4,  # Closed (depende de la configuración del proyecto)
        "comment": "Issue resuelto. Se agregó validación mejorada."
    }
)

print("Issue cerrado")
```

---

## Resumen de Endpoints Principales

### Autenticación
- `POST /api/v1/auth` - Login
- `POST /api/v1/auth/refresh` - Refresh token

### Proyectos
- `GET/POST /api/v1/projects`
- `GET/PUT/PATCH/DELETE /api/v1/projects/{id}`
- `GET /api/v1/projects/by_slug?slug={slug}`
- `GET /api/v1/projects/{id}/stats`

### User Stories
- `GET/POST /api/v1/userstories`
- `GET/PUT/PATCH/DELETE /api/v1/userstories/{id}`
- `POST /api/v1/userstories/bulk_create`
- `POST /api/v1/userstories/bulk_update_*`
- `POST /api/v1/userstories/{id}/upvote|downvote|watch|unwatch`

### Issues
- `GET/POST /api/v1/issues`
- `GET/PUT/PATCH/DELETE /api/v1/issues/{id}`
- `POST /api/v1/issues/bulk_create`
- `POST /api/v1/issues/{id}/upvote|downvote|watch|unwatch`

### Epics
- `GET/POST /api/v1/epics`
- `GET/PUT/PATCH/DELETE /api/v1/epics/{id}`
- `GET/POST /api/v1/epics/{id}/related_userstories`
- `POST /api/v1/epics/bulk_create`

### Tasks
- `GET/POST /api/v1/tasks`
- `GET/PUT/PATCH/DELETE /api/v1/tasks/{id}`
- `POST /api/v1/tasks/bulk_create`
- `POST /api/v1/tasks/{id}/upvote|downvote|watch|unwatch`

### Milestones/Sprints
- `GET/POST /api/v1/milestones`
- `GET/PUT/PATCH/DELETE /api/v1/milestones/{id}`
- `GET /api/v1/milestones/{id}/stats`
- `POST /api/v1/milestones/{id}/watch|unwatch`

### History
- `GET /api/v1/history/{entity}/{id}`
- `POST /api/v1/history/{entity}/{id}/edit_comment`
- `POST /api/v1/history/{entity}/{id}/delete_comment`

### Usuarios
- `GET /api/v1/users/me`
- `GET /api/v1/users`

Todas las funcionalidades de la API de Taiga están documentadas con ejemplos de uso completos.
