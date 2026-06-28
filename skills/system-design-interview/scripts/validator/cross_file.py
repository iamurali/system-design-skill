"""Cross-file consistency checks: numbers flow, API-schema alignment, requirements-architecture, deep-dive relevance, bottleneck authenticity."""

import re
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class ConsistencyResult:
    check_name: str
    passed: bool
    details: str
    matched: list[str] = field(default_factory=list)
    unmatched: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"


@dataclass
class ConsistencyReport:
    results: list[ConsistencyResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)


def extract_numbers_with_units(content: str) -> dict[str, list[str]]:
    """Extract QPS, storage, and bandwidth numbers from content."""
    numbers = {}

    qps_patterns = [
        r"(\d+[\d,]*\.?\d*)\s*[KMB]?\s*(QPS|req/s|requests?/s|ops/s|TPS|queries/s)",
        r"([\d,]+\.?\d*)\s*[KMB]\s*(QPS|req|ops|TPS)",
    ]
    numbers["qps"] = []
    for pat in qps_patterns:
        for match in re.finditer(pat, content, re.IGNORECASE):
            numbers["qps"].append(match.group(0))

    storage_patterns = [
        r"(\d+[\d,]*\.?\d*)\s*(TB|GB|MB|PB|KB)\s*(/?(?:day|month|year))?",
    ]
    numbers["storage"] = []
    for pat in storage_patterns:
        for match in re.finditer(pat, content, re.IGNORECASE):
            numbers["storage"].append(match.group(0))

    bw_patterns = [
        r"(\d+[\d,]*\.?\d*)\s*(GB/s|MB/s|Gbps|Mbps|TB/day)",
    ]
    numbers["bandwidth"] = []
    for pat in bw_patterns:
        for match in re.finditer(pat, content, re.IGNORECASE):
            numbers["bandwidth"].append(match.group(0))

    return numbers


def normalize_number(text: str) -> float:
    """Convert a number string with K/M/B suffix to raw float."""
    text = text.replace(",", "").strip()
    match = re.match(r"([\d.]+)\s*([KMBkmb])?", text)
    if not match:
        return 0
    val = float(match.group(1))
    suffix = (match.group(2) or "").upper()
    multipliers = {"K": 1e3, "M": 1e6, "B": 1e9}
    return val * multipliers.get(suffix, 1)


def extract_qps_magnitude(content: str) -> list[float]:
    """Extract QPS numbers and normalize to raw values."""
    patterns = [
        r"([\d,]+\.?\d*)\s*([KMB])?\s*(?:QPS|req/s|ops/s|TPS)",
        r"~?([\d,]+\.?\d*)\s*([KMB])\s*(?:QPS|req|ops)",
    ]
    values = []
    for pat in patterns:
        for match in re.finditer(pat, content, re.IGNORECASE):
            raw = match.group(1).replace(",", "")
            suffix = match.group(2) or ""
            val = float(raw)
            multipliers = {"K": 1e3, "M": 1e6, "B": 1e9, "k": 1e3, "m": 1e6, "b": 1e9}
            val *= multipliers.get(suffix, 1)
            values.append(val)
    return values


def check_numbers_flow(requirements_content: str, hld_content: str) -> ConsistencyResult:
    """Check 1: Numbers from requirements appear (order-of-magnitude) in HLD."""
    req_qps = extract_qps_magnitude(requirements_content)
    hld_qps = extract_qps_magnitude(hld_content)

    if not req_qps:
        return ConsistencyResult(
            check_name="Numbers flow",
            passed=False,
            details="No QPS numbers found in requirements"
        )

    if not hld_qps:
        return ConsistencyResult(
            check_name="Numbers flow",
            passed=False,
            details="No QPS numbers found in HLD"
        )

    matched = []
    unmatched = []

    for rq in req_qps[:5]:
        found_match = False
        for hq in hld_qps:
            ratio = max(rq, hq) / max(min(rq, hq), 1)
            if ratio <= 10:
                found_match = True
                matched.append(f"req={rq:.0f} ≈ hld={hq:.0f}")
                break
        if not found_match:
            unmatched.append(f"req={rq:.0f} not found in HLD (within 10x)")

    passed = len(matched) > 0 and len(unmatched) <= len(matched)

    details_parts = []
    if matched:
        details_parts.append(f"Matched: {'; '.join(matched[:3])}")
    if unmatched:
        details_parts.append(f"Unmatched: {'; '.join(unmatched[:3])}")

    return ConsistencyResult(
        check_name="Numbers flow",
        passed=passed,
        details=" | ".join(details_parts),
        matched=matched,
        unmatched=unmatched,
    )


def extract_endpoints(api_content: str) -> list[str]:
    """Extract API endpoint paths from the API design file."""
    patterns = [
        r"(?:GET|POST|PUT|DELETE|PATCH)\s+[`/]([^\s`]+)",
        r"`((?:GET|POST|PUT|DELETE|PATCH)\s+/[^\s`]+)`",
    ]
    endpoints = set()
    for pat in patterns:
        for match in re.finditer(pat, api_content, re.IGNORECASE):
            ep = match.group(1) if match.group(1).startswith("/") else match.group(0)
            ep = re.sub(r"[`\s]", "", ep)
            endpoints.add(ep)

    if not endpoints:
        path_pat = r"/[\w/{}\-:]+(?:\?[^\s]*)?"
        for match in re.finditer(path_pat, api_content):
            endpoints.add(match.group(0))

    return list(endpoints)[:20]


def extract_access_patterns(schema_content: str) -> list[str]:
    """Extract index names, access patterns, and key patterns from schema."""
    patterns_found = []

    idx_patterns = [
        r"(?:INDEX|KEY|idx_|index_)\w+",
        r"(?:BY|WHERE|USING)\s+(\w+)",
        r"(?:partition.key|sort.key|shard.key)[:\s]+[`]?(\w+)",
    ]
    for pat in idx_patterns:
        for match in re.finditer(pat, schema_content, re.IGNORECASE):
            patterns_found.append(match.group(0))

    access_pat = r"(?:access.pattern|query)[:\s]*[`\"']?([^`\"'\n]+)"
    for match in re.finditer(access_pat, schema_content, re.IGNORECASE):
        patterns_found.append(match.group(1).strip())

    return patterns_found[:30]


def check_api_schema_alignment(api_content: str, schema_content: str) -> ConsistencyResult:
    """Check 2: Every API endpoint has a supporting access pattern in schema."""
    endpoints = extract_endpoints(api_content)

    if not endpoints:
        return ConsistencyResult(
            check_name="API-schema alignment",
            passed=False,
            details="No endpoints extracted from API design"
        )

    schema_lower = schema_content.lower()
    matched = []
    unmatched = []

    for ep in endpoints:
        path_parts = re.findall(r"[a-zA-Z]+", ep)
        key_parts = [p for p in path_parts if len(p) > 2 and p.lower() not in ("get", "post", "put", "delete", "patch", "api", "v1", "v2")]

        found = False
        for part in key_parts:
            if part.lower() in schema_lower:
                found = True
                matched.append(f"{ep} → '{part}' in schema")
                break

        if not found and key_parts:
            unmatched.append(ep)

    total = len(endpoints)
    match_pct = len(matched) / total * 100 if total > 0 else 0
    passed = match_pct >= 60

    return ConsistencyResult(
        check_name="API-schema alignment",
        passed=passed,
        details=f"{len(matched)}/{total} endpoints have schema support ({match_pct:.0f}%)",
        matched=matched[:5],
        unmatched=unmatched[:5],
    )


def extract_functional_requirements(requirements_content: str) -> list[str]:
    """Extract functional requirements keywords/phrases."""
    fr_section = ""
    lines = requirements_content.split("\n")
    in_fr = False
    for line in lines:
        if re.search(r"(?i)(functional|key.behav|requirement|feature)", line) and re.match(r"^#{1,3}\s", line):
            in_fr = True
            continue
        if in_fr:
            if re.match(r"^#{1,2}\s", line) and not re.search(r"(?i)functional", line):
                break
            fr_section += line + "\n"

    if not fr_section:
        fr_section = requirements_content

    fr_items = []
    for line in fr_section.split("\n"):
        if re.match(r"\s*[-*|]\s*\*?\*?", line):
            cleaned = re.sub(r"[\s*|-]+", " ", line).strip()
            keywords = [w for w in cleaned.split() if len(w) > 3 and w.lower() not in ("must", "should", "will", "that", "this", "with", "from", "have")]
            if keywords:
                fr_items.append(" ".join(keywords[:4]))

    return fr_items[:15]


def check_requirements_architecture(requirements_content: str, hld_content: str) -> ConsistencyResult:
    """Check 3: Every FR has a traceable component path in HLD."""
    frs = extract_functional_requirements(requirements_content)

    if not frs:
        return ConsistencyResult(
            check_name="Requirements-architecture coverage",
            passed=False,
            details="No functional requirements extracted"
        )

    hld_lower = hld_content.lower()
    matched = []
    unmatched = []

    for fr in frs:
        words = fr.lower().split()
        key_words = [w for w in words if len(w) > 3]
        found = any(w in hld_lower for w in key_words)
        if found:
            matched.append(fr[:50])
        else:
            unmatched.append(fr[:50])

    total = len(frs)
    match_pct = len(matched) / total * 100 if total > 0 else 0
    passed = match_pct >= 70

    return ConsistencyResult(
        check_name="Requirements-architecture coverage",
        passed=passed,
        details=f"{len(matched)}/{total} FRs traceable in HLD ({match_pct:.0f}%)",
        matched=matched[:3],
        unmatched=unmatched[:3],
    )


def check_deep_dive_relevance(deep_dives_content: str, hld_content: str) -> ConsistencyResult:
    """Check 4: Every deep-dived component appears in HLD."""
    dive_headings = re.findall(r"^##\s+(?:Deep Dive \d+[:.]\s*)?(.+)$", deep_dives_content, re.MULTILINE)

    if not dive_headings:
        dive_headings = re.findall(r"^##\s+(.+)$", deep_dives_content, re.MULTILINE)

    if not dive_headings:
        return ConsistencyResult(
            check_name="Deep-dive relevance",
            passed=False,
            details="No dive headings found"
        )

    hld_lower = hld_content.lower()
    matched = []
    unmatched = []

    for heading in dive_headings:
        heading_clean = re.sub(r"[—\-:]+.*$", "", heading).strip()
        words = re.findall(r"[a-zA-Z]+", heading_clean)
        key_words = [w.lower() for w in words if len(w) > 3 and w.lower() not in ("deep", "dive", "system", "design")]

        found = any(w in hld_lower for w in key_words)
        if found:
            matched.append(heading_clean[:40])
        else:
            unmatched.append(heading_clean[:40])

    total = len(dive_headings)
    passed = len(unmatched) == 0 or (len(matched) / total >= 0.8 if total > 0 else False)

    return ConsistencyResult(
        check_name="Deep-dive relevance",
        passed=passed,
        details=f"{len(matched)}/{total} dives trace to HLD components",
        matched=matched[:5],
        unmatched=unmatched[:5],
    )


def check_bottleneck_authenticity(bottlenecks_content: str, hld_content: str) -> ConsistencyResult:
    """Check 5: Each bottleneck traces to a real constraint in the architecture."""
    bn_headings = re.findall(r"^###?\s*\d+\.?\s+(.+)$", bottlenecks_content, re.MULTILINE)

    if not bn_headings:
        bn_headings = re.findall(r"^###\s+(.+)$", bottlenecks_content, re.MULTILINE)

    if not bn_headings:
        return ConsistencyResult(
            check_name="Bottleneck authenticity",
            passed=True,
            details="No numbered bottleneck headings found (skipped)"
        )

    hld_lower = hld_content.lower()
    matched = []
    unmatched = []

    for heading in bn_headings:
        words = re.findall(r"[a-zA-Z]+", heading)
        key_words = [w.lower() for w in words if len(w) > 3 and w.lower() not in ("bottleneck", "issue", "problem", "handling")]

        found = any(w in hld_lower for w in key_words[:5])
        if found:
            matched.append(heading[:40])
        else:
            unmatched.append(heading[:40])

    total = len(bn_headings)
    passed = len(unmatched) <= 1 or (len(matched) / total >= 0.75 if total > 0 else False)

    return ConsistencyResult(
        check_name="Bottleneck authenticity",
        passed=passed,
        details=f"{len(matched)}/{total} bottlenecks trace to HLD components",
        matched=matched[:3],
        unmatched=unmatched[:3],
    )


def run_cross_file_checks(folder: Path) -> ConsistencyReport:
    """Run all 5 cross-file consistency checks."""
    report = ConsistencyReport()

    files = {}
    file_map = {
        "requirements": "01-requirements.md",
        "api": "04-api-design.md",
        "schema": "05-schema.md",
        "hld": "06-high-level-design.md",
        "deep_dives": "07-deep-dives.md",
        "bottlenecks": "08-bottlenecks-and-tradeoffs.md",
    }

    for key, fname in file_map.items():
        filepath = folder / fname
        if filepath.exists():
            files[key] = filepath.read_text(encoding="utf-8")
        else:
            files[key] = ""

    if files["requirements"] and files["hld"]:
        report.results.append(check_numbers_flow(files["requirements"], files["hld"]))
    else:
        report.results.append(ConsistencyResult(
            check_name="Numbers flow", passed=False,
            details="Missing 01-requirements.md or 06-high-level-design.md"
        ))

    if files["api"] and files["schema"]:
        report.results.append(check_api_schema_alignment(files["api"], files["schema"]))
    else:
        report.results.append(ConsistencyResult(
            check_name="API-schema alignment", passed=False,
            details="Missing 04-api-design.md or 05-schema.md"
        ))

    if files["requirements"] and files["hld"]:
        report.results.append(check_requirements_architecture(files["requirements"], files["hld"]))
    else:
        report.results.append(ConsistencyResult(
            check_name="Requirements-architecture coverage", passed=False,
            details="Missing required files"
        ))

    if files["deep_dives"] and files["hld"]:
        report.results.append(check_deep_dive_relevance(files["deep_dives"], files["hld"]))
    else:
        report.results.append(ConsistencyResult(
            check_name="Deep-dive relevance", passed=False,
            details="Missing 07-deep-dives.md or 06-high-level-design.md"
        ))

    if files["bottlenecks"] and files["hld"]:
        report.results.append(check_bottleneck_authenticity(files["bottlenecks"], files["hld"]))
    else:
        report.results.append(ConsistencyResult(
            check_name="Bottleneck authenticity", passed=False,
            details="Missing 08-bottlenecks-and-tradeoffs.md or 06-high-level-design.md"
        ))

    return report
