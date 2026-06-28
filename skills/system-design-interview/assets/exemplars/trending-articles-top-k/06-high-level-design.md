# High-Level Design — Trending Articles / Top-K

## Production Architecture: Real-World References

### Twitter's Trending Topics

Twitter's trending system (now X) processes billions of tweets and engagements. Key aspects from public disclosures and engineering blogs:

- **Real-time pipeline**: Tweets and engagements flow through a stream processing pipeline; trending updates every few minutes
- **Geo and topic segmentation**: "Trending in US", "Trending in Technology"
- **Anti-manipulation**: Coordinated inauthentic behavior detection; sudden spikes from bot networks suppressed
- **Velocity over volume**: A topic rising fast can trend over one with higher absolute volume (rate of change matters)
- **Challenges**: Repeated manipulation incidents (e.g., K-pop fan coordination, spam hashtags) led to algorithm changes and human review

### LinkedIn's Who's Viewed Your Profile

LinkedIn's "Who's Viewed Your Profile" and similar features use:

- **Apache Samza**: LinkedIn created and open-sourced Samza for stream processing; it powers many real-time pipelines
- **Kafka-centric**: Events flow through Kafka; Samza jobs consume, aggregate, and emit
- **Keyed state**: Per-entity (e.g., profile_id) state in RocksDB; windowed aggregations
- **Exactly-once**: Kafka transactions + Samza's checkpointing for exactly-once processing

### YouTube Trending Algorithm

YouTube's trending tab (publicly discussed):

- **Multiple signals**: Views, likes, dislikes (historically), watch time, velocity, novelty
- **Freshness bias**: Newer content favored; prevents evergreen content from dominating
- **Quality gates**: Clickbait, misleading thumbnails penalized
- **Geo and category**: Trending varies by country and category (Music, Gaming, etc.)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           EVENT SOURCES                                           │
│  Feed Service │ Engagement API │ Dwell Tracker │ Share/Repost Service             │
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Event Ingestion API (internal)                                                   │
│  - Validate, dedupe (event_id)                                                   │
│  - Abuse pre-check (user reputation, bot list)                                   │
│  - Partition key: content_id                                                      │
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  KAFKA: trending-engagement-events                                               │
│  - Partitions: 100–500 (scale with throughput)                                   │
│  - Partition by hash(content_id) → locality for same content                     │
│  - Retention: 7d (replay, batch reconciliation)                                  │
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  STREAM PROCESSOR: Flink / Samza                                                 │
│  - LinkedIn uses Samza (they created it)                                         │
│  - Consume events → update Count-Min Sketch → maintain top-K heap → emit         │
│  - Windowed aggregation: tumbling / sliding / hopping                             │
│  - Checkpointing: Chandy-Lamport (Flink) for fault tolerance                     │
│  - Parallelism: partition-level counting → periodic global merge                  │
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│  Redis (Top-K Cache)          │  │  Checkpoint Store (S3/HDFS)   │
│  - Sorted sets per segment    │  │  - Sketch state for recovery  │
│  - Push-based updates        │  │  - Exactly-once semantics     │
└──────────────────────────────┘  └──────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Trending API (Read Path)                                                        │
│  - GET /trending?window=1h&category=tech&geo=US                                 │
│  - Read from Redis; cache hit >99%                                                │
│  - SSE/WebSocket for real-time streaming                                         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Event Pipeline (Detail)

### Event Flow

1. **Sources**: Feed service emits view/like/comment; engagement service emits share/repost; dwell tracker emits time-on-content
2. **Ingestion API**: Validates schema, checks `event_id` for idempotency, applies abuse gates (user reputation, bot list, content quality)
3. **Kafka**: Events partitioned by `content_id` — all events for same content go to same partition → locality for aggregation
4. **Stream processor**: Consumes, updates sketch, maintains heap, emits top-K to Redis

### Partition Strategy

- **Why partition by content_id?** 
  - Same content's events land in same partition → single consumer can maintain sketch for that partition's content
  - Reduces cross-partition communication for aggregation
- **Hot partition risk**: Viral content (one content_id) can dominate a partition → partition count must be high enough to spread load; consider splitting hot content to dedicated consumers

---

## Stream Processing Layer (Detail)

### Technology Choice: Flink vs Samza

| Aspect | Flink | Samza |
|--------|-------|-------|
| **LinkedIn usage** | Used for some pipelines | **Primary**; LinkedIn created it |
| **State management** | RocksDB, incremental checkpoints | Kafka-backed state, RocksDB |
| **Windowing** | Rich: tumbling, sliding, session | Supported; configurable |
| **Exactly-once** | Chandy-Lamport snapshots | Kafka transactions |
| **Ecosystem** | Broader (batch + stream) | Kafka-centric |

For LinkedIn context, **Samza** is the natural choice; for generic design, **Flink** is widely used.

### Job Architecture

```
Flink/Samza Job:
  1. Source: Kafka consumer (partitioned)
  2. KeyBy: content_id (or (content_id, segment) for filtered aggregation)
  3. Process:
     a. For each event: apply decay, add weight to Count-Min Sketch
     b. Query sketch for content_id → approximate count
     c. Compute score = f(count, decay, velocity)
     d. Update min-heap of top-K (size 100–500)
  4. Sink: Emit top-K to Redis (or internal topic → Redis writer)
  5. Checkpoint: Every 1–5 min; state = (sketch, heap) per keyed partition
```

### Window Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Tumbling** | Fixed, non-overlapping (e.g., 1h buckets) | Simple; boundary artifacts at bucket edges |
| **Sliding** | Overlapping; slide by 1 unit | Smooth; expensive (many overlapping windows) |
| **Hopping** | Fixed size, advance by hop < size (e.g., 1h window, 5min hop) | Compromise; reduces artifacts, manageable cost |
| **Session** | Gap-based (for user sessions) | Less common for trending |

For 1h real-time trending: **hopping** (1h window, 1min slide) or **sliding** with pane-based optimization.

### Checkpointing (Flink)

- **Chandy-Lamport distributed snapshots**: Coordinated checkpoint across all operators
- **State**: Count-Min Sketch + top-K heap per key group
- **Recovery**: On failure, restore from last checkpoint; replay Kafka from checkpoint offset
- **Exactly-once**: Idempotent sink (Redis ZADD with same key overwrites) + checkpoint ensures no duplicate processing after recovery

### Parallelism

- **Partition-level counting**: Each Kafka partition → one subtask; maintains local sketch for keys in that partition
- **Global top-K merge**: 
  - **Option A**: Each partition emits its local top-K; separate merge job aggregates
  - **Option B**: Single job with keyed state; top-K is per-segment (segment = partition subset) — no global merge, approximate
  - **Option C**: Two-phase: partition-level sketches → periodic merge job → global top-K

---

## Counting Algorithms Comparison

| Algorithm | Space | Update | Query | Error | Use Case |
|-----------|-------|--------|-------|-------|----------|
| **Exact (HashMap)** | O(n) | O(1) | O(1) | 0 | Doesn't scale; billions of keys |
| **Space-Saving** | O(k) | O(1) | O(1) | Bounded for top-k | Heavy hitters; deterministic |
| **Count-Min Sketch** | O(w×d) | O(d) | O(d) | Overcounts; prob 1-δ | General frequency; sublinear |
| **HyperLogLog** | O(log log n) | O(1) | O(1) | ~1.04/√m | Unique count (distinct users) |

**Choice for trending**: Count-Min Sketch — sublinear space, handles high cardinality, overcount-only (safe for ranking). Space-Saving for top-K heavy hitters if we only care about top-K (no arbitrary count queries).

**Hybrid**: Count-Min Sketch for general counts + Space-Saving or heap for top-K maintenance.

---

## Scoring and Ranking

### Raw Count vs Weighted Score

- **Raw count**: Sum of events; simple but treats view = like = share
- **Weighted score**: `score = Σ (weight_i × count_i)` — like=2, comment=4, share=5, etc.
- **Dwell time**: Bucketed (0–5s, 5–30s, 30–60s, 60+s) with different weights; quality signal

### Time Decay

| Model | Formula | Use Case |
|-------|---------|----------|
| **Exponential** | `score = Σ w_i × e^(-λ(t_now - t_i))` | Recent events matter more; smooth decay |
| **Half-life** | `λ = ln(2)/half_life` | Configurable decay rate |
| **Linear** | `score = Σ w_i × (1 - (t_now - t_i)/window)` | Simpler; zero at window end |
| **Step** | Events in window count 1; outside count 0 | Tumbling window; boundary artifacts |

**Velocity-based**: `score += velocity_bonus × (rate - baseline_rate)` — rising fast gets a boost (Twitter-style).

### Normalization

- **Content age bias**: New content has less time to accumulate; optional boost: `score *= (1 + recency_factor × (1 - age/window))`
- **Category normalization**: Tech vs News may have different engagement rates; normalize by category baseline

---

## Serving Layer

### Pre-Computed Lists in Redis

- **Key**: `trending:{window}:{geo}:{category}:{scope}`
- **Value**: Sorted set (ZSET) — member=content_id, score=trending_score
- **Update**: Push-based — stream processor writes directly to Redis on each emission
- **Read**: `ZREVRANGE key 0 (limit-1) WITHSCORES` — O(log N + limit)

### Multiple Lists

| List Type | Example Key | Update Freq |
|-----------|-------------|-------------|
| Global | trending:1h:global | 30s |
| Per-geo | trending:1h:US:global | 30s |
| Per-industry | trending:1h:tech:global | 1min |
| Per-network | trending:1h:US:network:{user_id} | On-demand or pre-computed for active users |

### Cache Refresh Strategy

| Strategy | Description | Pros | Cons |
|----------|-------------|------|------|
| **Push-based** | Stream processor writes to Redis on update | Fresh; low read latency | Tight coupling; Redis write load |
| **Pull-based** | Periodic job queries processor/DB, updates Redis | Decoupled | Staleness; extra hop |
| **Hybrid** | Push for hot segments; pull for long-tail | Balance | More complex |

**Recommendation**: Push-based for top segments (1h, 24h, top geos); pull for long-tail.

---

## Anti-Gaming / Abuse

### Order of Operations

```
Event → [User reputation check] → [Bot/suspicious check] → [Content quality check] → [Count]
         ↓ fail                    ↓ fail                   ↓ fail
         Log, don't count          Log, don't count         Log, don't count
```

### Mechanisms

| Mechanism | Description |
|-----------|-------------|
| **User reputation** | Score 0–1 from account age, engagement history, reports; below threshold (e.g., 0.3) → exclude |
| **Bot detection** | Integration with integrity system; known bots excluded before counting |
| **Velocity anomaly** | Sudden spike from single IP/region (e.g., 10× baseline) → flag, temporary suppression |
| **Content quality** | Spam classifier score; content below 0.5 → exclude from trending |
| **Coordinated behavior** | Graph signals (many accounts from same cluster engaging same content) → delay or suppress |

### Tradeoff

- **Strict gates**: Fewer false trends, but may suppress organic viral content
- **Loose gates**: More responsive, higher manipulation risk
- **Tuning**: Admin config; A/B test thresholds
