# High-Level Design — In-Memory Cache (Staff-Level)

## 1. Full Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              LINKEDIN-SCALE CACHE ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────────┐
                                    │   Application   │
                                    │   (Feed, Auth,  │
                                    │    Profile)     │
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
           ┌────────────────┐      ┌────────────────┐      ┌────────────────┐
           │  L1 Local      │      │  L1 Local      │      │  L1 Local      │
           │  (Caffeine/    │      │  (per pod)     │      │  (Guava)       │
           │   Guava)       │      │  10K entries   │      │                │
           └───────┬────────┘      └───────┬────────┘      └───────┬────────┘
                   │ miss                 │ miss                  │ miss
                   └──────────────────────┼───────────────────────┘
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                         PROXY LAYER (mcrouter / Twemproxy / Envoy)                       │
│  - Consistent hashing (virtual nodes)                                                    │
│  - Connection pooling, multiplexing                                                      │
│  - Retry, failover, circuit breaker                                                     │
│  - Request coalescing (singleflight)                                                     │
│  - Shadow reads (optional)                                                                │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         │                               │                               │
         ▼                               ▼                               ▼
┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
│  Shard 0        │             │  Shard 1        │             │  Shard N        │
│  Primary + 2    │             │  Primary + 2    │             │  Primary + 2    │
│  Replicas       │             │  Replicas       │             │  Replicas       │
│  (Redis/        │             │  (Redis/        │             │  (Redis/        │
│   Couchbase)    │             │   Couchbase)    │             │   Couchbase)    │
└────────┬────────┘             └────────┬────────┘             └────────┬────────┘
         │                               │                               │
         └───────────────────────────────┼───────────────────────────────┘
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                         PERSISTENCE LAYER (Optional)                                    │
│  - RDB snapshots (warm restart)                                                         │
│  - AOF (durability for cache-as-primary)                                                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Flow: Reads

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Client   │───►│ L1 Cache │───►│  Proxy   │───►│  Node    │
│          │    │ (local)  │    │ (hash)   │    │ (primary)│
└──────────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
                     │ hit           │ miss          │
                     │               │               │
                     ▼               │               ▼
              ┌──────────┐           │        ┌──────────────┐
              │ Return   │           │        │ HashMap     │
              │ value    │           │        │ lookup      │
              └──────────┘           │        └──────┬──────┘
                                     │               │ hit/miss
                                     │               ▼
                                     │        ┌──────────────┐
                                     │        │ Return value │
                                     │        │ or null      │
                                     │        └──────┬──────┘
                                     │               │ miss
                                     │               ▼
                                     │        ┌──────────────┐
                                     └───────►│ Replica     │
                                              │ (failover)  │
                                              └──────────────┘
```

**Read path latency**: L1 hit ~1 μs; L2 hit ~200–500 μs; L2 miss → DB (ms).

---

## 3. Data Flow: Writes

```
┌──────────┐    ┌──────────┐    ┌──────────────────────────────────┐
│ Client   │───►│  Proxy   │───►│  Primary Node                     │
│          │    │ hash(key)│    │  1. Check capacity                │
└──────────┘    └────┬─────┘    │  2. Evict if full (policy)        │
                     │          │  3. Insert/update in hash table    │
                     │          │  4. Update eviction structure     │
                     │          └──────────────┬───────────────────┘
                     │                         │
                     │                         ▼
                     │          ┌──────────────────────────────────┐
                     │          │  Replication (async or sync)      │
                     │          │  - Async: Fire-and-forget to      │
                     │          │    replicas; low latency          │
                     │          │  - Sync: Wait for N/2+ acks;      │
                     │          │    strong consistency             │
                     │          └──────────────────────────────────┘
                     │
                     ▼
              ┌──────────────┐
              │ Invalidate   │  (if cache-aside)
              │ L1 on write  │
              └──────────────┘
```

---

## 4. Data Flow: Evictions

```
┌─────────────────────────────────────────────────────────────────┐
│  PUT arrives, capacity exceeded                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  EvictionPolicy.evict()                                           │
│  - LRU: Remove head of DLL                                        │
│  - LFU: Remove from lowest freq bucket                            │
│  - TTL: Remove soonest expiring                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Remove from hash table; free memory                              │
│  Optional: Publish eviction event (Kafka) for analytics           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Retry put (may need multiple evictions if value large)           │
└─────────────────────────────────────────────────────────────────┘
```

**Eviction storm**: Many puts + full cache → burst of evictions. Mitigate with soft limit (start evicting at 90%), background evictor, or reject writes (noeviction).

---

## 5. Memcached and Redis at Production Scale

### 5.1 Memcached (Meta/LinkedIn)

| Aspect | Implementation |
|--------|----------------|
| **Threading** | Multi-threaded; one thread per core. Each thread has its own LRU. |
| **Memory** | Slab allocator. Fixed size classes. |
| **Network** | Event-driven (libevent). Async I/O. |
| **Sharding** | Client-side or mcrouter. Consistent hashing. |
| **Replication** | None native. Mcrouter replicates to multiple clusters. |
| **Persistence** | None. Ephemeral. |
| **Scale** | 100K+ ops/sec per node. 1000s of nodes at Meta. |

**Meta scale**: Billions of objects, 100+ TB, mcrouter for routing and replication.

### 5.2 Redis

| Aspect | Implementation |
|--------|----------------|
| **Threading** | Single-threaded for commands (6.0+: io_threads for I/O). |
| **Memory** | jemalloc. Dict + eviction structure (approx LRU/LFU). |
| **Network** | Event loop (epoll/kqueue). Pipelining for throughput. |
| **Sharding** | Redis Cluster (16384 slots) or client-side. |
| **Replication** | Async replication. Sentinel for HA. |
| **Persistence** | RDB, AOF, or both. |
| **Scale** | 100K–500K ops/sec per node. Cluster for horizontal scale. |

**Redis Cluster**: Hash slot (CRC16 mod 16384). Each node owns subset of slots. Gossip for topology. Redirect (MOVED/ASK) for client.

### 5.3 LinkedIn Couchbase

- **Couchbase** as cache + session store. Memcached protocol compatible.
- **vbuckets**: Sharding unit. 1024 vbuckets, mapped to nodes.
- **Cross-DC replication**: XDCR for geo replication.
- **Memory**: Managed by Couchbase; similar to Memcached slabs.

---

## 6. Consistent Hashing with Virtual Nodes

### 6.1 Basic Algorithm

```
Hash ring: 0 to 2^32-1 (or 2^64)
Place N physical nodes, each with V virtual nodes → N×V points on ring
Key: hash(key) → point on ring → clockwise to next node
```

### 6.2 Virtual Nodes (LinkedIn/Meta)

**Without virtual nodes**: 3 nodes → 3 points. Random placement can cause 50% of keys on one node (imbalance).

**With virtual nodes**: 3 nodes × 150 = 450 points. Smoother distribution. Standard: 100–200 virtual nodes per physical node.

```
Node A: tokens at h(A,0), h(A,1), ..., h(A,149)
Node B: tokens at h(B,0), h(B,1), ..., h(B,149)
Node C: tokens at h(C,0), h(C,1), ..., h(C,149)
```

### 6.3 Bounded Loads (Google)

**Problem**: Even with virtual nodes, one node can get more keys (hash variance).

**Solution**: Bounded loads. When assigning key to node, if node already has > (1+ε)×avg load, skip to next node. Guarantees max load (1+ε)×avg.

**Jump consistent hash**: Alternative. `jump_hash(key, num_buckets)` — minimal disruption when N changes. Used by Google for sharding.

---

## 7. Replication Topologies

### 7.1 Master-Slave (Redis)

```
     ┌─────────┐
     │ Master  │
     └────┬────┘
          │ async replication
    ┌─────┼─────┐
    ▼     ▼     ▼
┌──────┐ ┌──────┐ ┌──────┐
│Slave1│ │Slave2│ │Slave3│
└──────┘ └──────┘ └──────┘
```

- Writes to master only. Reads from master or replica (scale reads).
- Replica lag: ms to seconds. Failover: promote replica to master (Sentinel).

### 7.2 Redis Sentinel (HA)

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│Sentinel1│  │Sentinel2│  │Sentinel3│  (Quorum for failover)
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │
     └────────────┼────────────┘
                  │ monitor
     ┌────────────┼────────────┐
     │            │            │
     ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Master  │  │ Replica │  │ Replica │
└─────────┘  └─────────┘  └─────────┘
```

**Failover**: Sentinel detects master down → elect leader → promote replica. 10–30 sec typical.

### 7.3 Redis Cluster

```
Shard 0: M0 + R0
Shard 1: M1 + R1
Shard 2: M2 + R2
...
16384 slots distributed across nodes
```

- No proxy; client routes by slot. Redirect (MOVED) when topology changes.
- Gossip protocol for topology. Config epoch for split-brain resolution.

### 7.4 Master-Master (Couchbase)

- Multi-master replication. Conflict resolution: last-writer-wins or custom.
- Use for geo-distributed writes. Complex; eventual consistency.

---

## 8. Client-Side vs Server-Side Sharding

| Approach | Pros | Cons |
|----------|------|------|
| **Client-side** | No proxy; lower latency | Client must know topology; update on change |
| **Server-side (proxy)** | Client simple; central routing | Extra hop; proxy scaling |
| **Hybrid** | Client has ring; proxy for compatibility | Complexity |

**Production**: Proxy (mcrouter, Twemproxy) for legacy clients; smart client (knows topology) for performance-critical paths.

---

## 9. Proxy Layer (Twemproxy, mcrouter)

### 9.1 Twemproxy (Twitter)

- Stateless. Consistent hashing. Connection pooling.
- Single-threaded. One proxy per core.
- Redis and Memcached protocol.
- **Limitation**: No replication logic. Client configures multiple pools.

### 9.2 Mcrouter (Meta)

- **Replication**: Replicate writes to N pools. Read from primary; fallback.
- **Failover**: Automatic. Shadow reads to compare.
- **Pools**: Different clusters (e.g., flash vs RAM).
- **Routing**: Prefix-based, custom routes.
- **Scale**: Used by Meta for all Memcached traffic.

### 9.3 Envoy + Redis Proxy

- Envoy filter for Redis. Connection pooling, routing.
- Integrates with service mesh. Observability.

---

## 10. Cache Patterns: When to Use Each

### 10.1 Cache-Aside (Lazy Loading)

```
Read:  App → Cache. Miss → App → DB → App → Cache.put() → App
Write: App → DB → App → Cache.delete() (invalidate)
```

**When**: Default. App controls consistency. DB is source of truth.  
**LinkedIn**: Profile cache, feed cache.

### 10.2 Read-Through

```
Read:  App → Cache. Miss → Cache loads from DB (loader) → Cache.put() → return
Write: App → DB → Cache invalidates (or write-through)
```

**When**: Cache has built-in loader. Simpler app logic.  
**Example**: Guava LoadingCache, Caffeine.

### 10.3 Write-Through

```
Write: App → Cache → Cache writes to DB synchronously → return
Read:  App → Cache (always consistent)
```

**When**: Strong consistency. Write latency higher.  
**Example**: Session store with DB backup.

### 10.4 Write-Behind (Write-Back)

```
Write: App → Cache (immediate ack) → Async flush to DB
Read:  App → Cache
```

**When**: Write throughput critical. Risk: data loss on crash.  
**Example**: Analytics, view counts. Use with care.

---

## 11. Connection Management & Multiplexing

### 11.1 Redis Single-Threaded Model

- One event loop. All commands serialized. No locks.
- **Pipelining**: Client sends multiple commands; server queues; responds in order. Throughput = 1 RTT for N commands.
- **Blocking ops**: BLPOP, etc. Block connection. Use dedicated connections.

### 11.2 Redis 6+ I/O Threads

- **io-threads**: Network I/O (read, parse, write) in multiple threads.
- **Command execution**: Still single-threaded. Reduces bottleneck for high connection count.
- **Config**: `io-threads 4`, `io-threads-do-reads yes`.

### 11.3 Connection Pool Sizing

- **Per node**: `max_clients` (Redis default 10000). Pool size = connections / nodes.
- **Rule of thumb**: 50–100 connections per client process per node. Scale clients before saturating.

---

## 12. Warm-Up and Cache Priming

### 12.1 Cold Start

- New node: Empty cache. All reads miss. DB overload.
- **Mitigation**: Preload hot keys before traffic.

### 12.2 Warm-Up Strategies

| Strategy | How | When |
|----------|-----|------|
| **RDB load** | Load snapshot from file | Restart with persistence |
| **Replicate from peer** | Sync from replica | New replica |
| **Preload list** | Load known-hot keys from DB | After deploy, flush |
| **Traffic replay** | Replay recent requests | Test environment |
| **Staggered traffic** | Ramp traffic slowly | New cluster |

### 12.3 LinkedIn Warm-Up

- **Blue-green deploy**: New nodes join; traffic shifts gradually. Hash ring rebalance spreads load.
- **Cache priming job**: Batch load top 1M keys from DB before cutover.

---

## 13. Multi-Datacenter Caching

```
┌─────────────────────────────────────────────────────────────────┐
│  DC1 (Primary)                                                    │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                       │
│  │ L1      │───►│ L2      │───►│ DB      │                       │
│  │ (local) │    │ (Redis) │    │         │                       │
│  └─────────┘    └────┬────┘    └─────────┘                       │
│                      │ XDCR / async replicate                    │
└──────────────────────┼──────────────────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────────────────┐
│  DC2 (Secondary)     │                                           │
│  ┌─────────┐    ┌────▼────┐    ┌─────────┐                       │
│  │ L1      │───►│ L2      │───►│ DB      │                       │
│  │ (local) │    │ (Redis) │    │ replica │                       │
│  └─────────┘    └─────────┘    └─────────┘                       │
│                 (read replica)                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 13.1 Cross-DC Replication

- **Async**: Replicate cache updates to remote DC. Lag: 100ms–1s.
- **Use**: Read from local DC cache. Lower latency. Stale acceptable.
- **Couchbase XDCR**: Replicates vbuckets. Conflict resolution configurable.

### 13.2 Local + Remote Tiers

- **L1**: Process-local (Caffeine). ~1 μs.
- **L2**: Same-rack/ same-AZ. ~200 μs.
- **L3**: Cross-AZ or cross-DC. ~1–5 ms.

**Routing**: Try L1 → L2 → L3 → DB. Or: L1 → L2 (skip L3 for critical path).

---

## 14. Summary: Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **L1 cache** | In-process (Caffeine/Guava) | Sub-μs; reduce L2 load |
| **L2 cache** | Redis or Couchbase | Battle-tested; rich features |
| **Proxy** | mcrouter or Envoy | Routing, replication, observability |
| **Sharding** | Consistent hashing + virtual nodes | Minimal migration |
| **Replication** | 1–2 replicas per shard | HA; 99.99% |
| **Consistency** | Eventual (async replicate) | Low latency |
| **Persistence** | RDB for warm restart | Fast recovery |
| **Eviction** | LRU or LFU by workload | Hit ratio |
