---
name: format-code
description: "Formatea automáticamente el código Python usando black y organiza imports con isort. Úsame cuando el código necesite formateo o al finalizar implementación"
model: claude-sonnet-4-5
allowed-tools: Bash, Read, Write, Glob
---

# Skill: Format Code

Este skill formatea automáticamente el código Python siguiendo estándares de la industria.

## Cuándo se invoca automáticamente

Este skill se activa cuando:
- Se completa la implementación de una feature
- El Experto DDD termina de implementar código
- El usuario solicita formateo de código
- Antes de generar documentación (para ejemplos de código limpios)

## Herramientas utilizadas

1. **black**: Formateador de código opinionado
   - Línea máxima: 100 caracteres
   - Python 3.11+

2. **isort**: Organizador de imports
   - Compatible con black
   - Agrupa: stdlib, terceros, propios

## Acciones

1. **Instalar dependencias** (si no están):
   ```bash
   uv add --dev black isort
   ```

2. **Formatear código**:
   ```bash
   uv run black src/ tests/ --line-length 100
   ```

3. **Organizar imports**:
   ```bash
   uv run isort src/ tests/ --profile black
   ```

4. **Reportar cambios**:
   - Archivos modificados
   - Tipo de cambios aplicados

## Ejemplo de output

```
===================== Code Formatting =====================

Running black...
  reformatted src/domain/entities/prestamo.py
  reformatted src/application/use_cases/realizar_prestamo.py
  reformatted tests/unit/test_prestamo.py

  3 files reformatted, 12 files left unchanged.

Running isort...
  Fixing src/infrastructure/persistence/repositorio_libro.py

  1 file fixed, 14 files already well formatted.

✅ Código formateado correctamente
```

## Configuración pyproject.toml

```toml
[tool.black]
line-length = 100
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 100
```

## Notas

- El formateo se aplica automáticamente
- No requiere aprobación manual
- Compatible con DDD (no afecta estructura de capas)
