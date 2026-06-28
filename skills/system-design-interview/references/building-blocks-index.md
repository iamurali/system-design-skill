# Building Blocks Index (L0-L7)

Bottom-up catalog of composable building blocks. Each layer depends only on
the ones beneath it. Use this to select components during Phase 4 (architecture)
and to run the coverage sweep during Phase 6 (synthesis).

---

## L0 -- Frame

### Requirements Scoping

**Purpose**: Turn a vague prompt into functional requirements, non-functional
constraints, and explicit out-of-scope.

- **Reach for it**: At the start of every design, before drawing anything.
- **Do not skip**: Rushing to design is failure mode #3.
- **Key tradeoff**: Scope breadth vs depth. Narrower scope = deeper design
  within the time budget.
- **PE depth signal**: Interviewer probes whether you can distinguish
  load-bearing requirements from nice-to-haves. Can you propose scope that
  changes the architecture?

### Back-of-the-Envelope Estimation

**Purpose**: Convert "high traffic" into numbers that decide the design.

- **Reach for it**: Right after requirements, and any time a choice depends on
  scale.
- **Do not over-estimate**: Skip numbers that will not change a decision (YAGNI).
  Round to one significant figure. Think in orders of magnitude.
- **Key tradeoff**: Estimation precision vs time spent. Directional correctness
  beats precision.
- **PE depth signal**: Can you re-derive the chain when an input changes? Do
  you size on peak, not average? Do you estimate reads and writes separately?
- **Reference**: `numbers-to-know.md`

---

## L1 -- Edge

### DNS

**Purpose**: How clients resolve the service. Geo-routing, failover, latency-
based routing.

- **Reach for it**: Multi-region designs, failover strategy, global services.
- **Not needed**: Single-region, internal services behind a service mesh.
- **Key tradeoff**: TTL length -- short TTL enables fast failover but increases
  DNS query load; long TTL caches better but delays failover.
- **PE depth signal**: Anycast vs unicast, DNS-based GSLB vs application-level
  routing, propagation delay implications during failover.

### Load Balancing

**Purpose**: Distribute traffic across service instances. Health checks. L4
vs L7 routing decisions.

- **Reach for it**: Any multi-instance service tier.
- **Key tradeoff**: L4 (fast, protocol-agnostic, no request inspection) vs L7
  (content-based routing, SSL termination, but higher latency and state).
- **PE depth signal**: Consistent hashing for stateful routing, connection
  draining during deploys, health check design (shallow vs deep), power-of-two-
  choices algorithm, Google's "bounded loads" approach.

### Content Delivery (CDN)

**Purpose**: Serve static/media content from edge locations close to users.

- **Reach for it**: Static assets, media-heavy products, global user base.
- **Not needed**: Internal APIs, dynamic-only content, single-region.
- **Key tradeoff**: Cache hit rate vs freshness. Purge complexity. Origin
  shield to prevent thundering herd on cache miss.
- **PE depth signal**: Cache hierarchy (edge -> shield -> origin), signed URLs
  for access control, adaptive bitrate for video, edge compute for
  personalization.

---

## L2 -- Services

### API Design

**Purpose**: The contract between clients and the system. Endpoints, request/
response shapes, pagination, idempotency, versioning.

- **Reach for it**: Always. The API makes requirements concrete.
- **Key tradeoff**: REST (simple, cacheable, widely understood) vs gRPC
  (efficient, typed, streaming) vs GraphQL (flexible queries, client-driven).
- **PE depth signal**: Idempotency key design, cursor-based pagination at scale,
  backward-compatible versioning strategy, API gateway responsibilities (auth,
  rate limiting, request transformation).

### Service Decomposition

**Purpose**: Monolith vs microservices. Service boundaries, API gateway, service
discovery, service mesh.

- **Reach for it**: Only when a real driver appears -- independent deploy/scale/
  ownership, cross-service consistency, gateway/discovery. Many prompts should
  stay monolith or modular monolith.
- **Not needed by default**: Do not decompose for its own sake. YAGNI.
- **Key tradeoff**: Monolith (simple, fast, one deploy) vs microservices
  (independent scaling/deployment, but distributed system complexity, network
  calls, data consistency challenges).
- **PE depth signal**: What drives the split (team autonomy, independent
  scaling, fault isolation)? How do you handle cross-service transactions
  (sagas, eventual consistency)? Service mesh vs client-side discovery?

---

## L3 -- State

### Data Storage

**Purpose**: Where data lives. SQL vs NoSQL, schema design, indexing, sharding,
replication.

- **Reach for it**: Every design needs a storage decision.
- **Key tradeoff**: SQL (strong consistency, joins, mature tooling, ~1K QPS) vs
  NoSQL (horizontal scale, flexible schema, ~10K QPS, but limited query
  patterns). Within NoSQL: document (MongoDB) vs wide-column (Cassandra,
  Bigtable) vs KV (DynamoDB, Redis).
- **PE depth signal**: Access-pattern-driven schema design. Partition key
  selection and hot partition mitigation. LSM-tree vs B-tree tradeoffs.
  Read/write amplification. Secondary index cost.
- **Problems**: Every problem.

### Caching

**Purpose**: Put hot data closer to the reader. Offload the origin. Buy latency.

- **Reach for it**: Read-heavy workloads (high read:write ratio), hot working
  set, expensive recomputation.
- **Not needed**: Write-heavy data, read-once patterns, data requiring zero
  staleness.
- **Key tradeoff**: Cache-aside (simple, resilient) vs read-through (centralized)
  vs write-through (fresh reads, slower writes) vs write-back (fast writes,
  data loss window).
- **PE depth signal**: Thundering herd mitigation (single-flight, probabilistic
  early refresh, TTL jitter). Hot key replication. Cache-aside invalidation
  races. Facebook's lease-based approach. L1 (in-process) + L2 (distributed)
  tiering.
- **Problems**: In-memory cache, distributed cache, news feed, session store.

### Blob Store

**Purpose**: Store large unstructured objects (images, video, files). Chunking,
multipart upload, signed URLs, tiering.

- **Reach for it**: Media uploads, file storage, backup/archive.
- **Key tradeoff**: Managed (S3, GCS -- durable, operational simplicity, egress
  cost) vs self-hosted (MinIO, HDFS -- control, no egress cost, operational
  burden).
- **PE depth signal**: Erasure coding vs replication for durability. Multipart
  upload for large files. Signed URLs with expiry for access control. Storage
  tiering (hot/warm/cold) for cost optimization.

### Sequencer (Unique ID Generation)

**Purpose**: Generate globally unique, optionally ordered IDs at scale.

- **Reach for it**: Any system needing unique identifiers across distributed
  nodes.
- **Key tradeoff**: UUID v4 (random, no coordination, not sortable, 128-bit) vs
  Snowflake (time-sortable, 64-bit, requires clock sync) vs ticket server
  (centralized, simple, SPOF).
- **PE depth signal**: Clock skew and its impact on Snowflake ordering. Leap
  second handling. ID entropy requirements for security-sensitive contexts.

### Sharded Counters

**Purpose**: Count things (views, likes, votes) at extreme write rates without
hot-key contention.

- **Reach for it**: High-write counters where a single row would be a
  bottleneck (celebrity likes, video views).
- **Key tradeoff**: Exact counting (sharded rows, merge on read -- accurate but
  read amplification) vs approximate (HyperLogLog for cardinality, CMS for
  frequency -- sublinear space, bounded error).
- **PE depth signal**: Stripe count tuning. Write-contention avoidance patterns.
  CMS width/depth sizing and error bounds. When approximate is acceptable
  (trending) vs when it is not (billing).
- **Problems**: Top-K, like counters, rate limiting.

### Distributed Search

**Purpose**: Full-text search, inverted index, autocomplete, relevance ranking.

- **Reach for it**: Search features, typeahead, content discovery.
- **Key tradeoff**: Elasticsearch/OpenSearch (powerful, operational complexity)
  vs Postgres full-text search (simpler, limited at scale) vs purpose-built
  (Lucene-based, custom ranking).
- **PE depth signal**: Inverted index structure. TF-IDF vs BM25 scoring.
  Segment merge strategy. Index refresh interval vs query freshness. Sharding
  by document vs by term.
- **Problems**: Inverted index search, typeahead, content search.

---

## L4 -- Async

### Messaging and Streaming

**Purpose**: Decouple producers from consumers. Absorb write spikes. Enable
event-driven architectures.

- **Reach for it**: Write spikes, async processing, event sourcing, fan-out.
- **Key tradeoff**: Queue (SQS -- at-least-once, simple, per-message) vs log
  (Kafka -- ordered, replayable, partitioned, higher operational complexity) vs
  pub/sub (SNS, Pub/Sub -- fan-out, no replay).
- **PE depth signal**: Exactly-once semantics (idempotent consumers + Kafka
  transactions). Consumer group rebalancing storms. Partition count sizing.
  Backpressure and DLQ design. Retention vs replay tradeoffs.
- **Problems**: Kafka pipeline, notification system, event-driven architectures.

### Task Scheduling

**Purpose**: Background, scheduled, recurring, and delayed jobs. Worker leasing,
priorities, fairness.

- **Reach for it**: Cron jobs, delayed processing, workflow orchestration,
  batch jobs.
- **Key tradeoff**: Simple cron (easy, SPOF, no visibility) vs distributed
  scheduler (Temporal/Airflow -- durable, observable, complex to operate).
- **PE depth signal**: Task deduplication. At-least-once execution with
  idempotent handlers. Priority queues and fairness. Worker leasing and
  heartbeats. Temporal's durable execution model.

---

## L5 -- Correctness

### Consistency and Coordination

**Purpose**: CAP tradeoffs, consistency models, consensus, distributed
transactions, leader election.

- **Reach for it**: Multi-node writes, cross-service data integrity, leader
  election, distributed locks.
- **Key tradeoff**: Strong consistency (linearizable -- correct but higher
  latency, lower availability) vs eventual consistency (fast, available, but
  stale reads and conflict resolution needed).
- **PE depth signal**: Raft/Paxos mechanics (not just names). Quorum math
  (W + R > N). Read-your-writes via sticky routing or version vectors. Saga
  pattern for distributed transactions. CRDTs for conflict-free replicated
  state. Consistent hashing with bounded loads.
- **Problems**: Distributed KV store, collaborative editing, payment systems.

---

## L6 -- Ops

### Resilience and Failure

**Purpose**: Fault tolerance, circuit breakers, retries with backoff/jitter,
timeouts, bulkheads, graceful degradation, rate limiting.

- **Reach for it**: Every production system. If you have not discussed failure,
  the design is incomplete.
- **Key tradeoff**: Aggressive retries (fast recovery, but amplifies outages)
  vs conservative backoff (slower recovery, but stable under cascade).
- **PE depth signal**: Retry budget (not unlimited retries). Circuit breaker
  state machine (closed -> open -> half-open). Bulkhead isolation. Graceful
  degradation strategies (serve stale, hide feature, shed load). Rate limiting
  algorithms (token bucket, sliding window, leaky bucket). Chaos engineering.
- **Problems**: Rate limiter, API gateway, every system at the failure mode step.

### Observability

**Purpose**: Metrics, logs, traces. SLOs/SLIs/error budgets. Alerting. Health
checks.

- **Reach for it**: Every production system. The coverage sweep should always
  ask: "How do we know this is healthy?"
- **Key tradeoff**: Comprehensive instrumentation (high visibility, high
  cardinality cost) vs targeted metrics (lower cost, risk of blind spots).
- **PE depth signal**: SLO definition tied to user experience, not server health.
  Error budget policy (freeze deploys when budget exhausted). RED method
  (rate, errors, duration) for services. USE method (utilization, saturation,
  errors) for resources. Distributed tracing with context propagation.

### Distributed Logging

**Purpose**: High-volume log collection, shipping, indexing, retention pipeline.

- **Reach for it**: Systems with high event volume where logs are a primary
  debugging tool.
- **Key tradeoff**: Centralized (ELK/Datadog -- queryable, expensive at scale)
  vs sampled (reduces cost, loses rare events).
- **PE depth signal**: Structured logging with correlation IDs. Log levels and
  dynamic level adjustment. Retention policies and tiered storage. Log pipeline
  backpressure and dropping strategy.

---

## L7 -- Growth

### Scaling and Evolution

**Purpose**: How the design changes at 10x, 100x, 1000x. Bottleneck diagnosis.
Stateless tier extraction. Vertical vs horizontal scaling.

- **Reach for it**: The wrap-up of every design. "What breaks next?"
- **Key tradeoff**: Vertical scaling (simple, limited ceiling) vs horizontal
  (complex, but unbounded). Scaling the read path (replicas, cache) vs write
  path (sharding, async) have different tools.
- **PE depth signal**: Identify the specific bottleneck at the next order of
  magnitude. Distinguish "add more of the same" from "fundamental architecture
  change." Migration strategy from current to next architecture (not a rewrite
  fantasy). Capacity planning triggers and automation.
- **Problems**: Every problem at the evolution step.
