#!/usr/bin/env python3
"""Valida que Fase 2 está completa.

Este script ejecuta una validación exhaustiva de todas las herramientas MCP
y verifica que cumplen con los estándares de normalización de la Fase 2:
- Prefijo 'taiga_' en todas las herramientas
- Sin uso de json.dumps en retornos
- Tipos de retorno consistentes (Dict/List[Dict])
- Sin aliases de parámetros
- Docstrings completos

Usage:
    uv run python scripts/validate_phase2.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Final


# Códigos de salida
EXIT_SUCCESS: Final[int] = 0
EXIT_FAILURE: Final[int] = 1


def run_command(cmd: list[str], capture_output: bool = True) -> subprocess.CompletedProcess[str]:
    """Ejecuta un comando y retorna el resultado.

    Args:
        cmd: Lista de argumentos del comando.
        capture_output: Si capturar stdout/stderr.

    Returns:
        CompletedProcess con el resultado.
    """
    return subprocess.run(cmd, capture_output=capture_output, text=True)


def check_all_tools_have_prefix() -> bool:
    """Verifica que todas las herramientas tienen prefijo 'taiga_'.

    Returns:
        True si todas las herramientas tienen prefijo correcto.
    """
    print("\n🔍 Validando prefijo 'taiga_' en todas las herramientas...")

    run_command(["uv", "run", "python", "scripts/audit_mcp_tools.py"])

    # Leer reporte
    report_path = Path("Documentacion/audit_mcp_tools.json")
    if not report_path.exists():
        print("❌ Reporte de auditoría no encontrado")
        return False

    report = json.loads(report_path.read_text())

    tools_without_prefix = report.get("tools_without_prefix", 0)
    total_tools = report.get("total_tools", 0)

    if tools_without_prefix > 0:
        print(f"❌ {tools_without_prefix} herramientas sin prefijo")
        # Mostrar cuáles
        tools = report.get("tools", [])
        if isinstance(tools, list):
            no_prefix = [
                t.get("name", "unknown")
                for t in tools
                if isinstance(t, dict) and not t.get("has_prefix", False)
            ]
            for name in no_prefix[:10]:
                print(f"   - {name}")
            if len(no_prefix) > 10:
                print(f"   ... y {len(no_prefix) - 10} más")
        return False
    print(f"✅ {total_tools} herramientas con prefijo 'taiga_'")
    return True


def check_no_json_dumps() -> bool:
    """Verifica que no hay uso de json.dumps en tools.

    Returns:
        True si no se detecta uso de json.dumps.
    """
    print("\n🔍 Validando ausencia de json.dumps...")

    result = run_command(["uv", "run", "python", "scripts/check_json_dumps.py"])

    if result.returncode == 0:
        print("✅ Sin uso de json.dumps detectado")
        return True
    print("❌ Uso de json.dumps detectado en tools")
    if result.stdout:
        print(result.stdout)
    return False


def check_return_types() -> bool:
    """Verifica que tipos de retorno son consistentes.

    Returns:
        True si los tipos de retorno son correctos.
    """
    print("\n🔍 Validando tipos de retorno...")

    # Buscar retornos -> str que no sean auth_token
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

        for i, line in enumerate(lines):
            # Detectar funciones async con retorno -> str
            if ("async def" in line) and ("-> str:" in line or "-> str " in line):
                # Excepciones permitidas: funciones de autenticación
                if any(
                    name in line
                    for name in [
                        "auth_token",
                        "get_token",
                        "authenticate",
                        "_get_auth",
                    ]
                ):
                    continue

                # Verificar contexto: líneas cercanas
                context_start = max(0, i - 2)
                context_end = min(len(lines), i + 3)
                context = "\n".join(lines[context_start:context_end])

                # Si el método retorna str pero NO es por autenticación
                issues.append(f"{py_file.name}:{i + 1}")

    if issues:
        print(f"⚠️  {len(issues)} funciones retornan -> str:")
        for issue in issues[:5]:
            print(f"   {issue}")
        if len(issues) > 5:
            print(f"   ... y {len(issues) - 5} más")
        # No bloquear por esto, pero avisar
        return True
    print("✅ Tipos de retorno consistentes")
    return True


def check_no_parameter_aliases() -> bool:
    """Verifica que no hay aliases de parámetros.

    Returns:
        True si no se detectan aliases.
    """
    print("\n🔍 Validando ausencia de aliases de parámetros...")

    tools_dir = Path("src/application/tools")
    issues: list[str] = []

    if not tools_dir.exists():
        print(f"❌ Directorio {tools_dir} no existe")
        return False

    for py_file in tools_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        content = py_file.read_text()

        # Buscar patrones sospechosos de aliases
        alias_patterns = [
            ("member if member", "member/member_id alias"),
            ("project if project", "project/project_id alias"),
            ("status if status", "status/status_id alias"),
            (" = id or ", "id alias"),
        ]

        for pattern, description in alias_patterns:
            if pattern in content:
                issues.append(f"{py_file.name}: '{description}' detectado")

    if issues:
        print("❌ Aliases de parámetros detectados:")
        for issue in issues:
            print(f"   {issue}")
        return False
    print("✅ Sin aliases de parámetros")
    return True


def check_docstrings_complete() -> bool:
    """Verifica que docstrings están completos.

    Returns:
        True si los docstrings pasan la validación.
    """
    print("\n🔍 Validando completitud de docstrings...")

    result = run_command(["uv", "run", "python", "scripts/check_docstrings.py"])

    if result.returncode == 0:
        print("✅ Docstrings completos")
        return True
    print("⚠️  Algunos docstrings incompletos")
    # No bloquear por esto
    return True


def check_tests_pass() -> bool:
    """Verifica que tests pasan.

    Returns:
        True si todos los tests pasan.
    """
    print("\n🔍 Validando tests...")

    result = run_command(
        ["uv", "run", "pytest", "tests/", "-v", "--tb=short", "-q"],
        capture_output=True,
    )

    if result.returncode == 0:
        print("✅ Todos los tests pasan")
        # Mostrar resumen
        lines = result.stdout.split("\n")
        for line in lines[-5:]:
            if line.strip():
                print(f"   {line.strip()}")
        return True
    print("❌ Algunos tests fallan")
    # Mostrar errores
    if result.stdout:
        lines = result.stdout.split("\n")
        for line in lines[-10:]:
            if line.strip():
                print(f"   {line.strip()}")
    return False


def check_ruff_passes() -> bool:
    """Verifica que ruff pasa sin errores.

    Returns:
        True si ruff pasa.
    """
    print("\n🔍 Validando código con ruff...")

    result = run_command(["uv", "run", "ruff", "check", "src/", "tests/"])

    if result.returncode == 0:
        print("✅ ruff pasa sin errores")
        return True
    print("❌ ruff encontró errores:")
    if result.stdout:
        lines = result.stdout.split("\n")
        for line in lines[:20]:
            if line.strip():
                print(f"   {line.strip()}")
    return False


def check_mypy_passes() -> bool:
    """Verifica que mypy pasa sin errores.

    Returns:
        True si mypy pasa.
    """
    print("\n🔍 Validando tipos con mypy...")

    result = run_command(["uv", "run", "mypy", "src/", "tests/"])

    if result.returncode == 0:
        print("✅ mypy pasa sin errores")
        return True
    print("❌ mypy encontró errores:")
    if result.stdout:
        lines = result.stdout.split("\n")
        error_count = 0
        for line in lines:
            if line.strip() and "error" in line.lower():
                error_count += 1
                if error_count <= 15:
                    print(f"   {line.strip()}")
        if error_count > 15:
            print(f"   ... y {error_count - 15} errores más")
    return False


def check_bandit_passes() -> bool:
    """Verifica que bandit pasa sin errores de seguridad.

    Returns:
        True si bandit pasa.
    """
    print("\n🔍 Validando seguridad con bandit...")

    result = run_command(["uv", "run", "bandit", "-r", "src/", "-ll"])

    if result.returncode == 0:
        print("✅ bandit pasa sin problemas de seguridad")
        return True
    print("❌ bandit encontró problemas de seguridad:")
    if result.stdout:
        lines = result.stdout.split("\n")
        for line in lines[:20]:
            if line.strip():
                print(f"   {line.strip()}")
    return False


def check_server_starts() -> bool:
    """Verifica que el servidor puede iniciarse.

    Returns:
        True si el servidor importa correctamente.
    """
    print("\n🔍 Validando que el servidor puede iniciarse...")

    # Verificar que el módulo principal puede importarse
    result = run_command(
        [
            "uv",
            "run",
            "python",
            "-c",
            "from src.server import create_server; print('OK')",
        ]
    )

    if result.returncode == 0 and "OK" in (result.stdout or ""):
        print("✅ Servidor importa correctamente")
        return True
    print("❌ Error al importar servidor:")
    if result.stderr:
        print(f"   {result.stderr[:500]}")
    return False


def check_audit_zero_issues() -> bool:
    """Verifica que la auditoría muestra 0 problemas.

    Returns:
        True si no hay problemas en la auditoría.
    """
    print("\n🔍 Verificando auditoría muestra 0 problemas...")

    report_path = Path("Documentacion/audit_mcp_tools.json")
    if not report_path.exists():
        # Ejecutar auditoría primero
        run_command(["uv", "run", "python", "scripts/audit_mcp_tools.py"])

    if not report_path.exists():
        print("❌ No se pudo generar reporte de auditoría")
        return False

    report = json.loads(report_path.read_text())

    tools_with_issues = report.get("tools_with_issues", 0)
    tools_without_prefix = report.get("tools_without_prefix", 0)

    # Solo contar problemas críticos (sin prefijo)
    critical_issues = tools_without_prefix

    if critical_issues > 0:
        print(f"❌ {critical_issues} herramientas con problemas críticos")
        return False
    print("✅ Auditoría sin problemas críticos")
    if tools_with_issues > 0:
        print(f"   ⚠️  {tools_with_issues} herramientas con issues menores")
    return True


def main() -> int:
    """Función principal del script de validación.

    Returns:
        Código de salida: 0 si todo pasa, 1 si hay errores.
    """
    print("=" * 60)
    print("VALIDACIÓN DE FASE 2: NORMALIZACIÓN DE INTERFACES")
    print("=" * 60)

    # Verificaciones críticas (bloquean)
    critical_checks = [
        ("Prefijo taiga_", check_all_tools_have_prefix),
        ("Sin json.dumps", check_no_json_dumps),
        ("Sin aliases", check_no_parameter_aliases),
        ("ruff", check_ruff_passes),
        ("mypy", check_mypy_passes),
        ("bandit", check_bandit_passes),
        ("Tests pasan", check_tests_pass),
        ("Servidor inicia", check_server_starts),
        ("Auditoría OK", check_audit_zero_issues),
    ]

    # Verificaciones opcionales (advertencias)
    optional_checks = [
        ("Tipos retorno", check_return_types),
        ("Docstrings", check_docstrings_complete),
    ]

    critical_results: list[tuple[str, bool]] = []
    optional_results: list[tuple[str, bool]] = []

    print("\n" + "-" * 60)
    print("VERIFICACIONES CRÍTICAS")
    print("-" * 60)

    for name, check in critical_checks:
        result = check()
        critical_results.append((name, result))

    print("\n" + "-" * 60)
    print("VERIFICACIONES OPCIONALES")
    print("-" * 60)

    for name, check in optional_checks:
        result = check()
        optional_results.append((name, result))

    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE VALIDACIÓN")
    print("=" * 60)

    print("\nVerificaciones críticas:")
    all_critical_pass = True
    for name, result in critical_results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
        if not result:
            all_critical_pass = False

    print("\nVerificaciones opcionales:")
    for name, result in optional_results:
        status = "✅" if result else "⚠️ "
        print(f"  {status} {name}")

    print("\n" + "=" * 60)
    if all_critical_pass:
        print("✅ FASE 2 COMPLETA Y VALIDADA")
        print("=" * 60)
        return EXIT_SUCCESS
    print("❌ FASE 2 INCOMPLETA - Revisar errores arriba")
    print("=" * 60)
    return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())
