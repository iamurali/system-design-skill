# Functional Requirements — In-Memory Cache (Staff-Level)

## Executive Summary

Design an in-memory cache with pluggable eviction policies for a LinkedIn-scale infrastructure. The cache serves as a critical performance layer between application services and persistent storage (databases, object stores). This document captures functional requirements with production-scale context, capacity estimates, and back-of-envelope calculations.

---

## 1. Detailed Functional Requirements

### 1.1 Core Key-Value Operations

| Operation | Semantics | Complexity | LinkedIn Use Case |
|-----------|-----------|------------|-------------------|
| **GET(key)** | Retrieve value by key; return null/absent on miss | O(1) avg | Member profile lookup, feed fragment fetch |
| **PUT(key, value)** | Store key-value pair; evict if at capacity | O(1) avg | Profile update cache, session data |
| **PUT(key, value, TTL)** | Store with optional expiration | O(1) avg | Session tokens (15 min), rate-limit counters (1 min) |
| **DELETE(key)** | Remove key; return removed value or null | O(1) avg | Invalidation on profile update |
| **EXISTS(key)** | Check presence without deserializing value | O(1) | Pre-check before expensive computation |
| **CLEAR()** | Flush all entries (admin operation) | O(n) | Cache warm-up reset, disaster recovery |

**Atomicity**: All single-key operations must be atomic. No partial writes visible to concurrent readers. Use compare-and-swap or single-writer patterns internally.

### 1.2 Pluggable Eviction Policies

The cache must support **multiple eviction policies**, selectable at initialization or runtime (per-namespace or per-key-prefix in distributed mode):

| Policy | Description | Best For | LinkedIn Example |
|--------|--------------|----------|------------------|
| **LRU** | Evict least recently accessed | Temporal locality (recent activity) | Feed fragments, "people you may know" |
| **LFU** | Evict least frequently accessed | Steady-state popularity | Member profiles, company pages |
| **TTL** | Evict by expiration time | Time-sensitive data | Sessions, OAuth tokens, rate limits |
| **Priority** | Evict by configurable priority score | Mixed criticality | Critical config vs. best-effort suggestions |
| **Random** | Evict random entry | Fallback, simple | Noeviction alternative |
| **Hybrid (W-TinyLFU)** | Admission filter + LRU/LFU | High hit ratio, limited memory | Hot path caches (Caffeine-style) |

**Policy Interface**: `onAccess(entry)`, `onPut(entry)`, `evict() -> key`. Policy must be swappable without full cache rebuild (e.g., Redis allows `CONFIG SET maxmemory-policy` at runtime).

### 1.3 Capacity Management

- **Max capacity**: Enforce either **entry count** or **memory bytes** (or both). Memory-based is production standard (Redis `maxmemory`, Memcached `-m`).
- **Eviction trigger**: When capacity exceeded, run eviction policy until under threshold. Eviction can be **synchronous** (block put until space) or **asynchronous** (background evictor).
- **Soft vs hard limits**: Some systems use soft limit (start evicting) and hard limit (reject writes). LinkedIn-style: soft at 90%, hard at 100%.

### 1.4 Key Expiration (TTL)

- **Per-entry TTL**: Optional milliseconds or seconds. Expired entries removed on access (lazy) or by background sweeper (active).
- **Lazy + active hybrid**: Redis uses lazy deletion on access + periodic random sampling (ACTIVE_EXPIRE_CYCLE). Reduces CPU spikes from pure active expiry.
- **Sub-second precision**: Required for rate limiting (e.g., 100 req/sec window). Millisecond granularity minimum.

### 1.5 Distributed Requirements

- **Sharding**: Route keys to nodes via consistent hashing. Minimal key migration on node add/remove (O(K/N) keys).
- **Replication**: Configurable replicas (typically 1–2) per shard for failover. Read from primary; fallback to replica on failure.
- **Cross-DC**: Optional read replicas in remote DCs for geo-distributed reads. Write to primary DC; async replicate.

### 1.6 Advanced Operations (Production)

| Operation | Purpose | Scale Consideration |
|-----------|---------|---------------------|
| **MGET(keys)** | Batch get; reduce round-trips | Keys may span shards; client or proxy must fan-out |
| **MSET(entries)** | Batch put | Same; pipeline or parallel writes |
| **SCAN(pattern)** | Iterate keys (admin) | Cursor-based; never block; O(n) but amortized |
| **INCR/DECR(key)** | Atomic counter | Used for rate limits, view counts |
| **GETSET(key, value)** | Atomic read-and-replace | Session rotation |
| **CAS (Compare-And-Swap)** | Optimistic concurrency | Memcached-style; prevent overwrite races |

### 1.7 Admin & Observability

- **Stats**: Hit ratio, miss ratio, eviction count, memory usage, connection count, ops/sec.
- **Health**: Liveness (process up), readiness (accepting traffic, not overloaded).
- **Flush**: Flush all or by pattern (dangerous; use with care).
- **Warm-up**: Preload known-hot keys from DB or snapshot.

---

## 2. LinkedIn-Scale Use Cases (Concrete Context)

### 2.1 Member Profile Cache

- **Key format**: `profile:{memberId}` or `profile:v2:{memberId}`
- **Value**: Serialized profile (headline, summary, skills, ~2–5 KB typical)
- **Read pattern**: 100:1 read:write. Profile views >> profile edits.
- **Eviction**: LFU or LRU. Profiles of active users stay hot.
- **TTL**: 1–24 hours; invalidate on profile update via event (Kafka).

### 2.2 Feed Data Cache

- **Key format**: `feed:{memberId}:{pageToken}` or `feed:fragment:{hash}`
- **Value**: Pre-computed feed fragments, ~10–50 KB
- **Read pattern**: 50:1. Heavy read; writes on new posts, likes.
- **Eviction**: LRU. Recent feed views matter most.
- **TTL**: 5–15 minutes. Stale feed acceptable; refresh on next scroll.

### 2.3 Session & Auth Cache

- **Key format**: `session:{sessionId}` or `oauth:token:{tokenHash}`
- **Value**: Session payload, ~500 B–2 KB
- **Read pattern**: 10:1. Every request validates session.
- **Eviction**: TTL (15 min–24 hr). No eviction by policy; expire only.
- **Critical**: Low latency; auth on critical path.

### 2.4 Rate Limiting & Counters

- **Key format**: `ratelimit:{userId}:{window}` or `view_count:{entityId}`
- **Value**: Counter (integer) or small struct
- **Read/Write**: 1:1 or write-heavy. INCR/DECR atomic.
- **Eviction**: TTL only. Window-based (e.g., 1 min, 1 hr).
- **Scale**: High key cardinality (one per user per window).

---

## 3. Capacity Estimation

### 3.1 Assumptions (LinkedIn-like)

| Parameter | Value | Rationale |
|-----------|-------|------------|
| DAU | 200M | LinkedIn-scale |
| Cacheable entities | ~500M unique keys | Profiles, feeds, sessions, etc. |
| Avg value size | 5 KB | Mix of profiles, feed fragments |
| Hot working set | 10% of keys | 80/20 rule; 50M keys hot |
| Read:Write ratio | 100:1 | Typical for cache |
| Reads per DAU | ~500 | Feed scrolls, profile views, etc. |
| Writes per DAU | ~5 | Profile edits, posts, etc. |

### 3.2 Memory per Node

| Component | Size | Notes |
|-----------|------|-------|
| Key (avg) | 50 B | `profile:12345`, `feed:user:abc:page:1` |
| Value (avg) | 5 KB | Serialized object |
| Metadata (LRU) | ~40 B | prev, next, timestamps, refs |
| Metadata (LFU) | ~48 B | + freq counter, bucket ref |
| Hash table overhead | ~16 B per entry | Pointer, hash, next (chaining) |
| **Total per entry** | **~5.2 KB** | Dominated by value |

### 3.3 Cluster Sizing

**Hot working set**: 50M keys × 5.2 KB ≈ **260 GB** in cache.

**Per-node**: 32 GB usable (64 GB box, ~50% for cache).  
**Nodes needed**: 260 / 32 ≈ **9 nodes** for hot set only.

**With headroom (2x)**: 18 nodes.  
**With replication (2x)**: 36 nodes total (18 primaries + 18 replicas).

**Production buffer**: Plan for 50–100 nodes in a region for:
- Multiple cache tiers (L1 local, L2 distributed)
- Shard isolation (different workloads)
- Failure domains (AZ spread)

### 3.4 Throughput Estimation

**Reads**: 200M DAU × 500 reads = **100B reads/day** ≈ **1.2M reads/sec** global.

**Writes**: 200M × 5 = **1B writes/day** ≈ **12K writes/sec** global.

**Per-node (18 primaries)**:  
- Reads: 1.2M / 18 ≈ **67K reads/sec per node**  
- Writes: 12K / 18 ≈ **700 writes/sec per node**

**Redis/Memcached capability**: 100K–500K ops/sec per node (single-threaded, pipelined). **Within capacity.**

---

## 4. Back-of-Envelope Calculations

### 4.1 Latency Budget

| Stage | Time (μs) | Notes |
|-------|-----------|-------|
| Client → Proxy | 100 | Same AZ |
| Proxy hash + route | 10 | In-memory |
| Proxy → Node | 100 | Same AZ |
| Node lookup | 5–20 | Hash + eviction structure |
| Serialization (get) | 10–50 | Depends on value size |
| **Total P50** | **~250 μs** | Target < 500 μs |
| **P99** | **~1 ms** | Tail latency |

### 4.2 Network Bandwidth

**Read traffic**: 67K reads/sec × 5 KB ≈ **335 MB/sec** per node ≈ **2.7 Gbps**.  
**Write traffic**: 700 writes/sec × 5 KB ≈ **3.5 MB/sec** per node.  
**Read-dominated**; 10 Gbps NIC sufficient.

### 4.3 Connection Count

**Clients**: 500 app instances × 10 connections each = 5K connections per node.  
**Connection pooling**: 50–100 connections per client pool to each node.  
**Total per node**: 5K–10K connections. Redis handles 10K+ with `io-threads`.

---

## 5. Summary Table

| Requirement | Target |
|-------------|--------|
| Ops/sec per node | 100K+ (read-heavy) |
| P50 latency | < 500 μs |
| P99 latency | < 1 ms (single DC) |
| Memory per node | 32–64 GB |
| Cluster size | 50–100 nodes (multi-tier) |
| Eviction policies | LRU, LFU, TTL, Priority, W-TinyLFU |
| Replication | 1–2 replicas per shard |
| Key expiration | Lazy + active, ms precision |
