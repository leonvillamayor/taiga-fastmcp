---
name: coverage-check
description: "Verifica la cobertura de tests del proyecto y genera reporte detallado. Úsame cuando necesites verificar si se alcanza el objetivo de cobertura >= 80%"
model: claude-sonnet-4-5
allowed-tools: Bash, Read, Write, Grep, Glob
---

# Skill: Coverage Check

Este skill verifica la cobertura de código del proyecto y genera reportes detallados.

## Cuándo se invoca automáticamente

Este skill se activa cuando:
- Todos los tests pasan a VERDE (hook después de Experto DDD)
- El usuario pregunta por la cobertura
- Se necesita verificar cumplimiento de RNF-004 (Cobertura >= 80%)

## Acciones

1. **Ejecutar pytest con coverage**:
   ```bash
   uv run pytest --cov=src --cov-report=term-missing --cov-report=html
   ```

2. **Analizar resultados**:
   - Porcentaje de cobertura total
   - Archivos con baja cobertura (< 80%)
   - Líneas específicas no cubiertas

3. **Generar reporte**:
   - Terminal: resumen por módulo
   - HTML: reporte detallado en `htmlcov/`
   - Identificar gaps críticos

4. **Sugerencias**:
   - Si cobertura < 80%: listar archivos problemáticos
   - Sugerir tests adicionales necesarios

## Ejemplo de output

```
===================== Coverage Report =====================

Total Coverage: 87%

✅ CUMPLE objetivo >= 80%

Detalle por módulo:
  src/domain/entities/          95%  ✅
  src/domain/value_objects/     100% ✅
  src/application/use_cases/    82%  ✅
  src/infrastructure/persistence/ 73%  ❌

Archivos con baja cobertura:
  - src/infrastructure/persistence/repositorio_prestamo.py (73%)
    Líneas no cubiertas: 45-52, 78-82

Reporte HTML generado: htmlcov/index.html
```

## Configuración

- **Umbral mínimo**: 80%
- **Formato de salida**: Terminal + HTML
- **Inclusiones**: Solo `src/` (excluir tests)
