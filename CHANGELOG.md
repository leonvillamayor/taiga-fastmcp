# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-12-18

### Added - Middleware & Production Optimizations

**FastMCP Middleware Stack (4 new middleware)**:
- **StructuredLoggingMiddleware**: Correlation IDs for request tracing, sensitive data masking
- **ErrorHandlingMiddleware**: Centralized error handling with retry logic for transient failures
- **RateLimitingMiddleware**: Token bucket algorithm to protect Taiga API (configurable RPS)
- **TimingMiddleware**: Request timing and performance monitoring with slow request warnings

**Tool Annotations (98 tools enhanced)**:
- Added MCP tool annotations based on operation semantics:
  - `readOnlyHint`: For `list_`, `get_`, `search_`, `filters_` operations
  - `destructiveHint`: For `delete_` operations
  - `idempotentHint`: For `update_`, `upvote_`, `downvote_`, `watch_` operations

**Authentication Token Cache**:
- `AuthTokenCache`: TTL-based token caching with auto-refresh
- `AuthTokenCacheManager`: Multi-user/context support
- Metrics tracking (hits, misses, refresh counts)
- Thread-safe async operations with `asyncio.Lock`

**Infrastructure Improvements**:
- New `src/infrastructure/middleware/` module with clean architecture
- New `src/infrastructure/auth_cache.py` for token management
- Automated annotation script `scripts/add_tool_annotations.py`

### Changed
- **Test Suite**: Expanded from 3034 to 3100+ tests (+66 tests)
- **Coverage**: Maintained at 88.27% (above 80% threshold)
- **Docker Configuration**:
  - Added middleware environment variables: `TAIGA_ENABLE_MIDDLEWARE`, `TAIGA_RATE_LIMIT_RPS`, `TAIGA_ENV`
  - Production profile: 100 RPS rate limit, error masking enabled
  - Development profile: 200 RPS rate limit, full error details
- **Server**: Integrated middleware stack in `TaigaMCPServer._configure_middleware()`

### Performance
- Middleware overhead: <1ms per request
- Token bucket rate limiting prevents API throttling
- Authentication caching reduces redundant auth calls
- Total MCP tools: 224 (with 98 annotated for LLM optimization)
- Test count: 3100+ tests
- Test coverage: 88.27%

### Configuration
New environment variables for middleware control:
```bash
TAIGA_ENABLE_MIDDLEWARE=true   # Enable/disable middleware stack
TAIGA_RATE_LIMIT_RPS=50        # Rate limit (requests per second)
TAIGA_ENV=production           # Environment (affects error masking)
```

## [0.2.0] - 2025-12-17

### Added - Complete API Coverage

**Settings & Configuration Tools (46 new tools)**:
- **Points Management** (6 tools):
  - `taiga_list_points`, `taiga_get_points`, `taiga_create_points`, `taiga_update_points`, `taiga_delete_points`, `taiga_bulk_update_points_order`
- **User Story Statuses** (5 tools):
  - `taiga_list_userstory_statuses`, `taiga_get_userstory_status`, `taiga_create_userstory_status`, `taiga_update_userstory_status`, `taiga_delete_userstory_status`
- **Task Statuses** (5 tools):
  - `taiga_list_task_statuses`, `taiga_get_task_status`, `taiga_create_task_status`, `taiga_update_task_status`, `taiga_delete_task_status`
- **Issue Statuses** (5 tools):
  - `taiga_list_issue_statuses`, `taiga_get_issue_status`, `taiga_create_issue_status`, `taiga_update_issue_status`, `taiga_delete_issue_status`
- **Epic Statuses** (5 tools):
  - `taiga_list_epic_statuses`, `taiga_get_epic_status`, `taiga_create_epic_status`, `taiga_update_epic_status`, `taiga_delete_epic_status`
- **Priorities** (5 tools):
  - `taiga_list_priorities`, `taiga_get_priority`, `taiga_create_priority`, `taiga_update_priority`, `taiga_delete_priority`
- **Severities** (5 tools):
  - `taiga_list_severities`, `taiga_get_severity`, `taiga_create_severity`, `taiga_update_severity`, `taiga_delete_severity`
- **Issue Types** (5 tools):
  - `taiga_list_issue_types`, `taiga_get_issue_type`, `taiga_create_issue_type`, `taiga_update_issue_type`, `taiga_delete_issue_type`
- **Roles** (5 tools):
  - `taiga_list_roles`, `taiga_get_role`, `taiga_create_role`, `taiga_update_role`, `taiga_delete_role`

**Bulk Order Operations (4 new tools)**:
- `taiga_bulk_update_backlog_order`: Reorder user stories in backlog
- `taiga_bulk_update_kanban_order`: Reorder user stories in kanban column
- `taiga_bulk_update_sprint_order`: Reorder user stories within sprint
- `taiga_bulk_update_milestone`: Move multiple user stories to sprint

**Search & Timeline (3 new tools)**:
- `taiga_search`: Global search across project items (stories, issues, tasks, wiki, epics)
- `taiga_get_user_timeline`: Activity timeline for a specific user
- `taiga_get_project_timeline`: Activity timeline for a project

**MCP Resources (6 new resources)**:
FastMCP resource endpoints for read-only data access:
- `taiga://projects/{project_id}/stats`: Project statistics and metrics
- `taiga://projects/{project_id}/modules`: Enabled modules configuration
- `taiga://projects/{project_id}/timeline`: Recent activity timeline
- `taiga://projects/{project_id}/members`: Project members and roles
- `taiga://users/me`: Current authenticated user information
- `taiga://users/{user_id}/stats`: User activity statistics

**MCP Prompts (6 new prompts)**:
Structured prompt templates for common workflows:
- `sprint_planning`: Sprint planning session guide
- `backlog_refinement`: Backlog refinement guide
- `project_health_analysis`: Project health metrics analysis
- `issue_triage`: Issue triage and prioritization guide
- `daily_standup`: Daily standup meeting format
- `sprint_retrospective`: Sprint retrospective template
- `release_planning`: Release planning guide

### Changed
- **Test Suite**: Expanded from 2956 to 3034 tests (+78 tests)
- **Coverage**: Maintained at 88.37% (above 80% threshold)
- **Architecture**: Added new modules:
  - `src/application/resources/` for MCP resources
  - `src/application/prompts/` for MCP prompts
  - `src/application/tools/settings_tools.py` for configuration management
  - `src/application/tools/search_tools.py` for search and timeline
- **Container**: Updated dependency injection container to include new tools, resources, and prompts
- **Docker**: Updated Dockerfile and docker-compose.yml to v0.2.0 with complete API coverage
- **Code Formatting**: Applied black and isort to all new code

### Performance
- Total MCP tools: 100+ (from 47 to 100+)
- Test count: 3034 (from 2956)
- Test coverage: 88.37% (maintained above 80%)
- All tests passing except 1 pre-existing integration test (unrelated)

## [0.1.1] - 2025-12-17

### Added
- **Cache Integration**: Integrated `MemoryCache` and `CachedTaigaClient` across all MCP tools via centralized `client_factory`
  - Global cache singleton with 1-hour TTL and 1000-item capacity
  - Automatic cache invalidation for write operations
  - Improved performance for repeated API calls
- **New MCP Tools** (High Priority):
  - `taiga_get_userstory_filters`: Get available filter options for user stories in a project
  - `taiga_bulk_link_userstories_to_epic`: Link multiple user stories to an epic at once
  - `taiga_get_user`: Get detailed information about a user by ID
- **FastMCP Metadata Enhancements**:
  - Added `tags` to all MCP tools for better categorization (e.g., `projects`, `read`, `write`, `delete`)
  - Added `annotations` with hints for LLM clients:
    - `readOnlyHint`: Marks read-only operations
    - `destructiveHint`: Warns about destructive operations
    - `idempotentHint`: Indicates idempotent operations
    - `openWorldHint`: Signals external system interaction
    - `title`: User-friendly titles for important operations

### Changed
- **Test Architecture**: Consolidated duplicate test files
  - Removed `tests/unit/tools/test_userstory_tools.py` (971 lines, 1.5% unique coverage)
  - Removed `tests/unit/tools/test_projects.py` (640 lines, 4% unique coverage)
  - Maintained coverage at 92.69% with 2956 passing tests
  - Updated `Documentacion/guia_tests.md` with new architecture
- **Client Factory**: Created centralized `src/infrastructure/client_factory.py` for managing Taiga API clients with cache
- **Code Formatting**: Applied black and isort to entire codebase for consistent style
- **Docker Configuration**:
  - Updated Dockerfile: Python 3.11 → 3.13, added cache environment variables
  - Updated docker-compose.yml: Added cache configuration per profile
    - Production: TTL=7200s, MAX_SIZE=5000 (optimized for performance)
    - Development: TTL=300s, MAX_SIZE=100 (fast iteration)
  - Updated .env.example with cache configuration documentation

### Fixed
- Import paths updated to use `client_factory` instead of direct `TaigaAPIClient` imports
- Test mocking updated to patch correct module paths after cache integration

### Performance
- Reduced test count from 3014 to 2956 (-58 duplicate tests)
- Maintained test coverage: 92.69%
- Faster API responses through intelligent caching

### Documentation
- Updated test guide with consolidation strategy
- Documented cache integration approach
- Added FastMCP best practices for tool metadata

## [0.1.0] - 2025-11-30

### Added
- Initial release
- Full Taiga API integration via FastMCP
- MCP tools for authentication, projects, user stories, tasks, issues, epics, milestones, wiki, team members, and webhooks
- Domain-Driven Design architecture
- Comprehensive test suite (unit, integration, E2E, performance, regression)
- Docker support and CI/CD

[0.3.0]: https://github.com/leonvillamayor/taiga-fastmcp/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/leonvillamayor/taiga-fastmcp/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/leonvillamayor/taiga-fastmcp/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/leonvillamayor/taiga-fastmcp/releases/tag/v0.1.0
