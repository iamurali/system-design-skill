# Functional Requirements — [Problem Name]

## Problem Reframing

Before we design: [question that could change architecture]. **Decision:** [chosen scope and why].

## Early Problem Shape (provisional)

| Signal | Value |
|--------|-------|
| Provisional archetype (A1–A9) | |
| Dominant force (one sentence) | |
| Read:write ratio | :1 |

Refined in Phase 4 HLD; drives estimation emphasis here.

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

## Capacity Estimation

### Assumptions

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| DAU | | |
| Actions/user/day (read) | | |
| Actions/user/day (write) | | |
| Avg object size | | |
| Retention | | days |
| Peak factor | | × average (justify) |

### Estimation Chain

```
DAU = ___
Read QPS  = DAU × reads/user/day ÷ 86,400 = ___ avg → ___ peak
Write QPS = DAU × writes/user/day ÷ 86,400 = ___ avg → ___ peak
Storage/day = writes/day × object_size = ___
Total storage = storage/day × retention = ___
Read bandwidth  = peak_read_QPS × response_size = ___
Write bandwidth = peak_write_QPS × request_size = ___
Server count = peak_QPS ÷ per_server_QPS (from numbers-to-know.md) = ___
```

### Component Load Summary

| Component | Peak load | Notes |
|-----------|-----------|-------|
| | | |

### Growth Trajectory

| Tier | DAU / QPS | What breaks first |
|------|-----------|-------------------|
| 1× (launch) | | |
| 10× | | |
| 100× | | |

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
