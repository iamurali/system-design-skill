"""Semantic-ish technical depth checks for system design outputs.

The validator remains stdlib-only, so these checks are heuristic. They are
stricter than keyword counting: an algorithm mention is not depth unless the
nearby text includes mechanics, thresholds, derivations, or failure behavior.
"""

from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class DepthCheck:
    name: str
    count: int
    target: int
    passed: bool
    evidence: str
    examples: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"


@dataclass
class DepthReport:
    checks: list[DepthCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def score(self) -> float:
        if not self.checks:
            return 0.0
        return sum(1 for c in self.checks if c.passed) / len(self.checks) * 100


ALGORITHM_TERMS = {
    "Count-Min Sketch": r"(?i)count[- ]min sketch|CMS\b",
    "HyperLogLog": r"(?i)hyperloglog|HLL\b",
    "Consistent hashing": r"(?i)consistent hash",
    "Bloom filter": r"(?i)bloom filter",
    "LSM tree": r"(?i)\bLSM\b|log.structured merge",
    "B-tree": r"(?i)B[- ]?tree",
    "Trie": r"(?i)\btrie\b",
    "Heap/top-K": r"(?i)\bheap\b|top[- ]?K|priority queue",
    "CRDT": r"(?i)\bCRDT\b",
    "Merkle tree": r"(?i)merkle",
}

PROTOCOL_TERMS = {
    "Raft/Paxos": r"(?i)\bRaft\b|\bPaxos\b|leader election|quorum",
    "Two-phase commit": r"(?i)2PC|two.phase commit|3PC",
    "Kafka protocol": r"(?i)consumer group|rebalance|partition assignment|ISR|ack.*all",
    "Checkpointing": r"(?i)checkpoint|snapshot|barrier|Chandy.Lamport",
    "Backpressure": r"(?i)backpressure|flow control|credit.based",
    "Leases/fencing": r"(?i)lease|fencing token|epoch|heartbeat",
    "WAL/replication": r"(?i)write.ahead log|WAL|binlog|replication factor",
}

MECHANIC_PATTERNS = [
    r"(?i)step\s*\d+",
    r"(?i)sequence|state machine|transition|leader|follower|coordinator",
    r"(?i)partition|replica|quorum|epoch|offset|commit|checkpoint",
    r"(?i)collision|compaction|rebalance|recovery|overcount|under-count",
]

MATH_PATTERNS = [
    r"O\([^)]+\)",
    r"(?i)epsilon|delta|probability|variance|bound|ceil|log\(|ln\(",
    r"(?i)width|depth|false positive|error rate",
    r"\b\d+(?:\.\d+)?\s*(?:KB|MB|GB|TB|PB|ms|s|sec|min|QPS|TPS|req/s|ops/s|%)",
    r"=\s*[^.\n]{1,80}\d",
]

FAILURE_PATTERNS = [
    r"(?i)fail|failure|outage|partition|corruption|poison|stampede",
    r"(?i)recovery|fallback|degradation|retry|backoff|circuit breaker",
    r"(?i)RTO|RPO|MTTR|blast radius|stale",
]

COMPANIES = (
    "Facebook|Meta|Google|Twitter|X|LinkedIn|Netflix|Amazon|Uber|Airbnb|"
    "Stripe|Cloudflare|GitHub|Spotify|Pinterest|Dropbox|Slack|Microsoft"
)


def _read(folder: Path, filename: str) -> str:
    path = folder / filename
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _sentences(content: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n\s*\n", content)
    return [c.strip() for c in chunks if c.strip()]


def _window(content: str, start: int, end: int, radius: int = 450) -> str:
    left = max(0, start - radius)
    right = min(len(content), end + radius)
    return content[left:right].strip()


def _first_line(text: str) -> str:
    return " ".join(text.split())[:140]


def _score_depth_window(text: str) -> int:
    """Return L0-L3 for a local algorithm/protocol explanation."""
    has_math = any(re.search(p, text) for p in MATH_PATTERNS)
    has_mechanics = any(re.search(p, text) for p in MECHANIC_PATTERNS)
    has_failure = any(re.search(p, text) for p in FAILURE_PATTERNS)
    has_tradeoff = bool(re.search(r"(?i)solves|worsens|trade.?off|change.*when|would switch", text))

    if has_math and (has_mechanics or has_failure or has_tradeoff):
        return 3
    if has_mechanics or has_failure:
        return 2
    if has_tradeoff or re.search(r"(?i)used for|serves|handles|chosen because|applies", text):
        return 1
    return 0


def classify_algorithm_depth(content: str) -> list[tuple[str, int, str]]:
    """Classify algorithm and protocol mentions as L0-L3."""
    results: list[tuple[str, int, str]] = []
    all_terms = {**ALGORITHM_TERMS, **PROTOCOL_TERMS}

    for name, pattern in all_terms.items():
        for match in re.finditer(pattern, content):
            local = _window(content, match.start(), match.end())
            level = _score_depth_window(local)
            results.append((name, level, _first_line(local)))

    deduped: dict[str, tuple[int, str]] = {}
    for name, level, example in results:
        if name not in deduped or level > deduped[name][0]:
            deduped[name] = (level, example)

    return [(name, level, example) for name, (level, example) in deduped.items()]


def score_derivation_completeness(content: str) -> DepthCheck:
    classified = classify_algorithm_depth(content)
    l3 = [(name, ex) for name, level, ex in classified if level >= 3]
    l2_or_better = [(name, ex) for name, level, ex in classified if level >= 2]
    target = 2
    passed = len(l3) >= target or (len(l3) >= 1 and len(l2_or_better) >= 3)
    examples = [f"{name}: {ex}" for name, ex in l3[:3]]
    return DepthCheck(
        name="Derivation completeness",
        count=len(l3),
        target=target,
        passed=passed,
        evidence=f"L3 derivations={len(l3)}, L2+ mechanics={len(l2_or_better)}",
        examples=examples or [f"{name}: L{level}" for name, level, _ in classified[:5]],
    )


def score_algorithm_depth(content: str) -> DepthCheck:
    classified = classify_algorithm_depth(content)
    weighted = sum(level for _, level, _ in classified)
    target = 8
    passed = weighted >= target and any(level >= 3 for _, level, _ in classified)
    examples = [f"{name}=L{level}: {ex}" for name, level, ex in classified[:5]]
    return DepthCheck(
        name="Algorithm/protocol depth L0-L3",
        count=weighted,
        target=target,
        passed=passed,
        evidence=f"{len(classified)} distinct mentions, weighted depth={weighted}",
        examples=examples,
    )


def score_tradeoff_specificity(content: str) -> DepthCheck:
    triadish = []
    for sentence in _sentences(content):
        has_solve = re.search(r"(?i)solves|benefit|advantage|gain", sentence)
        has_worse = re.search(r"(?i)worsens|cost|downside|drawback|risk", sentence)
        has_change = re.search(r"(?i)change.*when|when.*change|switch|revisit|invalidat", sentence)
        has_specific = re.search(r"\d|QPS|latency|P99|storage|availability|freshness|consistency|oncall|blast", sentence, re.IGNORECASE)
        if (has_solve or has_worse or has_change) and has_specific:
            triadish.append(_first_line(sentence))

    target = 4
    return DepthCheck(
        name="Tradeoff specificity",
        count=len(triadish),
        target=target,
        passed=len(triadish) >= target,
        evidence="Tradeoffs must cite system constraints, not generic pros/cons",
        examples=triadish[:5],
    )


def score_breaking_point_precision(content: str) -> DepthCheck:
    patterns = [
        r"(?i)(?:breaks?|fails?|saturates?|exceeds?|bottleneck|limit).*?\b\d+(?:\.\d+)?\s*(?:K|M|B)?\s*(?:QPS|TPS|req/s|ops/s|GB|TB|PB|ms|s|sec|min|%)",
        r"(?i)at\s+\d+(?:\.\d+)?\s*(?:K|M|B)?\s*(?:QPS|TPS|req/s|ops/s|GB|TB|PB|ms|s|sec|min|%)",
        r"(?i)\b10x\b|\b100x\b|\b1000x\b",
    ]
    matches: list[str] = []
    for pattern in patterns:
        matches.extend(_first_line(m.group(0)) for m in re.finditer(pattern, content))

    target = 5
    return DepthCheck(
        name="Breaking point precision",
        count=len(matches),
        target=target,
        passed=len(matches) >= target,
        evidence="Breaking points should include numeric thresholds or scale tiers",
        examples=matches[:5],
    )


def score_incident_verifiability(content: str) -> DepthCheck:
    incident_pat = (
        rf"(?i)(?:{COMPANIES}).{{0,120}}(?:19|20)\d{{2}}.{{0,120}}"
        r"(?:incident|outage|post.?mortem|failure|cascade|partition|degradation)"
    )
    reverse_pat = (
        rf"(?i)(?:19|20)\d{{2}}.{{0,120}}(?:{COMPANIES}).{{0,120}}"
        r"(?:incident|outage|post.?mortem|failure|cascade|partition|degradation)"
    )
    matches = [_first_line(m.group(0)) for m in re.finditer(incident_pat, content)]
    matches.extend(_first_line(m.group(0)) for m in re.finditer(reverse_pat, content))

    target = 3
    return DepthCheck(
        name="Incident verifiability",
        count=len(matches),
        target=target,
        passed=len(matches) >= target,
        evidence="Production incidents need company plus approximate year and lesson",
        examples=matches[:5],
    )


def score_research_quality(transcript: str) -> DepthCheck:
    if not transcript.strip():
        return DepthCheck(
            name="Research quality",
            count=0,
            target=1,
            passed=False,
            evidence="10-interview-transcript.md missing",
            examples=[],
        )

    major_or_critical = len(re.findall(r"(?i)Severity:\s*(Critical|Major)", transcript))
    has_research = bool(re.search(r"(?i)^##\s+Research Findings", transcript, re.MULTILINE))
    source_count = len(re.findall(r"(?i)https?://|\[.+?\]\(.+?\)|Source:", transcript))
    applies_count = len(re.findall(r"(?i)why it applies|where it does not apply|does not apply", transcript))
    revision_count = len(re.findall(r"(?i)Revision Guidance|File/section to change|New tradeoff|New failure", transcript))

    if major_or_critical == 0:
        passed = bool(re.search(r"(?i)Research Triggers\s*\n\s*None|None\. Fix minor", transcript))
        evidence = "No major/critical findings; research should be explicitly skipped"
        count = 1 if passed else 0
    else:
        count = int(has_research) + min(source_count, 3) + min(applies_count, 2) + min(revision_count, 2)
        passed = has_research and source_count >= 1 and applies_count >= 1 and revision_count >= 1
        evidence = f"major/critical findings={major_or_critical}, sources={source_count}, applicability={applies_count}, revisions={revision_count}"

    return DepthCheck(
        name="Conditional research quality",
        count=count,
        target=1,
        passed=passed,
        evidence=evidence,
        examples=[],
    )


def score_interviewer_independence(transcript: str) -> DepthCheck:
    signals = [
        r"(?i)^##\s+Interviewer Review",
        r"(?i)Self-scores visible:\s*no",
        r"(?i)^###\s+Findings",
        r"(?i)^###\s+Independent Scores",
        r"(?i)Research Triggers",
    ]
    count = sum(1 for p in signals if re.search(p, transcript, re.MULTILINE))
    target = len(signals)
    return DepthCheck(
        name="Interviewer independence transcript",
        count=count,
        target=target,
        passed=count >= target,
        evidence="Transcript must show blind review, findings, independent scores, and research triggers",
        examples=[],
    )


def score_bottleneck_depth(content: str) -> DepthCheck:
    sections = re.split(r"(?im)^###?\s+(?:Bottleneck\s*)?\d+[.:]?\s+", content)
    strong = []
    for section in sections[1:]:
        has_root = re.search(r"(?i)root cause|cause|because|why", section)
        has_number = re.search(r"\b\d+(?:\.\d+)?\s*(?:K|M|B)?\s*(?:QPS|TPS|req/s|ops/s|GB|TB|PB|ms|s|sec|min|%)", section)
        has_mitigation = re.search(r"(?i)mitigation|remedy|fix|approach|solution", section)
        has_arch_trace = re.search(r"(?i)component|path|architecture|HLD|read path|write path|capacity", section)
        if has_root and has_number and has_mitigation and has_arch_trace:
            strong.append(_first_line(section))

    target = 4
    return DepthCheck(
        name="Bottleneck depth",
        count=len(strong),
        target=target,
        passed=len(strong) >= target,
        evidence="Bottlenecks need root cause, numeric trigger, mitigation, and architecture trace",
        examples=strong[:5],
    )


def run_depth_eval(folder: Path) -> DepthReport:
    dd_content = _read(folder, "07-deep-dives.md")
    bn_content = _read(folder, "08-bottlenecks-and-tradeoffs.md")
    hld_content = _read(folder, "06-high-level-design.md")
    transcript = _read(folder, "10-interview-transcript.md")

    combined_depth = "\n".join([dd_content, bn_content])
    combined_design = "\n".join([hld_content, dd_content, bn_content])

    report = DepthReport()
    report.checks.append(score_algorithm_depth(dd_content))
    report.checks.append(score_derivation_completeness(dd_content))
    report.checks.append(score_tradeoff_specificity(combined_design))
    report.checks.append(score_breaking_point_precision(combined_depth))
    report.checks.append(score_incident_verifiability(bn_content))
    report.checks.append(score_bottleneck_depth(bn_content))
    report.checks.append(score_interviewer_independence(transcript))
    report.checks.append(score_research_quality(transcript))
    return report
