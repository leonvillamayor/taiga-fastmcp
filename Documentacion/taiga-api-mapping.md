# Mapeo Completo de Funcionalidades de la API de Taiga

## Resumen Ejecutivo

**Total de funcionalidades identificadas**: 176+

Este documento mapea exhaustivamente todas las funcionalidades de la API de Taiga v1 para su implementación como herramientas MCP usando FastMCP.

## Distribución por Categorías

| Categoría | Funcionalidades | Prioridad |
|-----------|----------------|-----------|
| Autenticación | 2 | CRÍTICA |
| Proyectos | 21 | ALTA |
| User Stories | 24+ | ALTA |
| Issues | 20+ | ALTA |
| Epics | 27+ | MEDIA |
| Tasks | 20+ | MEDIA |
| Milestones/Sprints | 10 | ALTA |
| History/Comentarios | 20 | MEDIA |
| Usuarios/Membresías | 8 | ALTA |
| Atributos Personalizados | 24+ | BAJA |

## Implementación Actual vs Completa

### ✅ Ya Implementadas (Código actual)
- Proyectos: CRUD básico (6/21)
- User Stories: CRUD básico + bulk create (5/24)
- Issues: CRUD básico (5/20)
- Epics: CRUD básico + relaciones básicas (6/27)
- Tasks: CRUD básico (5/20)
- Milestones: CRUD básico + stats (6/10)

**Total implementado**: ~33/176 (18.75%)

### ❌ Funcionalidades Faltantes Críticas

#### Proyectos
- [ ] Obtener proyecto por slug
- [ ] Estadísticas de issues
- [ ] Gestión de módulos (backlog, kanban, wiki, issues, epics)
- [ ] Gestión de tags (create, edit, delete, mix)
- [ ] Like/Unlike proyecto
- [ ] Watch/Unwatch proyecto
- [ ] Duplicar proyecto
- [ ] Reordenar proyectos en lote

#### User Stories
- [ ] Obtener por referencia (ref + project)
- [ ] Filtros avanzados (milestone, status, assigned_to, tags, is_closed)
- [ ] Reordenar en backlog, kanban, sprint
- [ ] Actualizar milestone en lote
- [ ] Filtros disponibles (filters_data)
- [ ] Upvote/Downvote
- [ ] Obtener votantes
- [ ] Watch/Unwatch
- [ ] Obtener watchers
- [ ] Adjuntos (listar, crear, modificar, eliminar)

#### Issues
- [ ] Obtener por referencia
- [ ] Filtros avanzados (severity, priority, type)
- [ ] Filtros disponibles
- [ ] Upvote/Downvote + votantes
- [ ] Watch/Unwatch + watchers
- [ ] Adjuntos completos

#### Epics
- [ ] Obtener por referencia
- [ ] Modificar relaciones epic-userstory
- [ ] Bulk create relaciones
- [ ] Filtros disponibles
- [ ] Upvote/Downvote + votantes
- [ ] Watch/Unwatch + watchers
- [ ] Adjuntos completos

#### Tasks
- [ ] Obtener por referencia
- [ ] Filtros avanzados
- [ ] Filtros disponibles
- [ ] Upvote/Downvote + votantes
- [ ] Watch/Unwatch + watchers
- [ ] Adjuntos completos

#### Milestones
- [ ] Watch/Unwatch
- [ ] Obtener watchers

#### History/Comentarios (NO IMPLEMENTADO)
- [ ] Obtener historial (userstory, issue, task, wiki)
- [ ] Obtener versiones de comentario
- [ ] Editar comentario
- [ ] Eliminar comentario
- [ ] Restaurar comentario

#### Atributos Personalizados (NO IMPLEMENTADO)
- [ ] CRUD para userstory custom attributes
- [ ] CRUD para issue custom attributes
- [ ] CRUD para task custom attributes
- [ ] CRUD para epic custom attributes

## Plan de Implementación por Fases

### Fase 1: Completar CRUD Básico (Prioridad ALTA)
1. Añadir "get by ref" para todas las entidades
2. Implementar filtros avanzados
3. Añadir watch/unwatch para todas las entidades

### Fase 2: Funcionalidades Sociales (Prioridad MEDIA)
1. Upvote/Downvote + votantes
2. Watchers/Voters queries
3. Like/Unlike proyectos

### Fase 3: History y Comentarios (Prioridad MEDIA)
1. Obtener historial de cambios
2. CRUD de comentarios
3. Versiones de comentarios

### Fase 4: Adjuntos (Prioridad MEDIA-ALTA)
1. CRUD completo de adjuntos para todas las entidades
2. Upload/Download de archivos

### Fase 5: Atributos Personalizados (Prioridad BAJA)
1. CRUD de definiciones de atributos
2. Valores de atributos personalizados

### Fase 6: Funcionalidades Avanzadas (Prioridad BAJA)
1. Duplicar proyectos
2. Bulk operations avanzadas
3. Gestión de tags

## Entidades de Dominio Requeridas

1. **Project** (Aggregate Root)
   - Value Objects: ModulesConfig, ProjectStats
   - Entities: Tag

2. **UserStory** (Aggregate Root)
   - Value Objects: Points (map de role → points), StoryPoints
   - Behaviors: Vote, Watch, Attach

3. **Issue** (Aggregate Root)
   - Value Objects: Severity, Priority, IssueType
   - Behaviors: Vote, Watch, Attach

4. **Epic** (Aggregate Root)
   - Value Objects: EpicColor
   - Entities: EpicUserStoryRelation
   - Behaviors: Vote, Watch, Attach

5. **Task** (Entity bajo UserStory)
   - Value Objects: TaskStatus
   - Behaviors: Vote, Watch, Attach

6. **Milestone** (Aggregate Root)
   - Value Objects: MilestoneStats, BurndownData
   - Behaviors: Watch

7. **Attachment** (Value Object compartido)
   - Properties: file, description, owner, created_at

8. **HistoryEntry** (Value Object)
   - Properties: action, diff, comment, user, timestamp

9. **CustomAttribute** (Entity)
   - Value Objects: AttributeType (text, number, date, checkbox, etc.)

10. **User/Membership** (Aggregate Root)
    - Value Objects: Role, Permissions

## Casos de Uso Requeridos (por capa de aplicación)

### Proyectos (21 casos de uso)
- ListProjects
- GetProject, GetProjectBySlug
- CreateProject, UpdateProject, DeleteProject
- GetProjectStats, GetProjectIssuesStats
- ManageProjectModules
- ManageProjectTags (Create, Edit, Delete, Mix)
- LikeProject, UnlikeProject
- WatchProject, UnwatchProject
- DuplicateProject
- BulkUpdateProjectsOrder

### User Stories (24+ casos de uso)
- ListUserStories (con filtros avanzados)
- GetUserStory, GetUserStoryByRef
- CreateUserStory, UpdateUserStory, DeleteUserStory
- BulkCreateUserStories
- BulkUpdateBacklogOrder, BulkUpdateKanbanOrder, BulkUpdateSprintOrder
- BulkUpdateMilestone
- GetFiltersData
- UpvoteUserStory, DownvoteUserStory, GetVoters
- WatchUserStory, UnwatchUserStory, GetWatchers
- ManageAttachments (List, Create, Get, Update, Delete)

### Issues (20+ casos de uso)
- Similar a User Stories pero con filtros específicos (severity, priority, type)

### Epics (27+ casos de uso)
- CRUD básico + por referencia
- Gestión de relaciones epic-userstory
- BulkCreateRelations
- Voting, Watching, Attachments

### Tasks (20+ casos de uso)
- CRUD básico + filtros
- Voting, Watching, Attachments

### Milestones (10 casos de uso)
- CRUD básico
- GetStats (con burndown data)
- Watching

### History (20 casos de uso)
- GetHistory (por entidad)
- ManageComments (Edit, Delete, Undelete, GetVersions)

### Custom Attributes (24+ casos de uso)
- CRUD por cada tipo de entidad (userstory, issue, task, epic)

## Arquitectura de Repositorios

```
IProjectRepository
IUserStoryRepository  
IIssueRepository
IEpicRepository
ITaskRepository
IMilestoneRepository
IHistoryRepository
ICustomAttributeRepository
IAttachmentRepository
IUserRepository
IMembershipRepository
```

## Próximos Pasos

1. Completar entidades de dominio con todos los behaviors
2. Implementar casos de uso faltantes siguiendo TDD
3. Actualizar TaigaClient en capa de infraestructura
4. Refactorizar servidor MCP para exponer todas las herramientas
5. Crear tests de integración end-to-end
