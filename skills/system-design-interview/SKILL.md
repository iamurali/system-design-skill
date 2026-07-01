---
name: system-design-interview
description: >-
  Generate Principal-Engineer-grade system design interview preparation
  documents. Use when the user says "design a system", "system design for
  [company]", "prepare [system] for PE interview", "break down [system]",
  "system design interview", or names any system design problem (URL shortener,
  distributed cache, news feed, rate limiter, top-K, chat system, etc.).
  Produces 11 artifacts per problem (8 design docs + 1 Excalidraw diagram +
  1 eval report with PASS/FAIL evidence + 1 independent interview transcript)
  covering requirements, NFRs, entities, API, schema, HLD, deep dives,
  bottlenecks/tradeoffs, adversarial technical-depth review, and
  machine-verified quality validation. Calibrated for Principal Engineer interviews at
  Databricks, Anthropic, OpenAI, Google, Amazon, and Microsoft.
license: MIT
compatibility: >-
  Python 3.10+ (for validator only). No external dependencies — validator uses
  stdlib only. Excalidraw diagram rendering requires uv + Playwright (optional).
metadata:
  author: Murali K
  version: "1.1.0"
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
- Interviewer-Research loop that produces `10-interview-transcript.md`
- Context management protocol to prevent context overload
- Just-in-time reference loading schedule

**Step 2 -- Execute the orchestrator loop.**

Follow the orchestrator exactly. It tells you which reference files to load at
each phase, when to create a context checkpoint, and how to run the inner
generate-evaluate-fix cycle (max 2 iterations per phase gate).

**Step 3 -- Run the Interviewer-Research loop.**

After Phase 4, Phase 5, and Phase 6, run the Interviewer checkpoint from
`references/interviewer-protocol.md`. The Interviewer reviews blind to
self-scores and flags depth gaps, fake bottlenecks, wrong technology choices,
missing failures, and scale holes. Run `references/research-protocol.md` only
for **Major** or **Critical** findings; minor findings are fixed locally unless
they repeat. Append the critique, conditional Research findings, and revision
log to `10-interview-transcript.md`.

When the platform supports model selection, prefer a different model family for
the Interviewer to reduce self-eval leniency. Otherwise, use the same model with
the Interviewer protocol.

**Step 4 -- Run the outer eval loop.**

After all 8 design files pass their phase gates and the Interviewer-Research
loop has closed major/critical findings, score against the PE rubric using the
Interviewer findings as primary evidence. If below bar (avg < 4.5 or any
dimension < 4), revise the weakest file section. Max 1 revision pass.

**Step 5 -- Run the validator harness.**

After the outer eval loop completes, run the Python validator. Find the
validator at `scripts/validator/` relative to this skill directory. Run it
against the output folder:

```bash
python3 -m validator validate <output-folder>
```

Run this command from the `scripts/` directory within this skill, or use an
absolute path. This produces `09-eval-report.md` with PASS/FAIL evidence for
every gate criterion, cross-file consistency check, quality signal, and
technical-depth check. If FAIL, fix flagged issues (max 1 pass) and re-run.

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
- **[references/interviewer-protocol.md](references/interviewer-protocol.md)**
  -- Independent adversarial review protocol for technical depth.
- **[references/research-protocol.md](references/research-protocol.md)** --
  Conditional Research agent protocol for major/critical gaps.
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
- **[references/hld-design-protocol.md](references/hld-design-protocol.md)**
  -- **Phase 4 primary:** forces-first HLD; capability derivation; mandatory
  architecture research before product selection. Not a directional tech stack.
- **[references/faang-interview-patterns.md](references/faang-interview-patterns.md)**
  -- World-class calibration for requirements and interview bar. Read at Phase 1.
- **[assets/templates/](assets/templates/)** -- Required section skeletons per
  output file. Load the template matching the current phase before generating.
- **[references/numbers-to-know.md](references/numbers-to-know.md)** -- Latency
  table, QPS tiers, powers of 2, estimation recipes.

## Companion skills

- **excalidraw-diagram** -- Used at Phase 4b (after Gate 4 passes) to generate
  a visual `.excalidraw` companion diagram for the HLD. Bundled alongside this
  skill in the same repository.

## Exemplars

Use `assets/exemplars/trending-articles-top-k` as the **primary PE-grade
calibration exemplar** for **process** (capabilities → research → selection).
**Do not copy its Kafka/Flink/Redis choices** into other problems — run the
HLD protocol for each prompt. Use `assets/exemplars/in-memory-cache` for NFR
patterns. Read only the file matching the current phase.
