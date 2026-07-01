# Functional Requirements — Trending Articles / Top-K

## Problem Reframing

**Before we design:** Do users need **exact leaderboard positions** or **directional trending** where approximate ranks suffice?

**Decision:** Trending is a **discovery surface**, not analytics. We accept ±5% count error and minor rank swaps outside top-10. That unlocks approximate counting (Count-Min Sketch) and eliminates the need for exact per-content counters at billions of keys — the architecture changes entirely if exact counts were required.

### Hidden Requirements Surfaced

1. **Abuse resistance** — trending is a high-value manipulation target; events must pass reputation/bot gates before counting.
2. **Freshness vs cost** — 1-hour window needs sub-minute updates; 7-day window can tolerate 15-minute batch reconciliation.
3. **Segment cardinality** — `(windows × geos × industries)` explodes; we cannot materialize all combinations.

## Functional Requirements

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-1 | Ingest engagement events (view, like, comment, share, dwell) | P0 | Async; idempotent by `event_id` |
| FR-2 | Compute weighted trending score per content within time window | P0 | Read:write ≈ **1:50** (write-heavy ingestion, read-heavy API) |
| FR-3 | Serve global top-K per (window, geo, category) | P0 | Pre-computed lists |
| FR-4 | Filter by geo, industry, content type at query time | P1 | Hot segments pre-aggregated |
| FR-5 | Admin tuning of signal weights without deploy | P2 | Config service |

**Scope:** 3 windows (1h, 24h, 7d), top 20 geos, top 20 industries. No per-user network trending (see out-of-scope).

## Capacity Estimation

### Assumptions

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| DAU | 200M | LinkedIn-scale professional network |
| Feed impressions/DAU/day | 10 | Scroll-heavy feed |
| Engagement rate | 5% | View, like, comment, share |
| Avg event payload | 500 B | JSON with metadata |
| Retention (raw events) | 7 days | Kafka replay + reconciliation |
| Peak factor | 5× | Viral content / US business hours |

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

## Success Metrics (SLIs)

| Metric | Target | Type |
|--------|--------|------|
| Trending API P99 latency | < 50 ms | Technical |
| Freshness lag (1h window) | < 60 s | Technical |
| Top-10 rank stability | > 95% unchanged over 5 min | Business |
| Ingestion error rate | < 0.01% | Technical |

## Explicit Out-of-Scope

| Exclusion | Reason |
|-----------|--------|
| Per-user "trending in your network" | Requires graph-aware aggregation per member — 900M× cardinality; compute on-demand only for premium, not core |
| Exact view counts / billing-grade analytics | Approximate counts sufficient for discovery; exact path needs OLAP warehouse |
| ML-based personalized ranking | Separate recommendation system; we serve segment-level top-K |
| Real-time push notifications on trend changes | Different fanout infrastructure; API poll/SSE is sufficient |
