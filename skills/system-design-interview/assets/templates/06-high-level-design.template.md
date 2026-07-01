# High-Level Design — [Problem Name]

> Follow `references/hld-skill.md`. Classify archetype first. No default pipeline.

## Problem Shape Classification

| Signal | Value | Implication |
|--------|-------|-------------|
| Read QPS / Write QPS | | |
| Read:write ratio | | |
| P99 latency | ms | |
| Consistency | | |
| Dominant force | one sentence | |

**Primary archetype:** A_ from `hld-archetypes.md`  
**Secondary (if any):** A_

## Required Capabilities

No product names. Mark: **now** | **defer** | **skip**

| Capability | Layer | Trigger | Now / defer / skip |
|------------|-------|---------|-------------------|
| | | | |

## Architecture Evolution (Start Cheap)

| Version | Trigger | Capabilities added | Deferred |
|---------|---------|-------------------|----------|
| v0 | 1× | | |
| v1 | | | |

**Breaking point:** ___ breaks at ___ QPS because ___.

**Selected:** v___

## Architecture Research

### Research: [capability 1]

| Option class | Fits | Fails when | Ops / recovery | Verdict |
|--------------|------|------------|----------------|---------|
| | | | | |

**Selected:** ___ because ___

### Research: [capability 2]

(same table)

## System Overview

```
[Topology from YOUR archetype — CRUD, async, fanout, etc.]
```

## Flow 1: Write / Data Path

→ Durable at:

## Flow 2: Read / Query Path

| Hop | Role | Protocol | Latency budget |
|-----|------|----------|----------------|
| | | | ms |
| | **Total P99** | | |

## Flow 3: Failure and Degradation

### Failure: [component A]

- User impact / Degradation / Recovery / Stampede avoidance:

### Failure: [component B]

(same)

## Flow 4: Deploy and Migration

## Component Registry

| Role | Implementation | Capacity | Failure mode | Owner |
|------|----------------|----------|--------------|-------|

## Technology Trade-off Triads

### [Decision]

- **Solves:** / **Worsens:** / **When to change:**

## Production References

Mechanism or incident tied to a decision above — not a generic stack reference.
