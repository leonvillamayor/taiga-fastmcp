#!/usr/bin/env python3
"""Detecta uso incorrecto de json.dumps en tools.

Este script verifica que las herramientas MCP retornen tipos estructurados
(Dict, List) en lugar de strings JSON serializados.

Usage:
    uv run python scripts/check_json_dumps.py
"""

import re
import sys
from pathlib import Path


def check_json_dumps_usage() -> bool:
    """Verifica uso de json.dumps en archivos de tools.

    Returns:
        True si no hay problemas, False si se detectan usos incorrectos.
    """
    tools_dir = Path("src/application/tools")
    issues: list[str] = []

    if not tools_dir.exists():
        print(f"❌ Directorio {tools_dir} no existe")
        return False

    for py_file in tools_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        content = py_file.read_text()
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # Detectar return json.dumps
            if "json.dumps" in line and "return" in line:
                issues.append(f"{py_file}:{i} - {line.strip()}")

    if issues:
        print("⚠️  Uso incorrecto de json.dumps detectado:")
        for issue in issues:
            print(f"  {issue}")
        return False
    print("✅ No se detectó uso de json.dumps en returns")
    return True


def check_str_return_types() -> bool:
    """Verifica que los métodos no retornen -> str para datos JSON.

    Returns:
        True si no hay problemas, False si se detectan tipos incorrectos.
    """
    tools_dir = Path("src/application/tools")
    issues: list[str] = []

    if not tools_dir.exists():
        print(f"❌ Directorio {tools_dir} no existe")
        return False

    # Patrones para detectar métodos async que retornan str
    # (excluyendo aquellos que deben retornar str, como mensajes simples)
    async_method_pattern = re.compile(r"async def (\w+)\([^)]*\)\s*->\s*str:", re.MULTILINE)

    # Métodos que legítimamente pueden retornar str
    allowed_str_returns = {
        # Métodos que retornan mensajes simples, no datos JSON
    }

    for py_file in tools_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        content = py_file.read_text()

        for match in async_method_pattern.finditer(content):
            method_name = match.group(1)
            if method_name not in allowed_str_returns:
                # Verificar si el método usa json.dumps
                # Buscar el cuerpo del método
                start = match.end()
                # Buscar hasta el siguiente "async def" o fin de clase
                next_method = content.find("async def", start)
                if next_method == -1:
                    next_method = len(content)
                method_body = content[start:next_method]

                if "json.dumps" in method_body:
                    line_num = content[: match.start()].count("\n") + 1
                    issues.append(
                        f"{py_file}:{line_num} - Método '{method_name}' "
                        f"retorna str con json.dumps"
                    )

    if issues:
        print("\n⚠️  Métodos con tipo de retorno str que usan json.dumps:")
        for issue in issues:
            print(f"  {issue}")
        return False
    print("✅ No se detectaron métodos con -> str que usen json.dumps")
    return True


def main() -> int:
    """Ejecuta todas las verificaciones.

    Returns:
        0 si todo está bien, 1 si hay problemas.
    """
    print("=" * 60)
    print("Verificando uso de json.dumps en tools...")
    print("=" * 60)

    results = []

    # Verificar uso de json.dumps
    results.append(check_json_dumps_usage())

    # Verificar tipos de retorno str
    results.append(check_str_return_types())

    print("=" * 60)

    if all(results):
        print("✅ Todas las verificaciones pasaron")
        return 0
    print("❌ Se detectaron problemas - ver detalles arriba")
    return 1


if __name__ == "__main__":
    sys.exit(main())
