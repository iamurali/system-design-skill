# Bottlenecks and Tradeoffs — In-Memory Cache (Staff-Level)

## 1. Real Incident Examples

### 1.1 Facebook Memcache Cascade Failure (2010)

**What happened**: A configuration change caused many Memcached servers to restart simultaneously. Cache was cold. All requests fell through to MySQL. MySQL couldn't handle the load. Cascading failure.

**Root cause**: Cache as critical path. No graceful degradation. DB not sized for 100% cache miss rate.

**Lessons**:
- **Never assume cache**: Design for 100% cache miss. DB must handle full load (or reject with backpressure).
- **Stagger restarts**: Rolling deploy; never restart all cache nodes at once.
- **Warm-up**: Preload hot keys before traffic. Or ramp traffic slowly.

### 1.2 GitHub Redis Failover (2016)

**What happened**: Redis Sentinel promoted replica to master. Replication lag caused data loss. Some writes to old master were not replicated.

**Root cause**: Async replication. Failover during write burst. Replica missing recent writes.

**Lessons**:
- **Replication lag monitoring**: Alert when lag > 10s. Avoid failover during high lag.
- **Accept data loss for cache**: Cache is ephemeral. Document. Repopulate from DB.
- **Sync replication for critical**: If cache holds primary data, use sync replicate (with latency cost).

### 1.3 LinkedIn Feed Cache Stampede (Historical Pattern)

**What happened**: Popular post caused spike in feed fragment requests. Fragment cache expired. Thousands of requests hit feed computation service. Service overloaded.

**Root cause**: No request coalescing. No jitter on TTL. Thundering herd.

**Lessons**:
- **Singleflight**: Coalesce concurrent loads for same key.
- **TTL jitter**: Add random 0–20% to TTL to spread expiry.
- **Probabilistic early expiry**: Spread load near expiry.

### 1.4 Redis Memory Fragmentation (Common)

**What happened**: `used_memory_rss` grew to 2× `used_memory`. OOM killer terminated process. Restart; repeat.

**Root cause**: Many small allocations; mixed sizes. jemalloc fragmentation. No active defrag.

**Lessons**:
- **Monitor frag ratio**: Alert when > 1.5.
- **Active defrag**: Enable in Redis 4+. Tune CPU limits.
- **Restart with RDB**: Periodic restart to reclaim. Plan for it.

---

## 2. Network Partition Handling

### 2.1 Split-Brain Scenario

```
        ┌─────────┐         ┌─────────┐
        │ Node A  │         │ Node B  │
        │(Master) │   X     │(Replica)│
        └────┬────┘         └────┬────┘
             │                   │
        Partition                │
             │                   │
        ┌────▼────┐         ┌────▼────┐
        │Client 1 │         │Client 2 │
        │writes   │         │writes   │
        └─────────┘         └─────────┘
```

**Result**: A and B both accept writes. Divergent state. On heal: conflict.

### 2.2 Mitigation

| Strategy | How | Trade-off |
|----------|-----|-----------|
| **Quorum writes** | Write to N/2+ nodes. Partition with minority can't write. | Higher latency |
| **Last-writer-wins** | On heal, merge by timestamp. | Clock skew risk |
| **Prefer availability** | Serve from partition. Accept divergence. Reconcile later. | Stale reads |
| **Fail fast** | If partition detected, reject writes. | Availability hit |

**Cache recommendation**: Prefer availability. Cache is best-effort. DB is source of truth. On heal, invalidate conflicting keys; repopulate from DB.

### 2.3 Redis Sentinel and Partitions

- Sentinel uses **Raft-like** consensus. Quorum required for failover.
- If partition splits Sentinels: minority partition can't failover. No split-brain in Sentinel.
- If partition splits master from replicas: master in minority keeps accepting writes. Replicas in majority may elect new master. **Two masters** until heal. Redis Cluster uses config epoch to resolve.

---

## 3. Capacity Planning and Scaling Triggers

### 3.1 When to Scale

| Signal | Threshold | Action |
|--------|-----------|--------|
| **Memory usage** | > 85% maxmemory | Add nodes or increase memory |
| **Eviction rate** | > 1% of puts | Cache too small; add capacity |
| **Hit ratio** | < 90% (expected 95%) | Under-provisioned or wrong eviction policy |
| **Connection count** | > 80% maxclients | Add proxy or scale clients |
| **CPU** | > 70% sustained | Scale out (more nodes) |
| **Network** | > 70% bandwidth | Scale out |

### 3.2 Memory Pressure Signals

- **Evictions**: High `evicted_keys` rate. Indicates cache too small.
- **Fragmentation**: `mem_fragmentation_ratio` > 1.5. Restart or active defrag.
- **RSS growth**: Steady growth without key growth. Possible leak or fragmentation.

### 3.3 Forecasting

- **Linear extrapolation**: Plot memory over time. Extrapolate to capacity limit.
- **Growth events**: New features, traffic spikes. Model in forecast.
- **Rule**: Plan to add capacity when 6-month forecast exceeds 80% of current capacity.

---

## 4. Cost Analysis

### 4.1 Memory vs Compute vs Network

| Resource | Cost Driver | Optimization |
|----------|-------------|--------------|
| **Memory** | $/GB/month. Dominant for cache. | Smaller values, compression, eviction |
| **Compute** | CPU for serialization, eviction, network. | Pipelining, connection pooling |
| **Network** | Cross-AZ/DC traffic. | Local L1, same-AZ L2 |

**Typical**: Memory is 60–80% of cache cost. Optimize value size, hit ratio.

### 4.2 Cost per Request

```
Cost = (Memory_cost × working_set) + (Compute_cost × ops) + (Network_cost × bytes)

Per 1M requests:
  Memory: Amortized. ~$X per GB-month.
  Compute: Negligible for cache (100K ops/sec per core).
  Network: $Y per GB egress.
```

**Hit ratio impact**: 95% hit vs 80% hit = 5× fewer DB loads. DB cost often dominates; cache pays for itself.

---

## 5. Monitoring: Metrics to Alert On

### 5.1 Critical Alerts (Page On-Call)

| Metric | Threshold | Why |
|--------|-----------|-----|
| **Error rate** | > 0.1% | Availability SLA breach |
| **P99 latency** | > 5 ms | User-visible slowness |
| **Unavailable** | Any | Node down, partition |
| **Replication lag** | > 30 s | Failover risk; stale reads |

### 5.2 Warning Alerts (Investigate)

| Metric | Threshold | Why |
|--------|-----------|-----|
| **Hit ratio** | < 90% | Under-provisioned or policy wrong |
| **Eviction rate** | > 10K/sec | Cache too small |
| **Memory** | > 90% maxmemory | Near OOM |
| **Connections** | > 80% maxclients | Connection exhaustion |
| **Fragmentation** | > 1.5 | Memory waste; OOM risk |

### 5.3 Dashboard Panels

```
┌─────────────────────────────────────────────────────────────────┐
│  Request Rate (reads, writes, misses)                            │
├─────────────────────────────────────────────────────────────────┤
│  Latency (P50, P95, P99 by operation)                            │
├─────────────────────────────────────────────────────────────────┤
│  Hit Ratio (hits / (hits + misses))                              │
├─────────────────────────────────────────────────────────────────┤
│  Memory (used, max, fragmentation ratio)                        │
├─────────────────────────────────────────────────────────────────┤
│  Evictions (rate, policy)                                        │
├─────────────────────────────────────────────────────────────────┤
│  Connections (current, rejected)                                 │
├─────────────────────────────────────────────────────────────────┤
│  Replication (lag, sync status)                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.4 SLO/SLI Definitions

| SLI | Definition | Target |
|-----|------------|--------|
| **Availability** | Successful requests / Total requests | 99.99% |
| **Latency** | P99 of GET/PUT | < 2 ms |
| **Hit ratio** | Hits / (Hits + Misses) | > 95% |

**Error budget**: 0.01% = 43 min downtime/month. Track consumption.

---

## 6. Anti-Patterns

### 6.1 Cache as Source of Truth

**Anti-pattern**: Application writes to cache only. DB is backup. Cache is authoritative.

**Risk**: Cache loss = data loss. Replication lag = inconsistency. Failover = data loss.

**Correct**: DB is source of truth. Cache is performance optimization. Write to DB first; then cache.

### 6.2 Unbounded Caches

**Anti-pattern**: No maxmemory. Cache grows until OOM.

**Risk**: OOM kill. No eviction. Unpredictable behavior.

**Correct**: Always set `maxmemory`. Choose eviction policy. Monitor.

### 6.3 Missing Circuit Breakers

**Anti-pattern**: Client retries forever when cache node down. Threads block. Cascading failure.

**Risk**: One bad node exhausts all client connections. App hangs.

**Correct**: Circuit breaker. After N failures, fail fast. Recover after sleep window.

### 6.4 No Connection Limits

**Anti-pattern**: Each app instance opens 1000 connections to cache. 100 instances = 100K connections. Cache `maxclients` exceeded.

**Risk**: Rejected connections. Errors. Cascading failure.

**Correct**: Connection pooling. Limit per instance. `max_clients` on server. Plan total.

### 6.5 Cache Invalidation Bugs

**Anti-pattern**: Update DB but forget to invalidate cache. Stale reads indefinitely.

**Risk**: Users see old data. Consistency bugs.

**Correct**: Invalidate on write. Or use TTL. Or event-driven invalidation (CDC).

### 6.6 Hot Key in Application

**Anti-pattern**: One key (e.g., config) fetched on every request. No local cache. 100K req/sec to one cache key.

**Risk**: Overload cache node. Single point of failure.

**Correct**: Local cache (L1) for hot keys. Or replicate. Or split key.

---

## 7. Failure Scenario Matrix

| Failure | Impact | Detection | Mitigation |
|---------|--------|------------|------------|
| **Node crash** | Keys unavailable | Health check fail | Replica serves; rebalance |
| **Replica crash** | No read scaling | Replica down | Add replica; no immediate impact |
| **Network partition** | Split-brain, stale reads | Sentinel, timeout | Quorum; prefer availability |
| **Proxy overload** | All requests slow | Proxy CPU, latency | Scale proxies; client-side routing |
| **Full cluster restart** | Total cache loss | Planned | Persistence; warm from DB |
| **Eviction storm** | High latency, DB load | Eviction rate | Soft limit; background evictor |
| **Hot key** | One node overloaded | Per-key metrics | L1, replication, split |
| **Memory leak** | OOM eventually | RSS growth | Restart; fix leak |
| **Fragmentation** | OOM, slow alloc | Frag ratio | Active defrag; restart |

---

## 8. Consistency vs Availability Tradeoffs

### 8.1 CAP in Practice

**Partition**: Network splits cluster. Must choose.

| Choice | Implication |
|--------|-------------|
| **Consistency** | Reject writes in minority partition. Availability hit. |
| **Availability** | Serve from partition. Possible stale reads. |

**Cache**: Choose availability. Stale cache acceptable. DB is truth.

### 8.2 PACELC

- **If Partition (P)**: Choose A (availability) or C (consistency).
- **Else (E)**: Choose L (latency) or C (consistency).

**Cache**: PA. When partitioned, available. Else, low latency (async replicate).

### 8.3 When Strong Consistency

- Session data (read-your-writes)
- Rate limits (over-count bad)
- Distributed locks

**Cost**: Sync replication. Higher latency. More failure modes.

---

## 9. Summary: Staff-Level Checklist

| Area | Key Points |
|------|------------|
| **Incidents** | Design for cache miss; stagger restarts; warm-up; singleflight |
| **Partitions** | Prefer availability; document stale reads; reconcile on heal |
| **Capacity** | Monitor memory, eviction, hit ratio; plan 6 months ahead |
| **Cost** | Memory dominates; hit ratio saves DB cost |
| **Monitoring** | Latency, hit ratio, memory, eviction, replication lag |
| **Anti-patterns** | DB is truth; bounded cache; circuit breakers; connection limits |
| **Tradeoffs** | Eventual consistency for low latency; strong when required |
