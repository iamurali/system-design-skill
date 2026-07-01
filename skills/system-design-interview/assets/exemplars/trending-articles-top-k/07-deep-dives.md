# Deep Dives — Trending Articles / Top-K

## Deep Dive 1: Count-Min Sketch

### Workable

Fixed-size `d × w` counter array; update all `d` rows on each event; query returns min across rows.

**Limitations:** Overcounts on collisions; memory grows with ε; conservative merge invalid for distributed merge.

### Strong

Pairwise-independent hashes; width `w = ⌈e/ε⌉`, depth `d = ⌈ln(1/δ)⌉`. For ε=0.01, δ=0.001: w=272, d=7 → **7.4 KB/sketch**. 6,000 segments ≈ 44 MB.

**New challenges:** Heavy-tail items suffer collision bias; need conservative update (no cross-partition merge).

### Exceptional

**CMS update pseudocode:**

```python
for row in range(d):
    counters[row][h[row](content_id) % w] += weight
estimate = min(counters[row][h[row](content_id) % w] for row in range(d))
```

**Raft-style checkpoint sequence:** barrier inject → align checkpoints → persist to S3 → acknowledge → resume consumption.

**Sizing derivation:** P(estimate ≤ n_x + εN) ≥ 1−δ with w=⌈e/ε⌉.

**Breaking point:** At **500K QPS** per segment, single sketch update becomes CPU-bound (d=7 hashes × 500K = 3.5M ops/s per core).

**Resiliency pattern:** Replicate sketch state in Flink checkpoint every **5 min**; on failure, replay Kafka from offset with idempotent CMS updates.

### Curveball: What if writes go 10×?

1. **Constraint change:** 500K peak write QPS.
2. **Invalidated assumption:** Single-task sketch per segment fits in memory with <50ms update latency.
3. **Blast radius:** Flink aggregation layer only; ingestion and Redis serving unchanged.
4. **Scoped redesign:** Shard aggregation by `hash(content_id) % 32`; periodic merge job for global top-K.
5. **Verification:** Read path and Kafka retention still hold; only merge latency added (~30s).

---

## Deep Dive 2: Sliding Window Implementation

### Workable

Tumbling 1-hour buckets; cron aggregates each hour.

**Limitations:** Boundary artifacts at hour edges; rank jumps at rollover.

### Strong

```python
# Hopping window: 1h window, 1min slide
for pane in panes_in_window(event_time):
    sketch[segment][pane].update(content_id, weight)
```

**New challenges:** O(W/H) active panes; state size grows linearly with hop frequency.

### Exceptional

```java
// Flink allowedLateness + side output for late events
stream
  .keyBy(content_id)
  .window(TumblingEventTimeWindows.of(Time.hours(1)))
  .allowedLateness(Time.seconds(120))
  .sideOutputLateData(lateTag)
  .aggregate(new TrendingAggregate());
```

```python
# Global top-K merge every 30s
global_topk = heap_merge([partition.topk(100) for partition in partitions])
redis.zadd(segment_key, global_topk)
```


**Breaking point:** At **10× event rate**, sliding (not hopping) requires O(60) panes per key → **state exceeds 64 GB** per task slot.

**Resiliency pattern:** `allowedLateness=120s`; late events to side output; **retry budget** 3 retries with exponential backoff for Redis sink.

### Curveball: What if event-time delay P99 goes to 5 minutes?

1. **Constraint change:** Mobile offline queue flush delays events 5 min.
2. **Invalidated assumption:** 10s watermark slack sufficient.
3. **Blast radius:** Window closure timing; serving freshness.
4. **Scoped redesign:** Extend allowed lateness; serve with `X-Trending-Staleness` header; batch correction job for 24h window.
5. **Verification:** Abuse gates and read API unchanged.

---

## Deep Dive 3: Global Top-K Merge

### Workable

Each Kafka partition maintains local top-100 heap; API reads single partition's view.

**Limitations:** Incorrect global top-K; only valid for single-partition prototypes.

### Strong

Two-phase: partition-local top-K → merge job every 30s → global Redis ZSET.

**New challenges:** Merge lag 30s; merge service SPOF without standby.

### Exceptional

**Complexity:** Local heap insert O(log K), K=100; merge of P partitions O(P·K log K) every 30s — at P=200, negligible vs network.

**Breaking point:** At **100× scale**, merge job input = 200 × 100 = 20K items × 500B × 2/s = **20 MB/s** merge traffic — still fine; **Redis global key** becomes hot spot at **>500K read QPS**.

**Resiliency pattern:** Circuit breaker on merge service: **50% error rate over 10s → open 30s**; serve partition-local top-K degraded mode.

### Curveball: What if we need exact top-10 globally?

1. **Constraint change:** Regulatory audit requires exact counts for top-10.
2. **Invalidated assumption:** Approximate CMS acceptable.
3. **Blast radius:** Counting layer only.
4. **Scoped redesign:** Exact Space-Saving for top-10 candidates only + CMS for tail; hourly batch reconciliation from warehouse.
5. **Verification:** API contract unchanged; freshness SLA relaxed for audit window.

---

## Deep Dive 4: Abuse Gate Pipeline

### Workable

Static bot list filter before Kafka.

**Limitations:** Cannot catch new bots; false negatives on coordinated campaigns.

### Strong

Reputation score threshold (0.3) + velocity anomaly (10× baseline in 1 min) + content quality classifier.

**New challenges:** False positives suppress organic viral content; latency +5ms per event.

### Exceptional

**Order of operations:** `reputation → bot list → velocity → quality → count` — early exit saves 40% CPU on blocked events.

**Breaking point:** At **>100K rejected events/s**, audit log write path saturates Postgres audit table (**~5K write QPS** limit).

**Resiliency pattern:** Async audit to Kafka topic `trending-abuse-audit`; bulkhead thread pool **10 threads** for audit separate from hot path.

### Curveball: What if attackers spoof high-reputation accounts?

1. **Constraint change:** Compromised high-rep accounts pass gate.
2. **Invalidated assumption:** Static reputation sufficient.
3. **Blast radius:** Abuse gate only.
4. **Scoped redesign:** Add graph-based coordinated-engagement detector; delay trend emission 2 min for anomalous velocity clusters.
5. **Verification:** Stream topology unchanged; added side branch for anomaly scoring.
