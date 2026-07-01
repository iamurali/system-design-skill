# Deep Dive Skill — Depth on Demand

This is the **complete Phase 5 skill**. Deep dives go **2–3 levels below** the
Phase 4 diagram on the components that matter — not every box.

```
Pick fragile components → workable / strong / exceptional tiers →
breaking point + resiliency → curveball per dive
```

Read this file at the start of Phase 5. Pair with
`assets/templates/07-deep-dives.template.md` and the **context checkpoint**
(HLD component registry).

**Do not repeat the HLD.** Teach something the diagram cannot show.

---

## Phase 5 entry checklist

1. Open Phase 4 **component registry** — list fragile, contested, or hot-path roles.
2. Select **4–6** components (minimum 4 for Gate 5).
3. For each: three tiers + numeric breaking point + resiliency pattern.
4. Each dive includes **curveball** (5-step protocol).
5. At least **one** dive has algorithm, protocol, or math depth signal.
6. Depth matches **archetype** — not every problem needs stream processing math.

---

## Section 1: What to deep dive (selection matrix)

Score candidates from Phase 4 (pick highest):

| Signal | Examples by shape |
|--------|-------------------|
| **Hot path** | Cache (A3), read API (A1), merge (A2), top-K serve (A7) |
| **Contested research** | Store choice, fanout strategy, sharding |
| **Fragile under scale** | Single leader, hot partition, global counter |
| **Novel / interesting** | Consistent hashing, sketch, rate limiter window |
| **Failure amplification** | Retry storm, cache stampede, rebalance |

| Skip diving on | Why |
|----------------|-----|
| CDN, DNS | Unless problem is media (A8) |
| Components not in HLD | Gate 5 fails |
| "We use Postgres" alone | No depth — dive indexing, pooling, replication |

### Shape → recommended dive topics

| Archetype | Strong dive candidates | Usually skip |
|-----------|------------------------|--------------|
| A1 CRUD | ID generation, cache aside, DB sharding, redirect hot key | Flink, CMS |
| A2 Feed | Fanout on write vs read, celebrity problem, cursor pagination | Exact ranking proofs |
| A3 Cache | Eviction policy, consistent hash ring, replication lag | SQL query planner |
| A5/A6 | Presence protocol, message ordering, connection scale | Batch ETL |
| A7 | Sketch sizing, window aggregation, segment cardinality | Simple CRUD indexes |
| A8 | Multipart upload, CDN invalidation, transcoding pipeline | Feed merge |
| A9 | Idempotency keys, ledger immutability, distributed lock | Approximate counts |

---

## Section 2: Three-tier structure (per dive)

### Workable

- Solves the problem at **current-scale numbers** from checkpoint.
- State **limitations** explicitly.

### Strong

- Addresses workable limitations.
- State **new challenges** introduced.

### Exceptional (PE bar)

Must include **at least one** of:

- **Algorithm internals** + complexity (e.g., ring walk O(log N), CMS error bound)
- **Protocol mechanics** + sequence/state diagram (leader election, rebalance)
- **Mathematical derivation** (capacity formula, error probability, hop bound)

Also required in every dive:

- **Breaking point:** numeric threshold — *"at 500K QPS, single node exceeds …"*
- **Resiliency pattern:** named pattern + concrete config (timeout, retry budget,
  circuit breaker threshold, stale-while-revalidate TTL)

---

## Section 3: Curveball protocol (per dive)

Each deep dive ends with:

### Curveball: What if [constraint change]?

1. **Constraint change** — named (10× traffic, multi-region, exact counts required)
2. **Invalidated assumption** — what the tiers assumed
3. **Blast radius** — what breaks, who is affected
4. **Scoped redesign** — change only affected subsystem
5. **Verification rest holds** — why other components still valid

This mirrors `references/reasoning-engine.md` curveball protocol — do not
redesign the entire system for a local change.

---

## Section 4: Depth signals by topic (not stack-specific)

Use when relevant — **do not force** streaming math on CRUD problems.

| Topic | Exceptional tier content |
|-------|--------------------------|
| Sharding | Consistent hash, virtual nodes, rebalance cost |
| Cache | Stampede prevention, W-TinyLFU admission, TTL skew |
| Rate limit | Token bucket vs sliding window math |
| ID generation | Snowflake bit layout, clock skew handling |
| Replication | Quorum read/write, leader failover timeline |
| Sketch / approximate | CMS parameters, error vs memory |
| Stream processing | Watermark, late events, state size |
| Search index | Inverted index merge, segment sizing |

---

## Section 5: Anti-patterns in deep dives

| Anti-pattern | Fix |
|--------------|-----|
| Repeating HLD boxes | Go to internals, configs, formulas |
| Name-dropping Raft/Kafka | Show election steps or partition assignment |
| "Scale horizontally" | Shard math, data motion cost |
| Breaking point vague | Replace with QPS, GB, or connection count |
| Same curveball every dive | Vary constraint per component |

---

## Phase 5 quality signals

- **4+ dives**, all tied to HLD registry.
- Every tier has limitations / new challenges filled in.
- **Numeric** breaking points on all dives.
- **≥1** non-obvious teaching moment (algorithm/protocol/math).
- Curveballs invalidate **real** assumptions from earlier tiers.

---

## Exemplar selection (optional)

| Shape | `07-deep-dives.md` |
|-------|-------------------|
| A3 | `assets/exemplars/in-memory-cache/` |
| A7 | `assets/exemplars/trending-articles-top-k/` |
| A1 / other | **Skill + template** |

---

## Handoff to Phase 6

Phase 6 bottlenecks should reference dive breaking points and resiliency gaps —
not invent new failure modes disconnected from Phase 5.
