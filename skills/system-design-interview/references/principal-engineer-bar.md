# Principal Engineer Evaluation Bar

Score every design across these 10 dimensions. PE bar: average 4.5+, no
dimension below 4. After scoring, name the weakest dimension and what would
raise it. Never declare a design complete without this step.

---

## The 10 Dimensions

### 1. Problem Reframing (0-5)

Does the candidate question the problem itself, or blindly comply with the
prompt?

| Score | Signal |
|-------|--------|
| 5 | Reframes the problem to expose a simpler or more impactful formulation. Surfaces 2-3 hidden requirements the interviewer did not state. Proposes scope that reveals deep domain judgment. |
| 4 | Questions key assumptions. Identifies at least one hidden requirement. Scope is deliberate and justified. |
| 3 | Clarifies functional and non-functional requirements. States out-of-scope. No reframing. |
| 2 | Lists requirements but misses non-functional constraints or scope boundaries. |
| 1 | Jumps to design without clarifying. |

**Anti-pattern**: Accepting "design a top-K system" at face value without asking
whether the use case needs exact counts or approximate trending, whether windows
are tumbling or sliding, whether personalization is in scope.

**PE move**: "Before we design: do your users consume this as a leaderboard with
exact positions, or as a trending feed where directional accuracy suffices?
Because approximate counting with Count-Min Sketch saves us 100x memory and
eliminates the write bottleneck entirely."

---

### 2. Quantitative Grounding (0-5)

Do numbers force the architecture, or does the candidate design first and
retrofit numbers?

| Score | Signal |
|-------|--------|
| 5 | Full estimation chain (DAU -> QPS -> storage -> bandwidth -> servers) drives every architectural decision. Can re-derive instantly when an input changes. Orders of magnitude, not false precision. |
| 4 | Estimates QPS, storage, and working set. Numbers visibly influence component choices. |
| 3 | Some estimation but not connected to decisions. "We have 100K QPS" without explaining what that forces. |
| 2 | Vague scale references ("high traffic", "lots of data"). |
| 1 | No estimation. |

**Anti-pattern**: "This is high scale so we need Kafka and Redis." Scale is a
number, not a vibe.

**PE move**: "70B views/day / 100K seconds = 700K TPS. A single Postgres node
handles ~1K TPS for indexed writes. So we need either 700 shards (absurd) or a
fundamentally different write path -- stream aggregation with Flink reducing the
700K individual events to ~10K batched updates per hour."

---

### 3. Solution Space Navigation (0-5)

Does the candidate present one design and defend it, or map the solution space
and select with judgment?

| Score | Signal |
|-------|--------|
| 5 | Lays out 2-3 distinct architectures for the most contested decision. Names the forces that pick between them. Selects with stated tradeoffs. Can pivot instantly to an alternative when a constraint changes. |
| 4 | Acknowledges alternatives for major decisions. Selection is justified. |
| 3 | One design with some awareness of alternatives mentioned in passing. |
| 2 | Single design, defended when challenged. |
| 1 | Memorized architecture applied regardless of constraints. |

**Anti-pattern**: Presenting a Kafka -> Flink -> Redis pipeline as the only
option without considering simpler alternatives (Postgres with materialized
views, Redis alone with sorted sets, or batch processing for cold windows).

**PE move**: "For the hot 1-hour window, stream processing is forced by our
sub-minute freshness requirement. But for the monthly window, where staleness
of 15 minutes is acceptable, we have three viable paths: (1) extend the stream
job with larger state, (2) batch aggregation from the hourly tables, (3)
maintain rolling aggregates in the DB. Path 2 is cheapest and simplest -- the
monthly top-K changes slowly enough that a 5-minute cron is sufficient."

---

### 4. Trade-off Rigor (0-5)

For every major choice, can the candidate answer all three: what does it solve,
what does it make worse, what would make me change it?

| Score | Signal |
|-------|--------|
| 5 | Every major decision has the full triad. Tradeoffs are specific to this system's constraints, not generic. Connects worsened dimensions to concrete mitigation or acceptance criteria. |
| 4 | Most decisions have the triad. Tradeoffs are accurate and specific. |
| 3 | Some tradeoff awareness but incomplete. Generic tradeoffs ("CAP theorem") without connecting to this system. |
| 2 | Names technologies without justification. |
| 1 | No tradeoff discussion. |

**Anti-pattern**: "We use Kafka because it's industry standard for event
streaming." Industry standard is not a justification.

**PE move**: "Kafka solves our write buffering and replay-on-failure needs. It
worsens operational complexity (ZooKeeper/KRaft, topic management, consumer lag
monitoring) and adds 10-100ms of end-to-end latency. We would change this if
our freshness requirement tightened to sub-10ms -- at that point, in-process
aggregation with checkpointed state becomes necessary."

---

### 5. Depth on Demand (0-5)

Can the candidate go 3 levels deeper than the architecture diagram on any
component?

| Score | Signal |
|-------|--------|
| 5 | Goes to algorithm internals, protocol mechanics, mathematical foundations. Understands behavior under stress at the implementation level. Can teach the interviewer something. |
| 4 | Solid depth on 2-3 components. Knows the mechanics, not just the name. |
| 3 | Surface-level depth. Knows what a component does but not how it behaves under edge conditions. |
| 2 | Can name components but cannot explain their internals. |
| 1 | Treats all components as black boxes. |

**Anti-pattern**: "We use a Count-Min Sketch for approximate counting" without
being able to explain the width/depth sizing, collision behavior, conservative
update optimization, or why CMS overcounts but never undercounts.

**PE move**: Deriving CMS error bounds: "Width w = ceil(e/epsilon), depth d =
ceil(ln(1/delta)). For epsilon=0.01, delta=0.001: w=272, d=7. Memory = 272 * 7
* 4 bytes = 7.4 KB per sketch. We need one per (window, segment), so 6000
sketches * 7.4 KB = 44 MB total. That fits in a single Flink task's memory with
room to spare."

---

### 6. Failure Mode Mastery (0-5)

Does the candidate design for the world where everything fails?

| Score | Signal |
|-------|--------|
| 5 | Identifies every SPOF. Has a degradation story for each (stale > error). Knows that "more retries" amplifies outages. Designs recovery to avoid stampedes. Cites real incidents. |
| 4 | Identifies major failure modes. Degradation story exists. Recovery is considered. |
| 3 | Mentions failure modes but no degradation story. "We add replicas." |
| 2 | Assumes components don't fail. |
| 1 | No failure discussion. |

**Anti-pattern**: "If the stream processor fails, we just restart it." Without
addressing: What happens to in-flight state? How long is recovery? What serves
users during recovery? Does the restart cause a cascade?

**PE move**: "Flink recovery from checkpoint takes 5-15 minutes for 50-100 GB
state. During recovery: (1) Redis continues serving the last-written top-K --
stale but functional, (2) Kafka retains events with 7-day retention so nothing
is lost, (3) we run a hot standby job at 2x cost for sub-minute failover on
critical paths. The staleness during recovery is bounded by our checkpoint
interval (1-5 minutes), which is within our 1-minute freshness SLA."

---

### 7. Production Grounding (0-5)

Does the design feel like something the candidate has built, or something they
read about?

| Score | Signal |
|-------|--------|
| 5 | References specific production systems and their actual behavior. Cites real incidents and lessons learned. Operational patterns (deploy strategy, monitoring, capacity planning) are concrete and practiced. |
| 4 | Production references are accurate and relevant. Some operational awareness. |
| 3 | Mentions production systems but details are vague or possibly incorrect. |
| 2 | Textbook knowledge only. |
| 1 | No production context. |

**Anti-pattern**: "Google uses Bigtable for this kind of problem." Without
knowing why (sorted string tables, column-family flexibility, auto-sharding)
or when Bigtable is the wrong choice (small datasets, strong consistency needs,
complex queries).

---

### 8. Organizational Awareness (0-5)

Does the candidate think about the humans who will build, deploy, and operate
this system?

| Score | Signal |
|-------|--------|
| 5 | Considers team ownership boundaries, blast radius of failures and deploys, oncall burden, cross-team dependencies, migration strategy from existing systems. |
| 4 | Mentions ownership and operational impact. Deployment strategy is realistic. |
| 3 | Design is technically sound but ignores who owns what and how it gets deployed. |
| 2 | Implicit assumption that one team builds and owns everything. |
| 1 | No organizational consideration. |

**PE move**: "This system spans three ownership boundaries: the ingestion
pipeline (data platform team), the aggregation layer (real-time infra team),
and the serving API (product team). The interface contract between ingestion
and aggregation is the Kafka topic schema -- we version it with a schema
registry to prevent breaking changes. The aggregation team owns the SLO for
freshness; the product team owns the SLO for query latency."

---

### 9. Evolution Vision (0-5)

Does the candidate see where this system is going, not just where it is?

| Score | Signal |
|-------|--------|
| 5 | Articulates what breaks at 10x, 100x, 1000x. Names specific assumptions that will not hold. Distinguishes what to rebuild from what to extend. Has a migration strategy, not a rewrite fantasy. |
| 4 | Identifies the next bottleneck and has a plan for it. |
| 3 | Mentions scaling vaguely ("we'd shard more"). |
| 2 | Design is static. No forward-looking perspective. |
| 1 | No evolution discussion. |

**PE move**: "At 10x (7B views/day), Flink state grows to ~500 GB per window
-- exceeds single-task memory. We shard the aggregation by video-ID hash across
task slots. At 100x, the Kafka topic needs 5000+ partitions and the Redis
sorted sets become the bottleneck. At that point, we move to an in-Flink top-K
with direct cache push, eliminating the DB entirely for the hot path."

---

### 10. Collaboration Signal (0-5)

Is this a design review between peers, or a lecture?

| Score | Signal |
|-------|--------|
| 5 | Proposes, invites critique, adapts in real time. Treats constraint changes as opportunities, not attacks. Admits uncertainty and explores jointly. |
| 4 | Collaborative tone. Responds well to challenges. |
| 3 | Mostly monologue but accepts feedback. |
| 2 | Defensive when challenged. |
| 1 | Refuses to adapt. |

**Anti-pattern**: "No, we need Kafka here because..." (defending a sunk
decision when the constraint that justified it has changed).

---

## Scoring Template

After completing a design, fill this:

```
PE Rubric Score:
 1. Problem reframing:     _/5
 2. Quantitative grounding: _/5
 3. Solution space:         _/5
 4. Trade-off rigor:        _/5
 5. Depth on demand:        _/5
 6. Failure modes:          _/5
 7. Production grounding:   _/5
 8. Organizational:         _/5
 9. Evolution vision:       _/5
10. Collaboration:          _/5

Average: _/5
Weakest dimension: [name] -- [what would raise it]
```

PE bar: average 4.5+, no dimension below 4.
