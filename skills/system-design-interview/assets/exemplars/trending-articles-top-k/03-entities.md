# Core Entities — Trending Articles / Top-K

## Domain Entities

### ContentItem

Unified representation for all content types that can trend.

| Field | Type | Description |
|-------|------|-------------|
| `content_id` | URN | `urn:li:post:123`, `urn:li:article:456`, `urn:li:hashtag:AI`, etc. |
| `content_type` | enum | `post`, `article`, `hashtag`, `skill`, `job_title` |
| `author_id` | URN | Creator (for reputation/abuse checks) |
| `category` | string | e.g., `tech`, `news`, `career` |
| `industry` | string | LinkedIn industry code |
| `geo_metadata` | object | `{country, region, metro}` |
| `created_at` | timestamp | For recency bias and cold-start |
| `quality_score` | float | Spam/quality classifier output; gate for counting |

---

### EngagementEvent

Single engagement action used for counting and scoring.

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | UUID | Idempotency key; deduplication |
| `content_id` | URN | Target content |
| `event_type` | enum | `view`, `like`, `comment`, `share`, `repost`, `dwell` |
| `user_id` | URN | Actor |
| `timestamp` | ISO8601 | Event time (event-time for processing) |
| `weight` | float | Optional; override default weight for event_type |
| `metadata` | object | `{geo, device, session_id, dwell_sec}` |
| `user_reputation` | float | Pre-computed; used for abuse gate |
| `content_quality_score` | float | Pre-computed; used for quality gate |

**Event types and default weights** (configurable):

| event_type | Default weight | Notes |
|------------|----------------|-------|
| view | 1 | May dedupe per user per content |
| like | 2 | |
| comment | 4 | |
| share | 5 | |
| repost | 3 | |
| dwell | 0.5–2 | Bucketed by duration |

---

### TrendingScore

Aggregated score for a content item in a time window.

| Field | Type | Description |
|-------|------|-------------|
| `content_id` | URN | |
| `score` | float | Weighted sum with decay applied |
| `raw_count` | float | Approximate count (from sketch) |
| `decay_factor` | float | Time decay applied (0–1) |
| `velocity` | float | Optional; rate of change (events/min) |
| `window_start` | timestamp | Window boundary |
| `window_type` | enum | `1h`, `24h`, `7d` |
| `last_updated` | timestamp | When score was computed |

**Decay function parameters** (stored in TimeWindow config):

| Parameter | Description | Typical value |
|-----------|-------------|---------------|
| `decay_type` | `exponential`, `linear`, `step` | exponential |
| `half_life` | For exponential: time for score to halve | 6h for 24h window |
| `lambda` | Decay rate λ in e^(-λt) | 0.1–0.2 |

---

### TimeWindow

Configuration for a time-bounded aggregation.

| Field | Type | Description |
|-------|------|-------------|
| `window_id` | string | `1h`, `24h`, `7d` |
| `duration_sec` | int | 3600, 86400, 604800 |
| `window_type` | enum | `tumbling`, `sliding`, `hopping` |
| `slide_sec` | int | For hopping; e.g., 300 for 5-min slide |
| `decay_params` | object | `{decay_type, half_life, lambda}` |
| `update_interval_sec` | int | How often to refresh top-K |

---

## Probabilistic Data Structure Entities

### CountMinSketch

| Field | Type | Description |
|-------|------|-------------|
| `width` | int | w = number of columns; w ≈ e/ε for error ε |
| `depth` | int | d = number of rows; d ≈ ln(1/δ) for failure prob δ |
| `counters` | int[][] | d × w array; 4 bytes per counter |
| `hash_seeds` | int[] | Seeds for d pairwise-independent hash functions |
| `total_count` | long | Sum of all events (for normalization) |
| `conservative_update` | bool | If true, only increment min bucket (reduces overcount) |

**Parameters**:
- ε (epsilon): relative error; typical 0.01–0.05
- δ (delta): failure probability; typical 0.001
- Width: w = ⌈e/ε⌉
- Depth: d = ⌈ln(1/δ)⌉

---

### HeavyHitter

Entry for an item in the top-K or heavy-hitter list.

| Field | Type | Description |
|-------|------|-------------|
| `content_id` | URN | |
| `approximate_count` | float | From Count-Min Sketch or Space-Saving |
| `score` | float | Weighted score after decay |
| `confidence` | float | Optional; error bound or confidence interval |
| `rank` | int | 1-based position in list |
| `window_id` | string | |
| `segment_id` | string | geo, industry, etc. |

---

## Relationships

```
EngagementEvent ──(content_id)──▶ ContentItem
EngagementEvent ──(event_type, weight)──▶ ScoringConfig
EngagementEvent ──(abuse gates)──▶ [Filtered] ──▶ CountMinSketch

CountMinSketch ──(query)──▶ approximate_count
approximate_count + TimeWindow.decay_params ──▶ TrendingScore

TrendingScore ──(order by score)──▶ Top-K Heap ──▶ HeavyHitter[]
HeavyHitter[] ──▶ Materialized trending list (Redis)
```

---

## Entity Lifecycle (State Machine)

`EngagementEvent` in the stream processor:

```
received → validated → abuse_gated → counted → aggregated → emitted
              │            │ fail
              ▼            ▼
           rejected    audit_logged (not counted)
```

`TrendingList` segment:

```
pending → active → stale → refreshed
```

