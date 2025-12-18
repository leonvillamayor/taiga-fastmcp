# Taiga MCP Server

> Model Context Protocol (MCP) Server for Taiga Project Management Platform

[![Version](https://img.shields.io/badge/version-0.3.2-blue.svg)](https://github.com/leonvillamayor/taiga-fastmcp/releases)
[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/leonvillamayor/taiga-fastmcp/actions/workflows/tests.yml/badge.svg)](https://github.com/leonvillamayor/taiga-fastmcp/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/leonvillamayor/taiga-fastmcp/graph/badge.svg)](https://codecov.io/gh/leonvillamayor/taiga-fastmcp)
[![FastMCP](https://img.shields.io/badge/fastmcp-latest-brightgreen.svg)](https://github.com/jlowin/fastmcp)

## Description

**Taiga MCP Server** is a Model Context Protocol server that provides full programmatic access to the Taiga API. Built with FastMCP, it exposes **200+ MCP tools** to manage projects, epics, user stories, issues, tasks, sprints, wikis and more.

### What's New in v0.3.x

- **Middleware Stack**: Rate limiting, error handling, timing and structured logging
- **Tool Annotations**: `readOnlyHint`, `destructiveHint`, `idempotentHint` for each tool
- **Smart Caching**: Authentication token caching with auto-refresh
- **3100+ tests** with **88%+ coverage**

### Available MCP Tools

| Module | Tools | Description |
|--------|-------|-------------|
| **Auth** | 5 | Login, logout, refresh token, status, verification |
| **Cache** | 4 | Statistics, cleanup, invalidation |
| **Projects** | 22 | CRUD, statistics, modules, tags, likes, watchers |
| **User Stories** | 20 | CRUD, bulk ops, filters, votes, watchers |
| **Epics** | 35 | Full epic management and US relationships |
| **Issues** | 31 | CRUD, filters, comments, votes, attachments |
| **Tasks** | 25 | Task management, attachments, comments |
| **Milestones** | 11 | Sprints, statistics, watchers |
| **Wiki** | 12 | Wiki pages, links, attachments |
| **Webhooks** | 6 | Webhook configuration and testing |
| **Memberships** | 5 | Project members |
| **Settings** | 40+ | Points, statuses, priorities, severities, types, roles |

## Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (package manager)
- Docker and Docker Compose (for HTTP transport)
- Taiga account with access credentials

## Installation

```bash
# Clone repository
git clone https://github.com/leonvillamayor/taiga-fastmcp.git
cd taiga-fastmcp

# Install dependencies with uv
uv sync
```

## Configuration

Copy the example file and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Taiga credentials:

```env
# Taiga API (REQUIRED)
TAIGA_API_URL=https://api.taiga.io/api/v1
TAIGA_USERNAME=your_user@email.com
TAIGA_PASSWORD=your_password

# Alternative: use authentication token
# TAIGA_AUTH_TOKEN=your_token_here

# MCP Server
MCP_SERVER_NAME=Taiga MCP Server
MCP_TRANSPORT=stdio
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_DEBUG=false

# Request settings
TAIGA_TIMEOUT=30
TAIGA_MAX_RETRIES=3

# Cache (v0.3.0+)
TAIGA_CACHE_ENABLED=true
TAIGA_CACHE_TTL=3600
TAIGA_CACHE_MAX_SIZE=1000

# Middleware (v0.3.0+)
TAIGA_ENABLE_MIDDLEWARE=true
TAIGA_RATE_LIMIT_RPS=50
TAIGA_ENV=production
```

---

## Running the MCP Server

### Option 1: STDIO Transport (Local)

STDIO transport is ideal for integration with local MCP clients like Claude Desktop.

```bash
# Run server with stdio transport
uv run python -m src.server
```

#### Claude Desktop Configuration

Add this configuration to your Claude Desktop configuration file (`~/.config/claude/settings.json` or equivalent):

```json
{
  "mcpServers": {
    "taiga": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.server"],
      "cwd": "/path/to/taiga-fastmcp",
      "env": {
        "TAIGA_API_URL": "https://api.taiga.io/api/v1",
        "TAIGA_USERNAME": "your_user@email.com",
        "TAIGA_PASSWORD": "your_password",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

---

### Option 2: HTTP Transport (Docker)

HTTP transport allows running the server as a network service, ideal for remote integrations or microservices.

#### Quick Start

```bash
# 1. Configure credentials
cp .env.example .env
nano .env  # Edit with your credentials

# 2. Run server
docker compose up
```

The server will be available at `http://localhost:8000`

#### Available Profiles

| Command | Profile | Description |
|---------|---------|-------------|
| `docker compose up` | Default | 512MB RAM, 1 CPU |
| `docker compose --profile dev up` | Development | Debug enabled, source mounted, cache TTL 5min |
| `docker compose --profile prod up -d` | Production | 1GB RAM, 2 CPU, cache TTL 2h, restart policy |

#### Check Status

```bash
# Health check
curl http://localhost:8000/mcp

# View logs
docker compose logs -f taiga-mcp-server
```

#### Stop Server

```bash
# Stop
docker compose down

# Stop and remove volumes
docker compose down -v
```

---

## Architecture

The project follows a **Domain-Driven Design (DDD)** architecture:

```
src/
├── domain/                    # Pure business logic
│   ├── entities/              # Domain entities
│   ├── repositories/          # Interfaces (ABC)
│   └── exceptions.py          # Domain exceptions
├── application/               # Application layer
│   ├── tools/                 # MCP tools (200+)
│   │   ├── auth_tools.py
│   │   ├── cache_tools.py
│   │   ├── epic_tools.py
│   │   ├── issue_tools.py
│   │   ├── membership_tools.py
│   │   ├── milestone_tools.py
│   │   ├── project_tools.py
│   │   ├── settings_tools.py
│   │   ├── task_tools.py
│   │   ├── userstory_tools.py
│   │   ├── webhook_tools.py
│   │   └── wiki_tools.py
│   └── use_cases/             # Use cases
├── infrastructure/            # Technical implementation
│   ├── cache.py               # In-memory cache system
│   ├── cached_client.py       # Cached client
│   ├── client_factory.py      # Client factory
│   ├── container.py           # Dependency injection
│   ├── middleware.py          # Middleware stack
│   ├── repositories/          # Implementations
│   └── logging.py             # Structured logging
├── config.py                  # Configuration
├── server.py                  # Main MCP server
└── taiga_client.py            # HTTP client for Taiga
```

## Testing

```bash
# Unit tests
uv run pytest tests/unit/ -v

# Integration tests (requires real credentials)
uv run pytest tests/integration/ -v

# Performance tests
uv run pytest tests/performance/ -v

# Tests with coverage
uv run pytest --cov=src --cov-report=html

# All tests
uv run pytest
```

**Current status**: 3100+ tests with 88%+ coverage.

## CI/CD

The project uses GitHub Actions for CI:

| Job | Description |
|-----|-------------|
| **Linting** | Style verification with ruff |
| **Type Checking** | Type checking with mypy |
| **Unit Tests** | Unit tests with coverage |
| **Integration Tests** | Integration tests |
| **Performance Tests** | Performance tests |
| **Security Scan** | Security scan with bandit |

## License

This project is licensed under the GNU General Public License v3.0 - see [LICENSE](LICENSE) for details.

## Author

**Javier Leon** - [javier@leonvillamayor.org](mailto:javier@leonvillamayor.org)
