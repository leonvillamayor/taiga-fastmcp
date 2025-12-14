# Guía Completa de Funcionalidades y Uso Eficiente del API de Taiga

## Índice

1. [Introducción](#introducción)
2. [Funcionalidades de Autenticación](#funcionalidades-de-autenticación)
3. [Funcionalidades de Proyectos](#funcionalidades-de-proyectos)
4. [Funcionalidades de User Stories](#funcionalidades-de-user-stories)
5. [Funcionalidades de Issues](#funcionalidades-de-issues)
6. [Funcionalidades de Epics](#funcionalidades-de-epics)
7. [Funcionalidades de Tasks](#funcionalidades-de-tasks)
8. [Funcionalidades de Milestones/Sprints](#funcionalidades-de-milestonessprints)
9. [Funcionalidades de Historial y Comentarios](#funcionalidades-de-historial-y-comentarios)
10. [Funcionalidades de Usuarios y Membresías](#funcionalidades-de-usuarios-y-membresías)
11. [Funcionalidades de Atributos Personalizados](#funcionalidades-de-atributos-personalizados)
12. [Funcionalidades de Webhooks](#funcionalidades-de-webhooks)
13. [Patrones de Uso Eficiente](#patrones-de-uso-eficiente)
14. [Optimización de Llamadas al API](#optimización-de-llamadas-al-api)

---

## Introducción

Este documento presenta un análisis exhaustivo de todas las funcionalidades del API REST de Taiga, describiendo cada una en detalle y proporcionando guías sobre cómo utilizarlas de la manera más eficiente, tanto de forma individual como en combinación con otras funcionalidades.

**Base URL**: `https://api.taiga.io/api/v1`

**Formato**: JSON (UTF-8)

**Autenticación**: Bearer Token en header `Authorization`

---

## Funcionalidades de Autenticación

### 1. Login Estándar (POST /api/v1/auth)

**Descripción**: Autenticación mediante usuario y contraseña para obtener tokens de acceso.

**Parámetros**:
- `type`: "normal"
- `username`: Email o nombre de usuario
- `password`: Contraseña del usuario

**Response**:
- `auth_token`: Token JWT para autenticación (Bearer)
- `refresh`: Token para renovar la sesión
- Información completa del usuario

**Uso eficiente**:
- **Cachear el token**: Almacenar el `auth_token` de manera segura (variables de entorno, almacenamiento cifrado)
- **Reutilizar**: No hacer login en cada operación, usar el token obtenido
- **Monitorear expiración**: Implementar lógica para detectar tokens expirados (códigos 401)
- **Renovación proactiva**: Usar el refresh token antes de que expire el principal

**Combinación con otras funcionalidades**:
- Realizar login una sola vez al inicio de la sesión
- Guardar el token y usarlo en todas las llamadas subsiguientes
- Combinar con `GET /users/me` para verificar permisos del usuario

```python
# Patrón eficiente
class TaigaClient:
    def __init__(self):
        self.token = None
        self.refresh_token = None

    def login(self, username, password):
        # Login solo una vez
        response = requests.post(...)
        self.token = response.json()["auth_token"]
        self.refresh_token = response.json()["refresh"]

    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}
```

---

### 2. Refresh Token (POST /api/v1/auth/refresh)

**Descripción**: Renovar el token de autenticación usando el refresh token sin requerir credenciales nuevamente.

**Parámetros**:
- `refresh`: El refresh token obtenido en el login

**Response**:
- Nuevo `auth_token`
- Nuevo `refresh` token

**Uso eficiente**:
- **Renovación automática**: Implementar lógica que detecte token expirado y renueve automáticamente
- **Sin interrupción**: El usuario no necesita volver a autenticarse
- **Manejo de errores**: Si el refresh falla, entonces sí requerir login completo

**Combinación con otras funcionalidades**:
- Usar en middleware o interceptor de requests
- Detectar código 401 → intentar refresh → reintentar operación original

```python
def make_request_with_auto_refresh(url, method, data):
    try:
        response = requests.request(method, url, headers=get_headers(), json=data)
        if response.status_code == 401:
            # Token expirado, renovar
            refresh_auth_token()
            # Reintentar
            response = requests.request(method, url, headers=get_headers(), json=data)
        return response
    except:
        # Manejar errores
        pass
```

---

### 3. Obtener Usuario Actual (GET /api/v1/users/me)

**Descripción**: Obtener información completa del usuario autenticado actualmente.

**Response**:
- Datos del usuario (id, username, email, roles, etc.)
- Proyectos totales (públicos y privados)
- Configuraciones (idioma, tema, zona horaria)

**Uso eficiente**:
- **Cachear datos del usuario**: No consultar en cada operación
- **Verificación de permisos**: Obtener roles y permisos del usuario
- **Personalización**: Usar preferencias de idioma y tema

**Combinación con otras funcionalidades**:
- Llamar después del login para obtener `user_id` necesario en otras operaciones
- Verificar roles antes de permitir operaciones administrativas
- Usar en combinación con endpoints de proyectos para filtrar por ownership

```python
# Patrón de inicialización eficiente
def initialize_session(username, password):
    # 1. Login
    auth_response = login(username, password)
    token = auth_response["auth_token"]

    # 2. Obtener info de usuario (una sola vez)
    user_info = get_user_me(token)

    # 3. Cachear ambos
    session = {
        "token": token,
        "user_id": user_info["id"],
        "username": user_info["username"],
        "roles": user_info["roles"]
    }
    return session
```

---

## Funcionalidades de Proyectos

### 4. Listar Proyectos (GET /api/v1/projects)

**Descripción**: Obtener lista de todos los proyectos accesibles por el usuario autenticado.

**Parámetros opcionales**:
- `member`: Filtrar por ID de miembro
- `is_private`: Filtrar por privacidad (true/false)
- `is_backlog_activated`: Filtrar por backlog habilitado

**Response**:
- Array de proyectos con información completa
- Incluye estadísticas básicas (total_milestones, total_story_points)

**Uso eficiente**:
- **Paginación**: Usar header `x-disable-pagination: True` solo si necesitas TODOS los proyectos
- **Filtrado**: Usar parámetros de filtro en lugar de obtener todo y filtrar localmente
- **Cachear lista**: Si no cambia frecuentemente, mantener en caché local

**Combinación con otras funcionalidades**:
- Obtener lista de proyectos → cachear IDs → usar en operaciones subsiguientes
- Combinar con `GET /projects/{id}/stats` para proyectos específicos
- Útil antes de crear user stories/issues para elegir proyecto destino

```python
# Eficiente: Filtrar en servidor
projects = get_projects(is_private=True, member=user_id)

# Ineficiente: Obtener todo y filtrar localmente
all_projects = get_projects()
my_projects = [p for p in all_projects if p["is_private"]]
```

---

### 5. Crear Proyecto (POST /api/v1/projects)

**Descripción**: Crear un nuevo proyecto en Taiga.

**Parámetros requeridos**:
- `name`: Nombre del proyecto

**Parámetros opcionales**:
- `description`: Descripción del proyecto
- `is_private`: Visibilidad (default: true)
- `is_backlog_activated`: Habilitar backlog (default: true)
- `is_kanban_activated`: Habilitar kanban (default: true)
- `is_wiki_activated`: Habilitar wiki (default: true)
- `is_issues_activated`: Habilitar issues (default: true)
- `tags`: Etiquetas del proyecto

**Response**:
- Objeto completo del proyecto creado con ID asignado

**Uso eficiente**:
- **Configurar módulos desde inicio**: Especificar qué módulos están activos para evitar actualizaciones posteriores
- **Usar valores por defecto**: Si los defaults son correctos, omitir parámetros
- **Obtener ID inmediatamente**: Usar el ID retornado para operaciones subsiguientes

**Combinación con otras funcionalidades**:
- Después de crear proyecto → crear membresías (agregar miembros)
- Después de crear proyecto → crear atributos personalizados
- Después de crear proyecto → configurar webhooks

```python
# Patrón eficiente de creación completa
def create_project_full(name, description, team_emails):
    # 1. Crear proyecto
    project = create_project(name, description, is_private=True)
    project_id = project["id"]

    # 2. Agregar miembros (bulk si es posible)
    for email in team_emails:
        create_membership(project_id, email, role=2)

    # 3. Crear atributos personalizados necesarios
    create_custom_attribute(project_id, "Cliente", "text")

    return project_id
```

---

### 6. Obtener Proyecto por ID (GET /api/v1/projects/{projectId})

**Descripción**: Obtener información detallada de un proyecto específico.

**Response**:
- Información completa del proyecto
- Miembros del proyecto
- Configuración de módulos
- Estadísticas

**Uso eficiente**:
- **Usar cuando necesites detalles completos**: Para listados simples, usar `GET /projects`
- **Cachear resultado**: Si el proyecto no cambia frecuentemente

**Combinación con otras funcionalidades**:
- Antes de crear user stories/issues → verificar que módulo está activo
- Obtener información de miembros para asignaciones

---

### 7. Obtener Proyecto por Slug (GET /api/v1/projects/by_slug?slug={slug})

**Descripción**: Obtener proyecto usando su slug (URL-friendly identifier) en lugar del ID.

**Parámetros**:
- `slug`: Identificador textual del proyecto

**Response**:
- Mismo que obtener por ID

**Uso eficiente**:
- **Útil para URLs amigables**: Cuando trabajas con interfaces web
- **Cachear mapeo slug→ID**: Si usas frecuentemente, mantener diccionario local
- **Preferir ID cuando sea posible**: Los IDs son más eficientes en búsquedas

**Combinación con otras funcionalidades**:
- Obtener por slug → extraer ID → usar ID en todas las operaciones posteriores

```python
# Patrón de mapeo eficiente
class ProjectManager:
    def __init__(self):
        self.slug_to_id = {}

    def get_project_id(self, slug):
        if slug not in self.slug_to_id:
            project = get_project_by_slug(slug)
            self.slug_to_id[slug] = project["id"]
        return self.slug_to_id[slug]
```

---

### 8. Modificar Proyecto Parcialmente (PATCH /api/v1/projects/{projectId})

**Descripción**: Actualizar campos específicos de un proyecto sin enviar todos los datos.

**Parámetros requeridos**:
- `version`: Versión actual del proyecto (concurrencia optimista)

**Parámetros opcionales**:
- Cualquier campo que se desee actualizar

**Response**:
- Proyecto actualizado con nueva versión

**Uso eficiente**:
- **Usar PATCH en lugar de PUT**: Solo enviar campos modificados
- **Manejo de versión**: Siempre incluir versión para evitar conflictos
- **Manejo de errores 409**: Implementar lógica de retry o merge en conflictos

**Combinación con otras funcionalidades**:
- Obtener proyecto → modificar → actualizar (flujo completo)

```python
# Eficiente: Solo actualizar lo necesario
def update_project_name(project_id, new_name):
    project = get_project(project_id)
    response = patch_project(project_id, {
        "version": project["version"],
        "name": new_name
    })
    return response

# Ineficiente: Obtener todo, modificar localmente, enviar todo
project = get_project(project_id)
project["name"] = new_name
project["description"] = project["description"]  # Innecesario
project["is_private"] = project["is_private"]    # Innecesario
update_project_full(project_id, project)
```

---

### 9. Eliminar Proyecto (DELETE /api/v1/projects/{projectId})

**Descripción**: Eliminar permanentemente un proyecto y todos sus recursos asociados.

**Response**:
- `204 No Content` (éxito)

**Uso eficiente**:
- **Operación destructiva**: Implementar confirmación doble
- **Cascada automática**: No es necesario eliminar user stories, issues, etc. manualmente
- **Verificar permisos**: Solo owner puede eliminar

**Combinación con otras funcionalidades**:
- Antes de eliminar → obtener datos importantes para backup
- Después de eliminar → limpiar caché local

---

### 10. Estadísticas de Proyecto (GET /api/v1/projects/{projectId}/stats)

**Descripción**: Obtener estadísticas detalladas del proyecto (puntos, historias, issues).

**Response**:
- `total_points`: Puntos totales
- `closed_points`: Puntos completados
- `total_userstories`: Total de historias
- `closed_userstories`: Historias completadas
- `total_issues`: Total de issues
- `closed_issues`: Issues cerrados

**Uso eficiente**:
- **Endpoint específico para dashboards**: Usar este endpoint en lugar de calcular manualmente
- **Actualización periódica**: Llamar solo cuando se necesite actualizar estadísticas
- **Combinar con stats de milestones**: Para vistas más granulares

**Combinación con otras funcionalidades**:
- Obtener stats de proyecto para overview general
- Obtener stats de milestone para detalle de sprint
- Comparar con `GET /milestones/{id}/stats` para análisis de progreso

---

### 11. Duplicar Proyecto (POST /api/v1/projects/{projectId}/duplicate)

**Descripción**: Crear una copia completa de un proyecto existente.

**Uso eficiente**:
- **Plantillas de proyecto**: Crear proyecto plantilla → duplicar para nuevos proyectos
- **Operación costosa**: Puede tomar tiempo, implementar feedback asíncrono
- **Personalizar después**: Duplicar primero, luego modificar lo necesario

**Combinación con otras funcionalidades**:
- Duplicar proyecto → modificar nombre y descripción → agregar miembros específicos

---

### 12. Gestión de Etiquetas (Tags)

**Funcionalidades**:
- `POST /api/v1/projects/{projectId}/create_tag`: Crear etiqueta
- `POST /api/v1/projects/{projectId}/edit_tag`: Editar etiqueta
- `POST /api/v1/projects/{projectId}/delete_tag`: Eliminar etiqueta
- `POST /api/v1/projects/{projectId}/mix_tags`: Combinar etiquetas

**Uso eficiente**:
- **Centralizar gestión de tags**: Definir taxonomía antes de usar en user stories/issues
- **Mix tags para consolidación**: Útil para limpiar tags duplicados o similares
- **Consistencia**: Usar siempre las mismas tags para facilitar filtrado

**Combinación con otras funcionalidades**:
- Definir tags → usar en user stories, issues, tasks
- Usar tags para filtrado eficiente de elementos

---

### 13. Watch/Unwatch y Like/Unlike Proyecto

**Funcionalidades**:
- `POST /api/v1/projects/{projectId}/watch`: Seguir proyecto (notificaciones)
- `POST /api/v1/projects/{projectId}/unwatch`: Dejar de seguir
- `POST /api/v1/projects/{projectId}/like`: Dar like
- `POST /api/v1/projects/{projectId}/unlike`: Quitar like

**Uso eficiente**:
- **Watch para notificaciones**: Configurar en proyectos activos para estar al tanto
- **Like para organización personal**: Marcar proyectos favoritos
- **Batch operations**: Si múltiples usuarios, usar operaciones en lote

**Combinación con otras funcionalidades**:
- Combinar con filtrado de proyectos por favoritos en interfaces

---

## Funcionalidades de User Stories

### 14. Listar User Stories (GET /api/v1/userstories)

**Descripción**: Obtener lista de user stories con filtros opcionales.

**Filtros disponibles**:
- `project`: ID del proyecto (requerido en la práctica)
- `milestone`: Filtrar por sprint
- `status`: Filtrar por estado
- `assigned_to`: Filtrar por usuario asignado
- `tags`: Filtrar por etiquetas
- `is_closed`: Solo cerradas/abiertas

**Response**:
- Array de user stories con información completa
- Incluye información extra de status, assigned user, etc.

**Uso eficiente**:
- **SIEMPRE filtrar por proyecto**: Evitar obtener todas las user stories de la instancia
- **Usar múltiples filtros**: Combinar project + milestone + status para precisión
- **Paginación**: Para proyectos grandes, manejar paginación correctamente
- **Deshabilitar paginación con precaución**: Solo si realmente necesitas todas

**Combinación con otras funcionalidades**:
- Listar user stories de un sprint → mostrar en vista de sprint planning
- Filtrar por assigned_to → dashboard personalizado por usuario
- Combinar con `GET /userstories/filters_data` para obtener opciones de filtro válidas

```python
# Eficiente: Filtros específicos
def get_sprint_stories(project_id, milestone_id):
    return get_userstories(
        project=project_id,
        milestone=milestone_id,
        is_closed=False
    )

# Ineficiente: Obtener todo y filtrar localmente
all_stories = get_userstories(project=project_id)
sprint_stories = [s for s in all_stories if s["milestone"] == milestone_id and not s["is_closed"]]
```

---

### 15. Crear User Story (POST /api/v1/userstories)

**Descripción**: Crear una nueva user story en el proyecto.

**Parámetros requeridos**:
- `project`: ID del proyecto
- `subject`: Título de la user story

**Parámetros opcionales**:
- `description`: Descripción detallada
- `status`: ID del estado inicial
- `milestone`: ID del sprint
- `assigned_to`: ID del usuario asignado
- `tags`: Array de etiquetas
- `points`: Objeto con estimación por rol {role_id: points}
- `is_blocked`: Marcar como bloqueada
- `blocked_note`: Nota de bloqueo

**Response**:
- User story creada con ID asignado
- Incluye `ref` (número de referencia en el proyecto)

**Uso eficiente**:
- **Batch creation**: Usar `POST /userstories/bulk_create` para múltiples stories
- **Establecer milestone desde inicio**: Evitar actualización posterior
- **Puntos por rol**: Si no se usan roles, simplificar
- **Obtener ref**: Usar el `ref` retornado para referencias cruzadas

**Combinación con otras funcionalidades**:
- Crear user story → crear tasks asociadas → relacionar con epic
- Crear user story → agregar watchers → establecer custom attributes

```python
# Patrón eficiente de creación completa
def create_user_story_full(project_id, subject, description, tasks_subjects):
    # 1. Crear user story
    us = create_userstory(project_id, subject, description)
    us_id = us["id"]

    # 2. Crear tasks asociadas (bulk si es posible)
    bulk_create_tasks(project_id, us_id, [{"subject": t} for t in tasks_subjects])

    # 3. Watch automáticamente (si es el creador)
    watch_userstory(us_id)

    return us
```

---

### 16. Crear User Stories en Lote (POST /api/v1/userstories/bulk_create)

**Descripción**: Crear múltiples user stories en una sola llamada al API.

**Parámetros**:
- `project_id`: ID del proyecto
- `bulk_stories`: Array de objetos con datos de user stories
- `milestone`: (opcional) Sprint para todas las stories
- `status`: (opcional) Estado para todas las stories

**Response**:
- Array de user stories creadas

**Uso eficiente**:
- **Preferir sobre creación individual**: Mucho más eficiente en red y procesamiento
- **Límite de tamaño**: No exceder ~100 stories por batch (puede variar)
- **Transacción parcial**: Si una falla, las demás pueden crearse (verificar response)
- **Combinar parámetros comunes**: Usar `milestone` y `status` para aplicar a todas

**Combinación con otras funcionalidades**:
- Importar desde CSV → bulk create
- Crear epic → bulk create user stories → bulk relate con epic

```python
# Muy eficiente para múltiples stories
def import_stories_from_list(project_id, stories_data):
    bulk_create_userstories(project_id, stories_data)

# Ineficiente: Loop de creaciones individuales
for story_data in stories_data:
    create_userstory(project_id, **story_data)  # N llamadas al API
```

---

### 17. Obtener User Story (GET /api/v1/userstories/{usId})

**Descripción**: Obtener información completa de una user story específica.

**Response**:
- Información completa de la user story
- Incluye `*_extra_info` con datos expandidos de referencias

**Uso eficiente**:
- **Usar cuando necesites todos los detalles**: Para listados, el GET list ya tiene suficiente info
- **Cachear result**: Si se accede múltiples veces sin cambios
- **Version tracking**: Guardar el campo `version` para actualizaciones posteriores

**Combinación con otras funcionalidades**:
- Obtener story → obtener tasks asociadas → obtener history
- Obtener story → verificar watchers → verificar voters

---

### 18. Obtener User Story por Referencia (GET /api/v1/userstories/by_ref?ref={ref}&project={projectId})

**Descripción**: Obtener user story usando su número de referencia (más amigable para humanos).

**Parámetros**:
- `ref`: Número de referencia (ej: 1, 2, 3...)
- `project`: ID del proyecto

**Response**:
- Misma información que obtener por ID

**Uso eficiente**:
- **URLs amigables**: Usar en interfaces donde el usuario ve "#42" en lugar de ID largo
- **Mapeo ref→ID**: Cachear para operaciones subsiguientes
- **Requerido para comandos de chat**: "Actualiza la US #42"

**Combinación con otras funcionalidades**:
- Usuario menciona "#42" → obtener por ref → realizar operación

---

### 19. Actualizar User Story (PATCH /api/v1/userstories/{usId})

**Descripción**: Actualizar campos específicos de una user story.

**Parámetros requeridos**:
- `version`: Versión actual (concurrencia optimista)

**Parámetros opcionales**:
- Cualquier campo a actualizar
- `comment`: Agregar comentario al cambio (aparece en history)

**Response**:
- User story actualizada con nueva versión

**Uso eficiente**:
- **PATCH vs PUT**: Siempre usar PATCH para actualizaciones parciales
- **Agregar comentarios**: Usar `comment` para documentar cambios importantes
- **Manejo de versión**: Implementar retry con nueva versión en conflictos 409
- **Batch updates**: Para cambios masivos, usar `bulk_update_*` endpoints

**Combinación con otras funcionalidades**:
- Actualizar status → agregar comentario → notificar watchers (automático)
- Actualizar assigned_to → el nuevo usuario recibe notificación

```python
# Eficiente: Actualización con contexto
def move_to_in_progress(us_id, comment):
    us = get_userstory(us_id)
    return patch_userstory(us_id, {
        "version": us["version"],
        "status": STATUS_IN_PROGRESS,
        "comment": comment  # Documentar el cambio
    })

# Manejar conflictos de concurrencia
try:
    updated = patch_userstory(us_id, data)
except Conflict409:
    # Re-obtener versión actual y reintentar
    us = get_userstory(us_id)
    data["version"] = us["version"]
    updated = patch_userstory(us_id, data)
```

---

### 20. Eliminar User Story (DELETE /api/v1/userstories/{usId})

**Descripción**: Eliminar permanentemente una user story.

**Response**:
- `204 No Content`

**Uso eficiente**:
- **Cascada automática**: Tasks asociadas se eliminan automáticamente
- **Relaciones con epics**: Se eliminan las relaciones
- **Backup antes de eliminar**: Si es crítico, obtener datos completos primero
- **Considerar cerrar en lugar de eliminar**: Para mantener historial

**Combinación con otras funcionalidades**:
- Verificar relaciones antes de eliminar (epic relations, dependencies)

---

### 21. Reordenar User Stories en Backlog (POST /api/v1/userstories/bulk_update_backlog_order)

**Descripción**: Cambiar el orden de user stories en el backlog del proyecto.

**Parámetros**:
- `project_id`: ID del proyecto
- `bulk_stories`: Array de [us_id, order] pairs

**Uso eficiente**:
- **Operación batch**: Enviar todos los cambios de orden en una sola llamada
- **Orden relativo**: El order es relativo dentro del backlog
- **UI drag-and-drop**: Ideal para implementar reordenamiento visual

**Combinación con otras funcionalidades**:
- Usar después de filtrar/buscar stories para reorganizar prioridades

```python
# Eficiente: Reordenar múltiples en una llamada
new_order = [(story_ids[0], 0), (story_ids[1], 1), (story_ids[2], 2)]
bulk_update_backlog_order(project_id, new_order)

# Ineficiente: Actualizar una por una
for index, story_id in enumerate(story_ids):
    patch_userstory(story_id, {"backlog_order": index})
```

---

### 22. Reordenar User Stories en Kanban (POST /api/v1/userstories/bulk_update_kanban_order)

**Descripción**: Cambiar el orden de user stories dentro de una columna del tablero Kanban.

**Parámetros**:
- `project_id`: ID del proyecto
- `status_id`: ID del estado (columna)
- `bulk_stories`: Array de [us_id, order] pairs

**Uso eficiente**:
- **Por columna**: Solo afecta stories en el status especificado
- **Drag-and-drop visual**: Implementar movimiento entre columnas y reordenamiento
- **Combinar con cambio de status**: Mover story a nueva columna + reordenar

**Combinación con otras funcionalidades**:
- Cambiar status de story → reordenar en nueva columna

---

### 23. Reordenar User Stories en Sprint (POST /api/v1/userstories/bulk_update_sprint_order)

**Descripción**: Cambiar el orden de user stories dentro de un sprint.

**Parámetros**:
- `project_id`: ID del proyecto
- `milestone_id`: ID del sprint
- `bulk_stories`: Array de [us_id, order] pairs

**Uso eficiente**:
- **Sprint planning**: Reordenar stories por prioridad dentro del sprint
- **Vista de sprint**: Mantener orden consistente con prioridad de trabajo

**Combinación con otras funcionalidades**:
- Mover stories a sprint → reordenar por prioridad
- Combinar con `bulk_update_milestone` para mover múltiples stories a un sprint

---

### 24. Actualizar Milestone en Lote (POST /api/v1/userstories/bulk_update_milestone)

**Descripción**: Mover múltiples user stories a un sprint diferente.

**Parámetros**:
- `project_id`: ID del proyecto
- `milestone_id`: ID del sprint destino (o null para mover a backlog)
- `bulk_stories`: Array de IDs de user stories

**Uso eficiente**:
- **Sprint planning masivo**: Mover múltiples stories al sprint en una operación
- **Mover a backlog**: Usar `milestone_id: null` para remover de sprint
- **Mucho más eficiente**: Que actualizar stories una por una

**Combinación con otras funcionalidades**:
- Seleccionar stories del backlog → mover al sprint → reordenar en sprint
- Mover stories no completadas de sprint cerrado → mover a siguiente sprint

```python
# Eficiente: Sprint planning con batch operations
def plan_sprint(project_id, sprint_id, story_ids):
    # 1. Mover todas las stories al sprint
    bulk_update_milestone(project_id, sprint_id, story_ids)

    # 2. Reordenar por prioridad
    order_pairs = [(sid, idx) for idx, sid in enumerate(story_ids)]
    bulk_update_sprint_order(project_id, sprint_id, order_pairs)
```

---

### 25. Filtros de User Stories (GET /api/v1/userstories/filters_data?project={projectId})

**Descripción**: Obtener datos disponibles para filtrado (statuses, users, tags, etc.).

**Response**:
- `statuses`: Array de estados disponibles
- `assigned_to`: Lista de usuarios asignables
- `owners`: Lista de owners
- `tags`: Tags usados en user stories
- `epics`: Epics del proyecto

**Uso eficiente**:
- **Cachear para UI**: Llamar una vez al cargar vista de user stories
- **Actualizar periódicamente**: Cuando se agregan miembros, tags, etc.
- **Usar para validación**: Verificar que valores de filtro son válidos

**Combinación con otras funcionalidades**:
- Obtener filters_data → construir UI de filtros → listar con filtros aplicados

---

### 26. Votación en User Stories

**Funcionalidades**:
- `POST /api/v1/userstories/{usId}/upvote`: Votar por una story
- `POST /api/v1/userstories/{usId}/downvote`: Remover voto
- `GET /api/v1/userstories/{usId}/voters`: Obtener lista de votantes

**Uso eficiente**:
- **Priorización comunitaria**: Permitir al equipo votar por stories importantes
- **Indicador de interés**: Ver qué stories tienen más votos
- **Lightweight**: Operación rápida, no afecta datos críticos

**Combinación con otras funcionalidades**:
- Ordenar backlog por número de votos
- Filtrar/destacar stories con muchos votos

---

### 27. Watchers de User Stories

**Funcionalidades**:
- `POST /api/v1/userstories/{usId}/watch`: Seguir una story (recibir notificaciones)
- `POST /api/v1/userstories/{usId}/unwatch`: Dejar de seguir
- `GET /api/v1/userstories/{usId}/watchers`: Obtener lista de watchers

**Uso eficiente**:
- **Auto-watch al crear**: El creador automáticamente se vuelve watcher
- **Notificaciones selectivas**: Seguir solo stories relevantes
- **Team awareness**: Ver quién está siguiendo cada story

**Combinación con otras funcionalidades**:
- Asignar story a usuario → auto-watch (opcional)
- Cambiar status → notificar watchers (automático)

---

### 28. Adjuntos de User Stories

**Funcionalidades**:
- `GET /api/v1/userstories/attachments`: Listar adjuntos
- `POST /api/v1/userstories/attachments`: Crear adjunto
- `GET /api/v1/userstories/attachments/{attachmentId}`: Obtener adjunto
- `PATCH /api/v1/userstories/attachments/{attachmentId}`: Actualizar adjunto
- `DELETE /api/v1/userstories/attachments/{attachmentId}`: Eliminar adjunto

**Uso eficiente**:
- **multipart/form-data**: Usar formato correcto para upload
- `Listar por project+object_id`: Filtrar adjuntos de una story específica
- **Deprecar en lugar de eliminar**: Usar `is_deprecated` para soft delete
- **Límite de tamaño**: Verificar límites de la instancia Taiga

**Combinación con otras funcionalidades**:
- Crear story → adjuntar documentos de requisitos
- Adjuntar mockups/wireframes → referenciar en descripción

```python
# Crear adjunto eficientemente
def attach_file_to_story(us_id, file_path, description):
    with open(file_path, 'rb') as f:
        files = {'attached_file': f}
        data = {
            'project': project_id,
            'object_id': us_id,
            'description': description
        }
        response = requests.post(
            f"{base_url}/userstories/attachments",
            headers=headers,
            data=data,
            files=files
        )
    return response.json()
```

---

## Funcionalidades de Issues

### 29. Listar Issues (GET /api/v1/issues)

**Descripción**: Obtener lista de issues con filtros opcionales.

**Filtros disponibles**:
- `project`: ID del proyecto (requerido prácticamente)
- `status`: Filtrar por estado
- `severity`: Filtrar por severidad
- `priority`: Filtrar por prioridad
- `type`: Filtrar por tipo (bug, enhancement, etc.)
- `assigned_to`: Filtrar por asignado
- `tags`: Filtrar por etiquetas
- `is_closed`: Solo cerrados/abiertos

**Response**:
- Array de issues con información completa
- Incluye información extra de status, type, severity, priority

**Uso eficiente**:
- **Filtrar por proyecto siempre**: Esencial para performance
- **Combinar filtros**: type + severity + priority para bugs críticos
- **Paginación**: Manejar correctamente en proyectos grandes
- **Filtros en servidor**: Más eficiente que filtrar localmente

**Combinación con otras funcionalidades**:
- Filtrar bugs por severity → priorizar resolución
- Listar issues de milestone → tracking de bugs en sprint
- Combinar con `GET /issues/filters_data` para opciones válidas

```python
# Eficiente: Obtener bugs críticos sin resolver
critical_bugs = get_issues(
    project=project_id,
    type=TYPE_BUG,
    severity=SEVERITY_CRITICAL,
    is_closed=False
)
```

---

### 30. Crear Issue (POST /api/v1/issues)

**Descripción**: Crear un nuevo issue (bug, enhancement, question, etc.).

**Parámetros requeridos**:
- `project`: ID del proyecto
- `subject`: Título del issue

**Parámetros opcionales**:
- `description`: Descripción detallada
- `type`: Tipo de issue (bug, enhancement, etc.)
- `status`: Estado inicial
- `priority`: Prioridad (low, normal, high)
- `severity`: Severidad (wishlist, minor, normal, important, critical)
- `assigned_to`: Usuario asignado
- `milestone`: Sprint asociado
- `tags`: Etiquetas
- `is_blocked`: Marcar como bloqueado
- `blocked_note`: Nota de bloqueo

**Response**:
- Issue creado con ID y ref asignados

**Uso eficiente**:
- **Establecer type correctamente**: Bug vs enhancement vs question
- **Prioridad y severidad**: Definir desde inicio para triage correcto
- **Batch creation**: Usar `POST /issues/bulk_create` para múltiples
- **Auto-asignación**: Asignar al reportar si hay ownership claro

**Combinación con otras funcionalidades**:
- Crear issue → adjuntar screenshot/logs → asignar a developer
- Relacionar issue con user story (via tags o custom attributes)

```python
# Patrón eficiente de reporte de bug
def report_bug(project_id, subject, description, severity, logs_file):
    # 1. Crear issue
    issue = create_issue(
        project=project_id,
        subject=subject,
        description=description,
        type=TYPE_BUG,
        severity=severity,
        priority=PRIORITY_HIGH if severity == SEVERITY_CRITICAL else PRIORITY_NORMAL
    )

    # 2. Adjuntar logs
    if logs_file:
        attach_file_to_issue(issue["id"], logs_file, "Logs del error")

    # 3. Watch para seguimiento
    watch_issue(issue["id"])

    return issue
```

---

### 31. Crear Issues en Lote (POST /api/v1/issues/bulk_create)

**Descripción**: Crear múltiples issues en una sola llamada al API.

**Parámetros**:
- `project_id`: ID del proyecto
- `bulk_issues`: Array de objetos con datos de issues

**Response**:
- Array de issues creados

**Uso eficiente**:
- **Importación masiva**: Desde otros sistemas o CSV
- **Mucho más eficiente**: Que crear uno por uno
- **Establecer valores comunes**: Si todos son bugs, especificar en cada objeto

**Combinación con otras funcionalidades**:
- Importar issues desde Jira/GitHub → bulk create
- Detectar múltiples bugs en testing → bulk create

---

### 32. Obtener Issue (GET /api/v1/issues/{issueId})

**Descripción**: Obtener información completa de un issue específico.

**Response**:
- Información completa del issue
- Incluye `*_extra_info` con datos expandidos

**Uso eficiente**:
- **Usar cuando necesites todos los detalles**: Para listados, GET list es suficiente
- **Cachear result**: Si no cambia frecuentemente
- **Guardar version**: Para actualizaciones posteriores

---

### 33. Obtener Issue por Referencia (GET /api/v1/issues/by_ref?ref={ref}&project={projectId})

**Descripción**: Obtener issue usando su número de referencia.

**Parámetros**:
- `ref`: Número de referencia
- `project`: ID del proyecto

**Uso eficiente**:
- **URLs amigables**: Para interfaces web
- **Mapeo ref→ID**: Cachear para operaciones subsiguientes

---

### 34. Actualizar Issue (PATCH /api/v1/issues/{issueId})

**Descripción**: Actualizar campos específicos de un issue.

**Parámetros requeridos**:
- `version`: Versión actual

**Parámetros opcionales**:
- Cualquier campo a actualizar
- `comment`: Agregar comentario al cambio

**Uso eficiente**:
- **PATCH vs PUT**: Siempre usar PATCH para parcial
- **Agregar comentarios**: Documentar resoluciones, workarounds
- **Manejo de versión**: Implementar retry en conflictos
- **Cerrar con comentario**: Al resolver, agregar explicación

**Combinación con otras funcionalidades**:
- Resolver bug → cambiar status a closed → agregar comentario de resolución
- Cambiar severity → notificar watchers (automático)

```python
# Patrón de resolución de issue
def resolve_issue(issue_id, resolution_comment):
    issue = get_issue(issue_id)
    return patch_issue(issue_id, {
        "version": issue["version"],
        "status": STATUS_CLOSED,
        "comment": f"Resuelto: {resolution_comment}"
    })
```

---

### 35. Eliminar Issue (DELETE /api/v1/issues/{issueId})

**Descripción**: Eliminar permanentemente un issue.

**Uso eficiente**:
- **Considerar cerrar en lugar de eliminar**: Para mantener historial
- **Backup antes de eliminar**: Si contiene información valiosa

---

### 36. Filtros de Issues (GET /api/v1/issues/filters_data?project={projectId})

**Descripción**: Obtener datos disponibles para filtrado de issues.

**Response**:
- `statuses`: Estados disponibles
- `types`: Tipos de issues
- `severities`: Severidades disponibles
- `priorities`: Prioridades disponibles
- `assigned_to`: Usuarios asignables
- `tags`: Tags usados

**Uso eficiente**:
- **Cachear para UI**: Una llamada al cargar vista de issues
- **Usar para validación**: Verificar valores válidos antes de crear/actualizar
- **Construir filtros dinámicos**: Basado en datos reales del proyecto

**Combinación con otras funcionalidades**:
- Obtener filters_data → construir UI → listar con filtros

---

### 37. Votación, Watchers y Adjuntos de Issues

**Funcionalidades** (similares a user stories):
- Votación: `upvote`, `downvote`, `voters`
- Watchers: `watch`, `unwatch`, `watchers`
- Adjuntos: `list`, `create`, `get`, `update`, `delete`

**Uso eficiente**: (mismo que user stories)
- Votación para priorizar bugs
- Watch para seguimiento de issues críticos
- Adjuntos para screenshots, logs, dumps

---

## Funcionalidades de Epics

### 38. Listar Epics (GET /api/v1/epics)

**Descripción**: Obtener lista de epics del proyecto.

**Filtros disponibles**:
- `project`: ID del proyecto
- `status`: Estado del epic
- `assigned_to`: Asignado a usuario

**Response**:
- Array de epics con información completa

**Uso eficiente**:
- **Filtrar por proyecto**: Esencial
- **Menos elementos que stories**: Generalmente paginación no es problema
- **Vista de roadmap**: Listar todos los epics para planificación de alto nivel

**Combinación con otras funcionalidades**:
- Listar epics → para cada epic obtener related_userstories → mostrar progreso

```python
# Vista de roadmap eficiente
def get_roadmap_data(project_id):
    epics = get_epics(project=project_id)
    roadmap = []

    for epic in epics:
        # Obtener stories relacionadas
        related = get_epic_related_userstories(epic["id"])
        total = len(related)
        completed = sum(1 for r in related if r["user_story"]["is_closed"])

        roadmap.append({
            "epic": epic,
            "progress": completed / total if total > 0 else 0,
            "total_stories": total
        })

    return roadmap
```

---

### 39. Crear Epic (POST /api/v1/epics)

**Descripción**: Crear un nuevo epic para agrupar user stories relacionadas.

**Parámetros requeridos**:
- `project`: ID del proyecto
- `subject`: Título del epic

**Parámetros opcionales**:
- `description`: Descripción del epic
- `color`: Color para identificación visual
- `status`: Estado inicial
- `assigned_to`: Usuario responsable del epic
- `tags`: Etiquetas
- `client_requirement`: Si es requerimiento de cliente
- `team_requirement`: Si es requerimiento del equipo

**Response**:
- Epic creado con ID asignado

**Uso eficiente**:
- **Definir color único**: Para identificación visual rápida
- **Descripción clara**: Objetivo y alcance del epic
- **Usar client/team requirement**: Para tracking de origen

**Combinación con otras funcionalidades**:
- Crear epic → crear user stories → relacionar con epic (bulk)
- Crear epic → asignar a product owner → definir roadmap

---

### 40. Crear Epics en Lote (POST /api/v1/epics/bulk_create)

**Descripción**: Crear múltiples epics en una sola llamada.

**Parámetros**:
- `project_id`: ID del proyecto
- `bulk_epics`: Array de objetos con datos de epics

**Uso eficiente**:
- **Planificación de roadmap**: Crear múltiples epics para trimestre/año
- **Más eficiente**: Que crear uno por uno

```python
# Definir roadmap completo de una vez
def setup_roadmap(project_id, roadmap_items):
    bulk_epics = [
        {
            "subject": item["title"],
            "description": item["description"],
            "color": item["color"]
        }
        for item in roadmap_items
    ]
    return bulk_create_epics(project_id, bulk_epics)
```

---

### 41. Actualizar Epic (PATCH /api/v1/epics/{epicId})

**Descripción**: Actualizar campos específicos de un epic.

**Parámetros requeridos**:
- `version`: Versión actual

**Uso eficiente**: (similar a user stories/issues)
- PATCH para actualizaciones parciales
- Agregar comentarios en cambios importantes
- Manejo de versión para concurrencia

---

### 42. Eliminar Epic (DELETE /api/v1/epics/{epicId})

**Descripción**: Eliminar un epic.

**Uso eficiente**:
- **Relaciones se eliminan**: Las relaciones con user stories se borran
- **User stories permanecen**: Las stories no se eliminan, solo se desvinculan
- **Considerar archivar**: En lugar de eliminar, cambiar status a "archived"

---

### 43. User Stories Relacionadas con Epic

**Funcionalidades**:
- `GET /api/v1/epics/{epicId}/related_userstories`: Listar stories del epic
- `POST /api/v1/epics/{epicId}/related_userstories`: Relacionar una story
- `GET /api/v1/epics/{epicId}/related_userstories/{usId}`: Obtener relación
- `PATCH /api/v1/epics/{epicId}/related_userstories/{usId}`: Actualizar relación
- `DELETE /api/v1/epics/{epicId}/related_userstories/{usId}`: Eliminar relación

**Parámetros para crear relación**:
- `user_story`: ID de la user story
- `epic`: ID del epic
- `order`: Orden dentro del epic (opcional)

**Uso eficiente**:
- **Batch relate**: Usar `bulk_create` para relacionar múltiples stories
- **Order para prioridad**: Definir orden de implementación dentro del epic
- **Verificar existencia**: No intentar relacionar story ya relacionada

**Combinación con otras funcionalidades**:
- Crear epic → crear stories → bulk relate
- Filtrar stories por epic → mostrar progreso del epic
- Reordenar stories dentro del epic según prioridad

```python
# Patrón eficiente: Epic completo
def create_epic_with_stories(project_id, epic_data, stories_data):
    # 1. Crear epic
    epic = create_epic(project_id, **epic_data)
    epic_id = epic["id"]

    # 2. Crear stories
    stories = bulk_create_userstories(project_id, stories_data)
    story_ids = [s["id"] for s in stories]

    # 3. Relacionar todas con epic (bulk)
    bulk_create_epic_related_userstories(epic_id, story_ids)

    return epic
```

---

### 44. Relacionar User Stories en Lote (POST /api/v1/epics/{epicId}/related_userstories/bulk_create)

**Descripción**: Relacionar múltiples user stories con un epic en una sola operación.

**Parámetros**:
- `bulk_userstories`: Array de IDs de user stories

**Uso eficiente**:
- **Mucho más eficiente**: Que relacionar una por una
- **Planning de epic**: Seleccionar múltiples stories existentes y asociarlas

**Combinación con otras funcionalidades**:
- Filtrar stories por tag → bulk relate con epic
- Mover stories de un epic a otro (bulk delete + bulk create)

---

### 45. Filtros, Votación, Watchers y Adjuntos de Epics

**Funcionalidades** (similares a user stories e issues):
- Filtros: `GET /epics/filters_data`
- Votación: `upvote`, `downvote`, `voters`
- Watchers: `watch`, `unwatch`, `watchers`
- Adjuntos: Mismas operaciones CRUD

**Uso eficiente**: (mismo patrón que stories/issues)

---

## Funcionalidades de Tasks

### 46. Listar Tasks (GET /api/v1/tasks)

**Descripción**: Obtener lista de tasks con filtros.

**Filtros disponibles**:
- `project`: ID del proyecto
- `user_story`: ID de la user story (muy útil)
- `milestone`: ID del sprint
- `status`: Estado
- `assigned_to`: Usuario asignado
- `tags`: Etiquetas
- `is_closed`: Cerradas/abiertas

**Response**:
- Array de tasks con información completa

**Uso eficiente**:
- **Filtrar por user_story**: Para obtener tasks de una story específica
- **Filtrar por project + milestone**: Tasks de un sprint
- **Filtrar por assigned_to**: Dashboard personal de tasks
- **Combinar filtros**: project + milestone + assigned_to para vista de sprint personal

**Combinación con otras funcionalidades**:
- Obtener user story → listar tasks → mostrar desglose de trabajo
- Listar tasks del sprint por usuario → asignación de trabajo

```python
# Dashboard personal eficiente
def get_my_sprint_tasks(project_id, milestone_id, user_id):
    return get_tasks(
        project=project_id,
        milestone=milestone_id,
        assigned_to=user_id,
        is_closed=False
    )
```

---

### 47. Crear Task (POST /api/v1/tasks)

**Descripción**: Crear una nueva task.

**Parámetros requeridos**:
- `project`: ID del proyecto
- `subject`: Título de la task

**Parámetros opcionales**:
- `user_story`: ID de la user story padre (muy recomendado)
- `description`: Descripción detallada
- `status`: Estado inicial
- `milestone`: Sprint asociado
- `assigned_to`: Usuario asignado
- `tags`: Etiquetas
- `is_iocaine`: Marcar como "iocaine dose" (tarea que consume mucho tiempo inesperadamente)
- `is_blocked`: Marcar como bloqueada
- `blocked_note`: Nota de bloqueo

**Response**:
- Task creada con ID asignado

**Uso eficiente**:
- **Asociar con user story**: Casi siempre deberías especificar `user_story`
- **Milestone hereda de story**: Si la story está en un sprint, la task debería estarlo
- **Batch creation**: Usar `POST /tasks/bulk_create` para múltiples tasks
- **Granularidad adecuada**: Tasks de 2-4 horas idealmente

**Combinación con otras funcionalidades**:
- Crear user story → bulk create tasks de implementación
- Planning: Descomponer story en tasks → asignar tasks a desarrolladores

---

### 48. Crear Tasks en Lote (POST /api/v1/tasks/bulk_create)

**Descripción**: Crear múltiples tasks en una sola llamada.

**Parámetros**:
- `project_id`: ID del proyecto
- `user_story_id`: ID de la user story (opcional pero recomendado)
- `bulk_tasks`: Array de objetos con datos de tasks

**Response**:
- Array de tasks creadas

**Uso eficiente**:
- **Desglose de user story**: Crear todas las tasks de una story de una vez
- **Template de tasks**: Para stories similares, usar misma estructura
- **Más eficiente**: Que crear una por una

**Combinación con otras funcionalidades**:
- Crear user story → inmediatamente bulk create tasks → listo para asignación

```python
# Patrón eficiente: Story con tasks
def create_story_with_tasks(project_id, story_subject, task_subjects):
    # 1. Crear user story
    story = create_userstory(project_id, story_subject)
    story_id = story["id"]

    # 2. Crear todas las tasks de una vez
    tasks_data = [{"subject": t} for t in task_subjects]
    tasks = bulk_create_tasks(project_id, story_id, tasks_data)

    return story, tasks
```

---

### 49. Obtener Task (GET /api/v1/tasks/{taskId})

**Descripción**: Obtener información completa de una task.

**Uso eficiente**: (similar a user stories)
- Cachear cuando sea apropiado
- Guardar version para actualizaciones

---

### 50. Obtener Task por Referencia (GET /api/v1/tasks/by_ref?ref={ref}&project={projectId})

**Descripción**: Obtener task usando su número de referencia.

**Uso eficiente**: (similar a user stories)
- URLs amigables
- Mapeo ref→ID

---

### 51. Actualizar Task (PATCH /api/v1/tasks/{taskId})

**Descripción**: Actualizar campos específicos de una task.

**Parámetros requeridos**:
- `version`: Versión actual

**Parámetros opcionales**:
- Cualquier campo a actualizar
- `comment`: Agregar comentario

**Uso eficiente**:
- **Status tracking**: Actualizar status conforme se avanza (new → in progress → done)
- **Comentarios en bloqueos**: Si se bloquea, agregar `is_blocked=true` + `blocked_note`
- **Iocaine doses**: Marcar `is_iocaine=true` si la task tomó mucho más tiempo de lo esperado
- **Reasignación**: Cambiar `assigned_to` cuando sea necesario

**Combinación con otras funcionalidades**:
- Completar task → verificar si todas las tasks de la story están completas → cerrar story
- Bloquear task → notificar a watchers → escalar si es necesario

```python
# Patrón de trabajo en task
def start_task(task_id):
    task = get_task(task_id)
    return patch_task(task_id, {
        "version": task["version"],
        "status": STATUS_IN_PROGRESS,
        "comment": "Comenzando trabajo en esta task"
    })

def complete_task(task_id, work_notes):
    task = get_task(task_id)
    return patch_task(task_id, {
        "version": task["version"],
        "status": STATUS_DONE,
        "comment": f"Completado: {work_notes}"
    })
```

---

### 52. Eliminar Task (DELETE /api/v1/tasks/{taskId})

**Descripción**: Eliminar una task.

**Uso eficiente**:
- **Menos restrictivo**: Las tasks son más fáciles de eliminar que stories
- **Considerar completar**: En lugar de eliminar, marcar como completada o cancelada

---

### 53. Filtros de Tasks (GET /api/v1/tasks/filters_data?project={projectId})

**Descripción**: Obtener datos disponibles para filtrado de tasks.

**Uso eficiente**: (similar a stories/issues)
- Cachear para UI
- Usar para validación
- Construir filtros dinámicos

---

### 54. Votación, Watchers y Adjuntos de Tasks

**Funcionalidades** (mismas que stories/issues):
- Votación: `upvote`, `downvote`, `voters`
- Watchers: `watch`, `unwatch`, `watchers`
- Adjuntos: CRUD completo

**Uso eficiente**:
- **Watch para colaboración**: Múltiples developers en misma task
- **Adjuntos para evidencia**: Screenshots de trabajo completado
- **Votación menos común**: En tasks se usa menos que en stories

---

## Funcionalidades de Milestones/Sprints

### 55. Listar Milestones (GET /api/v1/milestones)

**Descripción**: Obtener lista de milestones/sprints del proyecto.

**Filtros disponibles**:
- `project`: ID del proyecto
- `closed`: Filtrar por abiertos/cerrados

**Response**:
- Array de milestones con información completa
- Incluye user stories asociadas
- Puntos totales y completados

**Uso eficiente**:
- **Filtrar por proyecto**: Esencial
- **closed=false**: Para obtener solo sprints activos/futuros
- **Incluye user_stories**: Ya viene con la info, no necesitas llamada adicional
- **Cachear para selección**: Al planificar, cachear lista de sprints disponibles

**Combinación con otras funcionalidades**:
- Listar milestones → para cada uno obtener stats → dashboard de progreso
- Filtrar milestones cerrados → análisis retrospectivo

```python
# Vista de sprints eficiente
def get_sprint_overview(project_id):
    sprints = get_milestones(project=project_id, closed=False)
    overview = []

    for sprint in sprints:
        # Ya incluye user_stories, no necesitamos otra llamada
        total_stories = len(sprint["user_stories"])

        # Llamar a stats solo si necesitamos datos detallados
        stats = get_milestone_stats(sprint["id"])

        overview.append({
            "sprint": sprint,
            "stats": stats,
            "velocity": stats["completed_points"] / stats["total_points"] if stats["total_points"] > 0 else 0
        })

    return overview
```

---

### 56. Crear Milestone (POST /api/v1/milestones)

**Descripción**: Crear un nuevo milestone/sprint.

**Parámetros requeridos**:
- `project`: ID del proyecto
- `name`: Nombre del sprint

**Parámetros opcionales**:
- `estimated_start`: Fecha de inicio (YYYY-MM-DD)
- `estimated_finish`: Fecha de fin (YYYY-MM-DD)
- `slug`: URL-friendly identifier (auto-generado si no se especifica)
- `disponibility`: Disponibilidad del equipo (0.0-1.0)
- `order`: Orden del sprint

**Response**:
- Milestone creado con ID asignado

**Uso eficiente**:
- **Fechas realistas**: Definir estimated_start y estimated_finish para planning
- **Disponibility**: Importante para cálculo de capacity (ej: 0.8 si hay feriados)
- **Orden secuencial**: Mantener order consistente para vista cronológica
- **Naming convention**: Usar convención consistente (Sprint 1, Sprint 2 o por fecha)

**Combinación con otras funcionalidades**:
- Crear sprint → mover stories desde backlog → planning completo

```python
# Crear sprint con planning
def create_sprint_with_stories(project_id, sprint_name, start, end, story_ids):
    # 1. Crear sprint
    sprint = create_milestone(project_id, sprint_name, start, end)
    sprint_id = sprint["id"]

    # 2. Mover stories al sprint
    bulk_update_milestone(project_id, sprint_id, story_ids)

    # 3. Reordenar por prioridad
    order_pairs = [(sid, idx) for idx, sid in enumerate(story_ids)]
    bulk_update_sprint_order(project_id, sprint_id, order_pairs)

    return sprint
```

---

### 57. Actualizar Milestone (PATCH /api/v1/milestones/{milestoneId})

**Descripción**: Actualizar campos específicos de un milestone.

**Parámetros opcionales**:
- `name`: Renombrar sprint
- `estimated_start`, `estimated_finish`: Ajustar fechas
- `closed`: Cerrar o reabrir sprint
- `disponibility`: Ajustar disponibilidad

**Uso eficiente**:
- **Cerrar sprint**: Importante marcar `closed=true` al finalizar para retrospectiva
- **Extender fechas**: Si sprint necesita más tiempo, actualizar estimated_finish
- **No modificar sprints cerrados**: Generalmente, dejar histórico intacto

**Combinación con otras funcionalidades**:
- Cerrar sprint → mover stories no completadas al siguiente sprint
- Ajustar fechas → notificar al equipo (manual o webhook)

---

### 58. Eliminar Milestone (DELETE /api/v1/milestones/{milestoneId})

**Descripción**: Eliminar un milestone.

**Uso eficiente**:
- **User stories permanecen**: Las stories regresan al backlog, no se eliminan
- **Cuidado con histórico**: No eliminar sprints completados (usar closed=true)
- **Solo sprints vacíos o planning**: Eliminar solo si fue error de creación

---

### 59. Estadísticas de Milestone (GET /api/v1/milestones/{milestoneId}/stats)

**Descripción**: Obtener estadísticas detalladas de un sprint.

**Response**:
- `total_points`: Puntos totales planificados
- `completed_points`: Puntos completados
- `total_userstories`: Total de stories
- `completed_userstories`: Stories completadas
- `total_tasks`: Total de tasks
- `completed_tasks`: Tasks completadas
- `iocaine_doses`: Número de tasks que tomaron más tiempo del esperado
- `days`: Array con progreso día a día (burndown data)

**Uso eficiente**:
- **Dashboard de sprint**: Llamar periódicamente para actualizar dashboard
- **Burndown chart**: Usar campo `days` para graficar burndown
- **Velocity calculation**: `completed_points` / días del sprint
- **Predictive analytics**: Comparar total_points vs completed_points vs días restantes

**Combinación con otras funcionalidades**:
- Obtener stats diariamente → actualizar burndown chart
- Al cierre del sprint → guardar stats para análisis histórico de velocity
- Comparar stats entre sprints → identificar tendencias

```python
# Dashboard de sprint actualizado
def get_sprint_dashboard(milestone_id):
    stats = get_milestone_stats(milestone_id)

    # Calcular métricas adicionales
    completion_rate = stats["completed_points"] / stats["total_points"] if stats["total_points"] > 0 else 0

    # Burndown data para gráfico
    burndown = [
        {
            "day": day["day"],
            "ideal": calculate_ideal_burndown(day, stats),
            "actual": day["completed_points"]
        }
        for day in stats["days"]
    ]

    return {
        "stats": stats,
        "completion_rate": completion_rate,
        "burndown": burndown
    }
```

---

### 60. Watchers de Milestone

**Funcionalidades**:
- `POST /api/v1/milestones/{milestoneId}/watch`: Seguir sprint
- `POST /api/v1/milestones/{milestoneId}/unwatch`: Dejar de seguir
- `GET /api/v1/milestones/{milestoneId}/watchers`: Lista de watchers

**Uso eficiente**:
- **Team awareness**: Todo el equipo debería hacer watch del sprint activo
- **Notificaciones de cambios**: Recibir notificaciones de cambios en el sprint
- **Stakeholders**: Product owners y stakeholders pueden hacer watch

**Combinación con otras funcionalidades**:
- Crear sprint → auto-watch por el creador
- Asignar stories a sprint → considerar auto-watch para asignados

---

## Funcionalidades de Historial y Comentarios

### 61. Obtener Historial de Entidad

**Endpoints**:
- `GET /api/v1/history/userstory/{usId}`: Historial de user story
- `GET /api/v1/history/issue/{issueId}`: Historial de issue
- `GET /api/v1/history/task/{taskId}`: Historial de task
- `GET /api/v1/history/wiki/{wikiId}`: Historial de wiki page

**Response**:
- Array de entradas de historial en orden cronológico
- Cada entrada incluye:
  - `user`: Usuario que hizo el cambio
  - `created_at`: Timestamp del cambio
  - `type`: Tipo de cambio (creación, modificación, comentario)
  - `is_snapshot`: Si es snapshot completo o diff
  - `diff`: Objeto con cambios (campo: [valor_anterior, valor_nuevo])
  - `values`: Valores actuales después del cambio
  - `comment`: Comentario asociado al cambio
  - `delete_comment_date`: Si el comentario fue eliminado

**Uso eficiente**:
- **Auditoría completa**: Ver todos los cambios históricos de un elemento
- **Timeline de trabajo**: Mostrar línea de tiempo de cambios
- **Cachear localmente**: Si necesitas mostrar history múltiples veces sin cambios
- **Filtrar por tipo**: Procesar solo comentarios o solo cambios de estado según necesidad

**Combinación con otras funcionalidades**:
- Mostrar timeline en vista de detalle de story/issue/task
- Análisis de tiempo: cuánto tiempo estuvo en cada estado
- Detección de patterns: qué usuarios modifican más, qué campos cambian más

```python
# Análisis de tiempo por estado
def analyze_time_in_status(userstory_id):
    history = get_userstory_history(userstory_id)
    time_by_status = {}
    current_status = None
    status_start = None

    for entry in history:
        if "status" in entry["diff"]:
            # Cambió de estado
            if current_status and status_start:
                duration = entry["created_at"] - status_start
                time_by_status[current_status] = time_by_status.get(current_status, 0) + duration

            current_status = entry["diff"]["status"][1]  # Nuevo valor
            status_start = entry["created_at"]

    return time_by_status
```

---

### 62. Agregar Comentario a Entidad

**Método**: A través de actualización (PATCH) con campo `comment`

**Ejemplo**:
```python
# Agregar comentario sin modificar otros campos
patch_userstory(userstory_id, {
    "version": current_version,
    "comment": "Este es un comentario importante"
})
```

**Uso eficiente**:
- **Documentar cambios**: Siempre agregar comentario al hacer cambios importantes
- **Comunicación asíncrona**: Comentarios como forma de comunicación del equipo
- **Lightweight**: No requiere endpoint separado, usar PATCH con solo version + comment
- **Markdown support**: Los comentarios soportan Markdown

**Combinación con otras funcionalidades**:
- Cambiar status → agregar comentario explicando razón
- Bloquear item → agregar blocked_note + comentario detallado
- Resolver issue → agregar comentario de resolución

---

### 63. Obtener Versiones de Comentario

**Endpoints**:
- `GET /api/v1/history/userstory/{usId}/commentVersions?id={commentId}`
- `GET /api/v1/history/issue/{issueId}/commentVersions?id={commentId}`
- `GET /api/v1/history/task/{taskId}/commentVersions?id={commentId}`

**Response**:
- Array de versiones del comentario (si fue editado)
- Cada versión incluye texto y timestamp

**Uso eficiente**:
- **Auditoría de ediciones**: Ver si un comentario fue modificado y qué decía originalmente
- **Usar solo cuando necesario**: No llamar por default, solo si el usuario pide ver historial de ediciones

**Combinación con otras funcionalidades**:
- Mostrar indicador "editado" en comentarios modificados
- Link para ver versiones anteriores

---

### 64. Editar Comentario

**Endpoints**:
- `POST /api/v1/history/userstory/{usId}/edit_comment?id={commentId}`
- `POST /api/v1/history/issue/{issueId}/edit_comment?id={commentId}`
- `POST /api/v1/history/task/{taskId}/edit_comment?id={commentId}`

**Parámetros**:
- `comment`: Nuevo texto del comentario (reemplaza el anterior)

**Uso eficiente**:
- **Corrección de errores**: Editar para corregir typos o agregar información
- **No eliminar información**: Mejor editar que eliminar si el comentario tiene valor
- **Marca de edición**: Taiga automáticamente marca el comentario como editado

**Combinación con otras funcionalidades**:
- Permitir edición solo al autor del comentario
- Mostrar timestamp de última edición

---

### 65. Eliminar Comentario

**Endpoints**:
- `POST /api/v1/history/userstory/{usId}/delete_comment?id={commentId}`
- `POST /api/v1/history/issue/{issueId}/delete_comment?id={commentId}`
- `POST /api/v1/history/task/{taskId}/delete_comment?id={commentId}`

**Uso eficiente**:
- **Soft delete**: El comentario se marca como eliminado pero permanece en el historial
- **Reversible**: Puede restaurarse con undelete
- **Permisos**: Verificar que el usuario puede eliminar (autor o admin)

**Combinación con otras funcionalidades**:
- Eliminar comentarios inapropiados
- Limpiar comentarios de prueba

---

### 66. Restaurar Comentario Eliminado

**Endpoints**:
- `POST /api/v1/history/userstory/{usId}/undelete_comment?id={commentId}`
- `POST /api/v1/history/issue/{issueId}/undelete_comment?id={commentId}`
- `POST /api/v1/history/task/{taskId}/undelete_comment?id={commentId}`

**Uso eficiente**:
- **Recuperación de errores**: Restaurar comentarios eliminados por error
- **Admin function**: Típicamente requiere permisos de administrador

---

## Funcionalidades de Usuarios y Membresías

### 67. Obtener Usuario Actual (GET /api/v1/users/me)

**Descripción**: Ya cubierto en sección de autenticación (#3)

---

### 68. Listar Usuarios (GET /api/v1/users)

**Descripción**: Obtener lista de usuarios.

**Filtros disponibles**:
- `project`: Filtrar usuarios de un proyecto específico

**Response**:
- Array de usuarios con información básica

**Uso eficiente**:
- **Filtrar por proyecto**: Para obtener solo miembros del proyecto
- **Cachear lista**: Si no cambia frecuentemente
- **Usar para asignación**: Poblar dropdowns de asignación de stories/issues/tasks

**Combinación con otras funcionalidades**:
- Obtener users del proyecto → mostrar en selector de asignación
- Usar con memberships para información más detallada de roles

---

### 69. Listar Membresías (GET /api/v1/memberships)

**Descripción**: Obtener lista de membresías (usuarios + roles en proyectos).

**Filtros**:
- `project`: ID del proyecto (recomendado)

**Response**:
- Array de membresías con:
  - Usuario
  - Rol en el proyecto
  - Permisos
  - Si es admin del proyecto

**Uso eficiente**:
- **Más completo que users**: Incluye roles y permisos
- **Filtrar por proyecto**: Para obtener equipo del proyecto con roles
- **Verificación de permisos**: Antes de permitir operaciones sensibles

**Combinación con otras funcionalidades**:
- Listar membresías → verificar rol → permitir/denegar operación
- Mostrar equipo del proyecto con roles

```python
# Verificar permisos
def can_delete_project(user_id, project_id):
    memberships = get_memberships(project=project_id)
    user_membership = [m for m in memberships if m["user"]["id"] == user_id]

    if not user_membership:
        return False

    return user_membership[0]["is_admin"]
```

---

### 70. Crear Membresía (POST /api/v1/memberships)

**Descripción**: Agregar un usuario a un proyecto.

**Parámetros requeridos**:
- `project`: ID del proyecto
- `role`: ID del rol a asignar

**Parámetros opcionales**:
- `email`: Email del usuario a invitar (si no está en la instancia, se envía invitación)
- `user`: ID del usuario (si ya existe en la instancia)
- `is_admin`: Si será admin del proyecto

**Response**:
- Membresía creada

**Uso eficiente**:
- **Invitación por email**: Si el usuario no existe, Taiga envía invitación automáticamente
- **Rol adecuado**: Asignar el rol correcto desde inicio (Product Owner, Developer, Designer, etc.)
- **is_admin con precaución**: Otorgar permisos de admin solo cuando necesario
- **Batch para equipos**: Si agregas múltiples usuarios, considerar operación en lote (si disponible)

**Combinación con otras funcionalidades**:
- Crear proyecto → agregar miembros del equipo
- Usuario acepta invitación → crear membresía

```python
# Setup inicial de proyecto con equipo
def setup_project_with_team(project_data, team_members):
    # 1. Crear proyecto
    project = create_project(**project_data)
    project_id = project["id"]

    # 2. Agregar miembros
    for member in team_members:
        create_membership(
            project=project_id,
            email=member["email"],
            role=member["role"],
            is_admin=member.get("is_admin", False)
        )

    return project
```

---

### 71. Obtener Membresía (GET /api/v1/memberships/{membershipId})

**Descripción**: Obtener información detallada de una membresía específica.

**Uso eficiente**:
- **Verificar permisos específicos**: Para operaciones sensibles
- **Cachear**: Si no cambia frecuentemente

---

### 72. Actualizar Membresía (PATCH /api/v1/memberships/{membershipId})

**Descripción**: Actualizar rol o permisos de un miembro del proyecto.

**Parámetros opcionales**:
- `role`: Cambiar rol
- `is_admin`: Cambiar permisos de admin

**Uso eficiente**:
- **Promociones/cambios de rol**: Cuando un miembro cambia de responsabilidad
- **Ajuste de permisos**: Otorgar o quitar permisos de admin

**Combinación con otras funcionalidades**:
- Developer → Tech Lead: cambiar rol + is_admin=true

---

### 73. Eliminar Membresía (DELETE /api/v1/memberships/{membershipId})

**Descripción**: Remover un usuario de un proyecto.

**Uso eficiente**:
- **Usuario permanece en Taiga**: Solo se remueve del proyecto específico
- **Reasignación previa**: Considerar reasignar sus stories/issues/tasks antes de remover
- **No afecta histórico**: Los cambios históricos mantienen su nombre

**Combinación con otras funcionalidades**:
- Antes de eliminar → listar items asignados → reasignar → eliminar membresía

---

## Funcionalidades de Atributos Personalizados

### 74. Listar Atributos Personalizados

**Endpoints**:
- `GET /api/v1/userstory-custom-attributes?project={projectId}`
- `GET /api/v1/issue-custom-attributes?project={projectId}`
- `GET /api/v1/task-custom-attributes?project={projectId}`
- `GET /api/v1/epic-custom-attributes?project={projectId}`

**Response**:
- Array de atributos personalizados definidos para el proyecto
- Cada atributo incluye:
  - `id`: ID del atributo
  - `name`: Nombre
  - `description`: Descripción
  - `type`: Tipo de dato (text, multiline, date, url, dropdown, etc.)
  - `order`: Orden de visualización

**Uso eficiente**:
- **Cachear definiciones**: Llamar una vez al inicio, reutilizar
- **Validación**: Verificar que atributos existen antes de establecer valores
- **UI dinámica**: Construir formularios basados en atributos definidos

**Combinación con otras funcionalidades**:
- Listar atributos → construir formulario de creación/edición
- Validar valores según tipo de atributo

---

### 75. Crear Atributo Personalizado

**Endpoints**:
- `POST /api/v1/userstory-custom-attributes`
- `POST /api/v1/issue-custom-attributes`
- `POST /api/v1/task-custom-attributes`
- `POST /api/v1/epic-custom-attributes`

**Parámetros requeridos**:
- `project`: ID del proyecto
- `name`: Nombre del atributo

**Parámetros opcionales**:
- `description`: Descripción del atributo
- `type`: Tipo de dato (text, multiline, richtext, date, url, dropdown, checkbox, number)
- `order`: Orden de visualización (para formularios)
- `extra`: Configuración adicional según tipo (ej: opciones para dropdown)

**Response**:
- Atributo creado con ID asignado

**Uso eficiente**:
- **Definir al inicio**: Crear atributos personalizados al setup del proyecto
- **Tipos apropiados**: Usar el tipo correcto para validación automática
- **Order para UX**: Definir orden lógico de presentación
- **Dropdown para valores fijos**: Usar dropdown en lugar de text si hay opciones predefinidas

**Combinación con otras funcionalidades**:
- Crear proyecto → definir atributos personalizados → usar en stories/issues

```python
# Setup de atributos personalizados del proyecto
def setup_project_custom_attributes(project_id):
    attributes = [
        {
            "name": "Cliente",
            "type": "text",
            "description": "Nombre del cliente que solicitó la funcionalidad",
            "order": 1
        },
        {
            "name": "Prioridad de Negocio",
            "type": "dropdown",
            "description": "Prioridad desde perspectiva de negocio",
            "order": 2,
            "extra": {"options": ["Alta", "Media", "Baja"]}
        },
        {
            "name": "Fecha Límite",
            "type": "date",
            "description": "Fecha límite de entrega",
            "order": 3
        }
    ]

    for attr_data in attributes:
        create_userstory_custom_attribute(project_id, **attr_data)
```

---

### 76. Obtener Atributo Personalizado

**Endpoints**:
- `GET /api/v1/userstory-custom-attributes/{attributeId}`
- `GET /api/v1/issue-custom-attributes/{attributeId}`
- `GET /api/v1/task-custom-attributes/{attributeId}`
- `GET /api/v1/epic-custom-attributes/{attributeId}`

**Uso eficiente**:
- **Usar lista en lugar de individual**: Generalmente más eficiente listar todos

---

### 77. Actualizar Atributo Personalizado

**Endpoints**:
- `PATCH /api/v1/userstory-custom-attributes/{attributeId}`
- `PATCH /api/v1/issue-custom-attributes/{attributeId}`
- `PATCH /api/v1/task-custom-attributes/{attributeId}`
- `PATCH /api/v1/epic-custom-attributes/{attributeId}`

**Uso eficiente**:
- **Renombrar**: Cambiar nombre o descripción
- **Reordenar**: Ajustar order para mejor UX
- **Modificar opciones**: En dropdowns, actualizar lista de opciones

---

### 78. Eliminar Atributo Personalizado

**Endpoints**:
- `DELETE /api/v1/userstory-custom-attributes/{attributeId}`
- (Similar para issue, task, epic)

**Uso eficiente**:
- **Valores se pierden**: Los valores establecidos en items se eliminarán
- **Considerar deprecación**: En lugar de eliminar, renombrar o marcar como no usado

---

### 79. Establecer Valores de Atributos Personalizados

**Método**: A través del campo `custom_attributes` al crear/actualizar entidad

**Ejemplo**:
```python
# Crear user story con valores de atributos personalizados
create_userstory(project_id, {
    "subject": "Nueva funcionalidad",
    "custom_attributes": {
        "1": "Cliente ABC",  # ID del atributo "Cliente"
        "2": "Alta",         # ID del atributo "Prioridad de Negocio"
        "3": "2025-03-15"    # ID del atributo "Fecha Límite"
    }
})

# Actualizar valores
patch_userstory(us_id, {
    "version": current_version,
    "custom_attributes": {
        "1": "Cliente XYZ"  # Solo actualizar atributo específico
    }
})
```

**Uso eficiente**:
- **IDs de atributos**: Usar IDs numéricos como keys del objeto custom_attributes
- **Actualización parcial**: Puedes actualizar solo algunos atributos
- **Validación de tipo**: Asegurar que el valor coincide con el tipo del atributo
- **Valores null**: Usar null para limpiar un valor

**Combinación con otras funcionalidades**:
- Filtrar stories por valor de atributo personalizado
- Reportes basados en atributos personalizados

---

## Funcionalidades de Webhooks

### 80. Listar Webhooks (GET /api/v1/webhooks)

**Descripción**: Obtener lista de webhooks configurados.

**Filtros**:
- `project`: ID del proyecto

**Response**:
- Array de webhooks con configuración

**Uso eficiente**:
- **Auditoría**: Ver qué webhooks están activos
- **Verificar configuración**: Antes de crear duplicados

---

### 81. Crear Webhook (POST /api/v1/webhooks)

**Descripción**: Configurar un nuevo webhook para recibir notificaciones de eventos.

**Parámetros requeridos**:
- `project`: ID del proyecto
- `name`: Nombre descriptivo del webhook
- `url`: URL que recibirá los eventos
- `key`: Clave secreta para validar requests

**Parámetros opcionales**:
- `events`: Array de eventos a escuchar (default: todos)
  - Eventos disponibles: `milestone`, `userstory`, `task`, `issue`, `wikipage`

**Response**:
- Webhook creado con ID

**Uso eficiente**:
- **Integración con otros sistemas**: Slack, Discord, sistemas CI/CD, etc.
- **Eventos específicos**: Filtrar solo eventos relevantes para reducir tráfico
- **Clave secreta**: Usar key para validar que requests vienen de Taiga
- **URL pública**: La URL debe ser accesible públicamente por Taiga

**Combinación con otras funcionalidades**:
- Webhook de userstory → notificar en Slack cuando story cambia a "Ready for Review"
- Webhook de issue → crear ticket en sistema externo
- Webhook de milestone → notificar al cerrar sprint

```python
# Configurar webhook para notificaciones de Slack
def setup_slack_webhook(project_id, slack_webhook_url):
    # Tu endpoint que procesará y reenviará a Slack
    intermediate_url = "https://tu-servidor.com/taiga-webhook"

    return create_webhook(
        project=project_id,
        name="Slack Notifications",
        url=intermediate_url,
        key="tu-clave-secreta-aleatoria",
        events=["userstory", "issue"]  # Solo stories e issues
    )
```

---

### 82. Obtener Webhook (GET /api/v1/webhooks/{webhookId})

**Descripción**: Obtener información de un webhook específico.

**Uso eficiente**:
- **Verificar configuración**: Antes de modificar

---

### 83. Actualizar Webhook (PATCH /api/v1/webhooks/{webhookId})

**Descripción**: Modificar configuración de un webhook.

**Parámetros opcionales**:
- `name`: Cambiar nombre
- `url`: Cambiar URL destino
- `key`: Cambiar clave secreta
- `events`: Modificar eventos escuchados

**Uso eficiente**:
- **Actualizar URL**: Si cambia el endpoint
- **Rotación de clave**: Por seguridad, cambiar key periódicamente
- **Ajustar eventos**: Agregar o remover eventos según necesidad

---

### 84. Eliminar Webhook (DELETE /api/v1/webhooks/{webhookId})

**Descripción**: Eliminar un webhook.

**Uso eficiente**:
- **Limpieza**: Eliminar webhooks no usados
- **Desactivación temporal**: Considerar actualizar events=[] en lugar de eliminar

---

### 85. Probar Webhook (POST /api/v1/webhooks/{webhookId}/test)

**Descripción**: Enviar un evento de prueba al webhook.

**Uso eficiente**:
- **Verificación**: Después de crear/actualizar, probar que funciona
- **Debug**: Para verificar que el endpoint está respondiendo correctamente
- **Incluye payload real**: El test envía un payload de ejemplo

**Combinación con otras funcionalidades**:
- Crear webhook → probar → verificar logs → activar

---

### 86. Obtener Logs de Webhook (GET /api/v1/webhooks/{webhookId}/logs)

**Descripción**: Obtener log de ejecuciones del webhook.

**Response**:
- Array de ejecuciones con:
  - Timestamp
  - Status code recibido
  - Response del endpoint
  - Errores si los hubo

**Uso eficiente**:
- **Debug**: Ver por qué un webhook no está funcionando
- **Monitoreo**: Verificar salud del webhook
- **Límite de retención**: Logs se mantienen por tiempo limitado

**Combinación con otras funcionalidades**:
- Si webhook falla consistentemente → verificar logs → corregir endpoint → probar

---

### 87. Payload de Webhook

**Estructura del payload recibido**:

```json
{
  "action": "change",  // "create", "change", "delete"
  "type": "userstory",  // "milestone", "task", "issue", "wikipage"
  "by": {
    "id": 888691,
    "username": "usuario",
    "full_name": "Usuario Completo"
  },
  "date": "2025-01-20T14:30:00Z",
  "data": {
    // Objeto completo de la entidad afectada
    "id": 123456,
    "ref": 1,
    "subject": "Login de usuarios",
    "status": 2,
    "project": {
      "id": 309804,
      "name": "Mi Proyecto",
      "slug": "mi-proyecto"
    }
    // ... más campos
  },
  "change": {  // Solo en action="change"
    "diff": {
      "status": {
        "from": 1,
        "to": 2
      }
      // ... otros campos modificados
    },
    "comment": "Cambiado a In Progress"
  }
}
```

**Uso eficiente**:
- **Validar signature**: Usar la key para verificar autenticidad
- **Filtrar por action**: Procesar solo create, change, o delete según necesidad
- **Filtrar por diff**: En change, solo actuar si ciertos campos cambiaron
- **Usar data completo**: El payload incluye el objeto completo, no necesitas hacer GET adicional

**Ejemplo de procesamiento eficiente**:

```python
def process_taiga_webhook(payload, signature):
    # 1. Validar signature
    if not validate_signature(payload, signature, WEBHOOK_KEY):
        return {"error": "Invalid signature"}, 401

    # 2. Extraer información relevante
    action = payload["action"]
    entity_type = payload["type"]

    # 3. Procesar según tipo y acción
    if entity_type == "userstory" and action == "change":
        # Verificar si cambió a "Ready for Review"
        if "status" in payload["change"]["diff"]:
            new_status = payload["change"]["diff"]["status"]["to"]
            if new_status == STATUS_READY_FOR_REVIEW:
                # Notificar en Slack
                notify_slack(
                    f"Story #{payload['data']['ref']} ready for review: {payload['data']['subject']}"
                )

    elif entity_type == "issue" and action == "create":
        # Crear ticket en sistema externo
        create_external_ticket(payload["data"])

    return {"status": "processed"}, 200
```

---

## Patrones de Uso Eficiente

### Patrón 1: Inicialización de Sesión Eficiente

**Objetivo**: Minimizar llamadas al API al inicio de sesión

```python
class TaigaSession:
    def __init__(self, username, password):
        # 1. Autenticación (1 llamada)
        auth_response = self.login(username, password)
        self.token = auth_response["auth_token"]
        self.refresh_token = auth_response["refresh"]

        # 2. Info de usuario (1 llamada)
        user_info = self.get_user_me()
        self.user_id = user_info["id"]
        self.username = user_info["username"]

        # 3. Lista de proyectos (1 llamada)
        self.projects = self.get_projects()

        # Total: 3 llamadas al inicio
        # Cachear todo para uso posterior
```

---

### Patrón 2: Creación Completa de Epic con Stories

**Objetivo**: Crear un epic completo con stories relacionadas eficientemente

```python
def create_epic_complete(project_id, epic_data, stories_data):
    # 1. Crear epic (1 llamada)
    epic = create_epic(project_id, **epic_data)
    epic_id = epic["id"]

    # 2. Crear stories en bulk (1 llamada para N stories)
    stories = bulk_create_userstories(project_id, stories_data)
    story_ids = [s["id"] for s in stories]

    # 3. Relacionar todas con epic en bulk (1 llamada para N relaciones)
    bulk_create_epic_related_userstories(epic_id, story_ids)

    # Total: 3 llamadas vs 1 + N + N (si fuera individual)
    return epic, stories
```

---

### Patrón 3: Sprint Planning Eficiente

**Objetivo**: Planificar un sprint completo con mínimas llamadas

```python
def plan_sprint(project_id, sprint_name, start_date, end_date, story_ids):
    # 1. Crear sprint (1 llamada)
    sprint = create_milestone(project_id, sprint_name, start_date, end_date)
    sprint_id = sprint["id"]

    # 2. Mover todas las stories al sprint (1 llamada para N stories)
    bulk_update_milestone(project_id, sprint_id, story_ids)

    # 3. Reordenar por prioridad (1 llamada para N reordenes)
    order_pairs = [(sid, idx) for idx, sid in enumerate(story_ids)]
    bulk_update_sprint_order(project_id, sprint_id, order_pairs)

    # 4. Obtener stats iniciales (1 llamada)
    stats = get_milestone_stats(sprint_id)

    # Total: 4 llamadas para planificar sprint completo
    return sprint, stats
```

---

### Patrón 4: Dashboard de Usuario Eficiente

**Objetivo**: Mostrar dashboard personal con mínimas llamadas

```python
def get_user_dashboard(user_id, project_id):
    # 1. Obtener sprint activo del proyecto (1 llamada, filtrada)
    sprints = get_milestones(project=project_id, closed=False)
    active_sprint = sprints[0] if sprints else None

    if not active_sprint:
        return {"message": "No active sprint"}

    sprint_id = active_sprint["id"]

    # 2. Obtener stories asignadas al usuario en el sprint (1 llamada, filtrada)
    my_stories = get_userstories(
        project=project_id,
        milestone=sprint_id,
        assigned_to=user_id,
        is_closed=False
    )

    # 3. Obtener tasks asignadas al usuario en el sprint (1 llamada, filtrada)
    my_tasks = get_tasks(
        project=project_id,
        milestone=sprint_id,
        assigned_to=user_id,
        is_closed=False
    )

    # Total: 3 llamadas para dashboard completo
    return {
        "sprint": active_sprint,
        "my_stories": my_stories,
        "my_tasks": my_tasks
    }
```

---

### Patrón 5: Importación Masiva Eficiente

**Objetivo**: Importar datos desde sistema externo eficientemente

```python
def import_from_external_system(project_id, external_data):
    # 1. Crear epics en bulk (1 llamada para N epics)
    epics_data = [e for e in external_data["epics"]]
    epics = bulk_create_epics(project_id, epics_data)
    epic_map = {e["subject"]: e["id"] for e in epics}

    # 2. Crear user stories en bulk (1 llamada para N stories)
    stories_data = [s for s in external_data["stories"]]
    stories = bulk_create_userstories(project_id, stories_data)

    # 3. Relacionar stories con epics
    # Agrupar por epic para hacer bulk relates
    stories_by_epic = {}
    for story in stories:
        epic_name = story.get("epic_name")  # Metadata de importación
        if epic_name and epic_name in epic_map:
            epic_id = epic_map[epic_name]
            if epic_id not in stories_by_epic:
                stories_by_epic[epic_id] = []
            stories_by_epic[epic_id].append(story["id"])

    # 1 llamada por epic (en lugar de 1 por story)
    for epic_id, story_ids in stories_by_epic.items():
        bulk_create_epic_related_userstories(epic_id, story_ids)

    # Total: 1 + 1 + num_epics llamadas vs 1 + N + N (individual)
    return epics, stories
```

---

### Patrón 6: Cierre de Sprint Eficiente

**Objetivo**: Cerrar sprint y mover items no completados

```python
def close_sprint(project_id, closing_sprint_id, next_sprint_id):
    # 1. Obtener stories no completadas del sprint (1 llamada, filtrada)
    incomplete_stories = get_userstories(
        project=project_id,
        milestone=closing_sprint_id,
        is_closed=False
    )

    incomplete_ids = [s["id"] for s in incomplete_stories]

    # 2. Mover stories no completadas al siguiente sprint (1 llamada para N stories)
    if incomplete_ids and next_sprint_id:
        bulk_update_milestone(project_id, next_sprint_id, incomplete_ids)

    # 3. Cerrar el sprint (1 llamada)
    closed_sprint = patch_milestone(closing_sprint_id, {
        "closed": True
    })

    # 4. Obtener stats finales para retrospectiva (1 llamada)
    final_stats = get_milestone_stats(closing_sprint_id)

    # Total: 4 llamadas para cerrar sprint completo
    return closed_sprint, final_stats, len(incomplete_ids)
```

---

### Patrón 7: Vista de Roadmap Eficiente

**Objetivo**: Mostrar roadmap completo con progreso de epics

```python
def get_project_roadmap(project_id):
    # 1. Listar todos los epics (1 llamada)
    epics = get_epics(project=project_id)

    roadmap = []

    # 2. Para cada epic, obtener stories relacionadas (1 llamada por epic)
    for epic in epics:
        related_stories = get_epic_related_userstories(epic["id"])

        # Calcular progreso
        total = len(related_stories)
        if total == 0:
            progress = 0
        else:
            completed = sum(1 for r in related_stories if r["user_story"]["is_closed"])
            progress = (completed / total) * 100

        roadmap.append({
            "epic": epic,
            "total_stories": total,
            "completed_stories": completed,
            "progress_percent": progress
        })

    # Total: 1 + num_epics llamadas
    # Alternativa más pesada sería: listar todas las stories y filtrar localmente
    return roadmap
```

---

### Patrón 8: Actualización con Reintentos (Manejo de Concurrencia)

**Objetivo**: Manejar conflictos de versión automáticamente

```python
def update_with_retry(entity_type, entity_id, updates, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Obtener versión actual
            if entity_type == "userstory":
                entity = get_userstory(entity_id)
                patch_func = patch_userstory
            elif entity_type == "issue":
                entity = get_issue(entity_id)
                patch_func = patch_issue
            # ... otros tipos

            # Incluir versión en updates
            updates["version"] = entity["version"]

            # Intentar actualizar
            return patch_func(entity_id, updates)

        except Conflict409Error:
            if attempt == max_retries - 1:
                raise  # Último intento, propagar error
            # Esperar un poco antes de reintentar
            time.sleep(0.5 * (attempt + 1))

    raise Exception("Max retries reached")

# Uso
update_with_retry("userstory", us_id, {
    "status": STATUS_IN_PROGRESS,
    "comment": "Moving to in progress"
})
```

---

### Patrón 9: Caché Inteligente

**Objetivo**: Cachear datos que no cambian frecuentemente

```python
class TaigaCache:
    def __init__(self, ttl_seconds=300):  # 5 minutos default
        self.cache = {}
        self.ttl = ttl_seconds

    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]  # Expiró
        return None

    def set(self, key, value):
        self.cache[key] = (value, time.time())

    def invalidate(self, key):
        if key in self.cache:
            del self.cache[key]

# Uso
cache = TaigaCache(ttl_seconds=600)  # 10 minutos

def get_project_filters(project_id):
    cache_key = f"filters_{project_id}"

    # Intentar obtener de caché
    cached = cache.get(cache_key)
    if cached:
        return cached

    # No está en caché, obtener del API
    filters = get_userstory_filters_data(project_id)

    # Cachear resultado
    cache.set(cache_key, filters)

    return filters

# Invalidar caché cuando cambian datos relevantes
def on_member_added(project_id):
    cache.invalidate(f"filters_{project_id}")  # Los filtros incluyen lista de usuarios
```

---

### Patrón 10: Procesamiento de Webhooks Eficiente

**Objetivo**: Procesar webhooks sin hacer llamadas innecesarias al API

```python
def process_webhook_efficiently(payload):
    # El payload YA incluye el objeto completo en payload["data"]
    # NO necesitas hacer GET adicional

    action = payload["action"]
    entity_type = payload["type"]
    entity_data = payload["data"]  # Objeto completo

    if entity_type == "userstory" and action == "change":
        # Acceder a datos directamente del payload
        story_id = entity_data["id"]
        story_ref = entity_data["ref"]
        story_subject = entity_data["subject"]
        current_status = entity_data["status"]

        # Verificar qué cambió
        if "status" in payload["change"]["diff"]:
            old_status = payload["change"]["diff"]["status"]["from"]
            new_status = payload["change"]["diff"]["status"]["to"]

            # Procesar según cambio
            if new_status == STATUS_READY_FOR_REVIEW:
                # Notificar sin llamadas al API
                notify_team(f"Story #{story_ref} is ready for review: {story_subject}")

        # Solo hacer llamadas al API si REALMENTE necesitas datos adicionales
        # Por ejemplo, obtener tasks de la story
        if new_status == STATUS_DONE:
            # Aquí sí necesitamos llamada adicional
            tasks = get_tasks(project=entity_data["project"], user_story=story_id)
            verify_all_tasks_done(tasks)

    return {"status": "processed"}
```

---

## Optimización de Llamadas al API

### Estrategia 1: Usar Operaciones en Lote (Bulk)

**Siempre que sea posible, usar endpoints bulk en lugar de loops**:

```python
# ❌ INEFICIENTE: N llamadas al API
for story_data in stories_data:
    create_userstory(project_id, **story_data)

# ✅ EFICIENTE: 1 llamada al API
bulk_create_userstories(project_id, stories_data)
```

**Endpoints bulk disponibles**:
- `POST /userstories/bulk_create`
- `POST /userstories/bulk_update_milestone`
- `POST /userstories/bulk_update_backlog_order`
- `POST /userstories/bulk_update_kanban_order`
- `POST /userstories/bulk_update_sprint_order`
- `POST /issues/bulk_create`
- `POST /epics/bulk_create`
- `POST /epics/{id}/related_userstories/bulk_create`
- `POST /tasks/bulk_create`

---

### Estrategia 2: Filtrar en el Servidor, No Localmente

**Usar parámetros de filtro del API en lugar de obtener todo y filtrar**:

```python
# ❌ INEFICIENTE: Obtener todos y filtrar localmente
all_stories = get_userstories(project=project_id)
my_stories = [s for s in all_stories if s["assigned_to"] == user_id and not s["is_closed"]]

# ✅ EFICIENTE: Filtrar en el servidor
my_stories = get_userstories(
    project=project_id,
    assigned_to=user_id,
    is_closed=False
)
```

**Beneficios**:
- Menos datos transferidos por red
- Procesamiento en el servidor (más eficiente)
- Respuesta más rápida

---

### Estrategia 3: Usar Paginación Apropiadamente

**Manejar paginación correctamente según caso de uso**:

```python
# Para listas cortas o cuando NECESITAS todo
headers = {"x-disable-pagination": "True"}
all_items = get_with_headers(url, headers)

# Para listas largas, procesar página por página
def process_all_pages(url):
    page = 1
    while True:
        response = get_with_pagination(url, page=page)
        items = response.json()

        if not items:
            break

        process_items(items)
        page += 1

# Para UIs, usar paginación nativa
def load_page(page_number):
    return get_userstories(project=project_id, page=page_number)
```

---

### Estrategia 4: Cachear Datos Estáticos o Semi-Estáticos

**Cachear datos que cambian infrecuentemente**:

```python
# Datos que cambian raramente
- Filtros del proyecto (statuses, types, severities)
- Lista de miembros del proyecto
- Atributos personalizados
- Configuración del proyecto

# Datos que cambian frecuentemente (NO cachear)
- User stories
- Issues
- Tasks
- Stats de milestone
```

**Implementar caché con TTL**:

```python
from functools import lru_cache
from datetime import datetime, timedelta

class TaigaClient:
    def __init__(self):
        self._filters_cache = {}
        self._filters_cache_time = {}
        self.CACHE_TTL = timedelta(minutes=10)

    def get_filters_cached(self, project_id):
        now = datetime.now()

        # Verificar si está en caché y no expiró
        if project_id in self._filters_cache:
            if now - self._filters_cache_time[project_id] < self.CACHE_TTL:
                return self._filters_cache[project_id]

        # No está en caché o expiró, obtener del API
        filters = self.get_userstory_filters_data(project_id)

        # Actualizar caché
        self._filters_cache[project_id] = filters
        self._filters_cache_time[project_id] = now

        return filters
```

---

### Estrategia 5: Usar PATCH en Lugar de PUT

**PATCH solo envía campos modificados, PUT requiere todos los campos**:

```python
# ❌ INEFICIENTE: PUT requiere todos los campos
story = get_userstory(us_id)
story["status"] = new_status
put_userstory(us_id, story)  # Envía TODO el objeto

# ✅ EFICIENTE: PATCH solo envía lo que cambia
patch_userstory(us_id, {
    "version": current_version,
    "status": new_status
})
```

---

### Estrategia 6: Agrupar Llamadas Secuenciales

**Cuando necesitas datos de múltiples endpoints, hacer llamadas en paralelo**:

```python
import asyncio
import aiohttp

# ❌ INEFICIENTE: Secuencial
project = get_project(project_id)
stats = get_project_stats(project_id)
users = get_project_users(project_id)
# Total: T1 + T2 + T3 segundos

# ✅ EFICIENTE: Paralelo
async def get_project_data(project_id):
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_project(session, project_id),
            fetch_project_stats(session, project_id),
            fetch_project_users(session, project_id)
        ]
        results = await asyncio.gather(*tasks)
        return results

# Total: max(T1, T2, T3) segundos
project, stats, users = asyncio.run(get_project_data(project_id))
```

---

### Estrategia 7: Minimizar Llamadas para Verificaciones

**Evitar hacer GET solo para verificar**:

```python
# ❌ INEFICIENTE: GET antes de cada operación
def update_story_if_exists(us_id, updates):
    try:
        story = get_userstory(us_id)  # Llamada 1
        patch_userstory(us_id, updates)  # Llamada 2
    except NotFound:
        return None

# ✅ EFICIENTE: Intentar directamente y manejar error
def update_story_direct(us_id, updates):
    try:
        return patch_userstory(us_id, updates)  # Solo 1 llamada
    except NotFound:
        return None
```

---

### Estrategia 8: Usar Relaciones Embedded

**Muchos endpoints ya incluyen datos relacionados en `*_extra_info`**:

```python
# ❌ INEFICIENTE: Obtener usuario separadamente
story = get_userstory(us_id)
user_id = story["assigned_to"]
user = get_user(user_id)  # Llamada adicional innecesaria
user_name = user["full_name"]

# ✅ EFICIENTE: Usar datos embedded
story = get_userstory(us_id)
user_name = story["assigned_to_extra_info"]["full_name_display"]
```

**Datos embedded disponibles**:
- `status_extra_info`: Información del status
- `assigned_to_extra_info`: Información del usuario asignado
- `owner_extra_info`: Información del owner
- `type_extra_info`: Información del tipo (issues)
- `severity_extra_info`: Información de severidad (issues)
- `priority_extra_info`: Información de prioridad (issues)

---

### Estrategia 9: Deshabilitar Paginación Solo Cuando Necesario

**La paginación está habilitada por defecto (30 items por página)**:

```python
# Para UIs con scroll infinito: usar paginación
def load_next_page(page):
    return get_userstories(project=project_id, page=page)

# Para procesamiento completo: deshabilitar paginación
headers = {"x-disable-pagination": "True"}
all_stories = get_userstories_with_headers(project=project_id, headers=headers)

# Pero cuidado con proyectos grandes!
# Mejor procesar por páginas si hay muchos items
```

---

### Estrategia 10: Aprovechar Webhooks en Lugar de Polling

**En lugar de hacer polling constante, usar webhooks**:

```python
# ❌ INEFICIENTE: Polling cada N segundos
def poll_for_changes():
    last_modified = None
    while True:
        stories = get_userstories(project=project_id)
        current_modified = max(s["modified_date"] for s in stories)

        if last_modified and current_modified > last_modified:
            process_changes(stories)

        last_modified = current_modified
        time.sleep(30)  # Polling cada 30 segundos

# ✅ EFICIENTE: Configurar webhook
setup_webhook(
    project=project_id,
    url="https://tu-servidor.com/webhook",
    events=["userstory"]
)

# Tu servidor recibe notificaciones en tiempo real
def webhook_handler(payload):
    if payload["action"] == "change":
        process_change(payload["data"])
```

---

## Resumen de Mejores Prácticas

### ✅ HACER:

1. **Usar operaciones bulk** siempre que sea posible
2. **Filtrar en el servidor** usando parámetros de query
3. **Cachear datos estáticos**: filtros, miembros, atributos personalizados
4. **Usar PATCH** en lugar de PUT para actualizaciones
5. **Aprovechar datos embedded** (`*_extra_info`)
6. **Configurar webhooks** para notificaciones en tiempo real
7. **Hacer llamadas en paralelo** cuando sean independientes
8. **Incluir comentarios** al hacer cambios importantes
9. **Manejar conflictos de versión** con retry automático
10. **Validar tokens** de webhooks por seguridad

### ❌ EVITAR:

1. **Loops con llamadas al API** (usar bulk en su lugar)
2. **Obtener todo y filtrar localmente** (filtrar en servidor)
3. **GET innecesarios** antes de operaciones
4. **Llamadas redundantes** para datos ya disponibles
5. **Polling frecuente** (usar webhooks)
6. **Crear sin asignar** (asignar proyecto/milestone desde inicio)
7. **Actualizar uno por uno** (usar bulk updates)
8. **Ignorar paginación** en listas grandes
9. **No cachear datos estáticos**
10. **No manejar errores de concurrencia**

---

## Conclusión

El API de Taiga proporciona un conjunto completo y robusto de funcionalidades para gestión de proyectos ágiles. La clave para un uso eficiente es:

1. **Entender las capacidades bulk** del API
2. **Aprovechar el filtrado del servidor**
3. **Cachear inteligentemente**
4. **Usar webhooks para eventos en tiempo real**
5. **Manejar correctamente la concurrencia**
6. **Procesar datos embedded** sin llamadas adicionales

Siguiendo estos patrones y estrategias, puedes construir integraciones y herramientas altamente eficientes que minimizan la latencia y el uso de recursos mientras maximizan la experiencia del usuario.
