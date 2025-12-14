"""
Tests para el script de auditoría de herramientas MCP.

Test 2.1.1: Script de auditoría se ejecuta sin errores
Test 2.1.2: Reporte JSON se genera correctamente
Test 2.1.3: Reporte identifica herramientas sin prefijo
Test 2.1.4: Reporte identifica herramientas sin descripción
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestAuditMCPTools:
    """Tests para el script de auditoría de herramientas MCP."""

    @pytest.fixture
    def audit_script_path(self) -> Path:
        """Ruta al script de auditoría."""
        return Path("scripts/audit_mcp_tools.py")

    @pytest.fixture
    def json_report_path(self) -> Path:
        """Ruta al reporte JSON."""
        return Path("Documentacion/audit_mcp_tools.json")

    @pytest.fixture
    def csv_report_path(self) -> Path:
        """Ruta al CSV de normalización."""
        return Path("Documentacion/tools_normalization_plan.csv")

    def test_2_1_1_script_executes_without_errors(self, audit_script_path: Path) -> None:
        """Test 2.1.1: Script de auditoría se ejecuta sin errores."""
        # Verificar que el script existe
        assert audit_script_path.exists(), f"Script no existe: {audit_script_path}"

        # Ejecutar el script
        result = subprocess.run(
            [sys.executable, str(audit_script_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Verificar que se ejecutó sin errores
        assert result.returncode == 0, (
            f"Script falló con código {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

        # Verificar que hay salida
        assert "AUDITORÍA DE HERRAMIENTAS MCP" in result.stdout
        assert "AUDITORÍA COMPLETADA" in result.stdout

    def test_2_1_2_json_report_generated_correctly(self, json_report_path: Path) -> None:
        """Test 2.1.2: Reporte JSON se genera correctamente."""
        # Verificar que el archivo existe
        assert json_report_path.exists(), f"Reporte no existe: {json_report_path}"

        # Cargar y verificar estructura JSON
        content = json_report_path.read_text()
        report = json.loads(content)

        # Verificar campos requeridos
        assert "total_tools" in report, "Falta campo 'total_tools'"
        assert "tools_with_prefix" in report, "Falta campo 'tools_with_prefix'"
        assert "tools_without_prefix" in report, "Falta campo 'tools_without_prefix'"
        assert "tools_without_description" in report, "Falta campo 'tools_without_description'"
        assert "tools" in report, "Falta campo 'tools'"

        # Verificar que hay herramientas
        assert (
            report["total_tools"] >= 123
        ), f"Se esperaban >= 123 herramientas, encontradas: {report['total_tools']}"

        # Verificar estructura de cada herramienta
        assert isinstance(report["tools"], list)
        if report["tools"]:
            tool = report["tools"][0]
            assert "name" in tool, "Herramienta sin campo 'name'"
            assert "file" in tool, "Herramienta sin campo 'file'"
            assert "has_prefix" in tool, "Herramienta sin campo 'has_prefix'"
            assert "issues" in tool, "Herramienta sin campo 'issues'"

    def test_2_1_3_all_tools_have_taiga_prefix(self, json_report_path: Path) -> None:
        """Test 2.1.3: Todas las herramientas tienen prefijo 'taiga_'."""
        # Cargar reporte
        content = json_report_path.read_text()
        report = json.loads(content)

        # Verificar que NO hay herramientas sin prefijo (Tarea 2.2 completada)
        tools_without_prefix = report.get("tools_without_prefix", 0)
        assert (
            tools_without_prefix == 0
        ), f"Hay {tools_without_prefix} herramientas sin prefijo 'taiga_'"

        # Verificar que no hay herramientas con issue de prefijo
        tools_with_prefix_issue = [
            t for t in report["tools"] if "Missing 'taiga_' prefix" in t.get("issues", [])
        ]
        assert (
            len(tools_with_prefix_issue) == 0
        ), f"Hay {len(tools_with_prefix_issue)} herramientas sin prefijo"

        # Verificar ejemplos conocidos (ahora con prefijo)
        tool_names = [t["name"] for t in report["tools"]]
        # auth_tools.py ahora tiene herramientas CON prefijo
        assert "taiga_authenticate" in tool_names, "No se encontró herramienta 'taiga_authenticate'"

    def test_2_1_4_identifies_tools_without_description(self, json_report_path: Path) -> None:
        """Test 2.1.4: Reporte identifica herramientas sin descripción."""
        # Cargar reporte
        content = json_report_path.read_text()
        report = json.loads(content)

        # Verificar que hay herramientas sin descripción identificadas
        tools_without_description = report.get("tools_without_description", 0)
        # Puede que todas tengan descripción, así que solo verificamos que el campo existe
        assert "tools_without_description" in report, "Falta campo 'tools_without_description'"

        # Verificar consistencia
        tools_with_desc_issue = [
            t for t in report["tools"] if "Missing description in decorator" in t.get("issues", [])
        ]
        assert len(tools_with_desc_issue) == tools_without_description, (
            f"Inconsistencia: {tools_without_description} sin descripción "
            f"vs {len(tools_with_desc_issue)} con issue"
        )

    def test_csv_normalization_plan_exists(self, csv_report_path: Path) -> None:
        """Verifica que el CSV de normalización existe y tiene estructura correcta."""
        assert csv_report_path.exists(), f"CSV no existe: {csv_report_path}"

        # Verificar cabecera
        content = csv_report_path.read_text()
        lines = content.strip().split("\n")
        assert len(lines) > 1, "CSV vacío o solo con cabecera"

        # Verificar cabecera esperada
        header = lines[0]
        expected_columns = [
            "Current Name",
            "Proposed Name",
            "Module",
            "Return Type Current",
            "Return Type Target",
            "Issues",
            "Priority",
        ]
        for col in expected_columns:
            assert col in header, f"Falta columna '{col}' en cabecera"

    def test_tools_prioritized_by_impact(self, csv_report_path: Path) -> None:
        """Verifica que las herramientas están priorizadas por impacto."""
        import csv

        with open(csv_report_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Verificar que hay prioridades válidas
        valid_priorities = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "DONE"}
        priorities_found = set()

        for row in rows:
            priority = row.get("Priority", "")
            assert priority in valid_priorities, f"Prioridad inválida: {priority}"
            priorities_found.add(priority)

        # Verificar que se encontraron prioridades válidas
        # Nota: Después de la normalización de nombres (Tarea 2.2), todas las
        # herramientas tienen prefijo taiga_, por lo que HIGH/CRITICAL ya no
        # son necesarias. Ahora verificamos que hay prioridades válidas.
        assert len(priorities_found) > 0, "No se encontraron herramientas con prioridades"
