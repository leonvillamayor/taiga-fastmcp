# Taiga MCP Server

> Servidor Model Context Protocol (MCP) para Taiga Project Management Platform

[![Version](https://img.shields.io/badge/version-0.3.2-blue.svg)](https://github.com/leonvillamayor/taiga-fastmcp/releases)
[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/leonvillamayor/taiga-fastmcp/actions/workflows/tests.yml/badge.svg)](https://github.com/leonvillamayor/taiga-fastmcp/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/leonvillamayor/taiga-fastmcp/graph/badge.svg)](https://codecov.io/gh/leonvillamayor/taiga-fastmcp)
[![FastMCP](https://img.shields.io/badge/fastmcp-latest-brightgreen.svg)](https://github.com/jlowin/fastmcp)

## Descripcion

**Taiga MCP Server** es un servidor Model Context Protocol que proporciona acceso programatico completo a la API de Taiga. Implementado con FastMCP, expone **+200 herramientas MCP** para gestionar proyectos, epicas, user stories, issues, tareas, sprints, wikis y mas.

### Novedades en v0.3.x

- **Middleware Stack**: Rate limiting, error handling, timing y structured logging
- **Tool Annotations**: `readOnlyHint`, `destructiveHint`, `idempotentHint` para cada herramienta
- **Cache Inteligente**: Cache de tokens de autenticacion con auto-refresh
- **+3100 tests** con **88%+ de cobertura**

### Herramientas MCP Disponibles

| Modulo | Herramientas | Descripcion |
|--------|--------------|-------------|
| **Auth** | 5 | Login, logout, refresh token, estado, verificacion |
| **Cache** | 4 | Estadisticas, limpieza, invalidacion |
| **Projects** | 22 | CRUD, estadisticas, modulos, tags, likes, watchers |
| **User Stories** | 20 | CRUD, bulk ops, filtros, votos, watchers |
| **Epics** | 35 | Gestion completa de epicas y relaciones con US |
| **Issues** | 31 | CRUD, filtros, comentarios, votos, attachments |
| **Tasks** | 25 | Gestion de tareas, attachments, comentarios |
| **Milestones** | 11 | Sprints, estadisticas, watchers |
| **Wiki** | 12 | Paginas wiki, links, attachments |
| **Webhooks** | 6 | Configuracion y testing de webhooks |
| **Memberships** | 5 | Miembros del proyecto |
| **Settings** | 40+ | Puntos, estados, prioridades, severidades, tipos, roles |

## Requisitos

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (gestor de paquetes)
- Docker y Docker Compose (para transporte HTTP)
- Cuenta en Taiga con credenciales de acceso

## Instalacion

```bash
# Clonar repositorio
git clone https://github.com/leonvillamayor/taiga-fastmcp.git
cd taiga-fastmcp

# Instalar dependencias con uv
uv sync
```

## Configuracion

Copia el archivo de ejemplo y configura tus credenciales:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales de Taiga:

```env
# Taiga API (REQUERIDO)
TAIGA_API_URL=https://api.taiga.io/api/v1
TAIGA_USERNAME=tu_usuario@email.com
TAIGA_PASSWORD=tu_password

# Alternativa: usar token de autenticacion
# TAIGA_AUTH_TOKEN=tu_token_aqui

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

## Ejecucion del Servidor MCP

### Opcion 1: Transporte STDIO (Local)

El transporte STDIO es ideal para integracion con clientes MCP locales como Claude Desktop.

```bash
# Ejecutar servidor con transporte stdio
uv run python -m src.server
```

#### Configuracion en Claude Desktop

Agrega esta configuracion en tu archivo de configuracion de Claude Desktop (`~/.config/claude/settings.json` o equivalente):

```json
{
  "mcpServers": {
    "taiga": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.server"],
      "cwd": "/ruta/a/taiga-fastmcp",
      "env": {
        "TAIGA_API_URL": "https://api.taiga.io/api/v1",
        "TAIGA_USERNAME": "tu_usuario@email.com",
        "TAIGA_PASSWORD": "tu_password",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

---

### Opcion 2: Transporte HTTP (Docker)

El transporte HTTP permite ejecutar el servidor como servicio de red, ideal para integraciones remotas o microservicios.

#### Inicio Rapido

```bash
# 1. Configurar credenciales
cp .env.example .env
nano .env  # Editar con tus credenciales

# 2. Ejecutar servidor
docker compose up
```

El servidor estara disponible en `http://localhost:8000`

#### Perfiles Disponibles

| Comando | Perfil | Descripcion |
|---------|--------|-------------|
| `docker compose up` | Default | 512MB RAM, 1 CPU |
| `docker compose --profile dev up` | Development | Debug habilitado, source mounted, cache TTL 5min |
| `docker compose --profile prod up -d` | Production | 1GB RAM, 2 CPU, cache TTL 2h, restart policy |

#### Verificar Estado

```bash
# Health check
curl http://localhost:8000/mcp

# Ver logs
docker compose logs -f taiga-mcp-server
```

#### Detener Servidor

```bash
# Detener
docker compose down

# Detener y eliminar volumenes
docker compose down -v
```

---

## Arquitectura

El proyecto sigue una arquitectura **Domain-Driven Design (DDD)**:

```
src/
├── domain/                    # Logica de negocio pura
│   ├── entities/              # Entidades de dominio
│   ├── repositories/          # Interfaces (ABC)
│   └── exceptions.py          # Excepciones del dominio
├── application/               # Capa de aplicacion
│   ├── tools/                 # Herramientas MCP (+200)
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
│   └── use_cases/             # Casos de uso
├── infrastructure/            # Implementacion tecnica
│   ├── cache.py               # Sistema de cache en memoria
│   ├── cached_client.py       # Cliente con cache
│   ├── client_factory.py      # Factory para clientes
│   ├── container.py           # Dependency injection
│   ├── middleware.py          # Middleware stack
│   ├── repositories/          # Implementaciones
│   └── logging.py             # Logging estructurado
├── config.py                  # Configuracion
├── server.py                  # Servidor MCP principal
└── taiga_client.py            # Cliente HTTP para Taiga
```

## Testing

```bash
# Tests unitarios
uv run pytest tests/unit/ -v

# Tests de integracion (requiere credenciales reales)
uv run pytest tests/integration/ -v

# Tests de rendimiento
uv run pytest tests/performance/ -v

# Tests con cobertura
uv run pytest --cov=src --cov-report=html

# Todos los tests
uv run pytest
```

**Estado actual**: +3100 tests con 88%+ de cobertura.

## CI/CD

El proyecto usa GitHub Actions para CI:

| Job | Descripcion |
|-----|-------------|
| **Linting** | Verificacion de estilo con ruff |
| **Type Checking** | Verificacion de tipos con mypy |
| **Unit Tests** | Tests unitarios con cobertura |
| **Integration Tests** | Tests de integracion |
| **Performance Tests** | Tests de rendimiento |
| **Security Scan** | Escaneo de seguridad con bandit |

## Licencia

Este proyecto esta licenciado bajo la GNU General Public License v3.0 - ver [LICENSE](LICENSE) para detalles.

## Autor

**Javier Leon** - [javier@leonvillamayor.org](mailto:javier@leonvillamayor.org)
