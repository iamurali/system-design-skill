# Functional Requirements — Trending Articles / Top-K

## Problem Reframing

**Before we design:** Do users need **exact leaderboard positions** or **directional trending** where approximate ranks suffice?

**Decision:** Trending is a **discovery surface**, not analytics. We accept ±5% count error and minor rank swaps outside top-10. That unlocks approximate counting (Count-Min Sketch) and eliminates the need for exact per-content counters at billions of keys — the architecture changes entirely if exact counts were required.

### Hidden Requirements Surfaced

1. **Abuse resistance** — trending is a high-value manipulation target; events must pass reputation/bot gates before counting.
2. **Freshness vs cost** — 1-hour window needs sub-minute updates; 7-day window can tolerate 15-minute batch reconciliation.
3. **Segment cardinality** — `(windows × geos × industries)` explodes; we cannot materialize all combinations.

## Early Problem Shape (provisional)

| Signal | Value |
|--------|-------|
| Provisional archetype | **A7** Aggregate / meter (top-K, windowed) |
| Dominant force | Ingest high-volume events; serve low-latency global top-K reads |
| Read:write ratio | ~1:50 ingest events vs trending API reads by volume; API is read-heavy at query time |

## Functional Requirements

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-1 | Ingest engagement events (view, like, comment, share, dwell) | P0 | Async; idempotent by `event_id` |
| FR-2 | Compute weighted trending score per content within time window | P0 | Write-heavy ingestion path |
| FR-3 | Serve global top-K per (window, geo, category) | P0 | Pre-computed lists; read-heavy API |
| FR-4 | Filter by geo, industry, content type at query time | P1 | Hot segments pre-aggregated |
| FR-5 | Admin tuning of signal weights without deploy | P2 | Config service |

**Scope:** 3 windows (1h, 24h, 7d), top 20 geos, top 20 industries. No per-user network trending (see out-of-scope).

## Scale Assumptions (inputs for Phase 2)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| DAU | 200M | LinkedIn-scale professional network |
| Feed impressions/DAU/day | 10 | Scroll-heavy feed |
| Engagement rate | 5% | View, like, comment, share |
| Trending API reads/DAU/day | 20 | Discovery surface usage |
| Avg event payload | 500 B | JSON with metadata |
| Retention (raw events) | 7 days | Kafka replay + reconciliation |
| Peak factor | 5× | Viral content / US business hours |

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
