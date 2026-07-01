# FAANG & Top-Tier System Design Interview Patterns

Synthesized from public interview guides, engineering blogs, and company
hiring loops (Google L5+, Amazon SDE II–Principal, Meta Staff+, LinkedIn,
Databricks, Microsoft). Use at **Phase 1** (framing), **Phase 2** (scale/NFRs),
and **Phase 4** (architecture).

> Google rewards first-principles depth over rehearsed buzzwords. Amazon rewards
> operational excellence and explicit assumptions. Both reward **numbers before
> boxes** and **tradeoffs before technology**.

---

## Universal 45–90 Minute Flow

| Segment | Time | What top candidates do |
|---------|------|------------------------|
| Clarify & reframe | 5–8 min | Turn one-line prompt into users, goals, success metrics, hidden requirements |
| Scale & constraints | 5–8 min | Full estimation chain; peak not average; read/write split; growth tiers |
| Interface | 5–8 min | Entities, API contracts, schema driven by access patterns |
| High-level design | 12–20 min | **Start cheap**; add components only when a number breaks; 2–3 options for contested decisions |
| Deep dive | 10–15 min | 2–4 components, 2–3 levels below the diagram; math or protocol mechanics |
| Stress & wrap | 5–10 min | Bottlenecks, failure matrix, 10× evolution, what you'd change with more time |

**Google-specific:** Interviewers push past managed-service name-drops ("why not just use X?") — explain internals or build-from-first-principles for one component.

**Amazon-specific:** State assumptions aloud; discuss blast radius, on-call, rollback; tie to Leadership Principles (Dive Deep, Ownership, Operational Excellence).

**Principal/Staff delta:** Not a bigger diagram — multi-year evolution, org boundaries, build-vs-buy, and defending a past architectural bet with failure stories.

---

## Requirements Phase (Phase 1) — Non-Negotiables

### Reframing (before listing features)

Ask questions that change the architecture:

- Exact vs approximate? (leaderboard vs trending feed)
- Real-time vs batch? (sub-second vs 15-minute staleness)
- Global vs single-region? (multi-master vs single writer)
- Who is the customer of this API? (end user vs internal service)

Document at least one reframing that **narrows scope with judgment**.

### Scale assumptions (inputs — not derived QPS)

Record inputs for Phase 2 math:

- DAU / MAU, actions per user per day (read vs write separate)
- Object / payload size, retention period, peak factor (2–10×)

### Out-of-scope

Minimum 3 exclusions, each with **one-line why** (not "we won't do ML" but "personalized ranking requires per-user feature store — out of scope; we serve global top-K only").

### Success metrics (SLIs)

Define 2–3 measurable signals before architecture:

- Business: CTR, time-on-feed, conversion
- Technical: P99 latency, freshness lag, error rate, cache hit ratio

---

## NFR Phase (Phase 2) — SRE-Grade Constraints

### Capacity estimation chain

Every design must show this chain in `02-non-functional-requirements.md`,
derived from Phase 1 assumptions:

```
DAU (or MAU)
  → actions/user/day
  → average read QPS, average write QPS (separate!)
  → peak QPS (state peak factor, typically 2–10×)
  → storage/day (writes × object size)
  → total storage (× retention)
  → bandwidth (QPS × payload, read and write separate)
  → server/instance count (peak QPS ÷ per-node capacity from numbers-to-know.md)
```

Also state **1×, 10×, 100×** scale inputs — evolution is not a Phase 6 surprise.

Capacity is a **non-functional** requirement (throughput, storage, scalability).
Interviews run this math in minutes 5–15, right after clarifying scope.

### Latency budget (must sum to P99)

Break end-to-end P99 into hops. Example:

| Hop | Budget |
|-----|--------|
| Client → LB | 5 ms |
| LB → API | 2 ms |
| API → cache | 1 ms |
| Cache lookup | 0.5 ms |
| Serialization | 1 ms |
| **Total P99** | **~10 ms** |

### Error budget math

Convert availability to concrete downtime:

- 99.9% → ~43 min/month
- 99.95% → ~22 min/month
- 99.99% → ~4.3 min/month

State what consumes the budget (deploys, dependency failures, hot spots).

### Consistency — user-facing consequence

Not "eventual consistency" alone. Example: *"User may see trending list up to 60s stale after a viral spike; rank order within top-10 remains stable."*

### Durability by data class

| Data class | RPO | RTO | Mechanism |
|------------|-----|-----|-----------|
| Engagement events | 0 (no loss) | minutes | Durable log + replay |
| Top-K snapshots | 5 min | 30 sec | Materialized store rebuild from stream |

### Runbook sketch

One top failure scenario with detect → mitigate → recover steps (not "add monitoring").

---

## HLD Phase — Use the HLD Skill

Read **`hld-skill.md`** and **`hld-archetypes.md`** at Phase 4. Classify the
problem shape (CRUD, cache, feed, fanout, aggregate, …) before drawing. Not
every system is a streaming pipeline.

### Process (mandatory order)

1. **Required capabilities** — map constraints to L0–L7 building blocks; no product names
2. **Start cheap (v0)** — fewest capabilities for current numbers; credible MVP
3. **Architecture research** — 2+ contested capabilities, 2–3 options each, forces + numbers
4. **Compose diagram** — role labels first; implementation in parentheses after selection
5. **Four flows** — write, read (latency budget), failure, deploy
6. **Component registry** — Role | Implementation | Capacity | Failure | Owner
7. **Trade-off triads** — per layer added after v0
8. **Production evidence** — behavior and incidents, not logos

### Start cheap (capability language)

Show what works at **1×** before adding async ingestion, stream processing, or
distributed cache. Example capability progression (problem-agnostic):

| Stage | Scale trigger | Capabilities added |
|-------|---------------|-------------------|
| v0 | Within single-node DB limits | Sync API + RDBMS + batch/cron aggregation |
| v1 | Write path exceeds DB TPS | Durable write buffer (log/queue) |
| v2 | Freshness SLA < batch interval | Stream or incremental aggregation |
| v3 | Read QPS exceeds DB | Materialized ranked/cached serving layer |

The v0 design must be **credible**, not a strawman. Thresholds come from
`numbers-to-know.md`, not from exemplar stacks.

### Four mandatory flows

1. **Write path** — every hop, protocol, async vs sync
2. **Read path** — hops with latency budget per hop (sums to Phase 2 P99)
3. **Failure path** — ≥2 components: user impact, degradation, recovery, stampede avoidance
4. **Deploy path** — canary/rolling, schema migration, rollback

### Component registry

| Role | Implementation | Capacity | Failure mode | Owner |
|------|----------------|----------|--------------|-------|

Implementation column is filled **after** architecture research — may be a
product, managed service, or first-principles component (Google-style).

### Trade-off triad (every capability added after v0)

**Solves** / **Worsens** / **When to change** — tied to constraint numbers.

### Production grounding

Prefer mechanism + failure mode over brand: *"Keyed stream state with
checkpoint recovery; 50GB state → 5–15 min restore"* not *"we use Flink."*

---

## Deep Dive Phase — Interview Depth

For each of 4+ components:

### Three tiers

- **Workable** — solves problem; state limitations
- **Strong** — addresses limitations; new challenges
- **Exceptional** — PE insight: sizing math, protocol steps, or non-obvious optimization

### Per dive

- **Breaking point** — numeric threshold ("at 500K QPS single Redis node exceeds 64GB...")
- **Resiliency pattern** — concrete config (circuit breaker: 50% error over 10s → open 30s)
- **Curveball** — constraint change → invalidated assumption → scoped redesign

---

## Phase 6 — Synthesis

- **6+ bottlenecks** with root cause, mitigations, real incident analogy
- **Failure matrix** — 5+ rows, different failure classes
- **3+ named incidents** — company, ~year, lesson
- **3+ anti-patterns** for this problem class
- **Evolution roadmap** — numeric breaking points at 10× and 100×
- **Coverage sweep** — building blocks used or explicitly deferred

---

## Company Calibration Quick Reference

| Company | Emphasize in output |
|---------|---------------------|
| **Google** | First-principles component design; global scale; data modeling rigor; skepticism of canned answers |
| **Amazon** | Operational excellence; blast radius; explicit assumptions; service ownership; failure recovery |
| **Meta** | Efficiency at scale; cache hierarchy; real-time social graph constraints |
| **LinkedIn** | Stream aggregation pipelines; feed freshness; professional graph segmentation |
| **Microsoft** | Enterprise multi-tenancy; regional compliance; hybrid cloud |
| **Databricks** | Data platform integration; lakehouse; stream-batch unification |

When user names a company, read `company-profiles.md` and weight the corresponding rows above.

---

## Anti-Patterns That Fail FAANG Loops

1. Architecture before numbers
2. Product-led HLD (Kafka/Redis/Flink defaults) without capability derivation or research
3. Single design with no alternatives for contested decisions
4. No failure degradation story ("we'll add replicas")
5. Deep dives that repeat the HLD diagram
6. Generic CAP theorem without user-facing consequence
7. No incremental path from simple to complex
