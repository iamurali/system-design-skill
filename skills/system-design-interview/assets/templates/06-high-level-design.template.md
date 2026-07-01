# High-Level Design — [Problem Name]

> **Process:** capabilities → research → selection → flows. Do not copy a
> canned stack. Technology names go in *Implementation* columns only after
> Step 3 research.

## Required Capabilities

Derived from Phase 1–3 constraints. **No product names in this section.**

| Constraint (number) | Required capability | Layer (L0–L7) | Mandatory when |
|---------------------|---------------------|---------------|----------------|
| | | | |

## Architecture Evolution (Start Cheap)

Capability-minimal versions — what you ship at 1× before adding layers.

| Version | Scale trigger | Capabilities present | Absent (deferred) | Why v0 works / breaks |
|---------|---------------|----------------------|-------------------|------------------------|
| v0 | 1× | | | |
| v1 | | | | |

**Selected for current scale:** v___ — justified by [number].

## Architecture Research

Run before finalizing products. Use `building-blocks-index.md` + research-protocol
(+ web if needed). Minimum **2 contested capabilities**, 2–3 options each.

### Research: [Capability 1 — e.g., durable write buffer]

| Option | Fits forces | Breaks when | Ops / failure notes | Verdict |
|--------|-------------|-------------|---------------------|---------|
| A | | | | |
| B | | | | |
| C | | | | |

**Selected:** ___ because ___ (cite QPS, freshness, or latency number).

### Research: [Capability 2 — e.g., ranked read serving]

(same table)

## System Overview

Use **roles** in the diagram; implementations in parentheses only if decided.

```
[Clients] → [Query API] → [Ranked materialized store] → response
[Writers] → [Ingestion] → [Event log] → [Aggregator] → [Ranked materialized store]
```

## Flow 1: Write / Data Path

1. [Role] → [Role] (protocol, ~X ms)
→ Durable at: [role / store class]

## Flow 2: Read / Query Path

| Hop | Role | Protocol | Latency budget |
|-----|------|----------|----------------|
| | | | ms |
| | **Total P99** | | **= Phase 2 target** |

## Flow 3: Failure and Degradation

### Failure: [Role / component] unavailable

- **User impact:**
- **Degradation:**
- **Recovery:**
- **Stampede avoidance:**

### Failure: [second component]

(same structure)

## Flow 4: Deploy and Migration

- **Strategy:**
- **Schema / contract migration:**
- **Rollback:**

## Component Registry

| Role | Implementation | Capacity | Failure mode | Owner |
|------|----------------|----------|--------------|-------|
| | | | | |

## Technology Trade-off Triads

Per capability added after v0:

### [Decision]

- **Solves:**
- **Worsens:**
- **When to change:**

## Production References

Evidence for **patterns**, not prescription: [system behavior, incident, lesson]
