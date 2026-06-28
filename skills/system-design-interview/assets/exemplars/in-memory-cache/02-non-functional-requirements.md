# Non-Functional Requirements — In-Memory Cache (Staff-Level)

## 1. Latency SLAs

### 1.1 Percentile Targets

| Percentile | Single-Node | Same-DC Distributed | Cross-DC |
|------------|-------------|----------------------|----------|
| **P50** | < 200 μs | < 500 μs | < 5 ms |
| **P95** | < 500 μs | < 1 ms | < 10 ms |
| **P99** | < 1 ms | < 2 ms | < 20 ms |
| **P99.9** | < 5 ms | < 10 ms | < 50 ms |

**Rationale**: Cache is on the critical path for feed, profile, and auth. P99 > 5 ms causes user-visible slowness. Cross-DC is for read replicas only; writes stay local.

### 1.2 Latency Budget Breakdown

```
Total P99 = Client→Proxy + Proxy→Node + Lookup + Serialization + Response
          = 100μs + 100μs + 50μs + 100μs + 100μs ≈ 450μs (target)
```

**Tail latency causes**: GC pauses (mitigate with off-heap or G1/ZGC), lock contention, eviction storms, network jitter.

### 1.3 No Disk I/O on Hot Path

- All reads and writes served from RAM.
- Persistence (RDB, AOF) is **async** and must not block GET/PUT.
- `fsync` policies: `everysec` (Redis default) or `no` for pure cache; `always` only for cache-as-primary-store.

---

## 2. Availability Targets

### 2.1 Uptime SLAs

| Tier | Target | Downtime/Year | Use Case |
|------|--------|---------------|----------|
| **L1 (local cache)** | 99.9% | 8.76 hr | Best-effort; fallback to L2 |
| **L2 (distributed)** | 99.95% | 4.38 hr | Feed, profile cache |
| **L2 (critical)** | 99.99% | 52.6 min | Session, auth cache |

### 2.2 Error Budget Math

**SRE-style error budget**: 99.99% = 0.01% failure budget.

- **Per month**: 43.2 minutes allowed downtime.
- **Per week**: ~10 minutes.
- **Budget consumption**: Failed requests count. 0.01% of 1M req/sec = 100 failed req/sec = budget burn.

**Implication**: Single node failure must NOT exhaust budget. Replicas + automatic failover required. Planned maintenance (deploys, scaling) should consume minimal budget.

### 2.3 Replication for HA

| Config | Failover | Availability | Consistency |
|--------|----------|--------------|-------------|
| 1 replica | Manual or Sentinel | 99.9% | Eventual |
| 2 replicas | Auto (quorum) | 99.99% | Eventual |
| 3 replicas + quorum read | Auto | 99.99% | Stronger (read-your-writes possible) |

**Failover time**: Target < 30 seconds (Redis Sentinel: 10–30s). During failover, writes may fail; reads from old replica may be stale.

### 2.4 Graceful Degradation

- **Node failure**: Route to replica. If no replica, return cache miss (application hits DB).
- **Replica lag**: Serve stale read if primary down; accept temporary inconsistency.
- **Cluster partition**: Prefer availability (serve from partition with majority) over consistency. Document stale reads.

---

## 3. Consistency Model

### 3.1 When to Use Strong Consistency

| Scenario | Rationale |
|----------|-----------|
| Session data | User must see own writes immediately |
| Rate limit counters | Over-counting could block legitimate users |
| Leader election / distributed lock | Strong consistency required |

**Cost**: Sync replication, higher latency, more failure modes (replica slow = write slow).

### 3.2 When to Use Eventual Consistency

| Scenario | Rationale |
|----------|-----------|
| Profile cache | Stale profile for seconds is acceptable |
| Feed cache | Stale feed; next refresh gets latest |
| Counters (view counts) | Slight under-count acceptable |

**Cost**: After failover, new primary may lack recent writes. Read-your-writes via sticky routing (same client → same primary) reduces visibility.

### 3.3 Cache-aside Semantics

- **Cache is not source of truth**. DB is authoritative.
- **Best-effort**: Cache miss → read from DB → populate cache.
- **Invalidation**: On DB write, invalidate (delete) cache key. Next read repopulates.
- **Consistency**: Eventual. Time-to-consistency = TTL or invalidation latency.

### 3.4 Read-Your-Writes

For strong read-your-writes in distributed cache:
- **Sticky routing**: Route client to same primary (by client ID or session).
- **Version vector**: Cache stores version; client sends "I've seen v5"; server returns if v > 5 or refetch.
- **Lease-based**: Facebook Memcache paper—lease prevents stale read after invalidation.

---

## 4. Durability Guarantees

### 4.1 Cache vs Durable Store

| Guarantee | Cache | Durable Store |
|-----------|-------|---------------|
| Survives process crash | No (unless RDB/AOF) | Yes |
| Survives node failure | No (replica may have partial) | Yes |
| Survives DC failure | No | Yes (with replication) |

**Design principle**: Cache is ephemeral. Never rely on cache for durability. Persistence (RDB, AOF) is for **fast restart**, not durability.

### 4.2 On Node Failure

| Scenario | Behavior |
|----------|----------|
| **Primary crash** | Replica promoted. Writes since last sync may be lost. Acceptable for cache. |
| **Replica crash** | No impact on reads. Replicate to new replica when added. |
| **Full shard loss** | All keys in shard lost. Application gets cache miss → DB. Repopulate over time. |
| **Network partition** | Split-brain. Each partition serves; may diverge. Reconcile on heal (last-writer-wins or merge). |

### 4.3 Persistence Modes (Redis-style)

| Mode | Durability | Restart time | Use case |
|------|------------|--------------|----------|
| **None** | None | N/A | Pure cache |
| **RDB only** | Crash-consistent snapshot | Fast (load snapshot) | Warm restart |
| **AOF only** | Every write logged | Slower (replay log) | Higher durability |
| **RDB + AOF** | Snapshot + incremental | Fast load + replay tail | Production cache with warm restart |

---

## 5. Operational Requirements

### 5.1 Zero-Downtime Deployments

- **Rolling deploy**: One node at a time. Drain connections, stop, deploy, start. Hash ring shrinks temporarily; keys rebalance to other nodes.
- **Config changes**: `maxmemory-policy`, `maxmemory`—Redis supports `CONFIG SET` at runtime. No restart for policy change.
- **Scaling**: Add nodes; consistent hashing minimizes migration. Rebalance can be gradual (background migration) or immediate (keys move on next access).

### 5.2 Capacity Planning

- **Memory growth**: Monitor `used_memory`, `used_memory_rss`. Alert when > 80% of `maxmemory`.
- **Key count**: Monitor `keyspace` (keys per DB). Correlate with memory.
- **Eviction rate**: `evicted_keys` / time. High rate = under-provisioned or hot set larger than cache.
- **Forecasting**: Linear extrapolation from growth rate. Plan to add nodes when 6-month projection exceeds capacity.

### 5.3 Monitoring & Alerting

#### Critical Alerts

| Metric | Threshold | Action |
|--------|-----------|--------|
| Error rate | > 0.1% | Page on-call |
| P99 latency | > 5 ms | Page |
| Hit ratio | < 90% (if expected 95%) | Investigate |
| Eviction rate | > 10K/sec sustained | Scale or tune |
| Memory usage | > 90% maxmemory | Scale |
| Rejected connections | > 0 | Connection limit hit |
| Replica lag | > 10 sec | Failover risk |

#### Dashboards

- **Request rate** (reads, writes, misses)
- **Latency** (P50, P95, P99 by operation)
- **Hit ratio** (hits / (hits + misses))
- **Memory** (used, peak, fragmentation ratio)
- **Connections** (current, rejected)
- **Evictions** (rate, policy)
- **Replication** (lag, sync status)

### 5.4 Runbooks

- **Node OOM**: Identify cause (large values? leak?). Restart node; replica serves. Scale if recurring.
- **Hot key**: Identify via `--hotkeys` (Redis 4) or sampling. Mitigate with local cache, replication, key splitting.
- **Failover**: Verify replica promoted. Check replication lag. Drain old primary if partitioned.
- **Cache stampede**: Enable request coalescing, add jitter to TTL, consider probabilistic early expiry.

---

## 6. Scalability NFRs

### 6.1 Horizontal Scaling

- **Add node**: O(K/N) keys migrate. No full rehash.
- **Remove node**: Same. Keys move to next node in ring.
- **Linear throughput**: 2x nodes ≈ 2x throughput (until network or client limit).

### 6.2 Vertical Scaling

- **Memory**: 64–256 GB per node common. Beyond that, GC pressure (Java) or fragmentation (C) may dominate.
- **CPU**: Redis single-threaded for commands; `io-threads` (Redis 6+) for network. Multi-core helps with connection handling.
- **Network**: 10–25 Gbps per node. Scale out before single-node network saturation.

---

## 7. Security NFRs

- **Encryption in transit**: TLS for client connections. Mandatory in multi-tenant.
- **Encryption at rest**: If persistence enabled, encrypt RDB/AOF.
- **Access control**: ACLs per key prefix or command. No `FLUSHALL` for app clients.
- **Audit**: Log admin operations (flush, config change, node add/remove).

---

## 8. Summary Matrix

| NFR | Target |
|-----|--------|
| P99 latency | < 2 ms (same DC) |
| Availability | 99.99% (with replication) |
| Consistency | Eventual (default); strong when needed |
| Durability | Best-effort; DB is source of truth |
| Failover | < 30 sec |
| Deploy | Zero-downtime rolling |
| Monitoring | Latency, hit ratio, memory, eviction, replication |
