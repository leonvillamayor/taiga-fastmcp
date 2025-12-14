# Servidor MCP de Taiga - Documentación Completa

## Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Requisitos](#requisitos)
4. [Instalación](#instalación)
5. [Configuración](#configuración)
6. [Generación del Servidor](#generación-del-servidor)
7. [Inicio del Servidor](#inicio-del-servidor)
8. [Detención del Servidor](#detención-del-servidor)
9. [Herramientas Disponibles](#herramientas-disponibles)
10. [Uso de las Herramientas](#uso-de-las-herramientas)
11. [Testing](#testing)
12. [Troubleshooting](#troubleshooting)

---

## Descripción General

El **Servidor MCP de Taiga** es un servidor que implementa el Protocolo de Contexto de Modelo (MCP) utilizando el framework FastMCP. Este servidor expone 34 herramientas que permiten interactuar con la API de Taiga para gestionar proyectos ágiles completos.

### Características Principales

- **34 herramientas MCP** para operaciones CRUD completas en Taiga
- **Soporte dual de transporte**: stdio (para Claude Desktop/Code) y HTTP (para clientes web)
- **Cliente asíncrono** optimizado para la API de Taiga
- **Autenticación segura** mediante tokens Bearer
- **Configuración mediante variables de entorno**
- **Tests completos** con pytest
- **Gestión completa** de proyectos, user stories, issues, épicas, tasks y milestones

---

## Arquitectura

### Componentes del Sistema

```
taiga_mcp_server/
├── src/
│   ├── server.py              # Servidor MCP principal
│   ├── server_tools_part1.py  # Herramientas de proyectos, US, issues
│   ├── server_tools_part2.py  # Herramientas de épicas, tasks, milestones
│   └── taiga_client.py        # Cliente asíncrono de Taiga API
├── tests/
│   └── test_server.py         # Suite de tests
├── .env                       # Configuración de credenciales
├── requirements.txt           # Dependencias Python
└── README.md
```

### Flujo de Datos

```
Cliente MCP (Claude) → Protocolo MCP → Servidor MCP → Taiga API
                                ↓
                        Herramientas (@mcp.tool)
                                ↓
                        TaigaClient (async)
                                ↓
                        API REST de Taiga
```

---

## Requisitos

### Sistema Operativo
- Linux, macOS o Windows
- Python 3.10 o superior

### Dependencias Python
```
fastmcp>=2.13.0
requests>=2.31.0
pydantic>=2.0.0
python-dotenv>=1.0.0
aiohttp>=3.9.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

### Cuenta Taiga
- Cuenta activa en [Taiga.io](https://taiga.io) o instancia self-hosted
- Credenciales de acceso (usuario y contraseña)

---

## Instalación

### 1. Clonar o Descargar el Proyecto

```bash
cd /ruta/a/tu/proyecto
cd taiga_mcp_server
```

### 2. Crear Entorno Virtual

```bash
# Crear el entorno virtual
python3 -m venv venv

# Activar el entorno virtual
# En Linux/macOS:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

---

## Configuración

### Variables de Entorno

Crear o editar el archivo `.env` en el directorio raíz del proyecto:

```bash
# Taiga API Configuration
TAIGA_API_URL=https://api.taiga.io/api/v1
TAIGA_USERNAME=tu_usuario@ejemplo.com
TAIGA_PASSWORD=tu_contraseña

# MCP Server Configuration
MCP_SERVER_NAME=Taiga MCP Server
MCP_TRANSPORT=stdio
MCP_HOST=127.0.0.1
MCP_PORT=8000
```

### Parámetros de Configuración

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `TAIGA_API_URL` | URL base de la API de Taiga | `https://api.taiga.io/api/v1` |
| `TAIGA_USERNAME` | Usuario de Taiga | **Requerido** |
| `TAIGA_PASSWORD` | Contraseña de Taiga | **Requerido** |
| `MCP_SERVER_NAME` | Nombre del servidor MCP | `Taiga MCP Server` |
| `MCP_TRANSPORT` | Protocolo de transporte | `stdio` |
| `MCP_HOST` | Host para transporte HTTP | `127.0.0.1` |
| `MCP_PORT` | Puerto para transporte HTTP | `8000` |

---

## Generación del Servidor

El servidor ya está generado y listo para usar. Los archivos principales son:

### `server.py` - Servidor Principal

```python
from fastmcp import FastMCP, Context
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Crear instancia del servidor MCP
mcp = FastMCP(
    name=os.getenv("MCP_SERVER_NAME", "Taiga MCP Server"),
    version="1.0.0"
)

# Las herramientas se definen con el decorador @mcp.tool
@mcp.tool
async def list_projects(ctx: Context) -> List[Dict[str, Any]]:
    """List all projects accessible to the authenticated user."""
    # Implementación...
```

### `taiga_client.py` - Cliente Asíncrono

```python
class TaigaClient:
    """Cliente asíncrono para la API de Taiga."""

    async def __aenter__(self):
        """Iniciar sesión asíncrona."""
        self.session = aiohttp.ClientSession()
        await self.authenticate()
        return self

    async def authenticate(self) -> Dict[str, Any]:
        """Autenticar con Taiga y obtener token."""
        # Implementación...
```

---

## Inicio del Servidor

### Modo 1: STDIO (Para Claude Desktop/Code)

Este es el modo recomendado para usar con Claude Desktop o Claude Code.

```bash
# Activar entorno virtual
source venv/bin/activate

# Iniciar servidor en modo stdio
python server.py
```

O especificar explícitamente el transporte:

```bash
python server.py --transport stdio
```

El servidor quedará escuchando en stdin/stdout para comunicarse con Claude.

### Modo 2: HTTP/SSE (Para Clientes Web)

Para usar el servidor con clientes web o aplicaciones personalizadas:

```bash
# Activar entorno virtual
source venv/bin/activate

# Iniciar servidor en modo HTTP
python server.py --transport http --host 127.0.0.1 --port 8000
```

El servidor estará disponible en: `http://127.0.0.1:8000/mcp`

### Parámetros de Línea de Comandos

```bash
python server.py [OPTIONS]

Opciones:
  --transport {stdio,http}  Protocolo de transporte (default: stdio)
  --host HOST               Host para modo HTTP (default: 127.0.0.1)
  --port PORT               Puerto para modo HTTP (default: 8000)
  -h, --help                Mostrar ayuda
```

### Verificar que el Servidor Está Ejecutándose

#### Modo STDIO
El servidor no mostrará salida visible, está esperando comandos MCP en stdin.

#### Modo HTTP
Deberías ver:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## Detención del Servidor

### Modo STDIO
```bash
# Presionar Ctrl+C o enviar señal SIGTERM
Ctrl+C
```

### Modo HTTP
```bash
# Presionar Ctrl+C
Ctrl+C
```

El servidor cerrará correctamente todas las conexiones y sesiones HTTP activas.

---

## Herramientas Disponibles

El servidor expone **34 herramientas** organizadas en 6 categorías:

### 1. Proyectos (6 herramientas)

| Herramienta | Descripción |
|-------------|-------------|
| `list_projects` | Listar todos los proyectos del usuario |
| `get_project` | Obtener detalles de un proyecto por ID |
| `create_project` | Crear un nuevo proyecto |
| `update_project` | Actualizar un proyecto existente |
| `delete_project` | Eliminar un proyecto |
| `get_project_stats` | Obtener estadísticas de un proyecto |

### 2. User Stories (5 herramientas)

| Herramienta | Descripción |
|-------------|-------------|
| `list_user_stories` | Listar user stories con filtros |
| `get_user_story` | Obtener una user story por ID |
| `create_user_story` | Crear una nueva user story |
| `update_user_story` | Actualizar una user story |
| `delete_user_story` | Eliminar una user story |

### 3. Issues (5 herramientas)

| Herramienta | Descripción |
|-------------|-------------|
| `list_issues` | Listar issues con filtros |
| `get_issue` | Obtener un issue por ID |
| `create_issue` | Crear un nuevo issue |
| `update_issue` | Actualizar un issue |
| `delete_issue` | Eliminar un issue |

### 4. Épicas (7 herramientas)

| Herramienta | Descripción |
|-------------|-------------|
| `list_epics` | Listar épicas con filtros |
| `get_epic` | Obtener una épica por ID |
| `create_epic` | Crear una nueva épica |
| `update_epic` | Actualizar una épica |
| `delete_epic` | Eliminar una épica |
| `list_epic_user_stories` | Listar user stories de una épica |
| `relate_user_story_to_epic` | Relacionar user story con épica |

### 5. Tasks (5 herramientas)

| Herramienta | Descripción |
|-------------|-------------|
| `list_tasks` | Listar tasks con filtros |
| `get_task` | Obtener una task por ID |
| `create_task` | Crear una nueva task |
| `update_task` | Actualizar una task |
| `delete_task` | Eliminar una task |

### 6. Milestones/Sprints (6 herramientas)

| Herramienta | Descripción |
|-------------|-------------|
| `list_milestones` | Listar milestones/sprints |
| `get_milestone` | Obtener un milestone por ID |
| `create_milestone` | Crear un nuevo milestone |
| `update_milestone` | Actualizar un milestone |
| `delete_milestone` | Eliminar un milestone |
| `get_milestone_stats` | Obtener estadísticas de un milestone |

---

## Uso de las Herramientas

### Desde Claude Desktop/Code

Una vez configurado el servidor en Claude (ver [cliente_mcp_doc.md](cliente_mcp_doc.md)), puedes usar lenguaje natural:

```
"Lista todos mis proyectos de Taiga"
→ Usa: list_projects

"Crea una user story llamada 'Implementar login' en el proyecto 123"
→ Usa: create_user_story

"Muéstrame las estadísticas del sprint 456"
→ Usa: get_milestone_stats
```

### Ejemplo Programático (Python)

```python
from fastmcp import Client
import server

async def ejemplo():
    async with Client(server.mcp) as client:
        await client.initialize()

        # Listar proyectos
        result = await client.call_tool("list_projects", {})
        print(result.content[0].text)

        # Crear user story
        result = await client.call_tool("create_user_story", {
            "project_id": 123,
            "subject": "Implementar login",
            "description": "Como usuario quiero poder iniciar sesión"
        })
        print(result.content[0].text)
```

### Ejemplos de Uso por Herramienta

#### Listar Proyectos
```python
# Parámetros: ninguno
await client.call_tool("list_projects", {})
```

#### Crear Proyecto
```python
await client.call_tool("create_project", {
    "name": "Mi Nuevo Proyecto",
    "description": "Descripción del proyecto",
    "is_private": true
})
```

#### Crear User Story
```python
await client.call_tool("create_user_story", {
    "project_id": 123,
    "subject": "Login de usuario",
    "description": "Como usuario quiero iniciar sesión",
    "points": 5,
    "tags": ["authentication", "frontend"]
})
```

#### Filtrar Issues
```python
await client.call_tool("list_issues", {
    "project_id": 123,
    "status": 1,  # ID del estado
    "assigned_to": 456  # ID del usuario asignado
})
```

#### Crear Épica
```python
await client.call_tool("create_epic", {
    "project_id": 123,
    "subject": "Sistema de Autenticación",
    "description": "Épica para todas las tareas de autenticación"
})
```

#### Relacionar User Story con Épica
```python
await client.call_tool("relate_user_story_to_epic", {
    "epic_id": 789,
    "user_story_id": 101
})
```

---

## Testing

### Ejecutar Tests

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar todos los tests
pytest tests/test_server.py -v -s

# Ejecutar un test específico
pytest tests/test_server.py::test_authentication -v -s
```

### Tests Disponibles

1. **test_server_initialization**: Verifica que el servidor se inicializa correctamente
2. **test_list_tools**: Verifica que las 34 herramientas están expuestas
3. **test_list_projects_tool**: Verifica que list_projects funciona
4. **test_tool_descriptions**: Verifica que todas las herramientas tienen descripciones
5. **test_authentication**: Verifica que la autenticación con Taiga funciona

### Resultado Esperado

```
============================= test session starts ==============================
collected 5 items

tests/test_server.py::test_server_initialization PASSED
tests/test_server.py::test_list_tools PASSED
✓ Total de herramientas expuestas: 34
✓ Todas las herramientas necesarias están disponibles

tests/test_server.py::test_list_projects_tool PASSED
✓ list_projects ejecutado correctamente

tests/test_server.py::test_tool_descriptions PASSED
✓ Todas las herramientas tienen descripciones válidas

tests/test_server.py::test_authentication PASSED
✓ Autenticación exitosa
✓ Se encontraron 30 proyectos

============================== 5 passed in 1.32s ===============================
```

---

## Troubleshooting

### Problema: "Missing required environment variables"

**Error:**
```
ValueError: Missing required environment variables: TAIGA_API_URL, TAIGA_USERNAME, TAIGA_PASSWORD
```

**Solución:**
- Verifica que el archivo `.env` existe en el directorio raíz
- Verifica que las variables están correctamente configuradas
- Asegúrate de que no hay espacios extra alrededor de los valores

### Problema: "Authentication failed"

**Error:**
```
TaigaAPIError: Authentication failed: {"_error_message": "Invalid credentials"}
```

**Solución:**
- Verifica que el usuario y contraseña son correctos
- Verifica que la cuenta está activa en Taiga
- Prueba iniciar sesión manualmente en la web de Taiga

### Problema: "API request failed (404)"

**Error:**
```
TaigaAPIError: API request failed (404): Not Found
```

**Solución:**
- Verifica que el ID del proyecto/user story/issue existe
- Verifica que tienes permisos para acceder a ese recurso
- Usa `list_projects` para obtener IDs válidos

### Problema: "Network error during authentication"

**Error:**
```
TaigaAPIError: Network error during authentication: Cannot connect to host api.taiga.io
```

**Solución:**
- Verifica tu conexión a Internet
- Verifica que `TAIGA_API_URL` está correctamente configurada
- Si usas una instancia self-hosted, verifica que esté accesible

### Problema: Tests fallan

**Error:**
```
AttributeError: 'Tool' object has no attribute 'get'
```

**Solución:**
- Asegúrate de usar la versión correcta de fastmcp: `pip install --upgrade fastmcp>=2.13.0`
- Verifica que estás usando el entorno virtual: `source venv/bin/activate`

### Problema: Puerto ya en uso (modo HTTP)

**Error:**
```
OSError: [Errno 48] Address already in use
```

**Solución:**
- Usa un puerto diferente: `python server.py --transport http --port 8001`
- O detén el proceso que está usando el puerto 8000

### Logs y Debugging

Para habilitar logs detallados:

```python
# Agregar al inicio de server.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

Esto mostrará información detallada de todas las solicitudes HTTP y respuestas de la API de Taiga.

---

## Seguridad

### Recomendaciones

1. **Nunca** commitees el archivo `.env` a Git
2. **Nunca** compartas tus credenciales de Taiga
3. Usa contraseñas fuertes y únicas
4. Considera usar variables de entorno del sistema en lugar de `.env` en producción
5. En modo HTTP, usa HTTPS en producción
6. Implementa autenticación adicional si expones el servidor HTTP públicamente

### Archivo `.gitignore`

Asegúrate de incluir:
```
.env
venv/
__pycache__/
*.pyc
.pytest_cache/
```

---

## Recursos Adicionales

- [Documentación de FastMCP](../Documentacion/fastmcp.md)
- [Documentación de Taiga API](../Documentacion/taiga.md)
- [Configuración del Cliente MCP](../Documentacion/cliente_mcp_doc.md)
- [Taiga API Official Docs](https://docs.taiga.io/api.html)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)

---

## Soporte

Para problemas o preguntas:

1. Revisa esta documentación y el troubleshooting
2. Revisa los tests para ver ejemplos de uso
3. Consulta la documentación de FastMCP y Taiga API
4. Revisa los logs del servidor para más detalles

---

**Versión del Documento:** 1.0.0
**Última Actualización:** 2025-11-29
**Autor:** Generado con Claude Code
