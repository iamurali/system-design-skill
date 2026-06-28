# Core Domain Entities — In-Memory Cache (Staff-Level)

## 1. Entity Relationship Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CACHE DOMAIN MODEL                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐      1:N      ┌──────────────────┐                     │
│   │  CacheStore  │◄──────────────│    CacheEntry    │                     │
│   │              │                │  (key, value,    │                     │
│   │ - hashTable  │                │   metadata)      │                     │
│   │ - eviction   │                └────────┬─────────┘                     │
│   │ - capacity   │                         │                               │
│   └──────┬───────┘                         │ used by                        │
│          │ uses                            ▼                               │
│          │                    ┌──────────────────────┐                     │
│          └───────────────────►│   EvictionPolicy     │                     │
│                               │   (interface)        │                     │
│                               │   - LRU, LFU, TTL,  │                     │
│                               │     Priority, etc.   │                     │
│                               └──────────────────────┘                     │
│                                                                             │
│   DISTRIBUTED LAYER                                                         │
│                                                                             │
│   ┌──────────────┐      N:1      ┌──────────────────┐     1:N             │
│   │    Router    │◄──────────────│     HashRing      │◄──────────┐         │
│   │  (Proxy)     │               │  - virtualNodes   │           │         │
│   └──────┬───────┘               │  - tokens[]       │           │         │
│          │ routes to             └──────────────────┘           │         │
│          ▼                              ▲                       │         │
│   ┌──────────────┐                      │ contains              │         │
│   │  CacheNode   │──────────────────────┘                       │         │
│   │  - nodeId    │     N:1                                        │         │
│   │  - store     │     ┌──────────────────┐                     │         │
│   │  - replicas  │────►│  ReplicaSet      │                     │         │
│   └──────────────┘     │  - primary       │                     │         │
│                        │  - replicas[]   │                     │         │
│                        └──────────────────┘                     │         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Entity Definitions with Cardinality

### 2.1 CacheEntry

**Purpose**: Wraps stored value with metadata for eviction, TTL, and versioning.

| Field | Type | Size (est.) | Purpose |
|-------|------|-------------|---------|
| `key` | bytes/string | 8–256 B | Lookup key; hash for routing |
| `value` | bytes | variable | Serialized payload |
| `createdAt` | int64 (ms) | 8 B | For TTL, age-based eviction |
| `lastAccessedAt` | int64 (ms) | 8 B | LRU ordering |
| `accessCount` | int32/64 | 4–8 B | LFU frequency |
| `ttl` | int64 (ms) | 8 B | Expiration; 0 = no TTL |
| `priority` | int32 | 4 B | Priority-based eviction |
| `version` | int64 | 8 B | Optimistic concurrency, invalidation |
| `prev`, `next` | ptr | 8 B each | Doubly-linked list (LRU) |
| `freqBucket` | ptr | 8 B | LFU O(1) bucket reference |
| `flags` | uint32 | 4 B | Deleted, dirty, etc. |

**Cardinality**: 1 CacheEntry per cached key. 50M–500M entries per cluster.

**Relations**:
- Belongs to **CacheStore** (N:1)
- Referenced by **EvictionPolicy** for ordering (N:1)

### 2.2 EvictionPolicy (Interface)

**Purpose**: Decides which entry to evict when capacity exceeded.

| Method | Signature | Invariant |
|--------|-----------|-----------|
| `onAccess(entry)` | void | Update ordering (e.g., move to tail for LRU) |
| `onPut(entry)` | void | Add to ordering structure |
| `onRemove(entry)` | void | Remove from ordering |
| `evict()` | key \| null | Return key to evict; null if nothing to evict |
| `selectForExpiry()` | key \| null | TTL-specific; return expired key |

**Implementations**:
- `LRUPolicy`: Doubly-linked list + HashMap
- `LFUPolicy`: Freq buckets + DLL (O(1) LFU)
- `TTLPolicy`: Min-heap by expiry or time-wheel
- `PriorityPolicy`: Heap by priority
- `W-TinyLFUPolicy`: Admission filter + LRU window + LRU main

**Cardinality**: 1 policy per CacheStore (or per namespace in multi-tenant).

### 2.3 CacheStore

**Purpose**: Holds data; enforces capacity; delegates eviction.

| Field | Type | Purpose |
|-------|------|---------|
| `hashTable` | Dict/HashMap | O(1) key → CacheEntry |
| `evictionPolicy` | EvictionPolicy | Policy implementation |
| `maxCapacity` | long (bytes or count) | Eviction trigger |
| `currentSize` | long | Current usage |
| `stats` | Stats | Hits, misses, evictions |
| `namespace` | string | Multi-tenant isolation |

**Cardinality**: 1 per CacheNode (single-node) or per shard (distributed).

### 2.4 CacheNode (Distributed)

**Purpose**: Physical or virtual node running a CacheStore.

| Field | Type | Purpose |
|-------|------|---------|
| `nodeId` | string | Unique identifier |
| `host` | string | IP or hostname |
| `port` | int | Service port |
| `store` | CacheStore | Local data |
| `replicaSet` | ReplicaSet | Primary + replicas |
| `tokens` | List<int> | Hash ring positions |
| `status` | enum | healthy, draining, down |

**Cardinality**: N nodes per cluster (50–100+).

### 2.5 HashRing (Consistent Hashing)

**Purpose**: Maps key hash to node with minimal disruption on topology change.

| Field | Type | Purpose |
|-------|------|---------|
| `tokens` | Sorted array of (hash, nodeId) | Ring positions |
| `virtualNodesPerNode` | int | Balance (100–200 typical) |
| `nodeToTokens` | Map<nodeId, List<hash>> | Reverse index for removal |

**Cardinality**: 1 per cluster (or per shard in multi-ring).

### 2.6 Router / Proxy

**Purpose**: Routes requests to correct node; handles retries, failover.

| Field | Type | Purpose |
|-------|------|---------|
| `hashRing` | HashRing | Key → node mapping |
| `clientPool` | Map<nodeId, ConnectionPool> | Connections per node |
| `retryPolicy` | RetryPolicy | Retry config |
| `circuitBreaker` | CircuitBreaker | Fail-fast on repeated failures |

**Cardinality**: Stateless; N instances for scale.

---

## 3. Serialization Considerations

### 3.1 Format Comparison

| Format | Size | Speed | Schema Evolution | Use Case |
|--------|------|-------|------------------|----------|
| **JSON** | Large (verbose) | Slow | Good (ignore unknown) | Debug, human-readable |
| **MessagePack** | Smaller | Fast | Manual | Compact binary |
| **Protobuf** | Smallest | Fastest | Excellent (field IDs) | Production (Google, LinkedIn) |
| **Kryo/FST** | Small | Fast | Poor | Java-only, internal |
| **Custom binary** | Minimal | Fastest | Manual | Redis, Memcached |

### 3.2 Production Choice: Protobuf

```protobuf
message CacheEntry {
  bytes key = 1;
  bytes value = 2;
  int64 created_at_ms = 3;
  int64 last_accessed_ms = 4;
  int32 access_count = 5;
  int64 ttl_ms = 6;
  int32 priority = 7;
  int64 version = 8;
}
```

**Benefits**: Backward/forward compatible via field IDs. Compact. Fast parsers (C++, Java, Go). Used by LinkedIn, Google, Meta for internal RPC and storage.

### 3.3 Key Serialization

- **String keys**: UTF-8 bytes. Max length 256 B (configurable). Longer keys hashed to fixed size (e.g., SHA-256 → 32 B) with collision handling.
- **Binary keys**: Use as-is. Ensure deterministic hash (e.g., murmur3, xxHash).

---

## 4. Memory Layout Optimization

### 4.1 Object Overhead (JVM Example)

| Component | Size (64-bit JVM) | Notes |
|-----------|------------------|-------|
| Object header | 12 B | Mark word + class ptr |
| Alignment padding | 0–7 B | 8-byte alignment |
| Reference (ptr) | 8 B | Per reference |
| **CacheEntry (Java)** | ~80–120 B | Before value |

**Mitigation**: Use primitive arrays, off-heap (ByteBuffer, Unsafe), or native (C/Rust) for hot path.

### 4.2 Cache Line Considerations (64 B)

- **False sharing**: Adjacent entries in array can share cache line. One thread updating `lastAccessedAt` invalidates line for neighbor.
- **Padding**: Pad hot fields to separate cache lines. Or use `@Contended` (Java).
- **Access pattern**: Sequential scan (LRU list) is cache-friendly. Random access (hash table) causes cache misses.

### 4.3 Off-Heap Storage

| Approach | Pros | Cons |
|----------|------|------|
| **On-heap (Java)** | Simple, GC-managed | GC pauses, overhead |
| **Off-heap (ByteBuffer)** | No GC for data | Manual management, serialization |
| **Native (C/Rust)** | Full control, no GC | Complexity |
| **Slab allocator (Memcached)** | Reduced fragmentation | Fixed size classes |
| **jemalloc (Redis)** | Good fragmentation | External dependency |

**Redis**: Uses jemalloc. Custom `zmalloc` wrapper for tracking.  
**Memcached**: Slab allocator—pre-allocated chunks of 1.1^n sizes.  
**LinkedIn Couchbase**: Uses memory-mapped files + custom allocator for persistence.

### 4.4 Compact Representation

- **Small values (< 64 B)**: Inline in CacheEntry (avoid indirection).
- **Large values**: Store pointer to off-heap buffer. Reduces hash table overhead.
- **Compression**: LZ4/Snappy for values > 1 KB. Trade CPU for memory. Use for cold data.

---

## 5. Version / Schema Evolution Strategy

### 5.1 Backward Compatibility

- **Add field**: New fields have default values. Old clients ignore.
- **Remove field**: Deprecate first; stop writing; remove after grace period.
- **Change type**: Avoid. Use new field ID if necessary.

### 5.2 Cache Entry Versioning

- **Optimistic locking**: `version` field. Put includes expected version; reject if stale.
- **Invalidation**: Version bump on source-of-truth update. Cache entries with old version considered stale.
- **Schema version**: Embed in value or metadata. Reader checks version before deserializing.

### 5.3 Migration Strategy

1. **Dual-write**: Write both old and new format during transition.
2. **Read both**: Prefer new; fallback to old.
3. **Background migration**: Async job rewrites entries to new format.
4. **TTL flush**: Let entries expire; new writes use new format. Simpler but slower.

---

## 6. Entity Size Summary

| Entity | Approx. Size | Notes |
|--------|--------------|-------|
| CacheEntry (metadata) | 80–120 B | Excludes value |
| EvictionPolicy (LRU node) | 24 B | prev, next, ref |
| Hash table entry | 16–32 B | Key ptr, value ptr, hash, next |
| HashRing token | 16 B | hash + nodeId ref |
| **Total overhead per key** | **~120–170 B** | Before value |

For 50M keys, 5 KB avg value: 50M × (150 B + 5 KB) ≈ **257 GB**.
