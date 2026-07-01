# Non-Functional Requirements — Trending Articles / Top-K

## Capacity Estimation

Derived from **Scale Assumptions** in `01-requirements.md`.

### Estimation Chain

```
DAU = 200M

Read QPS (Trending API):
  200M DAU × 20 trending reads/day ÷ 86,400 = 46K avg read QPS
  Peak read QPS = 46K × 5 = 230K read QPS

Write QPS (Event ingestion):
  200M × 10 impressions × 5% engagement = 100M events/day
  Avg write QPS = 100M ÷ 86,400 = 1.2K write QPS
  Peak write QPS = 1.2K × 5 = 6K write QPS (engagement only)
  With dwell pings + multi-surface: peak write QPS ≈ 50K write QPS

Storage/day:
  100M events/day × 500 B = 50 GB/day raw events

Total storage (7-day retention):
  50 GB/day × 7 = 350 GB Kafka + 30 GB aggregation state (sketches, top-K)

Read bandwidth:
  230K read QPS × 5 KB response = 1.15 GB/s peak read bandwidth

Write bandwidth:
  50K write QPS × 500 B = 25 MB/s peak write bandwidth

Server count (API tier):
  230K peak read QPS ÷ 10K QPS per API node = 24 nodes (+ 2× for HA → 48 API nodes)
```

### Component Load Summary

| Component | Peak load | Notes |
|-----------|-----------|-------|
| Event ingestion API | 50K write QPS | Validate, dedupe, produce to Kafka |
| Kafka | 50K msg/s | Partition by `content_id` |
| Stream processor | 50K events/s | Sketch + top-K per segment |
| Redis writes | 2K QPS | Batched top-K pushes per segment |
| Trending read API | 230K read QPS | >99% cache hit on Redis |

### Growth Trajectory

| Tier | Scale | First constraint |
|------|-------|------------------|
| 1× (launch) | 50K write QPS, 230K read QPS | Single Postgres aggregation viable for writes <1K QPS only |
| 10× | 500K write QPS, 2.3M read QPS | Sketch memory + hot Kafka partitions |
| 100× | 5M write QPS, 23M read QPS | Global merge of top-K; Redis memory per segment |

## Latency Targets

| Percentile | Trending Read API | Event Ingestion (accept) |
|------------|-------------------|--------------------------|
| P50 | < 10 ms | < 20 ms |
| P95 | < 30 ms | < 50 ms |
| P99 | < 50 ms | < 100 ms |
| P99.9 | < 100 ms | < 200 ms |

End-to-end freshness: 1-hour trending list updates within **60 seconds** of events.

### Latency Budget Breakdown (Read API P99 = 50 ms)

| Hop | Budget | Notes |
|-----|--------|-------|
| Client → CDN/edge | 5 ms | Static assets only; API direct |
| CDN → load balancer | 3 ms | Same region |
| LB → API gateway | 2 ms | Auth token validation |
| Gateway → Trending API | 5 ms | Routing |
| API → Redis (same AZ) | 2 ms | Connection pool |
| Redis ZREVRANGE + deserialize | 3 ms | O(log N + K), K≤50 |
| API response serialization | 5 ms | JSON 5 KB |
| Tail buffer (GC, jitter) | 25 ms | Headroom for P99 |
| **Total P99** | **50 ms** | Sum = 50 ms |

## Availability and Error Budget

| Component | Target | Error budget (concrete) |
|-----------|--------|-------------------------|
| Trending read API | 99.9% | ~43 min downtime/month |
| Event ingestion | 99.95% | ~22 min downtime/month |
| Stream processor | 99.9% | ~43 min/month; checkpoint recovery |

**Budget consumers:** rolling deploys (planned ~5 min/week), Redis failover (~30s), Flink checkpoint recovery (5–15 min — serve stale during recovery).

## Consistency Model

| Data | Model | User-facing consequence |
|------|-------|-------------------------|
| Top-K lists | Eventual | User may see trending list up to **60s stale** after a viral spike; rank order within top-10 remains stable |
| Event ingestion ack | At-least-once to Kafka | Duplicate `event_id` deduped at consumer |
| Cross-window (1h vs 24h) | Independent | 1h and 24h lists may reflect different snapshot times — acceptable |

## Durability

| Data class | RPO | RTO | Mechanism |
|------------|-----|-----|-----------|
| Raw engagement events | 0 | 5 min | Kafka 7-day retention, acks=all, ISR ≥2 |
| Aggregation state | 5 min | 10 min | Flink checkpoint to S3 every 5 min |
| Top-K snapshots (Redis) | 1 min | 30 sec | Rebuild from stream replay; AOF everysec |

## Security NFRs

- **Auth:** Internal services mTLS; public API OAuth 2.0 bearer tokens.
- **Encryption:** TLS 1.3 in transit; Kafka and Redis encrypted at rest.
- **Abuse:** Reputation gate before count; rate limit 10K events/sec per `content_id`.

## Operational Requirements

| Requirement | Target |
|-------------|--------|
| Zero-downtime deploy | Rolling canary on API; Flink savepoint migration |
| Alerting | Consumer lag > 5 min; API P99 > 80 ms; sketch audit drift > 10% |
| Capacity review | Monthly; scale Kafka partitions when >70% broker CPU |

### Runbook: Stream Processor Lag > 10 Minutes

1. **Detect:** Flink consumer lag alert; trending freshness SLO breach.
2. **Mitigate:** Scale task parallelism; shed non-critical segments (7d window); increase allowed lateness temporarily.
3. **Recover:** Identify hot `content_id` partition; optional dedicated consumer for hot key; replay from last checkpoint.
4. **Post-incident:** Add hot-content detection to ingestion path; partition split playbook.
