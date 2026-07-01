# Orchestrator -- Generate-Evaluate-Fix Loop

This file defines the execution protocol for producing a Principal-Engineer-grade
system design. It is not a checklist. It is a loop engine with gates, iteration
limits, and exit conditions.

Every platform wrapper (Cursor SKILL.md, CLAUDE.md, AGENTS.md, ChatGPT prompt)
delegates execution to this file.

---

## Execution Overview

```
For each phase 1-6:
  INNER LOOP (max 2 iterations):
    1. GENERATE the phase output file(s)
    2. EVALUATE against the phase gate
    3. PASS → proceed to next phase
    4. FAIL → identify failure, FIX only that part, re-evaluate
    5. After 2 failures: document in context checkpoint "known issues" and
       fix in outer eval loop — do NOT proceed with known Gate failures on
       capacity chain, start-cheap design, or missing failure flows.

After all 6 phases:
  INTERVIEWER-RESEARCH LOOP (default after Phases 4, 5, 6):
    1. Interviewer agent reviews generated files blind to self-scores
    2. If findings are critical/major -> Research agent investigates only those gaps
    3. Revise affected sections and append evidence to 10-interview-transcript.md
  CROSS-FILE CONSISTENCY PROTOCOL (5 checks)
  OUTER EVAL LOOP (max 1 revision pass):
    1. Score all 10 PE rubric dimensions using the Interviewer's independent findings
    2. If avg ≥ 4.5 and no dim < 4 → DONE
    3. Else → revise weakest file section, re-score
  VALIDATOR HARNESS:
    1. Run python validator → produces 09-eval-report.md
    2. If FAIL: fix flagged issues (max 1 pass), re-run
    3. Final output: 10 files plus diagram with traceable PASS/FAIL evidence
```

---

## Before Starting

1. Read `references/reasoning-engine.md` lines 1-131 (phase descriptions only).
   Skip the failure modes and checklists -- they are needed only at Phase 6.
2. Read `references/faang-interview-patterns.md` for world-class calibration
   (requirements framing, estimation chain, HLD incremental design, company bar).
3. Scan existing problem folders in the output directory (default:
   `system-design/` relative to the user's project root) to check for slug
   collisions. Derive `<problem-name>` as a short kebab-case slug from the
   prompt (e.g., "url-shortener", "distributed-cache", "news-feed").
4. **Load the phase skill** from `references/` (e.g., `requirements-skill.md` for
   Phase 1, `hld-skill.md` for Phase 4). Read it before the template.
5. **Load the phase template** from `assets/templates/` for the current phase
   (e.g., `01-requirements.template.md`). Fill every required section; do not
   skip headings the template defines.
6. Read one exemplar file (not all 8) from `assets/exemplars/` matching the
   current phase **and provisional shape** when calibrating output quality.
   Exemplars must pass the validator — use them for depth and tone, templates
   for structure. **Never default to A7 trending for non-aggregate prompts.**
7. If the user names a company, read `references/company-profiles.md` and
   apply the calibration table in `faang-interview-patterns.md`.
8. If the user asks "what should I practice," read `references/problem-bank.md`.

Do NOT preload all 7 reference files. Load just-in-time per phase.

### Optional agent independence

When the platform supports explicit model selection, run the Interviewer agent
with a different model family from the generator (for example, GPT judging a
Claude-generated design). When unavailable, use the same model with the
Interviewer prompt from `references/interviewer-protocol.md`. In both cases, the
Interviewer must be blind to self-scores and phase gate PASS/FAIL claims.

---

## Phase 1: Frame the Problem

**Output**: `01-requirements.md`
**Load (in order — do not skip):**
1. `references/requirements-skill.md` — **primary** problem-agnostic requirements skill
2. `references/numbers-to-know.md`
3. `references/faang-interview-patterns.md`
4. `references/hld-archetypes.md` — provisional shape classification only
5. `assets/templates/01-requirements.template.md`

**Exemplar (optional, shape-matched only):**

| If provisional shape is… | Read `01-requirements.md` |
|--------------------------|---------------------------|
| A3 Read-scaled | `assets/exemplars/in-memory-cache/` |
| A7 Aggregate / top-K | `assets/exemplars/trending-articles-top-k/` |
| A1 CRUD / other | **No requirements exemplar** — skill + template only |

Follow `requirements-skill.md` and the template. This phase combines
**functional requirements and the full capacity estimation chain** — FAANG
interviews treat scale as part of requirements, not a separate afterthought.

- State functional requirements with company-scale context (2–4 core features).
- **Early problem shape**: provisional archetype + dominant force + read:write ratio.
- **Problem reframing**: question the prompt; surface hidden requirements.
- **Capacity estimation chain** (all links required):
  DAU → read QPS → write QPS → storage/day → total storage → bandwidth →
  server count. Show assumptions and math inline. Use shape-aware component load
  rows only when the archetype requires them.
- **Growth trajectory**: 1×, 10×, 100× inputs and what breaks first at each tier.
- **Success metrics (SLIs)**: 2–3 measurable signals before architecture.
- Explicit out-of-scope: minimum 3 items, each with one-line reasoning.

### Gate 1 -- evaluate before proceeding

| # | Criterion | Pass condition |
|---|-----------|----------------|
| a | Capacity chain complete | All links: DAU, read QPS, write QPS, storage/day, total storage, bandwidth, server count. |
| b | Reframing present | At least 1 problem reframing or hidden requirement (not just clarifications). |
| c | Out-of-scope coverage | At least 3 out-of-scope items, each with one-line reasoning. |
| d | Numbers plausibility | Cross-check against `numbers-to-know.md`. Order-of-magnitude correct. |
| e | Growth trajectory | 10× and 100× scale inputs stated with first breaking constraint. |

**If any criterion fails**: identify the specific gap, fix only that section of
`01-requirements.md`, re-evaluate. Max 2 iterations.

---

## Phase 2: Set the Constraints

**Output**: `02-non-functional-requirements.md`
**Load (in order):**
1. `references/nfr-skill.md` — **primary** NFR derivation skill
2. `references/numbers-to-know.md`
3. `assets/templates/02-non-functional-requirements.template.md`

**Exemplar (optional, shape-matched):** same table as Phase 1 (`02-non-functional-requirements.md`).

NFRs must **trace to Phase 1 numbers**. Do not invent a separate scale story.
Follow `nfr-skill.md` for shape-aware latency paths and consistency tables.

- Percentile latency targets (P50/P95/P99/P99.9) with latency budget breakdown
  that sums to P99 (±10%).
- Availability with SRE error budget math (concrete downtime per month).
- Consistency model with explicit user-facing consequence.
- Durability guarantees by data class (RPO/RTO table).
- Security NFRs (auth, encryption, abuse).
- Operational requirements: zero-downtime deploy, monitoring thresholds, runbook
  sketch for top failure scenario.

### Gate 2 -- evaluate before proceeding

| # | Criterion | Pass condition |
|---|-----------|----------------|
| a | Latency budget sums | Breakdown components sum to the stated P99 target (±10%). |
| b | Error budget concrete | Produces a specific number (e.g., "22 min downtime/month at 99.95%"). |
| c | Consistency consequence | Names the user-facing effect (e.g., "user may see stale feed for up to 5s"), not just "eventual consistency." |
| d | Runbook exists | At least 1 runbook sketch for a top failure scenario with specific steps. |

---

## Phase 3: Define the Interface

**Output**: `03-entities.md`, `04-api-design.md`, `05-schema.md`
**Load (in order):**
1. `references/interface-skill.md` — **primary** unified entities/API/schema skill
2. `references/building-blocks-index.md` (L4 storage vocabulary)
3. `assets/templates/03-entities.template.md`
4. `assets/templates/04-api-design.template.md`
5. `assets/templates/05-schema.template.md`

**Exemplar (optional, shape-matched):**

| Shape | Read |
|-------|------|
| A3 | `assets/exemplars/in-memory-cache/03–05` |
| A7 | `assets/exemplars/trending-articles-top-k/03–05` |
| A1 / other | **Skill + templates only** |

Complete **one design pass** per `interface-skill.md` — access patterns from
Phase 1–2 drive all three files.

Entities:
- Core domain objects, relationships, cardinality, lifecycle.
- State machines for entities with multiple states.

API:
- Concrete REST or gRPC contracts with exact request/response shapes.
- Cursor-based pagination at scale, idempotency keys, versioning, rate
  limiting headers, error contract.

Schema:
- Primary keys, sort keys, indexes with access pattern justification.
- Partitioning/sharding strategy tied to Phase 1 capacity numbers.
- **PE signal**: Access patterns drive schema. Denormalization justified by
  read/write ratio. Index choices with cost analysis.

### Gate 3 -- evaluate before proceeding

| # | Criterion | Pass condition |
|---|-----------|----------------|
| a | API shapes concrete | Every endpoint has explicit request shape AND response shape. No "returns data." |
| b | Schema-API alignment | Every API access pattern has a matching index or scan strategy in schema. |
| c | Sharding justified | Partition/shard key traces to write QPS from Phase 1. Reasoning stated. |
| d | State machines present | Entities with multiple states have explicit state machine diagrams. |

---

## Context Checkpoint -- run after Phase 3

After files 01-05 are generated and gated, create a running summary to carry
forward. This replaces re-reading all 5 files during Phases 4-6.

```
## Context Checkpoint
- Problem: [one sentence]
- Scale: [DAU, read QPS, write QPS, total storage]
- Key NFRs: [P99 latency, availability target, consistency model]
- Core entities: [list with cardinality]
- Critical access patterns: [top 3-5 from API design]
- Sharding key: [from schema]
- Constraints that force architecture: [top 2-3]
- Known issues from gates: [any flagged weaknesses]
```

Do NOT re-read files 01-05 in full during Phases 4-6. Use this checkpoint.

---

## Phase 4: Design the Architecture

**Output**: `06-high-level-design.md`
**Load (in order — do not skip):**
1. `references/hld-skill.md` — **primary** problem-agnostic HLD skill
2. `references/hld-archetypes.md` — classify shape before any diagram
3. `references/building-blocks-index.md` — capability vocabulary
4. `references/tradeoff-framework.md`
5. `references/research-protocol.md` — when Section 4 research is open
6. `assets/templates/06-high-level-design.template.md`

**Exemplar (optional, shape-matched only):**

| If archetype is… | Read HLD exemplar |
|------------------|-------------------|
| A1 Point CRUD | `assets/exemplars/url-shortener/06-high-level-design.md` |
| A3 Read-scaled | `assets/exemplars/in-memory-cache/06-high-level-design.md` |
| A7 Aggregate / top-K | `assets/exemplars/trending-articles-top-k/06-high-level-design.md` |
| Other / mixed | **No HLD exemplar** — skill + template only |

**Never** default to the trending/top-K exemplar. If the prompt is not aggregation-heavy, loading it will bias the design.

### Phase 4 workflow (from hld-skill.md)

1. **Problem Shape Classification** — signals table + primary archetype
2. **Required Capabilities** — no product names; now/defer/skip per capability
3. **Architecture Evolution** — credible v0 at 1×; breaking points with numbers
4. **Architecture Research** — ≥2 contested capabilities (or 1 if trivial CRUD at low QPS)
5. **System Overview** — topology from **archetype**, not a default pipeline
6. **Flows 1–4** — write, read (latency budget), failure, deploy
7. **Component Registry** — Role | Implementation | Capacity | Failure | Owner
8. **Trade-off triads** — per capability added after v0
9. **Production evidence** — tied to decisions made above

**Do not** start with product names. **Do not** assume ingest→log→stream→cache unless A7 (or hybrid) classification requires it.

### Mandatory Flow Coverage

The HLD MUST explicitly cover 4 flows:

1. **Write/Data Flow**: End-to-end path from client write to durable storage.
   Show every hop with protocol (gRPC, HTTP, async queue) and latency
   contribution.

2. **Read/Query Flow**: End-to-end path from client query to response. Include
   latency budget per hop (must sum to the P99 target from Phase 2).

3. **Failure Flow**: For at least 2 critical components, trace what happens
   when they fail. Show the degradation cascade: which users see what, for how
   long, and how recovery happens without stampede.

4. **Deploy Flow**: How the system is updated without downtime. Canary/
   blue-green/rolling strategy. What rollback looks like. Migration strategy
   for schema changes.

### Component Annotations

Every major component (not leaf utilities) in the architecture MUST have:

- **Capacity**: The QPS, storage, or throughput it handles (from Phase 1/2).
- **Failure mode**: What breaks when it goes down, and how the system degrades.
- **Owner**: Which team operates it (for organizational awareness scoring).

### Gate 4 -- evaluate before proceeding

| # | Criterion | Pass condition |
|---|-----------|----------------|
| a | Starting design valid | The "cheap" starting design genuinely handles current-scale numbers from the context checkpoint (not a strawman dismissed in one sentence). |
| b | Components justified | Every component added beyond starting design traces to a specific bottleneck number from the checkpoint. |
| c | Options presented | At least **2 contested capabilities** (or 1 if trivial low-QPS CRUD) with 2–3 options and numeric justification. |
| c2 | Shape-led design | `Problem Shape Classification` + archetype present; capabilities include explicit **skip** for irrelevant patterns (e.g. no stream if not A7). |
| c3 | Research before products | `Architecture Research` sections present; diagram topology matches archetype, not a default pipeline. |
| d | Checkpoint consistency | Architecture handles the QPS, storage, and latency from the context checkpoint. Spot-check: do the numbers match? |
| e | Failure flow present | At least 2 component failures are traced through the system showing degradation behavior, recovery path, and user-facing impact. |
| f | Deploy flow present | Canary/rolling strategy, schema migration, and rollback documented. |
| g | Component registry | Table with capacity, failure mode, and owner for each major component. |
| h | Read-path latency budget | Per-hop budgets in Flow 2 sum to Phase 2 P99 (±10%). |

---

## Phase 4b: Visual Diagram

**Output**: `06-high-level-design.excalidraw`
**Load**: The `excalidraw-diagram` companion skill (bundled in this repository
at `../../excalidraw-diagram/SKILL.md`, or use `$excalidraw-diagram` if your
agent supports skill references)

After Gate 4 passes, read the Excalidraw diagram skill and follow its design
process to produce a visual companion diagram. Use the architecture from
`06-high-level-design.md` as the source content.

The Excalidraw diagram should:
- Separate read path (left or top) from write path (right or bottom)
- Annotate arrows with QPS and protocols (gRPC, HTTP, async)
- Annotate stores with capacity numbers from the context checkpoint
- Use color semantically per the skill's `references/color-palette.md`
- Follow the section-by-section generation strategy from the skill

The `.excalidraw` file is a companion to the `.md` — it does not replace the
ASCII diagram. The `.md` remains the primary artifact (text-searchable,
diffable, works in any renderer).

No separate gate for this phase. If the render-validate loop in the Excalidraw
skill produces a clean diagram, proceed.

---

## Interviewer Checkpoint A -- after Phase 4

**Output**: append to `10-interview-transcript.md`
**Load**: `references/interviewer-protocol.md`

Run the Interviewer agent against:
- `01-requirements.md` through `06-high-level-design.md`
- The context checkpoint
- The Phase 4 HLD and Excalidraw source context

Focus on:
- Wrong technology choices that are not forced by numbers
- Scale reasoning holes between requirements and HLD
- Missing failure/deploy flows
- Architecture options that were skipped too quickly

If the Interviewer produces any **Critical** or **Major** finding, load
`references/research-protocol.md` and run the Research agent only for those
findings. Revise the affected HLD sections before Phase 5. If findings are only
minor, fix locally and proceed without Research.

---

## Phase 5: Go Deep

**Output**: `07-deep-dives.md`
**Load (in order):**
1. `references/deep-dive-skill.md` — **primary** depth-on-demand skill
2. `references/reasoning-engine.md` (curveball protocol, lines 228-244)
3. `assets/templates/07-deep-dives.template.md`

**Exemplar (optional, shape-matched):**

| Shape | Read `07-deep-dives.md` |
|-------|-------------------------|
| A3 | `assets/exemplars/in-memory-cache/` |
| A7 | `assets/exemplars/trending-articles-top-k/` |
| A1 / other | **Skill + template only** |

Follow `deep-dive-skill.md` for component selection by archetype — do not default
to streaming/sketch dives unless Phase 4 classification requires them.

- **Minimum 4 deep dives** (recommend 5-6 for complex systems) on the most
  fragile or interesting components from Phase 4.
- Each deep dive has solution tiers:
  - **Workable**: Solves the problem. States limitations.
  - **Strong**: Addresses those limitations. States new challenges.
  - **Exceptional**: PE-grade insight. Novel optimization or non-obvious
    connection.
- Curveball handling per deep dive: name the constraint change, the
  invalidated assumption, blast radius scope, redesign only the affected part,
  verify that the rest holds.
- **PE signal**: Goes 3 levels deeper than the diagram. Teaches the reader
  something non-obvious.

### Mandatory Depth Requirements (per dive)

Each deep dive MUST include:

1. **Breaking Point**: A specific numeric threshold where the approach stops
   working. Not "at higher scale" but "at 500K QPS, the single Redis node
   exceeds its memory limit of 64 GB because..."

2. **Resiliency Pattern**: The specific pattern used to handle failure at this
   component (circuit breaker, bulkhead, retry budget, graceful degradation,
   stale-while-revalidate, etc.) with concrete configuration values.

3. **Depth Signal in Exceptional Tier**: Each Exceptional tier MUST contain at
   least ONE of:
   - Algorithm internals with complexity analysis (e.g., CMS sizing math,
     consistent hashing bounds, LSM compaction cost)
   - Protocol mechanics with sequence or state diagram (e.g., Raft leader
     election steps, Kafka rebalance protocol, 2PC commit flow)
   - Mathematical derivation or proof sketch (e.g., error bound derivation,
     probability analysis, capacity threshold formula)

### Gate 5 -- evaluate before proceeding

| # | Criterion | Pass condition |
|---|-----------|----------------|
| a | Dive targets relevant | Every deep-dived component appears in the Phase 4 HLD as fragile or interesting. No dives on components absent from the architecture. |
| b | Three tiers each | Each deep dive has all 3 tiers (Workable / Strong / Exceptional) with explicit limitations per tier. |
| c | Curveball protocol | Each deep dive has a "what if" with: (1) named constraint change, (2) invalidated assumption, (3) blast radius scope, (4) scoped redesign, (5) verification rest holds. |
| d | Depth signal | At least 1 deep dive includes algorithm internals, protocol mechanics, or mathematical reasoning that teaches something non-obvious. |
| e | Breaking point per dive | Each deep dive names a specific numeric threshold where the approach stops working (not "at higher scale" — a number). |

---

## Interviewer Checkpoint B -- after Phase 5

**Output**: append to `10-interview-transcript.md`
**Load**: `references/interviewer-protocol.md`

Run the Interviewer agent against:
- `06-high-level-design.md`
- `07-deep-dives.md`
- The context checkpoint

Focus on:
- Deep dives that repeat the HLD instead of going 2-3 levels deeper
- Algorithm or protocol name-drops without mechanics
- Missing math, thresholds, or recovery behavior
- Curveballs that do not invalidate a real assumption

If there are **Critical** or **Major** findings, run the Research agent for
those findings only. Revise the affected deep dives before Phase 6. Minor
findings are fixed locally unless the same minor pattern appears in multiple
dives.

---

## Phase 6: Stress-Test and Synthesize

**Output**: `08-bottlenecks-and-tradeoffs.md`
**Load (in order):**
1. `references/bottlenecks-skill.md` — **primary** synthesis skill
2. `references/principal-engineer-bar.md`
3. `references/building-blocks-index.md`
4. `references/tradeoff-framework.md`
5. `references/reasoning-engine.md` lines 152-244 (failure modes, coverage sweep)
6. `assets/templates/08-bottlenecks-and-tradeoffs.template.md`

**Exemplar (optional, shape-matched):** same table as Phase 5 (`08-bottlenecks-and-tradeoffs.md`).

Follow `bottlenecks-skill.md` — bottlenecks must trace to checkpoint numbers,
not generic stack assumptions.

- Bottleneck analysis: **minimum 6 bottlenecks**, each with root cause, 2-3
  mitigations, and a real-world incident or analogy.
- Tradeoff summary matrix covering every major decision from Phases 4-5.
- Interview talking points: 5-7 key points demonstrating PE understanding.
- Coverage sweep: scan building blocks index, confirm no relevant block was
  silently skipped.
- Evolution strategy: what changes at 10x and 100x.
- Self-assessment: score against the 10-dimension PE rubric.

### Mandatory Sections

The bottlenecks file MUST contain these sections:

1. **Failure Matrix**: A table with columns:
   `| Failure | Blast Radius | Detection | Degradation | Recovery | RTO |`
   Minimum 5 rows covering different failure classes: node crash, network
   partition, cascading failure, data corruption, deployment failure.

2. **Real-World Incidents**: Minimum 3 named production incidents from real
   companies (Facebook, Google, Twitter, LinkedIn, Amazon, Netflix, etc.)
   with root cause and lesson learned. Not fabricated — cite the company and
   approximate year.

3. **Anti-Patterns**: Minimum 3 common mistakes for this problem class. Each
   with: (a) the mistake, (b) why it seems right, (c) why it fails in
   production, (d) the correct approach.

4. **Evolution Roadmap**: Concrete breaking points at 10x and 100x with
   specific architectural changes required. Not "shard more" but "at 10x
   (7M QPS), the Redis sorted set ZADD becomes the bottleneck because ZADD
   is O(log N) and at 70K items per set..." Include migration strategy.

5. **Interview Talking Points**: 5-7 PE-level insights that would teach an
   interviewer something non-obvious about this system.

6. **PE Rubric Self-Assessment**: Score all 10 dimensions using the template
   from `references/principal-engineer-bar.md`. Name the weakest dimension.
   State what would raise it.

### Gate 6 -- evaluate before proceeding to outer loop

| # | Criterion | Pass condition |
|---|-----------|----------------|
| a | Bottlenecks authentic | Each bottleneck traces to a real constraint in the Phase 4 architecture. No hypothetical bottlenecks for components not in the design. |
| b | Tradeoff matrix complete | Matrix covers every major decision from Phases 4-5. No major choice missing. |
| c | Coverage sweep done | Building blocks index scanned. Skipped blocks listed with one-line reason each. |
| d | Cross-file consistency | All 5 checks from the Cross-File Consistency Protocol pass (see below). |
| e | Failure matrix present | Failure matrix has >= 5 rows covering different failure classes with blast radius, detection, degradation, and recovery for each. |

---

## Interviewer Checkpoint C -- after Phase 6

**Output**: append to `10-interview-transcript.md`
**Load**: `references/interviewer-protocol.md`

Run the Interviewer agent against the complete design set:
- `01-requirements.md` through `08-bottlenecks-and-tradeoffs.md`
- The context checkpoint
- Any prior Interviewer findings and Research findings in
  `10-interview-transcript.md`

Focus on:
- Bottleneck authenticity
- Incident reality and production grounding
- Evolution roadmap depth at 10x/100x
- Whether the weakest PE rubric dimension is genuine
- Any unresolved major/critical finding from earlier checkpoints

If there are **Critical** or **Major** findings, run the Research agent only for
those findings and revise the affected sections. Then append a **Revision Log**
to `10-interview-transcript.md` listing which files changed and which findings
were closed. If only minor findings remain, document them as known residual
risks and proceed.

---

## Interviewer-Research Loop Rules

The Interviewer-Research loop is a depth-control mechanism, not a second
generator. Keep revisions scoped.

1. **Interviewer runs at configurable points.** Default:
   `interview_points: [4, 5, 6]`. Trial runs may disable a checkpoint if it adds
   cost without changing depth scores.
2. **Research is conditional.** Research runs only when at least one finding is
   **Critical** or **Major**. Minor findings are fixed locally unless repeated
   across phases.
3. **Research is targeted.** The Research agent investigates only the named
   major/critical findings, using local references first and web research for
   gaps.
4. **Transcript is mandatory.** Append every Interviewer pass, Research pass,
   and revision log to `10-interview-transcript.md`.
5. **Blind review.** The Interviewer must not see phase self-evaluations,
   PE self-scores, or `09-eval-report.md`.
6. **Cross-model when available.** Prefer a different model family for the
   Interviewer when the platform supports it. Otherwise, use the same model with
   `references/interviewer-protocol.md`.
7. **No broad rewrites.** A major/critical finding maps to specific sections.
   Revise those sections only unless the architecture is critically invalid.

### Platform spawning guidance

- **Cursor**: use a subagent/task with the Interviewer prompt. If model
  selection is available, choose a different model family from the generator.
- **Claude Code**: spawn a separate agent or subprocess with the Interviewer
  prompt and pass only the files under review.
- **Codex CLI**: run the Interviewer as a parallel agent or separate CLI pass.
- **SKILL.md-compatible agents without subagents**: simulate the roles
  sequentially, but preserve the blind-review rule by hiding self-scores from
  the Interviewer prompt.

---

## Cross-File Consistency Protocol

Run during Gate 6. Re-read the generated files (use the context checkpoint for
01-05 context, re-read 06/07/08 directly).

### Check 1: Numbers flow

The capacity chain in `01-requirements.md` (DAU, QPS, storage) must match the
numbers that drive decisions in `06-high-level-design.md`. If the HLD uses
"100K QPS" but requirements say "50K QPS," one is wrong. Fix it.

### Check 2: API-schema alignment

Every endpoint in `04-api-design.md` must have a supporting access pattern in
`05-schema.md`. If the API has `GET /feed?cursor=X`, the schema must have an
index that serves cursor-based feed retrieval. List each endpoint and its
supporting index. Flag any without one.

### Check 3: Requirements-architecture coverage

Every functional requirement in `01-requirements.md` must have a traceable
component path in `06-high-level-design.md`. List each FR and name the
component path that serves it. Flag any FR with no path.

### Check 4: Deep-dive relevance

Every component deep-dived in `07-deep-dives.md` must appear in the
architecture from `06-high-level-design.md`. A deep dive on a component not in
the HLD is fabricated. Flag and replace.

### Check 5: Bottleneck authenticity

Each bottleneck in `08-bottlenecks-and-tradeoffs.md` must trace to a real
constraint in the architecture. If a bottleneck says "Redis write throughput"
but the architecture does not use Redis, it is fabricated. Flag and remove.

**For each failed check**: name the inconsistency, identify the file to revise,
fix it before proceeding.

---

## Outer Eval Loop

Runs after all 8 files pass their phase gates and the cross-file consistency
protocol, and after the Interviewer-Research loop has closed all critical and
major findings or documented why they remain.

```
REPEAT (max 1 revision pass):
  1. Score the design against all 10 PE rubric dimensions
     (read references/principal-engineer-bar.md scoring template)
     Use the Interviewer's independent findings in 10-interview-transcript.md
     as the primary evidence for technical depth, failure mastery, production
     grounding, and collaboration/adaptability.
  2. If average ≥ 4.5 AND no dimension < 4 → DONE
  3. If below bar:
     a. Identify the weakest dimension
     b. Map it to the specific file and section that is weakest
     c. Revise that section only (not the entire file)
     d. Re-score only the affected dimensions
  4. Write the final self-assessment into 08-bottlenecks-and-tradeoffs.md
     - Must name genuine weaknesses (not performative humility)
     - Must state what would raise the weakest dimension
```

The self-assessment is the last thing written. It reflects the actual design,
not an aspirational version. It must not contradict unresolved critical/major
Interviewer findings.

---

## Validator Harness (post-generation)

After all files are generated and the outer eval loop completes, run the
executable validator to produce a machine-verified eval report.

```
VALIDATOR STEP:
  1. Run: python3 -m validator validate <folder>
     (from the scripts/ directory within this skill)
  2. Read 09-eval-report.md produced by the validator
  3. If OVERALL = FAIL:
     a. Read the "Known Issues" section for specific failures
     b. Fix the flagged issues (max 1 remediation pass)
     c. Re-run validator
  4. If still FAIL after remediation:
     a. Document remaining failures in 09-eval-report.md "Known Issues"
     b. Proceed — the report transparently shows what passed and what didn't
  5. Final output: 9 files (01-08 + 09-eval-report.md)
```

The validator checks:
- **Structural**: File existence, required sections, capacity chain, latency
  budget math, error budget, PE rubric scores.
- **Cross-file consistency**: Numbers flow, API-schema alignment,
  requirements-architecture coverage, deep-dive relevance, bottleneck
  authenticity.
- **Quality signals**: Algorithm/protocol depth, production references, failure
  scenarios, tradeoff triads, coverage sweep completeness.
- **Depth eval**: L0-L3 algorithm/protocol depth, derivation completeness,
  tradeoff specificity, numeric breaking points, incident verifiability,
  bottleneck depth, Interviewer transcript independence, and conditional
  Research quality.

The `09-eval-report.md` is the final output artifact. It provides traceable
evidence that quality gates were checked.

---

## Context Management Protocol

These rules prevent context window exhaustion during the multi-phase generation.

1. **Just-in-time references.** Each phase header names 1-2 references to load.
   Never preload all 7 reference files at once.

2. **Context checkpoint.** After Phase 3, compress files 01-05 into a ~20-line
   summary (template above). Use this summary during Phases 4-6 instead of
   re-reading all 5 files.

3. **One file at a time.** Generate each output file completely before starting
   the next. Do not hold multiple partial drafts.

4. **Exemplar sampling.** When calibrating against existing problems, read only
   the corresponding file from `assets/exemplars/` (e.g., only the exemplar's
   `07-deep-dives.md` when generating deep dives), not the full 8-file set.

5. **Loop context.** During fix iterations, re-read only the file being fixed
   and the specific gate criteria. Do not re-read the entire generation history.

6. **Reference unloading.** After a phase completes, the phase-specific
   references are no longer needed. Do not carry `numbers-to-know.md` into
   Phase 5.

---

## Output File Convention

Generate all files in `system-design/<problem-name>/` relative to the user's
project root (the repo where the user invoked the skill — not relative to
this skill's install location):

```
01-requirements.md
02-non-functional-requirements.md
03-entities.md
04-api-design.md
05-schema.md
06-high-level-design.md
06-high-level-design.excalidraw    (visual companion — produced via excalidraw-diagram skill)
07-deep-dives.md
08-bottlenecks-and-tradeoffs.md
09-eval-report.md                  (produced by validator harness — PASS/FAIL evidence)
10-interview-transcript.md         (Interviewer critique, conditional Research findings, revision log)
```

Derive `<problem-name>` as a short kebab-case slug from the problem prompt
(e.g., "news-aggregation-feed", "url-shortener", "distributed-cache").
Scan existing folders in the output directory to avoid name collisions.

---

## Hard Rules

- **No name-dropping.** Every technology choice gets the trade-off triad:
  solves / worsens / when-to-change.
- **No design before numbers.** Capacity estimation precedes architecture.
- **No vague boxes.** If you cannot write the request, response, and primary
  key, the component is guesswork.
- **No infinite uptime.** Every component fails. State the degradation story.
- **No defending sunk designs.** When a constraint changes, name the
  invalidated assumption and redesign only the affected part.
- **No complexity for its own sake.** The cheapest design that meets the
  constraints wins. Justify every added component.

---

## Format Conventions

- Use markdown tables for structured comparisons.
- Use ASCII box diagrams for architecture (match existing HLD style).
- Use code blocks for API contracts, SQL queries, pseudocode.
- Use LaTeX math notation for algorithmic analysis where appropriate.
- Include capacity estimation math as inline code blocks.
- Every deep dive section should be self-contained and independently readable.

---

## Reference Index

All references live in `references/` relative to this file.

| File | When to load |
|------|-------------|
| `references/reasoning-engine.md` | Before starting (lines 1-131). Full file at Phase 6. |
| `references/principal-engineer-bar.md` | Phase 6 and outer eval loop. |
| `references/interviewer-protocol.md` | Interviewer checkpoints after Phases 4, 5, 6. |
| `references/research-protocol.md` | Conditional Research for major/critical Interviewer findings. |
| `references/building-blocks-index.md` | Phase 3, Phase 4, Phase 6 coverage sweep. |
| `references/company-profiles.md` | When user names a company. |
| `references/problem-bank.md` | When user asks for a problem to practice. |
| `references/tradeoff-framework.md` | Phase 4 when articulating design decisions. |
| `references/numbers-to-know.md` | Phase 1 and Phase 2 for estimation. |
| `references/faang-interview-patterns.md` | Phase 1 and Phase 4 for world-class calibration. |
| `references/hld-skill.md` | **Phase 4 primary** — problem-agnostic HLD loop. |
| `references/hld-archetypes.md` | Phase 4 — classify CRUD / feed / cache / aggregate / etc. |
| `assets/templates/` | Each phase — load matching template before generating. |
| `excalidraw-diagram` skill (companion) | Phase 4b (after Gate 4 passes). |
