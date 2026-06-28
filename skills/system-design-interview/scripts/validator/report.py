"""Report generator: produces 09-eval-report.md with structured PASS/FAIL results."""

from pathlib import Path
from datetime import datetime

from .structural import StructuralReport
from .cross_file import ConsistencyReport
from .quality_signals import QualityReport


def generate_report(
    folder: Path,
    structural: StructuralReport,
    consistency: ConsistencyReport,
    quality: QualityReport,
    problem_name: str = "",
) -> str:
    """Generate the full 09-eval-report.md content."""
    if not problem_name:
        problem_name = folder.name

    lines = []
    lines.append(f"# Eval Report — {problem_name}")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Folder**: `{folder}`")
    lines.append("")

    # Overall verdict
    all_passed = structural.passed and consistency.passed and quality.passed
    struct_pass = sum(1 for r in structural.results if r.passed)
    struct_total = len(structural.results)
    consist_pass = sum(1 for r in consistency.results if r.passed)
    consist_total = len(consistency.results)
    quality_pass = sum(1 for s in quality.signals if s.passed)
    quality_total = len(quality.signals)

    total_pass = struct_pass + consist_pass + quality_pass
    total_checks = struct_total + consist_total + quality_total
    overall_pct = total_pass / total_checks * 100 if total_checks > 0 else 0

    verdict = "PASS" if all_passed else "FAIL"
    lines.append(f"## Overall: **{verdict}** ({total_pass}/{total_checks} checks passed, {overall_pct:.0f}%)")
    lines.append("")
    lines.append("| Layer | Passed | Total | Status |")
    lines.append("|-------|--------|-------|--------|")
    lines.append(f"| Structural gates | {struct_pass} | {struct_total} | {'PASS' if structural.passed else 'FAIL'} |")
    lines.append(f"| Cross-file consistency | {consist_pass} | {consist_total} | {'PASS' if consistency.passed else 'FAIL'} |")
    lines.append(f"| Quality signals | {quality_pass} | {quality_total} | {'PASS' if quality.passed else 'FAIL'} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Gate Results
    lines.append("## Gate Results")
    lines.append("")
    lines.append("| Gate | Criterion | Status | Evidence |")
    lines.append("|------|-----------|--------|----------|")
    for r in structural.results:
        evidence = r.evidence.replace("|", "\\|")[:80]
        lines.append(f"| {r.gate} | {r.criterion} | **{r.status}** | {evidence} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Cross-File Consistency
    lines.append("## Cross-File Consistency")
    lines.append("")
    lines.append("| Check | Status | Details |")
    lines.append("|-------|--------|---------|")
    for r in consistency.results:
        details = r.details.replace("|", "\\|")[:80]
        lines.append(f"| {r.check_name} | **{r.status}** | {details} |")
    lines.append("")

    for r in consistency.results:
        if r.unmatched:
            lines.append(f"**{r.check_name} — unmatched items:**")
            for item in r.unmatched[:5]:
                lines.append(f"- {item}")
            lines.append("")

    lines.append("---")
    lines.append("")

    # Quality Signals
    lines.append("## Quality Signals")
    lines.append("")
    lines.append("| Signal | Count | Target | Status |")
    lines.append("|--------|-------|--------|--------|")
    for s in quality.signals:
        lines.append(f"| {s.name} | {s.count} | >= {s.target} | **{s.status}** |")
    lines.append("")
    lines.append(f"**Quality score**: {quality.score:.0f}%")
    lines.append("")

    # Quality details
    for s in quality.signals:
        if s.examples and not s.passed:
            lines.append(f"**{s.name}** (needs improvement):")
            for ex in s.examples[:3]:
                lines.append(f"  - {ex}")
            lines.append("")

    lines.append("---")
    lines.append("")

    # Known Issues
    lines.append("## Known Issues")
    lines.append("")
    failed_gates = [r for r in structural.results if not r.passed]
    failed_consistency = [r for r in consistency.results if not r.passed]
    failed_quality = [s for s in quality.signals if not s.passed]

    if not failed_gates and not failed_consistency and not failed_quality:
        lines.append("None — all checks passed.")
    else:
        if failed_gates:
            lines.append("### Gate Failures")
            for r in failed_gates:
                lines.append(f"- **{r.gate} / {r.criterion}**: {r.evidence}")
            lines.append("")
        if failed_consistency:
            lines.append("### Consistency Failures")
            for r in failed_consistency:
                lines.append(f"- **{r.check_name}**: {r.details}")
            lines.append("")
        if failed_quality:
            lines.append("### Quality Gaps")
            for s in failed_quality:
                lines.append(f"- **{s.name}**: found {s.count}, need >= {s.target}")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Report generated by `system-design-skill/validator`. Run with:*")
    lines.append(f"*`python -m system_design_skill.validator validate {folder.name}/`*")

    return "\n".join(lines)


def write_report(
    folder: Path,
    structural: StructuralReport,
    consistency: ConsistencyReport,
    quality: QualityReport,
) -> Path:
    """Generate and write 09-eval-report.md to the problem folder."""
    content = generate_report(folder, structural, consistency, quality)
    report_path = folder / "09-eval-report.md"
    report_path.write_text(content, encoding="utf-8")
    return report_path
