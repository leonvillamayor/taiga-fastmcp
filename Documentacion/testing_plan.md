# Plan de Testing - Taiga MCP Server

## Resumen Ejecutivo

**Fecha del análisis**: 2025-12-13
**Cobertura actual**: 74.87%
**Objetivo de cobertura**: 80%
**Gap a cubrir**: 5.13 puntos porcentuales

## 1. Estado Actual de Cobertura

### 1.1 Métricas Totales

| Métrica | Valor |
|---------|-------|
| **Cobertura Total** | 74.87% |
| Líneas Cubiertas | 6,854 |
| Líneas Sin Cubrir | 2,300 |
| Total Líneas | 9,154 |

### 1.2 Cobertura por Capa DDD

| Capa | Cobertura | Líneas | Archivos | Estado |
|------|-----------|--------|----------|--------|
| domain/exceptions | 100.0% | 16/16 | 1 | :white_check_mark: |
| domain/repositories | 100.0% | 161/161 | 9 | :white_check_mark: |
| domain/value_objects | 98.2% | 54/55 | 3 | :white_check_mark: |
| application/responses | 99.0% | 199/201 | 3 | :white_check_mark: |
| domain/validators | 95.0% | 569/599 | 1 | :white_check_mark: |
| infrastructure (otros) | 92.3% | 740/802 | 9 | :white_check_mark: |
| application/use_cases | 91.8% | 716/780 | 9 | :white_check_mark: |
| domain/entities | 90.8% | 570/628 | 11 | :white_check_mark: |
| infrastructure/repositories | 90.1% | 534/593 | 9 | :white_check_mark: |
| infrastructure/logging | 60.2% | 244/405 | 5 | :warning: |
| **application/tools** | **59.9%** | **2,727/4,555** | **11** | :x: |

## 2. Identificación de Gaps Críticos

### 2.1 Gaps por Impacto (Top 15)

El impacto se calcula como: `Líneas Faltantes × Peso de Capa`

| Rank | Archivo | Capa | Cobertura | Faltan | Impact |
|------|---------|------|-----------|--------|--------|
| 1 | application/tools/epic_tools.py | application/tools | 47.3% | 385 | 1,155 |
| 2 | application/tools/project_tools.py | application/tools | 58.4% | 311 | 933 |
| 3 | application/tools/userstory_tools.py | application/tools | 66.4% | 261 | 783 |
| 4 | application/tools/issue_tools.py | application/tools | 59.9% | 251 | 753 |
| 5 | application/tools/wiki_tools.py | application/tools | 48.9% | 201 | 603 |
| 6 | application/tools/task_tools.py | application/tools | 65.3% | 170 | 510 |
| 7 | infrastructure/logging/decorators.py | infrastructure/logging | 8.9% | 153 | 306 |
| 8 | application/tools/webhook_tools.py | application/tools | 52.4% | 98 | 294 |
| 9 | application/tools/membership_tools.py | application/tools | 67.2% | 58 | 174 |
| 10 | application/tools/auth_tools.py | application/tools | 78.4% | 41 | 123 |
| 11 | infrastructure/repositories/epic_repository_impl.py | infrastructure/repos | 70.0% | 30 | 90 |
| 12 | application/tools/user_tools.py | application/tools | 63.2% | 21 | 63 |
| 13 | infrastructure/http_session_pool.py | infrastructure | 61.2% | 31 | 62 |

### 2.2 Pesos de Capa (Criticidad DDD)

| Capa | Peso | Justificación |
|------|------|---------------|
| domain/entities | 5 | Núcleo del negocio - máxima prioridad |
| domain/value_objects | 5 | Inmutabilidad y validación crítica |
| domain/repositories | 4 | Interfaces de acceso a datos |
| domain/validators | 4 | Reglas de negocio |
| application/use_cases | 4 | Orquestación de lógica |
| application/tools | 3 | Wrappers FastMCP |
| infrastructure/repositories | 3 | Implementaciones concretas |
| application/responses | 2 | DTOs de respuesta |
| infrastructure/logging | 2 | Infraestructura auxiliar |
| infrastructure | 2 | Servicios técnicos |

## 3. Plan de Testing por Módulo

### 3.1 Prioridad ALTA - application/tools (59.9%)

**Objetivo**: Alcanzar 80% de cobertura
**Líneas a cubrir**: ~918 líneas adicionales

#### Estrategia

1. **epic_tools.py** (47.3% → 80%)
   - Tests para funciones de creación masiva
   - Tests para manejo de errores de API
   - Tests para validación de parámetros

2. **project_tools.py** (58.4% → 80%)
   - Tests para operaciones CRUD completas
   - Tests para filtros y paginación
   - Tests para manejo de permisos

3. **userstory_tools.py** (66.4% → 80%)
   - Tests para operaciones de bulk
   - Tests para attachments
   - Tests para custom attributes

4. **issue_tools.py** (59.9% → 80%)
   - Tests para comentarios
   - Tests para votación
   - Tests para watchers

5. **wiki_tools.py** (48.9% → 80%)
   - Tests para páginas
   - Tests para links
   - Tests para attachments

### 3.2 Prioridad MEDIA - infrastructure/logging (60.2%)

**Objetivo**: Alcanzar 80% de cobertura
**Líneas a cubrir**: ~80 líneas adicionales

#### Estrategia

1. **decorators.py** (8.9% → 80%)
   - Tests para decoradores de logging
   - Tests para formateo de mensajes
   - Tests para niveles de log

### 3.3 Prioridad BAJA - infrastructure/repositories (90.1%)

**Objetivo**: Mantener >90%

1. **epic_repository_impl.py** (70.0% → 80%)
   - Tests para métodos de filtrado
   - Tests para paginación

### 3.4 Prioridad BAJA - infrastructure (92.3%)

1. **http_session_pool.py** (61.2% → 80%)
   - Tests para manejo de conexiones
   - Tests para timeouts

## 4. Baseline de Cobertura

### 4.1 Baseline Establecido (2025-12-13)

```
Total:                     74.87%
domain/entities:           90.8%
domain/value_objects:      98.2%
domain/repositories:       100.0%
domain/exceptions:         100.0%
domain/validators:         95.0%
application/use_cases:     91.8%
application/tools:         59.9%
application/responses:     99.0%
infrastructure/repos:      90.1%
infrastructure/logging:    60.2%
infrastructure (otros):    92.3%
```

### 4.2 Objetivos de Cobertura

| Milestone | Fecha Objetivo | Cobertura |
|-----------|---------------|-----------|
| Baseline | 2025-12-13 | 74.87% |
| Fase 1 | TBD | 77% |
| Fase 2 | TBD | 80% |
| Objetivo Final | TBD | 85% |

## 5. Herramientas y Configuración

### 5.1 Herramientas de Coverage

- **pytest-cov**: Plugin de pytest para coverage
- **coverage.py**: Motor de análisis de cobertura

### 5.2 Archivos de Configuración

| Archivo | Propósito |
|---------|-----------|
| `pyproject.toml` | Configuración principal de pytest y coverage |
| `.coveragerc` | Configuración adicional de coverage |
| `scripts/coverage_analysis.py` | Script de análisis personalizado |

### 5.3 Comandos de Coverage

```bash
# Análisis completo
uv run pytest --cov=src --cov-report=html --cov-report=term-missing

# Generar JSON para análisis
uv run pytest --cov=src --cov-report=json:coverage.json

# Ejecutar script de análisis
uv run python scripts/coverage_analysis.py

# Generar reporte Markdown
uv run python scripts/coverage_analysis.py --format markdown --output report.md

# Verificar threshold
uv run python scripts/coverage_analysis.py --threshold 80
```

## 6. Métricas y Monitoreo

### 6.1 Métricas a Monitorizar

1. **Cobertura total**: Porcentaje de líneas cubiertas
2. **Cobertura por capa**: Distribución por arquitectura DDD
3. **Gaps críticos**: Archivos con cobertura < 80%
4. **Tendencia**: Evolución de cobertura en el tiempo

### 6.2 Reportes

- **HTML**: `htmlcov/index.html` - Reporte visual detallado
- **Terminal**: `--cov-report=term-missing` - Vista rápida
- **JSON**: `coverage.json` - Datos para análisis automatizado
- **XML**: `coverage.xml` - Integración CI/CD

## 7. Tests Asociados al Análisis

### 7.1 Test 4.1.1: Script de análisis ejecuta sin errores

**Estado**: :white_check_mark: PASSED

```bash
uv run python scripts/coverage_analysis.py --json coverage.json
# Exit code: 0 (aunque cobertura < 80%, el script funciona correctamente)
```

### 7.2 Test 4.1.2: Reporte HTML se genera correctamente

**Estado**: :white_check_mark: PASSED

```bash
ls htmlcov/index.html
# Archivo existe y es accesible
```

## 8. Próximos Pasos

1. [ ] Implementar tests para application/tools (prioridad alta)
2. [ ] Implementar tests para infrastructure/logging/decorators.py
3. [ ] Alcanzar 77% de cobertura (Fase 1)
4. [ ] Alcanzar 80% de cobertura (Fase 2)
5. [ ] Configurar CI/CD para verificar cobertura automáticamente

---

**Generado por**: scripts/coverage_analysis.py
**Última actualización**: 2025-12-13
