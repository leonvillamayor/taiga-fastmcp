#!/bin/bash
# Script de validación exhaustiva para Experto TDD
# Valida TODOS los archivos generados y su contenido

set -e

echo "=========================================="
echo "🔍 VALIDACIÓN EXHAUSTIVA: EXPERTO TDD"
echo "=========================================="

ERRORS=0
WARNINGS=0

# Función para reportar error
error() {
    echo "❌ ERROR: $1"
    ERRORS=$((ERRORS + 1))
}

# Función para reportar warning
warning() {
    echo "⚠️  WARNING: $1"
    WARNINGS=$((WARNINGS + 1))
}

# Función para reportar éxito
success() {
    echo "✅ $1"
}

echo ""
echo "📁 VERIFICANDO ESTRUCTURA DE ARCHIVOS..."
echo ""

# 1. Verificar archivos de documentación OBLIGATORIOS
echo "1️⃣ Documentación del análisis:"
if [ ! -f "Documentacion/analisis_tdd.md" ]; then
    error "No existe Documentacion/analisis_tdd.md"
else
    success "Existe Documentacion/analisis_tdd.md"

    # Validar contenido del análisis
    echo "   Validando contenido..."

    if ! grep -q "Requerimientos Identificados" "Documentacion/analisis_tdd.md"; then
        error "analisis_tdd.md no contiene sección 'Requerimientos Identificados'"
    fi

    if ! grep -q "Matriz de Trazabilidad" "Documentacion/analisis_tdd.md"; then
        error "analisis_tdd.md no contiene 'Matriz de Trazabilidad'"
    fi

    if ! grep -q "Arquitectura de Tests" "Documentacion/analisis_tdd.md"; then
        error "analisis_tdd.md no contiene 'Arquitectura de Tests'"
    fi

    # Contar requerimientos identificados
    RF_COUNT=$(grep -c "^### RF-" "Documentacion/analisis_tdd.md" || echo "0")
    RNF_COUNT=$(grep -c "^### RNF-" "Documentacion/analisis_tdd.md" || echo "0")

    if [ "$RF_COUNT" -eq 0 ]; then
        error "No se identificaron requerimientos funcionales (RF-XXX)"
    else
        success "Identificados $RF_COUNT requerimientos funcionales"
    fi

    if [ "$RNF_COUNT" -eq 0 ]; then
        warning "No se identificaron requerimientos no funcionales (RNF-XXX)"
    else
        success "Identificados $RNF_COUNT requerimientos no funcionales"
    fi
fi

echo ""
echo "2️⃣ Documentación de herramientas:"
if [ ! -f "Documentacion/herramientas_testing.md" ]; then
    error "No existe Documentacion/herramientas_testing.md"
else
    success "Existe Documentacion/herramientas_testing.md"

    # Validar que menciona pytest
    if ! grep -qi "pytest" "Documentacion/herramientas_testing.md"; then
        error "herramientas_testing.md no menciona pytest"
    fi

    # Validar que tiene ejemplos de uso
    if ! grep -q "\`\`\`" "Documentacion/herramientas_testing.md"; then
        warning "herramientas_testing.md no contiene ejemplos de código"
    fi
fi

echo ""
echo "3️⃣ Guía de tests:"
if [ ! -f "Documentacion/guia_tests.md" ]; then
    error "No existe Documentacion/guia_tests.md"
else
    success "Existe Documentacion/guia_tests.md"

    # Validar contenido
    if ! grep -q "Ejecutar Tests" "Documentacion/guia_tests.md"; then
        error "guia_tests.md no tiene sección 'Ejecutar Tests'"
    fi

    if ! grep -q "Requerimientos Cubiertos" "Documentacion/guia_tests.md"; then
        warning "guia_tests.md no tiene matriz de 'Requerimientos Cubiertos'"
    fi
fi

echo ""
echo "📦 VERIFICANDO ESTRUCTURA DE TESTS..."
echo ""

# 4. Verificar estructura de directorios de tests
echo "4️⃣ Estructura de directorios:"
if [ ! -d "tests" ]; then
    error "No existe el directorio tests/"
else
    success "Existe directorio tests/"

    # Verificar subdirectorios
    if [ ! -d "tests/unit" ]; then
        error "No existe tests/unit/"
    else
        success "Existe tests/unit/"
    fi

    if [ ! -d "tests/integration" ]; then
        warning "No existe tests/integration/ (puede no ser necesario)"
    else
        success "Existe tests/integration/"
    fi

    if [ ! -d "tests/functional" ]; then
        warning "No existe tests/functional/ (puede no ser necesario)"
    else
        success "Existe tests/functional/"
    fi

    # Verificar conftest.py
    if [ ! -f "tests/conftest.py" ]; then
        error "No existe tests/conftest.py (fixtures globales)"
    else
        success "Existe tests/conftest.py"
    fi
fi

echo ""
echo "🧪 VERIFICANDO ARCHIVOS DE TEST..."
echo ""

# 5. Contar y validar archivos de test
echo "5️⃣ Archivos de test:"
TEST_FILES=$(find tests -name "test_*.py" 2>/dev/null | wc -l)

if [ "$TEST_FILES" -eq 0 ]; then
    error "No se encontraron archivos test_*.py"
else
    success "Encontrados $TEST_FILES archivos de test"

    # Validar cada archivo de test
    echo "   Validando contenido de cada test..."

    for test_file in $(find tests -name "test_*.py" 2>/dev/null); do
        echo "   📄 Validando: $test_file"

        # Verificar que tiene imports
        if ! grep -q "^import\|^from" "$test_file"; then
            warning "$test_file no tiene imports (puede estar vacío)"
        fi

        # Verificar que tiene al menos una función test
        if ! grep -q "^def test_" "$test_file"; then
            error "$test_file no contiene ninguna función test_*()"
        else
            TEST_FUNC_COUNT=$(grep -c "^def test_" "$test_file")
            success "   → $TEST_FUNC_COUNT funciones de test"
        fi

        # Verificar que las funciones tienen docstrings
        if ! grep -q '"""' "$test_file" && ! grep -q "'''" "$test_file"; then
            warning "$test_file: los tests no tienen docstrings"
        fi

        # Verificar que usa pytest
        if grep -q "import unittest" "$test_file"; then
            warning "$test_file usa unittest en lugar de pytest"
        fi

        # Verificar que tiene asserts
        if ! grep -q "assert " "$test_file"; then
            error "$test_file no contiene ningún assert"
        fi
    done
fi

echo ""
echo "⚙️  VERIFICANDO CONFIGURACIÓN..."
echo ""

# 6. Verificar pyproject.toml
echo "6️⃣ Configuración de pytest:"
if [ ! -f "pyproject.toml" ]; then
    error "No existe pyproject.toml"
else
    success "Existe pyproject.toml"

    # Verificar configuración de pytest
    if ! grep -q "\[tool.pytest.ini_options\]" "pyproject.toml"; then
        error "pyproject.toml no tiene configuración de pytest"
    else
        success "Tiene configuración de pytest"
    fi

    # Verificar configuración de cobertura
    if ! grep -q "\[tool.coverage" "pyproject.toml"; then
        warning "pyproject.toml no tiene configuración de cobertura"
    else
        success "Tiene configuración de cobertura"
    fi

    # Verificar que está configurado para usar pytest-cov
    if ! grep -q "cov" "pyproject.toml"; then
        warning "pyproject.toml no menciona cobertura (pytest-cov)"
    fi
fi

echo ""
echo "🔴 VERIFICANDO QUE LOS TESTS ESTÁN EN ROJO..."
echo ""

# 7. Ejecutar pytest para verificar que los tests fallan (ROJO)
echo "7️⃣ Ejecución de tests (deben fallar - ROJO):"

if command -v uv &> /dev/null; then
    # Intentar recolectar tests
    if uv run pytest --collect-only > /dev/null 2>&1; then
        COLLECTED=$(uv run pytest --collect-only -q 2>/dev/null | grep "test session starts" -A 1 | tail -1 || echo "0")
        success "Tests recolectados correctamente"
        echo "   Total de tests: $COLLECTED"
    else
        error "pytest no puede recolectar los tests (sintaxis incorrecta?)"
    fi

    # Ejecutar tests (deberían fallar)
    echo "   Ejecutando tests..."
    if uv run pytest -v --tb=no 2>&1 | tee /tmp/pytest_output.txt; then
        warning "⚠️  ALERTA: Los tests PASARON (deberían estar en ROJO)"
        echo "   Esto puede indicar que:"
        echo "   - Los tests son triviales"
        echo "   - El código ya está implementado"
        echo "   - Los tests no validan correctamente"
    else
        success "✅ Los tests FALLAN correctamente (están en ROJO)"

        # Contar tests fallidos
        FAILED=$(grep -c "FAILED" /tmp/pytest_output.txt || echo "0")
        echo "   Tests fallidos: $FAILED"
    fi
else
    warning "uv no está instalado, no se pueden ejecutar tests"
fi

echo ""
echo "📊 VERIFICANDO TRAZABILIDAD..."
echo ""

# 8. Verificar trazabilidad requerimientos -> tests
echo "8️⃣ Matriz de trazabilidad:"

if [ -f "Documentacion/analisis_tdd.md" ]; then
    # Extraer todos los IDs de requerimientos
    REQ_IDS=$(grep -o "RF-[0-9]\{3\}\|RNF-[0-9]\{3\}" "Documentacion/analisis_tdd.md" | sort -u)

    if [ -z "$REQ_IDS" ]; then
        error "No se encontraron IDs de requerimientos (RF-XXX, RNF-XXX)"
    else
        TOTAL_REQS=$(echo "$REQ_IDS" | wc -l)
        echo "   Total de requerimientos: $TOTAL_REQS"

        # Verificar que cada requerimiento tiene tests asociados
        UNCOVERED=0
        for req_id in $REQ_IDS; do
            # Buscar el requerimiento en tests (en docstrings o comentarios)
            if ! grep -r "$req_id" tests/ > /dev/null 2>&1; then
                warning "Requerimiento $req_id no está cubierto por ningún test"
                UNCOVERED=$((UNCOVERED + 1))
            fi
        done

        if [ $UNCOVERED -eq 0 ]; then
            success "Todos los requerimientos están cubiertos por tests"
        else
            error "$UNCOVERED requerimientos sin cobertura de tests"
        fi
    fi
fi

echo ""
echo "📝 VERIFICANDO CALIDAD DE DOCUMENTACIÓN..."
echo ""

# 9. Verificar calidad de la documentación
echo "9️⃣ Calidad de documentación:"

for doc_file in Documentacion/analisis_tdd.md Documentacion/herramientas_testing.md Documentacion/guia_tests.md; do
    if [ -f "$doc_file" ]; then
        # Verificar longitud mínima (documentación exhaustiva)
        LINES=$(wc -l < "$doc_file")
        if [ "$LINES" -lt 50 ]; then
            warning "$doc_file tiene solo $LINES líneas (parece incompleto)"
        else
            success "$doc_file: $LINES líneas (documentación exhaustiva)"
        fi

        # Verificar que tiene títulos markdown
        if ! grep -q "^#" "$doc_file"; then
            error "$doc_file no tiene estructura de títulos markdown"
        fi
    fi
done

echo ""
echo "=========================================="
echo "📊 RESUMEN DE VALIDACIÓN"
echo "=========================================="
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "🎉 VALIDACIÓN COMPLETA: TODO PERFECTO"
    echo ""
    echo "✅ 0 errores"
    echo "✅ 0 warnings"
    echo ""
    echo "El Experto TDD completó su trabajo correctamente."
    echo "Se puede proceder con el Experto DDD."
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "✅ VALIDACIÓN COMPLETADA CON WARNINGS"
    echo ""
    echo "✅ 0 errores"
    echo "⚠️  $WARNINGS warnings"
    echo ""
    echo "El Experto TDD completó su trabajo con algunas observaciones."
    echo "Revisar warnings antes de continuar."
    exit 0
else
    echo "❌ VALIDACIÓN FALLIDA"
    echo ""
    echo "❌ $ERRORS errores"
    echo "⚠️  $WARNINGS warnings"
    echo ""
    echo "El Experto TDD NO completó correctamente su trabajo."
    echo "Revisar y corregir los errores antes de continuar."
    exit 1
fi
