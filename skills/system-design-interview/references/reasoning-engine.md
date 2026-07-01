# Reasoning Engine -- The 6-Phase Design Loop

The loop turns a vague prompt into a justified, stress-tested architecture. It
is iterative: later phases routinely force revisions to earlier ones. The
thinking IS the deliverable, not the final diagram.

> Do not memorize architectures; learn the forces that shape them.

---

## The 6 Phases

### Phase 1: Frame the Problem (5-8 min)

**Output**: `01-requirements.md`
**Template**: `assets/templates/01-requirements.template.md`
**References**: `numbers-to-know.md`, `faang-interview-patterns.md`

Turn the vague prompt into functional requirements, **full capacity estimation chain**,
growth trajectory (1×/10×/100×), success metrics, and explicit out-of-scope.
Scope to 2-4 core features and say so.

**What to clarify before drawing anything:**
- Who are the users? How many? Growth trajectory?
- Read-heavy or write-heavy? What ratio?
- Consistency tolerance? Can users see stale data for seconds? Minutes?
- Latency SLA? Sub-100ms? Sub-second?
- Existing stack to integrate with?
- Regulatory or privacy constraints?

**PE protocol**: Do not just clarify -- reframe. Question whether the stated
problem is the right problem. Surface hidden requirements. Propose alternative
scopes that reveal domain judgment.

### Phase 2: Set the Constraints (3-5 min)

**Output**: `02-non-functional-requirements.md`

Quantify everything. Convert "high traffic" into numbers that force architecture.

**Estimation chain** (read `numbers-to-know.md` for reference data):
```
DAU × actions/user/day ÷ 86,400 = average QPS
average QPS × peak_factor (≈2x) = peak QPS
writes/day × avg_object_size = storage/day
storage/day × retention_days = total storage
QPS × payload_size = bandwidth (separate read/write)
peak_QPS ÷ per_server_QPS = server count
```

**Beyond the numbers**: Percentile latency targets (not just averages),
availability with error budget math, consistency model with justification,
durability guarantees by failure class, operational requirements (deploys,
monitoring, runbooks).

### Phase 3: Define the Interface (5-7 min)

**Output**: `03-entities.md`, `04-api-design.md`, `05-schema.md`

Make the design concrete before going to architecture. If you cannot write the
request, response, and primary key, the diagram is guesswork.

**Entities**: Domain objects, relationships, cardinality, lifecycle/state
machines.

**API**: Exact endpoints with request/response shapes. Pagination (cursor-based
at scale). Idempotency keys for mutations. Versioning strategy. Error contract.

**Schema**: Primary keys, sort keys, indexes -- each justified by an access
pattern. Partitioning strategy tied to capacity numbers. Denormalization
decisions justified by read/write ratio.

### Phase 4: Design the Architecture (10-15 min)

**Output**: `06-high-level-design.md`
**Template**: `assets/templates/06-high-level-design.template.md`
**References**: `building-blocks-index.md`, `tradeoff-framework.md`, `faang-interview-patterns.md`

**Mandatory order:** Architecture Evolution (start cheap) → contested decision options →
four flows (write, read with latency budget, failure, deploy) → component registry →
trade-off triads.

Start cheap. A single DB, a monolith, no cache. This works at small scale.

Incrementally optimize: capacity numbers from Phase 2 reveal bottlenecks.
Add components only when a number forces them. Each addition gets the
trade-off triad (read `tradeoff-framework.md`):
- What does it solve?
- What does it make worse?
- What would make me change it?

Use `building-blocks-index.md` to select components from the right layer.
Cite production system references where the design mirrors or diverges from
real systems.

**PE protocol**: For the most contested decision, present 2-3 architecture
options with the forces that pick between them. Make the selection a judgment
call, not a default.

### Phase 5: Go Deep (10-15 min)

**Output**: `07-deep-dives.md`

Pick 3-5 components that are most interesting or most fragile. For each:

**Solution tiers**:
- **Workable**: Solves the problem. State the limitations.
- **Strong**: Addresses those limitations. State new challenges.
- **Exceptional**: PE-grade insight. Novel optimization, elegant
  simplification, or a non-obvious connection.

Each tier includes a **Challenges** section. The reader should understand why
you might choose a simpler tier over a more sophisticated one.

**Curveball handling**: For each deep dive, include a "what if" scenario:
1. Name the constraint change ("writes go 10x").
2. Name the assumption it invalidates ("single-partition aggregation").
3. Redesign only the affected part ("shard the aggregation by key hash").

### Phase 6: Stress-Test and Synthesize (5-8 min)

**Output**: `08-bottlenecks-and-tradeoffs.md`

**Bottleneck analysis**: Each bottleneck with root cause, mitigation options,
and a real-world incident example.

**Tradeoff summary matrix**: The key decisions in tabular form.

**Coverage sweep**: Scan the building blocks index. For each block that is
plausibly relevant but was not used, state one line: why it was excluded.
Blocks commonly missed: `blob-store`, `sequencer`, `dns`, `observability`,
`distributed-logging`, `distributed-search`, `task-scheduling`,
`sharded-counters`, `service-decomposition`.

**Evolution strategy**: What changes at 10x and 100x. Which assumptions
break. What to rebuild vs extend.

**Self-assessment**: Score against the PE rubric (read
`principal-engineer-bar.md`). Name the weakest dimension. State what would
fix it.

---

## Time Budget (~45 min interview)

| Phase | Minutes | Focus |
|-------|---------|-------|
| 1 -- Frame | 5-8 | Requirements, scope, reframing |
| 2 -- Constraints | 3-5 | Numbers, NFRs (woven into Phase 1 in fast delivery) |
| 3 -- Interface | 5-7 | Entities, API, schema |
| 4 -- Architecture | 10-15 | HLD, incremental optimization, tradeoffs |
| 5 -- Depth | 10-15 | Deep dives on 2-3 components |
| 6 -- Synthesis | 5-8 | Bottlenecks, evolution, wrap-up |

Trade-off articulation and failure mode analysis are woven through Phases 4
and 5, not a separate time block. Spend more time on phases where the problem
is most interesting.

---

## The 10 Failure Modes

These are the reasons strong engineers get rejected. None is "the design was
wrong." They are signal failures -- the design may be fine, but the reasoning
is not visible or not sound.

### The modes

1. **Weak distributed-systems fundamentals.** Cannot explain
   consistency/replication tradeoffs when a partition happens.
2. **Opaque building blocks.** Names a cache/queue/DB without knowing how it
   behaves under spike or failure.
3. **Rushing to design.** Applies a familiar solution to an unread problem.
   When load doubles, says "add more servers" instead of diagnosing the
   bottleneck.
4. **Name-dropping without tradeoffs.** Lists technologies without context.
   "We use Kafka" is not a justification.
5. **No sense of scale.** "High traffic" is meaningless. 1K and 1M QPS are
   different systems.
6. **Ignoring failure.** Designs assume infinite uptime. "More retries"
   amplifies outages.
7. **Over-indexing on the canonical answer.** Treats Kafka/sharding as defaults
   regardless of prompt. Small constraint change collapses the design.
8. **Vague interfaces.** "NoSQL" box with no primary key or access patterns.
   "Fetch the feed" with no API contract.
9. **Presenting, not collaborating.** Monologue. Defends every challenge as an
   attack.
10. **Cannot course-correct.** Sunk-cost defense of outdated assumptions when
    constraints change.

### Self-check protocol

Before finalizing any design, verify:

- [ ] Requirements stated (FR + NFR + out-of-scope) before designing?
- [ ] Peak QPS, storage, growth estimated? Numbers drove decisions?
- [ ] Request/response, keys, pagination are concrete?
- [ ] Each major choice: solves / worsens / when-to-change?
- [ ] Read and write paths handled deliberately and separately?
- [ ] Every SPOF identified? Degradation story? Recovery without stampede?
- [ ] Behavior at 10x/100x known?
- [ ] All relevant building blocks addressed or explicitly deferred?
- [ ] Design adapts to constraint changes without collapsing?
- [ ] Tone is collaborative, not defensive?

---

## Coverage Sweep Checklist

Before wrapping, scan these building blocks against the in-scope features.
For each relevant one not addressed, either incorporate it or defer with a
one-line reason.

| Block | Question to Ask |
|-------|----------------|
| `dns` | How do clients resolve the service? Geo/failover routing? |
| `load-balancing` | How is traffic distributed? L4 or L7? Health checks? |
| `content-delivery` | Is there static/media content served at the edge? |
| `api-design` | Are API contracts concrete? Pagination? Idempotency? |
| `service-decomposition` | Monolith or microservices? What drives the split? |
| `data-storage` | SQL or NoSQL? Sharding? Replication? |
| `caching` | Is the read path hot enough to justify a cache? |
| `blob-store` | Are there large objects (images, video, files)? |
| `sequencer` | Are unique IDs needed? UUID, Snowflake, or ticket? |
| `sharded-counters` | Are there high-write counters (views, likes)? |
| `distributed-search` | Is full-text search or autocomplete needed? |
| `messaging-streaming` | Is there async work? Queues vs streams? |
| `task-scheduling` | Are there background, scheduled, or recurring jobs? |
| `consistency-coordination` | Is consensus, ordering, or coordination needed? |
| `resilience-failure` | What are the SPOFs? Degradation story? |
| `observability` | What metrics, logs, traces? SLOs? Alerting? |
| `distributed-logging` | Is there a high-volume log pipeline? |
| `scaling-evolution` | What is the next bottleneck? 10x/100x plan? |

---

## Curveball Handling Protocol

When a constraint changes mid-design:

1. **Acknowledge** the change explicitly.
2. **Name** the assumption it invalidates.
3. **Scope** the blast radius -- which components are affected.
4. **Redesign** only the affected part.
5. **Verify** the rest of the design still holds.

Example: "10x writes invalidates our assumption that a single Flink task can
hold the aggregation state. The ingestion path and serving path are unaffected.
We shard the aggregation by video-ID hash across N task slots, with a merge
step that combines per-shard top-K lists into a global top-K."

A design that collapses entirely under a small change was memorized. A reasoned
design bends locally.
