"""Quality signal scoring: algorithm depth, production references, failure scenarios, tradeoff triads, coverage sweep."""

import re
from pathlib import Path
from dataclasses import dataclass, field

from .depth_eval import (
    ALGORITHM_TERMS,
    PROTOCOL_TERMS,
    classify_algorithm_depth,
    score_research_quality,
)


@dataclass
class QualitySignal:
    name: str
    count: int
    target: int
    passed: bool
    examples: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"


@dataclass
class QualityReport:
    signals: list[QualitySignal] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(s.passed for s in self.signals)

    @property
    def score(self) -> float:
        if not self.signals:
            return 0.0
        return sum(1 for s in self.signals if s.passed) / len(self.signals) * 100


ALGORITHM_PATTERNS = [
    r"O\([^)]+\)",
    r"(?i)(time.complexity|space.complexity|amortized|worst.case)",
    r"(?i)(hash.*(table|map|function)|B-tree|LSM|skip.list|bloom.filter|trie)",
    r"(?i)(count.min.sketch|hyperloglog|consistent.hash|merkle)",
    r"(?i)(heap|priority.queue|sorted.set|ring.buffer|circular.buffer)",
    r"(?i)(binary.search|two.pointer|sliding.window|dynamic.programming)",
    r"(?i)(CAS|compare.and.swap|lock.free|wait.free)",
    r"(?i)(epsilon|delta|probability|expectation|variance|bound)",
    r"(?i)(convergence|lineariz|serializab|causal)",
    r"=\s*\d+\s*[×*]\s*\d+",
]

PROTOCOL_PATTERNS = [
    r"(?i)(Paxos|Raft|ZAB|gossip.protocol|CRDT)",
    r"(?i)(2PC|two.phase.commit|3PC|saga)",
    r"(?i)(leader.election|quorum|consensus|vector.clock)",
    r"(?i)(heartbeat|lease|fencing.token|epoch)",
    r"(?i)(TCP|gRPC|HTTP/2|WebSocket|SSE).*(handshake|connection|stream)",
    r"(?i)(ISR|in.sync.replica|replication.factor|ack.*all)",
    r"(?i)(WAL|write.ahead.log|redo.log|binlog)",
    r"(?i)(snapshot|checkpoint|Chandy.Lamport|barrier)",
    r"(?i)(backpressure|flow.control|credit.based|token.bucket)",
    r"(?i)(partition.assignment|rebalance|consumer.group)",
]

PRODUCTION_PATTERNS = [
    r"(?i)(Facebook|Meta|Google|Twitter|LinkedIn|Netflix|Amazon|Uber|Airbnb|Stripe|Cloudflare|GitHub|Spotify|Pinterest|Dropbox)",
    r"(?i)(production|real.world|at.scale|in.practice|we.ran|we.observed|incident)",
    r"(?i)(paper|publication|blog.post|engineering.blog|whitepaper)",
    r"(?i)(\d{4}).*(outage|incident|post.?mortem|failure|cascade)",
    r"(?i)(TAO|Spanner|Bigtable|Dynamo|Cassandra|Kafka|Flink|Samza|Spark)",
    r"(?i)(Redis|Memcached|RocksDB|LevelDB|ZooKeeper|etcd|Consul)",
]

FAILURE_PATTERNS = [
    r"(?i)(cause|root.cause)[:\s]",
    r"(?i)(mitigat|solution|remedy|fix)[:\s]",
    r"(?i)(failure.mode|failure.scenario|what.happens.when|if.*fails)",
    r"(?i)(cascading|cascade|domino|amplif|thundering.herd|stampede)",
    r"(?i)(split.brain|network.partition|byzantine|clock.skew)",
    r"(?i)(circuit.breaker|bulkhead|retry.budget|backoff|jitter)",
    r"(?i)(graceful.degradation|stale.while|serve.stale|fallback)",
    r"(?i)(blast.radius|isolation|containment|quarantine)",
    r"(?i)(RTO|RPO|recovery.time|recovery.point|MTTR|MTTF)",
    r"(?i)(hot.standby|warm.standby|cold.standby|failover)",
]

TRADEOFF_PATTERNS = [
    r"(?i)(solves|what.*solve|benefit|advantage|gain)",
    r"(?i)(worsens|what.*worse|cost|downside|drawback|disadvantage)",
    r"(?i)(change.*when|when.*change|invalidat|would.*switch|revisit.if)",
]

COVERAGE_BLOCKS = [
    ("DNS", r"(?i)\bdns\b"),
    ("Load Balancing", r"(?i)load.balanc"),
    ("CDN", r"(?i)(CDN|content.delivery)"),
    ("API Design", r"(?i)api.design"),
    ("Service Decomposition", r"(?i)service.decompos"),
    ("Data Storage", r"(?i)data.stor"),
    ("Caching", r"(?i)\bcach"),
    ("Blob Store", r"(?i)blob.stor"),
    ("Sequencer", r"(?i)(sequencer|unique.id|snowflake|UUID)"),
    ("Sharded Counters", r"(?i)sharded.counter"),
    ("Distributed Search", r"(?i)(distributed.search|elasticsearch|full.text)"),
    ("Messaging/Streaming", r"(?i)(messag|stream|queue|kafka|rabbit|SQS)"),
    ("Task Scheduling", r"(?i)task.schedul"),
    ("Consistency/Coordination", r"(?i)(consisten|coordinat|consensus)"),
    ("Resilience/Failure", r"(?i)(resilien|failure.mode|circuit.breaker)"),
    ("Observability", r"(?i)(observab|monitor|metric|trace|alert)"),
    ("Distributed Logging", r"(?i)(distributed.log|log.aggregat|ELK|fluentd)"),
    ("Scaling/Evolution", r"(?i)(scal|evolution|10x|100x)"),
]


def count_algorithm_signals(content: str) -> QualitySignal:
    classified = [
        (name, level, example)
        for name, level, example in classify_algorithm_depth(content)
        if name in ALGORITHM_TERMS
    ]
    total = sum(level for _, level, _ in classified)
    target = 6
    has_derivation = any(level >= 3 for _, level, _ in classified)
    return QualitySignal(
        name="Algorithm depth L0-L3",
        count=total,
        target=target,
        passed=total >= target and has_derivation,
        examples=[f"{name}=L{level}: {example}" for name, level, example in classified[:5]],
    )


def count_protocol_signals(content: str) -> QualitySignal:
    classified = [
        (name, level, example)
        for name, level, example in classify_algorithm_depth(content)
        if name in PROTOCOL_TERMS
    ]
    total = sum(level for _, level, _ in classified)
    target = 5
    has_mechanics = any(level >= 2 for _, level, _ in classified)
    return QualitySignal(
        name="Protocol mechanics L0-L3",
        count=total,
        target=target,
        passed=total >= target and has_mechanics,
        examples=[f"{name}=L{level}: {example}" for name, level, example in classified[:5]],
    )


def count_production_signals(content: str) -> QualitySignal:
    total = 0
    examples = []
    for pattern in PRODUCTION_PATTERNS:
        matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
        for m in matches[:2]:
            example = m if isinstance(m, str) else str(m)
            if example and example not in examples:
                examples.append(example[:50])
        total += len(matches)

    target = 5
    return QualitySignal(
        name="Production references",
        count=total,
        target=target,
        passed=total >= target,
        examples=examples[:5],
    )


def count_failure_signals(content: str) -> QualitySignal:
    total = 0
    examples = []
    for pattern in FAILURE_PATTERNS:
        matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
        for m in matches[:2]:
            example = m if isinstance(m, str) else str(m)
            if example and example not in examples:
                examples.append(example[:50])
        total += len(matches)

    target = 6
    return QualitySignal(
        name="Failure scenarios with mitigation",
        count=total,
        target=target,
        passed=total >= target,
        examples=examples[:5],
    )


def count_tradeoff_signals(content: str) -> QualitySignal:
    solves = len(re.findall(TRADEOFF_PATTERNS[0], content, re.MULTILINE | re.IGNORECASE))
    worsens = len(re.findall(TRADEOFF_PATTERNS[1], content, re.MULTILINE | re.IGNORECASE))
    change_when = len(re.findall(TRADEOFF_PATTERNS[2], content, re.MULTILINE | re.IGNORECASE))

    triads = min(solves, worsens, change_when)
    target = 4

    return QualitySignal(
        name="Tradeoff triads (solves/worsens/change)",
        count=triads,
        target=target,
        passed=triads >= target,
        examples=[f"solves={solves}, worsens={worsens}, change_when={change_when}"],
    )


def count_coverage_blocks(content: str) -> QualitySignal:
    addressed = []
    for name, pattern in COVERAGE_BLOCKS:
        if re.search(pattern, content, re.IGNORECASE):
            addressed.append(name)

    target = 12
    return QualitySignal(
        name="Building blocks coverage",
        count=len(addressed),
        target=target,
        passed=len(addressed) >= target,
        examples=addressed[:8],
    )


def count_code_blocks(content: str) -> QualitySignal:
    """Count substantive code/pseudocode blocks (>2 lines)."""
    blocks = re.findall(r"```[\s\S]*?```", content)
    substantial = [b for b in blocks if b.count("\n") > 2]

    target = 4
    return QualitySignal(
        name="Code/pseudocode blocks",
        count=len(substantial),
        target=target,
        passed=len(substantial) >= target,
        examples=[f"{len(substantial)} blocks with >2 lines"],
    )


def count_tables(content: str) -> QualitySignal:
    """Count markdown tables."""
    table_rows = re.findall(r"^\|[^|]+\|[^|]+\|", content, re.MULTILINE)
    header_separators = re.findall(r"^\|[-:| ]+\|", content, re.MULTILINE)
    tables = len(header_separators)

    target = 3
    return QualitySignal(
        name="Comparison tables",
        count=tables,
        target=target,
        passed=tables >= target,
        examples=[f"{tables} tables, {len(table_rows)} total rows"],
    )


def count_research_quality(transcript: str) -> QualitySignal:
    depth_check = score_research_quality(transcript)
    return QualitySignal(
        name=depth_check.name,
        count=depth_check.count,
        target=depth_check.target,
        passed=depth_check.passed,
        examples=depth_check.examples or [depth_check.evidence],
    )


def run_quality_scoring(folder: Path) -> QualityReport:
    """Run quality signal scoring across deep dives + bottlenecks files."""
    report = QualityReport()

    dd_path = folder / "07-deep-dives.md"
    bn_path = folder / "08-bottlenecks-and-tradeoffs.md"
    hld_path = folder / "06-high-level-design.md"
    transcript_path = folder / "10-interview-transcript.md"

    dd_content = dd_path.read_text(encoding="utf-8") if dd_path.exists() else ""
    bn_content = bn_path.read_text(encoding="utf-8") if bn_path.exists() else ""
    hld_content = hld_path.read_text(encoding="utf-8") if hld_path.exists() else ""
    transcript_content = transcript_path.read_text(encoding="utf-8") if transcript_path.exists() else ""

    combined_deep = dd_content + "\n" + bn_content
    combined_all = dd_content + "\n" + bn_content + "\n" + hld_content

    report.signals.append(count_algorithm_signals(dd_content))
    report.signals.append(count_protocol_signals(dd_content))
    report.signals.append(count_production_signals(combined_deep))
    report.signals.append(count_failure_signals(bn_content))
    report.signals.append(count_tradeoff_signals(hld_content))
    report.signals.append(count_coverage_blocks(combined_all))
    report.signals.append(count_code_blocks(dd_content))
    report.signals.append(count_tables(combined_all))
    report.signals.append(count_research_quality(transcript_content))

    return report
