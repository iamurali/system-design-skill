# Problem Bank -- PE-Level System Design

30+ curated problems organized by archetype. Each entry includes: companies
that ask it, building blocks exercised, the typical curveball, and one PE-level
insight that separates exceptional candidates.

---

## Data-Intensive Systems

### Top-K / Trending

- **Companies**: Google, Amazon, Databricks
- **Blocks**: `sharded-counters`, `messaging-streaming`, `caching`, `data-storage`
- **Curveball**: Switch from tumbling to sliding windows. Or: support arbitrary
  time ranges, not just fixed windows.
- **PE insight**: Approximate counting (CMS) with a paired heap gives sublinear
  space. The real challenge is not counting -- it is maintaining the top-K list
  when sketches cannot enumerate their keys. Pair CMS with Space-Saving or a
  bounded sorted structure.

### News Feed / Timeline

- **Companies**: Google, Amazon, Microsoft
- **Blocks**: `data-storage`, `caching`, `messaging-streaming`, `api-design`
- **Curveball**: Add ranked feed (ML scoring) instead of chronological. Or:
  support mixed media (text, images, video, polls).
- **PE insight**: Fan-out-on-write vs fan-out-on-read is the core tradeoff.
  Hybrid: fan-out-on-write for users with <10K followers, fan-out-on-read for
  celebrities. The threshold is a tunable parameter, not a fixed number.

### Ad Click Aggregator

- **Companies**: Google, Amazon, Databricks
- **Blocks**: `messaging-streaming`, `data-storage`, `sharded-counters`,
  `consistency-coordination`
- **Curveball**: Add exactly-once semantics for billing accuracy. Or: support
  real-time fraud detection in the aggregation pipeline.
- **PE insight**: Billing requires exactly-once. Kafka transactions +
  idempotent writes achieve this, but the real complexity is late-arriving
  clicks and attribution window management. Reconciliation between real-time
  and batch aggregates is necessary.

### Metrics Monitoring System

- **Companies**: Google, Amazon, Databricks
- **Blocks**: `messaging-streaming`, `data-storage`, `caching`, `observability`,
  `distributed-logging`
- **Curveball**: Support high-cardinality labels (user ID as a label). Or: add
  anomaly detection on ingested metrics.
- **PE insight**: Time-series DBs optimize for narrow queries (one metric, many
  timestamps). High cardinality (millions of label combinations) blows up
  indexes. The solution is pre-aggregation at ingestion (rollup by time bucket)
  and query-time downsampling, not bigger indexes.

### Time-Series Database

- **Companies**: Databricks, Google, Amazon
- **Blocks**: `data-storage`, `caching`, `messaging-streaming`, `blob-store`
- **Curveball**: Support both real-time queries and historical batch analysis
  on the same data.
- **PE insight**: LSM-tree with time-partitioned compaction. Writes are
  append-only (fast). Reads for recent data hit memtable; historical reads
  hit sorted files with bloom filters. The hard part is compaction scheduling
  that does not interfere with query latency.

---

## Real-Time Systems

### Chat / Messaging (WhatsApp-scale)

- **Companies**: Google, Amazon, Microsoft
- **Blocks**: `messaging-streaming`, `data-storage`, `consistency-coordination`,
  `sequencer`, `api-design`
- **Curveball**: Add end-to-end encryption. Or: support message editing and
  deletion with consistency guarantees across devices.
- **PE insight**: Message ordering requires per-conversation sequence numbers,
  not global timestamps. The hard problem is online/offline sync: a device
  that was offline for 3 days needs to catch up without downloading the entire
  conversation history. Monotonic sequence numbers per conversation with
  cursor-based sync solve this.

### Live Comments / Real-Time Feed

- **Companies**: Google, Amazon, Microsoft
- **Blocks**: `messaging-streaming`, `caching`, `load-balancing`, `api-design`
- **Curveball**: Handle viral events (100K+ concurrent viewers on one stream).
  Or: add real-time sentiment analysis on comments.
- **PE insight**: Fan-out via persistent connections (WebSocket/SSE) does not
  scale linearly with viewers. The solution is a pub/sub tier between the
  comment ingestion and the connection servers, with connection servers
  subscribing to channels. Hot channels need multiple connection server
  replicas with load-balanced subscriptions.

### Collaborative Editing (Google Docs)

- **Companies**: Google, Microsoft
- **Blocks**: `consistency-coordination`, `messaging-streaming`, `data-storage`,
  `sequencer`
- **Curveball**: Support offline editing with conflict resolution. Or: add
  real-time presence (cursor positions, selections).
- **PE insight**: OT (Operational Transform) vs CRDT. OT requires a central
  server for transformation ordering but is well-understood. CRDTs are
  peer-to-peer capable but have higher memory overhead for text (e.g., RGA,
  YATA). Google Docs uses OT. The PE move is knowing why and when you would
  choose the other.

### Notification System

- **Companies**: Amazon, Google, Microsoft
- **Blocks**: `messaging-streaming`, `task-scheduling`, `api-design`,
  `data-storage`, `resilience-failure`
- **Curveball**: Add notification preferences with complex rules (quiet hours,
  channel preferences per notification type). Or: guarantee at-most-once
  delivery for financial notifications.
- **PE insight**: The hard problem is not sending notifications -- it is not
  sending them. Rate limiting, deduplication, aggregation ("3 people liked
  your post"), and preference honoring are where the complexity lives.

### Presence System (Online/Offline Status)

- **Companies**: Google, Microsoft, Amazon
- **Blocks**: `caching`, `messaging-streaming`, `consistency-coordination`
- **Curveball**: Support "last seen" with minute-level accuracy for 500M users.
- **PE insight**: Heartbeat-based presence with aggressive TTL in Redis. The
  tradeoff is heartbeat interval vs battery drain (mobile) vs staleness. Fan-
  out of presence updates to all contacts is O(friends * users) -- use lazy
  pull (query on view) instead of eager push for non-close contacts.

---

## Storage Systems

### Distributed Cache

- **Companies**: Google, Amazon, Microsoft
- **Blocks**: `caching`, `consistency-coordination`, `load-balancing`,
  `data-storage`
- **Curveball**: Add multi-tenant isolation. Or: support cache-as-primary-store
  for session data with durability guarantees.
- **PE insight**: The interesting design is not the cache itself -- it is the
  invalidation strategy, the thundering herd protection, and the failure mode
  when the cache layer goes down. Facebook's lease-based invalidation (Memcache
  paper) is the canonical PE reference.

### Distributed Key-Value Store

- **Companies**: Google, Amazon, Databricks
- **Blocks**: `data-storage`, `consistency-coordination`, `sequencer`,
  `resilience-failure`
- **Curveball**: Add tunable consistency (allow per-request consistency level).
  Or: support range queries, not just point lookups.
- **PE insight**: The Dynamo paper is the canonical reference. Consistent
  hashing with virtual nodes, vector clocks for conflict detection, sloppy
  quorum with hinted handoff, anti-entropy with Merkle trees. Know why each
  mechanism exists and what breaks without it.

### Distributed File System

- **Companies**: Google, Databricks
- **Blocks**: `blob-store`, `consistency-coordination`, `data-storage`,
  `sequencer`
- **Curveball**: Support small files efficiently (GFS/HDFS are optimized for
  large files). Or: add snapshot/versioning.
- **PE insight**: Master (NameNode) is the SPOF. GFS solved this with shadow
  masters and operation log replay. HDFS solved it with HA NameNode using
  JournalNodes. The chunk size tradeoff (large = fewer metadata entries but
  wasted space for small files) is load-bearing for the design.

### Object / Blob Store (S3-like)

- **Companies**: Amazon, Google, Microsoft
- **Blocks**: `blob-store`, `data-storage`, `caching`, `content-delivery`
- **Curveball**: Add versioning with rollback. Or: support cross-region
  replication with eventual consistency.
- **PE insight**: Erasure coding (Reed-Solomon) vs 3x replication for
  durability. Erasure coding uses ~1.5x storage for similar durability vs 3x
  for replication, but repair is more CPU-intensive. S3 uses erasure coding.

---

## Infrastructure Systems

### Rate Limiter

- **Companies**: Google, Amazon, OpenAI, Anthropic
- **Blocks**: `resilience-failure`, `caching`, `sharded-counters`, `api-design`
- **Curveball**: Multi-dimensional rate limiting (per user, per API, per IP,
  global). Or: distributed rate limiting across 100 API gateway nodes.
- **PE insight**: Token bucket is the default. The distributed challenge is
  synchronization across nodes. Options: (1) sticky routing (simple, uneven
  load), (2) centralized Redis counter (accurate, Redis as SPOF), (3) local
  counters with sync (fast, approximate). The PE move is knowing when
  approximate is sufficient (most cases) and when it is not (billing).

### Job Scheduler

- **Companies**: Google, Amazon, Databricks
- **Blocks**: `task-scheduling`, `messaging-streaming`, `data-storage`,
  `consistency-coordination`
- **Curveball**: Support exactly-once execution with at-least-once delivery.
  Or: add priority queues with starvation prevention.
- **PE insight**: Worker leasing with heartbeats prevents double execution.
  The hard problems are: task deduplication (idempotency keys), priority
  inversion (high-priority task starved by many low-priority), and cascading
  retry storms when a downstream dependency fails.

### API Gateway

- **Companies**: Amazon, Google, OpenAI, Anthropic
- **Blocks**: `load-balancing`, `resilience-failure`, `api-design`, `caching`,
  `observability`
- **Curveball**: Add request transformation and protocol translation (REST to
  gRPC). Or: multi-model routing for AI APIs.
- **PE insight**: The gateway is the single point where cross-cutting concerns
  converge: auth, rate limiting, logging, metrics, circuit breaking, request
  routing. The PE tradeoff is thick gateway (all logic centralized, single
  point of failure, deployment bottleneck) vs thin gateway (routing only,
  push concerns to sidecars/service mesh).

### Service Mesh / Config Service

- **Companies**: Google, Microsoft, Amazon
- **Blocks**: `service-decomposition`, `consistency-coordination`,
  `observability`, `resilience-failure`
- **Curveball**: Support configuration rollback with canary deployment.
- **PE insight**: Config service needs strong consistency for writes (a bad
  config must not propagate) but can tolerate eventual consistency for reads
  (with bounded staleness). The watch/subscribe pattern (ZooKeeper, etcd) is
  the building block.

---

## ML Infrastructure

### Model Serving Platform

- **Companies**: Anthropic, OpenAI, Google, Databricks
- **Blocks**: `load-balancing`, `caching`, `api-design`, `observability`,
  `resilience-failure`
- **Curveball**: Serve multiple model versions simultaneously with traffic
  splitting. Or: support streaming responses for LLM inference.
- **PE insight**: LLM serving is memory-bound, not compute-bound. KV cache
  management (PagedAttention) is the key to throughput. Continuous batching
  at the iteration level (not request level) maximizes GPU utilization. The
  tradeoff is latency (time-to-first-token) vs throughput (total tokens/sec).

### Feature Store

- **Companies**: Databricks, Google, Amazon
- **Blocks**: `data-storage`, `caching`, `messaging-streaming`, `api-design`
- **Curveball**: Support point-in-time correctness (avoid data leakage in
  training). Or: real-time feature computation from streaming events.
- **PE insight**: Dual storage: offline store (batch features in Parquet/Delta
  for training) and online store (low-latency KV for serving). The hard
  problem is keeping them in sync without drift. Point-in-time joins for
  training data require time-travel semantics in the offline store.

### Training Pipeline / ML Platform

- **Companies**: OpenAI, Anthropic, Google, Databricks
- **Blocks**: `task-scheduling`, `blob-store`, `messaging-streaming`,
  `observability`
- **Curveball**: Handle training run failures gracefully (checkpoint and
  resume without losing days of compute). Or: support multi-tenant GPU
  scheduling with fairness guarantees.
- **PE insight**: Checkpoint frequency tradeoff: too frequent wastes GPU time
  on I/O, too infrequent loses days of compute on failure. The answer depends
  on MTBF of the cluster. For 1000-GPU runs with ~2 hour MTBF, checkpoint
  every 10-20 minutes. Elastic training (adjust GPU count mid-run) is the
  frontier.

### A/B Testing Platform

- **Companies**: Google, Amazon, Microsoft, Databricks
- **Blocks**: `data-storage`, `caching`, `messaging-streaming`, `api-design`
- **Curveball**: Support interaction effects between concurrent experiments.
  Or: real-time experiment monitoring with automated early stopping.
- **PE insight**: The hard problem is experiment isolation. Layered
  experimentation (Google's Overlapping Experiments paper) allows concurrent
  experiments on orthogonal parameters. Assignment must be deterministic
  (hash-based) and reproducible. Statistical rigor requires proper sample
  size calculation and sequential testing to avoid peeking bias.

---

## Data Platform

### Data Lakehouse

- **Companies**: Databricks, Google, Amazon
- **Blocks**: `data-storage`, `blob-store`, `messaging-streaming`,
  `consistency-coordination`
- **Curveball**: Support ACID transactions across multiple tables. Or: add
  time-travel queries for regulatory compliance.
- **PE insight**: Delta Lake's transaction log is a sequence of JSON files in
  the object store. Optimistic concurrency: readers never block writers.
  Conflict resolution on concurrent writes uses file-level conflict detection.
  The checkpoint mechanism (every 10 commits, write a Parquet summary)
  prevents the log from growing unbounded.

### Query Engine (Distributed SQL)

- **Companies**: Databricks, Google
- **Blocks**: `data-storage`, `caching`, `load-balancing`
- **Curveball**: Optimize for both short interactive queries and long-running
  ETL in the same engine.
- **PE insight**: Cost-based optimizer with cardinality estimation is the
  differentiator. Join order selection is NP-hard; practical engines use
  dynamic programming with pruning. Adaptive query execution (Spark AQE,
  Databricks Photon) re-optimizes mid-execution based on actual data
  statistics. Vectorized execution (columnar batches through operators) gives
  10x+ throughput over row-at-a-time.

### ETL Pipeline

- **Companies**: Databricks, Amazon, Google
- **Blocks**: `messaging-streaming`, `data-storage`, `task-scheduling`,
  `blob-store`
- **Curveball**: Support schema evolution without breaking downstream
  consumers. Or: add data quality validation as a pipeline stage.
- **PE insight**: Idempotent pipeline stages enable safe retry. The hard
  problem is exactly-once across the full pipeline (extract -> transform ->
  load). Spark's structured streaming achieves this with write-ahead logs and
  idempotent sinks. Data quality checks (Great Expectations, Deequ) should
  fail the pipeline, not silently propagate bad data.

### Data Catalog / Schema Registry

- **Companies**: Databricks, Google, Amazon
- **Blocks**: `data-storage`, `api-design`, `consistency-coordination`
- **Curveball**: Support lineage tracking (which downstream tables are affected
  by a schema change). Or: automated PII detection and classification.
- **PE insight**: Schema compatibility (backward, forward, full) determines
  what changes are safe. Confluent Schema Registry uses Avro compatibility
  rules. The PE move is connecting schema governance to deployment pipelines:
  a breaking schema change should block the deploy, not break consumers at
  runtime.

### Vector Search / Embedding Store

- **Companies**: Anthropic, OpenAI, Google, Databricks
- **Blocks**: `data-storage`, `caching`, `api-design`, `distributed-search`
- **Curveball**: Support hybrid search (vector + keyword). Or: handle
  embedding model updates that invalidate all stored vectors.
- **PE insight**: ANN algorithms (HNSW, IVF, ScaNN) trade recall for speed.
  HNSW gives ~95%+ recall at sub-millisecond latency but uses significant
  memory (graph structure). IVF is more space-efficient but requires a
  training step. The hardest operational problem is re-indexing when the
  embedding model changes -- this requires a dual-write period and traffic
  shifting, analogous to a database migration.
