#!/bin/bash
# Script de validación exhaustiva para Experto DDD
# Valida TODOS los archivos generados y su contenido

set -e

echo "=========================================="
echo "🔍 VALIDACIÓN EXHAUSTIVA: EXPERTO DDD"
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
echo "📁 VERIFICANDO ESTRUCTURA DE CÓDIGO..."
echo ""

# 1. Verificar estructura DDD completa
echo "1️⃣ Estructura de directorios DDD:"

# Verificar src/
if [ ! -d "src" ]; then
    error "No existe el directorio src/"
else
    success "Existe directorio src/"
fi

# Capa Domain
echo ""
echo "   🏛️ Capa Domain:"
if [ ! -d "src/domain" ]; then
    error "No existe src/domain/ (capa de dominio)"
else
    success "Existe src/domain/"

    # Subdirectorios de domain
    for subdir in entities value_objects; do
        if [ ! -d "src/domain/$subdir" ]; then
            warning "No existe src/domain/$subdir/"
        else
            success "  → src/domain/$subdir/"
        fi
    done

    # Opcionales pero recomendados
    for subdir in aggregates domain_services repositories events; do
        if [ -d "src/domain/$subdir" ]; then
            success "  → src/domain/$subdir/ (opcional)"
        fi
    done
fi

# Capa Application
echo ""
echo "   📋 Capa Application:"
if [ ! -d "src/application" ]; then
    error "No existe src/application/ (capa de aplicación)"
else
    success "Existe src/application/"

    # Subdirectorios de application
    for subdir in use_cases; do
        if [ ! -d "src/application/$subdir" ]; then
            warning "No existe src/application/$subdir/"
        else
            success "  → src/application/$subdir/"
        fi
    done

    # Opcionales
    for subdir in commands queries dtos; do
        if [ -d "src/application/$subdir" ]; then
            success "  → src/application/$subdir/ (opcional)"
        fi
    done
fi

# Capa Infrastructure
echo ""
echo "   🔧 Capa Infrastructure:"
if [ ! -d "src/infrastructure" ]; then
    warning "No existe src/infrastructure/ (puede no ser necesario)"
else
    success "Existe src/infrastructure/"

    # Subdirectorios de infrastructure
    for subdir in persistence adapters config; do
        if [ -d "src/infrastructure/$subdir" ]; then
            success "  → src/infrastructure/$subdir/"
        fi
    done
fi

echo ""
echo "🐍 VERIFICANDO ARCHIVOS PYTHON..."
echo ""

# 2. Verificar archivos __init__.py
echo "2️⃣ Archivos __init__.py:"
MISSING_INIT=0

for dir in $(find src -type d); do
    if [ ! -f "$dir/__init__.py" ]; then
        warning "Falta $dir/__init__.py"
        MISSING_INIT=$((MISSING_INIT + 1))
    fi
done

if [ $MISSING_INIT -eq 0 ]; then
    success "Todos los directorios tienen __init__.py"
else
    warning "$MISSING_INIT directorios sin __init__.py"
fi

echo ""
echo "3️⃣ Archivos de código Python:"

# Contar archivos Python (excluyendo __init__.py)
PY_FILES=$(find src -name "*.py" ! -name "__init__.py" | wc -l)

if [ "$PY_FILES" -eq 0 ]; then
    error "No se encontraron archivos Python en src/"
else
    success "Encontrados $PY_FILES archivos Python"

    # Validar cada archivo Python
    echo "   Validando contenido..."

    for py_file in $(find src -name "*.py" ! -name "__init__.py"); do
        echo "   📄 $py_file"

        # Verificar que tiene contenido
        if [ ! -s "$py_file" ]; then
            error "$py_file está vacío"
            continue
        fi

        # Verificar docstrings de módulo
        if ! head -10 "$py_file" | grep -q '"""' && ! head -10 "$py_file" | grep -q "'''"; then
            warning "$py_file no tiene docstring de módulo"
        fi

        # Verificar que tiene clases o funciones
        if ! grep -q "^class \|^def " "$py_file"; then
            warning "$py_file no tiene clases ni funciones"
        fi

        # Contar clases
        CLASS_COUNT=$(grep -c "^class " "$py_file" || echo "0")
        if [ "$CLASS_COUNT" -gt 0 ]; then
            success "   → $CLASS_COUNT clases"

            # Verificar PascalCase en clases
            if grep "^class " "$py_file" | grep -q "[a-z]"; then
                # Buscar clases que no empiezan con mayúscula
                if grep "^class [a-z]" "$py_file" > /dev/null; then
                    warning "$py_file: clase no sigue PascalCase"
                fi
            fi
        fi

        # Contar funciones
        FUNC_COUNT=$(grep -c "^def " "$py_file" || echo "0")
        if [ "$FUNC_COUNT" -gt 0 ]; then
            success "   → $FUNC_COUNT funciones"
        fi

        # Verificar type hints (recomendado)
        if ! grep -q "-> " "$py_file"; then
            warning "$py_file no usa type hints"
        fi
    done
fi

echo ""
echo "🏗️ VERIFICANDO PRINCIPIOS DDD..."
echo ""

# 4. Verificar entidades
echo "4️⃣ Entidades (Entities):"
if [ -d "src/domain/entities" ]; then
    ENTITY_COUNT=$(find src/domain/entities -name "*.py" ! -name "__init__.py" | wc -l)

    if [ "$ENTITY_COUNT" -eq 0 ]; then
        warning "No hay entidades en src/domain/entities/"
    else
        success "$ENTITY_COUNT archivos de entidades"

        # Verificar que tienen ID único
        for entity_file in $(find src/domain/entities -name "*.py" ! -name "__init__.py"); do
            if ! grep -q "id.*:" "$entity_file"; then
                warning "$(basename $entity_file): la entidad debería tener un campo 'id'"
            fi
        done
    fi
fi

# 5. Verificar Value Objects
echo ""
echo "5️⃣ Value Objects:"
if [ -d "src/domain/value_objects" ]; then
    VO_COUNT=$(find src/domain/value_objects -name "*.py" ! -name "__init__.py" | wc -l)

    if [ "$VO_COUNT" -eq 0 ]; then
        warning "No hay value objects en src/domain/value_objects/"
    else
        success "$VO_COUNT archivos de value objects"

        # Verificar que son inmutables (frozen=True en dataclass)
        for vo_file in $(find src/domain/value_objects -name "*.py" ! -name "__init__.py"); do
            if grep -q "@dataclass" "$vo_file"; then
                if ! grep -q "frozen=True" "$vo_file"; then
                    warning "$(basename $vo_file): value object debería ser inmutable (frozen=True)"
                fi
            fi
        done
    fi
fi

# 6. Verificar Use Cases
echo ""
echo "6️⃣ Use Cases:"
if [ -d "src/application/use_cases" ]; then
    UC_COUNT=$(find src/application/use_cases -name "*.py" ! -name "__init__.py" | wc -l)

    if [ "$UC_COUNT" -eq 0 ]; then
        error "No hay use cases en src/application/use_cases/"
    else
        success "$UC_COUNT archivos de use cases"

        # Verificar que tienen método ejecutar/execute
        for uc_file in $(find src/application/use_cases -name "*.py" ! -name "__init__.py"); do
            if ! grep -q "def ejecutar\|def execute" "$uc_file"; then
                warning "$(basename $uc_file): use case debería tener método ejecutar() o execute()"
            fi
        done
    fi
fi

# 7. Verificar Repositorios (interfaces)
echo ""
echo "7️⃣ Repositorios (interfaces en Domain):"
if [ -d "src/domain/repositories" ]; then
    REPO_COUNT=$(find src/domain/repositories -name "*.py" ! -name "__init__.py" | wc -l)

    if [ "$REPO_COUNT" -gt 0 ]; then
        success "$REPO_COUNT interfaces de repositorios"

        # Verificar que son interfaces (ABC)
        for repo_file in $(find src/domain/repositories -name "*.py" ! -name "__init__.py"); do
            if ! grep -q "ABC\|abstractmethod" "$repo_file"; then
                error "$(basename $repo_file): repositorio en domain debe ser interfaz (ABC)"
            fi
        done
    fi
fi

# 8. Verificar implementaciones de Repositorios
echo ""
echo "8️⃣ Repositorios (implementaciones en Infrastructure):"
if [ -d "src/infrastructure/persistence" ]; then
    IMPL_COUNT=$(find src/infrastructure/persistence -name "*.py" ! -name "__init__.py" | wc -l)

    if [ "$IMPL_COUNT" -gt 0 ]; then
        success "$IMPL_COUNT archivos de persistencia"
    fi
fi

echo ""
echo "🔗 VERIFICANDO DEPENDENCIAS ENTRE CAPAS..."
echo ""

# 9. Verificar que Domain NO depende de Application ni Infrastructure
echo "9️⃣ Independencia de la capa Domain:"

DOMAIN_VIOLATIONS=0

for domain_file in $(find src/domain -name "*.py" 2>/dev/null); do
    # Buscar imports de application o infrastructure
    if grep -q "from src.application\|import src.application\|from src.infrastructure\|import src.infrastructure" "$domain_file"; then
        error "$(basename $domain_file): Domain importa de Application o Infrastructure (violación DDD)"
        DOMAIN_VIOLATIONS=$((DOMAIN_VIOLATIONS + 1))
    fi
done

if [ $DOMAIN_VIOLATIONS -eq 0 ]; then
    success "La capa Domain NO depende de Application ni Infrastructure ✅"
fi

# 10. Verificar que Application NO depende de Infrastructure
echo ""
echo "🔟 Independencia de la capa Application:"

APP_VIOLATIONS=0

if [ -d "src/application" ]; then
    for app_file in $(find src/application -name "*.py" 2>/dev/null); do
        if grep -q "from src.infrastructure\|import src.infrastructure" "$app_file"; then
            warning "$(basename $app_file): Application importa de Infrastructure (no crítico pero revisar)"
            APP_VIOLATIONS=$((APP_VIOLATIONS + 1))
        fi
    done

    if [ $APP_VIOLATIONS -eq 0 ]; then
        success "La capa Application NO depende directamente de Infrastructure ✅"
    fi
fi

echo ""
echo "✅ VERIFICANDO QUE LOS TESTS ESTÁN EN VERDE..."
echo ""

# 11. Ejecutar pytest para verificar que TODOS los tests pasan
echo "1️⃣1️⃣ Ejecución de tests (deben PASAR - VERDE):"

if command -v uv &> /dev/null; then
    echo "   Ejecutando pytest..."

    if uv run pytest -v --tb=short 2>&1 | tee /tmp/pytest_ddd_output.txt; then
        success "✅ TODOS LOS TESTS PASAN (VERDE)"

        # Contar tests pasados
        PASSED=$(grep -c "PASSED" /tmp/pytest_ddd_output.txt || echo "0")
        echo "   Tests pasados: $PASSED"
    else
        error "❌ HAY TESTS FALLANDO"
        echo ""
        echo "El Experto DDD debe poner TODOS los tests en verde."
        echo "Revisa el output de pytest arriba para ver qué falló."

        FAILED=$(grep -c "FAILED" /tmp/pytest_ddd_output.txt || echo "0")
        echo "   Tests fallidos: $FAILED"
    fi
else
    error "uv no está instalado, no se pueden ejecutar tests"
fi

echo ""
echo "📊 VERIFICANDO COBERTURA DE CÓDIGO..."
echo ""

# 12. Verificar cobertura >= 80%
echo "1️⃣2️⃣ Cobertura de código (objetivo: >= 80%):"

if command -v uv &> /dev/null; then
    if uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80 2>&1 | tee /tmp/coverage_ddd.txt; then
        success "✅ Cobertura >= 80%"

        # Extraer porcentaje de cobertura
        COVERAGE=$(grep "TOTAL" /tmp/coverage_ddd.txt | awk '{print $NF}' || echo "N/A")
        echo "   Cobertura total: $COVERAGE"
    else
        error "❌ Cobertura < 80%"

        COVERAGE=$(grep "TOTAL" /tmp/coverage_ddd.txt | awk '{print $NF}' || echo "N/A")
        echo "   Cobertura actual: $COVERAGE"
        echo "   Se requiere >= 80%"
    fi
else
    warning "uv no está instalado, no se puede verificar cobertura"
fi

echo ""
echo "📝 VERIFICANDO DOCUMENTACIÓN ARQUITECTURA..."
echo ""

# 13. Verificar documentación de arquitectura
echo "1️⃣3️⃣ Documentación de arquitectura DDD:"

if [ ! -f "Documentacion/arquitectura_ddd.md" ]; then
    error "No existe Documentacion/arquitectura_ddd.md"
else
    success "Existe Documentacion/arquitectura_ddd.md"

    # Verificar contenido
    if ! grep -q "Domain" "Documentacion/arquitectura_ddd.md"; then
        error "arquitectura_ddd.md no describe la capa Domain"
    fi

    if ! grep -q "Application" "Documentacion/arquitectura_ddd.md"; then
        error "arquitectura_ddd.md no describe la capa Application"
    fi

    # Verificar diagramas
    if ! grep -q "mermaid\|```" "Documentacion/arquitectura_ddd.md"; then
        warning "arquitectura_ddd.md no tiene diagramas"
    else
        success "Tiene diagramas de arquitectura"
    fi

    # Verificar longitud
    LINES=$(wc -l < "Documentacion/arquitectura_ddd.md")
    if [ "$LINES" -lt 50 ]; then
        warning "arquitectura_ddd.md tiene solo $LINES líneas (parece incompleto)"
    else
        success "Documentación exhaustiva ($LINES líneas)"
    fi
fi

echo ""
echo "🔍 VERIFICANDO CALIDAD DE CÓDIGO..."
echo ""

# 14. Verificar que NO se modificaron los tests
echo "1️⃣4️⃣ Integridad de los tests (no deben modificarse):"

# Esta verificación requeriría comparar con versión anterior
# Por ahora solo verificamos que existen tests
if [ -d "tests" ]; then
    TEST_COUNT=$(find tests -name "test_*.py" | wc -l)
    if [ "$TEST_COUNT" -eq 0 ]; then
        error "No hay tests (fueron eliminados?)"
    else
        success "Existen $TEST_COUNT archivos de test"
    fi
fi

# 15. Verificar que no hay imports circulares
echo ""
echo "1️⃣5️⃣ Verificando imports circulares:"

# Herramienta simple: verificar que src/__init__.py no importa todo
if [ -f "src/__init__.py" ]; then
    if grep -q "from .* import \*" "src/__init__.py"; then
        warning "src/__init__.py usa import * (puede causar problemas)"
    fi
fi

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
    echo "El Experto DDD completó su trabajo correctamente:"
    echo "  ✅ Tests en VERDE"
    echo "  ✅ Cobertura >= 80%"
    echo "  ✅ Arquitectura DDD correcta"
    echo ""
    echo "Se puede proceder con el Experto Documentación."
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "✅ VALIDACIÓN COMPLETADA CON WARNINGS"
    echo ""
    echo "✅ 0 errores"
    echo "⚠️  $WARNINGS warnings"
    echo ""
    echo "El Experto DDD completó su trabajo con algunas observaciones."
    echo "Revisar warnings antes de continuar."
    exit 0
else
    echo "❌ VALIDACIÓN FALLIDA"
    echo ""
    echo "❌ $ERRORS errores"
    echo "⚠️  $WARNINGS warnings"
    echo ""
    echo "El Experto DDD NO completó correctamente su trabajo."
    echo ""
    echo "Errores críticos que deben corregirse:"
    if grep -q "HAY TESTS FALLANDO" /tmp/pytest_ddd_output.txt 2>/dev/null; then
        echo "  ❌ Tests NO están en verde"
    fi
    if grep -q "Cobertura < 80%" /tmp/coverage_ddd.txt 2>/dev/null; then
        echo "  ❌ Cobertura insuficiente"
    fi
    echo ""
    exit 1
fi
