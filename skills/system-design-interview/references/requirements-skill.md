# Requirements Skill — Problem-Agnostic Framing

This is the **complete Phase 1 skill**. It defines **what** the system does and
**who** it serves — not how fast or how big (those are Phase 2 NFRs).

**The requirements skill does not assume a tech stack or archetype outcome.** It
prescribes a **reasoning loop** that produces scope and forces that Phase 2
quantifies.

```
Reframe → early shape → scope FRs → scale assumptions → SLIs → out-of-scope
```

Read this file at the start of Phase 1. Pair with
`assets/templates/01-requirements.template.md`.

**Capacity estimation (QPS, storage, bandwidth, server count) belongs in Phase 2**
(`nfr-skill.md`). Phase 1 records **inputs only** — DAU, actions/day, object
size, retention, peak factor.

---

## Phase 1 entry checklist

Before listing features:

1. Read the raw prompt once — do not jump to a familiar architecture.
2. Complete **Problem Reframing** (Section 1) — at least one decision that
   narrows scope with judgment.
3. Complete **Early Problem Shape** (Section 2) — provisional archetype from
   `hld-archetypes.md` (refined in Phase 4).
4. Scope **2–4 core FRs** tied to the dominant access pattern.
5. Record **scale assumptions** (Section 4) — inputs for Phase 2 math.
6. Define **2–3 SLIs** measurable before boxes exist.
7. List **≥3 out-of-scope** items with one-line reasoning each.

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

Classify **before** deep design. Phase 4 will refine; Phase 2 will quantify using
this shape.

Use the quick classifier in `hld-archetypes.md`:

| Provisional archetype | Phase 2 estimation emphasis | Typical read:write |
|-----------------------|----------------------------|-------------------|
| A1 Point CRUD | GET QPS, object size, retention | Often read-heavy |
| A2 Feed / timeline | Fanout factor, list size, cursor depth | Read-heavy |
| A3 Read-scaled | Cache working set, miss rate | Very read-heavy |
| A4 Search / discovery | Index size, query fanout | Read-heavy |
| A5 Fanout / realtime | Subscribers per write, push rate | Write amplification |
| A6 Chat / presence | Concurrent connections, message rate | Bidirectional |
| A7 Aggregate / meter | Event rate, window cardinality, top-K size | Write-heavy ingest |
| A8 Media / object | Blob size, CDN bandwidth | Bandwidth-bound |
| A9 Ledger / coordination | TPS, invariant checks | Write with strong consistency |

**Dominant force (one sentence):** qualitative — e.g. *"Optimize read path at
LinkedIn scale"* or *"Absorb viral write spikes without loss."*

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

## Section 4: Scale Assumptions (inputs only)

Record **inputs** for Phase 2 — do **not** derive QPS, storage, or server count
here.

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| DAU (or MAU) | | |
| Actions/user/day (read) | | |
| Actions/user/day (write) | | |
| Avg object / response size | | |
| Retention | | days |
| Peak factor | | × average (justify) |

Optional qualitative note: *"Expect read-heavy (~20:1)"* — Phase 2 proves it with
math.

---

## Section 5: Success Metrics (SLIs)

Define **2–3** metrics **before** architecture (targets may be refined in Phase 2):

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
- **Read-heavy vs write-heavy stated** — even before QPS math in Phase 2.
- **Shape stated** — prevents defaulting to streaming stack in later phases.
- **No premature architecture** — no QPS-derived component rows here.

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

Phase 2 (`nfr-skill.md`) derives the **full capacity chain** from assumptions
above, then sets latency, availability, consistency, and durability targets.

Carry forward:

- Scale assumptions table
- Provisional archetype + dominant force + read:write ratio
- Consistency **hint** from reframing (exact vs approximate)
- SLI candidates (quantified in Phase 2)
