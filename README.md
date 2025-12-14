# Taiga MCP Server

> Servidor Model Context Protocol (MCP) para Taiga Project Management Platform

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/leonvillamayor/taiga-fastmcp/actions/workflows/tests.yml/badge.svg)](https://github.com/leonvillamayor/taiga-fastmcp/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/leonvillamayor/taiga-fastmcp/graph/badge.svg)](https://codecov.io/gh/leonvillamayor/taiga-fastmcp)
[![FastMCP](https://img.shields.io/badge/fastmcp-latest-brightgreen.svg)](https://github.com/jlowin/fastmcp)

## Descripcion

**Taiga MCP Server** es un servidor Model Context Protocol que proporciona acceso programatico completo a la API de Taiga. Implementado con FastMCP, expone +150 herramientas MCP para gestionar proyectos, epicas, user stories, issues, tareas, sprints, wikis y mas.

### Herramientas MCP Disponibles

| Modulo | Herramientas | Descripcion |
|--------|--------------|-------------|
| **Auth** | 4 | Login, logout, refresh token, estado |
| **Projects** | 6 | CRUD, estadisticas, modulos |
| **User Stories** | 37 | CRUD, bulk ops, filtros, attachments |
| **Epics** | 28 | Gestion de epicas y relaciones |
| **Issues** | 35 | CRUD, filtros, comentarios, votos |
| **Tasks** | 8 | Gestion de tareas |
| **Milestones** | 10 | Sprints, estadisticas |
| **Wiki** | 10 | Paginas wiki |
| **Webhooks** | 7 | Configuracion de webhooks |
| **Memberships** | 6 | Miembros del proyecto |

## Requisitos

- Python 3.11+
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
| `docker compose --profile dev up` | Development | Debug habilitado, source mounted |
| `docker compose --profile prod up -d` | Production | 1GB RAM, 2 CPU, restart policy |

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

```
src/
├── domain/                    # Logica de negocio pura
│   ├── entities/              # Entidades de dominio
│   ├── repositories/          # Interfaces (ABC)
│   └── exceptions.py          # Excepciones del dominio
├── application/               # Capa de aplicacion
│   ├── tools/                 # Herramientas MCP
│   └── use_cases/             # Casos de uso
├── infrastructure/            # Implementacion tecnica
│   ├── repositories/          # Implementaciones
│   └── config.py              # Configuracion
├── server.py                  # Servidor MCP principal
└── taiga_client.py            # Cliente HTTP para Taiga
```

## Testing

```bash
# Tests unitarios
uv run pytest tests/unit/ -v

# Tests de integracion (requiere credenciales reales)
uv run pytest tests/integration/ -v

# Tests con cobertura
uv run pytest --cov=src --cov-report=html

# Todos los tests
uv run pytest
```

## CI/CD

El proyecto usa GitHub Actions para CI:

| Job | Descripcion |
|-----|-------------|
| **lint** | Verificacion de estilo con ruff |
| **type-check** | Verificacion de tipos con mypy |
| **test** | Tests unitarios con cobertura |
| **integration** | Tests de integracion |
| **performance** | Tests de rendimiento |
| **security** | Escaneo con bandit |

## Licencia

Este proyecto esta licenciado bajo la GNU General Public License v3.0 - ver [LICENSE](LICENSE) para detalles.

## Autor

**Javier León** - [javier@leonvillamayor.org](mailto:javier@leonvillamayor.org)
