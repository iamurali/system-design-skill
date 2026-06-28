# Functional Requirements — Trending Articles / Top-K

## LinkedIn Context

LinkedIn's trending system surfaces **what's hot** across multiple content types and surfaces:

| Content Type | Description | Example |
|--------------|-------------|---------|
| **Posts** | Feed posts, articles, carousels | "Top posts in your network this week" |
| **Articles** | Long-form content from creators | "Trending articles in Technology" |
| **Hashtags** | Topic aggregation | #AI, #RemoteWork, #CareerAdvice |
| **Skills** | Endorsement and hiring trends | "Python trending in Software Engineering" |
| **Job Titles** | Hiring demand signals | "Staff Engineer" trending in Bay Area |

Each surface has distinct engagement semantics and ranking signals. The system must unify event ingestion while supporting type-specific scoring.

---

## Scale

| Metric | Target | Rationale |
|--------|--------|------------|
| **Feed impressions** | 2B+ / day | LinkedIn's feed scale; trending surfaces are a subset |
| **Engagement events** | Millions / second (peak) | Views, likes, comments, shares, dwell-time pings |
| **Unique content items** | Hundreds of millions | Posts, articles, hashtags, skills, jobs |
| **Active users** | 900M+ members | Global audience; geo and industry segmentation |

---

## Ranking Signals

Multiple signals contribute to trending score. Each has different weight and freshness requirements:

| Signal | Weight (typical) | Latency sensitivity | Notes |
|--------|------------------|---------------------|-------|
| **View** | 1 | High | Most frequent; may be deduplicated per user |
| **Like** | 2–3 | Medium | Strong intent signal |
| **Comment** | 3–5 | Medium | High engagement; expensive to compute |
| **Share** | 4–6 | High | Viral amplification |
| **Dwell time** | 0.5–2 (bucketed) | Low | Quality signal; aggregate per session |
| **Repost** | 2–4 | High | Content propagation |

Weights are configurable per content type and surface. Admin API allows tuning without code deploy.

---

## Time Windows

| Window | Use Case | Update frequency |
|--------|----------|------------------|
| **1 hour** | Real-time trending | Sub-minute; most latency-sensitive |
| **24 hours** | Daily trends | 1–5 min acceptable |
| **7 days** | Weekly trends | 5–15 min acceptable |

Windows can be **tumbling** (fixed boundaries) or **sliding** (smooth decay). Real-time trending (1h) typically uses sliding or hopping windows to avoid boundary artifacts.

---

## Personalization

| Mode | Description | Complexity |
|------|-------------|------------|
| **Global trending** | Top-K across all members | Single pre-computed list per (window, geo, category) |
| **Trending in your network** | Top-K among 1st/2nd degree connections | Requires graph-aware aggregation; higher cost |
| **Trending in your industry** | Filter by member industry | Pre-computed per industry segment |
| **Trending in your region** | Geo-filtered (country, metro) | Pre-computed per geo |

Personalization increases cardinality: `(windows × geos × industries × network_slices)`. Not all combinations are materialized; long-tail uses query-time filtering.

---

## Geo and Industry Segmentation

- **Geo**: Country, region (e.g., US-West), metro (e.g., SF Bay Area). Pre-aggregate for top geos; others computed on demand.
- **Industry**: LinkedIn's industry taxonomy (200+). Pre-aggregate for top 20–50 industries.
- **Combinations**: `geo × industry` for "Trending in Tech in US" — selective materialization.

---

## Capacity Estimation

### Events per Second

```
Assumptions:
- 2B feed impressions/day ≈ 23K impressions/sec average
- Engagement rate ~5% → ~1.2K engagement events/sec average
- Peak 10× average → ~12K engagement events/sec peak
- Add views, dwell pings → 50K–200K events/sec peak (conservative)
- LinkedIn scale: 500K–2M events/sec peak (multiple surfaces)
```

| Component | Peak load | Notes |
|-----------|-----------|-------|
| Event ingestion API | 500K–2M req/sec | Async; write to Kafka |
| Kafka throughput | Same | Partitioned by content_id |
| Stream processor | Same | Consume, aggregate, emit |
| Redis writes | 1K–10K/sec | Top-K list updates (batched) |
| Trending API reads | 100K–500K req/sec | Cache hit ratio >99% |

### Storage for Counters

```
Count-Min Sketch per (window, segment):
- Width w = 2^18 ≈ 256K counters
- Depth d = 5
- 4 bytes per counter → 256K × 5 × 4 = 5 MB per sketch

Segments: 3 windows × 50 geos × 20 industries × 2 (global/network) = 6,000 sketches
Total: 6,000 × 5 MB = 30 GB (sketches only)

Add: Top-K heaps, Redis sorted sets, checkpoint state → 50–100 GB for counting layer
```

---

## Key Behaviors

| Requirement | Description |
|-------------|-------------|
| **Event ingestion** | Accept high-volume engagement events; validate, dedupe, route to Kafka |
| **Multi-signal aggregation** | Weighted sum of engagement types per content within time window |
| **Approximate counting** | Count-Min Sketch or Space-Saving; bounded error acceptable |
| **Ranking** | Score = f(counts, decay, velocity); maintain top-K per segment |
| **Filtering** | Category, geo, industry at query time; pre-compute hot combinations |
| **Personalization** | Network-based and industry-based trending where feasible |
