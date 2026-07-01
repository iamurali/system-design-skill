# HLD Skill — Problem-Agnostic Architecture Design

This is the **complete Phase 4 skill**. It applies to every system design
problem: URL shortener, chat, cache, rate limiter, news feed, payments, storage,
top-K, or greenfield prompts.

**The HLD skill does not prescribe a tech stack.** It prescribes a **reasoning
loop** that ends in a defensible architecture for *this* problem's shape.

```
Classify shape → derive capabilities → v0 → research options → compose → flows
```

Read this file at the start of Phase 4. Pair with `hld-archetypes.md` for
classification and `assets/templates/06-high-level-design.template.md` for output shape.

---

## Phase 4 entry checklist

Before drawing boxes:

1. Read the **context checkpoint** (scale, NFRs, access patterns).
2. Complete **Problem Shape Classification** (Section 1).
3. Open the matching **archetype card** in `hld-archetypes.md`.
4. Fill the HLD template section by section — **no product names until Section 5**.

---

## Section 1: Problem Shape Classification

Answer from Phase 1–3. Numbers drive everything.

| Signal | Your value | Architectural implication |
|--------|------------|---------------------------|
| Read QPS vs write QPS | R:___ W:___ | Read-heavy → cache/replica; write-heavy → buffer/shard |
| Read:write ratio | ___:1 | >10:1 often needs read path optimization first |
| P99 latency target | ___ ms | Sub-50ms rules out cold storage on hot path |
| Consistency | strong / eventual / session | Strong → fewer caches, more coordination |
| Payload size (typical) | ___ | Large → blob store; small → KV/row store |
| Fanout (1 write → N readers) | none / modest / massive | Chat/notifications need push or pub/sub |
| Durability (RPO) | ___ | Zero loss → durable log or sync replicate |
| Freshness / staleness SLA | ___ | Tight → sync or stream; loose → batch OK |
| Hot key risk | low / medium / high | Sharding key design, isolation |
| Multi-region | yes / no | Replication, conflict resolution |

**Primary archetype(s):** pick 1–2 from `hld-archetypes.md` (e.g. A3 Read-scaled CRUD, not "top-K").

**Dominant force (one sentence):** e.g. *"Optimize read path at 100K QPS with 50ms P99"* or *"Absorb 1M write spikes without losing events."*

---

## Section 2: Required Capabilities (technology-agnostic)

From classification + archetype card, list **capabilities** the system must provide.
Use `building-blocks-index.md` layer IDs (L1–L7) as vocabulary.

Rules:
- **No product names** (no Kafka, Redis, DynamoDB, Flink).
- Each row ties to a **number or NFR** from the checkpoint.
- Mark each: **required now** | **defer** | **not needed** with threshold.

| Capability (what, not how) | Layer | Trigger (number/NFR) | Now / defer / skip |
|----------------------------|-------|----------------------|--------------------|
| Edge routing & TLS termination | L1 | Any public API | |
| Request authentication | L1/L7 | User-facing API | |
| Primary durable store for entities | L4 | All stateful systems | |
| Read replica or cache | L3 | R:W > 10:1 and P99 tight | |
| Write buffer / async decoupling | L5 | Write spikes or slow consumers | |
| Id generation | L6 | Need global unique keys | |
| ... | | | |

**Defer list:** capabilities you explicitly skip at 1× with the number that would force them later.

---

## Section 3: Architecture Evolution (start cheap)

Design **v0 for today's numbers only**. v0 must be shippable, not a strawman.

| Version | Scale / trigger | What you add (capability) | What stays absent |
|---------|-----------------|---------------------------|-------------------|
| v0 | 1× current | | |
| v1 | first bottleneck | | |
| v2 | 10× (optional) | | |

**Breaking point table:**

| Component / pattern | Breaks at | Symptom | Next capability |
|--------------------|-----------|---------|-----------------|
| Single DB primary | ___ QPS | Connection pool, disk IO | Read replica / cache / shard |
| ... | | | |

**Selected version for current scale:** v___ because ___.

---

## Section 4: Architecture Research (mandatory)

For **each capability added after v0**, research before naming products.

### 4.1 Local sources
`building-blocks-index.md`, `tradeoff-framework.md`, `numbers-to-know.md`, `company-profiles.md` (if named).

### 4.2 External research
Use `research-protocol.md` or web when:
- Two or more viable implementations exist at this scale
- You lack confidence in failure modes or ops cost
- User asked for Google (build internals) or Amazon (ops depth)

### 4.3 Research table (repeat per contested capability)

#### Research: [Capability name]

| Option class | Examples (research, don't default) | Fits | Fails when | Ops / recovery | Verdict |
|--------------|-----------------------------------|------|------------|----------------|----------------|
| | | | | | |

**Selected:** ___ **because** ___ (cite checkpoint number).

**Rejected:** ___ **because** ___.

Minimum **2 contested capabilities** for any non-trivial problem. Trivial CRUD at low QPS may have one (primary store choice).

---

## Section 5: System Composition

### 5.1 Diagram rules

- **Boxes = roles** (Query API, Primary store, Read cache, Write buffer).
- **Implementations** go in registry table or small parentheses — not the main narrative.
- **Label edges:** protocol, sync/async, approximate QPS from Phase 1.
- **Do not** default to a pipeline shape unless classification says write-buffer + async compute.

Pick diagram topology from archetype (see `hld-archetypes.md`):
- **CRUD:** client → API → store (± cache)
- **Async:** client → API → queue → worker → store
- **Fanout:** writer → bus → N subscribers
- **Not every problem is:** ingest → log → stream → cache → API

### 5.2 System overview

```
[Fill based on YOUR archetype — not a template pipeline]
```

---

## Section 6: Four Flows (always)

### Flow 1: Write / mutation path
Hops to durability. Idempotency, ordering, conflict handling if relevant.

### Flow 2: Read / query path
Per-hop latency budget → must sum to Phase 2 P99 (±10%).

### Flow 3: Failure & degradation
≥2 failure scenarios on **components in YOUR diagram**. User impact, stale vs error, recovery, stampede avoidance.

### Flow 4: Deploy & migration
Rollout, schema/contract change, rollback.

---

## Section 7: Component Registry

| Role | Implementation (post-research) | Capacity | Failure mode | Owner |
|------|----------------------------------|----------|--------------|-------|

---

## Section 8: Trade-off Triads

One triad per capability **added after v0**: Solves / Worsens / When to change.

---

## Section 9: Production Evidence

Cite **mechanisms and incidents**, not brand laundry lists. Tie evidence to a decision you made in Section 4.

---

## Exemplar policy (critical)

| Exemplar folder | Use for HLD calibration when... |
|-----------------|--------------------------------|
| `url-shortener` | Point lookup, CRUD, read-heavy, sharding |
| `in-memory-cache` | Cache layer, eviction, replication |
| `trending-articles-top-k` | **Only** when prompt is aggregation/top-K/streaming |

**Never** load `trending-articles-top-k` HLD for unrelated prompts. If no exemplar matches, follow this skill + template only.

---

## Anti-patterns

| Failure | Fix |
|---------|-----|
| Same ingest→log→stream→cache diagram for every problem | Classify shape first |
| Top-K / sketch / ranked store without aggregation in requirements | Remove unused capabilities |
| Products in Section 2 | Move to Section 4–7 only |
| Skipping research ("we'll use X") | Fill research tables |
| v0 is "won't scale" | Credible MVP with numbers |
| Copying exemplar stack | Copy process only |

---

## Research agent (Phase 4)

Trigger during Phase 4 when Section 4 has a row with verdict still open after local refs.
Append to `10-interview-transcript.md` under `## Research Findings -- Phase 4`.
