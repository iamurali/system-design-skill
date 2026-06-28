"""CLI entry point for the system design validator.

Usage:
    python -m system_design_skill.validator validate <folder>
    python -m system_design_skill.validator validate system-design/01-news-aggregation-personalized-feed/
"""

import sys
import argparse
from pathlib import Path

from .structural import run_structural_validation
from .cross_file import run_cross_file_checks
from .quality_signals import run_quality_scoring
from .report import write_report


def print_header(text: str):
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def print_section(title: str, passed: bool, pass_count: int, total: int):
    status = "\033[32mPASS\033[0m" if passed else "\033[31mFAIL\033[0m"
    print(f"  [{status}] {title}: {pass_count}/{total} checks passed")


def validate_command(args):
    folder = Path(args.folder).resolve()

    if not folder.exists():
        print(f"\033[31mError\033[0m: Folder not found: {folder}")
        sys.exit(2)

    if not folder.is_dir():
        print(f"\033[31mError\033[0m: Not a directory: {folder}")
        sys.exit(2)

    problem_name = folder.name
    print_header(f"Validating: {problem_name}")

    schemas_dir = Path(__file__).parent / "schemas"

    print("  Running structural validation...")
    structural = run_structural_validation(folder, schemas_dir)
    struct_pass = sum(1 for r in structural.results if r.passed)
    struct_total = len(structural.results)
    print_section("Structural", structural.passed, struct_pass, struct_total)

    print("  Running cross-file consistency checks...")
    consistency = run_cross_file_checks(folder)
    consist_pass = sum(1 for r in consistency.results if r.passed)
    consist_total = len(consistency.results)
    print_section("Consistency", consistency.passed, consist_pass, consist_total)

    print("  Running quality signal scoring...")
    quality = run_quality_scoring(folder)
    quality_pass = sum(1 for s in quality.signals if s.passed)
    quality_total = len(quality.signals)
    print_section("Quality", quality.passed, quality_pass, quality_total)

    report_path = write_report(folder, structural, consistency, quality)

    print(f"\n  Report written to: {report_path.relative_to(folder.parent)}")

    total_pass = struct_pass + consist_pass + quality_pass
    total_checks = struct_total + consist_total + quality_total
    overall_pct = total_pass / total_checks * 100 if total_checks > 0 else 0
    all_passed = structural.passed and consistency.passed and quality.passed

    print_header(f"OVERALL: {'PASS' if all_passed else 'FAIL'} ({total_pass}/{total_checks}, {overall_pct:.0f}%)")

    if not all_passed:
        print("  Failed checks:")
        for r in structural.results:
            if not r.passed:
                print(f"    - [{r.gate}] {r.criterion}: {r.evidence[:60]}")
        for r in consistency.results:
            if not r.passed:
                print(f"    - [Consistency] {r.check_name}: {r.details[:60]}")
        for s in quality.signals:
            if not s.passed:
                print(f"    - [Quality] {s.name}: {s.count}/{s.target}")
        print()

    sys.exit(0 if all_passed else 1)


def main():
    parser = argparse.ArgumentParser(
        prog="system_design_skill.validator",
        description="Validate system design output against PE-grade quality gates",
    )
    subparsers = parser.add_subparsers(dest="command")

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a system design problem folder",
    )
    validate_parser.add_argument(
        "folder",
        help="Path to the problem folder (e.g., system-design/01-news-aggregation-personalized-feed/)",
    )
    validate_parser.set_defaults(func=validate_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
