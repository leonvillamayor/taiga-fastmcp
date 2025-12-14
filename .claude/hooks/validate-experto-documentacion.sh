#!/bin/bash
# Script de validación exhaustiva para Experto Documentación
# Valida TODOS los archivos de documentación generados y su contenido

set -e

echo "=========================================="
echo "🔍 VALIDACIÓN EXHAUSTIVA: EXPERTO DOCUMENTACIÓN"
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
echo "📄 VERIFICANDO DOCUMENTACIÓN PRINCIPAL..."
echo ""

# 1. Verificar README.md
echo "1️⃣ README.md:"
if [ ! -f "README.md" ]; then
    error "No existe README.md"
else
    success "Existe README.md"

    # Verificar contenido del README
    echo "   Validando contenido..."

    # Secciones obligatorias
    REQUIRED_SECTIONS=(
        "Descripción"
        "Arquitectura"
        "Inicio Rápido\|Quick Start\|Instalación"
        "Uso"
        "Testing\|Tests"
        "Documentación"
    )

    for section in "${REQUIRED_SECTIONS[@]}"; do
        if ! grep -qi "$section" "README.md"; then
            error "README.md no tiene sección: $section"
        else
            success "  ✓ Sección: $section"
        fi
    done

    # Verificar que tiene ejemplos de código
    if ! grep -q "\`\`\`" "README.md"; then
        error "README.md no tiene ejemplos de código"
    else
        CODE_BLOCKS=$(grep -c "\`\`\`" "README.md")
        CODE_BLOCKS=$((CODE_BLOCKS / 2))  # Dividir por 2 (apertura y cierre)
        success "  → $CODE_BLOCKS bloques de código"
    fi

    # Verificar que tiene diagramas mermaid
    if ! grep -q "mermaid" "README.md"; then
        warning "README.md no tiene diagramas mermaid"
    else
        MERMAID_COUNT=$(grep -c "\`\`\`mermaid" "README.md" || echo "0")
        success "  → $MERMAID_COUNT diagramas mermaid"
    fi

    # Verificar badges (opcional pero recomendado)
    if ! grep -q "badge\|\!\[.*\](https://img.shields.io" "README.md"; then
        warning "README.md no tiene badges de estado"
    else
        success "  → Tiene badges de estado"
    fi

    # Verificar tabla de contenidos
    if ! grep -qi "tabla de contenidos\|table of contents\|TOC" "README.md"; then
        warning "README.md no tiene tabla de contenidos"
    fi

    # Verificar longitud mínima
    LINES=$(wc -l < "README.md")
    if [ "$LINES" -lt 100 ]; then
        warning "README.md tiene solo $LINES líneas (debería ser más exhaustivo)"
    else
        success "  → $LINES líneas (documentación completa)"
    fi

    # Verificar que menciona el caso de negocio
    if [ -f "Documentacion/caso_negocio.txt" ]; then
        # Leer primera línea del caso de negocio
        FIRST_LINE=$(head -1 "Documentacion/caso_negocio.txt" || echo "")
        if [ -n "$FIRST_LINE" ]; then
            # Buscar si el README menciona algo relacionado
            if ! grep -qi "caso de negocio\|business case\|requerimiento" "README.md"; then
                warning "README.md no referencia el caso de negocio"
            fi
        fi
    fi
fi

echo ""
echo "2️⃣ guia_uso.md:"
if [ ! -f "guia_uso.md" ]; then
    error "No existe guia_uso.md"
else
    success "Existe guia_uso.md"

    # Verificar contenido
    echo "   Validando contenido..."

    # Secciones obligatorias para guía de uso
    GUIDE_SECTIONS=(
        "Introducción\|Introduction"
        "Instalación\|Installation"
        "Configuración\|Configuration"
        "Ejemplos\|Examples"
        "Casos de Uso\|Use Cases"
        "FAQ\|Preguntas Frecuentes"
        "Troubleshooting\|Solución de Problemas"
    )

    for section in "${GUIDE_SECTIONS[@]}"; do
        if ! grep -qi "$section" "guia_uso.md"; then
            error "guia_uso.md no tiene sección: $section"
        else
            success "  ✓ Sección: $section"
        fi
    done

    # Verificar ejemplos ejecutables
    if ! grep -q "\`\`\`python" "guia_uso.md" && ! grep -q "\`\`\`bash" "guia_uso.md"; then
        error "guia_uso.md no tiene ejemplos ejecutables"
    else
        PYTHON_EXAMPLES=$(grep -c "\`\`\`python" "guia_uso.md" || echo "0")
        BASH_EXAMPLES=$(grep -c "\`\`\`bash" "guia_uso.md" || echo "0")
        success "  → $PYTHON_EXAMPLES ejemplos Python"
        success "  → $BASH_EXAMPLES ejemplos Bash"
    fi

    # Verificar paso a paso
    if ! grep -qi "paso 1\|step 1\|1\." "guia_uso.md"; then
        warning "guia_uso.md no tiene instrucciones paso a paso"
    fi

    # Verificar longitud
    LINES=$(wc -l < "guia_uso.md")
    if [ "$LINES" -lt 200 ]; then
        warning "guia_uso.md tiene solo $LINES líneas (debería ser más exhaustivo)"
    else
        success "  → $LINES líneas (guía completa)"
    fi
fi

echo ""
echo "📚 VERIFICANDO DOCUMENTACIÓN ADICIONAL..."
echo ""

# 3. Verificar documentación de estructura
echo "3️⃣ Documentacion/estructura_proyecto.md:"
if [ ! -f "Documentacion/estructura_proyecto.md" ]; then
    warning "No existe Documentacion/estructura_proyecto.md (recomendado)"
else
    success "Existe Documentacion/estructura_proyecto.md"

    # Verificar que documenta la estructura
    if ! grep -q "src/\|tests/\|Documentacion/" "Documentacion/estructura_proyecto.md"; then
        error "estructura_proyecto.md no documenta la estructura de directorios"
    fi

    # Verificar diagramas
    if ! grep -q "mermaid\|\`\`\`" "Documentacion/estructura_proyecto.md"; then
        warning "estructura_proyecto.md no tiene diagramas de estructura"
    fi
fi

# 4. Verificar que se mantiene la documentación TDD
echo ""
echo "4️⃣ Documentación TDD (debe mantenerse):"
for doc_file in analisis_tdd.md herramientas_testing.md guia_tests.md; do
    if [ ! -f "Documentacion/$doc_file" ]; then
        error "Se eliminó Documentacion/$doc_file (debe mantenerse)"
    else
        success "Preservado: Documentacion/$doc_file"
    fi
done

# 5. Verificar que se mantiene la documentación DDD
echo ""
echo "5️⃣ Documentación DDD (debe mantenerse):"
if [ ! -f "Documentacion/arquitectura_ddd.md" ]; then
    error "Se eliminó Documentacion/arquitectura_ddd.md (debe mantenerse)"
else
    success "Preservado: Documentacion/arquitectura_ddd.md"
fi

echo ""
echo "🎨 VERIFICANDO CALIDAD DE FORMATO..."
echo ""

# 6. Verificar formato Markdown correcto
echo "6️⃣ Formato Markdown:"

MD_FILES=$(find . -name "*.md" ! -path "./node_modules/*" ! -path "./.git/*" 2>/dev/null)
MD_COUNT=$(echo "$MD_FILES" | wc -l)

success "Encontrados $MD_COUNT archivos Markdown"

for md_file in $MD_FILES; do
    echo "   Validando: $md_file"

    # Verificar que tiene títulos
    if ! grep -q "^#" "$md_file"; then
        warning "$md_file no tiene títulos markdown"
    fi

    # Verificar enlaces rotos (formato básico)
    if grep -q "\[.*\]()" "$md_file"; then
        error "$md_file tiene enlaces vacíos []() "
    fi

    # Verificar que los bloques de código están cerrados
    CODE_TICKS=$(grep -c "\`\`\`" "$md_file" || echo "0")
    if [ $((CODE_TICKS % 2)) -ne 0 ]; then
        error "$md_file tiene bloques de código sin cerrar"
    fi
done

echo ""
echo "�� VERIFICANDO REFERENCIAS Y ENLACES..."
echo ""

# 7. Verificar que README enlaza a otros documentos
echo "7️⃣ Enlaces entre documentos:"

if [ -f "README.md" ]; then
    # Verificar que README enlaza a guia_uso.md
    if ! grep -q "guia_uso.md\|guía de uso" "README.md"; then
        warning "README.md no enlaza a guia_uso.md"
    else
        success "README.md → guia_uso.md"
    fi

    # Verificar que enlaza a documentación técnica
    if ! grep -q "Documentacion/\|arquitectura\|análisis" "README.md"; then
        warning "README.md no enlaza a documentación técnica"
    else
        success "README.md → Documentacion/"
    fi
fi

# 8. Verificar coherencia entre documentos
echo ""
echo "8️⃣ Coherencia entre documentos:"

# Verificar que todos mencionan el mismo nombre de proyecto
if [ -f "README.md" ] && [ -f "guia_uso.md" ]; then
    # Extraer título de README
    README_TITLE=$(grep "^# " "README.md" | head -1 | sed 's/^# //')

    if [ -n "$README_TITLE" ]; then
        if ! grep -q "$README_TITLE" "guia_uso.md"; then
            warning "El título del proyecto no coincide entre README y guia_uso.md"
        else
            success "Título coherente: $README_TITLE"
        fi
    fi
fi

echo ""
echo "📋 VERIFICANDO EJEMPLOS EJECUTABLES..."
echo ""

# 9. Verificar que los ejemplos son ejecutables
echo "9️⃣ Ejemplos de código:"

if [ -f "guia_uso.md" ]; then
    # Extraer bloques de código Python
    echo "   Verificando ejemplos Python..."

    # Contar imports en ejemplos
    if ! grep -A 20 "\`\`\`python" "guia_uso.md" | grep -q "import\|from"; then
        warning "Los ejemplos Python no tienen imports (pueden no ser ejecutables)"
    else
        success "Ejemplos tienen imports"
    fi

    # Verificar que los ejemplos tienen comentarios
    if ! grep -A 20 "\`\`\`python" "guia_uso.md" | grep -q "#"; then
        warning "Los ejemplos Python no tienen comentarios explicativos"
    else
        success "Ejemplos tienen comentarios"
    fi
fi

echo ""
echo "🎯 VERIFICANDO COBERTURA DEL CASO DE NEGOCIO..."
echo ""

# 10. Verificar que toda la funcionalidad está documentada
echo "🔟 Cobertura de funcionalidad:"

if [ -f "Documentacion/caso_negocio.txt" ] && [ -f "README.md" ]; then
    # Extraer palabras clave del caso de negocio
    echo "   Verificando que se documentaron todas las funcionalidades..."

    # Buscar requerimientos funcionales
    if [ -f "Documentacion/analisis_tdd.md" ]; then
        RF_IDS=$(grep -o "RF-[0-9]\{3\}" "Documentacion/analisis_tdd.md" | sort -u)

        UNDOCUMENTED=0
        for rf_id in $RF_IDS; do
            # Buscar el requerimiento en la documentación final
            if ! grep -q "$rf_id" "README.md" && ! grep -q "$rf_id" "guia_uso.md"; then
                warning "Requerimiento $rf_id no está documentado en README/guía"
                UNDOCUMENTED=$((UNDOCUMENTED + 1))
            fi
        done

        if [ $UNDOCUMENTED -eq 0 ]; then
            success "Todos los requerimientos están documentados"
        else
            error "$UNDOCUMENTED requerimientos sin documentar en README/guía"
        fi
    fi
fi

echo ""
echo "📊 VERIFICANDO DIAGRAMAS..."
echo ""

# 11. Verificar diagramas de arquitectura
echo "1️⃣1️⃣ Diagramas de arquitectura:"

TOTAL_DIAGRAMS=0

# Contar diagramas mermaid en todos los archivos
for md_file in $(find . -name "*.md" 2>/dev/null); do
    DIAGRAMS=$(grep -c "\`\`\`mermaid" "$md_file" || echo "0")
    if [ "$DIAGRAMS" -gt 0 ]; then
        echo "   $md_file: $DIAGRAMS diagramas"
        TOTAL_DIAGRAMS=$((TOTAL_DIAGRAMS + DIAGRAMS))
    fi
done

if [ "$TOTAL_DIAGRAMS" -eq 0 ]; then
    error "No hay diagramas mermaid en la documentación"
else
    success "Total de diagramas: $TOTAL_DIAGRAMS"

    # Verificar tipos de diagramas
    if grep -r "sequenceDiagram\|graph\|flowchart\|classDiagram" . --include="*.md" > /dev/null 2>&1; then
        success "Hay diagramas de diferentes tipos"
    fi
fi

# 12. Validar sintaxis de diagramas mermaid
echo ""
echo "1️⃣2️⃣ Validación de sintaxis mermaid:"

for md_file in $(find . -name "*.md" 2>/dev/null); do
    if grep -q "\`\`\`mermaid" "$md_file"; then
        # Extraer bloques mermaid y verificar que tienen contenido
        if awk '/```mermaid/,/```/' "$md_file" | grep -v "^```" | grep -q "[a-zA-Z]"; then
            success "Diagramas en $md_file tienen contenido"
        else
            error "Diagramas en $md_file están vacíos"
        fi
    fi
done

echo ""
echo "✅ VERIFICANDO COMPLETITUD..."
echo ""

# 13. Verificar que TODO está documentado
echo "1️⃣3️⃣ Completitud de la documentación:"

# Lista de archivos que DEBEN existir
REQUIRED_DOCS=(
    "README.md"
    "guia_uso.md"
    "Documentacion/analisis_tdd.md"
    "Documentacion/herramientas_testing.md"
    "Documentacion/guia_tests.md"
    "Documentacion/arquitectura_ddd.md"
)

MISSING_DOCS=0

for doc_file in "${REQUIRED_DOCS[@]}"; do
    if [ ! -f "$doc_file" ]; then
        error "Falta documentación obligatoria: $doc_file"
        MISSING_DOCS=$((MISSING_DOCS + 1))
    fi
done

if [ $MISSING_DOCS -eq 0 ]; then
    success "Toda la documentación obligatoria está presente"
fi

# 14. Verificar archivos de licencia y contribución
echo ""
echo "1️⃣4️⃣ Documentación complementaria:"

if [ -f "LICENSE" ] || [ -f "LICENSE.md" ]; then
    success "Tiene archivo de licencia"
else
    warning "No tiene archivo LICENSE (recomendado)"
fi

if [ -f "CONTRIBUTING.md" ]; then
    success "Tiene guía de contribución"
else
    warning "No tiene CONTRIBUTING.md (opcional)"
fi

if [ -f ".gitignore" ]; then
    success "Tiene .gitignore configurado"
else
    warning "No tiene .gitignore"
fi

echo ""
echo "🔍 VERIFICANDO CALIDAD DEL CONTENIDO..."
echo ""

# 15. Verificar calidad del contenido
echo "1️⃣5️⃣ Calidad del contenido:"

for doc_file in README.md guia_uso.md; do
    if [ -f "$doc_file" ]; then
        # Verificar que no tiene TODOs pendientes
        if grep -qi "TODO\|FIXME\|XXX" "$doc_file"; then
            error "$doc_file tiene TODOs pendientes"
        fi

        # Verificar que no tiene placeholders
        if grep -q "\[.*\]\|\{.*\}\|<.*>" "$doc_file"; then
            # Excluir enlaces válidos
            if grep -q "\[TODO\]\|\{PENDIENTE\}\|<COMPLETAR>" "$doc_file"; then
                error "$doc_file tiene placeholders sin completar"
            fi
        fi
    fi
done

echo ""
echo "=========================================="
echo "📊 RESUMEN DE VALIDACIÓN"
echo "=========================================="
echo ""

# Resumen de archivos generados
echo "📄 Archivos de documentación generados:"
find . -name "*.md" ! -path "./node_modules/*" ! -path "./.git/*" 2>/dev/null | sort

echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "🎉 VALIDACIÓN COMPLETA: TODO PERFECTO"
    echo ""
    echo "✅ 0 errores"
    echo "✅ 0 warnings"
    echo ""
    echo "El Experto Documentación completó su trabajo correctamente:"
    echo "  ✅ README.md completo y profesional"
    echo "  ✅ guia_uso.md exhaustiva"
    echo "  ✅ Diagramas de arquitectura"
    echo "  ✅ Ejemplos ejecutables"
    echo "  ✅ FAQ y troubleshooting"
    echo ""
    echo "🚀 LA APLICACIÓN ESTÁ COMPLETAMENTE DOCUMENTADA"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "✅ VALIDACIÓN COMPLETADA CON WARNINGS"
    echo ""
    echo "✅ 0 errores"
    echo "⚠️  $WARNINGS warnings"
    echo ""
    echo "El Experto Documentación completó su trabajo con algunas observaciones."
    echo "Los warnings no impiden el uso pero se recomienda revisarlos."
    exit 0
else
    echo "❌ VALIDACIÓN FALLIDA"
    echo ""
    echo "❌ $ERRORS errores"
    echo "⚠️  $WARNINGS warnings"
    echo ""
    echo "El Experto Documentación NO completó correctamente su trabajo."
    echo "La documentación está incompleta o tiene errores."
    echo ""
    exit 1
fi
