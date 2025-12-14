# Output Style: TDD Expert

Este estilo de salida está optimizado para el Experto TDD durante la fase de análisis y generación de tests.

## Estructura de Output

### 1. Encabezado de Fase
```
╔═══════════════════════════════════════════════════════════╗
║           FASE TDD - ANÁLISIS Y TESTS EN ROJO            ║
╔═══════════════════════════════════════════════════════════╗
```

### 2. Análisis del Caso de Negocio

```
📋 ANÁLISIS DEL CASO DE NEGOCIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Archivo: Documentacion/caso_negocio.txt
Estado: ✅ Leído correctamente

Requerimientos Funcionales Identificados: X
  RF-001: [Descripción breve]
  RF-002: [Descripción breve]
  ...

Requerimientos No Funcionales Identificados: X
  RNF-001: [Descripción breve]
  ...

Reglas de Negocio Identificadas: X
  RN-001: [Descripción breve]
  ...

Casos de Uso Principales: X
  CU-001: [Descripción breve]
  ...
```

### 3. Investigación de Librerías

```
🔍 INVESTIGACIÓN DE LIBRERÍAS (context7)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Librería: pytest
Versión recomendada: X.X.X
Uso: Testing framework principal

Librería: pytest-cov
Versión recomendada: X.X.X
Uso: Medición de cobertura

[... más librerías investigadas]
```

### 4. Arquitectura de Tests

```
🏗️ ARQUITECTURA DE TESTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

tests/
├── unit/                    # Tests de Dominio
│   ├── entities/
│   ├── value_objects/
│   └── domain_services/
├── integration/             # Tests de Infraestructura
│   └── repositories/
└── functional/              # Tests End-to-End
    └── use_cases/

Total de archivos de test: X
Total de tests planeados: X
```

### 5. Matriz de Trazabilidad

```
📊 MATRIZ DE TRAZABILIDAD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Requerimiento     | Tests Asociados                      | Cobertura
──────────────────|────────────────────────────────────--|──────────
RF-001            | test_registrar_libro                 | 100%
                  | test_isbn_unico                      |
                  | test_buscar_libro_por_isbn           |
──────────────────|────────────────────────────────────--|──────────
RF-002            | test_registrar_usuario               | 100%
                  | test_dni_unico                       |
...
```

### 6. Generación de Tests

```
✍️ GENERANDO TESTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[CREAR] tests/unit/entities/test_libro.py
  ✓ test_crear_libro_valido
  ✓ test_isbn_invalido_longitud
  ✓ test_titulo_vacio
  ✓ test_año_invalido_menor_1500
  ✓ test_año_invalido_mayor_actual

[CREAR] tests/unit/value_objects/test_isbn.py
  ✓ test_isbn_10_digitos_valido
  ✓ test_isbn_13_digitos_valido
  ✓ test_isbn_formato_invalido
...

Total: X tests creados
```

### 7. Verificación de Tests en Rojo

```
🔴 VERIFICACIÓN: TESTS EN ROJO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ejecutando: uv run pytest --collect-only

Tests recolectados: X

Ejecutando: uv run pytest

RESULTADO: ❌ X tests FALLARON (como se esperaba)

Los tests están correctamente en ROJO porque la implementación no existe.
```

### 8. Resumen Final

```
✅ FASE TDD COMPLETADA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Requerimientos analizados:           X
Tests generados:                     X
  - Unitarios:                       X
  - Integración:                     X
  - Funcionales:                     X

Cobertura de requerimientos:        100%
Estado de tests:                    🔴 ROJO (esperado)

Documentación generada:
  ✓ Documentacion/analisis_tdd.md

Librerías investigadas:
  ✓ pytest (versión X.X.X)
  ✓ pytest-cov (versión X.X.X)
  ✓ pytest-mock (versión X.X.X)

🎯 SIGUIENTE PASO: Experto DDD debe implementar código para poner tests en VERDE
```

## Formato de Mensajes

- **Títulos de sección**: Emojis + MAYÚSCULAS + línea separadora
- **Listas**: Símbolos Unicode (✓, ✗, →, •)
- **Estado**: Emojis descriptivos (✅ ❌ 🔴 🟢 ⚠️)
- **Progreso**: Barras de texto cuando sea aplicable
- **Código**: Bloques de código con sintaxis resaltada
- **Diagramas**: ASCII art simple o descripción textual clara

## Tonalidad

- Técnico y preciso
- Orientado a análisis exhaustivo
- Foco en cobertura 100% de requerimientos
- Detallado en trazabilidad
