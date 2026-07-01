# Bottlenecks & Synthesis Skill — Stress-Test the Design

This is the **complete Phase 6 skill**. Synthesize Phases 1–5 into production
realism: bottlenecks, failures, tradeoffs, evolution, and interview-ready
insights.

```
Real bottlenecks from numbers → failure matrix → incidents → anti-patterns →
tradeoff matrix → evolution → coverage sweep → PE self-score
```

Read this file at the start of Phase 6. Pair with
`assets/templates/08-bottlenecks-and-tradeoffs.template.md`,
`references/principal-engineer-bar.md`, and `references/building-blocks-index.md`.

Load `references/reasoning-engine.md` lines 152–244 for failure modes and
coverage sweep vocabulary.

---

## Phase 6 entry checklist

1. Re-read **context checkpoint** — scale, shard key, archetype, known gate issues.
2. List **6+ bottlenecks** with root cause, mitigations, real-world analogy.
3. Build **failure matrix** (5+ rows, distinct failure classes).
4. Cite **3+ real incidents** (company, ~year, lesson) — not fabricated.
5. Document **3+ anti-patterns** for this problem class.
6. **Tradeoff matrix** — every major Phase 4–5 decision.
7. **Evolution roadmap** at 10× and 100× from Phase 1 tiers.
8. **Coverage sweep** — L0–L7 building blocks used vs deferred.
9. **5–7 talking points** + **PE rubric self-assessment**.

---

## Section 1: Bottleneck analysis (6+)

Each bottleneck must trace to **checkpoint numbers**, not generic "database slow."

### Bottleneck template

#### Bottleneck N: [Name]

**Root cause:** [mechanism + number — e.g., single primary at 80K write QPS]

**Mitigations:** (2–3 concrete, not "add cache" alone)

**Real-world analogy:** [Company, ~year, what happened]

### Shape → typical bottleneck families

| Shape | Likely bottlenecks (verify against YOUR numbers) |
|-------|--------------------------------------------------|
| A1 | DB connections, hot row, cache miss storm, ID exhaustion |
| A2 | Celebrity fanout, inbox size, merge latency |
| A3 | Memory cap, hot key, replication lag, hash rebalance |
| A5/A6 | Connection memory, push fanout, ordering backlog |
| A7 | Sketch memory, segment explosion, ingest lag, Redis hot ZSET |
| A8 | Origin bandwidth, storage cost, transcode queue |
| A9 | Lock contention, serializable conflicts, audit growth |

**PE signal:** Prioritize bottlenecks that **actually bind** at 1× and 10× from
Phase 1 — not theoretical Kafka issues on a sync CRUD system.

---

## Section 2: Failure matrix (mandatory)

| Failure | Blast Radius | Detection | Degradation | Recovery | RTO |
|---------|--------------|-----------|-------------|----------|-----|
| Node crash | | | | | |
| Network partition | | | | | |
| Cascading failure | | | | | |
| Data corruption | | | | | |
| Deploy failure | | | | | |

Minimum **5 rows**, **distinct classes**. Tie degradation to Phase 2 consistency
policy (stale vs error).

---

## Section 3: Real-world incidents (3+)

Named production events with lesson learned:

1. **[Company] (~year):** root cause — lesson for **this** design
2. ...

Sources: public postmortems, engineering blogs (Facebook, Google, Amazon,
Netflix, LinkedIn, Cloudflare, etc.). Relate to **your** components — not
generic trivia.

---

## Section 4: Anti-patterns (3+)

Problem-class mistakes — especially **shape-appropriate** wrong answers:

| Anti-pattern | Why it seems right | Why it fails | Correct approach |
|--------------|-------------------|--------------|------------------|
| Default streaming stack on CRUD | "Scale" | Ops cost, latency | Sync store until W QPS forces buffer |
| Exact global counter | Simple | Hot key | Approximate / local aggregate |
| Cache everything | Fast reads | Invalidation nightmare | Cache working set only |

---

## Section 5: Tradeoff summary matrix

| Decision | Chosen | Alternative | Why (number or NFR) |
|----------|--------|-------------|---------------------|
| | | | |

Cover **every major** Phase 4–5 choice — store class, fanout strategy, cache
policy, consistency level, shard key.

Use `references/tradeoff-framework.md` triad vocabulary where helpful.

---

## Section 6: Evolution roadmap

Extend Phase 1 growth trajectory with **architectural** changes:

| Scale | Breaking point (specific) | Architectural change | Migration |
|-------|---------------------------|----------------------|-----------|
| 10× | At ___ QPS, ___ breaks because … | | |
| 100× | | | |

Not "shard more" — name the mechanism (ZADD O(log N), connection pool size,
fanout write amp).

---

## Section 7: Coverage sweep

Scan `references/building-blocks-index.md` L0–L7:

| Building block | Used / Deferred | Reason if deferred |
|----------------|-----------------|-------------------|
| DNS / CDN | | |
| Load balancing | | |
| API gateway | | |
| Cache | | |
| Primary store | | |
| Async buffer | | |
| Search | | |
| ... | | |

**Deferred is valid** — document why (YAGNI at 1×). Silent skip fails PE bar.

---

## Section 8: Interview talking points (5–7)

PE-level insights that **teach** something non-obvious about this design:

1. ...
2. ...

Draw from reframing, contested research, dive math, incident lessons.

---

## Section 9: PE rubric self-assessment

Score all 10 dimensions from `references/principal-engineer-bar.md`. Name
weakest dimension and what would raise it. Honest scores — Interviewer may
disagree.

---

## Phase 6 quality signals

- Bottlenecks are **mechanistic** and numbered.
- Failure matrix matches HLD failure flows (no contradictions).
- Evolution matches Phase 1 10×/100× tiers.
- Tradeoffs cover skipped alternatives from Phase 4 research tables.
- Coverage sweep explicit about deferred blocks.

---

## Exemplar selection (optional)

| Shape | `08-bottlenecks-and-tradeoffs.md` |
|-------|----------------------------------|
| A3 | `assets/exemplars/in-memory-cache/` |
| A7 | `assets/exemplars/trending-articles-top-k/` |
| A1 / other | **Skill + template** |

---

## Final handoff

After Gate 6: run Interviewer Checkpoint C, cross-file consistency protocol,
outer eval loop, validator harness (`09-eval-report.md`).
