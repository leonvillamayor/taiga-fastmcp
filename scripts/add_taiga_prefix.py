"""Agrega prefijo 'taiga_' a herramientas que no lo tienen."""

import re
from pathlib import Path


def add_prefix_to_file(file_path: Path) -> list[tuple[str, str]]:
    """
    Agrega prefijo 'taiga_' a tools en un archivo.

    Returns:
        Lista de tuplas (nombre_anterior, nombre_nuevo)
    """
    content = file_path.read_text()
    changes: list[tuple[str, str]] = []

    # Caso 1: Buscar @self.mcp.tool(name="xxx") en una sola línea
    pattern_single_line = r'@self\.mcp\.tool\(name="([^"]+)"'

    def replacer_single_line(match: re.Match[str]) -> str:
        old_name = match.group(1)
        if not old_name.startswith("taiga_"):
            new_name = f"taiga_{old_name}"
            changes.append((old_name, new_name))
            return f'@self.mcp.tool(name="{new_name}"'
        return match.group(0)

    new_content = re.sub(pattern_single_line, replacer_single_line, content)

    # Caso 2: Buscar decorador multi-línea con name="xxx"
    # Ejemplo: @self.mcp.tool(\n    name="xxx",
    pattern_multiline = r'(@self\.mcp\.tool\(\n\s+name=")([^"]+)(")'

    def replacer_multiline(match: re.Match[str]) -> str:
        prefix = match.group(1)
        old_name = match.group(2)
        suffix = match.group(3)
        if not old_name.startswith("taiga_"):
            new_name = f"taiga_{old_name}"
            changes.append((old_name, new_name))
            return f"{prefix}{new_name}{suffix}"
        return match.group(0)

    new_content = re.sub(pattern_multiline, replacer_multiline, new_content)

    # Caso 3: Buscar @self.mcp.tool() seguido de async def xxx(
    # donde xxx no tiene prefijo taiga_
    pattern_no_name = r"@self\.mcp\.tool\(\)\n(\s+)(async def )(\w+)\("

    def replacer_no_name(match: re.Match[str]) -> str:
        indent = match.group(1)
        async_def = match.group(2)
        func_name = match.group(3)
        if not func_name.startswith("taiga_"):
            new_name = f"taiga_{func_name}"
            changes.append((func_name, new_name))
            return f'@self.mcp.tool(name="{new_name}")\n{indent}{async_def}{func_name}('
        return match.group(0)

    new_content = re.sub(pattern_no_name, replacer_no_name, new_content)

    if new_content != content:
        file_path.write_text(new_content)
        print(f"✅ Actualizado: {file_path}")
        for old, new in changes:
            print(f"    {old} → {new}")

    return changes


def main() -> None:
    tools_dir = Path("src/application/tools")
    all_changes: list[tuple[str, str]] = []

    for py_file in tools_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        changes = add_prefix_to_file(py_file)
        all_changes.extend(changes)

    print(f"\n📊 Total de cambios: {len(all_changes)}")

    # Generar migration guide
    migration_guide = Path("Documentacion/tool_names_migration.md")
    with migration_guide.open("w") as f:
        f.write("# Guía de Migración de Nombres de Herramientas\n\n")
        f.write("| Nombre Anterior | Nombre Nuevo |\n")
        f.write("|----------------|---------------|\n")
        for old, new in sorted(all_changes):
            f.write(f"| `{old}` | `{new}` |\n")

    print(f"\n📄 Guía de migración generada: {migration_guide}")


if __name__ == "__main__":
    main()
