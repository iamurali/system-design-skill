# Requirements Skill — Problem-Agnostic Framing & Scale

This is the **complete Phase 1 skill**. It applies to every system design
problem before any interface or architecture work.

**The requirements skill does not assume a tech stack or archetype outcome.** It
prescribes a **reasoning loop** that produces numbers, scope, and forces that
every later phase traces back to.

```
Reframe → early shape → scope FRs → estimate by forces → SLIs → out-of-scope
```

Read this file at the start of Phase 1. Pair with
`assets/templates/01-requirements.template.md` for output shape and
`references/numbers-to-know.md` for plausibility checks.

---

## Phase 1 entry checklist

Before listing features:

1. Read the raw prompt once — do not jump to a familiar architecture.
2. Complete **Problem Reframing** (Section 1) — at least one decision that
   narrows scope with judgment.
3. Complete **Early Problem Shape** (Section 2) — provisional archetype from
   `hld-archetypes.md` (refined in Phase 4).
4. Scope **2–4 core FRs** tied to the dominant access pattern.
5. Run the **full capacity chain** with shape-aware emphasis (Section 4).
6. State **1×, 10×, 100×** and what breaks first at each tier.
7. Define **2–3 SLIs** measurable before boxes exist.
8. List **≥3 out-of-scope** items with one-line reasoning each.

---

## Section 1: Problem Reframing

Reframing questions that **change architecture** — pick the ones relevant to
this prompt; do not ask all mechanically.

| Question | If yes → | If no → |
|----------|----------|---------|
| Exact vs approximate? | Strong consistency, exact stores | Sketching, eventual ranks, cheaper reads |
| Real-time vs batch? | Sync path, tight freshness SLAs | Async workers, minutes of staleness OK |
| Global vs single-region? | Replication, conflict resolution | Simpler consistency, lower latency |
| Who is the API customer? | Internal contract vs UX polish | Different auth, rate limits, SLAs |
| Read-heavy vs write-heavy? | Cache, replicas first | Buffers, sharding, ordering first |
| Strong invariants (money, inventory)? | Ledger, transactions | Eventual OK |
| 1 write → N readers? | Fanout, pub/sub, push | Point CRUD patterns |

**Document format:**

- **Before we design:** [question that could change everything]
- **Decision:** [chosen scope] **because** [judgment, not "interviewer said so"]

### Hidden requirements surfacer

Look for unstated needs:

- **Abuse / fraud** — high-value surfaces (trending, payments, sign-up)
- **Idempotency** — retries, mobile clients, async pipelines
- **Deletion / GDPR** — user data lifecycle
- **Multi-tenancy** — isolation between customers or regions
- **Cold start** — new entity with no history (feeds, recommendations)

Minimum **1** hidden requirement with why it matters architecturally.

---

## Section 2: Early Problem Shape (provisional)

Classify **before** deep design. Phase 4 will refine; Phase 1 sets estimation
emphasis.

Use the quick classifier in `hld-archetypes.md`:

| Provisional archetype | Estimation emphasis | Typical read:write |
|-----------------------|---------------------|-------------------|
| A1 Point CRUD | GET QPS, object size, retention | Often read-heavy |
| A2 Feed / timeline | Fanout factor, list size, cursor depth | Read-heavy |
| A3 Read-scaled | Cache working set, miss rate | Very read-heavy |
| A4 Search / discovery | Index size, query fanout | Read-heavy |
| A5 Fanout / realtime | Subscribers per write, push rate | Write amplification |
| A6 Chat / presence | Concurrent connections, message rate | Bidirectional |
| A7 Aggregate / meter | Event rate, window cardinality, top-K size | Write-heavy ingest |
| A8 Media / object | Blob size, CDN bandwidth | Bandwidth-bound |
| A9 Ledger / coordination | TPS, invariant checks | Write with strong consistency |

**Dominant force (one sentence):** e.g. *"Serve 200K read QPS at 30ms P99 on
key lookup"* or *"Ingest 50K events/s without loss."*

**Read:write ratio:** state explicitly — drives Phase 2 latency path and Phase 3
index strategy.

---

## Section 3: Functional Requirements

Rules:

- **2–4 P0 features** — resist feature creep.
- Each FR maps to an **access pattern** (point read, range scan, append, aggregate).
- Mark **P0 / P1 / P2** — architecture covers P0; P1 noted as follow-on.
- No implementation in FRs (no "use Redis").

| ID | Requirement | Priority | Access pattern |
|----|-------------|----------|----------------|
| FR-1 | | P0 | point read / write / scan / aggregate |

### Shape-specific FR traps (avoid)

| Trap | Wrong for CRUD | Wrong for top-K |
|------|----------------|-----------------|
| Assuming async pipeline | Sync write is fine at low W QPS | Events need durable ingest |
| Assuming personalization | Global entity is enough | Segment explosion if per-user ranks |
| Assuming strong ranking | Approximate OK for discovery | Exact order may be required |

---

## Section 4: Capacity Estimation (shape-aware)

### Universal chain (all problems)

Every design must show **all links** with inline math:

```
DAU (or MAU)
  → actions/user/day (read and write separate)
  → average read QPS, average write QPS
  → peak QPS (state peak factor: 2–10×, justify)
  → storage/day (writes × object size)
  → total storage (× retention)
  → read bandwidth (peak read QPS × response size)
  → write bandwidth (peak write QPS × request size)
  → server count (peak QPS ÷ per-node capacity from numbers-to-know.md)
```

Cross-check orders of magnitude against `numbers-to-know.md`.

### Shape-specific extensions

Add rows to **Component Load Summary** only when the shape needs them:

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
decision, not a requirements default.

### Growth trajectory (mandatory)

| Tier | Scale input | What breaks first |
|------|-------------|-------------------|
| 1× (launch) | From assumptions | [first constraint] |
| 10× | Multiply DAU/QPS | [constraint + symptom] |
| 100× | | |

Breaking constraints must be **specific** ("single primary DB connection pool")
not vague ("scale issues").

---

## Section 5: Success Metrics (SLIs)

Define **2–3** metrics **before** architecture:

| Metric | Target | Type | Why it matters |
|--------|--------|------|----------------|
| | | Business / Technical | |

Examples by shape:

- **CRUD:** P99 read latency, availability, error rate
- **Feed:** freshness lag, empty-feed rate, P99 feed load
- **Aggregate:** ranking freshness, ingest lag, cache hit ratio
- **Cache:** hit ratio, eviction rate, P99 GET latency

---

## Section 6: Explicit Out-of-Scope

Minimum **3** exclusions. Each needs **one-line why** tied to complexity or
non-goals.

| Exclusion | Reason |
|-----------|--------|
| | |

Good: *"Per-user personalized trending — requires feature store + online ML;
we serve global segments only."*

Bad: *"ML — out of scope."* (no reasoning)

---

## Phase 1 quality signals (PE bar)

- **Reframes before listing features** — shows judgment, not transcription.
- **Separate read and write QPS** — never a single "QPS" number.
- **Peak factor justified** — business hours, viral events, batch jobs.
- **Growth tier names a first breaker** — proves you see evolution early.
- **Shape stated** — prevents defaulting to streaming stack in later phases.

---

## Exemplar selection (optional)

Load **one** file for tone, matched to provisional shape:

| Shape | Exemplar `01-requirements.md` |
|-------|-------------------------------|
| A3 Read-scaled | `assets/exemplars/in-memory-cache/` |
| A7 Aggregate | `assets/exemplars/trending-articles-top-k/` |
| A1 CRUD / other | **Skill + template only** (do not load A7 for URL shortener) |

---

## Handoff to Phase 2

Phase 2 NFRs **must trace** to numbers in this file. Carry forward:

- Peak read QPS, peak write QPS, total storage
- P99 latency **candidate** (refined in Phase 2 with budget)
- Consistency **hint** from reframing (exact vs approximate)
- Provisional archetype + dominant force
