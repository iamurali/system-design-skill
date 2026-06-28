# Deep Dives — In-Memory Cache (Staff-Level)

## Deep Dive 1: Eviction Algorithm Internals

### 1.1 Redis LRU Clock Approximation

**Problem**: True LRU requires 16 B per key (prev/next pointers). At 50M keys, that's 800 MB overhead.

**Redis solution**: 24-bit LRU clock (seconds × 10, or ms). Fits in `redisObject.lru` field. On each access, store current clock. Eviction: sample N keys (default 5), evict one with smallest LRU.

```
Object structure:
  type (4b) | encoding (4b) | lru (24b) | refcount (32b) | ptr
```

**Approximation quality**: With 5 samples, Redis achieves ~90% of true LRU accuracy. Good enough for cache. Tune with `maxmemory-samples` (higher = more accurate, more CPU).

**Eviction cycle**: When `maxmemory` reached, run `freeMemoryIfNeeded()`. Sample, evict, repeat until under limit.

### 1.2 LFU with Morris Counters

**Problem**: Exact frequency requires 32–64 bits. Updates on every access.

**Morris counter**: Probabilistic counter. Increment with probability `1/(2^count)`. Expected value ≈ log2(actual count). 8 bits can represent millions of accesses.

```
Increment:
  if random() < 1/(1 << counter):
    counter++
```

**Redis LFU**: 8-bit counter (0–255) + 16-bit decay time. Logarithmic increment. Decay: periodically halve counter based on time since last decay. Prevents old items from staying forever.

```c
// Redis LFU decay
unsigned long LFUDecrAndReturn(robj *o) {
  unsigned long ldt = o->lru >> 8;  // decay time
  unsigned long counter = o->lru & 255;
  if (counter > 0 && now - ldt > 1) {
    counter--;
    o->lru = (counter | (now << 8));
  }
  return counter;
}
```

### 1.3 W-TinyLFU (Caffeine)

**Problem**: LRU is susceptible to one-time scans; LFU retains stale items. Need: admission filter + recency.

**Design**:
- **Window cache (1%)**: Small LRU. New items land here first.
- **Main cache (99%)**: SLRU (Segmented LRU)—protected (recent) and probation (candidates for eviction).
- **Count-Min Sketch**: Approximate frequency. 4 bits per counter. Compact.
- **Admission**: When main cache full, compare victim vs. window evictee. Admit evictee only if its estimated frequency > victim's.

**Result**: Better hit ratio than LRU or LFU alone on many workloads. Used in Caffeine, Apache Druid.

**Memory**: Count-Min Sketch ~4 B × 256 counters = 1 KB per sketch. Negligible.

---

## Deep Dive 2: Consistent Hashing with Bounded Loads

### 2.1 Standard Consistent Hashing Imbalance

With 100 nodes and 1M keys, expected 10K keys per node. Standard deviation can be high—one node may get 15K, another 6K. Causes:
- Hash variance
- Random token placement

### 2.2 Google's Bounded Loads

**Algorithm**: When placing key K, compute hash. Find node N clockwise. If N's load > (1+ε) × avg_load, skip to next node. Repeat until find node under load.

**Guarantee**: No node has more than (1+ε) × avg_load keys. ε=0.1 → max 10% imbalance.

**Implementation**: Track load per node. On placement, check load. O(log n) for sorted ring.

### 2.3 Jump Consistent Hash

**Paper**: "A Fast, Minimal Memory, Consistent Hash Algorithm" (Lamping, Veach).

```c
int32_t JumpConsistentHash(uint64_t key, int32_t num_buckets) {
  int64_t b = -1, j = 0;
  while (j < num_buckets) {
    b = j;
    key = key * 2862933555777941757ULL + 1;
    j = (b + 1) * (double(1LL << 31) / double((key >> 33) + 1));
  }
  return b;
}
```

**Properties**:
- No ring data structure. O(ln n) computation.
- When adding bucket N, only keys that previously mapped to bucket 0 move. Minimal disruption.
- Deterministic. No virtual nodes.

**Use**: Google uses for sharding. Good when num_buckets changes rarely.

---

## Deep Dive 3: Hot Key Detection and Mitigation

### 3.1 Problem

One key (e.g., celebrity profile) gets 10% of traffic. Single node overloaded. 100K ops/sec to one key → node can't keep up.

### 3.2 Detection

| Method | How | Overhead |
|--------|-----|----------|
| **Redis --hotkeys** | LFU-based; reports keys with high freq | Sampling; some CPU |
| **Client-side metrics** | Track per-key access in client | Minimal |
| **Proxy metrics** | Count requests per key in proxy | Per-request |
| **Statistical sampling** | Sample 1% of requests; count keys | Low |

### 3.3 Mitigation Strategies

**1. Local Cache (L1)**

- Cache hot key in application process (Caffeine, Guava). TTL 1–10 sec.
- Reduces L2 traffic by 90%+ for hot key.
- **Trade-off**: Stale reads; memory per process.

**2. Key Splitting (Sharding)**

- `user:123` → `user:123:0`, `user:123:1`, ..., `user:123:9`
- Read from random shard; write to all shards.
- Spreads load across 10 nodes. **Trade-off**: 10× writes; complexity.

**3. Shadow Keys**

- Replicate hot key to multiple nodes. Proxy round-robins reads.
- **Trade-off**: Replication overhead; consistency.

**4. Request Coalescing (Singleflight)**

- Multiple concurrent gets for same key → one in-flight load. Others wait.
- Reduces DB load on miss. Doesn't reduce cache load on hit.

**5. Dedicated Hot Key Cache**

- Separate small cluster for known hot keys. Route hot keys there.
- **LinkedIn**: Pre-identify hot keys (trending); route to dedicated tier.

---

## Deep Dive 4: Cache Invalidation Strategies

### 4.1 TTL (Time-To-Live)

- Set expiry per key. Lazy delete on access or active sweeper.
- **Pros**: Simple. No coordination. **Cons**: Stale until expiry. Burst of expiry (thundering herd).

### 4.2 Event-Driven (CDC/Kafka)

```
DB → Change Data Capture (Debezium, etc.) → Kafka
  → Consumer → Invalidate cache key
```

**Flow**: DB write → CDC captures → Kafka topic → Cache invalidation service deletes key. Next read repopulates.

**Pros**: Near real-time. **Cons**: Complexity; ordering; exactly-once delivery.

**LinkedIn**: Uses Kafka for profile cache invalidation. Profile update → event → invalidate `profile:{id}`.

### 4.3 Lease-Based (Facebook Memcache Paper)

**Problem**: Cache invalidation race. Client A invalidates; Client B has stale data; B writes back stale → cache corrupted.

**Lease**:
- On miss, server returns a lease (64-bit token) instead of null.
- Client fetches from DB, writes back with lease.
- Server rejects if lease invalid (key was invalidated since).
- If rejected, client invalidates and retries.

**Prevents**: Stale read-after-invalidation. **Reduces**: Thundering herd (only lease holder loads).

### 4.4 Version-Based

- Cache stores version. Source of truth has version.
- On read, if cache version < DB version, invalidate.
- **Polling**: Periodic check. **Push**: DB notifies on change.

---

## Deep Dive 5: Thundering Herd / Cache Stampede Protection

### 5.1 Problem

Popular key expires. 1000 concurrent requests miss. All 1000 hit DB. DB overload.

### 5.2 Request Coalescing (Singleflight)

```
Concurrent requests for key K:
  Request 1: Acquire lock for K
  Request 2–1000: Wait on lock
  Request 1: Load from DB, put in cache, release lock
  Request 2–1000: Read from cache

Result: 1 DB load instead of 1000.
```

**Implementation**: Map<key, channel> or Map<key, Promise>. First request does load; others wait on result.

**Guava/Caffeine**: `LoadingCache` does this internally.

### 5.3 Probabilistic Early Expiry

**Idea**: When key is near expiry, expire it early with probability to spread load.

**Algorithm** (from Facebook):
```
if (key near expiry):
  beta = 1 (or configurable)
  p = 1 - exp(-beta * (now - last_access) / ttl_remaining)
  if random() < p:
    expire now; trigger load
```

**Effect**: Spreads load over time instead of burst at expiry.

### 5.4 Stale-While-Revalidate

- Serve stale value immediately while background refresh.
- Client gets fast response. Background refresh updates cache for next time.
- **HTTP**: `Cache-Control: stale-while-revalidate=60`

### 5.5 Lease Mechanism (Facebook TAO)

- On miss, return lease. Only one client loads (lease holder).
- Others wait or get "lease" response and retry.

---

## Deep Dive 6: Memory Management (Slab, jemalloc, Fragmentation)

### 6.1 Memcached Slab Allocator

**Design**:
- **Slab**: 1 MB page. Divided into equal chunks.
- **Slab class**: Chunk size. Classes: 88, 112, 144, 184, ... (1.25× growth).
- **Allocation**: Find smallest class that fits. Get free chunk from slab. O(1).

**Fragmentation**:
- **Internal**: Chunk 88 B, value 50 B → 38 B wasted. Mitigate with more size classes.
- **External**: Slab half-used; no demand for that size. `slab_reassign` moves slab to different class.

**Memory overhead**: ~48 B per slab for metadata. Per chunk: 0 (no ptr; chunks are contiguous).

### 6.2 jemalloc (Redis)

**Structure**:
- **Arenas**: 1 per CPU. Reduces contention.
- **Runs**: Contiguous pages. Size classes.
- **Thread caches**: Small allocations served without lock.
- **Large allocations**: Direct mmap.

**Why jemalloc**: Better fragmentation than glibc malloc. Redis uses `zmalloc` wrapper for tracking. `INFO memory` shows used_memory (jemalloc's view).

### 6.3 Memory Fragmentation

**Ratio** = `used_memory_rss / used_memory`

- **RSS**: Physical memory (from OS).
- **used_memory**: Logical allocation.

**> 1.5**: Significant fragmentation. Causes: allocator overhead, external frag (small holes).

**Mitigation**:
- **Active defrag (Redis 4)**: Background process moves objects to coalesce. Incremental.
- **Restart**: Load RDB; fresh memory. Downtime or failover.
- **Limit value size**: Reject very large values; use object store.

### 6.4 Redis Active Defragmentation

```
Config:
  activedefrag yes
  active-defrag-threshold-lower 10   # Start when frag > 10%
  active-defrag-threshold-upper 100  # Aggressive when frag > 100%
  active-defrag-cycle-min 5          # Min CPU %
  active-defrag-cycle-max 75         # Max CPU %
```

**Process**: Scan keys; copy to new location; free old. Runs in event loop; limits CPU per iteration.

---

## Summary

| Deep Dive | Key Takeaway |
|-----------|--------------|
| **Eviction** | Redis uses approximate LRU/LFU to save memory; W-TinyLFU combines recency + frequency |
| **Consistent hashing** | Virtual nodes for balance; bounded loads or jump hash for strict guarantees |
| **Hot keys** | L1 cache, key splitting, replication, singleflight |
| **Invalidation** | TTL, CDC/Kafka, lease-based (Facebook) |
| **Stampede** | Singleflight, probabilistic early expiry, stale-while-revalidate |
| **Memory** | Slab (Memcached), jemalloc (Redis), active defrag for fragmentation |
