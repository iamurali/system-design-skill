# API Design — Trending Articles / Top-K

## Event Ingestion API (Internal, High-Throughput)

### Record Engagement Event

```
POST /v1/internal/events/engagement
Content-Type: application/json
X-Idempotency-Key: {event_id}

Request:
{
  "event_id": "uuid",
  "content_id": "urn:li:post:123",
  "content_type": "post",
  "event_type": "view" | "like" | "comment" | "share" | "repost" | "dwell",
  "user_id": "urn:li:member:456",
  "timestamp": "2025-03-09T12:00:00.000Z",
  "weight": 1.0,
  "metadata": {
    "geo": "US",
    "industry": "94",
    "dwell_sec": 45,
    "session_id": "sess_xyz"
  }
}

Response: 202 Accepted
X-Request-Id: req_abc123
```

- **Internal only**: Called by feed service, engagement service; not exposed to clients
- **Async**: Writes to Kafka; returns immediately after successful enqueue
- **Idempotent**: `event_id` or `X-Idempotency-Key` for exactly-once; duplicate events deduplicated in stream processor
- **Partition key**: `content_id` for locality (all events for same content to same partition)
- **Rate limit**: Per-service quotas; backpressure on 429

---

## Trending Query API (External)

### Get Trending List

```
GET /v1/trending
  ?window=1h|24h|7d
  &category=tech|news|career
  &geo=US|US-CA|GB
  &industry=94|96
  &scope=global|network
  &limit=50
  &content_type=post|article|hashtag

Response: 200 OK
{
  "items": [
    {
      "content_id": "urn:li:post:123",
      "content_type": "post",
      "score": 15420.5,
      "rank": 1,
      "approximate_count": 12500,
      "trend_direction": "up" | "stable" | "down"
    },
    ...
  ],
  "window": "1h",
  "segment": {
    "geo": "US",
    "category": "tech",
    "scope": "global"
  },
  "updated_at": "2025-03-09T12:05:00Z",
  "next_refresh_sec": 30
}
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| window | No | 24h | Time window |
| category | No | all | Content category filter |
| geo | No | user's geo | Geography |
| industry | No | all | Industry filter |
| scope | No | global | `global` or `network` (trending in your network) |
| limit | No | 10 | Max items; cap at 100 |
| content_type | No | post | post, article, hashtag, skill, job_title |

- **Auth**: Member token; geo/industry may be inferred from profile
- **Cache**: Response cacheable by client; `updated_at` and `next_refresh_sec` for staleness

---

### Get Trending Score for Single Item

```
GET /v1/trending/{content_id}
  ?window=1h|24h|7d
  &geo=US

Response: 200 OK
{
  "content_id": "urn:li:post:123",
  "score": 15420.5,
  "rank": 5,
  "approximate_count": 12500,
  "window": "1h",
  "segment": { "geo": "US" },
  "updated_at": "2025-03-09T12:05:00Z"
}

Response: 404 Not Found
{
  "error": "content_not_in_trending",
  "message": "Content not in top-K for this segment"
}
```

- Use case: Show "Trending #5 in Tech" badge on a post
- If not in top-K, may return 404 or score=0 with rank=null

---

## Streaming API (Real-Time Updates)

### Server-Sent Events (SSE)

```
GET /v1/trending/stream
  ?window=1h
  &category=tech
  &geo=US
  &limit=50

Accept: text/event-stream

Response: 200 OK (streaming)
event: snapshot
data: {"items": [...], "updated_at": "..."}

event: delta
data: {"changes": [{"content_id": "...", "rank": 1, "score": ...}], "updated_at": "..."}
```

- **Snapshot**: Full list on connect
- **Delta**: Incremental updates when top-K changes (new entrant, rank change)
- **Heartbeat**: `event: ping` every 30s to keep connection alive
- **Reconnect**: Client reconnects on disconnect; receives snapshot

### WebSocket Alternative

```
WS /v1/trending/ws?window=1h&category=tech&geo=US

Messages (server → client):
  {"type": "snapshot", "items": [...], "updated_at": "..."}
  {"type": "delta", "changes": [...], "updated_at": "..."}
  {"type": "ping", "ts": "..."}
```

- Use when bidirectional or lower overhead needed
- Same semantics as SSE

---

## Admin API (Internal, Config)

### Configure Event Weights

```
PUT /v1/admin/config/weights
{
  "weights": {
    "view": 1,
    "like": 2.5,
    "comment": 4,
    "share": 5,
    "repost": 3,
    "dwell": {"0-5": 0.5, "5-30": 1, "30-60": 1.5, "60+": 2}
  },
  "content_type_overrides": {
    "article": { "view": 1.2, "comment": 5 }
  }
}
```

### Configure Time Windows

```
PUT /v1/admin/config/windows
{
  "windows": [
    {
      "id": "1h",
      "duration_sec": 3600,
      "type": "sliding",
      "slide_sec": 60,
      "decay": {"type": "exponential", "half_life_sec": 1800},
      "update_interval_sec": 30
    },
    ...
  ]
}
```

### Configure Abuse Thresholds

```
PUT /v1/admin/config/abuse
{
  "min_user_reputation": 0.3,
  "min_content_quality_score": 0.5,
  "velocity_anomaly_threshold": 10.0,
  "bot_list_enabled": true
}
```

---

## Internal: Partition-Level Aggregation API

Used by stream processor for distributed counting and merge.

### Get Partition Sketch (Internal)

```
GET /v1/internal/partitions/{partition_id}/sketch?window=1h

Response: 200 OK
{
  "partition_id": 42,
  "window": "1h",
  "sketch": { "width": 262144, "depth": 5, "counters": "base64..." },
  "total_count": 1234567,
  "updated_at": "..."
}
```

### Merge Partitions (Internal)

```
POST /v1/internal/trending/merge
{
  "window": "1h",
  "segment": {"geo": "US", "category": "tech"},
  "partition_sketches": [...]
}

Response: 200 OK
{
  "top_k": [...],
  "merged_sketch": {...}
}
```

- Called by coordinator to merge per-partition sketches into global top-K
- Not exposed externally
