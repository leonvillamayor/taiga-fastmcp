#!/usr/bin/env python3
"""Valida que todos los tools tienen docstrings completos en formato Google Style.

Este script analiza los archivos de herramientas MCP y verifica que cada
función decorada con @mcp.tool tenga documentación completa incluyendo:
- Descripción general
- Args: documentación de parámetros
- Returns: documentación del valor de retorno
- Raises: (opcional) documentación de excepciones
- Example: (requerido) ejemplo de uso

Usage:
    uv run python scripts/check_docstrings.py
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final


@dataclass
class DocstringCheck:
    """Resultado de verificación de docstring para una función."""

    function_name: str
    file_path: str
    has_docstring: bool = False
    has_description: bool = False
    has_args: bool = False
    has_returns: bool = False
    has_raises: bool = False
    has_example: bool = False
    line_number: int = 0

    def is_complete(self) -> bool:
        """Verifica si el docstring cumple todos los requisitos obligatorios.

        Returns:
            True si tiene docstring, descripción, Args, Returns y Example.
        """
        return (
            self.has_docstring
            and self.has_description
            and self.has_args
            and self.has_returns
            and self.has_example
        )

    def get_missing_sections(self) -> list[str]:
        """Obtiene lista de secciones faltantes.

        Returns:
            Lista de nombres de secciones que faltan.
        """
        missing: list[str] = []
        if not self.has_docstring:
            missing.append("docstring")
        else:
            if not self.has_description:
                missing.append("descripción")
            if not self.has_args:
                missing.append("Args")
            if not self.has_returns:
                missing.append("Returns")
            if not self.has_example:
                missing.append("Example")
        return missing


@dataclass
class ValidationReport:
    """Reporte completo de validación de docstrings."""

    total_tools: int = 0
    complete_tools: int = 0
    incomplete_tools: list[DocstringCheck] = field(default_factory=list)

    def add_check(self, check: DocstringCheck) -> None:
        """Agrega un resultado de verificación al reporte.

        Args:
            check: Resultado de verificación de docstring.
        """
        self.total_tools += 1
        if check.is_complete():
            self.complete_tools += 1
        else:
            self.incomplete_tools.append(check)

    def is_passing(self) -> bool:
        """Verifica si la validación pasa (100% completos).

        Returns:
            True si todos los tools tienen docstrings completos.
        """
        return len(self.incomplete_tools) == 0

    def get_completion_percentage(self) -> float:
        """Calcula el porcentaje de completitud.

        Returns:
            Porcentaje de tools con docstrings completos.
        """
        if self.total_tools == 0:
            return 100.0
        return (self.complete_tools / self.total_tools) * 100


class DocstringChecker:
    """Verificador de docstrings para herramientas MCP."""

    REQUIRED_SECTIONS: Final[list[str]] = ["Args", "Returns", "Example"]
    OPTIONAL_SECTIONS: Final[list[str]] = ["Raises", "Note", "Notes", "Warning"]

    def check_docstring(self, docstring: str | None, func_name: str) -> DocstringCheck:
        """Verifica que un docstring tiene todas las secciones requeridas.

        Args:
            docstring: El docstring a verificar, puede ser None.
            func_name: Nombre de la función para el reporte.

        Returns:
            DocstringCheck con los resultados de la verificación.
        """
        check = DocstringCheck(function_name=func_name, file_path="")

        if not docstring:
            return check

        check.has_docstring = True

        # Verificar que hay descripción (texto antes de cualquier sección)
        lines = docstring.strip().split("\n")
        if lines and lines[0].strip():
            # La primera línea no vacía es la descripción
            first_line = lines[0].strip()
            # No debe empezar con una sección conocida
            if not any(
                first_line.startswith(f"{sec}:")
                for sec in self.REQUIRED_SECTIONS + self.OPTIONAL_SECTIONS
            ):
                check.has_description = True

        # Verificar secciones requeridas
        check.has_args = "Args:" in docstring
        check.has_returns = "Returns:" in docstring
        check.has_example = "Example:" in docstring or "Examples:" in docstring

        # Verificar secciones opcionales
        check.has_raises = "Raises:" in docstring

        return check

    def _has_mcp_tool_decorator(self, node: ast.AsyncFunctionDef) -> bool:
        """Verifica si una función tiene el decorador @mcp.tool o similar.

        Args:
            node: Nodo AST de la función.

        Returns:
            True si tiene decorador de tool MCP.
        """
        for decorator in node.decorator_list:
            # Caso: @self.mcp.tool(...) o @mcp.tool(...)
            if isinstance(decorator, ast.Call):
                func = decorator.func
                if isinstance(func, ast.Attribute) and func.attr == "tool":
                    return True
            # Caso: @self.mcp.tool (sin paréntesis)
            elif isinstance(decorator, ast.Attribute) and decorator.attr == "tool":
                return True
        return False

    def check_file(self, file_path: Path) -> list[DocstringCheck]:
        """Verifica todos los tools en un archivo Python.

        Args:
            file_path: Ruta al archivo Python a verificar.

        Returns:
            Lista de DocstringCheck para cada tool encontrado.
        """
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        results: list[DocstringCheck] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                if self._has_mcp_tool_decorator(node):
                    docstring = ast.get_docstring(node)
                    check = self.check_docstring(docstring, node.name)
                    check.file_path = str(file_path)
                    check.line_number = node.lineno
                    results.append(check)

        return results

    def check_directory(self, tools_dir: Path) -> ValidationReport:
        """Verifica todos los archivos de tools en un directorio.

        Args:
            tools_dir: Directorio que contiene los archivos de tools.

        Returns:
            ValidationReport con los resultados completos.
        """
        report = ValidationReport()

        for py_file in sorted(tools_dir.glob("*.py")):
            if py_file.name == "__init__.py":
                continue

            file_results = self.check_file(py_file)
            for check in file_results:
                report.add_check(check)

        return report


def print_report(report: ValidationReport) -> None:
    """Imprime el reporte de validación en formato legible.

    Args:
        report: Reporte de validación a imprimir.
    """
    print("\n" + "=" * 70)
    print("📋 REPORTE DE VALIDACIÓN DE DOCSTRINGS")
    print("=" * 70)

    print("\n📊 Estadísticas:")
    print(f"   Total de herramientas: {report.total_tools}")
    print(f"   ✅ Completas: {report.complete_tools}")
    print(f"   ⚠️  Incompletas: {len(report.incomplete_tools)}")
    print(f"   📈 Porcentaje: {report.get_completion_percentage():.1f}%")

    if report.incomplete_tools:
        print("\n" + "-" * 70)
        print("⚠️  HERRAMIENTAS CON DOCUMENTACIÓN INCOMPLETA:")
        print("-" * 70)

        # Agrupar por archivo
        by_file: dict[str, list[DocstringCheck]] = {}
        for check in report.incomplete_tools:
            file_name = Path(check.file_path).name
            if file_name not in by_file:
                by_file[file_name] = []
            by_file[file_name].append(check)

        for file_name, checks in sorted(by_file.items()):
            print(f"\n📁 {file_name}:")
            for check in checks:
                missing = check.get_missing_sections()
                print(f"   ❌ {check.function_name} (línea {check.line_number})")
                print(f"      Falta: {', '.join(missing)}")

    print("\n" + "=" * 70)

    if report.is_passing():
        print("✅ VALIDACIÓN EXITOSA: Todos los docstrings están completos")
    else:
        print("❌ VALIDACIÓN FALLIDA: Hay docstrings incompletos")

    print("=" * 70 + "\n")


def main() -> int:
    """Punto de entrada principal del script.

    Returns:
        0 si la validación pasa, 1 si hay errores.
    """
    tools_dir = Path("src/application/tools")

    if not tools_dir.exists():
        print(f"❌ Error: No se encontró el directorio {tools_dir}")
        return 1

    checker = DocstringChecker()
    report = checker.check_directory(tools_dir)

    print_report(report)

    return 0 if report.is_passing() else 1


if __name__ == "__main__":
    sys.exit(main())
