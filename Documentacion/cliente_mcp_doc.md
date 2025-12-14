# Cliente MCP - Configuración para Claude Code

## Tabla de Contenidos

1. [Inicio Rápido](#inicio-rápido)
2. [Descripción General](#descripción-general)
3. [Requisitos Previos](#requisitos-previos)
4. [Instalación](#instalación)
5. [Configuración de Claude Code](#configuración-de-claude-code)
6. [Verificación de la Instalación](#verificación-de-la-instalación)
7. [Uso del Cliente](#uso-del-cliente)
8. [Ejemplos de Uso](#ejemplos-de-uso)
9. [Configuración Avanzada](#configuración-avanzada)
10. [Troubleshooting](#troubleshooting)
11. [Mejores Prácticas](#mejores-prácticas)

---

## Inicio Rápido

Si ya tienes el servidor instalado y solo quieres configurarlo rápidamente en Claude Code:

```bash
# 1. Obtener rutas necesarias
cd /ruta/a/tu/proyecto/taiga_mcp_server
source venv/bin/activate
which python3  # Copia esta ruta
pwd            # Copia esta ruta

# 2. Agregar el servidor a Claude Code
claude mcp add taiga

# Cuando te pida la información:
# Command: /ruta/completa/venv/bin/python3
# Args: ["/ruta/completa/server.py"]
# Env: {} (dejarlo vacío si usas .env)

# 3. Verificar
claude mcp list
claude mcp test taiga

# 4. ¡Listo! Inicia Claude Code
claude
```

Para configuración detallada, continúa leyendo.

---

## Descripción General

Este documento describe cómo instalar y configurar el **Servidor MCP de Taiga** para usarlo con **Claude Code** (o Claude Desktop). Claude Code es la interfaz de línea de comandos oficial de Anthropic para Claude que permite interactuar con servidores MCP.

Una vez configurado, podrás usar lenguaje natural en Claude para gestionar proyectos Taiga, crear user stories, asignar issues, organizar sprints y mucho más.

---

## Requisitos Previos

### 1. Claude Code Instalado

Verifica que tienes Claude Code instalado:

```bash
claude --version
```

Si no está instalado, sigue las instrucciones en [Claude Code Documentation](https://claude.ai/claude-code).

### 2. Servidor MCP de Taiga

Asegúrate de haber completado la instalación del servidor siguiendo [servidor_mcp_doc.md](servidor_mcp_doc.md):

- ✅ Servidor instalado en `taiga_mcp_server/`
- ✅ Entorno virtual creado y activado
- ✅ Archivo `.env` configurado con credenciales de Taiga
- ✅ Tests pasando correctamente

### 3. Cuenta Taiga

- Cuenta activa en [Taiga.io](https://taiga.io)
- Credenciales configuradas en `.env`

---

## Instalación

### Paso 1: Ubicación del Servidor

Asegúrate de conocer la ruta completa al servidor:

```bash
# Ir al directorio del servidor
cd /ruta/a/tu/proyecto/taiga_mcp_server

# Obtener ruta absoluta
pwd
# Ejemplo: /home/usuario/proyectos/taiga_mcp_server
```

### Paso 2: Verificar Python Virtual Environment

```bash
# Desde el directorio taiga_mcp_server/
source venv/bin/activate

# Verificar que Python está en el venv
which python3
# Debe mostrar: /ruta/a/tu/proyecto/taiga_mcp_server/venv/bin/python3
```

### Paso 3: Obtener Ruta al Ejecutable de Python

```bash
# Estando en el venv activado
which python3
```

Anota esta ruta, la necesitarás para la configuración.

---

## Configuración de Claude Code

### Opción 1: Usando `claude mcp add` (Método Recomendado)

La forma más sencilla de configurar el servidor MCP es usando el comando `claude mcp add`:

#### 1.1 Preparar el Comando

Primero, obtén las rutas necesarias:

```bash
# Obtener ruta al Python del venv
cd /ruta/a/tu/proyecto/taiga_mcp_server
source venv/bin/activate
which python3
# Ejemplo: /home/usuario/proyectos/taiga_mcp_server/venv/bin/python3

# Obtener ruta al server.py
pwd
# Ejemplo: /home/usuario/proyectos/taiga_mcp_server
```

#### 1.2 Ejecutar el Comando

```bash
claude mcp add taiga
```

Esto abrirá un asistente interactivo. Cuando te pida la configuración, proporciona:

**Command:**
```
/ruta/completa/a/taiga_mcp_server/venv/bin/python3
```

**Args (como array JSON):**
```json
["/ruta/completa/a/taiga_mcp_server/server.py"]
```

**Environment Variables (opcional):**
```json
{
  "TAIGA_API_URL": "https://api.taiga.io/api/v1",
  "TAIGA_USERNAME": "tu_usuario@ejemplo.com",
  "TAIGA_PASSWORD": "tu_contraseña",
  "MCP_SERVER_NAME": "Taiga MCP Server",
  "MCP_TRANSPORT": "stdio"
}
```

#### 1.3 Ejemplo Completo

```bash
$ claude mcp add taiga

✓ Name: taiga
✓ Command: /home/usuario/proyectos/taiga_mcp_server/venv/bin/python3
✓ Args: ["/home/usuario/proyectos/taiga_mcp_server/server.py"]
✓ Env: {"TAIGA_API_URL":"https://api.taiga.io/api/v1","TAIGA_USERNAME":"usuario@ejemplo.com","TAIGA_PASSWORD":"password"}

✓ MCP server 'taiga' added successfully!
```

#### 1.4 Verificar la Configuración

```bash
claude mcp list
```

Deberías ver:
```
Available MCP Servers:
- taiga: Taiga MCP Server
```

### Opción 2: Configuración Manual

Si prefieres editar el archivo de configuración directamente, Claude Code usa un archivo JSON.

#### 2.1 Ubicar el Archivo de Configuración

Claude Code almacena la configuración en:

```bash
# En Linux/macOS
~/.config/claude/claude_desktop_config.json

# O posiblemente en (depende de la versión)
~/.claude/config.json
```

#### 2.2 Editar la Configuración

Abre el archivo de configuración con tu editor favorito:

```bash
nano ~/.config/claude/claude_desktop_config.json
# o
code ~/.config/claude/claude_desktop_config.json
```

#### 2.3 Agregar el Servidor MCP

Agrega la siguiente configuración (adapta las rutas a tu sistema):

```json
{
  "mcpServers": {
    "taiga": {
      "command": "/ruta/completa/a/taiga_mcp_server/venv/bin/python3",
      "args": [
        "/ruta/completa/a/taiga_mcp_server/server.py"
      ],
      "env": {
        "TAIGA_API_URL": "https://api.taiga.io/api/v1",
        "TAIGA_USERNAME": "tu_usuario@ejemplo.com",
        "TAIGA_PASSWORD": "tu_contraseña",
        "MCP_SERVER_NAME": "Taiga MCP Server",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

**IMPORTANTE:** Reemplaza:
- `/ruta/completa/a/taiga_mcp_server/` con tu ruta real
- `tu_usuario@ejemplo.com` con tu usuario de Taiga
- `tu_contraseña` con tu contraseña de Taiga

#### Ejemplo Completo:

```json
{
  "mcpServers": {
    "taiga": {
      "command": "/home/usuario/proyectos/taiga_mcp_server/venv/bin/python3",
      "args": [
        "/home/usuario/proyectos/taiga_mcp_server/server.py"
      ],
      "env": {
        "TAIGA_API_URL": "https://api.taiga.io/api/v1",
        "TAIGA_USERNAME": "usuario@ejemplo.com",
        "TAIGA_PASSWORD": "password",
        "MCP_SERVER_NAME": "Taiga MCP Server",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

#### 2.4 Guardar y Cerrar

Guarda el archivo (Ctrl+O en nano, Ctrl+S en VSCode).

### Opción 3: Usar Variables de Entorno del Sistema

Si prefieres no poner las credenciales en el archivo de configuración:

**Usando `claude mcp add`:**
```bash
claude mcp add taiga \
  --command "/ruta/completa/a/taiga_mcp_server/venv/bin/python3" \
  --args '["/ruta/completa/a/taiga_mcp_server/server.py"]'
```

El servidor leerá las credenciales del archivo `.env` automáticamente.

**O editando el archivo de configuración:**
```json
{
  "mcpServers": {
    "taiga": {
      "command": "/ruta/completa/a/taiga_mcp_server/venv/bin/python3",
      "args": [
        "/ruta/completa/a/taiga_mcp_server/server.py"
      ],
      "env": {}
    }
  }
}
```

El servidor cargará automáticamente las variables del archivo `.env` ubicado en `taiga_mcp_server/.env`.

### Comandos Útiles de `claude mcp`

```bash
# Listar servidores MCP configurados
claude mcp list

# Ver detalles de un servidor
claude mcp show taiga

# Actualizar configuración de un servidor
claude mcp update taiga

# Eliminar un servidor
claude mcp remove taiga

# Probar conexión con un servidor
claude mcp test taiga
```

---

## Verificación de la Instalación

### Paso 1: Verificar el Servidor con `claude mcp`

Primero, verifica que el servidor está correctamente configurado:

```bash
# Listar servidores configurados
claude mcp list
```

Deberías ver:
```
Available MCP Servers:
- taiga: Taiga MCP Server
```

Para más detalles:
```bash
claude mcp show taiga
```

Verás la configuración completa del servidor:
```
Server: taiga
Command: /home/usuario/proyectos/taiga_mcp_server/venv/bin/python3
Args: ["/home/usuario/proyectos/taiga_mcp_server/server.py"]
Environment Variables: {
  "TAIGA_API_URL": "https://api.taiga.io/api/v1",
  ...
}
```

### Paso 2: Probar la Conexión

Prueba que el servidor puede conectarse correctamente:

```bash
claude mcp test taiga
```

Si todo funciona, verás:
```
✓ Server started successfully
✓ Connected to Taiga API
✓ Authentication successful
✓ 34 tools available
```

### Paso 3: Iniciar Claude Code

Inicia Claude Code:

```bash
claude
```

### Paso 4: Verificar Herramientas en Claude Code

Dentro de Claude Code, verifica que las herramientas están disponibles:

```bash
# Dentro de Claude Code
/mcp list
```

Deberías ver:
```
Available MCP Servers:
- taiga: Taiga MCP Server (34 tools)
```

Listar todas las herramientas:
```bash
/tools
```

Deberías ver las 34 herramientas del servidor Taiga:

```
Available Tools from Taiga MCP Server:

Projects:
- list_projects
- get_project
- create_project
- update_project
- delete_project
- get_project_stats

User Stories:
- list_user_stories
- get_user_story
- create_user_story
- update_user_story
- delete_user_story

Issues:
- list_issues
- get_issue
- create_issue
- update_issue
- delete_issue

Epics:
- list_epics
- get_epic
- create_epic
- update_epic
- delete_epic
- list_epic_user_stories
- relate_user_story_to_epic

Tasks:
- list_tasks
- get_task
- create_task
- update_task
- delete_task

Milestones:
- list_milestones
- get_milestone
- create_milestone
- update_milestone
- delete_milestone
- get_milestone_stats
```

### Paso 5: Prueba Simple

Haz una prueba simple para verificar que funciona. Dentro de Claude Code, escribe:

```
"Lista mis proyectos de Taiga"
```

Claude debería:
1. Reconocer que necesita usar el servidor MCP de Taiga
2. Llamar a la herramienta `list_projects`
3. Mostrarte la lista de tus proyectos

Si ves tus proyectos, ¡la configuración es exitosa! 🎉

---

## Uso del Cliente

### Interacción con Lenguaje Natural

Una vez configurado, simplemente chatea con Claude usando lenguaje natural:

```
Usuario: "Muéstrame todos mis proyectos de Taiga"
Claude: [Usa list_projects y muestra los resultados]

Usuario: "Crea una nueva user story en el proyecto 'Mi Proyecto' con título 'Implementar login'"
Claude: [Usa get_project para obtener el ID, luego create_user_story]

Usuario: "Cuáles son los issues abiertos del proyecto 123?"
Claude: [Usa list_issues con filtros]
```

### Comandos Directos

También puedes ser más específico:

```
"Usa la herramienta list_projects para mostrar mis proyectos"

"Con create_user_story crea una historia con título 'Login' en proyecto 456"

"Obtén las estadísticas del milestone 789 con get_milestone_stats"
```

---

## Ejemplos de Uso

### Ejemplo 1: Listar y Explorar Proyectos

```
Usuario: "Lista mis proyectos de Taiga"

Claude: Voy a listar tus proyectos...
[Usa list_projects]

Tienes 5 proyectos:
1. Proyecto A (ID: 123) - 15 user stories, 8 issues
2. Proyecto B (ID: 456) - 23 user stories, 12 issues
...

Usuario: "Dame más detalles del Proyecto A"

Claude: [Usa get_project con ID 123]

Proyecto A (ID: 123):
- Nombre: Proyecto A
- Descripción: Sistema de gestión...
- Propietario: Juan Pérez
- Miembros: 5
- Creado: 2024-01-15
...
```

### Ejemplo 2: Crear y Gestionar User Stories

```
Usuario: "Crea una user story en el proyecto 123 titulada 'Login de usuario'"

Claude: [Usa create_user_story]

✓ User story creada exitosamente:
- ID: 789
- Título: Login de usuario
- Proyecto: Proyecto A (123)
- Estado: New

Usuario: "Agrégale una descripción y ponle 5 puntos"

Claude: [Usa update_user_story con ID 789]

✓ User story actualizada:
- Descripción: Como usuario quiero poder iniciar sesión...
- Puntos: 5
```

### Ejemplo 3: Gestionar un Sprint

```
Usuario: "Crea un nuevo sprint para el proyecto 123 que comience el lunes próximo"

Claude: [Usa create_milestone]

✓ Sprint creado:
- ID: 234
- Nombre: Sprint 1
- Fecha inicio: 2024-12-02
- Fecha fin: 2024-12-16
- Proyecto: Proyecto A (123)

Usuario: "Muéstrame las estadísticas de ese sprint"

Claude: [Usa get_milestone_stats con ID 234]

Estadísticas del Sprint 1:
- Total user stories: 12
- Completadas: 8
- En progreso: 3
- Pendientes: 1
- Velocidad: 32 puntos
```

### Ejemplo 4: Organizar Épicas

```
Usuario: "Crea una épica llamada 'Sistema de Autenticación' en el proyecto 123"

Claude: [Usa create_epic]

✓ Épica creada:
- ID: 567
- Título: Sistema de Autenticación
- Proyecto: Proyecto A (123)

Usuario: "Relaciona la user story 789 con esta épica"

Claude: [Usa relate_user_story_to_epic]

✓ User story 789 ahora está relacionada con la épica 567
```

### Ejemplo 5: Filtrar y Buscar

```
Usuario: "Muéstrame todos los issues del proyecto 123 que estén asignados a mí"

Claude: [Usa list_issues con filtros]

Issues asignados a ti en Proyecto A:
1. Bug #45: Error en login
2. Bug #52: Validación de email
3. Task #67: Actualizar documentación

Usuario: "Muéstrame solo los user stories del sprint actual"

Claude: [Usa list_user_stories con filtro de milestone]

User Stories en el sprint actual:
1. US #12: Login de usuario (5 pts)
2. US #15: Registro de usuario (3 pts)
...
```

---

## Configuración Avanzada

### Múltiples Instancias de Taiga

Si trabajas con múltiples instancias de Taiga (ej. producción y staging):

```json
{
  "mcpServers": {
    "taiga-prod": {
      "command": "/ruta/a/taiga_mcp_server/venv/bin/python3",
      "args": ["/ruta/a/taiga_mcp_server/server.py"],
      "env": {
        "TAIGA_API_URL": "https://api.taiga.io/api/v1",
        "TAIGA_USERNAME": "usuario-prod@ejemplo.com",
        "TAIGA_PASSWORD": "password-prod",
        "MCP_SERVER_NAME": "Taiga Production"
      }
    },
    "taiga-staging": {
      "command": "/ruta/a/taiga_mcp_server/venv/bin/python3",
      "args": ["/ruta/a/taiga_mcp_server/server.py"],
      "env": {
        "TAIGA_API_URL": "https://staging.taiga.io/api/v1",
        "TAIGA_USERNAME": "usuario-staging@ejemplo.com",
        "TAIGA_PASSWORD": "password-staging",
        "MCP_SERVER_NAME": "Taiga Staging"
      }
    }
  }
}
```

Luego puedes especificar qué servidor usar:

```
"Lista proyectos del servidor taiga-prod"
"Crea un issue en taiga-staging"
```

### Taiga Self-Hosted

Si usas una instancia self-hosted de Taiga:

```json
{
  "mcpServers": {
    "taiga": {
      "command": "/ruta/a/taiga_mcp_server/venv/bin/python3",
      "args": ["/ruta/a/taiga_mcp_server/server.py"],
      "env": {
        "TAIGA_API_URL": "https://taiga.miempresa.com/api/v1",
        "TAIGA_USERNAME": "mi.usuario",
        "TAIGA_PASSWORD": "mi.password",
        "MCP_SERVER_NAME": "Taiga Empresa"
      }
    }
  }
}
```

### Timeouts Personalizados

Si tienes proyectos muy grandes que tardan en cargar:

```json
{
  "mcpServers": {
    "taiga": {
      "command": "/ruta/a/taiga_mcp_server/venv/bin/python3",
      "args": ["/ruta/a/taiga_mcp_server/server.py"],
      "env": {
        "TAIGA_API_URL": "https://api.taiga.io/api/v1",
        "TAIGA_USERNAME": "usuario@ejemplo.com",
        "TAIGA_PASSWORD": "password"
      },
      "timeout": 30000
    }
  }
}
```

---

## Troubleshooting

### Diagnóstico Rápido con `claude mcp`

Antes de profundizar en problemas específicos, usa estos comandos para diagnosticar:

```bash
# Ver si el servidor está registrado
claude mcp list

# Ver configuración detallada
claude mcp show taiga

# Probar conexión y funcionalidad
claude mcp test taiga
```

### Problema: "Server not found"

**Síntoma:**
```
Error: MCP server 'taiga' not found
```

**Soluciones:**

**Opción 1: Verificar con `claude mcp`**
```bash
# Listar servidores
claude mcp list

# Si no aparece, agregarlo
claude mcp add taiga
```

**Opción 2: Verificar configuración manual**
1. Verifica que el archivo de configuración está en la ubicación correcta
2. Verifica que la sintaxis JSON es correcta (usa [jsonlint.com](https://jsonlint.com))
3. Reinicia Claude Code después de editar la configuración
4. Verifica que el nombre del servidor coincide exactamente

```bash
# Ver contenido del archivo de configuración
cat ~/.config/claude/claude_desktop_config.json
```

### Problema: "Command not found"

**Síntoma:**
```
Error: Failed to start MCP server: command not found
```

**Diagnóstico:**
```bash
# Ver configuración actual
claude mcp show taiga
```

**Soluciones:**
1. Verifica que la ruta al `python3` es correcta y absoluta
2. Verifica que el archivo `server.py` existe en la ruta especificada
3. Usa rutas absolutas, no relativas (ej. `/home/...` no `~/...`)

```bash
# Verificar ruta a python3
ls -la /ruta/a/taiga_mcp_server/venv/bin/python3

# Verificar ruta a server.py
ls -la /ruta/a/taiga_mcp_server/server.py

# Actualizar configuración si es incorrecta
claude mcp remove taiga
claude mcp add taiga
# O
claude mcp update taiga
```

### Problema: "Authentication failed"

**Síntoma:**
```
Error: TaigaAPIError: Authentication failed
```

**Soluciones:**
1. Verifica que las credenciales en la configuración son correctas
2. Verifica que no hay espacios extra en username/password
3. Prueba iniciar sesión manualmente en taiga.io con esas credenciales
4. Verifica que la cuenta no está bloqueada

### Problema: "No tools available"

**Síntoma:**
```
/tools shows no tools from Taiga
```

**Diagnóstico:**
```bash
# Probar el servidor directamente
claude mcp test taiga

# Si falla, ver los errores
```

**Soluciones:**
1. Verifica que el servidor se está ejecutando correctamente
2. Ejecuta los tests del servidor para verificar que funciona:
```bash
cd /ruta/a/taiga_mcp_server
source venv/bin/activate
pytest tests/test_server.py -v
```
3. Verifica que no hay errores de importación en `server.py`
4. Revisa que las dependencias están instaladas:
```bash
cd /ruta/a/taiga_mcp_server
source venv/bin/activate
pip install -r requirements.txt
```

### Problema: "Connection timeout"

**Síntoma:**
```
Error: Connection to MCP server timed out
```

**Soluciones:**
1. Verifica tu conexión a Internet
2. Verifica que api.taiga.io es accesible
3. Aumenta el timeout en la configuración
4. Si usas VPN o proxy, verifica la configuración

### Problema: "Module not found"

**Síntoma:**
```
ModuleNotFoundError: No module named 'fastmcp'
```

**Soluciones:**
1. Verifica que estás usando el Python del venv correcto
2. Reinstala las dependencias:
```bash
cd /ruta/a/taiga_mcp_server
source venv/bin/activate
pip install -r requirements.txt
```

### Ver Logs del Servidor

Para debug avanzado, puedes redirigir los logs a un archivo:

```json
{
  "mcpServers": {
    "taiga": {
      "command": "/bin/bash",
      "args": [
        "-c",
        "cd /ruta/a/taiga_mcp_server && source venv/bin/activate && python3 server.py 2>&1 | tee /tmp/taiga_mcp.log"
      ],
      "env": { ... }
    }
  }
}
```

Luego revisa `/tmp/taiga_mcp.log` para ver errores detallados.

---

## Mejores Prácticas

### Seguridad

1. **Nunca** compartas tu archivo `claude_desktop_config.json` con credenciales
2. Usa variables de entorno del sistema en lugar de poner contraseñas en JSON
3. Considera usar un token de API en lugar de contraseña (si Taiga lo soporta)
4. Revisa regularmente los permisos del archivo de configuración:
```bash
chmod 600 ~/.config/claude/claude_desktop_config.json
```

### Rendimiento

1. Para proyectos grandes, usa filtros al listar items:
```
"Muéstrame solo los issues abiertos del proyecto X"
# en lugar de
"Muéstrame todos los issues del proyecto X"
```

2. Usa IDs específicos cuando los conozcas:
```
"Muéstrame el issue 123"
# en lugar de
"Busca el issue llamado 'Bug en login'"
```

### Organización

1. Agrupa operaciones relacionadas:
```
"Crea un sprint llamado 'Sprint 5' del 1 al 15 de diciembre,
y luego asígnale las user stories 45, 67 y 89"
```

2. Usa nombres descriptivos para proyectos y milestones

3. Aprovecha las épicas para organizar historias relacionadas

### Workflows Eficientes

#### Inicio de Sprint
```
1. "Lista todos los proyectos"
2. "Crea un nuevo sprint para el proyecto X del DD/MM al DD/MM"
3. "Lista las user stories pendientes del proyecto X"
4. "Asigna las stories A, B, C al sprint recién creado"
```

#### Cierre de Sprint
```
1. "Muéstrame las estadísticas del sprint X"
2. "Lista las user stories no completadas del sprint X"
3. "Mueve las historias incompletas al siguiente sprint"
```

#### Gestión Diaria
```
1. "Muéstrame mis issues asignados"
2. "Actualiza el estado del issue X a 'In Progress'"
3. "Crea un nuevo issue de bug en el proyecto Y"
```

---

## Recursos Adicionales

- [Documentación del Servidor](servidor_mcp_doc.md)
- [Documentación de FastMCP](fastmcp.md)
- [Documentación de Taiga API](taiga.md)
- [Claude Code Official Docs](https://claude.ai/claude-code)
- [Taiga.io Documentation](https://docs.taiga.io)

---

## Actualización del Servidor

Para actualizar a una nueva versión del servidor:

```bash
# 1. Ir al directorio del servidor
cd /ruta/a/taiga_mcp_server

# 2. Activar venv
source venv/bin/activate

# 3. Actualizar dependencias
pip install --upgrade -r requirements.txt

# 4. Ejecutar tests
pytest tests/test_server.py -v

# 5. Reiniciar Claude Code
```

No necesitas cambiar la configuración de Claude Code a menos que cambien las rutas o variables de entorno.

---

## Desinstalación

### Remover el Servidor de Claude Code

**Método Rápido (Recomendado):**
```bash
# Remover el servidor de Claude Code
claude mcp remove taiga

# Verificar que se eliminó
claude mcp list
```

**Método Manual:**
1. Edita `~/.config/claude/claude_desktop_config.json`
2. Elimina la sección del servidor `"taiga": { ... }`
3. Guarda el archivo
4. Reinicia Claude Code

### Eliminar los Archivos del Servidor

Si deseas eliminar completamente el servidor:

```bash
# 1. Remover de Claude Code
claude mcp remove taiga

# 2. Eliminar los archivos
rm -rf /ruta/a/taiga_mcp_server
```

**Nota:** Esto es irreversible. Asegúrate de hacer backup si necesitas conservar algo.

---

**Versión del Documento:** 1.1.0
**Última Actualización:** 2025-11-29
**Cambios en v1.1.0:**
- ✨ Agregado método recomendado con `claude mcp add`
- ✨ Agregada sección de Inicio Rápido
- ✨ Agregados comandos útiles de `claude mcp`
- ✨ Mejoradas secciones de Troubleshooting con diagnóstico usando `claude mcp`
- ✨ Actualizada sección de Desinstalación con `claude mcp remove`

**Autor:** Generado con Claude Code

---

¡Disfruta gestionando tus proyectos Taiga con Claude! 🚀
