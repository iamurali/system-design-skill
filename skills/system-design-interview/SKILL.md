---
name: system-design-interview
description: >-
  Generate Principal-Engineer-grade system design interview preparation
  documents. Use when the user says "design a system", "system design for
  [company]", "prepare [system] for PE interview", "break down [system]",
  "system design interview", or names any system design problem (URL shortener,
  distributed cache, news feed, rate limiter, top-K, chat system, etc.).
  Produces 10 artifacts per problem (8 design docs + 1 Excalidraw diagram +
  1 eval report with PASS/FAIL evidence) covering requirements, NFRs, entities,
  API, schema, HLD, deep dives, bottlenecks/tradeoffs, and machine-verified
  quality validation. Calibrated for Principal Engineer interviews at
  Databricks, Anthropic, OpenAI, Google, Amazon, and Microsoft.
license: MIT
compatibility: >-
  Python 3.10+ (for validator only). No external dependencies — validator uses
  stdlib only. Excalidraw diagram rendering requires uv + Playwright (optional).
metadata:
  author: Murali K
  version: "1.0.0"
  repository: https://github.com/iamurali/system-design-skill
---

# System Design Interview -- Principal Engineer Grade

Generate rigorous system design documents by reasoning through the problem, not
by recalling memorized architectures. Every design is a hypothesis that holds
until a constraint changes.

## How to use this skill

**Step 1 -- Read the orchestrator:**

Read `references/orchestrator.md` (relative to this skill directory). It defines:
- The 6-phase generate-evaluate-fix loop with per-phase quality gates (27
  criteria across 6 gates)
- Cross-file consistency protocol (5 checks across all output files)
- Outer eval loop with PE rubric scoring
- Validator harness that produces machine-verified `09-eval-report.md`
- Context management protocol to prevent context overload
- Just-in-time reference loading schedule

**Step 2 -- Execute the orchestrator loop.**

Follow the orchestrator exactly. It tells you which reference files to load at
each phase, when to create a context checkpoint, and how to run the inner
generate-evaluate-fix cycle (max 2 iterations per phase gate).

**Step 3 -- Run the outer eval loop.**

After all 8 files pass their phase gates, score against the PE rubric. If below
bar (avg < 4.5 or any dimension < 4), revise the weakest file section. Max 1
revision pass.

**Step 4 -- Run the validator harness.**

After the outer eval loop completes, run the Python validator. Find the
validator at `scripts/validator/` relative to this skill directory. Run it
against the output folder:

```bash
python3 -m validator validate <output-folder>
```

Run this command from the `scripts/` directory within this skill, or use an
absolute path. This produces `09-eval-report.md` with PASS/FAIL evidence for
every gate criterion, cross-file consistency check, and quality signal. If
FAIL, fix flagged issues (max 1 pass) and re-run.

**Output location:** Generate all files in `system-design/<problem-name>/`
relative to the user's project root (the repo where the user invoked the
skill), not relative to this skill's install location.

## The Principal Engineer bar (quick calibration)

PE is not "Staff but more." It is a qualitatively different signal:

- **Reframes before solving.** Questions the problem itself. "Do users need
  exact ranking or would approximate trending suffice? That changes the entire
  architecture."
- **Sees the full solution space.** Lays out 2-3 architectures, explains the
  forces that pick between them, selects with judgment. Pivots instantly when a
  constraint changes.
- **Brings production war stories.** Not "Redis can do this" but "We ran Redis
  at 2M QPS and the failure mode that bit us was..."
- **Thinks organizationally.** Team ownership, blast radius of a bad deploy,
  oncall burden, cross-team dependencies.
- **Anticipates the 3-5 year arc.** What breaks at 10x, 100x, 1000x. What to
  rebuild vs evolve.
- **Teaches the interviewer something.** Novel insight, non-obvious tradeoff, a
  connection between subsystems that surprises.
- **YAGNI at scale.** Chooses the cheapest design that satisfies constraints and
  explains why the fancier option is not justified yet.

## Hard rules

- **No name-dropping.** Every technology choice gets the trade-off triad:
  solves / worsens / when-to-change.
- **No design before numbers.** Capacity estimation precedes architecture.
- **No vague boxes.** If you cannot write the request, response, and primary
  key, the component is guesswork.
- **No infinite uptime.** Every component fails. State the degradation story.
  "More retries" amplifies outages.
- **No defending sunk designs.** When a constraint changes, name the
  invalidated assumption and redesign only the affected part.
- **No complexity for its own sake.** The cheapest design that meets the
  constraints wins. Justify every added component.

## References (all relative to this skill directory)

- **[references/orchestrator.md](references/orchestrator.md)** -- The
  generate-evaluate-fix loop, phase gates, cross-file consistency, outer eval,
  validator harness. Read first, always.
- **[scripts/validator/](scripts/validator/)** -- Python CLI that produces
  `09-eval-report.md` with machine-verified PASS/FAIL results.
- **[references/principal-engineer-bar.md](references/principal-engineer-bar.md)**
  -- The 10-dimension PE rubric and self-scoring.
- **[references/reasoning-engine.md](references/reasoning-engine.md)** -- The
  6-phase design loop, failure modes, coverage sweep, curveball protocol.
- **[references/building-blocks-index.md](references/building-blocks-index.md)**
  -- L0-L7 bottom-up component catalog with PE depth signals.
- **[references/company-profiles.md](references/company-profiles.md)** --
  Interview format and PE expectations for 6 companies.
- **[references/problem-bank.md](references/problem-bank.md)** -- 30+ curated
  problems with company attribution and curveballs.
- **[references/tradeoff-framework.md](references/tradeoff-framework.md)** --
  The 3-question method and common axis tradeoffs.
- **[references/numbers-to-know.md](references/numbers-to-know.md)** -- Latency
  table, QPS tiers, powers of 2, estimation recipes.

## Companion skills

- **excalidraw-diagram** -- Used at Phase 4b (after Gate 4 passes) to generate
  a visual `.excalidraw` companion diagram for the HLD. Bundled alongside this
  skill in the same repository.

## Exemplars

Use `assets/exemplars/in-memory-cache` (exemplar for NFRs, latency budgets,
runbooks) or `assets/exemplars/trending-articles-top-k` (exemplar for deep
dives, capacity estimation) for output calibration. Read only the specific
file matching the current phase, not the full 8-file set.
