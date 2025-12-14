"""Tests de regresión y snapshot para Taiga MCP Server.

Este módulo contiene tests de snapshot que verifican que los formatos
de respuestas y schemas no cambian inesperadamente entre versiones.

Actualización de Snapshots
--------------------------
Para actualizar los snapshots después de cambios intencionales:

    uv run pytest tests/regression/ --snapshot-update

Esto actualizará todos los snapshots que hayan cambiado.

Para ver qué cambiaría sin actualizar:

    uv run pytest tests/regression/ -v

Los tests fallidos mostrarán las diferencias entre el snapshot
actual y el nuevo valor.

Estructura de Snapshots
-----------------------
Los snapshots se almacenan en formato JSON en:
    tests/regression/__snapshots__/

Cada archivo de test tiene su propio subdirectorio de snapshots.

Tests Incluidos
---------------
- Test 4.10.1: Snapshot de respuestas de proyecto
- Test 4.10.2: Snapshot de respuestas de epic
- Test 4.10.3: Snapshot de schemas de herramientas
- Test 4.10.4: Snapshot de mensajes de error
"""
