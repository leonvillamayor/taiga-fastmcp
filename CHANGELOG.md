# Changelog

All notable changes to the Taiga MCP Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-12-09

### Added
- **Validation Scripts**: Comprehensive Phase 2 validation tooling
  - `scripts/validate_phase2.py`: Full validation of interface normalization
  - `scripts/audit_mcp_tools.py`: MCP tools auditing with detailed reports
  - `scripts/check_json_dumps.py`: JSON serialization pattern detection
  - `scripts/check_docstrings.py`: Google-style docstring validation

### Changed
- **Tool Normalization (Phase 2 Complete)**:
  - All 164 MCP tools now use `taiga_` prefix consistently
  - Removed all `json.dumps` usage in tool returns (native Dict/List types)
  - Eliminated all parameter aliases for cleaner API
  - Complete Google-style docstrings with Args, Returns, Raises, and Example sections
  - Consistent return types (Dict/List[Dict]) across all tools

### Fixed
- Bandit B113: Added explicit timeout to all HTTP requests in `taiga_client.py`
- Removed backward compatibility parameter aliases in `epic_tools.py`
- Updated `validate_phase2.py` to use correct `create_server` import

### Quality Metrics
- **Tests**: 1313 passed, 78% coverage (exceeds 75% threshold)
- **Linting**: ruff passes 100%
- **Type Checking**: mypy passes 100% (148 source files)
- **Security**: bandit passes 100% (no issues)
- **Docstrings**: 100% complete for all MCP tools

## [0.2.0] - 2025-12-09

### Added

#### Domain Layer (DDD Architecture)
- **Entities**: Base entity class with ID management (`src/domain/entities/base.py`)
- **Domain Entities**: Epic, Issue, Member, Milestone, Project, Task, UserStory, WikiPage, Attachment, RelatedUserStory
- **Value Objects**: AuthToken, Email, ProjectSlug with validation
- **Repository Interfaces**: Abstract base repository and specific interfaces for all entities
- **Domain Exceptions**: Comprehensive exception hierarchy (DomainException, ValidationError, NotFoundError, AuthenticationError, etc.)

#### Infrastructure Layer
- **Repository Implementations**: Concrete implementations for all domain repositories
- **Dependency Injection**: ApplicationContainer using dependency-injector library
- **Configuration**: Enhanced ServerConfig and TaigaConfig classes

#### Application Layer
- **Use Cases**: Business logic encapsulation for Epic, Issue, Member, Milestone, Project, Task, UserStory, Wiki operations
- **Base Use Case**: Abstract base class for all use cases
- **MCP Tools**: Refactored tools using dependency injection

#### Code Quality
- **Pre-commit Hooks**: Configured with ruff, mypy, and bandit
- **Type Checking**: Strict mypy configuration for src/ (tests excluded to match pre-commit)
- **Linting**: Comprehensive ruff rules including flake8-bugbear, flake8-comprehensions, etc.
- **Test Coverage**: 77.35% overall coverage (Domain/Use Cases at 90%+)

### Changed
- Migrated from flat module structure to DDD layered architecture
- Tools now use dependency injection via ApplicationContainer
- Server initialization uses container-based wiring
- Removed legacy `src/tools/` directory (functionality moved to `src/application/tools/`)

### Fixed
- Added missing `TaigaError` exception alias for backward compatibility
- Added missing `create_server()` factory function in server.py
- Fixed type annotations in test files

### Technical Debt
- `taiga_client.py` excluded from coverage (low-level HTTP infrastructure)
- Coverage threshold set to 75% for Phase 1 (target: 80% in Phase 2)
- Tools layer (FastMCP wrappers) coverage to be improved in Phase 2

## [0.1.0] - 2025-11-30

### Added
- Initial release of Taiga MCP Server
- FastMCP integration for Model Context Protocol
- Basic Taiga API client implementation
- Authentication tools (login, logout, token refresh)
- Project management tools (CRUD operations)
- User Story tools (CRUD, bulk operations, attachments)
- Task tools (CRUD, bulk operations, custom attributes)
- Epic tools (CRUD, related user stories)
- Issue tools (CRUD, attachments, custom attributes)
- Milestone tools (CRUD, statistics, watchers)
- Wiki tools (pages, attachments)
- Webhook tools (CRUD, testing)
- Membership tools (CRUD, role management)
- User tools (profile, current user)
- STDIO and HTTP transport support
- pytest-based test suite

### Technical Details
- Python 3.11+ required
- Uses httpx for async HTTP client
- Pydantic for data validation
- pytest-asyncio for async testing
