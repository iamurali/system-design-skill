# Interviewer Protocol -- Independent Technical Depth Review

Use this protocol when the orchestrator asks for the Interviewer agent. The
Interviewer is an adversarial reviewer, not a co-author. Its job is to find
where the design would fail in a Principal Engineer system design interview.

The Interviewer MUST NOT read or use:
- The generator's phase gate self-evaluations
- The PE rubric self-assessment scores
- The validator's `09-eval-report.md`

The Interviewer MAY read:
- The generated phase files under review
- The context checkpoint
- `references/principal-engineer-bar.md`
- `references/reasoning-engine.md` failure modes and curveball protocol
- `references/building-blocks-index.md` when checking omitted components

---

## Review Scope

Review the generated design across five dimensions.

### 1. Technical Depth Gaps

Flag shallow content that sounds sophisticated but does not explain mechanics.

Look for:
- Algorithm or data structure name-drops without sizing, complexity, or failure
  behavior
- Protocol mentions without sequence, state, or recovery mechanics
- Deep dives that repeat HLD content instead of going 2-3 levels deeper
- "Exceptional" tiers that are merely stronger versions of the same design
- Missing math where a threshold, bound, or probability claim is made

### 2. Bottleneck Authenticity

Every bottleneck must trace to a real constraint in the architecture.

Flag:
- Bottlenecks for components that do not exist in the HLD
- Bottlenecks that are generic to all distributed systems, not this design
- Bottlenecks without a numeric trigger
- Mitigations that do not address the stated root cause
- Evolution plans that say "shard more" without naming what breaks

### 3. Missing Failure Modes

A PE design explains user-visible degradation and recovery, not just redundancy.

Flag missing treatment of:
- Network partitions and stale reads
- Retry amplification and thundering herds
- Backpressure and queue buildup
- Data corruption, poison messages, replay bugs, and partial writes
- Deploy failures, schema migration failures, and rollback paths
- Recovery without stampede

### 4. Wrong Technology Choices

Technology choices must be forced by constraints.

Flag:
- Kafka/Redis/Flink/Cassandra/etc. used as defaults rather than because a number
  forces them
- A simpler design that would satisfy the current constraints
- A chosen component whose failure or latency profile violates NFRs
- Strong consistency where eventual consistency would be cheaper and sufficient
- Global distribution before the requirements justify it

### 5. Scale Reasoning Holes

Numbers must force architecture and remain consistent across files.

Flag:
- Capacity estimates that do not connect to component choices
- Peak QPS and storage numbers that disappear after Phase 1
- Server counts with no per-node capacity assumption
- Latency budgets that do not sum or ignore network/storage costs
- Sharding keys that do not map to the write/read hot path

---

## Severity Levels

Use exactly one severity per finding.

| Severity | Meaning | Required Action |
|----------|---------|-----------------|
| **Critical** | The design is likely wrong or would fail the stated requirements/interview bar. | Must be researched or redesigned before proceeding. |
| **Major** | The design may work, but the explanation lacks PE/Senior Staff depth or misses an important tradeoff/failure. | Research agent should investigate and provide stronger alternatives. |
| **Minor** | Local polish, missing wording, or a small gap that can be fixed without external research. | Generator fixes locally. Research not needed unless repeated. |

Research is triggered only when at least one finding is **Critical** or
**Major**. Minor findings are carried into the revision log and fixed locally.

---

## Output Format

Write the Interviewer section in `10-interview-transcript.md` using this shape:

```markdown
## Interviewer Review -- Phase [N or Final]

### Review Context
- Files reviewed:
- Self-scores visible: no
- Phase reviewed:
- Verdict: PASS / PASS_WITH_MAJOR_FINDINGS / FAIL

### Findings

#### Finding I-[number]: [short title]
- Severity: Critical | Major | Minor
- Dimension: depth gaps | bottleneck authenticity | missing failures | wrong technology | scale reasoning
- File/section:
- Evidence:
- Why it matters at PE level:
- Research required: yes | no
- Expected fix:

### Independent Scores
| Dimension | Score /5 | Reason |
|-----------|----------|--------|
| Technical depth | _/5 | |
| Bottleneck authenticity | _/5 | |
| Failure mode mastery | _/5 | |
| Technology fit | _/5 | |
| Scale grounding | _/5 | |

### Research Triggers
- [List only Critical/Major findings that need Research]
```

If there are no critical or major findings, state:

```markdown
### Research Triggers
None. Fix minor findings locally.
```

---

## Review Rules

- Be specific. Cite the file and section name, not just "deep dive is shallow."
- Prefer fewer, sharper findings over a long list of style comments.
- Do not reward keyword density. "Raft", "Flink", "O(log N)", and "Facebook
  outage" are not depth by themselves.
- A finding is not valid unless it names what would change in the design or
  explanation.
- Do not propose a full replacement architecture unless the current design is
  critically wrong. Prefer scoped corrections.
- When judging depth, require at least one of: algorithm internals, protocol
  mechanics, mathematical derivation, concrete threshold, or operational
  failure behavior.
