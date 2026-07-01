# High-Level Design — URL Shortener

> **Archetype A1 (Point CRUD), read-heavy.** Generic HLD exemplar — not a streaming/top-K design.

## Problem Shape Classification

| Signal | Value | Implication |
|--------|-------|-------------|
| Read QPS / Write QPS | 12K / 120 peak | 100:1 read-heavy → optimize read path first |
| P99 latency | 100 ms redirect | Hot path is read + HTTP 302 |
| Consistency | Eventual for analytics | Redirect must be correct; clicks can lag |
| Dominant force | Sub-100ms redirect at 12K read QPS | Cache + shard before async pipeline |

**Primary archetype:** A1 Point CRUD  
**Secondary:** none (analytics optional, out of scope)

## Required Capabilities

| Capability | Layer | Trigger | Status |
|------------|-------|---------|--------|
| Redirect API | L1/L7 | 12K read QPS | **now** |
| Primary mapping store | L4 | Durable short→long URL | **now** |
| Read cache | L3 | R:W 100:1, P99 100ms | **now** at 1× |
| ID generation | L6 | Non-guessable short keys | **now** |
| Sharded data plane | L4 | >8K read QPS per shard | **defer** until 10× |
| Write buffer / stream | L5 | 120 write QPS | **skip** — sync write OK |
| Aggregate / top-K | — | Not in requirements | **skip** |

## Architecture Evolution (Start Cheap)

| Version | Trigger | Added | Deferred |
|---------|---------|-------|----------|
| v0 | 1× (12K/120 QPS) | Monolith + Postgres + app cache | Sharding, separate cache tier |
| v1 | 10× read (120K QPS) | Distributed cache + read replicas | Sharding |
| v2 | 100× or 1B rows | Shard by `short_key` hash | — |

**Breaking point:** Single Postgres primary saturates ~1K–2K indexed read QPS → v1 adds cache.

**Selected:** v0 with L1 cache in API pods; plan v1 cache cluster at 10×.

## Architecture Research

### Research: Primary mapping store (L4)

| Option class | Fits | Fails when | Ops / recovery | Verdict |
|--------------|------|------------|----------------|---------|
| Relational (Postgres) | ACID, simple ops | >2K hot read QPS on primary | Replica failover | **Selected** v0 |
| Wide-column / KV | Massive partition scale | Overkill at 1B URLs with 12K QPS | Tunable per product | Defer to 100× |
| In-memory only | Fast | Durability loss | N/A | Reject |

**Selected:** Postgres — **120 write QPS** and **12K read QPS** with cache fit single primary + replicas.

### Research: Read path acceleration (L3)

| Option class | Fits | Fails when | Ops / recovery | Verdict |
|--------------|------|------------|----------------|---------|
| App-local cache | 12K QPS, tiny values | Pod restart cold | N/A | **Selected** v0 |
| Distributed cache cluster | 120K+ QPS | Ops at low scale | Failover to DB | v1 |
| CDN edge cache | Public redirects | Invalidation on delete | TTL stale risk | Optional v1 |

**Selected:** App-local LRU + DB fallback — meets **P99 100ms** without extra tier at 1×.

## System Overview

```
[Client] ──HTTPS──► [Redirect API] ──► [Read cache (local)]
                           │ miss
                           ▼
                    [Primary store (Postgres)]
                           ▲
[Create API] ──HTTPS───────┘  (write path, low QPS)
```

## Flow 1: Write / Data Path

1. Client → Create API (HTTPS, ~20 ms): validate URL, auth optional.
2. Generate `short_key` via base62 + uniqueness check (~5 ms).
3. INSERT into primary store (~15 ms) — **durable at commit**.

## Flow 2: Read / Query Path

| Hop | Role | Protocol | Latency budget |
|-----|------|----------|----------------|
| 1 | Client → edge/LB | HTTPS | 15 ms |
| 2 | Redirect API | — | 10 ms |
| 3 | Local cache hit | in-proc | 1 ms |
| 3b | Cache miss → DB | SQL | 40 ms (amortized) |
| 4 | 302 response | — | 5 ms |
| 5 | Tail | — | 29 ms |
| | **Total P99** | | **100 ms** |

## Flow 3: Failure and Degradation

### Failure: Primary store unavailable

- **User impact:** Creates fail 503; redirects serve from cache only (stale OK for TTL).
- **Degradation:** Read-only mode for cached keys.
- **Recovery:** Failover to replica ~30s.
- **Stampede:** Singleflight on cache miss per key.

### Failure: API pod loss

- **User impact:** Brief errors on that pod.
- **Degradation:** LB routes to healthy pods; cold cache → higher DB load.
- **Recovery:** K8s replace pod.
- **Stampede:** Jittered retry; DB connection pool limits.

## Flow 4: Deploy and Migration

- Rolling deploy 10% steps; backward-compatible API.
- Schema: additive columns only; expand-contract for index changes.
- Rollback: previous deployment revision.

## Component Registry

| Role | Implementation | Capacity | Failure mode | Owner |
|------|----------------|----------|--------------|-------|
| Redirect API | Go service, 8 pods | 12K QPS reads | Pod crash → LB drain | Edge team |
| Create API | Same service | 120 QPS writes | Same | Edge team |
| Primary store | Postgres | 12K QPS cached reads | Primary down → replica | Data team |
| Read cache | In-process LRU | 80% hit target | Cold start → DB spike | Edge team |

## Technology Trade-off Triads

### Postgres primary store

- **Solves:** 120 write QPS, ACID, simple ops.
- **Worsens:** Vertical read ceiling ~2K QPS uncached.
- **When to change:** 10× read QPS → distributed cache + replicas.

### App-local cache

- **Solves:** P99 100ms at 12K QPS without Redis cluster.
- **Worsens:** Per-pod inconsistency on delete (TTL 60s acceptable).
- **When to change:** 120K QPS → shared cache tier.

### Base62 short keys

- **Solves:** Compact URLs, no coordination at low write rate.
- **Worsens:** Collision check on insert.
- **When to change:** >10K write QPS → distributed ID service.

## Production References

- **Cache stampede (Facebook 2010):** singleflight on miss informed read path.
- **Read replica lag:** redirect tolerates stale cache; create/delete invalidate explicitly.
