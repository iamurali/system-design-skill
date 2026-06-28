# Data Model / Storage Schema — In-Memory Cache (Staff-Level)

## 1. Memory Data Structures — Byte-Level Analysis

### 1.1 Primary Lookup: Hash Table

**Redis dict.c**: Uses hash table with chaining. Two tables for incremental rehashing.

| Component | Size (64-bit) | Purpose |
|-----------|----------------|---------|
| `dictEntry` | 24 B | key ptr, value ptr, next ptr |
| `dict` (struct) | ~96 B | ht[2], rehashidx, type |
| `dictht` (bucket array) | 8 B + n×8 B | size, sizemask, table ptr |
| **Overhead per entry** | **~32 B** | Entry + chain pointer |

**Load factor**: Redis resizes when `used/size > 1` (no load factor threshold; resize on any add when full). Typical load factor 0.5–1.0.

**Collision handling**: Chaining (linked list). Redis 4+ uses adaptive: switch to open addressing for small tables when beneficial.

### 1.2 Open Addressing vs Chaining

| Approach | Pros | Cons |
|----------|------|------|
| **Chaining** | Simple, no clustering | Pointer overhead, cache misses |
| **Open addressing** | Cache-friendly, no ptrs | Clustering, complex delete |
| **Robin Hood** | Bounded probe length | More complex |
| **Cuckoo hashing** | O(1) lookup | High overhead, rehash cost |

**Memcached**: Chaining. **Redis**: Chaining. **Google**: Often open addressing for small tables.

### 1.3 Resizing Strategy

```
Current: size=8, used=8  →  add triggers resize
New: size=16, copy entries incrementally (rehashing)
Rehash: On each add/delete, copy 1 bucket from old to new
```

**Incremental rehash**: Avoid blocking. Redis does `dictRehashMilliseconds(1)` per event loop iteration—rehashes for 1ms max.

---

## 2. Eviction Structure by Policy

### 2.1 LRU: Doubly Linked List + HashMap

```
HashMap: key → CacheEntry
DLL:     head (LRU) ←→ ... ←→ tail (MRU)

On access: unlink from current pos, append to tail. O(1).
On evict:  remove head. O(1).
```

**Redis LRU**: Approximate—24-bit LRU clock, sampled on access. Not true LRU; saves 16 B per key (no prev/next). See Deep Dive 1.

**Memory per entry**:
- True LRU: 2×8 B (prev, next) = 16 B
- Redis approx: 24-bit timestamp = 3 B

### 2.2 LFU: O(1) Implementation (Freq Buckets)

```
Freq 1:  [e1] ←→ [e2] ←→ [e3]   (DLL)
Freq 2:  [e4] ←→ [e5]
Freq 3:  [e6]

HashMap: key → (value, ptr to node in freq bucket)
On access: move node from freq bucket F to F+1. O(1).
On evict: remove from lowest non-empty bucket head. O(1).
```

**Redis LFU**: 8-bit counter (log scale) + 16-bit decay time. Morris counter for approximate count. Max 255.

**Memory**: 1 ptr (8 B) to freq bucket node.

### 2.3 TTL: Expiry Structures

| Structure | Add | Remove | Evict | Memory |
|-----------|-----|--------|-------|--------|
| Min-heap by expiry | O(log n) | O(log n) | O(1) | 8 B ptr |
| Time-wheel | O(1) | O(1) | O(1) | 8 B per slot |
| Red-black tree | O(log n) | O(log n) | O(1) | 24 B |

**Redis**: Expires dict (key → timestamp) + lazy delete on access + active expire cycle (random sample). No global heap—per-key expiry in dict.

### 2.4 W-TinyLFU (Caffeine)

```
Window Cache (1%):  LRU, small
Main Cache (99%):   SLRU (Segmented LRU)
Admission:          Count-Min Sketch for frequency
                    Admit from window to main only if new freq > victim's
```

**Memory**: Count-Min Sketch ~4 B per counter × number of counters. Compact.

---

## 3. Off-Heap Storage

### 3.1 Memcached Slab Allocator

```
Slab Class 1:  96 B chunks   (88 B usable)
Slab Class 2:  120 B chunks
Slab Class 3:  152 B chunks
...
Slab Class N:  ~1 MB chunks

Each slab = 1 MB page, divided into equal chunks.
Allocation: Find smallest class that fits → get free chunk. O(1).
```

**Fragmentation**: Internal (chunk larger than value) and external (unused chunks). Memcached has `slab_reassign` to move pages between classes.

**Size classes**: 1.25× growth (96, 120, 152, ...). Or 2× for simpler math.

### 3.2 Redis / jemalloc

**Redis**: Uses libc malloc by default; jemalloc recommended. `zmalloc` wrapper tracks allocations for `INFO memory`.

**jemalloc**: Arena-based, size classes, thread-local caches. Reduces fragmentation vs dlmalloc. Used by Redis, Facebook, FreeBSD.

**Memory layout**:
```
Arena → Runs (contiguous pages) → Size classes
Thread cache → Small allocations served without lock
```

### 3.3 Off-Heap in Java (ByteBuffer)

```java
ByteBuffer buffer = ByteBuffer.allocateDirect(size);  // Off-heap
// Or: Unsafe.allocateMemory(size)
```

**Pros**: No GC for data. **Cons**: Manual free; serialization overhead. Used by Chronicle Map, Hazelcast for large caches.

---

## 4. Redis Internal Data Structures (Reference)

### 4.1 String (SDS)

```
struct sdshdr {
  int len;      // 4 B
  int alloc;    // 4 B
  char flags;   // 1 B
  char buf[];   // Flexible array
}
```

**Optimization**: For small strings (< 44 B on 64-bit), embedded in RedisObject. No separate allocation.

### 4.2 List (quicklist)

**Redis 3.2+**: Linked list of ziplists. Each ziplist ~8 KB. Compresses sequential small entries.

**Ziplist**: Compact encoding—no pointers, length-prefixed. Good for small lists.

### 4.3 Hash (ziplist or hashtable)

- Small (< 512 entries, configurable): ziplist. Compact.
- Large: hashtable (dict).

### 4.4 Sorted Set (zskiplist + dict)

- **Skip list**: O(log n) insert, delete, range. Probabilistic levels.
- **Dict**: key → score for O(1) score lookup.
- **Memory**: ~40 B per element (skip list node + dict entry).

### 4.5 Set (intset or hashtable)

- Small (all ints, < 512): intset—sorted array. Compact.
- Large or mixed: hashtable.

---

## 5. Memory Fragmentation

### 5.1 Fragmentation Ratio

```
mem_fragmentation_ratio = used_memory_rss / used_memory

RSS = Resident Set Size (actual physical memory)
used_memory = logical allocation
```

**> 1.5**: Significant fragmentation. Allocator overhead, external fragmentation.  
**< 1**: Swap or shared memory. Investigate.

### 5.2 Redis Active Defragmentation (4.0+)

- **Background**: Scans and moves objects to coalesce free space.
- **Config**: `activedefrag yes`, `active-defrag-threshold-lower 10` (start when frag > 10%).
- **Cost**: CPU. Runs incrementally to avoid latency spikes.

### 5.3 Mitigation Strategies

| Strategy | How |
|----------|-----|
| **Slab allocator** | Fixed sizes reduce external frag |
| **jemalloc** | Better than glibc malloc |
| **Value size limit** | Reject very large values; use object store |
| **Compression** | Smaller values = less frag |
| **Restart** | Periodic restart to reclaim (with persistence) |

---

## 6. CacheEntry Memory Layout (Production)

### 6.1 Compact Layout (C-style)

```c
struct CacheEntry {
  uint32_t  key_len;
  uint32_t  value_len;
  uint32_t  flags;        // TTL, priority, etc.
  uint32_t  lru_bits;     // 24-bit for Redis-style approx LRU
  int64_t   expire_at_ms;
  uint64_t  version;
  char      data[];       // key \0 value (inline)
};
```

**Total**: 32 B metadata + key_len + value_len. Inline key/value avoids indirection.

### 6.2 With Eviction Metadata (LRU)

```c
struct CacheEntryLRU {
  CacheEntry base;
  CacheEntry* prev;
  CacheEntry* next;
};
// +16 B for DLL
```

### 6.3 With Eviction Metadata (LFU)

```c
struct CacheEntryLFU {
  CacheEntry base;
  uint16_t  freq;
  uint16_t  decay_time;   // For logarithmic decay
  LFUBucket* bucket;
};
// +8-16 B
```

---

## 7. Hash Ring Schema (Distributed)

```
Tokens:  Sorted array of (hash, node_id)
         Binary search: O(log V) where V = virtual nodes

Virtual nodes:  V = N × 100 to N × 200
                N = physical nodes
                Total tokens: 10,000 to 20,000 for 100 nodes

Per token: 8 B (hash) + 8 B (node_id ptr) = 16 B
Total: 20,000 × 16 B = 320 KB (negligible)
```

---

## 8. Persistence Schema (Redis-style)

### 8.1 RDB (Snapshot)

```
Format: Binary. Magic "REDIS", version, DB selector, key-value pairs, EOF.

Key-value: Type (1 B), key (len+bytes), value (type-specific encoding).

Compression: Optional LZF for values.
```

**Size**: Roughly equal to used_memory. Save time: O(n) where n = key count.

### 8.2 AOF (Append-Only Log)

```
Format: *3\r\n$3\r\nSET\r\n$4\r\nkey1\r\n$5\r\nvalue\r\n
        (Redis protocol: number of args, length-prefixed strings)
```

**Rewrite**: Compact AOF by replaying to in-memory state, writing new AOF. Reduces size.

**fsync**: always (every write), everysec (batch), no (OS decides).

---

## 9. Summary: Memory Budget per 1M Keys

| Component | Bytes/Key | 1M Keys |
|-----------|-----------|---------|
| Key (avg 50 B) | 50 | 50 MB |
| Value (avg 5 KB) | 5120 | 5 GB |
| Hash entry | 32 | 32 MB |
| LRU metadata | 16 | 16 MB |
| **Total** | **~5.2 KB** | **~5.2 GB** |

**Overhead**: ~4% (200 MB for 5 GB values). Dominated by value size.
