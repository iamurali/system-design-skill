# Functional Requirements — [Problem Name]

## Problem Reframing

Before we design: [question that could change architecture]. **Decision:** [chosen scope and why].

## Early Problem Shape (provisional)

| Signal | Value |
|--------|-------|
| Provisional archetype (A1–A9) | |
| Dominant force (one sentence) | |
| Read:write ratio | :1 |

Refined in Phase 4 HLD; drives estimation emphasis in Phase 2.

### Hidden Requirements Surfaced

1. [Requirement interviewer did not state] — [why it matters]
2. [Optional second hidden requirement]

## Functional Requirements

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-1 | | P0 | |
| FR-2 | | P0 | |
| FR-3 | | P1 | |

Scope to **2–4 core features**. State read-heavy vs write-heavy ratio explicitly.

## Scale Assumptions (inputs for Phase 2)

**Do not derive QPS here** — the full capacity chain lives in
`02-non-functional-requirements.md`. Record inputs only.

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| DAU (or MAU) | | |
| Actions/user/day (read) | | |
| Actions/user/day (write) | | |
| Avg object / response size | | |
| Retention | | days |
| Peak factor | | × average (justify) |

## Success Metrics (SLIs)

| Metric | Target | Type |
|--------|--------|------|
| | | Business / Technical |

## Explicit Out-of-Scope

| Exclusion | Reason |
|-----------|--------|
| | One-line why |
| | |
| | |
