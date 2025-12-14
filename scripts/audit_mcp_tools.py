"""
Audita todas las herramientas MCP del servidor.

Este script analiza todos los archivos de tools en src/application/tools/
y genera un reporte detallado con información sobre cada herramienta.
"""

import ast
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ToolInfo:
    """Información de una herramienta MCP."""

    name: str = ""
    description: str = ""
    file_path: str = ""
    function_name: str = ""
    parameters: list[dict[str, str]] = field(default_factory=list)
    return_type: str = ""
    has_prefix: bool = False
    issues: list[str] = field(default_factory=list)
    line_number: int = 0


class ToolExtractor(ast.NodeVisitor):
    """Extractor de herramientas MCP usando AST."""

    def __init__(self, file_path: Path) -> None:
        """Inicializa el extractor."""
        self.file_path = file_path
        self.tools: list[ToolInfo] = []
        self._current_class: str | None = None
        self._current_function: str | None = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visita definiciones de clase."""
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visita definiciones de función para encontrar decoradores @mcp.tool."""
        self._process_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visita definiciones de función asíncrona."""
        self._process_function(node)
        self.generic_visit(node)

    def _process_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Procesa una función buscando decoradores de herramientas MCP."""
        for decorator in node.decorator_list:
            tool_info = self._extract_tool_from_decorator(decorator, node)
            if tool_info:
                self.tools.append(tool_info)

    def _extract_tool_from_decorator(
        self,
        decorator: ast.expr,
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> ToolInfo | None:
        """Extrae información de un decorador @mcp.tool o @self.mcp.tool."""
        if not isinstance(decorator, ast.Call):
            return None

        # Verificar si es un decorador .tool()
        if not isinstance(decorator.func, ast.Attribute):
            return None

        if decorator.func.attr != "tool":
            return None

        # Verificar que es mcp.tool o self.mcp.tool
        func_value = decorator.func.value
        is_mcp_tool = (isinstance(func_value, ast.Name) and func_value.id == "mcp") or (
            isinstance(func_value, ast.Attribute) and func_value.attr == "mcp"
        )

        if not is_mcp_tool:
            return None

        # Crear ToolInfo
        tool = ToolInfo()
        tool.file_path = str(self.file_path)
        tool.function_name = func_node.name
        tool.line_number = func_node.lineno

        # Extraer argumentos del decorador
        for keyword in decorator.keywords:
            if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                tool.name = str(keyword.value.value)
            elif keyword.arg == "description" and isinstance(keyword.value, ast.Constant):
                tool.description = str(keyword.value.value)

        # Si no tiene name en el decorador, usar nombre de función
        if not tool.name:
            tool.name = func_node.name

        # Extraer parámetros de la función
        tool.parameters = self._extract_parameters(func_node)

        # Extraer tipo de retorno
        tool.return_type = self._extract_return_type(func_node)

        # Analizar problemas
        self._analyze_issues(tool)

        return tool

    def _extract_parameters(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> list[dict[str, str]]:
        """Extrae los parámetros de una función."""
        params: list[dict[str, str]] = []
        args = func_node.args

        # Parámetros posicionales
        for i, arg in enumerate(args.args):
            if arg.arg == "self":
                continue

            param: dict[str, str] = {"name": arg.arg}

            # Tipo del parámetro
            if arg.annotation:
                param["type"] = ast.unparse(arg.annotation)

            # Valor por defecto
            default_offset = len(args.args) - len(args.defaults)
            if i >= default_offset:
                default = args.defaults[i - default_offset]
                if isinstance(default, ast.Constant):
                    param["default"] = repr(default.value)
                else:
                    param["default"] = ast.unparse(default)

            params.append(param)

        return params

    def _extract_return_type(self, func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        """Extrae el tipo de retorno de una función."""
        if func_node.returns:
            return ast.unparse(func_node.returns)
        return ""

    def _analyze_issues(self, tool: ToolInfo) -> None:
        """Analiza problemas potenciales en la herramienta."""
        # Verificar prefijo taiga_
        if tool.name.startswith("taiga_"):
            tool.has_prefix = True
        else:
            tool.has_prefix = False
            tool.issues.append("Missing 'taiga_' prefix")

        # Verificar descripción
        if not tool.description:
            tool.issues.append("Missing description in decorator")

        # Verificar tipo de retorno
        if not tool.return_type:
            tool.issues.append("Missing return type annotation")
        elif tool.return_type == "str":
            tool.issues.append("Returns str instead of Dict (possible JSON string)")

        # Verificar inconsistencias en nombres
        if (
            "userstory" in tool.name.lower()
            and "user_story" not in tool.name
            and "userstory" in tool.name
        ):
            tool.issues.append("Inconsistent naming: 'userstory' should be 'user_story'")


def extract_tools_from_file(file_path: Path) -> list[ToolInfo]:
    """Extrae información de tools de un archivo."""
    content = file_path.read_text()
    tree = ast.parse(content)

    extractor = ToolExtractor(file_path)
    extractor.visit(tree)

    return extractor.tools


def audit_all_tools() -> dict[str, object]:
    """Audita todas las herramientas del proyecto."""
    tools_dir = Path("src/application/tools")
    all_tools: list[ToolInfo] = []

    print(f"Buscando herramientas en: {tools_dir.absolute()}")

    for py_file in sorted(tools_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue

        print(f"  Analizando: {py_file.name}")
        file_tools = extract_tools_from_file(py_file)
        print(f"    Encontradas: {len(file_tools)} herramientas")
        all_tools.extend(file_tools)

    # Estadísticas por módulo
    modules_stats: dict[str, int] = {}
    for tool in all_tools:
        module = Path(tool.file_path).stem
        modules_stats[module] = modules_stats.get(module, 0) + 1

    # Generar reporte
    tools_list: list[dict[str, object]] = []
    for t in all_tools:
        tool_dict: dict[str, object] = {
            "name": t.name,
            "file": t.file_path,
            "function_name": t.function_name,
            "line_number": t.line_number,
            "has_prefix": t.has_prefix,
            "description": (
                t.description[:100] + "..." if len(t.description) > 100 else t.description
            ),
            "parameters": t.parameters,
            "return_type": t.return_type,
            "issues": t.issues,
        }
        tools_list.append(tool_dict)

    report: dict[str, object] = {
        "total_tools": len(all_tools),
        "tools_with_prefix": sum(1 for t in all_tools if t.has_prefix),
        "tools_without_prefix": sum(1 for t in all_tools if not t.has_prefix),
        "tools_without_description": sum(
            1 for t in all_tools if "Missing description in decorator" in t.issues
        ),
        "tools_with_issues": sum(1 for t in all_tools if t.issues),
        "modules_stats": modules_stats,
        "tools": tools_list,
    }

    return report


def generate_normalization_csv(report: dict[str, object]) -> str:
    """Genera el CSV de plan de normalización usando el módulo csv."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Escribir cabecera
    writer.writerow(
        [
            "Current Name",
            "Proposed Name",
            "Module",
            "Return Type Current",
            "Return Type Target",
            "Issues",
            "Priority",
        ]
    )

    tools = report.get("tools", [])
    if not isinstance(tools, list):
        return output.getvalue()

    for tool in tools:
        if not isinstance(tool, dict):
            continue

        name = str(tool.get("name", ""))
        file_path = str(tool.get("file", ""))
        module = Path(file_path).stem if file_path else ""
        return_type = str(tool.get("return_type", ""))
        issues_list = tool.get("issues", [])
        issues = "; ".join(issues_list) if isinstance(issues_list, list) else str(issues_list)
        has_prefix = tool.get("has_prefix", False)

        # Proponer nombre normalizado
        proposed_name = name if has_prefix else f"taiga_{name}"

        # Determinar tipo de retorno objetivo
        if return_type == "str":
            target_return_type = "dict[str, Any]"
        elif return_type:
            target_return_type = return_type
        else:
            target_return_type = "dict[str, Any]"

        # Determinar prioridad
        if not issues:
            priority = "DONE"
        elif "Returns str" in issues or "Missing return type" in issues:
            priority = "CRITICAL"
        elif "Missing 'taiga_' prefix" in issues:
            priority = "HIGH"
        elif "Inconsistent naming" in issues:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        writer.writerow(
            [
                name,
                proposed_name,
                module,
                return_type,
                target_return_type,
                issues,
                priority,
            ]
        )

    return output.getvalue()


def main() -> None:
    """Función principal del script de auditoría."""
    print("=" * 60)
    print("AUDITORÍA DE HERRAMIENTAS MCP")
    print("=" * 60)

    report = audit_all_tools()

    total_tools = report.get("total_tools", 0)
    with_prefix = report.get("tools_with_prefix", 0)
    without_prefix = report.get("tools_without_prefix", 0)
    without_desc = report.get("tools_without_description", 0)
    with_issues = report.get("tools_with_issues", 0)

    print(f"\n{'=' * 60}")
    print("RESUMEN")
    print("=" * 60)
    print(f"  Total herramientas: {total_tools}")
    print(f"  Con prefijo 'taiga_': {with_prefix}")
    print(f"  Sin prefijo: {without_prefix}")
    print(f"  Sin descripción: {without_desc}")
    print(f"  Con problemas: {with_issues}")

    # Estadísticas por módulo
    modules_stats = report.get("modules_stats", {})
    if isinstance(modules_stats, dict):
        print(f"\n{'=' * 60}")
        print("HERRAMIENTAS POR MÓDULO")
        print("=" * 60)
        for module, count in sorted(modules_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {module}: {count}")

    # Guardar reporte JSON
    output_dir = Path("Documentacion")
    output_dir.mkdir(exist_ok=True)

    json_path = output_dir / "audit_mcp_tools.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nReporte JSON guardado en: {json_path}")

    # Generar CSV de normalización
    csv_content = generate_normalization_csv(report)
    csv_path = output_dir / "tools_normalization_plan.csv"
    csv_path.write_text(csv_content)
    print(f"Plan de normalización guardado en: {csv_path}")

    # Mostrar herramientas problemáticas
    tools = report.get("tools", [])
    if isinstance(tools, list):
        problematic = [t for t in tools if isinstance(t, dict) and t.get("issues")]
        if problematic:
            print(f"\n{'=' * 60}")
            print(f"HERRAMIENTAS CON PROBLEMAS ({len(problematic)})")
            print("=" * 60)

            # Agrupar por tipo de problema
            by_issue: dict[str, list[str]] = {}
            for tool in problematic:
                issues = tool.get("issues", [])
                name = str(tool.get("name", "unknown"))
                if isinstance(issues, list):
                    for issue in issues:
                        if issue not in by_issue:
                            by_issue[issue] = []
                        by_issue[issue].append(name)

            for issue, tool_names in sorted(by_issue.items()):
                print(f"\n  {issue} ({len(tool_names)}):")
                for name in tool_names[:5]:
                    print(f"    - {name}")
                if len(tool_names) > 5:
                    print(f"    ... y {len(tool_names) - 5} más")

    print(f"\n{'=' * 60}")
    print("AUDITORÍA COMPLETADA")
    print("=" * 60)


if __name__ == "__main__":
    main()
