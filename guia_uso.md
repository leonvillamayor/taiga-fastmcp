# Guia de Uso Detallada - Taiga MCP Server

## Tabla de Contenidos

- [Introduccion](#introduccion)
- [Conceptos Clave](#conceptos-clave)
- [Instalacion y Configuracion](#instalacion-y-configuracion)
- [Casos de Uso](#casos-de-uso)
- [Ejemplos Practicos](#ejemplos-practicos)
- [Referencia de API](#referencia-de-api)
- [Solucion de Problemas](#solucion-de-problemas)
- [FAQ](#faq)

## Introduccion

### ¿Que hace este sistema?

**Taiga MCP Server** es un servidor que implementa el **Model Context Protocol (MCP)**, permitiendo que aplicaciones cliente (especialmente LLMs como Claude) interactuen con Taiga Project Management Platform de forma programatica y estructurada.

El servidor expone todas las operaciones de Taiga como **herramientas MCP**, que pueden ser invocadas por clientes MCP para:
- Autenticarse en Taiga
- Gestionar proyectos (crear, listar, actualizar, eliminar)
- Gestionar historias de usuario (CRUD, bulk operations, filtros)
- Consultar estadisticas y metricas
- Administrar watchers y votaciones

### ¿Para quien es este sistema?

Este sistema es ideal para:

1. **Desarrolladores** que quieren integrar Taiga con sus aplicaciones
2. **Equipos de proyecto** que usan Claude Desktop y quieren gestionar Taiga desde el chat
3. **Automatizadores** que necesitan operaciones programaticas sobre Taiga
4. **Integradores** que construyen pipelines de datos con Taiga
5. **DevOps** que quieren monitorear y reportar sobre proyectos Taiga

### ¿Que problemas resuelve?

El sistema resuelve varios problemas comunes:

1. **Acceso programatico a Taiga**: No necesitas aprender la API REST de Taiga, el servidor MCP abstrae toda la complejidad
2. **Integracion con LLMs**: Claude (y otros LLMs) pueden gestionar tu Taiga mediante lenguaje natural
3. **Automatizacion**: Crea scripts que interactuen con Taiga sin escribir codigo de bajo nivel
4. **Validacion automatica**: Todas las operaciones estan validadas con Pydantic
5. **Manejo de errores robusto**: Retry logic, rate limiting, autenticacion automatica

## Conceptos Clave

### Model Context Protocol (MCP)

**Definicion**: MCP es un protocolo estandar que permite a las aplicaciones exponer funcionalidades como "herramientas" que pueden ser invocadas por clientes (especialmente LLMs).

**Por que es importante**: Permite que Claude y otros LLMs ejecuten acciones reales en sistemas externos de forma estructurada y segura.

**Ejemplo**: En lugar de que Claude solo "simule" crear un proyecto, con MCP realmente lo crea en Taiga.

### FastMCP Framework

**Definicion**: FastMCP es un framework Python para crear servidores MCP de forma rapida y Pythonica usando decoradores.

**Por que es importante**: Simplifica enormemente el desarrollo de servidores MCP, con soporte async nativo y decoradores elegantes.

**Ejemplo**:
```python
@mcp.tool(name="authenticate", description="Authenticate with Taiga")
async def authenticate(username: str, password: str):
    # La funcion se registra automaticamente como herramienta MCP
    return await client.authenticate(username, password)
```

### Transporte STDIO vs HTTP

**Definicion**:
- **STDIO**: El servidor se comunica via entrada/salida estandar (stdin/stdout)
- **HTTP**: El servidor expone un endpoint HTTP que acepta peticiones MCP

**Por que es importante**:
- STDIO es ideal para Claude Desktop (un proceso por sesion)
- HTTP es ideal para servicios en red (multiples clientes simultaneos)

**Ejemplo de uso**:
```bash
# STDIO (default)
uv run python src/server.py

# HTTP
MCP_TRANSPORT=http uv run python src/server.py
```

### Herramientas MCP (Tools)

**Definicion**: Las herramientas son funciones que el servidor MCP expone al cliente. Cada herramienta tiene nombre, descripcion y parametros tipados.

**Por que es importante**: Es la forma estandarizada de exponer funcionalidad a LLMs y otros clientes MCP.

**Ejemplo**: La herramienta `authenticate` permite al cliente autenticarse en Taiga:
```json
{
  "name": "authenticate",
  "description": "Authenticate with Taiga using username and password",
  "parameters": {
    "username": "string",
    "password": "string"
  }
}
```

### Domain-Driven Design (DDD)

**Definicion**: Arquitectura que separa el codigo en capas: Domain (logica de negocio), Application (casos de uso), Infrastructure (detalles tecnicos).

**Por que es importante**: Mantiene el codigo organizado, testeable y facil de mantener.

**Ejemplo**:
- `TaigaAPIClient` (Infrastructure) solo sabe como hacer peticiones HTTP
- `AuthTools` (Application) orquesta la autenticacion
- `AuthenticationError` (Domain) modela errores de negocio

## Instalacion y Configuracion

### Paso 1: Preparar el Entorno

**Requisitos del Sistema**:
- Sistema Operativo: Linux, macOS o Windows
- Python: 3.11 o superior
- Memoria RAM: Minimo 4GB
- Disco: 500MB libres
- Conexion a internet (para acceder a Taiga API)

**Instalar Python 3.11+**:

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**macOS con Homebrew**:
```bash
brew install python@3.11
```

**Windows**:
```powershell
# Descargar instalador desde https://www.python.org/downloads/
# O usar Chocolatey
choco install python311
```

**Instalar uv (gestor de paquetes moderno)**:

**Linux/macOS**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell)**:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verifica la instalacion:
```bash
uv --version
# Deberia mostrar: uv 0.x.x
```

### Paso 2: Clonar e Instalar el Proyecto

```bash
# 1. Clonar repositorio (reemplaza con tu URL)
git clone https://github.com/tu-usuario/taiga_mcp_claude_code.git
cd taiga_mcp_claude_code

# 2. Instalar dependencias (uv crea automaticamente el venv)
uv sync

# 3. Verificar instalacion
uv run python --version
# Deberia mostrar: Python 3.11.x o superior

uv run pytest --version
# Deberia mostrar: pytest 8.x.x
```

**¿Que hace `uv sync`?**
- Crea un entorno virtual en `.venv/`
- Instala todas las dependencias del `pyproject.toml`
- Bloquea versiones en `uv.lock` para reproducibilidad

### Paso 3: Configuracion de Credenciales Taiga

**Crear cuenta en Taiga** (si no tienes una):
1. Ve a [https://taiga.io](https://taiga.io)
2. Registrate gratuitamente
3. Crea un proyecto de prueba
4. Anota tu email y contraseña

**Configurar archivo .env**:

1. Copia el archivo de ejemplo:
```bash
cp .env.example .env
```

2. Edita `.env` con tu editor favorito:
```bash
nano .env
# o
vim .env
# o
code .env  # VSCode
```

3. Completa las credenciales:
```bash
# === Taiga API Configuration ===
# Para Taiga Cloud (default)
TAIGA_API_URL=https://api.taiga.io/api/v1

# Para Taiga Self-Hosted, usa tu URL:
# TAIGA_API_URL=https://tu-servidor-taiga.com/api/v1

# Tus credenciales de Taiga
TAIGA_USERNAME=tu_email@example.com
TAIGA_PASSWORD=tu_contraseña_segura

# Opcional: Si ya tienes un token, puedes especificarlo
TAIGA_AUTH_TOKEN=

# === Configuracion de Timeouts (opcional) ===
TAIGA_TIMEOUT=30.0
TAIGA_AUTH_TIMEOUT=30.0
TAIGA_MAX_RETRIES=3
TAIGA_MAX_AUTH_RETRIES=3

# === MCP Server Configuration (opcional) ===
MCP_TRANSPORT=stdio  # o "http"
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_DEBUG=False
```

**IMPORTANTE**:
- Nunca compartas tu archivo `.env` (esta en `.gitignore`)
- Usa contraseñas seguras
- En produccion, usa variables de entorno del sistema en lugar de `.env`

### Paso 4: Verificar que Todo Funciona

**Ejecutar tests unitarios**:
```bash
uv run pytest tests/unit -v

# Salida esperada:
# =================== test session starts ===================
# tests/unit/test_server.py::test_server_initialization PASSED
# tests/unit/test_config.py::test_load_config PASSED
# ...
# =================== 277 passed in 5.23s ===================
```

**Ejecutar test de autenticacion real** (opcional):
```bash
# Esto requiere credenciales validas en .env
uv run pytest tests/integration/test_auth_integration.py -v

# Si falla con "Authentication failed", verifica:
# 1. TAIGA_API_URL esta correcto
# 2. TAIGA_USERNAME y TAIGA_PASSWORD son validos
# 3. Tienes conexion a internet
```

**Probar servidor manualmente**:
```bash
# Arrancar servidor en modo STDIO
uv run python src/server.py

# El servidor quedara esperando comandos MCP en stdin
# Presiona Ctrl+C para salir
```

Si todo funciona, estas listo para usar el servidor!

## Casos de Uso

### Caso de Uso 1: Autenticacion Basica

**Descripcion**: Autenticarse en Taiga para obtener un token de acceso

**Actores**: Usuario o aplicacion cliente

**Precondiciones**:
- Servidor MCP arrancado
- Credenciales validas en `.env` o proporcionadas manualmente

**Flujo Principal**:

1. Cliente invoca herramienta `authenticate`
2. Servidor envia credenciales a Taiga API
3. Taiga valida y retorna token de autenticacion
4. Servidor almacena token en memoria
5. Cliente recibe confirmacion con datos de usuario

**Postcondiciones**: Cliente tiene un `auth_token` valido para operaciones posteriores

**Ejemplo de Codigo**:

```python
#!/usr/bin/env python3
"""
Ejemplo: Autenticacion basica con Taiga
"""
import asyncio
import os
from dotenv import load_dotenv
from src.config import TaigaConfig
from src.taiga_client import TaigaAPIClient

async def main():
    # Cargar configuracion
    load_dotenv()
    config = TaigaConfig()

    # Crear cliente
    async with TaigaAPIClient(config) as client:
        # Autenticar
        result = await client.authenticate(
            username=config.taiga_username,
            password=config.taiga_password
        )

        print(f"✅ Autenticacion exitosa!")
        print(f"Usuario: {result['username']}")
        print(f"Email: {result['email']}")
        print(f"Token: {result['auth_token'][:20]}...")
        print(f"User ID: {result['id']}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Ejecutar**:
```bash
uv run python ejemplos/ejemplo_auth.py
```

**Salida Esperada**:
```
✅ Autenticacion exitosa!
Usuario: jleon
Email: jleon@example.com
Token: eyJ0eXAiOiJKV1QiLCJ...
User ID: 888691
```

### Caso de Uso 2: Listar Proyectos

**Descripcion**: Obtener lista de todos los proyectos accesibles

**Actores**: Usuario autenticado

**Precondiciones**: Token de autenticacion valido

**Flujo Principal**:

1. Cliente proporciona `auth_token`
2. Servidor consulta endpoint `/projects` de Taiga
3. Taiga retorna lista de proyectos
4. Servidor filtra y formatea datos
5. Cliente recibe lista simplificada

**Postcondiciones**: Cliente conoce proyectos disponibles con sus IDs

**Ejemplo de Codigo**:

```python
#!/usr/bin/env python3
"""
Ejemplo: Listar proyectos de Taiga
"""
import asyncio
from dotenv import load_dotenv
from src.config import TaigaConfig
from src.taiga_client import TaigaAPIClient

async def main():
    load_dotenv()
    config = TaigaConfig()

    async with TaigaAPIClient(config) as client:
        # Autenticar
        auth_result = await client.authenticate(
            username=config.taiga_username,
            password=config.taiga_password
        )
        token = auth_result['auth_token']

        # Listar proyectos
        client.auth_token = token
        projects = await client.list_projects()

        print(f"📋 Encontrados {len(projects)} proyectos:\n")

        for project in projects:
            print(f"ID: {project['id']}")
            print(f"Nombre: {project['name']}")
            print(f"Slug: {project['slug']}")
            print(f"Privado: {project['is_private']}")
            print(f"Story Points: {project.get('total_story_points', 0)}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
```

**Ejecutar**:
```bash
uv run python ejemplos/ejemplo_list_projects.py
```

**Salida Esperada**:
```
📋 Encontrados 3 proyectos:

ID: 309804
Nombre: Proyecto Demo
Slug: jleon-proyecto-demo
Privado: True
Story Points: 42
--------------------------------------------------
ID: 123456
Nombre: Otro Proyecto
Slug: otro-proyecto
Privado: False
Story Points: 0
--------------------------------------------------
```

### Caso de Uso 3: Crear User Story

**Descripcion**: Crear una nueva historia de usuario en un proyecto

**Actores**: Usuario autenticado con permisos en el proyecto

**Precondiciones**:
- Token de autenticacion valido
- ID de proyecto conocido

**Flujo Principal**:

1. Cliente proporciona datos de la historia (subject, description, etc.)
2. Servidor valida parametros
3. Servidor envia POST a `/userstories`
4. Taiga crea la historia y asigna ID
5. Cliente recibe datos de la historia creada

**Postcondiciones**: Nueva user story existe en Taiga

**Ejemplo de Codigo**:

```python
#!/usr/bin/env python3
"""
Ejemplo: Crear user story en Taiga
"""
import asyncio
from dotenv import load_dotenv
from src.config import TaigaConfig
from src.taiga_client import TaigaAPIClient

async def main():
    load_dotenv()
    config = TaigaConfig()

    async with TaigaAPIClient(config) as client:
        # Autenticar
        auth_result = await client.authenticate(
            username=config.taiga_username,
            password=config.taiga_password
        )
        client.auth_token = auth_result['auth_token']

        # Datos de la user story
        story_data = {
            "project": 309804,  # Reemplaza con tu project_id
            "subject": "Como usuario quiero autenticarme en el sistema",
            "description": "Implementar sistema de login con email y password",
            "tags": ["backend", "auth", "security"],
            "is_blocked": False
        }

        # Crear user story
        story = await client.create_userstory(story_data)

        print(f"✅ User Story creada exitosamente!")
        print(f"ID: {story['id']}")
        print(f"Ref: #{story['ref']}")
        print(f"Subject: {story['subject']}")
        print(f"Status: {story['status']}")
        print(f"Is Closed: {story['is_closed']}")
        print(f"Tags: {', '.join(story.get('tags', []))}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Ejecutar**:
```bash
uv run python ejemplos/ejemplo_create_userstory.py
```

**Salida Esperada**:
```
✅ User Story creada exitosamente!
ID: 7654321
Ref: #123
Subject: Como usuario quiero autenticarme en el sistema
Status: 1
Is Closed: False
Tags: backend, auth, security
```

### Caso de Uso 4: Buscar User Stories por Tags

**Descripcion**: Filtrar historias de usuario por etiquetas especificas

**Actores**: Usuario autenticado

**Precondiciones**:
- Token valido
- Proyecto con user stories etiquetadas

**Flujo Principal**:

1. Cliente especifica tags a buscar
2. Servidor construye query con filtros
3. Taiga retorna stories que coinciden
4. Cliente procesa resultados

**Postcondiciones**: Cliente tiene lista de stories filtradas

**Ejemplo de Codigo**:

```python
#!/usr/bin/env python3
"""
Ejemplo: Buscar user stories por tags
"""
import asyncio
from dotenv import load_dotenv
from src.config import TaigaConfig
from src.taiga_client import TaigaAPIClient

async def main():
    load_dotenv()
    config = TaigaConfig()

    async with TaigaAPIClient(config) as client:
        # Autenticar
        auth_result = await client.authenticate(
            username=config.taiga_username,
            password=config.taiga_password
        )
        client.auth_token = auth_result['auth_token']

        # Buscar por tags
        tags_to_search = ["backend", "auth"]
        stories = await client.list_userstories(
            project=309804,  # Tu project_id
            tags=tags_to_search
        )

        print(f"🔍 Encontradas {len(stories)} stories con tags {tags_to_search}:\n")

        for story in stories:
            print(f"#{story['ref']}: {story['subject']}")
            print(f"   Tags: {', '.join(story.get('tags', []))}")
            print(f"   Status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
            print()

if __name__ == "__main__":
    asyncio.run(main())
```

**Ejecutar**:
```bash
uv run python ejemplos/ejemplo_search_by_tags.py
```

**Salida Esperada**:
```
🔍 Encontradas 5 stories con tags ['backend', 'auth']:

#123: Como usuario quiero autenticarme en el sistema
   Tags: backend, auth, security
   Status: In Progress

#124: Como admin quiero gestionar usuarios
   Tags: backend, auth, admin
   Status: Ready for Dev

#125: Implementar JWT tokens
   Tags: backend, auth, api
   Status: Done
```

## Ejemplos Practicos

### Ejemplo 1: Script Completo de Gestion de Proyecto

**Contexto**: Quieres crear un script que automatice la creacion de un proyecto completo con user stories iniciales

**Objetivo**: Crear proyecto + crear 5 user stories + asignarlas a un sprint

**Codigo Completo**:

```python
#!/usr/bin/env python3
"""
Script completo: Crear proyecto con user stories iniciales

Este script demuestra como:
1. Autenticarse en Taiga
2. Crear un nuevo proyecto
3. Crear multiples user stories
4. Listar el resultado
"""
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv
from src.config import TaigaConfig
from src.taiga_client import TaigaAPIClient

async def create_project_with_stories():
    """Crear proyecto completo con user stories."""
    load_dotenv()
    config = TaigaConfig()

    async with TaigaAPIClient(config) as client:
        # Paso 1: Autenticar
        print("🔐 Autenticando...")
        auth_result = await client.authenticate(
            username=config.taiga_username,
            password=config.taiga_password
        )
        client.auth_token = auth_result['auth_token']
        print(f"✅ Autenticado como {auth_result['username']}\n")

        # Paso 2: Crear proyecto
        print("📁 Creando proyecto...")
        project_data = {
            "name": "Proyecto Automatizado",
            "description": "Proyecto creado mediante script automatico",
            "is_private": True,
            "is_backlog_activated": True,
            "is_kanban_activated": True,
            "tags": ["automatizado", "demo"]
        }
        project = await client.create_project(project_data)
        project_id = project['id']
        print(f"✅ Proyecto creado: {project['name']} (ID: {project_id})\n")

        # Paso 3: Crear user stories
        print("📝 Creando user stories...")
        stories_data = [
            {
                "subject": "Como usuario quiero registrarme",
                "description": "Formulario de registro con email y password",
                "tags": ["backend", "auth"]
            },
            {
                "subject": "Como usuario quiero login",
                "description": "Autenticacion con email y password",
                "tags": ["backend", "auth"]
            },
            {
                "subject": "Como usuario quiero recuperar contraseña",
                "description": "Enviar email con link de reset",
                "tags": ["backend", "auth", "email"]
            },
            {
                "subject": "Como usuario quiero ver mi perfil",
                "description": "Pagina de perfil con datos personales",
                "tags": ["frontend", "ui"]
            },
            {
                "subject": "Como usuario quiero editar mi perfil",
                "description": "Formulario para actualizar datos",
                "tags": ["frontend", "backend", "ui"]
            }
        ]

        created_stories = []
        for story_data in stories_data:
            story_data["project"] = project_id
            story = await client.create_userstory(story_data)
            created_stories.append(story)
            print(f"   ✅ #{story['ref']}: {story['subject']}")

        print(f"\n🎉 Creadas {len(created_stories)} user stories")

        # Paso 4: Resumen
        print("\n" + "="*60)
        print("RESUMEN DEL PROYECTO")
        print("="*60)
        print(f"Proyecto: {project['name']}")
        print(f"ID: {project_id}")
        print(f"Slug: {project['slug']}")
        print(f"\nUser Stories creadas:")
        for story in created_stories:
            tags_str = ", ".join(story.get('tags', []))
            print(f"  - #{story['ref']}: {story['subject']}")
            print(f"    Tags: {tags_str}")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(create_project_with_stories())
```

**Ejecutar el ejemplo**:
```bash
uv run python ejemplos/ejemplo_proyecto_completo.py
```

**Salida Esperada**:
```
🔐 Autenticando...
✅ Autenticado como jleon

📁 Creando proyecto...
✅ Proyecto creado: Proyecto Automatizado (ID: 310000)

📝 Creando user stories...
   ✅ #1: Como usuario quiero registrarme
   ✅ #2: Como usuario quiero login
   ✅ #3: Como usuario quiero recuperar contraseña
   ✅ #4: Como usuario quiero ver mi perfil
   ✅ #5: Como usuario quiero editar mi perfil

🎉 Creadas 5 user stories

============================================================
RESUMEN DEL PROYECTO
============================================================
Proyecto: Proyecto Automatizado
ID: 310000
Slug: jleon-proyecto-automatizado

User Stories creadas:
  - #1: Como usuario quiero registrarme
    Tags: backend, auth
  - #2: Como usuario quiero login
    Tags: backend, auth
  - #3: Como usuario quiero recuperar contraseña
    Tags: backend, auth, email
  - #4: Como usuario quiero ver mi perfil
    Tags: frontend, ui
  - #5: Como usuario quiero editar mi perfil
    Tags: frontend, backend, ui
============================================================
```

### Ejemplo 2: Reporte de Estadisticas de Proyecto

**Contexto**: Necesitas generar un reporte de estado de un proyecto

**Objetivo**: Obtener metricas y estadisticas para reportar

**Codigo Completo**:

```python
#!/usr/bin/env python3
"""
Ejemplo: Generar reporte de estadisticas de proyecto
"""
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from src.config import TaigaConfig
from src.taiga_client import TaigaAPIClient

async def generate_project_report(project_id: int):
    """Generar reporte completo de proyecto."""
    load_dotenv()
    config = TaigaConfig()

    async with TaigaAPIClient(config) as client:
        # Autenticar
        auth_result = await client.authenticate(
            username=config.taiga_username,
            password=config.taiga_password
        )
        client.auth_token = auth_result['auth_token']

        # Obtener datos del proyecto
        project = await client.get_project(project_id)
        stats = await client.get(f"/projects/{project_id}/stats")
        stories = await client.list_userstories(project=project_id)

        # Calcular metricas
        total_stories = len(stories)
        closed_stories = len([s for s in stories if s.get('is_closed')])
        blocked_stories = len([s for s in stories if s.get('is_blocked')])
        completion_rate = (closed_stories / total_stories * 100) if total_stories > 0 else 0

        # Generar reporte
        print("╔" + "="*78 + "╗")
        print(f"║ REPORTE DE PROYECTO - {datetime.now().strftime('%Y-%m-%d %H:%M')}".ljust(79) + "║")
        print("╠" + "="*78 + "╣")
        print(f"║ Proyecto: {project['name'][:60]}".ljust(79) + "║")
        print(f"║ ID: {project['id']}".ljust(79) + "║")
        print(f"║ Slug: {project['slug'][:60]}".ljust(79) + "║")
        print("╠" + "-"*78 + "╣")
        print(f"║ ESTADISTICAS GENERALES".ljust(79) + "║")
        print("╠" + "-"*78 + "╣")
        print(f"║ Total Milestones: {stats.get('total_milestones', 0)}".ljust(79) + "║")
        print(f"║ Total Story Points: {stats.get('total_points', 0)}".ljust(79) + "║")
        print(f"║ Story Points Cerrados: {stats.get('closed_points', 0)}".ljust(79) + "║")
        print(f"║ Total User Stories: {total_stories}".ljust(79) + "║")
        print(f"║ Stories Completadas: {closed_stories}".ljust(79) + "║")
        print(f"║ Stories Bloqueadas: {blocked_stories}".ljust(79) + "║")
        print(f"║ Tasa de Completitud: {completion_rate:.1f}%".ljust(79) + "║")
        print("╠" + "-"*78 + "╣")
        print(f"║ ISSUES".ljust(79) + "║")
        print("╠" + "-"*78 + "╣")
        print(f"║ Total Issues: {stats.get('total_issues', 0)}".ljust(79) + "║")
        print(f"║ Issues Abiertos: {stats.get('open_issues', 0)}".ljust(79) + "║")
        print(f"║ Issues Cerrados: {stats.get('closed_issues', 0)}".ljust(79) + "║")
        print("╠" + "-"*78 + "╣")
        print(f"║ ESTADO DEL PROYECTO".ljust(79) + "║")
        print("╠" + "-"*78 + "╣")

        # Determinar estado
        if completion_rate == 100:
            status = "✅ COMPLETADO"
            color = "green"
        elif completion_rate >= 75:
            status = "🟢 EN BUEN ESTADO"
            color = "green"
        elif completion_rate >= 50:
            status = "🟡 PROGRESO MODERADO"
            color = "yellow"
        elif completion_rate >= 25:
            status = "🟠 NECESITA ATENCION"
            color = "orange"
        else:
            status = "🔴 CRITICO"
            color = "red"

        if blocked_stories > 0:
            status += f" ({blocked_stories} bloqueadas)"

        print(f"║ {status}".ljust(79) + "║")
        print("╚" + "="*78 + "╝")

if __name__ == "__main__":
    # Reemplaza con tu project_id
    PROJECT_ID = 309804
    asyncio.run(generate_project_report(PROJECT_ID))
```

**Ejecutar**:
```bash
uv run python ejemplos/ejemplo_reporte.py
```

**Salida Esperada**:
```
╔==============================================================================╗
║ REPORTE DE PROYECTO - 2025-12-04 14:30                                      ║
╠==============================================================================╣
║ Proyecto: Proyecto Automatizado                                             ║
║ ID: 310000                                                                   ║
║ Slug: jleon-proyecto-automatizado                                           ║
╠------------------------------------------------------------------------------╣
║ ESTADISTICAS GENERALES                                                      ║
╠------------------------------------------------------------------------------╣
║ Total Milestones: 2                                                         ║
║ Total Story Points: 42                                                      ║
║ Story Points Cerrados: 28                                                   ║
║ Total User Stories: 15                                                      ║
║ Stories Completadas: 10                                                     ║
║ Stories Bloqueadas: 1                                                       ║
║ Tasa de Completitud: 66.7%                                                  ║
╠------------------------------------------------------------------------------╣
║ ISSUES                                                                      ║
╠------------------------------------------------------------------------------╣
║ Total Issues: 8                                                             ║
║ Issues Abiertos: 3                                                          ║
║ Issues Cerrados: 5                                                          ║
╠------------------------------------------------------------------------------╣
║ ESTADO DEL PROYECTO                                                         ║
╠------------------------------------------------------------------------------╣
║ 🟡 PROGRESO MODERADO (1 bloqueadas)                                         ║
╚==============================================================================╝
```

## Referencia de API

### Herramienta: authenticate

**Descripcion**: Autenticar con Taiga API usando username y password

**Request**:
```json
{
  "name": "authenticate",
  "arguments": {
    "username": "tu_email@example.com",
    "password": "tu_contraseña"
  }
}
```

**Response (Exitosa - 200)**:
```json
{
  "id": 888691,
  "username": "jleon",
  "email": "jleon@example.com",
  "full_name": "Juan Leon",
  "is_active": true,
  "auth_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "authenticated": true,
  "message": "Successfully authenticated with Taiga"
}
```

**Errores Posibles**:

- **400 Bad Request**: Credenciales invalidas
  ```json
  {
    "error": "Authentication failed: Invalid credentials"
  }
  ```

- **401 Unauthorized**: Username o password incorrectos
  ```json
  {
    "error": "Authentication failed: Unauthorized"
  }
  ```

- **500 Internal Server Error**: Error del servidor Taiga
  ```json
  {
    "error": "API error during authentication: Server error"
  }
  ```

**Ejemplo con curl** (invocando herramienta MCP via HTTP):
```bash
# Nota: Esto asume servidor MCP corriendo en HTTP transport
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "authenticate",
      "arguments": {
        "username": "tu_email@example.com",
        "password": "tu_contraseña"
      }
    }
  }'
```

**Ejemplo con Python (usando servidor programaticamente)**:
```python
from src.server import TaigaMCPServer

server = TaigaMCPServer()
# Acceder a AuthTools
auth_tools = server._auth_tools
result = await auth_tools.authenticate(
    username="tu_email@example.com",
    password="tu_contraseña"
)
print(result['auth_token'])
```

### Herramienta: list_projects

**Descripcion**: Listar todos los proyectos accesibles al usuario autenticado

**Request**:
```json
{
  "name": "list_projects",
  "arguments": {
    "auth_token": "eyJ0eXAiOiJKV1QiLC...",
    "member": 888691,
    "is_private": true,
    "is_backlog_activated": true
  }
}
```

**Parametros**:
- `auth_token` (string, required): Token de autenticacion
- `member` (integer, optional): Filtrar por ID de miembro
- `member_id` (integer, optional): Alias de `member`
- `is_private` (boolean, optional): Filtrar por proyectos privados (true) o publicos (false)
- `is_backlog_activated` (boolean, optional): Filtrar por backlog activado

**Response (200)**:
```json
[
  {
    "id": 309804,
    "name": "Proyecto Demo",
    "slug": "jleon-proyecto-demo",
    "description": "Proyecto de demostracion",
    "is_private": true,
    "owner": "jleon",
    "created_date": "2025-01-15T10:30:00Z",
    "modified_date": "2025-12-04T14:00:00Z",
    "total_story_points": 42,
    "total_milestones": 3
  },
  {
    "id": 310000,
    "name": "Otro Proyecto",
    "slug": "otro-proyecto",
    "description": "",
    "is_private": false,
    "owner": "admin",
    "created_date": "2025-02-01T09:00:00Z",
    "modified_date": "2025-03-10T16:30:00Z",
    "total_story_points": 0,
    "total_milestones": 0
  }
]
```

**Errores Posibles**:
- **401 Unauthorized**: Token invalido o expirado
- **500 Internal Server Error**: Error del servidor

### Herramienta: create_userstory

**Descripcion**: Crear una nueva user story en un proyecto

**Request**:
```json
{
  "name": "create_userstory",
  "arguments": {
    "auth_token": "eyJ0eXAiOiJKV1QiLC...",
    "project_id": 309804,
    "subject": "Como usuario quiero login",
    "description": "Implementar autenticacion con email y password",
    "tags": ["backend", "auth"],
    "status": 1,
    "assigned_to": 888691,
    "is_blocked": false,
    "milestone": 5678,
    "points": {
      "1": 5,
      "2": 3
    }
  }
}
```

**Parametros**:
- `auth_token` (string, required): Token de autenticacion
- `project_id` (integer, required): ID del proyecto
- `subject` (string, required): Titulo de la user story
- `description` (string, optional): Descripcion detallada
- `tags` (array[string], optional): Etiquetas
- `status` (integer, optional): ID del estado
- `assigned_to` (integer, optional): ID del usuario asignado
- `is_blocked` (boolean, optional): Si esta bloqueada
- `blocked_note` (string, optional): Razon del bloqueo
- `milestone` (integer, optional): ID del milestone/sprint
- `points` (object, optional): Story points por rol
- `client_requirement` (boolean, optional): Es requerimiento del cliente
- `team_requirement` (boolean, optional): Es requerimiento del equipo
- `attachments` (array, optional): Adjuntos

**Response (201 Created)**:
```json
{
  "id": 7654321,
  "ref": 123,
  "subject": "Como usuario quiero login",
  "description": "Implementar autenticacion con email y password",
  "project": 309804,
  "status": 1,
  "points": {
    "1": 5,
    "2": 3
  },
  "total_points": 8,
  "is_closed": false,
  "attachments": [],
  "message": "Successfully created user story 'Como usuario quiero login'"
}
```

**Errores Posibles**:
- **400 Bad Request**: Parametros invalidos
- **401 Unauthorized**: No autenticado
- **403 Forbidden**: Sin permisos en el proyecto
- **404 Not Found**: Proyecto no existe

## Solucion de Problemas

### Problema: "TAIGA_API_URL is required in environment variables"

**Causa**: El archivo `.env` no existe o no contiene `TAIGA_API_URL`

**Diagnostico**:
```bash
# Verificar si existe .env
ls -la .env

# Ver contenido
cat .env | grep TAIGA_API_URL
```

**Solucion**:
```bash
# Si no existe .env, crearlo
cp .env.example .env

# Editar y añadir:
echo "TAIGA_API_URL=https://api.taiga.io/api/v1" >> .env
echo "TAIGA_USERNAME=tu_email@example.com" >> .env
echo "TAIGA_PASSWORD=tu_contraseña" >> .env

# Verificar
cat .env
```

### Problema: "Authentication failed: 401"

**Causa**: Username o password incorrectos

**Diagnostico**:
```bash
# Probar manualmente con curl
curl -X POST https://api.taiga.io/api/v1/auth \
  -H "Content-Type: application/json" \
  -d '{
    "type": "normal",
    "username": "tu_email@example.com",
    "password": "tu_contraseña"
  }'

# Si retorna 401, las credenciales son incorrectas
```

**Solucion**:
1. Verifica que `TAIGA_USERNAME` es tu email real de Taiga
2. Verifica que `TAIGA_PASSWORD` es correcto (sin espacios extra)
3. Intenta hacer login en https://taiga.io para confirmar credenciales
4. Si olvidaste la contraseña, usa "Forgot password" en Taiga

### Problema: "Connection timeout"

**Causa**: No hay conexion a Taiga API o timeout muy corto

**Diagnostico**:
```bash
# Verificar conectividad
ping api.taiga.io

# Probar endpoint manualmente
curl -I https://api.taiga.io/api/v1/projects
```

**Solucion**:
```bash
# Aumentar timeout en .env
echo "TAIGA_TIMEOUT=60.0" >> .env

# Verificar firewall/proxy
echo $http_proxy
echo $https_proxy

# Si estas detras de proxy, configuralo
export http_proxy=http://proxy.empresa.com:8080
export https_proxy=http://proxy.empresa.com:8080
```

### Problema: "Rate limit exceeded"

**Causa**: Demasiadas peticiones a Taiga API en poco tiempo

**Diagnostico**:
```bash
# Ver headers de rate limiting
curl -I https://api.taiga.io/api/v1/projects \
  -H "Authorization: Bearer TU_TOKEN"

# Buscar X-RateLimit headers
```

**Solucion**:
```python
# El cliente tiene retry automatico
# Pero puedes aumentar el delay entre reintentos

# En codigo:
config.max_retries = 5
config.timeout = 60.0

# Esperar entre operaciones
import asyncio
await asyncio.sleep(2)  # 2 segundos entre llamadas
```

### Problema: Tests de integracion fallan

**Causa**: Credenciales no configuradas o Taiga API no accesible

**Diagnostico**:
```bash
# Ver que tests fallan exactamente
uv run pytest tests/integration -v --tb=short

# Verificar credenciales
python -c "from src.config import TaigaConfig; c=TaigaConfig(); print(c.taiga_api_url)"
```

**Solucion**:
```bash
# Ejecutar solo tests unitarios (no necesitan API real)
uv run pytest tests/unit -v

# Para tests de integracion, asegurate de tener:
# 1. .env con credenciales validas
# 2. Conexion a internet
# 3. Proyecto de prueba en Taiga

# Crear proyecto de prueba manualmente en taiga.io
# Luego usa su ID en tests
```

### Problema: "Module not found: src"

**Causa**: No estas ejecutando con `uv run` o el PYTHONPATH no esta configurado

**Diagnostico**:
```bash
# Ver si estas en el directorio correcto
pwd
# Debe estar en /ruta/a/taiga_mcp_claude_code

# Verificar estructura
ls src/
# Debe mostrar: server.py, config.py, etc.
```

**Solucion**:
```bash
# SIEMPRE usar uv run para ejecutar scripts
uv run python src/server.py

# NO hacer:
python src/server.py  # ❌ Puede fallar

# Si necesitas ejecutar sin uv, activar venv:
source .venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python src/server.py
```

## FAQ

### ¿Puedo usar el servidor con Taiga self-hosted?

Si, absolutamente. Solo cambia `TAIGA_API_URL` en `.env`:

```bash
# Para Taiga self-hosted
TAIGA_API_URL=https://tu-servidor-taiga.com/api/v1
```

### ¿Como agrego soporte para Issues, Tasks, Epics?

El servidor ya tiene la infraestructura. Solo necesitas crear nuevas herramientas:

1. Crea `src/tools/issues.py` o `src/application/tools/issue_tools.py`
2. Define herramientas MCP con `@mcp.tool`
3. Registra las herramientas en el servidor

Ejemplo:
```python
# src/tools/issues.py
class IssueTools:
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp

    def register_tools(self):
        @self.mcp.tool(name="list_issues", description="List issues")
        async def list_issues(auth_token: str, project_id: int):
            # Implementacion
            pass
```

### ¿El servidor guarda el token de autenticacion?

Si, pero solo en **memoria** durante la sesion. Cuando cierras el servidor, el token se pierde.

Para persistencia, podrias:
- Guardar en archivo (inseguro en produccion)
- Usar keyring del sistema operativo
- Usar variables de entorno (recomendado para servers)

### ¿Puedo ejecutar multiples instancias del servidor?

Si:
- **STDIO transport**: Cada instancia es independiente (un proceso por cliente)
- **HTTP transport**: Puedes tener multiples clientes conectados a un mismo servidor

### ¿Como aumento el nivel de debug?

```bash
# En .env
MCP_DEBUG=True

# O en codigo
import logging
logging.basicConfig(level=logging.DEBUG)
```

### ¿Funcionara con Claude Desktop?

Si! Agrega a tu config de Claude Desktop:

```json
{
  "mcpServers": {
    "taiga": {
      "command": "uv",
      "args": ["run", "python", "/ruta/completa/taiga_mcp_claude_code/src/server.py"],
      "env": {
        "TAIGA_API_URL": "https://api.taiga.io/api/v1",
        "TAIGA_USERNAME": "tu_email@example.com",
        "TAIGA_PASSWORD": "tu_contraseña"
      }
    }
  }
}
```

Reinicia Claude Desktop y podras usar comandos como:
- "Lista mis proyectos de Taiga"
- "Crea una user story en el proyecto X"
- "¿Cuantas historias tengo abiertas?"

### ¿Que pasa si mi contraseña tiene caracteres especiales?

Pydantic maneja correctamente cualquier caracter. Solo asegurate de:

```bash
# En .env, NO uses comillas a menos que sean parte de la contraseña
TAIGA_PASSWORD=Mi@Contraseña#Compleja!123

# Si la contraseña tiene espacios, usa comillas:
TAIGA_PASSWORD="Mi Contraseña Con Espacios"
```

### ¿Como actualizo a una nueva version de FastMCP?

```bash
# Ver version actual
uv run python -c "import fastmcp; print(fastmcp.__version__)"

# Actualizar
uv sync --upgrade-package fastmcp

# Verificar cambios en changelog
# Ejecutar tests
uv run pytest
```

### ¿Donde puedo ver logs del servidor?

Actualmente los logs van a stdout/stderr. Para persistirlos:

```bash
# Redirigir a archivo
uv run python src/server.py > server.log 2>&1

# O usar systemd/supervisor en produccion
```

### ¿Como contribuyo al proyecto?

1. Fork el repositorio
2. Crea branch: `git checkout -b feature/mi-feature`
3. Escribe tests primero (TDD)
4. Implementa la feature
5. Ejecuta tests: `uv run pytest`
6. Ejecuta linter: `uv run ruff check src/`
7. Commit: `git commit -m "Add: mi feature"`
8. Push: `git push origin feature/mi-feature`
9. Abre Pull Request

---

**¿Mas preguntas?** Abre un issue en GitHub o consulta la documentacion adicional en `/Documentacion/`
