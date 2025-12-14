# Output Style: DDD Expert

Este estilo de salida está optimizado para el Experto DDD durante la fase de implementación.

## Estructura de Output

### 1. Encabezado de Fase
```
╔═══════════════════════════════════════════════════════════╗
║         FASE DDD - IMPLEMENTACIÓN Y TESTS EN VERDE        ║
╔═══════════════════════════════════════════════════════════╗
```

### 2. Análisis de Tests Existentes

```
📖 ANÁLISIS DE TESTS A IMPLEMENTAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total de tests en ROJO: X

Distribución por capa:
  Domain:          X tests
  Application:     X tests
  Infrastructure:  X tests

Prioridad de implementación:
  1. Domain (entidades, value objects, agregados)
  2. Application (casos de uso)
  3. Infrastructure (repositorios, adaptadores)
```

### 3. Investigación de Librerías

```
🔍 INVESTIGACIÓN DE LIBRERÍAS (context7)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Librería: pydantic
Versión: X.X.X
Uso: Validación y modelado de Value Objects

Librería: sqlalchemy
Versión: X.X.X
Uso: ORM para capa de persistencia (si es necesario)

[... más librerías]
```

### 4. Arquitectura DDD

```
🏗️ ARQUITECTURA DDD A IMPLEMENTAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

src/
├── domain/
│   ├── entities/           # Objetos con identidad
│   │   ├── libro.py
│   │   ├── usuario.py
│   │   └── prestamo.py
│   ├── value_objects/      # Objetos inmutables
│   │   ├── isbn.py
│   │   ├── dni.py
│   │   └── email.py
│   ├── aggregates/         # Raíces de agregado
│   │   └── prestamo_aggregate.py
│   ├── domain_services/    # Lógica de dominio compleja
│   │   └── validador_prestamo.py
│   └── repositories/       # Interfaces (contratos)
│       ├── repositorio_libro.py
│       ├── repositorio_usuario.py
│       └── repositorio_prestamo.py
├── application/
│   ├── use_cases/          # Casos de uso
│   │   ├── registrar_libro.py
│   │   ├── registrar_usuario.py
│   │   ├── realizar_prestamo.py
│   │   └── devolver_libro.py
│   ├── commands/           # DTOs de entrada
│   └── queries/            # DTOs de consulta
└── infrastructure/
    ├── persistence/        # Implementación de repositorios
    │   ├── repositorio_libro_impl.py
    │   ├── repositorio_usuario_impl.py
    │   └── repositorio_prestamo_impl.py
    └── adapters/           # Adaptadores externos
        ├── cli/
        └── api/
```

### 5. Implementación Test por Test

```
⚙️ IMPLEMENTACIÓN EN PROGRESO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[CAPA: DOMAIN] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Implementando: src/domain/value_objects/isbn.py
  Tests objetivo:
    • test_isbn_10_digitos_valido        🔴 → 🟢
    • test_isbn_13_digitos_valido        🔴 → 🟢
    • test_isbn_formato_invalido         🔴 → 🟢

  Ejecutando: uv run pytest tests/unit/value_objects/test_isbn.py -v

  Resultado: ✅ 3/3 tests PASARON

─────────────────────────────────────────────────────────────

Implementando: src/domain/entities/libro.py
  Tests objetivo:
    • test_crear_libro_valido            🔴 → 🟢
    • test_isbn_unico                    🔴 → 🟢
    • test_titulo_vacio                  🔴 → 🟢
    • test_año_invalido                  🔴 → 🟢

  Ejecutando: uv run pytest tests/unit/entities/test_libro.py -v

  Resultado: ✅ 4/4 tests PASARON

─────────────────────────────────────────────────────────────

Progreso Domain Layer: [████████░░░░░░░░░░] 40% (X/Y tests)
```

### 6. Progreso General

```
📊 PROGRESO DE IMPLEMENTACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Capa               | Tests  | 🔴 Rojo | 🟢 Verde | Progreso
───────────────────|───────|─────────|──────────|-----------
Domain             |   45  |    12   |    33    | ████████░░ 73%
Application        |   28  |    28   |     0    | ░░░░░░░░░░  0%
Infrastructure     |   15  |    15   |     0    | ░░░░░░░░░░  0%
───────────────────|───────|─────────|──────────|-----------
TOTAL              |   88  |    55   |    33    | ███░░░░░░░ 38%

Cobertura actual: 45%
Objetivo: >= 80%
```

### 7. Reporte de Incoherencias (si las hay)

```
⚠️ INCOHERENCIAS DETECTADAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[INCOHERENCIA #1]
Archivo: tests/unit/test_prestamo.py
Test: test_prestamo_con_libro_no_disponible
Línea: 45

Problema:
  El test espera excepción LibroNoDisponibleError pero según
  el caso de negocio (RF-003) debe ser PrestamoInvalidoError

Requerimiento relacionado: RF-003, línea 52

Acción sugerida:
  Por favor revise el test o el caso de negocio para aclarar
  qué excepción específica debe lanzarse.

⛔ IMPLEMENTACIÓN PAUSADA hasta resolver incoherencia
```

### 8. Resumen de Cobertura

```
📈 REPORTE DE COBERTURA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ejecutando: uv run pytest --cov=src --cov-report=term-missing

Módulo                                    Cobertura    Líneas    Missing
──────────────────────────────────────────────────────────────────────────
src/domain/entities/libro.py                 100%        45
src/domain/entities/usuario.py               100%        38
src/domain/value_objects/isbn.py             100%        22
src/application/use_cases/realizar_prestamo  87%         56      34-38
src/infrastructure/persistence/repo_libro    73%         89      45-52, 67-71
──────────────────────────────────────────────────────────────────────────
TOTAL                                         87%       450

✅ CUMPLE objetivo >= 80%
```

### 9. Resumen Final

```
✅ FASE DDD COMPLETADA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tests implementados:                 X/X (100%)
  - Unitarios:                       X/X 🟢
  - Integración:                     X/X 🟢
  - Funcionales:                     X/X 🟢

Cobertura de código:                 XX%
Estado objetivo (>= 80%):            ✅ CUMPLIDO

Arquitectura DDD:
  ✓ Domain Layer completa
  ✓ Application Layer completa
  ✓ Infrastructure Layer completa
  ✓ Separación de responsabilidades clara
  ✓ Dependency Inversion aplicada

Librerías utilizadas:
  ✓ pydantic (versión X.X.X)
  ✓ [otras librerías]

Incoherencias detectadas:            0

🎯 SIGUIENTE PASO: Experto Documentación debe generar documentación completa
```

## Formato de Mensajes

- **Títulos de sección**: Emojis + MAYÚSCULAS + línea separadora
- **Progreso visual**: Barras de progreso ASCII
- **Estados**: 🔴 (rojo) → 🟢 (verde) para mostrar transición
- **Tablas**: ASCII tables para reportes estructurados
- **Alertas**: ⚠️ para incoherencias, ✅ para éxitos
- **Código**: Bloques con sintaxis resaltada

## Tonalidad

- Técnico y orientado a arquitectura
- Foco en separación de capas DDD
- Énfasis en progreso test por test
- Transparente sobre incoherencias
- Preciso en métricas de cobertura
