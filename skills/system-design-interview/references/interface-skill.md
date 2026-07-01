# Interface Skill — Entities, API, Schema as One System

This is the **complete Phase 3 skill**. Three output files — but **one design
pass**: access patterns drive entities, APIs, and storage together.

```
Access patterns (from Phase 1–2) → entities + lifecycles → API contracts →
schema / indexes / shard key
```

Read this file at the start of Phase 3. Outputs:

- `03-entities.md`
- `04-api-design.md`
- `05-schema.md`

Templates: `assets/templates/03-entities.template.md`,
`04-api-design.template.md`, `05-schema.template.md`.

Load `references/building-blocks-index.md` (L4 storage vocabulary) when choosing
store **class** — not product names in schema section unless exemplar depth
requires it.

---

## Phase 3 entry checklist

1. List **top 3–5 access patterns** from Phase 1 FRs with QPS from capacity chain.
2. For each pattern: read or write? Latency budget from Phase 2?
3. Define **entities** with cardinality and lifecycle.
4. Design **APIs** — every endpoint has request **and** response shape.
5. Design **schema** — every API pattern has index or scan strategy.
6. Choose **partition / shard key** from **write QPS** and access locality.
7. Cross-check: no API field without entity home; no hot query without index.

---

## Section 1: Access pattern inventory

Complete before entities.

| ID | Pattern | Type | Peak QPS | P99 budget | Consistency |
|----|---------|------|----------|------------|-------------|
| AP-1 | e.g. GET by key | read | | ms | |
| AP-2 | | write | | | |

### Shape-specific pattern catalogs

**A1 Point CRUD**

| Pattern | API sketch | Schema implication |
|---------|------------|-------------------|
| Get by ID | `GET /v1/{id}` | PK lookup |
| Create | `POST /v1/` | Unique constraint on natural key |
| Update | `PUT/PATCH` | Row lock or version field |

**A2 Feed**

| Pattern | API sketch | Schema implication |
|---------|------------|-------------------|
| User timeline | `GET /feed?cursor=` | Per-user list store or fanout index |
| Publish | `POST /post` | Fanout write or async job |

**A7 Aggregate**

| Pattern | API sketch | Schema implication |
|---------|------------|-------------------|
| Ingest event | `POST /events` async | Append log, idempotent key |
| Query top-K | `GET /trending` | Precomputed segment key |

**A3 Cache**

| Pattern | API sketch | Schema implication |
|---------|------------|-------------------|
| GET/SET key | gRPC/Redis protocol | Key namespace, TTL metadata |

Pick only patterns **in scope** for this problem.

---

## Section 2: Entities (`03-entities.md`)

### Entity card template

For each core entity:

| Field | Type | Description |
|-------|------|-------------|
| | | |

Include:

- **Cardinality** — orders of magnitude (1B users, 10M posts/day).
- **Relationships** — 1:N, N:M; avoid over-normalizing at scale.
- **Lifecycle** — created → active → archived → deleted.
- **Identity** — natural key vs surrogate ID; global uniqueness needs.

### State machines (mandatory when states exist)

Entities with workflow (order, upload, invitation) need explicit states:

```
[draft] → [published] → [archived]
              ↓
          [deleted]
```

Gate 3 requires state machines for multi-state entities.

### Shape notes

| Shape | Entity focus |
|-------|--------------|
| A1 | Few core entities, ID-centric |
| A2 | Actor, content, edge (follow), inbox |
| A7 | Event, aggregate score, segment/window config |
| A9 | Account, transaction, ledger entry (immutable) |

---

## Section 3: API design (`04-api-design.md`)

### Contract rules

- **Concrete shapes** — JSON or protobuf fields, not "returns data."
- **HTTP semantics** — correct status codes (201, 202, 404, 409, 429).
- **Versioning** — `/v1/` prefix or header strategy.
- **Pagination** — cursor-based at scale; offset only for tiny lists.
- **Idempotency** — `Idempotency-Key` or natural id for writes.
- **Error contract** — stable error codes + retry guidance.

### Per-endpoint template

```
METHOD /v1/resource
Headers: ...

Request:
{ ... }

Response: 200 OK
{ ... }
```

### Rate limiting (tie to Phase 1)

| API class | Limit basis | Backpressure |
|-----------|-------------|--------------|
| Public read | per user + global | 429 + Retry-After |
| Write | per user | 429 |
| Internal ingest | per caller service | 429 / queue |

### Internal vs external

Split APIs when QPS or auth differs (e.g., high-throughput internal ingest vs
public query).

---

## Section 4: Schema (`05-schema.md`)

**Access patterns drive schema.** Denormalize when read:write and join cost
justify it — cite Phase 1 ratio.

### For relational / KV row stores

| Table / collection | PK | SK / sort | Indexes | Serves AP- |
|--------------------|----|-----------|---------|-----------|
| | | | | |

### For logs / streams (only if shape requires)

Topic, partition key, retention, schema evolution — tie to ingest AP.

### For derived stores (cache, search, aggregate)

Key structure, TTL, update path — tie to read AP.

### Sharding / partitioning (mandatory)

| Key | Rationale | Hot spot risk |
|-----|-----------|---------------|
| | Traces to write QPS from Phase 1 | |

Rules:

- Shard by **highest write rate** dimension unless read locality dominates.
- Call out **hot keys** (celebrity, viral content, global counter).
- Mitigation sketch (isolate shard, local aggregate, split key).

### Index cost analysis (PE signal)

For each non-PK index:

- Write amplification on ingest QPS
- Storage overhead
- Why query cannot use PK alone

---

## Section 5: Cross-file alignment gate

Before leaving Phase 3, verify:

| Check | Pass condition |
|-------|----------------|
| API ↔ Entity | Every request field maps to entity or derived view |
| API ↔ Schema | Every query has index, PK, or bounded scan |
| QPS ↔ Shard | Shard key handles peak write QPS |
| NFR ↔ API | P99 path hop count matches Phase 2 budget |
| Shape ↔ Complexity | No event pipeline schema for pure A1 CRUD |

---

## Phase 3 quality signals

- Pagination cursors for large lists.
- Idempotency on non-read APIs that can retry.
- Shard key is a **choice with tradeoff**, not default `user_id`.
- State machines where workflow exists.

---

## Exemplar selection (optional)

| Shape | Read one file per sub-phase |
|-------|----------------------------|
| A3 | `assets/exemplars/in-memory-cache/03–05` |
| A7 | `assets/exemplars/trending-articles-top-k/03–05` |
| A1 / other | **Skill + templates** |

---

## Handoff — Context Checkpoint

After Gate 3, orchestrator builds checkpoint. Phase 3 contributes:

- Core entities + cardinality
- Top 3–5 access patterns with QPS
- Shard / partition key
- Critical indexes

Phases 4–6 use checkpoint — do not re-read full 01–05.
