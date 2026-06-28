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
    After 2 failures: flag in "known issues", proceed anyway

After all 6 phases:
  CROSS-FILE CONSISTENCY PROTOCOL (5 checks)
  OUTER EVAL LOOP (max 1 revision pass):
    1. Score all 10 PE rubric dimensions
    2. If avg ≥ 4.5 and no dim < 4 → DONE
    3. Else → revise weakest file section, re-score
  VALIDATOR HARNESS:
    1. Run python validator → produces 09-eval-report.md
    2. If FAIL: fix flagged issues (max 1 pass), re-run
    3. Final output: 9 files with traceable PASS/FAIL evidence
```

---

## Before Starting

1. Read `references/reasoning-engine.md` lines 1-131 (phase descriptions only).
   Skip the failure modes and checklists -- they are needed only at Phase 6.
2. Scan existing problem folders in the output directory (default:
   `system-design/` relative to the user's project root) to check for slug
   collisions. Derive `<problem-name>` as a short kebab-case slug from the
   prompt (e.g., "url-shortener", "distributed-cache", "news-feed").
   Read one exemplar file (not all 8) from `assets/exemplars/` matching the
   current phase when calibrating output quality.
3. If the user names a company, read `references/company-profiles.md`.
4. If the user asks "what should I practice," read `references/problem-bank.md`.

Do NOT preload all 7 reference files. Load just-in-time per phase.

---

## Phase 1: Frame the Problem

**Output**: `01-requirements.md`
**Load**: `references/numbers-to-know.md`

- State functional requirements with company-scale context.
- Capacity estimation: DAU → read QPS → write QPS → storage/day → total
  storage → bandwidth → server count.
- Explicit out-of-scope with one-line reasoning per exclusion.
- For data-intensive problems: ranking signals, time windows, personalization.
- **PE signal**: Question the problem framing. Surface hidden requirements.
  Propose scope that reveals judgment.

### Gate 1 -- evaluate before proceeding

| # | Criterion | Pass condition |
|---|-----------|----------------|
| a | Capacity chain complete | All links present: DAU → read QPS → write QPS → storage/day → total storage → bandwidth. No gaps. |
| b | Reframing present | At least 1 problem reframing or hidden requirement surfaced (not just clarifications). |
| c | Out-of-scope coverage | At least 3 out-of-scope items, each with one-line reasoning. |
| d | Numbers plausibility | Cross-check key numbers against `references/numbers-to-know.md`. Order-of-magnitude correct. |

**If any criterion fails**: identify the specific gap, fix only that section of
`01-requirements.md`, re-evaluate. Max 2 iterations.

---

## Phase 2: Set the Constraints

**Output**: `02-non-functional-requirements.md`
**Load**: `references/numbers-to-know.md` (if not already loaded)

- Percentile latency targets (P50/P95/P99/P99.9) with latency budget breakdown
  showing where each millisecond goes.
- Availability with SRE error budget math.
- Consistency model with explicit user-facing consequence.
- Durability guarantees by failure class.
- Operational requirements: zero-downtime deploy, monitoring thresholds, runbook
  sketches.
- Security NFRs.
- **PE signal**: Error budget math connecting to deployment cadence. Runbooks
  beyond "add monitoring."

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
**Load**: `references/building-blocks-index.md` (for storage options)

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
**Load**: `references/building-blocks-index.md`, `references/tradeoff-framework.md`

- Start with the cheapest design that satisfies requirements. Single DB,
  monolith, no cache. State why it works at current scale.
- Incrementally optimize: capacity numbers reveal bottlenecks. Add components
  only when a number forces them. Each addition gets the trade-off triad:
  solves / worsens / when-to-change.
- Cite production system references where the design mirrors or diverges.
- ASCII architecture diagrams with component boundaries, data flow, protocols.
- For each technology choice: what it solves, what it worsens, what would
  change it.
- **PE signal**: 2-3 architecture options for the most contested decision with
  named forces. Selection is judgment, not default.

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
| c | Options presented | At least 1 contested decision shows 2-3 options with named forces that pick between them. |
| d | Checkpoint consistency | Architecture handles the QPS, storage, and latency from the context checkpoint. Spot-check: do the numbers match? |
| e | Failure flow present | At least 2 component failures are traced through the system showing degradation behavior, recovery path, and user-facing impact. |

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

## Phase 5: Go Deep

**Output**: `07-deep-dives.md`
**Load**: `references/reasoning-engine.md` (curveball protocol, lines 228-244)

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

## Phase 6: Stress-Test and Synthesize

**Output**: `08-bottlenecks-and-tradeoffs.md`
**Load**: `references/principal-engineer-bar.md`, `references/building-blocks-index.md`
Also load `references/reasoning-engine.md` lines 152-244 (failure modes,
self-check, coverage sweep).

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
protocol.

```
REPEAT (max 1 revision pass):
  1. Score the design against all 10 PE rubric dimensions
     (read references/principal-engineer-bar.md scoring template)
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
not an aspirational version.

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
| `references/building-blocks-index.md` | Phase 3, Phase 4, Phase 6 coverage sweep. |
| `references/company-profiles.md` | When user names a company. |
| `references/problem-bank.md` | When user asks for a problem to practice. |
| `references/tradeoff-framework.md` | Phase 4 when articulating design decisions. |
| `references/numbers-to-know.md` | Phase 1 and Phase 2 for estimation. |
| `excalidraw-diagram` skill (companion) | Phase 4b (after Gate 4 passes). |
