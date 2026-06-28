# Company Profiles -- PE-Level System Design Interviews

Interview patterns, evaluation axes, and what makes a Principal Engineer
candidate stand out at each target company.

---

## Google

### Interview Format
- 1-2 system design rounds (45 min each) within a 5-6 round loop.
- Interviewer is typically a Senior Staff+ engineer from the target org.
- Virtual or onsite. Whiteboard or shared doc.

### Evaluation Axes
- **Distributed systems depth** is the primary differentiator. Google expects
  you to reason about consistency, replication, and partitioning at a level
  that reflects building systems at Google scale.
- **Scale reasoning**: Google operates at a scale where most shortcuts break.
  They want to see you reason about billions of entities, millions of QPS.
- **Data modeling rigor**: Schema design, access patterns, and storage engine
  choice are probed deeply.

### Signature Systems to Reference
- **Bigtable**: Sorted string table (SSTable) architecture, column families,
  tablet splitting, compaction. Use when discussing wide-column storage.
- **Spanner**: Globally distributed SQL with TrueTime. Use when discussing
  strong consistency at global scale.
- **Colossus/GFS**: Distributed file system. Use when discussing blob storage
  or chunk-based replication.
- **Borg/Kubernetes**: Container orchestration. Use when discussing service
  deployment and resource scheduling.
- **MapReduce/Dataflow**: Batch and stream processing. Use when discussing
  data pipelines.
- **Zanzibar**: Global authorization system. Use when discussing access control
  at scale.

### PE Expectations at Google
- Can reason about globally distributed systems with cross-region consistency.
- Understands why Spanner needs TrueTime and what happens without it.
- Does not treat "just use Bigtable" as a complete storage answer -- knows
  when Bigtable is wrong (small datasets, strong consistency needs, complex
  joins).
- Thinks about Borg-level deployment: how the system gets scheduled, resource
  limits, bin-packing efficiency.

### Communication Style
- Technical depth is valued over presentation polish. Google prefers candidates
  who can go deep on any component rather than those who give a polished but
  surface-level overview.
- "Googliness": collaborative, curious, willing to be wrong and adapt.

---

## Amazon

### Interview Format
- 1 system design round (60 min) in a 5-6 round loop (includes bar raiser).
- Heavy emphasis on Leadership Principles alongside technical depth.
- Virtual loop is standard. Whiteboard or shared doc.

### Evaluation Axes
- **Operational excellence**: Amazon cares intensely about how systems fail,
  how they recover, and how you prevent the blast radius from spreading.
- **Ownership and blast radius**: Who owns this? What happens when it breaks
  at 2 AM? How do you limit the damage?
- **Service-oriented architecture**: Amazon pioneered SOA. They expect you to
  think in services with clear ownership boundaries.
- **Leadership Principles**: Every answer is evaluated against LPs. "Disagree
  and commit", "Dive deep", "Bias for action" should be visible in your
  design process.

### Signature Systems to Reference
- **DynamoDB**: Single-digit millisecond KV store with predictable performance.
  Use when discussing partition key design, provisioned vs on-demand capacity.
- **SQS/SNS**: Queue and pub/sub. Use when discussing async decoupling.
- **Kinesis**: Real-time streaming. Use when discussing event ingestion.
- **S3**: Object storage with 11 nines durability. Use when discussing blob
  storage and data lakes.
- **Aurora**: MySQL/Postgres-compatible with storage-compute separation. Use
  when discussing relational storage at scale.
- **Step Functions**: Workflow orchestration. Use when discussing sagas and
  multi-step processes.

### PE Expectations at Amazon
- Thinks in terms of services with clear API contracts and SLAs between them.
- Designs for operational excellence: runbooks, alarms, deployment strategy,
  rollback plan.
- Considers blast radius of every failure and every deploy.
- Can articulate the "two-pizza team" ownership model for the system.
- Mentions cell-based architecture for fault isolation.

### Communication Style
- STAR format for behavioral signals embedded in design discussion.
- Ownership mentality: "I would own this" not "someone would build this."
- Data-driven decisions, metrics-first.

---

## Microsoft

### Interview Format
- 1-2 system design rounds (45-60 min) in a 4-5 round loop.
- Often includes "design review" format: present your design and defend it.
- Virtual or onsite (Redmond/remote).

### Evaluation Axes
- **Enterprise-scale thinking**: Microsoft serves enterprise customers with
  different constraints (compliance, hybrid cloud, SLAs with financial
  penalties).
- **Reliability at scale**: Azure operates massive multi-tenant infrastructure.
  Reliability engineering is deeply valued.
- **Breadth**: Microsoft expects you to consider the full stack, from client
  to infrastructure, including deployment, monitoring, and security.

### Signature Systems to Reference
- **Azure Cosmos DB**: Multi-model, globally distributed DB with tunable
  consistency (5 levels from strong to eventual). Use when discussing
  consistency model selection.
- **Service Fabric**: Microservices platform with stateful services. Use when
  discussing stateful service patterns.
- **Azure Event Hubs**: Event streaming (Kafka-compatible). Use when discussing
  event ingestion at scale.
- **Azure Functions / Durable Functions**: Serverless with durable execution.
  Use when discussing workflow orchestration.

### PE Expectations at Microsoft
- Considers multi-tenant isolation and noisy neighbor problems.
- Thinks about compliance requirements (SOC2, GDPR, FedRAMP) as first-class
  design constraints.
- Understands hybrid cloud scenarios (on-prem + cloud).
- Designs for enterprise SLAs with financial penalties for downtime.

### Communication Style
- Structured and methodical. Clear problem statement before design.
- Expects to discuss security and compliance proactively.

---

## Databricks

### Interview Format
- 1-2 system design rounds (45-60 min) in a 5-6 round loop.
- Strong bias toward data systems and data engineering problems.
- Interviewer expects deep knowledge of data processing paradigms.

### Evaluation Axes
- **Data systems expertise**: This is the dominant signal. Understanding of
  storage formats, query engines, data pipelines, and the lakehouse paradigm.
- **Distributed computation**: Spark, distributed SQL, shuffle optimization,
  data skew handling.
- **Storage layer design**: Column-oriented formats (Parquet, ORC), Delta Lake
  transaction log, time travel, schema evolution.
- **ML infrastructure**: Feature stores, model serving, training pipeline
  orchestration.

### Signature Systems to Reference
- **Delta Lake**: ACID transactions on data lakes via a transaction log.
  Optimistic concurrency with conflict resolution. Time travel. Schema
  enforcement and evolution.
- **Apache Spark**: Distributed computation engine. RDD lineage, catalyst
  optimizer, tungsten memory management, adaptive query execution.
- **Unity Catalog**: Unified governance for data and AI assets. Fine-grained
  access control across workspaces.
- **MLflow**: ML lifecycle management. Experiment tracking, model registry,
  model serving.
- **Photon**: Vectorized query engine written in C++. Use when discussing
  query performance optimization.

### PE Expectations at Databricks
- Deep understanding of columnar storage formats and their performance
  implications (predicate pushdown, column pruning, min/max statistics).
- Can reason about data skew and its mitigation (salting, adaptive partitioning).
- Understands the Delta Lake transaction log protocol and how it achieves
  ACID semantics on object storage.
- Thinks about query optimization: join strategies, broadcast vs shuffle,
  partition pruning.
- Can design an end-to-end data pipeline from ingestion to serving with
  exactly-once guarantees.

### Communication Style
- Depth-first. They want to see you reason through data system internals.
- Practical experience with large-scale data processing is a strong signal.

---

## Anthropic

### Interview Format
- 1 system design round (60 min) in a 4-5 round loop.
- Problems skew toward ML infrastructure, model serving, and safety-critical
  systems.
- Smaller company; interviewers are often founders or early engineers.

### Evaluation Axes
- **ML serving infrastructure**: How to serve large language models at scale
  with low latency and high throughput.
- **Safety-critical systems**: Systems where correctness has outsized
  consequences. Monitoring, fallback, human-in-the-loop.
- **Scaling inference**: GPU cluster management, batching strategies, KV cache
  management, model parallelism.
- **Systems thinking**: How infrastructure decisions affect product safety and
  alignment research velocity.

### Signature Systems to Reference
- **Model serving at scale**: vLLM, TensorRT-LLM, Triton Inference Server.
  Continuous batching, PagedAttention, speculative decoding.
- **GPU cluster management**: NVIDIA InfiniBand, NVLink topology, multi-node
  training with FSDP/DeepSpeed. Scheduling for GPU utilization.
- **Safety infrastructure**: Content filtering pipelines, Constitutional AI
  enforcement layers, monitoring for model behavior drift.
- **API gateway for AI**: Token-based rate limiting, streaming responses
  (SSE), multi-model routing, usage metering.

### PE Expectations at Anthropic
- Understands the unique constraints of serving LLMs: memory-bound inference,
  KV cache growth, prefill vs decode phases.
- Can reason about batching strategies (continuous batching, iteration-level
  scheduling) and their impact on latency vs throughput.
- Thinks about safety as a system property, not an afterthought. Monitoring
  for harmful outputs, fallback policies, graceful degradation.
- Understands the research-to-production pipeline: how to build infrastructure
  that accelerates alignment research without compromising safety.

### Communication Style
- Intellectual depth valued. Be ready to discuss novel approaches.
- Mission-driven: connect your design to Anthropic's safety mission.
- Small team mentality: think about operational burden on a small infra team.

---

## OpenAI

### Interview Format
- 1-2 system design rounds (45-60 min) in a 5-6 round loop.
- Problems focus on AI infrastructure, API platforms, and real-time systems.
- Fast-growing company; interview process may evolve.

### Evaluation Axes
- **AI infrastructure at scale**: GPU cluster management, inference serving,
  training pipeline reliability.
- **API platform design**: Rate limiting, metering, multi-model routing,
  streaming responses, developer experience.
- **Real-time systems**: ChatGPT-scale real-time interaction, WebSocket
  management, stateful conversation handling.
- **Reliability under growth**: Systems that scale with hypergrowth while
  maintaining reliability.

### Signature Systems to Reference
- **ChatGPT infrastructure**: Stateful conversation management, streaming
  token delivery, function calling routing, plugin/tool execution.
- **API gateway at scale**: Token-based rate limiting (not request-based),
  usage-based billing, API key management, multi-model routing.
- **Training infrastructure**: Large-scale distributed training, checkpoint
  management, training run reliability, GPU scheduling.
- **Inference optimization**: Batching, quantization (INT8/INT4), model
  parallelism (tensor, pipeline), speculative decoding.

### PE Expectations at OpenAI
- Can design inference serving that optimizes for both latency (time-to-first-
  token) and throughput (tokens/second across all requests).
- Understands token-based economics: cost per token, how batching amortizes
  GPU cost, when to use smaller models.
- Designs API platforms with developer experience as a first-class concern:
  clear error messages, predictable rate limiting, streaming with backpressure.
- Thinks about the GPU scheduling problem: how to maximize utilization across
  heterogeneous workloads (short inference, long training, fine-tuning).

### Communication Style
- Move fast, practical solutions. Less academic, more "what ships."
- Strong opinions, loosely held. Be ready to pivot quickly.
- Engineering velocity matters: designs that are simple to implement and
  iterate on are valued over architecturally perfect but slow-to-build systems.
