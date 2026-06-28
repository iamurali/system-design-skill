# Trade-off Framework

Every design choice is a trade. The difference between a PE and a mid-level
engineer is not which technology they pick -- it is how they articulate why.

---

## The 3-Question Method

For every major design decision, answer all three:

1. **What does this solve?** -- The specific constraint or problem this choice
   addresses. Not "it's scalable" but "it handles our 700K TPS write load by
   buffering events and batching writes to the DB every minute."

2. **What does it make worse?** -- The dimension that degrades. Every choice
   worsens something. If you cannot name it, you do not understand the choice.
   Not "it adds complexity" but "it adds 10-100ms of end-to-end latency,
   requires operating a Kafka cluster (ZooKeeper/KRaft, topic management,
   consumer lag monitoring), and introduces a failure mode where lagging
   consumers cause data delay."

3. **What would make me change this decision?** -- The constraint change that
   invalidates this choice. Not "if requirements change" but "if our freshness
   requirement tightens from 1 minute to sub-10ms, Kafka's batching latency
   becomes unacceptable and we need in-process aggregation with checkpointed
   state."

### How to apply

State the triad inline when introducing the component:

> "We add a Redis cache in front of the DB. **Solves**: offloads 95% of reads
> (our 100K read QPS drops to 5K DB queries). **Worsens**: introduces staleness
> (up to TTL duration), a new failure mode (cache down = full load on DB), and
> cache invalidation complexity. **Change it when**: staleness tolerance drops
> below the TTL floor we can practically set, or write patterns shift to make
> the cache hit rate uneconomical (<80%)."

### Anti-patterns

- **Name-dropping**: "We use Kafka because it's industry standard." Industry
  standard is not a justification. WHY does this system need Kafka specifically?
- **One-sided tradeoff**: "Redis is fast and handles high QPS." What does it
  cost? What failure modes does it introduce?
- **Generic tradeoff**: "There's a tradeoff between consistency and
  availability." Be specific: which consistency model did you choose, for which
  data, and what user experience results from that choice?
- **Defending sunk decisions**: When a constraint changes, the right response is
  "that invalidates my assumption X, so I'd change Y" -- not "no, Kafka is
  still the right choice because..."

---

## Common Axis Tradeoffs

These pairs appear in most designs. For each, know which end wins under which
conditions.

### Latency vs Throughput

- **Latency wins**: User-facing read paths, interactive APIs, real-time
  responses. Optimize for single-request speed.
- **Throughput wins**: Batch processing, data pipelines, background jobs.
  Optimize for total work completed per unit time.
- **Tension**: Batching improves throughput but increases latency for individual
  items. Caching improves read latency but does not help write throughput.
- **PE articulation**: "Our read path optimizes for P99 latency (<50ms) by
  serving from cache. Our write path optimizes for throughput by batching
  events in Flink and flushing every minute. These are deliberately different
  optimization targets for different paths."

### Consistency vs Availability

- **Consistency wins**: Financial transactions, inventory management, leader
  election, distributed locks. Wrong data is worse than no data.
- **Availability wins**: Social feeds, caches, analytics, status pages. Stale
  data is better than an error.
- **Tension**: Strong consistency requires coordination (quorum writes, leader
  acknowledgment) which reduces availability during partitions.
- **PE articulation**: "For view counts, eventual consistency is sufficient --
  showing 1,234 vs 1,237 views does not affect user experience. For payment
  processing, we need linearizability -- a double charge is unacceptable. These
  are different data paths with different consistency requirements, not a global
  setting."

### Freshness vs Cost

- **Freshness wins**: Real-time dashboards, trending feeds, live scores. Users
  expect current data.
- **Cost wins**: Weekly reports, historical analytics, cold storage queries.
  Nobody notices if the monthly summary is 15 minutes old.
- **Tension**: Real-time processing (stream) is 10-100x more expensive than
  batch processing for the same data volume.
- **PE articulation**: "We use stream processing for the 1-hour window (sub-
  minute freshness is required) and batch aggregation for the monthly window
  (15-minute staleness is acceptable). This saves us ~80% of compute cost for
  the cold windows without affecting user experience."

### Simplicity vs Scalability

- **Simplicity wins**: Early-stage products, low traffic, small teams. A single
  Postgres instance with proper indexes handles a lot. YAGNI.
- **Scalability wins**: When numbers force it -- single-node QPS is exceeded,
  working set does not fit in memory, single-region latency is unacceptable.
- **Tension**: Every scalability mechanism (sharding, caching, async processing)
  adds operational complexity, failure modes, and cognitive load.
- **PE articulation**: "At our current 10K QPS, a single Postgres node with
  read replicas handles the load. I would not introduce sharding until we
  approach 50K QPS -- the operational cost of managing sharded Postgres
  (routing, cross-shard queries, rebalancing) is not justified at current
  scale. The migration path is: read replicas at 10K, connection pooling at
  30K, sharding at 50K+."

### Accuracy vs Performance

- **Accuracy wins**: Billing, compliance, financial reporting. Every number
  must be exact.
- **Performance wins**: Trending, analytics, recommendations. Directional
  correctness is sufficient.
- **Tension**: Exact counting at scale requires O(n) space and coordination.
  Approximate counting (CMS, HLL) uses sublinear space but introduces bounded
  error.
- **PE articulation**: "For trending, Count-Min Sketch with epsilon=0.01 gives
  us 1% error bound in 7 KB per sketch. That is 100x more memory-efficient
  than exact counting for 3.6B videos. For the billing path, we use exact
  counting with sharded counters and reconciliation."

### Precomputation vs Query-Time Computation

- **Precomputation wins**: Fixed query patterns, latency-sensitive reads, hot
  data. Compute once, serve many times.
- **Query-time wins**: Ad-hoc queries, rare access patterns, cold data. Do not
  pay compute cost for data nobody reads.
- **Tension**: Precomputation uses storage and compute upfront. It also
  creates a staleness window between computation and serving.
- **PE articulation**: "We precompute the top-K for each (window, geo,
  industry) combination -- 6,000 segments updated every minute. Per-user
  personalized trending is computed on-demand with a 500ms timeout and 5-minute
  cache, because materializing it for 900M users would require petabytes."

---

## Handling "It Depends" at PE Level

"It depends" is not an answer -- it is the start of one. The PE move is to
name exactly what it depends on:

- "It depends on the **read:write ratio**. At 95% reads, cache-aside with TTL.
  At 50/50, write-through with invalidation. At 95% writes, skip the cache
  entirely and optimize the write path."
- "It depends on the **consistency requirement**. For the user profile cache,
  eventual is fine (staleness < 5s). For the payment ledger, linearizable
  with synchronous replication."
- "It depends on the **scale**. At 1K QPS, single Postgres. At 100K QPS,
  Postgres with read replicas and connection pooling. At 1M QPS, sharded
  with application-level routing."

Always complete the sentence: "It depends on X, and given our constraint Y,
the answer is Z."
