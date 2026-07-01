# NFR Skill — Scale, Capacity, and Constraints

This is the **complete Phase 2 skill**. NFRs cover **how well** the system must
perform — including **capacity estimation**, which is a core non-functional
concern (throughput, storage, bandwidth, scalability).

```
Read Phase 1 assumptions → full capacity chain → latency budget → error budget →
consistency per operation → durability → security → ops
```

Read this file at the start of Phase 2. Pair with
`assets/templates/02-non-functional-requirements.template.md` and
`references/numbers-to-know.md`.

**Do not invent a second scale story.** Every derived number must trace to Phase 1
assumptions.

---

## Phase 2 entry checklist

1. Re-read Phase 1 **scale assumptions**, read:write ratio, provisional archetype.
2. Complete **capacity estimation chain** (Section 1) — all links with inline math.
3. Add **component load summary** and **growth trajectory** (1×, 10×, 100×).
4. Choose **hot path** for latency budget (read vs write vs both).
5. Set P50/P95/P99/P99.9 with **hop budget that sums to P99 (±10%)**.
6. Compute **error budget** in concrete downtime per month.
7. Assign **consistency model per operation** with user-facing consequence.
8. Classify data by **durability** (RPO/RTO table).
9. Add **security NFRs** proportional to exposure.
10. Sketch **one runbook** for the top failure scenario from growth trajectory.

---

## Section 1: Capacity estimation (mandatory)

Capacity is an NFR: it defines throughput, storage, and scale constraints the
architecture must satisfy.

### Estimation chain (all problems)

Derive from Phase 1 assumptions. Show **all links** with inline math:

```
DAU (or MAU) — from Phase 1
  → actions/user/day (read and write separate)
  → average read QPS, average write QPS
  → peak QPS (peak factor from Phase 1)
  → storage/day (writes × object size)
  → total storage (× retention)
  → read bandwidth (peak read QPS × response size)
  → write bandwidth (peak write QPS × request size)
  → server count (peak QPS ÷ per-node capacity from numbers-to-know.md)
```

Cross-check orders of magnitude against `numbers-to-know.md`.

### Shape-specific extensions

Add rows to **Component Load Summary** only when the archetype needs them:

| Shape | Extra rows to estimate |
|-------|------------------------|
| A1 CRUD | DB connections, cache working set |
| A2 Feed | Fanout writes or merge reads per request |
| A3 Cache | Memory per node, hit ratio target |
| A5/A6 Fanout | Messages per write, connection count |
| A7 Aggregate | Events/s, segment cardinality, sketch/state size |
| A8 Media | Egress GB/s, multipart upload rate |
| A9 Ledger | Contention TPS, audit log growth |

**Do not** add Kafka/stream rows for A1 CRUD at 500 write QPS — that is a Phase 4
decision unless numbers force it.

### Growth trajectory (mandatory)

| Tier | Scale input | What breaks first |
|------|-------------|-------------------|
| 1× (launch) | From capacity chain | [first constraint] |
| 10× | Multiply DAU/QPS | [constraint + symptom] |
| 100× | | |

Breaking constraints must be **specific** ("single primary DB connection pool")
not vague ("scale issues").

---

## Section 2: Latency — shape-aware paths

### Pick the budgeted path

| Dominant force (Phase 1) | Budget this path first |
|--------------------------|------------------------|
| Read-heavy CRUD / cache | Client → response on cache hit |
| Write-heavy ingest | Ack path (client → durable enqueue) |
| Feed load | End-to-end feed page assembly |
| Fanout / chat | Message delivery to recipient |
| Aggregate query | Query API → ranked result (not batch job) |

State which path the P99 target applies to. Secondary paths get looser targets
in a separate table if needed.

### Percentile targets

| Percentile | Target | Path |
|------------|--------|------|
| P50 | ms | |
| P95 | ms | |
| P99 | ms | **Primary SLA** |
| P99.9 | ms | (optional; required for payments/ads) |

### Latency budget breakdown (mandatory)

Decompose P99 into hops. **Sum must equal stated P99 ±10%.**

| Hop | Budget (ms) | Notes |
|-----|-------------|-------|
| Client → edge | | TLS, DNS |
| Edge → service | | LB, routing |
| Service logic | | Auth, validation |
| Data fetch | | Cache / DB / fanout |
| Serialization | | |
| **Total P99** | **ms** | |

#### Shape-specific hop hints

| Shape | Typical hot hops | Common mistake |
|-------|------------------|----------------|
| A1 + cache | Cache hit vs miss split | Budgeting only hit path |
| A2 feed | Merge N sources | Ignoring fanout read amp |
| A7 aggregate | API → precomputed store | Budgeting stream job latency |
| A8 media | CDN edge vs origin | Omitting TTFB for large objects |

Use `numbers-to-know.md` for hop plausibility (cross-DC ~50–150ms, SSD read ~0.1ms).

---

## Section 3: Availability and error budget

### Targets

| Surface | Availability | Error budget (concrete) |
|---------|--------------|-------------------------|
| User-facing API | 99.9% / 99.95% / 99.99% | ~43 / ~22 / ~4.3 min per month |
| Internal ingest | May be lower if async | |

**Budget consumers:** planned deploys, dependency outages, hot partitions,
cascading retries.

### Degradation policy (tie to consistency)

When over budget or under dependency failure:

- **Fail open** (stale OK) vs **fail closed** (error) — state per API.
- Example: trending may serve stale ranks; payments must fail closed.

---

## Section 4: Consistency model

Per **operation or data class**, not one word for the whole system.

| Data / Operation | Model | User-facing consequence |
|------------------|-------|-------------------------|
| | Strong / Eventual / Read-your-writes / Causal | User may see … for up to X |

### Shape defaults (override with Phase 1 reframing)

| Shape | Typical consistency | When strong is required |
|-------|---------------------|---------------------------|
| A1 CRUD | Strong for writes; eventual for read replicas | Inventory, balances |
| A2 feed | Eventual fanout | None for social feed |
| A7 aggregate | Eventual freshness | Exact billing counts |
| A9 ledger | Strong per entity | Always |

**PE signal:** Name the consequence — *"user may see stale feed for up to 30s"*
not just "eventual consistency."

---

## Section 5: Durability

| Data class | RPO | RTO | Mechanism sketch |
|------------|-----|-----|------------------|
| User-facing state | | | |
| Event log / audit | | | |
| Derived / cache | | | Rebuild from source |

- **RPO:** max acceptable data loss window.
- **RTO:** max time to restore service.

Shape notes:

- **A7:** event log often RPO ≈ 0 (replicated log); sketches may be rebuildable.
- **A3 cache:** RPO infinite (cache); RTO = warm-up time.
- **A1:** primary DB replication defines RPO.

---

## Section 6: Security NFRs

Scale to exposure — not every problem needs every row.

- **Authentication / authorization:** mechanism, token TTL.
- **Encryption:** in transit (TLS), at rest (if PII/financial).
- **Abuse:** rate limits tied to **peak QPS from Section 1** and Phase 1 reframing.
- **Audit:** who did what, retention.

---

## Section 7: Operational requirements

| Requirement | Target |
|-------------|--------|
| Zero-downtime deploy | Strategy name (rolling / canary) |
| Monitoring | SLI thresholds → alert |
| Capacity planning | Review cadence |
| On-call | Severity definitions |

### Runbook sketch (mandatory — one scenario)

Pick the **top failure** from growth trajectory or highest-risk dependency.

1. **Detect:** symptom / alert
2. **Mitigate:** immediate action (disable feature, failover, throttle)
3. **Recover:** restoration steps
4. **Post-incident:** prevention

---

## Traceability matrix (recommended)

| NFR | Traces to |
|-----|-----------|
| Peak 230K read QPS | Phase 1 DAU × reads/day × peak factor |
| P99 30ms read | Read-heavy shape, cache hit path |
| 99.95% API | Revenue-facing surface |

---

## Phase 2 quality signals

- Capacity chain **complete** and plausible vs `numbers-to-know.md`.
- **Separate read and write QPS** — never a single "QPS" number.
- Latency budget **arithmetic** checks out.
- Error budget is a **number**, not "high availability."
- Consistency has **user-visible** effect.

---

## Handoff to Phase 3

Carry forward for interface design:

- Peak read QPS, peak write QPS, total storage (from capacity chain)
- P99 target and hop budget
- Consistency per entity type
- Idempotency / durability needs for write APIs
- Rate-limit and auth requirements
