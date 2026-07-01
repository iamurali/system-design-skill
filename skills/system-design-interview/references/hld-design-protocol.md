# HLD Design Protocol — Forces-First, Research-Driven

This protocol governs **Phase 4** (`06-high-level-design.md`). The HLD is **not**
a canned stack (Kafka + Redis + Flink). It is the output of reasoning:

```
Constraints + numbers → required capabilities → researched options → selected design
```

Technology names appear **only after** capability needs and option evaluation.
If you cannot explain why a capability is needed without naming a product,
the reasoning is not done.

> **Google bar:** Interviewers penalize rehearsed FAANG stacks. They reward
> deriving the shape of the system from constraints, then defending specific
> choices with tradeoffs and production evidence.

---

## Step 0: Inputs (do not design yet)

From the context checkpoint, list:

| Input | Source |
|-------|--------|
| Peak read/write QPS, storage, bandwidth | Phase 1 |
| P99 latency, freshness, consistency consequence | Phase 2 |
| Top access patterns, sharding key | Phase 3 |
| Top 2–3 constraints that force architecture | Derived |

---

## Step 1: Derive required capabilities (technology-agnostic)

Map each constraint to **capabilities**, not products. Use
`building-blocks-index.md` layer names (L0–L7) as vocabulary.

| Constraint (number) | Required capability | Building-block layer |
|---------------------|---------------------|----------------------|
| 50K peak write QPS, burst tolerance | Durable write buffer; decouple producers from aggregators | L5 messaging/streaming |
| 60s freshness on 1h window | Windowed incremental aggregation with recoverable state | L5 stream processing |
| 230K read QPS, P99 50ms | Pre-materialized ranked lists; sub-ms reads | L3 caching / L4 data store |
| ±5% count error acceptable | Approximate frequency / top-K structures | Algorithm choice, not a product |
| Billions of keys, bounded memory | Sublinear counting (sketch, Space-Saving, etc.) | Algorithm choice |

**Output section:** `## Required Capabilities` — no product names in this section.

Ask for each capability:
- What happens if we **omit** it at current scale?
- At what **number** does it become mandatory?

---

## Step 2: Start cheap (capability-minimal v0)

Design v0 using the **fewest capabilities** that satisfy Phase 1 numbers **today**.

| Version | Scale trigger | Capabilities present | What is intentionally absent |
|---------|---------------|----------------------|------------------------------|
| v0 | 1× (current) | Sync API + RDBMS + batch rollups | No stream processor, no distributed cache |
| v1 | bottleneck X | + write buffer | ... |

v0 must be **credible** — a team could ship it. State what breaks first and the
**numeric threshold** (e.g., "RDBMS write path saturates at ~1K indexed writes/s").

---

## Step 3: Architecture research (mandatory before product names)

For **each capability added after v0**, run a mini research pass. This is not
optional for contested layers (storage, streaming, caching, search).

### 3a. Local references first

- `building-blocks-index.md` — options at that layer
- `tradeoff-framework.md` — triad framing
- `numbers-to-know.md` — per-node limits
- `company-profiles.md` — if user named a company

### 3b. External research when depth matters

Use `research-protocol.md` (or web search) when:

- Multiple viable products exist at this scale (stream processor, ranked store, etc.)
- User asked for company-specific bar (Google first-principles, Amazon ops)
- Interviewer checkpoint flagged wrong technology choice
- You are unsure of failure modes or operational limits

**Research question format:**

> "For [capability] at [peak QPS / latency / freshness], compare [option A],
> [option B], [option C] on: latency, ops burden, failure recovery, cost,
> team familiarity. Which fits our constraints?"

### 3c. Document in HLD

**Output section:** `## Architecture Research`

Per contested capability, include:

| Capability | Options evaluated | Key forces | Selected | Why not the others |
|------------|-------------------|------------|----------|-------------------|
| Write buffer | managed queue vs log vs DB outbox | burst absorption, replay | ... | ... |

Minimum **2 contested decisions** with 2–3 options each. Selection cites **forces
and numbers**, not "industry standard."

---

## Step 4: Compose the architecture (roles first, products second)

### Diagram convention

Use **role labels** in the main diagram; optional implementation in parentheses:

```
[Ingestion API] → [Durable event log] → [Stream aggregator] → [Ranked store] → [Query API]
                         (Kafka)              (Flink)            (Redis ZSET)
```

If the problem is greenfield and no product is chosen yet, **omit parentheses**
and describe implementation class: "log-based message broker", "in-memory ranked store."

### Four flows (unchanged)

1. Write path — hops to durability
2. Read path — per-hop latency budget → Phase 2 P99
3. Failure — ≥2 components, degradation, stampede avoidance
4. Deploy — canary, migration, rollback

### Component registry

| Role | Implementation (if decided) | Capacity | Failure mode | Owner |

---

## Step 5: Trade-off triads (per addition beyond v0)

For every capability layer added after v0:

- **Solves:** which constraint number
- **Worsens:** latency, ops, consistency, cost, complexity
- **When to change:** constraint change that invalidates the choice

---

## Step 6: Production grounding (evidence, not name-drops)

Cite **behavior**, not logos:

- Good: "Keyed stream state with checkpoint recovery; 50GB state → 5–15 min restore"
- Bad: "We use Flink because LinkedIn uses Flink"

Prefer engineering blogs, papers, postmortems when research supports the choice.

---

## Anti-Patterns (automatic quality failures)

| Anti-pattern | Why it fails |
|--------------|--------------|
| Diagram opens with Kafka/Redis/Flink boxes | Product-led, not constraint-led |
| Single option per layer | No solution-space navigation |
| v0 is one sentence ("won't scale") | Strawman, not incremental design |
| Same stack for every problem | Skill collapse; ignores read/write shape |
| Research section missing | LLM guessed; not defensible in interview |
| Capabilities copied from exemplar | Exemplar is **one researched outcome**, not a template stack |

---

## Relationship to exemplars

`assets/exemplars/*/06-high-level-design.md` show **one valid path** after
research for that problem. **Do not copy its product choices** into unrelated
problems. Copy the **process**: capabilities → research table → selection → flows.

---

## When to invoke Research agent in Phase 4

Run research **during** Phase 4 (not only after Interviewer), when:

1. Adding any L5 (messaging/streaming) or L4 (storage) component beyond v0
2. Freshness vs latency tradeoff is non-obvious
3. User named Google (first-principles / build-vs-buy) or Amazon (ops/blast radius)
4. Two options remain viable after local references

Append findings to `10-interview-transcript.md` under `## Research Findings -- Phase 4`.
