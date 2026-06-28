# Deep Dives — Trending Articles / Top-K

## Deep Dive 1: Count-Min Sketch Internals

### Structure

- **d rows × w columns** of counters
- **d independent hash functions** \(h_1, \ldots, h_d\), each mapping item \(x\) to a column in \(\{0, \ldots, w-1\}\)
- **Update**: For item \(x\) and increment \(c\): for each row \(i\), do `counters[i][h_i(x) % w] += c`
- **Query**: Return \(\min_i \text{counters}[i][h_i(x) \bmod w]\) — always overcounts or exact, never undercounts

### Hash Function Selection

- **Pairwise independent** hash family: \(\Pr[h_i(x) = a \wedge h_i(y) = b] = 1/w^2\) for \(x \neq y\)
- **Construction**: \(h(x) = ((a \cdot x + b) \bmod p) \bmod w\) where \(a, b\) random in \(\mathbb{Z}_p\), \(p\) prime
- **Tabulation hashing**: Alternative; faster in practice; 4–8 bits per character
- **MurmurHash, xxHash**: Good for CMS; use different seeds per row

### Width and Depth Sizing

**Theorem** (Cormode & Muthukrishnan): With probability at least \(1 - \delta\), the estimate \(\hat{n}_x\) for true count \(n_x\) satisfies:
\[
\hat{n}_x \leq n_x + \frac{\varepsilon}{e} \cdot N
\]
where \(N\) = total stream size, with:
- **Width**: \(w = \lceil e / \varepsilon \rceil\)
- **Depth**: \(d = \lceil \ln(1/\delta) \rceil\)

**Examples**:
| ε | δ | w | d | Memory (d×w×4 bytes) |
|---|---|-----|---|----------------------|
| 0.01 | 0.001 | 272 | 7 | ~7.4 KB |
| 0.001 | 0.0001 | 2719 | 9 | ~98 KB |
| 0.05 | 0.01 | 55 | 5 | ~1.1 KB |

For trending: ε ≈ 0.01–0.05, δ ≈ 0.001 → w ≈ 55–272, d ≈ 5–7. In practice, w = 2^16–2^18 for high cardinality.

### Conservative Update Optimization

- **Standard**: Increment all d counters
- **Conservative**: Only increment the **minimum** counter among the d cells — reduces overcount
- **Tradeoff**: Conservative reduces overcount (empirically 30–50%) but breaks linearity — **merge of two conservative sketches is not valid**. Use only when merge not needed (single partition).

### Count-Min-Log for Heavy Tails

- **Problem**: CMS overcounts heavily for items with many collisions; heavy tail (few items with huge counts) suffers
- **Count-Min-Log**: Store log(1 + count) instead of count; reduces impact of collisions on heavy hitters
- **Merge**: Approximate; not linear

### Count-Sketch (Unbiased Estimator)

- **Structure**: Similar to CMS but with **signed** updates: increment or decrement based on sign hash \(s_i(x) \in \{-1, +1\}\)
- **Query**: Median of d estimates (each row gives signed estimate)
- **Property**: Unbiased — \(\mathbb{E}[\hat{n}_x] = n_x\); variance depends on w, d
- **Use case**: When undercount is as bad as overcount; when unbiased estimate needed

**Comparison**: CMS overcounts; Count-Sketch unbiased but higher variance. For trending (ranking), overcount is acceptable → CMS preferred.

---

## Deep Dive 2: Sliding Window Implementation

### Tumbling Windows

- **Definition**: Fixed-size, non-overlapping. Window 1: [0, 1h), Window 2: [1h, 2h), ...
- **Pros**: Simple; deterministic; low state (one bucket per window)
- **Cons**: Boundary artifacts — item at 0:59 and 1:01 are in different windows; rank can jump at boundaries

### Sliding Windows

- **Definition**: Window of size W slides by 1 unit. At time t, window = [t-W, t).
- **Pros**: Smooth; no boundary jump
- **Cons**: Expensive — O(W) windows active; each event updates O(W) windows

### Hopping Windows

- **Definition**: Window size W, advance by hop H (H < W). Overlap = W - H.
- **Example**: 1h window, 5min hop → windows at 0:00, 0:05, 0:10, ...
- **Pros**: Balance — reduces boundary artifacts; O(W/H) windows vs O(W) for sliding
- **Cons**: Still some boundary effects at hop boundaries

### Pane-Based Optimization

- **Idea**: Divide window into **panes** (sub-windows). Sliding window = union of panes.
- **Example**: 1h window, 5min pane → 12 panes. Sliding window at t = sum of last 12 panes.
- **Update**: On event, update current pane only. Query: sum last 12 panes. O(1) update, O(W/H) query.
- **Implementation**: Circular buffer of pane counts; evict pane when it exits window.

### Late Events and Watermarks

- **Event time vs processing time**: Events have timestamp; may arrive out of order.
- **Watermark**: Assert "no event with timestamp < T will arrive". Used to close windows.
- **Flink**: `WatermarkStrategy` — periodic or punctuated watermarks. `allowedLateness` for late events (side output).
- **Late event handling**: 
  - **Drop**: Simple; may undercount
  - **Side output + separate correction**: Recompute affected windows; merge with main stream
  - **Allowed lateness**: Keep window state open for X seconds; update if late event arrives

---

## Deep Dive 3: Distributed Counting

### Per-Partition Local Counting

- **Setup**: Kafka partition P → consumer/processor maintains local Count-Min Sketch for keys in P
- **Locality**: Partition by content_id → same content's events in same partition → local sketch sufficient for that partition's keys
- **Problem**: Global top-K requires merging across partitions

### Two-Phase Aggregation

1. **Phase 1**: Each partition emits its **local top-K** (e.g., top 100 per partition)
2. **Phase 2**: Merge job collects all local top-K, merges (CMS is linear — sum sketches for keys that appear in any local top-K), computes global top-K
3. **Emission**: Global top-K to Redis

**Accuracy**: Merged sketch has same (ε, δ) guarantees. Top-K from merged sketch is correct.

### Accuracy vs Communication Cost

- **More partitions** → smaller local sketches, more merge overhead
- **Larger local top-K** → fewer false negatives (missing a global top-K item) but more data to merge
- **Rule of thumb**: Emit local top-2K to 5K when global K=100; ensures overlap with high probability

### Partition Rebalancing

- **Problem**: Consumer fails; partitions reassigned. State (sketch) lost or migrated.
- **Flink/Samza**: State is checkpointed. On rebalance, new consumer loads state from checkpoint. Kafka offset from checkpoint.
- **State migration**: Flink rescales; state redistributed. May take minutes for large state.
- **Alternative**: Stateless merge — each partition only emits counts for its keys; merge job holds no long-lived state, rebuilds from partition outputs. Higher latency, simpler recovery.

---

## Deep Dive 4: Scoring and Ranking Algorithms

### Time-Decay Models

| Model | Formula | Behavior |
|-------|---------|----------|
| **Exponential** | \(s = \sum_i w_i e^{-\lambda (t - t_i)}\) | Smooth; recent dominates |
| **Linear** | \(s = \sum_i w_i \max(0, 1 - (t - t_i)/W)\) | Linear drop to 0 at W |
| **Step** | \(s = \sum_i w_i \cdot \mathbf{1}[t - t_i < W]\) | Binary; in or out |

**Half-life**: For exponential, \(\lambda = \ln 2 / t_{1/2}\). E.g., 6h half-life → 6h-old event has half the weight.

### Reddit's Hot Ranking

\[
\text{score} = \frac{\log_{10}(|s|) + \frac{s \cdot \text{sign}}{45000}}{(t + 2)^{1.8}}
\]
- \(s\) = upvotes - downvotes; sign = direction
- Logarithm dampens viral effect; time denominator penalizes age
- Parameters tuned empirically

### Hacker News Algorithm

\[
\text{score} = \frac{(v - 1)}{(t + 2)^{1.8}}
\]
- \(v\) = upvotes; simple
- Gravity factor 1.8; newer posts rank higher

### Wilson Score Interval

- **Problem**: New content with few votes has high variance; 2 upvotes vs 0 downvotes could be luck
- **Wilson score**: Lower bound of binomial proportion confidence interval
- **Use**: Rank by lower bound instead of raw proportion; conservative for low-count items
- **Formula**: Complex; involves normal approximation. Used for "best" ranking with uncertainty.

### Cold Start (New Content)

- **Problem**: New content has few interactions; can't compete with established high-count items
- **Recency boost**: \(score \times (1 + \alpha \cdot (1 - \text{age}/\text{window}))\) — newer content gets multiplier
- **Velocity bonus**: Fast-rising content gets boost even with lower absolute count
- **Separate list**: "Rising" or "Trending now" for high-velocity, lower-absolute items

---

## Deep Dive 5: Exactly-Once Counting in Stream Processing

### Flink Checkpointing (Chandy-Lamport)

1. **Coordinator** (JobManager) triggers checkpoint; injects barrier into source
2. **Barrier** flows downstream; when operator receives barrier on all inputs, it checkpoints its state
3. **State backend** (RocksDB) writes to durable storage (S3, HDFS)
4. **Exactly-once**: On recovery, restore state; reset source to checkpoint offset; replay from there. No duplicate processing.

### Kafka Exactly-Once Semantics

- **Idempotent producer**: Producer assigns PID; sequence numbers per partition; broker deduplicates
- **Transactions**: Producer commits offset and output atomically. Consumer reads committed messages only.
- **Flink-Kafka**: Uses Kafka transactions for sink; exactly-once end-to-end with Kafka as source and sink

### End-to-End Exactly-Once

**Source** (Kafka) → **Processor** (Flink) → **Sink** (Redis)

- **Source**: Kafka consumer with checkpoint; offset committed in checkpoint
- **Processor**: State checkpointed; deterministic processing
- **Sink**: Idempotent writes — Redis ZADD with same key overwrites; or two-phase commit if sink supports

**Idempotent aggregation**: If we use `(content_id, event_id)` as dedup key in state, replay of same event is idempotent (no double count).

### Cost of Exactly-Once

- **Checkpoint overhead**: Pause processing during checkpoint (or unaligned checkpoint for lower pause)
- **State size**: Larger state → longer checkpoint
- **At-least-once + idempotent**: Simpler; may overcount slightly; acceptable for trending (approximate). Use when exactly-once cost too high.

---

## Deep Dive 6: Real-Time vs Batch Hybrid (Lambda Architecture)

### Lambda Architecture

- **Real-time path**: Stream processor (Flink) → approximate, low-latency trending
- **Batch path**: Nightly or hourly batch job (Spark) → accurate counts from raw events
- **Merge**: Serve real-time for freshness; batch corrects for drift. Or: batch for 7d, real-time for 1h.

**Use case**: When real-time approximate is OK for 1h/24h, but 7d needs accuracy (batch has time to run).

### Kappa Architecture Alternative

- **Single pipeline**: One stream processing job for all windows
- **Replay**: For correction, replay Kafka from earlier offset; reprocess. No separate batch.
- **Simpler**: One codebase; one pipeline. Requires Kafka retention long enough (e.g., 7d).

### Reconciliation Between Real-Time and Batch

- **Approach 1**: Batch overwrites Redis for 7d window; real-time for 1h, 24h
- **Approach 2**: Batch emits corrections; stream processor applies as delta
- **Approach 3**: Run both; compare; alert on drift; batch used for audit, not serving

**Tradeoff**: Lambda adds operational complexity (two pipelines); Kappa simpler but replay can be expensive at scale.
