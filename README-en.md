# Taiga MCP Server

> Model Context Protocol (MCP) Server for Taiga Project Management Platform

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/leonvillamayor/taiga-fastmcp/actions/workflows/tests.yml/badge.svg)](https://github.com/leonvillamayor/taiga-fastmcp/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/leonvillamayor/taiga-fastmcp/graph/badge.svg)](https://codecov.io/gh/leonvillamayor/taiga-fastmcp)
[![FastMCP](https://img.shields.io/badge/fastmcp-latest-brightgreen.svg)](https://github.com/jlowin/fastmcp)

## Description

**Taiga MCP Server** is a Model Context Protocol server that provides full programmatic access to the Taiga API. Built with FastMCP, it exposes 150+ MCP tools to manage projects, epics, user stories, issues, tasks, sprints, wikis and more.

### Available MCP Tools

| Module | Tools | Description |
|--------|-------|-------------|
| **Auth** | 4 | Login, logout, refresh token, status |
| **Projects** | 6 | CRUD, statistics, modules |
| **User Stories** | 37 | CRUD, bulk ops, filters, attachments |
| **Epics** | 28 | Epic management and relationships |
| **Issues** | 35 | CRUD, filters, comments, votes |
| **Tasks** | 8 | Task management |
| **Milestones** | 10 | Sprints, statistics |
| **Wiki** | 10 | Wiki pages |
| **Webhooks** | 7 | Webhook configuration |
| **Memberships** | 6 | Project members |

## Requirements

- Python 3.11+
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
| `docker compose --profile dev up` | Development | Debug enabled, source mounted |
| `docker compose --profile prod up -d` | Production | 1GB RAM, 2 CPU, restart policy |

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

```
src/
├── domain/                    # Pure business logic
│   ├── entities/              # Domain entities
│   ├── repositories/          # Interfaces (ABC)
│   └── exceptions.py          # Domain exceptions
├── application/               # Application layer
│   ├── tools/                 # MCP tools
│   └── use_cases/             # Use cases
├── infrastructure/            # Technical implementation
│   ├── repositories/          # Implementations
│   └── config.py              # Configuration
├── server.py                  # Main MCP server
└── taiga_client.py            # HTTP client for Taiga
```

## Testing

```bash
# Unit tests
uv run pytest tests/unit/ -v

# Integration tests (requires real credentials)
uv run pytest tests/integration/ -v

# Tests with coverage
uv run pytest --cov=src --cov-report=html

# All tests
uv run pytest
```

## CI/CD

The project uses GitHub Actions for CI:

| Job | Description |
|-----|-------------|
| **lint** | Style verification with ruff |
| **type-check** | Type checking with mypy |
| **test** | Unit tests with coverage |
| **integration** | Integration tests |
| **performance** | Performance tests |
| **security** | Security scan with bandit |

## License

This project is licensed under the GNU General Public License v3.0 - see [LICENSE](LICENSE) for details.
