# API Design — In-Memory Cache (Staff-Level)

## 1. Interface Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  Application (Java, Go, Python)                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │ Client SDK
┌────────────────────────────▼────────────────────────────────────┐
│  REST / gRPC (Public API)                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  Proxy / Router (mcrouter, Twemproxy, Envoy)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │ Memcached / Redis protocol
┌────────────────────────────▼────────────────────────────────────┐
│  Cache Nodes (Redis, Memcached, custom)                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. gRPC API (Production Standard)

### 2.1 Service Definition

```protobuf
syntax = "proto3";
package cache.v1;

service CacheService {
  rpc Get(GetRequest) returns (GetResponse);
  rpc Put(PutRequest) returns (PutResponse);
  rpc Delete(DeleteRequest) returns (DeleteResponse);
  rpc GetMany(GetManyRequest) returns (GetManyResponse);
  rpc PutMany(PutManyRequest) returns (PutManyResponse);
  rpc Incr(IncrRequest) returns (IncrResponse);
  rpc Cas(CasRequest) returns (CasResponse);
}

message GetRequest {
  bytes key = 1;
  optional string namespace = 2;
  optional uint64 min_version = 3;  // Read-your-writes
}

message GetResponse {
  bytes value = 1;
  uint64 version = 2;
  bool found = 3;
  CacheError error = 4;
}

message PutRequest {
  bytes key = 1;
  bytes value = 2;
  optional int64 ttl_ms = 3;
  optional int32 priority = 4;
  optional uint64 expected_version = 5;  // CAS
}

message PutResponse {
  uint64 version = 1;
  bool evicted = 2;
  CacheError error = 4;
}

message CacheError {
  int32 code = 1;
  string message = 2;
}
```

### 2.2 Error Codes

| Code | Name | Meaning |
|------|------|---------|
| 0 | OK | Success |
| 1 | NOT_FOUND | Key not in cache |
| 2 | VERSION_MISMATCH | CAS failed; stale version |
| 3 | CAPACITY_EXCEEDED | Rejected (noeviction policy) |
| 4 | TIMEOUT | Operation timed out |
| 5 | UNAVAILABLE | Node down, partition |
| 6 | INVALID_ARGUMENT | Bad key/value/ttl |

---

## 3. REST API (Admin & Debug)

### 3.1 Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/cache/{key}` | Get value (base64 key) |
| PUT | `/v1/cache/{key}` | Put value (body: JSON with value, ttl) |
| DELETE | `/v1/cache/{key}` | Delete key |
| POST | `/v1/cache/batch/get` | Batch get (body: keys[]) |
| POST | `/v1/cache/batch/put` | Batch put |
| GET | `/v1/stats` | Hit ratio, memory, evictions |
| POST | `/v1/admin/flush` | Flush all (dangerous) |
| GET | `/v1/health` | Liveness/readiness |
| GET | `/v1/topology` | Cluster topology |

### 3.2 Request/Response Schemas

**GET /v1/cache/{key}**
```json
// Response 200
{
  "value": "<base64>",
  "version": 12345,
  "ttl_ms": 3600000,
  "created_at_ms": 1700000000000
}

// Response 404
{ "error": "NOT_FOUND" }
```

**PUT /v1/cache/{key}**
```json
// Request
{
  "value": "<base64>",
  "ttl_ms": 3600000,
  "priority": 1
}

// Response 200
{
  "version": 12346,
  "evicted": false
}
```

---

## 4. Client Library Design

### 4.1 Connection Pooling

```
┌─────────────┐     ┌──────────────────────────────────────┐
│  App Thread │────►│  Connection Pool (per node)          │
│  Pool 1     │     │  - min_idle: 5                        │
│  Pool 2     │     │  - max_total: 50                     │
│  ...        │     │  - max_wait: 100ms                   │
└─────────────┘     │  - health_check_interval: 30s         │
                    └──────────────────────────────────────┘
```

**Config**:
- `min_idle`: Keep N connections warm per node.
- `max_total`: Cap to avoid exhausting server `maxclients`.
- `max_wait`: Fail fast if pool exhausted.
- **Per-node pools**: Router maintains pool per CacheNode. Hash(key) → node → get connection from that node's pool.

### 4.2 Retry Policy

| Scenario | Action |
|----------|--------|
| Transient timeout | Retry with exponential backoff (1ms, 2ms, 4ms, max 3) |
| Connection refused | Retry on different node (replica) |
| NOT_FOUND | No retry (expected) |
| VERSION_MISMATCH | No retry (client must refetch) |
| UNAVAILABLE | Retry with backoff; circuit breaker if sustained |

**Idempotency**: GET is idempotent. PUT with same key is overwrite (idempotent if same value). Use idempotency key for non-idempotent ops.

### 4.3 Circuit Breaker

```
States: CLOSED → OPEN → HALF_OPEN → CLOSED

CLOSED: Normal operation. On failure count > threshold in window → OPEN.
OPEN: Fail fast, no requests to node. After sleep window → HALF_OPEN.
HALF_OPEN: Allow 1 probe request. Success → CLOSED. Failure → OPEN.
```

**Config**: `failure_threshold=5`, `window=10s`, `sleep_window=30s`. Per-node circuit breaker.

### 4.4 Timeouts

| Operation | Default | Rationale |
|-----------|---------|-----------|
| Connect | 2s | TCP handshake |
| Get | 100ms | P99 target < 2ms; 100ms allows for tail |
| Put | 200ms | May trigger eviction |
| Batch | 500ms | Fan-out to multiple nodes |

---

## 5. Batch Operations

### 5.1 GetMany (MGET)

**Challenge**: Keys may hash to different nodes. Fan-out required.

```
Client: GetMany([k1, k2, k3, k4])
         │
         ▼
Router:  hash(k1)→N1, hash(k2)→N1, hash(k3)→N2, hash(k4)→N2
         │
         ├──► N1: Get(k1), Get(k2)  [pipeline]
         └──► N2: Get(k3), Get(k4)  [pipeline]
         │
         ▼
Client:  {k1:v1, k2:v2, k3:v3, k4:null}  [merge, preserve order]
```

**Optimization**: Group by node; pipeline per node; parallel across nodes. Redis `MGET` only works for same slot (Redis Cluster); otherwise client/proxy does fan-out.

### 5.2 PutMany (MSET)

Same pattern. Group by node; pipeline; parallel. Consider atomicity: each put is atomic; batch is not atomic across keys.

### 5.3 Pipelining

**Redis pipelining**: Send multiple commands without waiting for response. Server queues; responds in order. Reduces RTT from N×RTT to 1×RTT for N commands.

```
Without pipeline:  Get(k1) → wait → Get(k2) → wait → Get(k3) → wait
With pipeline:     Get(k1), Get(k2), Get(k3) → wait once → [v1, v2, v3]
```

**Limit**: Don't pipeline 10K commands. Batch into 100–500 per pipeline to avoid memory spike.

---

## 6. Admin APIs

### 6.1 Stats

```
GET /v1/stats
GET /v1/stats?node=node-1
```

**Response**:
```json
{
  "hits": 1000000,
  "misses": 50000,
  "hit_ratio": 0.952,
  "evictions": 1200,
  "memory_used_bytes": 32212254720,
  "memory_max_bytes": 34359738368,
  "keys": 5000000,
  "connections": 150,
  "ops_per_sec": 50000
}
```

### 6.2 Flush

```
POST /v1/admin/flush
POST /v1/admin/flush?pattern=session:*
```

**Danger**: Flush all causes thundering herd on next access. Use for disaster recovery or controlled warm-up reset.

### 6.3 Warm-up

```
POST /v1/admin/warm
Body: { "keys": ["k1", "k2", ...], "source": "db" }
```

Preload keys from DB. Used after deploy or flush. Async; returns job ID.

### 6.4 Health Checks

```
GET /health/live   → 200 if process up
GET /health/ready  → 200 if accepting traffic, not overloaded
```

**Readiness**: Reject if memory > 95%, connection count > 90% max, or replica lag > 30s.

---

## 7. Cache Stampede Protection (Singleflight)

### 7.1 Problem

Many clients miss same key simultaneously → all hit DB → DB overload.

### 7.2 Singleflight Pattern

```
┌──────┐ ┌──────┐ ┌──────┐
│Client│ │Client│ │Client│  All request key K (miss)
└──┬───┘ └──┬───┘ └──┬───┘
   │        │        │
   └────────┼────────┘
            ▼
   ┌────────────────────┐
   │  Singleflight      │  Only 1 in-flight load per key
   │  - map[key]→chan   │  Others wait on channel
   └────────┬───────────┘
            │ 1 load
            ▼
   ┌────────────────────┐
   │  DB / Loader       │
   └────────────────────┘
            │
            ▼  Result broadcast to waiters
```

**Implementation** (Go-style):
```go
func (c *Cache) Get(key string) (Value, error) {
  if v := c.store.Get(key); v != nil { return v, nil }
  return c.singleflight.Do(key, func() (Value, error) {
    v := c.loader.Load(key)  // Only one goroutine runs this
    c.store.Put(key, v)
    return v, nil
  })
}
```

**Guava/Caffeine**: `LoadingCache` with `CacheLoader` does this internally.

### 7.3 Probabilistic Early Expiry

To avoid many keys expiring at same time:
- Add jitter to TTL: `ttl = base_ttl * (1 + random(0, 0.2))`
- Or: expire with probability `1/(ttl_remaining)` when accessed near expiry (Facebook Memcache).

### 7.4 Lease-Based (Facebook TAO)

- On miss, return a **lease** (token) instead of null.
- Client uses lease when writing back. Server rejects if lease invalid (key was updated).
- Prevents stale write after invalidation. Reduces thundering herd (only lease holder loads).

---

## 8. Idempotency

| Operation | Idempotent? | Notes |
|-----------|-------------|-------|
| GET | Yes | Same result for same key |
| PUT (overwrite) | Yes | Same key, same value = same state |
| DELETE | Yes | Deleting absent key = no-op |
| INCR | No | Each call changes value |
| CAS | Yes | Same expected_version + value = same outcome |

**Idempotency key** (for non-idempotent): Client sends `Idempotency-Key: uuid`. Server deduplicates by key within window (e.g., 24h).

---

## 9. Protocol Comparison

| Protocol | Use Case | Pros | Cons |
|----------|----------|------|------|
| **gRPC** | Service-to-service | Typed, streaming, efficient | Not browser-native |
| **REST** | Admin, debug | Simple, universal | Verbose |
| **Memcached** | Legacy, compatibility | Simple, ubiquitous | Limited ops |
| **Redis** | Rich data types | Lists, sets, pub/sub | Protocol complexity |

**Production**: gRPC for app clients; Redis/Memcached protocol for compatibility with existing clients (mcrouter, Twemproxy).
