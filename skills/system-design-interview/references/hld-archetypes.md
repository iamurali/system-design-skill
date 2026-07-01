# HLD Problem Archetypes

Use at Phase 4 **before** choosing components. Every interview prompt maps to
one or two archetypes. Archetypes describe **forces and capability candidates** —
not products.

---

## Quick classifier

```
                    ┌─────────────────────────────────────┐
                    │  What is the dominant access pattern? │
                    └─────────────────┬───────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         ▼                            ▼                            ▼
   Point read/write              Scan / feed / list            1 write → N readers
   (get by key)                  (range, cursor)               (fanout)
         │                            │                            │
    A1 CRUD                   A2 Feed / timeline              A5 Fanout / realtime
    A3 Read-scaled            A4 Search / discovery           A6 Chat / presence
         │                            │
         │                     High write rate + windows?
         │                            │
         │                       A7 Aggregate / meter
         │                       (counters, rate limit, top-K)
         ▼
   Large blobs? → A8 Media / object
   Strong invariants? → A9 Ledger / coordination
```

---

## A1 — Point CRUD (key-value entity)

**Examples:** URL shortener, user profile, product catalog, session store.

| Force | Typical signal |
|-------|----------------|
| Dominant | GET/PUT by primary key |
| v0 | Monolith + single SQL or KV |
| First scale break | Read QPS or storage size |

**Capability candidates (not all required):**

| Capability | Consider when |
|------------|---------------|
| L3 cache | R:W > 10:1, P99 < 50ms |
| L4 sharding | Working set > one node |
| L6 ID service | Non-guessable IDs at scale |
| L5 write buffer | Rare unless async side effects |

**v0 topology:** `[Client] → [API] → [Primary store]`

**Common research topics:** SQL vs KV; cache-aside vs read-through; shard key.

**Exemplar HLD:** `assets/exemplars/url-shortener/06-high-level-design.md`

---

## A2 — Feed / timeline (ordered lists)

**Examples:** News feed, activity stream, inbox.

| Force | Typical signal |
|-------|----------------|
| Dominant | Per-user ordered list, cursor pagination |
| v0 | Fan-out on write or fan-out on read (pick one) |
| First break | Celebrity fanout or read QPS |

**Capability candidates:**

| Capability | Consider when |
|------------|---------------|
| Precomputed fan-out | Many followers, acceptable write amp |
| Pull/merge on read | Few active users, simpler ops |
| L3 cache | Hot users |
| L5 async fan-out workers | Write path too slow sync |

**Common research topics:** push vs pull; hybrid (push for normal, pull for celebs).

**Not the same as A7** — feed is per-user ordering, not global ranking.

---

## A3 — Read-scaled serving

**Examples:** Distributed cache, CDN-backed API, read replicas.

| Force | Typical signal |
|-------|----------------|
| Dominant | Extreme read QPS, tolerant staleness |
| v0 | Single cache node or DB replica |
| First break | Memory, hot keys, cross-AZ latency |

**Capability candidates:** L3 multi-tier cache, L1 local cache, L2 proxy/sharding, replication.

**Exemplar HLD:** `assets/exemplars/in-memory-cache/06-high-level-design.md`

---

## A4 — Search / discovery

**Examples:** Autocomplete, full-text search, geo search.

| Force | Typical signal |
|-------|----------------|
| Dominant | Fuzzy match, ranking, indexes unlike primary DB |
| v0 | DB LIKE / prefix index (low scale) |
| First break | Index size, query latency |

**Capability candidates:** inverted index, search engine (L7), async indexing pipeline (L5).

---

## A5 — Fanout / realtime delivery

**Examples:** Notifications, live scores, websocket push.

| Force | Typical signal |
|-------|----------------|
| Dominant | 1 event → millions of deliveries |
| v0 | Poll API (tiny scale) |
| First break | Delivery QPS, connection count |

**Capability candidates:** pub/sub, push gateways, connection pools, partial failure handling.

---

## A6 — Chat / presence

**Examples:** 1:1 chat, group chat, online status.

| Force | Typical signal |
|-------|----------------|
| Dominant | Ordering per channel, delivery guarantees |
| v0 | Single room server + store |
| First break | Cross-region, group size, message rate |

**Capability candidates:** ordering service, presence heartbeats, conflict resolution.

---

## A7 — Aggregate / meter / windowed compute

**Examples:** Rate limiter, view counters, **top-K / trending**, metrics rollups.

| Force | Typical signal |
|-------|----------------|
| Dominant | Many writes, few read queries over aggregates |
| v0 | DB counters + cron (low QPS) |
| First break | Write TPS, freshness SLA, cardinality |

**Capability candidates:**

| Capability | Consider when |
|------------|---------------|
| L5 write buffer | Write spikes |
| Stream / incremental compute | Freshness < batch interval |
| Approximate structures | Cardinality >> memory |
| Materialized serving view | Read QPS high on aggregate |

**Only use this archetype if requirements include aggregation.** Do not assume A7 for every prompt.

**Exemplar HLD:** `assets/exemplars/trending-articles-top-k/06-high-level-design.md` (aggregation-specific)

---

## A8 — Media / large object

**Examples:** Image/video upload, file storage, backups.

| Force | Typical signal |
|-------|----------------|
| Dominant | Multi-MB+ objects, bandwidth |
| v0 | App server disk (dev only) |
| First break | Storage cost, upload concurrency |

**Capability candidates:** blob store (L4), CDN (L2), multipart upload, metadata DB separate from blobs.

---

## A9 — Ledger / strong coordination

**Examples:** Payments, inventory, reservations, distributed locks.

| Force | Typical signal |
|-------|----------------|
| Dominant | Invariants, no double-spend |
| v0 | Single DB transactions |
| First break | Throughput vs strong consistency |

**Capability candidates:** 2PC/saga, consensus, idempotency keys, audit log.

---

## Hybrid prompts

Many problems combine archetypes:

| Prompt | Primary | Secondary |
|--------|---------|-----------|
| News feed | A2 Feed | A3 Read-scaled |
| URL shortener + analytics | A1 CRUD | A7 Aggregate (async) |
| Chat | A6 Chat | A5 Fanout |
| Rate limiter | A7 Aggregate | A3 Cache (token bucket in memory) |

List primary + secondary in HLD Section 1. Design **primary path first**; add secondary capabilities only if requirements demand.

---

## Archetype → building blocks (coverage hint)

After classification, scan `building-blocks-index.md` for layers marked **consider** on your archetype card. Explicitly **defer** layers not on the card with one line each in HLD.
