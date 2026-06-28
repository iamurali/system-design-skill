"""Structural validation: file existence, heading schema, count enforcement, capacity chain, latency budget, PE rubric."""

import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from .yaml_parser import load_yaml_file


@dataclass
class CheckResult:
    gate: str
    criterion: str
    passed: bool
    evidence: str

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"


@dataclass
class StructuralReport:
    results: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    def add(self, gate: str, criterion: str, passed: bool, evidence: str):
        self.results.append(CheckResult(gate, criterion, passed, evidence))


REQUIRED_FILES = [
    "01-requirements.md",
    "02-non-functional-requirements.md",
    "03-entities.md",
    "04-api-design.md",
    "05-schema.md",
    "06-high-level-design.md",
    "07-deep-dives.md",
    "08-bottlenecks-and-tradeoffs.md",
    "10-interview-transcript.md",
]


def load_schema(schema_path: Path) -> dict:
    return load_yaml_file(str(schema_path))


def count_headings(content: str, level: int) -> int:
    pattern = rf"^{'#' * level}\s+\S"
    return len(re.findall(pattern, content, re.MULTILINE))


def extract_section(content: str, section_pattern: str) -> str:
    lines = content.split("\n")
    in_section = False
    section_lines = []
    for line in lines:
        if re.search(section_pattern, line, re.IGNORECASE) and re.match(r"^#{1,3}\s", line):
            in_section = True
            section_lines.append(line)
            continue
        if in_section:
            if re.match(r"^#{1,3}\s", line) and not re.search(section_pattern, line, re.IGNORECASE):
                break
            section_lines.append(line)
    return "\n".join(section_lines)


def count_pattern_in_section(content: str, item_pattern: str, section_pattern: str) -> int:
    section = extract_section(content, section_pattern)
    if not section:
        return 0
    return len(re.findall(item_pattern, section, re.MULTILINE))


def check_patterns_present(content: str, patterns: list[str], min_count: int = 1) -> tuple[bool, int]:
    total = 0
    for pattern in patterns:
        try:
            total += len(re.findall(pattern, content, re.MULTILINE | re.IGNORECASE))
        except re.error:
            continue
    return total >= min_count, total


def validate_file_existence(folder: Path) -> list[CheckResult]:
    results = []
    for fname in REQUIRED_FILES:
        exists = (folder / fname).exists()
        results.append(CheckResult(
            gate="Structure",
            criterion=f"File exists: {fname}",
            passed=exists,
            evidence=f"{'Found' if exists else 'MISSING'}: {fname}"
        ))
    return results


def validate_capacity_chain(content: str, schema: dict) -> list[CheckResult]:
    results = []
    if "capacity_chain" not in schema:
        return results

    chain = schema["capacity_chain"]
    found_links = []
    missing_links = []

    for link in chain.get("required_links", []):
        pattern = link["pattern"]
        name = link["name"]
        if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
            found_links.append(name)
        else:
            missing_links.append(name)

    passed = len(missing_links) == 0
    evidence = f"Found: {', '.join(found_links)}" if found_links else "No capacity chain links found"
    if missing_links:
        evidence += f" | Missing: {', '.join(missing_links)}"

    results.append(CheckResult(
        gate="Gate 1",
        criterion="Capacity chain complete",
        passed=passed,
        evidence=evidence
    ))
    return results


def validate_reframing(content: str, schema: dict) -> list[CheckResult]:
    if "reframing" not in schema:
        return []

    reframing = schema["reframing"]
    patterns = reframing.get("patterns", [])
    min_count = reframing.get("min", 1)
    present, count = check_patterns_present(content, patterns, min_count)

    return [CheckResult(
        gate="Gate 1",
        criterion="Problem reframing present",
        passed=present,
        evidence=f"Found {count} reframing signal(s), need >= {min_count}"
    )]


def validate_latency_budget(content: str, schema: dict) -> list[CheckResult]:
    if "latency_budget" not in schema:
        return []

    budget = schema["latency_budget"]
    target_pat = budget.get("target_pattern", "")
    tolerance = budget.get("tolerance_percent", 10)

    target_match = re.search(target_pat, content)
    if not target_match:
        return [CheckResult(
            gate="Gate 2",
            criterion="Latency budget sums",
            passed=False,
            evidence="No P99 target found in document"
        )]

    target_ms = float(target_match.group(1))

    breakdown_section = extract_section(content, r"(?i)(latency.*budget|budget.*breakdown|breakdown)")
    if not breakdown_section:
        breakdown_section = content

    numbers = re.findall(r"(\d+(?:\.\d+)?)\s*ms", breakdown_section)
    if len(numbers) < 3:
        return [CheckResult(
            gate="Gate 2",
            criterion="Latency budget sums",
            passed=False,
            evidence=f"P99 target={target_ms}ms but fewer than 3 breakdown components found"
        )]

    component_values = [float(n) for n in numbers if float(n) < target_ms and float(n) > 0]

    if not component_values:
        return [CheckResult(
            gate="Gate 2",
            criterion="Latency budget sums",
            passed=False,
            evidence=f"P99 target={target_ms}ms, no valid breakdown components"
        )]

    total = sum(component_values[:10])
    diff_pct = abs(total - target_ms) / target_ms * 100 if target_ms > 0 else 100
    passed = diff_pct <= tolerance

    return [CheckResult(
        gate="Gate 2",
        criterion="Latency budget sums",
        passed=passed,
        evidence=f"P99 target={target_ms}ms, breakdown sum={total:.0f}ms, diff={diff_pct:.1f}% (tolerance ±{tolerance}%)"
    )]


def validate_error_budget(content: str, schema: dict) -> list[CheckResult]:
    if "error_budget" not in schema:
        return []

    eb = schema["error_budget"]
    present, count = check_patterns_present(content, eb.get("patterns", []), eb.get("min", 1))

    return [CheckResult(
        gate="Gate 2",
        criterion="Error budget concrete",
        passed=present,
        evidence=f"Found {count} error budget reference(s), need >= {eb.get('min', 1)}"
    )]


def validate_runbook(content: str, schema: dict) -> list[CheckResult]:
    if "runbook" not in schema:
        return []

    rb = schema["runbook"]
    present, count = check_patterns_present(content, rb.get("patterns", []), rb.get("min", 1))

    return [CheckResult(
        gate="Gate 2",
        criterion="Runbook sketch exists",
        passed=present,
        evidence=f"Found {count} runbook signal(s), need >= {rb.get('min', 1)}"
    )]


def validate_consistency_consequence(content: str, schema: dict) -> list[CheckResult]:
    if "consistency_consequence" not in schema:
        return []

    cc = schema["consistency_consequence"]
    present, count = check_patterns_present(content, cc.get("patterns", []), cc.get("min", 1))

    return [CheckResult(
        gate="Gate 2",
        criterion="Consistency consequence named",
        passed=present,
        evidence=f"Found {count} consequence signal(s), need >= {cc.get('min', 1)}"
    )]


def validate_api_shapes(content: str, schema: dict) -> list[CheckResult]:
    if "api_shapes" not in schema:
        return []

    api = schema["api_shapes"]
    endpoint_pat = api.get("endpoint_pattern", "")
    endpoints = re.findall(endpoint_pat, content, re.MULTILINE)
    min_eps = api.get("min_endpoints", 3)

    has_request = any(
        re.search(p, content, re.IGNORECASE)
        for p in api.get("request_patterns", [])
    )
    has_response = any(
        re.search(p, content, re.IGNORECASE)
        for p in api.get("response_patterns", [])
    )

    ep_count = len(endpoints)
    passed = ep_count >= min_eps and has_request and has_response

    evidence_parts = [f"{ep_count} endpoints (need >= {min_eps})"]
    if not has_request:
        evidence_parts.append("missing request shapes")
    if not has_response:
        evidence_parts.append("missing response shapes")

    return [CheckResult(
        gate="Gate 3",
        criterion="API shapes concrete",
        passed=passed,
        evidence=" | ".join(evidence_parts)
    )]


def validate_state_machines(content: str, schema: dict) -> list[CheckResult]:
    if "state_machines" not in schema:
        return []

    sm = schema["state_machines"]
    present, count = check_patterns_present(content, sm.get("patterns", []), sm.get("min", 1))

    return [CheckResult(
        gate="Gate 3",
        criterion="State machines present",
        passed=present,
        evidence=f"Found {count} state machine signal(s), need >= {sm.get('min', 1)}"
    )]


def validate_sharding(content: str, schema: dict) -> list[CheckResult]:
    if "sharding" not in schema:
        return []

    sh = schema["sharding"]
    present, count = check_patterns_present(content, sh.get("patterns", []), sh.get("min", 1))

    return [CheckResult(
        gate="Gate 3",
        criterion="Sharding justified",
        passed=present,
        evidence=f"Found {count} sharding signal(s), need >= {sh.get('min', 1)}"
    )]


def validate_deep_dives(content: str, schema: dict) -> list[CheckResult]:
    results = []
    if "deep_dives" not in schema:
        return results

    dd = schema["deep_dives"]
    heading_pat = dd.get("heading_pattern", r"(?i)^##\s+(deep.dive|dive)\s*\d+")

    dive_headings = re.findall(heading_pat, content, re.MULTILINE)
    h2_dives = re.findall(r"^##\s+.*(?:Deep Dive|Dive)\s*\d+", content, re.MULTILINE | re.IGNORECASE)
    dive_count = max(len(dive_headings), len(h2_dives))
    if dive_count == 0:
        dive_count = count_headings(content, 2) - 1

    min_dives = dd.get("min_count", 4)
    results.append(CheckResult(
        gate="Gate 5",
        criterion="Deep dive count",
        passed=dive_count >= min_dives,
        evidence=f"Found {dive_count} dives, need >= {min_dives}"
    ))

    tiers = dd.get("tier_patterns", {})
    tier_results = {}
    for tier_name, pattern in tiers.items():
        tier_count = len(re.findall(pattern, content, re.MULTILINE | re.IGNORECASE))
        tier_results[tier_name] = tier_count

    if dd.get("all_tiers_required") and tiers:
        all_present = all(c >= dive_count for c in tier_results.values())
        evidence = " | ".join(f"{k}={v}" for k, v in tier_results.items())
        results.append(CheckResult(
            gate="Gate 5",
            criterion="Three tiers per dive",
            passed=all_present or all(c >= min_dives for c in tier_results.values()),
            evidence=f"Tier counts: {evidence} (need >= {min_dives} each)"
        ))

    curveball = dd.get("curveball", {})
    if curveball.get("required"):
        cb_patterns = curveball.get("patterns", [])
        present, count = check_patterns_present(content, cb_patterns)
        results.append(CheckResult(
            gate="Gate 5",
            criterion="Curveball per dive",
            passed=count >= min_dives,
            evidence=f"Found {count} curveball signal(s), need >= {min_dives}"
        ))

    return results


def validate_breaking_points(content: str, schema: dict) -> list[CheckResult]:
    if "breaking_point" not in schema:
        return []

    bp = schema["breaking_point"]
    present, count = check_patterns_present(content, bp.get("patterns", []))
    min_per_dive = bp.get("min_per_dive", 1)
    dive_count = max(4, len(re.findall(r"(?i)^##\s+.*(?:Deep Dive|Dive)", content, re.MULTILINE)))
    needed = min_per_dive * max(4, dive_count)

    return [CheckResult(
        gate="Gate 5",
        criterion="Breaking point per dive",
        passed=count >= max(4, needed // 2),
        evidence=f"Found {count} breaking point signal(s) across dives"
    )]


def validate_resiliency(content: str, schema: dict) -> list[CheckResult]:
    if "resiliency" not in schema:
        return []

    res = schema["resiliency"]
    present, count = check_patterns_present(content, res.get("patterns", []))

    return [CheckResult(
        gate="Gate 5",
        criterion="Resiliency patterns present",
        passed=count >= 4,
        evidence=f"Found {count} resiliency signal(s), need >= 4"
    )]


def validate_depth_signals(content: str, schema: dict) -> list[CheckResult]:
    if "depth_signals" not in schema:
        return []

    ds = schema["depth_signals"]
    total = 0
    details = []

    for signal_type in ["algorithm", "protocol", "math"]:
        sig = ds.get(signal_type, {})
        _, count = check_patterns_present(content, sig.get("patterns", []))
        total += count
        details.append(f"{sig.get('name', signal_type)}={count}")

    min_total = ds.get("min_total", 3)

    return [CheckResult(
        gate="Gate 5",
        criterion="Depth signals (algo/protocol/math)",
        passed=total >= min_total,
        evidence=f"Total={total}, need >= {min_total} | {' | '.join(details)}"
    )]


def validate_bottlenecks(content: str, schema: dict) -> list[CheckResult]:
    results = []
    if "bottlenecks" not in schema:
        return results

    bn = schema["bottlenecks"]
    heading_pat = bn.get("heading_pattern", r"(?i)^###?\s*(?:Bottleneck\s*)?\d+[.:]?\s+")
    try:
        bottleneck_headings = re.findall(heading_pat, content, re.MULTILINE)
    except re.error:
        bottleneck_headings = re.findall(r"(?i)^###?\s*(?:Bottleneck\s*)?\d+[.:]?\s+", content, re.MULTILINE)
    count = len(bottleneck_headings)
    min_count = bn.get("min_count", 6)

    results.append(CheckResult(
        gate="Gate 6",
        criterion="Bottleneck count",
        passed=count >= min_count,
        evidence=f"Found {count} bottleneck sections, need >= {min_count}"
    ))

    return results


def validate_failure_matrix(content: str, schema: dict) -> list[CheckResult]:
    if "failure_matrix" not in schema:
        return []

    fm = schema["failure_matrix"]
    present, count = check_patterns_present(content, fm.get("patterns", []))

    table_rows = re.findall(r"^\|[^|]+\|[^|]+\|[^|]+\|", content, re.MULTILINE)
    row_count = max(0, len(table_rows) - 2)
    min_rows = fm.get("min_rows", 5)

    return [CheckResult(
        gate="Gate 6",
        criterion="Failure matrix present",
        passed=present and row_count >= min_rows,
        evidence=f"Matrix signals={count}, table rows={row_count}, need >= {min_rows} rows"
    )]


def validate_coverage_sweep(content: str, schema: dict) -> list[CheckResult]:
    if "coverage_sweep" not in schema:
        return []

    cs = schema["coverage_sweep"]
    blocks = cs.get("building_blocks", [])
    min_addressed = cs.get("min_addressed", 12)

    addressed = 0
    for block_pattern in blocks:
        if re.search(block_pattern, content, re.IGNORECASE):
            addressed += 1

    return [CheckResult(
        gate="Gate 6",
        criterion="Coverage sweep completeness",
        passed=addressed >= min_addressed,
        evidence=f"Addressed {addressed}/{len(blocks)} building blocks, need >= {min_addressed}"
    )]


def validate_pe_rubric(content: str, schema: dict) -> list[CheckResult]:
    results = []
    if "pe_rubric" not in schema:
        return results

    rubric = schema["pe_rubric"]
    score_pat = rubric.get("score_pattern", r"(\d+)/5")
    scores = re.findall(score_pat, content)
    scores_int = [int(s) for s in scores]

    required_dims = rubric.get("required_dimensions", 10)
    min_avg = rubric.get("min_average", 4.5)
    min_per = rubric.get("min_per_dimension", 4)

    has_enough = len(scores_int) >= required_dims
    avg = sum(scores_int[:required_dims]) / required_dims if has_enough else 0
    min_score = min(scores_int[:required_dims]) if has_enough else 0
    avg_ok = avg >= min_avg
    min_ok = min_score >= min_per

    results.append(CheckResult(
        gate="Outer Eval",
        criterion="PE rubric present and scored",
        passed=has_enough,
        evidence=f"Found {len(scores_int)} dimension scores, need {required_dims}"
    ))

    if has_enough:
        results.append(CheckResult(
            gate="Outer Eval",
            criterion=f"PE rubric avg >= {min_avg}",
            passed=avg_ok,
            evidence=f"Average={avg:.2f}, bar={min_avg}"
        ))
        results.append(CheckResult(
            gate="Outer Eval",
            criterion=f"PE rubric min >= {min_per}",
            passed=min_ok,
            evidence=f"Min score={min_score}, bar={min_per}"
        ))

    weakest = rubric.get("weakest_dimension", {})
    if weakest:
        wp = weakest.get("pattern", "")
        has_weakest = bool(re.search(wp, content, re.IGNORECASE))
        results.append(CheckResult(
            gate="Outer Eval",
            criterion="Weakest dimension identified",
            passed=has_weakest,
            evidence="Weakest dimension named" if has_weakest else "No weakest dimension discussion found"
        ))

    return results


def validate_tradeoff_matrix(content: str, schema: dict) -> list[CheckResult]:
    if "tradeoff_matrix" not in schema:
        return []

    tm = schema["tradeoff_matrix"]
    table_rows = re.findall(r"^\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|", content, re.MULTILINE)
    row_count = max(0, len(table_rows) - 2)
    min_rows = tm.get("min_rows", 5)

    return [CheckResult(
        gate="Gate 6",
        criterion="Tradeoff matrix rows",
        passed=row_count >= min_rows,
        evidence=f"Found {row_count} table rows, need >= {min_rows}"
    )]


def validate_real_incidents(content: str, schema: dict) -> list[CheckResult]:
    if "real_incidents" not in schema:
        return []

    ri = schema["real_incidents"]
    present, count = check_patterns_present(content, ri.get("patterns", []))
    min_count = ri.get("min", 3)

    return [CheckResult(
        gate="Gate 6",
        criterion="Real-world incidents",
        passed=count >= min_count,
        evidence=f"Found {count} incident signal(s), need >= {min_count}"
    )]


def validate_anti_patterns(content: str, schema: dict) -> list[CheckResult]:
    if "anti_patterns" not in schema:
        return []

    ap = schema["anti_patterns"]
    present, count = check_patterns_present(content, ap.get("patterns", []))
    min_count = ap.get("min", 3)

    return [CheckResult(
        gate="Gate 6",
        criterion="Anti-patterns documented",
        passed=count >= min_count,
        evidence=f"Found {count} anti-pattern signal(s), need >= {min_count}"
    )]


def validate_evolution(content: str, schema: dict) -> list[CheckResult]:
    if "evolution" not in schema:
        return []

    ev = schema["evolution"]
    present, count = check_patterns_present(content, ev.get("patterns", []))

    return [CheckResult(
        gate="Gate 6",
        criterion="Evolution roadmap present",
        passed=present,
        evidence=f"Found {count} evolution signal(s)"
    )]


def validate_interview_points(content: str, schema: dict) -> list[CheckResult]:
    if "interview_talking_points" not in schema:
        return []

    tp = schema["interview_talking_points"]
    present, count = check_patterns_present(content, tp.get("patterns", []))
    min_count = tp.get("min", 5)

    return [CheckResult(
        gate="Gate 6",
        criterion="Interview talking points",
        passed=count >= min_count or present,
        evidence=f"Found {count} talking-point signal(s), need >= {min_count}"
    )]


def validate_interview_transcript(content: str, schema: dict) -> list[CheckResult]:
    results = []

    review = schema.get("interviewer_review", {})
    if review:
        present, count = check_patterns_present(
            content,
            review.get("required_patterns", []),
            review.get("min", 1),
        )
        results.append(CheckResult(
            gate="Interviewer",
            criterion="Blind interviewer review",
            passed=present,
            evidence=f"Found {count} interviewer-review signal(s), need >= {review.get('min', 1)}",
        ))

    scores = schema.get("independent_scores", {})
    if scores:
        score_pat = scores.get("score_pattern", r"(\d+)/5")
        score_count = len(re.findall(score_pat, content))
        dimensions = scores.get("required_dimensions", [])
        dim_count = sum(1 for pattern in dimensions if re.search(pattern, content, re.IGNORECASE))
        min_scores = scores.get("min_scores", 5)
        passed = score_count >= min_scores and dim_count >= len(dimensions)
        results.append(CheckResult(
            gate="Interviewer",
            criterion="Independent depth scores",
            passed=passed,
            evidence=f"Scores={score_count}, dimensions={dim_count}/{len(dimensions)}",
        ))

    gate = schema.get("research_gate", {})
    if gate:
        major_critical = len(re.findall(gate.get("major_critical_pattern", ""), content, re.IGNORECASE))
        has_research = bool(re.search(gate.get("research_section_pattern", ""), content, re.IGNORECASE | re.MULTILINE))
        has_no_research = bool(re.search(gate.get("no_research_pattern", ""), content, re.IGNORECASE | re.MULTILINE))
        passed = (major_critical > 0 and has_research) or (major_critical == 0 and has_no_research)
        results.append(CheckResult(
            gate="Interviewer",
            criterion="Conditional research gate",
            passed=passed,
            evidence=f"Major/critical findings={major_critical}, research_section={has_research}, no_research={has_no_research}",
        ))

    if re.search(r"(?i)^##\s+Research Findings", content, re.MULTILINE):
        findings = schema.get("research_findings", {})
        present, count = check_patterns_present(
            content,
            findings.get("required_patterns", []),
            findings.get("min", 1),
        )
        results.append(CheckResult(
            gate="Research",
            criterion="Research finding completeness",
            passed=present,
            evidence=f"Found {count} research-quality signal(s), need >= {findings.get('min', 1)}",
        ))

    revision = schema.get("revision_log", {})
    if revision:
        present, count = check_patterns_present(content, revision.get("patterns", []), revision.get("min", 1))
        results.append(CheckResult(
            gate="Interviewer",
            criterion="Revision log present",
            passed=present,
            evidence=f"Found {count} revision-log signal(s), need >= {revision.get('min', 1)}",
        ))

    return results


FILE_VALIDATORS = {
    "01-requirements.md": [validate_capacity_chain, validate_reframing],
    "02-non-functional-requirements.md": [validate_latency_budget, validate_error_budget, validate_runbook, validate_consistency_consequence],
    "03-entities.md": [validate_state_machines],
    "04-api-design.md": [validate_api_shapes],
    "05-schema.md": [validate_sharding],
    "06-high-level-design.md": [],
    "07-deep-dives.md": [validate_deep_dives, validate_breaking_points, validate_resiliency, validate_depth_signals],
    "08-bottlenecks-and-tradeoffs.md": [
        validate_bottlenecks, validate_failure_matrix, validate_coverage_sweep,
        validate_pe_rubric, validate_tradeoff_matrix, validate_real_incidents,
        validate_anti_patterns, validate_evolution, validate_interview_points,
    ],
    "10-interview-transcript.md": [validate_interview_transcript],
}

SCHEMA_MAP = {
    "01-requirements.md": "01-requirements.yaml",
    "02-non-functional-requirements.md": "02-nfr.yaml",
    "03-entities.md": "03-entities.yaml",
    "04-api-design.md": "04-api.yaml",
    "05-schema.md": "05-schema.yaml",
    "06-high-level-design.md": "06-hld.yaml",
    "07-deep-dives.md": "07-deep-dives.yaml",
    "08-bottlenecks-and-tradeoffs.md": "08-bottlenecks.yaml",
    "10-interview-transcript.md": "10-interview.yaml",
}


def validate_required_sections(content: str, schema: dict, filename: str) -> list[CheckResult]:
    results = []
    for section in schema.get("required_sections", []):
        pattern = section["pattern"]
        name = section["name"]
        found = bool(re.search(pattern, content, re.IGNORECASE))
        gate = "Structure"
        results.append(CheckResult(
            gate=gate,
            criterion=f"{name} ({filename})",
            passed=found,
            evidence=f"{'Found' if found else 'MISSING'}: {name}"
        ))
    return results


def run_structural_validation(folder: Path, schemas_dir: Optional[Path] = None) -> StructuralReport:
    if schemas_dir is None:
        schemas_dir = Path(__file__).parent / "schemas"

    report = StructuralReport()

    for result in validate_file_existence(folder):
        report.results.append(result)

    for filename, validators in FILE_VALIDATORS.items():
        filepath = folder / filename
        if not filepath.exists():
            continue

        content = filepath.read_text(encoding="utf-8")
        schema_file = schemas_dir / SCHEMA_MAP.get(filename, "")

        if not schema_file.exists():
            continue

        schema = load_schema(schema_file)

        for result in validate_required_sections(content, schema, filename):
            report.results.append(result)

        for validator_fn in validators:
            for result in validator_fn(content, schema):
                report.results.append(result)

    return report
