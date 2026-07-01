# High-Level Design — Trending Articles / Top-K

> **Exemplar note:** This file shows **one researched outcome** for this problem.
> Do not copy Kafka/Flink/Redis into other designs. Copy the **process**:
> capabilities → research → selection → flows.

## Required Capabilities

| Constraint (number) | Required capability | Layer | Mandatory when |
|---------------------|---------------------|-------|----------------|
| 50K peak write QPS, burst | Durable write buffer; decouple producers from aggregators | L5 messaging | Write path > ~1K TPS sustained |
| 60s freshness on 1h window | Windowed incremental aggregation + recoverable state | L5 stream processing | Freshness < batch interval (5 min) |
| 230K read QPS, P99 50ms | Pre-materialized ranked lists; sub-ms reads | L3 cache / L4 KV store | Read QPS > ~10K from DB |
| Billions of keys, ±5% error OK | Approximate frequency / top-K (sketch or Space-Saving) | Algorithm | Exact counters infeasible |
| 7d event retention, RPO 0 | Replayable durable log | L5 messaging | Cannot lose engagement events |

## Architecture Evolution (Start Cheap)

| Version | Scale trigger | Capabilities | Deferred | Why |
|---------|---------------|--------------|----------|-----|
| **v0** | <1K peak write QPS | RDBMS + cron aggregation | Log, stream, distributed cache | Postgres ~1K indexed writes/s |
| **v1** | >10K write QPS | + durable event log | Stream processor, sketch | Write path saturates DB |
| **v2** | >50K write QPS (current) | + stream aggregator + ranked store + sketch | Global merge sharding | Freshness + memory bounds |
| **v3** | >500K write QPS (10×) | + sharded aggregation + two-phase top-K merge | — | Hot partition on single key |

**Selected:** v2 for 50K write / 230K read QPS.

## Architecture Research

### Research: Durable write buffer (L5)

| Option | Fits forces | Breaks when | Ops / failure | Verdict |
|--------|-------------|-------------|-----------------|---------|
| DB write-behind / outbox | Simple, strong ordering | >5K write QPS | DB becomes bottleneck | Reject at current scale |
| Managed log (Kafka, Pulsar, Kinesis) | 50K+ QPS, replay, retention | Ops complexity | ISR / broker failover patterns known | **Selected** — replay + 7d retention |
| Direct HTTP to aggregator | Lowest latency | No burst absorption | Loses events on crash | Reject — RPO violation |

**Selected:** Kafka-class log — **50K peak write QPS** requires decoupling; outbox insufficient.

### Research: Windowed aggregation (L5)

| Option | Fits forces | Breaks when | Ops / failure | Verdict |
|--------|-------------|-------------|-----------------|---------|
| Cron + SQL (v0) | Simple | Freshness > 5 min | N/A | Reject — 60s SLA |
| Spark micro-batch (1–5 min) | Cheaper ops | 1–5 min staleness | Job restart delay | Reject for 1h window |
| Flink / Samza / managed stream | Sub-minute, keyed state | State size, checkpoint time | 5–15 min recovery at 50GB | **Selected** for 1h window |
| In-process counters only | Fast | No durability | Process crash = loss | Reject |

**Selected:** Flink (Samza equivalent at LinkedIn) — **60s freshness** at 50K events/s.

### Research: Ranked read serving (L3/L4)

| Option | Fits forces | Breaks when | Ops / failure | Verdict |
|--------|-------------|-------------|-----------------|---------|
| Read-through Postgres | Strong consistency | >1K read QPS | DB overload | Reject at 230K QPS |
| Application in-memory cache | Fast | Cold start, per-pod inconsistency | Pod loss | Partial — L1 only |
| Distributed ranked store (Redis ZSET, DynamoDB GSI) | 230K QPS, O(log N+K) | Memory cost, hot keys | Replica failover ~30s | **Selected** |
| Compute on read from sketch | No materialization | P99 >> 50ms | CPU per request | Reject |

**Selected:** Redis sorted sets — **230K read QPS**, P99 **50ms** budget.

## System Overview

```
WRITE (50K peak QPS)                           READ (230K peak QPS)
──────────────────                           ──────────────────

[Engagement services]                        [Clients]
        │ gRPC                                       │ HTTPS
        ▼                                            ▼
[Ingestion API] ──► [Durable event log]      [LB] ──► [Trending API]
        │              (Kafka)                         │
        │                  │                           ▼
        │                  ▼                    [Ranked materialized store]
        │           [Stream aggregator]            (Redis ZSET)
        │              (Flink + CMS)                  │
        └─ abuse gates ──┘                            └── P99 50ms
                           │
                           ▼ push 2K QPS
                     [Ranked materialized store]
```

## Flow 1: Write / Data Path

1. **Engagement service → Ingestion API** (gRPC, ~5 ms): validate, `event_id` dedupe.
2. **Abuse gates** (~2 ms): reputation, bot list, content quality.
3. **Ingestion → Durable event log** (async, acks=all, ~10 ms): partition by `content_id`.
4. **Stream aggregator** (consume, ~5 ms lag): CMS update + top-K heap.
5. **Sink → Ranked store** (batched ZADD every 30s, ~2K QPS).

**Durable at:** event log (7d) + aggregator checkpoint (S3) + ranked store (serving copy).

## Flow 2: Read / Query Path

| Hop | Role | Protocol | Latency budget |
|-----|------|----------|----------------|
| 1 | Client → LB | HTTPS | 8 ms |
| 2 | LB → Query API | HTTP/2 | 7 ms |
| 3 | API → Ranked store | TCP same-AZ | 5 ms |
| 4 | ZREVRANGE + deserialize | — | 3 ms |
| 5 | Serialize response | — | 5 ms |
| 6 | Tail buffer | — | 22 ms |
| | **Total P99** | | **50 ms** |

## Flow 3: Failure and Degradation

### Failure: Ranked store (Redis) unavailable

- **User impact:** Stale list from API pod cache (30s TTL) or 503 + last ETag.
- **Degradation:** Stale-while-revalidate.
- **Recovery:** Sentinel failover ~30s; jittered retry 100–500 ms.
- **Stampede avoidance:** Singleflight per segment key.

### Failure: Stream aggregator (Flink) crash

- **User impact:** Lists freeze 5–15 min; last ranked-store snapshot served.
- **Degradation:** Stale top-K per NFR.
- **Recovery:** Checkpoint restore + replay from event log offset.
- **Stampede avoidance:** Hot standby for 1h window.

## Flow 4: Deploy and Migration

- **API:** Canary 5% → 25% → 100%; k8s rollback.
- **Aggregator:** Savepoint → deploy → resume; dual-run one checkpoint interval.
- **Schema:** Avro registry; backward-compatible readers 2 weeks.
- **Rollback:** API instant; aggregator restore savepoint <10 min.

## Component Registry

| Role | Implementation | Capacity | Failure mode | Owner |
|------|----------------|----------|--------------|-------|
| Ingestion API | Custom gRPC service | 50K QPS writes | Overload → 429 | Product Platform |
| Durable event log | Kafka | 50K QPS, 200 partitions | Broker loss → ISR failover | Data Platform |
| Stream aggregator | Flink | 50K QPS, 50 GB state | Job fail → stale 5–15 min | Real-time Infra |
| Ranked materialized store | Redis Cluster | 230K QPS reads, 30 GB | Node loss → replica promote | Caching Platform |
| Query API | Trending API service | 230K QPS reads | Pod crash → LB drain | Product API |

## Technology Trade-off Triads

### Approximate counting (Count-Min Sketch)

- **Solves:** Sublinear memory at billions of keys; ±5% error acceptable.
- **Worsens:** Overcount bias; conservative merge invalid across partitions.
- **When to change:** Exact billing counts required → OLAP reconciliation path.

### Durable event log (Kafka)

- **Solves:** 50K/s write decoupling, replay, 7d retention.
- **Worsens:** 10–50 ms produce latency; hot partition on viral `content_id`.
- **When to change:** <1K write QPS → DB outbox sufficient.

### Stream aggregator (Flink)

- **Solves:** 60s freshness, windowed CMS + top-K state.
- **Worsens:** Checkpoint recovery 5–15 min at 50GB state.
- **When to change:** All windows tolerate 15 min → Spark micro-batch.

### Ranked store (Redis ZSET)

- **Solves:** 230K read QPS at P99 50ms.
- **Worsens:** Memory per segment; global key hot at 100×.
- **When to change:** Staleness tolerance rises → read-through DB + CDN.

## Production References

- **Keyed stream state + checkpoint:** recovery time grows with state size (50GB → 5–15 min) — drove hot-standby for 1h window.
- **Twitter trending (2019):** manipulation incident — velocity + integrity graph informed abuse gate ordering.
- **Memcached stampede (Facebook 2010):** stale-while-revalidate on read path.

```sql
-- v0 capability-minimal (cron aggregation)
SELECT content_id, SUM(weight) AS score
FROM engagement_events
WHERE ts > NOW() - INTERVAL '1 hour'
GROUP BY content_id ORDER BY score DESC LIMIT 100;
```

```python
# Ranked store read (implementation-specific)
ZREVRANGE trending:1h:US:tech 0 49 WITHSCORES
```
