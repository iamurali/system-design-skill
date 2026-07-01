# FAANG & Top-Tier System Design Interview Patterns

Synthesized from public interview guides, engineering blogs, and company
hiring loops (Google L5+, Amazon SDE II–Principal, Meta Staff+, LinkedIn,
Databricks, Microsoft). Use this reference at **Phase 1** (framing) and
**Phase 4** (architecture) to calibrate world-class output.

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

## Requirements Phase — Non-Negotiables

### Reframing (before listing features)

Ask questions that change the architecture:

- Exact vs approximate? (leaderboard vs trending feed)
- Real-time vs batch? (sub-second vs 15-minute staleness)
- Global vs single-region? (multi-master vs single writer)
- Who is the customer of this API? (end user vs internal service)

Document at least one reframing that **narrows scope with judgment**.

### Capacity estimation chain

Every design must show this chain with explicit assumptions:

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

### Out-of-scope

Minimum 3 exclusions, each with **one-line why** (not "we won't do ML" but "personalized ranking requires per-user feature store — out of scope; we serve global top-K only").

### Success metrics (SLIs)

Define 2–3 measurable signals before architecture:

- Business: CTR, time-on-feed, conversion
- Technical: P99 latency, freshness lag, error rate, cache hit ratio

---

## NFR Phase — SRE-Grade Constraints

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
| Engagement events | 0 (no loss) | minutes | Kafka retention + replay |
| Top-K snapshots | 5 min | 30 sec | Redis AOF + rebuild from stream |

### Runbook sketch

One top failure scenario with detect → mitigate → recover steps (not "add monitoring").

---

## HLD Phase — World-Class Architecture

### 1. Start cheap (mandatory)

Show the design that works **at current scale** before adding Kafka, Flink, etc.

Example progression for trending:

| Stage | Scale trigger | Architecture |
|-------|---------------|--------------|
| v0 | <1K write QPS | Postgres + periodic cron aggregation |
| v1 | >10K write QPS | Kafka buffer + single consumer |
| v2 | >100K write QPS | Stream processor + approximate counting |
| v3 | >500K write QPS | Sharded aggregation + push to Redis |

The v0 design must be **credible**, not a strawman dismissed in one sentence.

### 2. Four mandatory flows

1. **Write path** — every hop, protocol, async vs sync
2. **Read path** — hops with latency budget per hop (sums to Phase 2 P99)
3. **Failure path** — ≥2 component failures: user impact, degradation, recovery, stampede avoidance
4. **Deploy path** — canary/rolling, schema migration, rollback

### 3. Component registry

Every major component:

| Component | Capacity | Failure mode | Owner team |
|-----------|----------|--------------|------------|
| Ingestion API | 200K write QPS | Overload → 429 + queue | Product Platform |
| Kafka cluster | 500K msg/s | Broker loss → ISR failover | Data Platform |

### 4. Trade-off triad (every major addition)

**Solves** / **Worsens** / **When to change** — specific to this system.

### 5. Production grounding

Prefer: *"At LinkedIn, Samza jobs with keyed RocksDB state hold windowed aggregates; recovery from checkpoint takes 5–15 min for 50GB state"* over *"LinkedIn uses Samza."*

Cite real incidents when relevant (Twitter trending manipulation, Facebook cache stampede, etc.).

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
| **LinkedIn** | Kafka/Samza pipelines; feed freshness; professional graph segmentation |
| **Microsoft** | Enterprise multi-tenancy; regional compliance; hybrid cloud |
| **Databricks** | Data platform integration; lakehouse; stream-batch unification |

When user names a company, read `company-profiles.md` and weight the corresponding rows above.

---

## Anti-Patterns That Fail FAANG Loops

1. Architecture before numbers
2. Kafka/Redis as default without scale justification
3. Single design with no alternatives for contested decisions
4. No failure degradation story ("we'll add replicas")
5. Deep dives that repeat the HLD diagram
6. Generic CAP theorem without user-facing consequence
7. No incremental path from simple to complex
