# High-Level Design — Trending Articles / Top-K

## Architecture Evolution (Start Cheap)

| Version | Scale trigger | Architecture | Why |
|---------|---------------|--------------|-----|
| **v0** | <1K peak write QPS | Postgres + cron `GROUP BY` every 5 min | Handles launch scale; single-node Postgres ~1K indexed writes/s |
| **v1** | >10K write QPS | Kafka buffer + single Flink consumer + Redis | Postgres write path breaks; need async ingestion |
| **v2** | >50K write QPS (current) | Partitioned Kafka + Flink keyed state + CMS + Redis push | Current design; sketch bounds memory |
| **v3** | >500K write QPS (10×) | Sharded aggregation + two-phase global top-K merge | Single-partition hot keys dominate |

**Selected:** v2 for 50K peak write QPS / 230K read QPS. v0 is valid for MVP — we do not skip it.

## Contested Decision: Stream Processor — Flink vs Samza vs Batch

| | Flink | Samza | Batch (Spark hourly) |
|---|-------|-------|----------------------|
| Freshness | Sub-minute | Sub-minute | 15+ min |
| Ops complexity | Medium | Medium (Kafka-native) | Low |
| State recovery | Checkpoint 5–15 min | Kafka changelog | N/A |
| **Forces** | Rich windows, large community | LinkedIn production default | 7d window only |

**Selected:** Flink for generic design; Samza equivalent at LinkedIn.

- **Solves:** 60s freshness for 1h window at 50K events/s with windowed state.
- **Worsens:** Operational burden (checkpoint lag, state size); recovery 5–15 min for 50GB state.
- **When to change:** If freshness relaxes to 15 min for all windows → batch + materialized views is cheaper.

## System Overview

```
WRITE PATH (50K peak QPS)                    READ PATH (230K peak QPS)
─────────────                                ─────────────

[Feed/Engagement Svcs]                       [Mobile/Web]
        │ HTTP/gRPC                                   │ HTTPS
        ▼                                             ▼
[Ingestion API] ──50K QPS──► [Kafka]          [LB] ──230K QPS──► [Trending API]
        │                      │ 7d retention          │
        │                      ▼                       ▼
        │               [Flink Job]              [Redis Cluster]
        │               CMS + top-K                   │ ZREVRANGE
        │                      │                       │
        └──── abuse gates ─────┘                       └── P99 < 50ms
                               │
                               ▼ push 2K QPS
                         [Redis ZSET per segment]
```

## Flow 1: Write / Data Path

1. **Engagement service → Ingestion API** (gRPC, ~5 ms): validate schema, `event_id` dedupe (Redis SET 24h TTL).
2. **Abuse gates** (~2 ms): user reputation > 0.3, not on bot list, content quality > 0.5.
3. **Ingestion → Kafka** (async produce, acks=all, ~10 ms): partition key = `hash(content_id)`.
4. **Flink source** (consume, ~5 ms lag): keyed by `(content_id, segment)`.
5. **Process:** CMS update + heap top-K (~1 ms amortized per event).
6. **Sink → Redis** (batched ZADD every 30s per segment, ~2K Redis write QPS).

**Durable at:** Kafka (7d) + Flink checkpoint (S3) + Redis (ephemeral serving copy).

## Flow 2: Read / Query Path

| Hop | Component | Protocol | Latency budget |
|-----|-----------|----------|----------------|
| 1 | Client → LB | HTTPS | 8 ms |
| 2 | LB → API | HTTP/2 | 7 ms |
| 3 | API → Redis | TCP same-AZ | 5 ms |
| 4 | Redis ZREVRANGE | — | 3 ms |
| 5 | Serialize response | — | 5 ms |
| 6 | Tail buffer | — | 22 ms |
| | **Total P99** | | **50 ms** |

Cache hit ratio >99%; miss → return stale empty segment with `Retry-After` (degrade gracefully).

## Flow 3: Failure and Degradation

### Failure: Redis cluster partition unavailable

- **User impact:** Trending API returns **stale cached list** from local API pod cache (30s TTL) or HTTP 503 with last-known-good ETag.
- **Degradation:** Stale-while-revalidate; feed core unaffected.
- **Recovery:** Redis Sentinel failover ~30s; no thundering herd — jittered client retry 100–500 ms.
- **Stampede avoidance:** Singleflight per segment key in API tier.

### Failure: Flink job crash mid-checkpoint

- **User impact:** Trending lists **freeze** for 5–15 min; last Redis snapshot served.
- **Degradation:** Stale top-K acceptable per NFR (60s SLA breached — incident).
- **Recovery:** Restart from S3 checkpoint; replay Kafka from offset; idempotent ZADD to Redis.
- **Stampede avoidance:** Hot standby job for 1h window only (2× cost critical path).

## Flow 4: Deploy and Migration

- **API:** Canary 5% → 25% → 100% on k8s; rollback via deployment revision.
- **Flink:** Savepoint → deploy new job version → resume; dual-run 1 checkpoint interval for validation.
- **Schema migration:** Kafka schema registry (Avro); backward-compatible readers for 2 weeks.
- **Rollback:** API instant; Flink restore previous savepoint (<10 min).

## Component Registry

| Component | Capacity | Failure mode | Owner |
|-----------|----------|--------------|-------|
| Ingestion API | 50K QPS writes | Overload → 429 + client backoff | Product Platform |
| Kafka (`trending-events`) | 50K QPS, 200 partitions | Broker loss → ISR elect leader | Data Platform |
| Flink aggregation job | 50K QPS events, 50 GB state | Job fail → stale Redis 5–15 min | Real-time Infra |
| Redis Cluster | 230K QPS reads, 30 GB | Node loss → replica promote | Caching Platform |
| Trending API | 230K QPS reads | Pod crash → LB drain | Product API |

## Technology Trade-off Triads

### Kafka (event buffer)

- **Solves:** Decouples 50K/s bursty writes from aggregation; replay on failure.
- **Worsens:** 10–50 ms produce latency; partition hot spots on viral `content_id`.
- **When to change:** <1K write QPS → Postgres outbox sufficient.

### Count-Min Sketch (approximate counting)

- **Solves:** Sublinear memory vs billions of content keys; 30 GB vs terabytes for exact hash maps.
- **Worsens:** ±5% overcount; merge constraints with conservative updates.
- **When to change:** Exact billing counts required → OLAP path, not trending.

### Redis sorted sets (serving)

- **Solves:** O(log N + K) top-K read at 230K QPS with sub-ms latency.
- **Worsens:** Memory per segment; hot key on global list.
- **When to change:** 10× read QPS → local CDN edge cache + read replicas.

```sql
-- v0 start-cheap aggregation (cron every 5 min)
SELECT content_id, SUM(weight) AS score
FROM engagement_events
WHERE ts > NOW() - INTERVAL '1 hour'
GROUP BY content_id
ORDER BY score DESC LIMIT 100;
```

```python
# Redis top-K read path
ZREVRANGE trending:1h:US:tech 0 49 WITHSCORES
```


- **LinkedIn Samza:** Kafka-backed keyed RocksDB state for real-time aggregation; we mirror this with Flink + checkpointed state. Recovery time drove hot-standby for 1h window.
- **Twitter trending (~2019):** Velocity-weighted scoring + manipulation response; informed abuse gate ordering before count.
- **YouTube trending:** Freshness bias + quality gates; we use time-decay and content-quality filter similarly.
