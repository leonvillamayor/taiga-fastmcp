#!/bin/bash
# Script de automatización completa del flujo TDD/DDD
# Permite ejecución headless para CI/CD
#
# Uso:
#   ./run-flujo-completo.sh                    # Interactivo
#   ./run-flujo-completo.sh --headless         # No-interactivo para CI/CD
#   ./run-flujo-completo.sh --verbose          # Output detallado

set -e  # Salir en el primer error

# Variables
HEADLESS=false
VERBOSE=false
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LOG_DIR=".claude/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Parsear argumentos
for arg in "$@"; do
  case $arg in
    --headless)
      HEADLESS=true
      ;;
    --verbose)
      VERBOSE=true
      ;;
    *)
      echo "Argumento desconocido: $arg"
      echo "Uso: $0 [--headless] [--verbose]"
      exit 1
      ;;
  esac
done

# Función de logging
log() {
  echo "[$(date +%H:%M:%S)] $1"
  echo "[$(date +%H:%M:%S)] $1" >> "$LOG_DIR/flujo_completo_$TIMESTAMP.log"
}

error() {
  echo "❌ ERROR: $1" >&2
  echo "[$(date +%H:%M:%S)] ERROR: $1" >> "$LOG_DIR/flujo_completo_$TIMESTAMP.log"
  exit 1
}

success() {
  echo "✅ $1"
  echo "[$(date +%H:%M:%S)] SUCCESS: $1" >> "$LOG_DIR/flujo_completo_$TIMESTAMP.log"
}

# Crear directorio de logs
mkdir -p "$LOG_DIR"

log "==========================================="
log "FLUJO COMPLETO TDD/DDD - INICIO"
log "==========================================="
log "Modo: $([ "$HEADLESS" = true ] && echo "HEADLESS" || echo "INTERACTIVO")"
log "Directorio: $PROJECT_DIR"

# Verificar prerequisitos
log "Verificando prerequisitos..."

if [ ! -f "Documentacion/caso_negocio.txt" ]; then
  error "No existe Documentacion/caso_negocio.txt - Crea el archivo con el caso de negocio primero"
fi

if ! command -v claude &> /dev/null; then
  error "Claude Code CLI no está instalado"
fi

if ! command -v uv &> /dev/null; then
  error "uv no está instalado - Instálalo con: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

success "Prerequisitos verificados"

# ==================================================
# FASE 1: EXPERTO TDD - Análisis y Tests en Rojo
# ==================================================

log ""
log "==========================================="
log "FASE 1: EXPERTO TDD"
log "==========================================="

if [ "$HEADLESS" = true ]; then
  log "Ejecutando Experto TDD en modo headless..."

  TDD_OUTPUT=$(claude -p "Analiza exhaustivamente el archivo Documentacion/caso_negocio.txt y genera todos los tests necesarios siguiendo TDD. Los tests deben estar en ROJO." \
    --output-format json \
    --permission-mode plan \
    --max-turns 20 \
    2>&1) || error "Experto TDD falló"

  TDD_SESSION=$(echo "$TDD_OUTPUT" | jq -r '.session_id' 2>/dev/null || echo "")

  [ "$VERBOSE" = true ] && echo "$TDD_OUTPUT"
  log "Session ID TDD: $TDD_SESSION"
else
  log "Ejecutando Experto TDD en modo interactivo..."
  log "Por favor, invoca al experto-tdd para analizar el caso de negocio"

  read -p "Presiona ENTER cuando el Experto TDD haya terminado..."
fi

# Validar resultado Experto TDD
log "Validando output del Experto TDD..."

if [ ! -x ".claude/hooks/validate-experto-tdd.sh" ]; then
  chmod +x .claude/hooks/validate-experto-tdd.sh
fi

if .claude/hooks/validate-experto-tdd.sh > "$LOG_DIR/validation_tdd_$TIMESTAMP.log" 2>&1; then
  success "Experto TDD completado exitosamente"
  [ "$VERBOSE" = true ] && cat "$LOG_DIR/validation_tdd_$TIMESTAMP.log"
else
  error "Validación de Experto TDD FALLÓ - Ver: $LOG_DIR/validation_tdd_$TIMESTAMP.log"
fi

# ==================================================
# FASE 2: EXPERTO DDD - Implementación y Tests en Verde
# ==================================================

log ""
log "==========================================="
log "FASE 2: EXPERTO DDD"
log "==========================================="

if [ "$HEADLESS" = true ]; then
  log "Ejecutando Experto DDD en modo headless..."

  if [ -n "$TDD_SESSION" ]; then
    DDD_OUTPUT=$(claude --resume "$TDD_SESSION" \
      -p "Implementa el código siguiendo arquitectura DDD para pasar TODOS los tests a VERDE. NO modifiques los tests bajo ninguna circunstancia." \
      --output-format json \
      --permission-mode acceptEdits \
      --max-turns 50 \
      2>&1) || error "Experto DDD falló"

    DDD_SESSION=$(echo "$DDD_OUTPUT" | jq -r '.session_id' 2>/dev/null || echo "")
    [ "$VERBOSE" = true ] && echo "$DDD_OUTPUT"
    log "Session ID DDD: $DDD_SESSION"
  else
    error "No se pudo obtener TDD_SESSION"
  fi
else
  log "Ejecutando Experto DDD en modo interactivo..."
  log "Por favor, invoca al experto-ddd para implementar el código"

  read -p "Presiona ENTER cuando el Experto DDD haya terminado..."
fi

# Validar resultado Experto DDD
log "Validando output del Experto DDD..."

if [ ! -x ".claude/hooks/validate-experto-ddd.sh" ]; then
  chmod +x .claude/hooks/validate-experto-ddd.sh
fi

if .claude/hooks/validate-experto-ddd.sh > "$LOG_DIR/validation_ddd_$TIMESTAMP.log" 2>&1; then
  success "Experto DDD completado exitosamente"
  [ "$VERBOSE" = true ] && cat "$LOG_DIR/validation_ddd_$TIMESTAMP.log"
else
  error "Validación de Experto DDD FALLÓ - Ver: $LOG_DIR/validation_ddd_$TIMESTAMP.log"
fi

# ==================================================
# FASE 3: EXPERTO DOCUMENTACIÓN - README y Guías
# ==================================================

log ""
log "==========================================="
log "FASE 3: EXPERTO DOCUMENTACIÓN"
log "==========================================="

if [ "$HEADLESS" = true ]; then
  log "Ejecutando Experto Documentación en modo headless..."

  if [ -n "$DDD_SESSION" ]; then
    DOC_OUTPUT=$(claude --resume "$DDD_SESSION" \
      -p "Genera documentación completa del proyecto: README.md y guia_uso.md exhaustiva" \
      --output-format json \
      --permission-mode acceptEdits \
      --max-turns 20 \
      2>&1) || error "Experto Documentación falló"

    [ "$VERBOSE" = true ] && echo "$DOC_OUTPUT"
  else
    error "No se pudo obtener DDD_SESSION"
  fi
else
  log "Ejecutando Experto Documentación en modo interactivo..."
  log "Por favor, invoca al experto-documentacion para generar la documentación"

  read -p "Presiona ENTER cuando el Experto Documentación haya terminado..."
fi

# Validar resultado Experto Documentación
log "Validando output del Experto Documentación..."

if [ ! -x ".claude/hooks/validate-experto-documentacion.sh" ]; then
  chmod +x .claude/hooks/validate-experto-documentacion.sh
fi

if .claude/hooks/validate-experto-documentacion.sh > "$LOG_DIR/validation_doc_$TIMESTAMP.log" 2>&1; then
  success "Experto Documentación completado exitosamente"
  [ "$VERBOSE" = true ] && cat "$LOG_DIR/validation_doc_$TIMESTAMP.log"
else
  error "Validación de Experto Documentación FALLÓ - Ver: $LOG_DIR/validation_doc_$TIMESTAMP.log"
fi

# ==================================================
# RESUMEN FINAL
# ==================================================

log ""
log "==========================================="
log "🎉 FLUJO COMPLETO TDD/DDD EXITOSO"
log "==========================================="
log ""
log "✅ FASE 1 - Experto TDD:"
log "   - Tests generados en ROJO"
log "   - Análisis documentado en Documentacion/analisis_tdd.md"
log ""
log "✅ FASE 2 - Experto DDD:"
log "   - Tests en VERDE"
log "   - Arquitectura DDD implementada"
log "   - Cobertura >= 80%"
log ""
log "✅ FASE 3 - Experto Documentación:"
log "   - README.md generado"
log "   - guia_uso.md generado"
log ""
log "📁 Logs guardados en: $LOG_DIR/"
log "   - flujo_completo_$TIMESTAMP.log"
log "   - validation_tdd_$TIMESTAMP.log"
log "   - validation_ddd_$TIMESTAMP.log"
log "   - validation_doc_$TIMESTAMP.log"
log ""
log "🚀 LA APLICACIÓN ESTÁ LISTA PARA USAR"
log "==========================================="

exit 0
