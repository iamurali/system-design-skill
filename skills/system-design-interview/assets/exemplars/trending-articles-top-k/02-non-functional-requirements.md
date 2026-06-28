# Non-Functional Requirements — Trending Articles / Top-K

## Latency

| Metric | Target | Rationale |
|--------|--------|------------|
| **Trending API (read)** | P99 < 50 ms | User-facing; must feel instant |
| **P50** | < 10 ms | Cache hit path |
| **Event ingestion (write)** | P99 < 100 ms | Async accept; actual write to Kafka |
| **End-to-end freshness** | Trending list updates within **1 minute** of events | Near-real-time; balances cost and UX |

---

## Accuracy

| Dimension | Target | Implication |
|-----------|--------|-------------|
| **Count accuracy** | Within 5% error acceptable | Probabilistic structures (Count-Min Sketch); ε ≈ 0.05 |
| **Rank order** | Top-10 should be correct; order within top-50 may have minor swaps | Approximate counts sufficient for ranking |
| **Deduplication** | Unique user per content (optional) | HyperLogLog for cardinality; adds complexity |

Approximate counting is acceptable because:
- Trending is **discovery**, not analytics; exact counts not required
- Memory and compute cost of exact counting at scale is prohibitive
- Users tolerate small rank fluctuations

---

## Availability

| Component | Target | Rationale |
|-----------|--------|------------|
| **Trending read API** | 99.9% | Trending is not mission-critical; feed works without it |
| **Event ingestion** | 99.95% | Events must not be lost; buffering + retry |
| **Stream processor** | 99.9% | Checkpointing; recovery within minutes |

Degradation modes:
- **Read path down**: Serve stale cached list or empty; degrade gracefully
- **Write path backpressure**: Buffer events; shed load if necessary (prefer delay over drop for trending)

---

## Freshness vs Accuracy Tradeoff

| Scenario | Freshness | Accuracy | Choice |
|----------|-----------|----------|--------|
| Real-time (1h window) | < 1 min | ±5% OK | Prioritize freshness; smaller sketch if needed |
| 24h window | 1–5 min | ±3% preferred | Balance; larger sketch |
| 7d window | 5–15 min | ±2% preferred | Prioritize accuracy; can use batch reconciliation |

**Thresholds**:
- **Staleness SLA**: Trending list age < 2× update interval (e.g., 1h list updated every 30s → max 60s stale)
- **Accuracy SLA**: 95% of top-50 items have estimated count within 5% of true count (measured via sample audit)

---

## Abuse Resistance

Trending is a **high-value target** for manipulation (spam, bots, coordinated inauthentic behavior). Requirements:

| Layer | Requirement | Implementation |
|-------|-------------|----------------|
| **Pre-count gate** | Events from low-reputation users not counted | User reputation score threshold; check before aggregation |
| **Bot detection** | Known bot/suspicious accounts excluded | Integration with LinkedIn's integrity systems |
| **Velocity anomaly** | Sudden spike from single IP/region flagged | Rate-based anomaly detection; temporary suppression |
| **Content quality** | Spam/low-quality content gated | Spam classifier score; content below threshold excluded from trending |
| **Coordinated behavior** | Unusual engagement patterns detected | Graph-based signals; delay or suppress |

**Order of operations**: `Event → [Reputation check] → [Bot check] → [Content quality] → [Count]`. Failed checks: event logged for audit, not counted.

---

## Consistency

| Aspect | Requirement |
|--------|-------------|
| **Read-your-writes** | Not required; trending is eventually consistent |
| **Cross-window consistency** | 1h, 24h, 7d lists may be computed at different times; slight inconsistency OK |
| **Idempotency** | Event ingestion idempotent via `event_id`; exactly-once processing in stream |

---

## Operational Requirements

| Requirement | Target |
|-------------|--------|
| **Monitoring** | Lag, error rate, P99 latency, sketch accuracy (sample audit) |
| **Alerting** | Consumer lag > 5 min; error rate > 0.1%; API P99 > 100 ms |
| **Capacity planning** | Scale stream processors with event growth; Redis memory headroom |
