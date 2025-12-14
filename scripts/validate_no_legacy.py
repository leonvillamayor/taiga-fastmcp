"""Valida que no hay referencias a arquitectura legacy.

Este script verifica que no existen imports de src.tools en el código fuente
ni en los tests, asegurando que la migración a src.application.tools está completa.
"""

import sys
from pathlib import Path


def check_no_legacy_imports() -> bool:
    """Verifica que no hay imports de la arquitectura legacy src.tools.

    Returns:
        bool: True si no se encontraron referencias legacy, False en caso contrario.
    """
    src_dir = Path("src")
    tests_dir = Path("tests")
    legacy_refs: list[tuple[Path, int, str]] = []

    # Patrones a buscar
    legacy_patterns = ["from src.tools", "import src.tools"]

    # Verificar en src/ (excluyendo src/tools/ que será eliminado)
    for py_file in src_dir.rglob("*.py"):
        if "tools/" in str(py_file) and "application/tools" not in str(py_file):
            continue  # Saltar archivos legacy mismos

        content = py_file.read_text()
        for line_num, line in enumerate(content.splitlines(), 1):
            for pattern in legacy_patterns:
                if pattern in line:
                    legacy_refs.append((py_file, line_num, line.strip()))

    # Verificar en tests/
    for py_file in tests_dir.rglob("*.py"):
        content = py_file.read_text()
        for line_num, line in enumerate(content.splitlines(), 1):
            for pattern in legacy_patterns:
                if pattern in line:
                    legacy_refs.append((py_file, line_num, line.strip()))

    if legacy_refs:
        print("❌ LEGACY IMPORTS FOUND:")
        for file_path, line_num, line in legacy_refs:
            print(f"  - {file_path}:{line_num}: {line}")
        return False
    print("✅ No legacy imports found")
    return True


def check_legacy_directory_exists() -> bool:
    """Verifica si el directorio legacy src/tools existe.

    Returns:
        bool: True si el directorio NO existe (éxito), False si existe.
    """
    legacy_dir = Path("src/tools")
    if legacy_dir.exists() and legacy_dir.is_dir():
        # Verificar si tiene archivos .py (excluyendo __init__.py)
        py_files = [f for f in legacy_dir.glob("*.py") if f.name != "__init__.py"]
        if py_files:
            print(f"⚠️  Legacy directory exists with {len(py_files)} Python files:")
            for f in py_files:
                print(f"  - {f}")
            return False
        print("⚠️  Legacy directory exists but is empty or only has __init__.py")
        return True
    print("✅ Legacy directory src/tools/ does not exist")
    return True


def main() -> int:
    """Función principal que ejecuta todas las validaciones.

    Returns:
        int: 0 si todas las validaciones pasan, 1 en caso contrario.
    """
    print("=" * 60)
    print("Validando que no hay referencias a arquitectura legacy...")
    print("=" * 60)
    print()

    # Ejecutar validaciones
    no_imports = check_no_legacy_imports()
    print()
    no_directory = check_legacy_directory_exists()
    print()

    print("=" * 60)
    if no_imports and no_directory:
        print("✅ VALIDACIÓN EXITOSA: No hay arquitectura legacy")
        return 0
    print("❌ VALIDACIÓN FALLIDA: Se encontraron referencias legacy")
    if not no_imports:
        print("   - Hay imports de src.tools pendientes de migrar")
    if not no_directory:
        print("   - El directorio src/tools/ aún existe con archivos")
    return 1


if __name__ == "__main__":
    sys.exit(main())
