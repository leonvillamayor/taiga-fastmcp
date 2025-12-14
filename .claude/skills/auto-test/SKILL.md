---
name: auto-test
description: "Ejecuta automáticamente los tests cuando detectas cambios en archivos de código Python. Úsame cuando se modifiquen archivos en src/ o tests/"
model: claude-sonnet-4-5
allowed-tools: Bash, Read, Grep
---

# Skill: Auto-Test

Este skill ejecuta automáticamente los tests del proyecto cuando detecta cambios en el código.

## Cuándo se invoca automáticamente

Este skill se activa cuando:
- Se modifican archivos Python en `src/`
- Se modifican archivos de test en `tests/`
- El usuario solicita explícitamente ejecutar tests

## Acciones

1. **Verificar proyecto uv**: Asegurar que existe `pyproject.toml`
2. **Ejecutar tests**: `uv run pytest -v`
3. **Reportar resultados**:
   - Número de tests pasados/fallados
   - Tests que cambiaron de estado
   - Errores específicos si los hay

## Ejemplo de uso

```bash
# Se ejecuta automáticamente después de:
# - Editar src/domain/entities/libro.py
# - Editar tests/unit/test_libro.py

# Output esperado:
✅ 45 tests pasados
❌ 2 tests fallados:
  - tests/unit/test_prestamo.py::test_prestamo_con_usuario_inactivo
  - tests/integration/test_repositorio_prestamo.py::test_guardar_prestamo
```

## Configuración

- **Timeout**: 120 segundos
- **Modo de salida**: Verbose (`-v`)
- **Cobertura**: No (usar coverage-check skill para eso)
