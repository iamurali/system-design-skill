# NFR Skill — Constraints Derived from Numbers

This is the **complete Phase 2 skill**. NFRs are not a separate wish list —
they are **obligations implied by Phase 1 scale and shape**.

```
Read Phase 1 → pick latency path by shape → budget P99 → error budget →
consistency per operation → durability by data class → security → ops
```

Read this file at the start of Phase 2. Pair with
`assets/templates/02-non-functional-requirements.template.md`.

**Do not invent a second scale story.** Every target must cite Phase 1 numbers.

---

## Phase 2 entry checklist

1. Re-read Phase 1 peak QPS, read:write ratio, provisional archetype.
2. Choose **hot path** for latency budget (read path vs write path vs both).
3. Set P50/P95/P99/P99.9 with **hop budget that sums to P99 (±10%)**.
4. Compute **error budget** in concrete downtime per month.
5. Assign **consistency model per operation** with user-facing consequence.
6. Classify data by **durability** (RPO/RTO table).
7. Add **security NFRs** proportional to exposure (public API vs internal).
8. Sketch **one runbook** for the top failure scenario from Phase 1 growth tier.

---

## Section 1: Latency — shape-aware paths

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

## Section 2: Availability and error budget

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

## Section 3: Consistency model

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

## Section 4: Durability

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

## Section 5: Security NFRs

Scale to exposure — not every problem needs every row.

- **Authentication / authorization:** mechanism, token TTL.
- **Encryption:** in transit (TLS), at rest (if PII/financial).
- **Abuse:** rate limits tied to Phase 1 peak QPS and abuse reframing.
- **Audit:** who did what, retention.

---

## Section 6: Operational requirements

| Requirement | Target |
|-------------|--------|
| Zero-downtime deploy | Strategy name (rolling / canary) |
| Monitoring | SLI thresholds → alert |
| Capacity planning | Review cadence |
| On-call | Severity definitions |

### Runbook sketch (mandatory — one scenario)

Pick the **top failure** from Phase 1 growth trajectory or highest-risk
dependency.

1. **Detect:** symptom / alert
2. **Mitigate:** immediate action (disable feature, failover, throttle)
3. **Recover:** restoration steps
4. **Post-incident:** prevention

---

## Traceability matrix (recommended)

| NFR | Traces to Phase 1 |
|-----|-------------------|
| P99 30ms read | 230K peak read QPS, read-heavy |
| 99.95% API | Revenue-facing surface |
| 5s staleness OK | Approximate trending reframing |

---

## Phase 2 quality signals

- Latency budget **arithmetic** checks out.
- Error budget is a **number**, not "high availability."
- Consistency has **user-visible** effect.
- No NFR contradicts Phase 1 scale (e.g., 10ms P99 global with cross-region
  strong consistency on every write without justification).

---

## Handoff to Phase 3

Carry forward for interface design:

- P99 target and hop budget (defines how many sync calls allowed)
- Consistency per entity type
- Idempotency / durability needs for write APIs
- Rate-limit and auth requirements
