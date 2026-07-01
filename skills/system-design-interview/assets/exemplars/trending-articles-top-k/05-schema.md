# Schema — Trending Articles / Top-K

## Event Schema (Kafka / Avro)

```json
{
  "type": "record",
  "name": "EngagementEvent",
  "namespace": "com.linkedin.trending.events",
  "fields": [
    {"name": "event_id", "type": "string", "doc": "UUID for idempotency"},
    {"name": "content_id", "type": "string", "doc": "urn:li:post:123"},
    {"name": "content_type", "type": {"type": "enum", "name": "ContentType", "symbols": ["post", "article", "hashtag", "skill", "job_title"]}},
    {"name": "event_type", "type": {"type": "enum", "name": "EventType", "symbols": ["view", "like", "comment", "share", "repost", "dwell"]}},
    {"name": "user_id", "type": "string"},
    {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},
    {"name": "weight", "type": ["null", "float"], "default": null},
    {"name": "metadata", "type": ["null", {"type": "map", "values": "string"}], "default": null},
    {"name": "user_reputation", "type": ["null", "float"], "default": null},
    {"name": "content_quality_score", "type": ["null", "float"], "default": null}
  ]
}
```

- **Topic**: `trending-engagement-events`
- **Partition key**: `hash(content_id) % num_partitions` — locality for same content
- **Retention**: 7 days (for replay and batch reconciliation)
- **Compression**: Snappy or Zstd

---

## Count-Min Sketch Storage

### In-Memory Representation

```
Structure: int[d][w]  (depth × width)
- d = 5, w = 262144 (2^18)
- 4 bytes per counter
- Total: 5 × 262144 × 4 = 5.24 MB per sketch

Hash functions: h_i(x) = (a_i * x + b_i) mod p, then mod w
- a_i, b_i: random seeds per row
- p: large prime
```

### Serialization for Checkpointing

```json
{
  "version": 1,
  "width": 262144,
  "depth": 5,
  "hash_seeds": [12345, 67890, 11111, 22222, 33333],
  "counters": "base64_encoded_binary",
  "total_count": 123456789,
  "window_id": "1h",
  "segment_id": "US:tech:global",
  "updated_at": "2025-03-09T12:05:00Z"
}
```

- Checkpointed to durable storage (S3, HDFS) for Flink/Samza recovery
- Merge: element-wise sum of counter arrays (CMS is linear)

---

## Top-K Heap Entries

In-memory structure maintained by stream processor:

```
Entry:
  content_id: string (URN)
  score: float (weighted, decayed)
  raw_count: float (from sketch)
  window_start: timestamp
  last_updated: timestamp

Storage: Min-heap of size K (e.g., 100)
- Evict when new item has score > min(heap)
- O(log K) insert/evict
```

---

## Redis Sorted Sets (Real-Time Top-K)

```
Key: trending:{window}:{segment}
  e.g., trending:1h:US:tech:global

Type: ZSET
  Member: content_id (urn:li:post:123)
  Score: trending score (float)

Commands:
  ZADD trending:1h:US:tech:global 15420.5 "urn:li:post:123"
  ZREVRANGE trending:1h:US:tech:global 0 49 WITHSCORES
  ZREMRANGEBYRANK trending:1h:US:tech:global 0 -101  # Keep top 100

TTL: None (updated by stream processor)
```

- **Multiple keys**: One per (window, geo, category, industry, scope)
- **Memory**: ~100 bytes per member × 50 members × 1000 segments ≈ 5 MB (manageable)

---

## Time-Bucketed Counters (Sliding Window)

For sliding windows, use minute-level buckets to avoid recomputing entire window:

```
Key: counts:{content_id}:{window}:{bucket_minute}
  e.g., counts:urn:li:post:123:1h:202503091200

Value: aggregated count for that minute
TTL: window_duration + buffer (e.g., 2h for 1h window)

Sliding window query: SUM over last 60 buckets
```

- Enables O(1) update (increment current bucket) and O(window_size) query
- Alternative: Circular buffer in state store

---

## Materialized Trending Lists

Pre-computed lists for fast serving:

```
Key: trending:materialized:{window}:{segment}
  e.g., trending:materialized:1h:US:tech:global

Value: JSON array
[
  {"content_id": "urn:li:post:123", "score": 15420.5, "rank": 1},
  {"content_id": "urn:li:post:456", "score": 14200.0, "rank": 2},
  ...
]

Updated by: Stream processor (push) or periodic job (pull)
TTL: 2 × update_interval (e.g., 60s for 30s updates)
```

- **Cache layer**: CDN or API cache in front of Redis
- **Fallback**: On Redis miss, compute from sketch (slower, rare)

---

## Metadata Tables (DB)

### Content Metadata (for enrichment)

| Column | Type | Notes |
|--------|------|-------|
| content_id | string | PK, URN |
| content_type | enum | post, article, hashtag, etc. |
| author_id | string | |
| category | string | Indexed |
| industry | string | Indexed |
| geo_metadata | jsonb | |
| created_at | timestamp | |
| quality_score | float | Spam/quality |

### Segment Configuration

| Column | Type | Notes |
|--------|------|-------|
| segment_id | string | PK, e.g., US:tech:global |
| geo | string | |
| category | string | |
| industry | string | |
| scope | enum | global, network |
| materialized | bool | Pre-compute or on-demand |

---

## Sharding Strategy

**Kafka:** 200 partitions; shard key = `hash(content_id)`. Justified by **50K peak write QPS** — ~250 msg/s per partition average, ~1.25K peak with hot spots. Scale partitions at 10×.

**Redis Cluster:** 16 shards; key = `trending:{window}:{geo}:{category}`. Read path **230K QPS** → ~14K QPS per shard with replicas.

**Flink:** Parallelism = Kafka partitions; keyed state by `(segment_id, content_id_bucket)`.

