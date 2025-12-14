#!/usr/bin/env python3
"""Coverage analysis script for the Taiga MCP Server project.

This script analyzes pytest coverage data and generates detailed reports
by DDD layer, identifying gaps and prioritizing them by impact.

Usage:
    uv run python scripts/coverage_analysis.py
    uv run python scripts/coverage_analysis.py --json coverage.json
    uv run python scripts/coverage_analysis.py --threshold 80
    uv run python scripts/coverage_analysis.py --output report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict


class FileSummary(TypedDict):
    """Coverage summary for a single file."""

    covered_lines: int
    missing_lines: int
    num_statements: int
    percent_covered: float


class FileData(TypedDict):
    """Coverage data for a single file."""

    summary: FileSummary


class CoverageData(TypedDict):
    """Root coverage data structure."""

    totals: FileSummary
    files: dict[str, FileData]


@dataclass
class FileInfo:
    """Information about a file's coverage."""

    path: str
    percent: float
    covered: int
    missing: int
    total: int


@dataclass
class LayerCoverage:
    """Coverage data for a DDD layer."""

    name: str
    files: list[FileInfo] = field(default_factory=list)
    weight: int = 1

    @property
    def total_covered(self) -> int:
        return sum(f.covered for f in self.files)

    @property
    def total_missing(self) -> int:
        return sum(f.missing for f in self.files)

    @property
    def total_lines(self) -> int:
        return sum(f.total for f in self.files)

    @property
    def percent(self) -> float:
        if self.total_lines == 0:
            return 100.0
        return (self.total_covered / self.total_lines) * 100

    def get_gaps(self, threshold: float = 80.0) -> list[FileInfo]:
        """Get files with coverage below threshold."""
        return [f for f in self.files if f.percent < threshold]


@dataclass
class GapInfo:
    """Information about a coverage gap with impact score."""

    path: str
    layer: str
    percent: float
    missing: int
    impact_score: int
    weight: int


# DDD Layer weights (higher = more critical)
LAYER_WEIGHTS: dict[str, int] = {
    "domain/entities": 5,
    "domain/value_objects": 5,
    "domain/repositories": 4,
    "domain/exceptions": 3,
    "domain/validators": 4,
    "application/use_cases": 4,
    "application/tools": 3,
    "application/responses": 2,
    "infrastructure/repositories": 3,
    "infrastructure/logging": 2,
    "infrastructure": 2,
    "other": 1,
}


def load_coverage_data(json_path: Path) -> CoverageData:
    """Load coverage data from JSON file."""
    with open(json_path, encoding="utf-8") as f:
        data: CoverageData = json.load(f)
    return data


def classify_file(file_path: str) -> str:
    """Classify a file into its DDD layer."""
    if "domain/entities" in file_path:
        return "domain/entities"
    elif "domain/value_objects" in file_path:
        return "domain/value_objects"
    elif "domain/repositories" in file_path:
        return "domain/repositories"
    elif "domain/exceptions" in file_path:
        return "domain/exceptions"
    elif "domain/validators" in file_path:
        return "domain/validators"
    elif "application/use_cases" in file_path:
        return "application/use_cases"
    elif "application/tools" in file_path:
        return "application/tools"
    elif "application/responses" in file_path:
        return "application/responses"
    elif "infrastructure/repositories" in file_path:
        return "infrastructure/repositories"
    elif "infrastructure/logging" in file_path:
        return "infrastructure/logging"
    elif "infrastructure" in file_path:
        return "infrastructure"
    else:
        return "other"


def analyze_coverage(data: CoverageData, threshold: float = 80.0) -> dict[str, LayerCoverage]:
    """Analyze coverage data and organize by DDD layer."""
    layers: dict[str, LayerCoverage] = {}

    for layer_name, weight in LAYER_WEIGHTS.items():
        layers[layer_name] = LayerCoverage(name=layer_name, weight=weight)

    for file_path, file_data in data["files"].items():
        if not file_path.startswith("src/"):
            continue

        layer_name = classify_file(file_path)
        summary = file_data["summary"]

        file_info = FileInfo(
            path=file_path,
            percent=summary["percent_covered"],
            covered=summary["covered_lines"],
            missing=summary["missing_lines"],
            total=summary["num_statements"],
        )

        if layer_name in layers:
            layers[layer_name].files.append(file_info)

    return layers


def get_prioritized_gaps(
    layers: dict[str, LayerCoverage], threshold: float = 80.0
) -> list[GapInfo]:
    """Get all gaps prioritized by impact score."""
    gaps: list[GapInfo] = []

    for layer_name, layer in layers.items():
        for file_info in layer.files:
            if file_info.percent < threshold:
                impact = file_info.missing * layer.weight
                gaps.append(
                    GapInfo(
                        path=file_info.path,
                        layer=layer_name,
                        percent=file_info.percent,
                        missing=file_info.missing,
                        impact_score=impact,
                        weight=layer.weight,
                    )
                )

    # Sort by impact score (descending)
    gaps.sort(key=lambda x: x.impact_score, reverse=True)
    return gaps


def generate_text_report(
    data: CoverageData, layers: dict[str, LayerCoverage], gaps: list[GapInfo], threshold: float
) -> str:
    """Generate a text report of coverage analysis."""
    lines: list[str] = []
    totals = data["totals"]

    lines.append("=" * 60)
    lines.append("COVERAGE ANALYSIS REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append("=== TOTAL COVERAGE ===")
    lines.append(f"Total coverage: {totals['percent_covered']:.2f}%")
    lines.append(f"Covered lines: {totals['covered_lines']}")
    lines.append(f"Missing lines: {totals['missing_lines']}")
    lines.append(f"Total lines: {totals['num_statements']}")
    lines.append("")
    lines.append("=== COVERAGE BY DDD LAYER ===")
    lines.append("")

    for layer_name, layer in sorted(layers.items()):
        if not layer.files:
            continue
        lines.append(f"--- {layer_name.upper()} ---")
        lines.append(f"Coverage: {layer.percent:.1f}% ({layer.total_covered}/{layer.total_lines})")
        lines.append(f"Files: {len(layer.files)}")

        layer_gaps = layer.get_gaps(threshold)
        if layer_gaps:
            lines.append(f"Gaps (< {threshold}%):")
            for f in sorted(layer_gaps, key=lambda x: x.percent):
                lines.append(f"  - {f.path.replace('src/', '')}: {f.percent:.1f}% ({f.missing})")
        lines.append("")

    lines.append("=== PRIORITIZED GAPS BY IMPACT ===")
    lines.append("")
    lines.append(f"{'File':<45} | {'Layer':<20} | {'Cov%':>6} | {'Miss':>5} | {'Score':>6}")
    lines.append("-" * 95)

    for gap in gaps[:20]:
        path = gap.path.replace("src/", "")[:44]
        layer = gap.layer[:19]
        lines.append(f"{path:<45} | {layer:<20} | {gap.percent:>5.1f}% | {gap.missing:>5} | {gap.impact_score:>6}")

    return "\n".join(lines)


def generate_markdown_report(
    data: CoverageData, layers: dict[str, LayerCoverage], gaps: list[GapInfo], threshold: float
) -> str:
    """Generate a Markdown report of coverage analysis."""
    lines: list[str] = []
    totals = data["totals"]

    lines.append("# Coverage Analysis Report")
    lines.append("")
    lines.append("## Total Coverage")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Coverage | **{totals['percent_covered']:.2f}%** |")
    lines.append(f"| Covered Lines | {totals['covered_lines']} |")
    lines.append(f"| Missing Lines | {totals['missing_lines']} |")
    lines.append(f"| Total Lines | {totals['num_statements']} |")
    lines.append("")
    lines.append("## Coverage by DDD Layer")
    lines.append("")
    lines.append("| Layer | Coverage | Lines | Files | Status |")
    lines.append("|-------|----------|-------|-------|--------|")

    for layer_name, layer in sorted(layers.items()):
        if not layer.files:
            continue
        status = ":white_check_mark:" if layer.percent >= threshold else ":warning:"
        lines.append(
            f"| {layer_name} | {layer.percent:.1f}% | {layer.total_covered}/{layer.total_lines} | "
            f"{len(layer.files)} | {status} |"
        )

    lines.append("")
    lines.append("## Gaps Detail by Layer")
    lines.append("")

    for layer_name, layer in sorted(layers.items()):
        layer_gaps = layer.get_gaps(threshold)
        if not layer_gaps:
            continue
        lines.append(f"### {layer_name}")
        lines.append("")
        lines.append("| File | Coverage | Missing Lines |")
        lines.append("|------|----------|---------------|")
        for f in sorted(layer_gaps, key=lambda x: x.percent):
            path = f.path.replace("src/", "")
            lines.append(f"| {path} | {f.percent:.1f}% | {f.missing} |")
        lines.append("")

    lines.append("## Prioritized Gaps by Impact")
    lines.append("")
    lines.append("| Rank | File | Layer | Coverage | Missing | Impact Score |")
    lines.append("|------|------|-------|----------|---------|--------------|")

    for i, gap in enumerate(gaps[:20], 1):
        path = gap.path.replace("src/", "")
        lines.append(
            f"| {i} | {path} | {gap.layer} | {gap.percent:.1f}% | {gap.missing} | {gap.impact_score} |"
        )

    lines.append("")
    lines.append("## Impact Score Calculation")
    lines.append("")
    lines.append("Impact Score = Missing Lines × Layer Weight")
    lines.append("")
    lines.append("Layer weights:")
    lines.append("")
    for layer_name, weight in sorted(LAYER_WEIGHTS.items(), key=lambda x: -x[1]):
        lines.append(f"- **{layer_name}**: {weight}")

    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze pytest coverage data and generate reports"
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=Path("coverage.json"),
        help="Path to coverage JSON file (default: coverage.json)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=80.0,
        help="Coverage threshold percentage (default: 80.0)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path for Markdown report (optional)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "markdown"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args()

    if not args.json.exists():
        print(f"Error: Coverage file not found: {args.json}", file=sys.stderr)
        print("Run: uv run pytest --cov=src --cov-report=json:coverage.json", file=sys.stderr)
        return 1

    data = load_coverage_data(args.json)
    layers = analyze_coverage(data, args.threshold)
    gaps = get_prioritized_gaps(layers, args.threshold)

    if args.format == "markdown" or args.output:
        report = generate_markdown_report(data, layers, gaps, args.threshold)
    else:
        report = generate_text_report(data, layers, gaps, args.threshold)

    if args.output:
        args.output.write_text(report, encoding="utf-8")
        print(f"Report saved to: {args.output}")
    else:
        print(report)

    # Return non-zero if total coverage is below threshold
    if data["totals"]["percent_covered"] < args.threshold:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
