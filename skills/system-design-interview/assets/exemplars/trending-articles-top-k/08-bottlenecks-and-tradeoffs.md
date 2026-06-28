# Bottlenecks and Tradeoffs — Trending Articles / Top-K

## Bottlenecks

### 1. Viral Content Hotspot (Single content_id Receiving Millions of Events)

**Cause**: One post/article goes viral; all events partition to same Kafka partition (by content_id). Single consumer overwhelmed.

**Mitigations**:
- **High partition count**: 500+ partitions spreads load; viral content still hits one partition but others handle rest
- **Consumer scaling**: Multiple consumers per partition (Kafka consumer group) — but keyed state (content_id) means one consumer per partition for keyed aggregation
- **Separate hot path**: Detect hot content (e.g., >100K events/min); route to dedicated high-throughput pipeline with exact counting
- **Backpressure**: Slow down ingestion if consumer lag grows; prefer delayed events over dropped
- **Real example**: Twitter's trending had to handle K-pop fan coordination — millions of tweets for single hashtag in minutes

---

### 2. Count-Min Sketch Accuracy Degradation with High Cardinality

**Cause**: With millions of unique content_ids, collision probability increases. Sketch width w limits distinct items; many items hash to same bucket → overcount.

**Mitigations**:
- **Larger sketch**: w = 2^18 or 2^20; trade memory for accuracy
- **Conservative update**: Reduces overcount when merge not needed
- **Space-Saving for top-K**: If we only need top-K, use Space-Saving (deterministic) for heavy hitters; CMS for general count queries
- **Accept approximate**: Trending ranks; ±5% error often acceptable; top-10 order usually stable
- **Monitoring**: Sample audit — compare sketch estimates to batch-computed true counts; alert on drift

---

### 3. Late Events and Out-of-Order Processing

**Cause**: Events arrive late (network delay, mobile offline, cross-region). Processing uses event-time; late events can invalidate already-emitted results.

**Mitigations**:
- **Allowed lateness**: Flink's `allowedLateness` — keep window state open for X seconds; update if late event arrives; emit retraction + new result
- **Watermark tuning**: Aggressive watermark → close windows early → may drop late events. Conservative → high latency. Balance based on P99 event delay.
- **Side output**: Late events to side output; separate correction stream; merge periodically
- **Pragmatic**: For 1h trending, events >10 min late have small impact; drop or correct in next batch reconciliation

---

### 4. Stream Processor Failures and Checkpoint Recovery Time

**Cause**: Flink/Samza job fails; recovery requires loading state from checkpoint. With 50–100 GB state (sketches across partitions), recovery can take 5–15 minutes.

**Mitigations**:
- **Incremental checkpoints**: Flink incremental RocksDB checkpoints — only changed data; faster
- **Unaligned checkpoints**: Reduce pause time; more complex
- **Standby replicas**: Hot standby job (double cost); failover in seconds
- **Degradation**: During recovery, serve stale Redis data; no updates. Acceptable for trending (not mission-critical).
- **State compaction**: Periodically prune old window state; reduce checkpoint size

---

### 5. Redis Memory Limits for Sorted Sets with Millions of Entries

**Cause**: If we store top-K per (window, geo, category, industry) = 3 × 50 × 20 × 2 = 6,000 segments, each with 100 entries → 600K entries. Manageable. But if we add per-user "trending in your network" → 900M keys. Explodes.

**Mitigations**:
- **Selective materialization**: Pre-compute only top segments (global, top 20 geos, top 10 industries). Long-tail computed on-demand or not offered
- **Per-user**: "Trending in your network" — compute on-demand with timeout (e.g., 500ms); cache for 5 min
- **Sharding**: Redis Cluster; shard by segment key
- **Eviction**: If memory limit hit, evict least-accessed segments (e.g., small geo + rare industry)

---

### 6. Gaming/Manipulation Resistance vs Responsiveness

**Cause**: Strict abuse gates (reputation, bot detection, velocity anomaly) can suppress organic viral content. Loose gates → manipulation (spam, bots) trends.

**Mitigations**:
- **Tunable thresholds**: Admin config; A/B test. Start strict; relax if false positives high
- **Human review**: Flag suspicious trends; human can suppress. Twitter does this for trending
- **Velocity vs volume**: Favor velocity (rising fast) over raw volume — harder to game with slow bot ramp
- **Real example**: Twitter trending manipulation (K-pop, spam hashtags) led to algorithm changes, human review, and "context" notes on trends

---

### 7. Cost: Stream Processing Compute is Expensive at Scale

**Cause**: Flink/Samza clusters run 24/7; at 500K events/sec, need hundreds of CPU cores. Cost can be $100K–$1M+/month.

**Mitigations**:
- **Sampling**: For 7d window, sample 10% of events; scale counts. Accuracy tradeoff
- **Tiered processing**: 1h real-time (full stream); 24h/7d with reduced frequency (e.g., aggregate every 5 min instead of every event)
- **Batch for cold windows**: 7d trending from daily batch; no real-time stream for 7d
- **Right-size**: Scale down during low traffic; auto-scale with lag

---

### 8. Real-World Examples of Trending System Failures

| Incident | What happened | Lesson |
|----------|---------------|--------|
| **Twitter K-pop trending** | Fans coordinated to make hashtags trend; organic trends suppressed | Need velocity + diversity signals; detect coordination |
| **Twitter spam hashtags** | Spammers used trending for SEO; low-quality links | Content quality gate; human review |
| **YouTube trending criticism** | Clickbait, inappropriate content surfaced | Quality signals; not just engagement count |
| **LinkedIn connection spam** | Inauthentic engagement to game "Who's Viewed" | Reputation and bot detection before counting |

---

## Tradeoffs Summary

| Dimension | Option A | Option B | Choice |
|-----------|----------|----------|--------|
| **Count accuracy** | Exact (HashMap) | Approximate (CMS) | Approximate — scale |
| **Freshness** | <10s | <1 min | <1 min — cost/UX balance |
| **Window type** | Tumbling | Sliding/Hopping | Hopping — fewer artifacts, manageable cost |
| **Exactly-once** | Yes | At-least-once + idempotent | Exactly-once when feasible; idempotent fallback |
| **Filter application** | Pre-aggregate all | Query-time filter | Hybrid — pre-compute hot segments |
| **Abuse strictness** | Strict | Loose | Tunable; start strict |
| **Real-time vs batch** | Lambda (both) | Kappa (stream only) | Lambda for 7d accuracy; Kappa for simplicity |

---

## Interview Talking Points

1. **Why approximate?** At millions of events/sec and billions of content items, exact counting is O(n) space. Count-Min Sketch gives O(1) update, O(1) query, sublinear space, with bounded error — acceptable for ranking.

2. **Why stream over batch?** Sub-minute freshness requirement. Batch adds minutes to hours of lag. Stream processing (Flink/Samza) gives near-real-time aggregation.

3. **Why Redis for top-K?** Query latency P99 < 50ms. Redis in-memory, sub-ms. Pre-computed sorted sets avoid recomputation on every request. Push-based updates from stream processor keep it fresh.

4. **Why partition by content_id?** Locality — all events for same content to same partition → single consumer can aggregate without cross-partition communication. Enables efficient keyed state.

5. **LinkedIn uses Samza** — they created it. Kafka-centric, exactly-once with Kafka transactions. Natural fit for LinkedIn's event-driven architecture.
